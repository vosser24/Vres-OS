"""Build one standalone personal Windows desk folder + ZIP from pinned local source.

No git, download, installer, profile discovery, project access or task store.
All inputs and output paths are explicitly selected; writes are create-only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import sys
import zipfile
from pathlib import Path

SCHEMA = 'vres-personal-portable-delivery/1'
# Exact runtime closure accepted on native Windows for portable desk P1.
PINNED_BLOBS = {
    'src/vres_os/__init__.py': 'cae9ae5f04d1005900c8e82b1564abb164520851',
    'src/vres_os/personal_desk_cli.py': '0836374306c8a8619ec82d5478f252de940ce5be',
    'src/vres_os/personal_portable_desk.py': 'e762f6fc09bbd76a9ed77d47d6ece2d82a06691f',
    'src/vres_os/personal_task_lifecycle.py': 'db57c3775ada08f311a36a8c7d58cb7ee1d68596',
    'src/vres_os/personal_offline_workbench.py': '636d40b7229d27da6442e8089120cad0c3840529',
    'src/vres_os/personal_task_continuity.py': '949993cb7b730712e600cd71dac6181e0dc7ef9a',
    'src/vres_os/personal_daily_focus.py': '7f66743a9ac305294a4e9a0b5a04c6fda89ebd0a',
    'src/vres_os/personal_scratch_discovery.py': '695e864129cf14a920346b9a514f332d363c7094',
    'src/vres_os/personal_project_task_draft.py': '92016e79b22705c15cba6ee634ef135a7bc3eb21',
    'src/vres_os/personal_project_intake.py': '63fa8bb35bef68940195b8e4b463bfebaf7b2a13',
}
_REPARSE = 0x400
_MAX_BYTES = 128 * 1024

class DeliveryRefused(ValueError):
    """Refuse ambiguous inputs or unauthorized delivery paths."""


def _plain(path: Path, directory: bool) -> os.stat_result:
    try:
        info = path.lstat()
    except OSError as exc:
        raise DeliveryRefused('Missing or unreadable ordinary source') from exc
    if (stat.S_ISLNK(info.st_mode) or
            bool(getattr(info, 'st_file_attributes', 0) & _REPARSE) or
            (not directory and (not stat.S_ISREG(info.st_mode) or
                                getattr(info, 'st_nlink', 1) != 1)) or
            (directory and not stat.S_ISDIR(info.st_mode))):
        raise DeliveryRefused('Redirected or unexpected path type')
    return info


def _explicit_path(value: str, *, exists: bool) -> Path:
    if not isinstance(value, str) or not value.strip() or '\x00' in value:
        raise DeliveryRefused('Explicit absolute path required')
    path = Path(value)
    if not path.is_absolute() or '..' in path.parts:
        raise DeliveryRefused('Absolute path without traversal required')
    for parent in reversed(path.parents):
        _plain(parent, True)
    if exists:
        _plain(path, True)
    else:
        if not path.name.startswith('Vres-PortableDesk-Delivery-') or len(path.name) > 80:
            raise DeliveryRefused('New explicitly named delivery directory required')
        if os.path.lexists(path):
            raise DeliveryRefused('Delivery directory exists; no overwrite')
    return path


def _git_blob_sha1(raw: bytes) -> str:
    return hashlib.sha1(b'blob ' + str(len(raw)).encode('ascii') + b'\0' + raw).hexdigest()


def _read_pinned_source(source: Path) -> tuple[dict[str, bytes], dict[str, str]]:
    payloads: dict[str, bytes] = {}
    digests: dict[str, str] = {}
    for rel, expected in sorted(PINNED_BLOBS.items()):
        path = source.joinpath(*rel.split('/'))
        for parent in reversed(path.parents):
            _plain(parent, True)
        info = _plain(path, False)
        if not 0 < info.st_size <= _MAX_BYTES:
            raise DeliveryRefused('Source file outside bounded size')
        raw = path.read_bytes()
        if len(raw) != info.st_size or _plain(path, False).st_size != len(raw):
            raise DeliveryRefused('Source changed while being read')
        if _git_blob_sha1(raw) != expected:
            raise DeliveryRefused('Published Git source blob mismatch')
        payloads[rel] = raw
        digests[rel] = hashlib.sha256(raw).hexdigest()
    return payloads, digests


LAUNCHER = r'''#requires -Version 5.1
# Personal source-only Vres-OS desk launcher. NO installation, hooks or DB.
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][ValidateSet('init','add','focus','open','remove','revise','complete','archive','history','reopen')][string]$Operation,
    [Parameter(Mandatory=$true)][string]$PythonExe,
    [Parameter(Mandatory=$true)][string]$Desk,
    [string]$TaskKey,
    [string]$NoteFile,
    [switch]$Approve,
    [switch]$ShowAction,
    [ValidateSet('completed','archived')][string]$FromState = 'completed',
    [string]$SnapshotSha256
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
try {
    $py = Get-Item -LiteralPath $PythonExe -Force -ErrorAction Stop
    if ($py.PSIsContainer -or ($py.Attributes -band [IO.FileAttributes]::ReparsePoint) -or
        -not [IO.Path]::IsPathRooted($PythonExe)) { throw 'Python must be ordinary absolute path' }
    if ((Get-AuthenticodeSignature -FilePath $PythonExe).Status -ne 'Valid') {
        throw 'Python executable must have a valid Windows signature'
    }
    $expected = @{
__PINNED_SHA256_TABLE__
    }
    foreach ($name in $expected.Keys) {
        $file = Join-Path $PSScriptRoot ('src\vres_os\' + $name)
        $info = Get-Item -LiteralPath $file -Force -ErrorAction Stop
        if ($info.PSIsContainer -or ($info.Attributes -band [IO.FileAttributes]::ReparsePoint) -or
            (Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash.ToLowerInvariant() -cne $expected[$name]) {
            throw 'Portable source integrity check failed'
        }
    }
    $router = Join-Path $PSScriptRoot 'src\vres_os\personal_desk_cli.py'
    $argv = @('-I','-S','-B',$router,'desk',$Operation,'--desk',$Desk)
    if ($ShowAction -and $Operation -notin @('focus','open')) {
        throw 'Action disclosure applies only to focus/open'
    }
    if ($Approve -and $Operation -in @('focus','open','history')) {
        throw 'Approval is not applicable to read-only operations'
    }
    if ($SnapshotSha256 -and $SnapshotSha256 -cnotmatch '^[0-9a-f]{64}$') {
        throw 'Snapshot selector must be a lowercase SHA-256'
    }
    if ($Operation -ne 'reopen' -and ($SnapshotSha256 -or $FromState -ne 'completed')) {
        throw 'History snapshot selection applies only to reopen'
    }
    switch ($Operation) {
        'init' {
            if (-not $Approve) { throw 'Explicit create approval required' }
            $argv += '--yes'
        }
        'add' {
            if (-not $Approve -or -not $TaskKey -or -not $NoteFile) { throw 'Explicit task, note and approval required' }
            $argv += @('--task-key',$TaskKey,'--note-file',$NoteFile,'--yes')
        }
        'focus' {
            if (-not $TaskKey) { throw 'Explicit selection required' }
            $argv += @('--select',$TaskKey)
            if ($ShowAction) { $argv += '--show-selected-action' }
        }
        'open' {
            if (-not $TaskKey) { throw 'Explicit task required' }
            $argv += @('--task-key',$TaskKey)
            if ($ShowAction) { $argv += '--show-next-action' }
        }
        'remove' {
            if (-not $Approve -or -not $TaskKey) { throw 'Explicit task and removal approval required' }
            $argv += @('--task-key',$TaskKey,'--yes')
        }
        'revise' {
            if (-not $Approve -or -not $TaskKey -or -not $NoteFile) {
                throw 'Explicit revision task, note and approval required'
            }
            $argv += @('--task-key',$TaskKey,'--note-file',$NoteFile,'--yes')
        }
        'complete' {
            if (-not $Approve -or -not $TaskKey) { throw 'Explicit completion approval required' }
            $argv += @('--task-key',$TaskKey,'--yes')
        }
        'archive' {
            if (-not $Approve -or -not $TaskKey) { throw 'Explicit archive approval required' }
            $argv += @('--task-key',$TaskKey,'--yes')
        }
        'history' {
            # Read-only SHA/status inspection; no extra arguments.
        }
        'reopen' {
            if (-not $Approve -or -not $TaskKey) { throw 'Explicit reopen approval required' }
            $argv += @('--task-key',$TaskKey,'--from-state',$FromState,'--yes')
            if ($SnapshotSha256) { $argv += @('--sha256',$SnapshotSha256) }
        }
    }
} catch {
    [Console]::Error.WriteLine('VRES_PORTABLE_LAUNCH_REFUSED: verify signed Python, source integrity and explicit scope.')
    exit 2
}
& $PythonExe @argv
exit $LASTEXITCODE
'''

START_HERE = '''Vres-OS PERSONAL PORTABLE DESK -- SOURCE-ONLY / NO INSTALLATION

This is one portable folder you can move or keep next to its matching ZIP.
Nothing is registered with Windows. No credentials, Claude, PostgreSQL,
installer, new task database, project mutation or automatic discovery.

REQUIREMENTS: Windows PowerShell 5.1 and an existing Windows-signed Python
3.13.x. Use an explicitly selected ordinary Python executable on each call.
The published TEN-module Python runtime is verified at build time and before
EVERY launch. Keep source/launcher files unchanged.

DO NOT use real secrets in Markdown. Each source note must be UTF-8 and have
exactly one section of this form, with one line:

# A personal task

## Next action
- Review the report.

Example commands (edit all paths; use approved NEW scratch locations):
  $run = 'C:\\Projects\\Vres-PortableDesk\\Desk.ps1'
  $py = 'C:\\Projects\\MY_EXISTING_SIGNED_PYTHON\\python.exe'
  $desk = 'C:\\Projects\\Vres-Desk-MyDailyNotes'
  & $run -Operation init -PythonExe $py -Desk $desk -Approve
  & $run -Operation add -PythonExe $py -Desk $desk -TaskKey TASK-01 -NoteFile 'C:\\Projects\\my-task.md' -Approve
  & $run -Operation focus -PythonExe $py -Desk $desk -TaskKey TASK-01
  & $run -Operation focus -PythonExe $py -Desk $desk -TaskKey TASK-01 -ShowAction
  & $run -Operation open -PythonExe $py -Desk $desk -TaskKey TASK-01 -ShowAction
  & $run -Operation revise -PythonExe $py -Desk $desk -TaskKey TASK-01 -NoteFile 'C:\\Projects\\my-revised-task.md' -Approve
  & $run -Operation history -PythonExe $py -Desk $desk
  & $run -Operation complete -PythonExe $py -Desk $desk -TaskKey TASK-01 -Approve
  & $run -Operation reopen -PythonExe $py -Desk $desk -TaskKey TASK-01 -FromState completed -Approve
  & $run -Operation archive -PythonExe $py -Desk $desk -TaskKey TASK-01 -Approve
  & $run -Operation reopen -PythonExe $py -Desk $desk -TaskKey TASK-01 -FromState archived -Approve
  & $run -Operation remove -PythonExe $py -Desk $desk -TaskKey TASK-01 -Approve

APPROVAL: -Approve is required for init/add/remove/revise/complete/archive/reopen; never implicit.
FOCUS: requires -TaskKey to select one task; shows no action by default.
HISTORY: read-only SHA/status inventory; REVISE preserves previous exact bytes.
COMPLETE/ARCHIVE: move verified scratch into bounded local history.
REOPEN: copies one completed/archived snapshot and preserves history.
If multiple snapshots match, supply -SnapshotSha256 from history exactly.
REMOVE: removes only the unchanged, verified owned scratch workspace.
Keep the ORIGINAL Markdown input separately (never inside your desk).
When a note changes, the receipt becomes stale and the operation refuses.
The desk is not a validated task database or independent F1 approval.

No installed Vres files or Windows profile changes are part of this package.
Portable Windows execution requires its own next native acceptance check.
'''


def _output_bytes(payloads: dict[str, bytes], sha: dict[str, str]) -> dict[str, bytes]:
    table = '\n'.join("        '%s' = '%s'" % (Path(key).name, sha[key]) for key in sorted(sha))
    launcher = LAUNCHER.replace('__PINNED_SHA256_TABLE__', table)
    manifest = {
        'schema': SCHEMA, 'source_commit': '39fb74b80c899cad9199f6225b39e103b99b4fc3',
        'source_tree': '73743daffa611062863d7ba9d9e0bab011e43007',
        'runtime_files': [{'path': rel, 'git_blob_sha1': PINNED_BLOBS[rel], 'sha256': sha[rel]}
                          for rel in sorted(sha)],
        'installed_vres_modified': False, 'task_store_created': False,
        'windows_integration': 'NOT_RUN_FOR_THIS_PACKAGE',
    }
    data = dict(payloads)
    data['Desk.ps1'] = launcher.encode('ascii')
    data['START-HERE.txt'] = START_HERE.encode('ascii')
    data['SOURCE-MANIFEST.json'] = (json.dumps(manifest, indent=2, sort_keys=True) + '\n').encode('ascii')
    return data


def build(source_root: str, output_root: str, *, approved: bool = False) -> dict[str, object]:
    if approved is not True:
        raise DeliveryRefused('Explicit create-only approval required')
    source = _explicit_path(source_root, exists=True)
    target = _explicit_path(output_root, exists=False)
    source_bytes, sha = _read_pinned_source(source)  # before ANY writes
    output = _output_bytes(source_bytes, sha)
    # Single new output root. On an unexpected failure leave it for inspection;
    # never recursively delete or overwrite unexpected operator content.
    target.mkdir(mode=0o700)
    folder = target / 'Vres-PortableDesk'
    folder.mkdir(mode=0o700)
    for rel, raw in sorted(output.items()):
        dest = folder.joinpath(*rel.split('/'))
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open('xb') as f:
            f.write(raw)
        if dest.read_bytes() != raw:
            raise DeliveryRefused('Created folder failed exact byte readback')
    archive = target / 'Vres-PortableDesk.zip'
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_STORED, allowZip64=False) as z:
        for rel, raw in sorted(output.items()):
            info = zipfile.ZipInfo('Vres-PortableDesk/' + rel, date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_STORED
            info.external_attr = 0o100644 << 16
            z.writestr(info, raw)
    with zipfile.ZipFile(archive, 'r') as z:
        if sorted(z.namelist()) != sorted('Vres-PortableDesk/' + key for key in output):
            raise DeliveryRefused('ZIP paths failed exact inventory')
        for rel, raw in output.items():
            if z.read('Vres-PortableDesk/' + rel) != raw:
                raise DeliveryRefused('ZIP failed exact readback')
    zip_sha = hashlib.sha256(archive.read_bytes()).hexdigest()
    receipt = {'schema': SCHEMA, 'source_commit': '39fb74b80c899cad9199f6225b39e103b99b4fc3',
               'zip_sha256': zip_sha, 'files_in_zip': len(output),
               'installed_vres_modified': False, 'task_store_created': False}
    receipt_bytes = (json.dumps(receipt, indent=2, sort_keys=True) + '\n').encode('ascii')
    with (target / 'DELIVERY-RECEIPT.json').open('xb') as f:
        f.write(receipt_bytes)
    return receipt


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description='Create-only portable offline personal desk ZIP from pinned local source')
    p.add_argument('--source-root', required=True, help='Explicit already verified source root, not a real project')
    p.add_argument('--output-root', required=True, help='Absent Vres-PortableDesk-Delivery-* directory')
    p.add_argument('--yes', action='store_true', help='Approve one new output directory only')
    try:
        args = p.parse_args(argv)
        result = build(args.source_root, args.output_root, approved=args.yes)
    except Exception:
        print('VRES_PORTABLE_DELIVERY_REFUSED: inspect pinned source and explicit destination.', file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
