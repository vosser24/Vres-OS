"""#176 E7 Chunk 2: benchmark runtime - scenario materialization and the four frozen adapters.

Depends downward on the benchmark foundation, the retrieval scorer and the public E1-E6 owner
APIs; no E1-E6 module imports it. Truth is written only through public owner methods
(`OPERATION_OWNERS`); there is no benchmark SQL beyond `SELECT current_database()`.
"""

from __future__ import annotations

import hashlib
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from . import experience_benchmark as eb
from . import experience_benchmark_faithfulness as faithfulness
from . import experience_benchmark_outcome as outcome
from . import experience_benchmark_retrieval as retrieval
from . import experience_benchmark_streaming as streaming
from . import experience_benchmark_worker as worker
from . import experience_retrieval as er
from .experience_benchmark import BenchmarkError

# Owner-maximum native limits: the final cut is the common token budget only, never an item count.
RAW_REFIND_NATIVE_LIMIT = 50  # knowledge.chunk_search maximum
CURRENT_KNOWLEDGE_NATIVE_LIMIT = 50  # knowledge.search maximum
CURRENT_PROCEDURE_NATIVE_LIMIT = 20  # procedures.find_matches maximum
EXECUTABLE_OPS = (
    "source_add",
    "knowledge_propose",
    "knowledge_attach_source",
    "procedure_accept",
    "procedure_candidate",
    "knowledge_supersede",
    "knowledge_observe",
    "lifecycle_retire",
    "lifecycle_reinstate",
    "lifecycle_challenge",
    "lifecycle_supersede",
    "lifecycle_refresh",
    "source_revoke",
)
DEFAULT_TITLE = "Note"
INITIAL_STATUS = "proposed"  # the frozen OPERATION_OWNERS["knowledge_propose"] status
SOURCE_OWNER = "benchmark:176.e7"
_NON_SUPPORTING_ROLES = frozenset({"warning_example", "conflict", "stale_assumption"})
_KIND_BY_CLASS = {"procedural": "procedure", "raw_evidence": "chunk", "episodic": "experience"}


def retrieval_identity() -> dict:
    """Closed identity of the released retrieval policy the candidate_hybrid mode runs."""
    return {
        "experience_retrieval_schema": er.SCHEMA_VERSION,
        "e5_policy_digest": eb.sha256_hex(eb.canonical_bytes(er.POLICY)),
        "result_schema_version": retrieval.RESULT_SCHEMA_VERSION,
        "evidence_pack_schema": eb.SCHEMA_VERSIONS["evidence_pack"],
    }


# ---- pure row -> entry mappers (no database) ---


def _entry(alias: str, kind: str, content: str, rank: int) -> dict:
    return {"alias": alias, "kind": kind, "content": content, "rank": rank}


def raw_row_entry(row: dict, alias_map: eb.AliasMap, rank: int) -> dict:
    """One `chunk_search` row: source_key then knowledge_key owner; never ids or chunk keys."""
    alias = retrieval.resolve_reference(
        alias_map, [row.get("source_key"), row.get("knowledge_key")]
    )
    section = row.get("section")
    content = f"{section}\n{row['content']}" if section else row["content"]
    return _entry(alias, "chunk", content, rank)


def knowledge_row_entry(row: dict, alias_map: eb.AliasMap, rank: int) -> dict:
    alias = retrieval.resolve_reference(alias_map, [row["knowledge_key"]])
    return _entry(alias, "knowledge", f"{row['title']}: {row['statement']}", rank)


def _joined(value: Any) -> str:
    if isinstance(value, (list, tuple)):
        return "; ".join(str(v) for v in value)
    return str(value or "")


def procedure_row_entry(row: dict, alias_map: eb.AliasMap, rank: int) -> dict:
    """Procedures expose their method and invariants natively; knowledge does not."""
    alias = retrieval.resolve_reference(alias_map, [row["procedure_key"]])
    head = f"{row['name']}: {row['description']}" if row.get("description") else row["name"]
    lines = [head]
    if row.get("method"):
        lines.append(f"method: {_joined(row['method'])}")
    if row.get("invariants"):
        lines.append(f"invariants: {_joined(row['invariants'])}")
    return _entry(alias, "procedure", "\n".join(lines), rank)


def _confidence_key(value: Any) -> tuple:
    """`confidence DESC NULLS LAST` as an ascending sort key."""
    return (1, 0.0) if value is None else (0, -float(value))


