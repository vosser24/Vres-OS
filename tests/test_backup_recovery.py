"""P2-C backup and recovery, offline: disposable temp directories, a synthetic Claude home,
simulated PostgreSQL client runs and the P2-A1 guard over a private approval registry.
No real PostgreSQL client, installer, credential store or Claude configuration is used.
"""
from __future__ import annotations

import json
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
    assert (manifest["format"], manifest["version"], manifest["complete"]) == ("vres-state-backup", 1, True)
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
        "config.json", "credential-resources.json", "database-targets.json"]  # evidence never restored
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
        state_backup.restore_backup(backed_up.backup, backed_up.source, replace_existing=True)
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
    home.mkdir()
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

    def __init__(self, *, dump_rc=0, list_rc=0, listing=_TOC, restore_rc=0):
        self.calls, self.dump_rc, self.list_rc, self.listing, self.restore_rc = [], dump_rc, list_rc, listing, restore_rc

    def __call__(self, argv, env):
        self.calls.append((argv, env))
        tool = Path(argv[0]).name
        if tool == "pg_dump":
            target = Path(next(a for a in argv if a.startswith("--file="))[7:])
            if self.dump_rc == 0:
                target.write_bytes(b"PGDMP-simulated-archive")
            return SimpleNamespace(returncode=self.dump_rc, stdout="", stderr="pg_dump: error: password=hunter2 rejected")
        if "--list" in argv:
            return SimpleNamespace(returncode=self.list_rc, stdout=self.listing, stderr="")
        return SimpleNamespace(returncode=self.restore_rc, stdout="", stderr="pg_restore: error: role missing")


_TOOLS = {"pg_dump": "C:/PG/bin/pg_dump", "pg_restore": "C:/PG/bin/pg_restore"}


def _backup(tmp_path, client, **overrides):
    args = dict(host="localhost", port=5432, dbname="vres_os", user="vres_migrator", sslmode="prefer",
                output=tmp_path / "vres.dump", password_provider=lambda: "synthetic-pw",
                runner=client, tool_lookup=_TOOLS.get)
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
                tool_lookup=_tripwire("tool lookup"))
    assert list(tmp_path.iterdir()) == []


def test_verified_backup_writes_archive_and_manifest_without_exposing_the_password(tmp_path, approve_database_target):
    approve_database_target(("localhost", 5432, "vres_os"))
    client = _Client()

    result = _backup(tmp_path, client)

    assert result["status"] == "verified_archive" and result["toc"] == {"entries": 4, "vres_tables": 2, "ledger": 1}
    manifest = json.loads((tmp_path / "vres.dump.manifest.json").read_text())
    assert manifest["sha256"] == pg_recovery._sha256_file(tmp_path / "vres.dump")
    for argv, env in client.calls:
        assert not any("synthetic-pw" in a for a in argv)
        assert not any(k.upper().startswith("PG") and k != "PGPASSWORD" for k in env)
    assert client.calls[0][1]["PGPASSWORD"] == "synthetic-pw" and "PGPASSWORD" not in client.calls[1][1]
    assert "synthetic-pw" not in json.dumps(result) + json.dumps(manifest)


@pytest.mark.parametrize(
    "client,message",
    [(_Client(dump_rc=1), "pg_dump failed"), (_Client(list_rc=1), "Archive verification"),
     (_Client(listing="; nothing\n10; 2615 1 SCHEMA - public o\n"), "migration ledger")],
    ids=["dump-fails", "listing-fails", "not-a-vres-archive"],
)
def test_simulated_client_failure_never_yields_a_backup_pass(tmp_path, approve_database_target, client, message):
    approve_database_target(("localhost", 5432, "vres_os"))

    with pytest.raises(DatabaseRecoveryError, match=message) as exc:
        _backup(tmp_path, client)
    assert "hunter2" not in str(exc.value)
    assert not (tmp_path / "vres.dump").exists() and not (tmp_path / "vres.dump.manifest.json").exists()


@pytest.fixture
def archive(tmp_path, approve_database_target):
    approve_database_target(("localhost", 5432, "vres_os"), ("localhost", 5432, "vres_restore_check1"))
    _backup(tmp_path, _Client())
    return tmp_path / "vres.dump"


def _restore(archive, client, **overrides):
    args = dict(archive=archive, host="localhost", port=5432, dbname="vres_restore_check1", user="vres_migrator",
                sslmode="prefer", confirmation="RESTORE vres_restore_check1", password_provider=lambda: "synthetic-pw",
                production=("localhost", 5432, "vres_os"), runner=client, tool_lookup=_TOOLS.get,
                verifier=lambda conninfo, manifest: {"ok": True})
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
    ],
    ids=["production", "non-disposable", "unapproved", "no-typed-confirmation", "configured-target"],
)
def test_restore_refuses_active_non_disposable_or_unauthorized_targets_before_any_process(archive, overrides, error):
    with pytest.raises(error):
        _restore(archive, _tripwire("pg_restore"), password_provider=_tripwire("credential"),
                 verifier=_tripwire("verifier"), **overrides)


def test_restore_refuses_an_incident_held_server(archive):
    database_targets.hold_target("localhost", 5432, reason="schema-048 incident")

    with pytest.raises(DatabaseTargetRefused, match="held"):
        _restore(archive, _tripwire("pg_restore"), password_provider=_tripwire("credential"))


def test_restore_is_single_transaction_never_destructive_and_needs_verification(archive):
    client = _Client()

    result = _restore(archive, client)

    argv = client.calls[0][0]
    assert result["status"] == "restored_verified"
    assert "--single-transaction" in argv and "--exit-on-error" in argv
    assert not {"--clean", "--create", "-c", "-C"} & set(argv)
    unverified = _restore(archive, _Client(), verifier=lambda *_a: {"ok": False, "vres_tables": 0})
    assert unverified["status"] == "restored_unverified"


def test_simulated_restore_failure_or_tampered_archive_never_reports_success(archive):
    with pytest.raises(DatabaseRecoveryError, match="nothing was applied"):
        _restore(archive, _Client(restore_rc=1), verifier=_tripwire("verifier"))
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
