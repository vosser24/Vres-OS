"""AUTHOR-ONLY / NOT_RUN: strict original Repository persistence regressions.

No installed FastMCP, native Claude, Windows or PostgreSQL access. All write
boundary checks use an in-memory connection double if later authorized to run.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from vres_os import repository as repository_module
from vres_os.redaction import redact, redact_for_persistence, redact_text
from vres_os.project import ProjectIdentity


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
        if "INSERT INTO vres.projects(" in sql:
            return _Cursor({"id": 7})
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

@pytest.mark.parametrize("secret_key", [
    "ssh_passphrase", "db_credential", "signing_key", "access_key",
    "encryption_key", "master_key", "client_key", "service_authorization",
    "auth", "key_data",
])
def test_original_repository_strictly_redacts_structured_secret_key_families(secret_key):
    """AUTHOR ONLY / NOT_RUN: plain values cannot bypass a sensitive mapping key."""
    value = "synthetic-mapping-secret"
    sanitized = redact_for_persistence({"safe": "Keep", secret_key: value, "source_key": "SRC-1"})
    assert sanitized == {"safe": "Keep", secret_key: "[REDACTED]", "source_key": "SRC-1"}
    assert value not in json.dumps(sanitized)


@pytest.mark.parametrize("credential_key", [
    "password=synthetic-dict-key-01",
    "ssh_passphrase: tiny",
    "Authorization: Basic synthetic-dict-key-02",
    "password=[REDACTED] synthetic-ambiguous-tail",
])
def test_original_repository_rejects_credential_text_in_json_keys(credential_key):
    """AUTHOR ONLY / NOT_RUN: keys need protection as well as JSON values."""
    sanitized = redact_for_persistence({
        "safe": "Retain this sibling",
        "details": {"safe_in_inner": "unsafe key makes this whole nested mapping ambiguous",
                    credential_key: "unrelated value"},
    })
    assert sanitized == {"safe": "Retain this sibling", "details": UNSAFE}
    assert "synthetic-dict-key" not in json.dumps(sanitized)
    assert redact_for_persistence(sanitized) == sanitized


def test_original_event_jsonb_structured_sensitive_keys_are_masked(fake_connection):
    """AUTHOR ONLY / NOT_RUN: actual owner recording route, fake DB only."""
    repository_module.Repository().record_event(
        "TASK-TEST", "TASK_UPDATED", "chairman",
        {"metadata": "safe", "context": {"db_credential": "synthetic-db-password",
                                          "signing_key": "synthetic-signing-material",
                                          "source_key": "SRC-1"}},
    )
    event = _single_statement(fake_connection, "INSERT INTO vres.task_events(")
    assert json.loads(event[3]) == {
        "metadata": "safe",
        "context": {"db_credential": "[REDACTED]",
                    "signing_key": "[REDACTED]", "source_key": "SRC-1"},
    }
    assert "synthetic-db-password" not in event[3]
    assert "synthetic-signing-material" not in event[3]

# R-5 source-only regressions, written against the original Repository with a
# fake connection. NOT_RUN: no actual source Python, PostgreSQL or host access.


def _project(*, key="project:synthetic", root=None, name="Safe project",
             remote_url=None, branch="main"):
    return ProjectIdentity(
        root=root or Path("/safe/synthetic-project"), key=key, name=name,
        remote_url=remote_url, branch=branch,
    )


def test_original_project_metadata_suppresses_secret_fields_without_changing_identity(fake_connection):
    project = _project(
        name="password: correct horse battery",
        remote_url="postgresql://synthetic-user:synthetic-pass@host.example/db",
        branch="ssh_passphrase: tiny",
    )
    assert repository_module.Repository().ensure_project(project) == 7
    params = _single_statement(fake_connection, "INSERT INTO vres.projects(")
    assert params == ("project:synthetic", UNSAFE, str(project.root), UNSAFE, UNSAFE)
    assert "synthetic-pass" not in str(params)
    assert "correct horse battery" not in str(params)


@pytest.mark.parametrize("field,value", [
    ("key", "password=synthetic-project-secret"),
    ("root", Path("/safe/password=synthetic-directory-secret")),
])
def test_project_join_or_path_identity_is_rejected_before_db_connect(monkeypatch, field, value):
    project = _project()
    setattr(project, field, value)

    def forbidden_connect():
        raise AssertionError("A rejected identity must never open the DB")

    monkeypatch.setattr(repository_module, "connect", forbidden_connect)
    with pytest.raises(ValueError, match="unsafe credential material"):
        repository_module.Repository().ensure_project(project)


@pytest.mark.parametrize("field,value", [
    ("task_family", "password=synthetic-task-family"),
    ("lead_role", "Authorization: Basic synthetic-role-value"),
])
def test_begin_task_authority_fields_cannot_enter_sql(fake_connection, field, value):
    kwargs = dict(project_id=7, title="Safe", objective="Safe objective",
                  task_family=None, lead_role="chairman")
    kwargs[field] = value
    with pytest.raises(ValueError, match="unsafe credential material"):
        repository_module.Repository().begin_task(**kwargs)
    assert fake_connection.statements == []


@pytest.mark.parametrize("field,value", [
    ("event_type", "password=synthetic-event-type"),
    ("actor", "ssh_passphrase: tiny"),
    ("session_id", "Authorization: Basic synthetic-session"),
])
def test_original_event_envelope_identifiers_reject_credential_material_before_connect(
    fake_connection, field, value
):
    kwargs = dict(task_key="TASK-SYNTHETIC", event_type="TASK_UPDATED",
                  actor="chairman", payload={"summary": "safe"}, session_id=None)
    kwargs[field] = value
    with pytest.raises(ValueError, match="unsafe credential material"):
        repository_module.Repository().record_event(**kwargs)
    assert fake_connection.statements == []


def test_original_session_close_masks_reason_and_keeps_binding_key(fake_connection):
    repository_module.Repository().close_session(
        7, "synthetic-claude-session", "password: correct horse battery"
    )
    sql, params = next(
        (sql, params) for sql, params in fake_connection.statements
        if "UPDATE vres.sessions SET ended_at" in sql
    )
    assert "provider_session_id" in sql
    assert params == (UNSAFE, "synthetic-claude-session", 7)


def test_original_checkpoint_reason_is_cleaned_without_changing_actor(fake_connection):
    repository_module.Repository().checkpoint(
        "TASK-SYNTHETIC", "Safe review", "position", "next",
        {"safe": "context"}, "ssh_passphrase: tiny", "chairman",
    )
    params = _single_statement(fake_connection, "INSERT INTO vres.checkpoints(")
    assert params[6] == UNSAFE
    assert params[7] == "chairman"


@pytest.mark.parametrize("method,kwargs", [
    ("open_session", {"project_id": 7, "provider_session_id": "password=synthetic-session"}),
    ("bind_session", {"project_id": 7, "provider_session_id": "password=synthetic-session",
                      "task_key": "TASK-SAFE"}),
])
def test_session_binding_identity_refused_before_db_connect(fake_connection, method, kwargs):
    with pytest.raises(ValueError, match="unsafe credential material"):
        getattr(repository_module.Repository(), method)(**kwargs)
    assert fake_connection.statements == []
