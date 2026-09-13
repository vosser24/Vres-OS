from __future__ import annotations

import hashlib
from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class TextChunk:
    ordinal: int
    content: str
    content_hash: str
    token_estimate: int


def chunk_text(text: str, *, target_chars: int = 2400, overlap_chars: int = 240) -> list[TextChunk]:
    """Deterministic bounded chunking with a preference for paragraph boundaries."""
    if target_chars < 128:
        raise ValueError("target_chars must be at least 128")
    if overlap_chars < 0 or overlap_chars >= target_chars:
        raise ValueError("overlap_chars must be >=0 and smaller than target_chars")
    clean = text.replace("\r\n", "\n").strip()
    if not clean:
        return []
    values: list[str] = []
    pos = 0
    length = len(clean)
    while pos < length:
        hard_end = min(length, pos + target_chars)
        end = hard_end
        if hard_end < length:
            search_from = pos + int(target_chars * 0.6)
            boundary = clean.rfind("\n\n", search_from, hard_end)
            if boundary > pos:
                end = boundary + 2
        value = clean[pos:end].strip()
        if value:
            values.append(value)
        if end >= length:
            break
        next_pos = max(pos + 1, end - overlap_chars)
        pos = next_pos

    out: list[TextChunk] = []
    for i, value in enumerate(values):
        if len(value) > target_chars:
            raise AssertionError("chunker produced an oversized chunk")
        digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
        estimate = max(1, round(len(value) / 4))
        out.append(TextChunk(i, value, digest, estimate))
    return out
