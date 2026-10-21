import contextlib
import json
import ntpath
import os
import re
import shutil
import stat
import sys
import tempfile
import threading
from pathlib import Path

import platformdirs
import pytest

# --------------------------------------------------------------------------------------------------
# Live application-data isolation.
#
# pytest imports this module before it collects (imports) any test module, so this block runs before
# any vres_os module exists in the process. In this order it:
#   1. computes the protected live roots (%LOCALAPPDATA%\VresOS as the Windows shell, the environment
#      and platformdirs name it) from strings only, never touching them;
#   2. validates the temporary base (TEMP/TMP/TMPDIR agreement, every path component, the volume) with
#      read-only checks, before anything is written;
#   3. creates the session directory in that base, validates it, then creates the disposable Vres
#      application-data root inside it;
#   4. enables the isolation: VRES_DATA_DIR points at that root (every test then gets its own, below),
#      inherited database-target variables are removed, platformdirs is fenced so resolving the Vres
#      default data directory raises, and an irremovable audit hook refuses in-process filesystem
#      access resolving into a protected root and every unsafe or unreviewed child process.
#
# Child processes: the audit hook and the fence exist only in this interpreter, never inside a child.
# Before a child starts, the hook checks its effective environment (a safe disposable VRES_DATA_DIR,
# no database or libpq variables, no git execution/config variables) and its command line under the
# reviewed child-process policy below (no protected path, no Claude/Codex, only reviewed test files,
# and git, icacls and taskkill only in reviewed, scoped forms; never by executable name alone). What a
# permitted child then does is not observed: this is not an operating-system sandbox. In particular a
# child running Vres code resolves the database guard's registry through the Windows shell, not
# VRES_DATA_DIR, and git still reads the system git configuration of this machine.
# --------------------------------------------------------------------------------------------------

_LIVE_MESSAGE = "A test resolved or touched the live Vres application data"
_APP_NAME = "VresOS"
_DATA_DIR_ENV = "VRES_DATA_DIR"
_REGISTRY_NAME = "database-targets.json"
_OPERATIONAL_DATABASE_ENVIRONMENT = (
    "VRES_DATABASE_URL",
    "VRES_PROVENANCE_WRITER_DATABASE_URL",
    "VRES_MIGRATION_DATABASE_URL",
    "DATABASE_URL",
)
_TEST_DATABASE_ENVIRONMENT = ("VRES_TEST_DATABASE_URL", "VRES_ALLOW_TEST_DB")
_UNSAFE_COMPONENTS = frozenset({"google drive", "my drive", "googledrive", "onedrive", "vresbackups"})
# FILE_ATTRIBUTE_OFFLINE, _RECALL_ON_OPEN, _PINNED, _UNPINNED, _RECALL_ON_DATA_ACCESS: cloud placeholders.
_CLOUD_ATTRIBUTES = 0x1000 | 0x40000 | 0x80000 | 0x100000 | 0x400000
_LOCAL_FILESYSTEMS = frozenset({"NTFS", "REFS"})
_DRIVE_FIXED = 3
_WINDOWS = sys.platform == "win32"
_REPOSITORY = Path(__file__).resolve().parents[1]
_SOURCE_ROOT = _REPOSITORY / "src"


class LiveAppDataAccessRefused(PermissionError):
    """Raised (and recorded) when a test resolves or touches a protected live root."""


class IsolationError(RuntimeError):
    """A proposed temporary base or application-data root is not an acceptable disposable location."""


def _norm(path) -> str:
    text = os.fsdecode(os.fspath(path))
    if not text:
        raise ValueError("empty path")
    if text.startswith("\\\\?\\UNC\\"):
        text = "\\\\" + text[8:]
    elif text.startswith("\\\\?\\"):
        text = text[4:]
    return os.path.normcase(os.path.abspath(text))


def _within(form: str, root: str) -> bool:
    return form == root or form.startswith(root.rstrip(os.sep) + os.sep)


def _env_lookup(environment, name: str):
    """Environment names are case-insensitive on Windows."""
    if not _WINDOWS:
        return environment.get(name)
    wanted = name.upper()
    for key, value in environment.items():
        if str(key).upper() == wanted:
            return value
    return None


def _shell_local_app_data() -> str | None:
    """LocalAppData as the Windows shell (and the database guard) resolves it; a string, no file access."""
    if not _WINDOWS:
        return None
    import ctypes
    import uuid
    from ctypes import wintypes

    class GUID(ctypes.Structure):
        _fields_ = [("Data1", wintypes.DWORD), ("Data2", wintypes.WORD), ("Data3", wintypes.WORD),
                    ("Data4", ctypes.c_ubyte * 8)]

    value = uuid.UUID("F1B32785-6FBA-4FCF-9D55-7B8E7F157091")
    folder_id = GUID(value.time_low, value.time_mid, value.time_hi_version, (ctypes.c_ubyte * 8)(*value.bytes[8:]))
    shell32, ole32 = ctypes.WinDLL("shell32"), ctypes.WinDLL("ole32")
    shell32.SHGetKnownFolderPath.argtypes = [ctypes.POINTER(GUID), wintypes.DWORD, wintypes.HANDLE,
                                             ctypes.POINTER(ctypes.c_void_p)]
    shell32.SHGetKnownFolderPath.restype = ctypes.c_long
    ole32.CoTaskMemFree.argtypes = [ctypes.c_void_p]
    buffer = ctypes.c_void_p()
    try:
        if shell32.SHGetKnownFolderPath(ctypes.byref(folder_id), 0, None, ctypes.byref(buffer)) != 0:
            return None
        return ctypes.wstring_at(buffer.value) if buffer.value else None
    finally:
        if buffer.value:
            ole32.CoTaskMemFree(buffer)


_REAL_USER_DATA_DIR = platformdirs.user_data_dir
_REAL_USER_DATA_PATH = platformdirs.user_data_path


def _live_roots() -> list[str]:
    candidates = [_REAL_USER_DATA_DIR(_APP_NAME, appauthor=False, roaming=False),  # how vres_os.paths names it
                  _REAL_USER_DATA_DIR(_APP_NAME, appauthor=False, roaming=True)]
    shell = _shell_local_app_data()
    if shell:
        candidates.append(os.path.join(shell, _APP_NAME))
    for variable in ("LOCALAPPDATA", "APPDATA"):
        if os.environ.get(variable):
            candidates.append(os.path.join(os.environ[variable], _APP_NAME))
    return sorted({_norm(candidate) for candidate in candidates})


_PROTECTED = _live_roots()  # tests may temporarily append a decoy through live_app_data_fence.protect
_LIVE_REGISTRY_FILES = frozenset(os.path.join(root, _REGISTRY_NAME) for root in _PROTECTED)
_INSTALLED_PLUGIN = _norm(os.path.join(os.path.expanduser("~"), ".claude", "skills", "vres-os"))
_REFUSALS: list[str] = []
_UNEXPECTED: list[str] = []
_INIT_ORDER: list[str] = []


def _matches(form: str) -> bool:
    return any(_within(form, root) for root in _PROTECTED)


def _is_protected(path) -> bool:
    """Whether a path is, or resolves (through links and junctions) into, a protected root.

    A path that already names a protected root by its spelling is refused without touching it.
    """
    try:
        form = _norm(path)
    except (TypeError, ValueError):
        return False
    if _matches(form):
        return True
    try:
        return _matches(_norm(os.path.realpath(form)))
    except (OSError, ValueError):
        return False


def _refuse(record: str):
    _REFUSALS.append(record[:400])
    raise LiveAppDataAccessRefused(f"{_LIVE_MESSAGE}: {record[:400]}")


def _cloud_roots(environ) -> list[str]:
    roots = []
    for key, value in environ.items():
        if str(key).upper().startswith("ONEDRIVE") and value:
            with contextlib.suppress(ValueError, TypeError):
                roots.append(_norm(value))
    return roots


def _inspect_components(path: str, lstat=os.lstat) -> None:
    """Every component must exist and be a plain directory: no link, junction or cloud placeholder."""
    current = Path(path)
    for component in (current, *current.parents):
        try:
            info = lstat(component)
        except FileNotFoundError:
            raise IsolationError(f"a temporary-path component does not exist: {component}") from None
        except OSError as exc:
            raise IsolationError(f"a temporary-path component could not be inspected: {component}") from exc
        attributes = getattr(info, "st_file_attributes", 0)
        if stat.S_ISLNK(info.st_mode) or attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:
            raise IsolationError(f"a temporary-path component is a link, junction or reparse point: {component}")
        if attributes & _CLOUD_ATTRIBUTES:
            raise IsolationError(f"a temporary-path component is a cloud or offline placeholder: {component}")
        if not stat.S_ISDIR(info.st_mode):
            raise IsolationError(f"a temporary-path component is not a directory: {component}")


def _check_location(form: str, environ) -> None:
    """Not live data, not synchronized or backup storage, not a repository or git worktree."""
    if _is_protected(form):
        raise IsolationError(f"the location is protected live Vres data: {form}")
    if any(part.lower() in _UNSAFE_COMPONENTS for part in Path(form).parts):
        raise IsolationError(f"the location is in synchronized or backup storage: {form}")
    if any(_within(form, root) for root in _cloud_roots(environ)):
        raise IsolationError(f"the location is inside a OneDrive folder: {form}")
    if _within(form, _norm(_REPOSITORY)):
        raise IsolationError(f"the location is inside the repository: {form}")
    for ancestor in (Path(form), *Path(form).parents):
        if ancestor.parent != ancestor and os.path.lexists(ancestor / ".git"):
            raise IsolationError(f"the location is inside a git worktree: {ancestor}")


