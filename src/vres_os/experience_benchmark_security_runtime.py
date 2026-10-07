"""E7 Chunk 5: security runtime - real-owner scenarios plus READ-ONLY evidence collection.

Scenario state is built only through the public E1-E6 owners (`BenchmarkRuntime`). Everything this
module adds is a read: SQL SELECTs for evidence, public owner reads, and the public E5 result of the
same candidate_hybrid retrieval call. Evidence is alias-normalized; no raw row, canary text, runtime
key, id or timestamp is emitted. The deterministic scorer lives in `experience_benchmark_security`.
"""

from __future__ import annotations

import json
from pathlib import Path

from . import experience_benchmark as eb
from . import experience_benchmark_retrieval as retrieval
from . import experience_benchmark_runtime as rt
from . import experience_benchmark_security as sec
from . import experience_consolidation as e2
from . import experience_lifecycle as e4
from . import experience_observability as e6
from . import experience_retrieval as er
from .db import connect
from .experience_benchmark import BenchmarkError

_FIXTURE_TASK = "benchmark approval fixture"
_HIDDEN_RE = r'"(' + "|".join(sec.HIDDEN_REASONING_KEYS) + r')"\s*:'


# ---- read-only SQL evidence (counts and categories only) ---


def _tables(conn) -> list[str]:
    rows = conn.execute(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema='vres' AND table_type='BASE TABLE' ORDER BY table_name"
    ).fetchall()
    return [r["table_name"] for r in rows]


def table_fingerprints(conn) -> dict[str, tuple[int, str]]:
    """{table: (row_count, server md5 of row text)}; digests stay in the collector."""
    out = {}
    for name in _tables(conn):
        row = conn.execute(
            f"SELECT count(*) AS n, "
            f"md5(coalesce(string_agg(t::text, E'\\n' ORDER BY t::text), '')) AS d "
            f'FROM vres."{name}" t'
        ).fetchone()
        out[name] = (int(row["n"]), row["d"])
    return out


def rewrite_evidence(before: dict, after: dict) -> dict:
    changed = sorted(t for t in set(before) | set(after) if before.get(t) != after.get(t))
    return {"tables_checked": sorted(before), "changed_tables": changed}


def exact_canary_hits(conn, canaries: list[str]) -> int:
    """Rows (every Vres base table) whose text holds an exact canary; a count only."""
    total = 0
    for name in _tables(conn):
        for canary in canaries:
            row = conn.execute(
                f'SELECT count(*) AS n FROM vres."{name}" t WHERE position(%s in t::text) > 0',
                (canary,),
            ).fetchone()
            total += int(row["n"])
    return total


def hidden_reasoning_scan(conn) -> dict:
    """Structural scan: prohibited column names and prohibited JSON keys in persisted rows."""
    findings = []
    tables = _tables(conn)
    for name in tables:
        cols = conn.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema='vres' AND table_name=%s",
            (name,),
        ).fetchall()
        if any(c["column_name"] in sec.HIDDEN_REASONING_KEYS for c in cols):
            findings.append(f"{name}:column")
        hits = conn.execute(
            f'SELECT count(*) AS n FROM vres."{name}" t WHERE t::text ~* %s', (_HIDDEN_RE,)
        ).fetchone()
        if int(hits["n"]):
            findings.append(f"{name}:json_key")
    return {"scanned": len(tables), "findings": sorted(findings)}


def user_instruction_events(conn, project_ids: list[int]) -> int:
    row = conn.execute(
        "SELECT count(*) AS n FROM vres.task_events e JOIN vres.tasks t ON t.id=e.task_id "
        "WHERE e.event_type='USER_INSTRUCTION' AND t.project_id = ANY(%s) AND t.title <> %s",
        (project_ids, _FIXTURE_TASK),
    ).fetchone()
    return int(row["n"])


# ---- alias-normalized owner state ---


def _ops(case: dict, op: str) -> list[dict]:
    return [s for s in case.get("timeline", []) if s["op"] == op]


