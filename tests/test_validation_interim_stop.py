import vres_os.validation_audit as validation_audit
from vres_os.validation_audit import (
    _DEFERRED_REASON,
    _GENERIC_NOT_FOUND,
    _classify_ingestion,
    classify_rejection,
)


def test_accepted_always_wins_regardless_of_allow_defer_or_reason():
    for allow_defer in (True, False):
        disposition, reason = _classify_ingestion(True, "any reason at all", allow_defer)
        assert disposition == "accepted"
        assert reason == "any reason at all"
    disposition, reason = _classify_ingestion(True, _GENERIC_NOT_FOUND, True)
    assert disposition == "accepted"
    assert reason == _GENERIC_NOT_FOUND


def test_generic_not_found_defers_when_allow_defer_is_true():
    disposition, reason = _classify_ingestion(False, _GENERIC_NOT_FOUND, True)
    assert disposition == "deferred"
    assert reason == _DEFERRED_REASON


def test_specific_stale_reason_is_not_deferred_even_when_allow_defer_true():
    reason = "Task changed during validation; fresh review required"
    disposition, out_reason = _classify_ingestion(False, reason, True)
    assert disposition == classify_rejection(reason) == "stale"
    assert out_reason == reason


def test_specific_rejected_reason_is_not_deferred_even_when_allow_defer_true():
    reason = "A skipped or failed check cannot establish PASS"
    disposition, out_reason = _classify_ingestion(False, reason, True)
    assert disposition == classify_rejection(reason) == "rejected"
    assert out_reason == reason


def test_unobserved_reason_is_not_deferred_even_when_allow_defer_true():
    reason = "Only an observed namespaced validator completion is accepted"
    disposition, out_reason = _classify_ingestion(False, reason, True)
    assert disposition == classify_rejection(reason) == "unobserved"
    assert out_reason == reason


def test_generic_not_found_never_defers_when_allow_defer_is_false():
    disposition, reason = _classify_ingestion(False, _GENERIC_NOT_FOUND, False)
    assert disposition == classify_rejection(_GENERIC_NOT_FOUND) == "rejected"
    assert reason == _GENERIC_NOT_FOUND


def test_no_defer_possible_when_allow_defer_false_regardless_of_reason_content():
    for reason in (
        _GENERIC_NOT_FOUND,
        "Task changed during validation; fresh review required",
        "A skipped or failed check cannot establish PASS",
        "Only an observed namespaced validator completion is accepted",
    ):
        disposition, _ = _classify_ingestion(False, reason, False)
        assert disposition != "deferred"
        assert disposition == classify_rejection(reason)


def test_live_background_task_helper_no_longer_exists():
    assert not hasattr(validation_audit, "_has_live_background_task")
    assert not hasattr(validation_audit, "_LIVE_BACKGROUND_STATUSES")
