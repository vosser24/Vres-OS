"""P2-B: automatic E1 episode capture at the committed completion boundaries, and Chairman retrieval guidance.

Offline. The E1 ledger is a scripted, transactional stand-in for PostgreSQL (an exception
inside a transaction rolls back its writes); completion services are stubbed at their seams.
The P2-A1 conftest tripwire refuses any real connection.
"""
from __future__ import annotations

import re
from contextlib import contextmanager
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from vres_os import experience, mcp_server, routing_completion
from vres_os.experience import POLICY_DIGEST, POLICY_SCHEMA_VERSION, capture_completed_task

_ROOT = Path(__file__).resolve().parents[1]
_WHEN = datetime(2026, 10, 19, 12, 0, tzinfo=UTC)


class _Cursor:
    def __init__(self, row=None, rows=()):
        self._row, self._rows = row, list(rows)

    def fetchone(self):
        return self._row

    def fetchall(self):
        return self._rows


class _Ledger:
    """Answers exactly the statements ExperienceEpisodeService.capture/get issue."""

    def __init__(self, *, project_id=7, validation_status="passed", validation="passed", work_units=()):
        self.task = {
            "id": 11, "task_key": "T-1", "project_id": project_id, "task_family": "general",
            "objective": "Ship the quarterly report", "status": "active", "completed_at": None,
            "updated_at": _WHEN, "constraints": [], "validation_status": validation_status,
        }
        self.validation = (
            {"request_key": "VR-1", "status": validation, "state_digest": "d" * 64, "observed_model": "fable",
             "agent_id": "a-1", "created_at": _WHEN, "completed_at": _WHEN}
            if validation else None
        )
        self.work_units = [dict(unit) for unit in work_units]
        self.episodes: dict[str, dict] = {}
        self.relations: list[dict] = []
        self.writes: list[str] = []
        self.fail_insert = False

    def complete(self, validation_status=None):
        self.task.update(status="completed", completed_at=_WHEN)
        if validation_status:
            self.task["validation_status"] = validation_status

    # connection protocol
    def __call__(self):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        return False

    @contextmanager
    def transaction(self):
        saved = deepcopy((self.episodes, self.relations))
        try:
            yield self
        except BaseException:
            self.episodes, self.relations = saved
            raise

    def execute(self, sql, params=()):
        text = " ".join(str(sql).split())
        if re.match(r"(INSERT|UPDATE|DELETE)\b", text):
            self.writes.append(text.split("(")[0])
        if "pg_advisory_xact_lock" in text:
            return _Cursor()
        if "FROM vres.experience_policy_versions" in text:
            return _Cursor({"schema_version": POLICY_SCHEMA_VERSION, "policy_digest": POLICY_DIGEST})
        if "FROM vres.tasks t JOIN vres.task_state" in text:
            return _Cursor(dict(self.task) if params[0] == self.task["task_key"] else None)
        if "FROM vres.task_decisions" in text or "FROM vres.procedure_runs" in text or "FROM vres.artifacts a" in text:
            return _Cursor(rows=[])
        if "FROM vres.validation_requests WHERE task_id" in text:
            return _Cursor(self.validation)
        if "FROM vres.orchestration_work_units WHERE task_id=%s AND status IN" in text:
            return _Cursor(rows=[dict(unit) for unit in self.work_units])
        if "FROM vres.experience_episodes WHERE task_id=%s AND work_unit_key IS NULL" in text:
            found = [e for e in self.episodes.values() if e["task_id"] == params[0] and e["work_unit_key"] is None]
            return _Cursor(found[0] if found else None)
        if text.startswith("INSERT INTO vres.experience_episodes"):
            if self.fail_insert:
                raise RuntimeError("transient storage failure")
            (key, project_id, task_id, work_unit_key, report_key, family, policy, trust, outcome, payload,
             source_digest, payload_digest, disposition, observed_at) = params
            self.episodes[key] = {
                "episode_key": key, "project_id": project_id, "task_id": task_id, "work_unit_key": work_unit_key,
                "report_key": report_key, "task_family": family, "policy_version": policy,
                "participation_class": "participated", "trust_class": trust, "outcome_status": outcome,
                "payload": payload, "source_digest": source_digest, "payload_digest": payload_digest,
                "security_disposition": disposition, "observed_at": observed_at, "created_at": _WHEN,
            }
            return _Cursor()
        if "SELECT id,project_id FROM vres.experience_episodes WHERE episode_key" in text:
            return _Cursor({"id": 1, "project_id": self.episodes[params[0]]["project_id"]})
        if text.startswith("SELECT id,project_id FROM vres.") or "JOIN vres.tasks t ON t.id=v.task_id" in text:
            return _Cursor({"id": 1, "project_id": self.task["project_id"]})
        if text.startswith("INSERT INTO vres.relations("):
            self.relations.append({"relation_type": params[2], "target_kind": params[3], "target_key": params[4],
                                   "provenance": params[5], "confidence": params[6], "source_key": params[1]})
            return _Cursor({"id": len(self.relations)})
        if text.startswith("INSERT INTO vres.relation_evidence"):
            return _Cursor()
        if "FROM vres.experience_episodes WHERE episode_key=%s AND project_id IS NOT DISTINCT FROM" in text:
            row = self.episodes.get(params[0])
            return _Cursor(dict(row) if row and row["project_id"] == params[1] else None)
        if "FROM vres.relations WHERE source_kind='episode'" in text:
            return _Cursor(rows=[{k: v for k, v in r.items() if k != "source_key"}
                                 for r in self.relations if r["source_key"] == params[0]])
        raise AssertionError(f"unscripted statement: {text[:120]}")


