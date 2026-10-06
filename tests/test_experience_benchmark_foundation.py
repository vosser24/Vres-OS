"""E7 Chunk 0: strict loader, digests, alias normalization, EvidencePack, held-out boundary.

DB-free. Synthetic fixtures only; no real or held-out corpus content.
"""

from __future__ import annotations

import builtins
import hashlib
import io
import json
import os
import pathlib
import re
import subprocess

import pytest

import vres_os.experience_benchmark as eb

SRC = pathlib.Path(__file__).resolve().parents[1] / "src" / "vres_os"
CANARY = "sk-" + "E7CANARY0123456789ABCDEF"  # documented fixed synthetic secret pattern


def _case(case_id="c1", prefix="dev_", **over):
    case = {
        "schema_version": 1,
        "case_id": case_id,
        "category": "static_state",
        "query": "what is x",
        "aliases": [prefix + "a", prefix + "b"],
    }
    case.update(over)
    return case


def _jsonl(cases):
    return "".join(json.dumps(c, sort_keys=True) + "\n" for c in cases)


def _expected(case_ids_to_entry):
    return {"schema_version": 1, "cases": case_ids_to_entry}


def _sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _bundle_digest(files, case_ids):
    body = json.dumps(
        {"case_ids": sorted(case_ids), "files": files},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return _sha(body)


def write_bundle(root, split, cases, expected=None, corpus_text=None, expected_text=None):
    d = root / split
    d.mkdir(parents=True, exist_ok=True)
    corpus = corpus_text if corpus_text is not None else _jsonl(cases)
    exp = (
        expected_text
        if expected_text is not None
        else json.dumps(
            expected
            if expected is not None
            else _expected({c.get("case_id", "c1"): {} for c in cases}),
            sort_keys=True,
        )
    )
    (d / "corpus.jsonl").write_bytes(corpus.encode("utf-8"))
    (d / "expected_evidence.json").write_bytes(exp.encode("utf-8"))
    files = {f"{split}/corpus.jsonl": _sha(corpus), f"{split}/expected_evidence.json": _sha(exp)}
    ids = sorted({c.get("case_id", "c1") for c in cases})
    return {"files": files, "case_ids": sorted(ids), "bundle_digest": _bundle_digest(files, ids)}


def write_manifest(root, bundles, **over):
    m = {"schema_version": 1, "heldout_version": 1, "consumed": [], "bundles": bundles}
    m.update(over)
    (root / "manifest.json").write_text(
        json.dumps(m, sort_keys=True), encoding="utf-8", newline="\n"
    )
    return m


@pytest.fixture
def root(tmp_path):
    r = tmp_path / "bench"
    r.mkdir()
    dev = write_bundle(r, "development", [_case("c1"), _case("c2")])
    adv = write_bundle(r, "adversarial", [_case("x1", "adv_")])
    held = write_bundle(r, "heldout", [_case("h1", "held_")])
    write_manifest(r, {"development": dev, "adversarial": adv, "heldout": held})
    return r


def rewrite_dev(root, cases=None, expected=None, corpus_text=None, expected_text=None):
    cases = cases if cases is not None else [_case("c1"), _case("c2")]
    dev = write_bundle(root, "development", cases, expected, corpus_text, expected_text)
    m = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    m["bundles"]["development"] = dev
    (root / "manifest.json").write_text(
        json.dumps(m, sort_keys=True), encoding="utf-8", newline="\n"
    )


# ---- 0C.0 baseline: a valid synthetic bundle loads ---


def test_valid_bundle_loads(root):
    b = eb.load_development_bundle(root, "development")
    assert [c["case_id"] for c in b["cases"]] == ["c1", "c2"]
    assert b["split"] == "development"


# ---- 0C.1-0C.9 loader strictness -----------------------------------------------------------------


def test_malformed_json_rejected(root):
    rewrite_dev(root, corpus_text='{"case_id": \n')
    with pytest.raises(eb.BenchmarkError, match="malformed"):
        eb.load_development_bundle(root, "development")


def test_duplicate_json_keys_rejected(root):
    line = (
        '{"schema_version":1,"case_id":"c1","case_id":"c2",'
        '"category":"x","query":"q","aliases":["dev_a"]}\n'
    )
    rewrite_dev(root, corpus_text=line)
    with pytest.raises(eb.BenchmarkError, match="duplicate"):
        eb.load_development_bundle(root, "development")


def test_unknown_field_rejected(root):
    rewrite_dev(root, [_case("c1", surprise=1)])
    with pytest.raises(eb.BenchmarkError, match="unknown"):
        eb.load_development_bundle(root, "development")


@pytest.mark.parametrize("missing", ["schema_version", "case_id", "category", "query", "aliases"])
def test_missing_required_field_rejected(root, missing):
    case = _case("c1")
    del case[missing]
    rewrite_dev(root, [case])
    with pytest.raises(eb.BenchmarkError, match="missing"):
        eb.load_development_bundle(root, "development")


def test_duplicate_case_ids_rejected(root):
    rewrite_dev(root, [_case("c1"), _case("c1")])
    with pytest.raises(eb.BenchmarkError, match="duplicate case"):
        eb.load_development_bundle(root, "development")


@pytest.mark.parametrize(
    "alias", ["Dev_a", "dev-a", "1dev_a", "dev a", "", "dev_" + "a" * 64, "dev_é"]
)
def test_invalid_alias_syntax_rejected(root, alias):
    rewrite_dev(root, [_case("c1", aliases=[alias])])
    with pytest.raises(eb.BenchmarkError, match="alias"):
        eb.load_development_bundle(root, "development")


def test_duplicate_alias_in_case_rejected(root):
    rewrite_dev(root, [_case("c1", aliases=["dev_a", "dev_a"])])
    with pytest.raises(eb.BenchmarkError, match="duplicate alias"):
        eb.load_development_bundle(root, "development")


def test_reserved_unmapped_alias_rejected(root):
    rewrite_dev(root, [_case("c1", aliases=["unmapped_1"])])
    with pytest.raises(eb.BenchmarkError, match="alias"):
        eb.load_development_bundle(root, "development")


def test_expected_unknown_alias_rejected(root):
    rewrite_dev(root, expected=_expected({"c1": {"relevant": ["dev_zzz"]}, "c2": {}}))
    with pytest.raises(eb.BenchmarkError, match="unknown alias"):
        eb.load_development_bundle(root, "development")


def test_expected_unknown_case_rejected(root):
    rewrite_dev(root, expected=_expected({"c1": {}, "c2": {}, "nope": {}}))
    with pytest.raises(eb.BenchmarkError, match="unknown case"):
        eb.load_development_bundle(root, "development")


def test_expected_missing_case_rejected(root):
    rewrite_dev(root, expected=_expected({"c1": {}}))
    with pytest.raises(eb.BenchmarkError, match="missing"):
        eb.load_development_bundle(root, "development")


def test_expected_unknown_field_rejected(root):
    rewrite_dev(root, expected=_expected({"c1": {"bogus": []}, "c2": {}}))
    with pytest.raises(eb.BenchmarkError, match="unknown"):
        eb.load_development_bundle(root, "development")


@pytest.mark.parametrize(
    "key",
    [
        "expected_evidence",
        "expected",
        "relevant",
        "stale",
        "answer",
        "score",
        "near_duplicate_of",
        "must_abstain",
    ],
)
def test_scoring_material_in_corpus_rejected(root, key):
    rewrite_dev(root, [_case("c1", **{key: ["dev_a"]})])
    with pytest.raises(eb.BenchmarkError, match="scoring"):
        eb.load_development_bundle(root, "development")


def test_scoring_material_nested_in_timeline_rejected(root):
    rewrite_dev(
        root,
        [
            _case(
                "c1", timeline=[{"t": 0, "op": "capture", "args": {"expected_evidence": ["dev_a"]}}]
            )
        ],
    )
    with pytest.raises(eb.BenchmarkError, match="scoring"):
        eb.load_development_bundle(root, "development")


def test_float_in_corpus_rejected(root):
    rewrite_dev(root, [_case("c1", timeline=[{"t": 0, "op": "capture", "args": {"n": 1.5}}])])
    with pytest.raises(eb.BenchmarkError, match="float"):
        eb.load_development_bundle(root, "development")


def test_bom_rejected(root):
    rewrite_dev(root, corpus_text="﻿" + _jsonl([_case("c1")]))
    with pytest.raises(eb.BenchmarkError, match="BOM"):
        eb.load_development_bundle(root, "development")


def test_crlf_normalized_to_same_digest(root):
    text = _jsonl([_case("c1"), _case("c2")])
    assert eb.sha256_hex(eb.normalize_text_bytes(text.replace("\n", "\r\n").encode())) == _sha(text)


def test_lone_cr_rejected():
    with pytest.raises(eb.BenchmarkError, match="line ending"):
        eb.normalize_text_bytes(b"a\rb\n")


# ---- 0C.10 manifest digests ----------------------------------------------------------------------


def test_invalid_manifest_file_digest_rejected(root):
    m = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    m["bundles"]["development"]["files"]["development/corpus.jsonl"] = "0" * 64
    (root / "manifest.json").write_text(json.dumps(m), encoding="utf-8", newline="\n")
    with pytest.raises(eb.BenchmarkError, match="digest"):
        eb.load_development_bundle(root, "development")


@pytest.mark.parametrize("bad", ["", "xyz", "A" * 64, "0" * 63, 7])
def test_malformed_manifest_digest_rejected(root, bad):
    m = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    m["bundles"]["development"]["files"]["development/corpus.jsonl"] = bad
    (root / "manifest.json").write_text(json.dumps(m), encoding="utf-8", newline="\n")
    with pytest.raises(eb.BenchmarkError, match="digest"):
        eb.load_development_bundle(root, "development")


def test_bundle_digest_mismatch_rejected(root):
    m = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    m["bundles"]["development"]["bundle_digest"] = "1" * 64
    (root / "manifest.json").write_text(json.dumps(m), encoding="utf-8", newline="\n")
    with pytest.raises(eb.BenchmarkError, match="digest"):
        eb.load_development_bundle(root, "development")


def test_manifest_case_ids_disagree_with_corpus_rejected(root):
    m = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    ids = ["c1", "c9"]
    files = m["bundles"]["development"]["files"]
    m["bundles"]["development"]["case_ids"] = ids
    m["bundles"]["development"]["bundle_digest"] = _bundle_digest(files, ids)
    (root / "manifest.json").write_text(json.dumps(m), encoding="utf-8", newline="\n")
    with pytest.raises(eb.BenchmarkError, match="case ids"):
        eb.load_development_bundle(root, "development")


def test_case_id_registered_in_two_bundles_rejected(root):
    adv = write_bundle(root, "adversarial", [_case("c1", "adv_")])
    m = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    m["bundles"]["adversarial"] = adv
    (root / "manifest.json").write_text(json.dumps(m), encoding="utf-8", newline="\n")
    with pytest.raises(eb.BenchmarkError, match="more than one"):
        eb.load_development_bundle(root, "development")


def test_manifest_unknown_field_rejected(root):
    m = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    m["expected"] = []
    (root / "manifest.json").write_text(json.dumps(m), encoding="utf-8", newline="\n")
    with pytest.raises(eb.BenchmarkError, match="unknown"):
        eb.load_development_bundle(root, "development")


# ---- 0C.11-0C.12 path safety ---


@pytest.mark.parametrize(
    "path",
    [
        "../outside.jsonl",
        "/abs/corpus.jsonl",
        "development/../heldout/corpus.jsonl",
        "development\\corpus.jsonl",
        "heldout/corpus.jsonl",
        "development/sub/corpus.jsonl",
        "development/other.jsonl",
    ],
)
def test_path_traversal_rejected(root, path):
    m = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    files = m["bundles"]["development"]["files"]
    files[path] = files.pop("development/corpus.jsonl")
    (root / "manifest.json").write_text(json.dumps(m), encoding="utf-8", newline="\n")
    with pytest.raises(eb.BenchmarkError, match="path"):
        eb.load_development_bundle(root, "development")


def _link_dir(target, link):
    """Directory symlink, or a Windows junction when symlinks are denied; skip if neither works."""
    try:
        os.symlink(target, link, target_is_directory=True)
        return
    except (OSError, NotImplementedError):
        pass
    if os.name == "nt":
        done = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(link), str(target)], capture_output=True
        )
        if done.returncode == 0:
            return
    pytest.skip("neither symlink nor junction creation is permitted on this host")


