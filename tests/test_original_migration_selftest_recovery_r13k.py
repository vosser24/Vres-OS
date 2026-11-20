"""R13K original-owner migration partial-failure and selftest safety contract.

SOURCE AUTHORED ONLY / NOT_RUN. No Python/SQL/PG/Claude/Windows execution.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "src/vres_os/db.py"
BOUNDARY = ROOT / "src/vres_os/database_boundary.py"
SELFTEST = ROOT / "src/vres_os/selftest.py"
CLI = ROOT / "src/vres_os/cli.py"
RELEASE = ROOT / "src/vres_os/release_inputs.py"


def test_original_writer_and_runtime_calls_restore_before_each_migration_commit():
    code = DB.read_text(encoding="utf-8").split("def migrate(", 1)[1]
    code = code.split("for name in names:", 1)[1]
    transaction = code.split("with conn.transaction():", 1)[1].split("applied.append(name)", 1)[0]
    positions = [
        transaction.index("conn.execute(sql_text)"),
        transaction.index("_restrict_original_function_execute(conn, cfg.database.user)"),
        transaction.index("_restore_original_runtime_migration_calls(conn, cfg.database.user)"),
        transaction.index("_restore_original_writer_migration_calls("),
        transaction.index("INSERT INTO vres.schema_migrations(version,checksum)"),
    ]
    assert positions == sorted(positions)
    assert 'if cfg.database.provenance_writer_user:' in transaction
    assert "with conn.transaction():" in code


def test_writer_restoration_is_narrow_and_migration_explicit():
    source = BOUNDARY.read_text(encoding="utf-8")
    helper = source.split("def _restore_original_writer_migration_calls(", 1)[1]
    helper = helper.split("def _revoke_original_task_history_deletes(", 1)[0]
    assert "require_w4_schema_clearance()" in helper
    assert "SELECT to_regprocedure(%s) AS routine" in helper
    assert "sql.Identifier(writer)" in helper
    assert "stage_strict_user_input(bigint,text,text,text,text,text,text,timestamptz,text)" in helper
    assert "issue_context_refresh_attestation(text,text,text,text)" in helper
    assert "record_experience_retrieval_replay(bigint,bigint,jsonb)" in helper
    assert "cancel_task_from_current_observation" not in helper
    assert "GRANT EXECUTE ON ALL FUNCTIONS" not in helper


def test_unsafe_multiconnection_original_selftest_refuses_before_migrate():
    source = SELFTEST.read_text(encoding="utf-8")
    func = source.split("def run_core_selftest()", 1)[1]
    assert func.index("_require_original_selftest_cleanup_clearance()") < func.index("migrate()")
    held = source.split("def _require_original_selftest_cleanup_clearance()", 1)[1]
    held = held.split("def run_core_selftest()", 1)[0]
    assert "OriginalSelftestCleanupHeld" in held
    assert "HELD_NO_RUNTIME_DELETE_OR_TASK_CASCADE" in source
    # Historical fixture/cleanup remain visible but UNCALLABLE under this hold.
    assert "DELETE FROM vres.tasks" in func
    assert "DELETE FROM vres.projects" in func
    cli = CLI.read_text(encoding="utf-8")
    assert "except OriginalSelftestCleanupHeld as exc:" in cli


def test_absolute_incidents_and_unapplied_release_pin_preserved():
    db = DB.read_text(encoding="utf-8")
    release = RELEASE.read_text(encoding="utf-8")
    assert 'W4_SCHEMA_048_SOURCE_INTERLOCK = "HELD_NO_POSTGRESQL_EVEN_SELECT"' in db
    assert "require_w4_schema_clearance()  # BEFORE importing driver" in db
    assert 'W4_RELEASE_INPUT_SOURCE_INTERLOCK = "HELD_NO_ORIGINAL_RELEASE_VALIDATION"' in release
    assert "PERSONAL_RELEASE_MAX_MIGRATION = 41" in release
