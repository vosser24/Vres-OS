from __future__ import annotations

import inspect
from pathlib import Path

from vres_os.mcp_server import task_checkpoint
from vres_os.validation import state_digest

ROOT = Path(__file__).resolve().parents[1]


def test_checkpoint_tool_exposes_first_class_decisions():
    parameters = inspect.signature(task_checkpoint).parameters
    assert "decisions" in parameters
    assert parameters["decisions"].default is None


def test_decisions_are_material_validation_state():
    base = {
        "objective": "Prove continuity",
        "state_summary": "Ready",
        "decisions": ["Use synthetic test information only."],
    }
    assert state_digest(base) != state_digest(
        base | {"decisions": ["Use production information."]}
    )


def test_task_decisions_migration_is_bounded_to_task_state():
    migration = (ROOT / "src" / "vres_os" / "migrations" / "016_task_decisions.sql").read_text(encoding="utf-8")
    assert "ALTER TABLE vres.task_state" in migration
    assert "decisions jsonb NOT NULL DEFAULT '[]'::jsonb" in migration
    assert "approval" not in migration.lower()
