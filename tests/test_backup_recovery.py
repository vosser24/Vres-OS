"""P2-C backup and recovery, offline: disposable temp directories, a synthetic Claude home,
simulated PostgreSQL client runs and the P2-A1 guard over a private approval registry.
No real PostgreSQL client, installer, credential store or Claude configuration is used.
"""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from types import SimpleNamespace

import pytest

from vres_os import database_targets, install_recovery, pg_recovery, state_backup
from vres_os.db import DatabaseTargetRefused
from vres_os.install_recovery import InstallRecoveryError
from vres_os.pg_recovery import DatabaseRecoveryError
from vres_os.state_backup import StateBackupError

_ROOT = Path(__file__).resolve().parents[1]


def _tripwire(name):
    def fired(*_a, **_kw):
        pytest.fail(f"side effect reached: {name}")

    return fired


@pytest.fixture(autouse=True)
def _no_libpq_routing(monkeypatch):
    for name in database_targets.ROUTING_ENVIRONMENT:
        monkeypatch.delenv(name, raising=False)


# ---------------------------------------------------------------------------------------------- state backup

def _state(root: Path) -> Path:
    root.mkdir(parents=True)
    (root / "config.json").write_text(json.dumps({"configured": True, "database": {
        "password_key": "postgres.default", "migration_user": "vres_migrator",
        "migration_password_key": "postgres.migration", "provenance_writer_user": ""}}), encoding="utf-8")
    (root / "credential-resources.json").write_text(json.dumps({
        "version": 1, "user_namespace": "user-namespace-0123456789", "bindings": {}, "pending_captures": {},
        "resources": {"github": {"fields": ["token"], "service_type": "github", "origin": "o", "account": "a",
                                 "created_at": "t", "updated_at": "t"}}}), encoding="utf-8")
    (root / "database-targets.json").write_text('{"version": 1, "approved": [], "held": []}', encoding="utf-8")
    (root / "active-install.json").write_text('{"release": "R0"}', encoding="utf-8")
    for excluded in ("logs/hook-errors.log", "runtime/x.lock", "releases/R0/venv/x.py", "bin/vres.cmd",
                     "backups/R0/plugin.json", "config.json.abc.tmp", "installation.lock"):
        (root / excluded).parent.mkdir(parents=True, exist_ok=True)
        (root / excluded).write_text("not state", encoding="utf-8")
    return root


@pytest.fixture
def backed_up(tmp_path):
    source = _state(tmp_path / "VresOS")
    protected = []
    result = state_backup.create_backup(source, tmp_path / "backup-1", protect=protected.append)
    return SimpleNamespace(source=source, backup=tmp_path / "backup-1", result=result, protected=protected)


def test_valid_state_backup_has_exact_files_versioned_manifest_and_owner_protection(backed_up):
    manifest = json.loads((backed_up.backup / "manifest.json").read_text())

    assert backed_up.result["status"] == "complete"
    assert sorted(p.name for p in backed_up.backup.iterdir()) == [
        "active-install.json", "config.json", "credential-resources.json", "database-targets.json", "manifest.json"]
    assert (manifest["format"], manifest["version"], manifest["complete"]) == ("vres-state-backup", 2, True)
    assert {f["path"]: f["category"] for f in manifest["files"]}["database-targets.json"] == "evidence"
    assert {f["path"]: f["category"] for f in manifest["files"]}["active-install.json"] == "evidence"
    assert all(len(f["sha256"]) == 64 for f in manifest["files"])
    assert any("Credential Locker" in item for item in manifest["excluded"])
    assert len(backed_up.protected) == 1 and backed_up.protected[0].name.startswith(".backup-1.incomplete-")
    assert not list(backed_up.backup.parent.glob(".backup-1.incomplete-*"))  # staging renamed into place


@pytest.mark.parametrize("where", ["existing", "inside"])
def test_backup_never_overwrites_and_never_lands_inside_the_managed_directory(backed_up, where):
    destination = backed_up.backup if where == "existing" else backed_up.source / "my-backup"
    before = sorted(p.name for p in backed_up.backup.iterdir())

    with pytest.raises(StateBackupError, match="already exists|outside the managed"):
        state_backup.create_backup(backed_up.source, destination, protect=lambda _p: None)
    assert sorted(p.name for p in backed_up.backup.iterdir()) == before


def test_backup_refuses_an_ambiguous_file_type(tmp_path):
    source = _state(tmp_path / "VresOS")
    (source / "config.json").unlink()
    (source / "config.json").mkdir()

    with pytest.raises(StateBackupError, match="not an ordinary file"):
        state_backup.create_backup(source, tmp_path / "b", protect=lambda _p: None)
    assert not (tmp_path / "b").exists()


def test_backup_refuses_a_link_in_place_of_a_state_file(tmp_path):
    source = _state(tmp_path / "VresOS")
    (source / "config.json").unlink()
    try:
        (source / "config.json").symlink_to(tmp_path / "elsewhere.json")
    except OSError:
        pytest.skip("symbolic links are not available on this host")

    with pytest.raises(StateBackupError, match="link"):
        state_backup.create_backup(source, tmp_path / "b", protect=lambda _p: None)


@pytest.mark.parametrize("damage", ["altered", "missing", "extra", "escape-path", "unknown-path"])
def test_altered_or_missing_backup_data_is_rejected(backed_up, damage):
    manifest_path = backed_up.backup / "manifest.json"
    if damage == "altered":
        (backed_up.backup / "config.json").write_text('{"configured": false}')
    elif damage == "missing":
        (backed_up.backup / "credential-resources.json").unlink()
    elif damage == "extra":
        (backed_up.backup / "notes.txt").write_text("x")
    else:
        manifest = json.loads(manifest_path.read_text())
        manifest["files"][0]["path"] = "..\\..\\config.json" if damage == "escape-path" else "settings.json"
        manifest_path.write_text(json.dumps(manifest))

    with pytest.raises(StateBackupError):
        state_backup.verify_backup(backed_up.backup)
    with pytest.raises(StateBackupError):
        state_backup.restore_backup(backed_up.backup, backed_up.source, replace_existing=True,
                                    presence=_tripwire("credential presence"))


