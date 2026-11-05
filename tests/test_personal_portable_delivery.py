"""One integrated create-only delivery test with a disposable synthetic source fixture.

The prior exact-runtime Windows gate is separately accepted; this test checks
packaging, integrity, launcher contents, deterministic ZIP and refusal behavior.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import zipfile
from pathlib import Path

import pytest

MODULE = Path(__file__).resolve().parents[1] / 'src' / 'vres_os' / 'personal_portable_delivery.py'
spec = importlib.util.spec_from_file_location('personal_portable_delivery', MODULE)
assert spec and spec.loader
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


def test_one_complete_portable_delivery_byte_integrity_and_fail_closed(tmp_path, monkeypatch):
    source = tmp_path / 'previous-accepted-source'
    source.mkdir()
    expected_blobs = {}
    source_original = {}
    # Construct a local stand-in for exactly the same nine named pinned paths;
    # patch only the test instance's expected SHAs, never published production pins.
    for i, rel in enumerate(sorted(builder.PINNED_BLOBS)):
        raw = (f'# Synthetic disposable module {i}: {rel}\n').encode('ascii')
        path = source.joinpath(*rel.split('/'))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        expected_blobs[rel] = builder._git_blob_sha1(raw)
        source_original[rel] = raw
    monkeypatch.setattr(builder, 'PINNED_BLOBS', expected_blobs)
    out = tmp_path / 'Vres-PortableDesk-Delivery-TestA'

    with pytest.raises(builder.DeliveryRefused):
        builder.build(str(source), str(out))
    assert not out.exists()
    bad = source / 'src' / 'vres_os' / 'personal_desk_cli.py'
    clean = bad.read_bytes()
    bad.write_bytes(clean + b'CHANGED')
    with pytest.raises(builder.DeliveryRefused, match='blob mismatch'):
        builder.build(str(source), str(out), approved=True)
    assert not out.exists()  # all nine source blobs checked before any output writes
    bad.write_bytes(clean)

    receipt = builder.build(str(source), str(out), approved=True)
    assert receipt['files_in_zip'] == 12
    assert receipt['installed_vres_modified'] is False
    assert receipt['task_store_created'] is False
    folder = out / 'Vres-PortableDesk'
    zpath = out / 'Vres-PortableDesk.zip'
    assert hashlib.sha256(zpath.read_bytes()).hexdigest() == receipt['zip_sha256']
    manifest = json.loads((folder / 'SOURCE-MANIFEST.json').read_text())
    assert manifest['source_commit'] == '76c3eca84677343883464dee4c1d8ba33d30cbad'
    assert manifest['windows_integration'] == 'NOT_RUN_FOR_THIS_PACKAGE'
    assert len(manifest['runtime_files']) == 9
    assert {v['path']: v['git_blob_sha1'] for v in manifest['runtime_files']} == expected_blobs
    assert {rel: source.joinpath(*rel.split('/')).read_bytes() for rel in source_original} == source_original
    script = (folder / 'Desk.ps1').read_text(encoding='ascii')
    for token in ('Get-AuthenticodeSignature', 'Get-FileHash', "'-I','-S','-B'",
                  "'init','add','focus','open','remove'", '[switch]$ShowAction', 'exit $LASTEXITCODE'):
        assert token in script
    for rel, raw in source_original.items():
        assert folder.joinpath(*rel.split('/')).read_bytes() == raw
        assert hashlib.sha256(raw).hexdigest() in script
    with zipfile.ZipFile(zpath) as z:
        assert len(z.namelist()) == 12
        for rel in source_original:
            assert z.read('Vres-PortableDesk/' + rel) == source_original[rel]
        assert z.read('Vres-PortableDesk/Desk.ps1') == script.encode('ascii')
    with pytest.raises(builder.DeliveryRefused, match='exists'):
        builder.build(str(source), str(out), approved=True)

    out2 = tmp_path / 'Vres-PortableDesk-Delivery-TestB'
    receipt2 = builder.build(str(source), str(out2), approved=True)
    assert receipt2['zip_sha256'] == receipt['zip_sha256']
    assert (out2 / 'Vres-PortableDesk.zip').read_bytes() == zpath.read_bytes()
    assert sorted(p.name for p in out.iterdir()) == [
        'DELIVERY-RECEIPT.json', 'Vres-PortableDesk', 'Vres-PortableDesk.zip'
    ]
