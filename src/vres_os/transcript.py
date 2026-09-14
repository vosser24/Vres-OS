from __future__ import annotations
import json
from pathlib import Path
from typing import Any

MAX_TRANSCRIPT_TAIL = 2 * 1024 * 1024

def _text_from_content(value: Any, depth: int = 0) -> list[str]:
    if depth > 12:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [text for item in value[:100] for text in _text_from_content(item, depth + 1)]
    if isinstance(value, dict):
        if value.get("type") in {"thinking", "tool_use", "tool_result"}:
            return []
        if value.get("type") == "text" and isinstance(value.get("text"), str):
            return [value["text"]]
        return [text for key in ("content", "message") if key in value
                for text in _text_from_content(value[key], depth + 1)]
    return []

def transcript_tail(path: Path) -> list[dict]:
    if path.is_symlink() or not path.is_file():
        return []
    try:
        with path.open("rb") as handle:
            size = handle.seek(0, 2)
            start = max(0, size - MAX_TRANSCRIPT_TAIL)
            handle.seek(start)
            raw = handle.read(MAX_TRANSCRIPT_TAIL)
        lines = raw.splitlines()
        if start and lines:
            lines = lines[1:]  # first line may start inside a UTF-8 character / JSON record
    except OSError:
        return []
    result = []
    for line in lines[-300:]:
        try:
            obj = json.loads(line)
        except (ValueError, UnicodeError, RecursionError):
            continue
        if isinstance(obj, dict):
            result.append(obj)
    return result

def last_assistant_snapshot(payload: dict[str, Any], max_chars: int = 6000) -> str | None:
    """Bounded recovery aid, never an authority source or hidden-reasoning store."""
    if max_chars <= 0:
        return None
    direct = payload.get("last_assistant_message")
    if isinstance(direct, str) and direct:
        return direct[-max_chars:]
    raw_path = payload.get("transcript_path") or payload.get("transcriptPath")
    if not raw_path:
        return None
    for obj in reversed(transcript_tail(Path(str(raw_path)))):
        message = obj.get("message")
        role = message.get("role") if isinstance(message, dict) else obj.get("role")
        if obj.get("type") == "assistant" or role == "assistant":
            texts = _text_from_content(message if message is not None else obj)
            if texts:
                return "\n".join(texts)[-max_chars:]
    return None
