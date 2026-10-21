"""Routine tests can neither resolve nor touch the live Vres application data (%LOCALAPPDATA%\\VresOS).

The isolation lives in tests/conftest.py. Everything here works on disposable directories or on a decoy
root registered as protected; nothing reads, lists or writes the real live directory.
"""
from __future__ import annotations

import json
import os
import re
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
THIS_SITE = "tests/test_live_app_data_isolation.py"
SYNTHETIC_DSN = "host=disposable.invalid port=1 dbname=synthetic user=synthetic password=synthetic-secret-value"


def _norm(path) -> str:
    return os.path.normcase(os.path.abspath(os.fspath(path)))


def _within(path, root) -> bool:
    path, root = _norm(path), _norm(root)
    return path == root or path.startswith(root + os.sep)


def test_isolation_is_established_before_any_vres_module_is_imported(live_app_data_fence):
    # The conftest block runs before collection imports any test module (and so any vres_os module).
    assert live_app_data_fence.preloaded_vres_modules == ()
    assert live_app_data_fence.session_root.is_dir()
    assert not live_app_data_fence.is_protected(live_app_data_fence.session_root)


def test_live_root_is_protected_without_touching_it(live_app_data_fence):
    # Pure string computation: the live directory itself is never accessed.
    live = live_app_data_fence.live_root
    assert live_app_data_fence.is_protected(live)
    assert live_app_data_fence.is_protected(os.path.join(live, "logs", "hook-errors.log"))
    if sys.platform == "win32":  # the Windows shell/environment spelling, any case, either separator
        shell = os.path.join(os.environ["LOCALAPPDATA"], "VresOS")
        assert live_app_data_fence.is_protected(shell)
        assert live_app_data_fence.is_protected(os.path.join(shell.upper(), "config.json"))
        assert live_app_data_fence.is_protected(shell.replace("\\", "/") + "/database-targets.json")


def test_normal_environment_resolves_a_disposable_root(live_app_data_fence, tmp_path_factory):
    from vres_os import paths

    root = paths.data_dir()
    assert _norm(root) == _norm(os.environ["VRES_DATA_DIR"])
    assert _within(root, tmp_path_factory.getbasetemp())
    assert not live_app_data_fence.is_protected(root)
    assert live_app_data_fence.require_disposable(root) == root
    assert list(root.iterdir()) == []  # fresh per test: nothing copied in, no live config or credentials


def test_each_test_gets_its_own_root(live_app_data_fence):
    from vres_os import paths

    marker = paths.data_dir() / "marker"
    assert not marker.exists()
    marker.write_text("x", encoding="utf-8")


def test_each_test_gets_its_own_root_again(live_app_data_fence):
    from vres_os import paths

    assert not (paths.data_dir() / "marker").exists()


def test_direct_fallback_to_the_live_default_is_refused(live_app_data_fence, monkeypatch):
    from vres_os import paths

    monkeypatch.delenv("VRES_DATA_DIR")
    with live_app_data_fence.refused():
        paths.data_dir()
    with live_app_data_fence.refused():
        paths.logs_dir()


def test_platformdirs_fence_is_what_paths_resolves_through(live_app_data_fence):
    import platformdirs

    from vres_os import paths

    assert getattr(platformdirs.user_data_dir, "__vres_live_fence__", False) is True
    assert paths.user_data_dir is platformdirs.user_data_dir
    # Other applications still resolve normally; only the Vres application is fenced.
    assert "SomeOtherApp" in platformdirs.user_data_dir("SomeOtherApp", appauthor=False, roaming=False)


def test_a_resolver_that_re_enables_the_live_path_is_detected(live_app_data_fence, monkeypatch):
    import platformdirs

    from vres_os import paths

    def live_resolver(*_args, **_kwargs):  # what restoring the real resolver would return; never used for I/O
        return live_app_data_fence.live_root

    for owner in (paths, platformdirs):
        with monkeypatch.context() as patch:
            patch.setattr(owner, "user_data_dir", live_resolver)
            with pytest.raises(AssertionError, match="re-enabled"):
                live_app_data_fence.check_fence_intact()
    live_app_data_fence.check_fence_intact()  # restored
    # A test-local resolver that returns a disposable path is legitimate.
    with monkeypatch.context() as patch:
        patch.setattr(paths, "user_data_dir", lambda *_a, **_kw: os.environ["VRES_DATA_DIR"])
        live_app_data_fence.check_fence_intact()


def test_config_store_cannot_load_the_live_configuration(live_app_data_fence, monkeypatch, tmp_path):
    from vres_os.config import ConfigStore

    store = ConfigStore()
    assert _within(store.path, os.environ["VRES_DATA_DIR"])
    assert store.load().database.host == "localhost"  # defaults, not any live configuration

    monkeypatch.delenv("VRES_DATA_DIR")
    with live_app_data_fence.refused():
        ConfigStore()

    decoy = tmp_path / "decoy-live" / "VresOS"
    decoy.mkdir(parents=True)
    (decoy / "config.json").write_text(json.dumps({"configured": True}), encoding="utf-8")
    with live_app_data_fence.protect(decoy):
        with live_app_data_fence.refused():
            ConfigStore(decoy / "config.json").load()


def test_hook_error_log_is_written_only_under_the_disposable_root(live_app_data_fence, tmp_path):
    from vres_os import hooks, paths

    hooks._log_hook_error("IsolationProbe", RuntimeError("synthetic"))
    log = paths.logs_dir() / "hook-errors.log"
    assert log.read_text(encoding="utf-8").count("IsolationProbe: RuntimeError: synthetic") == 1
    assert _within(log, os.environ["VRES_DATA_DIR"])

    decoy = tmp_path / "decoy-live" / "VresOS"
    (decoy / "logs").mkdir(parents=True)
    with live_app_data_fence.protect(decoy):
        with live_app_data_fence.refused():
            with open(decoy / "logs" / "hook-errors.log", "a", encoding="utf-8") as handle:
                handle.write("must not be written\n")
    assert not (decoy / "logs" / "hook-errors.log").exists()


def test_setup_result_is_written_only_under_the_disposable_root(live_app_data_fence):
    from vres_os import bootstrap, paths

    bootstrap._write_setup_result("failed", error=RuntimeError("synthetic failure"), cleanup="probe")
    path = paths.logs_dir() / "setup-last.json"
    assert json.loads(path.read_text(encoding="utf-8"))["message"] == "synthetic failure"
    assert _within(path, os.environ["VRES_DATA_DIR"])


def test_child_processes_inherit_the_disposable_root(live_app_data_fence):
    script = "import sys; sys.path.insert(0, sys.argv[1]); from vres_os import paths; print(paths.data_dir())"
    done = subprocess.run([sys.executable, "-I", "-B", "-c", script, str(SRC)], capture_output=True, text=True,
                          timeout=120)
    assert done.returncode == 0, done.stderr
    assert _norm(done.stdout.strip()) == _norm(os.environ["VRES_DATA_DIR"])
    # A child that inherits an explicitly copied environment keeps it as well.
    done = subprocess.run([sys.executable, "-I", "-c", "import os; print(os.environ['VRES_DATA_DIR'])"],
                          capture_output=True, text=True, env=dict(os.environ), timeout=120)
    assert _norm(done.stdout.strip()) == _norm(os.environ["VRES_DATA_DIR"])


def test_child_without_the_override_is_refused_before_it_starts(live_app_data_fence, tmp_path):
    env = {k: v for k, v in os.environ.items() if k != "VRES_DATA_DIR"}
    marker = tmp_path / "started"
    with live_app_data_fence.refused():
        subprocess.run([sys.executable, "-I", "-c", f"open({str(marker)!r}, 'w').close()"], env=env, timeout=120)
    assert not marker.exists()


def test_child_with_an_unsafe_override_is_refused_before_it_starts(live_app_data_fence, tmp_path):
    decoy = tmp_path / "decoy-live" / "VresOS"
    decoy.mkdir(parents=True)
    marker = tmp_path / "started"
    with live_app_data_fence.protect(decoy):
        with live_app_data_fence.refused():
            subprocess.run([sys.executable, "-I", "-c", f"open({str(marker)!r}, 'w').close()"],
                           env={**os.environ, "VRES_DATA_DIR": str(decoy)}, timeout=120)
    assert not marker.exists()


def test_unsafe_disposable_roots_are_rejected(live_app_data_fence, tmp_path):
    reject = live_app_data_fence.require_disposable
    error = live_app_data_fence.IsolationError
    live = Path(live_app_data_fence.live_root)
    for unsafe in (live, live / "pytest", Path(__file__).resolve().parents[1] / "app-data",
                   Path("relative") / "app-data"):
        with pytest.raises(error):
            reject(unsafe)
    for name in ("Google Drive", "My Drive", "VresBackups"):
        with pytest.raises(error):
            reject(tmp_path / name / "app-data")
    decoy = tmp_path / "decoy-live" / "VresOS"
    decoy.mkdir(parents=True)
    with live_app_data_fence.protect(decoy):
        with pytest.raises(error):
            reject(decoy / "nested")


@pytest.mark.skipif(sys.platform != "win32", reason="junctions are a Windows reparse-point mechanism")
def test_junction_aliases_cannot_redirect_into_a_protected_root(live_app_data_fence, tmp_path):
    import _winapi

    decoy = tmp_path / "decoy-live" / "VresOS"
    (decoy / "logs").mkdir(parents=True)
    # A pre-existing alias (created before the root is protected) is resolved, not trusted.
    alias = tmp_path / "innocent-looking"
    _winapi.CreateJunction(str(decoy), str(alias))
    with live_app_data_fence.protect(decoy):
        with live_app_data_fence.refused():
            open(alias / "logs" / "hook-errors.log", "a").close()
        with pytest.raises(live_app_data_fence.IsolationError):
            live_app_data_fence.require_disposable(alias / "logs")
        # Creating a new alias that targets the protected root is refused outright.
        with live_app_data_fence.refused():
            _winapi.CreateJunction(str(decoy), str(tmp_path / "second-alias"))
    assert not (decoy / "logs" / "hook-errors.log").exists()
    # A junction to an ordinary directory is still not an acceptable disposable root.
    plain = tmp_path / "plain"
    plain.mkdir()
    _winapi.CreateJunction(str(plain), str(tmp_path / "plain-alias"))
    with pytest.raises(live_app_data_fence.IsolationError):
        live_app_data_fence.require_disposable(tmp_path / "plain-alias")


