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
        view.inventory_packet = {"original_offered_choices": [{
            "kind": "ACTIVE_TASK", "task_key_claimed": "TASK-NEXT",
            "selected_note_sha256": "a" * 64}]}
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


def _triage_owner_packet():
    return {
        "schema": desktop.owner.PERSONAL_DAY_SCHEMA,
        "status": "READ_ONLY_ONE_ORIGINAL_CHAIRMAN_PERSONAL_DAY",
        "task_selection_or_completion_performed": False,
        "native_claude_or_hooks_executed": False,
        "database_contacted": False,
        "original_166_168_activation_or_rollback_performed": False,
        "original_167_live_catalog_freshness_verified": False,
        "original_174_protected_fable_granted": False,
        "original_176_live_memory_eligibility_or_promotion": False,
        "writes_performed": False, "task_selected_explicitly": False,
        "active_task_count": 1, "linked_historical_result_choice_count": 2,
        "saved_completed_snapshot_count": 3, "archived_snapshot_count": 1,
        "revision_snapshot_count": 2,
        "manual_revision_recovery_attention_required": True,
        "original_offered_choices": [
            {"kind": "ACTIVE_TASK", "task_key_claimed": "TASK-TODAY",
             "selected_note_sha256": "a" * 64},
            {"kind": "SAVED_COMPLETED_RESULT", "task_key_claimed": "TASK-OLD",
             "selected_note_sha256": "b" * 64},
            {"kind": "SAVED_COMPLETED_RESULT", "task_key_claimed": "TASK-TODAY",
             "selected_note_sha256": "c" * 64},
        ],
    }


def test_triage_original_active_and_saved_choices_are_not_mixed(monkeypatch):
    monkeypatch.setattr(desktop.owner, "render_personal_day", lambda p: "read only")
    packet = _triage_owner_packet()
    assert len(desktop.triage_personal_day(packet)["rows"]) == 3
    active = desktop.triage_personal_day(packet, query="today", mode="ACTIVE")
    saved = desktop.triage_personal_day(packet, query="today", mode="HISTORY")
    assert active["rows"] == [("ACTIVE_TASK", "TASK-TODAY", "a" * 64)]
    assert saved["rows"] == [("SAVED_COMPLETED_RESULT", "TASK-TODAY", "c" * 64)]
    assert saved["manual_recovery_attention_required"] is True
    assert "MANUAL RECOVERY ATTENTION" in saved["summary"]
    assert "NEVER current" in saved["summary"]


def test_triage_refuses_invalid_filter_and_mismatched_original_counts(monkeypatch):
    monkeypatch.setattr(desktop.owner, "render_personal_day", lambda p: "read only")
    packet = _triage_owner_packet()
    for query, mode in (("a" * 65, "ALL"), ("", "INVALID")):
        with pytest.raises(desktop.DesktopRefused):
            desktop.triage_personal_day(packet, query=query, mode=mode)
    for field, value in (("active_task_count", 2),
                         ("linked_historical_result_choice_count", 0),
                         ("manual_revision_recovery_attention_required", None)):
        with pytest.raises(desktop.DesktopRefused):
            desktop.triage_personal_day({**packet, field: value})
    duplicated = {**packet, "original_offered_choices":
                  packet["original_offered_choices"] +
                  [packet["original_offered_choices"][0]]}
    with pytest.raises(desktop.DesktopRefused):
        desktop.triage_personal_day(duplicated)


def test_triage_edit_invalidates_decision_with_zero_owner_actions(monkeypatch):
    monkeypatch.setattr(desktop.owner, "render_personal_day", lambda p: "read only")
    monkeypatch.setattr(desktop.owner, "review_personal_day",
                        lambda *a, **k: pytest.fail("No owner reads on filter edit"))
    class Listing:
        def __init__(self): self.items = {"old": None}
        def get_children(self): return tuple(self.items)
        def delete(self, *names):
            for name in names: self.items.pop(name, None)
        def insert(self, *a, **kw): self.items[kw["iid"]] = kw["values"]
    view = _View()
    view.inventory_packet = _triage_owner_packet()
    view.triage_query, view.triage_mode = _Var("today"), _Var("HISTORY")
    view.triage_summary, view.status = _Var(""), _Var("")
    view.listing, view.choices = Listing(), {"old": ("ACTIVE_TASK", "TASK-TODAY", "a"*64)}
    view.focused, view.decision = (("old",), {}, None), {"binding": ("old",)}
    view._sync_guidance = lambda: None
    shown = []
    view._display = shown.append
    view._invalidate = lambda: desktop.PersonalDayDesktop._invalidate(view)
    view._render_triage = lambda: desktop.PersonalDayDesktop._render_triage(view)
    desktop.PersonalDayDesktop._triage_changed(view)
    assert view.focused is None and view.decision is None
    assert view.choices == {
        "choice-0": ("SAVED_COMPLETED_RESULT", "TASK-TODAY", "c" * 64)}
    assert view.listing.items["choice-0"][0] == "SAVED · HISTORICAL"
    assert shown == ["", "read only"]


def test_add_task_with_history_filter_verifies_unfiltered_owner_receipt(monkeypatch):
    view, refusals = _existing_add_view()
    _mock_existing_day(monkeypatch)
    _mock_existing_preview(monkeypatch)
    monkeypatch.setattr(desktop.messagebox, "askyesno", lambda *a, **k: True)
    calls = []
    def add(*a, **kw):
        calls.append(kw["approved"])
        return {"status": "USER_AUTHORED_SCRATCH_DRAFT_NOT_VALIDATED",
                "task_key_claimed": "TASK-NEXT", "sha256": "a" * 64,
                "installed_or_project_write_authorized": False}
    monkeypatch.setattr(desktop.portable, "add_task", add)
    def refresh():
        view.choices = {}  # HISTORY view hides new ACTIVE task.
        view.inventory_packet = {"original_offered_choices": [{
            "kind": "ACTIVE_TASK", "task_key_claimed": "TASK-NEXT",
            "selected_note_sha256": "a" * 64}]}
        return True
    view.refresh = refresh
    desktop.PersonalDayDesktop.add_existing(view)
    assert refusals == [] and calls == [True]
    assert view.choices == {}  # No implicit current task selection.
    assert "ALL/ACTIVE" in view.status.get()


