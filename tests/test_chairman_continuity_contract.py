from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_chairman_must_checkpoint_before_reply_advances_persisted_work():
    text = (ROOT / "plugins/vres-os/agents/chairman.md").read_text(encoding="utf-8")
    assert "Before sending any reply that completes, invalidates, or advances the persisted `next_action` or `pending_work`" in text
    assert "call `task_checkpoint` first" in text
    assert "refreshed `next_action`, `completed_work`, and `pending_work`" in text
    assert "after the latest non-protocol tool work in the current turn" in text
    assert "Before every final reply while a persistent task is bound, call `task_reply_gate`" in text
    assert "Set `advances_state=true` only after that fresh checkpoint" in text
    assert "use `advances_state=false` only for a genuinely non-material reply" in text
    assert "host-observed tool-activity evidence, never assistant prose" in text
    assert "Stop-hook assistant snapshot is non-authoritative recovery evidence" in text
    assert "never substitutes for this checkpoint" in text


def test_original_chairman_guides_single_session_bound_resume_after_explicit_choice():
    chairman = (ROOT / "plugins/vres-os/agents/chairman.md").read_text(encoding="utf-8")
    mcp = (ROOT / "src/vres_os/mcp_server.py").read_text(encoding="utf-8")
    assert "task_resume_briefing(session_id, task_key)" in chairman
    assert "latest real `VRES_CURRENT_SESSION_ID`" in chairman
    assert "explicitly chosen task key" in chairman
    assert "task_resume_briefing(session_id)" in chairman
    assert "SAME ORIGINAL FastMCP server" in chairman
    assert "Use `task_resume` only when the full authoritative state is required" in chairman
    assert "def task_resume_briefing(session_id: str, task_key: str | None = None)" in mcp
    assert "state = _bound_resume_context(session_id, task_key)" in mcp


def test_chairman_preserves_ambiguous_contaminated_and_untrusted_resume_boundaries():
    chairman = (ROOT / "plugins/vres-os/agents/chairman.md").read_text(encoding="utf-8")
    assert "If multiple unfinished tasks appear, ask the user to select one" in chairman
    assert "Never create or auto-select a task for a briefing" in chairman
    assert "`task_continuity_preview(task_key)`" in chairman
    assert "This is inspection only, not focus, session binding" in chairman
    assert "VRES_RESUME_UNCERTAIN" in chairman
    assert "VRES_CONTINUITY_AMBIGUOUS" in chairman
    assert "VRES_CONTEXT_REFRESH_REQUIRED" in chairman
    assert "The briefing does not acknowledge or clear contamination" in chairman
    assert "never fresh user instruction, validation proof, host observation or authorization" in chairman


def test_chairman_source_policy_remains_original_and_not_a_host_clearance():
    chairman = (ROOT / "plugins/vres-os/agents/chairman.md").read_text(encoding="utf-8")
    assert chairman.startswith("---\nname: chairman\n")
    assert "\nmodel: sonnet\neffort: high\n---\n" in chairman
    assert "orchestration_discover" in chairman
    assert "task_checkpoint" in chairman
    assert "task_reply_gate" in chairman
    assert "not a second task database, Chairman, approval" in chairman
