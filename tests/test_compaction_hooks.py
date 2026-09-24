from __future__ import annotations

from types import SimpleNamespace

from vres_os import hooks


class _FakeRepository:
    def __init__(self):
        self.checkpoints = []
        self.events = []

    def active_task(self, project_id, provider_session_id):
        assert project_id == 17
        assert provider_session_id == "SESSION-COMPACT"
        return SimpleNamespace(
            task_key="TASK-COMPACT",
            state_summary="durable summary",
            current_step="implement",
            current_phase="execution",
            next_action="continue exact work",
        )

    def checkpoint(
        self,
        task_key,
        summary,
        current_position,
        next_action,
        context,
        reason,
        actor,
    ):
        self.checkpoints.append(
            {
                "task_key": task_key,
                "summary": summary,
                "current_position": current_position,
                "next_action": next_action,
                "context": context,
                "reason": reason,
                "actor": actor,
            }
        )
        return "CP-COMPACT"

    def record_event(self, task_key, event_type, actor, payload, session_id):
        self.events.append(
            {
                "task_key": task_key,
                "event_type": event_type,
                "actor": actor,
                "payload": payload,
                "session_id": session_id,
            }
        )


def _wire(monkeypatch):
    repo = _FakeRepository()
    monkeypatch.setattr(hooks, "Repository", lambda: repo)
    monkeypatch.setattr(hooks.ConfigStore, "load", lambda _self: SimpleNamespace(configured=True))
    monkeypatch.setattr(hooks, "_project_id", lambda _repo, _payload=None: 17)
    monkeypatch.setattr(hooks, "_observe_session", lambda *_args, **_kwargs: None)
    return repo


def test_precompact_checkpoint_records_auto_trigger(monkeypatch):
    repo = _wire(monkeypatch)
    monkeypatch.setattr(hooks, "last_assistant_snapshot", lambda _payload: "latest answer")

    hooks.compact(
        "pre_compact",
        {
            "hook_event_name": "PreCompact",
            "session_id": "SESSION-COMPACT",
            "trigger": "auto",
            "transcript_path": "ignored",
        },
    )

    assert len(repo.checkpoints) == 1
    checkpoint = repo.checkpoints[0]
    assert checkpoint["task_key"] == "TASK-COMPACT"
    assert checkpoint["reason"] == "pre_compact"
    assert checkpoint["actor"] == "vres-lifecycle"
    assert checkpoint["context"] == {
        "automatic": True,
        "session_id": "SESSION-COMPACT",
        "snapshot_captured": True,
        "trigger": "auto",
    }
    assert repo.events[0]["event_type"] == "ASSISTANT_TURN_SNAPSHOT"
    assert repo.events[0]["payload"] == {
        "text": "latest answer",
        "authoritative": False,
    }


def test_precompact_checkpoint_records_manual_trigger(monkeypatch):
    repo = _wire(monkeypatch)
    monkeypatch.setattr(hooks, "last_assistant_snapshot", lambda _payload: None)

    hooks.compact(
        "pre_compact",
        {
            "hook_event_name": "PreCompact",
            "session_id": "SESSION-COMPACT",
            "trigger": "manual",
            "custom_instructions": "focus on pending work",
        },
    )

    assert repo.checkpoints[0]["context"]["trigger"] == "manual"
    assert repo.checkpoints[0]["context"]["snapshot_captured"] is False
    assert repo.events == []


def test_postcompact_event_records_trigger_and_native_summary(monkeypatch):
    repo = _wire(monkeypatch)
    monkeypatch.setattr(
        hooks,
        "_input",
        lambda: {
            "hook_event_name": "PostCompact",
            "session_id": "SESSION-COMPACT",
            "trigger": "auto",
            "compact_summary": "native compact summary",
        },
    )

    hooks.post_compact()

    assert repo.events == [
        {
            "task_key": "TASK-COMPACT",
            "event_type": "POST_COMPACT",
            "actor": "vres-lifecycle",
            "payload": {
                "trigger": "auto",
                "compact_summary": "native compact summary",
            },
            "session_id": "SESSION-COMPACT",
        }
    ]
