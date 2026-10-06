"""#176 E4 Chunk C: pure (no DB) contract of provenance traversal, grounding, budget and ledger keys."""
import ast
import hashlib
import inspect
import json
import re
from pathlib import Path

import pytest

from vres_os import experience_lifecycle as el
from vres_os import source_revocation as sr
from vres_os.source_revocation import NodeInfo, ProvenanceBudgetExceeded, SourceRevocationService, analyse

PID, OTHER = 7, 8
SRC_DIR = Path(sr.__file__).resolve().parent


class FakeGraph:
    """In-memory support graph: `edges` maps node -> forward support targets; dependents are the inverse."""

    def __init__(self, nodes, edges, corrupt=None):
        self.nodes, self.edges, self.corrupt = nodes, edges, corrupt or {}
        self.calls = 0

    def node(self, n):
        self.calls += 1
        return self.nodes.get(n, NodeInfo(exists=False))

    def supports(self, n):
        return list(self.edges.get(n, [])), list(self.corrupt.get(n, []))

    def dependents(self, n):
        return [src for src, targets in self.edges.items() if n in targets], []


def S(key, status="active", pid=PID):
    return ("source", key), NodeInfo(exists=True, project_id=pid, status=status)


def K(key, status="validated", pid=PID):
    return ("knowledge", key), NodeInfo(exists=True, project_id=pid, status=status)


def E(key, status="grounded", pid=PID):
    return ("episode", key), NodeInfo(exists=True, project_id=pid, status=status)


def A(key, pid=PID):
    return ("artifact", key), NodeInfo(exists=True, project_id=pid, status=None)


def graph(*pairs, edges, corrupt=None):
    nodes = dict(pairs)
    return FakeGraph(nodes, {n: [t for t in ts] for n, ts in edges.items()}, corrupt)


def keys(nodes):
    return sorted(k for _, k in nodes)


s, s2 = S("S", "revoked"), S("S2")


def test_production_budget_and_policy_constants():
    assert sr.MAX_DEPTH == 4 and sr.MAX_NODES == 500
    assert sr.APPROVAL_TYPE == el.APPROVAL_TYPE == "e4_lifecycle"
    assert sr.POLICY_VERSION == el.POLICY_VERSION == "176.e4.v1"
    public = {n for n, v in inspect.getmembers(SourceRevocationService) if not n.startswith("_") and callable(v)}
    assert public == {"revoke_source"}


def test_single_source_revokes_dependent_knowledge():
    k = K("K")
    out = analyse(graph(s, k, edges={k[0]: [s[0]]}), s[0], PID)
    assert keys(out.revoked) == ["K"] and out.retained == [] and out.corrupt == 0


def test_two_independent_roots_retain_support():
    k = K("K")
    out = analyse(graph(s, s2, k, edges={k[0]: [s[0], s2[0]]}), s[0], PID)
    assert out.revoked == [] and keys(out.retained) == ["K"]


def test_duplicate_paths_to_one_source_are_not_multi_support():
    k, e, a = K("K"), E("E"), A("A")
    edges = {k[0]: [s[0], s[0], e[0]], e[0]: [s[0], a[0]], a[0]: [s[0]]}
    out = analyse(graph(s, k, e, a, edges=edges), s[0], PID)
    assert keys(out.revoked) == ["E", "K"]


def test_corrupt_path_plus_valid_root_keeps_root():
    k = K("K")
    out = analyse(graph(s, s2, k, edges={k[0]: [s[0], s2[0], ("knowledge", "dangling")]},
                        corrupt={k[0]: [("evidence", 1)]}), s[0], PID)
    assert keys(out.retained) == ["K"] and out.revoked == [] and out.corrupt == 2


def test_corrupt_only_support_never_counts():
    k = K("K")
    foreign = S("SF", pid=OTHER)
    out = analyse(graph(s, foreign, k, edges={k[0]: [s[0], foreign[0], ("source", "missing")]},
                        corrupt={k[0]: [("evidence", 1), ("relation", 9)]}), s[0], PID)
    assert keys(out.revoked) == ["K"] and out.corrupt == 4


