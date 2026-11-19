"""R-11 original writer quarantining tests: AUTHORED NOT_RUN; no host or database."""
from pathlib import Path
from vres_os import session_prompts

ROOT = Path(__file__).resolve().parents[1]


def test_strict_stage_preserves_readonly_and_never_sends_tainted_text(monkeypatch):
    class Result:
        def fetchone(self): return {"staged": True}
    class Fake:
        def __init__(self): self.calls = []
        def __enter__(self): return self
        def __exit__(self, *_args): return False
        def transaction(self): return self
        def execute(self, sql, args):
            self.calls.append((sql, args))
            return Result()
    fake = Fake()
    monkeypatch.setattr(session_prompts, "_writer_available", lambda: True)
    monkeypatch.setattr(session_prompts, "connect", lambda purpose=None: fake)
    assert session_prompts.stage_user_instruction(
        7, "SESSION-CLEAN", "Inspection only. password=synthetic,tail"
    )
    assert len(fake.calls) == 1
    sql, args = fake.calls[0]
    assert "SELECT vres.stage_strict_user_input(" in sql
    assert args[2] == "Inspection only."
    assert args[4] == "control"
    assert args[-1] == session_prompts.STRICT_STAGE_CONTRACT
    assert "synthetic,tail" not in repr(fake.calls)


def test_migration_quarantines_unverified_legacy_event_state_return_and_tool_ids():
    sql = (ROOT / "src/vres_os/migrations/043_legacy_observation_commit_quarantine.sql").read_text("utf-8")
    assert "ADD COLUMN strict_persistence_stage_version smallint" in sql
    assert "CREATE OR REPLACE FUNCTION vres.stage_strict_user_input(" in sql
    assert "SELECT vres.stage_user_input(" in sql
    assert "p_strict_stage_contract IS DISTINCT FROM 'vres-python-strict-v1'" in sql
    assert "session_user <> allowed::text" in sql
    assert "CREATE OR REPLACE FUNCTION vres.commit_user_inputs(" in sql
    assert "'legacy_unverified_held',(obs.strict_persistence_stage_version IS DISTINCT FROM 1)" in sql
    assert sql.count("[UNVERIFIED_LEGACY_USER_INPUT_HELD]") >= 3
    assert "'question',CASE WHEN obs.strict_persistence_stage_version=1" in sql
    assert "'tool_use_id',CASE WHEN obs.strict_persistence_stage_version=1" in sql
    assert "AND strict_persistence_stage_version=1" in sql
    assert "REVOKE ALL ON FUNCTION vres.stage_strict_user_input(" in sql


def test_versioned_functions_get_conditional_writer_grants():
    src = (ROOT / "src/vres_os/database_boundary.py").read_text("utf-8")
    assert "vres.latest_observed_user_input(bigint,text)" in src
    assert "vres.stage_strict_user_input(bigint,text,text,text,text,text,text,timestamptz,text)" in src
    assert "SELECT to_regprocedure(%s) AS routine" in src
    assert "protected_functions.append(optional_signature)" in src
