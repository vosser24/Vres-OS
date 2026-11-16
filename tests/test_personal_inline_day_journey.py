"""Original-owner integrated PERSONAL inline planning journey in disposable scratch.

No installed Windows app, live user profile, native Claude, hooks, PostgreSQL,
credentials, project adoption, or F1/Fable/Experience promotion.
"""
from __future__ import annotations

import hashlib

import pytest

from vres_os import personal_day_desktop as desktop
from vres_os import personal_offline_workbench as workbench
from vres_os import personal_portable_desk as portable
from vres_os import personal_task_lifecycle as lifecycle
from vres_os import personal_work_result as work_result
from vres_os import personal_work_session as owner

TASK = 'TASK-ONE-REAL-DAY'
PROJECT_KEY = 'project:' + 'a' * 24
FIRST = '# Today\n\n## Next action\n- Write the sample brief.\n'
REVISED = '# Today\n\n## Next action\n- Review the sample brief.\n'


def test_inline_one_coherent_daily_plan_revision_decision_result_replay_archive(tmp_path):
    desk = tmp_path / 'Vres-Desk-Inline-Day'
    project = tmp_path / 'Empty-Sample-Project'
    project.mkdir()
    first_sha = workbench.preview_note(TASK, FIRST)['sha256']
    # New desk/task from ephemeral Markdown through the ORIGINAL session owner.
    started = owner.start_session(
        desk, TASK, None, project, PROJECT_KEY, approved=True,
        note_markdown=FIRST, expected_sha256=first_sha)
    assert started['selected_note_sha256'] == first_sha
    assert started['original_scratch_task_created'] is True
    assert list(project.iterdir()) == []
    day = desktop.checked_day(owner.review_personal_day(desk), selected=False)
    assert ('ACTIVE_TASK', TASK, first_sha) in desktop.triage_personal_day(day)['rows']
    selected = desktop.checked_day(
        owner.review_personal_day(desk, TASK, show_selected_action=True), selected=True)
    assert selected['selected_original_journey']['selected_next_action_disclosed'] is True
    assert 'Write the sample brief' in selected['selected_original_journey'][
        'selected_next_action_untrusted']

    # Revision is separately approved, preserves exactly one prior snapshot.
    revised_sha = workbench.preview_note(TASK, REVISED)['sha256']
    revised = lifecycle.revise(
        desk, TASK, None, approved=True, note_markdown=REVISED,
        expected_sha256=first_sha, expected_new_sha256=revised_sha)
    assert revised['previous_snapshot_preserved'] is True
    assert portable.open_task(desk, TASK)['sha256'] == revised_sha
    history = lifecycle.list_history(desk)
    assert any(row['state'] == 'revisions' and row['sha256'] == first_sha
               for row in history['snapshots'])

    # User manually creates external result; Vres never executes the next action.
    report = project / 'sample-brief.md'
    report.write_text('# Example\n\nSynthetic report.\n', encoding='utf-8')
    checkpoint = work_result.inspect_work_result(
        desk, TASK, project, PROJECT_KEY, report)['checkpoint_sha256']
    decision = owner.prepare_completion_decision(
        desk, TASK, project, PROJECT_KEY, report,
        expected_checkpoint_sha256=checkpoint)
    assert decision['status'] == 'READ_ONLY_EXACT_PERSONAL_COMPLETION_DECISION'
    assert decision['writes_performed'] is False
    assert lifecycle.list_history(desk)['count'] == history['count']
    saved = owner.finish_reviewed_decision(
        desk, TASK, project, PROJECT_KEY, report,
        expected_checkpoint_sha256=checkpoint,
        expected_decision_sha256=decision['decision_sha256'], approved=True)
    assert saved['status'] == 'SEPARATELY_APPROVED_PERSONAL_RESULT_SAVED_IN_ORIGINAL_HISTORY'
    snapshot_sha = saved['saved_snapshot_sha256']
    assert snapshot_sha == revised_sha
    assert owner.reopen_saved(desk, TASK, snapshot_sha, approved=True)[
        'status'] == 'SAVED_WORK_SESSION_TASK_REOPENED'
    replay = owner.replay_saved(desk, TASK, snapshot_sha, approved=True)
    assert replay['status'] == 'SAVED_WORK_SESSION_EXACT_CONTEXT_REPLAY_MATCH'
    assert replay['result_quality_validated'] is False
    assert replay['future_document_bytes_guaranteed_unchanged'] is False

    # Original lifecycle exclusively controls active archive/restore.
    active = portable.open_task(desk, TASK)
    assert active['sha256'] == revised_sha
    archived = lifecycle.move_out(
        desk, TASK, state='archived', expected_sha256=revised_sha, approved=True)
    assert archived['status'] == 'OWN_TASK_ARCHIVED'
    restored = lifecycle.reopen(desk, TASK, state='archived',
                                expected_sha256=revised_sha, approved=True)
    assert restored['status'] == 'OWN_TASK_REOPENED'
    assert portable.open_task(desk, TASK)['sha256'] == revised_sha
    assert hashlib.sha256(report.read_bytes()).hexdigest() == replay['result_sha256']
    assert not (project / 'CLAUDE.md').exists()


