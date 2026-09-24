"""Vres-owned live Claude Code experiment producer.

Host-evidence plumbing only: it runs one bounded, isolated ``claude --print`` call and
returns a validated immutable observation. It never touches routing, model policy or the
protected validator, and it is deliberately not exposed through MCP. The frozen invocation
contract and the evidence rules are owned by ``model_experiments``; the parser here is
fail-closed against the physically observed Claude Code 2.1.281 result envelope.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import tempfile
import time
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Any

from .model_experiments import (
    CLAUDE_HOST_ADAPTER,
    CLAUDE_HOST_COST_SEMANTICS,
    CLAUDE_HOST_EVIDENCE_KIND,
    CLAUDE_HOST_FAMILIES,
    CLAUDE_HOST_PROVIDER_LABEL,
    CLAUDE_HOST_SOURCE,
    CLAUDE_MODEL_RE,
    HOST_ID_RE,
    claude_host_invocation,
    parse_host_cost,
    project_estimated_cost,
)
from .processes import MAX_OUTPUT_BYTES, MAX_PROMPT_BYTES, run_bounded
from .redaction import redact, redact_text

# Markers that Claude Code exports into its own child processes. Their presence means this
# process runs inside Claude Code; the producer refuses instead of scrubbing and continuing.
NESTED_ENV_MARKERS = (
    "CLAUDECODE",
    "CLAUDE_CODE_SESSION_ID",
    "CLAUDE_CODE_CHILD_SESSION",
    "CLAUDE_CODE_ENTRYPOINT",
    "CLAUDE_CODE_EXECPATH",
    "CLAUDE_CODE_MESSAGING_SOCKET",
    "CLAUDE_CODE_MESSAGING_TOKEN",
    "CLAUDE_CODE_SESSION_ATTENDED",
    "CLAUDE_PID",
)
# Host-level overrides that could silently replace the explicit --effort request.
OVERRIDE_ENV_MARKERS = ("CLAUDE_EFFORT",)
_WRAPPER_SUFFIXES = frozenset({".cmd", ".bat", ".ps1", ".vbs", ".js"})
_VERSION_RE = re.compile(r"^(\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?) \(Claude Code\)$")
_RAW_ENTRY_LIMIT = 4096


class ClaudeExperimentError(ValueError):
    """The experiment call is unsafe, failed, or produced evidence that cannot be trusted."""


@dataclass(slots=True, frozen=True)
class ClaudeExperimentObservation:
    requested_family: str
    effort: str
    physical_model: str
    input_digest: str
    output_digest: str
    result_text: str = field(repr=False)
    runtime_ms: int
    input_tokens: int
    output_tokens: int
    cache_read_input_tokens: int
    cache_creation_input_tokens: int
    thinking_tokens: int | None
    context_window: int
    host_cost_usd: str
    host_total_cost_usd: str
    host_result_id: str
    host_session_id: str
    host_duration_ms: int | None
    host_duration_api_ms: int | None
    host_provider_label: str
    host_cost_basis: str
    claude_code_version: str
    host_model_usage_raw: dict[str, Any] | None = field(repr=False)

    @property
    def estimated_cost(self) -> Decimal:
        """Host list-price estimate projected to the numeric(14,6) column scale."""
        return project_estimated_cost(self.host_cost_usd)

    def execution_evidence(self) -> dict[str, Any]:
        evidence: dict[str, Any] = {
            "evidence_kind": CLAUDE_HOST_EVIDENCE_KIND,
            "adapter": CLAUDE_HOST_ADAPTER,
            "provider": "claude",
            "provider_model": self.physical_model,
            "requested_model_family": self.requested_family,
            "identity_source": CLAUDE_HOST_SOURCE,
            "usage_source": CLAUDE_HOST_SOURCE,
            "host_result_id": self.host_result_id,
            "host_session_id": self.host_session_id,
            "effort_source": "adapter_request",
            "requested_effort": self.effort,
            "runtime_source": "adapter_monotonic",
            "runtime_ms": self.runtime_ms,
            "host_duration_ms": self.host_duration_ms,
            "host_duration_api_ms": self.host_duration_api_ms,
            "completion_success": True,
            "host_provider_label": self.host_provider_label,
            "host_cost_basis": self.host_cost_basis,
            "claude_code_version": self.claude_code_version,
            "invocation_contract": claude_host_invocation(self.requested_family, self.effort),
            "host_usage": {
                "input_tokens": self.input_tokens,
                "output_tokens": self.output_tokens,
                "cache_read_input_tokens": self.cache_read_input_tokens,
                "cache_creation_input_tokens": self.cache_creation_input_tokens,
                "thinking_tokens": self.thinking_tokens,
                "context_window": self.context_window,
            },
            "host_cost_usd": self.host_cost_usd,
            "host_total_cost_usd": self.host_total_cost_usd,
            "cost_semantics": CLAUDE_HOST_COST_SEMANTICS,
        }
        if self.host_model_usage_raw is not None:
            evidence["host_model_usage_raw"] = self.host_model_usage_raw
        return evidence


def assert_not_nested(environ: Any = None) -> None:
    env = os.environ if environ is None else environ
    nested = [name for name in NESTED_ENV_MARKERS if name in env]
    if nested:
        raise ClaudeExperimentError(
            "Refusing to run Claude Code from inside a Claude Code session; "
            "run this command from a separate terminal (found " + ", ".join(nested) + ")"
        )
    overrides = [name for name in OVERRIDE_ENV_MARKERS if name in env]
    if overrides:
        raise ClaudeExperimentError(
            "Refusing to run with an environment override that could replace the explicit effort: "
            + ", ".join(overrides)
        )


def find_native_claude() -> str:
    found = shutil.which("claude")
    if not found:
        raise ClaudeExperimentError("The native claude executable was not found on PATH")
    path = Path(found)
    suffix = path.suffix.lower()
    if suffix in _WRAPPER_SUFFIXES or (os.name == "nt" and suffix != ".exe"):
        raise ClaudeExperimentError("Refusing a claude script/shell wrapper; a native executable is required")
    if not path.is_file():
        raise ClaudeExperimentError("The claude executable path is not a regular file")
    return str(path)


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _no_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            raise ValueError(f"duplicate JSON key {key!r}")
        out[key] = value
    return out


def _reject_constant(name: str) -> Any:
    raise ValueError(f"non-finite JSON constant {name}")


def _int(value: Any, label: str, *, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        raise ClaudeExperimentError(f"Claude Code result {label} must be an integer >= {minimum}")
    return value


def _optional_int(value: Any, label: str) -> int | None:
    return None if value is None else _int(value, label)


def _cost(value: Any, label: str) -> Decimal:
    if type(value) is int:
        value = Decimal(value)
    if not isinstance(value, Decimal):  # the host emits a JSON number, never text
        raise ClaudeExperimentError(f"Claude Code result {label} must be a JSON number")
    try:
        return parse_host_cost(value, label)
    except ValueError as exc:
        raise ClaudeExperimentError(f"Claude Code result {label} is invalid: {exc}") from exc


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ClaudeExperimentError(f"Claude Code result is missing {label}")
    return value


def _host_id(value: Any, label: str) -> str:
    if not isinstance(value, str) or not HOST_ID_RE.fullmatch(value):
        raise ClaudeExperimentError(f"Claude Code result has no valid {label}")
    return value


def _jsonable(value: Any, depth: int = 0) -> Any:
    if depth > 3:
        raise ValueError("nested too deeply")
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, dict):
        return {str(k): _jsonable(v, depth + 1) for k, v in value.items()}
    if isinstance(value, list):
        return [_jsonable(v, depth + 1) for v in value]
    return value


def _raw_entry(entry: dict[str, Any]) -> dict[str, Any] | None:
    """Keep the verbatim modelUsage entry only when it is small and free of secret-like text."""
    try:
        safe = _jsonable(entry)
        encoded = json.dumps(safe, sort_keys=True)
    except (TypeError, ValueError):
        return None
    if len(encoded) > _RAW_ENTRY_LIMIT or redact(safe) != safe:
        return None
    return safe


def parse_claude_result(
    text: str,
    *,
    family: str,
    effort: str,
    input_digest: str,
    runtime_ms: int,
    claude_code_version: str,
) -> ClaudeExperimentObservation:
    """Parse one Claude Code ``--output-format json`` result, failing closed on any deviation."""
    claude_host_invocation(family, effort)  # validates family/effort membership
    if text.startswith("[earlier output omitted]"):
        raise ClaudeExperimentError("Claude Code output was truncated")
    try:
        data = json.loads(
            text,
            parse_float=Decimal,
            parse_constant=_reject_constant,
            object_pairs_hook=_no_duplicate_keys,
        )
    except (ValueError, RecursionError) as exc:
        raise ClaudeExperimentError("Claude Code output is not exactly one JSON object") from exc
    if not isinstance(data, dict):
        raise ClaudeExperimentError("Claude Code output is not exactly one JSON object")
    if data.get("type") != "result" or data.get("subtype") != "success":
        raise ClaudeExperimentError("Claude Code did not report a successful result")
    if data.get("is_error") is not False:
        raise ClaudeExperimentError("Claude Code reported an error result")
    if type(data.get("num_turns")) is not int or data["num_turns"] != 1:
        raise ClaudeExperimentError("Claude Code experiment must complete in exactly one turn")
    result = data.get("result")
    if not isinstance(result, str):
        raise ClaudeExperimentError("Claude Code result text is missing")
    try:
        output_bytes = result.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise ClaudeExperimentError("Claude Code result text is not valid UTF-8") from exc
    session_id = _host_id(data.get("session_id"), "session_id")
    result_id = _host_id(data.get("uuid"), "result uuid")

    models = data.get("modelUsage")
    if not isinstance(models, dict) or len(models) != 1:
        raise ClaudeExperimentError("Claude Code result must report exactly one physical model")
    (physical, entry), = models.items()
    matched = CLAUDE_MODEL_RE.fullmatch(physical)
    if not matched or matched.group(1) != family:
        raise ClaudeExperimentError("Claude Code physical model does not match the requested family")
    if not isinstance(entry, dict):
        raise ClaudeExperimentError("Claude Code modelUsage entry is malformed")
    if entry.get("canonicalModel") != physical:
        raise ClaudeExperimentError("Claude Code canonicalModel does not match the physical model")
    if entry.get("provider") != CLAUDE_HOST_PROVIDER_LABEL:
        raise ClaudeExperimentError("Claude Code provider label must be firstParty")
    cost_basis = _text(entry.get("costBasis"), "costBasis")

    counts = {
        "input_tokens": _int(entry.get("inputTokens"), "inputTokens"),
        "output_tokens": _int(entry.get("outputTokens"), "outputTokens"),
        "cache_read_input_tokens": _int(entry.get("cacheReadInputTokens"), "cacheReadInputTokens"),
        "cache_creation_input_tokens": _int(entry.get("cacheCreationInputTokens"), "cacheCreationInputTokens"),
    }
    usage = data.get("usage")
    if not isinstance(usage, dict):
        raise ClaudeExperimentError("Claude Code result has no top-level usage")
    for key, value in counts.items():
        if _int(usage.get(key), f"usage.{key}") != value:
            raise ClaudeExperimentError("Claude Code top-level usage disagrees with per-model usage")
    if counts["output_tokens"] <= 0 or (
        counts["input_tokens"] + counts["cache_read_input_tokens"] + counts["cache_creation_input_tokens"] <= 0
    ):
        raise ClaudeExperimentError("Claude Code reported no observed usage")
    thinking = _optional_int(entry.get("thinkingTokens"), "thinkingTokens")
    details = usage.get("output_tokens_details")
    top_thinking = (
        _optional_int(details.get("thinking_tokens"), "usage.thinking_tokens")
        if isinstance(details, dict)
        else None
    )
    if thinking is not None and top_thinking is not None and thinking != top_thinking:
        raise ClaudeExperimentError("Claude Code thinking-token counts disagree")
    thinking = thinking if thinking is not None else top_thinking
    context_window = _int(entry.get("contextWindow"), "contextWindow", minimum=1)

    model_cost = _cost(entry.get("costUSD"), "costUSD")
    total_cost = _cost(data.get("total_cost_usd"), "total_cost_usd")
    if model_cost != total_cost:
        raise ClaudeExperimentError("Claude Code per-model cost and total cost disagree")

    return ClaudeExperimentObservation(
        requested_family=family,
        effort=effort,
        physical_model=physical,
        input_digest=input_digest,
        output_digest=_digest(output_bytes),
        result_text=result,
        runtime_ms=_int(runtime_ms, "adapter runtime"),
        thinking_tokens=thinking,
        context_window=context_window,
        host_cost_usd=format(model_cost, "f"),
        host_total_cost_usd=format(total_cost, "f"),
        host_result_id=result_id,
        host_session_id=session_id,
        host_duration_ms=_optional_int(data.get("duration_ms"), "duration_ms"),
        host_duration_api_ms=_optional_int(data.get("duration_api_ms"), "duration_api_ms"),
        host_provider_label=CLAUDE_HOST_PROVIDER_LABEL,
        host_cost_basis=cost_basis,
        claude_code_version=_text(claude_code_version, "claude_code_version"),
        host_model_usage_raw=_raw_entry(entry),
        **counts,
    )


def _claude_version(executable: str, cwd: Path) -> str:
    probe = run_bounded(
        [executable, "--version"],
        cwd=cwd,
        timeout=30,
        max_output_bytes=4096,
        max_result_chars=4096,
        redact_output=False,
        stdin_devnull=True,
    )
    matched = _VERSION_RE.fullmatch(probe.output.strip()) if probe.ok else None
    if not matched:
        raise ClaudeExperimentError("Could not read the Claude Code version")
    return matched.group(1)


def run_claude_experiment(
    *,
    prompt: str,
    family: str,
    effort: str,
    timeout: float = 300,
) -> ClaudeExperimentObservation:
    """Run one bounded, isolated, tool-less Claude Code call and return validated host evidence."""
    if family not in CLAUDE_HOST_FAMILIES:
        raise ClaudeExperimentError("Claude Code experiments support only the sonnet and opus families")
    contract = claude_host_invocation(family, effort)
    if not isinstance(prompt, str) or not prompt.strip():
        raise ClaudeExperimentError("A non-empty experiment prompt is required")
    try:
        prompt_bytes = prompt.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise ClaudeExperimentError("The experiment prompt is not valid UTF-8") from exc
    if len(prompt_bytes) > MAX_PROMPT_BYTES:
        raise ClaudeExperimentError("The experiment prompt exceeds the prompt budget")
    if redact_text(prompt) != prompt:
        raise ClaudeExperimentError("Remove credentials from the prompt before invoking Claude Code")
    assert_not_nested()
    executable = find_native_claude()
    with tempfile.TemporaryDirectory(prefix="vres-claude-experiment-") as scratch:
        cwd = Path(scratch)
        version = _claude_version(executable, cwd)
        started = time.monotonic_ns()
        outcome = run_bounded(
            [executable, *contract["argv"]],
            cwd=cwd,
            prompt=prompt,
            timeout=timeout,
            max_output_bytes=MAX_OUTPUT_BYTES,
            max_result_chars=MAX_OUTPUT_BYTES,
            redact_output=False,
        )
        runtime_ms = (time.monotonic_ns() - started) // 1_000_000
    if not outcome.ok:
        reason = {124: "timed out", 125: "exceeded its output budget"}.get(
            outcome.returncode, f"exited with code {outcome.returncode}"
        )
        raise ClaudeExperimentError(f"Claude Code {reason}: {redact_text(outcome.output)[:300]}")
    return parse_claude_result(
        outcome.output,
        family=family,
        effort=effort,
        input_digest=_digest(prompt_bytes),
        runtime_ms=runtime_ms,
        claude_code_version=version,
    )
