"""Behavioral regression tests. Scripted DB boundaries do not claim PostgreSQL execution."""
from __future__ import annotations

import ast
import inspect
import json
import math
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace

import pytest

from vres_os.approvals import ApprovalService, explicit_acceptance, require_approval
from vres_os.config import ConfigStore, VresConfig
from vres_os.knowledge import KnowledgeService
from vres_os.metrics import validate_metrics
from vres_os.model_policy import ModelPolicyService
from vres_os.optimization import contracts_equivalent, pareto_gate
from vres_os.procedures import ProcedureService
from vres_os.redaction import redact, redact_text
from vres_os.repository import Repository
from vres_os.transcript import last_assistant_snapshot
from vres_os.validation import artifact_manifest, parse_validator_report, state_digest

ROOT = Path(__file__).resolve().parents[1]


class ScriptedConnection:
    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = []

    def execute(self, sql, params=None):
        self.calls.append((sql, params))
        assert self.replies, f"Unexpected SQL: {sql}"
        expected, reply = self.replies.pop(0)
        assert expected in str(sql), f"Expected {expected!r}, got {sql!r}"
        if isinstance(reply, Exception):
            raise reply
        return SimpleNamespace(fetchone=lambda: reply, fetchall=lambda: reply)

    def transaction(self):
        return nullcontext()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        assert not self.replies, f"Unconsumed SQL expectations: {self.replies}"


@pytest.mark.parametrize("field", ["quality_score", "runtime_ms", "input_tokens", "output_tokens", "retries", "estimated_cost"])
@pytest.mark.parametrize("value", [-1, math.nan, math.inf, -math.inf, True, "12"])
def test_invalid_measurements_never_enter_policy(field, value):
    with pytest.raises(ValueError):
        validate_metrics({field: value})


@pytest.mark.parametrize("field", ["input_tokens", "output_tokens", "runtime_ms", "retries"])
def test_fractional_counts_are_not_silently_truncated(field):
    with pytest.raises(ValueError):
        validate_metrics({field: 1.25})


def test_zero_and_missing_are_distinct_valid_measurements():
    validate_metrics({"input_tokens": 0, "output_tokens": None, "quality_score": 1.0})
    gate = pareto_gate(baseline_quality=1, candidate_quality=1, baseline_runtime_ms=5,
                       candidate_runtime_ms=4, baseline_tokens=10, candidate_tokens=None,
                       validation_passed=True)
    assert not gate.auto_promote


def test_pareto_has_no_implicit_validation():
    result = pareto_gate(baseline_quality=1, candidate_quality=1, baseline_runtime_ms=5,
                         candidate_runtime_ms=4, baseline_tokens=10, candidate_tokens=9)
    assert not result.auto_promote
    assert "validation" in result.reason


def test_two_missing_contracts_do_not_establish_equivalence():
    assert not contracts_equivalent({}, {})


@pytest.mark.parametrize("bad", ["policy2", "truth", "obsevation", "", "canonical"])
def test_unknown_knowledge_categories_fail_before_database(bad):
    with pytest.raises(ValueError, match="knowledge type"):
        KnowledgeService().propose(key="K-1", title="t", statement="s", knowledge_type=bad, status="canonical")


def test_lesson_cannot_skip_evidence():
    with pytest.raises(ValueError, match="attach evidence"):
        KnowledgeService().propose(key="L-1", title="t", statement="s", knowledge_type="lesson", status="canonical")


def test_task_cannot_self_certify_without_database():
    with pytest.raises(ValueError, match="validation"):
        Repository().update_state("TASK-x", validation_status="passed")
    with pytest.raises(ValueError, match="validation"):
        Repository().update_state("TASK-x", validation_status="not_required")


def test_bound_completed_task_does_not_jump_to_other_task():
    conn = ScriptedConnection([("LEFT JOIN vres.tasks", {"task_id": 42, "status": "completed"})])
    assert Repository()._selected_task_id(conn, 1, "session-A") is None
    assert len(conn.calls) == 1


def test_validator_is_protected_without_database_or_telemetry(monkeypatch):
    import vres_os.model_policy as module
    monkeypatch.setattr(module, "_connect", lambda: pytest.fail("validator selection queried optimizer"))
    chosen = ModelPolicyService().recommend("validate")
    assert chosen["model"] == "fable" and chosen["effort"] == "high"
    assert chosen["protected"] and not chosen["fallback_allowed"]


@pytest.mark.parametrize("text", ["OK", "yes", "Approved!", "Looks good.", "Ναι", "Το εγκρίνω"])
def test_unconditional_acceptance_is_recognized(text):
    assert explicit_acceptance(text)


@pytest.mark.parametrize("text", ["not OK", "OK but change the totals", "OK for now", "What does approved mean?", "fine but change title", "maybe", "", "no"])
def test_qualified_acceptance_is_not_approval(text):
    assert not explicit_acceptance(text)


@pytest.mark.parametrize("change", [{"subject_key": "OTHER"}, {"approval_type": "knowledge_publish"}, {"project_id": 2}])
def test_approval_cannot_be_reused_for_another_subject_action_or_project(change):
    row = {"id": 1, "project_id": 1, "approval_type": "procedure_accept", "subject_key": "PROC-1"} | change
    conn = ScriptedConnection([("approval_events", row)])
    with pytest.raises(ValueError):
        require_approval(conn, "APP-1", 1, "procedure_accept", "PROC-1")


