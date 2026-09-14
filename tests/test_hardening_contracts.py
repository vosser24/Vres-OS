import json
import zipfile
from pathlib import Path

import pytest

from vres_os.chunking import chunk_text
from vres_os.config import ConfigStore, DatabaseConfig
from vres_os.embeddings import dot_same_dimension, embedding_text
from vres_os.ingestion import InputTooLarge, UnsafeContainer, _bounded_plain, _ooxml_preflight
from vres_os.model_policy import empirical_dominates
from vres_os.optimization import contracts_equivalent, pareto_gate
from vres_os.project import normalize_remote
from vres_os.refresh import validate_reviewed_delta


def test_config_rejects_unknown_fields_and_invalid_ssl(tmp_path: Path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"mystery": True}), encoding="utf-8")
    with pytest.raises(ValueError, match="Unknown top-level"):
        ConfigStore(path).load()
    with pytest.raises(ValueError, match="sslmode"):
        DatabaseConfig(sslmode="anything").validate()


def test_git_remote_identity_normalizes_ssh_and_https():
    assert normalize_remote("git@GitHub.com:Vosser24/Vres-OS.git") == "github.com/vosser24/vres-os"
    assert normalize_remote("https://github.com/Vosser24/Vres-OS.git") == "github.com/vosser24/vres-os"


def test_chunker_never_exceeds_target_even_without_paragraphs():
    chunks = chunk_text("x" * 10_000, target_chars=512, overlap_chars=64)
    assert len(chunks) > 1
    assert max(len(c.content) for c in chunks) <= 512
    with pytest.raises(ValueError):
        chunk_text("abc", target_chars=64)


def test_pareto_requires_independent_validation_and_complete_metrics():
    blocked = pareto_gate(
        baseline_quality=1.0, candidate_quality=1.0,
        baseline_runtime_ms=1000, candidate_runtime_ms=900,
        baseline_tokens=1000, candidate_tokens=900,
        validation_passed=False,
    )
    assert not blocked.auto_promote
    assert "validation" in blocked.reason
    incomplete = pareto_gate(
        baseline_quality=1.0, candidate_quality=None,
        baseline_runtime_ms=1000, candidate_runtime_ms=900,
        baseline_tokens=1000, candidate_tokens=900, validation_passed=True,
    )
    assert not incomplete.auto_promote
    assert "incomplete" in incomplete.reason


def test_protected_procedure_contracts_must_match_exactly():
    baseline = {
        "input_contract": {"files": 2},
        "invariants": ["top=net sales"],
        "validation_contract": ["totals reconcile"],
        "output_contract": {"rows": 10},
    }
    assert contracts_equivalent(baseline, dict(baseline))
    changed = dict(baseline)
    changed["output_contract"] = {"rows": 20}
    assert not contracts_equivalent(baseline, changed)


def test_model_empirical_challenger_must_be_pareto_better():
    base = {"success_rate": .98, "quality": .95, "runtime": 10.0, "tokens": 1000.0}
    assert empirical_dominates(base, {"success_rate": .98, "quality": .95, "runtime": 9.0, "tokens": 900.0})
    assert not empirical_dominates(base, {"success_rate": .98, "quality": .95, "runtime": 8.0, "tokens": 1001.0})
    assert not empirical_dominates(base, {"success_rate": .99, "quality": .96, "runtime": 9.0})


def test_embedding_prefix_and_dimension_safety():
    assert embedding_text("intfloat/multilingual-e5-base", "hello", query=True) == "query: hello"
    assert embedding_text("intfloat/multilingual-e5-base", "hello", query=False) == "passage: hello"
    with pytest.raises(ValueError, match="dimension"):
        dot_same_dimension([1.0, 2.0], [1.0])


def test_refresh_validation_binds_exact_reviewed_artifact(tmp_path):
    from vres_os.validation import artifact_manifest
    data = {"refresh_key": "R-1", "delta_summary": {"new": ["test"]}, "knowledge_version": "2"}
    p = tmp_path / "delta.json"
    p.write_text(json.dumps(data))
    manifest = artifact_manifest(tmp_path, ["delta.json"])
    validate_reviewed_delta(tmp_path, "delta.json", manifest, "R-1", data["delta_summary"], "2")
    with pytest.raises(ValueError, match="differ"):
        validate_reviewed_delta(tmp_path, "delta.json", manifest, "R-2", data["delta_summary"], "2")
    p.write_text("{}")
    with pytest.raises(ValueError, match="changed"):
        validate_reviewed_delta(tmp_path, "delta.json", manifest, "R-1", data["delta_summary"], "2")


def test_large_plain_file_is_bounded_and_marks_omission(tmp_path: Path):
    p = tmp_path / "huge.txt"
    from vres_os.ingestion import MAX_TEXT_BYTES
    p.write_bytes(b"a" * (MAX_TEXT_BYTES + 1024))
    doc = _bounded_plain(p)
    assert doc.metadata["sampled"] is True
    assert "middle omitted" in doc.text
    assert len(doc.text.encode("utf-8")) < MAX_TEXT_BYTES + 1024


def test_ooxml_preflight_rejects_suspicious_expansion(tmp_path: Path):
    p = tmp_path / "bomb.xlsx"
    # Highly compressible payload over the ratio threshold and 32 MB uncompressed threshold.
    payload = b"0" * (33 * 1024 * 1024)
    with zipfile.ZipFile(p, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("xl/sharedStrings.xml", payload)
    with pytest.raises(UnsafeContainer):
        _ooxml_preflight(p)


def test_ooxml_preflight_rejects_raw_container_over_limit(tmp_path: Path, monkeypatch):
    p = tmp_path / "huge.xlsx"
    p.write_bytes(b"x")
    from vres_os import ingestion
    class FakeStat:
        st_size = ingestion.MAX_CONTAINER_BYTES + 1
    monkeypatch.setattr(Path, "stat", lambda self: FakeStat())
    with pytest.raises(InputTooLarge):
        _ooxml_preflight(p)
