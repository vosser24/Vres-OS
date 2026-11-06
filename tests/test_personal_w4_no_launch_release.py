"""Author simulation only. Full original-owner Windows W4 gate is NOT_RUN."""
from __future__ import annotations

import hashlib
import inspect
import importlib.util
import json
import os
import sys
import threading
import types
import zipfile
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[1] / 'src' / 'vres_os' / 'personal_w4_no_launch_release.py'


def _module(monkeypatch):
    owner = types.ModuleType('vres_os.release_artifact')
    owner.ReleaseArtifactError = type('ReleaseArtifactError', (RuntimeError,), {})
    package = types.ModuleType('vres_os')
    package.__path__ = []
    monkeypatch.setitem(sys.modules, 'vres_os', package)
    monkeypatch.setitem(sys.modules, 'vres_os.release_artifact', owner)
    spec = importlib.util.spec_from_file_location('vres_os.personal_w4_no_launch_release', HERE)
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, spec.name, module)
    spec.loader.exec_module(module)
    return module, owner


def _synthetic(monkeypatch, tmp_path):
    w4, owner = _module(monkeypatch)
    if os.name == 'nt':
        # Author simulation uses pytest's disposable tmp_path, never a real W4 root.
        # A separate guarded Windows gate tests the actual C:/Projects restriction.
        def synthetic_root(value, *, new):
            p = Path(value)
            if not p.is_absolute() or '..' in p.parts:
                raise w4.W4Refused('Invalid synthetic path')
            for ancestor in reversed(p.parents):
                w4._ordinary(ancestor)
            if new:
                if not w4._NAME.fullmatch(p.name) or os.path.lexists(p):
                    raise w4.W4Refused('Existing or invalid synthetic candidate')
                w4._ordinary(p.parent)
            else:
                w4._ordinary(p)
            return p
        monkeypatch.setattr(w4, '_path', synthetic_root)
    source = tmp_path / 'Vres-W4-Source-aaaaaaaa'
    source.mkdir()
    (source / '.git').mkdir()
    (source / '.git' / 'config').write_text('[core]\nrepositoryformatversion = 0\n', encoding='utf-8')
    p = b'[project]\nname = "vres-os"\ndependencies = ["platformdirs>=4.2,<5", "psycopg[binary]>=3.2,<4"]\n'
    files = {rel: ('100644', sha, p if rel == 'pyproject.toml' else (rel + '\n').encode())
             for rel, sha in w4.OWNER_BLOBS.items()}
    files['src/vres_os/migrations/001_initial.sql'] = ('100644', '1' * 40, b'SELECT 1;\n')
    files['src/vres_os/migrations/041_last.sql'] = ('100644', '2' * 40, b'SELECT 2;\n')
    files['plugins/vres-os/README.txt'] = ('100644', '3' * 40, b'INERT\n')
    entry = HERE.read_bytes()
    entry_oid = hashlib.sha1(b'blob ' + str(len(entry)).encode() + b'\0' + entry).hexdigest()
    files[w4._W4_REL] = ('100644', entry_oid, entry)

    def verified(src, commit, *, git, objects):
        assert src == source
        assert commit == 'f' * 40
        return commit, 'e' * 40, files

    def stage(src, out, manifest, *, source_commit, git, objects,
              preserve_failed_stage=False):
        assert src == source and source_commit == 'f' * 40
        assert preserve_failed_stage is True
        out.mkdir()
        for rel, v in files.items():
            target = out / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(v[2])
        result = {'source_commit': source_commit, 'source_tree': 'e' * 40,
                  'files': [{'path': rel, 'git_blob': v[1], 'sha256': hashlib.sha256(v[2]).hexdigest()}
                            for rel, v in files.items()]}
        manifest.write_text(json.dumps(result, sort_keys=True))
        return result
    owner.verified_source = verified
    owner.stage = stage

    class DummyReader:
        def close(self):
            return None

    monkeypatch.setattr(w4, '_trusted_git', lambda *a: (lambda args: '', lambda: DummyReader()))
    monkeypatch.setattr(w4, '_verify_w3_ancestry', lambda *a: None)
    return w4, owner, source, files