def test_symlink_file_escape_rejected(root, tmp_path):
    outside = tmp_path / "outside.jsonl"
    outside.write_bytes((root / "development" / "corpus.jsonl").read_bytes())
    link = root / "development" / "corpus.jsonl"
    link.unlink()
    try:
        os.symlink(outside, link)
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation not permitted on this host")
    with pytest.raises(eb.BenchmarkError, match="path"):
        eb.load_development_bundle(root, "development")


def test_symlink_or_junction_directory_escape_rejected(root, tmp_path):
    outside = tmp_path / "elsewhere"
    outside.mkdir()
    for n in ("corpus.jsonl", "expected_evidence.json"):
        (outside / n).write_bytes((root / "development" / n).read_bytes())
    for n in ("corpus.jsonl", "expected_evidence.json"):
        (root / "development" / n).unlink()
    (root / "development").rmdir()
    _link_dir(outside, root / "development")
    with pytest.raises(eb.BenchmarkError, match="path"):
        eb.load_development_bundle(root, "development")


# ---- 0C.13 split alias prefix ---


def test_alias_prefix_mismatch_rejected(root):
    rewrite_dev(root, [_case("c1", aliases=["held_a"])])
    with pytest.raises(eb.BenchmarkError, match="prefix"):
        eb.load_development_bundle(root, "development")