def test_build_dsn_never_inherits_the_live_operational_target(live_app_data_fence, monkeypatch):
    from vres_os import db
    from vres_os.database_targets import DatabaseTargetRefused

    for name in ("VRES_DATABASE_URL", "VRES_PROVENANCE_WRITER_DATABASE_URL", "VRES_MIGRATION_DATABASE_URL",
                 "VRES_TEST_DATABASE_URL", "VRES_ALLOW_TEST_DB"):
        assert name not in os.environ, name
    assert not [name for name in os.environ if name.upper().startswith("PG")]

    def no_secret(*_a, **_kw):
        raise AssertionError("a credential was requested")

    monkeypatch.setattr(db, "SecretStore", lambda: type("S", (), {"get": no_secret})())
    with pytest.raises(DatabaseTargetRefused) as refused:
        db.build_dsn("runtime")
    message = str(refused.value)
    assert "localhost" in message and "127.0.0.1" not in message  # the disposable default, not a live target


def test_database_guard_registry_stays_private(live_app_data_fence, tmp_path_factory):
    from vres_os import database_targets

    root = database_targets.personal_release_root()
    assert _within(root, tmp_path_factory.getbasetemp())
    assert not live_app_data_fence.is_protected(root)


# ---------------------------------------------------------------------------------------------------
# D1-R1: child processes never receive database-target, test-database or libpq variables.
# ---------------------------------------------------------------------------------------------------

DATABASE_NAMES = ("VRES_DATABASE_URL", "VRES_PROVENANCE_WRITER_DATABASE_URL", "VRES_MIGRATION_DATABASE_URL",
                  "DATABASE_URL", "VRES_TEST_DATABASE_URL", "VRES_ALLOW_TEST_DB", "PGHOST", "PGHOSTADDR",
                  "PGPORT", "PGDATABASE", "PGUSER", "PGPASSWORD", "PGPASSFILE", "PGSERVICE", "PGSERVICEFILE")


def _marker_child(marker: Path, *extra: str) -> list[str]:
    """A child that would only create its marker file: proof of whether it started."""
    return [sys.executable, "-I", "-c", f"open({str(marker)!r}, 'w').close()", *extra]


def test_the_session_is_not_an_integration_opt_in_run(live_app_data_fence):
    assert live_app_data_fence.integration_opt_in is False
    assert not [name for name in os.environ if name.upper() in DATABASE_NAMES or name.upper().startswith("PG")]


@pytest.mark.parametrize("name", DATABASE_NAMES)
def test_a_child_inheriting_a_database_variable_is_refused_before_it_starts(live_app_data_fence, monkeypatch,
                                                                             tmp_path, name):
    monkeypatch.setenv(name, SYNTHETIC_DSN)
    marker = tmp_path / "started"
    with live_app_data_fence.refused() as records:
        subprocess.run(_marker_child(marker), timeout=120)
    assert not marker.exists()
    assert any(name in record for record in records)
    assert not any("synthetic-secret-value" in record or "disposable.invalid" in record for record in records)


@pytest.mark.parametrize("name", ["VRES_DATABASE_URL", "vres_database_url", "Vres_Test_Database_Url",
                                  "vres_allow_test_db", "database_url", "pgpassword", "PgHost", "pgservicefile"])
def test_a_child_given_a_database_variable_explicitly_is_refused_in_any_case(live_app_data_fence, tmp_path, name):
    if sys.platform != "win32" and name != name.upper():
        pytest.skip("environment names are case-insensitive only on Windows")
    marker = tmp_path / "started"
    with live_app_data_fence.refused() as records:
        subprocess.run(_marker_child(marker), env={**os.environ, name: SYNTHETIC_DSN}, timeout=120)
    assert not marker.exists()
    assert any(name in record for record in records)
    assert not any("synthetic-secret-value" in record for record in records)


def test_the_database_decision_reports_names_only_and_its_integration_exception_is_narrow(live_app_data_fence):
    decide = live_app_data_fence.child_database_names
    assert decide({"PATH": "x", "TEMP": "y"}, integration_opt_in_test=False) == []
    found = decide({"PATH": "x", "VRES_DATABASE_URL": SYNTHETIC_DSN, "PGPASSWORD": "p"}, integration_opt_in_test=False)
    assert found == ["PGPASSWORD", "VRES_DATABASE_URL"]
    test_env = {"VRES_TEST_DATABASE_URL": "dbname=disposable_test", "VRES_ALLOW_TEST_DB": "1",
                "VRES_DATABASE_URL": "dbname=disposable_test"}
    assert decide(test_env, integration_opt_in_test=False) == sorted(test_env)  # ordinary tests: never
    assert decide(test_env, integration_opt_in_test=True) == []  # only an authorized integration test
    assert decide({**test_env, "VRES_DATABASE_URL": "dbname=other"}, integration_opt_in_test=True) == [
        "VRES_DATABASE_URL"]
    assert decide({**test_env, "VRES_ALLOW_TEST_DB": "0"}, integration_opt_in_test=True) == ["VRES_DATABASE_URL"]
    assert decide({**test_env, "PGPASSWORD": "p", "DATABASE_URL": "x"}, integration_opt_in_test=True) == [
        "DATABASE_URL", "PGPASSWORD"]
    assert decide({**test_env, "VRES_PROVENANCE_WRITER_DATABASE_URL": "x"}, integration_opt_in_test=True) == [
        "VRES_PROVENANCE_WRITER_DATABASE_URL"]


# ---------------------------------------------------------------------------------------------------
# D1-R2: the reviewed child-process inventory. The parent audit hook judges each launch before the child
# exists; it does not run inside the child, and a static scan cannot see every dynamic launch.
# ---------------------------------------------------------------------------------------------------

_SPAWN = re.compile(r"subprocess\.(?:run|Popen|check_output|check_call|call)\(|\brun_bounded\(|(?<![\w.])Popen\("
                    r"|os\.system\(|create_subprocess_(?:exec|shell)\(")
# Direct spawn call sites per test file and what they start (reviewed 2026-10-21). "patched" sites replace
# the launch with a fake; "git" sites start git only; "python"/"python-vres"/"node"/"shell" sites must be
# reviewed in tests/conftest.py's _REVIEWED_CHILD_SITES for that class.
STATIC_SPAWN_INVENTORY = {
    "tests/integration/test_secret_safe_onboarding_journey.py": (1, ("shell",)),  # mklink; opt-in only
    "tests/test_claude_experiment_producer.py": (1, ("python-vres",)),  # import-only module check
    "tests/test_codex_handoff.py": (7, ("git", "patched")),  # git on test repositories; workers faked
    "tests/test_credential_broker.py": (3, ("git", "python")),  # git; env-echo child via the broker
    "tests/test_database_contact_guard.py": (1, ("python-vres",)),  # registry lock on a temporary root
    "tests/test_e4_frozen_contract_integrity.py": (1, ("git",)),
    "tests/test_e6_observability_hook.py": (2, ("git",)),
    "tests/test_executor.py": (1, ("python-vres",)),  # vres_os.procedure_worker
    "tests/test_install_preflight.py": (3, ("python", "python-vres")),  # import smoke; report/pip stubs
    "tests/test_live_app_data_isolation.py": (22, ("git", "python", "python-vres")),  # these regressions
    "tests/test_local_secrets.py": (3, ("git", "python")),  # git; env-echo child via the manager
    "tests/test_personal_feature_fence.py": (1, ("python",)),  # scripts/release_gate.py
    "tests/test_process_stdio.py": (2, ("patched",)),  # run_bounded(["git", ...]) with a faked Popen
    "tests/test_release_artifact.py": (5, ("git", "python-vres")),  # stdlib release_artifact.py tool
    "tests/test_release_boundaries.py": (7, ("python", "python-vres", "taskkill")),  # locks, bounded, parser
    "tests/test_runtime_surfaces.py": (1, ("python",)),  # scripts/release_gate.py -O
    "tests/test_windows_node_mcp_git.py": (2, ("git", "node")),  # node -> python discover_project
}


def _scan_spawn_sites() -> dict[str, int]:
    found = {}
    for path in sorted((ROOT / "tests").rglob("*.py")):
        count = len(_SPAWN.findall(path.read_text(encoding="utf-8")))
        if count:
            found[path.relative_to(ROOT).as_posix()] = count
    return found


def test_the_static_spawn_inventory_is_the_reviewed_one(live_app_data_fence):
    assert _scan_spawn_sites() == {path: count for path, (count, _kind) in STATIC_SPAWN_INVENTORY.items()}
    reviewed = live_app_data_fence.reviewed_child_sites
    for path, (_count, kinds) in STATIC_SPAWN_INVENTORY.items():
        for kind in kinds:
            if kind in ("python", "python-vres", "node", "shell", "powershell", "git", "icacls", "taskkill"):
                assert kind in reviewed.get(path, ()), (path, kind)
    for site in reviewed:
        assert (ROOT / site).is_file(), site


def test_children_are_attributed_to_the_running_test_file(live_app_data_fence):
    assert live_app_data_fence.active_site() == THIS_SITE
    assert {"python", "python-vres"} <= live_app_data_fence.reviewed_child_sites[THIS_SITE]


@pytest.mark.parametrize("program,line,kind", [
    (sys.executable, "-I -c print(1)", "python"),
    (sys.executable, "-c import vres_os.paths", "python-vres"),
    (sys.executable, f"-I {SRC / 'vres_os' / 'release_artifact.py'} check", "python-vres"),
    (sys.executable, "-I -c import runpy,sys; runpy.run_module(sys.argv.pop(1)) vres_os.procedure_worker", "python-vres"),
    ("python.exe", "python.exe -c pass", "python"),
    ("C:\\Program Files\\Git\\cmd\\git.exe", "git --version", "git"),
    ("icacls", "icacls x /inheritance:r", "icacls"),
    ("taskkill.exe", "taskkill /T /F /PID 1", "taskkill"),
    ("node", "node parent.js", "node"),
    ("cmd", "cmd /c mklink /J a b", "shell"),
    ("powershell.exe", "powershell -File x.ps1", "powershell"),
    ("pwsh", "pwsh -c 1", "powershell"),
    ("claude", "claude -p hi", "provider"),
    ("C:\\tools\\codex.cmd", "codex exec -", "provider"),
    ("C:\\tools\\unknown-tool.exe", "unknown-tool", "other"),
])
def test_child_classification(live_app_data_fence, program, line, kind):
    assert live_app_data_fence.classify_child(program, line) == kind


