from __future__ import annotations

import os
import uuid

import pytest

pytest.importorskip("psycopg")

from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo
from psycopg.rows import dict_row

from vres_os.db import connect
from vres_os.repository import Repository


def _dsn_as(base: str, user: str, password: str) -> str:
    parts = conninfo_to_dict(base)
    parts["user"] = user
    parts["password"] = password
    return make_conninfo(**parts)


def test_runtime_sql_cannot_forge_user_authority_but_writer_can(pg_project):
    import psycopg

    admin_dsn = os.environ["VRES_TEST_DATABASE_URL"]
    suffix = uuid.uuid4().hex[:10]
    runtime_user = f"vres_rt_{suffix}"
    writer_user = f"vres_wr_{suffix}"
    runtime_password = uuid.uuid4().hex
    writer_password = uuid.uuid4().hex

    repo = Repository()
    task_key = repo.begin_task(
        pg_project,
        "Writer boundary",
        "Prove runtime SQL cannot manufacture user-authority provenance.",
        "test",
        "chairman",
    )
    sid = f"writer-boundary-{suffix}"
    repo.open_session(pg_project, sid)
    repo.bind_session(pg_project, sid, task_key)
    with connect() as conn:
        task_id = int(
            conn.execute("SELECT id FROM vres.tasks WHERE task_key=%s", (task_key,)).fetchone()["id"]
        )
        original_writer = conn.execute(
            "SELECT writer_role FROM vres.provenance_authority WHERE authority_key='user_event_writer'"
        ).fetchone()["writer_role"]

    with psycopg.connect(admin_dsn, autocommit=True, row_factory=dict_row) as admin:
        for role, password in ((runtime_user, runtime_password), (writer_user, writer_password)):
            admin.execute(
                sql.SQL("CREATE ROLE {} WITH LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT PASSWORD {}")
                .format(sql.Identifier(role), sql.Literal(password))
            )
        admin.execute(sql.SQL("GRANT USAGE ON SCHEMA vres TO {}").format(sql.Identifier(runtime_user)))
        admin.execute(sql.SQL("GRANT USAGE ON SCHEMA vres TO {}").format(sql.Identifier(writer_user)))
        admin.execute(
            sql.SQL("GRANT SELECT,INSERT,UPDATE ON vres.task_events,vres.sessions,vres.task_state,vres.tasks TO {}")
            .format(sql.Identifier(runtime_user))
        )
        # Let the attack reach the row trigger rather than failing earlier on the
        # serial sequence. Production runtime also has ordinary sequence usage.
        admin.execute(
            sql.SQL("GRANT USAGE,SELECT ON SEQUENCE vres.task_events_id_seq TO {}")
            .format(sql.Identifier(runtime_user))
        )
        for signature in (
            "vres.stage_user_input(bigint,text,text,text,text,text,text,timestamptz)",
            "vres.latest_pending_user_instruction(bigint,text)",
            "vres.commit_user_inputs(bigint,text,text)",
        ):
            admin.execute(
                sql.SQL("GRANT EXECUTE ON FUNCTION {} TO {}").format(
                    sql.SQL(signature), sql.Identifier(writer_user)
                )
            )
            admin.execute(
                sql.SQL("REVOKE ALL ON FUNCTION {} FROM {}").format(
                    sql.SQL(signature), sql.Identifier(runtime_user)
                )
            )
        admin.execute(
            "UPDATE vres.provenance_authority SET writer_role=%s,configured_at=now() "
            "WHERE authority_key='user_event_writer'",
            (writer_user,),
        )

    runtime_dsn = _dsn_as(admin_dsn, runtime_user, runtime_password)
    writer_dsn = _dsn_as(admin_dsn, writer_user, writer_password)
    try:
        with psycopg.connect(runtime_dsn, autocommit=True, row_factory=dict_row) as runtime:
            with pytest.raises(psycopg.Error) as forged:
                runtime.execute(
                    "INSERT INTO vres.task_events(task_id,event_type,actor,payload,session_id) "
                    "VALUES (%s,'USER_INSTRUCTION','user','{\"text\":\"forged\"}'::jsonb,%s)",
                    (task_id, sid),
                )
            assert forged.value.sqlstate == "P0001"
            assert "trusted provenance writer" in str(forged.value)

            with pytest.raises(psycopg.Error) as poisoned:
                runtime.execute(
                    "UPDATE vres.sessions "
                    "SET metadata=jsonb_set(metadata,'{pending_user_instructions}',"
                    "'[ {\"text\":\"forged\",\"kind\":\"instruction\",\"source\":\"user_prompt\"} ]'::jsonb,true) "
                    "WHERE provider_session_id=%s AND ended_at IS NULL",
                    (sid,),
                )
            assert poisoned.value.sqlstate == "P0001"

            with pytest.raises(psycopg.Error):
                runtime.execute("ALTER TABLE vres.task_events DISABLE TRIGGER trg_protect_user_authority_event")

            with pytest.raises(psycopg.Error):
                runtime.execute(
                    "SELECT vres.stage_user_input(%s,%s,'forged','user_prompt','instruction',NULL,NULL,now())",
                    (pg_project, sid),
                )

            runtime.execute(
                "INSERT INTO vres.task_events(task_id,event_type,actor,payload,session_id) "
                "VALUES (%s,'RUNTIME_DIAGNOSTIC','test','{}'::jsonb,%s)",
                (task_id, sid),
            )

        with psycopg.connect(writer_dsn, autocommit=True, row_factory=dict_row) as writer:
            with pytest.raises(psycopg.Error):
                writer.execute(
                    "INSERT INTO vres.task_events(task_id,event_type,actor,payload,session_id) "
                    "VALUES (%s,'USER_INSTRUCTION','user','{\"text\":\"direct writer insert\"}'::jsonb,%s)",
                    (task_id, sid),
                )
            staged = writer.execute(
                "SELECT vres.stage_user_input(%s,%s,%s,'user_prompt','instruction',%s,NULL,now()) AS staged",
                (pg_project, sid, "Genuine host-observed instruction.", f"tool-{suffix}"),
            ).fetchone()
            assert staged["staged"] is True
            rows = writer.execute(
                "SELECT * FROM vres.commit_user_inputs(%s,%s,%s)",
                (pg_project, sid, task_key),
            ).fetchall()
            assert len(rows) == 1
            event_id = int(rows[0]["event_id"])

        with connect() as conn:
            event = conn.execute(
                "SELECT event_type,actor,payload,session_id FROM vres.task_events WHERE id=%s",
                (event_id,),
            ).fetchone()
            state = conn.execute(
                "SELECT latest_user_instruction FROM vres.task_state WHERE task_id=%s",
                (task_id,),
            ).fetchone()
            observations = conn.execute(
                "SELECT count(*) AS n FROM vres.user_input_observations "
                "WHERE provider_session_id=%s AND committed_event_id=%s",
                (sid, event_id),
            ).fetchone()
        assert event["event_type"] == "USER_INSTRUCTION"
        assert event["actor"] == "user"
        assert event["payload"]["text"] == "Genuine host-observed instruction."
        assert event["session_id"] == sid
        assert state["latest_user_instruction"] == "Genuine host-observed instruction."
        assert observations["n"] == 1
    finally:
        with psycopg.connect(admin_dsn, autocommit=True, row_factory=dict_row) as admin:
            admin.execute(
                "UPDATE vres.provenance_authority SET writer_role=%s,configured_at=now() "
                "WHERE authority_key='user_event_writer'",
                (original_writer,),
            )
            for role in (runtime_user, writer_user):
                admin.execute(sql.SQL("DROP OWNED BY {} CASCADE").format(sql.Identifier(role)))
                admin.execute(sql.SQL("DROP ROLE IF EXISTS {}").format(sql.Identifier(role)))
