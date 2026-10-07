"""#176 E7 Chunk 2: DB-free contract of the benchmark runtime adapters (no database)."""

import json
from pathlib import Path

import pytest

from vres_os import experience_benchmark as eb
from vres_os import experience_benchmark_runtime as rt
from vres_os import experience_retrieval as er
from vres_os.experience_benchmark import BenchmarkError

ROOT = Path(__file__).resolve().parents[1] / "benchmarks" / "experience_e7"
SCORING = eb.load_scoring(ROOT)


def _amap():
    m = eb.AliasMap(["dev_a", "dev_b", "dev_src"])
    m.bind("dev_a", "K-a")
    m.bind("dev_b", "K-b")
    m.bind("dev_src", "SRC-1")
    return m


def _amap2():
    m = eb.AliasMap(["dev_a", "dev_src"])
    m.bind("dev_a", "SRC-2")
    m.bind("dev_src", "SRC-1")
    return m


def test_retrieval_identity_is_closed_and_hashes_the_released_policy():
    ident = rt.retrieval_identity()
    assert set(ident) == {
        "experience_retrieval_schema",
        "e5_policy_digest",
        "result_schema_version",
        "evidence_pack_schema",
    }
    assert ident["experience_retrieval_schema"] == er.SCHEMA_VERSION == "176.e5.v1"
    assert ident["e5_policy_digest"] == eb.sha256_hex(eb.canonical_bytes(er.POLICY))
    assert ident["evidence_pack_schema"] == eb.SCHEMA_VERSIONS["evidence_pack"]


def test_raw_row_resolves_source_then_knowledge_and_never_leaks_keys():
    row = {
        "chunk_key": "CHUNK-1",
        "source_id": 7,
        "knowledge_id": 9,
        "source_key": "SRC-1",
        "knowledge_key": None,
        "section": "Intro",
        "content": "port is 8417",
    }
    entry = rt.raw_row_entry(row, _amap(), 1)
    assert entry == {
        "alias": "dev_src",
        "kind": "chunk",
        "content": "Intro\nport is 8417",
        "rank": 1,
    }
    knowledge_owned = dict(row, source_key=None, knowledge_key="K-b", section=None)
    assert rt.raw_row_entry(knowledge_owned, _amap(), 2)["alias"] == "dev_b"
    unresolved = dict(row, source_key="SRC-zzz")
    assert rt.raw_row_entry(unresolved, _amap(), 3)["alias"] == "unmapped_1"
    for forbidden in ("CHUNK-1", "SRC-1", "K-b", "source_id", "knowledge_id"):
        assert forbidden not in json.dumps(entry)


def test_raw_row_conflicting_owners_fail_closed():
    row = {
        "chunk_key": "C",
        "source_key": "SRC-1",
        "knowledge_key": "K-a",
        "section": None,
        "content": "x",
    }
    with pytest.raises(BenchmarkError):
        rt.raw_row_entry(row, _amap(), 1)


def _item(key, cls, role, flags=(), text="t", evidence=(), fusion=0.5):
    return {
        "memory_key": key,
        "memory_class": cls,
        "role": role,
        "flags": sorted(flags),
        "text": text,
        "evidence": list(evidence),
        "signals": {
            "authority_tier": 1,
            "scope_rank": 0,
            "task_family_match": False,
            "capability_match": False,
            "fusion_rank_score": fusion,
            "recency_epoch": 0,
        },
    }


def _pack(**sections):
    base = {name: [] for name in er.SECTIONS}
    base.update(sections)
    return {"abstained": not any(sections.values()), **base}


def test_hybrid_flatten_order_kind_alias_and_closed_entries():
    pack = _pack(
        validated_lessons=[_item("K-a", "semantic", "instruction", text="A")],
        current_decisions=[_item("K-b", "decision", "instruction", text="B")],
        accepted_procedures=[_item("PROC-9", "procedural", "instruction", text="P")],
        raw_evidence_refs=[
            _item("CHUNK-1", "raw_evidence", "evidence_ref", text="R", evidence=["source:SRC-1"])
        ],
    )
    entries, signals = rt.hybrid_entries_and_signals(pack, _amap())
    assert [e["alias"] for e in entries] == ["dev_b", "unmapped_1", "dev_a", "dev_src"]
    assert [e["kind"] for e in entries] == ["knowledge", "procedure", "knowledge", "chunk"]
    assert [e["rank"] for e in entries] == [1, 2, 3, 4]
    for e in entries:
        assert set(e) == {"alias", "kind", "content", "rank"}
    assert signals["abstained"] is False