def test_an_unreviewed_python_child_is_refused_before_it_starts(live_app_data_fence, tmp_path):
    marker = tmp_path / "started"
    with live_app_data_fence.as_test_site("tests/test_not_reviewed_example.py"):
        with live_app_data_fence.refused() as records:
            subprocess.run(_marker_child(marker), timeout=120)
    assert not marker.exists()
    assert "unreviewed python child" in records[0]


def test_a_vres_capable_child_from_a_site_reviewed_only_for_plain_python_is_refused(live_app_data_fence, tmp_path):
    marker = tmp_path / "started"
    assert "python-vres" not in live_app_data_fence.reviewed_child_sites["tests/test_local_secrets.py"]
    with live_app_data_fence.as_test_site("tests/test_local_secrets.py"):
        with live_app_data_fence.refused() as records:
            subprocess.run([sys.executable, "-I", "-c", f"import sys; open({str(marker)!r}, 'w').close()",
                            "vres_os"], timeout=120)
    assert not marker.exists()
    assert "unreviewed python-vres child" in records[0]


def test_a_child_whose_command_line_names_live_data_is_refused(live_app_data_fence, tmp_path):
    live = live_app_data_fence.live_root  # a string argument only; never accessed
    plugin = os.path.join(os.path.expanduser("~"), ".claude", "skills", "vres-os")
    for argument in (live, live.replace("\\", "/") + "/config.json", plugin):
        marker = tmp_path / "started"
        with live_app_data_fence.refused() as records:
            subprocess.run(_marker_child(marker, argument), timeout=120)
        assert not marker.exists()
        assert "names live Vres data or the installed plugin" in records[0]


@pytest.mark.parametrize("argv", [
    ["claude", "-p", "hello"],
    ["C:\\tools\\codex.cmd", "exec", "-"],
    ["powershell.exe", "-NoProfile", "-File", str(ROOT / "scripts" / "windows" / "vres-launch.ps1")],
    ["cmd", "/c", "echo", "x"],
    ["C:\\tools\\unknown-tool.exe"],
])
def test_provider_shell_and_unknown_children_are_refused_without_starting_anything(live_app_data_fence, argv):
    # check_child evaluates the would-be launch exactly as the audit hook does; no process is created.
    with live_app_data_fence.refused():
        live_app_data_fence.check_child("subprocess.Popen", (None, argv, None, None))


def test_reviewed_ordinary_children_still_run(live_app_data_fence, tmp_path):
    done = subprocess.run(["git", "--version"], capture_output=True, text=True, timeout=120)
    assert done.returncode == 0 and "git version" in done.stdout
    marker = tmp_path / "started"
    subprocess.run(_marker_child(marker), timeout=120, check=True)
    assert marker.exists()


# ---------------------------------------------------------------------------------------------------
# D1-R3: the temporary base is trusted before the first write.
# ---------------------------------------------------------------------------------------------------

def _volume(path, **overrides):
    info = {"root": "C:\\", "drive_type": 3, "filesystem": "NTFS", "label": "", "device": "\\Device\\HarddiskVolume3",
            "long_path": os.path.realpath(path)}
    info.update(overrides)
    return info


WINDOWS_ONLY = pytest.mark.skipif(sys.platform != "win32", reason="Windows TEMP/TMP and volume semantics")


def _env(base, **extra):
    return {"TEMP": str(base), "TMP": str(base), **extra}


def _host_env(base, **extra):
    """The temporary-base variables of the platform the suite runs on."""
    if sys.platform == "win32":
        return _env(base, **extra)
    return {"TMPDIR": str(base), **extra}


def _refused_host_base(fence, environ, **kwargs):
    """Assess with the host platform's real path semantics (Windows volume metadata simulated)."""
    options = {"platform": sys.platform, **({"volume": _volume} if sys.platform == "win32" else {}), **kwargs}
    with pytest.raises(fence.IsolationError) as refused:
        fence.assess_temp_base(environ, **options)
    return str(refused.value)


def test_initialization_validated_the_base_before_creating_anything(live_app_data_fence):
    assert live_app_data_fence.init_order == ("validate-temp-base", "create-session-directory",
                                              "validate-session-directory", "create-app-data-root",
                                              "enable-isolation")


@pytest.mark.skipif(sys.platform != "win32", reason="the approved base is the Windows TEMP directory")
def test_the_actual_windows_temp_directory_is_the_trusted_base(live_app_data_fence, tmp_path_factory):
    base = live_app_data_fence.trusted_temp_base
    assert _norm(base) == _norm(os.environ["TEMP"]) == _norm(os.environ["TMP"]) == _norm(tempfile.gettempdir())
    assert live_app_data_fence.assess_temp_base(os.environ, current_tempdir=tempfile.gettempdir()) == base
    info = live_app_data_fence.windows_volume(base)
    assert info["drive_type"] == 3 and info["filesystem"].upper() in ("NTFS", "REFS")
    assert re.fullmatch(r"\\Device\\HarddiskVolume\d+", info["device"])
    assert _within(live_app_data_fence.session_root, base)
    assert _within(tmp_path_factory.getbasetemp(), base)
    assert _within(os.environ["VRES_DATA_DIR"], base)


@WINDOWS_ONLY
def test_a_simulated_local_windows_base_is_accepted(live_app_data_fence, tmp_path):
    base = tmp_path / "base"
    base.mkdir()
    assess = live_app_data_fence.assess_temp_base
    assert _norm(assess(_env(base), platform="win32", volume=_volume)) == _norm(base)
    assert _norm(assess(_env(base, TMPDIR=str(base)), platform="win32", volume=_volume)) == _norm(base)


def _refused_base(fence, environ, **kwargs):
    with pytest.raises(fence.IsolationError) as refused:
        fence.assess_temp_base(environ, **{"platform": "win32", "volume": _volume, **kwargs})
    return str(refused.value)


