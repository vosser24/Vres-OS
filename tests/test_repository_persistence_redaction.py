"""AUTHOR-ONLY / NOT_RUN: strict original Repository persistence regressions.

No installed FastMCP, native Claude, Windows or PostgreSQL access. All write
boundary checks use an in-memory connection double if later authorized to run.
"""
from __future__ import annotations

import json
from datetime import date

import pytest

from vres_os import repository as repository_module
from vres_os.redaction import redact, redact_for_persistence, redact_text


UNSAFE = "[REDACTED_UNSAFE_FIELD]"


@pytest.mark.parametrize("text", [
    "password=abc,def",
    "password: correct horse battery",
    "ssh_passphrase = tiny",
    "Authorization: Basic abc",
    "postgresql://service:synthetic-pass@host.example/db",
    'password="[REDACTED]"synthetic-tail',
    "password_policy: required-by-security",
])
def test_ambiguous_known_credentials_suppress_whole_persisted_string(text):
    assert redact_for_persistence(text) == UNSAFE


def test_clean_content_and_precisely_premasked_placeholder_are_preserved():
    assert redact_for_persistence("Inspect recorded result before resuming.") == (
        "Inspect recorded result before resuming."
    )
    assert redact_for_persistence("password=[REDACTED]") == "password=[REDACTED]"
    assert redact_for_persistence(17) == 17
    assert redact_for_persistence(date(2026, 11, 18)) == "2026-11-18"


def test_original_display_redactors_are_unchanged():
    assert redact_text("password=synthetic-secret") == "password=[REDACTED]"
    assert redact({"message": "password=synthetic-secret"}) == {
        "message": "password=[REDACTED]"
    }


def test_nested_structures_keep_safe_siblings_and_mask_only_tainted_scalar():
    payload = {
        "summary": "Complete the source review.",
        "state": ["Inspect", "password=abc,def", {"next": "Review issue 185"}],
        "DATABASE_PASSWORD": "synthetic-secret",
    }
    safe = redact_for_persistence(payload)
    assert safe == {
        "summary": "Complete the source review.",
        "state": ["Inspect", UNSAFE, {"next": "Review issue 185"}],
        "DATABASE_PASSWORD": "[REDACTED]",
    }
    assert "abc" not in json.dumps(safe) and "synthetic-secret" not in json.dumps(safe)
    assert redact_for_persistence(safe) == safe


def test_nested_depth_limit_still_fails_closed():
    nested = "plain"
    for _ in range(34):
        nested = [nested]
    with pytest.raises(ValueError, match="nesting exceeds"):
        redact_for_persistence(nested)



@pytest.mark.parametrize("text", [
    "password=[REDACTED],def",
    "password: [REDACTED] horse battery",
    'db_credential="[REDACTED]" synthetic-tail',
    "Authorization: [REDACTED_SECRET] extra-content",
])
def test_previously_partial_masks_with_suspicious_tails_fail_closed(text):
    """AUTHOR-ONLY / NOT_RUN: legacy partial masks are not safe storage input."""
    assert redact_for_persistence(text) == UNSAFE


class _Cursor:
    def __init__(self, row=None):
        self.row = row

    def fetchone(self):
        return self.row


class _NoDbConnection:
    """Explicitly local test double; never opens a real connection."""

    def __init__(self):
        self.statements = []

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def transaction(self):
        return self

    def execute(self, sql, params=None):
        self.statements.append((sql, params))
        if "INSERT INTO vres.tasks(" in sql or "SELECT id FROM vres.tasks WHERE task_key" in sql:
            return _Cursor({"id": 19})
        if "SELECT * FROM vres.task_state" in sql:
            return _Cursor({"state_summary": "Prior", "validation_status": "pending"})
        return _Cursor()


@pytest.fixture
def fake_connection(monkeypatch):
    fake = _NoDbConnection()
    monkeypatch.setattr(repository_module, "connect", lambda: fake)
    return fake


def _single_statement(fake, fragment):
    matches = [(sql, params) for sql, params in fake.statements if fragment in sql]
    assert len(matches) == 1
    return matches[0][1]


def test_original_begin_task_never_stores_partial_objective(fake_connection):
    repository_module.Repository().begin_task(
        project_id=7, title="Follow up with reviewer",
        objective="password: correct horse battery",
        task_family=None, lead_role="chairman",
    )
    row = _single_statement(fake_connection, "INSERT INTO vres.tasks(")
    assert row[2] == "Follow up with reviewer"
    assert row[3] == UNSAFE
    seed = _single_statement(fake_connection, "INSERT INTO vres.task_state(")
    assert "correct horse battery" not in str(seed)
    assert UNSAFE in str(seed)


def test_original_event_jsonb_preserves_only_clean_siblings(fake_connection):
    repository_module.Repository().record_event(
        "TASK-TEST", "TASK_UPDATED", "chairman",
        {"summary": "password=abc,def", "next": "Inspect safe notes"},
    )
    event = _single_statement(fake_connection, "INSERT INTO vres.task_events(")
    payload = json.loads(event[3])
    assert payload == {"summary": UNSAFE, "next": "Inspect safe notes"}
    assert "abc,def" not in event[3]


def test_original_state_update_uses_same_strict_write_and_compare(fake_connection):
    repository_module.Repository().update_state("TASK-TEST", state_summary="password=abc,def")
    update = _single_statement(fake_connection, "UPDATE vres.task_state SET")
    assert update[0] == UNSAFE
    assert not any("abc,def" in str(params) for sql, params in fake_connection.statements
                   if sql.startswith("UPDATE "))


def test_original_checkpoint_jsonb_and_completion_use_strict_boundary(fake_connection):
    owner = repository_module.Repository()
    owner.checkpoint(
        "TASK-TEST", "password=abc,def", "review", "Read issue 185",
        {"notes": "password: correct horse battery", "safe": "Keep context"},
        "material_transition", "chairman",
    )
    cp = _single_statement(fake_connection, "INSERT INTO vres.checkpoints(")
    assert cp[2] == UNSAFE
    assert json.loads(cp[5]) == {"notes": UNSAFE, "safe": "Keep context"}
    assert "abc,def" not in str(cp) and "correct horse battery" not in str(cp)