def test_adversarial_requires_adv_prefix(root):
    write = write_bundle(root, "adversarial", [_case("x1", "dev_")])
    m = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    m["bundles"]["adversarial"] = write
    (root / "manifest.json").write_text(json.dumps(m), encoding="utf-8", newline="\n")
    with pytest.raises(eb.BenchmarkError, match="prefix"):
        eb.load_development_bundle(root, "adversarial")


def test_adversarial_bundle_loads(root):
    assert eb.load_development_bundle(root, "adversarial")["split"] == "adversarial"


# ---- 0C.14 near_duplicate_of ---


def _nd(mapping):
    return _expected({"c1": {"near_duplicate_of": mapping}, "c2": {}})


def test_near_duplicate_valid_flat_cluster_loads(root):
    rewrite_dev(
        root,
        [_case("c1", aliases=["dev_a", "dev_b", "dev_c"]), _case("c2")],
        expected=_nd({"dev_b": "dev_a", "dev_c": "dev_a"}),
    )
    assert eb.load_development_bundle(root, "development")["expected"]["c1"][
        "near_duplicate_of"
    ] == {"dev_b": "dev_a", "dev_c": "dev_a"}


@pytest.mark.parametrize(
    "mapping,why",
    [
        ({"dev_b": "dev_zzz"}, "unknown alias"),  # missing target
        ({"dev_b": "dev_b"}, "self"),  # self target
        ({"dev_a": "dev_b", "dev_b": "dev_a"}, "cycle"),
        ({"dev_b": "dev_c", "dev_c": "dev_a"}, "canonical"),  # chained / non-canonical target
    ],
)
def test_near_duplicate_invalid_rejected(root, mapping, why):
    rewrite_dev(
        root, [_case("c1", aliases=["dev_a", "dev_b", "dev_c"]), _case("c2")], expected=_nd(mapping)
    )
    with pytest.raises(eb.BenchmarkError, match=why):
        eb.load_development_bundle(root, "development")


