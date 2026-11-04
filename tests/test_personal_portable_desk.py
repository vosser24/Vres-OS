"""Focused real-parent offline journey: one explicit desk, two tasks, no store."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from vres_os import personal_desk_cli as router
from vres_os import personal_offline_workbench as workbench
from vres_os import personal_portable_desk as desk

A, B = 'TASK-DESK-01', 'TASK-DESK-02'
ACTION_A = 'Review the draft before choosing a change.'
ACTION_B = 'Κατάγραψε το επόμενο βήμα για την αναφορά.'


@pytest.fixture
def inputs(tmp_path):
    d = tmp_path / 'Vres-Desk-Daily'
    src = tmp_path / 'inputs'
    src.mkdir()
    doc_a = src / 'my-note-a.md'
    doc_b = src / 'my-note-b.md'
    doc_a.write_text('# Project note\n\n## Next action\n- ' + ACTION_A + '\n', encoding='utf-8')
    doc_b.write_text('# Project note\n\n## Next action\n- ' + ACTION_B + '\n', encoding='utf-8')
    untouched = tmp_path / 'KEEP.txt'
    untouched.write_bytes(b'KEEP-UNRELATED-PROJECT-FILE')
    return d, doc_a, doc_b, untouched


def ready(inputs):
    d, a, b, untouched = inputs
    assert desk.init_desk(d, approved=True)['status'] == 'EMPTY_PORTABLE_DESK_CREATED'
    first = desk.add_task(d, A, a, approved=True)
    second = desk.add_task(d, B, b, approved=True)
    return d, a, b, untouched, first, second


def test_real_two_task_day_and_exact_owned_undo_without_manual_digest(inputs):
    d, a, b, untouched, first, second = ready(inputs)
    originals = {p: p.read_bytes() for p in (a, b, untouched)}
    assert first['sha256'] == hashlib.sha256(originals[a]).hexdigest()
    assert second['sha256'] == hashlib.sha256(originals[b]).hexdigest()
    hidden = desk.focus_desk(d, B)
    assert hidden['task_count'] == 2 and hidden['selected_task_key_claimed'] == B
    assert hidden['writes_performed'] is False and 'selected_next_action' not in hidden
    revealed = desk.focus_desk(d, B, show_selected_action=True)
    assert revealed['selected_next_action'] == ACTION_B and ACTION_A not in str(revealed)
    reopen = desk.open_task(d, A, show_next_action=True)
    assert reopen['next_action'] == ACTION_A and reopen['writes_performed'] is False
    undone = desk.remove_task(d, A, approved=True)
    assert undone['status'] == 'OWN_SCRATCH_NOTE_UNDONE'
    assert not (d / ('Vres-Workbench-' + A)).exists()
    assert desk.focus_desk(d, B)['task_count'] == 1
    assert desk.remove_task(d, B, approved=True)['status'] == 'OWN_SCRATCH_NOTE_UNDONE'
    assert list(d.iterdir()) == [] and d.exists()
    assert {p: p.read_bytes() for p in originals} == originals


def test_init_only_creates_an_empty_explicit_parent(inputs):
    d, _, _, untouched = inputs
    with pytest.raises(desk.PortableDeskRefused):
        desk.init_desk(d)
    assert not d.exists()
    result = desk.init_desk(d, approved=True)
    assert result['task_store_created'] is False and result['tasks_created'] == 0
    assert list(d.iterdir()) == [] and untouched.read_bytes() == b'KEEP-UNRELATED-PROJECT-FILE'
    with pytest.raises(desk.PortableDeskRefused, match='already exists'):
        desk.init_desk(d, approved=True)


def test_add_requires_approval_and_input_outside_desk(inputs):
    d, a, _, _ = inputs
    desk.init_desk(d, approved=True)
    with pytest.raises(desk.PortableDeskRefused, match='approval'):
        desk.add_task(d, A, a)
    assert list(d.iterdir()) == []
    inner = d / 'input.md'
    inner.write_bytes(a.read_bytes())
    with pytest.raises(desk.PortableDeskRefused, match='outside'):
        desk.add_task(d, A, inner, approved=True)
    assert not (d / ('Vres-Workbench-' + A)).exists()


def test_remove_requires_approval_even_for_valid_receipt(inputs):
    d, _, _, _, _, _ = ready(inputs)
    with pytest.raises(desk.PortableDeskRefused, match='approval'):
        desk.remove_task(d, A)
    assert workbench.inspect_note(d / ('Vres-Workbench-' + A))['task_key_claimed'] == A


def test_wrong_task_cannot_fallback_to_other_receipt(inputs):
    d, _, _, _, _, _ = ready(inputs)
    with pytest.raises(workbench.WorkbenchRefused):
        desk.open_task(d, 'TASK-NOT-PRESENT', show_next_action=True)
    with pytest.raises(workbench.WorkbenchRefused):
        desk.remove_task(d, 'TASK-NOT-PRESENT', approved=True)
    assert desk.focus_desk(d, A)['task_count'] == 2


def test_duplicate_task_refused_and_existing_note_unchanged(inputs):
    d, a, _, _ = inputs
    desk.init_desk(d, approved=True)
    first = desk.add_task(d, A, a, approved=True)
    with pytest.raises(desk.PortableDeskRefused, match='Duplicate'):
        desk.add_task(d, A, a, approved=True)
    assert workbench.inspect_note(d / ('Vres-Workbench-' + A)) == first


def test_duplicate_task_inside_different_named_workspace_is_refused(inputs):
    d, a, _, _ = inputs
    desk.init_desk(d, approved=True)
    workbench.create_note(d / 'Vres-Workbench-manual-extra', A, a.read_text(), approved=True)
    with pytest.raises(desk.PortableDeskRefused, match='Duplicate'):
        desk.add_task(d, A, a, approved=True)


def test_modified_note_never_reopened_or_removed(inputs):
    d, _, _, _, _, _ = ready(inputs)
    note = d / ('Vres-Workbench-' + A) / 'notes' / 'next-step.md'
    note.write_text('## Next action\n- FORGED NOTE\n', encoding='utf-8')
    for fn in (
        lambda: desk.open_task(d, A, show_next_action=True),
        lambda: desk.remove_task(d, A, approved=True),
        lambda: desk.focus_desk(d, B, show_selected_action=True),
    ):
        with pytest.raises(workbench.WorkbenchRefused):
            fn()
    assert note.exists() and 'FORGED' in note.read_text()


def test_unexpected_file_in_task_workspace_blocks_remove(inputs):
    d, _, _, _, _, _ = ready(inputs)
    extra = d / ('Vres-Workbench-' + A) / 'unrelated.txt'
    extra.write_text('PRESERVE')
    with pytest.raises(workbench.WorkbenchRefused):
        desk.remove_task(d, A, approved=True)
    assert extra.read_text() == 'PRESERVE'


def test_desk_six_tasks_capacity_is_enforced_before_extra_write(inputs):
    d, a, _, _ = inputs
    desk.init_desk(d, approved=True)
    for i in range(6):
        desk.add_task(d, f'TASK-ROW-{i}', a, approved=True)
    with pytest.raises(desk.PortableDeskRefused, match='limit'):
        desk.add_task(d, 'TASK-ROW-7', a, approved=True)
    assert not (d / 'Vres-Workbench-TASK-ROW-7').exists()
    assert desk.focus_desk(d, 'TASK-ROW-3')['task_count'] == 6


@pytest.mark.parametrize('path', ['Vres-Desk-relative', '.', 'C:\\fake\\Vres-Desk-relative', 'Vres-Desk-../other'])
def test_nonabsolute_or_ambiguous_desk_is_refused_without_writes(path):
    with pytest.raises(desk.PortableDeskRefused):
        desk.init_desk(path, approved=True)


def test_symlinked_parent_cannot_be_followed(inputs):
    d, a, _, _ = inputs
    desk.init_desk(d, approved=True)
    link = d.parent / 'Vres-Desk-redirect'
    try:
        link.symlink_to(d, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip('Host cannot create symlink')
    with pytest.raises(workbench.WorkbenchRefused):
        desk.add_task(link, A, a, approved=True)
    assert list(d.iterdir()) == []


def test_cli_two_real_notes_through_unified_entrypoint_in_separate_processes(inputs):
    d, a, b, untouched = inputs
    cmd = [sys.executable, '-I', '-S', '-B', router.__file__, 'desk']
    def run(args, expected=0):
        proc = subprocess.run(cmd + args, capture_output=True, text=True)
        assert proc.returncode == expected, proc.stderr
        return proc
    init = json.loads(run(['init', '--desk', str(d), '--yes']).stdout)
    assert init['status'] == 'EMPTY_PORTABLE_DESK_CREATED'
    for task, path in ((A, a), (B, b)):
        obj = json.loads(run(['add', '--desk', str(d), '--task-key', task,
                              '--note-file', str(path), '--yes']).stdout)
        assert obj['task_key_claimed'] == task
    hidden = json.loads(run(['open', '--desk', str(d), '--task-key', A]).stdout)
    assert 'next_action' not in hidden and hidden['next_action_disclosed'] is False
    focus_view = json.loads(run(['focus', '--desk', str(d), '--select', B, '--format', 'json',
                                 '--show-selected-action']).stdout)
    assert focus_view['selected_next_action'] == ACTION_B and ACTION_A not in str(focus_view)
    wrong = run(['open', '--desk', str(d), '--task-key', 'TASK-NONEXISTENT',
                 '--show-next-action'], expected=2)
    assert 'VRES_PORTABLE_DESK_REFUSED' in wrong.stderr and str(d) not in wrong.stderr
    for task in (A, B):
        assert json.loads(run(['remove', '--desk', str(d), '--task-key', task, '--yes']).stdout)['status'] == 'OWN_SCRATCH_NOTE_UNDONE'
    assert list(d.iterdir()) == [] and untouched.read_bytes() == b'KEEP-UNRELATED-PROJECT-FILE'


def test_cli_rejects_unknown_command_without_reading_project(inputs):
    d, _, _, _ = inputs
    assert router.main(['desk', 'some-unknown-command', '--desk', str(d)]) == 2
    assert not d.exists()


def test_empty_desk_focus_refuses_instead_of_fabricating_tasks(inputs):
    d, _, _, _ = inputs
    desk.init_desk(d, approved=True)
    with pytest.raises(desk.ScratchDiscoveryRefused if hasattr(desk, 'ScratchDiscoveryRefused') else ValueError):
        desk.focus_desk(d, A)