def _ranked(pairs: list[tuple[tuple, dict]]) -> list[dict]:
    """Sort (public-order-key, entry) pairs by key then alias; assign ranks 1..n."""
    ordered = sorted(pairs, key=lambda p: (p[0], p[1]["alias"]))
    return [{**entry, "rank": n} for n, (_, entry) in enumerate(ordered, 1)]


def ordered_raw_entries(rows: list[dict], alias_map: eb.AliasMap) -> list[dict]:
    """raw_refind: public `rank DESC`, then alias ASC (native chunk_key tie is never trusted)."""
    return _ranked([((-float(r["rank"]),), raw_row_entry(r, alias_map, 0)) for r in rows])


def ordered_knowledge_entries(rows: list[dict], alias_map: eb.AliasMap) -> list[dict]:
    """current knowledge: `rank DESC`, `confidence DESC NULLS LAST`, then alias ASC."""
    return _ranked(
        [
            (
                (-float(r["rank"]), _confidence_key(r.get("confidence"))),
                knowledge_row_entry(r, alias_map, 0),
            )
            for r in rows
        ]
    )


def ordered_procedure_entries(rows: list[dict], alias_map: eb.AliasMap) -> list[dict]:
    """current procedure: public `score DESC`, then alias ASC (no updated_at / accepted_at)."""
    return _ranked([((-float(r["score"]),), procedure_row_entry(r, alias_map, 0)) for r in rows])


def _tie_prefix(item: dict) -> tuple:
    """The E5 ranking tuple without its final physical `memory_key` element."""
    sig = item["signals"]
    if "conflict" in item.get("flags", []):
        return (sig["authority_tier"], sig["scope_rank"], 0, 0.0, 0)
    return (
        sig["authority_tier"],
        sig["scope_rank"],
        -int(sig["task_family_match"] or sig["capability_match"]),
        -sig["fusion_rank_score"],
        -sig["recency_epoch"],
    )


def _alias_of(item: dict, alias_map: eb.AliasMap) -> str:
    if item["memory_class"] == "raw_evidence":
        refs = [
            e.split(":", 1)[1]
            for e in item.get("evidence", [])
            if e.startswith(("source:", "knowledge:"))
        ]
        refs = refs or [item["memory_key"]]
    else:
        refs = [item["memory_key"]]
    return retrieval.resolve_reference(alias_map, refs)


def _alias_tie_order(items: list[dict], aliases: list[str]) -> list[tuple[dict, str]]:
    """Order E5 items that tie on every ranking signal by alias instead of the random physical key.

    E5's final tie-break is the physical key, which differs between databases; the benchmark
    result must not. Items are only permuted inside a run of identical ranking prefixes.
    """
    out: list[tuple[dict, str]] = []
    run: list[tuple[dict, str]] = []
    for item, alias in zip(items, aliases, strict=True):
        if run and _tie_prefix(run[0][0]) != _tie_prefix(item):
            out.extend(sorted(run, key=lambda pair: pair[1]))
            run = []
        run.append((item, alias))
    out.extend(sorted(run, key=lambda pair: pair[1]))
    return out


def hybrid_entries_and_signals(result: dict, alias_map: eb.AliasMap) -> tuple[list[dict], dict]:
    """Flatten E5 sections in frozen order; roles/flags go only to the scorer sidecar."""
    entries: list[dict] = []
    mismatch, conflict, supporting = [], [], []
    for section in er.SECTIONS:
        items = result[section]
        aliases = [_alias_of(item, alias_map) for item in items]
        for item, alias in _alias_tie_order(items, aliases):
            flags = set(item.get("flags", []))
            entries.append(
                _entry(
                    alias,
                    _KIND_BY_CLASS.get(item["memory_class"], "knowledge"),
                    item["text"],
                    len(entries) + 1,
                )
            )
            if "premise_mismatch" in flags:
                mismatch.append(alias)
            if "conflict" in flags:
                conflict.append(alias)
            if "premise_mismatch" not in flags and item["role"] not in _NON_SUPPORTING_ROLES:
                supporting.append(alias)
    signals = retrieval.build_signals(
        premise_mismatch=mismatch,
        conflict_flagged=conflict,
        supporting_aliases=supporting,
        abstained=bool(result["abstained"]),
    )
    return entries, signals


def _plain(pack: list[dict]) -> list[dict]:
    return [{k: i[k] for k in ("alias", "kind", "content", "rank")} for i in pack]