def _windows_volume(path: str) -> dict:
    """Read-only volume metadata for a path; raises when any query is unavailable."""
    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    def unavailable(query):
        raise IsolationError(f"Windows volume metadata is unavailable ({query}) for {path}")

    root = ctypes.create_unicode_buffer(1024)
    if not kernel32.GetVolumePathNameW(path, root, 1024):
        unavailable("GetVolumePathNameW")
    label, filesystem = ctypes.create_unicode_buffer(261), ctypes.create_unicode_buffer(261)
    serial, length, flags = wintypes.DWORD(), wintypes.DWORD(), wintypes.DWORD()
    if not kernel32.GetVolumeInformationW(root.value, label, 261, ctypes.byref(serial), ctypes.byref(length),
                                          ctypes.byref(flags), filesystem, 261):
        unavailable("GetVolumeInformationW")
    device = None
    if re.fullmatch(r"[A-Za-z]:\\", root.value):
        target = ctypes.create_unicode_buffer(1024)
        if not kernel32.QueryDosDeviceW(root.value[:2], target, 1024):
            unavailable("QueryDosDeviceW")
        device = target.value
    long_path = ctypes.create_unicode_buffer(32768)
    if not kernel32.GetLongPathNameW(path, long_path, 32768):
        unavailable("GetLongPathNameW")
    return {"root": root.value, "drive_type": kernel32.GetDriveTypeW(root.value), "filesystem": filesystem.value,
            "label": label.value, "device": device, "long_path": long_path.value}


def _check_windows_volume(info) -> None:
    """A fixed local disk volume (by device, type and filesystem), never a network, virtual or cloud drive."""
    if not isinstance(info, dict) or any(not info.get(key) for key in ("root", "filesystem", "long_path")):
        raise IsolationError("Windows volume metadata is inconclusive")
    if str(info["root"]).startswith(("\\\\", "//")):
        raise IsolationError(f"the temporary base is on a UNC or non-drive volume: {info['root']}")
    if info.get("drive_type") != _DRIVE_FIXED:
        raise IsolationError(f"the temporary base is not on a fixed local disk (drive type {info.get('drive_type')})")
    if str(info["filesystem"]).upper() not in _LOCAL_FILESYSTEMS:
        raise IsolationError(f"the temporary base filesystem is not NTFS or ReFS: {info['filesystem']}")
    if str(info.get("label") or "").strip().lower() in {"google drive", "onedrive"}:
        raise IsolationError(f"the temporary base is on a cloud-drive volume: {info.get('label')}")
    if not re.fullmatch(r"\\Device\\HarddiskVolume\d+", str(info.get("device") or "")):
        raise IsolationError(f"the temporary base volume is not a local disk volume: {info.get('device')}")


def _assess_temp_base(environ, *, platform=sys.platform, current_tempdir=None, volume=None, lstat=os.lstat,
                      realpath=os.path.realpath) -> str:
    """Return the temporary base only if it is trustworthy; read-only, raises IsolationError otherwise.

    Windows: TEMP and TMP (and TMPDIR if set) must be absolute drive paths naming the same directory,
    which must agree with tempfile's own base, consist of existing plain directories (no link, junction,
    reparse point or cloud placeholder), lie outside live data, synchronized/backup storage and any
    repository, and sit on a fixed local NTFS/ReFS disk volume whose long path is not redirected.
    Other platforms: TMPDIR (default /tmp) must be absolute; its resolved path must consist of plain
    directories and pass the same location checks (no volume API exists there).
    """
    windows = platform == "win32"
    if windows:
        temp, tmp, tmpdir = (_env_lookup(environ, name) for name in ("TEMP", "TMP", "TMPDIR"))
        if not temp or not tmp:
            raise IsolationError("TEMP and TMP must both be set")
        values = [temp, tmp] + ([tmpdir] if tmpdir else [])
        for value in values:
            if str(value).startswith(("\\\\", "//")):
                raise IsolationError(f"the temporary base is a UNC path: {value}")
            if not re.match(r"^[A-Za-z]:[\\/]", str(value)) or not ntpath.isabs(str(value)):
                raise IsolationError(f"the temporary base is not an absolute drive path: {value}")
        if len({_norm(value) for value in values}) != 1:
            raise IsolationError("TEMP, TMP and TMPDIR do not name the same directory")
        base = os.path.abspath(temp)
    else:
        candidate = environ.get("TMPDIR") or "/tmp"
        if not os.path.isabs(candidate):
            raise IsolationError(f"TMPDIR is not absolute: {candidate}")
        if _matches(_norm(candidate)):  # refused by its spelling, before resolving (touching) it
            raise IsolationError(f"the location is protected live Vres data: {candidate}")
        base = realpath(candidate)
    form = _norm(base)
    if current_tempdir is not None and _norm(current_tempdir) != form:
        raise IsolationError(f"tempfile already uses a different base: {current_tempdir}")
    _check_location(form, environ)  # first: a protected location is refused by its spelling, untouched
    _inspect_components(base, lstat)
    if windows:
        info = (volume or _windows_volume)(base)
        _check_windows_volume(info)
        if _norm(info["long_path"]) != _norm(realpath(base)):
            raise IsolationError(f"the temporary base resolves elsewhere: {base}")
    return base


_TRUSTED_TEMP_BASE: str | None = None


def _require_disposable(path, *, base=None) -> Path:
    """Accept only a location inside the trusted temporary base that is not, and does not resolve into, live data."""
    base = base if base is not None else _TRUSTED_TEMP_BASE
    if base is None:
        raise IsolationError("the temporary base has not been validated")
    if path is None or not str(path):
        raise IsolationError("no application-data root is set")
    raw = os.fsdecode(os.fspath(path))
    if not os.path.isabs(raw):
        raise IsolationError(f"the application-data root must be absolute: {raw}")
    form = _norm(raw)
    if _is_protected(form):
        raise IsolationError(f"the application-data root is protected live data: {raw}")
    if any(part.lower() in _UNSAFE_COMPONENTS for part in Path(form).parts):
        raise IsolationError(f"the application-data root is in a synchronized or backup location: {raw}")
    real = _norm(os.path.realpath(form))
    if not _within(real, _norm(os.path.realpath(base))):
        raise IsolationError(f"the application-data root is outside the trusted temporary base: {raw}")
    if _within(real, _norm(_REPOSITORY)):
        raise IsolationError(f"the application-data root is inside the repository: {raw}")
    current = Path(form)
    for ancestor in (current, *current.parents):
        try:
            info = os.lstat(ancestor)
        except FileNotFoundError:
            continue
        except OSError as exc:
            raise IsolationError(f"the application-data root could not be inspected: {raw}") from exc
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
            raise IsolationError(f"the application-data root passes through a link or junction: {ancestor}")
        if ancestor != current and ancestor.parent != ancestor and (ancestor / ".git").exists():
            raise IsolationError(f"the application-data root is inside a git worktree: {ancestor}")
    return Path(path)


def _establish_session_root(environ, *, assess=_assess_temp_base, order=None, adopt_tempdir=False):
    """Validate the base, then create and validate the session directory, then the Vres root.

    Nothing is written before the base is trusted; an inherited VRES_DATA_DIR is judged (read-only)
    against that base before anything is created.
    """
    order = _INIT_ORDER if order is None else order
    order.append("validate-temp-base")
    base = assess(environ, current_tempdir=tempfile.tempdir)
    inherited = _env_lookup(environ, _DATA_DIR_ENV)
    if inherited:
        _require_disposable(inherited, base=base)
    if adopt_tempdir:
        tempfile.tempdir = base  # every later tempfile/pytest temporary path uses the validated base
    order.append("create-session-directory")
    session = tempfile.mkdtemp(prefix="vres-pytest-app-data-", dir=base)
    order.append("validate-session-directory")
    info = os.lstat(session)
    if (stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT
            or not stat.S_ISDIR(info.st_mode) or _norm(os.path.dirname(session)) != _norm(base)
            or _norm(os.path.realpath(session)) != _norm(os.path.join(os.path.realpath(base),
                                                                       os.path.basename(session)))):
        raise IsolationError(f"the session directory is not a plain directory in the temporary base: {session}")
    order.append("create-app-data-root")
    root = Path(session) / _APP_NAME
    root.mkdir()
    _require_disposable(root, base=base)
    return base, root


def _fenced(real, name):
    def resolver(*args, **kwargs):
        value = real(*args, **kwargs)
        if _is_protected(value):
            _refuse(f"platformdirs.{name} resolved {value}")
        return value

    resolver.__vres_live_fence__ = True
    resolver.__name__ = name
    return resolver


def _check_fence_intact() -> None:
    """Fail if any resolver Vres can reach now resolves the live default again."""
    resolvers = {"platformdirs.user_data_dir": platformdirs.user_data_dir,
                 "platformdirs.user_data_path": platformdirs.user_data_path}
    paths = sys.modules.get("vres_os.paths")
    if paths is not None:
        resolvers["vres_os.paths.user_data_dir"] = getattr(paths, "user_data_dir", None)
    for name, resolver in resolvers.items():
        if resolver is None or getattr(resolver, "__vres_live_fence__", False):
            continue
        if _is_protected(resolver(_APP_NAME, appauthor=False, roaming=False)):
            raise AssertionError(f"{name} was replaced and re-enabled the live Vres application-data path")