def _next_action_view():
    """No Tk or filesystem; all original owners are mocked to prevent effects."""
    view = _View()
    view.values = {"desk": _Var("/test/Vres-Desk-Selected")}
    view.loaded_desk = "/test/Vres-Desk-Selected"
    view.inventory_packet = {"owner_packet": "read-only"}
    view._selected = lambda: ("ACTIVE_TASK", "TASK-SELECTED", "a" * 64)
    view.focused = (("old",), {"stage": "RESULT_REVIEW_READY_SEPARATE_DECISION"}, None)
    view.decision = {"binding": ("old",)}
    view.status = _Var("")
    view._sync_guidance = lambda: None
    view._invalidate = lambda: desktop.PersonalDayDesktop._invalidate(view)
    displayed, refusals = [], []
    view._display = displayed.append
    view._refuse = lambda: refusals.append("REFUSED")
    return view, displayed, refusals


def _next_action_owner_packet():
    return {
        "selected_choice_kind": "ACTIVE_TASK",
        "selected_task_key_claimed": "TASK-SELECTED",
        "source_context_selected_explicitly": False,
        "selected_original_journey": {
            "selected_note_sha256": "a" * 64,
            "selected_next_action_disclosed": True,
            "selected_next_action_untrusted": "Review the task's next manual step.",
        },
    }


def test_selected_next_action_reads_only_explicit_original_task(monkeypatch):
    view, shown, refused = _next_action_view()
    calls = []
    def original_day(desk, task, *, show_selected_action=False):
        calls.append((desk, task, show_selected_action))
        return _next_action_owner_packet()
    monkeypatch.setattr(desktop.owner, "review_personal_day", original_day)
    monkeypatch.setattr(desktop, "checked_day", lambda p, *, selected: p)
    monkeypatch.setattr(desktop.owner, "render_personal_day",
                        lambda p: "UNTRUSTED TASK ACTION: " +
                        p["selected_original_journey"]["selected_next_action_untrusted"])
    monkeypatch.setattr(desktop.owner, "finish_reviewed_decision",
                        lambda *a, **kw: pytest.fail("Never write or complete"))
    monkeypatch.setattr(desktop.owner, "reopen_saved",
                        lambda *a, **kw: pytest.fail("Never reopen history"))
    desktop.PersonalDayDesktop.inspect_next_action(view)
    assert refused == []
    assert calls == [("/test/Vres-Desk-Selected", "TASK-SELECTED", True)]
    assert view.focused is None and view.decision is None
    assert shown == ["", "UNTRUSTED TASK ACTION: Review the task's next manual step."]
    assert "never execute" in view.status.get().lower()


def test_selected_next_action_refuses_history_or_unloaded_desk_without_reads(monkeypatch):
    monkeypatch.setattr(desktop.owner, "review_personal_day",
                        lambda *a, **k: pytest.fail("Unselected owner must not be read"))
    for kind, loaded in (("SAVED_COMPLETED_RESULT", "/test/Vres-Desk-Selected"),
                         ("ACTIVE_TASK", None),
                         ("ACTIVE_TASK", "/test/Vres-Desk-Other")):
        view, shown, refused = _next_action_view()
        view._selected = lambda kind=kind: (kind, "TASK-SELECTED", "a" * 64)
        view.loaded_desk = loaded
        desktop.PersonalDayDesktop.inspect_next_action(view)
        assert refused == ["REFUSED"] and shown == [""]
        assert view.focused is None and view.decision is None


def test_selected_next_action_rejects_stale_or_unauthorized_disclosure(monkeypatch):
    view, shown, refused = _next_action_view()
    monkeypatch.setattr(desktop, "checked_day", lambda p, *, selected: p)
    monkeypatch.setattr(desktop.owner, "render_personal_day",
                        lambda p: pytest.fail("Refused action must not render"))
    for change in (
        {"selected_choice_kind": "SAVED_COMPLETED_RESULT"},
        {"selected_task_key_claimed": "TASK-OTHER"},
        {"source_context_selected_explicitly": True},
        {"selected_original_journey": {"selected_note_sha256": "b" * 64,
                                       "selected_next_action_disclosed": True,
                                       "selected_next_action_untrusted": "Never"}},
        {"selected_original_journey": {"selected_note_sha256": "a" * 64,
                                       "selected_next_action_disclosed": False,
                                       "selected_next_action_untrusted": "Never"}},
        {"selected_original_journey": {"selected_note_sha256": "a" * 64,
                                       "selected_next_action_disclosed": True,
                                       "selected_next_action_untrusted": "bad\nnew line"}},
    ):
        packet = {**_next_action_owner_packet(), **change}
        monkeypatch.setattr(desktop.owner, "review_personal_day",
                            lambda *a, packet=packet, **k: packet)
        desktop.PersonalDayDesktop.inspect_next_action(view)
    assert refused == ["REFUSED"] * 6
    assert shown == [""] * 6