def test_inline_owner_refuses_ambiguous_sources_and_wrong_hash_before_writes(tmp_path):
    desk = tmp_path / 'Vres-Desk-No-Ambiguity'
    project = tmp_path / 'Empty-Project'
    project.mkdir()
    draft = tmp_path / 'selected.md'
    draft.write_text(FIRST, encoding='utf-8')
    with pytest.raises(owner.WorkSessionRefused, match='exactly one'):
        owner.start_session(desk, TASK, draft, project, PROJECT_KEY,
                            approved=True, note_markdown=FIRST)
    assert not desk.exists()
    with pytest.raises(owner.WorkSessionRefused, match='digest changed'):
        owner.start_session(desk, TASK, None, project, PROJECT_KEY,
                            approved=True, note_markdown=FIRST,
                            expected_sha256='0' * 64)
    assert not desk.exists()
    portable.init_desk(desk, approved=True)
    with pytest.raises(portable.PortableDeskRefused, match='exactly one'):
        portable.add_task(desk, TASK, draft, approved=True, note_markdown=FIRST)
    with pytest.raises(portable.PortableDeskRefused, match='digest changed'):
        portable.add_task(desk, TASK, None, approved=True,
                          note_markdown=FIRST, expected_sha256='0' * 64)
    assert portable._existing_tasks(desk) == []


def test_inline_revision_manual_recovery_hold_and_identical_note_refusal(tmp_path):
    desk = tmp_path / 'Vres-Desk-Interrupted'
    portable.init_desk(desk, approved=True)
    first = portable.add_task(
        desk, TASK, None, approved=True, note_markdown=FIRST,
        expected_sha256=workbench.preview_note(TASK, FIRST)['sha256'])
    with pytest.raises(lifecycle.LifecycleRefused, match='No change'):
        lifecycle.revise(desk, TASK, None, approved=True, note_markdown=FIRST,
                         expected_sha256=first['sha256'])
    pending = desk / 'Vres-Lifecycle-History' / 'pending'
    pending.mkdir(parents=True)
    (pending / 'interrupted-stage').mkdir()
    with pytest.raises(lifecycle.LifecycleRefused, match='manual'):
        lifecycle.revise(desk, TASK, None, approved=True, note_markdown=REVISED,
                         expected_sha256=first['sha256'])
    assert portable.open_task(desk, TASK)['sha256'] == first['sha256']
    assert lifecycle.inspect_pending_revision_attention(desk)[
        'manual_recovery_attention_required'] is True


class _Var:
    def __init__(self, value): self.value = value
    def get(self): return self.value


class _Editor:
    def __init__(self, value): self.value = value
    def get(self, *_args): return self.value


def test_desktop_editor_accepts_exactly_one_transient_source():
    class View: pass
    view = View()
    view.values = {'note': _Var('')}
    view.inline_editor = _Editor(FIRST)
    assert desktop._selected_note_input(view) == (None, FIRST)
    view.values['note'] = _Var('/tmp/external.md')
    with pytest.raises(desktop.DesktopRefused, match='exactly ONE'):
        desktop._selected_note_input(view)
    view.inline_editor.value = '  '
    assert desktop._selected_note_input(view) == ('/tmp/external.md', None)
    view.values['note'] = _Var('')
    with pytest.raises(desktop.DesktopRefused, match='exactly ONE'):
        desktop._selected_note_input(view)
    view.inline_editor.value = '\x01 secret control'
    with pytest.raises(workbench.WorkbenchRefused):
        workbench.preview_note(TASK, view.inline_editor.value)
