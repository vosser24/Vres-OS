from types import SimpleNamespace

from vres_os import hooks
from vres_os.config import VresConfig
from vres_os.session_prompts import is_system_prompt_event
from vres_os.validation import ValidationService, state_digest


def test_task_notification_is_not_user_intent():
    assert is_system_prompt_event("<task-notification>validator complete</task-notification>")
    assert is_system_prompt_event("  <task-notification id='x'>done</task-notification>")
    assert not is_system_prompt_event("Please explain <task-notification> as text")


def test_user_prompt_is_staged_before_task_attribution(monkeypatch, capsys):
    monkeypatch.setattr(hooks, "_input", lambda: {"session_id": "S-NEW", "prompt": "Start LV-09"})
    monkeypatch.setattr(hooks, "ConfigStore", lambda: SimpleNamespace(load=lambda: VresConfig(configured=True)))
    monkeypatch.setattr(hooks, "_project_id", lambda _repo, _payload: 7)

    staged = []
    focused = []
    observed = []
    armed = []

    class Repo:
        def open_session(self, project_id, sid):
            assert (project_id, sid) == (7, "S-NEW")

        def active_task(self, project_id, sid):
            return SimpleNamespace(task_key="TASK-OLD")

        def needs_context_rehydration(self, _task_key):
            return False

        def update_state(self, *_args, **_kwargs):
            raise AssertionError("UserPromptSubmit must not mutate the previously focused task")

        def record_event(self, *_args, **_kwargs):
            raise AssertionError("UserPromptSubmit must not attribute the prompt before task resolution")

    monkeypatch.setattr(hooks, "Repository", Repo)
    monkeypatch.setattr(
        hooks,
        "_observe_session",
        lambda project_id, sid, reconcile=False: observed.append((project_id, sid, reconcile)),
    )
    monkeypatch.setattr(
        hooks,
        "bind_session_to_project_focus",
        lambda project_id, sid: focused.append((project_id, sid)),
    )
    monkeypatch.setattr(
        hooks,
        "stage_user_instruction",
        lambda project_id, sid, prompt: staged.append((project_id, sid, prompt)),
    )
    monkeypatch.setattr(
        hooks,
        "arm_reply_checkpoint_guard",
        lambda project_id, sid: armed.append((project_id, sid)) or True,
    )

    hooks.user_prompt()

    assert observed == [(7, "S-NEW", True)]
    assert focused == [(7, "S-NEW")]
    assert staged == [(7, "S-NEW", "Start LV-09")]
    assert armed == [(7, "S-NEW")]
    assert "VRES_CURRENT_SESSION_ID=S-NEW" in capsys.readouterr().out


def test_stop_commits_prompt_to_final_bound_task(monkeypatch):
    monkeypatch.setattr(hooks, "_input", lambda: {"session_id": "S-1"})
    monkeypatch.setattr(hooks, "ConfigStore", lambda: SimpleNamespace(load=lambda: VresConfig(configured=True)))
    monkeypatch.setattr(hooks, "_project_id", lambda _repo, _payload: 9)
    monkeypatch.setattr(hooks, "last_assistant_snapshot", lambda _payload: None)
    monkeypatch.setattr(hooks, "_observe_session", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        hooks,
        "evaluate_reply_checkpoint_guard",
        lambda *_args, **_kwargs: {"action": "allow", "reason": "guard_not_armed"},
    )

    committed = []
    events = []

    class Repo:
        def active_task(self, project_id, sid):
            assert (project_id, sid) == (9, "S-1")
            return SimpleNamespace(task_key="TASK-NEW")

        def record_event(self, task_key, event_type, actor, payload, sid):
            events.append((task_key, event_type, actor, payload, sid))

    monkeypatch.setattr(hooks, "Repository", Repo)
    monkeypatch.setattr(
        hooks,
        "commit_staged_user_instruction",
        lambda project_id, sid, task_key: committed.append((project_id, sid, task_key)),
    )

    hooks.stop()

    assert committed == [(9, "S-1", "TASK-NEW")]
    assert events == [("TASK-NEW", "MODEL_STOP", "vres-lifecycle", {}, "S-1")]


def test_validation_digest_ignores_latest_instruction_but_not_material_state():
    base = {
        "objective": "ship",
        "state_summary": "ready",
        "next_action": "validate",
        "latest_user_instruction": "first wording",
    }
    assert state_digest(base) == state_digest(base | {"latest_user_instruction": "later wording"})
    assert state_digest(base) != state_digest(base | {"next_action": "different"})


def test_validation_prepare_states_exact_machine_vocabulary():
    source = __import__("inspect").getsource(ValidationService.prepare)
    assert "lowercase outcome exactly 'passed' or 'failed'" in source
    assert "'passed', 'failed', or 'not_run'" in source
