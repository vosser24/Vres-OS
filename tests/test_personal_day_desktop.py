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
    ui.focused = (("stable",), {"stage": "RESULT_REVIEW_READY_SEPARATE_DECISION"}, None)
    ui._recheck_original_source = lambda _task: None
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

def test_desktop_opted_in_source_recheck_refuses_changed_original_digest(monkeypatch):
    view = _source_view(catalog=True)
    view.values.update({
        "desk": _Var("/scratch/Vres-Desk-TEST"),
        "project": _Var("/scratch/Project"),
        "key": _Var("project:" + "a" * 24),
        "result": _Var("/scratch/Project/report.md"),
    })
    journey = {"stage": "RESULT_REVIEW_READY_SEPARATE_DECISION",
               "selected_note_sha256": "b" * 64}
    view.focused = (("stable",), journey, "c" * 64)
    view._binding = lambda: ("stable",)
    view._acceptance = lambda _desk: {}
    view._sources = lambda _desk: {"include_saved_catalog": True}
    packet = {
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
        "task_selected_explicitly": True,
        "selected_choice_kind": "ACTIVE_TASK",
        "selected_original_journey": journey,
        "selected_original_source_context": {
            "integrated_source_context_sha256": "c" * 64},
    }
    calls = []
    def review(*args, **kwargs):
        calls.append((args, kwargs))
        return packet
    monkeypatch.setattr(desktop.owner, "review_personal_day", review)
    monkeypatch.setattr(desktop.owner, "render_personal_day", lambda _packet: "read only")
    desktop.PersonalDayDesktop._recheck_original_source(view, "TASK-SYNTHETIC")
    assert len(calls) == 1
    assert calls[0][1]["include_source_context"] is True
    assert calls[0][1]["include_saved_catalog"] is True
    packet["selected_original_source_context"]["integrated_source_context_sha256"] = "d" * 64
    with pytest.raises(desktop.DesktopRefused):
        desktop.PersonalDayDesktop._recheck_original_source(view, "TASK-SYNTHETIC")
    packet["selected_original_source_context"]["integrated_source_context_sha256"] = "c" * 64
    packet["selected_original_journey"] = {"stage": "PROJECT_SELECTED_NO_RESULT"}
    with pytest.raises(desktop.DesktopRefused):
        desktop.PersonalDayDesktop._recheck_original_source(view, "TASK-SYNTHETIC")


def test_desktop_source_drift_blocks_completion_before_any_approval(monkeypatch):
    view, refused = _completion_view()
    view._recheck_original_source = lambda _task: (_ for _ in ()).throw(
        desktop.DesktopRefused("changed source"))
    monkeypatch.setattr(desktop.messagebox, "askyesno",
                        lambda *a, **k: pytest.fail("No consent after source drift"))
    monkeypatch.setattr(desktop.owner, "finish_reviewed_decision",
                        lambda *a, **k: pytest.fail("No original write after source drift"))
    desktop.PersonalDayDesktop.complete(view)
    assert refused == ["REFUSED"]


def test_desktop_source_is_rechecked_after_separate_known_gap_consent(monkeypatch):
    view, refused = _completion_view(known_gaps=True)
    checks = []
    def source_check(_task):
        checks.append("RECHECK")
        if len(checks) == 2:
            raise desktop.DesktopRefused("post-consent source changed")
    view._recheck_original_source = source_check
    approvals = []
    def approve(title, *_args, **_kwargs):
        approvals.append(title)
        return True
    monkeypatch.setattr(desktop.messagebox, "askyesno", approve)
    monkeypatch.setattr(desktop.owner, "finish_reviewed_decision",
                        lambda *a, **k: pytest.fail("No write after late source drift"))
    desktop.PersonalDayDesktop.complete(view)
    assert checks == ["RECHECK", "RECHECK"]
    assert approvals == ["Separate completion approval",
                         "Separate known-gap acknowledgement"]
    assert refused == ["REFUSED"]