@pytest.fixture
def ledger(monkeypatch):
    def make(**kwargs):
        book = _Ledger(**kwargs)
        monkeypatch.setattr(experience, "connect", book)
        return book

    return make


@pytest.fixture
def direct_completion(monkeypatch, tmp_path):
    """task_complete with its validation/completion seams stubbed; records the call order."""
    order = []
    monkeypatch.setattr(mcp_server, "_require_node", lambda *a, **kw: order.append("scope"))
    monkeypatch.setattr(mcp_server, "_project", lambda: (7, SimpleNamespace(root=tmp_path)))
    from vres_os import validation

    monkeypatch.setattr(validation.ValidationService, "assert_current",
                        lambda self, *a: order.append("assert_current"))
    real_capture = experience.ExperienceEpisodeService.capture

    def capture(self, *args, **kwargs):
        order.append("capture")
        return real_capture(self, *args, **kwargs)

    monkeypatch.setattr(experience.ExperienceEpisodeService, "capture", capture)
    return order


# 1. Direct protected completion


def test_protected_completion_captures_one_validated_episode_after_the_commit(ledger, direct_completion, monkeypatch):
    book = ledger()
    monkeypatch.setattr(mcp_server.Repository, "complete_task",
                        lambda self, key, summary: direct_completion.append("complete") or book.complete())

    result = mcp_server.task_complete("T-1", "done")

    assert result["completed"] is True
    assert result["experience"]["status"] == "captured"
    assert result["experience"]["trust_class"] == "validated_runtime"  # backed by the real protected PASS
    assert result["experience"]["authority"] == "no_promotion"
    assert direct_completion == ["scope", "assert_current", "complete", "capture"]
    assert len(book.episodes) == 1
    episode = next(iter(book.episodes.values()))
    assert (episode["project_id"], episode["outcome_status"]) == (7, "completed")
    assert {r["target_kind"] for r in book.relations} == {"task", "validation"}


# 2. Governed routine completion


