"""P1 one end-to-end disposable personal daily journey: synthetic-only tests.

No installed package, user credentials, native Claude/hooks, PostgreSQL, or
real legacy project. Accepted parent API checks receive their own focused suites.
"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import hashlib
import inspect

import pytest

from vres_os import personal_disposable_daily_journey as journey
from vres_os.personal_disposable_daily_journey import (
    DisposableJourneyRefusal, preview_disposable_resume,
    render_disposable_daily_journey, run_disposable_daily_journey,
)


def test_one_integrated_personal_journey_yields_correct_honest_outcome():
    report = run_disposable_daily_journey()
    assert report['status'] == 'synthetic_disposable_journey_completed_not_installed'
    assert report['task']['selected_task_unambiguous'] is True
    assert report['task']['ambiguous_task_selection_refused'] is True
    assert report['task']['synthetic_checkpoint_reloaded'] is True
    assert report['task']['post_resume_next_action_unchanged'] is True
    assert report['deliverable']['logical_name'] == 'notes/next-step.md'
    assert report['deliverable']['staged_bytes_verified'] is True
    assert report['deliverable']['discarded_after_preview'] is True
    assert report['deliverable']['sha256'] == hashlib.sha256(journey._DRAFT).hexdigest()
    assert report['resource_metadata']['project_a_bound'] is True
    assert report['resource_metadata']['project_b_bound'] is True
    assert report['resource_metadata']['project_c_denied'] is True
    assert report['resource_metadata']['credential_value_read'] is False
    assert report['global_onboarding']['items_reviewed'] == 6
    assert report['global_onboarding']['pending_numbers'] == []
    assert report['global_onboarding']['real_activation_authorized'] is False
    assert report['global_onboarding']['simulated_global_interruption_recovered'] is True
    assert report['disposable_release_recovery']['exact_previous_managed_plugin_restored'] is True
    assert report['disposable_release_recovery']['pending_recovery_journal_removed_after_proof'] is True
    assert report['experience']['db_backed_retrieval_performed'] is False
    assert report['validation']['real_host_validation'] == 'NOT_RUN'
    assert all(report[key] is False for key in journey._DENIED)


def test_complete_accepted_owner_workflow_repeats_deterministically():
    assert run_disposable_daily_journey() == run_disposable_daily_journey()


def test_operator_facing_result_is_bounded_and_explicitly_non_authorizing():
    report = run_disposable_daily_journey()
    displayed = render_disposable_daily_journey(report)
    assert 'SYNTHETIC DAILY-USE WALKTHROUGH ONLY' in displayed
    assert 'Resource metadata: demo A/B bound, unbound C denied' in displayed
    assert 'real E6 PostgreSQL retrieval NOT RUN' in displayed
    assert 'not installed, validated by Fable, or daily-pilot approved' in displayed
    assert 'C:\\Users' not in displayed and '.credentials.json' not in displayed
    assert 'SYNTHETIC-OPAQUE-NATIVE' not in displayed
    assert len(displayed) <= 3200


@pytest.mark.parametrize('project,task', [
    ('project:' + 'b'*24, journey._TASK),
    (journey._PROJECT, 'TASK-OTHER-DEMO'),
    (journey._PROJECT, ''),
    (journey._PROJECT, 'TASK-REAL-WORK'),
    (journey._PROJECT, None),
    (None, journey._TASK),
    ('C:\\Users\\User\\project', journey._TASK),
])
def test_unauthorized_project_or_wrong_task_refused_before_temp_io(project, task, monkeypatch):
    def forbidden_temp(*_args, **_kwargs):
        raise AssertionError('Should refuse before creating a directory')
    monkeypatch.setattr(journey.tempfile, 'TemporaryDirectory', forbidden_temp)
    with pytest.raises(DisposableJourneyRefusal):
        run_disposable_daily_journey(selected_project=project, selected_task=task)


@pytest.mark.parametrize('altered', [
    lambda raw: raw + b' ',
    lambda raw: raw.replace(b'TASK-DEMO-CHECKLIST-01', b'TASK-OTHER-DEMO'),
    lambda raw: raw.replace(b'"not_required"', b'"passed"'),
    lambda raw: b'{}',
    lambda raw: None,
])
def test_disposable_checkpoint_mutation_does_not_resume_wrong_work(altered):
    digest = hashlib.sha256(journey._DRAFT).hexdigest()
    original = journey._json_bytes(journey._checkpoint_for(digest))
    with pytest.raises(DisposableJourneyRefusal):
        preview_disposable_resume(altered(original), draft_sha256=digest)
    assert 'Task: ' + journey._TASK in preview_disposable_resume(original, draft_sha256=digest)


def test_wrong_checkpoint_binding_denied_even_when_checkpoint_bytes_unchanged():
    digest = hashlib.sha256(journey._DRAFT).hexdigest()
    raw = journey._json_bytes(journey._checkpoint_for(digest))
    with pytest.raises(DisposableJourneyRefusal):
        preview_disposable_resume(raw, draft_sha256='f'*64)
    with pytest.raises(DisposableJourneyRefusal):
        preview_disposable_resume(raw, draft_sha256=digest, selected_task='TASK-OTHER-DEMO')
    with pytest.raises(DisposableJourneyRefusal):
        preview_disposable_resume(raw, draft_sha256=digest, selected_project='project:' + 'c'*24)


def test_disposable_fixture_temporary_roots_are_cleaned_after_return(monkeypatch):
    real = journey.tempfile.TemporaryDirectory
    seen = []
    def guarded(*args, **kwargs):
        entry = real(*args, **kwargs)
        seen.append(Path(entry.name))
        return entry
    monkeypatch.setattr(journey.tempfile, 'TemporaryDirectory', guarded)
    report = run_disposable_daily_journey()
    assert report['status'].startswith('synthetic_disposable')
    assert seen and all(not path.exists() for path in seen)


def test_release_recovery_refusal_does_not_leak_into_installed_system(monkeypatch):
    real = journey.tempfile.TemporaryDirectory
    roots = []
    def guarded(*args, **kwargs):
        entry = real(*args, **kwargs)
        roots.append(Path(entry.name))
        return entry
    monkeypatch.setattr(journey.tempfile, 'TemporaryDirectory', guarded)
    def refuse(*args, **kwargs):
        raise journey.install_recovery.InstallRecoveryError('test injected stop')
    monkeypatch.setattr(journey.install_recovery, 'recover', refuse)
    with pytest.raises(journey.install_recovery.InstallRecoveryError):
        run_disposable_daily_journey()
    assert roots and all(not path.exists() for path in roots)


def test_a_forged_positive_authority_cannot_pass_the_operator_renderer():
    original = run_disposable_daily_journey()
    for key in journey._DENIED:
        forged = deepcopy(original)
        forged[key] = True
        with pytest.raises(DisposableJourneyRefusal):
            render_disposable_daily_journey(forged)


def test_missing_integration_proof_does_not_render_as_success():
    original = run_disposable_daily_journey()
    for key in ('task', 'deliverable', 'resource_metadata', 'global_onboarding',
                'disposable_release_recovery', 'experience', 'validation'):
        incomplete = deepcopy(original)
        incomplete.pop(key)
        with pytest.raises(DisposableJourneyRefusal):
            render_disposable_daily_journey(incomplete)


def test_module_does_not_own_a_second_task_store_model_or_credential_engine():
    source = inspect.getsource(journey)
    for forbidden in ('psycopg', 'from .experience_retrieval import',
                      'from .credential_broker import', 'requests',
                      'subprocess.', 'os.environ', 'CLAUDE_CONFIG_DIR',
                      'connect(', 'SecretStore(', 'sqlite3', 'load_dotenv'):
        assert forbidden not in source
    assert 'render_personal_resume_briefing' in source
    assert 'PersonalDataSources(' in source
    assert 'install_recovery.recover(' in source
    assert 'begin_synthetic_migration_dry_run(' in source


def test_nested_forged_positive_evidence_does_not_render_as_success():
    original = run_disposable_daily_journey()
    mutations = [
        ('task','ambiguous_task_selection_refused',False),
        ('task','task_key','TASK-OTHER-DEMO'),
        ('deliverable','discarded_after_preview',False),
        ('deliverable','sha256','0'*64),
        ('resource_metadata','project_c_denied',False),
        ('resource_metadata','project_b_bound',False),
        ('resource_metadata','credential_value_read',True),
        ('global_onboarding','real_activation_authorized',True),
        ('global_onboarding','pending_numbers',[2]),
        ('disposable_release_recovery','pending_recovery_journal_removed_after_proof',False),
        ('disposable_release_recovery','exact_previous_managed_plugin_restored',False),
        ('experience','db_backed_retrieval_performed',True),
        ('validation','installed_release_validation','PASS'),
    ]
    for section, key, value in mutations:
        forged = deepcopy(original)
        forged[section][key] = value
        with pytest.raises(DisposableJourneyRefusal):
            render_disposable_daily_journey(forged)