def test_guided_active_task_steps_never_skip_original_decision():
    plan = desktop.guided_action_plan("ACTIVE_TASK")
    assert plan["enabled"]["focus"] is True
    assert not plan["enabled"]["decision"]
    assert not plan["enabled"]["complete"]
    for stage in ("TASK_SELECTED_NO_PROJECT", "PROJECT_SELECTED_NO_RESULT"):
        plan = desktop.guided_action_plan("ACTIVE_TASK", stage, focused=True)
        assert plan["enabled"]["focus"]
        assert not plan["enabled"]["decision"]
        assert not plan["enabled"]["complete"]
    ready = desktop.guided_action_plan(
        "ACTIVE_TASK", "RESULT_REVIEW_READY_SEPARATE_DECISION", focused=True)
    assert ready["enabled"]["decision"]
    assert not ready["enabled"]["complete"]
    approved_for_button = desktop.guided_action_plan(
        "ACTIVE_TASK", "RESULT_REVIEW_READY_SEPARATE_DECISION",
        focused=True, decision_ready=True)
    assert approved_for_button["enabled"]["complete"]
    assert not approved_for_button["enabled"]["reopen"]
    assert not approved_for_button["enabled"]["replay"]
    assert "consent" in approved_for_button["next_step"].lower()


def test_guided_history_stays_separate_and_requires_cleared_ui():
    dirty = desktop.guided_action_plan("SAVED_COMPLETED_RESULT")
    assert dirty["enabled"]["clear_history"]
    assert not dirty["enabled"]["focus"]
    assert not dirty["enabled"]["reopen"]
    assert not dirty["enabled"]["replay"]
    clean = desktop.guided_action_plan(
        "SAVED_COMPLETED_RESULT", history_clear=True)
    assert not clean["enabled"]["clear_history"]
    assert clean["enabled"]["focus"]
    assert clean["enabled"]["reopen"]
    assert clean["enabled"]["replay"]
    assert not clean["enabled"]["decision"]
    assert not clean["enabled"]["complete"]
    assert "separately" in clean["next_step"].lower()


def test_guided_no_or_untrusted_selection_cannot_offer_any_action():
    for kind in (None, "UNVERIFIED_KIND", ""):
        plan = desktop.guided_action_plan(
            kind, "RESULT_REVIEW_READY_SEPARATE_DECISION",
            focused=True, decision_ready=True, history_clear=True)
        assert not any(plan["enabled"].values())


def test_ui_plan_rejects_stale_binding_and_unfocused_decision():
    view = _View()
    view._selected = lambda: ("ACTIVE_TASK", "TASK-SYNTHETIC", "a" * 64)
    view._binding = lambda: ("new-context",)
    view.focused = (("old-context",),
                    {"stage": "RESULT_REVIEW_READY_SEPARATE_DECISION"}, None)
    view.decision = {"binding": ("old-context",), "packet": {}}
    view._history_inputs_clear = lambda: True
    plan = desktop.PersonalDayDesktop._ui_plan(view)
    assert plan["enabled"]["focus"]
    assert not plan["enabled"]["decision"]
    assert not plan["enabled"]["complete"]
    view.focused = (("new-context",),
                    {"stage": "RESULT_REVIEW_READY_SEPARATE_DECISION"}, None)
    plan = desktop.PersonalDayDesktop._ui_plan(view)
    assert plan["enabled"]["decision"]
    assert not plan["enabled"]["complete"]


def test_history_clear_requires_explicit_yes_and_never_calls_original_owner(monkeypatch):
    view = _View()
    fields = desktop._HISTORY_CONTEXT_FIELDS
    view.values = {name: _Var("transient") for name in fields}
    view.with_intake, view.with_acceptance = _Var(True), _Var(True)
    view.with_catalog, view.with_synthetic = _Var(True), _Var(True)
    view._selected = lambda: ("SAVED_COMPLETED_RESULT", "TASK-SYNTHETIC", "d" * 64)
    view._history_inputs_clear = lambda: desktop.PersonalDayDesktop._history_inputs_clear(view)
    invalidations = []
    view._invalidate = lambda: invalidations.append(True)
    view._display = lambda content: None
    view.status = _Var("")
    view.master = None
    view._refuse = lambda: pytest.fail("UI-only history clear should not refuse")
    monkeypatch.setattr(desktop.owner, "reopen_saved",
                        lambda *a, **k: pytest.fail("History must not reopen"))
    monkeypatch.setattr(desktop.owner, "replay_saved",
                        lambda *a, **k: pytest.fail("History must not replay"))
    monkeypatch.setattr(desktop.messagebox, "askyesno", lambda *a, **k: False)
    desktop.PersonalDayDesktop.clear_history_context(view)
    assert all(view.values[name].get() == "transient" for name in fields)
    assert not invalidations
    monkeypatch.setattr(desktop.messagebox, "askyesno", lambda *a, **k: True)
    desktop.PersonalDayDesktop.clear_history_context(view)
    assert all(view.values[name].get() == "" for name in fields)
    assert not any(v.get() for v in (
        view.with_intake, view.with_acceptance, view.with_catalog,
        view.with_synthetic))
    assert invalidations == [True]
    assert "separate approvals" in view.status.get()