def test_routine_governed_completion_keeps_its_assurance_and_captures_without_fabricated_validation(
    ledger, monkeypatch, tmp_path
):
    unit = {"work_unit_key": "W-1", "plan_key": "P-1", "role": "analyst", "status": "passed", "covers": ["pricing"],
            "capability_keys": ["cap.pricing"], "acceptance_criteria": [], "verifies": [], "report_key": "R-1",
            "last_error": None, "host_agent_id": "agent-1", "observed_model": "sonnet", "completed_at": _WHEN}
    book = ledger(validation_status="pending", validation=None, work_units=[unit])
    state = SimpleNamespace(updates=[])

    class RoutineGate:
        def __call__(self):
            return self

        def __enter__(self):
            return self

        def __exit__(self, *_exc):
            return False

        def transaction(self):
            return self

        def execute(self, sql, params=()):
            if "UPDATE vres.task_state" in sql:
                state.updates.append("not_required")
            return _Cursor({"id": 11, "status": "active", "validation_status": "pending"})

    monkeypatch.setattr(routing_completion, "connect", RoutineGate())
    monkeypatch.setattr(routing_completion.RoutingService, "_completion_contract",
                        lambda self, **kw: {"protected": False, "request_key": "RR-1", "task_id": 11})

    def complete(self, **kw):
        book.complete(validation_status="not_required")
        return {"completed": True, "assurance": "routine", "routing_request_key": "RR-1"}

    monkeypatch.setattr(routing_completion.RoutingService, "complete", complete)

    result = routing_completion.complete_routed_task(
        project_id=7, task_key="T-1", root=tmp_path, summary="done", session_id="S-1"
    )

    assert (result["completed"], result["assurance"], result["routing_request_key"]) == (True, "routine", "RR-1")
    assert state.updates == ["not_required"]  # the existing routine gate ran unchanged
    assert result["experience"]["status"] == "captured"
    assert result["experience"]["trust_class"] == "trusted_project_source"  # never claims validated_runtime
    episode = next(iter(book.episodes.values()))
    assert '"work_unit_key":"W-1"' in episode["payload"] and '"validation":null' in episode["payload"]
    assert {r["target_kind"] for r in book.relations} == {"task", "capability"}


# 3. Rejected completion


def test_rejected_direct_completion_creates_no_episode(ledger, direct_completion, monkeypatch):
    book = ledger(validation_status="pending")

    def reject(self, key, summary):
        raise ValueError("Task cannot complete while validation is pending or failed")

    monkeypatch.setattr(mcp_server.Repository, "complete_task", reject)

    with pytest.raises(ValueError, match="cannot complete"):
        mcp_server.task_complete("T-1", "done")
    assert "capture" not in direct_completion and book.episodes == {}


def test_rejected_routed_completion_creates_no_episode(ledger, monkeypatch, tmp_path):
    book = ledger()
    monkeypatch.setattr(routing_completion.RoutingService, "_completion_contract",
                        lambda self, **kw: {"protected": True, "request_key": "RR-1", "task_id": 11})

    def reject(self, **kw):
        raise ValueError("Routine completion cannot contain a non-Sonnet worker")

    monkeypatch.setattr(routing_completion.RoutingService, "complete", reject)

    with pytest.raises(ValueError, match="non-Sonnet"):
        routing_completion.complete_routed_task(project_id=7, task_key="T-1", root=tmp_path, summary="s",
                                                session_id="S-1")
    assert book.episodes == {}


def test_capture_never_runs_for_an_unfinished_task(ledger):
    book = ledger()  # still active

    result = capture_completed_task("T-1", project_id=7)

    assert result["status"] == "failed" and result["episode_key"] is None
    assert book.episodes == {} and book.writes == []


# 4. Idempotence and immutable conflict


def test_repeated_capture_is_idempotent_and_changed_evidence_is_an_explicit_conflict(ledger):
    book = ledger()
    book.complete()

    first = capture_completed_task("T-1", project_id=7)
    second = capture_completed_task("T-1", project_id=7)

    assert first["status"] == second["status"] == "captured"
    assert first["episode_key"] == second["episode_key"] and len(book.episodes) == 1
    stored = deepcopy(book.episodes)

    book.task["objective"] = "Rewritten after the fact"
    conflict = capture_completed_task("T-1", project_id=7)

    assert conflict["status"] == "conflict" and conflict["retry_safe"] is False
    assert "Immutable experience episode conflicts" in conflict["error"]
    assert book.episodes == stored  # the immutable episode is untouched


# 5. Honest failure and safe retry


def test_capture_failure_keeps_the_completion_and_is_safely_retryable(ledger, direct_completion, monkeypatch):
    book = ledger()
    monkeypatch.setattr(mcp_server.Repository, "complete_task", lambda self, key, summary: book.complete())
    book.fail_insert = True

    result = mcp_server.task_complete("T-1", "done")

    assert result["completed"] is True  # the committed completion is never reported as incomplete
    assert result["experience"]["status"] == "failed" and result["experience"]["episode_key"] is None
    assert result["experience"]["retry_safe"] is True and "transient storage failure" in result["experience"]["error"]
    assert book.episodes == {} and book.relations == []  # nothing claimed, nothing half-written

    book.fail_insert = False
    retried = mcp_server.experience_capture_retry("T-1")
    again = mcp_server.experience_capture_retry("T-1")

    assert retried["status"] == again["status"] == "captured"
    assert retried["episode_key"] == again["episode_key"] and len(book.episodes) == 1