def test_next_action_button_only_for_selected_active_loaded_original_owner():
    class Button:
        def __init__(self):
            self.state = None
        def configure(self, **kw):
            self.state = kw["state"]
    view, _, _ = _next_action_view()
    view.action_buttons = {}
    view.guide = _Var("")
    view.add_button = Button()
    view.action_preview_button = Button()
    view._ui_plan = lambda: {"enabled": {}, "next_step": "Read only"}
    view._selected = lambda: ("ACTIVE_TASK", "TASK-SELECTED", "a" * 64)
    desktop.PersonalDayDesktop._sync_guidance(view)
    assert view.action_preview_button.state == "normal"
    view._selected = lambda: ("SAVED_COMPLETED_RESULT", "TASK-OLD", "a" * 64)
    desktop.PersonalDayDesktop._sync_guidance(view)
    assert view.action_preview_button.state == "disabled"
    view._selected = lambda: ("ACTIVE_TASK", "TASK-SELECTED", "a" * 64)
    view.loaded_desk = "/test/Vres-Desk-Other"
    desktop.PersonalDayDesktop._sync_guidance(view)
    assert view.action_preview_button.state == "disabled"


def _completion_briefing_view():
    view, refused = _completion_view()
    view.loaded_desk = "/bounded/Vres-Desk-Synthetic"
    view._sync_guidance = lambda: None
    shown = []
    view._display = shown.append
    view.focused = (("stable",), {
        "stage": "RESULT_REVIEW_READY_SEPARATE_DECISION",
        "task_key_claimed": "TASK-SYNTHETIC",
        "selected_note_sha256": "c" * 64,
        "selected_project_binding_sha256": "d" * 64,
        "checkpoint_sha256": "a" * 64,
        "current_result_sha256": "e" * 64,
        "decision_sha256": "b" * 64,
        "acceptance_claims_state": "NO_CHECKLIST_REVIEWED",
        "unresolved_criterion_ids": [],
        "extra_known_gap_acknowledgement_required": False,
    }, None)
    return view, shown, refused


def _completion_briefing_packet():
    return {
        "schema": desktop.owner.COMPLETION_BRIEFING_SCHEMA,
        "status": "READ_ONLY_ONE_TASK_COMPLETION_BRIEFING",
        "task_key_claimed": "TASK-SYNTHETIC",
        "selected_note_sha256": "c" * 64,
        "selected_project_binding_sha256": "d" * 64,
        "checkpoint_sha256": "a" * 64,
        "current_result_sha256": "e" * 64,
        "decision_sha256": "b" * 64,
        "acceptance_claims_state": "NO_CHECKLIST_REVIEWED",
        "unresolved_criterion_ids": [],
        "extra_known_gap_acknowledgement_required": False,
        "selected_next_action_disclosed": False,
        "selected_next_action_untrusted": None,
        "historical_result_current_bytes_verified": False,
        "separate_exact_decide_with_yes_required": True,
        "digest_authenticates_user_or_host": False,
        "result_quality_validated": False,
        "original_174_protected_fable_granted": False,
        "original_176_live_episode_or_reuse_eligible": False,
        "task_completion_approved_or_performed": False,
        "native_claude_or_hooks_executed": False,
        "database_contacted": False,
        "writes_performed": False,
        "new_store_created": False,
    }


def test_briefing_guidance_requires_explicit_focused_result_not_history():
    for kind, stage, focused in (
            ("ACTIVE_TASK", None, False),
            ("ACTIVE_TASK", "PROJECT_SELECTED_NO_RESULT", True),
            ("SAVED_COMPLETED_RESULT", "RESULT_REVIEW_READY_SEPARATE_DECISION", True)):
        assert not desktop.guided_action_plan(
            kind, stage, focused=focused, history_clear=True)["enabled"]["briefing"]
    ready = desktop.guided_action_plan(
        "ACTIVE_TASK", "RESULT_REVIEW_READY_SEPARATE_DECISION", focused=True)
    assert ready["enabled"]["briefing"]
    assert not ready["enabled"]["complete"]


def test_briefing_reuses_original_owner_and_clears_previous_decision(monkeypatch):
    view, shown, refused = _completion_briefing_view()
    checks, calls = [], []
    view._recheck_original_source = lambda task: checks.append(task)
    def original_brief(*args, **kwargs):
        calls.append((args, kwargs))
        return _completion_briefing_packet()
    monkeypatch.setattr(desktop.owner, "prepare_completion_briefing", original_brief)
    monkeypatch.setattr(desktop.owner, "render_completion_briefing",
                        lambda packet: "Vres-OS PERSONAL COMPLETION BRIEFING -- READ ONLY\nTask")
    monkeypatch.setattr(desktop.owner, "finish_reviewed_decision",
                        lambda *a, **kw: pytest.fail("Briefing cannot finish"))
    desktop.PersonalDayDesktop.preview_briefing(view)
    assert refused == []
    assert shown == ["", "Vres-OS PERSONAL COMPLETION BRIEFING -- READ ONLY\nTask"]
    assert calls[0][0] == ("/bounded/Vres-Desk-Synthetic", "TASK-SYNTHETIC",
                            "/bounded/Project", "project:" + "d" * 24,
                            "/bounded/Project/report.md")
    assert calls[0][1]["show_selected_action"] is False
    assert calls[0][1]["expected_checkpoint_sha256"] == "a" * 64
    assert checks == ["TASK-SYNTHETIC"] * 2
    assert view.decision is None and view.focused is not None
    assert "Review decision separately" in view.status.get()


def test_briefing_refuses_saved_unloaded_unfocused_and_nonresult_before_read(monkeypatch):
    monkeypatch.setattr(desktop.owner, "prepare_completion_briefing",
                        lambda *a, **k: pytest.fail("Unfocused briefing cannot read"))
    for case in ("saved", "unloaded", "unfocused", "planning"):
        view, shown, refused = _completion_briefing_view()
        if case == "saved":
            view._selected = lambda: ("SAVED_COMPLETED_RESULT", "TASK-SYNTHETIC", "c" * 64)
        elif case == "unloaded":
            view.loaded_desk = None
        elif case == "unfocused":
            view.focused = None
        else:
            view.focused[1]["stage"] = "PROJECT_SELECTED_NO_RESULT"
        desktop.PersonalDayDesktop.preview_briefing(view)
        assert refused == ["REFUSED"] and shown == [""]
        assert view.decision is None