def test_editing_selected_desk_drops_old_inventory_without_auto_selection():
    view = _View()
    class Listing:
        def __init__(self):
            self.items = ["choice-0"]
        def get_children(self):
            return tuple(self.items)
        def delete(self, *selected):
            self.items = [x for x in self.items if x not in selected]
    view.listing = Listing()
    view.choices = {"choice-0": ("ACTIVE_TASK", "TASK-OLD", "a" * 64)}
    view.focused = (("old",), {"stage": "RESULT_REVIEW_READY_SEPARATE_DECISION"}, None)
    view.decision = {"binding": ("old",), "packet": {}}
    view.status = _Var("")
    displayed = []
    view._display = displayed.append
    view._sync_guidance = lambda: None
    desktop.PersonalDayDesktop._edited(view, "desk")
    assert not view.choices and not view.listing.items
    assert view.focused is None and view.decision is None
    assert displayed == [""]
    assert "Load this desk" in view.status.get()


def _existing_add_view():
    """Headless existing-desk form; no real filesystem or Tk window."""
    view = _View()
    view.values = {
        name: _Var("") for name in (
            "desk", "new_task", "note", *desktop._HISTORY_CONTEXT_FIELDS)}
    view.values["desk"].set("/test/Vres-Desk-Existing")
    view.values["new_task"].set("TASK-NEXT")
    view.values["note"].set("/test/note.md")
    view.loaded_desk = "/test/Vres-Desk-Existing"
    view.with_intake = _Var(True)
    view.with_acceptance = _Var(True)
    view.with_catalog = _Var(True)
    view.with_synthetic = _Var(True)
    view.status = _Var("")
    view.master = None
    view.focused = None
    view.decision = None
    view.choices = {}
    view._invalidate = lambda: None
    view._display = lambda value: None
    refusals = []
    view._refuse = lambda: refusals.append(True)
    return view, refusals


def _mock_existing_day(monkeypatch, *, drift=False):
    snapshots = []
    def day(_desk):
        packet = {"proposal_sha256": "p" * 64, "active_task_count": 1,
                  "original_offered_choices": []}
        if drift and snapshots:
            packet["proposal_sha256"] = "q" * 64
        snapshots.append(packet)
        return packet
    monkeypatch.setattr(desktop.owner, "review_personal_day", day)
    monkeypatch.setattr(desktop, "checked_day", lambda value, *, selected: value)
    return snapshots


def _mock_existing_preview(monkeypatch, *, drift=False):
    calls = []
    def preview(*args):
        calls.append(args)
        return {"sha256": ("b" if drift and len(calls) > 1 else "a") * 64}
    monkeypatch.setattr(desktop, "preview_existing_desk_task", preview)
    return calls


def test_existing_task_preview_uses_only_original_bounded_scratch_owners(monkeypatch):
    from pathlib import Path
    root = Path("/test/Vres-Desk-Existing")
    visited = []
    monkeypatch.setattr(desktop.portable, "_desk",
                        lambda value, *, must_exist: root)
    monkeypatch.setattr(desktop.portable, "_owned_task",
                        lambda value, task: root / ("Vres-Workbench-" + task))
    monkeypatch.setattr(desktop.portable, "_existing_tasks", lambda value: ["TASK-OLD"])
    monkeypatch.setattr(desktop.portable.workbench, "_stat", lambda value: None)
    monkeypatch.setattr(desktop.portable.project_draft, "_under",
                        lambda path, ancestor: False)
    monkeypatch.setattr(desktop.portable.project_draft, "_manual_markdown",
                        lambda file: (visited.append(file) or "# new"))
    monkeypatch.setattr(desktop.portable.workbench, "preview_note",
                        lambda task, body: {
                            "status": "DRAFT_PREVIEW_ONLY",
                            "task_key_claimed": task, "sha256": "a" * 64,
                            "writes_performed": False,
                            "installed_or_project_write_authorized": False})
    assert desktop.preview_existing_desk_task(str(root), "TASK-NEXT", "/test/note.md")[
        "sha256"] == "a" * 64
    assert visited == ["/test/note.md"]
    monkeypatch.setattr(desktop.portable, "_existing_tasks", lambda value: ["TASK-NEXT"])
    with pytest.raises(desktop.DesktopRefused):
        desktop.preview_existing_desk_task(str(root), "TASK-NEXT", "/test/note.md")
    monkeypatch.setattr(desktop.portable, "_existing_tasks",
                        lambda value: ["TASK-" + str(i) for i in range(6)])
    with pytest.raises(desktop.DesktopRefused):
        desktop.preview_existing_desk_task(str(root), "TASK-NEXT", "/test/note.md")
    monkeypatch.setattr(desktop.portable, "_existing_tasks", lambda value: [])
    monkeypatch.setattr(desktop.portable.project_draft, "_under",
                        lambda path, ancestor: True)
    with pytest.raises(desktop.DesktopRefused):
        desktop.preview_existing_desk_task(str(root), "TASK-NEXT", "/test/note.md")
    assert visited == ["/test/note.md"]


