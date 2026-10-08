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
    assert ident["experience_retrieval_schema"] == er.SCHEMA_VERSION == "176.e5.v5"
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
        "tests/integration/trusted_provenance_writer.py",
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


# ---- #176 E7 Chunk 2 repair: R1 status, R3 owner-max limits, R4 native tie order, R5 ----


def test_initial_status_is_the_frozen_proposed_and_supersession_rank_allows_it():
    from vres_os.knowledge import _RANK  # owner supersession rule

    frozen = eb.OPERATION_OWNERS["knowledge_propose"]
    assert "proposed" in json.dumps(dict(frozen), default=str)
    assert rt.INITIAL_STATUS == "proposed"
    assert _RANK[rt.INITIAL_STATUS] <= _RANK[rt.INITIAL_STATUS]  # proposed -> proposed allowed


def test_native_limits_are_owner_maxima_and_no_artificial_cap_remains():
    assert (
        rt.RAW_REFIND_NATIVE_LIMIT,
        rt.CURRENT_KNOWLEDGE_NATIVE_LIMIT,
        rt.CURRENT_PROCEDURE_NATIVE_LIMIT,
    ) == (50, 50, 20)
    assert not hasattr(rt, "NATIVE_LIMIT")


class _Stub:
    def __init__(self, rows):
        self.rows, self.limits = rows, []

    def chunk_search(self, query, limit, project_id):
        self.limits.append(limit)
        return self.rows

    def search(self, query, limit, project_id):
        self.limits.append(limit)
        return self.rows

    def find_matches(self, query, task_family=None, limit=5, project_id=None):
        self.limits.append(limit)
        return self.rows


def _owners(**kw):
    return rt.Owners(**{k: kw.get(k) for k in rt.Owners.__dataclass_fields__})


class _ProjectMap(eb.AliasMap):
    project_id = 7


def _many_amap(n):
    names = [f"dev_{i:02d}" for i in range(n)]
    m = _ProjectMap(names)
    for i, name in enumerate(names):
        m.bind(name, f"SRC-{i}")
    return m, names


def test_raw_refind_is_not_cut_at_ten_when_entries_fit_the_budget():
    m, names = _many_amap(15)
    rows = [
        {"source_key": f"SRC-{i}", "content": "x", "rank": 1.0 - i / 100, "section": None}
        for i in range(15)
    ]
    stub = _Stub(rows)
    out = rt.RawRefind(_owners(knowledge=stub)).retrieve({"query": "q", "request": {}}, m, SCORING)
    assert stub.limits == [50]
    assert [i["alias"] for i in out["pack"]] == names  # 15 > 10, cut only by the token budget


def test_current_vres_uses_owner_maxima():
    m, _ = _many_amap(1)
    k, p = _Stub([]), _Stub([])
    rt.CurrentVres(_owners(knowledge=k, procedures=p)).retrieve(
        {"query": "q", "request": {}}, m, SCORING
    )
    assert k.limits == [50] and p.limits == [20]


def _raw(src, rank):
    return {"source_key": src, "content": "c", "rank": rank, "section": None}


def _aliases(entries):
    return [e["alias"] for e in entries]


def test_raw_order_equal_rank_uses_alias_and_different_rank_keeps_rank():
    m = eb.AliasMap(["dev_a", "dev_b", "dev_c"])
    for n, k in (("dev_a", "S1"), ("dev_b", "S2"), ("dev_c", "S3")):
        m.bind(n, k)
    tied = rt.ordered_raw_entries([_raw("S2", 0.5), _raw("S1", 0.5)], m)
    assert _aliases(tied) == ["dev_a", "dev_b"] and [e["rank"] for e in tied] == [1, 2]
    mixed = rt.ordered_raw_entries([_raw("S3", 0.9), _raw("S1", 0.5), _raw("S2", 0.7)], m)
    assert _aliases(mixed) == ["dev_c", "dev_b", "dev_a"]


def _krow(key, rank, confidence):
    return {
        "knowledge_key": key,
        "title": "t",
        "statement": "s",
        "rank": rank,
        "confidence": confidence,
    }


def test_knowledge_order_rank_then_confidence_null_last_then_alias():
    m = eb.AliasMap(["dev_a", "dev_b", "dev_c"])
    for n, k in (("dev_a", "K1"), ("dev_b", "K2"), ("dev_c", "K3")):
        m.bind(n, k)
    both = rt.ordered_knowledge_entries([_krow("K2", 0.5, 0.5), _krow("K1", 0.5, 0.5)], m)
    assert _aliases(both) == ["dev_a", "dev_b"]
    conf = rt.ordered_knowledge_entries([_krow("K1", 0.5, 0.2), _krow("K2", 0.5, 0.9)], m)
    assert _aliases(conf) == ["dev_b", "dev_a"]  # higher confidence first, not alias order
    null = rt.ordered_knowledge_entries([_krow("K1", 0.5, None), _krow("K2", 0.5, 0.1)], m)
    assert _aliases(null) == ["dev_b", "dev_a"]  # NULL last
    rank = rt.ordered_knowledge_entries([_krow("K2", 0.9, None), _krow("K1", 0.1, 0.99)], m)
    assert _aliases(rank) == ["dev_b", "dev_a"]


