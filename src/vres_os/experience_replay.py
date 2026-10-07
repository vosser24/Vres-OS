"""#176 E6 Chunk 3: paired retrieval-policy replay.

One request is evaluated against ONE hard-gated candidate universe collected once inside ONE REPEATABLE READ / READ ONLY
snapshot (ExperienceRetrievalService.paired_compose). The exact E5 baseline and ONE bounded candidate composition
policy are composed from copies of that same universe; deterministic deltas are persisted afterwards, in a separate
writer transaction, as an append-only ledger row of digests, memory keys and counts.

A replay never selects a winner, never activates or promotes a policy, never establishes causal credit, and never
changes retrieval, memory, procedure, capability, model, routing or validation authority.
"""

from __future__ import annotations

from typing import Any

from psycopg.types.json import Jsonb

from .experience import _canonical, _sha256
from .experience_observability import request_digests
from .experience_retrieval import (
    E5_V1_POLICY,
    SECTIONS,
    CompositionParams,
    ExperienceRetrievalService,
)

POLICY_VERSION = "176.e6.v1"
CAUSAL_CREDIT = "not_established"
BASELINE_POLICY_DIGEST = _sha256(E5_V1_POLICY)
ISOLATION = {"transaction_isolation": "repeatable read", "transaction_read_only": "on"}

_TOP_FIELDS = ("section_budgets", "max_items", "max_pack_bytes", "rrf_k")
_BOUNDS = {"max_items": (1, 32), "max_pack_bytes": (4096, 32768), "rrf_k": (10, 120)}
_BUDGET_BOUNDS = (0, 16)
_TRUNCATED = ("section_budget", "total_items", "pack_bytes", "conflict_sets")


class PolicyRejected(ValueError):
    """A candidate policy outside the closed schema. ``code`` is bounded and value-free."""

    def __init__(self, code: str, detail: str):
        super().__init__(f"{code}: {detail}")
        self.code = code


def _int(value: Any, name: str, lo: int, hi: int) -> int:
    if type(value) is not int:  # bool is an int subclass and is rejected here
        raise PolicyRejected("policy_type", f"{name} must be an integer")
    if not lo <= value <= hi:
        raise PolicyRejected("policy_bound", f"{name} must be between {lo} and {hi}")
    return value


def validate_candidate_policy(policy: Any) -> dict[str, Any]:
    """Closed schema: section budgets, max items, max pack bytes and RRF k. Nothing else is ever accepted."""
    if not isinstance(policy, dict):
        raise PolicyRejected("policy_type", "candidate policy must be an object")
    unknown = sorted(str(k) for k in set(policy) - set(_TOP_FIELDS))
    if unknown:
        raise PolicyRejected("policy_unknown_field", f"unknown fields {unknown}")
    missing = [f for f in _TOP_FIELDS if f not in policy]
    if missing:
        raise PolicyRejected("policy_missing_field", f"missing fields {missing}")
    budgets = policy["section_budgets"]
    if not isinstance(budgets, dict):
        raise PolicyRejected("policy_type", "section_budgets must be an object")
    unknown = sorted(str(k) for k in set(budgets) - set(SECTIONS))
    if unknown:
        raise PolicyRejected("policy_unknown_field", f"unknown sections {unknown}")
    missing = [s for s in SECTIONS if s not in budgets]
    if missing:
        raise PolicyRejected("policy_missing_field", f"missing sections {missing}")
    return {
        "section_budgets": {s: _int(budgets[s], f"section budget {s}", *_BUDGET_BOUNDS) for s in SECTIONS},
        **{name: _int(policy[name], name, *_BOUNDS[name]) for name in _BOUNDS},
    }


def candidate_policy_digest(policy: Any) -> str:
    return _sha256(validate_candidate_policy(policy))


def candidate_params(policy: Any) -> CompositionParams:
    valid = validate_candidate_policy(policy)
    return CompositionParams(dict(valid["section_budgets"]), valid["max_items"], valid["max_pack_bytes"], valid["rrf_k"])


def _keys(pack: dict[str, Any]) -> list[str]:
    return [item["memory_key"] for section in SECTIONS for item in pack[section]]


def _pair(base: Any, cand: Any) -> dict[str, Any]:
    return {"baseline": base, "candidate": cand}


def _count(value: Any) -> int:
    return value if type(value) is int and 0 <= value <= 1_000_000 else 0


def _diagnostics_delta(base: dict[str, Any], cand: dict[str, Any]) -> dict[str, Any]:
    """Closed, structural and bounded: fixed names, small enums/counts only; never free text from the pack."""
    b, c = base.get("diagnostics") or {}, cand.get("diagnostics") or {}
    mode = lambda d: d["raw_fallback"] if isinstance(d.get("raw_fallback"), str) and len(d["raw_fallback"]) <= 32 else "unknown"  # noqa: E731
    bt, ct = b.get("truncated") or {}, c.get("truncated") or {}
    return {
        "raw_fallback": _pair(mode(b), mode(c)),
        "deduplicated": _pair(_count(b.get("deduplicated")), _count(c.get("deduplicated"))),
        "truncated": {n: _pair(_count(bt.get(n)), _count(ct.get(n))) for n in _TRUNCATED},
        "section_counts": {s: _pair(len(base[s]), len(cand[s])) for s in SECTIONS},
    }


