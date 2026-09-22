from pathlib import Path

import pytest

from vres_os.ingestion import ParserInputError, classify_mechanically, extract, sha256_file


def test_plain_extraction_and_hash(tmp_path: Path):
    p = tmp_path / "supplier_process.md"
    p.write_text("# Supplier process\nApproval workflow and process steps", encoding="utf-8")
    doc = extract(p)
    assert doc and "Approval workflow" in doc.text
    assert len(sha256_file(p)) == 64
    kind, confidence = classify_mechanically(p, doc)
    assert kind == "process"
    assert confidence >= .57


def test_json_without_bom_still_parses(tmp_path: Path):
    p = tmp_path / "plain.json"
    p.write_text('{"kind":"plain","value":42}', encoding="utf-8")
    doc = extract(p)
    assert doc is not None
    assert doc.text == '{"kind":"plain","value":42}'
    assert doc.metadata["structured"] is True


def test_json_with_utf8_bom_parses(tmp_path: Path):
    p = tmp_path / "bom.json"
    p.write_bytes(b"\xef\xbb\xbf" + b'{"kind":"bom","value":42}')
    doc = extract(p)
    assert doc is not None
    assert doc.text == '{"kind":"bom","value":42}'
    assert doc.metadata["structured"] is True
    assert p.read_bytes().startswith(b"\xef\xbb\xbf")


def test_malformed_json_with_utf8_bom_still_errors(tmp_path: Path):
    p = tmp_path / "bad-bom.json"
    p.write_bytes(b"\xef\xbb\xbf" + b'{"kind":"broken",')
    with pytest.raises(ParserInputError):
        extract(p)


def test_plain_json_is_not_classified_as_code_by_js_substring(tmp_path: Path):
    p = tmp_path / "plain.json"
    p.write_text('{"kind":"plain","value":42}', encoding="utf-8")
    doc = extract(p)
    kind, confidence = classify_mechanically(p, doc)
    assert kind == "document"
    assert confidence == 0.5


def test_real_js_file_still_classifies_as_code(tmp_path: Path):
    p = tmp_path / "example.js"
    p.write_text('function greet(name) { return "hello " + name; }\n', encoding="utf-8")
    doc = extract(p)
    kind, confidence = classify_mechanically(p, doc)
    assert kind == "code"
    assert confidence == 1.0


def test_json_with_process_signal_still_classifies_as_process(tmp_path: Path):
    p = tmp_path / "process.json"
    p.write_text('{"kind":"process","note":"process definition"}', encoding="utf-8")
    doc = extract(p)
    kind, confidence = classify_mechanically(p, doc)
    assert kind == "process"
    assert confidence == pytest.approx(0.57)
