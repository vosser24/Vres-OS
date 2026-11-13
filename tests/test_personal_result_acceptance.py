"""Original #165 Chairman result-quality self-review: source-only synthetic UAT.

These tests exercise the actual existing task/result/CLI/completion owners; never
claim real user authentication, independent quality validation or #176 reuse.
"""
from __future__ import annotations

import hashlib
import json

import pytest

from vres_os import personal_desk_cli as cli
from vres_os import personal_portable_desk as desk_owner
from vres_os import personal_task_lifecycle as lifecycle
from vres_os import personal_work_result as result_owner
from vres_os import personal_work_completion as completion_owner
from vres_os import personal_work_session as session
from vres_os import personal_result_acceptance as acceptance


def _scratch(tmp_path):
    desk = tmp_path / 'Vres-Desk-Result-Review'
    desk.mkdir()
    project = tmp_path / 'OrdinaryProject'
    project.mkdir()
    note = tmp_path / 'task.md'
    note.write_text('# Task\n\n## Next action\n- Prepare report.\n', encoding='utf-8')
    task = 'TASK-ACCEPT-REPORT'
    desk_owner.add_task(desk, task, note, approved=True)
    document = project / 'report.md'
    document.write_text('# Report\n\nNonsensitive synthetic example.\n', encoding='utf-8')
    ctx = (desk, task, project, 'project:' + 'a' * 24, document)
    checkpoint = result_owner.inspect_work_result(*ctx)['checkpoint_sha256']
    proposed = session.propose_chairman_turn(desk)
    item = next(i for i in proposed['choices'] if i['kind'] == 'ACTIVE_TASK')
    options = dict(proposal_sha256=proposed['proposal_sha256'], task=task,
                   selected_note_sha256=item['selected_note_sha256'], approved=True,
                   project_root=project, project_key=ctx[3],
                   result_file=document, expected_checkpoint_sha256=checkpoint)
    baseline = session.select_chairman_turn(desk, **options)
    return ctx, options, baseline['selected_task_result_continuity']


def _fixture(ctx, receipt, states=('CLAIMED_MET', 'UNREVIEWED')):
    rows = []
    for i, status in enumerate(states, 1):
        rows.append(dict(id=f'C{i:02d}', criterion=f'Review criterion {i}: inspect report',
                         status=status, evidence_sha256=('1' * 64 if status != 'UNREVIEWED' else None)))
    data = {
        'schema': acceptance.SCHEMA,
        'selected_task_key': ctx[1],
        'selected_note_sha256': receipt['selected_note_sha256'],
        'selected_project_binding_sha256': receipt['selected_project_binding_sha256'],
        'selected_result_sha256': receipt['selected_result_sha256'],
        'selected_result_checkpoint_sha256': receipt['selected_result_checkpoint_sha256'],
        'selected_continuity_receipt_sha256': receipt['continuity_receipt_sha256'],
        'criteria': rows,
    }
    raw = json.dumps(data, ensure_ascii=False, sort_keys=True).encode('utf-8')
    return data, raw, hashlib.sha256(raw).hexdigest()


def _select(ctx, options, raw, sha):
    return session.select_chairman_turn(
        ctx[0], **options, include_result_acceptance_evidence=True,
        acceptance_evidence_document=raw,
        expected_acceptance_evidence_sha256=sha)


def test_self_claimed_met_is_redacted_not_accepted_or_completed(tmp_path):
    ctx, options, receipt = _scratch(tmp_path)
    data, raw, sha = _fixture(ctx, receipt, ('CLAIMED_MET', 'CLAIMED_MET'))
    first = _select(ctx, options, raw, sha)
    second = _select(ctx, options, raw, sha)
    review = first['selected_result_acceptance_evidence']
    assert review['acceptance_claims_state'] == 'ALL_SELF_CLAIMED_MET_NOT_VALIDATED'
    assert review['review_receipt_sha256'] == second[
        'selected_result_acceptance_evidence']['review_receipt_sha256']
    assert review['claimed_met_count'] == 2
    assert review['claims_independently_validated'] is False
    assert review['task_completion_approved_or_performed'] is False
    assert review['original_176_experience_eligible_or_promoted'] is False
    assert first['selected_task_result_continuity'] == receipt
    assert 'Review criterion' not in json.dumps(first)
    assert str(ctx[2]) not in json.dumps(first)
    assert lifecycle.list_history(ctx[0])['count'] == 0