# The reviewed child-process policy (D1-R2/R4). Every child is judged before it is created, from its actual
# executable, its arguments, the invoking test file, its working directory and repository scope, the paths
# or processes it targets and its effective environment. Nothing is permitted by executable name alone:
#   python, python-vres, node, shell, powershell   only from test files reviewed for that class
#                (python-vres: the command line references vres_os, the source tree or a Vres worker loader);
#   git        only from reviewed test files, as an approved git binary, with an allowlisted builtin
#              subcommand (so no alias), allowlisted -c settings and git environment, no system or global
#              configuration (GIT_CONFIG_NOSYSTEM=1, GIT_CONFIG_GLOBAL=<null device>), inside a scratch
#              repository in the trusted temporary base whose local configuration and hooks run nothing,
#              with every filesystem operand contained in that base (subcommand grammar, no "..", no
#              drive-relative form); in this repository only read-only object inspection; never a network
#              or remote operation; clone only from a local temporary bundle;
#   shell      only from reviewed test files, and only "cmd /c mklink /J <temporary path> <temporary path>";
#   icacls     only from reviewed test files: <disposable path> /inheritance:r /grant:r <current user>:<rights>;
#   taskkill   only from reviewed test files: /PID <n> /T /F where <n> is a direct child of this process.
# os.system, os.startfile, os.spawn*, os.exec* and os.posix_spawn are refused outright: a shell command string
# cannot be judged by splitting it. Claude/Codex children and command lines naming live data or the installed
# plugin are always refused.
_REVIEWED_CHILD_SITES = {
    "tests/test_claude_experiment_producer.py": frozenset({"python-vres"}),  # import-only module check
    # scratch repositories and worktrees (workers faked); taskkill when generate_patch stops its own git child
    # at the patch byte ceiling (timing-dependent, so not every run reaches it)
    "tests/test_codex_handoff.py": frozenset({"git", "taskkill"}),
    "tests/test_credential_broker.py": frozenset({"python", "git", "icacls"}),  # env echo; git; ACLs on temp files
    "tests/test_database_contact_guard.py": frozenset({"python-vres"}),  # registry lock on a temporary root
    "tests/test_e4_frozen_contract_integrity.py": frozenset({"git"}),  # git show <rev>:<path> in this repository
    "tests/test_e6_observability_hook.py": frozenset({"git"}),  # ls-tree/cat-file of this repository's HEAD
    "tests/test_e6_reference_hooks.py": frozenset({"git"}),  # project discovery on temporary projects
    "tests/test_executor.py": frozenset({"python-vres"}),  # vres_os.procedure_worker: no paths, no database
    "tests/test_install_preflight.py": frozenset({"python", "python-vres"}),  # import smoke, report/pip stubs
    "tests/test_live_app_data_isolation.py": frozenset({"python", "python-vres", "git"}),  # these regressions
    "tests/test_local_secrets.py": frozenset({"python", "git", "icacls"}),  # env echo; git; ACLs on temp files
    "tests/test_personal_feature_fence.py": frozenset({"python"}),  # scripts/release_gate.py on a temp tree
    "tests/test_project.py": frozenset({"git"}),  # project discovery on temporary directories
    "tests/test_release_artifact.py": frozenset({"python-vres", "git"}),  # release_artifact.py tool; bundles
    "tests/test_release_boundaries.py": frozenset({"python", "python-vres", "taskkill"}),  # bounded runs
    "tests/test_runtime_surfaces.py": frozenset({"python"}),  # scripts/release_gate.py -O refusal
    "tests/test_windows_node_mcp_git.py": frozenset({"node", "git"}),  # node -> python discover_project
    "tests/integration/test_secret_safe_onboarding_journey.py": frozenset({"shell"}),  # mklink, opt-in only
}
_ACTIVE_TEST = {"file": None, "integration": False}

_GIT_NETWORK_COMMANDS = frozenset({
    "fetch", "push", "pull", "remote", "ls-remote", "submodule", "daemon", "archive", "send-email", "send-pack",
    "fetch-pack", "upload-pack", "receive-pack", "upload-archive", "request-pull", "svn", "p4", "cvsimport",
    "cvsexportcommit", "cvsserver", "http-fetch", "http-push", "imap-send", "instaweb", "credential",
    "credential-cache", "credential-store", "remote-ext", "remote-fd", "remote-http", "remote-https"})
# Builtin subcommands reviewed for scratch repositories (the census of the suite plus read-only queries).
_GIT_SCRATCH_COMMANDS = frozenset({
    "add", "apply", "branch", "bundle", "cat-file", "check-ignore", "checkout", "clone", "commit", "config", "diff",
    "for-each-ref", "fsck", "hash-object", "init", "log", "ls-files", "ls-tree", "merge-base", "mv", "rev-list",
    "rev-parse", "rm", "show", "show-ref", "stash", "status", "tag", "update-index", "update-ref", "worktree"})
_GIT_REPOSITORY_COMMANDS = frozenset({"cat-file", "ls-tree", "rev-parse", "show"})  # read-only inspection
_GIT_COMMAND_OPTIONS = {"user.name": None, "user.email": None, "commit.gpgsign": "false", "core.quotepath": None,
                        "core.fsmonitor": "false"}  # -c key: required value (None: any value)
_GIT_CONFIG_WRITABLE = frozenset({"core.autocrlf", "core.symlinks", "extensions.worktreeconfig", "user.name",
                                  "user.email", "commit.gpgsign"})
_GIT_ENVIRONMENT = {"GIT_OPTIONAL_LOCKS": None, "GIT_NO_REPLACE_OBJECTS": None, "GIT_TERMINAL_PROMPT": "0",
                    "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull, "GIT_EDITOR": ":",
                    "GIT_PAGER": "cat", "GIT_AUTHOR_NAME": None,
                    "GIT_AUTHOR_EMAIL": None, "GIT_AUTHOR_DATE": None, "GIT_COMMITTER_NAME": None,
                    "GIT_COMMITTER_EMAIL": None, "GIT_COMMITTER_DATE": None}
# Subcommand arguments that run programs, reach remotes, install hooks or write outside the repository.
# (Clone's short forms -u/-c are refused by its own option allowlist.)
_GIT_DANGEROUS_ARGUMENTS = re.compile(r"^(--upload-pack|--receive-pack|--exec|--template|--config|"
                                      r"--recurse-submodules|--separate-git-dir|--reference|--shared|--ext-diff|"
                                      r"--textconv|--filters|--output|--no-index|--unsafe-paths|--directory)",
                                      re.I)
