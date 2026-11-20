"""R13I source-only migration ACL contract. AUTHORED / NOT_RUN.

No Vres import, SQL, PostgreSQL connection, native Claude hook or Windows run.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "src/vres_os/db.py"
BOUNDARY = ROOT / "src/vres_os/database_boundary.py"
RELEASE = ROOT / "src/vres_os/release_inputs.py"


def test_migration_sql_and_acl_revoke_precede_same_ledger_commit():
    migration = DB.read_text(encoding="utf-8").split("def migrate(", 1)[1]
    loop = migration.split("for name in names:", 1)[1]
    markers = (
        "with conn.transaction():",
        "conn.execute(sql_text)",
        'if purpose == "migrator":',
        "from .database_boundary import _restrict_original_function_execute",
        "_restrict_original_function_execute(conn, cfg.database.user)",
        "INSERT INTO vres.schema_migrations(version,checksum)",
        "applied.append(name)",
    )
    positions = [loop.index(s) for s in markers]
    assert positions == sorted(positions)
    assert len(set(positions)) == len(positions)


def test_existing_original_function_boundary_is_reused_not_bypassed():
    boundary = BOUNDARY.read_text(encoding="utf-8")
    helper = boundary.split("def _restrict_original_function_execute(", 1)[1]
    assert "require_w4_schema_clearance()" in helper
    assert "REVOKE EXECUTE ON ALL FUNCTIONS IN SCHEMA vres FROM PUBLIC" in helper
    assert "REVOKE EXECUTE ON ALL FUNCTIONS IN SCHEMA vres FROM {}" in helper
    assert "sql.Identifier(runtime)" in helper
    assert 'governance_signature = "vres.assert_governance_mutation_allowed(bigint,text)"' in boundary
    assert "_activate_context_refresh_attestations(conn, runtime, writer)" in boundary
    assert "_activate_experience_observability(conn, runtime, writer)" in boundary


def test_incident_holds_and_release_pin_still_present():
    db = DB.read_text(encoding="utf-8")
    release = RELEASE.read_text(encoding="utf-8")
    assert 'W4_SCHEMA_048_SOURCE_INTERLOCK = "HELD_NO_POSTGRESQL_EVEN_SELECT"' in db
    assert "require_w4_schema_clearance()  # BEFORE importing driver" in db
    assert 'W4_RELEASE_INPUT_SOURCE_INTERLOCK = "HELD_NO_ORIGINAL_RELEASE_VALIDATION"' in release
    assert "PERSONAL_RELEASE_MAX_MIGRATION = 41" in release
