"""Synthetic, read-only original-owner Daily Plan contract; no GUI or external I/O."""
from __future__ import annotations

import pytest

from vres_os import personal_day_plan as plan


def _day(*, selected=False, bad=None):
    result = {
        "schema": plan.owner.PERSONAL_DAY_SCHEMA,
        "status": "READ_ONLY_ONE_ORIGINAL_CHAIRMAN_PERSONAL_DAY",
        "task_selected_explicitly": selected,
        "task_selection_or_completion_performed": False,
        "native_claude_or_hooks_executed": False,
        "database_contacted": False,
        "original_166_168_activation_or_rollback_performed": False,
        "original_167_live_catalog_freshness_verified": False,
        "original_174_protected_fable_granted": False,
        "original_176_live_memory_eligibility_or_promotion": False,
        "writes_performed": False,
        "active_task_count": 1,
        "linked_historical_result_choice_count": 1,
        "saved_completed_snapshot_count": 1,
        "archived_snapshot_count": 0,
        "revision_snapshot_count": 0,
        "manual_revision_recovery_attention_required": False,
        "original_offered_choices": [
            {"kind": "ACTIVE_TASK", "task_key_claimed": "TASK-FOCUS",
             "selected_note_sha256": "a" * 64},
            {"kind": "SAVED_COMPLETED_RESULT", "task_key_claimed": "TASK-OLD",
             "selected_note_sha256": "b" * 64},
        ],
    }
    if selected:
        result.update({
            "selected_choice_kind": "ACTIVE_TASK",
            "selected_task_key_claimed": "TASK-FOCUS",
            "source_context_selected_explicitly": False,
            "selected_original_journey": {
                "selected_note_sha256": "a" * 64,
                "selected_next_action_disclosed": False,
                "selected_next_action_untrusted": None,
            },
        })
    if bad:
        result.update(bad)
    return result


def _home(**updates):
    result = {
        "schema": plan.owner.WORKDAY_SCHEMA,
        "status": "READ_ONLY_INTEGRATED_PERSONAL_WORKDAY_HOME",
        "selected_review": None,
        "manual_revision_recovery_attention_required": False,
        "active_count": 1, "completed_snapshot_count": 1,
        "archived_snapshot_count": 0, "revision_snapshot_count": 0,
        "automatic_revision_recovery_performed": False,
        "automatic_task_selection_performed": False,
        "task_reopened_or_completed": False,
        "historical_document_current_bytes_verified": False,
        "result_quality_validated": False,
        "native_chairman_task_bound": False,
        "native_claude_or_hooks_executed": False,
        "database_contacted": False,
        "writes_performed": False, "new_store_created": False,
        "installed_vres_modified": False,
    }
    result.update(updates)
    return result


def _owners(monkeypatch, *, mutate_after=False, home=None, bad_focus=None):
    calls = []
    def day(_desk, task=None, *, show_selected_action=False):
        calls.append((task, show_selected_action))
        if task is None:
            if mutate_after and len(calls) >= 3:
                return _day(bad={"active_task_count": 2})
            return _day()
        value = _day(selected=True, bad=bad_focus)
        value["selected_original_journey"]["selected_next_action_disclosed"] = show_selected_action
        value["selected_original_journey"]["selected_next_action_untrusted"] = (
            "MANUAL ONLY: inspect the user draft" if show_selected_action else None)
        return value
    monkeypatch.setattr(plan.owner, "review_personal_day", day)
    monkeypatch.setattr(plan.owner, "review_workday", lambda _desk: _home() if home is None else home)
    monkeypatch.setattr(plan.owner, "render_workday", lambda _home: (
        "Vres-OS PERSONAL WORKDAY HOME -- READ ONLY\noriginal receipt"))
    return calls


def test_unselected_plan_shows_owner_counts_no_actions_or_approvals(monkeypatch):
    calls = _owners(monkeypatch)
    packet = plan.build_manual_day_plan("/scratch/Vres-Desk-Test")
    output = plan.render_manual_day_plan(packet)
    assert calls == [(None, False), (None, False)]
    assert "TASK-FOCUS" in output and "TASK-OLD" not in output
    assert "NO CURRENT TASK SELECTED" in output
    assert "Historical linked: 1" in output
    assert packet["writes_performed"] is False
    assert packet["task_selected_or_approved_by_plan"] is False