def test_unresolved_ids_differ_from_unvalidated_self_claims(tmp_path):
    ctx, options, receipt = _scratch(tmp_path)
    _, raw, sha = _fixture(ctx, receipt, ('CLAIMED_MET', 'CLAIMED_GAP', 'UNREVIEWED'))
    report = _select(ctx, options, raw, sha)['selected_result_acceptance_evidence']
    assert report['claimed_met_count'] == 1
    assert report['claimed_gap_count'] == 1
    assert report['unreviewed_count'] == 1
    assert report['unresolved_criterion_ids'] == ['C02', 'C03']
    assert 'separately decide' in report['next_safe_step']
    assert lifecycle.list_history(ctx[0])['count'] == 0


def test_unselected_or_stale_acceptance_refused_without_mutation(tmp_path):
    ctx, options, receipt = _scratch(tmp_path)
    _, raw, sha = _fixture(ctx, receipt)
    with pytest.raises(session.WorkSessionRefused):
        session.select_chairman_turn(ctx[0], **options,
                                     acceptance_evidence_document=raw,
                                     expected_acceptance_evidence_sha256=sha)
    with pytest.raises(session.WorkSessionRefused):
        _select(ctx, options, raw, '0' * 64)
    ctx[4].write_text('# Modified after checkpoint\n', encoding='utf-8')
    with pytest.raises((session.WorkSessionRefused, result_owner.WorkResultRefused)):
        _select(ctx, options, raw, sha)
    assert lifecycle.list_history(ctx[0])['count'] == 0


def test_mismatched_result_and_forged_authority_not_trusted(tmp_path):
    ctx, options, receipt = _scratch(tmp_path)
    data, raw, sha = _fixture(ctx, receipt)
    for altered in ({**data, 'selected_result_sha256': '2' * 64},
                    {**data, 'task_completion_approved': True},
                    {**data, 'criteria': [
                        dict(id='C01', criterion='Claimed passed',
                             status='CLAIMED_MET', evidence_sha256=None)]}):
        blob = json.dumps(altered, sort_keys=True).encode()
        with pytest.raises(session.WorkSessionRefused):
            _select(ctx, options, blob, hashlib.sha256(blob).hexdigest())
    assert lifecycle.list_history(ctx[0])['count'] == 0


def test_late_result_change_after_acceptance_read_refused(tmp_path, monkeypatch):
    ctx, options, receipt = _scratch(tmp_path)
    _, raw, sha = _fixture(ctx, receipt)
    original = acceptance.review_selected_result_acceptance
    def change_result(*args, **kwargs):
        review = original(*args, **kwargs)
        ctx[4].write_text('# Late change after acceptance parsing\n', encoding='utf-8')
        return review
    monkeypatch.setattr(acceptance, 'review_selected_result_acceptance', change_result)
    with pytest.raises((session.WorkSessionRefused, result_owner.WorkResultRefused)):
        _select(ctx, options, raw, sha)
    assert lifecycle.list_history(ctx[0])['count'] == 0


def test_original_completion_is_a_separate_explicit_decision(tmp_path):
    ctx, options, receipt = _scratch(tmp_path)
    _, raw, sha = _fixture(ctx, receipt, ('CLAIMED_MET',))
    reviewed = _select(ctx, options, raw, sha)
    assert reviewed['automatic_task_reopen_or_completion'] is False
    with pytest.raises(completion_owner.WorkCompletionRefused):
        completion_owner.finish_work(
            *ctx, expected_checkpoint_sha256=options['expected_checkpoint_sha256'])
    assert lifecycle.list_history(ctx[0])['count'] == 0
    completed = completion_owner.finish_work(
        *ctx, expected_checkpoint_sha256=options['expected_checkpoint_sha256'],
        approved=True)
    assert completed['user_confirmed_scratch_completion'] is True
    assert completed['result_quality_validated'] is False
    assert lifecycle.list_history(ctx[0])['count'] == 1