def knowledge_state(conn, case: dict, amap) -> dict:
    out = {}
    for step in _ops(case, "knowledge_propose"):
        alias = step["alias"]
        row = conn.execute(
            "SELECT id, knowledge_type, status, superseded_by, approval_event_id, "
            "coalesce(metadata->>'trust_class', metadata->>'derived_trust_class', "
            "'unspecified') AS trust "
            "FROM vres.knowledge_items WHERE knowledge_key=%s",
            (amap.runtime_key_for(alias),),
        ).fetchone()
        sources = conn.execute(
            "SELECT s.source_key FROM vres.knowledge_evidence ev "
            "JOIN vres.sources s ON s.id=ev.source_id "
            "WHERE ev.knowledge_id=%s",
            (row["id"],),
        ).fetchall()
        successor = row["superseded_by"]
        out[alias] = {
            "alias": alias,
            "kind": "knowledge",
            "knowledge_type": row["knowledge_type"],
            "status": row["status"],
            "trust_class": row["trust"],
            "approval_present": row["approval_event_id"] is not None,
            "superseded_by": amap.alias_for(successor) if successor else None,
            "source_aliases": sorted(
                a for a in (amap.alias_for(s["source_key"]) for s in sources) if a is not None
            ),
        }
    return out


def source_state(conn, case: dict, amap, canaries: list[str]) -> dict:
    out = {}
    for step in _ops(case, "source_add"):
        alias = step["alias"]
        row = conn.execute(
            "SELECT id, status, authority_level FROM vres.sources WHERE source_key=%s",
            (amap.runtime_key_for(alias),),
        ).fetchone()
        present = False
        for canary in canaries:
            hit = conn.execute(
                "SELECT count(*) AS n FROM vres.knowledge_chunks WHERE source_id=%s "
                "AND position(%s in content) > 0",
                (row["id"], canary),
            ).fetchone()
            present = present or int(hit["n"]) > 0
        out[alias] = {
            "alias": alias,
            "state": "revoked" if row["status"] == "revoked" else "active",
            "authority_level": row["authority_level"],
            "canary_present": present,
        }
    return out


def procedure_state(conn, case: dict, amap) -> dict:
    out = {}
    for step in _ops(case, "procedure_candidate"):
        baseline = step["args"]["baseline"]
        proc = conn.execute(
            "SELECT id, preferred_version FROM vres.procedures WHERE procedure_key=%s",
            (amap.runtime_key_for(baseline),),
        ).fetchone()
        cand = conn.execute(
            "SELECT baseline_version, candidate_version, decision "
            "FROM vres.optimization_candidates "
            "WHERE procedure_id=%s ORDER BY id DESC LIMIT 1",
            (proc["id"],),
        ).fetchone()
        status = None
        if cand:
            ver = conn.execute(
                "SELECT status FROM vres.procedure_versions "
                "WHERE procedure_id=%s AND version_no=%s",
                (proc["id"], cand["candidate_version"]),
            ).fetchone()
            status = ver["status"] if ver else None
        out[baseline] = {
            "baseline_alias": baseline,
            "preferred_version_changed": bool(
                cand and proc["preferred_version"] != cand["baseline_version"]
            ),
            "candidate_decision": cand["decision"] if cand else None,
            "candidate_status": status,
            "candidate_auto_promoted": bool(cand and cand["decision"] == "auto_promoted"),
        }
    return out


def hybrid_view(result: dict, amap) -> list[dict]:
    """Closed security view of the PUBLIC E5 result of the same call (flattened)."""
    rows: list[dict] = []
    for section in er.SECTIONS:
        items = result[section]
        aliases = [rt._alias_of(item, amap) for item in items]
        for item, alias in rt._alias_tie_order(items, aliases):
            rows.append(
                {
                    "alias": alias,
                    "section": section,
                    "role": item["role"],
                    "authority_class": item["authority_class"],
                    "trust_class": item["trust_class"],
                    "flags": sorted(item.get("flags", [])),
                    "position": len(rows) + 1,
                }
            )
    return rows


def _knowledge_snapshots(runtime, case: dict, amap) -> dict:
    return {
        s["alias"]: rt.knowledge_snapshot(
            s["alias"], runtime.o.knowledge.get(amap.runtime_key_for(s["alias"])), amap
        )
        for s in _ops(case, "knowledge_propose")
    }


# ---- one case ---


