"""E7 Chunk 4: deterministic proxy worker (policy v1). Pure stdlib; no model, no I/O.

The worker sees only its arguments: the public query, the public request, the public task template,
the canonical evidence pack, and a closed config. It cannot open files, reach the database,
or import any benchmark module, so nothing private can reach it. It returns a closed trace of rows
`{step, action, used_aliases, retry, tool_call}` and nothing else (no scores, no explanations).
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from typing import Any

WORKER_POLICY_VERSION = "176.e7.proxy.v1"
ABSTAIN = "abstain"

NEGATIVE_CUES = (
    ("do", "not"),
    ("don", "t"),
    ("never",),
    ("avoid",),
    ("failed",),
    ("failure",),
    ("stale",),
    ("wrong",),
)

POLICY = {
    "version": WORKER_POLICY_VERSION,
    "text_normalization": "nfc_casefold_alphanumeric_tokens",
    "action_terms": "action_id_split_on_underscore",
    "action_matcher": "exact_or_prefix_both_min_length_4",
    "contribution": "distinct_matching_terms_signed_by_negative_cue",
    "negative_cues": [" ".join(cue) for cue in NEGATIVE_CUES],
    "action_score": "sum_over_pack_no_owner_score_or_rank",
    "tie_break": "smallest_sha256_hex_of_utf8_action_id",
    "used_aliases": "nonzero_contribution_to_any_action_in_step_including_negative",
    "abstain": "every_action_strictly_negative_and_may_abstain",
    "retry": "ambiguous_nonzero_top_tie_repeats_final_choice_retry_limit_times",
}

_TOKEN = re.compile(r"[^\W_]+")
_MIN_PREFIX = 4
_CONFIG_KEYS = {"policy_version", "max_trace_steps"}
_STEP_KEYS = {"step", "actions", "retry_limit", "retry_when", "may_abstain"}
_RETRY_WHEN = ("never", "ambiguous_nonzero")


class WorkerError(ValueError):
    """The proxy worker fails closed on malformed input or an oversized trace."""


def _tokens(text: str) -> list[str]:
    return _TOKEN.findall(unicodedata.normalize("NFC", text).casefold())


def _terms_match(term: str, token: str) -> bool:
    if term == token:
        return True
    if len(term) < _MIN_PREFIX or len(token) < _MIN_PREFIX:
        return False
    return term.startswith(token) or token.startswith(term)


def _has_negative_cue(tokens: list[str]) -> bool:
    for cue in NEGATIVE_CUES:
        width = len(cue)
        for start in range(len(tokens) - width + 1):
            if tuple(tokens[start : start + width]) == cue:
                return True
    return False


def _sha(action: str) -> str:
    return hashlib.sha256(action.encode("utf-8")).hexdigest()


def _check_config(config: Any) -> int:
    if not isinstance(config, dict) or set(config) != _CONFIG_KEYS:
        raise WorkerError("worker config must have exactly policy_version and max_trace_steps")
    if config["policy_version"] != WORKER_POLICY_VERSION:
        raise WorkerError("unsupported worker policy version")
    limit = config["max_trace_steps"]
    if type(limit) is not int or limit <= 0:
        raise WorkerError("max_trace_steps must be a positive integer")
    return limit


def _check_pack(pack: Any) -> list[tuple[str, list[str], bool]]:
    if not isinstance(pack, (list, tuple)):
        raise WorkerError("pack must be a list")
    items = []
    for item in pack:
        if (
            not isinstance(item, dict)
            or not isinstance(item.get("alias"), str)
            or not isinstance(item.get("content"), str)
        ):
            raise WorkerError("pack item needs text alias and content")
        tokens = _tokens(item["content"])
        items.append((item["alias"], tokens, _has_negative_cue(tokens)))
    return items


def _check_task(task: Any) -> list[dict]:
    steps = task.get("steps") if isinstance(task, dict) else None
    if not isinstance(steps, list) or not steps:
        raise WorkerError("task needs a non-empty steps list")
    for entry in steps:
        if not isinstance(entry, dict) or set(entry) != _STEP_KEYS:
            raise WorkerError("task step has the wrong shape")
        actions = entry["actions"]
        if (
            not isinstance(actions, list)
            or len(actions) < 2
            or len(set(actions)) != len(actions)
            or not all(isinstance(a, str) and a for a in actions)
        ):
            raise WorkerError("task step needs two or more distinct action ids")
        if entry["retry_when"] not in _RETRY_WHEN:
            raise WorkerError("task step retry_when is not supported")
        if type(entry["retry_limit"]) is not int or entry["retry_limit"] < 0:
            raise WorkerError("task step retry_limit must be a non-negative integer")
        if type(entry["may_abstain"]) is not bool:
            raise WorkerError("task step may_abstain must be a boolean")
    return steps


def _score_step(entry: dict, items: list[tuple[str, list[str], bool]]) -> tuple[dict, list[str]]:
    scores = {action: 0 for action in entry["actions"]}
    used: set[str] = set()
    for alias, tokens, negative in items:
        for action in entry["actions"]:
            terms = {t for t in _tokens(action.replace("_", " "))}
            overlap = sum(1 for term in terms if any(_terms_match(term, tok) for tok in tokens))
            if not overlap:
                continue
            scores[action] += -overlap if negative else overlap
            used.add(alias)
    return scores, sorted(used)


def _step_rows(entry: dict, items: list[tuple[str, list[str], bool]]) -> list[dict]:
    scores, used = _score_step(entry, items)
    if entry["may_abstain"] and all(score < 0 for score in scores.values()):
        return [
            {
                "step": entry["step"],
                "action": ABSTAIN,
                "used_aliases": used,
                "retry": False,
                "tool_call": False,
            }
        ]
    top = max(scores.values())
    tied = [a for a, score in scores.items() if score == top]
    choice = min(tied, key=_sha)
    retries = entry["retry_limit"] if entry["retry_when"] == "ambiguous_nonzero" else 0
    if len(tied) < 2 or top == 0:
        retries = 0
    row = {"step": entry["step"], "action": choice, "used_aliases": used, "tool_call": True}
    return [{**row, "retry": True} for _ in range(retries)] + [{**row, "retry": False}]


def run_worker(query: Any, request: Any, task: Any, pack: Any, config: Any) -> list[dict]:
    """Choose one action per task step from the pack alone. Deterministic; no model call."""
    limit = _check_config(config)
    if not isinstance(query, str) or not isinstance(request, dict):
        raise WorkerError("query must be text and request an object")
    steps = _check_task(task)
    items = _check_pack(pack)
    rows: list[dict] = []
    for entry in steps:
        rows.extend(_step_rows(entry, items))
        if len(rows) > limit:
            raise WorkerError("worker trace exceeds max_trace_steps")
    return rows
