"""#176 E7 B4B: Repository.begin_task shares the canonical sanitizer and fails closed before any write."""
import pytest

from vres_os import repository
from vres_os.repository import Repository


class _NoDatabase:
    def __call__(self, *a, **k):
        raise AssertionError("begin_task touched the database before rejecting")


@pytest.mark.parametrize("field", ["title", "objective"])
def test_begin_task_rejects_unredactable_credential_shape_before_any_write(monkeypatch, field):
    monkeypatch.setattr(repository, "connect", _NoDatabase())
    args = {"title": "Deploy report", "objective": "Ship the report"}
    args[field] = "service_key_id=Zq8!x7Lm2Pq4Rt"
    with pytest.raises(ValueError, match="could not be reliably sanitized") as exc:
        Repository().begin_task(1, args["title"], args["objective"], "engineering", "chairman")
    assert "Zq8" not in str(exc.value)


def test_begin_task_uses_the_shared_sanitizer_for_redactable_forms(monkeypatch):
    seen = {}

    class _Conn:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def transaction(self): return self
        def execute(self, sql, params=()):
            seen.setdefault("params", []).append(params)
            class _R:
                def fetchone(_s): return {"id": 1}
            return _R()

    monkeypatch.setattr(repository, "connect", lambda: _Conn())
    Repository().begin_task(1, "t", "the pipeline printed the service key Zq8!x7Lm2Pq4Rt in its log",
                            "engineering", "chairman")
    blob = repr(seen["params"])
    assert "Zq8!x7Lm2Pq4Rt" not in blob
    assert "[REDACTED]" in blob


@pytest.mark.parametrize("error", ["pipeline printed sk_test_" + "Zq8x7Lm2Pq4Rt9Ab", "auth=" + "Zq8x7Lm2Pq4Rt9Ab",
                                   "key AKIA" + "ABCDEFGHIJKLMNOP"])
def test_fail_work_unit_rejects_residual_only_credential_before_any_write(monkeypatch, error):
    from vres_os import orchestration
    monkeypatch.setattr(orchestration, "connect", _NoDatabase())
    with pytest.raises(ValueError) as exc:
        orchestration.OrchestrationService().fail_work_unit(
            project_id=1, task_key="T", session_id="S", work_unit_key="W", error=error)
    assert "Zq8x7Lm2Pq4Rt9Ab" not in str(exc.value) and "AKIA" not in str(exc.value)


def _crit(statement, key="C1"):
    from vres_os.orchestration import _acceptance_criteria
    return _acceptance_criteria([{"key": key, "statement": statement, "verification": "deterministic"}])


def test_acceptance_criterion_redacts_recognised_secret_before_persistence():
    out = _crit("Deploy succeeds; password=" + "Zq8x7Lm2Pq4Rt9Ab" + " is never logged")
    assert "Zq8x7Lm2Pq4Rt9Ab" not in repr(out) and "[REDACTED]" in out[0]["statement"]


@pytest.mark.parametrize("statement", ["no sk_test_" + "Zq8x7Lm2Pq4Rt9Ab" + " in output", "auth=" + "Zq8x7Lm2Pq4Rt9Ab"])
def test_acceptance_criterion_rejects_residual_only_credential(statement):
    with pytest.raises(ValueError) as exc:
        _crit(statement)
    assert "Zq8x7Lm2Pq4Rt9Ab" not in str(exc.value)


def test_acceptance_criterion_rejects_credential_bearing_key_and_keeps_benign_text():
    with pytest.raises(ValueError):
        _crit("ok", key="password=" + "Zq8x7Lm2Pq4Rt9Ab")
    benign = "All tests pass; robot key mapping documented; password policy check exits 0"
    assert _crit(benign)[0]["statement"] == benign
