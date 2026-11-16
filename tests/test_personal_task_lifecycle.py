"""One integrated disposable personal lifecycle journey; no installed state."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from vres_os import personal_offline_workbench as workbench
from vres_os import personal_portable_desk as desk
from vres_os import personal_task_lifecycle as lifecycle

A, B = 'TASK-LIFE-01', 'TASK-LIFE-02'


def test_one_personal_revision_completion_archive_and_reopen_journey(tmp_path, capsys):
    root = tmp_path / 'Vres-Desk-Lifecycle'
    notes = tmp_path / 'inputs'
    notes.mkdir()
    note_a = notes / 'A.md'
    note_new = notes / 'A-revised.md'
    note_b = notes / 'B.md'
    note_a.write_text('# One\n\n## Next action\n- Read the summary.\n', encoding='utf-8')
    note_new.write_text('# One\n\n## Next action\n- Share the summary.\n', encoding='utf-8')
    note_b.write_text('# Two\n\n## Next action\n- Collect one source.\n', encoding='utf-8')
    originals = {p: p.read_bytes() for p in (note_a, note_new, note_b)}
    untouched = tmp_path / 'UNRELATED.txt'
    untouched.write_bytes(b'preserve this unrelated user-owned neighbor')

    assert desk.init_desk(root, approved=True)['tasks_created'] == 0
    first = desk.add_task(root, A, note_a, approved=True)
    desk.add_task(root, B, note_b, approved=True)
    assert len(root.joinpath('Vres-Workbench-' + A).name) < 80
    assert lifecycle.main(['revise', '--desk', str(root), '--task-key', A,
                           '--note-file', str(note_new)]) == 2  # no approval
    assert desk.focus_desk(root, A)['task_count'] == 2
    assert lifecycle.main(['unknown', '--desk', str(root), '--secret', 'DO_NOT_PRINT']) == 2
    assert 'DO_NOT_PRINT' not in capsys.readouterr().err
    changed = lifecycle.revise(root, A, note_new, approved=True)
    assert changed['status'] == 'OWN_TASK_REVISED'
    assert changed['previous_sha256'] == first['sha256']
    assert changed['sha256'] == hashlib.sha256(originals[note_new]).hexdigest()
    assert desk.focus_desk(root, A, show_selected_action=True)['selected_next_action'] == 'Share the summary.'
    assert desk.focus_desk(root, B)['task_count'] == 2
    hist = lifecycle.list_history(root)
    assert hist['count'] == 1 and hist['snapshots'][0]['state'] == 'revisions'
    assert hist['snapshots'][0]['sha256'] == first['sha256']
    assert hist['writes_performed'] is False
    assert desk.main(['history', '--desk', str(root)]) == 0  # unified owner routing

    assert lifecycle.main(['complete', '--desk', str(root), '--task-key', A]) == 2
    completed = lifecycle.move_out(root, A, state='completed', approved=True)
    assert completed['archived_bytes_preserved'] is True
    assert desk.focus_desk(root, B)['task_count'] == 1
    hist = lifecycle.list_history(root)
    assert {s['state'] for s in hist['snapshots']} == {'revisions', 'completed'}
    assert lifecycle.reopen(root, A, state='completed', approved=True)['status'] == 'OWN_TASK_REOPENED'
    assert desk.focus_desk(root, A, show_selected_action=True)['selected_next_action'] == 'Share the summary.'
    assert lifecycle.list_history(root)['count'] == 2  # completion evidence remains immutable
    assert lifecycle.main(['reopen', '--desk', str(root), '--task-key', A, '--yes']) == 2

    # Archive an unrelated active task and reopen it without changing A.
    assert lifecycle.move_out(root, B, state='archived', approved=True)['status'] == 'OWN_TASK_ARCHIVED'
    assert desk.focus_desk(root, A)['task_count'] == 1
    assert lifecycle.reopen(root, B, state='archived', approved=True)['status'] == 'OWN_TASK_REOPENED'
    assert desk.focus_desk(root, B, show_selected_action=True)['selected_next_action'] == 'Collect one source.'
    assert lifecycle.list_history(root)['count'] == 3

    # Tamper with an archived revision; any history operation must refuse, not skip it.
    snaps = lifecycle.list_history(root)['snapshots']
    revision = next(x for x in snaps if x['state'] == 'revisions')
    archived = root / 'Vres-Lifecycle-History' / 'revisions' / lifecycle._archive_name(A, revision['sha256'])
    previous = archived / 'notes' / 'next-step.md'
    original_previous = previous.read_bytes()
    previous.write_bytes(b'## Next action\n- FORGED\n')
    try:
        assert lifecycle.main(['history', '--desk', str(root)]) == 2
        assert lifecycle.main(['complete', '--desk', str(root), '--task-key', A, '--yes']) == 2
        assert desk.focus_desk(root, A)['task_count'] == 2  # active notes unchanged
    finally:
        previous.write_bytes(original_previous)
    assert lifecycle.list_history(root)['count'] == 3
    assert {p: p.read_bytes() for p in originals} == originals
    assert untouched.read_bytes() == b'preserve this unrelated user-owned neighbor'
    assert (root / ('Vres-Workbench-' + A)).exists()
    assert (root / ('Vres-Workbench-' + B)).exists()


def test_original_revision_requires_exact_preimage_and_replacement_before_write(tmp_path, monkeypatch):
    """Synthetic scratch only; expected digests fail closed before staging."""
    import pytest
    root = tmp_path / 'Vres-Desk-Digest-Bound-Revision'
    inputs = tmp_path / 'explicit-inputs'
    inputs.mkdir()
    prior = inputs / 'original.md'
    updated = inputs / 'replacement.md'
    prior.write_text('# Day\n\n## Next action\n- Plan the day.\n', encoding='utf-8')
    updated.write_text('# Day\n\n## Next action\n- Check the results.\n', encoding='utf-8')
    desk.init_desk(root, approved=True)
    old = desk.add_task(root, A, prior, approved=True)
    next_digest = hashlib.sha256(updated.read_bytes()).hexdigest()
    for old_digest, new_digest in (
            ('f' * 64, next_digest), (old['sha256'], 'e' * 64),
            ('INVALID', next_digest), (old['sha256'], 'INVALID')):
        with pytest.raises(lifecycle.LifecycleRefused):
            lifecycle.revise(root, A, updated, approved=True,
                             expected_sha256=old_digest,
                             expected_new_sha256=new_digest)
        assert lifecycle.list_history(root)['count'] == 0
        assert desk.open_task(root, A)['sha256'] == old['sha256']
    # A recovered/abandoned original pending revision blocks new writes.
    original_attention = lifecycle.inspect_pending_revision_attention
    monkeypatch.setattr(lifecycle, 'inspect_pending_revision_attention',
                        lambda value: {'manual_revision_recovery_attention_required': True})
    with pytest.raises(lifecycle.LifecycleRefused, match='manual'):
        lifecycle.revise(root, A, updated, approved=True,
                         expected_sha256=old['sha256'], expected_new_sha256=next_digest)
    monkeypatch.setattr(lifecycle, 'inspect_pending_revision_attention', original_attention)
    changed = lifecycle.revise(root, A, updated, approved=True,
                               expected_sha256=old['sha256'],
                               expected_new_sha256=next_digest)
    assert changed['status'] == 'OWN_TASK_REVISED'
    assert changed['previous_sha256'] == old['sha256']
    assert changed['sha256'] == next_digest
    assert changed['previous_snapshot_preserved'] is True
    history = lifecycle.list_history(root)
    assert history['count'] == 1
    assert history['snapshots'][0]['state'] == 'revisions'
    assert history['snapshots'][0]['sha256'] == old['sha256']
    assert prior.read_text(encoding='utf-8').endswith('Plan the day.\n')


def test_interrupted_original_revision_blocks_completion_and_reopen(tmp_path):
    """One synthetic scratch: no mutation while staged revision needs manual review."""
    root = tmp_path / 'Vres-Desk-Recovery-Hold'
    inputs = tmp_path / 'inputs'
    inputs.mkdir()
    note = inputs / 'only.md'
    note.write_text('# Task\n\n## Next action\n- Inspect results.\n', encoding='utf-8')
    desk.init_desk(root, approved=True)
    created = desk.add_task(root, A, note, approved=True)
    pending = root / 'Vres-Lifecycle-History' / 'pending' / 'Vres-Workbench-Ptest'
    pending.mkdir(parents=True)
    attention = lifecycle.inspect_pending_revision_attention(root)
    assert attention['manual_recovery_attention_required'] is True
    with pytest.raises(lifecycle.LifecycleRefused, match='manual'):
        lifecycle.move_out(root, A, state='completed', approved=True)
    assert desk.open_task(root, A)['sha256'] == created['sha256']
    pending.rmdir()  # synthetic human-controlled test fixture only
    completed = lifecycle.move_out(root, A, state='completed', approved=True)
    assert completed['sha256'] == created['sha256']
    pending.mkdir()
    with pytest.raises(lifecycle.LifecycleRefused, match='manual'):
        lifecycle.reopen(root, A, state='completed', approved=True)
    assert not (root / ('Vres-Workbench-' + A)).exists()
    assert lifecycle.list_history(root)['count'] == 1


def test_pending_revision_appearing_late_blocks_original_final_move(tmp_path, monkeypatch):
    """Cooperative second pre-move read is a guard, not an atomic transaction."""
    root = tmp_path / 'Vres-Desk-Late-Recovery-Hold'
    inputs = tmp_path / 'inputs'
    inputs.mkdir()
    note = inputs / 'only.md'
    note.write_text('# Task\n\n## Next action\n- Inspect results.\n', encoding='utf-8')
    desk.init_desk(root, approved=True)
    initial = desk.add_task(root, A, note, approved=True)
    reads = []
    def attention(_root):
        reads.append(len(reads))
        pending = len(reads) >= 2
        return {'schema': lifecycle.SCHEMA,
                'status': 'READ_ONLY_PENDING_REVISION_ATTENTION',
                'pending_revision_staging_present': pending,
                'manual_recovery_attention_required': pending,
                'pending_contents_opened': False,
                'automatic_recovery_performed': False,
                'writes_performed': False}
    monkeypatch.setattr(lifecycle, 'inspect_pending_revision_attention', attention)
    with pytest.raises(lifecycle.LifecycleRefused, match='manual'):
        lifecycle.move_out(root, A, state='completed', approved=True,
                           expected_sha256=initial['sha256'])
    assert len(reads) == 2
    assert desk.open_task(root, A)['sha256'] == initial['sha256']