def _build(w4, source, dest, *, approval, source_commit='f' * 40):
    return w4.build_no_launch(source, dest, source_commit=source_commit,
                               approval=approval, git_executable=source.parent / 'git.exe',
                               git_sha256='0' * 64)


def test_accepted_owners_create_one_inert_deterministic_source_zip(monkeypatch, tmp_path):
    w4, _, source, files = _synthetic(monkeypatch, tmp_path)
    receipts = []
    for n in ['aaaaaaaa', 'bbbbbbbb']:
        dest = tmp_path / ('Vres-W4-NoLaunch-' + n)
        result = _build(w4, source, dest, approval=w4.STAGE_APPROVAL)
        receipts.append(result)
        assert result['launch_authorized'] is False
        assert result['install_authorized'] is False
        assert result['runtime_ready'] is False
        assert result['source_files'] == len(files)
        assert not (dest / 'W4-INCOMPLETE.json').exists()
        digest = hashlib.sha256((dest / 'W4-SOURCE-ONLY-NO-LAUNCH.zip').read_bytes()).hexdigest()
        assert digest == result['zip_sha256']
        with zipfile.ZipFile(dest / 'W4-SOURCE-ONLY-NO-LAUNCH.zip') as archive:
            assert archive.read('source/src/vres_os/migrations/001_initial.sql') == b'SELECT 1;\n'
            caps = json.loads(archive.read('W4-CAPABILITIES.json'))
            deps = json.loads(archive.read('W4-DEPENDENCIES.json'))
            assert caps['db_migration_execution_allowed'] is False
            assert caps['native_claude_or_hooks_allowed'] is False
            assert caps['production_release_ready'] is False
            assert deps['resolver_status'] == 'NOT_RUN'
            assert not deps['resolved_wheel_sha256']
            assert 'psycopg[binary]>=3.2,<4' in deps['declared_dependencies']
    assert receipts[0]['zip_sha256'] == receipts[1]['zip_sha256']


def test_no_preflight_approval_or_wrong_owner_writes(monkeypatch, tmp_path):
    w4, owner, source, files = _synthetic(monkeypatch, tmp_path)
    dest = tmp_path / 'Vres-W4-NoLaunch-aaaaaaaa'
    with pytest.raises(w4.W4Refused):
        _build(w4, source, dest, approval='yes')
    assert not dest.exists()
    modified = dict(files)
    modified['src/vres_os/personal_w3_reuse.py'] = ('100644', '0' * 40, b'BAD')
    owner.verified_source = lambda a, b, **kw: (b, 'e' * 40, modified)
    with pytest.raises(w4.W4Refused):
        _build(w4, source, dest, approval=w4.STAGE_APPROVAL)
    assert not dest.exists()


def test_selected_root_cannot_be_overwritten_and_no_parent_escape(monkeypatch, tmp_path):
    w4, owner, source, _ = _synthetic(monkeypatch, tmp_path)
    dest = tmp_path / 'Vres-W4-NoLaunch-aaaaaaaa'
    dest.mkdir()
    with pytest.raises(w4.W4Refused):
        _build(w4, source, dest, approval=w4.STAGE_APPROVAL)
    with pytest.raises(w4.W4Refused):
        _build(w4, source, tmp_path / 'real-user-profile', approval=w4.STAGE_APPROVAL)
    assert list(dest.iterdir()) == []
    assert not (tmp_path / 'real-user-profile').exists()