# Every git child reads no system or global configuration, and starts no editor (":" is git's no-editor
# value) and no pager ("cat" is git's no-pager value).
_GIT_ISOLATION = {"GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull, "GIT_EDITOR": ":", "GIT_PAGER": "cat"}
# Local (scratch-repository) configuration that can run a program, include other configuration or reach out.
_GIT_RISKY_CONFIGURATION = re.compile(
    r"^(core\.(hookspath|fsmonitor|sshcommand|gitproxy|askpass|pager|editor|attributesfile)|"
    r"filter\..+\.(clean|smudge|process)|diff\..+\.(textconv|command)|merge\..+\.driver|include\.path|"
    r"includeif\..+\.path|credential\..*|alias\..*|gpg\..*|ssh\..*|uploadpack\..*|receive\..*|"
    r"sequence\.editor|pager\..*|url\..+\.(insteadof|pushinsteadof)|http\..*|protocol\..*|init\.templatedir|"
    r"core\.worktree|core\.alternaterefscommand|diff\.(external|tool|guitool)|merge\.(tool|guitool)|"
    r"(diff|merge)tool\..*|interactive\..*|trailer\..+\.(command|cmd)|pretty\..*|hook\..*|"
    r"remote\..+\.(uploadpack|receivepack|vcs|proxy))$")
# Local settings that sign or verify signatures (gpg, ssh-keygen or an X.509 tool): refused unless false.
_GIT_SIGNING_CONFIGURATION = frozenset({"commit.gpgsign", "tag.gpgsign", "tag.forcesignannotated", "push.gpgsign",
                                        "log.showsignature", "merge.verifysignatures", "pull.verifysignatures"})
_GIT_FALSE = frozenset({"false", "no", "off", "0", ""})
# Options that sign, verify a signature, open an editor or run an interactive selection, for every
# subcommand; an unambiguous abbreviation (git accepts those) counts as the option.
_GIT_EXECUTION_LONG_OPTIONS = {"--gpg-sign": "signs", "--show-signature": "verifies a signature",
                               "--edit": "opens an editor", "--edit-description": "opens an editor",
                               "--reedit-message": "opens an editor", "--interactive": "is interactive"}
# Per subcommand: the same behaviours under their short and command-specific names, and the reviewed
# option grammar (flags, options taking a value); anything else is refused as unreviewed.
_GIT_EXECUTION_OPTIONS = {
    "commit": {"-S": "signs", "-e": "opens an editor", "-c": "opens an editor", "-p": "is interactive",
               "--patch": "is interactive"},
    "tag": {"-s": "signs", "--sign": "signs", "-u": "signs", "--local-user": "signs", "-v": "verifies a signature",
            "--verify": "verifies a signature", "-e": "opens an editor"},
    "add": {"-p": "is interactive", "--patch": "is interactive", "-i": "is interactive", "-e": "opens an editor"},
    "checkout": {"-p": "is interactive", "--patch": "is interactive"},
    "stash": {"-p": "is interactive", "--patch": "is interactive"},
}
_GIT_OPTION_GRAMMAR = {
    "commit": ({"-q", "--quiet", "-a", "--all", "--allow-empty", "--allow-empty-message", "--no-verify", "-n",
                "--no-gpg-sign", "--amend", "--no-edit", "-s", "--signoff", "--reset-author", "-o", "--only", "-i",
                "--include", "--dry-run"},
               {"-m", "--message", "-F", "--file", "-C", "--reuse-message", "--author", "--date", "--cleanup"}),
    "tag": ({"-d", "--delete", "-l", "--list", "-f", "--force", "-a", "--annotate", "--no-sign"},
            {"-m", "--message", "-F", "--file", "--sort", "--contains", "--points-at", "--cleanup"}),
    "add": ({"-A", "--all", "-f", "--force", "-u", "--update", "-n", "--dry-run", "-v", "--verbose", "-N",
             "--intent-to-add", "--refresh", "--ignore-errors", "--ignore-missing", "--renormalize"},
            {"--chmod"}),
    "checkout": ({"--detach", "-f", "--force", "-q", "--quiet"}, {"-b", "-B", "--orphan"}),
    "stash": ({"-u", "--include-untracked", "-k", "--keep-index", "--no-keep-index", "-q", "--quiet", "-a",
               "--all", "-S", "--staged"}, {"-m", "--message"}),
}
_GIT_MESSAGE_OPTIONS = frozenset({"-m", "--message", "-F", "--file", "-C", "--reuse-message"})
# Credential and key stores never appear as a git operand, even inside the temporary base.
_SENSITIVE_COMPONENTS = frozenset({".ssh", ".gnupg", ".aws", ".azure", ".kube", ".docker", ".claude",
                                   ".git-credentials", ".netrc", "_netrc"})
_FORBIDDEN_LAUNCH_EVENTS = frozenset({"os.system", "os.startfile", "os.spawn", "os.exec", "os.posix_spawn"})


def _approved_executables(name: str) -> frozenset[str]:
    """The binaries a bare or explicit program name may be: what PATH resolves now (and, for Git for
    Windows, the same installation's cmd, mingw64/bin and bin launchers)."""
    found = shutil.which(name)
    if not found:
        return frozenset()
    real = Path(os.path.realpath(found))
    approved = {_norm(real)}
    if _WINDOWS and name == "git":
        for ancestor in real.parents:
            if (ancestor / "cmd" / "git.exe").is_file() and (ancestor / "mingw64" / "bin" / "git.exe").is_file():
                approved |= {_norm(ancestor / "cmd" / "git.exe"), _norm(ancestor / "mingw64" / "bin" / "git.exe"),
                             _norm(ancestor / "bin" / "git.exe")}
                break
    return frozenset(approved)


_APPROVED_EXECUTABLES = {name: _approved_executables(name) for name in ("git", "icacls", "taskkill")}
if _WINDOWS:
    _APPROVED_EXECUTABLES["shell"] = _approved_executables("cmd")


def _split_command_line(line: str) -> list[str]:
    """Split a command line exactly as the child will see it (CommandLineToArgvW on Windows)."""
    if not line.strip():
        return []
    if not _WINDOWS:
        import shlex

        return shlex.split(line)
    import ctypes
    from ctypes import wintypes

    shell32, kernel32 = ctypes.WinDLL("shell32"), ctypes.WinDLL("kernel32")
    shell32.CommandLineToArgvW.argtypes = [wintypes.LPCWSTR, ctypes.POINTER(ctypes.c_int)]
    shell32.CommandLineToArgvW.restype = ctypes.POINTER(wintypes.LPWSTR)
    kernel32.LocalFree.argtypes = [ctypes.c_void_p]
    count = ctypes.c_int()
    parsed = shell32.CommandLineToArgvW(line, ctypes.byref(count))
    if not parsed:
        raise IsolationError("a child command line could not be parsed")
    try:
        return [parsed[index] for index in range(count.value)]
    finally:
        kernel32.LocalFree(parsed)


def _child_command(event: str, args) -> tuple[str, list[str], str, str | None]:
    """(program, argv, command line, working directory) of a would-be child."""
    cwd = None
    if event == "subprocess.Popen":
        executable, argv, cwd = args[0], args[1], args[2]
    elif event == "os.system":
        executable, argv = None, args[0]
    elif event == "os.spawn":
        executable, argv = args[1], args[2]
    else:  # os.exec, os.posix_spawn
        executable, argv = args[0], args[1]
    if isinstance(argv, (str, bytes, os.PathLike)):
        line = os.fsdecode(argv)
        parts = _split_command_line(line)
    else:
        parts = [os.fsdecode(a) if isinstance(a, (bytes, os.PathLike)) else str(a) for a in (argv or ())]
        line = " ".join(parts)
    program = os.fsdecode(executable) if executable else (parts[0] if parts else "")
    return program, parts, line, (os.fsdecode(cwd) if cwd is not None else None)


def _classify_child(program: str, command_line: str) -> str:
    stem = re.sub(r"\.(exe|cmd|bat|com)$", "", os.path.basename(program.strip().strip('"')).lower())
    line = os.path.normcase(command_line)
    if stem in {"claude", "codex"}:
        return "provider"
    if stem.startswith("python") or stem == "py" or (program and _norm(program) == _norm(sys.executable)):
        vres = "vres_os" in line or os.path.normcase(str(_SOURCE_ROOT)) in line or "run_module" in line
        return "python-vres" if vres else "python"
    return {"git": "git", "icacls": "icacls", "taskkill": "taskkill", "node": "node", "cmd": "shell",
            "sh": "shell", "bash": "shell", "zsh": "shell", "dash": "shell", "powershell": "powershell",
            "pwsh": "powershell"}.get(stem, "other")


def _executable_problem(kind: str, program: str) -> str | None:
    """The program must be the approved binary, and a bare name must not be shadowed in the directories
    Windows searches before PATH (the interpreter's own directory and the current directory)."""
    approved = _APPROVED_EXECUTABLES.get(kind) or frozenset()
    if not approved:
        return f"no approved {kind} executable was found"
    text = program.strip().strip('"')
    if os.path.dirname(text):
        return None if _norm(os.path.realpath(text)) in approved else f"{text} is not the approved {kind} executable"
    if _WINDOWS:
        names = [text] if os.path.splitext(text)[1] else [text + suffix for suffix in (".exe", ".com", ".bat", ".cmd")]
        for directory in {os.path.dirname(sys.executable), os.getcwd()}:
            for name in names:
                if os.path.lexists(os.path.join(directory, name)):
                    return f"{name} in {directory} would shadow the approved {kind}"
    found = shutil.which(text)
    if not found or _norm(os.path.realpath(found)) not in approved:
        return f"{text} does not resolve to the approved {kind} executable"
    return None


def _is_absolute_argument(value: str) -> bool:
    return bool(re.match(r"^[A-Za-z]:[\\/]", value)) or value.startswith(("\\\\", "//")) or \
        (not _WINDOWS and value.startswith("/"))


def _disposable_path_problem(value: str, relative_to: str | None = None) -> str | None:
    """A filesystem operand (relative ones resolved against relative_to) must stay in the trusted base."""
    path = value if _is_absolute_argument(value) or relative_to is None else os.path.join(relative_to, value)
    if _is_protected(path):
        return f"{value} is protected live data"
    real = _norm(os.path.realpath(path))
    if any(part.lower() in _UNSAFE_COMPONENTS | _SENSITIVE_COMPONENTS for part in Path(real).parts):
        return f"{value} is in synchronized, backup or credential storage"
    if not _within(real, _norm(os.path.realpath(_TRUSTED_TEMP_BASE))):
        return f"{value} is outside the trusted temporary base"
    if _within(real, _norm(_REPOSITORY)):
        return f"{value} is inside the repository"
    return None


def _has_parent_component(value: str) -> bool:
    """A ".." path component; revision syntax (A..B, A...B, HEAD~1..) never has one."""
    return any(part == ".." for part in re.split(r"[\\/]", value))


def _is_drive_relative(value: str) -> bool:
    return _WINDOWS and bool(re.match(r"^[A-Za-z]:(?![\\/])", value))


def _git_scope(directory: str) -> str | None:
    real = _norm(os.path.realpath(directory))
    if _is_protected(real):
        return None
    if _within(real, _norm(os.path.realpath(_TRUSTED_TEMP_BASE))) and not _within(real, _norm(_REPOSITORY)):
        return "scratch"
    if _within(real, _norm(_REPOSITORY)):
        return "repository"
    return None


def _git_problem(argv: list[str], cwd: str | None, environment) -> str | None:
    for key, value in environment.items():
        name = (os.fsdecode(key) if isinstance(key, bytes) else str(key))
        name = name.upper() if _WINDOWS else name
        if name.startswith("GIT_"):
            if name not in _GIT_ENVIRONMENT:
                return f"git environment variable {name} is not allowed"
            required = _GIT_ENVIRONMENT[name]
            if required is not None and str(value).lower() != str(required).lower():
                return f"git environment variable {name} has an unreviewed value"
    args = argv[1:]
    if args == ["--version"]:
        return None
    directories, index = [], 0
    while index < len(args) and args[index].startswith("-"):
        option = args[index]
        if option == "-C" and index + 1 < len(args):
            directories.append(args[index + 1])
            index += 2
            continue
        if option == "-c" and index + 1 < len(args):
            key, _, value = args[index + 1].partition("=")
            key = key.lower()
            if key not in _GIT_COMMAND_OPTIONS or (
                    _GIT_COMMAND_OPTIONS[key] is not None and value.lower() != _GIT_COMMAND_OPTIONS[key]):
                return f"git -c {key} is not an allowed setting"
            index += 2
            continue
        return f"git global option {option.split('=')[0]} is not allowed"
    if index >= len(args):
        return "git without a subcommand"
    command, rest = args[index], args[index + 1:]
    if command in _GIT_NETWORK_COMMANDS:
        return f"git {command} (network or remote operation) is never allowed"
    directory = cwd or os.getcwd()
    for part in directories:
        directory = os.path.join(directory, part)
    scope = _git_scope(directory)
    if scope is None:
        return f"git outside a scratch repository or this repository: {directory}"
    for argument in rest:
        if "://" in argument or argument.lower().startswith("ext::"):
            return "git URL or remote-helper argument is not allowed"
        if _GIT_DANGEROUS_ARGUMENTS.match(argument):
            return f"git argument {argument.split('=')[0]} is not allowed"
        candidate = argument.split("=", 1)[1] if argument.startswith("-") and "=" in argument else argument
        if _has_parent_component(candidate):
            return f"git operand {candidate} escapes its directory (..)"
        if _is_drive_relative(candidate):
            return f"git operand {candidate} is an ambiguous drive-relative path"
        if _is_absolute_argument(candidate):
            problem = _disposable_path_problem(candidate)
            if problem:
                return f"git path argument: {problem}"
    problem = _git_execution_problem(command, rest)
    if problem:
        return problem
    if scope == "repository":
        if command not in _GIT_REPOSITORY_COMMANDS:
            return f"git {command} may not run in this repository (read-only object inspection only)"
        if command == "show" and not (len(rest) == 1 and ":" in rest[0] and not rest[0].startswith("-")):
            return "git show in this repository is limited to <rev>:<path>"
        return None
    if command not in _GIT_SCRATCH_COMMANDS:
        return f"git {command} is not a reviewed scratch-repository operation"
    problem = _git_operand_problem(command, rest, directory)
    if problem:
        return problem
    if command == "config":
        problem = _git_config_problem(rest)
    elif command == "clone":
        problem = _git_clone_problem(rest, directory)
    return problem or _scratch_repository_problem(directory)


def _git_execution_problem(command: str, rest: list[str]) -> str | None:
    """No signing, signature verification, editor or interactive selection: each starts a program git
    chooses (gpg/ssh-keygen/X.509 signer, the editor, the interactive filter). Commits and annotated tags
    must carry their message on the command line or in a file."""
    specific = _GIT_EXECUTION_OPTIONS.get(command, {})
    stash_action = rest[0] if command == "stash" and rest and not rest[0].startswith("-") else "push"
    if command == "stash" and stash_action not in {"push", "save"}:
        specific = {}  # show -p prints a patch; list/show/pop/apply/drop select nothing interactively
    previous = ""
    for argument in rest:
        if argument == "--":
            break
        if (previous in {"--format", "--pretty"} or argument.startswith(("--format=", "--pretty="))) and (
                "%G" in argument or "%(signature" in argument):
            return f"git {command}: a signature placeholder verifies a signature"
        previous = argument
        if argument.startswith("--"):
            name = argument.split("=", 1)[0].lower()
            for option, behaviour in (*_GIT_EXECUTION_LONG_OPTIONS.items(), *(
                    (key, value) for key, value in specific.items() if key.startswith("--"))):
                if name == option or (len(name) >= 4 and option.startswith(name) and not name.startswith("--no-")):
                    return f"git {command} {option} {behaviour}"
    grammar = _GIT_OPTION_GRAMMAR.get(command)
    if grammar is None:
        return None
    if command == "stash":
        if stash_action not in {"push", "save"}:
            return None
        arguments = rest[1:] if rest and rest[0] in {"push", "save"} else rest
    else:
        arguments = rest
    flags, valued = grammar
    seen, index = set(), 0
    while index < len(arguments):
        argument = arguments[index]
        index += 1
        if argument == "--":
            break
        if argument == "-" or not argument.startswith("-"):
            continue  # an operand (pathspec, name, revision, stash message)
        if argument.startswith("--"):
            name, has_value, _ = argument.partition("=")
            if name in specific:
                return f"git {command} {name} {specific[name]}"
            if name in valued:
                index += 0 if has_value else 1
            elif has_value or name not in flags:
                return f"git {command} option {name} is not reviewed"
            seen.add(name)
            continue
        for position, letter in enumerate(argument[1:], start=1):  # a short-option cluster such as -qm
            option = "-" + letter
            if option in specific:
                return f"git {command} {option} {specific[option]}"
            seen.add(option)
            if option in valued:
                index += 0 if position + 1 < len(argument) else 1  # -mvalue, or -m value
                break
            if option not in flags:
                return f"git {command} option {option} is not reviewed"
    if command == "commit" and not seen & _GIT_MESSAGE_OPTIONS and not {"--amend", "--no-edit"} <= seen:
        return "git commit without -m/-F/-C (or --amend --no-edit) opens an editor"
    if command == "tag" and seen & {"-a", "--annotate"} and not seen & {"-m", "--message", "-F", "--file"}:
        return "git tag -a without -m/-F opens an editor"
    return None


def _git_operand_problem(command: str, rest: list[str], directory: str) -> str | None:
    """Filesystem operands by subcommand grammar; any other operand naming an existing path is contained too."""
    paths: list[str] = []

    def operands(arguments, flags, valued=()):
        found, index = [], 0
        while index < len(arguments):
            argument = arguments[index]
            if argument in valued:
                index += 2
                continue
            if argument.startswith("-"):
                if argument not in flags and not any(argument.startswith(prefix) for prefix in flags if
                                                     prefix.endswith("=")):
                    raise IsolationError(f"git {command} option {argument.split('=')[0]} is not reviewed")
            else:
                found.append(argument)
            index += 1
        return found

    try:
        if command == "init":
            paths = operands(rest, {"-q", "--quiet", "--bare", "--initial-branch="})
            if len(paths) > 1:
                return "git init takes at most one directory"
        elif command == "bundle":
            action = rest[0] if rest else ""
            if action not in {"create", "verify", "list-heads"}:
                return "git bundle is limited to create, verify and list-heads"
            tail = rest[1:]
            leading = 0
            while leading < len(tail) and tail[leading] in {"-q", "--quiet", "--no-progress"}:
                leading += 1
            if leading >= len(tail) or tail[leading].startswith("-"):
                return f"git bundle {action} needs its bundle file first"
            paths = [tail[leading]]
        elif command == "worktree":
            action = rest[0] if rest else ""
            tail = rest[1:]
            if action == "add":
                found = operands(tail, {"--detach", "-f", "--force", "--no-checkout", "--checkout", "--lock", "-q",
                                        "--quiet"}, valued=("-b", "-B", "--reason"))
                if not 1 <= len(found) <= 2:
                    return "git worktree add takes <path> [<commit>]"
                paths = [found[0]]
            elif action == "remove":
                found = operands(tail, {"-f", "--force"})
                if len(found) != 1:
                    return "git worktree remove takes exactly one <path>"
                paths = found
            elif action == "list":
                if operands(tail, {"--porcelain", "-z", "-v", "--verbose"}):
                    return "git worktree list takes no operand"
            elif action == "prune":
                if operands(tail, {"-n", "--dry-run", "-v", "--verbose"}, valued=("--expire",)):
                    return "git worktree prune takes no operand"
            else:
                return "git worktree is limited to add, list, remove and prune"
        elif command == "apply":
            paths = operands(rest, {"--binary", "--check", "--cached", "--index", "-R", "--reverse", "--3way", "-3",
                                    "--stat", "--numstat", "--summary", "--allow-empty", "--recount", "-v",
                                    "--verbose", "--apply", "--whitespace=", "-p="})
        elif command == "hash-object":
            paths = operands(rest, {"-w", "--stdin", "--no-filters", "--literally"}, valued=("-t",))
    except IsolationError as exc:
        return str(exc)
    for operand in paths:
        problem = _disposable_path_problem(operand, directory)
        if problem:
            return f"git {command} operand: {problem}"
    for argument in rest:  # anything else that names an existing path (pathspecs, files) stays contained
        if argument.startswith("-") or argument in paths:
            continue
        candidate = argument if _is_absolute_argument(argument) else os.path.join(directory, argument)
        if os.path.lexists(candidate):
            problem = _disposable_path_problem(candidate)
            if problem:
                return f"git {command} operand: {problem}"
    return None


def _git_configuration_entries(path: Path) -> list[tuple[str, str]]:
    """(section[.subsection].key, value) pairs of a git configuration file, lowercased keys."""
    entries, section = [], ""
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = line.strip()
        if not stripped or stripped[0] in "#;":
            continue
        header = re.match(r'^\[\s*([A-Za-z0-9.-]+)(?:\s+"((?:[^"\\]|\\.)*)")?\s*\]', stripped)
        if header:
            section = header.group(1).lower() + (f".{header.group(2).lower()}" if header.group(2) is not None else "")
            stripped = stripped[header.end():].strip()
            if not stripped:
                continue
        entry = re.match(r"^([A-Za-z][A-Za-z0-9-]*)\s*(?:=\s*(.*))?$", stripped)
        if not entry:
            entries.append((f"{section}.<unparsed>", stripped))
            continue
        value = "true" if entry.group(2) is None else entry.group(2).strip().strip('"')  # a bare key is true
        entries.append((f"{section}.{entry.group(1).lower()}", value))
    return entries


def _scratch_repository_problem(directory: str) -> str | None:
    """The scratch repository's local configuration and hooks must not run anything or reach out."""
    base = _norm(os.path.realpath(_TRUSTED_TEMP_BASE))
    current = Path(os.path.realpath(directory))
    gitdir = None
    while _within(_norm(current), base):
        marker = current / ".git"
        if marker.is_dir():
            gitdir = marker
        elif marker.is_file():
            pointer = marker.read_text(encoding="utf-8", errors="replace").strip()
            if not pointer.startswith("gitdir:"):
                return f"unrecognized .git file in {current}"
            target = Path(pointer[len("gitdir:"):].strip())
            gitdir = target if target.is_absolute() else current / target
        elif (current / "HEAD").is_file() and (current / "objects").is_dir() and (current / "config").is_file():
            gitdir = current  # a bare repository
        if gitdir is not None or current.parent == current:
            break
        current = current.parent
    if gitdir is None:
        return None  # not inside a repository yet (for example before git init)
    gitdir = Path(os.path.realpath(gitdir))
    common = gitdir
    if (gitdir / "commondir").is_file():
        pointer = Path((gitdir / "commondir").read_text(encoding="utf-8", errors="replace").strip())
        common = Path(os.path.realpath(pointer if pointer.is_absolute() else gitdir / pointer))
    for location in (gitdir, common):
        if not _within(_norm(location), base):
            return f"the repository's git directory is outside the trusted temporary base: {location}"
    for configuration in (common / "config", gitdir / "config.worktree"):
        if configuration.is_file():
            for key, value in _git_configuration_entries(configuration):
                if (key == "core.fsmonitor" or key in _GIT_SIGNING_CONFIGURATION) and value.lower() in _GIT_FALSE:
                    continue
                if key.endswith(".<unparsed>") or key in _GIT_SIGNING_CONFIGURATION or \
                        _GIT_RISKY_CONFIGURATION.match(key):
                    return f"the scratch repository's local configuration sets {key}"
    hooks = common / "hooks"
    if hooks.is_dir():
        active = sorted(entry.name for entry in hooks.iterdir() if not entry.name.endswith(".sample"))
        if active:
            return f"the scratch repository has active git hooks {active}"
    return None


def _isolate_git_configuration(env) -> str | None:
    """Give a git child no system or global configuration.

    The inherited environment carries GIT_CONFIG_NOSYSTEM=1 and GIT_CONFIG_GLOBAL=<null device> from
    initialization. An explicit mapping without them (product code strips every GIT_* variable before
    running git) is completed with them: it is the very mapping the child is created with. A conflicting
    value, a mapping that cannot be completed, or an inherited environment that lost them is refused.
    """
    target = os.environ if env is None else env
    for name, value in _GIT_ISOLATION.items():
        current = _env_lookup(target, name)
        if current is None:
            if env is None:
                return f"the test environment lost {name}"
            try:
                env[name] = value
            except TypeError:
                return f"the child environment lacks {name} and cannot be completed"
        elif str(current).lower() != value.lower():
            return f"git environment variable {name} has an unreviewed value"
    return None


def _shell_problem(argv: list[str]) -> str | None:
    """The only reviewed shell command: cmd /c mklink /J <temporary path> <temporary path>."""
    if len(argv) != 6 or [part.lower() for part in argv[1:4]] != ["/c", "mklink", "/j"]:
        return "the only reviewed shell command is cmd /c mklink /J <temporary path> <temporary path>"
    for part in argv[4:]:
        if any(character in part for character in '&|<>^%!()"\n\r') or not _is_absolute_argument(part):
            return "mklink operands must be plain absolute temporary paths"
        problem = _disposable_path_problem(part)
        if problem:
            return f"mklink operand: {problem}"
    return None


def _git_config_problem(rest: list[str]) -> str | None:
    flags = [argument for argument in rest if argument.startswith("-")]
    values = [argument for argument in rest if not argument.startswith("-")]
    for flag in flags:
        if flag not in {"--get", "--worktree", "--local", "--unset", "--bool"}:
            return f"git config {flag} is not allowed"
    if not values:
        return "git config without a key"
    key = values[0].lower()
    if "--get" in flags:
        return None  # reading a value executes nothing
    if key == "commit.gpgsign" and "--unset" not in flags and (
            len(values) != 2 or values[1].lower() not in _GIT_FALSE - {""}):
        return "git config may set commit.gpgsign only to false"
    if key in _GIT_CONFIG_WRITABLE or key.startswith("some."):  # "some.*": synthetic keys of the worktree tests
        return None
    return f"git config may not set {key}"


def _git_clone_problem(rest: list[str], directory: str | None = None) -> str | None:
    options = [argument for argument in rest if argument.startswith("-")]
    positional = [argument for argument in rest if not argument.startswith("-")]
    if any(option not in {"-q", "--quiet"} for option in options):
        return "git clone options are limited to -q"
    if len(positional) != 2:
        return "git clone needs exactly a local source and a destination"
    source, destination = positional
    if re.match(r"^[^\\/]+:", source) and not re.match(r"^[A-Za-z]:[\\/]", source):
        return "git clone source looks remote"
    for path in (source, destination):
        if not _is_absolute_argument(path):
            return "git clone paths must be absolute"
        problem = _disposable_path_problem(path, directory)
        if problem:
            return f"git clone: {problem}"
    if not os.path.isfile(source):
        return "git clone source must be an existing local bundle file"
    return None


def _icacls_problem(argv: list[str]) -> str | None:
    args = argv[1:]
    if len(args) != 4 or args[1].lower() != "/inheritance:r" or args[2].lower() != "/grant:r":
        return "icacls is limited to <path> /inheritance:r /grant:r <current user>:<rights>"
    if not _is_absolute_argument(args[0]):
        return "icacls path must be absolute"
    problem = _disposable_path_problem(args[0])
    if problem:
        return f"icacls path: {problem}"
    principal, _, rights = args[3].rpartition(":")
    import getpass

    user = getpass.getuser().lower()
    domain = (os.environ.get("USERDOMAIN") or "").lower()
    if principal.lower() not in {user, f"{domain}\\{user}"}:
        return "icacls may grant rights only to the current user"
    if not re.fullmatch(r"(\((?:OI|CI|IO|NP|I)\))*\((?:F|M|RX|R|W|D)(?:,[A-Z]+)*\)", rights):
        return "icacls rights are not a reviewed simple grant"
    return None


def _parent_pid(pid: int) -> int | None:
    """Parent process id of a process object (read-only; None if it cannot be opened).

    OpenProcess + NtQueryInformationProcess also answer for a child that has just exited while its
    creator still holds its handle, the moment a tree-kill races with a normal exit; Windows does not
    reuse that process id while the handle is open, so the answer still identifies the same process.
    """
    if not _WINDOWS:
        return None
    import ctypes
    from ctypes import wintypes

    class PROCESS_BASIC_INFORMATION(ctypes.Structure):
        _fields_ = [("ExitStatus", ctypes.c_long), ("PebBaseAddress", ctypes.c_void_p),
                    ("AffinityMask", ctypes.c_size_t), ("BasePriority", ctypes.c_long),
                    ("UniqueProcessId", ctypes.c_size_t), ("InheritedFromUniqueProcessId", ctypes.c_size_t)]

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    ntdll = ctypes.WinDLL("ntdll")
    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    ntdll.NtQueryInformationProcess.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.ULONG,
                                                ctypes.POINTER(wintypes.ULONG)]
    ntdll.NtQueryInformationProcess.restype = ctypes.c_long
    if not 0 < pid <= 0xFFFFFFFF:
        return None
    handle = kernel32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
    if not handle:
        return None
    try:
        info = PROCESS_BASIC_INFORMATION()
        if ntdll.NtQueryInformationProcess(handle, 0, ctypes.byref(info), ctypes.sizeof(info), None) != 0:
            return None
        if info.UniqueProcessId != pid:
            return None
        return int(info.InheritedFromUniqueProcessId)
    finally:
        kernel32.CloseHandle(handle)


