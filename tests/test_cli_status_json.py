from datetime import date, datetime, timezone
from io import StringIO
from types import SimpleNamespace

from rich.console import Console

from vres_os import cli


def test_status_serializes_nested_database_datetimes_and_redacts(monkeypatch, tmp_path):
    cfg = SimpleNamespace(configured=True, profile="default")
    monkeypatch.setattr(cli, "ConfigStore", lambda: SimpleNamespace(load=lambda: cfg))
    monkeypatch.setattr(
        cli,
        "discover_project",
        lambda _root: SimpleNamespace(key="project:test", root=tmp_path),
    )

    class Repo:
        def ensure_project(self, _project):
            return 7

        def resume_context(self, _project_id):
            return {
                "task": {
                    "task_key": "TASK-test",
                    "updated_at": datetime(2026, 9, 14, 15, 56, 57, tzinfo=timezone.utc),
                    "due_on": date(2026, 9, 15),
                    "payload": {"password": "must-not-print"},
                }
            }

    monkeypatch.setattr(cli, "Repository", Repo)
    sink = StringIO()
    monkeypatch.setattr(cli, "console", Console(file=sink, force_terminal=False, color_system=None))

    cli.status()

    rendered = sink.getvalue()
    assert '"updated_at": "2026-09-14T15:56:57+00:00"' in rendered
    assert '"due_on": "2026-09-15"' in rendered
    assert "must-not-print" not in rendered
    assert '"password": "[REDACTED]"' in rendered