@WINDOWS_ONLY
def test_temp_variables_must_be_set_absolute_and_agree(live_app_data_fence, tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    a.mkdir()
    b.mkdir()
    fence = live_app_data_fence
    assert "both be set" in _refused_base(fence, {"TEMP": str(a)})
    assert "same directory" in _refused_base(fence, {"TEMP": str(a), "TMP": str(b)})
    assert "same directory" in _refused_base(fence, _env(a, TMPDIR=str(b)))
    assert "absolute drive path" in _refused_base(fence, _env("relative\\tmp"))
    assert "UNC" in _refused_base(fence, _env("\\\\server\\share\\tmp"))
    assert "does not exist" in _refused_base(fence, _env(a / "missing"))
    assert "different base" in _refused_base(fence, _env(a), current_tempdir=str(b))


@pytest.mark.skipif(sys.platform != "win32", reason="junctions are a Windows reparse-point mechanism")
def test_a_junction_component_is_refused(live_app_data_fence, tmp_path):
    import _winapi

    target = tmp_path / "target"
    (target / "inner").mkdir(parents=True)
    alias = tmp_path / "alias"
    _winapi.CreateJunction(str(target), str(alias))
    assert "link, junction or reparse point" in _refused_base(live_app_data_fence, _env(alias))
    # A junction anywhere above the base is refused too, not only the base itself.
    assert "link, junction or reparse point" in _refused_base(live_app_data_fence, _env(alias / "inner"))


@WINDOWS_ONLY
def test_a_cloud_placeholder_component_is_refused(live_app_data_fence, tmp_path):
    base = tmp_path / "base"
    base.mkdir()

    def placeholder_lstat(path):
        if _norm(path) == _norm(base):
            return SimpleNamespace(st_mode=stat.S_IFDIR | 0o700, st_file_attributes=0x400000)  # RECALL_ON_DATA_ACCESS
        return os.lstat(path)

    assert "cloud or offline placeholder" in _refused_base(live_app_data_fence, _env(base), lstat=placeholder_lstat)


@pytest.mark.parametrize("overrides,message", [
    ({"drive_type": 2}, "fixed local disk"),          # removable
    ({"drive_type": 4}, "fixed local disk"),          # remote (mapped network drive)
    ({"drive_type": 5}, "fixed local disk"),          # CD/DVD
    ({"filesystem": "FAT32", "label": "Google Drive"}, "NTFS or ReFS"),  # this machine's Google Drive volume
    ({"filesystem": "exFAT"}, "NTFS or ReFS"),
    ({"label": "Google Drive"}, "cloud-drive volume"),
    ({"device": "\\??\\C:\\subst-target"}, "not a local disk volume"),   # subst drive
    ({"device": "\\Device\\LanmanRedirector\\;Z:0\\server\\share"}, "not a local disk volume"),
    ({"device": None}, "not a local disk volume"),     # a volume mounted on a folder
    ({"root": "\\\\?\\Volume{00000000-0000-0000-0000-000000000000}\\"}, "UNC or non-drive volume"),
    ({"filesystem": ""}, "inconclusive"),
])
@WINDOWS_ONLY
def test_unsafe_or_unknown_volumes_are_refused(live_app_data_fence, tmp_path, overrides, message):
    base = tmp_path / "base"
    base.mkdir()
    assert message in _refused_base(live_app_data_fence, _env(base),
                                    volume=lambda path: _volume(path, **overrides))


@WINDOWS_ONLY
def test_unavailable_or_redirected_volume_metadata_is_refused(live_app_data_fence, tmp_path):
    base = tmp_path / "base"
    base.mkdir()
    fence = live_app_data_fence

    def unavailable(path):
        raise fence.IsolationError(f"Windows volume metadata is unavailable (GetVolumeInformationW) for {path}")

    assert "unavailable" in _refused_base(fence, _env(base), volume=unavailable)
    assert "inconclusive" in _refused_base(fence, _env(base), volume=lambda path: {})
    assert "resolves elsewhere" in _refused_base(fence, _env(base),
                                                 volume=lambda path: _volume(path, long_path="C:\\elsewhere"))


def test_synchronized_backup_repository_and_live_locations_are_refused(live_app_data_fence, tmp_path):
    fence = live_app_data_fence
    for name in ("OneDrive", "Google Drive", "VresBackups"):
        unsafe = tmp_path / name / "tmp"
        unsafe.mkdir(parents=True)
        assert "synchronized or backup storage" in _refused_host_base(fence, _host_env(unsafe))
    synced = tmp_path / "synced"
    (synced / "tmp").mkdir(parents=True)
    assert "OneDrive folder" in _refused_host_base(fence, _host_env(synced / "tmp", OneDriveConsumer=str(synced)))
    assert "inside the repository" in _refused_host_base(fence, _host_env(ROOT / "tests"))
    live = fence.live_root  # refused by its spelling before any access
    assert "protected live Vres data" in _refused_host_base(fence, _host_env(live))


def test_an_untrusted_base_creates_nothing(live_app_data_fence, tmp_path):
    base = tmp_path / "base"
    base.mkdir()
    fence = live_app_data_fence

    def untrusted(environ, *, current_tempdir):
        raise fence.IsolationError("simulated untrusted base")

    order = []
    with pytest.raises(fence.IsolationError, match="simulated untrusted base"):
        fence.establish_session_root(_host_env(base), assess=untrusted, order=order)
    assert order == ["validate-temp-base"] and list(base.iterdir()) == []
    # The real assessment also refuses before writing: tempfile already uses the trusted base, not this one.
    order = []
    with pytest.raises(fence.IsolationError, match="different base"):
        fence.establish_session_root(_host_env(base), order=order)
    assert order == ["validate-temp-base"] and list(base.iterdir()) == []
    # An unsafe inherited VRES_DATA_DIR is refused before anything is created as well.
    order = []
    live = fence.live_root
    with pytest.raises(fence.IsolationError, match="protected live data"):
        fence.establish_session_root(_host_env(base, VRES_DATA_DIR=live), assess=lambda env, **_: str(base),
                                     order=order)
    assert order == ["validate-temp-base"] and list(base.iterdir()) == []


def test_a_trusted_base_is_used_in_the_required_order(live_app_data_fence, tmp_path):
    base = tmp_path / "base"
    base.mkdir()
    order = []
    trusted, root = live_app_data_fence.establish_session_root(_env(base), assess=lambda env, **_: str(base),
                                                               order=order)
    assert order == ["validate-temp-base", "create-session-directory", "validate-session-directory",
                     "create-app-data-root"]
    assert _norm(trusted) == _norm(base) and root.is_dir() and root.name == "VresOS"
    assert _norm(root.parent.parent) == _norm(base) and list(root.iterdir()) == []


def test_the_posix_temporary_base_semantics_are_validated_on_every_platform(live_app_data_fence, tmp_path):
    """The non-Windows path: TMPDIR must be absolute; its resolved path is checked component by component."""
    fence = live_app_data_fence
    base = tmp_path / "posix-base"
    base.mkdir()
    assess = fence.assess_temp_base
    assert _norm(assess({"TMPDIR": str(base)}, platform="linux")) == _norm(os.path.realpath(base))

    def refused(environ, **kwargs):
        with pytest.raises(fence.IsolationError) as error:
            assess(environ, platform="linux", **kwargs)
        return str(error.value)

    def faked(mode):
        def lstat(path):
            if _norm(path) == _norm(base):
                return SimpleNamespace(st_mode=mode, st_file_attributes=0)
            return os.lstat(path)
        return lstat

    assert "not absolute" in refused({"TMPDIR": "relative/tmp"})
    assert "does not exist" in refused({"TMPDIR": str(base / "missing")})
    assert "link, junction or reparse point" in refused({"TMPDIR": str(base)}, lstat=faked(stat.S_IFLNK | 0o777))
    assert "not a directory" in refused({"TMPDIR": str(base)}, lstat=faked(stat.S_IFREG | 0o600))
    assert "different base" in refused({"TMPDIR": str(base)}, current_tempdir=str(tmp_path))
    assert "inside the repository" in refused({"TMPDIR": str(ROOT / "tests")})
    assert "protected live Vres data" in refused({"TMPDIR": fence.live_root})  # by spelling, never resolved
    backups = tmp_path / "VresBackups" / "tmp"
    backups.mkdir(parents=True)
    assert "synchronized or backup storage" in refused({"TMPDIR": str(backups)})


# ---------------------------------------------------------------------------------------------------
# D1-R4: git, icacls and taskkill are judged by executable, arguments, site, scope, targets and environment.
# These decisions are evaluated directly (check_child); no refused command is ever started.
# ---------------------------------------------------------------------------------------------------

def _decide(fence, argv, *, cwd=None, env=None, site=THIS_SITE):
    with fence.as_test_site(site):
        fence.check_child("subprocess.Popen", (None, argv, None if cwd is None else str(cwd), env))


def _refusal(fence, argv, **kwargs):
    with fence.refused() as records:
        _decide(fence, argv, **kwargs)
    return records[0]


def _scratch(tmp_path):
    scratch = tmp_path / "scratch-repo"
    scratch.mkdir(exist_ok=True)
    return scratch


def _fill(argv, scratch):
    return [part.format(scratch=str(scratch), repo=str(ROOT), anchor=ROOT.anchor) for part in argv]


@pytest.mark.parametrize("argv,reason", [
    (["git", "-C", "{scratch}", "fetch", "origin"], "network or remote"),
    (["git", "-C", "{scratch}", "push", "origin", "HEAD"], "network or remote"),
    (["git", "-C", "{scratch}", "pull"], "network or remote"),
    (["git", "-C", "{scratch}", "ls-remote", "https://example.invalid/r.git"], "network or remote"),
    (["git", "-C", "{scratch}", "remote", "add", "o", "https://example.invalid/r.git"], "network or remote"),
    (["git", "-C", "{scratch}", "submodule", "update", "--init"], "network or remote"),
    (["git", "-C", "{scratch}", "archive", "--remote=x", "HEAD"], "network or remote"),
    (["git", "-C", "{scratch}", "clone", "https://example.invalid/r.git", "{scratch}/c"], "URL"),
    (["git", "-C", "{scratch}", "clone", "git@example.invalid:r.git", "{scratch}/c"], "looks remote"),
    (["git", "-C", "{scratch}", "clone", "--upload-pack=calc", "{scratch}/b.bundle", "{scratch}/c"], "--upload-pack"),
    (["git", "-C", "{scratch}", "clone", "-u", "calc", "{scratch}/b.bundle", "{scratch}/c"], "clone options"),
    (["git", "-C", "{scratch}", "clone", "{repo}", "{scratch}/c"], "outside the trusted temporary base"),
    (["git", "-C", "{scratch}", "co", "main"], "not a reviewed scratch-repository operation"),  # an alias
    (["git", "-c", "alias.co=!calc", "-C", "{scratch}", "status"], "-c alias.co"),
    (["git", "-c", "core.sshCommand=calc", "-C", "{scratch}", "status"], "-c core.sshcommand"),
    (["git", "-c", "core.hooksPath={scratch}", "-C", "{scratch}", "commit", "-m", "x"], "-c core.hookspath"),
    (["git", "-c", "core.fsmonitor=calc", "-C", "{scratch}", "status"], "-c core.fsmonitor"),
    (["git", "-c", "credential.helper=calc", "-C", "{scratch}", "status"], "-c credential.helper"),
    (["git", "--exec-path={scratch}", "-C", "{scratch}", "status"], "global option --exec-path"),
    (["git", "-p", "-C", "{scratch}", "log"], "global option -p"),
    (["git", "-C", "{scratch}", "config", "--global", "user.name", "x"], "config --global"),
    (["git", "-C", "{scratch}", "config", "--system", "core.editor", "calc"], "config --system"),
    (["git", "-C", "{scratch}", "config", "--file", "{scratch}/c", "a.b", "c"], "config --file"),
    (["git", "-C", "{scratch}", "config", "alias.st", "!calc"], "may not set alias.st"),
    (["git", "-C", "{scratch}", "config", "core.hooksPath", "{scratch}"], "may not set core.hookspath"),
    (["git", "-C", "{scratch}", "init", "--template={scratch}"], "--template"),
    (["git", "-C", "{scratch}", "worktree", "add", "--detach", "{repo}/wt", "HEAD"],
     "outside the trusted temporary base"),
    (["git", "-C", "{scratch}", "worktree", "move", "a", "b"], "add, list, remove and prune"),
    (["git", "-C", "{repo}", "commit", "-m", "x"], "read-only object inspection only"),
    (["git", "-C", "{repo}", "add", "."], "read-only object inspection only"),
    (["git", "-C", "{repo}", "status"], "read-only object inspection only"),
    (["git", "-C", "{repo}", "config", "user.name", "x"], "read-only object inspection only"),
    (["git", "-C", "{repo}", "show", "HEAD"], "limited to <rev>:<path>"),
    (["git", "-C", "{anchor}", "status"], "outside a scratch repository"),
])
def test_unsafe_git_commands_are_refused_before_creation(live_app_data_fence, tmp_path, argv, reason):
    record = _refusal(live_app_data_fence, _fill(argv, _scratch(tmp_path)))
    assert "refused a git child" in record and reason.lower() in record.lower(), record


@pytest.mark.parametrize("name,value", [
    ("GIT_SSH_COMMAND", "calc"), ("GIT_ASKPASS", "calc"), ("git_editor", "calc"), ("GIT_EXEC_PATH", "x"),
    ("GIT_CONFIG_PARAMETERS", "'alias.st=!calc'"), ("GIT_CONFIG_COUNT", "1"), ("GIT_DIR", str(ROOT / ".git")),
    ("GIT_WORK_TREE", str(ROOT)), ("GIT_CONFIG_GLOBAL", str(ROOT / "evil.gitconfig")), ("GIT_TRACE", "1"),
    ("GIT_PROXY_COMMAND", "calc"), ("GIT_TEMPLATE_DIR", "x"),
])
def test_git_environment_that_executes_or_redirects_is_refused(live_app_data_fence, tmp_path, name, value):
    if sys.platform != "win32" and name != name.upper():
        pytest.skip("environment names are case-insensitive only on Windows")
    env = {**os.environ, name: value}
    record = _refusal(live_app_data_fence, ["git", "-C", str(_scratch(tmp_path)), "status"], env=env)
    assert "environment variable" in record and name.upper() in record


def test_the_inherited_git_environment_was_stripped_of_executables(live_app_data_fence):
    # Only reviewed variables remain; the isolation settings hold their neutral values.
    remaining = {name.upper(): value for name, value in os.environ.items() if name.upper().startswith("GIT_")}
    assert set(remaining) <= {"GIT_OPTIONAL_LOCKS", "GIT_NO_REPLACE_OBJECTS", "GIT_CONFIG_NOSYSTEM",
                              "GIT_CONFIG_GLOBAL", "GIT_EDITOR", "GIT_PAGER"}
    assert remaining["GIT_CONFIG_NOSYSTEM"] == "1" and remaining["GIT_CONFIG_GLOBAL"] == os.devnull
    assert remaining["GIT_EDITOR"] == ":" and remaining["GIT_PAGER"] == "cat"


def test_git_from_a_site_not_reviewed_for_git_is_refused(live_app_data_fence, tmp_path):
    record = _refusal(live_app_data_fence, ["git", "-C", str(_scratch(tmp_path)), "status"],
                      site="tests/test_runtime_surfaces.py")
    assert "unreviewed git child" in record


def test_git_must_be_the_approved_binary(live_app_data_fence, tmp_path):
    fence = live_app_data_fence
    impostor = tmp_path / "tools" / ("git.exe" if sys.platform == "win32" else "git")
    record = _refusal(fence, [str(impostor), "--version"])
    assert "not the approved git executable" in record
    assert fence.approved_executables["git"], "no approved git executable was found"


@pytest.mark.skipif(sys.platform != "win32", reason="current-directory executable search is a Windows behaviour")
def test_a_bare_git_shadowed_in_the_current_directory_is_refused(live_app_data_fence, tmp_path, monkeypatch):
    shadow = tmp_path / "shadow"
    shadow.mkdir()
    (shadow / "git.exe").write_bytes(b"not git")
    monkeypatch.chdir(shadow)
    record = _refusal(live_app_data_fence, ["git", "--version"])
    assert "would shadow the approved git" in record


@pytest.mark.parametrize("argv,cwd", [
    (["git", "--version"], None),
    (["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", "-c", "commit.gpgsign=false", "-C",
      "{scratch}", "commit", "-q", "-m", "x"], None),
    (["git", "-c", "user.email=test@example.com", "-c", "user.name=Vres Test", "-C", "{scratch}", "stash", "push",
      "-u", "-m", "test stash"], None),
    (["git", "-c", "core.quotepath=off", "-c", "core.fsmonitor=false", "-C", "{scratch}", "status",
      "--porcelain=v2", "-z", "--untracked-files=all", "--ignored=traditional"], None),
    (["git", "-C", "{scratch}", "config", "--worktree", "some.key", "value"], None),
    (["git", "-C", "{scratch}", "config", "core.autocrlf", "false"], None),
    (["git", "-C", "{scratch}", "config", "extensions.worktreeConfig", "true"], None),
    (["git", "-C", "{scratch}", "config", "--get", "remote.origin.url"], None),
    (["git", "-C", "{scratch}", "worktree", "add", "--detach", "{scratch}/wt", "HEAD"], None),
    (["git", "-C", "{scratch}", "worktree", "remove", "--force", "{scratch}/wt"], None),
    (["git", "-C", "{scratch}", "diff", "--cached", "--binary", "--find-renames=50%"], None),
    (["git", "-C", "{scratch}", "update-index", "--add", "--cacheinfo", "100644,0123,f.txt"], None),
    (["git", "-C", "{scratch}", "bundle", "create", "-q", "{scratch}/b.bundle", "--all"], None),
    (["git", "bundle", "verify", "{scratch}/b.bundle"], "{scratch}"),
    (["git", "clone", "{scratch}/b.bundle", "{scratch}/clone"], "{scratch}"),
    (["git", "fsck", "--full"], "{scratch}"),
    (["git", "-C", "{repo}", "ls-tree", "-r", "-z", "HEAD", "--", "plugins/vres-os/bin"], None),
    (["git", "-C", "{repo}", "cat-file", "-t", "HEAD"], None),
    (["git", "-C", "{repo}", "rev-parse", "HEAD"], None),
    (["git", "show", "HEAD:README.md"], "{repo}"),
])
def test_reviewed_git_operations_are_permitted(live_app_data_fence, tmp_path, argv, cwd):
    scratch = _scratch(tmp_path)
    (scratch / "b.bundle").write_bytes(b"synthetic")  # clone's source must exist as a local file
    _decide(live_app_data_fence, _fill(argv, scratch), cwd=None if cwd is None else _fill([cwd], scratch)[0])


def test_reviewed_git_environment_values_are_permitted(live_app_data_fence, tmp_path):
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith("GIT_")}
    env.update(GIT_OPTIONAL_LOCKS="0", GIT_NO_REPLACE_OBJECTS="1", GIT_CONFIG_NOSYSTEM="1",
               GIT_CONFIG_GLOBAL=os.devnull, GIT_TERMINAL_PROMPT="0")
    _decide(live_app_data_fence, ["git", "-C", str(ROOT), "cat-file", "--batch"], env=env)


