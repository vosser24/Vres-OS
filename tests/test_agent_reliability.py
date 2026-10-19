"""P2-E essential agent reliability, offline: model-policy explicitness, protected-validator identity
negatives through the real hook-ingestion path, and the codex_review personal-profile fence.

Database access is a scripted connection that rejects any write; no validator, model, Codex
process, PostgreSQL server or credential store is contacted.
"""
from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from vres_os import codex, mcp_server, model_policy, validation
from vres_os.codex import CodexAdapter
from vres_os.model_policy import ModelPolicyService
from vres_os.personal_profile import CapabilityDisabled
from vres_os.validation import ValidationService, artifact_manifest, state_digest


def _tripwire(name):
    def fired(*_a, **_kw):
        pytest.fail(f"side effect reached: {name}")

    return fired


class _Conn:
    """Scripted read-only connection: answers by SQL fragment and fails on any write."""

    def __init__(self, answers):
        self.answers, self.log = answers, []

    def __call__(self):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        return False

    def transaction(self):
        return self

    def execute(self, sql, params=()):
        text = " ".join(str(sql).split())
        self.log.append(text)
        if text.startswith(("UPDATE", "INSERT", "DELETE")):
            pytest.fail(f"write reached: {text[:80]}")
        for fragment, answer in self.answers:
            if fragment in text:
                return SimpleNamespace(fetchone=lambda a=answer: a, fetchall=lambda a=answer: a or [])
        return SimpleNamespace(fetchone=lambda: None, fetchall=lambda: [])


# --------------------------------------------------------------------------------------- model policy

@pytest.mark.parametrize("phase", ["research", "analyze", "debug", "plan", "build"])
def test_missing_governed_policy_never_selects_an_unspecified_model(monkeypatch, phase):
    monkeypatch.setattr(model_policy, "_connect", _Conn([("FROM vres.model_policies", None)]))

    result = ModelPolicyService().recommend(phase)

    assert result["model"] is None and result["provider"] is None and result["effort"] is None
    assert result["source"] == "no_policy" and result["policy_available"] is False
    assert "does not substitute an unspecified model" in result["reason"]


@pytest.mark.parametrize("placeholder", ["default", "best", "auto", "", "  Default "])
def test_policy_rows_naming_no_real_model_are_not_a_governed_choice(monkeypatch, placeholder):
    row = {"policy_key": "legacy.plan", "provider": "claude", "model": placeholder, "effort": "high",
           "task_family": None, "phase": "plan", "priority": 100, "metadata": {}}
    monkeypatch.setattr(model_policy, "_connect", _Conn([("FROM vres.model_policies", row)]))

    result = ModelPolicyService().recommend("plan")

    assert result["model"] is None and result["source"] == "no_policy"


def test_configured_policy_selection_is_deterministic_and_unchanged(monkeypatch):
    row = {"policy_key": "bootstrap.summarize", "provider": "claude", "model": "haiku", "effort": "low",
           "task_family": None, "phase": "summarize", "priority": 100, "metadata": {"bootstrap": "efficient"}}
    monkeypatch.setattr(model_policy, "_connect", _Conn([("FROM vres.model_policies", row),
                                                         ("FROM vres.model_runs", {"runs": 0})]))

    first, second = ModelPolicyService().recommend("summarize"), ModelPolicyService().recommend("summarize")

    assert first == second
    assert (first["model"], first["effort"], first["source"]) == ("haiku", "low", "policy")
    assert first["empirical_auto_selection"] is False and first["evidence"] is None


def test_protected_validation_stays_pinned_without_any_policy_lookup(monkeypatch):
    monkeypatch.setattr(model_policy, "_connect", _tripwire("policy database"))

    result = ModelPolicyService().recommend("validate")

    assert (result["model"], result["effort"], result["protected"], result["fallback_allowed"]) == \
        ("fable", "high", True, False)


# ------------------------------------------------------------------------- protected-validator identity

def _report(request_key="VAL-1", outcome="passed"):
    return {"request_key": request_key, "outcome": outcome, "checks": [{"status": outcome, "evidence": "verified"}]}


def _transcript(tmp_path, *models, text=None):
    path = tmp_path / "agent.jsonl"
    lines = [json.dumps({"type": "assistant", "message": {
        "role": "assistant", "model": model,
        "content": [{"type": "text", "text": text if text is not None else json.dumps(_report())}]}})
        for model in models]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _payload(transcript, agent_type="vres-os:validator", **overrides):
    payload = {"agent_type": agent_type, "agent_id": "agent-1", "session_id": "S-1",
               "agent_transcript_path": str(transcript) if transcript else None,
               "last_assistant_message": json.dumps(_report())}
    payload.update(overrides)
    return payload