def test_briefing_refuses_tampered_receipts_without_render(monkeypatch):
    monkeypatch.setattr(desktop.owner, "render_completion_briefing",
                        lambda *_: pytest.fail("Invalid receipt cannot render"))
    for field, value in (
            ("selected_note_sha256", "f" * 64),
            ("checkpoint_sha256", "f" * 64),
            ("selected_next_action_disclosed", True),
            ("selected_next_action_untrusted", "execute-this"),
            ("task_completion_approved_or_performed", True),
            ("database_contacted", True),
            ("original_176_live_episode_or_reuse_eligible", True)):
        view, shown, refused = _completion_briefing_view()
        packet = {**_completion_briefing_packet(), field: value}
        monkeypatch.setattr(desktop.owner, "prepare_completion_briefing",
                            lambda *a, packet=packet, **k: packet)
        desktop.PersonalDayDesktop.preview_briefing(view)
        assert refused == ["REFUSED"] and shown == [""]
        assert view.decision is None


def test_briefing_refuses_late_source_drift_without_render(monkeypatch):
    view, shown, refused = _completion_briefing_view()
    checks = []
    def recheck(_task):
        checks.append("CHECK")
        if len(checks) == 2:
            raise desktop.DesktopRefused("late source drift")
    view._recheck_original_source = recheck
    monkeypatch.setattr(desktop.owner, "prepare_completion_briefing",
                        lambda *a, **k: _completion_briefing_packet())
    monkeypatch.setattr(desktop.owner, "render_completion_briefing",
                        lambda *_: pytest.fail("Late drift cannot render"))
    desktop.PersonalDayDesktop.preview_briefing(view)
    assert checks == ["CHECK", "CHECK"]
    assert refused == ["REFUSED"] and shown == [""]
    assert view.decision is None


def test_revision_inventory_requires_same_active_note_and_no_manual_recovery(monkeypatch):
    monkeypatch.setattr(desktop.owner, "render_personal_day", lambda p: "READ ONLY")
    packet = _triage_owner_packet()
    packet["manual_revision_recovery_attention_required"] = False
    assert desktop.checked_revision_inventory(
        packet, task="TASK-TODAY", note_sha256="a" * 64) is None
    for task, digest in (("TASK-TODAY", "b" * 64),
                         ("TASK-OLD", "b" * 64),
                         ("TASK-OTHER", "a" * 64)):
        with pytest.raises(desktop.DesktopRefused):
            desktop.checked_revision_inventory(packet, task=task, note_sha256=digest)
    packet["manual_revision_recovery_attention_required"] = True
    with pytest.raises(desktop.DesktopRefused, match="MANUAL"):
        desktop.checked_revision_inventory(
            packet, task="TASK-TODAY", note_sha256="a" * 64)


def test_revision_preview_delegates_exact_original_readers_no_writes(monkeypatch):
    from pathlib import Path
    root = Path("/test/Vres-Desk-Existing")
    visited = []
    monkeypatch.setattr(desktop.portable, "_desk",
                        lambda value, *, must_exist: root)
    monkeypatch.setattr(desktop.portable, "_existing_tasks",
                        lambda value: ["TASK-TODAY"])
    monkeypatch.setattr(desktop.lifecycle, "_active",
                        lambda value, key: (root / "Vres-Workbench-TASK-TODAY",
                                            {"sha256": "a" * 64}))
    attention = {
        "schema": desktop.lifecycle.SCHEMA,
        "status": "READ_ONLY_PENDING_REVISION_ATTENTION",
        "manual_recovery_attention_required": False,
        "automatic_recovery_performed": False,
        "pending_contents_opened": False,
        "writes_performed": False,
    }
    monkeypatch.setattr(desktop.lifecycle, "inspect_pending_revision_attention",
                        lambda value: attention)
    monkeypatch.setattr(desktop.portable.project_draft, "_under",
                        lambda path, ancestor: False)
    monkeypatch.setattr(desktop.portable.project_draft, "_manual_markdown",
                        lambda file: (visited.append(file) or
                                      "# Task\n\n## Next action\n- Review the note.\n"))
    monkeypatch.setattr(desktop.portable.continuity, "_action",
                        lambda text: visited.append("validated-untrusted-action"))
    receipt = {
        "status": "DRAFT_PREVIEW_ONLY", "task_key_claimed": "TASK-TODAY",
        "sha256": "b" * 64, "writes_performed": False,
        "installed_or_project_write_authorized": False,
    }
    monkeypatch.setattr(desktop.portable.workbench, "preview_note",
                        lambda task, markdown: receipt)
    out = desktop.preview_selected_task_revision(
        str(root), "TASK-TODAY", "/test/new.md", "a" * 64)
    assert out == {
        "task_key_claimed": "TASK-TODAY", "previous_sha256": "a" * 64,
        "sha256": "b" * 64, "writes_performed": False,
    }
    assert visited == ["/test/new.md", "validated-untrusted-action"]
    attention["manual_recovery_attention_required"] = True
    with pytest.raises(desktop.DesktopRefused):
        desktop.preview_selected_task_revision(
            str(root), "TASK-TODAY", "/test/new.md", "a" * 64)
    attention["manual_recovery_attention_required"] = False
    receipt["writes_performed"] = True
    with pytest.raises(desktop.DesktopRefused):
        desktop.preview_selected_task_revision(
            str(root), "TASK-TODAY", "/test/new.md", "a" * 64)
    receipt["writes_performed"] = False
    receipt["sha256"] = "a" * 64
    with pytest.raises(desktop.DesktopRefused):
        desktop.preview_selected_task_revision(
            str(root), "TASK-TODAY", "/test/new.md", "a" * 64)


