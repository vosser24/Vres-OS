from importlib import resources
from pathlib import Path

from vres_os.reply_guard import confirm_reply_gate

ROOT = Path(__file__).resolve().parents[1]


def _migration(name: str) -> str:
    return resources.files("vres_os").joinpath("migrations", name).read_text(encoding="utf-8")


def test_migration_022_guards_decision_insert_provenance():
    sql = _migration("022_task_decision_insert_provenance.sql")
    assert "CREATE OR REPLACE FUNCTION vres.validate_task_decision_insert" in sql
    assert "BEFORE INSERT ON vres.task_decisions" in sql
    assert "legacy_unstructured decisions may only originate from migration 020" in sql
    assert "USER_INSTRUCTION event on the same task" in sql
    assert "source session/time must match" in sql
    assert "source session must be open and bound to the task" in sql
    assert "replacement decision must supersede an active decision on the same task" in sql


def test_reply_guard_contains_mechanically_verified_validation_in_flight_mode():
    source = Path(confirm_reply_gate.__code__.co_filename).read_text(encoding="utf-8")
    assert "_current_validation_in_flight" in source
    assert '"validation_in_flight"' in source
    assert "request['state_digest']" in source or 'request["state_digest"]' in source
    assert "checkpoint[\"created_at\"] < started_at" in source
    assert "request[\"created_at\"] < checkpoint[\"created_at\"]" in source


def test_chairman_contract_freezes_before_validation_and_does_not_checkpoint_after_freeze():
    text = (ROOT / "plugins" / "vres-os" / "agents" / "chairman.md").read_text(encoding="utf-8")
    assert "checkpoint the final review state before `validation_prepare`" in text
    assert "mode to be `validation_in_flight`" in text
    assert "Do not call `task_checkpoint` after `validation_prepare` merely to announce dispatch" in text
    assert "Never mis-declare other material progress as non-material" in text