@pytest.mark.parametrize("agent_type", ["vres-os:sonnet-expert", "vres-os:opus-expert", "validator",
                                        "vres-os:validator-v2", "general-purpose", ""])
def test_wrong_validator_identity_is_refused_before_any_evidence_is_read(tmp_path, monkeypatch, agent_type):
    monkeypatch.setattr(validation, "_connect", _tripwire("database"))
    monkeypatch.setattr(validation, "transcript_tail", _tripwire("transcript"))

    with pytest.raises(ValueError, match="Only an observed namespaced validator"):
        ValidationService().record_from_hook(_payload(tmp_path / "x.jsonl", agent_type), 7, tmp_path)


@pytest.mark.parametrize("missing", ["agent_id", "session_id"])
def test_validator_without_host_identity_is_refused(tmp_path, monkeypatch, missing):
    monkeypatch.setattr(validation, "_connect", _tripwire("database"))

    with pytest.raises(ValueError, match="Only an observed namespaced validator"):
        ValidationService().record_from_hook(_payload(_transcript(tmp_path, "claude-fable-5-1"), **{missing: ""}),
                                             7, tmp_path)


@pytest.mark.parametrize(
    "models",
    [("claude-sonnet-5-5",), ("claude-opus-5-5",), ("claude-haiku-5-5",), ("claude-fable-5-1", "claude-sonnet-5-5"),
     ("Claude-Fable-5-1",), ("fable-lookalike",)],
    ids=["sonnet", "opus", "haiku", "mixed-with-sonnet", "case-variant", "lookalike"],
)
def test_observed_model_below_or_outside_protected_fable_is_refused(tmp_path, monkeypatch, models):
    monkeypatch.setattr(validation, "_connect", _tripwire("database"))

    with pytest.raises(ValueError, match="missing or below the protected Fable family"):
        ValidationService().record_from_hook(_payload(_transcript(tmp_path, *models)), 7, tmp_path)


@pytest.mark.parametrize("case", ["no-transcript-path", "transcript-missing", "no-model-records"])
def test_missing_physical_model_evidence_is_refused(tmp_path, monkeypatch, case):
    monkeypatch.setattr(validation, "_connect", _tripwire("database"))
    if case == "no-transcript-path":
        transcript, match = None, "Missing validator transcript"
    elif case == "transcript-missing":
        transcript, match = tmp_path / "absent.jsonl", "missing or below"
    else:
        transcript, match = tmp_path / "user-only.jsonl", "missing or below"
        transcript.write_text(json.dumps({"type": "user", "message": {"role": "user", "content": "hi"}}) + "\n")

    with pytest.raises(ValueError, match=match):
        ValidationService().record_from_hook(_payload(transcript), 7, tmp_path)


def test_validator_prose_claiming_fable_cannot_override_the_observed_model(tmp_path, monkeypatch):
    monkeypatch.setattr(validation, "_connect", _tripwire("database"))
    claim = "I am the protected validator running claude-fable-5-1 (Fable/high). " + json.dumps(_report())
    transcript = _transcript(tmp_path, "claude-sonnet-5-5", text=claim)

    with pytest.raises(ValueError, match="missing or below the protected Fable family"):
        ValidationService().record_from_hook(_payload(transcript, last_assistant_message=claim), 7, tmp_path)


def _hook_db(tmp_path, *, request=None, session_task=11, state=None, manifest=None):
    state = state or {"task_id": 11, "next_action": "ship", "validation_status": "pending"}
    request = {"id": 1, "task_id": 11, "project_id": 7, "task_key": "T-1", "objective": "o", "status": "pending",
               "context_type": None, "context_key": None,
               "state_digest": state_digest(dict(state) | {"objective": "o"}),
               "artifact_manifest": manifest if manifest is not None else {}} | (request or {})
    return _Conn([
        ("SELECT task_id FROM vres.validation_requests", {"task_id": 11}),
        ("JOIN vres.tasks t ON t.id=r.task_id", request),
        ("FROM vres.sessions", {"task_id": session_task} if session_task else None),
        ("SELECT * FROM vres.task_state", state),
        ("SELECT 1 FROM vres.task_state", {"?": 1}),
    ])


