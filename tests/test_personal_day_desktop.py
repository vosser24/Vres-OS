"""Headless, original-owner Desktop UX safeguards. AUTHOR ONLY until isolated suite proven.

These tests do not create a Tk root, launch native Windows, touch a profile,
run hooks, contact a database, or establish F1/Fable/host authority.
"""
from __future__ import annotations

import pytest

from vres_os import personal_day_desktop as desktop


class _Var:
    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


class _View:
    """Enough non-Tk instance state to probe an action without a display."""


def test_desktop_context_never_silently_selects_result_or_project():
    assert desktop.checked_context("", "", "") == {
        "project_root": None, "project_key": None, "result_file": None}
    assert desktop.checked_context(" /project ", " project:abc ", " /result ") == {
        "project_root": "/project", "project_key": "project:abc", "result_file": "/result"}
    for args in (("", "", "/result"), ("/project", "", ""),
                 ("", "project:abc", "")):
        with pytest.raises(desktop.DesktopRefused):
            desktop.checked_context(*args)


def test_desktop_readonly_contract_refuses_forged_protection_or_hidden_selection(monkeypatch):
    valid = {
        "schema": desktop.owner.PERSONAL_DAY_SCHEMA,
        "status": "READ_ONLY_ONE_ORIGINAL_CHAIRMAN_PERSONAL_DAY",
        "task_selection_or_completion_performed": False,
        "native_claude_or_hooks_executed": False,
        "database_contacted": False,
        "original_166_168_activation_or_rollback_performed": False,
        "original_167_live_catalog_freshness_verified": False,
        "original_174_protected_fable_granted": False,
        "original_176_live_memory_eligibility_or_promotion": False,
        "writes_performed": False,
        "task_selected_explicitly": False,
    }
    monkeypatch.setattr(desktop.owner, "render_personal_day", lambda packet: "bounded")
    assert desktop.checked_day(valid, selected=False) is valid
    with pytest.raises(desktop.DesktopRefused):
        desktop.checked_day(valid, selected=True)
    for field in (
            "writes_performed", "database_contacted", "native_claude_or_hooks_executed",
            "original_166_168_activation_or_rollback_performed",
            "original_174_protected_fable_granted",
            "original_176_live_memory_eligibility_or_promotion"):
        with pytest.raises(desktop.DesktopRefused):
            desktop.checked_day({**valid, field: True}, selected=False)


def _completion_view(known_gaps=False):
    ui = _View()
    ui.decision = {
        "binding": ("stable",),
        "packet": {
            "checkpoint_sha256": "a" * 64,
            "decision_sha256": "b" * 64,
            "extra_known_gap_acknowledgement_required": known_gaps,
        },
    }
    ui._binding = lambda: ("stable",)
    ui._selected = lambda: ("ACTIVE_TASK", "TASK-SYNTHETIC", "c" * 64)
    ui._acceptance = lambda _desk: {}
    ui.values = {
        "desk": _Var("/bounded/Vres-Desk-Synthetic"),
        "project": _Var("/bounded/Project"),
        "key": _Var("project:" + "d" * 24),
        "result": _Var("/bounded/Project/report.md"),
    }
    ui.status = _Var("")
    ui.master = None
    refused = []
    ui._refuse = lambda: refused.append("REFUSED")
    ui.refresh = lambda: True
    return ui, refused


def test_desktop_complete_requires_previously_separate_decision(monkeypatch):
    view, refused = _completion_view()
    view.decision = None
    monkeypatch.setattr(desktop.owner, "finish_reviewed_decision",
                        lambda *a, **k: pytest.fail("Owner must not be called"))
    desktop.PersonalDayDesktop.complete(view)
    assert refused == ["REFUSED"]


def test_desktop_completion_cancellation_does_not_call_owner(monkeypatch):
    view, refused = _completion_view()
    monkeypatch.setattr(desktop.messagebox, "askyesno", lambda *a, **k: False)
    monkeypatch.setattr(desktop.owner, "finish_reviewed_decision",
                        lambda *a, **k: pytest.fail("No completion approval"))
    desktop.PersonalDayDesktop.complete(view)
    assert refused == []
    assert "cancelled" in view.status.get().lower()


def test_desktop_known_gaps_require_second_independent_yes(monkeypatch):
    view, refused = _completion_view(known_gaps=True)
    answers = iter((True, False))
    calls = []
    def confirm(*a, **k):
        calls.append(a[0])
        return next(answers)
    monkeypatch.setattr(desktop.messagebox, "askyesno", confirm)
    monkeypatch.setattr(desktop.owner, "finish_reviewed_decision",
                        lambda *a, **k: pytest.fail("Known gaps not accepted"))
    desktop.PersonalDayDesktop.complete(view)
    assert calls == ["Separate completion approval", "Separate known-gap acknowledgement"]
    assert refused == []
    assert "not acknowledged" in view.status.get()


def test_desktop_replay_never_implicitly_reopens_or_promotes_history(monkeypatch):
    view = _View()
    view._history_only = lambda: ("SAVED_COMPLETED_RESULT", "TASK-SYNTHETIC", "d" * 64)
    view.values = {"desk": _Var("/bounded/Vres-Desk-Synthetic")}
    view.master = None
    view.status = _Var("")
    view._invalidate = lambda: None
    shown = []
    view._display = shown.append
    refused = []
    view._refuse = lambda: refused.append("REFUSED")
    monkeypatch.setattr(desktop.messagebox, "askyesno", lambda *a, **k: True)
    monkeypatch.setattr(desktop.owner, "reopen_saved",
                        lambda *a, **k: pytest.fail("Reopen must be a separate action"))
    approvals = []
    def replay(desk, task, sha, *, approved=False):
        approvals.append((desk, task, sha, approved))
        return {
            "status": "SAVED_WORK_SESSION_EXACT_CONTEXT_REPLAY_MATCH",
            "current_result_bytes_matched_in_this_read": True,
            "future_document_bytes_guaranteed_unchanged": False,
            "writes_performed": False,
            "result_sha256": "a" * 64, "checkpoint_sha256": "b" * 64,
        }
    monkeypatch.setattr(desktop.owner, "replay_saved", replay)
    desktop.PersonalDayDesktop.replay(view)
    assert approvals == [("/bounded/Vres-Desk-Synthetic",
                          "TASK-SYNTHETIC", "d" * 64, True)]
    assert refused == []
    assert "THIS READ ONLY" in shown[0]
    assert "memory" in shown[0]
