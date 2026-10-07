"""#176 E7 Chunk 5: focused PG proof of the security ladder (disposable `_test` DB only).

One integration test per executable adversarial case (real E1-E6 owners), plus the full-run test that
proves the second-user N/A row and the six owner-gap rows make zero owner and retrieval calls.
"""

import pytest
from e7_c4_support import ROOT, SRC, make_runtime
from e7_trusted_writer import trusted_test_writer

from vres_os import experience_benchmark as eb
from vres_os import experience_benchmark_security as sec
from vres_os import experience_benchmark_security_runtime as sr

BUNDLE = eb.load_development_bundle(ROOT, "adversarial")
CASES = {c["case_id"]: c for c in BUNDLE["cases"]}
GAPS = {
    "adv_poisoned_trajectory": ["observed_episode_writer_missing"],
    "adv_secret_episode": ["failed_episode_requires_host_observed_routed_work_unit"],
    "adv_flood_burst": ["failed_episode_requires_host_observed_routed_work_unit"],
    "adv_varied_poison": ["failed_episode_requires_host_observed_routed_work_unit"],
    "adv_recurrence": ["observed_episode_writer_missing"],
    "adv_participation": ["observed_episode_writer_missing"],
}
NA = {"adv_second_user"}
EXECUTABLE = sorted(set(CASES) - set(GAPS) - NA)
# Cases whose hardening lands in a later, separately committed regression test file section.
HARDENED_LATER = {"adv_doc_instruction", "adv_reset_injection", "adv_secret_source"}


@pytest.fixture
def runtime(monkeypatch):
    dsn, runtime = make_runtime(monkeypatch)
    with trusted_test_writer(dsn):
        yield runtime


def _failed(result):
    return [
        (a["name"], c["check"])
        for a in result["assertions"]
        for c in a["checks"]
        if c["gating"] and not c["ok"]
    ]


def test_admission_matches_the_frozen_classifier():
    assert len(CASES) == 20
    admitted = {cid: sec.admit(CASES[cid], BUNDLE["expected"][cid]) for cid in CASES}
    assert sorted(c for c, a in admitted.items() if a["status"] == "executable") == EXECUTABLE
    assert len(EXECUTABLE) == 13
    assert {c: a["reasons"] for c, a in admitted.items() if a["status"] == sec.GAP} == GAPS
    assert [c for c, a in admitted.items() if a["status"] == sec.NA] == sorted(NA)


@pytest.mark.parametrize("case_id", sorted(set(EXECUTABLE) - HARDENED_LATER))
def test_executable_case_passes_against_real_owners(runtime, case_id):
    result = sr.run_case(runtime, CASES[case_id], BUNDLE["expected"][case_id])
    assert _failed(result) == [], case_id
    assert result["status"] == sec.PASS
    assert result["assertions"], "every executed case scores at least one assertion"


def test_gap_and_na_rows_make_zero_owner_and_retrieval_calls(runtime, monkeypatch):
    materialized, retrieved = [], []
    real_mat = runtime.materialize

    def mat(case):
        materialized.append(case["case_id"])
        return real_mat(case)

    monkeypatch.setattr(runtime, "materialize", mat)
    for adapter in runtime.adapters.values():
        real = adapter.retrieve

        def counted(*a, _real=real, **k):
            retrieved.append(1)
            return _real(*a, **k)

        monkeypatch.setattr(adapter, "retrieve", counted)
    run = sr.run_security(runtime, ROOT, source=SRC)
    by_id = {c["case_id"]: c for c in run["cases"]}
    assert len(by_id) == 20
    for cid, reasons in GAPS.items():
        assert by_id[cid] == {"case_id": cid, "status": sec.GAP, "reasons": reasons}
    assert by_id["adv_second_user"]["status"] == sec.NA
    assert not set(materialized) & (set(GAPS) | NA)
    assert sorted(materialized) == EXECUTABLE
    assert len(retrieved) == 3 * len(EXECUTABLE)  # three retrieving modes per executed case
    assert run["owner_gap"]["count"] == 6 and run["model_judge"] == "not_used"
    inv = run["invariants"]
    assert inv["untrusted_recurrence_authority"]["status"] == sec.GAP
    assert inv["hidden_reasoning_persistence"]["status"] == sec.PASS
    assert inv["cross_project_unauthorized_retrieval"]["status"] == sec.PASS
    assert inv["revoked_evidence_current_influence"]["status"] == sec.PASS
    sec.validate_security_run(run)
    assert sec.deterministic_digest(run) == run["result_digest"]
    assert not any(k in eb.canonical_bytes(run).decode() for k in runtime.physical)