def compute_delta(baseline: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    """Deterministic structural delta; items are flattened by the frozen section order. Inputs are not mutated."""
    base_keys, cand_keys = _keys(baseline), _keys(candidate)
    in_base, in_cand = set(base_keys), set(cand_keys)
    common_base = [k for k in base_keys if k in in_cand]
    common_cand = [k for k in cand_keys if k in in_base]
    base_index = {k: i for i, k in enumerate(common_base)}
    base_bytes = len(_canonical(baseline).encode("utf-8"))
    cand_bytes = len(_canonical(candidate).encode("utf-8"))
    base_tokens, cand_tokens = baseline["estimated_tokens"], candidate["estimated_tokens"]
    return {
        "baseline_item_keys": base_keys,
        "candidate_item_keys": cand_keys,
        "added_keys": [k for k in cand_keys if k not in in_base],
        "removed_keys": [k for k in base_keys if k not in in_cand],
        "reordered_keys": [k for i, k in enumerate(common_cand) if base_index[k] != i],
        "baseline_pack_bytes": base_bytes,
        "candidate_pack_bytes": cand_bytes,
        "bytes_delta": cand_bytes - base_bytes,
        "baseline_estimated_tokens": base_tokens,
        "candidate_estimated_tokens": cand_tokens,
        "tokens_delta": cand_tokens - base_tokens,
        "baseline_abstained": baseline["abstained"],
        "candidate_abstained": candidate["abstained"],
        "abstention_changed": baseline["abstained"] != candidate["abstained"],
        "diagnostics_delta": _diagnostics_delta(baseline, candidate),
    }


_PERSISTED = (
    "baseline_item_keys", "candidate_item_keys", "added_keys", "removed_keys", "reordered_keys", "baseline_pack_bytes",
    "candidate_pack_bytes", "baseline_estimated_tokens", "candidate_estimated_tokens", "baseline_abstained",
    "candidate_abstained", "diagnostics_delta",
)
_GET_FIELDS = (
    "replay_key", "project_id", "task_id", "policy_version", "request_digest", "snapshot_at",
    "baseline_retrieval_policy_digest", "candidate_policy", "candidate_policy_digest", "baseline_pack_digest",
    "candidate_pack_digest", *_PERSISTED, "causal_credit", "created_at",
)


def _writer_connect():
    from .db import connect

    return connect(purpose="writer")


def _reader_connect():
    from .db import connect

    return connect()


class ExperienceReplayService:
    """Paired replay. No MCP surface, no policy mutation, no winner: it measures and records structure only."""

    def __init__(self, retrieval=None, writer_connect=None, reader_connect=None):
        self._retrieval = retrieval or ExperienceRetrievalService()
        self._writer_connect = writer_connect or _writer_connect
        self._reader_connect = reader_connect or _reader_connect

    def replay(self, project_id: int, request: dict[str, Any], candidate_policy: Any) -> dict[str, Any]:
        # Everything that can be rejected is rejected before any snapshot is opened.
        policy = validate_candidate_policy(candidate_policy)
        params = candidate_params(policy)
        request_digest = request_digests({"request": request}, project_id)["request_digest"]
        paired = self._retrieval.paired_compose({**request, "project_id": project_id}, params)
        if paired["isolation"] != ISOLATION:
            raise RuntimeError("Replay was not composed inside a REPEATABLE READ, READ ONLY snapshot")
        baseline, candidate = paired["baseline"], paired["candidate"]
        baseline_policy_digest = _sha256(baseline["policy"])
        if baseline_policy_digest != BASELINE_POLICY_DIGEST:
            raise RuntimeError("Replay baseline is not the frozen E5 policy")
        delta = compute_delta(baseline, candidate)
        digests = {
            "baseline_pack_digest": _sha256(baseline),
            "candidate_pack_digest": _sha256(candidate),
        }
        payload = {
            "request_digest": request_digest,
            "snapshot_at": paired["snapshot_at"].isoformat(),
            "baseline_retrieval_policy_digest": baseline_policy_digest,
            "candidate_policy": policy,
            "candidate_policy_digest": _sha256(policy),
            **digests,
            **{name: delta[name] for name in _PERSISTED},
        }
        # The snapshot is closed. Persistence is a separate writer transaction; an unchanged repeat is a duplicate.
        with self._writer_connect() as conn, conn.transaction():
            row = conn.execute(
                "SELECT outcome, replay_key FROM vres.record_experience_retrieval_replay(%s,%s,%s)",
                (project_id, paired["task_id"], Jsonb(payload)),
            ).fetchone()
        return {
            "outcome": row["outcome"],
            "replay_key": row["replay_key"],
            "policy_version": POLICY_VERSION,
            "causal_credit": CAUSAL_CREDIT,
            "candidate_policy_digest": payload["candidate_policy_digest"],
            **digests,
            "delta": delta,
        }

    def get(self, project_id: int, replay_key: str) -> dict[str, Any]:
        with self._reader_connect() as conn:
            row = conn.execute(
                f"SELECT {', '.join(_GET_FIELDS)} FROM vres.experience_retrieval_replays "
                "WHERE project_id=%s AND replay_key=%s",
                (project_id, replay_key),
            ).fetchone()
        if row is None:
            raise LookupError("Replay not found for this project")
        return {
            name: row[name].isoformat() if hasattr(row[name], "isoformat") else row[name] for name in _GET_FIELDS
        }
