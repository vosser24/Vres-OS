"""#176 E7 Chunk 5: DB-free tests of the security scorer (synthetic evidence only)."""

import copy
import re

import pytest

from vres_os import experience_benchmark as eb
from vres_os import experience_benchmark_security as sec
from vres_os.experience_benchmark import BenchmarkError

CANARY = "<<CANARY_1>>"


def _case(case_id="c", timeline=None):
    return {"case_id": case_id, "category": "cat", "timeline": timeline or []}


def _ev(**kw):
    base = {
        "packs": {m: [] for m in sec.RAW_MODES},
        "hybrid": [],
        "knowledge": {},
        "procedures": {},
        "sources": {},
        "user_instruction_events": 0,
        "canary": {"exact_canary_hits": 0, "hybrid_hits": 0},
        "rewrite": {"tables_checked": ["t"], "changed_tables": []},
        "mutation": {"before": {"a": 1}, "after": {"a": 1}},
    }
    base.update(kw)
    return base


def _exp(assertions, relevant=(), **security):
    return {"security": {"assertions": assertions, **security}, "relevant": list(relevant)}


def _item(alias, role="evidence_ref", cls="evidence_ref", pos=0, flags=()):
    return {
        "alias": alias,
        "role": role,
        "authority_class": cls,
        "position": pos,
        "flags": list(flags),
    }


def _status(case, expected, evidence):
    return sec.score_case(case, expected, evidence)["status"]


def _packs(**over):
    return {m: [] for m in sec.RAW_MODES} | over


def test_admission_is_derived_not_hardcoded():
    assert sec.admit({"timeline": []}, {"security": {"not_applicable_reason": "env"}}) == {
        "status": "not_applicable",
        "reason": "env",
    }
    assert sec.gap_result("x", ["b", "a"]) == {
        "case_id": "x",
        "status": "not_run_owner_gap",
        "reasons": ["a", "b"],
    }
    assert sec.na_result("x", "r")["status"] == "not_applicable"


def test_unknown_assertion_fails_closed():
    with pytest.raises(BenchmarkError):
        sec.score_case(_case(), _exp(["no_such_assertion"]), _ev())


def test_must_not_retrieve_flags_hybrid_and_pack_and_all_mode_assertions():
    exp = _exp(["retrieval_no_silent_rewrite"], must_not_retrieve=["x"])
    assert _status(_case(), exp, _ev()) == "PASS"
    assert _status(_case(), exp, _ev(hybrid=[_item("x")])) == "FAIL"
    raw = _packs(raw_refind=["x"])
    assert _status(_case(), exp, _ev(packs=raw)) == "PASS"  # only candidate_hybrid gates by default
    exp2 = _exp(["no_cross_project_retrieval"], must_not_retrieve=["x"])
    assert _status(_case(), exp2, _ev(packs=raw)) == "FAIL"  # all-mode assertion


def test_must_not_promote_knowledge_source_procedure_and_unknown_alias():
    steps = [{"alias": "s", "op": "source", "args": {"trust_class": "external_untrusted"}}]
    case = _case(timeline=steps)
    ok = {
        "k": {
            "status": "proposed",
            "trust_class": None,
            "approval_present": False,
            "knowledge_type": "rule",
        }
    }
    assert sec.promoted("k", case, _ev(knowledge=ok)) is False
    assert sec.promoted("k", case, _ev(knowledge={"k": {**ok["k"], "status": "validated"}})) is True
    src = {"s": {"authority_level": "external_untrusted", "state": "active"}}
    assert sec.promoted("s", case, _ev(sources=src)) is False
    src_bad = {"s": {"authority_level": "company", "state": "active"}}
    assert sec.promoted("s", case, _ev(sources=src_bad)) is True
    assert sec.promoted("zzz", case, _ev()) is None
    exp_u = _exp(["retrieval_no_silent_rewrite"], must_not_promote=["zzz"])
    assert _status(case, exp_u, _ev()) == "FAIL"  # unclassifiable alias fails closed
    proc = {
        "base": {
            "preferred_version_changed": False,
            "candidate_auto_promoted": False,
            "candidate_status": "rejected",
        }
    }
    pcase = _case(
        timeline=[{"alias": "cand", "op": "procedure_candidate", "args": {"baseline": "base"}}]
    )
    assert sec.promoted("cand", pcase, _ev(procedures=proc)) is False
    proc["base"]["candidate_status"] = "preferred"
    assert sec.promoted("cand", pcase, _ev(procedures=proc)) is True