def _taskkill_problem(argv: list[str]) -> str | None:
    args = argv[1:]
    if len(args) != 4 or args[0].upper() != "/PID" or not args[1].isdigit() or \
            sorted(argument.upper() for argument in args[2:]) != ["/F", "/T"]:
        return "taskkill is limited to /PID <n> /T /F"
    pid = int(args[1])
    if _parent_pid(pid) != os.getpid():
        return f"taskkill target {pid} is not a direct child of this test process"
    return None


def _child_database_names(environment, *, integration_opt_in_test: bool) -> list[str]:
    """Names (never values) of database-target, test-database and libpq variables in a child environment."""
    forbidden = {name.upper() for name in _OPERATIONAL_DATABASE_ENVIRONMENT + _TEST_DATABASE_ENVIRONMENT}
    found = []
    for key in environment:
        name = os.fsdecode(key) if isinstance(key, bytes) else str(key)
        compared = name.upper() if _WINDOWS else name
        if compared in forbidden or compared.startswith("PG"):
            found.append(name)
    if integration_opt_in_test:  # a separately authorized disposable integration database only
        allowed = {"VRES_TEST_DATABASE_URL", "VRES_ALLOW_TEST_DB"}
        test_url = _env_lookup(environment, "VRES_TEST_DATABASE_URL")
        if test_url and _env_lookup(environment, "VRES_ALLOW_TEST_DB") == "1" \
                and _env_lookup(environment, "VRES_DATABASE_URL") == test_url:
            allowed.add("VRES_DATABASE_URL")
        found = [name for name in found if (name.upper() if _WINDOWS else name) not in allowed]
    return sorted(found)


