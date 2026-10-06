"""Real-asset tests for the committed E7 development and adversarial bundles (DB-free)."""

from __future__ import annotations

import builtins
import copy
import importlib.util
import json
import re
import shutil
from pathlib import Path

import pytest

from vres_os import experience_benchmark as eb

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO / "benchmarks" / "experience_e7"


def _audit_module():
    spec = importlib.util.spec_from_file_location(
        "e7_corpus_audit", REPO / "scripts" / "e7_corpus_audit.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def bundles():
    return {s: eb.load_development_bundle(ROOT, s) for s in eb.DEVELOPMENT_SPLITS}


def test_manifest_and_scoring_load_and_bind():
    manifest = eb.load_manifest(ROOT)
    assert manifest["heldout_status"] == "not_authored"
    assert set(manifest["bundles"]) == {"development", "adversarial"}
    assert eb.scoring_digest(eb.load_scoring(ROOT)) == manifest["scoring_digest"]


def test_heldout_files_do_not_exist():
    assert not (ROOT / "heldout").exists()
    assert not [p for p in ROOT.rglob("*") if "heldout" in p.name.lower()]
    assert not (ROOT / "thresholds.json").exists()


def test_counts(bundles):
    assert len(bundles["development"]["cases"]) == 24
    assert len(bundles["adversarial"]["cases"]) == 20


def test_case_ids_and_aliases_split_disjoint(bundles):
    ids = {s: {c["case_id"] for c in b["cases"]} for s, b in bundles.items()}
    assert not ids["development"] & ids["adversarial"]
    aliases = {s: {a for c in b["cases"] for a in c["aliases"]} for s, b in bundles.items()}
    assert not aliases["development"] & aliases["adversarial"]
    assert all(a.startswith("dev_") for a in aliases["development"])
    assert all(a.startswith("adv_") for a in aliases["adversarial"])


def test_every_case_has_expected_evidence(bundles):
    for b in bundles.values():
        assert {c["case_id"] for c in b["cases"]} == set(b["expected"])


def test_audit_script_passes_on_committed_assets():
    report = _audit_module().audit(ROOT)
    assert report["ok"], report["problems"]
    assert all(r["ok"] for r in report["checks"].values())


def test_all_18_red_team_families_covered():
    report = _audit_module().audit(ROOT)
    assert sorted(map(int, report["family_coverage"])) == list(range(1, 19))
    assert all(report["family_coverage"][str(f)] for f in range(1, 19))


def test_family_11_is_explicitly_not_applicable(bundles):
    entry = bundles["adversarial"]["expected"]["adv_second_user"]["security"]
    assert entry["assertions"] == ["second_user_isolation"]
    assert entry["not_applicable_reason"]


def test_a9_subcriteria_are_encoded(bundles):
    exp = bundles["adversarial"]["expected"]
    assert "burst_fails_closed" in exp["adv_flood_burst"]["security"]["assertions"]
    flood = bundles["adversarial"]["cases"]
    burst = next(c for c in flood if c["case_id"] == "adv_flood_burst")
    attempts = [s for s in burst["timeline"] if s["op"] == "experience_consolidate"]
    assert len(attempts) > 20  # beyond the owner's open-proposal cap, without naming any budget
    assert exp["adv_varied_poison"]["security"]["lineage_groups"]
    assert exp["adv_diversity"]["security"]["lineage_groups"]
    assert "recurrence_cannot_raise_authority" in exp["adv_recurrence"]["security"]["assertions"]


def test_rebuild_from_parsed_assets_is_byte_identical(bundles):
    for split, b in bundles.items():
        assert eb.render_jsonl(b["cases"]) == (ROOT / split / "corpus.jsonl").read_bytes()
        expected = {"schema_version": 1, "cases": b["expected"]}
        assert eb.render_json(expected) == (ROOT / split / "expected_evidence.json").read_bytes()
    cfg = eb.load_scoring(ROOT)
    assert eb.render_json(cfg) == (ROOT / "scoring.json").read_bytes()


def test_mutating_a_corpus_fact_changes_corpus_and_bundle_identity(bundles):
    b = bundles["development"]
    cases = copy.deepcopy(b["cases"])
    step = next(s for c in cases for s in c.get("timeline", []) if s["op"] == "knowledge_propose")
    step["args"]["statement"] += " (changed)"
    assert eb.corpus_digest(cases) != b["digests"]["corpus"]
    manifest = eb.load_manifest(ROOT)["bundles"]["development"]
    files = dict(manifest["files"])
    files["development/corpus.jsonl"] = eb.sha256_hex(eb.render_jsonl(cases))
    assert eb.bundle_digest(files, manifest["case_ids"]) != manifest["bundle_digest"]


def test_mutating_an_expected_answer_changes_expected_and_bundle_identity(bundles):
    b = bundles["development"]
    expected = copy.deepcopy(b["expected"])
    entry = expected["dev_static_port"]
    entry["relevant"], entry["irrelevant"] = entry["irrelevant"], entry["relevant"]
    assert eb.expected_digest(expected) != b["digests"]["expected_evidence"]
    manifest = eb.load_manifest(ROOT)["bundles"]["development"]
    files = dict(manifest["files"])
    files["development/expected_evidence.json"] = eb.sha256_hex(
        eb.render_json({"schema_version": 1, "cases": expected})
    )
    assert eb.bundle_digest(files, manifest["case_ids"]) != manifest["bundle_digest"]


def test_mutating_scoring_config_changes_scoring_identity():
    cfg = copy.deepcopy(eb.load_scoring(ROOT))
    cfg["retrieval"]["k_values"] = [1, 3]
    assert eb.scoring_digest(cfg) != eb.load_manifest(ROOT)["scoring_digest"]


def _copy_root(tmp_path):
    dst = tmp_path / "bench"
    shutil.copytree(ROOT, dst)
    return dst


def test_on_disk_corpus_mutation_is_rejected(tmp_path):
    dst = _copy_root(tmp_path)
    path = dst / "development" / "corpus.jsonl"
    path.write_bytes(path.read_bytes().replace(b"8417", b"8418", 1))
    with pytest.raises(eb.BenchmarkError, match="digest"):
        eb.load_development_bundle(dst, "development")


def test_on_disk_scoring_mutation_is_rejected(tmp_path):
    dst = _copy_root(tmp_path)
    path = dst / "scoring.json"
    cfg = json.loads(path.read_text(encoding="utf-8"))
    cfg["pack_budget_tokens"] = 1
    cfg["evidence"]["pack_budget_tokens"] = 1999
    del cfg["pack_budget_tokens"]
    path.write_bytes(eb.render_json(cfg))
    with pytest.raises(eb.BenchmarkError, match="scoring digest mismatch"):
        eb.load_scoring(dst)


def test_development_loading_never_opens_heldout_paths(monkeypatch):
    opened: list[str] = []
    real_open = builtins.open

    def spy(file, *args, **kwargs):
        opened.append(str(file))
        return real_open(file, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", spy)
    for split in eb.DEVELOPMENT_SPLITS:
        eb.load_development_bundle(ROOT, split)
    eb.load_scoring(ROOT)
    assert opened
    assert not [p for p in opened if "heldout" in p.lower()]


def test_heldout_loader_request_is_rejected():
    with pytest.raises(eb.BenchmarkError, match="held-out"):
        eb.load_development_bundle(ROOT, "heldout")


def test_outcome_cases_keep_private_criteria_out_of_the_public_task(bundles):
    for b in bundles.values():
        for case in b["cases"]:
            entry = b["expected"][case["case_id"]]
            if "outcome" not in entry:
                assert "task" not in case
                continue
            public = json.dumps(case["task"]).lower()
            tokens = set(re.findall(r"[a-z0-9_]+", public))
            texts = [
                str(v).lower()
                for step in case["timeline"]
                for k, v in step.get("args", {}).items()
                if k in ("statement", "objective", "method", "quote", "text")
            ]
            assert "forbidden" not in public and "criteria" not in public
            for crit in entry["outcome"]["criteria"]:
                assert crit["id"].lower() not in tokens
            for text in texts:  # precedent wording must not be copied into the worker input
                assert text not in public