# ---- owners, alias map, clock ---


@dataclass
class Owners:
    repository: Any
    knowledge: Any
    sources: Any
    procedures: Any
    approvals: Any
    lifecycle: Any
    revocation: Any
    retrieval: Any
    user_input: Any = None  # trusted-writer ingress for the synthetic approval fixture


class TrustedUserInput:
    """Existing production provenance-writer wrapper (`session_prompts`), nothing re-implemented."""

    def stage(self, project_id: int, session_id: str, text: str) -> bool:
        from . import session_prompts

        return session_prompts.stage_user_instruction(project_id, session_id, text)

    def commit(self, project_id: int, session_id: str, task_key: str) -> list[dict]:
        from . import session_prompts

        return session_prompts.commit_staged_user_instruction_events(
            project_id, session_id, task_key
        )


class _Clock:
    def __init__(self) -> None:
        self.now = datetime.fromisoformat("2026-01-01T00:00:00+00:00")

    def __call__(self) -> datetime:
        return self.now


def default_owners(clock: Callable[[], datetime]) -> Owners:
    from .approvals import ApprovalService
    from .experience_lifecycle import ExperienceLifecycleService
    from .experience_retrieval import ExperienceRetrievalService
    from .knowledge import KnowledgeService
    from .procedures import ProcedureService
    from .repository import Repository
    from .source_revocation import SourceRevocationService
    from .sources import SourceService

    return Owners(
        repository=Repository(),
        knowledge=KnowledgeService(),
        sources=SourceService(),
        procedures=ProcedureService(),
        approvals=ApprovalService(),
        lifecycle=ExperienceLifecycleService(clock),
        revocation=SourceRevocationService(clock),
        retrieval=ExperienceRetrievalService(),
        user_input=TrustedUserInput(),
    )


def current_database_name() -> str:
    from .db import connect

    with connect() as conn:
        return conn.execute("SELECT current_database() AS name").fetchone()["name"]


def knowledge_snapshot(alias: str, item: dict, alias_map: eb.AliasMap) -> dict:
    """Closed, alias-only semantic snapshot of a public `KnowledgeService.get` result.

    Runtime keys, DB ids, evidence row ids, approval keys and every timestamp are dropped. A
    reference that does not resolve through the AliasMap fails closed without echoing the key.
    """

    def ref(key: str) -> str:
        found = alias_map.alias_for(key)
        if found is None:
            raise BenchmarkError("knowledge snapshot references an unmapped runtime key")
        return found

    successor = item.get("superseded_by")
    return {
        "alias": alias,
        "kind": "knowledge",
        "knowledge_type": item.get("knowledge_type"),
        "title": item.get("title"),
        "statement": item.get("statement"),
        "status": item["status"],
        "superseded_by": ref(successor) if successor else None,
        "evidence_sources": sorted(
            {ref(e["source_key"]) for e in item.get("evidence", []) if e.get("source_key")}
        ),
    }


def _step_refs(step: dict) -> list[str]:
    required, optional = eb._OPERATIONS[step["op"]]
    args = step.get("args", {})
    return [
        args[k] for k, kind in {**required, **optional}.items() if kind == "alias" and k in args
    ]


class RuntimeAliasMap(eb.AliasMap):
    """Case-local alias map that also carries the retrieval project and physical bookkeeping."""

    def __init__(self, aliases: list[str], project_id: int):
        super().__init__(aliases)
        self.project_id = project_id
        self.physical: list[str] = []

    def bind(self, alias: str, runtime_key: str) -> None:
        super().bind(alias, runtime_key)
        self.physical.append(runtime_key)


# ---- adapters ---


class _Adapter:
    def __init__(self, owners: Owners):
        self._o = owners

    def _done(self, entries, scoring, signals, started):
        return retrieval.finish_adapter(
            entries, scoring, signals=signals, elapsed_ns=time.perf_counter_ns() - started
        )

    @staticmethod
    def _all_supporting(entries: list[dict]) -> dict:
        return retrieval.build_signals(supporting_aliases=[e["alias"] for e in entries])


class MemoryDisabled(_Adapter):
    def retrieve(self, shared, alias_map, scoring):
        started = time.perf_counter_ns()
        return self._done([], scoring, retrieval.build_signals(), started)