# ---- 0C.15-0C.16 scoring config ---


def _scoring(repeats):
    return {
        "schema_version": 1,
        "latency": {"repeats": repeats},
        "evidence": {"content_max_code_points": 400},
        "time": {"epoch_anchor": "2026-01-01T00:00:00Z", "step_seconds": 3600},
    }


@pytest.mark.parametrize("bad", [0, -4, 3, 6, True, "8", 8.0, None])
def test_latency_repeats_rejected(bad):
    with pytest.raises(eb.BenchmarkError, match="repeats"):
        eb.validate_scoring_config(_scoring(bad))


@pytest.mark.parametrize("good", [4, 8])
def test_latency_repeats_accepted(good):
    assert eb.validate_scoring_config(_scoring(good))["latency"]["repeats"] == good


def test_latency_repeats_missing_rejected():
    cfg = _scoring(4)
    del cfg["latency"]["repeats"]
    with pytest.raises(eb.BenchmarkError, match="repeats"):
        eb.validate_scoring_config(cfg)


@pytest.mark.parametrize("bad", [0, -1, True, "400", 4.0, None])
def test_content_max_code_points_rejected(bad):
    cfg = _scoring(4)
    cfg["evidence"]["content_max_code_points"] = bad
    with pytest.raises(eb.BenchmarkError, match="content_max_code_points"):
        eb.validate_scoring_config(cfg)


def test_scoring_unknown_field_and_threshold_like_rejected():
    for extra in ({"thresholds": {}}, {"pass_at": 1}):
        cfg = _scoring(4)
        cfg.update(extra)
        with pytest.raises(eb.BenchmarkError, match="unknown"):
            eb.validate_scoring_config(cfg)


# ---- 0C.17 / 0G held-out boundary ---


def test_heldout_split_name_rejected(root):
    with pytest.raises(eb.BenchmarkError, match="held-out"):
        eb.load_development_bundle(root, "heldout")


@pytest.mark.parametrize(
    "split", ["development/../heldout", "heldout/", "HELDOUT", "heldout/corpus.jsonl", "unknown"]
)
def test_heldout_path_forms_and_unknown_split_rejected(root, split):
    with pytest.raises(eb.BenchmarkError):
        eb.load_development_bundle(root, split)


def test_heldout_case_id_rejected(root):
    with pytest.raises(eb.BenchmarkError, match="held-out case"):
        eb.load_development_bundle(root, "development", case_ids=["c1", "h1"])


def test_heldout_digests_rejected(root):
    m = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    held = m["bundles"]["heldout"]
    for digest in (held["bundle_digest"], *held["files"].values()):
        with pytest.raises(eb.BenchmarkError, match="held-out digest"):
            eb.load_development_bundle(root, "development", digests=[digest])


@pytest.mark.parametrize("split", ["development", "adversarial"])
def test_development_mode_never_opens_heldout_files(root, monkeypatch, split):
    opened = []
    real_open, real_io_open = builtins.open, io.open

    def spy(file, *a, **k):
        opened.append(str(file))
        return real_open(file, *a, **k)

    def spy_io(file, *a, **k):
        opened.append(str(file))
        return real_io_open(file, *a, **k)

    monkeypatch.setattr(builtins, "open", spy)
    monkeypatch.setattr(io, "open", spy_io)
    eb.load_development_bundle(root, split)
    assert opened, "spy saw no opens; the check would be vacuous"
    assert not [p for p in opened if re.search(r"[\\/]heldout([\\/]|$)", p)]


def test_rejection_happens_before_any_open(root, monkeypatch):
    opened = []
    real_open = builtins.open
    monkeypatch.setattr(
        builtins, "open", lambda f, *a, **k: (opened.append(str(f)), real_open(f, *a, **k))[1]
    )
    with pytest.raises(eb.BenchmarkError):
        eb.load_development_bundle(root, "development", case_ids=["h1"])
    assert not [p for p in opened if "heldout" in p]


def test_heldout_bytes_corruption_is_invisible_to_development_loader(root):
    (root / "heldout" / "corpus.jsonl").write_bytes(b"\xff\xfe not json at all")
    (root / "heldout" / "expected_evidence.json").write_bytes(b"\x00garbage")
    assert eb.load_development_bundle(root, "development")["split"] == "development"


