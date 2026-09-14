from __future__ import annotations

from .redaction import redact_text


def _connect():
    from .db import connect
    return connect()


class PreferenceService:
    def set(self, key: str, statement: str, *, task_key: str) -> str:
        """Persist a literal user preference, not an agent's inferred personality."""
        if not key.strip() or not statement.strip():
            raise ValueError("preference key and exact user statement are required")
        safe = redact_text(statement)
        with _connect() as conn, conn.transaction():
            conn.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s,0))", ("preference:" + key,))
            event = conn.execute(
                "SELECT e.id,e.payload,t.project_id FROM vres.task_events e JOIN vres.tasks t ON t.id=e.task_id "
                "WHERE t.task_key=%s AND e.actor='user' AND e.event_type='USER_INSTRUCTION' ORDER BY e.id DESC LIMIT 1",
                (task_key,),
            ).fetchone()
            if not event or statement.strip() != str(event["payload"].get("text", "")).strip():
                raise ValueError("Preference must quote the actual latest user instruction, not an inferred preference")
            previous = conn.execute("SELECT * FROM vres.preferences WHERE preference_key=%s FOR UPDATE", (key,)).fetchone()
            if previous and previous["project_id"] != event["project_id"]:
                raise ValueError("Preference key belongs to another scope")
            if previous and previous["statement"] == safe and previous["source_event_id"] == event["id"]:
                return key
            if previous:
                conn.execute(
                    "INSERT INTO vres.preference_history(preference_key,statement,source,confidence,status,source_event_id,project_id) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s)",
                    (key, previous["statement"], previous["source"], previous["confidence"], previous["status"],
                     previous["source_event_id"], previous["project_id"]),
                )
            conn.execute(
                "INSERT INTO vres.preferences(preference_key,statement,source,confidence,source_event_id,project_id) "
                "VALUES (%s,%s,'user-event',1,%s,%s) ON CONFLICT(preference_key) DO UPDATE SET "
                "statement=excluded.statement,source=excluded.source,source_event_id=excluded.source_event_id,"
                "confidence=1,status='active',updated_at=now()",
                (key, safe, event["id"], event["project_id"]),
            )
        return key

    def list_active(self, project_id: int | None = None) -> list[dict]:
        with _connect() as conn:
            rows = conn.execute(
                "SELECT preference_key,statement,source,confidence,source_event_id,project_id FROM vres.preferences "
                "WHERE status='active' AND source_event_id IS NOT NULL AND (%s IS NULL OR project_id=%s) ORDER BY updated_at DESC",
                (project_id, project_id),
            ).fetchall()
        return [dict(r) for r in rows]
