from pathlib import Path

from vres_os.ingestion import classify_mechanically, extract, sha256_file


def test_plain_extraction_and_hash(tmp_path: Path):
    p = tmp_path / "supplier_process.md"
    p.write_text("# Supplier process\nApproval workflow and process steps", encoding="utf-8")
    doc = extract(p)
    assert doc and "Approval workflow" in doc.text
    assert len(sha256_file(p)) == 64
    kind, confidence = classify_mechanically(p, doc)
    assert kind == "process"
    assert confidence >= .57
