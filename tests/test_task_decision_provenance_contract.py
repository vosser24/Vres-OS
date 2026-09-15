from __future__ import annotations

import inspect
from importlib import resources
from pathlib import Path

from vres_os.mcp_entrypoint import (
    task_decision_list,
    task_decision_record,
    task_decision_retire,
    task_decision_supersede,
)

ROOT = Path(__file__).resolve().parents[1]


def test_decision_provenance_migration_is_append_only_and_separate_from_approvals():
    sql = resources.files("vres_os").joinpath(
        "migrations", "020_task_decision_provenance.sql"
    ).read_text(encoding="utf-8")
    assert "CREATE TABLE IF NOT EXISTS vres.task_decisions" in sql
    assert "CREATE TABLE IF NOT EXISTS vres.checkpoint_decisions" in sql
    assert "source_kind IN ('chairman','user_instruction','legacy_unstructured')" in sql
    assert "decided_at timestamptz" in sql
    assert "recorded_at timestamptz NOT NULL DEFAULT now()" in sql
    assert "status IN ('active','superseded','retired')" in sql
    assert "legacy_unstructured' AND decided_at IS NULL" in sql
    assert "capture_checkpoint_decisions" in sql
    assert "enforce_task_decision_projection" in sql
    assert "approval_events" not in sql


def test_structured_decision_tools_require_session_for_mutations():
    assert "session_id" not in inspect.signature(task_decision_list).parameters
    for tool in (task_decision_record, task_decision_supersede, task_decision_retire):
        params = inspect.signature(tool).parameters
        assert "task_key" in params
        assert "session_id" in params


def test_user_source_is_event_backed_not_a_freeform_authority_flag():
    record = inspect.signature(task_decision_record).parameters
    supersede = inspect.signature(task_decision_supersede).parameters
    assert "source_event_id" in record
    assert "source_event_id" in supersede
    assert "source_kind" not in record
    assert "source_kind" not in supersede


def test_chairman_contract_uses_structured_decision_lifecycle():
    text = (ROOT / "plugins" / "vres-os" / "agents" / "chairman.md").read_text(encoding="utf-8")
    for tool in ("task_decision_record", "task_decision_supersede", "task_decision_retire"):
        assert tool in text
    assert "decision never creates approval" in text.lower()