def test_heldout_manifest_entry_malformed_does_not_open_files(root):
    # A development load validates only the manifest structure, never the held-out files themselves.
    assert eb.load_manifest(root)["bundles"]["heldout"]["case_ids"] == ["h1"]


# ---- 0D canonicalization and digests -------------------------------------------------------------


def test_canonical_bytes_sorted_compact_unicode():
    assert (
        eb.canonical_bytes({"b": 1, "a": "é", "c": [True, None]})
        == '{"a":"é","b":1,"c":[true,null]}'.encode()
    )


def test_canonical_bytes_key_order_independent():
    assert eb.canonical_bytes({"a": 1, "b": 2}) == eb.canonical_bytes({"b": 2, "a": 1})


@pytest.mark.parametrize("bad", [1.5, float("nan"), float("inf"), {"a": [1.0]}])
def test_canonical_forbids_floats(bad):
    with pytest.raises(eb.BenchmarkError, match="float"):
        eb.canonical_bytes(bad)


def test_canonical_rejects_lone_surrogate_and_non_str_keys():
    with pytest.raises(eb.BenchmarkError):
        eb.canonical_bytes({"a": "\ud800"})
    with pytest.raises(eb.BenchmarkError):
        eb.canonical_bytes({1: "a"})


def test_sha256_hex_matches_hashlib():
    assert eb.sha256_hex(b"abc") == hashlib.sha256(b"abc").hexdigest()


def test_loads_strict_rejects_nan_and_duplicates():
    with pytest.raises(eb.BenchmarkError):
        eb.loads_strict("NaN")
    with pytest.raises(eb.BenchmarkError, match="duplicate"):
        eb.loads_strict('{"a":1,"a":2}')
    with pytest.raises(eb.BenchmarkError, match="duplicate"):
        eb.loads_strict('{"x":{"a":1,"a":2}}')


def test_artifact_digests_deterministic_and_distinct(root):
    b = eb.load_development_bundle(root, "development")
    again = eb.load_development_bundle(root, "development")
    assert b["digests"] == again["digests"]
    d = b["digests"]
    assert set(d) >= {"corpus", "expected_evidence", "bundle"}
    assert len({d["corpus"], d["expected_evidence"], d["bundle"]}) == 3
    assert all(re.fullmatch(r"[0-9a-f]{64}", v) for v in d.values())


def test_corpus_digest_independent_of_formatting_and_key_order(root):
    cases = [_case("c1"), _case("c2")]
    reordered = [dict(reversed(list(c.items()))) for c in cases]
    assert eb.corpus_digest(cases) == eb.corpus_digest(reordered)
    assert eb.corpus_digest(cases) != eb.corpus_digest(cases[:1])


def test_scoring_digest_changes_with_value():
    assert eb.scoring_digest(eb.validate_scoring_config(_scoring(4))) != eb.scoring_digest(
        eb.validate_scoring_config(_scoring(8))
    )


def test_schema_version_mismatch_rejected(root):
    rewrite_dev(root, [_case("c1", schema_version=2)])
    with pytest.raises(eb.BenchmarkError, match="schema_version"):
        eb.load_development_bundle(root, "development")


def test_schema_versions_are_exposed():
    assert eb.SCHEMA_VERSIONS["corpus"] == 1 and eb.SCHEMA_VERSIONS["evidence_pack"] == 1


# ---- 0E alias / runtime-key normalization ---


def test_alias_map_bidirectional_and_resolution():
    m = eb.AliasMap(["dev_a", "dev_b"])
    m.bind("dev_a", "KN-0001")
    m.bind("dev_b", "KN-0002")
    assert m.alias_for("KN-0001") == "dev_a" and m.runtime_key_for("dev_b") == "KN-0002"
    assert m.resolve(["KN-0002", "KN-0001"]) == ["dev_b", "dev_a"]


def test_alias_map_refuses_duplicate_mappings():
    m = eb.AliasMap(["dev_a", "dev_b"])
    m.bind("dev_a", "KN-1")
    with pytest.raises(eb.BenchmarkError, match="already bound"):
        m.bind("dev_a", "KN-2")
    with pytest.raises(eb.BenchmarkError, match="already bound"):
        m.bind("dev_b", "KN-1")


def test_alias_map_refuses_undeclared_alias():
    with pytest.raises(eb.BenchmarkError, match="undeclared"):
        eb.AliasMap(["dev_a"]).bind("dev_zzz", "KN-1")


def test_unknown_keys_become_deterministic_unmapped_ordinals():
    m = eb.AliasMap(["dev_a"])
    m.bind("dev_a", "KN-1")
    out = m.resolve(["KN-9", "KN-1", "KN-8", "KN-9"])
    assert out == ["unmapped_1", "dev_a", "unmapped_2", "unmapped_1"]
    assert m.resolve(["KN-8"]) == ["unmapped_2"]  # stable ordinal for the same unknown key


def test_unmapped_output_never_contains_runtime_keys():
    m = eb.AliasMap(["dev_a"])
    m.bind("dev_a", "KN-REAL-7788")
    out = m.resolve(["KN-REAL-7788", "KN-SECRET-9999"])
    blob = eb.canonical_bytes(out).decode()
    assert "KN-REAL-7788" not in blob and "KN-SECRET-9999" not in blob