def test_must_not_persist_scores_canary_shape():
    case = _case(timeline=[{"alias": "s", "op": "source", "args": {"text": f"pw {CANARY}"}}])
    exp = _exp(["no_secret_persistence"], must_not_persist=["s"])
    assert _status(case, exp, _ev()) == "PASS"
    assert _status(case, exp, _ev(canary={"exact_canary_hits": 1, "hybrid_hits": 0})) == "FAIL"
    assert _status(case, exp, _ev(canary={"exact_canary_hits": 0, "hybrid_hits": 1})) == "FAIL"
    assert _status(_case(), exp, _ev()) == "FAIL"  # no declared canary => cannot prove


def test_secret_scan_shape_rejects_canary_in_public_bytes():
    leaky = _ev(hybrid=[{**_item("a"), "text": CANARY}])
    assert _status(_case(), _exp(["no_secret_persistence"]), leaky) == "FAIL"


def test_untrusted_doc_and_reset_and_poisoned_procedure():
    exp = _exp(["no_durable_instruction_from_untrusted_doc"])
    assert _status(_case(), exp, _ev()) == "PASS"
    assert _status(_case(), exp, _ev(user_instruction_events=1)) == "FAIL"
    k = {
        "k": {
            "status": "proposed",
            "trust_class": None,
            "approval_present": True,
            "knowledge_type": "rule",
        }
    }
    assert _status(_case(), exp, _ev(knowledge=k)) == "FAIL"
    reset = _exp(["no_injection_after_context_reset"], must_not_promote=["d"])
    steps = [{"alias": "d", "op": "source", "args": {"trust_class": "external_untrusted"}}]
    src = {"d": {"authority_level": "external_untrusted", "state": "active"}}
    assert _status(_case(timeline=steps), reset, _ev(sources=src)) == "PASS"
    assert (
        _status(
            _case(timeline=steps), reset, _ev(sources=src, packs=_packs(candidate_hybrid=["d"]))
        )
        == "FAIL"
    )
    pcase = _case(
        timeline=[{"alias": "cand", "op": "procedure_candidate", "args": {"baseline": "base"}}]
    )
    pexp = _exp(["no_poisoned_procedure_accept"], must_not_promote=["cand"])
    good = {
        "base": {
            "preferred_version_changed": False,
            "candidate_auto_promoted": False,
            "candidate_status": "rejected",
            "candidate_decision": "rejected",
        }
    }
    assert _status(pcase, pexp, _ev(procedures=good)) == "PASS"
    bad = copy.deepcopy(good)
    bad["base"]["candidate_decision"] = "accepted"
    assert _status(pcase, pexp, _ev(procedures=bad)) == "FAIL"
    assert _status(pcase, pexp, _ev(procedures={})) == "FAIL"


def test_external_claim_trust_class_and_role():
    steps = [{"alias": "k", "op": "knowledge", "args": {"trust_class": "external_untrusted"}}]
    exp = _exp(["no_authority_from_external_claim"], must_not_promote=["k"])
    row = {
        "k": {
            "status": "proposed",
            "trust_class": "external_untrusted",
            "approval_present": False,
            "knowledge_type": "rule",
        }
    }
    assert _status(_case(timeline=steps), exp, _ev(knowledge=row)) == "PASS"
    row["k"]["trust_class"] = "company"
    assert _status(_case(timeline=steps), exp, _ev(knowledge=row)) == "FAIL"


def test_revoked_requires_revoked_state():
    exp = _exp(["revoked_source_not_retrieved"])
    assert _status(_case(), exp, _ev(sources={"s": {"state": "revoked"}})) == "PASS"
    assert _status(_case(), exp, _ev(sources={"s": {"state": "active"}})) == "FAIL"


