from __future__ import annotations

from typing import Any

from .redaction import redact_text

_ALLOWED_KINDS = {"knowledge", "registry", "procedure", "source", "artifact", "task"}
_ALLOWED_RELATIONS = {
    "depends_on", "uses", "produces", "consumes", "affects", "governed_by", "implements",
    "supersedes", "superseded_by", "informs", "derived_from", "related_to", "owned_by",
}


def _connect():
    from .db import connect

    return connect()


def _node(conn, kind: str, key: str) -> dict[str, Any]:
    if kind == "knowledge":
        row = conn.execute("SELECT id,project_id FROM vres.knowledge_items WHERE knowledge_key=%s", (key,)).fetchone()
    elif kind == "registry":
        row = conn.execute("SELECT id,project_id FROM vres.registry_objects WHERE object_key=%s", (key,)).fetchone()
    elif kind == "procedure":
        row = conn.execute("SELECT id,project_id FROM vres.procedures WHERE procedure_key=%s", (key,)).fetchone()
    elif kind == "source":
        row = conn.execute("SELECT id,project_id FROM vres.sources WHERE source_key=%s", (key,)).fetchone()
    elif kind == "artifact":
        row = conn.execute("SELECT id,project_id FROM vres.artifacts WHERE artifact_key=%s", (key,)).fetchone()
    elif kind == "task":
        row = conn.execute("SELECT id,project_id FROM vres.tasks WHERE task_key=%s", (key,)).fetchone()
    else:
        raise ValueError(f"Unsupported relation node kind {kind}")
    if not row:
        raise KeyError(f"Unknown {kind} node {key}")
    return dict(row)


def relate(
    source_kind: str,
    source_key: str,
    relation: str,
    target_kind: str,
    target_key: str,
    *,
    provenance: str,
    confidence: float | None = None,
) -> None:
    source_kind = source_kind.strip().lower()
    target_kind = target_kind.strip().lower()
    relation = relation.strip().lower()
    if source_kind not in _ALLOWED_KINDS or target_kind not in _ALLOWED_KINDS:
        raise ValueError("Unsupported relation node kind")
    if relation not in _ALLOWED_RELATIONS:
        raise ValueError(f"Unsupported relation type {relation}")
    if not provenance.strip():
        raise ValueError("Semantic relations require provenance")
    if confidence is not None and not 0 <= confidence <= 1:
        raise ValueError("relation confidence must be between 0 and 1")
    with _connect() as conn, conn.transaction():
        source = _node(conn, source_kind, source_key)
        target = _node(conn, target_kind, target_key)
        if source["project_id"] is not None and target["project_id"] is not None and source["project_id"] != target["project_id"]:
            raise ValueError("Cannot create a semantic relation across two different project-local objects")
        edge = conn.execute(
            """
            INSERT INTO vres.relations(source_kind,source_key,relation_type,target_kind,target_key,provenance,confidence)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT(source_kind,source_key,relation_type,target_kind,target_key)
            DO UPDATE SET id=vres.relations.id RETURNING id
            """,
            (source_kind, source_key, relation, target_kind, target_key, redact_text(provenance), confidence),
        ).fetchone()
        conn.execute(
            "INSERT INTO vres.relation_evidence(relation_id,provenance,confidence) VALUES (%s,%s,%s) "
            "ON CONFLICT(relation_id,provenance) DO NOTHING",
            (edge["id"], redact_text(provenance), confidence),
        )


_NODE_TABLES = {
    "knowledge": ("knowledge_items", "knowledge_key"),
    "registry": ("registry_objects", "object_key"),
    "procedure": ("procedures", "procedure_key"),
    "source": ("sources", "source_key"),
    "artifact": ("artifacts", "artifact_key"),
    "task": ("tasks", "task_key"),
}
# Only constant identifiers enter this SQL, never user-supplied identifiers.
_NODE_UNION = " UNION ALL ".join(
    f"SELECT '{kind}'::text AS kind,{key} AS key,project_id FROM vres.{table}"
    for kind, (table, key) in sorted(_NODE_TABLES.items())
)


def impact(object_key: str, *, object_kind: str | None = None, project_id: int | None = None,
           depth: int = 2, limit: int = 200) -> list[dict[str, Any]]:
    """Bounded typed traversal. An unknown object is not evidence of zero impact."""
    if object_kind is not None and object_kind not in _ALLOWED_KINDS:
        raise ValueError("Unsupported object kind")
    depth, limit = max(1, min(int(depth), 4)), max(1, min(int(limit), 500))
    with _connect() as conn:
        nodes = conn.execute(
            f"SELECT kind,key,project_id FROM ({_NODE_UNION}) n WHERE key=%s "
            "AND (%s IS NULL OR kind=%s) AND (%s IS NULL OR project_id=%s OR project_id IS NULL)",
            (object_key, object_kind, object_kind, project_id, project_id),
        ).fetchall()
        if not nodes:
            raise KeyError(f"Unknown or inaccessible semantic object {object_key}")
        if len(nodes) != 1:
            raise ValueError("Ambiguous semantic key; supply the object_kind instead of guessing")
        frontier = {(nodes[0]["kind"], nodes[0]["key"])}
        visited = set(frontier)
        result: dict[int, dict] = {}
        for level in range(1, depth + 1):
            if not frontier:
                break
            ordered = sorted(frontier)
            marks = ",".join("(%s,%s)" for _ in ordered)
            params = tuple(x for pair in ordered for x in pair)
            rows = conn.execute(
                f"SELECT r.*, (SELECT jsonb_agg(jsonb_build_object('provenance',e.provenance,"
                "'confidence',e.confidence,'created_at',e.created_at) ORDER BY e.id) "
                "FROM vres.relation_evidence e WHERE e.relation_id=r.id) AS evidence "
                f"FROM vres.relations r JOIN ({_NODE_UNION}) a ON (a.kind,a.key)=(r.source_kind,r.source_key) "
                f"JOIN ({_NODE_UNION}) b ON (b.kind,b.key)=(r.target_kind,r.target_key) "
                "WHERE (%s IS NULL OR a.project_id=%s OR a.project_id IS NULL) "
                "AND (%s IS NULL OR b.project_id=%s OR b.project_id IS NULL) AND "
                f"((r.source_kind,r.source_key) IN ({marks}) OR (r.target_kind,r.target_key) IN ({marks})) "
                "ORDER BY r.id LIMIT %s",
                (project_id, project_id, project_id, project_id) + params + params + (limit + 1,),
            ).fetchall()
            frontier = set()
            for edge in rows:
                result.setdefault(int(edge["id"]), dict(edge) | {"depth": level})
                for node in ((edge["source_kind"], edge["source_key"]), (edge["target_kind"], edge["target_key"])):
                    if node not in visited:
                        frontier.add(node)
                        visited.add(node)
            if len(result) > limit:
                raise ValueError("Impact exceeds the result budget; narrow the scope. Completeness cannot be asserted")
    return sorted(result.values(), key=lambda row: (row["depth"], row["id"]))
