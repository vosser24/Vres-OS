"""#176 E7 hygiene: the restricted test writer's grants match the production boundary.

No database needed.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests" / "integration"))

import e7_trusted_writer  # noqa: E402
import trusted_provenance_writer as twp  # noqa: E402

BOUNDARY = (ROOT / "src" / "vres_os" / "database_boundary.py").read_text(encoding="utf-8")
SIGNATURE = re.compile(r"vres\.(\w+)\(([^)]*)\)")


def _boundary_signatures() -> dict[str, str]:
    return {m.group(1): m.group(0) for m in SIGNATURE.finditer(BOUNDARY)}


def test_writer_function_grants_are_exactly_the_six_writer_functions():
    assert len(twp.WRITER_FUNCTIONS) == 6 and len(set(twp.WRITER_FUNCTIONS)) == 6
    assert sorted(twp.WRITER_FUNCTIONS) == sorted(
        [
            "vres.stage_user_input(bigint,text,text,text,text,text,text,timestamptz)",
            "vres.latest_pending_user_instruction(bigint,text)",
            "vres.commit_user_inputs(bigint,text,text)",
            "vres.record_experience_retrieval_observation(bigint,text,text,text,text,jsonb,jsonb)",
            "vres.record_experience_retrieval_references(bigint,text,text,text,text,text,text,text[])",
            "vres.record_experience_retrieval_replay(bigint,bigint,jsonb)",
        ]
    )


def test_writer_function_signatures_match_database_boundary_source():
    declared = _boundary_signatures()
    for signature in twp.WRITER_FUNCTIONS:
        name = SIGNATURE.fullmatch(signature).group(1)
        assert declared.get(name) == signature, f"{name} drifted from database_boundary.py"


def test_e7_module_is_a_thin_reexport_of_the_generic_fixture():
    assert e7_trusted_writer.trusted_test_writer is twp.trusted_provenance_writer
    assert e7_trusted_writer.WRITER_FUNCTIONS is twp.WRITER_FUNCTIONS
    assert e7_trusted_writer.seed_test_user_instruction is twp.seed_test_user_instruction


def test_fixture_never_grants_table_dml_or_a_default_writer():
    source = (ROOT / "tests" / "integration" / "trusted_provenance_writer.py").read_text(
        encoding="utf-8"
    )
    assert not re.search(r"GRANT\s+(INSERT|UPDATE|DELETE|ALL|SELECT)", source, re.I)
    assert not re.search(r"writer_role\s*=\s*(session_user|current_user|'postgres')", source, re.I)