def _check_child(event: str, args) -> None:
    if event in _FORBIDDEN_LAUNCH_EVENTS:
        _refuse(f"{event} is refused in tests: a shell or exec command string cannot be judged before it runs")
    index = _CHILD_ENV_INDEX[event]
    env = args[index] if index is not None and index < len(args) else None
    environment = os.environ if env is None else env
    try:
        _require_disposable(_env_lookup(environment, _DATA_DIR_ENV))
    except IsolationError as exc:
        _refuse(f"{event} would start a child without a safe {_DATA_DIR_ENV}: {exc}")
    names = _child_database_names(
        environment, integration_opt_in_test=_INTEGRATION_OPT_IN and _ACTIVE_TEST["integration"])
    if names:
        _refuse(f"{event} would start a child carrying database variable(s) {names} (values not recorded)")
    try:
        program, argv, line, cwd = _child_command(event, args)
    except IsolationError as exc:
        _refuse(f"{event}: {exc}")
    normalized = os.path.normcase(line.replace("/", "\\") if _WINDOWS else line)
    if any(root in normalized for root in _PROTECTED) or _INSTALLED_PLUGIN in normalized:
        _refuse(f"{event} would start a child whose command line names live Vres data or the installed plugin")
    kind = _classify_child(program, line)
    if kind == "provider":
        _refuse(f"{event} would start a Claude/Codex child")
    site = _ACTIVE_TEST["file"]
    if kind not in _REVIEWED_CHILD_SITES.get(site, frozenset()):
        _refuse(f"{event} would start an unreviewed {kind} child from {site or 'outside any test'}")
    problem = _executable_problem(kind, program) if kind in _APPROVED_EXECUTABLES else None
    if problem is None and kind == "git":
        problem = _isolate_git_configuration(env) or _git_problem(argv, cwd, environment)
    elif problem is None and kind == "shell":
        problem = _shell_problem(argv)
    elif problem is None and kind == "icacls":
        problem = _icacls_problem(argv)
    elif problem is None and kind == "taskkill":
        problem = _taskkill_problem(argv)
    if problem:
        _refuse(f"{event} refused a {kind} child: {problem}")