def test_unrelated_node_without_provenance_is_untouched():
    k, lone = K("K"), K("LONE")
    out = analyse(graph(s, k, lone, edges={k[0]: [s[0]]}), s[0], PID)
    assert keys(out.revoked) == ["K"] and "LONE" not in keys(out.revoked + out.retained)


def test_cycle_never_supports_itself():
    k1, k2 = K("K1"), K("K2")
    out = analyse(graph(s, k1, k2, edges={k1[0]: [s[0], k2[0]], k2[0]: [k1[0]]}), s[0], PID)
    assert keys(out.revoked) == ["K1", "K2"]
    out = analyse(graph(s, s2, k1, k2, edges={k1[0]: [s[0], k2[0]], k2[0]: [k1[0], s2[0]]}), s[0], PID)
    assert out.revoked == [] and keys(out.retained) == ["K1", "K2"]


def test_transitive_episode_and_lesson_shape():
    e1, e2, lesson = E("E1"), E("E2"), K("L", "proposed")
    a = A("A")
    out = analyse(graph(s, e1, lesson, a, edges={lesson[0]: [e1[0]], e1[0]: [a[0], ("task", "T")], a[0]: [s[0]]}),
                  s[0], PID)
    assert keys(out.revoked) == ["E1", "L"]
    edges = {lesson[0]: [e1[0], e2[0]], e1[0]: [s[0]], e2[0]: [s2[0]]}
    out = analyse(graph(s, s2, e1, e2, lesson, edges=edges), s[0], PID)
    assert keys(out.revoked) == ["E1"] and keys(out.retained) == ["L"]


def test_dead_intermediates_and_ledger_revoked_episodes_do_not_carry_support():
    for dead in (K("K1", "retired"), K("K1", "superseded"), K("K1", "revoked"), E("K1", "revoked")):
        k2 = K("K2")
        out = analyse(graph(s, s2, dead, k2, edges={k2[0]: [s[0], dead[0]], dead[0]: [s2[0]]}), s[0], PID)
        assert keys(out.revoked) == ["K2"], dead


def test_already_revoked_candidate_is_not_revoked_again_and_dead_candidates_can_be():
    old, ret = K("OLD", "revoked"), K("RET", "retired")
    out = analyse(graph(s, old, ret, edges={old[0]: [s[0]], ret[0]: [s[0]]}), s[0], PID)
    assert keys(out.revoked) == ["RET"]


def test_cross_scope_company_reported_and_foreign_counted_corrupt():
    company, foreign, k = K("CO", pid=None), K("FK", pid=OTHER), K("K")
    out = analyse(graph(s, company, foreign, k, edges={company[0]: [s[0]], foreign[0]: [s[0]], k[0]: [s[0]]}),
                  s[0], PID)
    assert keys(out.revoked) == ["K"] and keys(out.unresolved_cross_scope) == ["CO"] and out.corrupt == 1


def test_company_and_foreign_sources_never_ground_project_nodes():
    k = K("K")
    out = analyse(graph(s, S("SC", pid=None), k, edges={k[0]: [s[0], ("source", "SC")]}), s[0], PID)
    assert keys(out.revoked) == ["K"] and out.corrupt == 0


def _chain(n, extra_root=False):
    nodes, edges, prev = [s], {}, s[0]
    for i in range(1, n + 1):
        k = K(f"K{i}")
        nodes.append(k)
        edges[k[0]] = [prev]
        prev = k[0]
    return nodes, edges


def test_reverse_depth_within_budget_is_ok():
    nodes, edges = _chain(4)
    out = analyse(graph(*nodes, edges=edges), s[0], PID)
    assert keys(out.revoked) == ["K1", "K2", "K3", "K4"]


def test_reverse_depth_overflow_fails_closed():
    nodes, edges = _chain(5)
    with pytest.raises(ProvenanceBudgetExceeded, match="depth"):
        analyse(graph(*nodes, edges=edges), s[0], PID)


def test_forward_depth_overflow_fails_closed():
    k1 = K("K1")
    chain = [K(f"F{i}") for i in range(1, 5)]
    edges = {k1[0]: [s[0], chain[0][0]]}
    for a, b in zip(chain, chain[1:]):
        edges[a[0]] = [b[0]]
    edges[chain[-1][0]] = [s2[0]]  # active root at distance 5 from K1
    with pytest.raises(ProvenanceBudgetExceeded, match="depth"):
        analyse(graph(s, s2, k1, *chain, edges=edges), s[0], PID)
    edges[chain[-2][0]] = [s2[0]]  # root at distance 4 is inside the budget
    out = analyse(graph(s, s2, k1, *chain, edges=edges), s[0], PID)
    assert keys(out.retained) == ["K1"]


