"""#176 E7 authority closure: E1 v2 external-observation owner contract (no database)."""
import inspect
from importlib import resources

from vres_os import experience as e1
from vres_os import experience_benchmark as eb

V1_DIGEST = "49e5d6eb17940baf5e1d9c239f9355dd8a65bab60e62e30c81787334ddda519a"
V2_DIGEST = "66e11e1319dd85b6d01fc74e4ad3f2fa4a7ee9857ab5d72fe5016e781b88efa0"
V2_POLICY_JSON = (
    '{"authority":"no_promotion","capture":"external_source_observation_only",'
    '"participation":"observed_only","payload":"bounded_sanitized_no_private_reasoning",'
    '"policy_version":"176.e1.v2","provenance":"active_project_source_required",'
    '"relations":"existing_relations_and_relation_evidence","schema_version":2,'
    '"trust":"external_untrusted_observation_only"}'
)


def _sql(name: str) -> str:
    return resources.files("vres_os").joinpath("migrations", name).read_text(encoding="utf-8")


def test_e1_v1_is_unchanged():
    assert e1.POLICY_VERSION == "176.e1.v1"
    assert e1.POLICY_DIGEST == V1_DIGEST
    assert e1.POLICY["capture"] == "mechanically_known_terminal_task_or_work_unit_only"


def test_e1_v2_policy_is_frozen_and_canonical():
    assert e1.OBSERVED_POLICY_VERSION == "176.e1.v2"
    assert e1.OBSERVED_POLICY_SCHEMA_VERSION == 2
    assert e1._canonical(e1.OBSERVED_POLICY) == V2_POLICY_JSON
    assert e1.OBSERVED_POLICY_DIGEST == V2_DIGEST


def test_observe_owner_accepts_only_project_source_and_closed_outcome():
    sig = inspect.signature(e1.ExperienceEpisodeService.observe_external_source)
    assert list(sig.parameters) == ["self", "project_id", "source_key", "claimed_outcome"]


def test_migration_043_contract():
    sql = _sql("043_experience_observed_episode.sql")
    assert "ALTER COLUMN task_id DROP NOT NULL" in sql
    assert V2_DIGEST in sql and V2_POLICY_JSON in sql and "'176.e1.v2'" in sql
    assert "ck_experience_episode_participation_provenance" in sql
    for needle in (
        "participation_class = 'participated'",
        "task_id IS NOT NULL",
        "participation_class = 'observed'",
        "project_id IS NOT NULL",
        "task_id IS NULL",
        "work_unit_key IS NULL",
        "report_key IS NULL",
        "trust_class = 'external_untrusted_observation'",
        "policy_version = '176.e1.v2'",
    ):
        assert needle in sql, needle
    stripped = sql.upper().replace("CREATE TABLE IF NOT EXISTS vres.experience_policy", "")
    assert "CREATE TABLE" not in stripped


def test_episode_observe_is_an_owner_sequence_not_a_gap():
    row = eb.OPERATION_OWNERS["episode_observe"]
    assert row["owner_gap"] is False
    assert row["methods"] == ("register", "add_chunks", "observe_external_source")
    assert "episode_observe" not in eb.OWNER_GAP_REASONS
