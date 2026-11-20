"""R13H source-only original function-execution authorization contract.

ALL tests NOT_RUN. Do not import Vres, connect to PostgreSQL, run Claude hooks,
execute SQL, or alter a Windows installation under the current incidents.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOUNDARY = ROOT / "src/vres_os/database_boundary.py"
MIGRATOR = ROOT / "src/vres_os/db.py"
R13G = ROOT / "tests/test_original_runtime_permission_contract_r13g.py"
RELEASE = ROOT / "src/vres_os/release_inputs.py"


def test_no_blanket_runtime_execute_grants_in_original_provisioning():
    text = BOUNDARY.read_text(encoding="utf-8")
    assert "GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA vres" not in text
    assert "GRANT EXECUTE ON FUNCTIONS TO {}" not in text
    assert "_restrict_original_function_execute(conn, cfg.database.user)" in text
    assert "_restrict_original_function_execute(conn, runtime)" in text
    assert "REVOKE EXECUTE ON ALL FUNCTIONS IN SCHEMA vres FROM PUBLIC" in text
    assert "REVOKE EXECUTE ON ALL FUNCTIONS IN SCHEMA vres FROM {}" in text
    assert 'REVOKE EXECUTE ON FUNCTIONS FROM {}' in text


def test_runtime_governance_trigger_dependency_and_writer_routing_preserved():
    text = BOUNDARY.read_text(encoding="utf-8")
    assert 'governance_signature = "vres.assert_governance_mutation_allowed(bigint,text)"' in text
    assert 'SELECT to_regprocedure(%s) AS routine' in text
    assert 'GRANT EXECUTE ON FUNCTION {} TO {}' in text
    assert 'protected_functions = [' in text
    assert 'vres.stage_user_input(bigint,text,text,text,text,text,text,timestamptz)' in text
    assert 'vres.commit_user_inputs(bigint,text,text)' in text
    assert 'vres.stage_strict_user_input(bigint,text,text,text,text,text,text,timestamptz,text)' in text
    assert 'vres.cancel_task_from_current_observation(bigint,text,text,bigint,text,jsonb)' in text
    assert '_activate_context_refresh_attestations(conn, runtime, writer)' in text
    assert '_activate_experience_observability(conn, runtime, writer)' in text


def test_existing_schema_hold_and_release_migration_pin_unchanged():
    text = BOUNDARY.read_text(encoding="utf-8")
    migrations = MIGRATOR.read_text(encoding="utf-8")
    release = RELEASE.read_text(encoding="utf-8")
    assert "require_w4_schema_clearance()  # P0: never touch DB under Schema-048 hold" in text
    assert "require_w4_schema_clearance()  # BEFORE importing driver" in migrations
    assert 'W4_RELEASE_INPUT_SOURCE_INTERLOCK = "HELD_NO_ORIGINAL_RELEASE_VALIDATION"' in release
    assert "PERSONAL_RELEASE_MAX_MIGRATION = 41" in release
    assert R13G.is_file()