def _revision_view():
    view, refused = _existing_add_view()
    view._selected = lambda: ("ACTIVE_TASK", "TASK-TODAY", "a" * 64)
    view.inventory_packet = {"loaded": True}
    view.values["note"].set("/test/revised.md")
    view.focused = (("stale",), {"stage": "RESULT_REVIEW_READY_SEPARATE_DECISION"}, None)
    view.decision = {"old": True}
    def invalidate():
        view.focused = None
        view.decision = None
    view._invalidate = invalidate
    return view, refused


def _mock_revision_owner(monkeypatch, *, drift=None):
    packet = _triage_owner_packet()
    packet["manual_revision_recovery_attention_required"] = False
    monkeypatch.setattr(desktop.owner, "render_personal_day", lambda p: "READ ONLY")
    reads, previews = [], []
    def day(desk):
        reads.append(desk)
        state = dict(packet)
        if drift == "owner" and len(reads) == 2:
            state["proposal_sha256"] = "f" * 64
        return state
    def preview(desk, task, note, digest):
        previews.append((desk, task, note, digest))
        return {"task_key_claimed": task, "previous_sha256": digest,
                "sha256": ("c" if drift == "note" and len(previews) > 1 else "b") * 64,
                "writes_performed": False}
    monkeypatch.setattr(desktop.owner, "review_personal_day", day)
    monkeypatch.setattr(desktop, "preview_selected_task_revision", preview)
    return reads, previews, packet


def test_revision_refuses_unloaded_saved_or_missing_note_before_owner_reads(monkeypatch):
    monkeypatch.setattr(desktop.owner, "review_personal_day",
                        lambda *a: pytest.fail("Invalid selection must not read owner"))
    monkeypatch.setattr(desktop.lifecycle, "revise",
                        lambda *a, **k: pytest.fail("Invalid selection must never revise"))
    for case in ("unloaded", "history", "no-note", "no-snapshot"):
        view, refused = _revision_view()
        if case == "unloaded":
            view.loaded_desk = None
        elif case == "history":
            view._selected = lambda: ("SAVED_COMPLETED_RESULT", "TASK-TODAY", "a" * 64)
        elif case == "no-note":
            view.values["note"].set("")
        else:
            view.inventory_packet = None
        desktop.PersonalDayDesktop.revise_selected(view)
        assert refused == [True]
        assert view.focused is None and view.decision is None


def test_revision_cancel_discards_old_decision_without_original_write(monkeypatch):
    view, refused = _revision_view()
    reads, previews, _ = _mock_revision_owner(monkeypatch)
    monkeypatch.setattr(desktop.messagebox, "askyesno", lambda *a, **kw: False)
    monkeypatch.setattr(desktop.lifecycle, "revise",
                        lambda *a, **kw: pytest.fail("Cancelled revision cannot write"))
    desktop.PersonalDayDesktop.revise_selected(view)
    assert refused == [] and len(reads) == len(previews) == 1
    assert view.focused is None and view.decision is None
    assert "cancelled" in view.status.get().lower()


def test_revision_refuses_postconsent_owner_or_note_drift_without_write(monkeypatch):
    monkeypatch.setattr(desktop.messagebox, "askyesno", lambda *a, **kw: True)
    monkeypatch.setattr(desktop.lifecycle, "revise",
                        lambda *a, **kw: pytest.fail("Drift cannot call original write"))
    for case in ("owner", "note"):
        view, refused = _revision_view()
        reads, previews, _ = _mock_revision_owner(monkeypatch, drift=case)
        desktop.PersonalDayDesktop.revise_selected(view)
        assert refused == [True]
        assert len(reads) == 2
        assert len(previews) == (1 if case == "owner" else 2)
        assert view.decision is None


def test_revision_single_exact_owner_write_and_unselected_history_readback(monkeypatch):
    view, refused = _revision_view()
    reads, previews, packet = _mock_revision_owner(monkeypatch)
    monkeypatch.setattr(desktop.messagebox, "askyesno", lambda *a, **kw: True)
    writes = []
    def revise(desk, task, note, *, approved=False,
               expected_sha256=None, expected_new_sha256=None):
        writes.append((desk, task, note, approved, expected_sha256, expected_new_sha256))
        return {"schema": desktop.lifecycle.SCHEMA, "status": "OWN_TASK_REVISED",
                "task_key_claimed": task, "previous_sha256": "a" * 64,
                "sha256": "b" * 64, "previous_snapshot_preserved": True,
                "installed_vres_modified": False}
    monkeypatch.setattr(desktop.lifecycle, "revise", revise)
    def refresh():
        view.inventory_packet = {
            **packet,
            "revision_snapshot_count": packet["revision_snapshot_count"] + 1,
            "original_offered_choices": [
                {**choice, "selected_note_sha256": (
                    "b" * 64 if choice["kind"] == "ACTIVE_TASK" else choice["selected_note_sha256"])}
                for choice in packet["original_offered_choices"]],
        }
        return True
    view.refresh = refresh
    desktop.PersonalDayDesktop.revise_selected(view)
    assert refused == []
    assert reads == ["/test/Vres-Desk-Existing"] * 2
    assert len(previews) == 2
    assert writes == [("/test/Vres-Desk-Existing", "TASK-TODAY", "/test/revised.md",
                       True, "a" * 64, "b" * 64)]
    assert view.focused is None and view.decision is None
    assert view.values["note"].get() == "" and view.values["new_task"].get() == ""
    assert all(view.values[field].get() == "" for field in desktop._HISTORY_CONTEXT_FIELDS)
    assert not any(var.get() for var in (
        view.with_intake, view.with_acceptance, view.with_catalog, view.with_synthetic))
    assert "revised" in view.status.get().lower()