def test_existing_add_refuses_unloaded_desk_before_original_reads(monkeypatch):
    view, refusals = _existing_add_view()
    view.loaded_desk = None
    monkeypatch.setattr(desktop.owner, "review_personal_day",
                        lambda *_: pytest.fail("Unloaded desk must not be read"))
    monkeypatch.setattr(desktop.portable, "add_task",
                        lambda *_a, **_kw: pytest.fail("Unloaded desk must not be written"))
    desktop.PersonalDayDesktop.add_existing(view)
    assert refusals == [True]


def test_existing_add_cancel_has_no_original_task_write(monkeypatch):
    view, refusals = _existing_add_view()
    snapshots = _mock_existing_day(monkeypatch)
    calls = _mock_existing_preview(monkeypatch)
    monkeypatch.setattr(desktop.messagebox, "askyesno", lambda *a, **k: False)
    monkeypatch.setattr(desktop.portable, "add_task",
                        lambda *_a, **_kw: pytest.fail("No approval: no write"))
    desktop.PersonalDayDesktop.add_existing(view)
    assert not refusals
    assert len(snapshots) == 1 and len(calls) == 1
    assert view.values["new_task"].get() == "TASK-NEXT"
    assert "cancelled" in view.status.get()


def test_existing_add_refuses_changed_owner_or_note_after_consent(monkeypatch):
    for source in ("owner", "note"):
        view, refusals = _existing_add_view()
        snapshots = _mock_existing_day(monkeypatch, drift=(source == "owner"))
        previews = _mock_existing_preview(monkeypatch, drift=(source == "note"))
        monkeypatch.setattr(desktop.messagebox, "askyesno", lambda *a, **k: True)
        monkeypatch.setattr(desktop.portable, "add_task",
                            lambda *_a, **_kw: pytest.fail("Drift must not write"))
        desktop.PersonalDayDesktop.add_existing(view)
        assert refusals == [True]
        assert len(snapshots) == 2
        assert len(previews) == (1 if source == "owner" else 2)


def test_existing_add_success_delegates_one_original_write_then_unselects(monkeypatch):
    view, refusals = _existing_add_view()
    snapshots = _mock_existing_day(monkeypatch)
    previews = _mock_existing_preview(monkeypatch)
    monkeypatch.setattr(desktop.messagebox, "askyesno", lambda *a, **k: True)
    writes = []
    def add(desk, task, note, *, approved=False):
        writes.append((desk, task, note, approved))
        return {"status": "USER_AUTHORED_SCRATCH_DRAFT_NOT_VALIDATED",
                "task_key_claimed": task, "sha256": "a" * 64,
                "installed_or_project_write_authorized": False}
    monkeypatch.setattr(desktop.portable, "add_task", add)
    def refresh():
        view.choices = {"new": ("ACTIVE_TASK", "TASK-NEXT", "a" * 64)}
        return True
    view.refresh = refresh
    desktop.PersonalDayDesktop.add_existing(view)
    assert not refusals
    assert len(snapshots) == 2 and len(previews) == 2
    assert writes == [("/test/Vres-Desk-Existing", "TASK-NEXT", "/test/note.md", True)]
    assert view.values["new_task"].get() == "" and view.values["note"].get() == ""
    assert all(view.values[name].get() == "" for name in desktop._HISTORY_CONTEXT_FIELDS)
    assert not any(flag.get() for flag in (view.with_intake, view.with_acceptance,
                                          view.with_catalog, view.with_synthetic))
    assert "no project bound" in view.status.get().lower()


def test_selection_change_drops_old_decision_and_visible_preview():
    view = _View()
    view.focused = (("old",), {"stage": "RESULT_REVIEW_READY_SEPARATE_DECISION"}, None)
    view.decision = {"binding": ("old",), "packet": {}}
    view._sync_guidance = lambda: None
    displayed = []
    view._display = displayed.append
    view.status = _Var("")
    desktop.PersonalDayDesktop._selection_changed(view)
    assert view.focused is None and view.decision is None
    assert displayed == [""]
    assert "Focus" in view.status.get()