def test_partial_backup_is_never_accepted(tmp_path, monkeypatch):
    source = _state(tmp_path / "VresOS")
    real = state_backup._write_atomic
    monkeypatch.setattr(state_backup, "_write_atomic", lambda *_a: (_ for _ in ()).throw(OSError("disk full")))

    with pytest.raises(OSError):
        state_backup.create_backup(source, tmp_path / "b", protect=lambda _p: None)
    monkeypatch.setattr(state_backup, "_write_atomic", real)

    assert not (tmp_path / "b").exists()
    staging = next(tmp_path.glob(".b.incomplete-*"))
    with pytest.raises(StateBackupError, match="no manifest"):
        state_backup.verify_backup(staging)
    manifest = {"format": "vres-state-backup", "version": 1, "complete": False, "files": []}
    (staging / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(StateBackupError, match="incomplete"):
        state_backup.verify_backup(staging)


def test_restore_writes_only_owned_restorable_files(backed_up, tmp_path):
    target = tmp_path / "fresh"
    target.mkdir()

    result = state_backup.restore_backup(backed_up.backup, target, presence=lambda _k: True)

    assert result["status"] == "restored"
    assert sorted(p.name for p in target.iterdir() if p.is_file()) == [
        "config.json", "credential-resources.json"]  # evidence (incl. the P2-A1 registry) never restored
    assert not (target / "active-install.json").exists()
    assert {p.name for p in target.iterdir() if p.is_dir()} == {"restore-points"}


def test_restore_does_not_replace_existing_state_without_an_explicit_decision(backed_up):
    (backed_up.source / "config.json").write_text('{"configured": false}')
    before = (backed_up.source / "config.json").read_bytes()

    with pytest.raises(StateBackupError, match="explicit replace decision"):
        state_backup.restore_backup(backed_up.backup, backed_up.source, presence=_tripwire("presence"))
    assert (backed_up.source / "config.json").read_bytes() == before
    assert not (backed_up.source / "restore-points").exists()


def test_failure_during_restore_rolls_back_and_keeps_recovery_evidence(backed_up, monkeypatch):
    for name in ("config.json", "credential-resources.json"):
        (backed_up.source / name).write_text(f'"changed {name}"')
    before = {n: (backed_up.source / n).read_bytes() for n in state_backup.RESTORABLE if (backed_up.source / n).exists()}
    real, calls = state_backup._write_atomic, []

    def flaky(path, data):
        calls.append(path.name)
        if path.name == "credential-resources.json" and calls.count(path.name) == 1:
            raise OSError("simulated power loss")
        return real(path, data)

    monkeypatch.setattr(state_backup, "_write_atomic", flaky)

    with pytest.raises(StateBackupError, match="rolled back"):
        state_backup.restore_backup(backed_up.backup, backed_up.source, replace_existing=True,
                                    presence=_tripwire("presence"))
    after = {n: (backed_up.source / n).read_bytes() for n in state_backup.RESTORABLE if (backed_up.source / n).exists()}
    assert after == before
    assert not (backed_up.source / "restore-journal.json").exists()
    assert len(list((backed_up.source / "restore-points").iterdir())) == 1  # evidence kept


def test_interrupted_restore_blocks_further_restores_until_recovered(backed_up, monkeypatch):
    (backed_up.source / "config.json").write_text('"local edit"')
    before = (backed_up.source / "config.json").read_bytes()
    real_write, real_recover = state_backup._write_atomic, state_backup.recover_restore

    def crash(path, data):
        if path.name == "config.json":
            real_write(path, data)  # the new file landed, then the process "died"
            raise KeyboardInterrupt
        return real_write(path, data)

    monkeypatch.setattr(state_backup, "_write_atomic", crash)
    monkeypatch.setattr(state_backup, "recover_restore", lambda _root: (_ for _ in ()).throw(OSError("dead")))
    with pytest.raises(StateBackupError, match="journal and recovery point were kept"):
        state_backup.restore_backup(backed_up.backup, backed_up.source, replace_existing=True,
                                    presence=_tripwire("presence"))
    monkeypatch.setattr(state_backup, "_write_atomic", real_write)
    monkeypatch.setattr(state_backup, "recover_restore", real_recover)

    assert (backed_up.source / "restore-journal.json").exists()
    with pytest.raises(StateBackupError, match="interrupted restore journal"):
        state_backup.restore_backup(backed_up.backup, backed_up.source, replace_existing=True,
                                    presence=_tripwire("credential presence"))
    result = state_backup.recover_restore(backed_up.source)

    assert result["status"] == "rolled_back"
    assert (backed_up.source / "config.json").read_bytes() == before
    assert not (backed_up.source / "restore-journal.json").exists()


def test_missing_credential_locker_values_are_reported_never_fabricated(backed_up, tmp_path):
    target = tmp_path / "fresh"
    target.mkdir()
    asked = []

    def presence(key):
        asked.append(key)
        return key == "postgres.default"

    result = state_backup.restore_backup(backed_up.backup, target, presence=presence)

    assert asked == ["postgres.default", "postgres.migration", "credential:user-namespace-0:github:token"]
    assert result["credentials_missing"] == ["postgres.migration", "credential:user-namespace-0:github:token"]
    assert {c["status"] for c in result["credentials"]} == {"present", "missing"}
    restored = b"".join((target / n).read_bytes() for n in state_backup.RESTORABLE if (target / n).exists())
    assert b"password\":" not in restored.lower()


# ------------------------------------------------------------------------------------- installer recovery

def _plugin(path: Path, version: str, *, managed=True):
    path.mkdir(parents=True)
    (path / "plugin.json").write_text(json.dumps({"version": version}))
    if managed:
        (path / ".vres-managed").write_text("Vres-OS")


@pytest.fixture
def interrupted_install(tmp_path):
    """A synthetic Claude home and install root, interrupted after every installer mutation."""
    root, home = tmp_path / "VresOS", tmp_path / "claude"
    (root / "bin").mkdir(parents=True)
    (root / "backups").mkdir()
    (root / "bin" / "vres.cmd").write_bytes(b"@echo old\r\n")
    (root / "active-install.json").write_text(json.dumps({"product": "Vres-OS", "release": "R0"}))
    home.mkdir()
    (home / "CLAUDE.md").write_bytes(b"\xef\xbb\xbfMy own global notes\r\n")
    (home / "settings.json").write_bytes(b'{"theme": "dark", "model": "sonnet"}')
    (home / ".credentials.json").write_bytes(b'{"claudeAiOauth": "native-auth-material"}')
    _plugin(home / "skills" / "other-plugin", "1", managed=False)
    _plugin(home / "skills" / "vres-os", "R0")
    original = {p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}

    install_recovery.snapshot(root, home, "R1")
    journal = {"product": "Vres-OS", "new_release": "R1", "previous": {"product": "Vres-OS", "release": "R0"},
               "plugin_backup": str(root / "backups" / "R1"), "plugin_path": str(home / "skills" / "vres-os"),
               "had_plugin": True, "claude_snapshot": str(root / "install-recovery" / "R1"), "claude_home": str(home)}
    (root / "pending-install.json").write_text(json.dumps(journal))
    # The installer's mutations, then an abrupt stop (no catch block ran).
    shutil.move(str(home / "skills" / "vres-os"), str(root / "backups" / "R1"))
    _plugin(home / "skills" / "vres-os", "R1")
    (root / "bin" / "vres.cmd").write_bytes(b"@echo new\r\n")
    (root / "bin" / "vres-mcp.cmd").write_bytes(b"@echo new mcp\r\n")
    (root / "active-install.json").write_text(json.dumps({"product": "Vres-OS", "release": "R1"}))
    (home / "CLAUDE.md").write_bytes(b"\xef\xbb\xbfMy own global notes\r\n<!-- vres -->\r\n")
    (home / "vres-rules.md").write_bytes(b"rules")
    (home / "settings.json").write_bytes(b'{"theme": "dark", "model": "sonnet", "statusLine": {}}')
    return SimpleNamespace(root=root, home=home, base=tmp_path, original=original)


def test_interrupted_install_recovers_exactly_from_the_persisted_snapshot(interrupted_install):
    env = interrupted_install
    plan = install_recovery.inspect(env.root)

    assert plan["recoverable"] is True and plan["refusals"] == []
    assert [a["action"] for a in plan["actions"]] == [
        "restore_active_pointer", "restore_plugin_from_backup", "restore_launchers",
        "restore_claude_file", "restore_claude_file", "restore_claude_file", "remove_journal"]
    with pytest.raises(InstallRecoveryError, match="explicit confirmation"):
        install_recovery.recover(env.root, confirm=False)

    result = install_recovery.recover(env.root, confirm=True)

    now = {p.relative_to(env.base): p.read_bytes() for p in env.base.rglob("*") if p.is_file()
           if "install-recovery" not in p.parts}
    assert now == env.original  # every byte back, including BOM/CRLF, and no extra files
    assert result["status"] == "recovered"
    kept = Path(result["pre_recovery_copy"])
    assert b"<!-- vres -->" in (kept / "claude" / "CLAUDE.md").read_bytes()  # interrupted state preserved too


def test_recovery_never_touches_native_claude_authentication_or_other_plugins(interrupted_install):
    env = interrupted_install
    auth = env.home / ".credentials.json"
    other = env.home / "skills" / "other-plugin" / "plugin.json"
    auth_before, other_before = auth.read_bytes(), other.read_bytes()

    install_recovery.recover(env.root, confirm=True)

    assert auth.read_bytes() == auth_before and other.read_bytes() == other_before
    snapshot_names = {p.name for p in (env.root / "install-recovery" / "R1").rglob("*") if p.is_file()}
    assert ".credentials.json" not in snapshot_names and "plugin.json" not in snapshot_names


@pytest.mark.parametrize("ambiguity", ["unmanaged-plugin", "third-release", "tampered-snapshot", "old-journal"])
def test_ambiguous_recovery_is_refused_without_any_change(interrupted_install, ambiguity):
    env = interrupted_install
    if ambiguity == "unmanaged-plugin":
        (env.home / "skills" / "vres-os" / ".vres-managed").unlink()
    elif ambiguity == "third-release":
        (env.root / "active-install.json").write_text(json.dumps({"release": "R9"}))
    elif ambiguity == "tampered-snapshot":
        (env.root / "install-recovery" / "R1" / "claude" / "settings.json").write_bytes(b"{}")
    else:
        journal = json.loads((env.root / "pending-install.json").read_text())
        del journal["claude_snapshot"]
        (env.root / "pending-install.json").write_text(json.dumps(journal))
    before = {p: p.read_bytes() for p in env.base.rglob("*") if p.is_file()}

    plan = install_recovery.inspect(env.root)
    assert plan["recoverable"] is False and plan["refusals"]
    with pytest.raises(InstallRecoveryError, match="refused"):
        install_recovery.recover(env.root, confirm=True)
    assert {p: p.read_bytes() for p in env.base.rglob("*") if p.is_file()} == before


def test_interruption_right_after_the_journal_only_clears_the_journal(tmp_path):
    root, home = tmp_path / "VresOS", tmp_path / "claude"
    root.mkdir()
    (root / "backups").mkdir()
    (home / "skills").mkdir(parents=True)  # the installer creates both parents before writing the journal
    (home / "settings.json").write_bytes(b"{}")
    install_recovery.snapshot(root, home, "R1")
    (root / "pending-install.json").write_text(json.dumps({
        "product": "Vres-OS", "new_release": "R1", "previous": None, "plugin_backup": str(root / "backups" / "R1"),
        "plugin_path": str(home / "skills" / "vres-os"), "had_plugin": False,
        "claude_snapshot": str(root / "install-recovery" / "R1"), "claude_home": str(home)}))

    assert [a["action"] for a in install_recovery.inspect(root)["actions"]] == ["remove_journal"]
    install_recovery.recover(root, confirm=True)
    assert not (root / "pending-install.json").exists() and (home / "settings.json").read_bytes() == b"{}"


def test_snapshot_is_never_overwritten_and_the_installer_takes_it_before_any_mutation(tmp_path):
    root, home = tmp_path / "VresOS", tmp_path / "claude"
    root.mkdir()
    home.mkdir()
    install_recovery.snapshot(root, home, "R1")
    with pytest.raises(InstallRecoveryError, match="already exists"):
        install_recovery.snapshot(root, home, "R1")

    installer = (_ROOT / "install.ps1").read_text(encoding="utf-8")
    snap = installer.index("install_recovery.py'),'snapshot'")
    assert snap < installer.index("Write-JsonAtomic (Join-Path $InstallRoot 'pending-install.json')")
    assert snap < installer.index("Move-Item -LiteralPath $PluginTarget")
    assert snap < installer.index("'install-global'")
    assert "claude_snapshot=$ClaudeSnapshot; claude_home=$ClaudeHome" in installer


# -------------------------------------------------------------------------------------------- PostgreSQL

_TOC = ";\n; Archive\n;\n10; 2615 16400 SCHEMA - vres owner\n" \
       "20; 1259 16401 TABLE vres schema_migrations owner\n21; 1259 16402 TABLE vres tasks owner\n" \
       "30; 0 16401 TABLE DATA vres schema_migrations owner\n"


class _Client:
    """Simulated pg_dump/pg_restore. Records argv and env; never runs anything."""

    def __init__(self, *, dump_rc=0, list_rc=0, listing=_TOC, restore_rc=0, partial_on_failure=False, raises=None):
        self.calls, self.dump_rc, self.list_rc, self.listing, self.restore_rc = [], dump_rc, list_rc, listing, restore_rc
        self.partial_on_failure, self.raises = partial_on_failure, raises

    def __call__(self, argv, env):
        self.calls.append((argv, env))
        if self.raises:
            raise self.raises
        tool = Path(argv[0]).stem
        if tool == "pg_dump":
            target = Path(next(a for a in argv if a.startswith("--file="))[7:])
            if self.dump_rc == 0 or self.partial_on_failure:
                target.write_bytes(b"PGDMP-simulated-archive" if self.dump_rc == 0 else b"PGDMP-trunc")
            return SimpleNamespace(returncode=self.dump_rc, stdout="", stderr="pg_dump: error: password=hunter2 rejected")
        if "--list" in argv:
            return SimpleNamespace(returncode=self.list_rc, stdout=self.listing, stderr="")
        return SimpleNamespace(returncode=self.restore_rc, stdout="", stderr="pg_restore: error: role missing")


_BIN: dict[str, Path] = {}


@pytest.fixture(autouse=True)
def _trusted_client_bin(tmp_path_factory):
    """A synthetic trusted PostgreSQL bin directory (empty placeholder files; nothing is ever executed)."""
    program_files = tmp_path_factory.mktemp("ProgramFiles")
    bin_dir = program_files / "PostgreSQL" / "16" / "bin"
    bin_dir.mkdir(parents=True)
    for exe in ("pg_dump.exe", "pg_restore.exe"):
        (bin_dir / exe).write_bytes(b"")
    _BIN.update(program_files=program_files, bin=bin_dir)


def _backup(tmp_path, client, **overrides):
    protected = overrides.pop("protected", [])
    args = dict(host="localhost", port=5432, dbname="vres_os", user="vres_migrator", sslmode="prefer",
                output=tmp_path / "vres.dump", password_provider=lambda: "synthetic-pw",
                runner=client, client_dir=lambda: _BIN["bin"], protect=protected.append)
    args.update(overrides)
    return pg_recovery.backup_database(**args)


@pytest.mark.parametrize("state", ["unknown", "held", "libpq-routing-env"])
def test_database_backup_refuses_unknown_or_quarantined_targets_before_any_process(
    tmp_path, approve_database_target, monkeypatch, state
):
    if state != "unknown":
        approve_database_target(("localhost", 5432, "vres_os"))
    if state == "held":
        database_targets.hold_target("127.0.0.1", 5432, reason="schema-048 incident")
    if state == "libpq-routing-env":
        monkeypatch.setenv("PGHOST", "elsewhere")

    with pytest.raises(DatabaseTargetRefused):
        _backup(tmp_path, _tripwire("client process"), password_provider=_tripwire("credential"),
                client_dir=_tripwire("client resolution"))
    assert list(tmp_path.iterdir()) == []


def test_verified_backup_writes_protected_archive_and_manifest_without_exposing_the_password(
    tmp_path, approve_database_target
):
    approve_database_target(("localhost", 5432, "vres_os"))
    client, protected = _Client(), []

    result = _backup(tmp_path, client, protected=protected)

    assert result["status"] == "verified_archive" and result["toc"] == {"entries": 4, "vres_tables": 2, "ledger": 1}
    manifest = json.loads((tmp_path / "vres.dump.manifest.json").read_text())
    assert manifest["sha256"] == pg_recovery._sha256_file(tmp_path / "vres.dump")
    assert protected[0].name.startswith(".vres.dump.partial-")
    assert protected[1].name.startswith(".vres.dump.manifest.json.partial-")  # protected before publication
    assert sorted(p.name for p in tmp_path.iterdir()) == ["vres.dump", "vres.dump.manifest.json"]
    assert client.calls[0][0][0] == str(_BIN["bin"] / "pg_dump.exe")  # the verified absolute client
    for argv, env in client.calls:
        assert not any("synthetic-pw" in a for a in argv)
        assert not any(k.upper().startswith("PG") and k != "PGPASSWORD" for k in env)
    assert client.calls[0][1]["PGPASSWORD"] == "synthetic-pw" and "PGPASSWORD" not in client.calls[1][1]
    assert "synthetic-pw" not in json.dumps(result) + json.dumps(manifest)


@pytest.mark.parametrize(
    "client,message",
    [(_Client(dump_rc=1), "pg_dump failed"), (_Client(dump_rc=1, partial_on_failure=True), "pg_dump failed"),
     (_Client(list_rc=1), "Archive verification"),
     (_Client(listing="; nothing\n10; 2615 1 SCHEMA - public o\n"), "migration ledger"),
     (_Client(raises=__import__("subprocess").TimeoutExpired("pg_dump", 1)), "timed out")],
    ids=["dump-fails", "partial-archive-then-nonzero", "listing-fails", "not-a-vres-archive", "timeout"],
)
def test_simulated_client_failure_never_yields_a_backup_pass(tmp_path, approve_database_target, client, message):
    approve_database_target(("localhost", 5432, "vres_os"))

    with pytest.raises(DatabaseRecoveryError, match=message) as exc:
        _backup(tmp_path, client)
    assert "hunter2" not in str(exc.value)
    assert list(tmp_path.iterdir()) == []  # the attempt's own partial archive was removed; nothing else exists


def test_unverifiable_partial_cleanup_reports_the_residue_and_never_succeeds(tmp_path, approve_database_target,
                                                                             monkeypatch):
    approve_database_target(("localhost", 5432, "vres_os"))
    real_unlink = Path.unlink

    def stuck(self, *args, **kwargs):
        if ".partial-" in self.name:
            raise PermissionError("file in use")
        return real_unlink(self, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", stuck)

    with pytest.raises(DatabaseRecoveryError, match="Residual files could not be removed; delete them manually"):
        _backup(tmp_path, _Client(dump_rc=1, partial_on_failure=True))
    assert not (tmp_path / "vres.dump").exists() and not (tmp_path / "vres.dump.manifest.json").exists()


def test_credential_failure_after_the_partial_is_created_still_cleans_up(tmp_path, approve_database_target):
    approve_database_target(("localhost", 5432, "vres_os"))

    def no_credential():
        raise RuntimeError("credential store unavailable")

    with pytest.raises(DatabaseRecoveryError, match="Backup failed"):
        _backup(tmp_path, _tripwire("client process"), password_provider=no_credential)
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("layout", ["no-postgresql", "path-only-client", "junction-version", "missing-restore"])
def test_untrusted_postgresql_clients_refuse_before_any_credential(tmp_path, approve_database_target, monkeypatch,
                                                                   layout):
    approve_database_target(("localhost", 5432, "vres_os"))
    program_files = tmp_path / "ProgramFiles"
    program_files.mkdir()
    if layout == "path-only-client":
        rogue = tmp_path / "project-bin"
        rogue.mkdir()
        (rogue / "pg_dump.exe").write_bytes(b"")
        monkeypatch.setenv("PATH", str(rogue))
    elif layout == "junction-version":
        _winapi = pytest.importorskip("_winapi")
        if not hasattr(_winapi, "CreateJunction"):
            pytest.skip("Windows directory junction")

        real = tmp_path / "real16"
        (real / "bin").mkdir(parents=True)
        for exe in ("pg_dump.exe", "pg_restore.exe"):
            (real / "bin" / exe).write_bytes(b"")
        (program_files / "PostgreSQL").mkdir()
        _winapi.CreateJunction(str(real), str(program_files / "PostgreSQL" / "16"))
    elif layout == "missing-restore":
        (program_files / "PostgreSQL" / "16" / "bin").mkdir(parents=True)
        (program_files / "PostgreSQL" / "16" / "bin" / "pg_dump.exe").write_bytes(b"")
    monkeypatch.setattr(pg_recovery, "_program_files", lambda: program_files)
    output = tmp_path / "out"
    output.mkdir()

    with pytest.raises(DatabaseRecoveryError, match="trusted|missing or not ordinary"):
        _backup(output, _tripwire("client process"), password_provider=_tripwire("credential"),
                client_dir=pg_recovery.trusted_client_dir)
    assert list(output.iterdir()) == []


def test_trusted_client_resolution_picks_the_highest_installed_major(tmp_path, monkeypatch):
    for major in ("15", "17", "notaversion"):
        (tmp_path / "PostgreSQL" / major / "bin").mkdir(parents=True)
        for exe in ("pg_dump.exe", "pg_restore.exe"):
            (tmp_path / "PostgreSQL" / major / "bin" / exe).write_bytes(b"")
    monkeypatch.setattr(pg_recovery, "_program_files", lambda: tmp_path)

    assert pg_recovery.trusted_client_dir() == tmp_path / "PostgreSQL" / "17" / "bin"


@pytest.fixture
def archive(tmp_path, approve_database_target):
    approve_database_target(("localhost", 5432, "vres_os"), ("localhost", 5432, "vres_restore_check1"))
    _backup(tmp_path, _Client())
    return tmp_path / "vres.dump"


def _empty(conninfo, dbname, password):
    return {"empty": True, "found": {}, "reason": None}


def _restore(archive, client, **overrides):
    args = dict(archive=archive, host="localhost", port=5432, dbname="vres_restore_check1", user="vres_migrator",
                sslmode="prefer", confirmation="RESTORE vres_restore_check1", password_provider=lambda: "synthetic-pw",
                production=("localhost", 5432, "vres_os"), runner=client, client_dir=lambda: _BIN["bin"],
                inspector=_empty, verifier=lambda conninfo, manifest, password: {"ok": True})
    args.update(overrides)
    return pg_recovery.restore_database(**args)


@pytest.mark.parametrize(
    "overrides,error",
    [
        ({"dbname": "vres_os"}, DatabaseRecoveryError),  # the configured production database
        ({"dbname": "customer_erp"}, DatabaseRecoveryError),  # not a disposable recovery database
        ({"dbname": "vres_restore_unapproved"}, DatabaseTargetRefused),
        ({"confirmation": "yes"}, DatabaseRecoveryError),
        ({"production": ("localhost", 5432, "vres_restore_check1")}, DatabaseRecoveryError),
        ({"client_dir": lambda: Path("relative/bin")}, DatabaseRecoveryError),
    ],
    ids=["production", "non-disposable", "unapproved", "no-typed-confirmation", "configured-target",
         "untrusted-client"],
)
def test_restore_refuses_active_non_disposable_or_unauthorized_targets_before_any_process(archive, overrides, error):
    with pytest.raises(error):
        _restore(archive, _tripwire("pg_restore"), password_provider=_tripwire("credential"),
                 inspector=_tripwire("inspector"), verifier=_tripwire("verifier"), **overrides)


def test_restore_refuses_an_incident_held_server(archive):
    database_targets.hold_target("localhost", 5432, reason="schema-048 incident")

    with pytest.raises(DatabaseTargetRefused, match="held"):
        _restore(archive, _tripwire("pg_restore"), password_provider=_tripwire("credential"),
                 inspector=_tripwire("inspector"))


class _CatalogConnection:
    """Scripted read-only catalog answers for the emptiness preflight."""

    def __init__(self, *, name="vres_restore_check1", counts=(0, 0, 0, 0, 0, 0, 0), fail=None):
        self.name, self.counts, self.fail, self.log = name, counts, fail, []

    def __call__(self, conninfo, **kwargs):
        self.conninfo, self.kwargs = conninfo, kwargs
        return self

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        return False

    def execute(self, sql, params=None):
        text = " ".join(str(sql).split())
        self.log.append(text)
        if self.fail:
            raise self.fail
        if text == "SELECT current_database()":
            return SimpleNamespace(fetchone=lambda: (self.name,))
        if text.startswith("SELECT (SELECT count(*) FROM pg_namespace"):
            return SimpleNamespace(fetchone=lambda: self.counts)
        return SimpleNamespace(fetchone=lambda: None)


@pytest.mark.parametrize(
    "connection,reason",
    [
        (_CatalogConnection(counts=(0, 3, 0, 0, 0, 0, 0)), "already contains user objects or data"),
        (_CatalogConnection(counts=(1, 0, 0, 0, 0, 0, 0)), "already contains user objects or data"),
        (_CatalogConnection(counts=(0, 0, 0, 0, 1, 0, 0)), "already contains user objects or data"),
        (_CatalogConnection(name="vres_os"), "not the named restore target"),
        (_CatalogConnection(counts=(0, 0, 0)), "could not be established"),
        (_CatalogConnection(fail=RuntimeError("permission denied for pg_largeobject_metadata")),
         "could not be established"),
    ],
    ids=["tables", "user-schema", "extension", "wrong-database", "unexpected-answer", "inspection-error"],
)
def test_populated_or_unprovable_restore_target_refuses_before_pg_restore(archive, monkeypatch, connection, reason):
    from vres_os import db

    monkeypatch.setattr(db, "_driver", lambda: SimpleNamespace(connect=connection))

    with pytest.raises(DatabaseRecoveryError, match=reason):
        _restore(archive, _tripwire("pg_restore"), inspector=pg_recovery.inspect_target,
                 verifier=_tripwire("verifier"))
    assert connection.log[0] == "SET TRANSACTION READ ONLY"
    assert not [s for s in connection.log if re.search(r"\b(INSERT|UPDATE|DELETE|CREATE|DROP|ALTER)\b", s)]
    assert "dbname=vres_restore_check1" in connection.conninfo and connection.kwargs == {"password": "synthetic-pw"}


def test_proven_empty_target_restores_single_transaction_and_needs_verification(archive, monkeypatch):
    from vres_os import db

    connection = _CatalogConnection()
    monkeypatch.setattr(db, "_driver", lambda: SimpleNamespace(connect=connection))
    client = _Client()

    result = _restore(archive, client, inspector=pg_recovery.inspect_target)

    argv = client.calls[0][0]
    assert result["status"] == "restored_verified" and result["preflight"]["empty"] is True
    assert argv[0] == str(_BIN["bin"] / "pg_restore.exe")
    assert "--single-transaction" in argv and "--exit-on-error" in argv
    assert not {"--clean", "--create", "-c", "-C"} & set(argv)
    unverified = _restore(archive, _Client(), verifier=lambda *_a: {"ok": False, "vres_tables": 0})
    assert unverified["status"] == "restored_unverified"


def test_simulated_restore_failure_or_tampered_archive_never_reports_success(archive):
    with pytest.raises(DatabaseRecoveryError, match="nothing was applied"):
        _restore(archive, _Client(restore_rc=1), verifier=_tripwire("verifier"))
    with pytest.raises(DatabaseRecoveryError, match="timed out"):
        _restore(archive, _Client(raises=__import__("subprocess").TimeoutExpired("pg_restore", 1)),
                 verifier=_tripwire("verifier"))
    archive.write_bytes(b"PGDMP-tampered")
    with pytest.raises(DatabaseRecoveryError, match="integrity"):
        _restore(archive, _tripwire("pg_restore"))


@pytest.mark.skipif(not hasattr(__import__("_winapi"), "CreateJunction"), reason="Windows directory junction")
def test_junctions_are_refused_by_backup_and_install_snapshot(tmp_path):
    import _winapi

    real = _state(tmp_path / "real")
    _winapi.CreateJunction(str(real), str(tmp_path / "VresOS"))
    with pytest.raises(StateBackupError, match="junction"):
        state_backup.create_backup(tmp_path / "VresOS", tmp_path / "b", protect=lambda _p: None)

    root, home = tmp_path / "root", tmp_path / "claude"
    root.mkdir()
    home.mkdir()
    (tmp_path / "elsewhere").mkdir()
    _winapi.CreateJunction(str(tmp_path / "elsewhere"), str(root / "bin"))
    with pytest.raises(InstallRecoveryError, match="junction"):
        install_recovery.snapshot(root, home, "R1")
    assert not (root / "install-recovery").exists()


# ------------------------------------------------- B1: the P2-A1 approval/hold registry is never rolled back

_HELD_NOW = b'{"version": 1, "approved": [], "held": [{"host": "localhost", "port": 5432, "dbname": null, ' \
            b'"reason": "schema-048 incident", "held_at": "2026-10-19T00:00:00+00:00"}]}'


def test_newer_quarantine_hold_survives_restore_and_interrupted_restore_recovery(backed_up, monkeypatch):
    registry = backed_up.source / "database-targets.json"
    registry.write_bytes(_HELD_NOW)  # a hold recorded after the backup was taken
    (backed_up.source / "config.json").write_text('"local edit"')

    state_backup.restore_backup(backed_up.backup, backed_up.source, replace_existing=True, presence=lambda _k: True)
    assert registry.read_bytes() == _HELD_NOW

    (backed_up.source / "config.json").write_text('"another edit"')
    real_write, real_recover = state_backup._write_atomic, state_backup.recover_restore

    def crash(path, data):
        real_write(path, data)
        if path.name == "config.json":
            raise KeyboardInterrupt

    monkeypatch.setattr(state_backup, "_write_atomic", crash)
    monkeypatch.setattr(state_backup, "recover_restore", lambda _root: (_ for _ in ()).throw(OSError("dead")))
    with pytest.raises(StateBackupError):
        state_backup.restore_backup(backed_up.backup, backed_up.source, replace_existing=True,
                                    presence=_tripwire("credential presence"))
    monkeypatch.setattr(state_backup, "_write_atomic", real_write)  # never undo(): conftest tripwires stay
    monkeypatch.setattr(state_backup, "recover_restore", real_recover)
    state_backup.recover_restore(backed_up.source)

    assert registry.read_bytes() == _HELD_NOW
    assert (backed_up.source / "config.json").read_text() == '"another edit"'


def test_historical_approval_is_never_reactivated_and_fresh_install_stays_default_deny(tmp_path):
    source = _state(tmp_path / "VresOS")
    old_approval = b'{"version": 1, "approved": [{"host": "localhost", "port": 5432, "dbname": "vres_os", ' \
                   b'"approved_at": "2026-01-01T00:00:00+00:00", "approved_by": "secure-setup"}], "held": []}'
    (source / "database-targets.json").write_bytes(old_approval)
    state_backup.create_backup(source, tmp_path / "b", protect=lambda _p: None)
    withdrawn = b'{"version": 1, "approved": [], "held": []}'
    (source / "database-targets.json").write_bytes(withdrawn)
    (source / "config.json").write_text('"local edit"')

    state_backup.restore_backup(tmp_path / "b", source, replace_existing=True, presence=lambda _k: True)
    fresh = tmp_path / "fresh"
    fresh.mkdir()
    state_backup.restore_backup(tmp_path / "b", fresh, presence=lambda _k: True)

    assert (source / "database-targets.json").read_bytes() == withdrawn
    assert not (fresh / "database-targets.json").exists()  # no approval exists until P2-A1 approval is given


def test_version_1_backup_is_readable_but_its_registry_copy_is_evidence_only(backed_up, tmp_path):
    manifest_path = backed_up.backup / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["version"] = 1
    for entry in manifest["files"]:
        if entry["path"] == "database-targets.json":
            entry["category"] = "restorable"  # how a version 1 backup recorded it
    manifest_path.write_text(json.dumps(manifest))
    fresh = tmp_path / "fresh"
    fresh.mkdir()

    result = state_backup.restore_backup(backed_up.backup, fresh, presence=lambda _k: True)

    assert "database-targets.json" not in result["restored"] and not (fresh / "database-targets.json").exists()
    manifest["version"] = 3
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(StateBackupError, match="unsupported format/version"):
        state_backup.verify_backup(backed_up.backup)


@pytest.mark.parametrize("journal", [{"state": "applying", "restore_point": "x"}, "not json"])
def test_historical_or_unreadable_restore_journal_fails_closed(backed_up, journal):
    path = backed_up.source / "restore-journal.json"
    path.write_text(journal if isinstance(journal, str) else json.dumps(journal))
    before = {p.name: p.read_bytes() for p in backed_up.source.iterdir() if p.is_file()}

    with pytest.raises(StateBackupError, match="unsupported|unreadable"):
        state_backup.recover_restore(backed_up.source)
    assert {p.name: p.read_bytes() for p in backed_up.source.iterdir() if p.is_file()} == before


# ------------------------------------------------------ B3: unprovable plugin identity without a backup refuses

def _journal(root, home, *, had_plugin=True):
    (root / "pending-install.json").write_text(json.dumps({
        "product": "Vres-OS", "new_release": "R1", "previous": {"product": "Vres-OS", "release": "R0"},
        "plugin_backup": str(root / "backups" / "R1"), "plugin_path": str(home / "skills" / "vres-os"),
        "had_plugin": had_plugin, "claude_snapshot": str(root / "install-recovery" / "R1"), "claude_home": str(home)}))


@pytest.fixture
def journaled(tmp_path):
    root, home = tmp_path / "VresOS", tmp_path / "claude"
    (root / "backups").mkdir(parents=True)
    (root / "active-install.json").write_text(json.dumps({"product": "Vres-OS", "release": "R0"}))
    home.mkdir()
    _plugin(home / "skills" / "vres-os", "R0")
    install_recovery.snapshot(root, home, "R1")
    _journal(root, home)
    return SimpleNamespace(root=root, home=home, plugin=home / "skills" / "vres-os")


def test_interruption_before_the_plugin_moved_is_proven_by_the_snapshot_digest(journaled):
    assert [a["action"] for a in install_recovery.inspect(journaled.root)["actions"]] == ["remove_journal"]


@pytest.mark.parametrize("change", ["edited", "replaced-by-new-copy"])
def test_missing_backup_with_an_unprovable_plugin_refuses_and_keeps_the_journal(journaled, change):
    if change == "edited":
        (journaled.plugin / "plugin.json").write_text(json.dumps({"version": "half-copied"}))
    else:
        shutil.rmtree(journaled.plugin)
        _plugin(journaled.plugin, "R1")  # the new plugin, with no backup of the original

    plan = install_recovery.inspect(journaled.root)

    assert plan["recoverable"] is False
    assert any("cannot be proven to be the pre-install plugin" in r for r in plan["refusals"])
    with pytest.raises(InstallRecoveryError, match="manual recovery"):
        install_recovery.recover(journaled.root, confirm=True)
    assert (journaled.root / "pending-install.json").exists()


def test_version_1_snapshot_cannot_prove_plugin_identity(journaled):
    snapshot = journaled.root / "install-recovery" / "R1" / "snapshot.json"
    manifest = json.loads(snapshot.read_text())
    manifest["version"] = 1
    del manifest["plugin"]
    snapshot.write_text(json.dumps(manifest))

    plan = install_recovery.inspect(journaled.root)

    assert plan["recoverable"] is False and any("cannot be proven" in r for r in plan["refusals"])


# ---------------------------------------------------------------- B4: redirected recovery parents are refused

def _junction(target: Path, link: Path):
    winapi = pytest.importorskip("_winapi")
    if not hasattr(winapi, "CreateJunction"):
        pytest.skip("Windows directory junction")
    target.mkdir(parents=True, exist_ok=True)
    winapi.CreateJunction(str(target), str(link))


def test_redirected_restore_points_directory_is_refused(backed_up, tmp_path):
    (backed_up.source / "config.json").write_text('"local edit"')
    _junction(tmp_path / "elsewhere", backed_up.source / "restore-points")
    before = (backed_up.source / "config.json").read_bytes()

    with pytest.raises(StateBackupError, match="link or junction"):
        state_backup.restore_backup(backed_up.backup, backed_up.source, replace_existing=True,
                                    presence=_tripwire("credential presence"))
    assert (backed_up.source / "config.json").read_bytes() == before
    assert list((tmp_path / "elsewhere").iterdir()) == []


def test_redirected_restore_points_directory_is_refused_during_recovery(backed_up, tmp_path):
    (backed_up.source / "restore-journal.json").write_text(json.dumps(
        {"version": 2, "state": "applying", "restore_point": "20261019T000000Z-0123abcd"}))
    _junction(tmp_path / "elsewhere" / "20261019T000000Z-0123abcd", backed_up.source / "restore-points")

    with pytest.raises(StateBackupError, match="link or junction"):
        state_backup.recover_restore(backed_up.source)


def test_redirected_install_recovery_parent_is_refused_by_snapshot(tmp_path):
    root, home = tmp_path / "VresOS", tmp_path / "claude"
    root.mkdir()
    home.mkdir()
    _junction(tmp_path / "elsewhere", root / "install-recovery")

    with pytest.raises(InstallRecoveryError, match="link, junction"):
        install_recovery.snapshot(root, home, "R1")
    assert list((tmp_path / "elsewhere").iterdir()) == []


@pytest.mark.parametrize("redirect", ["install-recovery", "backups"])
def test_redirected_recovery_parents_make_inspect_refuse(journaled, tmp_path, redirect):
    original = journaled.root / redirect
    moved = tmp_path / f"moved-{redirect}"
    original.rename(moved)
    _junction(moved, original)

    plan = install_recovery.inspect(journaled.root)

    assert plan["recoverable"] is False
    with pytest.raises(InstallRecoveryError, match="refused"):
        install_recovery.recover(journaled.root, confirm=True)


# ------------------------------------------- B6: missing recovery parents refuse; state root validated first

@pytest.mark.parametrize("missing", ["skills", "backups"])
def test_missing_plugin_recovery_parent_refuses_before_any_change(interrupted_install, missing):
    env = interrupted_install
    if missing == "skills":
        shutil.rmtree(env.home / "skills")  # the plugin backup still exists in backups/
    else:
        shutil.rmtree(env.root / "backups")
    before = {p: p.read_bytes() for p in env.base.rglob("*") if p.is_file()}

    plan = install_recovery.inspect(env.root)

    assert plan["recoverable"] is False
    assert any("required plugin recovery directories are missing" in r for r in plan["refusals"])
    with pytest.raises(InstallRecoveryError, match="refused"):
        install_recovery.recover(env.root, confirm=True)
    assert {p: p.read_bytes() for p in env.base.rglob("*") if p.is_file()} == before


def test_redirected_state_root_is_refused_before_its_journal_is_touched(tmp_path):
    real = tmp_path / "real-state"
    real.mkdir()
    journal = b'{"version": 2, "state": "applying", "restore_point": "20261019T000000Z-0123abcd"}'
    (real / "restore-journal.json").write_bytes(journal)
    _junction(real, tmp_path / "VresOS")

    with pytest.raises(StateBackupError, match="link or junction"):
        state_backup.recover_restore(tmp_path / "VresOS")
    assert (real / "restore-journal.json").read_bytes() == journal


# ------------------------------------- B7: archive and manifest are published together or not at all

def _failing_rename(monkeypatch, *, fail_on: str):
    real = __import__("os").rename

    def rename(src, dst):
        if Path(dst).name == fail_on:
            raise PermissionError("simulated publication failure")
        return real(src, dst)

    monkeypatch.setattr(pg_recovery.os, "rename", rename)


@pytest.mark.parametrize("failure", ["manifest-write", "manifest-acl", "archive-acl", "manifest-publication"])
def test_failed_manifest_or_publication_leaves_no_backup_artifacts(tmp_path, approve_database_target, monkeypatch,
                                                                   failure):
    approve_database_target(("localhost", 5432, "vres_os"))
    protect_calls = []

    def protect(path):
        protect_calls.append(path)
        if (failure == "manifest-acl" and len(protect_calls) == 2) or (failure == "archive-acl" and len(protect_calls) == 1):
            raise OSError("simulated ACL failure")

    if failure == "manifest-write":
        monkeypatch.setattr(pg_recovery.json, "dump", lambda *_a, **_kw: (_ for _ in ()).throw(OSError("disk full")))
    if failure == "manifest-publication":
        _failing_rename(monkeypatch, fail_on="vres.dump.manifest.json")
    client = _tripwire("client process") if failure == "archive-acl" else _Client()

    with pytest.raises(DatabaseRecoveryError, match="Backup failed before the archive and its manifest were both published"):
        _backup(tmp_path, client, protect=protect)
    assert list(tmp_path.iterdir()) == []  # neither final names nor staged files remain


def test_unremovable_published_archive_is_reported_exactly_and_never_succeeds(tmp_path, approve_database_target,
                                                                            monkeypatch):
    approve_database_target(("localhost", 5432, "vres_os"))
    _failing_rename(monkeypatch, fail_on="vres.dump.manifest.json")
    real_unlink = Path.unlink

    def stuck(self, *args, **kwargs):
        if self.name == "vres.dump":
            raise PermissionError("file in use")
        return real_unlink(self, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", stuck)

    with pytest.raises(DatabaseRecoveryError) as exc:
        _backup(tmp_path, _Client())
    assert f"delete them manually: {tmp_path / 'vres.dump'}." in str(exc.value)
    assert "No backup was produced" in str(exc.value)
    assert sorted(p.name for p in tmp_path.iterdir()) == ["vres.dump"]  # no manifest: never a usable-looking backup


def test_existing_manifest_is_never_overwritten(tmp_path, approve_database_target):
    approve_database_target(("localhost", 5432, "vres_os"))
    (tmp_path / "vres.dump.manifest.json").write_text("operator file")

    with pytest.raises(DatabaseRecoveryError, match="nothing is overwritten"):
        _backup(tmp_path, _tripwire("client process"), password_provider=_tripwire("credential"))
    assert (tmp_path / "vres.dump.manifest.json").read_text() == "operator file"
