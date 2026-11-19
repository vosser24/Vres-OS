"""R13C original host-observed turn and validated cancellation SOURCE tests; NOT_RUN."""
from pathlib import Path

from vres_os.task_lifecycle import _is_explicit_cancel_instruction

ROOT = Path(__file__).resolve().parents[1]
SQL = ROOT / "src/vres_os/migrations/047_original_cancel_observed_turn_and_validation_r13c.sql"


def test_original_stage_keeps_provenance_bound_to_observed_turn():
    sql = SQL.read_text(encoding="utf-8")
    assert "ADD COLUMN observed_turn_id text" in sql
    assert "CREATE OR REPLACE FUNCTION vres.stage_strict_user_input(" in sql
    assert "observed_session_id=observed_binding.id" in sql
    assert "observed_task_id=observed_binding.task_id" in sql
    assert "observed_turn_id=NULLIF(btrim(observed_binding.metadata" in sql
    assert "REVOKE ALL ON FUNCTION vres.stage_strict_user_input(" in sql
    assert "CREATE TABLE" not in sql


def test_original_cancel_sql_rejects_ambiguous_phrase_in_both_languages():
    sql = SQL.read_text(encoding="utf-8")
    cancel = sql.split("CREATE OR REPLACE FUNCTION vres.cancel_task_from_current_observation(", 1)[1]
    assert "'cancel this'," not in cancel
    assert "'cancel this task'," in cancel
    assert _is_explicit_cancel_instruction("cancel this") is False
    assert _is_explicit_cancel_instruction("cancel this task") is True


def test_cancel_rechecks_current_observed_turn_and_locked_task():
    cancel = SQL.read_text(encoding="utf-8").split(
        "CREATE OR REPLACE FUNCTION vres.cancel_task_from_current_observation(", 1
    )[1]
    assert "obs.observed_session_id IS DISTINCT FROM sess.id" in cancel
    assert "obs.observed_task_id IS DISTINCT FROM target.id" in cancel
    assert "obs.observed_turn_id IS NULL" in cancel
    assert "obs.observed_turn_id IS DISTINCT FROM NULLIF(btrim(sess.metadata" in cancel
    assert "(sess.metadata->'reply_guard'->>'gate') IS NOT NULL" in cancel
    assert "obs.id IS DISTINCT FROM p_observation_id" in cancel
    assert "actual_siblings IS DISTINCT FROM p_sibling_snapshot" in cancel
    assert cancel.count("ORDER BY s.id FOR UPDATE NOWAIT") == 2
    assert cancel.index("PERFORM vres.commit_user_inputs(") < cancel.index("UPDATE vres.tasks")
    assert "REVOKE ALL ON FUNCTION vres.cancel_task_from_current_observation(" in cancel


def test_terminal_cancel_does_not_invalidate_existing_passed_validation():
    cancel = SQL.read_text(encoding="utf-8").split(
        "CREATE OR REPLACE FUNCTION vres.cancel_task_from_current_observation(", 1
    )[1]
    assert "SET validation_status='pending'" not in cancel
    assert "UPDATE vres.validation_requests" in cancel
    assert "SET status='cancelled'" in cancel
    assert "vres.explicit_validation_invalidation" not in cancel


def test_host_turn_is_created_before_staging_and_unbound_intake_is_not_reassigned():
    h = (ROOT / "src/vres_os/hooks.py").read_text(encoding="utf-8")
    prompt = h.split("def user_prompt() -> None:", 1)[1].split("def compact(", 1)[0]
    assert prompt.index("turn_id = begin_reply_turn(") < prompt.index("stage_user_instruction(")
    assert "Cannot establish a current host-observed reply turn" in prompt
    assert "VRES_UNBOUND_INPUT" in prompt
    assert "Do not claim this prompt was committed to a task" in prompt


def test_source_only_and_unobserved_turn_residual_are_explicit():
    sql = SQL.read_text(encoding="utf-8")
    assert "NOT_APPLIED / NOT_RUN" in sql
    assert "C-3 when later host turns were not observed is NOT fully solved" in sql
    release = (ROOT / "src/vres_os/release_inputs.py").read_text(encoding="utf-8")
    assert "001-041" in release
