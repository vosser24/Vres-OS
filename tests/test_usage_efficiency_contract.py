from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_usage_efficiency_rules_stay_small_and_native():
    rules = (ROOT / "rules" / "vres-rules.md").read_text(encoding="utf-8")
    assert "Context compaction." in rules
    for phrase in [
        "user objective/constraints",
        "tests/evidence actually run",
        "unresolved blockers",
        "exact next action",
        "Drop repeated explanations",
        "Vres checkpoints remain authoritative",
    ]:
        assert phrase in rules
    assert "custom compactor" not in rules.lower()


def test_engineering_skill_uses_conditional_bounded_reads_and_native_bash():
    skill = (
        ROOT / "plugins" / "vres-os" / "skills" / "engineering-execution" / "SKILL.md"
    ).read_text(encoding="utf-8")
    assert "For large or unfamiliar files/logs" in skill
    assert "Read short or already-known files directly" in skill
    assert "smallest useful surrounding range" in skill
    assert "Keep native Bash output bounded" in skill
    assert "Preserve the real command exit status" in skill
    assert "Avoid dumping large trees, logs, or full build/test output" in skill


def test_usage_efficiency_does_not_move_statusline_into_plugin_defaults():
    settings = (
        ROOT / "plugins" / "vres-os" / "settings.json"
    ).read_text(encoding="utf-8")
    assert "statusLine" not in settings
    assert '"agent": "chairman"' in settings


def test_statusline_renderer_has_no_db_network_transcript_or_polling_dependency():
    text = (ROOT / "src" / "vres_os" / "statusline.py").read_text(encoding="utf-8")
    lowered = text.lower()
    assert "vres_os.statusline" in text
    assert "rate_limits" in text and "five_hour" in text and "seven_day" in text
    assert "context_window" in text and "effort" in text
    assert "from .db" not in text
    assert "connect(" not in text
    assert "requests" not in lowered
    assert "httpx" not in lowered
    assert "transcript_path" not in text
    assert "sleep(" not in text
    assert "refreshInterval" not in text