def test_revision_postwrite_mismatch_refuses_without_auto_retry(monkeypatch):
    view, refused = _revision_view()
    _reads, _previews, packet = _mock_revision_owner(monkeypatch)
    monkeypatch.setattr(desktop.messagebox, "askyesno", lambda *a, **kw: True)
    calls = []
    def revise(*a, **kw):
        calls.append((a, kw))
        return {"schema": desktop.lifecycle.SCHEMA, "status": "OWN_TASK_REVISED",
                "task_key_claimed": "TASK-TODAY", "previous_sha256": "a" * 64,
                "sha256": "b" * 64, "previous_snapshot_preserved": True,
                "installed_vres_modified": False}
    monkeypatch.setattr(desktop.lifecycle, "revise", revise)
    def stale_refresh():
        view.inventory_packet = packet  # stale OLD active note and revision count
        return True
    view.refresh = stale_refresh
    desktop.PersonalDayDesktop.revise_selected(view)
    assert refused == [True] and len(calls) == 1


def test_revision_button_enabled_only_for_loaded_explicit_active_choice():
    class Button:
        def __init__(self):
            self.state = None
        def configure(self, **kw):
            self.state = kw["state"]
    view, _, _ = _next_action_view()
    view.action_buttons = {}
    view.guide = _Var("")
    view.add_button = Button()
    view.action_preview_button = Button()
    view.revise_button = Button()
    view.inventory_packet = {"manual_revision_recovery_attention_required": False}
    view._ui_plan = lambda: {"enabled": {}, "next_step": "Read only"}
    desktop.PersonalDayDesktop._sync_guidance(view)
    assert view.revise_button.state == "normal"
    view.inventory_packet["manual_revision_recovery_attention_required"] = True
    desktop.PersonalDayDesktop._sync_guidance(view)
    assert view.revise_button.state == "disabled"
    view.inventory_packet["manual_revision_recovery_attention_required"] = False
    view._selected = lambda: ("SAVED_COMPLETED_RESULT", "TASK-OLD", "a" * 64)
    desktop.PersonalDayDesktop._sync_guidance(view)
    assert view.revise_button.state == "disabled"
    view._selected = lambda: ("ACTIVE_TASK", "TASK-SELECTED", "a" * 64)
    view.loaded_desk = "/test/Vres-Desk-Other"
    desktop.PersonalDayDesktop._sync_guidance(view)
    assert view.revise_button.state == "disabled"


def _workday_home_fixture():
    """Original owner-shaped bounded day/home with pending recovery attention."""
    day = _triage_owner_packet()
    saved = [
        ("completed", "TASK-OLD", "b" * 64, True),
        ("completed", "TASK-TODAY", "c" * 64, True),
        ("completed", "TASK-UNLINKED", "d" * 64, False),
        ("archived", "TASK-ARCHIVED", "e" * 64, False),
        ("revisions", "TASK-REV1", "f" * 64, False),
        ("revisions", "TASK-REV2", "0" * 64, False),
    ]
    history = [
        {"state": state, "task_key_claimed": task, "note_sha256": sha,
         "saved_result_linked": linked, "current_result_bytes_verified": False,
         "saved_acceptance_self_claims_linked": False}
        for state, task, sha, linked in saved
    ]
    home = {
        "schema": desktop.owner.WORKDAY_SCHEMA,
        "status": "READ_ONLY_INTEGRATED_PERSONAL_WORKDAY_HOME",
        "active_count": 1,
        "active_tasks": [{"task_key_claimed": "TASK-TODAY",
                          "note_sha256": "a" * 64, "note_bytes": 50}],
        "completed_snapshot_count": 3,
        "archived_snapshot_count": 1,
        "revision_snapshot_count": 2,
        "saved_history": history,
        "selected_review": None,
        "manual_revision_recovery_attention_required": True,
    }
    for field in (
            "automatic_revision_recovery_performed", "automatic_task_selection_performed",
            "history_has_timestamps", "historical_document_current_bytes_verified",
            "result_quality_validated", "task_reopened_or_completed",
            "native_chairman_task_bound", "native_claude_or_hooks_executed",
            "database_contacted", "writes_performed", "new_store_created",
            "installed_vres_modified"):
        home[field] = False
    return day, home


def test_workday_home_reads_original_bounded_day_and_pending_attention(monkeypatch):
    day, home = _workday_home_fixture()
    monkeypatch.setattr(desktop.owner, "render_personal_day",
                        lambda p: "ORIGINAL PERSONAL DAY READ ONLY")
    text = desktop.render_verified_workday_home(day, home)
    assert text.startswith("Vres-OS PERSONAL WORKDAY HOME -- READ ONLY")
    assert "interrupted task revision staging" in text
    assert "Saved completed snapshots (UNDATED): 3" in text
    assert "No task automatically selected" in text
    assert "Task note action hidden" not in text


