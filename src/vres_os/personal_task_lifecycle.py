"""Personal portable desk task revision/completion/archive/reopen, source only.

Keeps the accepted scratch-note and exact SHA-256 receipt format: completed,
archived and previous revisions are ordinary, verified workbench folders in one
hidden subdirectory of the explicitly selected Vres-Desk-* parent. No second
store, database, installed application or project/profile discovery.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import secrets
import sys
import unicodedata
from itertools import islice
from pathlib import Path, PurePosixPath
from typing import Any, Sequence

if not __package__:
    sys.path.insert(0, str(Path(__file__).absolute().parent.parent))
    from vres_os import personal_offline_workbench as workbench
    from vres_os import personal_portable_desk as desk
    from vres_os import personal_project_task_draft as draft
    from vres_os import personal_task_continuity as continuity
else:
    from . import personal_offline_workbench as workbench
    from . import personal_portable_desk as desk
    from . import personal_project_task_draft as draft
    from . import personal_task_continuity as continuity

SCHEMA = 'vres-personal-task-lifecycle/1'
_HISTORY = 'Vres-Lifecycle-History'
_BUCKETS = ('revisions', 'completed', 'archived', 'pending')
_STATES = ('completed', 'archived')
_MAX_HISTORY_ENTRIES = 48
_RESULT_LINK_SCHEMA = 'vres-personal-result-history-link/1'
_RESULT_LINK_CHAIRMAN_SCHEMA = 'vres-personal-result-history-link/2'
_CHAIRMAN_SOURCE_KEYS = frozenset({
    'source_link_sha256', 'history_sha256', 'latest_proposal_sha256',
    'template_sha256', 'rendered_candidate_sha256', 'requested_family',
    'requested_effort', 'host_evidence_status',
})
_RESULT_NAME = re.compile(r'Vres-Result-H[a-f0-9]{64}\.json\Z', re.ASCII)
_PROJECT_KEY = re.compile(r'project:[A-Za-z0-9][A-Za-z0-9_.:-]{0,95}\Z', re.ASCII)
_RESULT_TYPES = frozenset(('.md', '.txt', '.py', '.json', '.csv',
                           '.pdf', '.docx', '.xlsx', '.pptx'))
_MAX_RESULT_LINK_BYTES = 4096


class LifecycleRefused(ValueError):
    """Fail closed before changing any ambiguous or altered scratch note."""


class _SafeParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise LifecycleRefused('Invalid lifecycle CLI arguments')


def _root(value: str | Path) -> Path:
    return desk._desk(value, must_exist=True)


def _active(root: Path, key: str) -> tuple[Path, dict[str, Any]]:
    folder = desk._owned_task(root, key)
    receipt = workbench.inspect_note(folder)
    if receipt['task_key_claimed'] != key:
        raise LifecycleRefused('Wrong task receipt')
    return folder, receipt


def _history(root: Path, *, create: bool) -> Path | None:
    hist = root / _HISTORY
    if workbench._stat(hist) is None:
        if not create:
            return None
        hist.mkdir(mode=0o700)
    workbench._plain(hist, directory=True)
    entries = {p.name for p in islice(hist.iterdir(), len(_BUCKETS) + 2)}
    if entries.difference(_BUCKETS):
        raise LifecycleRefused('Unexpected history folder entries')
    for bucket in _BUCKETS:
        path = hist / bucket
        if workbench._stat(path) is None:
            if create:
                path.mkdir(mode=0o700)
        else:
            workbench._plain(path, directory=True)
    return hist


def _archive_name(key: str, sha: str) -> str:
    # Exact 80-character owned workspace name. A digest of both task identity
    # and note digest avoids aliasing different tasks containing the same note.
    ident = hashlib.sha256(key.encode('ascii') + b'\0' + bytes.fromhex(sha)).hexdigest()
    return 'Vres-Workbench-H' + ident


def _result_name(key: str, note_sha: str) -> str:
    return 'Vres-Result-H' + _archive_name(key, note_sha)[len('Vres-Workbench-H'):] + '.json'


def _result_bytes(record: dict[str, Any]) -> bytes:
    """Canonical bounded history metadata, not a current-document or task approval."""
    keys = {'schema', 'task_key_claimed', 'selected_note_sha256',
            'project_key', 'project_root', 'relative_result_path',
            'project_binding_sha256', 'result_sha256', 'result_bytes',
            'checkpoint_sha256', 'result_contents_disclosed',
            'result_quality_validated', 'native_chairman_task_bound'}
    if type(record) is not dict or record.get('schema') not in (
            _RESULT_LINK_SCHEMA, _RESULT_LINK_CHAIRMAN_SCHEMA):
        raise LifecycleRefused('Malformed history result record')
    with_chairman = record['schema'] == _RESULT_LINK_CHAIRMAN_SCHEMA
    if set(record) != (keys | {'chairman_candidate'} if with_chairman else keys):
        raise LifecycleRefused('Malformed history result record')
    key, note, project_key, root, rel = (
        record['task_key_claimed'], record['selected_note_sha256'],
        record['project_key'], record['project_root'], record['relative_result_path'])
    if (type(key) is not str or not workbench._TASK_KEY.fullmatch(key)
            or type(project_key) is not str or not _PROJECT_KEY.fullmatch(project_key)
            or type(root) is not str or len(root.encode('utf-8')) > 1024
            or not Path(root).is_absolute() or '..' in Path(root).parts
            or str(Path(root)) != root or type(rel) is not str or '\\' in rel
            or not rel or len(rel.encode('utf-8')) > 950):
        raise LifecycleRefused('Ambiguous history document location')
    parts = PurePosixPath(rel).parts
    if (not 1 <= len(parts) <= 6 or PurePosixPath(rel).is_absolute()
            or '/'.join(parts) != rel or PurePosixPath(rel).suffix.lower() not in _RESULT_TYPES
            or any(not part or part in ('.', '..') or part.startswith('.') or ':' in part
                   or len(part) > 150 or any(unicodedata.category(ch) in {'Cc', 'Cf', 'Cs', 'Zl', 'Zp'}
                      for ch in part) for part in parts)
            or any(unicodedata.category(ch) in {'Cc', 'Cf', 'Cs', 'Zl', 'Zp'} for ch in root)):
        raise LifecycleRefused('Ambiguous history result path')
    for name in ('selected_note_sha256', 'project_binding_sha256',
                 'result_sha256', 'checkpoint_sha256'):
        if type(record[name]) is not str or not workbench._SHA.fullmatch(record[name]):
            raise LifecycleRefused('Invalid history result digest')
    if (type(record['result_bytes']) is not int or not 0 < record['result_bytes'] <= 8*1024*1024
            or any(record[name] is not False for name in (
                'result_contents_disclosed', 'result_quality_validated', 'native_chairman_task_bound'))):
        raise LifecycleRefused('History result cannot grant validation or authority')
    canonical = lambda x: json.dumps(x, sort_keys=True, separators=(',', ':'),
                                     ensure_ascii=True, allow_nan=False).encode('ascii')
    binding = hashlib.sha256(canonical([project_key, root])).hexdigest()
    rel_digest = hashlib.sha256(rel.encode('utf-8')).hexdigest()
    checkpoint = hashlib.sha256(canonical([
        'vres-personal-work-result-evidence/1', key, note, binding, rel_digest,
        record['result_sha256'], record['result_bytes'],
    ])).hexdigest()
    if (record['project_binding_sha256'] != binding
            or record['checkpoint_sha256'] != checkpoint):
        raise LifecycleRefused('History result replay identity mismatch')
    if with_chairman:
        candidate = record['chairman_candidate']
        if (type(candidate) is not dict or set(candidate) != _CHAIRMAN_SOURCE_KEYS
                or candidate.get('host_evidence_status') != 'NO_HOST_MODEL_EVIDENCE_STOP'
                or candidate.get('requested_family') not in ('opus', 'sonnet')
                or candidate.get('requested_effort') not in ('low', 'medium', 'high')):
            raise LifecycleRefused('History cannot promote Chairman candidate to authority')
        for name in ('source_link_sha256', 'history_sha256',
                     'latest_proposal_sha256', 'template_sha256',
                     'rendered_candidate_sha256'):
            if (type(candidate[name]) is not str
                    or not workbench._SHA.fullmatch(candidate[name])):
                raise LifecycleRefused('Invalid Chairman candidate source digest')
        linked = hashlib.sha256(canonical([
            'vres-personal-work-chairman-source-link/1', key, note, binding,
            candidate['history_sha256'], candidate['latest_proposal_sha256'],
            candidate['template_sha256'], candidate['rendered_candidate_sha256'],
        ])).hexdigest()
        if candidate['source_link_sha256'] != linked:
            raise LifecycleRefused('Chairman source lineage differs from completed task')
    encoded = canonical(record) + b'\n'
    if len(encoded) > _MAX_RESULT_LINK_BYTES:
        raise LifecycleRefused('History result record exceeds byte bound')
    return encoded


def prepare_result_link(*, task: str, note_sha256: str, project_root: str | Path,
                        project_key: str, relative_result_path: str,
                        project_binding_sha256: str, result_sha256: str,
                        result_bytes: int, checkpoint_sha256: str,
                        chairman_candidate: dict[str, Any] | None = None) -> dict[str, Any]:
    """Validate record before any completion mutation; no disk write."""
    record = {
        'schema': _RESULT_LINK_SCHEMA, 'task_key_claimed': task,
        'selected_note_sha256': note_sha256, 'project_key': project_key,
        'project_root': str(project_root), 'relative_result_path': relative_result_path,
        'project_binding_sha256': project_binding_sha256,
        'result_sha256': result_sha256, 'result_bytes': result_bytes,
        'checkpoint_sha256': checkpoint_sha256,
        'result_contents_disclosed': False, 'result_quality_validated': False,
        'native_chairman_task_bound': False,
    }
    if chairman_candidate is not None:
        if (type(chairman_candidate) is not dict
                or chairman_candidate.get('status')
                   != 'NONAUTHORITATIVE_CHAIRMAN_CANDIDATE_TASK_SOURCE_ONLY'
                or chairman_candidate.get('task_key_claimed') != task
                or chairman_candidate.get('selected_note_sha256') != note_sha256
                or chairman_candidate.get('selected_project_binding_sha256')
                   != project_binding_sha256
                or chairman_candidate.get('approval_or_f1_fable_authority_granted') is not False
                or chairman_candidate.get('installed_chairman_verified') is not False
                or chairman_candidate.get('task_bound_in_live_chairman') is not False
                or chairman_candidate.get('policy_or_worker_routing_modified') is not False
                or chairman_candidate.get('native_claude_or_hooks_executed') is not False
                or chairman_candidate.get('database_contacted') is not False
                or chairman_candidate.get('files_written') is not False):
            raise LifecycleRefused('Chairman provenance is not a verified source-only preview')
        record['schema'] = _RESULT_LINK_CHAIRMAN_SCHEMA
        try:
            record['chairman_candidate'] = {
                field: chairman_candidate[field] for field in _CHAIRMAN_SOURCE_KEYS
            }
        except KeyError:
            raise LifecycleRefused('Missing Chairman candidate provenance') from None
    _result_bytes(record)
    return record


def _read_result_link(path: Path) -> dict[str, Any]:
    before = workbench._plain(path, directory=False)
    if not 0 < before.st_size <= _MAX_RESULT_LINK_BYTES:
        raise LifecycleRefused('History result record has unexpected size')
    try:
        raw = path.read_bytes()
        record = json.loads(raw.decode('ascii'))
    except (OSError, ValueError, UnicodeError) as exc:
        raise LifecycleRefused('History result record could not be read') from exc
    if (raw != _result_bytes(record) or
            workbench._plain(path, directory=False).st_size != len(raw)):
        raise LifecycleRefused('History result record changed or is noncanonical')
    if path.name != _result_name(record['task_key_claimed'], record['selected_note_sha256']):
        raise LifecycleRefused('History result filename and task receipt differ')
    return record


def _public_result(record: dict[str, Any], *, show_result_paths: bool) -> dict[str, Any]:
    public = {
        'schema': record['schema'], 'project_key': record['project_key'],
        'result_sha256': record['result_sha256'], 'result_bytes': record['result_bytes'],
        'checkpoint_sha256': record['checkpoint_sha256'],
        'document_path_hidden': not show_result_paths,
        'document_current_bytes_verified': False,
        'document_quality_validated': False,
        'native_chairman_task_bound': False,
    }
    if record['schema'] == _RESULT_LINK_CHAIRMAN_SCHEMA:
        public['chairman_candidate'] = {
            **record['chairman_candidate'],
            'caller_supplied_source_not_authenticated': True,
            'source_material_reverified_this_read': False,
            'host_observed_chairman_verified': False,
            'protected_f1_fable_authority_granted': False,
        }
    if show_result_paths:
        public.update({
            'project_root': record['project_root'],
            'relative_result_path': record['relative_result_path'],
            'result_file': str(Path(record['project_root']).joinpath(
                *PurePosixPath(record['relative_result_path']).parts)),
        })
    return public


def _snapshots(hist: Path | None, *, show_result_paths: bool = False) -> list[dict[str, Any]]:
    if hist is None:
        return []
    result: list[dict[str, Any]] = []
    links: dict[tuple[str, str], dict[str, Any]] = {}
    for bucket in ('revisions', 'completed', 'archived'):
        root = hist / bucket
        if workbench._stat(root) is None:
            continue
        workbench._plain(root, directory=True)
        # Existing snapshots are still the original exact note+receipt folders.
        # Result sidecars live alongside completed snapshots under this owner.
        members = list(islice(root.iterdir(), 2 * _MAX_HISTORY_ENTRIES + 1))
        if len(members) > 2 * _MAX_HISTORY_ENTRIES:
            raise LifecycleRefused('Personal history inventory limit reached')
        for entry in members:
            if bucket == 'completed' and _RESULT_NAME.fullmatch(entry.name):
                if len(links) >= _MAX_HISTORY_ENTRIES:
                    raise LifecycleRefused('Personal result history limit reached')
                record = _read_result_link(entry)
                ident = record['task_key_claimed'], record['selected_note_sha256']
                if ident in links:
                    raise LifecycleRefused('Duplicate completed result history link')
                links[ident] = record
                continue
            if len(result) >= _MAX_HISTORY_ENTRIES:
                raise LifecycleRefused('Personal history limit reached')
            workbench._plain(entry, directory=True)
            receipt = workbench.inspect_note(entry)
            key, sha = receipt['task_key_claimed'], receipt['sha256']
            if entry.name != _archive_name(key, sha):
                raise LifecycleRefused('History folder identity does not match receipt')
            result.append({'task_key_claimed': key, 'sha256': sha,
                           'bytes': receipt['bytes'], 'state': bucket})
    completed = {(row['task_key_claimed'], row['sha256']): row
                 for row in result if row['state'] == 'completed'}
    for ident, record in links.items():
        if ident not in completed:
            raise LifecycleRefused('Orphaned result link does not match completed history')
        completed[ident]['result_evidence'] = _public_result(
            record, show_result_paths=show_result_paths)
    return sorted(result, key=lambda r: (r['task_key_claimed'], r['state'], r['sha256']))


def persist_result_link(value: str | Path, record: dict[str, Any]) -> dict[str, Any]:
    """Attach one immutable document reference to an existing completed snapshot.

    An interrupted/failed write may leave a completed note without metadata;
    callers must report uncertainty and never retry completion blindly.
    """
    raw = _result_bytes(record)
    root = _root(value)
    hist = _history(root, create=False)
    existing = _snapshots(hist)
    exact = [item for item in existing
             if item['state'] == 'completed'
             and item['task_key_claimed'] == record['task_key_claimed']
             and item['sha256'] == record['selected_note_sha256']]
    if hist is None or len(exact) != 1 or 'result_evidence' in exact[0]:
        raise LifecycleRefused('Exactly one unlinked completed snapshot required')
    path = hist / 'completed' / _result_name(
        record['task_key_claimed'], record['selected_note_sha256'])
    workbench._plain(path.parent, directory=True)
    if workbench._stat(path) is not None:
        raise LifecycleRefused('Result link already exists; no overwrite permitted')
    with path.open('xb') as stream:
        stream.write(raw)
    if _read_result_link(path) != record:
        raise LifecycleRefused('Stored history link failed readback')
    after = [item for item in _snapshots(hist)
             if item['state'] == 'completed'
             and item['task_key_claimed'] == record['task_key_claimed']
             and item['sha256'] == record['selected_note_sha256']]
    if len(after) != 1 or after[0].get('result_evidence', {}).get('checkpoint_sha256') != record['checkpoint_sha256']:
        raise LifecycleRefused('Completed result link not found after write')
    return {'status': 'EXISTING_COMPLETED_HISTORY_RESULT_LINK_RECORDED',
            'checkpoint_sha256': record['checkpoint_sha256'], 'history_written': True,
            'new_task_store_created': False}


def _archive_destination(hist: Path, state: str, key: str, sha: str) -> Path:
    if state not in _BUCKETS[:3]:
        raise LifecycleRefused('Unrecognized archive state')
    path = hist / state / _archive_name(key, sha)
    if workbench._stat(path) is not None:
        raise LifecycleRefused('Identical history snapshot already exists; no overwrite')
    return path


def list_history(value: str | Path, *, show_result_paths: bool = False) -> dict[str, Any]:
    root = _root(value)
    hist = _history(root, create=False)
    if type(show_result_paths) is not bool:
        raise LifecycleRefused('Result path display requires explicit boolean opt-in')
    entries = _snapshots(hist, show_result_paths=show_result_paths)
    return {'schema': SCHEMA, 'status': 'READ_ONLY_PERSONAL_HISTORY',
            'snapshots': entries, 'count': len(entries), 'writes_performed': False,
            'authoritative_task_store': False, 'document_current_bytes_verified': False}


def read_daily_review(value: str | Path) -> dict[str, Any]:
    """Read only the existing desk's active receipts and verified history.

    This is a snapshot, NOT a "completed today" claim: history has no dates.
    No task text, project, profile, credential, installed state or DB is used.
    """
    root = _root(value)
    keys = sorted(desk._existing_tasks(root))
    active = []
    for key in keys:
        _, receipt = _active(root, key)
        active.append({'task_key_claimed': key, 'sha256': receipt['sha256'],
                       'bytes': receipt['bytes']})
    snapshots = _snapshots(_history(root, create=False))
    completed = [
        {'task_key_claimed': s['task_key_claimed'], 'sha256': s['sha256'],
         'bytes': s['bytes']}
        for s in snapshots if s['state'] == 'completed'
    ]
    return {'schema': SCHEMA, 'status': 'READ_ONLY_PERSONAL_DAILY_REVIEW',
            'active_tasks': active, 'active_count': len(active),
            'completed_snapshots': completed, 'completed_count': len(completed),
            'archived_count': sum(s['state'] == 'archived' for s in snapshots),
            'revision_count': sum(s['state'] == 'revisions' for s in snapshots),
            'history_has_timestamps': False,
            'task_binding_authoritative': False, 'writes_performed': False,
            'installed_vres_modified': False}

def inspect_pending_revision_attention(value: str | Path) -> dict[str, Any]:
    """Report original-owner interrupted revision staging without opening files.

    A leftover staging entry can follow a failed or interrupted revision.
    Presence requires human inspection; absence is only a cooperative
    read-only observation, never crash-safe recovery or write authority.
    """
    root = _root(value)
    hist = _history(root, create=False)
    present = False
    if hist is not None:
        pending = hist / 'pending'
        if workbench._stat(pending) is not None:
            workbench._plain(pending, directory=True)
            present = next(pending.iterdir(), None) is not None
    return {
        'schema': SCHEMA,
        'status': 'READ_ONLY_PENDING_REVISION_ATTENTION',
        'pending_revision_staging_present': present,
        'manual_recovery_attention_required': present,
        'pending_contents_opened': False,
        'automatic_recovery_performed': False,
        'writes_performed': False,
    }


def render_daily_review(report: dict[str, Any]) -> str:
    """Human-readable display of verified metadata; never disclose note text."""
    lines = ['Vres-OS PERSONAL -- DAILY REVIEW (READ ONLY)',
             'Active tasks: ' + str(report['active_count'])]
    lines.extend('  ' + t['task_key_claimed'] + ' | sha256=' + t['sha256']
                 for t in report['active_tasks'])
    lines.append('Completed snapshots: ' + str(report['completed_count']))
    lines.extend('  ' + t['task_key_claimed'] + ' | sha256=' + t['sha256']
                 for t in report['completed_snapshots'])
    lines.append('Archived snapshots: ' + str(report['archived_count']))
    lines.append('Revision snapshots: ' + str(report['revision_count']))
    lines.append('History has no timestamps; snapshots are not necessarily from today.')
    lines.append('No note text disclosed; no writes performed.')
    return '\n'.join(lines)


def move_out(value: str | Path, key: str, *, state: str,
             approved: bool = False, expected_sha256: str | None = None) -> dict[str, Any]:
    """Complete or archive one verified active task; preserve exact note bytes."""
    if approved is not True or state not in _STATES:
        raise LifecycleRefused('Explicit completion/archive approval required')
    if expected_sha256 is not None and (
            type(expected_sha256) is not str or not workbench._SHA.fullmatch(expected_sha256)):
        raise LifecycleRefused('Require an exact lowercase task receipt SHA-256')
    root = _root(value)
    desk._existing_tasks(root)  # refuse inconsistent active receipt inventory
    active, receipt = _active(root, key)
    if expected_sha256 is not None and receipt['sha256'] != expected_sha256:
        raise LifecycleRefused('Selected task changed since work-result confirmation')
    hist = _history(root, create=False)
    if hist is not None:
        _snapshots(hist)
        _archive_destination(hist, state, key, receipt['sha256'])
    hist = _history(root, create=True)
    assert hist is not None
    target = _archive_destination(hist, state, key, receipt['sha256'])
    # Recheck the precise user-confirmed note just before the only move.
    if (workbench.inspect_note(active) != receipt or
            (expected_sha256 is not None and receipt['sha256'] != expected_sha256)):
        raise LifecycleRefused('Selected task changed before completion')
    # Move, never unlink. A failure leaves the original intact for inspection.
    active.rename(target)
    if workbench.inspect_note(target) != receipt:
        raise LifecycleRefused('Archived receipt changed during operation')
    return {'schema': SCHEMA, 'status': 'OWN_TASK_' + state.upper(),
            'task_key_claimed': key, 'sha256': receipt['sha256'],
            'archived_bytes_preserved': True, 'installed_vres_modified': False}


def revise(value: str | Path, key: str, note_file: str | Path,
           *, approved: bool = False) -> dict[str, Any]:
    """Stage a verified replacement; preserve previous snapshot before swap."""
    if approved is not True:
        raise LifecycleRefused('Explicit revision approval required')
    root = _root(value)
    desk._existing_tasks(root)
    active, before = _active(root, key)
    note_path = Path(note_file)
    if draft._under(note_path, root):
        raise LifecycleRefused('New Markdown input must be outside the desk')
    markdown = draft._manual_markdown(note_path)
    continuity._action(markdown)  # guarantee the next focus action is readable
    next_receipt = workbench.preview_note(key, markdown)
    if next_receipt['sha256'] == before['sha256']:
        raise LifecycleRefused('No change to the existing note')
    hist = _history(root, create=False)
    if hist is not None:
        _snapshots(hist)
        _archive_destination(hist, 'revisions', key, before['sha256'])
    hist = _history(root, create=True)
    assert hist is not None
    archived = _archive_destination(hist, 'revisions', key, before['sha256'])
    pending = hist / 'pending' / ('Vres-Workbench-P' + secrets.token_hex(16))
    staged = workbench.create_note(pending, key, markdown, approved=True)
    if staged['sha256'] != next_receipt['sha256']:
        raise LifecycleRefused('Prepared revision changed; preserve pending for review')
    if workbench.inspect_note(active) != before:
        raise LifecycleRefused('Active task changed; preserve pending for review')
    # Atomic directory rename on the same filesystem, no overwrite or delete.
    active.rename(archived)
    try:
        pending.rename(active)
    except OSError:
        # Recovery of the active task is safe only while its original slot is
        # absent; otherwise preserve both snapshots for manual inspection.
        if workbench._stat(active) is None:
            archived.rename(active)
        raise
    if (workbench.inspect_note(active)['sha256'] != staged['sha256'] or
            workbench.inspect_note(archived) != before):
        raise LifecycleRefused('Revision readback discrepancy; inspect both copies')
    return {'schema': SCHEMA, 'status': 'OWN_TASK_REVISED',
            'task_key_claimed': key, 'previous_sha256': before['sha256'],
            'sha256': staged['sha256'], 'previous_snapshot_preserved': True,
            'installed_vres_modified': False}


def reopen(value: str | Path, key: str, *, state: str = 'completed',
           expected_sha256: str | None = None,
           approved: bool = False) -> dict[str, Any]:
    """Copy a selected, SHA-verified history snapshot into an absent task slot."""
    if approved is not True or state not in _STATES:
        raise LifecycleRefused('Explicit reopen approval and state required')
    root = _root(value)
    active_keys = desk._existing_tasks(root)
    if len(active_keys) >= desk._MAX_CHILDREN:
        raise LifecycleRefused('Personal desk already has six active tasks')
    target = desk._owned_task(root, key)
    if workbench._stat(target) is not None:
        raise LifecycleRefused('Task is already active; no overwrite')
    hist = _history(root, create=False)
    matches = [r for r in _snapshots(hist) if r['task_key_claimed'] == key and
               r['state'] == state and
               (expected_sha256 is None or r['sha256'] == expected_sha256)]
    if len(matches) != 1:
        raise LifecycleRefused('History selection is absent or ambiguous')
    chosen = matches[0]
    assert hist is not None
    source = hist / state / _archive_name(key, chosen['sha256'])
    verified = workbench.inspect_note(source)
    raw = (source / 'notes' / 'next-step.md').read_bytes()
    if (len(raw) != verified['bytes'] or
            hashlib.sha256(raw).hexdigest() != chosen['sha256']):
        raise LifecycleRefused('History changed during reopen')
    markdown = raw.decode('utf-8')
    continuity._action(markdown)
    restored = workbench.create_note(target, key, markdown, approved=True)
    if restored['sha256'] != chosen['sha256'] or workbench.inspect_note(source) != verified:
        raise LifecycleRefused('Reopened task readback mismatch')
    return {'schema': SCHEMA, 'status': 'OWN_TASK_REOPENED',
            'task_key_claimed': key, 'sha256': restored['sha256'],
            'archived_snapshot_preserved': True, 'installed_vres_modified': False}


def main(argv: Sequence[str] | None = None) -> int:
    p = _SafeParser(description='Offline personal task lifecycle; verified scratch only')
    commands = p.add_subparsers(dest='command', required=True)
    for name in ('revise', 'complete', 'archive', 'history', 'reopen', 'review'):
        sub = commands.add_parser(name)
        sub.add_argument('--desk', required=True)
        if name not in ('history', 'review'):
            sub.add_argument('--task-key', required=True)
            sub.add_argument('--yes', action='store_true')
        if name == 'review':
            sub.add_argument('--format', choices=('text', 'json'), default='text')
        if name == 'history':
            sub.add_argument('--show-result-paths', action='store_true')
        if name == 'revise':
            sub.add_argument('--note-file', required=True)
        if name == 'reopen':
            sub.add_argument('--from-state', choices=_STATES, default='completed')
            sub.add_argument('--sha256')
    try:
        args = p.parse_args(argv)
        if args.command == 'history':
            result = list_history(args.desk, show_result_paths=args.show_result_paths)
        elif args.command == 'review':
            result = read_daily_review(args.desk)
        elif args.command == 'revise':
            result = revise(args.desk, args.task_key, args.note_file, approved=args.yes)
        elif args.command in ('complete', 'archive'):
            result = move_out(args.desk, args.task_key, state=('completed' if args.command == 'complete' else 'archived'), approved=args.yes)
        else:
            result = reopen(args.desk, args.task_key, state=args.from_state,
                            expected_sha256=args.sha256, approved=args.yes)
    except Exception:
        print('VRES_PERSONAL_LIFECYCLE_REFUSED: check exact task, history and approved scope.', file=sys.stderr)
        return 2
    output = (render_daily_review(result)
              if args.command == 'review' and args.format == 'text'
              else json.dumps(result, sort_keys=True, ensure_ascii=True))
    print(output)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
