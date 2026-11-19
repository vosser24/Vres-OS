"""Synthetic source tests for ORIGINAL provenance outward and validator writer R-9.

AUTHORED, NOT_RUN. No database, native host or Windows test execution claimed.
"""
import json

import pytest

from vres_os import hooks, session_prompts, validation_audit


def test_historical_pending_mirror_strictly_suppresses_text_and_question():
    metadata = {
        "pending_user_instructions": [
            {
                "text": "password=synthetic,tail",
                "question": "client_secret=synthetic,tail",
                "source": "ask_user_question",
                "kind": "instruction",
                "tool_use_id": "TOOL-CLEAN",
            },
            {"text": "Clean follow-up", "kind": "instruction"},
        ]
    }
    entries = session_prompts.pending_user_entries(metadata)
    assert len(entries) == 2
    assert entries[0]["text"] == "[REDACTED_UNSAFE_FIELD]"
    assert entries[0]["question"] == "[REDACTED_UNSAFE_FIELD]"
    assert entries[0]["tool_use_id"] == "TOOL-CLEAN"
    assert entries[1]["text"] == "Clean follow-up"


def test_historical_pending_mirror_refuses_secret_bearing_json_keys():
    metadata = {
        "pending_user_instructions": [
            {"text": "Clean", "password=synthetic,tail": "value"},
        ]
    }
    assert session_prompts.pending_user_entries(metadata) == []


def test_legacy_pending_mirror_cannot_echo_raw_credential():
    metadata = {
        "pending_user_instruction": {
            "text": "password=synthetic,tail",
            "recorded_at": "2026-11-18T12:00:00+00:00",
        }
    }
    entries = session_prompts.pending_user_entries(metadata)
    assert entries[0]["text"] == "[REDACTED_UNSAFE_FIELD]"


def test_historical_committed_tool_identifiers_drop_tainted_and_oversized():
    metadata = {
        "committed_user_input_tool_ids": [
            "TOOL-CLEAN", "password=synthetic,tail", "X" * 301, 3, None
        ]
    }
    assert session_prompts.committed_user_input_tool_ids(metadata) == ["TOOL-CLEAN"]


def test_read_only_hold_mirror_sanitizes_historical_fields():
    hold = session_prompts.read_only_hold_from_metadata({
        "vres_read_only_hold": {
            "active": True,
            "observed_at": "2026-11-18T12:00:00+00:00",
            "reason": "password=synthetic,tail",
        }
    })
    assert hold["active"] is True
    assert hold["reason"] == "[REDACTED_UNSAFE_FIELD]"


def test_original_hook_error_log_never_persists_partial_display_mask(monkeypatch, tmp_path):
    monkeypatch.setattr(hooks, "logs_dir", lambda: tmp_path)
    hooks._log_hook_error("Stop", RuntimeError("password=synthetic,tail"))
    log = (tmp_path / "hook-errors.log").read_text(encoding="utf-8")
    assert "[REDACTED_UNSAFE_FIELD]" in log
    assert "synthetic" not in log
    assert "tail" not in log


class _FakeConnection:
    def __init__(self):
        self.calls = []

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def transaction(self):
        return self

    def execute(self, sql, params=()):
        self.calls.append((sql, params))
        return self


def test_validation_audit_direct_sql_fields_use_strict_persistence(monkeypatch):
    conn = _FakeConnection()
    monkeypatch.setattr(validation_audit, "connect", lambda: conn)
    result = validation_audit.record_validation_ingestion_attempt(
        {
            "agent_type": "password=synthetic,tail",
            "agent_id": "access_token=synthetic,tail",
            "password=synthetic,tail": "not a stored value",
        },
        7,
        accepted=False,
        reason="client_secret=synthetic,tail",
    )
    assert result["reason"] == "[REDACTED_UNSAFE_FIELD]"
    writes = [params for sql, params in conn.calls if "INSERT INTO vres.validation_ingestion_attempts" in sql]
    assert len(writes) == 1
    assert "synthetic" not in json.dumps(writes[0])
    assert "[REDACTED_UNSAFE_FIELD]" in json.dumps(writes[0])


@pytest.mark.parametrize("payload,request_key", [
    ({"session_id": "password=synthetic,tail"}, None),
    ({"session_id": "X" * 201}, None),
    ({}, "password=synthetic,tail"),
    ({}, "VAL-" + "X" * 201),
])
def test_validation_audit_refuses_tainted_or_oversized_identity_pre_connect(
    monkeypatch, payload, request_key
):
    connections = []
    monkeypatch.setattr(validation_audit, "connect", lambda: connections.append(True))
    with pytest.raises(ValueError):
        validation_audit.record_validation_ingestion_attempt(
            payload, 7, accepted=True, reason="Accepted", request_key=request_key
        )
    assert connections == []