_PATH_EVENTS = {
    "open": (0,), "os.mkdir": (0,), "os.rmdir": (0,), "os.remove": (0,), "os.rename": (0, 1), "os.listdir": (0,),
    "os.scandir": (0,), "os.chmod": (0,), "os.utime": (0,), "os.truncate": (0,), "os.symlink": (0, 1),
    "os.link": (0, 1), "os.chdir": (0,), "shutil.copyfile": (0, 1), "shutil.copytree": (0, 1),
    "shutil.rmtree": (0,), "shutil.move": (0, 1), "shutil.chown": (0,), "_winapi.CreateJunction": (0, 1),
}
_CHILD_ENV_INDEX = {"subprocess.Popen": 3}
_HOOK_STATE = threading.local()
_INTEGRATION_OPT_IN = (_env_lookup(os.environ, "VRES_ALLOW_TEST_DB") == "1"
                       and bool(_env_lookup(os.environ, "VRES_TEST_DATABASE_URL")))


def _allowed(event: str, args) -> bool:
    """Opt-in integration runs keep the real guard, which may read (only read) the live approval registry."""
    if not _INTEGRATION_OPT_IN or event != "open" or len(args) < 2 or not isinstance(args[1], str):
        return False
    return _norm(args[0]) in _LIVE_REGISTRY_FILES and set(args[1]) <= set("rb")


def _live_app_data_audit(event, args):
    paths, env_index = _PATH_EVENTS.get(event), _CHILD_ENV_INDEX.get(event, -1)
    if (paths is None and env_index == -1 and event not in _FORBIDDEN_LAUNCH_EVENTS) \
            or getattr(_HOOK_STATE, "active", False):
        return
    _HOOK_STATE.active = True
    try:
        if paths is None:
            _check_child(event, args)
            return
        for index in paths:
            value = args[index] if index < len(args) else None
            if isinstance(value, (str, bytes, os.PathLike)) and _is_protected(value) and not _allowed(event, args):
                _refuse(f"{event}: {os.fsdecode(os.fspath(value))}")
    finally:
        _HOOK_STATE.active = False


# ---- Initialization, in the required order -------------------------------------------------------
_PRELOADED_VRES_MODULES = tuple(sorted(m for m in sys.modules if m == "vres_os" or m.startswith("vres_os.")))
if _PRELOADED_VRES_MODULES:
    raise pytest.UsageError(
        f"vres_os was imported before the test isolation was established: {_PRELOADED_VRES_MODULES}")
try:
    _TRUSTED_TEMP_BASE, _SESSION_ROOT = _establish_session_root(os.environ, adopt_tempdir=True)
except IsolationError as exc:
    raise pytest.UsageError(f"Refusing to run tests without a trusted disposable temporary base: {exc}") from None
os.environ[_DATA_DIR_ENV] = str(_SESSION_ROOT)
_REMOVED_ENVIRONMENT = tuple(name for name in _OPERATIONAL_DATABASE_ENVIRONMENT if os.environ.pop(name, None))
if not _INTEGRATION_OPT_IN:
    _REMOVED_ENVIRONMENT += tuple(name for name in _TEST_DATABASE_ENVIRONMENT if os.environ.pop(name, None))
    _REMOVED_ENVIRONMENT += tuple(name for name in list(os.environ)
                                  if name.upper().startswith("PG") and os.environ.pop(name, None) is not None)
# Git variables that name programs (GIT_ASKPASS, GIT_EDITOR, GIT_SSH_COMMAND, ...) or redirect configuration
# or repositories are removed (the isolation values below then replace GIT_EDITOR and GIT_PAGER); the git
# policy refuses them if a test reintroduces one.
_REMOVED_ENVIRONMENT += tuple(name for name in list(os.environ)
                              if name.upper().startswith("GIT_") and (name.upper() not in _GIT_ENVIRONMENT
                                                                      or name.upper() in _GIT_ISOLATION)
                              and os.environ.pop(name, None) is not None)
# Git reads no system or global configuration and starts no editor or pager in this session. On Windows
# HOME and XDG_CONFIG_HOME also
# point at an empty disposable directory (Python itself ignores HOME there), so even git started by a
# child that strips GIT_* variables finds no user configuration; the system configuration of such a
# grandchild remains outside this hook's reach.
os.environ.update(_GIT_ISOLATION)
_GIT_HOME = None
if _WINDOWS:
    _GIT_HOME = _SESSION_ROOT.parent / "home"
    (_GIT_HOME / ".config").mkdir(parents=True)
    _require_disposable(_GIT_HOME)
    os.environ["HOME"] = str(_GIT_HOME)
    os.environ["XDG_CONFIG_HOME"] = str(_GIT_HOME / ".config")
platformdirs.user_data_dir = _fenced(_REAL_USER_DATA_DIR, "user_data_dir")
platformdirs.user_data_path = _fenced(_REAL_USER_DATA_PATH, "user_data_path")
sys.addaudithook(_live_app_data_audit)
_INIT_ORDER.append("enable-isolation")


def _site(path) -> str | None:
    try:
        return Path(path).resolve().relative_to(_REPOSITORY).as_posix()
    except (OSError, ValueError):
        return None


@pytest.hookimpl(wrapper=True)
def pytest_runtest_protocol(item, nextitem):
    """Attribute child processes started during a test's setup, call and teardown to its test file."""
    _ACTIVE_TEST.update(file=_site(item.path), integration="integration" in Path(item.path).parts)
    try:
        return (yield)
    finally:
        _ACTIVE_TEST.update(file=None, integration=False)


