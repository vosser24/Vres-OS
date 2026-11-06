"""Author simulation only. Full original-owner Windows W4 gate is NOT_RUN."""
from __future__ import annotations

import hashlib
import inspect
import importlib.util
import json
import os
import sys
import types
import zipfile
import zlib
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


def _git_module():
    path = HERE.with_name('personal_w4_inert_git.py')
    spec = importlib.util.spec_from_file_location('_synthetic_w4_loose_git', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _synthetic(monkeypatch, tmp_path):
    w4, owner = _module(monkeypatch)
    # Package-mode import never grants actual stage authority. Author simulation
    # substitutes trusted fake owners and never creates a real Windows W4 stage.
    monkeypatch.setattr(w4, '_W4_VERIFIED_DIRECT', True)
    monkeypatch.setattr(w4, 'release_owner', owner)
    owner._release_inputs = types.SimpleNamespace(release_record_problems=lambda records: [])
    if os.name == 'nt':
        monkeypatch.setattr(w4, '_require_trusted_windows_stage', lambda: None)
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

    def verified(src, commit, *, git, objects, max_files=None, max_bytes=None):
        assert src == source
        assert commit == 'f' * 40
        return commit, 'e' * 40, files

    owner.verified_source = verified

    class SyntheticWriter:
        """Test-only stand-in: NEVER a Windows/operational containment authority."""
        def __init__(self, root):
            self.root = root
            root.mkdir()
            self.expected = {}
        def __enter__(self): return self
        def __exit__(self, *_): return False
        def put(self, rel, raw):
            path = self.root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
            self.expected[rel] = raw
        def verify(self):
            for rel, raw in self.expected.items():
                if (self.root / rel).read_bytes() != raw:
                    raise w4.W4Refused('Synthetic writer pinned bytes mismatch')

    monkeypatch.setattr(w4, 'bound_output',
                        types.SimpleNamespace(BoundOutput=SyntheticWriter,
                                              BoundOutputRefused=w4.W4Refused))
    owner.source_manifest_bytes = lambda commit, tree, files: json.dumps(
        {'source_commit': commit, 'source_tree': tree,
         'files': [{'path': rel, 'git_blob': v[1],
                    'sha256': hashlib.sha256(v[2]).hexdigest()}
                   for rel, v in files.items()]}, sort_keys=True).encode()

    class DummyReader:
        def close(self): pass

    class DummyStore:
        def __init__(self, *args, **kwargs): pass
        def reader(self): return DummyReader()
        def git_runner(self, args): return ''

    monkeypatch.setattr(w4, 'git_source', types.SimpleNamespace(
        LooseGitSource=DummyStore, LooseGitRefused=type('LooseGitRefused', (ValueError,), {})))
    monkeypatch.setattr(w4, '_verify_w3_ancestry', lambda *a: None)
    return w4, owner, source, files


def _build(w4, source, dest, *, approval, source_commit='f' * 40):
    return w4.build_no_launch(source, dest, source_commit=source_commit,
                               approval=approval)


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
        # No path-unlink after success: receipt supersedes the diagnostic journal.
        assert (dest / 'W4-INCOMPLETE.json').is_file()
        assert (dest / 'W4-RECEIPT.json').is_file()
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
    w4, _, source, _ = _synthetic(monkeypatch, tmp_path)
    base_writer = w4.bound_output.BoundOutput
    class InterruptedWriter(base_writer):
        def put(self, rel, raw):
            super().put(rel, raw)
            if rel == 'W4-INCOMPLETE.json':
                raise w4.W4Refused('simulated interruption after journal')
    monkeypatch.setattr(w4.bound_output, 'BoundOutput', InterruptedWriter)
    dest = tmp_path / 'Vres-W4-NoLaunch-aaaaaaaa'
    with pytest.raises(w4.W4Refused, match='interruption'):
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


def test_git_common_directory_redirection_is_refused_before_git(monkeypatch, tmp_path):
    w4, _, source, _ = _synthetic(monkeypatch, tmp_path)
    external = tmp_path / 'synthetic-unapproved-git-store'
    external.mkdir()
    (source / '.git' / 'commondir').write_text(str(external), encoding='utf-8')
    with pytest.raises(w4.W4Refused, match='common directory'):
        w4._disposable_source(source)
    assert external.is_dir()


def test_r8_operational_entrypoint_exposes_no_git_executable_or_sha_arguments(monkeypatch):
    w4, _ = _module(monkeypatch)
    signature = inspect.signature(w4.build_no_launch)
    assert 'git_executable' not in signature.parameters
    assert 'git_sha256' not in signature.parameters
    assert w4._W4_VERIFIED_DIRECT is False
    assert w4.release_owner is None


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
    records = {'README.md': ('100644', 'b' * 40, b'inert\\n')}
    raw = module.source_manifest_bytes('a' * 40, 'c' * 40, records)
    assert json.loads(raw) == module.source_manifest('a' * 40, 'c' * 40, records)
    assert raw == module.source_manifest_bytes('a' * 40, 'c' * 40, records)


def _loose_fixture(tmp_path):
    git = _git_module()
    root = tmp_path / 'Vres-W4-Source-aaaaaaaa'
    (root / '.git' / 'objects').mkdir(parents=True)
    (root / '.git' / 'config').write_text('[core]\nrepositoryformatversion = 0\n')
    content = b'hello immutable Git world\n'
    def object_bytes(kind, body):
        payload = kind.encode() + b' ' + str(len(body)).encode() + b'\0' + body
        oid = hashlib.sha1(payload).hexdigest()
        entry = root / '.git' / 'objects' / oid[:2] / oid[2:]
        entry.parent.mkdir(exist_ok=True)
        entry.write_bytes(zlib.compress(payload))
        return oid, entry
    blob, entry = object_bytes('blob', content)
    commit, _ = object_bytes('commit', b'tree ' + b'a' * 40 + b'\n\nSynthetic\n')
    (root / '.git' / 'HEAD').write_text(commit + '\n')
    files = {}
    paths = ('src/vres_os/demo.py', 'plugins/vres-os/demo.txt',
             'scripts/windows/demo.ps1', 'pyproject.toml', 'README.md',
             'LICENSE', 'rules/vres-rules.md')
    for rel in paths:
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(content)
        files[rel] = ('100644', blob, content)

    class Owner:
        SCOPE_DIRS = ('src/vres_os/', 'plugins/vres-os/', 'scripts/windows/')
        SCOPE_FILES = ('pyproject.toml', 'README.md', 'LICENSE', 'rules/vres-rules.md')
        def _pathspecs(self):
            return [p.rstrip('/') for p in self.SCOPE_DIRS] + list(self.SCOPE_FILES)
        def _commit_files(self, objects, sha, *, max_files=None, max_bytes=None):
            assert sha == commit
            assert objects(blob) == ('blob', content)
            return 'a' * 40, files
        def _same_as_committed(self, running, committed):
            return running == committed

    return git, root, commit, blob, entry, content, Owner()


def test_strict_loose_git_source_runs_original_owner_interface_without_git_spawn(tmp_path, monkeypatch):
    git, root, commit, blob, _, content, owner = _loose_fixture(tmp_path)
    import subprocess
    monkeypatch.setattr(subprocess, 'run', lambda *a, **kw: pytest.fail('No Git subprocess.run'))
    monkeypatch.setattr(subprocess, 'Popen', lambda *a, **kw: pytest.fail('No Git Popen'))
    store = git.LooseGitSource(root, commit, owner, max_files=350, max_bytes=10000)
    reader = store.reader()
    assert reader(blob) == ('blob', content)
    reader.close()
    with pytest.raises(git.LooseGitRefused, match='Closed'):
        reader(blob)
    assert store.git_runner(['rev-parse', '--show-object-format']) == 'sha1\n'
    assert store.git_runner(['rev-parse', '--show-toplevel']) == str(root) + '\n'
    assert store.git_runner(['rev-parse', '--verify', '--end-of-options', 'HEAD^{commit}']) == commit + '\n'
    assert store.git_runner(['status', '--porcelain=v1', '-z', '--untracked-files=all',
                             '--', *owner._pathspecs()]) == ''
    with pytest.raises(git.LooseGitRefused, match='Unrecognized'):
        store.git_runner(['show', '--format'])


def test_strict_loose_git_rejects_packed_or_linked_storage(tmp_path):
    git, root, commit, _, _, _, owner = _loose_fixture(tmp_path)
    pack = root / '.git' / 'objects' / 'pack'
    pack.mkdir()
    (pack / 'pack-evil.idx').write_bytes(b'external')
    with pytest.raises(git.LooseGitRefused, match='Packed'):
        git.LooseGitSource(root, commit, owner, max_files=350, max_bytes=10000)
    (pack / 'pack-evil.idx').unlink()
    (root / '.git' / 'commondir').write_text('../outside')
    with pytest.raises(git.LooseGitRefused, match='storage'):
        git.LooseGitSource(root, commit, owner, max_files=350, max_bytes=10000)


def test_strict_loose_git_rejects_unpinned_symbolic_head(tmp_path):
    git, root, commit, _, _, _, owner = _loose_fixture(tmp_path)
    (root / '.git' / 'HEAD').write_text('ref: refs/heads/main\n')
    with pytest.raises(git.LooseGitRefused, match='detached'):
        git.LooseGitSource(root, commit, owner, max_files=350, max_bytes=10000)


def test_strict_loose_git_detects_corrupted_and_trailing_object(tmp_path):
    git, root, commit, blob, entry, _, owner = _loose_fixture(tmp_path)
    store = git.LooseGitSource(root, commit, owner, max_files=350, max_bytes=10000)
    entry.write_bytes(zlib.compress(b'blob 3\0BAD'))
    with pytest.raises(git.LooseGitRefused, match='SHA-1'):
        store.read_object(blob)
    entry.write_bytes(zlib.compress(b'blob 3\0BAD') + b'garbage')
    with pytest.raises(git.LooseGitRefused, match='trailing'):
        store.read_object(blob)


def test_strict_loose_git_rejects_untracked_and_modified_release_scope(tmp_path):
    git, root, commit, _, _, _, owner = _loose_fixture(tmp_path)
    store = git.LooseGitSource(root, commit, owner, max_files=350, max_bytes=10000)
    extra = root / 'src' / 'vres_os' / 'untracked.py'
    extra.write_bytes(b'injected')
    with pytest.raises(git.LooseGitRefused, match='differs'):
        store.assert_clean_scope()
    extra.unlink()
    target = root / 'README.md'
    target.write_bytes(b'untrusted modification')
    with pytest.raises(git.LooseGitRefused, match='modified'):
        store.assert_clean_scope()


def test_r9_original_owner_stage_is_never_called_and_substitution_refused(monkeypatch, tmp_path):
    w4, owner, source, _ = _synthetic(monkeypatch, tmp_path)
    owner.stage = lambda *a, **kw: pytest.fail('Forbidden original owner pathname stage')
    base_writer = w4.bound_output.BoundOutput
    class TamperingWriter(base_writer):
        def put(self, rel, raw):
            super().put(rel, raw)
            if rel == 'SOURCE-MANIFEST.json':
                (self.root / rel).write_bytes(b'{}')
    monkeypatch.setattr(w4.bound_output, 'BoundOutput', TamperingWriter)
    dest = tmp_path / 'Vres-W4-NoLaunch-aaaaaaaa'
    with pytest.raises(w4.W4Refused, match='pinned bytes mismatch'):
        _build(w4, source, dest, approval=w4.STAGE_APPROVAL)
    assert (dest / 'W4-INCOMPLETE.json').exists()
    assert not (dest / 'W4-RECEIPT.json').exists()


def test_windows_stage_block_precedes_source_root_access(monkeypatch, tmp_path):
    w4, _ = _module(monkeypatch)
    monkeypatch.setattr(w4, '_W4_VERIFIED_DIRECT', True)
    monkeypatch.setattr(w4, 'release_owner', types.SimpleNamespace())
    monkeypatch.setattr(w4, 'git_source', types.SimpleNamespace())
    with pytest.raises(w4.W4Refused, match='handle-bound'):
        w4._require_trusted_windows_stage(platform='nt')
    assert not (tmp_path / 'Vres-W4-NoLaunch-aaaaaaaa').exists()


def test_output_root_identity_shift_refuses_staging(monkeypatch, tmp_path):
    w4, _ = _module(monkeypatch)
    root = tmp_path / 'Vres-W4-NoLaunch-aaaaaaaa'
    root.mkdir()
    identity = w4._root_identity(root)
    w4._assert_root_identity(root, identity)
    monkeypatch.setattr(w4, '_root_identity',
                        lambda _path: (identity[0], identity[1] + 1))
    with pytest.raises(w4.W4Refused, match='identity shifted'):
        w4._assert_root_identity(root, identity)


def test_windows_production_root_guard_is_not_disabled(monkeypatch, tmp_path):
    w4, _ = _module(monkeypatch)
    if os.name != 'nt':
        pytest.skip('Windows-specific C:/Projects guard')
    dest = tmp_path / 'Vres-W4-NoLaunch-aaaaaaaa'
    with pytest.raises(w4.W4Refused, match='Windows'):
        w4._path(dest, new=True)


def test_r9_original_owner_release_inputs_validate_full_inert_inventory():
    path = HERE.with_name('release_inputs.py')
    spec = importlib.util.spec_from_file_location('_vres_r9_inert_release_inputs', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    migrations = path.parent / 'migrations'
    records = {
        'src/vres_os/migrations/' + name: (migrations / name).read_bytes()
        for name in module.PERSONAL_MIGRATION_PINS
    }
    assert module.release_record_problems(records) == []
    bad = dict(records)
    name = next(iter(module.PERSONAL_MIGRATION_PINS))
    bad['src/vres_os/migrations/' + name] = b'-- altered inert migration\n'
    assert module.release_record_problems(bad)
    bad = dict(records)
    bad['src/vres_os/experience_benchmark_violation.py'] = b'inert'
    assert module.release_record_problems(bad)


def test_r9_pure_in_memory_zip_is_reproducible_and_never_stages(monkeypatch, tmp_path):
    w4, _ = _module(monkeypatch)
    records = {'source/README.md': b'INERT\n', 'SOURCE-MANIFEST.json': b'{}\n'}
    first = w4._zip_bytes(records)
    second = w4._zip_bytes(dict(reversed(list(records.items()))))
    assert first == second
    with zipfile.ZipFile(__import__('io').BytesIO(first)) as archive:
        assert archive.read('source/README.md') == b'INERT\n'
    assert list(tmp_path.iterdir()) == []


def test_r9_full_source_pure_input_validator_refuses_before_root_creation(monkeypatch, tmp_path):
    w4, owner, source, _ = _synthetic(monkeypatch, tmp_path)
    owner._release_inputs.release_record_problems = lambda records: ['inert 041 migration changed']
    dest = tmp_path / 'Vres-W4-NoLaunch-aaaaaaaa'
    with pytest.raises(w4.W4Refused, match='release inputs refused'):
        _build(w4, source, dest, approval=w4.STAGE_APPROVAL)
    assert not dest.exists()


def test_r9_posix_bound_writer_creates_exclusive_verified_root(tmp_path):
    if os.name == 'nt':
        pytest.skip('Windows W4 output must remain completely refused')
    path = HERE.with_name('personal_w4_bound_output.py')
    spec = importlib.util.spec_from_file_location('_vres_r9_bound_output', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    root = tmp_path / 'Vres-W4-NoLaunch-aaaaaaaa'
    with module.BoundOutput(root) as writer:
        writer.put('W4-INCOMPLETE.json', b'INCOMPLETE\n')
        writer.put('source/src/vres_os/one.py', b'original-source\n')
        writer.verify()
        with pytest.raises(module.BoundOutputRefused):
            writer.put('W4-INCOMPLETE.json', b'OVERWRITE')
        writer.put('W4-RECEIPT.json', b'DONE\n')
        writer.verify()
    assert (root / 'W4-RECEIPT.json').read_bytes() == b'DONE\n'
    with pytest.raises(OSError):
        module.BoundOutput(root)


def test_r9_posix_bound_writer_preserves_failed_journal(tmp_path):
    if os.name == 'nt':
        pytest.skip('Windows W4 output must remain completely refused')
    path = HERE.with_name('personal_w4_bound_output.py')
    spec = importlib.util.spec_from_file_location('_vres_r9_bound_fail', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    root = tmp_path / 'Vres-W4-NoLaunch-aaaaaaaa'
    with pytest.raises(RuntimeError, match='simulated failure'):
        with module.BoundOutput(root) as writer:
            writer.put('W4-INCOMPLETE.json', b'INCOMPLETE\n')
            raise RuntimeError('simulated failure')
    assert (root / 'W4-INCOMPLETE.json').read_bytes() == b'INCOMPLETE\n'
    assert not (root / 'W4-RECEIPT.json').exists()


def test_r9_original_owner_git_inventory_enforces_streaming_limits():
    owner_path = HERE.with_name('release_artifact.py')
    spec = importlib.util.spec_from_file_location('_vres_r9_owner_limits', owner_path)
    module = importlib.util.module_from_spec(spec)
    module._w4_prechecked_release_inputs = HERE.with_name('release_inputs.py').read_bytes()
    exec(compile(owner_path.read_bytes(), str(owner_path), 'exec'), module.__dict__)
    def obj(kind, body):
        import hashlib
        full = kind.encode() + b' ' + str(len(body)).encode() + b'\0' + body
        return hashlib.sha1(full).hexdigest(), body
    blob, blob_body = obj('blob', b'hello\n')
    tree, tree_body = obj('tree', b'100644 README.md\0' + bytes.fromhex(blob))
    commit, commit_body = obj('commit', b'tree ' + tree.encode() + b'\n\nPinned source\n')
    values = {blob: ('blob', blob_body), tree: ('tree', tree_body),
              commit: ('commit', commit_body)}
    reader = lambda oid: values[oid]
    with pytest.raises(module.ReleaseArtifactError, match='file-count'):
        module._commit_files(reader, commit, max_files=0, max_bytes=100)
    with pytest.raises(module.ReleaseArtifactError, match='byte limit'):
        module._commit_files(reader, commit, max_files=1, max_bytes=1)


def test_r9_package_mode_cannot_access_bound_writer(monkeypatch):
    w4, _ = _module(monkeypatch)
    assert w4.bound_output is None
    assert w4.release_owner is None
    assert w4.git_source is None
    assert w4._W4_VERIFIED_DIRECT is False