def _prow(key, score):
    return {"procedure_key": key, "name": "n", "description": "d", "score": score}


def test_procedure_order_score_then_alias_and_native_order_kept_on_score_difference():
    m = eb.AliasMap(["dev_a", "dev_b"])
    m.bind("dev_a", "P1")
    m.bind("dev_b", "P2")
    assert _aliases(rt.ordered_procedure_entries([_prow("P2", 0.4), _prow("P1", 0.4)], m)) == [
        "dev_a",
        "dev_b",
    ]
    assert _aliases(rt.ordered_procedure_entries([_prow("P2", 0.9), _prow("P1", 0.4)], m)) == [
        "dev_b",
        "dev_a",
    ]


def test_runtime_has_no_hidden_maturity_helper():
    import inspect

    src = inspect.getsource(rt)
    assert "_match_successor_maturity" not in src
    assert not hasattr(rt.BenchmarkRuntime, "_match_successor_maturity")
    # the only status the runtime writes by itself is the declared "observed" step
    assert src.count("status=") == src.count('status="observed"') + src.count("status=INITIAL")


def test_knowledge_observe_is_executable_and_updates_to_observed_only():
    class K:
        def __init__(self):
            self.updates = []

        def update(self, key, **kw):
            self.updates.append((key, kw))

    assert "knowledge_observe" in rt.EXECUTABLE_OPS
    k = K()
    runtime = rt.BenchmarkRuntime.__new__(rt.BenchmarkRuntime)
    runtime.o = _owners(knowledge=k)
    runtime._project = lambda case_id, label: 1
    amap = type("M", (), {"runtime_key_for": staticmethod(lambda alias: f"K-{alias}")})()
    runtime._step("c", "p", {"t": 0, "op": "knowledge_observe", "alias": "dev_b"}, amap)
    assert k.updates == [("K-dev_b", {"status": "observed"})]


# ---- Chunk 3: operation trace + knowledge snapshots (no database) ---------------------------


def _kitem(key, statement="s", status="proposed", sup=None, evidence=(), **extra):
    return {
        "knowledge_key": key,
        "project_id": 99,
        "knowledge_type": "fact",
        "title": "Note",
        "statement": statement,
        "status": status,
        "superseded_by": sup,
        "created_at": "2026-01-01T00:00:00+00:00",
        "updated_at": "2026-01-01T00:00:00+00:00",
        "last_verified_at": None,
        "approval_key": "AP-1",
        "evidence": [{"id": 5, "source_key": s, "source_id": 3} for s in evidence],
        **extra,
    }


def test_knowledge_snapshot_has_the_closed_shape_and_only_aliases():
    m = eb.AliasMap(["dev_a", "dev_b", "dev_src"])
    m.bind("dev_a", "K-a")
    m.bind("dev_b", "K-b")
    m.bind("dev_src", "SRC-1")
    item = _kitem("K-a", status="superseded", sup="K-b", evidence=["SRC-1"])
    snap = rt.knowledge_snapshot("dev_a", item, m)
    assert snap == {
        "alias": "dev_a",
        "kind": "knowledge",
        "knowledge_type": "fact",
        "title": "Note",
        "statement": "s",
        "status": "superseded",
        "superseded_by": "dev_b",
        "evidence_sources": ["dev_src"],
    }
    text = json.dumps(snap)
    for forbidden in ("K-a", "K-b", "SRC-1", "AP-1", "99", "2026", "created_at"):
        assert forbidden not in text


def test_knowledge_snapshot_sorts_evidence_aliases_and_skips_sourceless_rows():
    m = eb.AliasMap(["dev_a", "dev_x", "dev_y"])
    m.bind("dev_a", "K-a")
    m.bind("dev_x", "S-x")
    m.bind("dev_y", "S-y")
    item = _kitem("K-a", evidence=["S-y", "S-x"])
    item["evidence"].append({"id": 9, "source_key": None})
    assert rt.knowledge_snapshot("dev_a", item, m)["evidence_sources"] == ["dev_x", "dev_y"]


@pytest.mark.parametrize("field", ["sup", "evidence"])
def test_knowledge_snapshot_unknown_reference_fails_closed_without_the_raw_key(field):
    m = eb.AliasMap(["dev_a"])
    m.bind("dev_a", "K-a")
    item = (
        _kitem("K-a", sup="K-SECRET-9")
        if field == "sup"
        else _kitem("K-a", evidence=["SRC-SECRET-9"])
    )
    with pytest.raises(BenchmarkError) as err:
        rt.knowledge_snapshot("dev_a", item, m)
    assert "SECRET" not in str(err.value)