def test_workday_home_refuses_owner_or_history_drift_and_claims(monkeypatch):
    day, home = _workday_home_fixture()
    monkeypatch.setattr(desktop.owner, "render_personal_day", lambda p: "READ ONLY")
    for field, forged in (
            ("active_count", 2), ("writes_performed", True),
            ("selected_review", {"kind": "EXPLICIT_ACTIVE_TASK"}),
            ("manual_revision_recovery_attention_required", False)):
        with pytest.raises(desktop.DesktopRefused):
            desktop.render_verified_workday_home(day, {**home, field: forged})
    for modified in ("note", "linked", "count", "unsafe_history"):
        other = {**home, "active_tasks": [dict(row) for row in home["active_tasks"]],
                 "saved_history": [dict(row) for row in home["saved_history"]]}
        if modified == "note":
            other["active_tasks"][0]["note_sha256"] = "f" * 64
        elif modified == "linked":
            other["saved_history"][0]["saved_result_linked"] = False
        elif modified == "count":
            other["saved_history"].pop()
        else:
            other["saved_history"][3]["current_result_bytes_verified"] = True
        with pytest.raises(desktop.DesktopRefused):
            desktop.render_verified_workday_home(day, other)


def test_workday_home_desktop_clears_old_decision_without_any_write(monkeypatch):
    day, home = _workday_home_fixture()
    view, shown, refused = _next_action_view()
    view.inventory_packet = day
    monkeypatch.setattr(desktop.owner, "review_personal_day",
                        lambda *a, **k: day)
    monkeypatch.setattr(desktop.owner, "review_workday",
                        lambda *a, **k: home)
    monkeypatch.setattr(desktop.owner, "render_personal_day",
                        lambda p: "ORIGINAL DAY READ ONLY")
    monkeypatch.setattr(desktop.owner, "finish_reviewed_decision",
                        lambda *a, **k: pytest.fail("Read-only Workday Home cannot finish"))
    desktop.PersonalDayDesktop.review_home(view)
    assert not refused
    assert view.focused is None and view.decision is None
    assert shown[-1].startswith("Vres-OS PERSONAL WORKDAY HOME -- READ ONLY")
    assert "MANUAL RECOVERY ATTENTION" in view.status.get()


def test_workday_home_refuses_changed_original_day_after_render(monkeypatch):
    day, home = _workday_home_fixture()
    view, shown, refused = _next_action_view()
    view.inventory_packet = day
    visits = []
    def changing_day(_desk):
        visits.append("READ")
        return day if len(visits) == 1 else {**day, "proposal_sha256": "f" * 64}
    monkeypatch.setattr(desktop.owner, "review_personal_day", changing_day)
    monkeypatch.setattr(desktop.owner, "review_workday", lambda _desk: home)
    monkeypatch.setattr(desktop.owner, "render_personal_day", lambda p: "READ ONLY")
    desktop.PersonalDayDesktop.review_home(view)
    assert visits == ["READ", "READ"]
    assert refused == ["REFUSED"]
    assert shown == [""]
    assert view.decision is None


def test_recovery_hold_guidance_disables_completion_and_reopen():
    view, _, _ = _next_action_view()
    view.inventory_packet = {"manual_revision_recovery_attention_required": True}
    view._binding = lambda: ("stable",)
    view._history_inputs_clear = lambda: True
    view.focused = (("stable",),
                    {"stage": "RESULT_REVIEW_READY_SEPARATE_DECISION"}, None)
    view.decision = {"binding": ("stable",)}
    plan = desktop.PersonalDayDesktop._ui_plan(view)
    assert not plan["enabled"]["complete"]
    assert "MANUAL RECOVERY HOLD" in plan["next_step"]
    view._selected = lambda: ("SAVED_COMPLETED_RESULT", "TASK-OLD", "b" * 64)
    plan = desktop.PersonalDayDesktop._ui_plan(view)
    assert not plan["enabled"]["reopen"]
    assert plan["enabled"]["replay"]  # read-only explicit verification remains possible


def test_original_archived_history_is_bounded_undated_and_read_only(monkeypatch):
    """Only original lifecycle snapshots, never a second task/history store."""
    day, home = _workday_home_fixture()
    monkeypatch.setattr(desktop.owner, "render_personal_day", lambda _day: "READ ONLY")
    rows = [
        {"state": row["state"], "task_key_claimed": row["task_key_claimed"],
         "sha256": row["note_sha256"], "bytes": 50}
        for row in home["saved_history"]]
    history = {
        "schema": desktop.lifecycle.SCHEMA,
        "status": "READ_ONLY_PERSONAL_HISTORY",
        "snapshots": rows, "count": len(rows),
        "writes_performed": False, "authoritative_task_store": False,
        "document_current_bytes_verified": False,
    }
    assert desktop.checked_archived_history(history, day) == [
        ("TASK-ARCHIVED", "e" * 64)]
    for changed in (
            {**history, "writes_performed": True},
            {**history, "count": 999},
            {**history, "snapshots": rows[:-1]},
            {**history, "snapshots": rows + [rows[0]]}):
        with pytest.raises(desktop.DesktopRefused):
            desktop.checked_archived_history(changed, day)
    assert desktop.checked_archived_history(history, day) == [
        ("TASK-ARCHIVED", "e" * 64)]  # even with pending HOLD, READ remains safe


def test_original_archive_cancel_and_postconsent_drift_never_move(monkeypatch):
    view, _, refused = _next_action_view()
    day = {"archived_snapshot_count": 2, "active_task_count": 1}
    view.inventory_packet = day
    monkeypatch.setattr(desktop, "checked_day", lambda packet, *, selected: packet)
    monkeypatch.setattr(desktop, "checked_revision_inventory", lambda *_a, **_k: None)
    monkeypatch.setattr(desktop, "checked_archived_history", lambda *_a: [])
    monkeypatch.setattr(desktop.lifecycle, "list_history", lambda _desk: {"history": 1})
    monkeypatch.setattr(desktop.owner, "review_personal_day", lambda _desk: day)
    monkeypatch.setattr(desktop.lifecycle, "move_out",
                        lambda *_a, **_k: pytest.fail("Cancelled archive cannot move task"))
    monkeypatch.setattr(desktop.messagebox, "askyesno", lambda *_a, **_k: False)
    desktop.PersonalDayDesktop.archive_selected(view)
    assert not refused
    assert "cancelled" in view.status.get().lower()
    assert view.focused is None and view.decision is None

    view, _, refused = _next_action_view()
    view.inventory_packet = day
    calls = []
    def changed(_desk):
        calls.append("READ")
        return day if len(calls) == 1 else {**day, "active_task_count": 0}
    monkeypatch.setattr(desktop.owner, "review_personal_day", changed)
    monkeypatch.setattr(desktop.messagebox, "askyesno", lambda *_a, **_k: True)
    desktop.PersonalDayDesktop.archive_selected(view)
    assert calls == ["READ", "READ"]
    assert refused == ["REFUSED"]