@pytest.mark.skipif(sys.platform != "win32", reason="the audit event carries a joined Windows command line")
def test_a_joined_windows_command_line_is_split_exactly(live_app_data_fence, tmp_path):
    fence = live_app_data_fence
    line = '"C:\\Program Files\\Git\\cmd\\git.exe" -c "user.name=Vres Test" -C "C:\\a b" status --short'
    assert fence.split_command_line(line) == ["C:\\Program Files\\Git\\cmd\\git.exe", "-c", "user.name=Vres Test",
                                              "-C", "C:\\a b", "status", "--short"]
    scratch = _scratch(tmp_path)
    record = _refusal(fence, subprocess.list2cmdline(["git", "-C", str(scratch), "fetch", "origin"]))
    assert "network or remote" in record
    _decide(fence, subprocess.list2cmdline(["git", "-C", str(scratch), "status", "--porcelain=v2", "-z"]))


def test_reviewed_git_operations_still_work_in_a_scratch_repository(live_app_data_fence, tmp_path):
    scratch = _scratch(tmp_path)
    identity = ["-c", "user.name=t", "-c", "user.email=t@example.invalid", "-c", "commit.gpgsign=false"]
    subprocess.run(["git", "-C", str(scratch), "init", "-q"], check=True, capture_output=True, timeout=120)
    (scratch / "f.txt").write_text("x", encoding="utf-8")
    subprocess.run(["git", "-C", str(scratch), "add", "f.txt"], check=True, capture_output=True, timeout=120)
    subprocess.run(["git", *identity, "-C", str(scratch), "commit", "-q", "-m", "x"], check=True,
                   capture_output=True, timeout=120)
    head = subprocess.run(["git", "-C", str(scratch), "rev-parse", "HEAD"], check=True, capture_output=True,
                          text=True, timeout=120).stdout.strip()
    assert re.fullmatch(r"[0-9a-f]{40}", head)


WINDOWS_TOOLS = pytest.mark.skipif(sys.platform != "win32", reason="icacls and taskkill are Windows tools")


def _user_grant(rights="(F)"):
    import getpass

    return f"{getpass.getuser()}:{rights}"


@WINDOWS_TOOLS
@pytest.mark.parametrize("argv,reason", [
    (["icacls.exe", "{repo}\\README.md", "/inheritance:r", "/grant:r", "USER"], "outside the trusted temporary base"),
    (["icacls.exe", "{anchor}Windows", "/inheritance:r", "/grant:r", "USER"], "outside the trusted temporary base"),
    (["icacls.exe", "{scratch}\\f", "/setowner", "Administrators"], "limited to"),
    (["icacls.exe", "{scratch}\\f", "/reset", "/T"], "limited to"),
    (["icacls.exe", "{scratch}\\f", "/save", "{scratch}\\acl"], "limited to"),
    (["icacls.exe", "{scratch}\\f", "/inheritance:r", "/grant:r", "USER", "/T"], "limited to"),
    (["icacls.exe", "{scratch}\\f", "/inheritance:r", "/grant:r", "Everyone:(F)"], "only to the current user"),
    (["icacls.exe", "{scratch}\\f", "/inheritance:r", "/grant:r", "USER(F)(WDAC)"], "not a reviewed simple grant"),
    (["icacls.exe", "relative\\f", "/inheritance:r", "/grant:r", "USER"], "must be absolute"),
])
def test_unsafe_icacls_commands_are_refused_before_creation(live_app_data_fence, tmp_path, argv, reason):
    scratch = _scratch(tmp_path)
    argv = [_user_grant(part[4:] or "(F)") if part.startswith("USER") else part for part in _fill(argv, scratch)]
    record = _refusal(live_app_data_fence, argv, site="tests/test_local_secrets.py")
    assert "refused a icacls child" in record and reason in record, record


@WINDOWS_TOOLS
def test_icacls_from_a_site_not_reviewed_for_it_is_refused(live_app_data_fence, tmp_path):
    argv = ["icacls.exe", str(_scratch(tmp_path) / "f"), "/inheritance:r", "/grant:r", _user_grant()]
    assert "unreviewed icacls child" in _refusal(live_app_data_fence, argv, site="tests/test_project.py")


@WINDOWS_TOOLS
@pytest.mark.parametrize("rights", ["(F)", "(R)", "(OI)(CI)(F)"])
def test_the_reviewed_icacls_grant_on_a_disposable_path_is_permitted(live_app_data_fence, tmp_path, rights):
    argv = ["icacls.exe", str(_scratch(tmp_path) / "f"), "/inheritance:r", "/grant:r", _user_grant(rights)]
    _decide(live_app_data_fence, argv, site="tests/test_local_secrets.py")