def test_knowledge_snapshot_revoked_tombstone_is_closed_and_keyless():
    m = eb.AliasMap(["dev_a"])
    m.bind("dev_a", "K-a")
    tomb = {"knowledge_key": "K-a", "project_id": 1, "status": "revoked", "evidence": []}
    snap = rt.knowledge_snapshot("dev_a", tomb, m)
    assert snap["status"] == "revoked" and snap["statement"] is None
    assert snap["evidence_sources"] == [] and snap["superseded_by"] is None
    assert "K-a" not in json.dumps(snap)


class _TraceKnowledge:
    """Fake of the public KnowledgeService surface the traced timeline touches."""

    def __init__(self):
        self.items, self.calls = {}, []

    def propose(self, *, key, statement, knowledge_type, title, status, **_):
        self.calls.append("propose")
        self.items[key] = _kitem(key, statement=statement, status=status)

    def update(self, key, *, status):
        self.calls.append("update")
        self.items[key]["status"] = status

    def supersede(self, old, new):
        self.calls.append("supersede")
        self.items[old].update(status="superseded", superseded_by=new)

    def get(self, key):
        self.calls.append("get")
        return dict(self.items[key])


class _Repo:
    def ensure_project(self, ident):
        return 41


def _traced_runtime(knowledge):
    owners = _owners(knowledge=knowledge, repository=_Repo())
    return rt.BenchmarkRuntime(SCORING, nonce="n1", owners=owners, environ={})


def _case(*steps):
    aliases = sorted({s["alias"] for s in steps})
    return {
        "case_id": "dev_x",
        "aliases": aliases,
        "request": {"project": "p"},
        "timeline": list(steps),
    }


def _propose(t, alias, statement="s"):
    return {
        "t": t,
        "op": "knowledge_propose",
        "alias": alias,
        "args": {"knowledge_type": "fact", "statement": statement, "project": "p"},
    }


def test_traced_materialization_records_exactly_the_corpus_operations():
    k = _TraceKnowledge()
    runtime = _traced_runtime(k)
    case = _case(
        _propose(0, "dev_a", "old"),
        _propose(1, "dev_b", "new"),
        {"t": 2, "op": "knowledge_observe", "alias": "dev_b"},
        {"t": 3, "op": "knowledge_supersede", "alias": "dev_b", "args": {"supersedes": "dev_a"}},
    )
    amap, trace = runtime.materialize_traced(case)
    rows = trace["rows"]
    assert [(r["t"], r["op"], r["alias"], r["refs"]) for r in rows] == [
        (0, "knowledge_propose", "dev_a", []),
        (1, "knowledge_propose", "dev_b", []),
        (2, "knowledge_observe", "dev_b", []),
        (3, "knowledge_supersede", "dev_b", ["dev_a"]),
    ]
    assert all(r["result"] == {"status": "applied"} for r in rows)
    assert set(rows[0]["after"]) == {"dev_a"} and rows[0]["before"] == {}
    assert rows[1]["before"] == rows[0]["after"]
    last = rows[-1]["after"]
    assert last["dev_a"]["status"] == "superseded" and last["dev_a"]["superseded_by"] == "dev_b"
    assert last["dev_b"]["status"] == "observed"
    # owner writes are exactly the declared operations; everything else is a public read
    assert [c for c in k.calls if c != "get"] == ["propose", "propose", "update", "supersede"]
    for physical in amap.physical:
        assert physical not in json.dumps(trace)
    assert "n1" not in json.dumps(trace)


def test_untraced_materialize_makes_no_snapshot_reads():
    k = _TraceKnowledge()
    _traced_runtime(k).materialize(_case(_propose(0, "dev_a")))
    assert "get" not in k.calls


class _Tripwire:
    def __getattr__(self, name):
        raise AssertionError(f"owner touched: {name}")


def test_faithfulness_owner_gap_case_touches_no_owner_through_the_runtime():
    bundle = eb.load_development_bundle(ROOT, "development")
    case = next(c for c in bundle["cases"] if c["case_id"] == "dev_recurring_priceexport")
    owners = _owners(
        **{name: _Tripwire() for name in rt.Owners.__dataclass_fields__ if name != "user_input"}
    )
    runtime = rt.BenchmarkRuntime(SCORING, nonce="n1", owners=owners, environ={})
    result = runtime.run_faithfulness_case(case, bundle["expected"][case["case_id"]])
    assert result["status"] == "not_run_owner_gap"
    assert result["reasons"] == eb.classify_case(case).removeprefix("OWNER_GAP:").split(",")
    assert runtime.physical == [] and runtime._projects == {}
