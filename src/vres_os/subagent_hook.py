from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

from .project import discover_project
from .redaction import redact_text
from .repository import Repository
from .routing import RoutingService, _json_report
from .transcript import _text_from_content, transcript_tail


def _input() -> dict[str, Any]:
    try:
        raw = sys.stdin.read(1024 * 1024 + 1)
        if len(raw) > 1024 * 1024:
            return {}
        value = json.loads(raw) if raw.strip() else {}
        return value if isinstance(value, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def _project_id(payload: dict[str, Any]) -> int:
    project = discover_project(payload.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR", "."))
    return Repository().ensure_project(project)


def _assistant_handback_messages(value: Any) -> list[str]:
    """Extract only assistant-authored SubagentHandback messages.

    Claude Code can deliver a background subagent's canonical final result through a
    SubagentHandback tool call instead of repeating it as ordinary assistant text.
    Tool results and non-assistant records are deliberately never treated as routing
    authority.
    """
    if not isinstance(value, dict):
        return []
    content = value.get("content")
    if not isinstance(content, list):
        return []
    result: list[str] = []
    for block in content[:100]:
        if not isinstance(block, dict) or block.get("type") != "tool_use":
            continue
        if block.get("name") != "SubagentHandback":
            continue
        tool_input = block.get("input")
        if not isinstance(tool_input, dict):
            continue
        message = tool_input.get("message")
        if isinstance(message, str) and message.strip():
            result.append(message)
    return result


def _routing_payload_with_handback(payload: dict[str, Any]) -> dict[str, Any]:
    """Bridge a canonical assistant hand-back into the existing routing hook contract.

    Priority stays identical to the routing service's intended trust order:
    last_assistant_message first, then ordinary assistant transcript text, and only
    then an assistant-authored SubagentHandback message. The routing service still
    re-reads the transcript, verifies the Fable model family, validates request_key
    and decision contents, and persists the result.
    """
    final = payload.get("last_assistant_message")
    if isinstance(final, str) and final.strip():
        try:
            _json_report(final)
            return payload
        except (ValueError, TypeError, json.JSONDecodeError):
            pass

    transcript = payload.get("agent_transcript_path")
    if not transcript:
        return payload
    records = transcript_tail(Path(str(transcript)).expanduser())

    # If ordinary assistant text already contains valid routing JSON, leave the
    # payload untouched so RoutingService._observed_report() recovers it itself.
    for obj in reversed(records):
        if not isinstance(obj, dict):
            continue
        message = obj.get("message")
        role = message.get("role") if isinstance(message, dict) else obj.get("role")
        if obj.get("type") != "assistant" and role != "assistant":
            continue
        observed = message if isinstance(message, dict) else obj
        texts = _text_from_content(observed)
        candidates: list[str] = []
        if texts:
            candidates.append("\n".join(texts))
            candidates.extend(reversed(texts))
        for candidate in candidates:
            try:
                _json_report(candidate)
                return payload
            except (ValueError, TypeError, json.JSONDecodeError):
                continue

    # Only after ordinary assistant text fails do we consider assistant-authored
    # hand-backs. Never inspect arbitrary tool_result content.
    seen: set[str] = set()
    for obj in reversed(records):
        if not isinstance(obj, dict):
            continue
        message = obj.get("message")
        role = message.get("role") if isinstance(message, dict) else obj.get("role")
        if obj.get("type") != "assistant" and role != "assistant":
            continue
        observed = message if isinstance(message, dict) else obj
        for candidate in reversed(_assistant_handback_messages(observed)):
            candidate = candidate.strip()
            if not candidate or candidate in seen:
                continue
            seen.add(candidate)
            try:
                _json_report(candidate)
            except (ValueError, TypeError, json.JSONDecodeError):
                continue
            bridged = dict(payload)
            bridged["last_assistant_message"] = candidate
            return bridged
    return payload


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    payload = _input()
    try:
        pid = _project_id(payload)
        service = RoutingService()
        if mode == "routing-stop":
            service.record_routing_from_hook(_routing_payload_with_handback(payload), pid)
        elif mode == "worker-stop":
            service.record_worker_from_hook(payload, pid)
        else:
            raise ValueError("Unsupported Vres subagent hook mode")
    except Exception as exc:
        detail = redact_text(str(exc))[:800]
        sys.stderr.write(f"Vres governed subagent evidence was not accepted: {detail}.\n")
        raise SystemExit(2) from exc


if __name__ == "__main__":
    main()
