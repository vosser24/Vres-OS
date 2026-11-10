"""Exact-context result metadata in original task lifecycle; synthetic only."""
from __future__ import annotations

import hashlib
import json

import pytest

from vres_os import personal_desk_cli as cli
from vres_os import personal_portable_desk as desk
from vres_os import personal_task_lifecycle as lifecycle
from vres_os import personal_work_completion as completion
from vres_os import personal_work_result as result


def _selected(tmp_path):
    personal = tmp_path / 'Vres-Desk-Result-History'
    personal.mkdir()
    project = tmp_path / 'Project'
    project.mkdir()
    note = tmp_path / 'task.md'
    note.write_text('# Report\n\n## Next action\n- Prepare the report.\n', encoding='utf-8')
    desk.add_task(personal, 'TASK-WORK-HISTORY', note, approved=True)
    document = project / 'report.md'
    document.write_text('# Output\n\nUser wrote this example.\n', encoding='utf-8')
    args = (personal, 'TASK-WORK-HISTORY', project, 'project:history', document)
    first = result.inspect_work_result(*args)
    return args, first


def _done(args, first):
    return completion.finish_work(*args,
        expected_checkpoint_sha256=first['checkpoint_sha256'], approved=True)


def test_completed_work_persists_original_result_link_and_exact_token(tmp_path):
    args, first = _selected(tmp_path)
    personal, task, project, key, document = args
    before_doc = document.read_bytes()
    receipt_sha = first['work_brief']['scratch_handoff']['selected_note_sha256']
    output = _done(args, first)
    assert output['status'] == 'USER_CONFIRMED_SCRATCH_WORK_RESULT_COMPLETED'
    assert output['checkpoint_persisted'] is True
    assert output['document_to_history_link_persisted'] is True
    assert output['new_task_or_evidence_store_created'] is False
    assert output['history_result_current_bytes_verified'] is False
    assert lifecycle.read_daily_review(personal)['completed_count'] == 1
    history = lifecycle.list_history(personal)
    assert len(history['snapshots']) == 1
    snapshot = history['snapshots'][0]
    assert snapshot['sha256'] == receipt_sha
    evidence = snapshot['result_evidence']
    assert evidence['checkpoint_sha256'] == first['checkpoint_sha256']
    assert evidence['result_sha256'] == hashlib.sha256(before_doc).hexdigest()
    assert evidence['document_path_hidden'] is True
    assert evidence['document_current_bytes_verified'] is False
    assert 'result_file' not in evidence and str(project) not in json.dumps(history)
    explicit = lifecycle.list_history(personal, show_result_paths=True)
    shown = explicit['snapshots'][0]['result_evidence']
    assert shown['result_file'] == str(document)
    assert shown['project_root'] == str(project)
    assert shown['relative_result_path'] == 'report.md'
    assert document.read_bytes() == before_doc
    # Original archived note remains the identical two-file exact receipt.
    saved = personal/'Vres-Lifecycle-History'/'completed'/lifecycle._archive_name(task,receipt_sha)
    assert {p.name for p in saved.iterdir()} == {'notes','draft-receipt.json'}
    assert saved.joinpath('draft-receipt.json').is_file()
    assert len(list((personal/'Vres-Lifecycle-History'/'completed').iterdir())) == 2


def test_history_cli_paths_require_explicit_opt_in(tmp_path,capsys):
    args, first = _selected(tmp_path)
    personal,task,project,key,document=args
    _done(args,first)
    assert cli.main(['desk','history','--desk',str(personal)]) == 0
    hidden=json.loads(capsys.readouterr().out)
    assert str(project) not in json.dumps(hidden)
    assert hidden['snapshots'][0]['result_evidence']['document_path_hidden'] is True
    assert cli.main(['desk','history','--desk',str(personal),'--show-result-paths']) == 0
    shown=json.loads(capsys.readouterr().out)
    assert shown['snapshots'][0]['result_evidence']['result_file'] == str(document)


def test_reopened_task_replays_from_history_without_manually_saving_token(tmp_path):
    args, first = _selected(tmp_path)
    personal,task,project,key,document=args
    _done(args,first)
    entry=lifecycle.list_history(personal,show_result_paths=True)['snapshots'][0]
    info=entry['result_evidence']
    re=lifecycle.reopen(personal, task, state='completed',
                        expected_sha256=entry['sha256'], approved=True)
    assert re['status']=='OWN_TASK_REOPENED'
    replay=result.inspect_work_result(personal,task,info['project_root'],
                                     info['project_key'],info['result_file'],
                                     expected_checkpoint_sha256=info['checkpoint_sha256'])
    assert replay['status']=='RESULT_EXACT_CONTEXT_CHECKPOINT_MATCH'
    assert lifecycle.list_history(personal)['count']==1