@WINDOWS_TOOLS
def test_taskkill_is_limited_to_a_direct_child_of_this_process(live_app_data_fence):
    fence = live_app_data_fence
    child = subprocess.Popen([sys.executable, "-I", "-c", "import time; time.sleep(60)"])
    try:
        assert fence.parent_pid(child.pid) == os.getpid()
        site = "tests/test_release_boundaries.py"
        _decide(fence, ["taskkill.exe", "/PID", str(child.pid), "/T", "/F"], site=site)  # permitted, not run
        # codex_handoff.generate_patch stops its own git child the same way at the patch byte ceiling.
        _decide(fence, ["taskkill.exe", "/PID", str(child.pid), "/T", "/F"], site="tests/test_codex_handoff.py")
        assert "unreviewed taskkill child" in _refusal(
            fence, ["taskkill.exe", "/PID", str(child.pid), "/T", "/F"], site="tests/test_project.py")
        # The race of a tree-kill with a normal exit: a child that has just exited, whose handle its creator
        # still holds, is still recognised as ours (its process id cannot be reused while the handle is open).
        exited = subprocess.Popen([sys.executable, "-I", "-c", "pass"])
        exited.wait(timeout=60)
        assert fence.parent_pid(exited.pid) == os.getpid()
        _decide(fence, ["taskkill.exe", "/PID", str(exited.pid), "/T", "/F"], site=site)  # permitted, not run
        for argv, reason in (
                (["taskkill.exe", "/PID", str(os.getppid()), "/T", "/F"], "not a direct child"),
                (["taskkill.exe", "/PID", "4294967", "/T", "/F"], "not a direct child"),
                (["taskkill.exe", "/PID", "0", "/T", "/F"], "not a direct child"),
                (["taskkill.exe", "/IM", "python.exe", "/T", "/F"], "limited to /PID"),
                (["taskkill.exe", "/PID", str(child.pid), "/F"], "limited to /PID"),
                (["taskkill.exe", "/S", "remote-host", "/PID", str(child.pid), "/T", "/F"], "limited to /PID"),
                (["taskkill.exe", "/FI", "STATUS eq RUNNING", "/T", "/F"], "limited to /PID")):
            record = _refusal(fence, argv, site=site)
            assert "refused a taskkill child" in record and reason in record, record
        assert "unreviewed taskkill child" in _refusal(
            fence, ["taskkill.exe", "/PID", str(child.pid), "/T", "/F"], site="tests/test_local_secrets.py")
    finally:
        child.kill()
        child.wait(timeout=60)


# ---------------------------------------------------------------------------------------------------
# D1-R6: git filesystem operands stay inside the trusted temporary base (decisions only; nothing runs).
# ---------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("argv,reason", [
    (["git", "-C", "{scratch}", "init", "../escape"], "escapes its directory"),
    (["git", "-C", "{scratch}", "init", "sub/../../escape"], "escapes its directory"),
    (["git", "-C", "{scratch}", "bundle", "create", "../out.bundle", "--all"], "escapes its directory"),
    (["git", "-C", "{scratch}", "bundle", "create", "-q", "..\\out.bundle", "--all"], "escapes its directory"),
    (["git", "-C", "{scratch}", "bundle", "create", "--all"], "needs its bundle file first"),
    (["git", "-C", "{scratch}", "worktree", "add", "--detach", "../wt", "HEAD"], "escapes its directory"),
    (["git", "-C", "{scratch}", "worktree", "add", "--detach", "..\\..\\wt", "HEAD"], "escapes its directory"),
    (["git", "-C", "{scratch}", "worktree", "add", "--orphan", "wt"], "option --orphan is not reviewed"),
    (["git", "-C", "{scratch}", "diff", "--no-index", "../a", "b"], "--no-index"),
    (["git", "-C", "{scratch}", "diff", "--no-index", "a", "b"], "--no-index"),
    (["git", "-C", "{scratch}", "apply", "../p.diff"], "escapes its directory"),
    (["git", "-C", "{scratch}", "apply", "--directory=sub"], "--directory"),
    (["git", "-C", "{scratch}", "apply", "--unsafe-paths", "p.diff"], "--unsafe-paths"),
    (["git", "-C", "{scratch}", "apply", "--include=x", "p.diff"], "option --include is not reviewed"),
    (["git", "-C", "{scratch}", "hash-object", "-w", "../secret"], "escapes its directory"),
    (["git", "-C", "{scratch}", "hash-object", "--path=x", "f"], "option --path is not reviewed"),
    (["git", "-C", "{scratch}", "init", "--object-format=sha256"], "option --object-format is not reviewed"),
    (["git", "-C", "{scratch}", "init", "a", "b"], "at most one directory"),
    (["git", "-C", "{scratch}", "add", "../outside.txt"], "escapes its directory"),
    (["git", "-C", "{scratch}", "checkout", "--", "../outside.txt"], "escapes its directory"),
])
def test_git_operands_that_escape_the_scratch_directory_are_refused(live_app_data_fence, tmp_path, argv, reason):
    record = _refusal(live_app_data_fence, _fill(argv, _scratch(tmp_path)))
    assert "refused a git child" in record and reason.lower() in record.lower(), record


def test_git_operands_reaching_credential_stores_or_outside_through_links_are_refused(live_app_data_fence, tmp_path):
    fence = live_app_data_fence
    scratch = _scratch(tmp_path)
    (scratch / ".ssh").mkdir()
    (scratch / ".ssh" / "id_synthetic").write_text("synthetic", encoding="utf-8")
    assert "credential storage" in _refusal(fence, ["git", "-C", str(scratch), "add", ".ssh/id_synthetic"])
    outside = Path(os.path.relpath(ROOT.anchor, scratch))  # enough ".." to leave the trusted base entirely
    assert "outside a scratch repository" in _refusal(fence, ["git", "-C", str(scratch), "-C", str(outside),
                                                              "status"])
    # A link inside the scratch directory to a protected root (a disposable decoy, so cleanup can never follow a
    # link into real data) is resolved, not trusted by its spelling.
    decoy = tmp_path / "decoy-live" / "VresOS"
    decoy.mkdir(parents=True)
    (decoy / "config.json").write_text("{}", encoding="utf-8")
    if sys.platform == "win32":
        import _winapi

        _winapi.CreateJunction(str(decoy), str(scratch / "link"))
    else:
        os.symlink(decoy, scratch / "link", target_is_directory=True)
    with fence.protect(decoy):
        assert "protected live data" in _refusal(fence, ["git", "-C", str(scratch), "add", "link/config.json"])
        assert "protected live data" in _refusal(
            fence, ["git", "-C", str(scratch), "worktree", "add", "--detach", "link/wt", "HEAD"])


@pytest.mark.skipif(sys.platform != "win32", reason="drive-relative paths are a Windows form")
def test_a_drive_relative_git_operand_is_refused_as_ambiguous(live_app_data_fence, tmp_path):
    record = _refusal(live_app_data_fence, ["git", "-C", str(_scratch(tmp_path)), "init", "C:escape"])
    assert "ambiguous drive-relative path" in record


@pytest.mark.parametrize("argv", [
    ["git", "-C", "{scratch}", "init", "sub"],
    ["git", "-C", "{scratch}", "init", "-q", "--initial-branch=main"],
    ["git", "-C", "{scratch}", "bundle", "create", "-q", "out.bundle", "--all"],
    ["git", "-C", "{scratch}", "bundle", "verify", "out.bundle"],
    ["git", "-C", "{scratch}", "worktree", "add", "--detach", "wt", "HEAD"],
    ["git", "-C", "{scratch}", "worktree", "add", "-b", "topic", "wt2"],
    ["git", "-C", "{scratch}", "worktree", "list", "--porcelain", "-z"],
    ["git", "-C", "{scratch}", "apply", "--check", "--binary"],
    ["git", "-C", "{scratch}", "hash-object", "-w", "--stdin"],
    ["git", "-C", "{scratch}", "log", "HEAD~1..HEAD"],            # revision ranges are not paths
    ["git", "-C", "{scratch}", "diff", "HEAD~2...HEAD", "--", "f.txt"],
    ["git", "-C", "{scratch}", "show", "HEAD:dir/f.txt"],
    ["git", "-C", "{scratch}", "rev-parse", "--git-path", "hooks"],
    ["git", "-C", "{scratch}", "add", "-A"],
    ["git", "-C", "{scratch}", "add", "f.txt"],
    ["git", "-C", "{scratch}", "checkout", "--", "."],
])
def test_bounded_git_operands_are_permitted(live_app_data_fence, tmp_path, argv):
    scratch = _scratch(tmp_path)
    (scratch / "f.txt").write_text("x", encoding="utf-8")
    _decide(live_app_data_fence, _fill(argv, scratch))


# ---------------------------------------------------------------------------------------------------
# D1-R7: no shell-mediated execution. os.system and friends are refused before a shell exists.
# ---------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("command", [
    "git status && calc", "git status & calc", "git status ; calc", "git log | more", "git status > out.txt",
    "git status 2>&1 >nul", "git status ^& calc", "git status %COMSPEC%", "git status `calc`", "git $(calc)",
    "git --version",
])
def test_os_system_is_refused_whatever_the_command(live_app_data_fence, command):
    with live_app_data_fence.refused() as records:
        live_app_data_fence.check_child("os.system", (command,))
    assert "os.system is refused" in records[0]


@pytest.mark.parametrize("event,args", [
    ("os.startfile", ("calc.exe", None, None, None, None)),
    ("os.spawn", (0, sys.executable, [sys.executable, "-c", "pass"], None)),
    ("os.exec", (sys.executable, [sys.executable, "-c", "pass"], None)),
    ("os.posix_spawn", (sys.executable, [sys.executable, "-c", "pass"], None)),
])
def test_other_shell_and_exec_launch_events_are_refused(live_app_data_fence, event, args):
    with live_app_data_fence.refused() as records:
        live_app_data_fence.check_child(event, args)
    assert f"{event} is refused" in records[0]


def test_a_real_os_system_call_is_refused_before_any_shell_starts(live_app_data_fence, tmp_path):
    marker = tmp_path / "started"
    command = subprocess.list2cmdline([sys.executable, "-I", "-c", f"open({str(marker)!r}, 'w').close()"])
    with live_app_data_fence.refused():
        os.system(command)
    assert not marker.exists()