def test_capture_retry_is_scoped_to_the_current_project(monkeypatch, tmp_path):
    from vres_os import db

    monkeypatch.setattr(mcp_server, "_project", lambda: (7, SimpleNamespace(root=tmp_path)))

    class OtherProjectTask:
        def __call__(self):
            return self

        def __enter__(self):
            return self

        def __exit__(self, *_exc):
            return False

        def execute(self, sql, params=()):
            return _Cursor({"id": 11, "project_id": 8})

    monkeypatch.setattr(db, "connect", OtherProjectTask())
    monkeypatch.setattr(experience.ExperienceEpisodeService, "capture",
                        lambda *a, **kw: pytest.fail("capture reached for another project's task"))

    with pytest.raises(ValueError, match="outside the current project"):
        mcp_server.experience_capture_retry("T-1")


# 6. Wrong-project capture and retrieval


def test_wrong_project_capture_is_refused_before_any_write(ledger):
    book = ledger(project_id=8)
    book.complete()

    result = capture_completed_task("T-1", project_id=7)

    assert result["status"] == "refused" and result["retry_safe"] is False
    assert book.episodes == {} and book.writes == []


def test_retrieval_cannot_name_another_project(monkeypatch):
    monkeypatch.setattr(mcp_server, "_trusted_project_id", lambda: pytest.fail("project lookup reached"))

    with pytest.raises(ValueError, match="without project_id"):
        mcp_server.experience_retrieve({"query": "pricing", "project_id": 8})


# 7. No promotion into instructions


def test_capture_integration_writes_only_the_episodic_ledger_and_grants_no_authority(ledger):
    book = ledger()
    book.complete()

    result = capture_completed_task("T-1", project_id=7)

    assert result["authority"] == "no_promotion"
    assert set(book.writes) <= {"INSERT INTO vres.experience_episodes", "INSERT INTO vres.relations",
                                "INSERT INTO vres.relation_evidence"}
    assert experience.POLICY["authority"] == "no_promotion"
    source = (_ROOT / "src/vres_os/experience.py").read_text(encoding="utf-8")
    helper = source[source.index("def capture_completed_task"):]
    assert not re.search(r"knowledge|procedure_accept|promote\(|consolidat", helper.split('"""', 2)[2])


def test_failed_precedent_is_presented_as_a_warning_not_a_recipe():
    source = (_ROOT / "src/vres_os/experience_retrieval.py").read_text(encoding="utf-8")

    assert '"Past failure, not a recipe. "' in source
    assert '"warning_example"' in source and '"gotcha_example"' in source


# 8. Chairman retrieval contract


def test_chairman_retrieval_guidance_is_selective_evidence_based_and_project_scoped():
    text = (_ROOT / "plugins/vres-os/agents/chairman.md").read_text(encoding="utf-8")
    rule = next(line for line in text.splitlines() if line.startswith("3. Check procedural memory"))

    assert "`experience_retrieve` once" in rule and "never for trivial or ephemeral questions" in rule
    assert "in this project" in rule and "never instructions" in rule
    assert "not from similarity or rank" in rule and "not recipes" in rule
    for gone in ("Revoked tombstones", "quarantined", "superseded", "low-trust"):
        assert gone in rule
    assert "never paste whole packs or transcripts" in rule
    assert "never replaces knowledge and procedure search" in rule
    assert "2. Search documented company/project knowledge" in text  # existing rules preserved
    assert "project_id" not in rule  # scoping stays server-side


def test_chairman_completion_guidance_never_overclaims_capture():
    text = (_ROOT / "plugins/vres-os/agents/chairman.md").read_text(encoding="utf-8")

    assert "Do not say an episode was saved unless the status is `captured`" in text
    assert "`experience_capture_retry`" in text and "never undoes the completion" in text
    assert "never promoted to knowledge, procedures or instructions automatically" in text