def test_alias_resolution_digest_ignores_runtime_keys():
    def run(k1, k2):
        m = eb.AliasMap(["dev_a", "dev_b"])
        m.bind("dev_a", k1)
        m.bind("dev_b", k2)
        return eb.sha256_hex(eb.canonical_bytes(m.resolve([k2, k1, "OTHER-" + k1])))

    assert run("KN-20261006-aaaa", "KN-20261006-bbbb") == run(
        "KN-20271111-cccc", "KN-20271111-dddd"
    )


def test_alias_map_rejects_bad_alias_declarations():
    with pytest.raises(eb.BenchmarkError, match="alias"):
        eb.AliasMap(["Bad"])
    with pytest.raises(eb.BenchmarkError, match="duplicate alias"):
        eb.AliasMap(["dev_a", "dev_a"])


# ---- 0F EvidencePack (B2) ---


def _item(**over):
    base = {
        "alias": "dev_a",
        "kind": "knowledge",
        "content": "hello",
        "truncated": False,
        "rank": 1,
    }
    base.update(over)
    return base


def test_item_valid_roundtrip():
    assert eb.validate_pack([_item()]) == [_item()]


def test_item_unknown_field_rejected():
    with pytest.raises(eb.BenchmarkError, match="unknown"):
        eb.validate_pack([_item(extra=1)])


@pytest.mark.parametrize("field", ["alias", "kind", "content", "truncated", "rank"])
def test_item_missing_field_rejected(field):
    item = _item()
    del item[field]
    with pytest.raises(eb.BenchmarkError, match="missing"):
        eb.validate_pack([item])


@pytest.mark.parametrize("kind", ["source_chunk", "raw", "", None, "Knowledge", 1])
def test_item_invalid_kind_rejected(kind):
    with pytest.raises(eb.BenchmarkError, match="kind"):
        eb.validate_pack([_item(kind=kind)])


@pytest.mark.parametrize("kind", ["knowledge", "chunk", "procedure", "experience"])
def test_item_valid_kinds(kind):
    assert eb.validate_pack([_item(kind=kind)])[0]["kind"] == kind


@pytest.mark.parametrize("rank", [0, -1, True, False, "1", 1.0, None])
def test_item_rank_must_be_positive_int(rank):
    with pytest.raises(eb.BenchmarkError, match="rank"):
        eb.validate_pack([_item(rank=rank)])


@pytest.mark.parametrize("alias", ["Bad", "dev-a", "", None, 5, "KN-20261006-abc"])
def test_item_invalid_alias_rejected(alias):
    with pytest.raises(eb.BenchmarkError, match="alias"):
        eb.validate_pack([_item(alias=alias)])


def test_item_unmapped_alias_allowed():
    assert eb.validate_pack([_item(alias="unmapped_3")])[0]["alias"] == "unmapped_3"


@pytest.mark.parametrize("trunc", [0, 1, "false", None])
def test_item_truncated_must_be_bool(trunc):
    with pytest.raises(eb.BenchmarkError, match="truncated"):
        eb.validate_pack([_item(truncated=trunc)])


def test_item_content_must_be_str():
    with pytest.raises(eb.BenchmarkError, match="content"):
        eb.validate_pack([_item(content=None)])


@pytest.mark.parametrize(
    "key",
    [
        "id",
        "chunk_id",
        "source_id",
        "knowledge_id",
        "memory_key",
        "runtime_key",
        "chunk_key",
        "score",
        "path_or_uri",
        "reasoning",
        "chain_of_thought",
        "vector",
    ],
)
def test_prohibited_hidden_fields_cannot_survive(key):
    with pytest.raises(eb.BenchmarkError, match="prohibited"):
        eb.validate_pack([_item(**{key: "x"})])


def test_secret_canary_fails_closed_on_build():
    with pytest.raises(eb.BenchmarkError, match="secret"):
        eb.build_evidence_item("dev_a", "chunk", "token is " + CANARY, 1, max_code_points=400)


def test_secret_canary_fails_closed_on_validate():
    with pytest.raises(eb.BenchmarkError, match="secret"):
        eb.validate_pack([_item(content="x " + CANARY)])


def test_canary_split_by_truncation_boundary_still_caught_before_cut():
    content = "a" * 10 + " " + CANARY
    with pytest.raises(eb.BenchmarkError, match="secret"):
        eb.build_evidence_item("dev_a", "chunk", content, 1, max_code_points=12)


def test_nfc_determinism():
    composed = eb.build_evidence_item("dev_a", "knowledge", "é", 1, max_code_points=50)
    decomposed = eb.build_evidence_item("dev_a", "knowledge", "é", 1, max_code_points=50)
    assert composed == decomposed and composed["content"] == "é"


