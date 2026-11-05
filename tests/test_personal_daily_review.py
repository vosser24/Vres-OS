"""One integrated personal review from actual scratch notes and lifecycle history."""
from __future__ import annotations

import json

from vres_os import personal_desk_cli as cli
from vres_os import personal_offline_workbench as workbench
from vres_os import personal_portable_desk as desk
from vres_os import personal_task_lifecycle as lifecycle


def test_one_active_to_completed_personal_daily_review_read_only(tmp_path, capsys):
    root = tmp_path / 'Vres-Desk-DailyReview'
    original = tmp_path / 'TASK-DAY-01.md'
    original.write_text('# Weather task\n\n## Next action\n- Understand the weather today.\n',
                        encoding='utf-8')
    unrelated = tmp_path / 'UNRELATED.txt'
    unrelated.write_bytes(b'unchanged unrelated file')
    original_raw = original.read_bytes()

    assert desk.init_desk(root, approved=True)['tasks_created'] == 0
    added = desk.add_task(root, 'TASK-DAY-01', original, approved=True)
    active_note = root / 'Vres-Workbench-TASK-DAY-01' / 'notes' / 'next-step.md'
    receipt_path = root / 'Vres-Workbench-TASK-DAY-01' / 'draft-receipt.json'
    before_note, before_receipt = active_note.read_bytes(), receipt_path.read_bytes()

    assert cli.main(['desk', 'review', '--desk', str(root), '--format', 'json']) == 0
    active_view = json.loads(capsys.readouterr().out)
    assert active_view['status'] == 'READ_ONLY_PERSONAL_DAILY_REVIEW'
    assert active_view['active_count'] == 1 and active_view['completed_count'] == 0
    assert active_view['active_tasks'][0]['sha256'] == added['sha256']
    assert not active_view['writes_performed'] and not active_view['history_has_timestamps']
    assert 'next_action' not in json.dumps(active_view)
    assert active_note.read_bytes() == before_note and receipt_path.read_bytes() == before_receipt
    assert cli.main(['desk', 'review', '--desk', str(root), '--yes']) == 2
    capsys.readouterr()  # refusal has no data and cannot be a hidden approval

    completed = lifecycle.move_out(root, 'TASK-DAY-01', state='completed', approved=True)
    assert completed['status'] == 'OWN_TASK_COMPLETED'
    assert cli.main(['desk', 'review', '--desk', str(root)]) == 0
    report = capsys.readouterr().out
    assert 'Active tasks: 0' in report and 'Completed snapshots: 1' in report
    assert 'TASK-DAY-01' in report and 'not necessarily from today' in report
    assert 'Understand the weather' not in report
    assert cli.main(['desk', 'review', '--desk', str(root), '--format', 'json']) == 0
    completed_view = json.loads(capsys.readouterr().out)
    assert completed_view['active_count'] == 0
    assert completed_view['completed_count'] == 1
    assert completed_view['completed_snapshots'][0]['sha256'] == added['sha256']
    assert not completed_view['writes_performed']

    snapshots = lifecycle.list_history(root)['snapshots']
    assert len(snapshots) == 1 and snapshots[0]['state'] == 'completed'
    archived = root / 'Vres-Lifecycle-History' / 'completed' / lifecycle._archive_name(
        'TASK-DAY-01', added['sha256'])
    completed_note = archived / 'notes' / 'next-step.md'
    assert workbench.inspect_note(archived)['sha256'] == added['sha256']
    assert completed_note.read_bytes() == before_note
    assert original.read_bytes() == original_raw
    assert unrelated.read_bytes() == b'unchanged unrelated file'

    # Malformed completed history must refuse, not emit partial report.
    completed_note.write_bytes(b'TAMPERED')
    try:
        assert cli.main(['desk', 'review', '--desk', str(root)]) == 2
        assert not capsys.readouterr().out
    finally:
        completed_note.write_bytes(before_note)
    assert workbench.inspect_note(archived)['sha256'] == added['sha256']
    assert original.read_bytes() == original_raw