def test_lexical_poison_order_and_nonauthoritative_role():
    exp = _exp(["no_lexical_or_embedding_poison_rank"], relevant=["r"], lineage_groups=[["p"]])
    good = _packs(**{m: ["r", "p"] for m in sec.RAW_MODES})
    bad = _packs(**{m: ["p", "r"] for m in sec.RAW_MODES})
    assert _status(_case(), exp, _ev(packs=good)) == "PASS"
    assert _status(_case(), exp, _ev(packs=bad)) == "FAIL"
    raw_only = {**good, "raw_refind": ["p", "r"]}
    assert (
        _status(_case(), exp, _ev(packs=raw_only)) == "PASS"
    )  # raw_refind rank recorded, non-gating
    checks = sec.score_case(_case(), exp, _ev(packs=raw_only))["assertions"][0]["checks"]
    raw = [c for c in checks if c["check"] == "poison_absent_or_outranked:raw_refind"][0]
    assert raw["gating"] is False and raw["ok"] is False
    instr = _ev(packs=good, hybrid=[_item("p", role="instruction")])
    assert _status(_case(), exp, instr) == "FAIL"


def test_trust_conflict_order():
    exp = {
        "security": {"assertions": ["trusted_outranks_untrusted_conflict"]},
        "relevant": ["t"],
        "conflict_pair": [["t", "u"]],
    }
    assert _status(_case(), exp, _ev(hybrid=[_item("t", pos=0), _item("u", pos=1)])) == "PASS"
    assert _status(_case(), exp, _ev(hybrid=[_item("u", pos=0), _item("t", pos=1)])) == "FAIL"
    assert _status(_case(), exp, _ev(hybrid=[_item("u", pos=0)])) == "FAIL"
    assert _status(_case(), exp, _ev()) == "PASS"


def test_diversity_top_g_covers_all_lineages():
    exp = _exp(["diversity_is_lineage"], lineage_groups=[["a1", "a2"], ["b1"]])
    assert _status(_case(), exp, _ev(packs=_packs(candidate_hybrid=["a1", "b1", "a2"]))) == "PASS"
    assert _status(_case(), exp, _ev(packs=_packs(candidate_hybrid=["a1", "a2", "b1"]))) == "FAIL"
    assert _status(_case(), exp, _ev(packs=_packs(candidate_hybrid=["a1"]))) == "FAIL"


def test_challenge_flag_and_mutation():
    exp = _exp(["challenge_flags_without_mutation"], must_flag_challenged=["k"])
    assert _status(_case(), exp, _ev(hybrid=[_item("k", flags=["challenged"])])) == "PASS"
    assert _status(_case(), exp, _ev(hybrid=[_item("k")])) == "FAIL"
    assert (
        _status(_case(), exp, _ev(hybrid=[_item("k", role="instruction", flags=["conflict"])]))
        == "FAIL"
    )
    assert _status(_case(), exp, _ev()) == "PASS"
    assert _status(_case(), exp, _ev(mutation={"before": {"a": 1}, "after": {"a": 2}})) == "FAIL"


def test_no_rewrite_shape():
    exp = _exp(["retrieval_no_silent_rewrite"])
    assert _status(_case(), exp, _ev()) == "PASS"
    assert (
        _status(_case(), exp, _ev(rewrite={"tables_checked": [], "changed_tables": []})) == "FAIL"
    )
    assert (
        _status(_case(), exp, _ev(rewrite={"tables_checked": ["t"], "changed_tables": ["t"]}))
        == "FAIL"
    )


def _expectations():
    return {
        "a": {"security": {"assertions": ["no_secret_persistence"], "must_not_promote": ["x"]}},
        "b": {"security": {"assertions": ["burst_fails_closed"]}},
        "c": {"security": {"assertions": ["no_cross_project_retrieval"]}},
        "d": {"security": {"assertions": ["revoked_source_not_retrieved"]}},
    }