def test_hybrid_signals_come_only_from_public_role_and_flags():
    pack = _pack(
        validated_lessons=[
            _item("K-a", "semantic", "instruction"),
            _item("K-b", "semantic", "warning_example", flags=("premise_mismatch",)),
        ],
        conflicts_and_stale=[_item("K-c", "semantic", "conflict", flags=("conflict",))],
    )
    entries, signals = rt.hybrid_entries_and_signals(pack, _amap())
    assert signals["premise_mismatch"] == ["dev_b"]
    assert signals["supporting_aliases"] == ["dev_a"]
    assert signals["conflict_flagged"] == ["unmapped_1"]
    assert "role" not in json.dumps(entries)


def test_hybrid_premise_flagged_item_is_not_supporting_even_when_not_demoted():
    pack = _pack(
        validated_lessons=[_item("K-a", "semantic", "evidence_ref", flags=("premise_mismatch",))]
    )
    _, signals = rt.hybrid_entries_and_signals(pack, _amap())
    assert signals["supporting_aliases"] == []


def test_hybrid_empty_pack_is_the_abstention_signal():
    entries, signals = rt.hybrid_entries_and_signals(_pack(), _amap())
    assert entries == [] and signals["abstained"] is True


def test_current_vres_entry_richness_and_no_alias_leak():
    k = rt.knowledge_row_entry(
        {"knowledge_key": "K-a", "title": "Note", "statement": "S"}, _amap(), 1
    )
    assert k["content"] == "Note: S" and k["kind"] == "knowledge" and k["alias"] == "dev_a"
    p = rt.procedure_row_entry(
        {
            "procedure_key": "PROC-1",
            "name": "N",
            "description": "D",
            "method": ["m1", "m2"],
            "invariants": ["i1"],
        },
        _amap(),
        1,
    )
    assert p["kind"] == "procedure" and p["alias"] == "unmapped_1"
    assert p["content"] == "N: D\nmethod: m1; m2\ninvariants: i1"


def test_executable_subset_never_contains_consolidate_or_gap_ops():
    for split in eb.DEVELOPMENT_SPLITS:
        bundle = eb.load_development_bundle(ROOT, split)
        for case in bundle["cases"]:
            if eb.classify_case(case) != "EXECUTABLE":
                continue
            ops = {s["op"] for s in case.get("timeline", [])}
            assert ops <= set(rt.EXECUTABLE_OPS), (case["case_id"], ops)


def test_owner_gap_case_short_circuits_before_any_owner_call():
    class Boom:
        def __getattr__(self, name):
            raise AssertionError("owner touched")

    bundle = eb.load_development_bundle(ROOT, "development")
    gap = next(c for c in bundle["cases"] if eb.classify_case(c) != "EXECUTABLE")
    runtime = rt.BenchmarkRuntime(
        SCORING,
        nonce="n0",
        owners=rt.Owners(
            repository=Boom(),
            knowledge=Boom(),
            sources=Boom(),
            procedures=Boom(),
            approvals=Boom(),
            lifecycle=Boom(),
            revocation=Boom(),
            retrieval=Boom(),
        ),
        environ={},
    )
    result = runtime.run_case(gap, bundle["expected"][gap["case_id"]])
    assert result["status"] == "not_run_owner_gap"


def test_approval_fixture_never_trusts_the_connecting_account():
    import re
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    bad = re.compile(r"writer_role\s*=\s*(session_user|current_user|'postgres'|\"postgres\")", re.I)
    for rel in (
        "src/vres_os/experience_benchmark_runtime.py",
        "tests/integration/e7_trusted_writer.py",
    ):
        assert not bad.search((root / rel).read_text(encoding="utf-8")), rel
    runtime_src = (root / "src/vres_os/experience_benchmark_runtime.py").read_text(encoding="utf-8")
    assert "record_event" not in runtime_src and "provenance_authority" not in runtime_src


def test_tied_items_are_ordered_by_alias_not_by_the_physical_key():
    def run(first, second):
        pack = _pack(
            raw_evidence_refs=[
                _item(first, "raw_evidence", "evidence_ref", evidence=[f"source:{first}"]),
                _item(second, "raw_evidence", "evidence_ref", evidence=[f"source:{second}"]),
            ]
        )
        return [e["alias"] for e in rt.hybrid_entries_and_signals(pack, _amap2())[0]]

    # E5 breaks the tie by physical key; the benchmark must not depend on which key sorted first.
    assert run("SRC-1", "SRC-2") == run("SRC-2", "SRC-1") == ["dev_a", "dev_src"]


def test_tie_order_never_reorders_items_that_differ_on_a_ranking_signal():
    pack = _pack(
        raw_evidence_refs=[
            _item("SRC-1", "raw_evidence", "evidence_ref", evidence=["source:SRC-1"], fusion=-0.9),
            _item("SRC-2", "raw_evidence", "evidence_ref", evidence=["source:SRC-2"], fusion=-0.1),
        ]
    )
    assert [e["alias"] for e in rt.hybrid_entries_and_signals(pack, _amap2())[0]] == [
        "dev_src",
        "dev_a",
    ]