class RawRefind(_Adapter):
    def retrieve(self, shared, alias_map, scoring):
        started = time.perf_counter_ns()
        rows = self._o.knowledge.chunk_search(
            shared["query"], limit=RAW_REFIND_NATIVE_LIMIT, project_id=alias_map.project_id
        )
        entries = ordered_raw_entries(rows, alias_map)
        return self._done(entries, scoring, self._all_supporting(entries), started)


class CurrentVres(_Adapter):
    def retrieve(self, shared, alias_map, scoring):
        started = time.perf_counter_ns()
        pid = alias_map.project_id
        k_rows = self._o.knowledge.search(
            shared["query"], limit=CURRENT_KNOWLEDGE_NATIVE_LIMIT, project_id=pid
        )
        p_rows = self._o.procedures.find_matches(
            shared["query"],
            task_family=shared["request"].get("task_family"),
            limit=CURRENT_PROCEDURE_NATIVE_LIMIT,
            project_id=pid,
        )
        knowledge = ordered_knowledge_entries(k_rows, alias_map)
        procedure = ordered_procedure_entries(p_rows, alias_map)
        _, collapsed = retrieval.merge_current_vres(knowledge, procedure, scoring)
        entries = _plain(collapsed)  # frozen merge collapses duplicates before budgeting
        return self._done(entries, scoring, self._all_supporting(entries), started)


class CandidateHybrid(_Adapter):
    def __init__(self, owners: Owners, scoring: dict):
        super().__init__(owners)
        self._time = scoring["time"]
        self.last_result: dict | None = None  # public E5 result of the latest call (security view)

    def retrieve(self, shared, alias_map, scoring):
        started = time.perf_counter_ns()
        req = shared["request"]
        request = {
            "project_id": alias_map.project_id,
            "query": shared["query"],
            "task_family": req.get("task_family"),
            "capability_keys": list(req.get("capability_keys", [])),
            "temporal_intent": req.get("temporal_intent", "current"),
        }
        if request["temporal_intent"] == "historical" and "as_of_t" in req:
            request["as_of"] = eb.benchmark_instant(self._time, req["as_of_t"])
        result = self._o.retrieval.retrieve(request)
        self.last_result = result
        entries, signals = hybrid_entries_and_signals(result, alias_map)
        return self._done(entries, scoring, signals, started)


# ---- runtime ---


def _parse_instant(text: str) -> datetime:
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