def test_original_archive_exact_owner_write_and_undated_readback(monkeypatch):
    view, _, refused = _next_action_view()
    day = {"archived_snapshot_count": 2, "active_task_count": 1}
    view.inventory_packet = day
    monkeypatch.setattr(desktop, "checked_day", lambda packet, *, selected: packet)
    monkeypatch.setattr(desktop, "checked_revision_inventory", lambda *_a, **_k: None)
    monkeypatch.setattr(desktop, "checked_archived_history", lambda *_a: [])
    monkeypatch.setattr(desktop.owner, "review_personal_day", lambda _desk: day)
    monkeypatch.setattr(desktop.lifecycle, "list_history", lambda _desk: {"history": 1})
    monkeypatch.setattr(desktop.messagebox, "askyesno", lambda *_a, **_k: True)
    calls = []
    def archive(desk, task, *, state, approved, expected_sha256):
        calls.append((desk, task, state, approved, expected_sha256))
        return {"schema": desktop.lifecycle.SCHEMA, "status": "OWN_TASK_ARCHIVED",
                "task_key_claimed": task, "sha256": expected_sha256,
                "archived_bytes_preserved": True, "installed_vres_modified": False}
    monkeypatch.setattr(desktop.lifecycle, "move_out", archive)
    monkeypatch.setattr(desktop, "triage_personal_day", lambda _day: {"rows": []})
    def refresh():
        view.inventory_packet = {"archived_snapshot_count": 3, "active_task_count": 0}
        return True
    view.refresh = refresh
    desktop.PersonalDayDesktop.archive_selected(view)
    assert not refused
    assert calls == [("/test/Vres-Desk-Selected", "TASK-SELECTED", "archived",
                      True, "a" * 64)]
    assert "NOT completed" in view.status.get()


def test_original_archived_restore_exact_owner_and_preserved_history(monkeypatch):
    view, _, refused = _next_action_view()
    day = {"archived_snapshot_count": 1, "active_task_count": 0,
           "manual_revision_recovery_attention_required": False,
           "original_offered_choices": []}
    view.inventory_packet = day
    view.archive_packet = {"history": 1}
    view.archive_choices = {"archived-0": ("TASK-ARCHIVED", "e" * 64)}
    class Listing:
        def selection(self):
            return ("archived-0",)
    view.archive_listing = Listing()
    monkeypatch.setattr(desktop, "checked_day", lambda packet, *, selected: packet)
    monkeypatch.setattr(desktop, "checked_archived_history",
                        lambda _history, _day: [("TASK-ARCHIVED", "e" * 64)])
    monkeypatch.setattr(desktop.owner, "review_personal_day", lambda _desk: day)
    monkeypatch.setattr(desktop.lifecycle, "list_history",
                        lambda _desk: {"history": 1})
    monkeypatch.setattr(desktop.messagebox, "askyesno", lambda *_a, **_k: True)
    calls = []
    def restore(desk, task, *, state, expected_sha256, approved):
        calls.append((desk, task, state, expected_sha256, approved))
        return {"schema": desktop.lifecycle.SCHEMA, "status": "OWN_TASK_REOPENED",
                "task_key_claimed": task, "sha256": expected_sha256,
                "archived_snapshot_preserved": True, "installed_vres_modified": False}
    monkeypatch.setattr(desktop.lifecycle, "reopen", restore)
    monkeypatch.setattr(desktop, "triage_personal_day",
                        lambda _day: {"rows": [
                            ("ACTIVE_TASK", "TASK-ARCHIVED", "e" * 64)]})
    def refresh():
        view.inventory_packet = {"archived_snapshot_count": 1, "active_task_count": 1}
        return True
    view.refresh = refresh
    desktop.PersonalDayDesktop.restore_archived(view)
    assert not refused
    assert calls == [("/test/Vres-Desk-Selected", "TASK-ARCHIVED", "archived",
                      "e" * 64, True)]
    assert "preserved" in view.status.get().lower()


def test_original_archived_restore_refuses_pending_recovery_without_write(monkeypatch):
    view, _, refused = _next_action_view()
    view.inventory_packet = {
        "manual_revision_recovery_attention_required": True}
    view.archive_packet = {"history": 1}
    view.archive_choices = {"archived-0": ("TASK-ARCHIVED", "e" * 64)}
    class Listing:
        def selection(self):
            return ("archived-0",)
    view.archive_listing = Listing()
    monkeypatch.setattr(desktop, "checked_day", lambda packet, *, selected: packet)
    monkeypatch.setattr(desktop.owner, "review_personal_day",
                        lambda _desk: view.inventory_packet)
    monkeypatch.setattr(desktop.lifecycle, "list_history",
                        lambda _desk: pytest.fail("Held restore must not read or write history"))
    monkeypatch.setattr(desktop.lifecycle, "reopen",
                        lambda *_a, **_k: pytest.fail("Held restore must never reopen"))
    desktop.PersonalDayDesktop.restore_archived(view)
    assert refused == ["REFUSED"]
    assert view.decision is None and view.focused is None