def test_a_shell_true_subprocess_is_refused_before_it_starts(live_app_data_fence, tmp_path):
    marker = tmp_path / "started"
    command = subprocess.list2cmdline([sys.executable, "-I", "-c", f"open({str(marker)!r}, 'w').close()"])
    with live_app_data_fence.refused() as records:
        subprocess.run(command, shell=True, timeout=120)
    assert not marker.exists()
    assert "unreviewed shell child" in records[0]


@pytest.mark.skipif(sys.platform != "win32", reason="cmd /c is the Windows shell")
def test_the_reviewed_shell_site_admits_only_the_exact_mklink_form(live_app_data_fence, tmp_path):
    fence = live_app_data_fence
    site = "tests/integration/test_secret_safe_onboarding_journey.py"
    comspec = os.environ.get("COMSPEC", "cmd")
    link, target = tmp_path / "junction", tmp_path / "target"
    _decide(fence, ["cmd", "/c", "mklink", "/J", str(link), str(target)], site=site)
    for argv, reason in (
            ([comspec, "/c", "git status && calc"], "only reviewed shell command"),
            (f'{comspec} /c "mklink /J {link} {target} & calc"', "only reviewed shell command"),
            (["cmd", "/c", "mklink", "/J", str(link) + "&calc", str(target)], "plain absolute temporary paths"),
            (["cmd", "/c", "mklink", "/J", str(link), str(ROOT)], "outside the trusted temporary base"),
            (["cmd", "/c", "del", "/q", str(target)], "only reviewed shell command")):
        record = _refusal(fence, argv, site=site)
        assert "refused a shell child" in record and reason in record, record


# ---------------------------------------------------------------------------------------------------
# D1-R8: git reads no system or global configuration, and scratch-repository configuration runs nothing.
# ---------------------------------------------------------------------------------------------------

def test_the_session_git_environment_is_isolated(live_app_data_fence):
    fence = live_app_data_fence
    assert fence.git_isolation == {"GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull, "GIT_EDITOR": ":",
                                   "GIT_PAGER": "cat"}
    for name, value in fence.git_isolation.items():
        assert os.environ[name] == value
    if sys.platform == "win32":
        home = fence.git_home
        assert _norm(os.environ["HOME"]) == _norm(home) and _norm(os.environ["XDG_CONFIG_HOME"]) == _norm(
            home / ".config")
        assert sorted(p.name for p in home.iterdir()) == [".config"] and list((home / ".config").iterdir()) == []
        assert _within(home, fence.trusted_temp_base)


def test_an_explicit_git_environment_is_completed_before_launch(live_app_data_fence, tmp_path):
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith("GIT_")}  # as product code builds it
    _decide(live_app_data_fence, ["git", "-C", str(_scratch(tmp_path)), "status"], env=env)
    assert env["GIT_CONFIG_NOSYSTEM"] == "1" and env["GIT_CONFIG_GLOBAL"] == os.devnull


def test_a_real_git_child_runs_with_the_completed_environment(live_app_data_fence, tmp_path):
    scratch = _scratch(tmp_path)
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith("GIT_")}
    done = subprocess.run(["git", "-C", str(scratch), "init", "-q"], env=env, capture_output=True, timeout=120)
    assert done.returncode == 0, done.stderr
    assert env["GIT_CONFIG_NOSYSTEM"] == "1" and env["GIT_CONFIG_GLOBAL"] == os.devnull


def test_conflicting_or_uncompletable_git_isolation_is_refused(live_app_data_fence, tmp_path, monkeypatch):
    from types import MappingProxyType

    fence = live_app_data_fence
    scratch = str(_scratch(tmp_path))
    synthetic = tmp_path / "synthetic.gitconfig"
    synthetic.write_text("[user]\n\tname = Synthetic\n", encoding="utf-8")
    base_env = {k: v for k, v in os.environ.items() if not k.upper().startswith("GIT_")}
    for env, reason in (({**base_env, "GIT_CONFIG_NOSYSTEM": "0"}, "GIT_CONFIG_NOSYSTEM has an unreviewed value"),
                        ({**base_env, "GIT_CONFIG_GLOBAL": str(synthetic)}, "GIT_CONFIG_GLOBAL has an unreviewed"),
                        (MappingProxyType(base_env), "cannot be completed")):
        assert reason in _refusal(fence, ["git", "-C", scratch, "status"], env=env)
    monkeypatch.delenv("GIT_CONFIG_NOSYSTEM")
    assert "test environment lost GIT_CONFIG_NOSYSTEM" in _refusal(fence, ["git", "-C", scratch, "status"])


def _synthetic_repository(root: Path, config: str = "", hooks: tuple[str, ...] = ()) -> Path:
    """A repository skeleton written directly (no git): only its configuration and hooks matter here."""
    gitdir = root / ".git"
    (gitdir / "hooks").mkdir(parents=True)
    (gitdir / "config").write_text("[core]\n\trepositoryformatversion = 0\n\tbare = false\n" + config,
                                   encoding="utf-8")
    for hook in hooks:
        (gitdir / "hooks" / hook).write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    return root


@pytest.mark.parametrize("config,hooks,reason", [
    ("[core]\n\thooksPath = elsewhere\n", (), "core.hookspath"),
    ("[core]\n\tfsmonitor = calc\n", (), "core.fsmonitor"),
    ("[core]\n\tsshCommand = calc\n", (), "core.sshcommand"),
    ('[filter "lfs"]\n\tclean = calc\n', (), "filter.lfs.clean"),
    ('[diff "x"]\n\ttextconv = calc\n', (), "diff.x.textconv"),
    ('[merge "x"]\n\tdriver = calc\n', (), "merge.x.driver"),
    ("[include]\n\tpath = other.gitconfig\n", (), "include.path"),
    ('[includeIf "gitdir:x"]\n\tpath = other.gitconfig\n', (), "includeif.gitdir:x.path"),
    ("[alias]\n\tco = !calc\n", (), "alias.co"),
    ('[credential]\n\thelper = calc\n', (), "credential.helper"),
    ("", ("pre-commit",), "active git hooks"),
    ("", ("post-checkout", "pre-commit.sample"), "active git hooks"),
])
def test_scratch_repository_configuration_that_could_run_programs_is_refused(live_app_data_fence, tmp_path,
                                                                             config, hooks, reason):
    repo = _synthetic_repository(tmp_path / "repo", config, hooks)
    record = _refusal(live_app_data_fence, ["git", "-C", str(repo), "status"])
    assert "refused a git child" in record and reason in record, record


def test_a_worktree_inherits_the_checks_of_its_common_repository(live_app_data_fence, tmp_path):
    fence = live_app_data_fence
    main = _synthetic_repository(tmp_path / "main", "[core]\n\tfsmonitor = calc\n")
    worktree_gitdir = main / ".git" / "worktrees" / "wt"
    worktree_gitdir.mkdir(parents=True)
    (worktree_gitdir / "commondir").write_text("../..\n", encoding="utf-8")
    worktree = tmp_path / "wt"
    worktree.mkdir()
    (worktree / ".git").write_text(f"gitdir: {worktree_gitdir}\n", encoding="utf-8")
    assert "core.fsmonitor" in _refusal(fence, ["git", "-C", str(worktree), "status"])
    escaped = tmp_path / "escaped"
    escaped.mkdir()
    (escaped / ".git").write_text(f"gitdir: {ROOT / '.git'}\n", encoding="utf-8")
    assert "outside the trusted temporary base" in _refusal(fence, ["git", "-C", str(escaped), "status"])


def test_a_clean_scratch_repository_configuration_is_permitted(live_app_data_fence, tmp_path):
    repo = _synthetic_repository(tmp_path / "repo", '[core]\n\tfsmonitor = false\n\tautocrlf = false\n'
                                                    '[remote "origin"]\n\turl = C:/synthetic/bundle\n'
                                                    '[extensions]\n\tworktreeConfig = true\n',
                                 hooks=("pre-commit.sample", "post-update.sample"))
    assert live_app_data_fence.scratch_repository_problem(str(repo)) is None
    _decide(live_app_data_fence, ["git", "-C", str(repo), "status"])


# ---------------------------------------------------------------------------------------------------
# D1-R9: no git child may sign, verify a signature, open an editor or pager, or run an interactive
# selection. Every refusal below is a decision only (check_child); no such command is ever started.
# ---------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("argv,reason", [
    (["commit", "-S", "-m", "x"], "signs"),
    (["commit", "-SABCDEF", "-m", "x"], "signs"),
    (["commit", "-qS", "-m", "x"], "signs"),
    (["commit", "--gpg-sign", "-m", "x"], "signs"),
    (["commit", "--gpg-sign=ABCDEF", "-m", "x"], "signs"),
    (["commit", "--gpg", "-m", "x"], "signs"),  # an abbreviation git would accept
    (["tag", "-s", "v1", "-m", "x"], "signs"),
    (["tag", "--sign", "v1", "-m", "x"], "signs"),
    (["tag", "-u", "ABCDEF", "v1", "-m", "x"], "signs"),
    (["tag", "--local-user=ABCDEF", "v1", "-m", "x"], "signs"),
    (["tag", "-as", "v1", "-m", "x"], "signs"),
    (["tag", "-v", "v1"], "verifies a signature"),
    (["tag", "--verify", "v1"], "verifies a signature"),
    (["log", "--show-signature"], "verifies a signature"),
    (["log", "--show-sig"], "verifies a signature"),
    (["show", "--show-signature", "HEAD"], "verifies a signature"),
    (["log", "--format=%G?"], "signature placeholder"),
    (["log", "--pretty=format:%H %GS"], "signature placeholder"),
    (["rev-list", "--format=%GK", "HEAD"], "signature placeholder"),
    (["for-each-ref", "--format=%(signature)"], "signature placeholder"),
    (["for-each-ref", "--format", "%(signature:key)"], "signature placeholder"),
    (["commit"], "editor"),
    (["commit", "-q"], "editor"),
    (["commit", "-a"], "editor"),
    (["commit", "--amend"], "editor"),
    (["commit", "-e", "-m", "x"], "editor"),
    (["commit", "--edit", "-m", "x"], "editor"),
    (["commit", "-c", "HEAD"], "editor"),
    (["commit", "--reedit-message=HEAD"], "editor"),
    (["commit", "--no-edit"], "editor"),  # --no-edit keeps a message only when amending
    (["tag", "-a", "v1"], "editor"),
    (["tag", "-a", "-e", "-m", "x", "v1"], "editor"),
    (["branch", "--edit-description"], "editor"),
    (["add", "-e"], "editor"),
    (["add", "--edit"], "editor"),
    (["commit", "-p", "-m", "x"], "interactive"),
    (["commit", "--interactive", "-m", "x"], "interactive"),
    (["add", "-p"], "interactive"),
    (["add", "--patch"], "interactive"),
    (["add", "-i"], "interactive"),
    (["add", "--interactive"], "interactive"),
    (["checkout", "-p"], "interactive"),
    (["checkout", "--patch"], "interactive"),
    (["stash", "-p"], "interactive"),
    (["stash", "push", "-p"], "interactive"),
    (["stash", "save", "--patch"], "interactive"),
    (["commit", "--trailer", "Signed-off-by=x", "-m", "x"], "not reviewed"),  # trailer commands
    (["commit", "--squash=HEAD"], "not reviewed"),
    (["commit", "-v", "-m", "x"], "not reviewed"),
    (["tag", "--cleanup=verbatim", "-e", "v1"], "editor"),
])
def test_git_that_could_sign_verify_or_open_an_editor_is_refused(live_app_data_fence, tmp_path, argv, reason):
    record = _refusal(live_app_data_fence, ["git", "-C", str(_scratch(tmp_path)), *argv])
    assert "refused a git child" in record and reason in record, record