class BenchmarkRuntime:
    def __init__(
        self,
        scoring: dict,
        *,
        nonce: str,
        owners: Owners,
        environ: Any,
        clock: _Clock | None = None,
        database_name: Callable[[], str] = current_database_name,
    ):
        if not nonce or not nonce.replace("-", "").isalnum():
            raise BenchmarkError("nonce must be alphanumeric text")
        self.scoring, self.nonce, self.o = scoring, nonce, owners
        self.environ, self.clock, self._database_name = environ, clock or _Clock(), database_name
        self._projects: dict[tuple[str, str], int] = {}
        self._approvals = 0
        self.physical: list[str] = []
        self.candidate_results: dict[
            tuple[str, str], dict
        ] = {}  # public evaluate_candidate returns
        self.adapters = {
            "memory_disabled": MemoryDisabled(owners),
            "raw_refind": RawRefind(owners),
            "current_vres": CurrentVres(owners),
            "candidate_hybrid": CandidateHybrid(owners, scoring),
        }

    # -- scenario --
    def _project(self, case_id: str, label: str) -> int:
        from .project import ProjectIdentity

        key = (case_id, label)
        if key not in self._projects:
            ident = ProjectIdentity(
                Path(f"benchmark/{self.nonce}/{case_id}/{label}"),
                f"e7bm:{self.nonce}:{case_id}:{label}",
                f"e7 benchmark {case_id} {label}",
                None,
                None,
            )
            self._projects[key] = self.o.repository.ensure_project(ident)
        return self._projects[key]

    def _runtime_key(self, prefix: str, case_id: str, alias: str) -> str:
        return f"{prefix}-{self.nonce}-{case_id}-{alias}"

    def _approve(self, pid: int, plan: dict) -> tuple[str, str]:
        """Synthetic benchmark user-input provenance fixture (not real user authority).

        The USER_INSTRUCTION enters only through the trusted provenance-writer ingress
        (`stage_user_input` / `commit_user_inputs`); the approval is then recorded by the
        normal application owner from that persisted event.
        """
        eb.check_approval_fixture_gate(self._database_name(), self.environ)
        self._approvals += 1
        sid = f"e7bm-{self.nonce}-{self._approvals}"
        repo = self.o.repository
        task = repo.begin_task(
            pid, "benchmark approval fixture", "synthetic benchmark approval", None, "benchmark"
        )
        repo.open_session(pid, sid)
        repo.bind_session(pid, sid, task)
        if self.o.user_input.stage(pid, sid, "Approved") is not True:
            raise BenchmarkError("synthetic approval input was not staged by the trusted writer")
        committed = self.o.user_input.commit(pid, sid, task)
        if [e["event_type"] for e in committed] != ["USER_INSTRUCTION"]:
            raise BenchmarkError("expected exactly one committed USER_INSTRUCTION event")
        key = self.o.approvals.record_latest_user_approval(
            task_key=task,
            approval_type=plan["approval_type"],
            statement="Approved",
            subject_key=plan["subject_key"],
        )
        return task, key

    def materialize(self, case: dict) -> RuntimeAliasMap:
        return self._timeline(case, None)

    def materialize_traced(self, case: dict) -> tuple[RuntimeAliasMap, dict]:
        """Materialize and return the operation trace: one row per corpus timeline step only.

        Snapshots are public `KnowledgeService.get` reads taken after each step; no owner write is
        added, so no hidden call can appear as a semantic transition.
        """
        rows: list[dict] = []
        amap = self._timeline(case, rows)
        return amap, {"rows": rows}

    def _timeline(self, case: dict, rows: list[dict] | None) -> RuntimeAliasMap:
        case_id, request = case["case_id"], case["request"]
        default_label = request.get("project", "default")
        amap = RuntimeAliasMap(case["aliases"], self._project(case_id, default_label))
        knowledge_aliases: list[str] = []
        before: dict[str, dict] = {}
        for step in case.get("timeline", []):
            if step["op"] not in EXECUTABLE_OPS:
                raise BenchmarkError(f"operation {step['op']!r} is not executable in a case")
            self.clock.now = _parse_instant(eb.benchmark_instant(self.scoring["time"], step["t"]))
            self._step(case_id, default_label, step, amap)
            if rows is None:
                continue
            if step["op"] == "knowledge_propose":
                knowledge_aliases.append(step["alias"])
            after = {
                a: knowledge_snapshot(a, self.o.knowledge.get(amap.runtime_key_for(a)), amap)
                for a in knowledge_aliases
            }
            rows.append(
                {
                    "t": step["t"],
                    "op": step["op"],
                    "alias": step["alias"],
                    "refs": _step_refs(step),
                    "result": {"status": "applied"},
                    "before": before,
                    "after": after,
                }
            )
            before = after
        self.physical.extend(amap.physical)
        return amap

    def _step(self, case_id: str, default_label: str, step: dict, amap: RuntimeAliasMap) -> None:
        op, alias, args = step["op"], step["alias"], step.get("args", {})
        pid = self._project(case_id, args.get("project", default_label))
        key_of = amap.runtime_key_for
        if op == "source_add":
            text = args["text"]
            source_key, source_id = self.o.sources.register(
                source_type="benchmark",
                title=args.get("title", alias),
                origin=SOURCE_OWNER,
                path_or_uri=f"benchmark://{self.nonce}/{case_id}/{alias}",
                content_hash=hashlib.sha256(text.encode("utf-8")).hexdigest(),
                version="1",
                project_id=pid,
                authority_level=args.get("trust_class", "trusted_project_source"),
                created_at=self.clock.now,
            )
            self.o.sources.add_chunks(source_id=source_id, text=text)
            amap.bind(alias, source_key)
        elif op == "knowledge_propose":
            key = self._runtime_key("BM", case_id, alias)
            self.o.knowledge.propose(
                key=key,
                knowledge_type=args["knowledge_type"],
                title=args.get("title", DEFAULT_TITLE),
                statement=args["statement"],
                status=INITIAL_STATUS,
                scope={},
                confidence=None,
                source_owner=SOURCE_OWNER,
                project_id=pid,
                review_after=None,
                metadata={"trust_class": args.get("trust_class", "trusted_project_source")},
            )
            amap.bind(alias, key)
        elif op == "knowledge_attach_source":
            self.o.sources.attach_evidence(
                knowledge_key=key_of(alias),
                source_key=key_of(args["source"]),
                evidence_type=args["evidence_type"],
            )
        elif op == "procedure_accept":
            key = self._runtime_key("BMP", case_id, alias)
            _, approval = self._approve(pid, eb.approval_plan(op, key))
            self.o.procedures.accept_baseline(
                procedure_key=key,
                name=args["name"],
                description=args.get("description", ""),
                task_family=None,
                project_id=pid,
                input_contract={},
                method=[args["method"]],
                invariants=list(args.get("invariants", [])),
                validation_contract=["benchmark fixture: no execution"],
                output_contract={},
                approval_key=approval,
                implementation_ref=None,
                initial_metrics=dict(eb.BASELINE_INITIAL_METRICS),
            )
            amap.bind(alias, key)
        elif op == "procedure_candidate":
            self.candidate_results[(case_id, alias)] = self.o.procedures.evaluate_candidate(
                procedure_key=key_of(args["baseline"]),
                candidate={
                    "method": [args["method"]],
                    "description": args.get("description", ""),
                    "invariants": list(args.get("invariants", [])),
                },
                metrics=dict(eb.CANDIDATE_METRICS),
            )
        elif op == "knowledge_supersede":
            self.o.knowledge.supersede(key_of(args["supersedes"]), key_of(alias))
        elif op == "knowledge_observe":
            self.o.knowledge.update(key_of(alias), status="observed")
        elif op == "source_revoke":
            source_key = key_of(alias)
            task, approval = self._approve(pid, eb.approval_plan(op, source_key))
            self.o.revocation.revoke_source(
                source_key,
                project_id=pid,
                approval_key=approval,
                reason=args.get("reason", "benchmark revocation"),
                task_key=task,
            )
        else:
            self._lifecycle(op, pid, alias, args, amap)

    def _lifecycle(self, op: str, pid: int, alias: str, args: dict, amap) -> None:
        target = amap.runtime_key_for(alias)
        reason = args.get("reason", "benchmark lifecycle")
        action = op.removeprefix("lifecycle_")
        if action == "supersede":
            old = amap.runtime_key_for(args["supersedes"])
            task, approval = self._approve(pid, eb.approval_plan(op, old, target))
            self.o.lifecycle.supersede(
                old, target, project_id=pid, approval_key=approval, reason=reason, task_key=task
            )
            return
        task, approval = self._approve(pid, eb.approval_plan(op, target))
        common = {"project_id": pid, "approval_key": approval, "reason": reason, "task_key": task}
        if action == "refresh":
            when = eb.benchmark_instant(self.scoring["time"], args["review_after_t"])
            self.o.lifecycle.refresh(target, review_after=_parse_instant(when), **common)
        else:
            getattr(self.o.lifecycle, action)(target, **common)

    # -- running --
    def run_case(self, case: dict, expected: dict) -> dict:
        return retrieval.run_case(case, expected, self.scoring, self.adapters, self.materialize)

    def run_faithfulness_case(self, case: dict, expected: dict) -> dict:
        return faithfulness.run_case(case, expected, lambda c: self.materialize_traced(c)[1])

    def run_outcome_case(self, case: dict, expected: dict) -> dict:
        """Materialize once; identical public task input for every mode, only the pack differs.

        The worker receives query, request, task and the canonical pack only. Private criteria and
        labels are read after every trace is complete.
        """
        gap = retrieval.owner_gap_result(case)
        if gap is not None:
            return gap
        amap = self.materialize(case)
        shared = retrieval.public_input(case)
        config = {
            "policy_version": worker.WORKER_POLICY_VERSION,
            "max_trace_steps": self.scoring["proxy_worker"]["max_trace_steps"],
        }
        raw, timings = {}, {}
        for mode in eb.MODES:
            got = self.adapters[mode].retrieve(shared, amap, self.scoring)
            worker_started = time.perf_counter_ns()
            rows = worker.run_worker(
                case["query"], case["request"], case["task"], got["pack"], config
            )
            worker_elapsed = time.perf_counter_ns() - worker_started
            raw[mode] = (got, rows)
            timings[mode] = outcome.timing_row(got["elapsed_ns"], worker_elapsed)
        criteria = expected["outcome"]["criteria"]
        scored = {
            mode: outcome.mode_result(
                rows, [i["alias"] for i in got["pack"]], got["token_estimate"], criteria
            )
            for mode, (got, rows) in raw.items()
        }
        labels = {k: list(expected.get(k, [])) for k in eb._LABEL_LISTS}
        labels["memory_not_needed"] = bool(expected.get("memory_not_needed", False))
        modes = {}
        for mode, (got, rows) in raw.items():
            entry = {
                "pack": got["pack"],
                "pack_digest": eb.pack_digest(got["pack"]),
                "token_estimate": got["token_estimate"],
                "trace": rows,
                "outcome": scored[mode]["outcome"],
                "negative_transfer": outcome.negative_transfer(
                    labels,
                    len(criteria),
                    scored[outcome.REFERENCE_MODE],
                    scored[mode],
                    is_reference=mode == outcome.REFERENCE_MODE,
                ),
            }
            modes[mode] = entry
        return {
            "case_id": case["case_id"],
            "status": retrieval.STATUS_EXECUTED,
            "labels": labels,
            "modes": modes,
            "timings": timings,
        }

    def run_streaming_case(self, case: dict, expected: dict) -> dict:
        """Admit the full case first (a gap short-circuits the sequence); then one fresh prefix
        rebuild per checkpoint, all four modes, identical public input. Labels load afterwards."""
        gap = retrieval.owner_gap_result(case)
        if gap is not None:
            return gap
        block = expected["streaming"]
        shared = retrieval.public_input(case)
        has_task = "task" in case and "outcome" in expected
        config = {
            "policy_version": worker.WORKER_POLICY_VERSION,
            "max_trace_steps": self.scoring["proxy_worker"]["max_trace_steps"],
        }
        raw: list[dict] = []
        for cp in block["checkpoints"]:
            amap = self.materialize(streaming.prefix_case(case, cp["after_t"]))
            at: dict = {}
            for mode in eb.MODES:
                got = self.adapters[mode].retrieve(shared, amap, self.scoring)
                rows = (
                    worker.run_worker(
                        case["query"], case["request"], case["task"], got["pack"], config
                    )
                    if has_task
                    else None
                )
                at[mode] = (got, rows)
            raw.append(at)
        criteria = expected["outcome"]["criteria"] if has_task else None
        positions = {mode: [] for mode in eb.MODES}
        metrics = {mode: [] for mode in eb.MODES}
        records = []
        for cp, at in zip(block["checkpoints"], raw, strict=True):
            labels = {k: list(cp.get(k, [])) for k in ("relevant", "acceptable", "irrelevant")}
            labels["stale"] = list(cp.get("stale", []))
            labels["premise"] = list(expected.get("premise", []))
            labels["memory_not_needed"] = bool(expected.get("memory_not_needed", False))
            scored = {}
            if has_task:
                scored = {
                    mode: outcome.mode_result(
                        rows, [i["alias"] for i in got["pack"]], got["token_estimate"], criteria
                    )
                    for mode, (got, rows) in at.items()
                }
            record = {"after_t": cp["after_t"], "modes": {}}
            for mode, (got, rows) in at.items():
                met = retrieval.score_retrieval(
                    {**labels, "must_abstain": cp.get("must_abstain", False)},
                    case["request"],
                    got["pack"],
                    got["signals"],
                    self.scoring,
                )
                nt = None
                if has_task:
                    nt = outcome.negative_transfer(
                        labels,
                        len(criteria),
                        scored[outcome.REFERENCE_MODE],
                        scored[mode],
                        is_reference=mode == outcome.REFERENCE_MODE,
                    )
                entry = {
                    "pack": got["pack"],
                    "pack_digest": eb.pack_digest(got["pack"]),
                    "token_estimate": got["token_estimate"],
                    "signals": got["signals"],
                    "metrics": met,
                }
                if has_task:
                    entry["trace"] = rows
                    entry["outcome"] = scored[mode]["outcome"]
                    entry["negative_transfer"] = nt
                record["modes"][mode] = entry
                metrics[mode].append(met)
                positions[mode].append(
                    {
                        "pack_aliases": [i["alias"] for i in got["pack"]],
                        "supporting_aliases": got["signals"]["supporting_aliases"],
                        "outcome": scored[mode]["outcome"] if has_task else None,
                        "negative_transfer": nt,
                    }
                )
            records.append(record)
        return {
            "case_id": case["case_id"],
            "status": retrieval.STATUS_EXECUTED,
            "positions": records,
            "measures": streaming.case_measures(block, case, positions, metrics),
        }

    def case_project_ids(self, case_id: str) -> list[int]:
        """Physical project ids created for one case (read-only evidence collection only)."""
        return sorted(pid for (cid, _), pid in self._projects.items() if cid == case_id)

    def physical_fingerprint(self) -> str:
        return eb.sha256_hex("\n".join(sorted(self.physical)).encode("utf-8"))