def test_truncation_is_code_point_cut_with_flag():
    item = eb.build_evidence_item("dev_a", "knowledge", "abcdef", 1, max_code_points=4)
    assert item["content"] == "abcd" and item["truncated"] is True
    exact = eb.build_evidence_item("dev_a", "knowledge", "abcd", 1, max_code_points=4)
    assert exact["content"] == "abcd" and exact["truncated"] is False
    astral = eb.build_evidence_item(
        "dev_a", "knowledge", "\U0001f600\U0001f600\U0001f600", 1, max_code_points=2
    )
    assert astral["content"] == "\U0001f600\U0001f600" and astral["truncated"] is True


def test_truncation_counts_after_nfc():
    # 'e' + combining acute is 2 code points raw but 1 after NFC: it fits a 1-code-point budget.
    item = eb.build_evidence_item("dev_a", "knowledge", "é", 1, max_code_points=1)
    assert item["truncated"] is False and item["content"] == "é"


def test_truncation_deterministic():
    a = eb.build_evidence_item("dev_a", "knowledge", "x" * 100, 1, max_code_points=10)
    b = eb.build_evidence_item("dev_a", "knowledge", "x" * 100, 1, max_code_points=10)
    assert a == b


@pytest.mark.parametrize("n", [0, -1, True, "5", 1.0])
def test_build_rejects_bad_max_code_points(n):
    with pytest.raises(eb.BenchmarkError, match="max_code_points"):
        eb.build_evidence_item("dev_a", "knowledge", "x", 1, max_code_points=n)


def test_items_differing_only_in_content_serialize_differently():
    a = eb.build_pack(
        [eb.build_evidence_item("dev_a", "knowledge", "alpha", 1, max_code_points=50)]
    )
    b = eb.build_pack([eb.build_evidence_item("dev_a", "knowledge", "beta", 1, max_code_points=50)])
    assert eb.pack_bytes(a) != eb.pack_bytes(b)
    assert eb.pack_digest(a) != eb.pack_digest(b)


def test_pack_total_order_rank_then_alias_and_input_order_independent():
    items = [
        eb.build_evidence_item(a, "knowledge", "t", r, max_code_points=10)
        for a, r in (("dev_b", 2), ("dev_c", 1), ("dev_a", 2))
    ]
    pack = eb.build_pack(items)
    assert [(i["rank"], i["alias"]) for i in pack] == [(1, "dev_c"), (2, "dev_a"), (2, "dev_b")]
    assert eb.pack_digest(pack) == eb.pack_digest(eb.build_pack(list(reversed(items))))


def test_pack_exact_alias_repeats_are_kept():
    items = [
        eb.build_evidence_item("dev_a", "knowledge", "t", r, max_code_points=10) for r in (1, 2, 3)
    ]
    assert [i["alias"] for i in eb.build_pack(items)] == ["dev_a"] * 3


def test_pack_serialization_has_no_float_and_only_closed_keys():
    pack = eb.build_pack([eb.build_evidence_item("dev_a", "chunk", "t", 1, max_code_points=10)])
    assert set(json.loads(eb.pack_bytes(pack))[0]) == {
        "alias",
        "kind",
        "content",
        "truncated",
        "rank",
    }


# ---- 0J boundary guards ---


def test_no_runtime_module_imports_benchmark_code():
    offenders = [
        p.name
        for p in SRC.glob("*.py")
        if p.name != "experience_benchmark.py"
        and "experience_benchmark" in p.read_text(encoding="utf-8")
    ]
    assert offenders == []


def test_benchmark_module_has_no_cli_or_mcp_surface_and_no_sql():
    text = (SRC / "experience_benchmark.py").read_text(encoding="utf-8")
    assert not re.search(
        r"^\s*(?:from|import)\s+(?:typer|click|argparse|mcp|psycopg|\.db|\.repository)", text, re.M
    )
    assert "@app.command" not in text and "SELECT " not in text and "INSERT " not in text


# ---- Chunk 0 repair R1: timeline ordinal `t` and deterministic time config ---


def _tl(*ts, **extra):
    return [{"t": t, "op": "capture", **extra} for t in ts]


def test_timeline_step_missing_t_rejected(root):
    rewrite_dev(root, [_case("c1", timeline=[{"op": "capture"}])])
    with pytest.raises(eb.BenchmarkError, match="missing"):
        eb.load_development_bundle(root, "development")


@pytest.mark.parametrize("bad", [True, False, -1, 1.5, "1", None])
def test_timeline_t_wrong_type_or_negative_rejected(root, bad):
    case = _case("c1", timeline=[{"t": bad, "op": "capture"}])
    rewrite_dev(root, [case], corpus_text=json.dumps(case, sort_keys=True) + "\n")
    with pytest.raises(
        eb.BenchmarkError, match="timeline t|float"
    ):  # a float t dies at the no-float parse rule
        eb.load_development_bundle(root, "development")


@pytest.mark.parametrize("ts", [(0, 0), (2, 1), (0, 2, 1)])
def test_timeline_t_not_strictly_increasing_rejected(root, ts):
    rewrite_dev(root, [_case("c1", timeline=_tl(*ts))])
    with pytest.raises(eb.BenchmarkError, match="strictly increasing"):
        eb.load_development_bundle(root, "development")


