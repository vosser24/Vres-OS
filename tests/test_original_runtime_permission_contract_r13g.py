"""R13G original runtime DML contract: SOURCE ONLY / TESTS NOT_RUN.

Source assertions only. Never run under the open Schema-048 or native-hook
incidents without a separate explicitly approved isolated test environment.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOUNDARY = ROOT / "src/vres_os/database_boundary.py"
DB = ROOT / "src/vres_os/db.py"
RELEASE = ROOT / "src/vres_os/release_inputs.py"


def test_original_provisioning_has_no_blanket_runtime_delete_or_sequence_update():
    text = BOUNDARY.read_text(encoding="utf-8")
    assert "GRANT SELECT,INSERT,UPDATE ON ALL TABLES IN SCHEMA vres TO {}" in text
    assert "GRANT SELECT,INSERT,UPDATE ON TABLES TO {}" in text
    assert "GRANT USAGE,SELECT ON ALL SEQUENCES IN SCHEMA vres TO {}" in text
    assert "GRANT USAGE,SELECT ON SEQUENCES TO {}" in text
    assert "GRANT SELECT,INSERT,UPDATE,DELETE" not in text
    assert "GRANT USAGE,SELECT,UPDATE ON ALL SEQUENCES" not in text


def test_original_boundary_narrows_old_acl_and_default_grants():
    text = BOUNDARY.read_text(encoding="utf-8")
    assert "REVOKE DELETE,TRUNCATE ON ALL TABLES IN SCHEMA vres FROM PUBLIC" in text
    assert "REVOKE DELETE,TRUNCATE ON ALL TABLES IN SCHEMA vres FROM {}" in text
    assert "REVOKE UPDATE ON ALL SEQUENCES IN SCHEMA vres FROM PUBLIC" in text
    assert "REVOKE UPDATE ON ALL SEQUENCES IN SCHEMA vres FROM {}" in text
    assert "REVOKE DELETE,TRUNCATE ON TABLES FROM {}" in text
    assert "REVOKE UPDATE ON SEQUENCES FROM {}" in text
    assert "require_w4_schema_clearance()  # P0: before DB metadata or role operations" in text
    assert "_revoke_original_task_history_deletes(conn, cfg.database.user)" in text
    assert "_revoke_original_task_history_deletes(conn, runtime)" in text


def test_original_tasks_have_column_update_not_table_update():
    text = BOUNDARY.read_text(encoding="utf-8")
    assert "REVOKE UPDATE ON TABLE vres.tasks FROM PUBLIC" in text
    assert "REVOKE UPDATE ON TABLE vres.tasks FROM {}" in text
    assert "GRANT UPDATE (status,updated_at,completed_at)" in text
    assert 'SELECT to_regclass(\'vres.tasks\') AS relation' in text


def test_absolute_incidents_and_release_pin_are_not_bypassed():
    db = DB.read_text(encoding="utf-8")
    release = RELEASE.read_text(encoding="utf-8")
    assert 'W4_SCHEMA_048_SOURCE_INTERLOCK = "HELD_NO_POSTGRESQL_EVEN_SELECT"' in db
    assert 'W4_RELEASE_INPUT_SOURCE_INTERLOCK = "HELD_NO_ORIGINAL_RELEASE_VALIDATION"' in release
    assert "PERSONAL_RELEASE_MAX_MIGRATION = 41" in release