def run_subset(
    runtime: BenchmarkRuntime,
    root: str | Path,
    split: str,
    case_ids: list[str],
    *,
    source: dict,
    digest_basis: dict | None = None,
) -> dict:
    """Run the named executable/gap cases of a development split and build the run result."""
    bundle = eb.load_development_bundle(root, split, case_ids=case_ids)
    cases = [
        runtime.run_case(c, bundle["expected"][c["case_id"]])
        for c in sorted(bundle["cases"], key=lambda c: c["case_id"])
        if c["case_id"] in set(case_ids)
    ]
    return retrieval.build_run_result(
        split=split,
        source=source,
        digests=digest_basis or bundle["digests"],
        scoring_digest=eb.scoring_digest(runtime.scoring),
        retrieval_identity=retrieval_identity(),
        cases=cases,
    )


def run_faithfulness(
    runtime: BenchmarkRuntime,
    root: str | Path,
    split: str,
    *,
    source: dict,
    order: list[str] | None = None,
) -> dict:
    """Run the faithfulness cohort of a development split; `order` only permutes execution."""
    bundle = eb.load_development_bundle(root, split)
    cohort = {c["case_id"]: c for c in faithfulness.faithfulness_cases(bundle)}
    if order is not None and sorted(order) != sorted(cohort):
        raise BenchmarkError("faithfulness run order must be a permutation of the cohort")
    results = [
        runtime.run_faithfulness_case(cohort[case_id], bundle["expected"][case_id])
        for case_id in (order or sorted(cohort))
    ]
    return faithfulness.build_run_result(
        split=split,
        source=source,
        digests=bundle["digests"],
        scoring_digest=eb.scoring_digest(runtime.scoring),
        policy=faithfulness.policy_identity(),
        cases=sorted(results, key=lambda c: c["case_id"]),
    )


