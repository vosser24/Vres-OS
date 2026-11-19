"""R13B synthetic author-side regressions: AUTHORED, NOT_RUN."""
from pathlib import Path
import pytest
from vres_os.task_lifecycle import _is_explicit_cancel_instruction

ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "src/vres_os/migrations/046_original_observation_rebind_quarantine_r13b.sql"

def test_existing_writer_filters_to_observed_original_task_and_session():
    sql = MIGRATION.read_text(encoding="utf-8")
    assert "CREATE OR REPLACE FUNCTION vres.commit_user_inputs(" in sql
    assert "AND observed_session_id=sess.id" in sql
    assert "AND observed_task_id=target.id" in sql
    assert "AND strict_persistence_stage_version=1" in sql
    assert "AND committed_at IS NULL" in sql
    assert "ORDER BY id\n         FOR UPDATE" in sql
    assert "REVOKE ALL ON FUNCTION vres.commit_user_inputs(" in sql
    assert "CREATE OR REPLACE FUNCTION vres.cancel_task_from_current_observation(" not in sql

def test_rebind_and_session_end_revoke_only_pending_strict_stage():
    sql = MIGRATION.read_text(encoding="utf-8")
    assert "OLD.task_id IS DISTINCT FROM NEW.task_id" in sql
    assert "OLD.ended_at IS NULL AND NEW.ended_at IS NOT NULL" in sql
    assert "WHERE observed_session_id=OLD.id" in sql
    assert "SET strict_persistence_stage_version=NULL" in sql
    assert "AFTER UPDATE OF task_id, ended_at ON vres.sessions" in sql
    assert "SECURITY DEFINER" in sql
    assert "SET search_path = pg_catalog, vres" in sql
    assert "REVOKE ALL ON FUNCTION vres.invalidate_strict_observations_on_rebind()" in sql

@pytest.mark.parametrize("prompt", ["cancel this", "Cancel this!", "cancel this."])
def test_ambiguous_cancel_this_not_authorized_in_python(prompt):
    assert _is_explicit_cancel_instruction(prompt) is False

@pytest.mark.parametrize("prompt", ["cancel this task", "please cancel this task", "yes, cancel this task"])
def test_explicit_cancel_this_task_still_classified(prompt):
    assert _is_explicit_cancel_instruction(prompt) is True

def test_r13b_neither_applies_migrations_nor_claims_current_turn_freshness():
    assert "Same-task unobserved-turn freshness (C-3) is NOT solved" in MIGRATION.read_text(encoding="utf-8")