def test_saved_historical_result_cannot_mint_new_acceptance(tmp_path):
    ctx, options, receipt = _scratch(tmp_path)
    _, raw, sha = _fixture(ctx, receipt)
    completion_owner.finish_work(*ctx,
         expected_checkpoint_sha256=options['expected_checkpoint_sha256'], approved=True)
    old = session.propose_chairman_turn(ctx[0])
    saved = next(i for i in old['choices'] if i['kind'] == 'SAVED_COMPLETED_RESULT')
    with pytest.raises(session.WorkSessionRefused):
        session.select_chairman_turn(ctx[0],
            proposal_sha256=old['proposal_sha256'], task=ctx[1],
            selected_note_sha256=saved['selected_note_sha256'],
            kind='SAVED_COMPLETED_RESULT', approved=True,
            include_result_acceptance_evidence=True,
            acceptance_evidence_document=raw,
            expected_acceptance_evidence_sha256=sha)


def test_existing_cli_accepts_only_selected_desk_fixture_and_redacts(tmp_path, capsys):
    ctx, options, receipt = _scratch(tmp_path)
    _, raw, sha = _fixture(ctx, receipt)
    fixture = ctx[0] / 'result-acceptance-evidence.json'
    fixture.write_bytes(raw)
    base = ['work-session', 'select', '--desk', str(ctx[0]),
            '--task-key', ctx[1], '--proposal-sha256', options['proposal_sha256'],
            '--selected-note-sha256', options['selected_note_sha256'],
            '--project-root', str(ctx[2]), '--project-key', ctx[3],
            '--result-file', str(ctx[4]),
            '--expected-checkpoint-sha256', options['expected_checkpoint_sha256'], '--yes']
    chosen = ['--include-result-acceptance-evidence',
              '--result-acceptance-evidence-file', str(fixture),
              '--expected-result-acceptance-evidence-sha256', sha]
    assert cli.main(base + chosen) == 0
    packet = json.loads(capsys.readouterr().out)
    assert packet['selected_result_acceptance_evidence']['status'] == (
        'CALLER_SUPPLIED_RESULT_ACCEPTANCE_REVIEW_HELD')
    assert str(ctx[0]) not in json.dumps(packet)
    assert str(ctx[2]) not in json.dumps(packet)
    assert lifecycle.list_history(ctx[0])['count'] == 0
    outside = tmp_path / 'result-acceptance-evidence.json'
    outside.write_bytes(raw)
    bad = chosen.copy()
    bad[2] = str(outside)
    assert cli.main(base + bad) == 2
    capsys.readouterr()
    assert cli.main(base + chosen[1:]) == 2


def test_legacy_architecture_source_owners_preserved_during_acceptance(tmp_path):
    ctx, options, receipt = _scratch(tmp_path)
    _, raw, sha = _fixture(ctx, receipt, ('CLAIMED_MET',))
    options['include_architecture_experience_decision_support'] = True
    initial = session.select_chairman_turn(ctx[0], **options)
    arch = initial['selected_architecture_experience_decision_support']
    # The evidence document must bind the same original continuity including
    # the selected original #174 audit digest, not the previous no-audit one.
    _, updated_raw, updated_sha = _fixture(
        ctx, initial['selected_task_result_continuity'], ('CLAIMED_MET',))
    result = _select(ctx, options, updated_raw, updated_sha)
    assert result['selected_architecture_experience_decision_support'] == arch
    assert result['selected_result_acceptance_evidence']['original_174_fable_high_authority_granted'] is False
    assert result['selected_result_acceptance_evidence']['original_176_live_trust_scope_revocation_checked'] is False
    assert result['selected_task_result_continuity']['architecture_decision_sha256'] == arch['decision_context_sha256']
    with pytest.raises(session.WorkSessionRefused):
        _select(ctx, options, raw, sha)  # old no-architecture receipt is stale