def run_case(runtime: rt.BenchmarkRuntime, case: dict, expected: dict) -> dict:
    """Materialize once, run the three retrieval modes, collect read-only evidence, then score."""
    security = expected["security"]
    names = set(security["assertions"])
    amap = runtime.materialize(case)
    shared = retrieval.public_input(case)
    packs: dict[str, list[str]] = {}
    for mode in ("raw_refind", "current_vres"):
        got = runtime.adapters[mode].retrieve(shared, amap, runtime.scoring)
        packs[mode] = [i["alias"] for i in got["pack"]]
    track_rewrite = "retrieval_no_silent_rewrite" in names
    with connect() as conn:
        fp_before = table_fingerprints(conn) if track_rewrite else None
        snap_before = _knowledge_snapshots(runtime, case, amap)
        got = runtime.adapters["candidate_hybrid"].retrieve(shared, amap, runtime.scoring)
        packs["candidate_hybrid"] = [i["alias"] for i in got["pack"]]
        result = runtime.adapters["candidate_hybrid"].last_result
        snap_after = _knowledge_snapshots(runtime, case, amap)
        fp_after = table_fingerprints(conn) if track_rewrite else None
        canaries = sec.canaries(case, security.get("must_not_persist", []))
        evidence = {
            "packs": packs,
            "hybrid": hybrid_view(result, amap),
            "knowledge": knowledge_state(conn, case, amap),
            "sources": source_state(conn, case, amap, canaries),
            "procedures": procedure_state(conn, case, amap),
            "user_instruction_events": user_instruction_events(
                conn, runtime.case_project_ids(case["case_id"])
            ),
            "canary": {
                "exact_canary_hits": exact_canary_hits(conn, canaries) if canaries else 0,
                "hybrid_hits": sum(1 for c in canaries if c in json.dumps(result)),
            },
            "mutation": {"before": snap_before, "after": snap_after},
            "rewrite": rewrite_evidence(fp_before, fp_after)
            if track_rewrite
            else {"tables_checked": [], "changed_tables": []},
        }
    return sec.score_case(case, expected, evidence)


def owner_identities() -> dict:
    return {
        "e1_policy": "176.e1.v1",
        "e2_policy": e2.POLICY_VERSION,
        "e2_policy_digest": e2.POLICY_DIGEST,
        "e4_policy": e4.POLICY_VERSION,
        "e5_policy_digest": eb.sha256_hex(eb.canonical_bytes(er.POLICY)),
        "e6_policy": e6.POLICY_VERSION,
        "e6_policy_digest": e6.E6_POLICY_DIGEST,
        "e5_v1_policy_digest": e6.FROZEN_E5_V1_POLICY_DIGEST,
        "e5_v2_policy_digest": e6.FROZEN_E5_V2_POLICY_DIGEST,
    }


def run_security(
    runtime: rt.BenchmarkRuntime,
    root: str | Path,
    *,
    source: dict,
    order: list[str] | None = None,
) -> dict:
    """Run the adversarial split. Gap/N-A cases are admitted first and make zero owner calls."""
    bundle = eb.load_development_bundle(root, "adversarial")
    by_id = {c["case_id"]: c for c in bundle["cases"]}
    if order is not None and sorted(order) != sorted(by_id):
        raise BenchmarkError("security run order must be a permutation of the adversarial cases")
    results = []
    for case_id in order or sorted(by_id):
        case, expected = by_id[case_id], bundle["expected"][case_id]
        admission = sec.admit(case, expected)
        if admission["status"] == sec.NA:
            results.append(sec.na_result(case_id, admission["reason"]))
        elif admission["status"] == sec.GAP:
            results.append(sec.gap_result(case_id, admission["reasons"]))
        else:
            results.append(run_case(runtime, case, expected))
    with connect() as conn:
        hidden = hidden_reasoning_scan(conn)
    exposed = any(
        r["status"] != sec.NA
        and r["status"] != sec.GAP
        and (r["evidence"]["canary"]["exact_canary_hits"] or r["evidence"]["canary"]["hybrid_hits"])
        for r in results
    )
    return sec.build_security_run(
        split="adversarial",
        source=source,
        digests=bundle["digests"],
        scoring_digest=eb.scoring_digest(runtime.scoring),
        retrieval_identity=rt.retrieval_identity(),
        owner_identities=owner_identities(),
        cases=results,
        corpus_cases=bundle["cases"],
        expectations=bundle["expected"],
        run_evidence={"hidden_reasoning": hidden, "canary_exposure": exposed},
    )