def test_node_budget_overflow_fails_closed(monkeypatch):
    fan = [K(f"K{i}") for i in range(501)]
    with pytest.raises(ProvenanceBudgetExceeded, match="node"):
        analyse(graph(s, *fan, edges={k[0]: [s[0]] for k in fan}), s[0], PID)
    small = [K(f"K{i}") for i in range(498)]
    out = analyse(graph(s, *small, edges={k[0]: [s[0]] for k in small}), s[0], PID)
    assert len(out.revoked) == 498 and out.nodes_visited == 499
    monkeypatch.setattr(sr, "MAX_NODES", 10)
    with pytest.raises(ProvenanceBudgetExceeded, match="node"):
        analyse(graph(s, *small[:10], edges={k[0]: [s[0]] for k in small[:10]}), s[0], PID)


def test_ledger_key_formula_matches_chunk_b_and_extends_target_kind():
    raw = "176.e4.v1|revoke_source|source|SRC-1|APR-1"
    assert sr.ledger_key("revoke_source", "source", "SRC-1", "APR-1") == hashlib.sha256(raw.encode()).hexdigest()
    assert el.idempotency_key("retire", "K-1", "APR-1") == sr.ledger_key("retire", "knowledge", "K-1", "APR-1")
    k = hashlib.sha256(b"176.e4.v1|invalidate_derived|episode|E-1|SRC-1").hexdigest()
    assert sr.ledger_key("invalidate_derived", "episode", "E-1", "SRC-1") == k
    with pytest.raises(ValueError, match="Unknown lifecycle action"):
        el.idempotency_key("revoke_source", "K-1", "APR-1")


def test_detail_lists_are_bounded_by_digest():
    small = sr.bounded_detail({"request_digest": "d"}, {"revoked_knowledge": ["K1"], "retained_with_support": []})
    assert small["revoked_knowledge"] == ["K1"] and "keys_digest_only" not in small
    many = [f"K-{'x' * 280}-{i}" for i in range(60)]
    big = sr.bounded_detail({"request_digest": "d"}, {"revoked_knowledge": many, "retained_with_support": ["A"]})
    assert big["keys_digest_only"] is True and "revoked_knowledge" not in big
    expect = hashlib.sha256(json.dumps(sorted(many), separators=(",", ":")).encode()).hexdigest()
    assert big["revoked_knowledge_sha256"] == expect
    assert len(json.dumps(big, sort_keys=True).encode()) <= 8192


def _string_constants(tree):
    docstrings = {id(n.body[0].value) for n in ast.walk(tree)
                  if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                  and n.body and isinstance(n.body[0], ast.Expr) and isinstance(n.body[0].value, ast.Constant)}
    return [n.value for n in ast.walk(tree)
            if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in docstrings]


def test_only_source_revocation_writes_the_revoked_status():
    writer = re.compile(r"status\s*=\s*'revoked'", re.I)
    offenders, readers = [], []
    for path in sorted(SRC_DIR.rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        consts = [c for c in _string_constants(ast.parse(text)) if re.search(r"\brevoked\b", c)]
        if path.name == "source_revocation.py":
            assert len(writer.findall(text)) == 2  # knowledge cascade + source status, nowhere else
            continue
        if writer.search(text):
            offenders.append(path.name)
        if consts:
            readers.append((path.name, consts))
    assert offenders == []
    # The only other code-level use is the read-side exclusion tuple.
    # E4 Chunk G: session_contamination.py only words the revoked-identifier phrase shown to the user (no status write).
    # E6: experience_utility.py is a read-side lifecycle projection (reader only; writers are already rejected above).
    assert sorted(r[0] for r in readers) == [
        "experience_utility.py", "knowledge_status.py", "session_contamination.py",
    ]
    assert [r for r in readers if r[0] == "knowledge_status.py"] == [("knowledge_status.py", ["revoked"])]
