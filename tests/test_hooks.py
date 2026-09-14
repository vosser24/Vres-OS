import json
from pathlib import Path

from vres_os.transcript import last_assistant_snapshot


def test_last_assistant_snapshot_best_effort(tmp_path: Path):
    p = tmp_path / "transcript.jsonl"
    rows = [
        {"type": "user", "message": {"role": "user", "content": [{"type": "text", "text": "hello"}]}},
        {"type": "assistant", "message": {"role": "assistant", "content": [{"type": "text", "text": "result one"}]}},
        {"type": "assistant", "message": {"role": "assistant", "content": [{"type": "text", "text": "latest result"}]}},
    ]
    p.write_text("\n".join(json.dumps(x) for x in rows), encoding="utf-8")
    assert last_assistant_snapshot({"transcript_path": str(p)}) == "latest result"
