"""R13L original release-cohort source contract. AUTHORED / NOT_RUN.

No original Vres import, Python AST/compile/pytest, SQL, PostgreSQL, host,
Windows update or release validation was run under the absolute holds.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / "src/vres_os/release_inputs.py"
HOOKS = ROOT / "src/vres_os/hooks.py"
STAGE = ROOT / "src/vres_os/session_prompts.py"
DB = ROOT / "src/vres_os/db.py"
ARTIFACT = ROOT / "src/vres_os/release_artifact.py"
INSTALL = ROOT / "install.ps1"
OPS = ROOT / "w4-operations-holds.json"


def test_original_strict_stage_requires_entire_prospective_host_turn_cohort():
    release = RELEASE.read_text(encoding="utf-8")
    stage = STAGE.read_text(encoding="utf-8")
    db = DB.read_text(encoding="utf-8")
    assert "PERSONAL_RELEASE_MAX_MIGRATION = 41" in release
    assert "ORIGINAL_CLAUDE_STRICT_STAGE_MIN_MIGRATION = 47" in release
    for version in ("042_", "043_", "044_", "045_", "046_", "047_"):
        assert version in release
    assert 'name not in PERSONAL_MIGRATION_PINS' in release
    assert '"VRES_W4_HELD_RELEASE_COHORT:' in release
    assert "stage_strict_user_input" in stage
    assert "begin_reply_turn" in HOOKS.read_text(encoding="utf-8")
    assert "require_w4_schema_clearance()" in db


def test_no_automatic_release_or_migration_pin_escalation():
    release = RELEASE.read_text(encoding="utf-8")
    artifact = ARTIFACT.read_text(encoding="utf-8")
    installer = INSTALL.read_text(encoding="utf-8")
    holds = OPS.read_text(encoding="utf-8")
    assert 'W4_RELEASE_INPUT_SOURCE_INTERLOCK = "HELD_NO_ORIGINAL_RELEASE_VALIDATION"' in release
    assert 'W4_STAGE_SOURCE_INTERLOCK = "HELD_SOURCE_ONLY"' in artifact
    assert "$W4SourceInterlock = 'HELD_SOURCE_ONLY'" in installer
    assert '"LIVE_SCHEMA_048_INCIDENT": "OPEN_NO_POSTGRESQL_EVEN_SELECT"' in holds
    assert '"HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED": "OPEN_NO_NATIVE_CLAUDE_OR_HOOKS"' in holds
    assert "048_" not in release.split("PERSONAL_MIGRATION_PINS = {", 1)[1].split("}", 1)[0]


def test_cohort_check_occurs_inside_original_validator_before_migration_scan():
    release = RELEASE.read_text(encoding="utf-8")
    function = release.split("def release_input_problems(", 1)[1].split("def main(", 1)[0]
    assert function.index("require_w4_release_input_clearance()") < function.index("missing_stage_pins =")
    assert function.index("missing_stage_pins =") < function.index("migrations = root / MIGRATIONS_DIR")
    assert "No PostgreSQL contact" in function