def test_staging_failure_preserves_partial_owned_root(monkeypatch, tmp_path):
    w4, owner, source, _ = _synthetic(monkeypatch, tmp_path)
    def fail(_a, out, _m, *, source_commit, git, objects,
             preserve_failed_stage=False):
        assert preserve_failed_stage is True
        out.mkdir()
        (out / 'src' / 'vres_os').mkdir(parents=True)
        (out / 'src' / 'vres_os' / 'personal_w3_reuse.py').write_text('disposable only')
        raise owner.ReleaseArtifactError('simulated interruption after creation')
    owner.stage = fail
    dest = tmp_path / 'Vres-W4-NoLaunch-aaaaaaaa'
    with pytest.raises(owner.ReleaseArtifactError):
        _build(w4, source, dest, approval=w4.STAGE_APPROVAL)
    assert dest.is_dir()
    assert (dest / 'W4-INCOMPLETE.json').is_file()
    assert source.is_dir()


def test_interruption_recovery_requires_explicit_permission_and_exact_inventory(monkeypatch, tmp_path):
    w4, _, source, _ = _synthetic(monkeypatch, tmp_path)
    dest = tmp_path / 'Vres-W4-NoLaunch-aaaaaaaa'
    dest.mkdir()
    (dest / 'W4-INCOMPLETE.json').write_bytes(w4._json({
        'schema': w4.SCHEMA, 'state': 'INCOMPLETE', 'output_name': dest.name,
        'source_commit': 'f'*40, 'source_tree': 'e'*40,
        'expected_paths': ['src/vres_os/personal_w3_reuse.py'],
    }))
    (dest / 'source' / 'src' / 'vres_os').mkdir(parents=True)
    (dest / 'source' / 'src' / 'vres_os' / 'personal_w3_reuse.py').write_text('synthetic')
    report = w4.inspect_interrupted(dest)
    assert report['removed'] is False
    assert report['ownership_proven'] is False
    assert report['rollback_authorized'] is False
    with pytest.raises(w4.W4Refused):
        w4.rollback_interrupted(dest, approval='yes')
    unwanted = dest / 'my-user-data.md'
    unwanted.write_text('preserve')
    with pytest.raises(w4.W4Refused):
        w4.rollback_interrupted(dest, approval=w4.ROLLBACK_APPROVAL)
    assert unwanted.exists()
    unwanted.unlink()
    with pytest.raises(w4.W4Refused, match='disabled'):
        w4.rollback_interrupted(dest, approval=w4.ROLLBACK_APPROVAL)
    assert dest.is_dir()
    assert source.is_dir()


def test_complete_root_never_recovery_deleted(monkeypatch, tmp_path):
    w4, _, _, _ = _synthetic(monkeypatch, tmp_path)
    dest = tmp_path / 'Vres-W4-NoLaunch-aaaaaaaa'
    dest.mkdir()
    (dest / 'W4-INCOMPLETE.json').write_text('nope')
    (dest / 'W4-RECEIPT.json').write_text('completed')
    with pytest.raises(w4.W4Refused):
        w4.rollback_interrupted(dest, approval=w4.ROLLBACK_APPROVAL)
    assert dest.is_dir()


def test_disposable_source_rejects_executable_git_config_and_alternates(monkeypatch, tmp_path):
    w4, _, source, _ = _synthetic(monkeypatch, tmp_path)
    assert w4._disposable_source(source) == source
    config = source / '.git' / 'config'
    config.write_text('[filter "evil"]\nprocess = external-command\n', encoding='utf-8')
    with pytest.raises(w4.W4Refused, match='configuration'):
        w4._disposable_source(source)
    config.write_text('[core]\nrepositoryformatversion = 0\n', encoding='utf-8')
    alternates = source / '.git' / 'objects' / 'info'
    alternates.mkdir(parents=True)
    (alternates / 'alternates').write_text('untrusted-objects')
    with pytest.raises(w4.W4Refused, match='Alternate'):
        w4._disposable_source(source)


def test_git_binary_hash_must_match_before_any_git_child(monkeypatch, tmp_path):
    w4, _ = _module(monkeypatch)
    fake_git = tmp_path / 'git.exe'
    fake_git.write_bytes(b'not a trusted executable')
    with pytest.raises(w4.W4Refused, match='approved pin'):
        w4._trusted_git(tmp_path, fake_git, '0' * 64)


