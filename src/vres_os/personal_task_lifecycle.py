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
import secrets
import sys
from itertools import islice
from pathlib import Path
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


def _snapshots(hist: Path | None) -> list[dict[str, Any]]:
    if hist is None:
        return []
    result: list[dict[str, Any]] = []
    for bucket in ('revisions', 'completed', 'archived'):
        root = hist / bucket
        if workbench._stat(root) is None:
            continue
        workbench._plain(root, directory=True)
        for entry in islice(root.iterdir(), _MAX_HISTORY_ENTRIES + 1):
            if len(result) >= _MAX_HISTORY_ENTRIES:
                raise LifecycleRefused('Personal history limit reached')
            workbench._plain(entry, directory=True)
            receipt = workbench.inspect_note(entry)
            key, sha = receipt['task_key_claimed'], receipt['sha256']
            if entry.name != _archive_name(key, sha):
                raise LifecycleRefused('History folder identity does not match receipt')
            result.append({'task_key_claimed': key, 'sha256': sha,
                           'bytes': receipt['bytes'], 'state': bucket})
    return sorted(result, key=lambda r: (r['task_key_claimed'], r['state'], r['sha256']))


def _archive_destination(hist: Path, state: str, key: str, sha: str) -> Path:
    if state not in _BUCKETS[:3]:
        raise LifecycleRefused('Unrecognized archive state')
    path = hist / state / _archive_name(key, sha)
    if workbench._stat(path) is not None:
        raise LifecycleRefused('Identical history snapshot already exists; no overwrite')
    return path


def list_history(value: str | Path) -> dict[str, Any]:
    root = _root(value)
    hist = _history(root, create=False)
    entries = _snapshots(hist)
    return {'schema': SCHEMA, 'status': 'READ_ONLY_PERSONAL_HISTORY',
            'snapshots': entries, 'count': len(entries), 'writes_performed': False,
            'authoritative_task_store': False}


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
        if name == 'revise':
            sub.add_argument('--note-file', required=True)
        if name == 'reopen':
            sub.add_argument('--from-state', choices=_STATES, default='completed')
            sub.add_argument('--sha256')
    try:
        args = p.parse_args(argv)
        if args.command == 'history':
            result = list_history(args.desk)
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