def test_timeline_strictly_increasing_t_accepted(root):
    rewrite_dev(root, [_case("c1", timeline=_tl(0, 1, 5))])
    loaded = eb.load_development_bundle(root, "development")
    assert [s["t"] for s in loaded["cases"][0]["timeline"]] == [0, 1, 5]


@pytest.mark.parametrize("drop", ["epoch_anchor", "step_seconds"])
def test_time_config_missing_field_rejected(drop):
    cfg = _scoring(4)
    del cfg["time"][drop]
    with pytest.raises(eb.BenchmarkError, match=drop):
        eb.validate_scoring_config(cfg)


def test_time_config_missing_block_rejected():
    cfg = _scoring(4)
    del cfg["time"]
    with pytest.raises(eb.BenchmarkError, match="time"):
        eb.validate_scoring_config(cfg)


@pytest.mark.parametrize(
    "bad",
    [
        "2026-01-01",
        "2026-01-01T00:00:00",
        "2026-01-01T00:00:00+02:00",
        "2026-01-01T00:00:00.5Z",
        "2026-13-01T00:00:00Z",
        "2026-01-01 00:00:00Z",
        20260101,
        None,
    ],
)
def test_time_config_bad_anchor_rejected(bad):
    cfg = _scoring(4)
    cfg["time"]["epoch_anchor"] = bad
    with pytest.raises(eb.BenchmarkError, match="epoch_anchor"):
        eb.validate_scoring_config(cfg)


@pytest.mark.parametrize("bad", [0, -1, True, "60", 1.5, None])
def test_time_config_bad_step_rejected(bad):
    cfg = _scoring(4)
    cfg["time"]["step_seconds"] = bad
    with pytest.raises(eb.BenchmarkError, match="step_seconds"):
        eb.validate_scoring_config(cfg)


def test_time_config_unknown_field_rejected():
    cfg = _scoring(4)
    cfg["time"]["jitter"] = 1
    with pytest.raises(eb.BenchmarkError, match="unknown"):
        eb.validate_scoring_config(cfg)


def test_time_config_valid_accepted_and_instant_deterministic():
    cfg = eb.validate_scoring_config(_scoring(4))
    t = cfg["time"]
    assert eb.benchmark_instant(t, 0) == "2026-01-01T00:00:00Z"
    assert eb.benchmark_instant(t, 3) == "2026-01-01T03:00:00Z"
    assert eb.benchmark_instant(t, 3) == eb.benchmark_instant(dict(t), 3)
    assert eb.benchmark_instant(
        {"epoch_anchor": "2026-01-01T00:00:00Z", "step_seconds": 1}, 90
    ) == ("2026-01-01T00:01:30Z")


@pytest.mark.parametrize("bad", [-1, True, 1.5, "1", None])
def test_benchmark_instant_rejects_bad_ordinal(bad):
    with pytest.raises(eb.BenchmarkError, match="ordinal"):
        eb.benchmark_instant(_scoring(4)["time"], bad)


# ---- Chunk 0 repair R2: memory_not_needed ---


@pytest.mark.parametrize("flag", [True, False])
def test_memory_not_needed_boolean_accepted(root, flag):
    rewrite_dev(root, expected=_expected({"c1": {"memory_not_needed": flag}, "c2": {}}))
    loaded = eb.load_development_bundle(root, "development")
    assert loaded["expected"]["c1"]["memory_not_needed"] is flag


@pytest.mark.parametrize("bad", [1, 0, "true", None, [], {}])
def test_memory_not_needed_non_boolean_rejected(root, bad):
    rewrite_dev(root, expected=_expected({"c1": {"memory_not_needed": bad}, "c2": {}}))
    with pytest.raises(eb.BenchmarkError, match="memory_not_needed must be a boolean"):
        eb.load_development_bundle(root, "development")


def test_memory_not_needed_not_allowed_in_corpus(root):
    rewrite_dev(root, [_case("c1", memory_not_needed=True)])
    with pytest.raises(eb.BenchmarkError, match="scoring"):
        eb.load_development_bundle(root, "development")


# ---- Chunk 0 repair R3: expected digest binds schema version ---


def test_expected_digest_is_over_versioned_object(root):
    loaded = eb.load_development_bundle(root, "development")
    versioned = {"schema_version": 1, "cases": loaded["expected"]}
    assert loaded["digests"]["expected_evidence"] == eb.sha256_hex(eb.canonical_bytes(versioned))
    assert eb.expected_digest(loaded["expected"]) == loaded["digests"]["expected_evidence"]


def test_expected_digest_differs_under_different_schema_identity(monkeypatch):
    cases = {"c1": {"relevant": ["dev_a"]}}
    before = eb.expected_digest(cases)
    monkeypatch.setitem(eb.SCHEMA_VERSIONS, "expected_evidence", 2)
    assert eb.expected_digest(cases) != before


def test_expected_digest_key_order_independent():
    a = {"c1": {"relevant": ["dev_a"], "stale": ["dev_b"]}, "c2": {}}
    b = {"c2": {}, "c1": {"stale": ["dev_b"], "relevant": ["dev_a"]}}
    assert eb.expected_digest(a) == eb.expected_digest(b)