def test_project_approval_cannot_publish_company_policy():
    conn = ScriptedConnection([("approval_events", {"id": 1, "project_id": 1, "approval_type": "procedure_accept", "subject_key": "P"})])
    with pytest.raises(ValueError):
        require_approval(conn, "A", None, "procedure_accept", "P")


def test_nonapproval_user_turn_cannot_create_approval(monkeypatch):
    import vres_os.approvals as module
    conn = ScriptedConnection([
        ("FROM vres.tasks", {"id": 1, "project_id": 1}),
        ("FROM vres.task_events", {"id": 2, "payload": {"text": "Explain the report"}}),
    ])
    monkeypatch.setattr(module, "_connect", lambda: conn)
    with pytest.raises(ValueError, match="acceptance"):
        ApprovalService().record_latest_user_approval(task_key="T", approval_type="procedure_accept", statement="accept", subject_key="P")


@pytest.mark.parametrize("value", [
    'postgresql://user:hunter2@localhost/db',
    'PASSWORD="two secret words"',
    "pwd='two secret words'",
    '{"api_key": "hunter2"}',
    "https://user:hunter2@example.invalid/repo",
    "-----BEGIN PRIVATE KEY-----\nhunter2\n-----END PRIVATE KEY-----",
])
def test_redaction_covers_uri_json_quoted_dsn_and_pem(value):
    cleaned = redact_text(value)
    assert "hunter2" not in cleaned and "secret words" not in cleaned


def test_dictionary_secrets_are_redacted_by_key():
    assert redact({"Password": "bare value", "nested": [{"access_token": "bare"}], "password_key": "postgres.default"}) == {
        "Password": "[REDACTED]", "nested": [{"access_token": "[REDACTED]"}], "password_key": "postgres.default"}


def test_recovery_ignores_nonobjects_malformed_and_hidden_reasoning(tmp_path):
    file = tmp_path / "transcript.jsonl"
    file.write_text('[]\nnull\ninvalid\n' + json.dumps({"type": "assistant", "message": {"content": [
        {"type": "thinking", "thinking": "private scratchpad"}, {"type": "text", "text": "visible result"}]}}))
    assert last_assistant_snapshot({"transcript_path": str(file)}) == "visible result"


def test_recovery_reads_bounded_tail_not_entire_transcript(tmp_path, monkeypatch):
    import vres_os.transcript as module
    monkeypatch.setattr(module, "MAX_TRANSCRIPT_TAIL", 512)
    p = tmp_path / "large.jsonl"
    p.write_text("x" * 5000 + "\n" + json.dumps({"type": "assistant", "message": {"content": "last result"}}))
    assert last_assistant_snapshot({"transcript_path": str(p)}) == "last result"


def test_documented_stop_payload_does_not_require_transcript_file():
    assert last_assistant_snapshot({"last_assistant_message": "direct result"}) == "direct result"


@pytest.mark.parametrize("field,value", [("configured", "false"), ("embeddings_enabled", 1), ("annual_refresh_day", True)])
def test_config_rejects_truthy_wrong_types(field, value):
    cfg = VresConfig()
    setattr(cfg, field, value)
    with pytest.raises(ValueError):
        cfg.validate()


def test_config_rejects_february_31():
    cfg = VresConfig(annual_refresh_month=2, annual_refresh_day=31)
    with pytest.raises(ValueError):
        cfg.validate()


def test_config_atomic_save_has_no_temp_leaks(tmp_path):
    store = ConfigStore(tmp_path / "config.json")
    store.save(VresConfig())
    assert store.load() == VresConfig()
    assert not list(tmp_path.glob("*.tmp"))


def test_selftest_uses_existing_procedure_signature():
    source = ast.parse((ROOT / "src/vres_os/selftest.py").read_text())
    allowed = inspect.signature(ProcedureService.accept_baseline).parameters
    calls = [x for x in ast.walk(source) if isinstance(x, ast.Call) and isinstance(x.func, ast.Attribute) and x.func.attr == "accept_baseline"]
    assert len(calls) == 1
    assert {k.arg for k in calls[0].keywords} <= set(allowed)
    assert "approval_key" in {k.arg for k in calls[0].keywords}


def test_validation_fingerprint_ignores_operational_timestamp_not_requirements():
    state = {"objective": "A", "state_summary": "B", "updated_at": "today"}
    assert state_digest(state) == state_digest(state | {"updated_at": "tomorrow", "validation_status": "passed"})
    assert state_digest(state) != state_digest(state | {"objective": "Changed"})


def test_artifact_manifest_detects_change_and_prevents_escape(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    (root / "x.py").write_text("print(1)")
    first = artifact_manifest(root, ["x.py"])
    (root / "x.py").write_text("print(2)")
    assert artifact_manifest(root, ["x.py"]) != first
    (tmp_path / "outside.py").write_text("bad")
    with pytest.raises(ValueError, match="inside"):
        artifact_manifest(root, ["../outside.py"])


def test_validator_cannot_call_skipped_checks_passed():
    with pytest.raises(ValueError, match="skipped"):
        parse_validator_report(json.dumps({"request_key": "V1", "outcome": "passed", "checks": [{"status": "not_run", "evidence": "not available"}]}))


def test_validator_requires_concrete_checks():
    with pytest.raises(ValueError):
        parse_validator_report('{"request_key":"V1","outcome":"passed","checks":[]}')
