"""R13F source-only original task integrity boundary contract: NOT_RUN.

These assertions inspect immutable source text only; they do not load psycopg,
connect to PostgreSQL, run SQL, start Claude/FastMCP or alter Windows.
"""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "src/vres_os/migrations/048_original_task_terminal_hold_r13f.sql"
BOUNDARY = ROOT / "src/vres_os/database_boundary.py"
LIFECYCLE = ROOT / "src/vres_os/task_lifecycle.py"
RELEASE = ROOT / "src/vres_os/release_inputs.py"


def test_prospective_terminal_guard_denies_sql_cancel_and_delete():
    text = MIGRATION.read_text(encoding="utf-8")
    assert "LIVE_SCHEMA_048_INCIDENT" in text
    assert "SECURITY INVOKER" in text
    assert "TG_OP = 'DELETE'" in text
    assert "NEW.status = 'cancelled'" in text
    assert "OLD.status IS DISTINCT FROM 'cancelled'" in text
    assert "OLD.status IN ('completed', 'cancelled')" in text
    assert "BEFORE UPDATE OF status OR DELETE ON vres.tasks" in text
    assert "FOR EACH ROW EXECUTE FUNCTION" in text
    assert "VRES_W4_HELD_TASK_CANCEL" in text
    assert "VRES_W4_HELD_TASK_DELETE" in text


def test_original_boundary_revokes_delete_during_setup_and_activation():
    text = BOUNDARY.read_text(encoding="utf-8")
    assert text.count("_revoke_original_task_history_deletes(conn, ") == 2
    helper = text.split("def _revoke_original_task_history_deletes(", 1)[1]
    assert "require_w4_schema_clearance()" in helper
    for table in ('"tasks"', '"task_state"', '"task_events"', '"checkpoints"'):
        assert table in helper
    assert "REVOKE DELETE ON {} FROM PUBLIC" in helper
    assert "REVOKE DELETE ON {} FROM {}" in helper
    assert "SELECT to_regclass(%s) AS relation" in helper


def test_existing_lifecycle_and_release_still_held():
    lifecycle = LIFECYCLE.read_text(encoding="utf-8")
    release = RELEASE.read_text(encoding="utf-8")
    assert 'if target == "cancelled":' in lifecycle
    assert "Task cancellation requires a reviewed operator-only route" in lifecycle
    assert "return _cancel_atomic(" not in lifecycle
    assert "PERSONAL_RELEASE_MAX_MIGRATION = 41" in release
    assert 'W4_RELEASE_INPUT_SOURCE_INTERLOCK = "HELD_NO_ORIGINAL_RELEASE_VALIDATION"' in release