class _Fence:
    """What tests may inspect about the isolation; it offers no way to reach the live data."""

    IsolationError = IsolationError
    RefusedError = LiveAppDataAccessRefused
    preloaded_vres_modules = _PRELOADED_VRES_MODULES
    session_root = _SESSION_ROOT
    trusted_temp_base = _TRUSTED_TEMP_BASE
    init_order = tuple(_INIT_ORDER)
    removed_environment = _REMOVED_ENVIRONMENT
    reviewed_child_sites = dict(_REVIEWED_CHILD_SITES)
    approved_executables = dict(_APPROVED_EXECUTABLES)
    live_root = _REAL_USER_DATA_DIR(_APP_NAME, appauthor=False, roaming=False)  # a string; never accessed
    is_protected = staticmethod(_is_protected)
    require_disposable = staticmethod(_require_disposable)
    check_fence_intact = staticmethod(_check_fence_intact)
    assess_temp_base = staticmethod(_assess_temp_base)
    establish_session_root = staticmethod(_establish_session_root)
    windows_volume = staticmethod(_windows_volume)
    classify_child = staticmethod(_classify_child)
    child_database_names = staticmethod(_child_database_names)
    check_child = staticmethod(_check_child)  # evaluates a would-be launch; starts nothing
    split_command_line = staticmethod(_split_command_line)
    git_isolation = dict(_GIT_ISOLATION)
    git_home = _GIT_HOME
    forbidden_launch_events = _FORBIDDEN_LAUNCH_EVENTS
    scratch_repository_problem = staticmethod(_scratch_repository_problem)
    parent_pid = staticmethod(_parent_pid)
    integration_opt_in = _INTEGRATION_OPT_IN

    @staticmethod
    def active_site():
        return _ACTIVE_TEST["file"]

    @staticmethod
    @contextlib.contextmanager
    def as_test_site(site):
        """Attribute children started in the block to another (for example an unreviewed) test file."""
        saved = dict(_ACTIVE_TEST)
        _ACTIVE_TEST["file"] = site
        try:
            yield
        finally:
            _ACTIVE_TEST.update(saved)

    @staticmethod
    @contextlib.contextmanager
    def protect(root):
        """Treat a disposable decoy directory as protected live data for the duration of the block."""
        forms = {_norm(root), _norm(os.path.realpath(root))}
        _PROTECTED.extend(forms)
        try:
            yield
        finally:
            for form in forms:
                _PROTECTED.remove(form)

    @staticmethod
    @contextlib.contextmanager
    def refused():
        """The block must be refused at least once; yields the refusal records, then clears them."""
        start = len(_REFUSALS)
        captured: list[str] = []
        try:
            yield captured
        except LiveAppDataAccessRefused:
            pass
        captured.extend(_REFUSALS[start:])
        assert captured, "expected the live application-data fence to refuse this"
        del _REFUSALS[start:]


@pytest.fixture(autouse=True)
def _disposable_app_data(monkeypatch, tmp_path_factory):
    """Every test (unit and integration) gets its own empty, validated application-data root."""
    root = tmp_path_factory.mktemp("vres-app-data") / _APP_NAME
    root.mkdir()
    _require_disposable(root)
    monkeypatch.setenv(_DATA_DIR_ENV, str(root))
    _check_fence_intact()
    start = len(_REFUSALS)
    yield root
    refused = _REFUSALS[start:]
    del _REFUSALS[start:]
    _UNEXPECTED.extend(refused)
    _check_fence_intact()
    assert not refused, f"{_LIVE_MESSAGE}: {refused}"


@pytest.fixture
def live_app_data_fence():
    return _Fence


def pytest_sessionfinish(session, exitstatus):
    stray = _REFUSALS + _UNEXPECTED
    if stray and session.exitstatus == 0:
        session.exitstatus = 1


def pytest_terminal_summary(terminalreporter):
    stray = _REFUSALS + _UNEXPECTED
    terminalreporter.write_line(
        f"LIVE APP-DATA FENCE: unexpected refusals={len(stray)} protected={_PROTECTED} "
        f"trusted_temp_base={_TRUSTED_TEMP_BASE} session_root={_SESSION_ROOT} init_order={_INIT_ORDER} "
        f"removed_env={list(_REMOVED_ENVIRONMENT)} integration_opt_in={_INTEGRATION_OPT_IN}")
    for record in stray:
        terminalreporter.write_line(f"  REFUSED: {record}")


def pytest_unconfigure(config):
    shutil.rmtree(_SESSION_ROOT.parent, ignore_errors=True)


_TRIPWIRE_MESSAGE = "A unit test attempted a real PostgreSQL connection"


class _ConnectionTripwire:
    """Default-deny stand-in for every in-process PostgreSQL connection route.

    Each attempt is recorded before it is refused, so an attempt stays visible even when
    the code under test swallows the AssertionError (setup converts any exception into a
    failed setup); the owning fixture fails the test at teardown unless the test itself
    inspected and cleared the record through the `connection_tripwire` fixture.
    """

    def __init__(self):
        self.attempts: list[str] = []

    def refuse(self, route: str):
        def refuse(*_args, **_kwargs):
            self.attempts.append(route)  # never the conninfo: it can carry a password
            raise AssertionError(_TRIPWIRE_MESSAGE)

        return refuse


class _RefusingDriver:
    """psycopg for everything except opening a connection."""

    def __init__(self, tripwire: _ConnectionTripwire):
        self.connect = tripwire.refuse("vres-driver")

    def __getattr__(self, name):
        import psycopg

        return getattr(psycopg, name)


def _install_psycopg_tripwire(monkeypatch, tripwire: _ConnectionTripwire) -> None:
    """Refuse direct psycopg use as well as the Vres seams.

    psycopg.generators.connect is the call-time choke point of Connection.connect,
    AsyncConnection.connect, psycopg.connect and pools built on them; the public entry
    points are replaced too, so older layouts and subclasses are refused before it.
    """
    try:
        import psycopg
        import psycopg.generators
    except ImportError:  # pragma: no cover - no driver, no connection route
        return
    monkeypatch.setattr(psycopg.generators, "connect", tripwire.refuse("psycopg.generators.connect"))
    monkeypatch.setattr(psycopg, "connect", tripwire.refuse("psycopg.connect"))
    monkeypatch.setattr(psycopg.Connection, "connect", tripwire.refuse("psycopg.Connection.connect"))
    monkeypatch.setattr(psycopg.AsyncConnection, "connect", tripwire.refuse("psycopg.AsyncConnection.connect"))


@pytest.fixture(autouse=True)
def _offline_guarded_installation(request, monkeypatch, tmp_path_factory):
    """Unit tests run as a guarded personal-release installation that cannot reach PostgreSQL.

    The contact guard is active on every platform with a private, empty approval registry,
    so nothing is approved unless a test asks for it through `approve_database_target`, and
    the real LocalAppData registry is never read. Every in-process connection route (the
    Vres driver seams and psycopg itself) is a recording tripwire, and a test that attempted
    a connection fails at teardown. Unit tests inherit no test-database or libpq environment.
    Integration tests are excluded only in an explicit opt-in run (VRES_ALLOW_TEST_DB=1 with a
    VRES_TEST_DATABASE_URL): they then use the real guard and only a disposable database.
    Subprocesses are not covered by this fixture.
    """
    integration = "integration" in request.node.path.parts
    if integration and _INTEGRATION_OPT_IN:
        yield None
        return
    if not integration:
        for name in _TEST_DATABASE_ENVIRONMENT:
            monkeypatch.delenv(name, raising=False)
    for name in [name for name in os.environ if name.upper().startswith("PG")]:
        monkeypatch.delenv(name)
    from vres_os import bootstrap, database_boundary, database_targets, db

    local_app_data = tmp_path_factory.mktemp("LocalAppData")
    monkeypatch.setattr(database_targets, "_guarded_platform", lambda: True)
    monkeypatch.setattr(database_targets, "_known_local_app_data", lambda: str(local_app_data))
    tripwire = _ConnectionTripwire()
    _install_psycopg_tripwire(monkeypatch, tripwire)
    driver = _RefusingDriver(tripwire)
    for module in (db, bootstrap, database_boundary):
        monkeypatch.setattr(module, "_driver", lambda: driver)
    yield tripwire
    assert tripwire.attempts == [], f"{_TRIPWIRE_MESSAGE}: {tripwire.attempts}"


@pytest.fixture
def connection_tripwire(_offline_guarded_installation):
    """The active tripwire, for tests that deliberately provoke and then clear an attempt."""
    return _offline_guarded_installation


@pytest.fixture(autouse=True)
def _feature_profile_outside_personal_release(request, monkeypatch):
    """Unit tests are platform-independent: they run outside the personal feature profile.

    On Windows every real process is in the personal profile, which would fence the
    features many unit tests exercise. Tests of the fence request `personal_profile`.
    This is test-only injection of the platform decision, never an environment switch.
    Integration tests are left untouched.
    """
    if "integration" in request.node.path.parts:
        return
    from vres_os import personal_profile

    monkeypatch.setattr(personal_profile, "_personal_platform", lambda: False)


@pytest.fixture
def personal_profile(_feature_profile_outside_personal_release, monkeypatch):
    """Run the test inside the personal feature profile, as every Windows process is."""
    from vres_os import personal_profile as profile

    monkeypatch.setattr(profile, "_personal_platform", lambda: True)
    return profile


@pytest.fixture
def approve_database_target():
    """Explicitly approve exact targets in the test's private registry; returns the registry path."""
    from vres_os import database_targets

    def approve(*targets: tuple[str, int, str]) -> Path:
        root = database_targets.personal_release_root()
        root.mkdir(parents=True, exist_ok=True)
        path = root / database_targets.REGISTRY_NAME
        approved = [
            {"host": h, "port": p, "dbname": d, "approved_at": "2026-10-19T00:00:00+00:00", "approved_by": "test"}
            for h, p, d in targets
        ]
        path.write_text(json.dumps({"version": 1, "approved": approved, "held": []}), encoding="utf-8")
        return path

    return approve
