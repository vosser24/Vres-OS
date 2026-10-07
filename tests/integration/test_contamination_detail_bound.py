"""#176 E4 hardening: a contamination whose key lists exceed the 8 KiB ledger bound stays digest-only end to end."""
import hashlib
import io
import json
import uuid

import pytest

pytest.importorskip("psycopg")

pytestmark = pytest.mark.usefixtures("provenance_writer")

from source_revocation_support import mk, trusted_ack  # noqa: E402
from vres_os import control_preflight  # noqa: E402
from vres_os.db import connect  # noqa: E402
from vres_os.experience_lifecycle import _lock_project  # noqa: E402
from vres_os.repository import Repository  # noqa: E402
from vres_os.session_contamination import (  # noqa: E402
    contamination_state,
    mark_open_sessions_contaminated,
)
from vres_os.source_revocation import MAX_DETAIL_BYTES, bounded_detail  # noqa: E402

LISTS = ("revoked_knowledge", "revoked_episodes")


class _ConfiguredStore:
    def load(self):
        return type("C", (), {"configured": True})()


def _keys(n, prefix="KNOW"):
    return [f"{prefix}-{uuid.uuid4().hex}" for _ in range(n)]


def _sha(keys) -> str:
    return hashlib.sha256(json.dumps(sorted(keys), separators=(",", ":")).encode()).hexdigest()


def _mark(pid, source_key, knowledge_keys, episode_keys):
    lists = {"revoked_knowledge": knowledge_keys, "revoked_episodes": episode_keys}
    assert len(json.dumps({"cause_event_key": "x", **lists}, sort_keys=True).encode()) > MAX_DETAIL_BYTES
    detail = bounded_detail({"cause_event_key": f"LCE-{uuid.uuid4().hex}"}, lists)
    with connect() as conn, conn.transaction():
        _lock_project(conn, pid)  # the caller-holds-the-lock contract of mark_open_sessions_contaminated
        assert mark_open_sessions_contaminated(conn, project_id=pid, source_key=source_key, approval_event_id=None,
                                               task_id=None, detail=detail) == 1
    return detail


def _row(pid, session_key, action):
    with connect() as conn:
        return conn.execute(
            "SELECT event_key,detail,detail::text AS text,octet_length(detail::text) AS bytes,reason "
            "FROM vres.experience_lifecycle_events WHERE project_id=%s AND session_key=%s AND action=%s "
            "ORDER BY id DESC LIMIT 1", (pid, session_key, action)).fetchone()


def _deny_reason(monkeypatch, capsys, sid):
    monkeypatch.setattr(control_preflight, "ConfigStore", _ConfiguredStore)
    payload = {"hook_event_name": "PreToolUse", "tool_name": "Bash", "session_id": sid,
               "tool_input": {"command": "echo hi"}}
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(payload)))
    assert control_preflight.main() == 0
    out = json.loads(capsys.readouterr().out)["hookSpecificOutput"]
    assert out["permissionDecision"] == "deny"
    return out["permissionDecisionReason"]


def _contaminate_and_ack(pid, monkeypatch, capsys, source_key, knowledge_keys, episode_keys):
    sid = f"host-{mk()}"
    session_key = Repository().open_session(pid, sid)
    detail = _mark(pid, source_key, knowledge_keys, episode_keys)

    row = _row(pid, session_key, "context_contaminated")
    assert row["bytes"] <= MAX_DETAIL_BYTES and len(row["text"].encode()) <= MAX_DETAIL_BYTES
    assert json.loads(row["text"]) == row["detail"] == detail
    assert set(row["detail"]) == {"cause_event_key", "keys_digest_only", *(f"{n}_sha256" for n in LISTS)}
    assert row["detail"]["keys_digest_only"] is True and not any(n in row["detail"] for n in LISTS)
    assert row["detail"]["revoked_knowledge_sha256"] == _sha(knowledge_keys)
    assert row["detail"]["revoked_episodes_sha256"] == _sha(episode_keys)
    assert "KNOW-" not in row["text"] and "EPI-" not in row["text"]

    with connect() as conn:
        state = contamination_state(conn, pid, session_key)
    assert state["contaminated"] is True and state["event_key"] == row["event_key"]
    reason = _deny_reason(monkeypatch, capsys, sid)
    assert "context refresh required" in reason and row["event_key"] in reason
    assert "KNOW-" not in reason and "EPI-" not in reason and source_key not in reason and "_sha256" not in reason

    out = trusted_ack(pid, sid, row["event_key"])
    assert out["new_state"] == "clean" and out["replayed"] is False
    ack = _row(pid, session_key, "context_refreshed")
    expected = _sha({source_key, f"revoked_knowledge_sha256:{_sha(knowledge_keys)}",
                     f"revoked_episodes_sha256:{_sha(episode_keys)}"})
    assert ack["detail"]["exclusion_sha256"] == expected and ack["detail"]["exclusion_count"] == 3
    assert ack["bytes"] <= MAX_DETAIL_BYTES and "KNOW-" not in ack["text"]
    Repository().close_session(pid, sid, "test")
    return ack["detail"]["exclusion_sha256"]


def test_detail_above_8kib_is_digest_only_bounded_acknowledgeable_and_never_leaks_keys(pg_project, monkeypatch,
                                                                                      capsys):
    source_key = f"SRC-{uuid.uuid4().hex}"
    knowledge_keys, episode_keys = _keys(700), _keys(40, "EPI")
    first = _contaminate_and_ack(pg_project, monkeypatch, capsys, source_key, knowledge_keys, episode_keys)
    # same source, same counts, one different revoked key: the attested exclusion digest must change
    changed = [*knowledge_keys[:-1], f"KNOW-{uuid.uuid4().hex}"]
    second = _contaminate_and_ack(pg_project, monkeypatch, capsys, source_key, changed, episode_keys)
    assert second != first
    # and it is a pure function of the digest entries: the same lists in another order give the same digest
    third = _contaminate_and_ack(pg_project, monkeypatch, capsys, source_key, list(reversed(knowledge_keys)),
                                 episode_keys)
    assert third == first
