"""#176 E4 Chunk B: pure (no DB) contract of the experience lifecycle service."""
import hashlib
import inspect
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest

from vres_os import experience_lifecycle as el
from vres_os.experience_lifecycle import ExperienceLifecycleService

T0 = datetime(2026, 9, 30, 12, 0, tzinfo=timezone.utc)
SOURCE = Path(el.__file__).read_text(encoding="utf-8")


def test_public_surface_is_exactly_the_five_lifecycle_actions():
    public = {n for n, v in inspect.getmembers(ExperienceLifecycleService) if not n.startswith("_") and callable(v)}
    assert public == {"retire", "reinstate", "challenge", "supersede", "refresh"}
    assert el.POLICY_VERSION == "176.e4.v1" and el.APPROVAL_TYPE == "e4_lifecycle"


def test_no_path_can_produce_revoked_or_touch_foreign_stores():
    assert "revoked" not in el.LIVE_PRIORS and "revoked" not in el.CHALLENGE_PRIORS
    assert el.CHALLENGE_PRIORS == frozenset({"proposed", "observed", "validated", "canonical"})
    assert el.LIVE_PRIORS == el.CHALLENGE_PRIORS | {"challenged"}
    assert "'revoked'" not in SOURCE and '"revoked"' not in SOURCE
    for table in ("sources", "knowledge_chunks", "embedding", "sessions", "experience_episodes",
                  "experience_transitions", "task_decisions", "checkpoint_decisions", "source_locations"):
        assert f"vres.{table}" not in SOURCE, table


def test_idempotency_key_formula_and_supersede_target():
    raw = "176.e4.v1|retire|knowledge|K-1|APR-1"
    assert el.idempotency_key("retire", "K-1", "APR-1") == hashlib.sha256(raw.encode()).hexdigest()
    sup = hashlib.sha256(b"176.e4.v1|supersede|knowledge|K-1->K-2|APR-1").hexdigest()
    assert el.idempotency_key("supersede", "K-1->K-2", "APR-1") == sup
    with pytest.raises(ValueError, match="Unknown lifecycle action"):
        el.idempotency_key("revoke", "K-1", "APR-1")


def test_approval_subject_binds_action_and_exact_targets():
    assert el.approval_subject("retire", "K-1") == "retire:K-1"
    assert el.approval_subject("supersede", "K-1", "K-2") == "supersede:K-1:K-2"
    for bad in ("revoke", "revoke_source", "expire_observed", ""):
        with pytest.raises(ValueError, match="Unknown lifecycle action"):
            el.approval_subject(bad, "K-1")
    with pytest.raises(ValueError):
        el.approval_subject("supersede", "K-1")
    with pytest.raises(ValueError):
        el.approval_subject("retire", "K-1", "K-2")


def test_request_digest_is_canonical_and_semantic():
    d = el.request_digest("because", None, None)
    canon = json.dumps({"reason": "because", "review_after": None, "successor_key": None},
                       sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    assert d == hashlib.sha256(canon.encode()).hexdigest()
    assert el.request_digest("because", "K-2", None) != d
    assert el.request_digest("other", None, None) != d
    athens = timezone(timedelta(hours=3))
    assert el.request_digest("r", None, T0) == el.request_digest("r", None, T0.astimezone(athens))


@pytest.mark.parametrize("bad", ["", "   ", "x" * 501, 'password: "synthetic-value"', None, 5, b"bytes"])
def test_reason_validation_rejects_empty_oversized_secret_and_non_text(bad):
    with pytest.raises(ValueError):
        el.validate_reason(bad)


def test_reason_validation_accepts_plain_text_and_strips():
    assert el.validate_reason("  no longer applies after the v2 cache rewrite ") == (
        "no longer applies after the v2 cache rewrite")
    assert el.validate_reason("x" * 500) == "x" * 500


@pytest.fixture
def no_db(monkeypatch):
    def boom():
        raise AssertionError("malformed input must be rejected before any database access")
    monkeypatch.setattr(el, "_connect", boom)


@pytest.mark.parametrize("call", [
    lambda s: s.retire("K-1", project_id=1, approval_key="A", reason=""),
    lambda s: s.retire("K-1", project_id=1, approval_key="A", reason="x" * 501),
    lambda s: s.retire("K-1", project_id=1, approval_key="A", reason='password: "synthetic-value"'),
    lambda s: s.retire("", project_id=1, approval_key="A", reason="r"),
    lambda s: s.retire("K" * 301, project_id=1, approval_key="A", reason="r"),
    lambda s: s.retire("K-1", project_id=1, approval_key="", reason="r"),
    lambda s: s.retire("K-1", project_id=1, approval_key=None, reason="r"),
    lambda s: s.retire("K-1", project_id=True, approval_key="A", reason="r"),
    lambda s: s.retire("K-1", project_id="1", approval_key="A", reason="r"),
    lambda s: s.retire("K-1", project_id=0, approval_key="A", reason="r"),
    lambda s: s.retire("K-1", project_id=1, approval_key="A", reason="r", task_key=""),
    lambda s: s.supersede("K-1", "K-1", project_id=1, approval_key="A", reason="r"),
    lambda s: s.supersede("K-1", "", project_id=1, approval_key="A", reason="r"),
    lambda s: s.refresh("K-1", project_id=1, approval_key="A", reason="r", review_after=None),
    lambda s: s.refresh("K-1", project_id=1, approval_key="A", reason="r", review_after="2027-01-01T00:00:00+00:00"),
    lambda s: s.refresh("K-1", project_id=1, approval_key="A", reason="r", review_after=date(2027, 1, 1)),
    lambda s: s.refresh("K-1", project_id=1, approval_key="A", reason="r", review_after=datetime(2027, 1, 1)),
    lambda s: s.refresh("K-1", project_id=1, approval_key="A", reason="r", review_after=T0),
    lambda s: s.refresh("K-1", project_id=1, approval_key="A", reason="r", review_after=T0 - timedelta(seconds=1)),
])
def test_malformed_input_rejected_before_db(no_db, call):
    with pytest.raises(ValueError):
        call(ExperienceLifecycleService(clock=lambda: T0))


def test_company_scope_is_deferred_before_db(no_db):
    with pytest.raises(el.LifecycleDenied) as err:
        ExperienceLifecycleService(clock=lambda: T0).retire("K-1", project_id=None, approval_key="A", reason="r")
    assert err.value.code == "company_scope_deferred"


def test_naive_or_invalid_clock_is_rejected(no_db):
    for clock in (lambda: datetime(2026, 1, 1), lambda: "now"):
        with pytest.raises(ValueError, match="clock"):
            ExperienceLifecycleService(clock=clock).retire("K-1", project_id=1, approval_key="A", reason="r")
