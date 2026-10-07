"""#176 E4: source revocation counts an episode as support only when its lifecycle state is eligible (PostgreSQL)."""
import json
import uuid

import pytest

pytest.importorskip("psycopg")

pytestmark = pytest.mark.usefixtures("provenance_writer")

from source_revocation_support import (  # noqa: E402
    approve, derived, episode, events, evidence, knowledge, revoke, source, status,
)
from vres_os.db import connect  # noqa: E402
from vres_os.experience_lifecycle import POLICY_VERSION  # noqa: E402


def _state_event(pid, ekey, action, new_state):
    """Append a legitimate (CHECK-satisfying) episode lifecycle event with an arbitrary stored new_state."""
    approval_id = None
    if action == "restore_derived":
        apr = approve(pid, f"restore:{ekey}")
        with connect() as conn:
            approval_id = conn.execute("SELECT id FROM vres.approval_events WHERE approval_key=%s",
                                       (apr,)).fetchone()["id"]
    with connect() as conn, conn.transaction():
        conn.execute(
            """INSERT INTO vres.experience_lifecycle_events(event_key,idempotency_key,project_id,policy_version,action,
               target_kind,target_key,prior_state,new_state,cause_kind,cause_key,approval_event_id,reason,detail)
               VALUES (%s,%s,%s,%s,%s,'episode',%s,NULL,%s,'time',%s,%s,'e4 state test',%s::jsonb)""",
            (f"LCE-{uuid.uuid4().hex}", uuid.uuid4().hex * 2, pid, POLICY_VERSION, action, ekey, new_state,
             ekey, approval_id, json.dumps({})))


def _setup(pid, *, extra_roots=0):
    """K depends on revoked-to-be root s only through episode E; E is also supported by an independent active source."""
    s, s2 = source(pid), source(pid)
    k, e = knowledge(pid), episode(pid)
    evidence(k, s)
    derived("knowledge", k, "episode", e)
    derived("episode", e, "source", s2)
    return s, k, e


def test_a_untouched_episode_is_valid_support(pg_project):
    s, k, _e = _setup(pg_project)
    out = revoke(pg_project, s)
    assert out["retained_with_support"] == [k] and out["revoked_knowledge"] == []
    assert out["counts"]["corrupt_provenance"] == 0 and status(k) == "validated"


def test_b_explicit_grounded_latest_event_is_support(pg_project):
    s, k, e = _setup(pg_project)
    _state_event(pg_project, e, "invalidate_derived", "revoked")
    _state_event(pg_project, e, "restore_derived", "grounded")
    out = revoke(pg_project, s)
    assert out["retained_with_support"] == [k] and out["counts"]["corrupt_provenance"] == 0
    assert status(k) == "validated"


def test_c_revoked_episode_is_not_support_and_not_corrupt(pg_project):
    s, k, e = _setup(pg_project)
    _state_event(pg_project, e, "invalidate_derived", "revoked")
    out = revoke(pg_project, s)
    assert out["revoked_knowledge"] == [k] and out["counts"]["corrupt_provenance"] == 0
    assert status(k) == "revoked"


@pytest.mark.parametrize("state", ["quarantined", None, "Grounded", "restored-ish", ""])
def test_d_e_unknown_null_or_malformed_state_is_not_support(pg_project, state):
    s, k, e = _setup(pg_project)
    _state_event(pg_project, e, "invalidate_derived", state)
    out = revoke(pg_project, s)
    assert out["revoked_knowledge"] == [k] and out["retained_with_support"] == []
    assert out["counts"]["corrupt_provenance"] == 1
    assert status(k) == "revoked"


def test_f_mixed_corrupt_episode_and_healthy_root(pg_project):
    s, s3 = source(pg_project), source(pg_project)
    s2 = source(pg_project)
    k, e_bad = knowledge(pg_project), episode(pg_project)
    evidence(k, s)
    derived("knowledge", k, "episode", e_bad)
    derived("episode", e_bad, "source", s2)
    derived("knowledge", k, "source", s3)
    _state_event(pg_project, e_bad, "invalidate_derived", "quarantined")
    out = revoke(pg_project, s)
    assert out["retained_with_support"] == [k] and out["revoked_knowledge"] == []
    assert out["counts"]["corrupt_provenance"] == 1 and status(k) == "validated"


def test_g_corrupt_only_support_revokes_knowledge(pg_project):
    s, k, e = _setup(pg_project)
    _state_event(pg_project, e, "invalidate_derived", "quarantined")
    out = revoke(pg_project, s)
    assert out["revoked_knowledge"] == [k] and status(k) == "revoked"
    assert [ev["target_key"] for ev in events(pid=pg_project) if ev["cause_kind"] == "source"] == [k]


def test_h_duplicate_paths_through_corrupt_episode_are_not_independent(pg_project):
    s, s2 = source(pg_project), source(pg_project)
    k, k2, e = knowledge(pg_project), knowledge(pg_project), episode(pg_project)
    evidence(k, s)
    evidence(k2, s)
    derived("knowledge", k, "episode", e)
    derived("knowledge", k, "knowledge", k2)
    derived("knowledge", k2, "episode", e)
    derived("episode", e, "source", s2)
    _state_event(pg_project, e, "invalidate_derived", "quarantined")
    out = revoke(pg_project, s)
    assert sorted(out["revoked_knowledge"]) == sorted([k, k2]) and out["retained_with_support"] == []
    assert out["counts"]["corrupt_provenance"] == 1