def test_ancestry_requires_object_hash_and_sole_parent(monkeypatch):
    w4, _ = _module(monkeypatch)

    def commit(body):
        raw = b'tree ' + b'0' * 40 + b'\nauthor test\ncommitter test\n' + body
        oid = hashlib.sha1(b'commit ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
        return oid, raw

    base, base_raw = commit(b'\naccepted base\n')
    head, head_raw = commit(b'parent ' + base.encode() + b'\n\nchild\n')
    monkeypatch.setattr(w4, 'BASE_W3_R2', base)
    data = {base: base_raw, head: head_raw}

    class Reader:
        def __call__(self, oid):
            return 'commit', data[oid]

    w4._verify_w3_ancestry(Reader(), head)
    data[head] = head_raw + b'tampered'
    with pytest.raises(w4.W4Refused, match='object verification'):
        w4._verify_w3_ancestry(Reader(), head)
    data[head] = head_raw
    monkeypatch.setattr(w4, 'BASE_W3_R2', 'f' * 40)
    with pytest.raises(w4.W4Refused):
        w4._verify_w3_ancestry(Reader(), head)


def test_os_walk_error_must_refuse_advisory_inventory(monkeypatch, tmp_path):
    w4, _, _, _ = _synthetic(monkeypatch, tmp_path)
    root = tmp_path / 'Vres-W4-NoLaunch-aaaaaaaa'
    root.mkdir()
    (root / 'W4-INCOMPLETE.json').write_bytes(w4._json({
        'schema': w4.SCHEMA, 'state': 'INCOMPLETE', 'output_name': root.name,
        'expected_paths': ['src/vres_os/personal_w3_reuse.py'],
    }))

    def fail_scan(root_path, *, followlinks, onerror):
        onerror(PermissionError('forced enumeration error'))
        yield root_path, [], []

    monkeypatch.setattr(w4.os, 'walk', fail_scan)
    with pytest.raises(w4.W4Refused, match='scan failed'):
        w4.inspect_interrupted(root)
    assert root.is_dir()

def test_original_release_owner_in_memory_bootstrap_and_default_are_preserved():
    owner_path = HERE.with_name('release_artifact.py')
    inputs_path = HERE.with_name('release_inputs.py')
    spec = importlib.util.spec_from_file_location('_vres_w4_pinned_release_owner', owner_path)
    module = importlib.util.module_from_spec(spec)
    module._w4_prechecked_release_inputs = inputs_path.read_bytes()
    exec(compile(owner_path.read_bytes(), str(owner_path), 'exec'), module.__dict__)
    assert module.release_input_problems is module._release_inputs.release_input_problems
    assert module._release_inputs.__file__ == str(inputs_path)
    assert inspect.signature(module.stage).parameters['preserve_failed_stage'].default is False


def test_git_batch_timeout_does_not_close_locked_reader(monkeypatch):
    w4, _ = _module(monkeypatch)
    entered, release = threading.Event(), threading.Event()

    class Stdin:
        def write(self, data): return len(data)
        def flush(self): pass
        def close(self): pass

    class Stdout:
        closed = False
        def readline(self, limit):
            entered.set()
            release.wait(timeout=5)
            return b''
        def close(self):
            self.closed = True

    class Child:
        def __init__(self):
            self.stdin, self.stdout = Stdin(), Stdout()
            self.killed = False
        def poll(self): return None if not self.killed else -9
        def kill(self): self.killed = True
        def wait(self, timeout): return -9

    child = Child()
    monkeypatch.setattr(w4.subprocess, 'Popen', lambda *a, **kw: child)
    monkeypatch.setattr(w4, '_GIT_READ_SECONDS', 0.05)
    monkeypatch.setattr(w4, '_GIT_WORKER_JOIN_SECONDS', 0.05)
    reader = w4._PinnedGitObjects(Path('/git'), Path('/synthetic'), {})
    try:
        with pytest.raises(w4.W4Refused, match='timed out'):
            reader('a' * 40)
        assert entered.wait(timeout=1)
        assert child.killed
        with pytest.raises(w4.W4Refused, match='reader still blocked'):
            reader.close()
        assert child.stdout.closed is False
        assert reader.process is child
        assert reader._worker is not None
    finally:
        release.set()
        if reader._worker is not None:
            reader._worker.join(timeout=2)
    reader.close()
    assert child.stdout.closed is True
    assert reader.process is None and reader._worker is None


def test_git_failed_reap_retains_child_handle_for_retry(monkeypatch):
    w4, _ = _module(monkeypatch)

    class Stream:
        def __init__(self): self.closed = False
        def close(self): self.closed = True

    class Child:
        def __init__(self):
            self.stdin, self.stdout = Stream(), Stream()
            self.killed = False
            self.allow_reap = False
        def poll(self): return None if not self.killed else -9
        def kill(self): self.killed = True
        def wait(self, timeout):
            if not self.allow_reap:
                raise w4.subprocess.TimeoutExpired(cmd='git', timeout=timeout)
            return -9

    child = Child()
    reader = w4._PinnedGitObjects(Path('/git'), Path('/synthetic'), {})
    reader.process = child
    with pytest.raises(w4.W4Refused, match='could not be reaped'):
        reader.close()
    assert reader.process is child
    assert child.stdout.closed is False
    child.allow_reap = True
    reader.close()
    assert reader.process is None
    assert child.stdin.closed and child.stdout.closed


def test_git_worker_start_failure_allows_safe_cleanup(monkeypatch):
    w4, _ = _module(monkeypatch)

    class Stream:
        def __init__(self): self.closed = False
        def close(self): self.closed = True

    class Child:
        def __init__(self):
            self.stdin, self.stdout = Stream(), Stream()
            self.killed = False
        def poll(self): return None if not self.killed else -9
        def kill(self): self.killed = True
        def wait(self, timeout): return -9

    child = Child()
    monkeypatch.setattr(w4.subprocess, 'Popen', lambda *a, **kw: child)
    monkeypatch.setattr(w4.threading.Thread, 'start',
                        lambda self: (_ for _ in ()).throw(RuntimeError('no worker')))
    reader = w4._PinnedGitObjects(Path('/git'), Path('/synthetic'), {})
    with pytest.raises(RuntimeError, match='no worker'):
        reader('a' * 40)
    assert reader.process is child
    assert reader._worker is not None and reader._worker.ident is None
    reader.close()
    assert reader.process is None
    assert child.stdin.closed and child.stdout.closed


def test_git_batch_success_uses_one_verified_bounded_response(monkeypatch):
    w4, _ = _module(monkeypatch)
    oid = 'a' * 40

    class Stdin:
        def write(self, data):
            assert data == oid.encode() + b'\n'
        def flush(self): pass
        def close(self): pass

    class Stdout:
        def __init__(self): self.calls = 0
        def readline(self, limit):
            assert limit == 128
            return oid.encode() + b' blob 3\n'
        def read(self, count):
            self.calls += 1
            return b'abc' if count == 3 else b'\n'
        def close(self): pass

    class Child:
        stdin, stdout = Stdin(), Stdout()
        killed = False
        def poll(self): return None if not self.killed else -9
        def kill(self): self.killed = True
        def wait(self, timeout): return -9

    child = Child()
    monkeypatch.setattr(w4.subprocess, 'Popen', lambda *a, **kw: child)
    reader = w4._PinnedGitObjects(Path('/git'), Path('/synthetic'), {})
    assert reader(oid) == ('blob', b'abc')
    assert child.stdout.calls == 2
    reader.close()
    assert child.killed


def test_windows_production_root_guard_is_not_disabled(monkeypatch, tmp_path):
    w4, _ = _module(monkeypatch)
    if os.name != 'nt':
        pytest.skip('Windows-specific C:/Projects guard')
    dest = tmp_path / 'Vres-W4-NoLaunch-aaaaaaaa'
    with pytest.raises(w4.W4Refused, match='Windows'):
        w4._path(dest, new=True)