def test_changed_result_does_not_make_history_claim_current_document(tmp_path):
    args, first = _selected(tmp_path)
    personal,task,project,key,document=args
    _done(args,first)
    document.write_text('Changed after confirmation',encoding='utf-8')
    entry=lifecycle.list_history(personal,show_result_paths=True)['snapshots'][0]
    assert entry['result_evidence']['document_current_bytes_verified'] is False
    lifecycle.reopen(personal,task,expected_sha256=entry['sha256'],approved=True)
    with pytest.raises(result.WorkResultRefused):
        result.inspect_work_result(*args,expected_checkpoint_sha256=entry['result_evidence']['checkpoint_sha256'])


def test_prior_completed_history_without_link_remains_compatible(tmp_path):
    args, first=_selected(tmp_path)
    personal,task,*_=args
    note_sha=first['work_brief']['scratch_handoff']['selected_note_sha256']
    done=lifecycle.move_out(personal,task,state='completed',approved=True,
                             expected_sha256=note_sha)
    assert done['status']=='OWN_TASK_COMPLETED'
    old=lifecycle.list_history(personal)
    assert old['count']==1 and 'result_evidence' not in old['snapshots'][0]
    assert lifecycle.read_daily_review(personal)['completed_count']==1
    assert lifecycle.reopen(personal,task,expected_sha256=note_sha,
                            approved=True)['status']=='OWN_TASK_REOPENED'


def test_bad_sidecar_refuses_history_and_reopen(tmp_path):
    args,first=_selected(tmp_path)
    personal,task,*_=args
    _done(args,first)
    note_sha=first['work_brief']['scratch_handoff']['selected_note_sha256']
    path=personal/'Vres-Lifecycle-History'/'completed'/lifecycle._result_name(task,note_sha)
    old=path.read_bytes()
    path.write_bytes(old[:-1]+b' ') # raw noncanonical, never silently trusted
    with pytest.raises(lifecycle.LifecycleRefused):
        lifecycle.list_history(personal)
    with pytest.raises(lifecycle.LifecycleRefused):
        lifecycle.reopen(personal,task,expected_sha256=note_sha,approved=True)


def test_orphan_result_link_refused(tmp_path):
    args,first=_selected(tmp_path)
    personal,task,*_=args
    _done(args,first)
    note_sha=first['work_brief']['scratch_handoff']['selected_note_sha256']
    folder=personal/'Vres-Lifecycle-History'/'completed'
    old=folder/lifecycle._archive_name(task,note_sha)
    orphan=folder/('Vres-Workbench-H'+'0'*64)
    old.rename(orphan)
    with pytest.raises(lifecycle.LifecycleRefused):
        lifecycle.list_history(personal)


def test_invalid_expected_replay_and_no_yes_do_not_complete(tmp_path):
    args,first=_selected(tmp_path)
    personal,task,*_=args
    with pytest.raises(completion.WorkCompletionRefused):
        completion.finish_work(*args,expected_checkpoint_sha256=first['checkpoint_sha256'])
    with pytest.raises(completion.WorkCompletionRefused):
        completion.finish_work(*args,expected_checkpoint_sha256='0'*64,approved=True)
    assert lifecycle.read_daily_review(personal)['active_count']==1
    assert lifecycle.list_history(personal)['count']==0


def test_result_change_after_history_move_reports_uncertain_not_success(tmp_path,monkeypatch):
    args,first=_selected(tmp_path)
    personal,task,project,key,document=args
    real=result._read_digest
    reads=0
    def changed_on_last_digest(path):
        nonlocal reads
        reads+=1
        if reads==2:
            document.write_text('changed during completion',encoding='utf-8')
        return real(path)
    monkeypatch.setattr(result,'_read_digest',changed_on_last_digest)
    with pytest.raises(completion.WorkCompletionRefused):
        _done(args,first)
    # The move already happened. No falsely successful link was persisted.
    assert reads==2
    assert lifecycle.read_daily_review(personal)['active_count']==0
    assert lifecycle.list_history(personal)['count']==1
    assert all('result_evidence' not in x for x in lifecycle.list_history(personal)['snapshots'])


def test_double_completion_does_not_duplicate_sidecar(tmp_path):
    args,first=_selected(tmp_path)
    personal,task,*_=args
    _done(args,first)
    with pytest.raises(completion.WorkCompletionRefused):
        _done(args,first)
    history=lifecycle.list_history(personal)
    assert history['count']==1
    assert 'result_evidence' in history['snapshots'][0]