@pytest.mark.parametrize("argv,reason", [
    (["git", "-c", "commit.gpgsign=true", "-C", "{scratch}", "commit", "-m", "x"], "-c commit.gpgsign"),
    (["git", "-c", "tag.gpgsign=false", "-C", "{scratch}", "tag", "v1"], "-c tag.gpgsign"),
    (["git", "-c", "core.editor=calc", "-C", "{scratch}", "status"], "-c core.editor"),
    (["git", "-c", "core.pager=calc", "-C", "{scratch}", "status"], "-c core.pager"),
    (["git", "-C", "{scratch}", "config", "commit.gpgsign", "true"], "commit.gpgsign only to false"),
    (["git", "-C", "{scratch}", "config", "commit.gpgSign", "yes"], "commit.gpgsign only to false"),
    (["git", "-C", "{scratch}", "config", "tag.gpgSign", "true"], "may not set tag.gpgsign"),
    (["git", "-C", "{scratch}", "config", "--edit"], "config --edit"),
])
def test_git_settings_that_enable_signing_or_programs_are_refused(live_app_data_fence, tmp_path, argv, reason):
    record = _refusal(live_app_data_fence, _fill(argv, _scratch(tmp_path)))
    assert "refused a git child" in record and reason in record, record


@pytest.mark.parametrize("config,reason", [
    ("[commit]\n\tgpgSign = true\n", "commit.gpgsign"),
    ("[commit]\n\tgpgsign\n", "commit.gpgsign"),  # a bare boolean key is true
    ("[tag]\n\tgpgSign = true\n", "tag.gpgsign"),
    ("[tag]\n\tforceSignAnnotated = true\n", "tag.forcesignannotated"),
    ("[log]\n\tshowSignature = true\n", "log.showsignature"),
    ("[merge]\n\tverifySignatures = true\n", "merge.verifysignatures"),
    ("[gpg]\n\tprogram = calc\n", "gpg.program"),
    ("[gpg]\n\tformat = ssh\n", "gpg.format"),
    ('[gpg "ssh"]\n\tdefaultKeyCommand = calc\n', "gpg.ssh.defaultkeycommand"),
    ("[core]\n\teditor = calc\n", "core.editor"),
    ("[core]\n\tpager = calc\n", "core.pager"),
    ("[core]\n\tfsmonitor\n", "core.fsmonitor"),  # bare: true, the built-in daemon
    ("[sequence]\n\teditor = calc\n", "sequence.editor"),
    ("[diff]\n\texternal = calc\n", "diff.external"),
    ('[difftool "x"]\n\tcmd = calc\n', "difftool.x.cmd"),
    ('[trailer "x"]\n\tcommand = calc\n', "trailer.x.command"),
    ("[interactive]\n\tdiffFilter = calc\n", "interactive.difffilter"),
    ("[pretty]\n\tsig = format:%G?\n", "pretty.sig"),
    ('[hook "x"]\n\tcommand = calc\n', "hook.x.command"),
    ("[core]\n\talternateRefsCommand = calc\n", "core.alternaterefscommand"),
])
def test_scratch_configuration_that_signs_or_runs_programs_is_refused(live_app_data_fence, tmp_path, config,
                                                                      reason):
    repo = _synthetic_repository(tmp_path / "repo", config)
    record = _refusal(live_app_data_fence, ["git", "-C", str(repo), "commit", "-q", "-m", "x"])
    assert "refused a git child" in record and f"configuration sets {reason}" in record, record


def test_scratch_configuration_that_disables_signing_is_permitted(live_app_data_fence, tmp_path):
    repo = _synthetic_repository(tmp_path / "repo", "[commit]\n\tgpgSign = false\n[tag]\n\tgpgSign = 0\n"
                                                    "\tforceSignAnnotated = no\n[log]\n\tshowSignature = off\n"
                                                    "[user]\n\tname = Synthetic\n\tsigningKey = ABCDEF\n")
    assert live_app_data_fence.scratch_repository_problem(str(repo)) is None
    _decide(live_app_data_fence, ["git", "-C", str(repo), "commit", "-q", "-m", "x"])


@pytest.mark.parametrize("argv", [
    ["commit", "-q", "-m", "x"],
    ["commit", "-m", "x", "--allow-empty"],
    ["commit", "-qm", "x"],
    ["commit", "-am", "x"],
    ["commit", "-m-S"],  # the message is "-S", not a signing option
    ["commit", "--message=x", "--no-gpg-sign"],
    ["commit", "-F", "msg.txt"],
    ["commit", "--file=msg.txt", "--cleanup=verbatim"],
    ["commit", "--amend", "--no-edit"],
    ["commit", "--amend", "-m", "x", "--no-verify"],
    ["commit", "-C", "HEAD", "--reset-author"],
    ["commit", "-q", "--author=Synthetic <s@example.invalid>", "--date=2026-01-01T00:00:00", "-m", "x"],
    ["commit", "-m", "100%G proof", "--", "f.txt"],  # a message is not a format
    ["tag", "v1"],
    ["tag", "v1", "HEAD"],
    ["tag", "-f", "v1"],
    ["tag", "-d", "tag00000"],
    ["tag", "-a", "v1", "-m", "x"],
    ["tag", "-am", "x", "v1"],
    ["tag", "--no-sign", "-F", "msg.txt", "v1"],
    ["tag", "-l"],
    ["tag", "--list", "--sort=refname", "v*"],
    ["log", "--oneline"],
    ["log", "--format=%H%x00%s", "-n", "1"],
    ["log", "--no-show-signature", "-p"],
    ["show", "--stat", "HEAD"],
    ["rev-list", "--format=%H", "HEAD"],
    ["for-each-ref", "--sort=refname", "refs/"],
    ["for-each-ref", "--format=%(refname) %(objectname)"],
    ["branch", "--show-current"],
    ["branch", "feature"],
    ["add", "-A"],
    ["add", "-f", "f.txt"],
    ["add", "-u"],
    ["add", "--", "f.txt"],
    ["checkout", "--", "."],
    ["checkout", "--detach"],
    ["checkout", "-q", "-b", "topic"],
    ["stash"],
    ["stash", "push", "-u", "-m", "test stash"],
    ["stash", "save", "message"],
    ["stash", "list"],
    ["stash", "show", "-p"],
    ["stash", "pop"],
])
def test_noninteractive_unsigned_git_operations_are_permitted(live_app_data_fence, tmp_path, argv):
    scratch = _scratch(tmp_path)
    (scratch / "msg.txt").write_text("synthetic message\n", encoding="utf-8")
    (scratch / "f.txt").write_text("x", encoding="utf-8")
    _decide(live_app_data_fence, ["git", "-C", str(scratch), *argv])


def test_git_children_get_no_editor_and_no_pager(live_app_data_fence, tmp_path):
    fence = live_app_data_fence
    assert fence.git_isolation["GIT_EDITOR"] == ":" and fence.git_isolation["GIT_PAGER"] == "cat"
    assert os.environ["GIT_EDITOR"] == ":" and os.environ["GIT_PAGER"] == "cat"
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith("GIT_")}
    _decide(fence, ["git", "-C", str(_scratch(tmp_path)), "status"], env=env)
    assert env["GIT_EDITOR"] == ":" and env["GIT_PAGER"] == "cat"
    for name, value in (("GIT_EDITOR", "calc"), ("GIT_PAGER", "less")):
        record = _refusal(fence, ["git", "-C", str(_scratch(tmp_path)), "status"], env={**env, name: value})
        assert f"{name} has an unreviewed value" in record


def test_a_real_noninteractive_scratch_commit_and_annotated_tag_still_work(live_app_data_fence, tmp_path):
    scratch = _scratch(tmp_path)
    identity = ["-c", "user.name=t", "-c", "user.email=t@example.invalid", "-c", "commit.gpgsign=false"]

    def git(*args):
        return subprocess.run(["git", *identity, "-C", str(scratch), *args], check=True, capture_output=True,
                              text=True, timeout=120).stdout

    git("init", "-q")
    (scratch / "f.txt").write_text("x", encoding="utf-8")
    git("add", "-A")
    git("commit", "-qm", "first")
    git("commit", "--amend", "--no-edit", "-q")
    git("tag", "-a", "v1", "-m", "release")
    assert git("for-each-ref", "--format=%(objecttype) %(refname)", "refs/tags/").split() == ["tag", "refs/tags/v1"]
    assert git("log", "--format=%s").split() == ["first"]
