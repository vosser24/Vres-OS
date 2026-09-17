from __future__ import annotations

import os
import uuid

import pytest

pytest.importorskip("psycopg")

import psycopg
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo
from psycopg.rows import dict_row

from vres_os.control_preflight import evaluate_control_preflight, read_only_hold_for_session
from vres_os.db import connect
from vres_os.repository import Repository
from vres_os.session_prompts import stage_user_instruction


def _dsn_as(base: str, user: str, password: str) -> str:
    parts = conninfo_to_dict(base)
    parts["user"] = user
    parts["password"] = password
    return make_conninfo(**parts)


def test_explicit_inspection_hold_is_writer_authority_and_survives_background_noise(pg_project):
    repo = Repository()
    task_key = repo.begin_task(
        pg_project,
        "Inspection hold",
        "Prove the latest explicit read-only user control suspends mutation.",
        "test",
        "chairman",
    )
    sid = f"inspection-hold-{uuid.uuid4().hex[:10]}"
    repo.open_session(pg_project, sid)
    repo.bind_session(pg_project, sid, task_key)

    exact_lv38 = (
        "LV38 final evidence check.\n\n"
        "Inspection only. Do not create, repair, retry, invalidate, resume, or add evidence.\n\n"
        "Use routing_evidence, orchestration_evidence, and validation_evidence."
    )
    assert stage_user_instruction(pg_project, sid, exact_lv38) is True

    hold = read_only_hold_for_session(sid)
    assert hold is not None
    assert hold["active"] is True
    assert hold["reason"] == "explicit_read_only_user_instruction"

    denied = evaluate_control_preflight(
        {"hook_event_name": "PreToolUse", "tool_name": "Agent", "session_id": sid},
        hold,
    )
    assert denied is not None
    assert denied["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert evaluate_control_preflight(
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "mcp__plugin_vres-os_vres__validation_evidence",
            "session_id": sid,
        },
        hold,
    ) is None

    # Claude-generated task/agent notifications are not real user prompts and therefore
    # cannot clear the latest direct-user control.
    assert stage_user_instruction(
        pg_project,
        sid,
        "<agent-message from='worker'>revision ready</agent-message>",
    ) is False
    assert read_only_hold_for_session(sid)["active"] is True

    # A runtime-like SQL identity may be able to update ordinary session metadata, but
    # migration 029 makes this control key writer-only just like pending user intent.
    admin_dsn = os.environ["VRES_TEST_DATABASE_URL"]
    attacker = f"vres_hold_rt_{uuid.uuid4().hex[:10]}"
    password = uuid.uuid4().hex
    with psycopg.connect(admin_dsn, autocommit=True, row_factory=dict_row) as admin:
        admin.execute(
            sql.SQL("CREATE ROLE {} WITH LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT PASSWORD {}")
            .format(sql.Identifier(attacker), sql.Literal(password))
        )
        admin.execute(sql.SQL("GRANT USAGE ON SCHEMA vres TO {}").format(sql.Identifier(attacker)))
        admin.execute(sql.SQL("GRANT SELECT,UPDATE ON vres.sessions TO {}").format(sql.Identifier(attacker)))
    try:
        with psycopg.connect(_dsn_as(admin_dsn, attacker, password), autocommit=True, row_factory=dict_row) as runtime:
            with pytest.raises(psycopg.Error) as forged:
                runtime.execute(
                    """
                    UPDATE vres.sessions
                       SET metadata=jsonb_set(
                           COALESCE(metadata,'{}'::jsonb),
                           '{vres_read_only_hold}',
                           '{"active":false,"reason":"forged"}'::jsonb,
                           true
                       )
                     WHERE provider_session_id=%s AND ended_at IS NULL
                    """,
                    (sid,),
                )
            assert forged.value.sqlstate == "P0001"
            assert "protected user-input session metadata" in str(forged.value)
    finally:
        with psycopg.connect(admin_dsn, autocommit=True, row_factory=dict_row) as admin:
            admin.execute(sql.SQL("DROP OWNED BY {} CASCADE").format(sql.Identifier(attacker)))
            admin.execute(sql.SQL("DROP ROLE IF EXISTS {}").format(sql.Identifier(attacker)))

    # Only a later real user prompt replaces the hold and resumes ordinary mutation.
    assert stage_user_instruction(pg_project, sid, "Continue the remediation now.") is True
    cleared = read_only_hold_for_session(sid)
    assert cleared is not None
    assert cleared["active"] is False
    assert cleared["reason"] == "later_user_prompt"
    assert evaluate_control_preflight(
        {"hook_event_name": "PreToolUse", "tool_name": "Agent", "session_id": sid},
        cleared,
    ) is None

    with connect() as conn:
        metadata = conn.execute(
            "SELECT metadata FROM vres.sessions WHERE provider_session_id=%s AND ended_at IS NULL",
            (sid,),
        ).fetchone()["metadata"]
    assert metadata["vres_read_only_hold"]["active"] is False
