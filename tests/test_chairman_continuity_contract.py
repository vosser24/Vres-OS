from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_chairman_must_checkpoint_before_reply_advances_persisted_work():
    text = (ROOT / "plugins/vres-os/agents/chairman.md").read_text(encoding="utf-8")
    assert "Before sending any reply that completes, invalidates, or advances the persisted `next_action` or `pending_work`" in text
    assert "call `task_checkpoint` first" in text
    assert "refreshed `next_action`, `completed_work`, and `pending_work`" in text
    assert "Before every final reply while a persistent task is bound, call `task_reply_gate`" in text
    assert "Set `advances_state=true` only after that current-turn checkpoint" in text
    assert "use `advances_state=false` only for a genuinely non-material reply" in text
    assert "The Stop hook checks only this authoritative gate/state evidence, never assistant prose" in text
    assert "Stop-hook assistant snapshot is non-authoritative recovery evidence" in text
    assert "never substitutes for this checkpoint" in text