def run_outcome(
    runtime: BenchmarkRuntime,
    root: str | Path,
    split: str,
    *,
    source: dict,
    order: list[str] | None = None,
) -> dict:
    """Run the outcome cohort (from expected outcomes); `order` only permutes execution."""
    bundle = eb.load_development_bundle(root, split)
    executable, gap = outcome.outcome_cohort(bundle)
    cohort = sorted(executable + gap)
    if order is not None and sorted(order) != cohort:
        raise BenchmarkError("outcome run order must be a permutation of the cohort")
    by_id = {c["case_id"]: c for c in bundle["cases"]}
    results = [runtime.run_outcome_case(by_id[i], bundle["expected"][i]) for i in (order or cohort)]
    return outcome.build_outcome_run(
        split=split,
        source=source,
        digests=bundle["digests"],
        scoring_digest=eb.scoring_digest(runtime.scoring),
        retrieval_identity=retrieval_identity(),
        worker_identity=outcome.worker_policy_identity(
            runtime.scoring["proxy_worker"]["max_trace_steps"]
        ),
        cases=sorted(results, key=lambda c: c["case_id"]),
    )


def run_streaming(
    runtime: BenchmarkRuntime,
    root: str | Path,
    split: str,
    *,
    source: dict,
    order: list[str] | None = None,
) -> dict:
    """Run the streaming cohort (from private blocks); `order` only permutes execution."""
    bundle = eb.load_development_bundle(root, split)
    executable, gap = streaming.streaming_cohort(bundle)
    cohort = sorted(executable + gap)
    if order is not None and sorted(order) != cohort:
        raise BenchmarkError("streaming run order must be a permutation of the cohort")
    by_id = {c["case_id"]: c for c in bundle["cases"]}
    results = [
        runtime.run_streaming_case(by_id[i], bundle["expected"][i]) for i in (order or cohort)
    ]
    return streaming.build_streaming_run(
        split=split,
        source=source,
        digests=bundle["digests"],
        scoring_digest=eb.scoring_digest(runtime.scoring),
        retrieval_identity=retrieval_identity(),
        worker_identity=outcome.worker_policy_identity(
            runtime.scoring["proxy_worker"]["max_trace_steps"]
        ),
        checkpoint_expectations={i: bundle["expected"][i]["streaming"] for i in cohort},
        cases=sorted(results, key=lambda c: c["case_id"]),
    )