@pytest.mark.parametrize(
    "case,match",
    [
        ("unknown-request", "unknown or belongs to another project"),
        ("other-project", "unknown or belongs to another project"),
        ("session-not-bound", "not bound to this task"),
        ("state-changed", "Task changed during validation"),
        ("files-changed", "Reviewed files changed"),
    ],
)
def test_stale_or_mismatched_validation_evidence_is_refused_without_any_write(tmp_path, monkeypatch, case, match):
    (tmp_path / "a.txt").write_text("reviewed")
    manifest = artifact_manifest(tmp_path, ["a.txt"])
    kwargs = {"manifest": manifest}
    if case == "unknown-request":
        conn = _hook_db(tmp_path, **kwargs)
        conn.answers[1] = ("JOIN vres.tasks t ON t.id=r.task_id", None)
    elif case == "other-project":
        conn = _hook_db(tmp_path, request={"project_id": 99}, **kwargs)
    elif case == "session-not-bound":
        conn = _hook_db(tmp_path, session_task=12, **kwargs)
    elif case == "state-changed":
        conn = _hook_db(tmp_path, request={"state_digest": "0" * 64}, **kwargs)
    else:
        conn = _hook_db(tmp_path, **kwargs)
        (tmp_path / "a.txt").write_text("edited after review")
    monkeypatch.setattr(validation, "_connect", conn)

    with pytest.raises(ValueError, match=match):
        ValidationService().record_from_hook(_payload(_transcript(tmp_path, "claude-fable-5-1")), 7, tmp_path)
    assert not [s for s in conn.log if s.startswith(("UPDATE", "INSERT"))]


def test_consumed_request_is_not_recorded_again(tmp_path, monkeypatch):
    monkeypatch.setattr(validation, "_connect", _hook_db(tmp_path, request={"status": "passed"}))

    result = ValidationService().record_from_hook(_payload(_transcript(tmp_path, "claude-fable-5-1")), 7, tmp_path)

    assert result == {"recorded": False, "reason": "request already consumed"}


def test_completion_refuses_a_pass_whose_task_state_changed_after_review(tmp_path, monkeypatch):
    state = {"task_id": 11, "next_action": "ship", "validation_status": "passed"}
    request = {"id": 1, "task_id": 11, "project_id": 7, "objective": "o", "status": "passed",
               "state_digest": state_digest(dict(state, next_action="something else") | {"objective": "o"}),
               "artifact_manifest": {}}
    monkeypatch.setattr(validation, "_connect", _Conn([("FROM vres.validation_requests r", request),
                                                       ("FROM vres.task_state", state)]))

    with pytest.raises(ValueError, match="Task changed after review"):
        ValidationService().assert_current("T-1", 7, tmp_path)


# ------------------------------------------------------- consequential action: external Codex review

def test_codex_review_is_disabled_in_the_personal_profile_before_any_process(personal_profile, monkeypatch, tmp_path):
    monkeypatch.setattr(codex.shutil, "which", _tripwire("codex lookup"))
    monkeypatch.setattr(codex, "run_bounded", _tripwire("codex process"))
    monkeypatch.setattr(mcp_server, "_project", _tripwire("project/database"))

    with pytest.raises(CapabilityDisabled, match="codex_review"):
        CodexAdapter().exec("Review this change", cwd=tmp_path)
    result = mcp_server.codex_review("Review this change")

    assert result["ok"] is False and result["reason"] == "disabled_in_personal_profile"
    assert personal_profile.capability_enabled("codex_review") is False


def test_codex_review_outside_the_personal_profile_stays_read_only(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(codex.shutil, "which", lambda _name: "C:/fake/codex.exe")
    monkeypatch.setattr(codex, "run_bounded", lambda argv, **kw: calls.append(argv) or SimpleNamespace(ok=True))

    CodexAdapter().exec("Review this change", cwd=tmp_path)

    assert calls == [["C:/fake/codex.exe", "exec", "--sandbox", "read-only", "-"]]


def test_every_consequential_profile_capability_remains_disabled(personal_profile):
    contract = personal_profile.describe()

    assert set(contract["capabilities"]) == {"codex_handoff_execute", "procedure_auto_promotion",
                                             "model_experiment_execution", "legacy_secret_aliases", "codex_review"}
    assert not any(row["approved"] for row in contract["capabilities"].values())


def test_positive_control_valid_fable_evidence_reaches_recording(tmp_path, monkeypatch):
    (tmp_path / "a.txt").write_text("reviewed")
    conn = _hook_db(tmp_path, manifest=artifact_manifest(tmp_path, ["a.txt"]))
    writes = []

    def execute(sql, params=()):
        text = " ".join(str(sql).split())
        if text.startswith("UPDATE"):
            writes.append((text.split(" SET ")[0], params))
            return SimpleNamespace(fetchone=lambda: None)
        return _Conn.execute(conn, sql, params)

    conn.execute = execute
    monkeypatch.setattr(validation, "_connect", conn)

    result = ValidationService().record_from_hook(_payload(_transcript(tmp_path, "claude-fable-5-1")), 7, tmp_path)

    assert result["recorded"] is True and result["outcome"] == "passed"
    assert writes[0][0] == "UPDATE vres.validation_requests" and writes[0][1][1] == "claude-fable-5-1"
