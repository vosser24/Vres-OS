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



def _source_view(*, catalog=False, synthetic=False, intake=True):
    view = _View()
    names = ("catalog_root", "catalog_namespace", "catalog_source",
             "catalog_sha", "catalog_revision", "synthetic_file", "synthetic_sha")
    view.values = {name: _Var("") for name in names}
    view.with_catalog = _Var(catalog)
    view.with_synthetic = _Var(synthetic)
    view.with_intake = _Var(intake)
    return view


def test_desktop_unselected_sources_and_missing_original_intake_refuse():
    view = _source_view(intake=False)
    view.values["catalog_root"].set("/scratch/saved")
    with pytest.raises(desktop.DesktopRefused):
        desktop.PersonalDayDesktop._sources(view, "/scratch/Vres-Desk-TEST")
    view.values["catalog_root"].set("")
    view.with_catalog.set(True)
    with pytest.raises(desktop.DesktopRefused):
        desktop.PersonalDayDesktop._sources(view, "/scratch/Vres-Desk-TEST")
    view.with_catalog.set(False)
    view.with_synthetic.set(True)
    with pytest.raises(desktop.DesktopRefused):
        desktop.PersonalDayDesktop._sources(view, "/scratch/Vres-Desk-TEST")


def test_desktop_selected_catalog_delegates_original_167_no_credential_broker(monkeypatch):
    from pathlib import Path
    from vres_os import personal_data_source_store
    view = _source_view(catalog=True)
    for name, value in {
        "catalog_root": "/scratch/current-user-data",
        "catalog_namespace": "test-user-namespace",
        "catalog_source": "source:test",
        "catalog_sha": "a" * 64,
        "catalog_revision": "3",
    }.items():
        view.values[name].set(value)
    calls = []
    class FakeOriginalStore:
        def __init__(self, root, namespace, callback):
            calls.append((root, namespace, callback))
    monkeypatch.setattr(personal_data_source_store,
                        "CurrentUserDataSourceStore", FakeOriginalStore)
    opts = desktop.PersonalDayDesktop._sources(view, "/scratch/Vres-Desk-TEST")
    assert opts["include_saved_catalog"] is True
    assert opts["expected_saved_catalog_sha256"] == "a" * 64
    assert opts["expected_saved_catalog_revision"] == 3
    assert len(calls) == 1 and calls[0][0] == Path("/scratch/current-user-data")
    assert calls[0][2] is desktop.owner._reject_catalog_credential_lookup


def test_desktop_catalog_rejects_ambiguous_revision_and_digest():
    view = _source_view(catalog=True)
    for name, value in {
        "catalog_root": "/scratch/data", "catalog_namespace": "synthetic",
        "catalog_source": "source:synthetic", "catalog_sha": "b" * 64,
        "catalog_revision": "01",
    }.items():
        view.values[name].set(value)
    with pytest.raises(desktop.DesktopRefused):
        desktop.PersonalDayDesktop._sources(view, "/scratch/Vres-Desk-TEST")
    view.values["catalog_revision"].set("0")
    view.values["catalog_sha"].set("B" * 64)
    with pytest.raises(desktop.DesktopRefused):
        desktop.PersonalDayDesktop._sources(view, "/scratch/Vres-Desk-TEST")


def test_desktop_synthetic_166_fixture_is_scratch_only_and_sha_bound(monkeypatch):
    import hashlib
    from pathlib import Path
    view = _source_view(synthetic=True)
    root = Path("/scratch/Vres-Desk-TEST")
    document = b'{"synthetic":true}'
    sha = hashlib.sha256(document).hexdigest()
    view.values["synthetic_file"].set(str(root / "synthetic-global-inventory.json"))
    view.values["synthetic_sha"].set(sha)
    monkeypatch.setattr(desktop.portable, "_desk", lambda *a, **k: root)
    reads = []
    def read(file, *, maximum):
        reads.append((file, maximum))
        return document
    monkeypatch.setattr(desktop.owner, "_read_selected_chairman_source", read)
    opts = desktop.PersonalDayDesktop._sources(view, str(root))
    assert opts == {
        "include_adoption_preparation": True,
        "synthetic_global_inventory_document": document,
        "expected_synthetic_global_inventory_sha256": sha,
    }
    assert reads == [(str(root / "synthetic-global-inventory.json"), 65536)]
    view.values["synthetic_sha"].set("a" * 64)
    with pytest.raises(desktop.DesktopRefused):
        desktop.PersonalDayDesktop._sources(view, str(root))
    view.values["synthetic_sha"].set(sha)
    view.values["synthetic_file"].set("/outside/synthetic-global-inventory.json")
    with pytest.raises(desktop.DesktopRefused):
        desktop.PersonalDayDesktop._sources(view, str(root))


def test_desktop_history_refuses_any_source_context_even_when_opted_in():
    view = _source_view(catalog=True)
    for name in ("project", "key", "result", "acceptance_path", "acceptance_sha"):
        view.values[name] = _Var("")
    view.with_acceptance = _Var(False)
    view._selected = lambda: ("SAVED_COMPLETED_RESULT", "TASK-SYNTHETIC", "e" * 64)
    with pytest.raises(desktop.DesktopRefused):
        desktop.PersonalDayDesktop._history_only(view)


def test_desktop_source_edit_invalidates_exact_prior_preview_binding():
    view = _source_view(catalog=True)
    for name in ("desk", "project", "key", "result", "acceptance_path", "acceptance_sha"):
        view.values[name] = _Var("")
    view.with_acceptance = _Var(False)
    view._selected = lambda: ("ACTIVE_TASK", "TASK-SYNTHETIC", "c" * 64)
    first = desktop.PersonalDayDesktop._binding(view)
    view.values["catalog_revision"].set("4")
    assert desktop.PersonalDayDesktop._binding(view) != first
