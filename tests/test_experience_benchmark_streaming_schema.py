"""#176 E7 Chunk 4: private streaming expected-evidence block (schema, DB-free)."""

from __future__ import annotations

import copy
from pathlib import Path

import pytest

from vres_os import experience_benchmark as eb

ROOT = Path(__file__).resolve().parents[1] / "benchmarks" / "experience_e7"


def _parse(case_id, streaming):
    bundle = eb.load_development_bundle(ROOT, "development")
    cases = copy.deepcopy(bundle["cases"])
    expected = copy.deepcopy(bundle["expected"])
    expected[case_id]["streaming"] = streaming
    return eb.parse_expected(eb.render_json({"schema_version": 1, "cases": expected}), cases)


def _cp(after_t, **labels):
    return {"after_t": after_t, **labels}


GOOD = {
    "checkpoints": [_cp(0, relevant=["dev_p"]), _cp(1, relevant=["dev_p"], irrelevant=["dev_n"])],
    "measures": ["forward_transfer", "learning_curve"],
}


def test_valid_block_parses():
    assert _parse("dev_procedure_reuse", GOOD)["dev_procedure_reuse"]["streaming"] == GOOD


@pytest.mark.parametrize(
    "mutate",
    [
        lambda s: s["checkpoints"].reverse(),  # not strictly increasing
        lambda s: s["checkpoints"].__setitem__(1, _cp(0, relevant=["dev_p"])),  # equal t
        lambda s: s["checkpoints"].__setitem__(1, _cp(7, relevant=["dev_p"])),  # t not in timeline
        lambda s: s["checkpoints"][0].update(relevant=["dev_n"]),  # alias not yet present at t=0
        lambda s: s["checkpoints"][1].update(acceptable=["dev_p"]),  # label sets overlap
        lambda s: s.update(checkpoints=s["checkpoints"][:1]),  # fewer than two checkpoints
        lambda s: s.update(measures=["learning_curve", "learning_curve"]),  # duplicate
        lambda s: s.update(measures=["bogus"]),  # open name
        lambda s: s["checkpoints"][0].update(extra=[]),  # unknown key
        lambda s: s.update(extra=1),
    ],
)
def test_invalid_blocks_are_rejected(mutate):
    block = copy.deepcopy(GOOD)
    mutate(block)
    with pytest.raises(eb.BenchmarkError):
        _parse("dev_procedure_reuse", block)


def test_single_checkpoint_only_allowed_for_owner_gap_case():
    block = {"checkpoints": [_cp(1, relevant=["dev_x"])], "measures": ["learning_curve"]}
    assert _parse("dev_trajectory_failure", block)  # OWNER_GAP coverage sequence
    with pytest.raises(eb.BenchmarkError):
        _parse("dev_procedure_reuse", {**block, "checkpoints": [_cp(0, relevant=["dev_p"])]})
