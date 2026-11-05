"""Author simulation only. Full original-owner Windows W4 gate is NOT_RUN."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
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
    source = tmp_path / 'Vres-W4-Source-aaaaaaaa'
    source.mkdir()
    p = b'[project]\nname = "vres-os"\ndependencies = ["platformdirs>=4.2,<5", "psycopg[binary]>=3.2,<4"]\n'
    files = {rel: ('100644', sha, p if rel == 'pyproject.toml' else (rel + '\n').encode())
             for rel, sha in w4.OWNER_BLOBS.items()}
    files['src/vres_os/migrations/001_initial.sql'] = ('100644', '1' * 40, b'SELECT 1;\n')
    files['src/vres_os/migrations/041_last.sql'] = ('100644', '2' * 40, b'SELECT 2;\n')
    files['plugins/vres-os/README.txt'] = ('100644', '3' * 40, b'INERT\n')

    def verified(src, commit):
        assert src == source
        assert commit == 'f' * 40
        return commit, 'e' * 40, files

    def stage(src, out, manifest, *, source_commit):
        assert src == source and source_commit == 'f' * 40
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
    return w4, owner, source, files


def test_accepted_owners_create_one_inert_deterministic_source_zip(monkeypatch, tmp_path):
    w4, _, source, files = _synthetic(monkeypatch, tmp_path)
    receipts = []
    for n in ['aaaaaaaa', 'bbbbbbbb']:
        dest = tmp_path / ('Vres-W4-NoLaunch-' + n)
        result = w4.build_no_launch(source, dest, source_commit='f' * 40,
                                    approval=w4.STAGE_APPROVAL)
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
        w4.build_no_launch(source, dest, source_commit='f' * 40, approval='yes')
    assert not dest.exists()
    modified = dict(files)
    modified['src/vres_os/personal_w3_reuse.py'] = ('100644', '0' * 40, b'BAD')
    owner.verified_source = lambda a, b: (b, 'e' * 40, modified)
    with pytest.raises(w4.W4Refused):
        w4.build_no_launch(source, dest, source_commit='f' * 40, approval=w4.STAGE_APPROVAL)
    assert not dest.exists()


def test_selected_root_cannot_be_overwritten_and_no_parent_escape(monkeypatch, tmp_path):
    w4, owner, source, _ = _synthetic(monkeypatch, tmp_path)
    dest = tmp_path / 'Vres-W4-NoLaunch-aaaaaaaa'
    dest.mkdir()
    with pytest.raises(w4.W4Refused):
        w4.build_no_launch(source, dest, source_commit='f' * 40, approval=w4.STAGE_APPROVAL)
    with pytest.raises(w4.W4Refused):
        w4.build_no_launch(source, tmp_path / 'real-user-profile', source_commit='f' * 40,
                           approval=w4.STAGE_APPROVAL)
    assert list(dest.iterdir()) == []
    assert not (tmp_path / 'real-user-profile').exists()


def test_staging_failure_cleans_only_new_owned_root(monkeypatch, tmp_path):
    w4, owner, source, _ = _synthetic(monkeypatch, tmp_path)
    def fail(_a, out, _m, *, source_commit):
        out.mkdir()
        (out / 'src' / 'vres_os').mkdir(parents=True)
        (out / 'src' / 'vres_os' / 'personal_w3_reuse.py').write_text('disposable only')
        raise owner.ReleaseArtifactError('simulated interruption after creation')
    owner.stage = fail
    dest = tmp_path / 'Vres-W4-NoLaunch-aaaaaaaa'
    with pytest.raises(owner.ReleaseArtifactError):
        w4.build_no_launch(source, dest, source_commit='f' * 40, approval=w4.STAGE_APPROVAL)
    assert not dest.exists()
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
    with pytest.raises(w4.W4Refused):
        w4.rollback_interrupted(dest, approval='yes')
    unwanted = dest / 'my-user-data.md'
    unwanted.write_text('preserve')
    with pytest.raises(w4.W4Refused):
        w4.rollback_interrupted(dest, approval=w4.ROLLBACK_APPROVAL)
    assert unwanted.exists()
    unwanted.unlink()
    w4.rollback_interrupted(dest, approval=w4.ROLLBACK_APPROVAL)
    assert not dest.exists()
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