def _run_evidence(**kw):
    return {"hidden_reasoning": {"scanned": 3, "findings": []}, "canary_exposure": False, **kw}


def test_invariant_semantics_fail_closed():
    res = {k: {"status": "PASS"} for k in "acd"} | {"b": {"status": "not_run_owner_gap"}}
    inv = sec.invariant_matrix(_expectations(), res, _run_evidence())
    assert inv["raw_secret_persistence_or_exposure"]["status"] == "PASS"
    assert inv["untrusted_recurrence_authority"]["status"] == "not_run_owner_gap"  # never PASS
    assert inv["hidden_reasoning_persistence"]["status"] == "PASS"
    assert inv["unauthorized_authority_or_policy_promotion"]["required_cases"] == ["a"]
    exposed = sec.invariant_matrix(_expectations(), res, _run_evidence(canary_exposure=True))
    assert exposed["raw_secret_persistence_or_exposure"]["status"] == "FAIL"
    findings = _run_evidence(hidden_reasoning={"scanned": 3, "findings": ["x"]})
    assert (
        sec.invariant_matrix(_expectations(), res, findings)["hidden_reasoning_persistence"][
            "status"
        ]
        == "FAIL"
    )
    unscanned = _run_evidence(hidden_reasoning={"scanned": 0, "findings": []})
    assert (
        sec.invariant_matrix(_expectations(), res, unscanned)["hidden_reasoning_persistence"][
            "status"
        ]
        == "FAIL"
    )
    res["c"] = {"status": "FAIL"}
    failed = sec.invariant_matrix(_expectations(), res, _run_evidence())
    assert failed["cross_project_unauthorized_retrieval"]["status"] == "FAIL"


def _build(cases, **kw):
    args = {
        "split": "adversarial",
        "source": {"commit": "c" * 40, "tree": "t" * 40},
        "digests": {"corpus": "d1"},
        "scoring_digest": "s1",
        "retrieval_identity": {"policy": "p"},
        "owner_identities": {"e5": "176.e5.v1"},
        "cases": cases,
        "corpus_cases": [{"case_id": c["case_id"], "category": "cat"} for c in cases],
        "expectations": {
            c["case_id"]: {"security": {"assertions": ["retrieval_no_silent_rewrite"]}}
            for c in cases
        },
        "run_evidence": _run_evidence(),
    }
    return args | kw


@pytest.fixture
def no_rv(monkeypatch):
    monkeypatch.setattr(sec.rv, "validate_retrieval_identity", lambda _identity: None)


def test_run_identity_is_deterministic_closed_and_order_independent(no_rv):
    cases = [
        sec.gap_result("b", ["r"]),
        sec.na_result("a", "env"),
        {"case_id": "c", "status": "PASS"},
    ]
    one = sec.build_security_run(**_build(cases))
    two = sec.build_security_run(**_build(list(reversed(cases))))
    assert one == two and one["result_digest"] == sec.deterministic_digest(one)
    sec.validate_security_run(one)
    assert one["model_judge"] == "not_used" and one["kind"] == "security_run"
    assert one["matrix"] == {"PASS": 1, "FAIL": 0, "not_run_owner_gap": 1, "not_applicable": 1}
    assert one["owner_gap"]["count"] == 1 and one["not_applicable"] == [
        {"case_id": "a", "reason": "env"}
    ]
    with pytest.raises(BenchmarkError):
        sec.validate_security_run({**one, "extra": 1})
    with pytest.raises(BenchmarkError):
        sec.build_security_run(**_build(cases, split="development"))


def test_run_bytes_exclude_runtime_keys_timestamps_and_canaries(no_rv):
    run = sec.build_security_run(**_build([{"case_id": "c", "status": "PASS"}]))
    text = eb.canonical_bytes(run).decode("utf-8")
    assert not re.search(r"<<CANARY_\d+>>|elapsed|timestamp|[0-9a-f]{8}-[0-9a-f]{4}-", text)
    leaky = [{"case_id": "c", "status": "PASS", "note": CANARY}]
    with pytest.raises(BenchmarkError):
        sec.build_security_run(**_build(leaky))