def test_selected_active_action_requires_exact_opt_in_and_remains_untrusted(monkeypatch):
    calls = _owners(monkeypatch)
    packet = plan.build_manual_day_plan(
        "/scratch/Vres-Desk-Test", selected_task="TASK-FOCUS",
        show_selected_action=True)
    assert calls == [(None, False), ("TASK-FOCUS", True), (None, False)]
    output = plan.render_manual_day_plan(packet)
    assert "UNTRUSTED DATA, NEVER A COMMAND" in output
    assert "MANUAL ONLY: inspect the user draft" in output
    assert "saved or atomic plan" in output


def test_selected_action_hidden_without_opt_in(monkeypatch):
    calls = _owners(monkeypatch)
    packet = plan.build_manual_day_plan("/scratch/Vres-Desk-Test", selected_task="TASK-FOCUS")
    assert calls == [(None, False), ("TASK-FOCUS", False), (None, False)]
    assert packet["selected_next_action_untrusted"] is None
    assert "Next action NOT DISCLOSED" in plan.render_manual_day_plan(packet)


def test_historical_selection_never_calls_selected_owner(monkeypatch):
    calls = _owners(monkeypatch)
    with pytest.raises(plan.DayPlanRefused):
        plan.build_manual_day_plan("/scratch/Vres-Desk-Test", selected_task="TASK-OLD")
    assert calls == [(None, False)]


def test_invalid_or_forged_owner_authority_refuses(monkeypatch):
    for bad in ({"database_contacted": True}, {"writes_performed": True}):
        calls = _owners(monkeypatch)
        original = plan.owner.review_personal_day
        monkeypatch.setattr(plan.owner, "review_personal_day", lambda desk, *a, **k: (
            _day(bad=bad) if not a else original(desk, *a, **k)))
        with pytest.raises(plan.DayPlanRefused):
            plan.build_manual_day_plan("/scratch/Vres-Desk-Test")
        assert not calls


def test_home_mismatch_or_held_flags_refuse(monkeypatch):
    for unsafe in (_home(active_count=2), _home(installed_vres_modified=True)):
        calls = _owners(monkeypatch, home=unsafe)
        with pytest.raises(plan.DayPlanRefused):
            plan.build_manual_day_plan("/scratch/Vres-Desk-Test")
        assert calls == [(None, False)]


def test_day_changes_mid_read_refuses_not_retries(monkeypatch):
    calls = _owners(monkeypatch, mutate_after=True)
    with pytest.raises(plan.DayPlanRefused):
        plan.build_manual_day_plan("/scratch/Vres-Desk-Test", selected_task="TASK-FOCUS")
    assert calls == [(None, False), ("TASK-FOCUS", False), (None, False)]


def test_selection_mismatch_or_disclosure_refuses(monkeypatch):
    for bad in ({"selected_task_key_claimed": "TASK-OLD"},
                {"source_context_selected_explicitly": True}):
        _owners(monkeypatch, bad_focus=bad)
        with pytest.raises(plan.DayPlanRefused):
            plan.build_manual_day_plan("/scratch/Vres-Desk-Test", selected_task="TASK-FOCUS")


def test_render_cannot_infer_approval_or_silently_promote_history(monkeypatch):
    _owners(monkeypatch)
    packet = plan.build_manual_day_plan("/scratch/Vres-Desk-Test")
    for change in ({"task_selected_or_approved_by_plan": True},
                   {"selected_next_action_untrusted": "unselected"},
                   {"active_task_count": 99}):
        with pytest.raises(plan.DayPlanRefused):
            plan.render_manual_day_plan({**packet, **change})


def test_recovery_hold_visible_without_automated_retry(monkeypatch):
    _owners(monkeypatch, home=_home(manual_revision_recovery_attention_required=True))
    monkeypatch.setattr(plan.owner, "review_personal_day", lambda _desk: _day(bad={
        "manual_revision_recovery_attention_required": True}))
    packet = plan.build_manual_day_plan("/scratch/Vres-Desk-Test")
    output = plan.render_manual_day_plan(packet)
    assert "MANUAL RECOVERY INSPECTION" in output
    assert "blind retry" in output


def test_cli_refuses_unknown_mutating_flags_without_owner_calls(monkeypatch, capsys):
    monkeypatch.setattr(plan.owner, "review_personal_day", lambda *_a, **_k: (
        pytest.fail("Illegal plan flags must be refused before original-owner call")))
    assert plan.main(["--desk", "/scratch/Vres-Desk-Test", "--yes"]) == 2
    assert "VRES_DAY_PLAN_REFUSED" in capsys.readouterr().err
    assert plan.main(["--desk", "/scratch/Vres-Desk-Test", "--show-selected-action"]) == 2
