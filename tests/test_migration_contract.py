import runpy
from importlib import resources
from pathlib import Path


def _migration(name: str) -> str:
    return resources.files("vres_os").joinpath("migrations", name).read_text(encoding="utf-8")


def test_initial_migration_contains_core_memory_contracts():
    sql = _migration("001_initial.sql")
    for table in [
        "vres.tasks", "vres.task_state", "vres.checkpoints", "vres.knowledge_items",
        "vres.procedures", "vres.procedure_versions", "vres.model_runs", "vres.review_queue",
    ]:
        assert table in sql


def test_operational_migration_contains_learning_contracts():
    sql = _migration("002_operational_memory.sql")
    for table in [
        "vres.sessions", "vres.artifacts", "vres.knowledge_chunks", "vres.embedding_jobs",
        "vres.preferences", "vres.domain_manifests", "vres.refresh_runs",
    ]:
        assert table in sql
    assert "pg_available_extensions" in sql
    assert "embedding_vector vector" in sql


def test_capability_seed_covers_core_domains():
    sql = _migration("003_capability_seed.sql")
    for capability in ["Software Engineering", "PostgreSQL", "Demand Forecasting", "Pricing", "Ecommerce Search"]:
        assert capability in sql


def test_governance_migration_adds_authoritative_objects_and_approval_provenance():
    sql = _migration("006_governance_hardening.sql")
    for table in ["vres.registry_objects", "vres.capability_proofs", "vres.preference_history", "vres.project_focus", "vres.approval_events"]:
        assert table in sql
    assert "approval_event_id" in sql
    assert "bootstrap.validate" in sql
    assert "'fable'" in sql


def test_company_authority_migration_preserves_scope_approval_provenance():
    sql = _migration("010_company_authority.sql")
    for table in [
        "vres.sources",
        "vres.knowledge_items",
        "vres.procedures",
        "vres.registry_objects",
        "vres.capabilities",
    ]:
        assert f"ALTER TABLE {table}" in sql
    assert sql.count("scope_approval_event_id") >= 5
    assert "ON DELETE RESTRICT" in sql
    assert "idx_approval_events_type_subject" in sql


def test_optimization_attestation_migration_separates_reported_and_runtime_evidence():
    sql = _migration("011_optimization_attestation.sql")
    assert "measurement_source" in sql
    assert "'reported','runtime'" in sql
    assert "input_digest" in sql and "output_digest" in sql
    assert "context_type" in sql and "context_key" in sql and "context_payload" in sql
    assert "vres.procedure_replay_attestations" in sql
    assert "validation_request_id" in sql
    assert "replay_attestation_id" in sql
    assert "ON DELETE RESTRICT" in sql


def test_model_run_provenance_migration_separates_reported_and_host_evidence():
    sql = _migration("012_model_run_provenance.sql")
    assert "ALTER TABLE vres.model_runs" in sql
    assert "measurement_source" in sql
    assert "'reported','host'" in sql
    assert "input_digest" in sql and "output_digest" in sql
    assert "execution_evidence" in sql
    assert "idx_model_runs_measurement_source" in sql


def test_company_optimization_migration_separates_candidate_and_promotion_authority():
    sql = _migration("013_company_optimization_authority.sql")
    assert "ALTER TABLE vres.procedure_versions" in sql
    assert "scope_approval_event_id" in sql
    assert "candidate_approval_event_id" in sql
    assert "promotion_approval_event_id" in sql
    assert "'company_promoted'" in sql
    assert "ON DELETE RESTRICT" in sql
    assert "idx_optimization_candidate_approvals" in sql


def test_model_experiment_migration_binds_host_runs_to_protected_validation():
    sql = _migration("014_model_experiment_attestation.sql")
    assert "vres.model_experiment_attestations" in sql
    assert "baseline_run_id" in sql and "candidate_run_id" in sql
    assert "validation_request_id" in sql
    assert "baseline_identity" in sql and "candidate_identity" in sql
    assert "candidate_quality_not_worse" in sql
    assert "protected_regression" in sql
    assert sql.count("ON DELETE RESTRICT") >= 3
    assert "idx_model_experiment_phase" in sql


def test_validation_status_contract_removes_not_required_vocabulary():
    sql = _migration("017_validation_status_contract.sql")
    assert "validation_status='not_required'" in sql
    assert "validation_status='pending'" in sql
    assert "ALTER COLUMN validation_status SET DEFAULT 'pending'" in sql
    assert "CHECK (validation_status IN ('pending','passed','failed'))" in sql


def test_task_status_contract_removes_legacy_new_vocabulary():
    sql = _migration("018_task_status_contract.sql")
    assert "status='new'" in sql
    assert "SET status='active'" in sql
    assert "DROP CONSTRAINT IF EXISTS tasks_status_check" in sql
    assert "CHECK (status IN ('active','waiting_user','blocked','completed','cancelled'))" in sql
    assert "'new'" not in sql.split("CHECK (status IN", 1)[1]


def test_dead_task_project_metadata_contract_is_removed():
    sql = _migration("019_remove_dead_task_project_metadata.sql")
    assert "ALTER TABLE vres.projects" in sql
    assert "ALTER TABLE vres.tasks" in sql
    assert sql.count("DROP COLUMN IF EXISTS metadata") == 2


def test_task_decision_provenance_adds_ledger_and_checkpoint_snapshots():
    sql = _migration("020_task_decision_provenance.sql")
    assert "CREATE TABLE IF NOT EXISTS vres.task_decisions" in sql
    assert "CREATE TABLE IF NOT EXISTS vres.checkpoint_decisions" in sql
    assert "legacy_unstructured" in sql
    assert "capture_checkpoint_decisions" in sql
    assert "enforce_task_decision_projection" in sql


def test_decision_hardening_protects_history_and_releases_completed_sessions():
    sql = _migration("021_decision_immutability_and_completion_sessions.sql")
    assert "protect_task_decision_update" in sql
    assert "protect_decision_ledger_delete" in sql
    assert "protect_checkpoint_decision_history" in sql
    assert "release_completed_task_sessions" in sql
    assert "task_completed" in sql
    assert "SESSION_UNBOUND" in sql
    assert "vres.allow_decision_ledger_delete" in sql


def test_user_read_only_hold_is_protected_by_trusted_writer_boundary():
    sql = _migration("029_user_read_only_hold.sql")
    assert "vres_read_only_hold" in sql
    assert "protect_user_input_metadata" in sql
    assert "stage_user_input" in sql
    assert "p_source = 'user_prompt'" in sql
    assert "explicit_read_only_user_instruction" in sql
    assert "later_user_prompt" in sql
    assert "session_user <> allowed::text" in sql


def test_latest_observed_user_instruction_is_writer_only_security_definer():
    sql = _migration("032_latest_observed_user_instruction.sql")
    assert "latest_observed_user_instruction" in sql
    assert "SECURITY DEFINER" in sql
    assert "session_user <> allowed::text" in sql
    assert "user_input_observations" in sql
    assert "REVOKE ALL ON FUNCTION" in sql


def test_project_agent_work_unit_migration_is_minimal_dependency_dag():
    sql = _migration("033_project_agent_work_units.sql")
    assert "orchestration_work_units" in sql
    assert "depends_on jsonb" in sql
    assert "write_scope jsonb" in sql
    assert "attempt_count" in sql
    assert "work_unit_key" in sql
    assert "project_agent_key" in sql
    assert "parallel_group" not in sql
    assert "enforce_current_work_graph_completion" in sql


def test_work_unit_acceptance_migration_extends_existing_dag_without_new_subsystem():
    sql = _migration("034_work_unit_acceptance_contract.sql")
    assert "acceptance_criteria jsonb" in sql
    assert "verifies jsonb" in sql
    assert "orchestration_work_units" in sql
    assert "CREATE TABLE" not in sql
    assert "story" not in sql.lower()
    assert "test_case" not in sql.lower()


def test_initial_migration_does_not_make_pg_trgm_a_hard_requirement():
    sql = _migration("001_initial.sql")
    assert "pg_available_extensions" in sql
    assert "pg_trgm could not be enabled" in sql

def test_release_gate_migration_digest_normalizes_checkout_newlines(tmp_path):
    gate_path = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "release_gate.py"
    )
    gate = runpy.run_path(str(gate_path))

    lf = tmp_path / "lf.sql"
    crlf = tmp_path / "crlf.sql"

    lf.write_bytes(b"SELECT 1;\nSELECT 2;\n")
    crlf.write_bytes(b"SELECT 1;\r\nSELECT 2;\r\n")

    assert gate["migration_digest"](lf) == gate["migration_digest"](crlf)


def test_experience_episode_migration_is_bounded_immutable_and_versioned():
    sql = _migration("037_experience_episode_ledger.sql")
    assert "CREATE TABLE IF NOT EXISTS vres.experience_policy_versions" in sql
    assert "CREATE TABLE IF NOT EXISTS vres.experience_episodes" in sql
    assert "176.e1.v1" in sql
    assert "policy_digest" in sql
    assert "source_digest" in sql and "payload_digest" in sql
    assert "participation_class" in sql and "trust_class" in sql
    assert "security_disposition" in sql
    assert "uq_experience_episode_task" in sql
    assert "uq_experience_episode_work_unit" in sql
    assert "protect_experience_episode_immutability" in sql
    assert "protect_experience_policy_immutability" in sql
    assert "allow_experience_ledger_delete" in sql


def test_experience_transition_migration_is_append_only_versioned_and_idempotent_by_candidate():
    from vres_os.experience_consolidation import POLICY, POLICY_DIGEST, POLICY_VERSION, _canonical

    sql = _migration("038_experience_transitions.sql")
    assert "CREATE TABLE IF NOT EXISTS vres.experience_transitions" in sql
    assert POLICY_VERSION == "176.e2.v1" and "'176.e2.v1'" in sql
    assert sql.count(POLICY_DIGEST) == 2
    assert _canonical(POLICY) in sql
    assert "UNIQUE (project_id, candidate_digest)" in sql
    assert "verdict IN ('accepted','deduplicated','quarantined')" in sql
    assert "protect_experience_transition_immutability" in sql
    assert "allow_experience_ledger_delete" in sql
    assert "RETURN NEW;" not in sql
    assert "176.e1.v1" not in sql


def test_experience_lifecycle_ledger_migration_is_append_only_bounded_and_additive():
    sql = _migration("039_experience_lifecycle_ledger.sql")
    assert sql.count("CREATE TABLE") == 1
    assert "CREATE TABLE IF NOT EXISTS vres.experience_lifecycle_events" in sql
    assert "protect_experience_lifecycle_immutability" in sql
    assert "BEFORE UPDATE ON vres.experience_lifecycle_events" in sql
    assert "BEFORE DELETE ON vres.experience_lifecycle_events" in sql
    assert "DROP TRIGGER IF EXISTS" in sql
    # No bypass: UPDATE and DELETE always raise (test cleanup disables the trigger as table owner).
    assert "allow_experience_ledger_delete" not in sql
    assert "current_setting" not in sql
    assert "RETURN OLD" not in sql
    assert "RETURN NEW" not in sql
    assert "TRUNCATE" not in sql
    assert "policy_version = '176.e4.v1'" in sql
    # nine-value knowledge status vocabulary, drop/re-add without a data rewrite
    assert "DROP CONSTRAINT IF EXISTS knowledge_items_status_check" in sql
    assert (
        "CHECK (status IN ('proposed','observed','validated','canonical','challenged',"
        "'superseded','rejected','retired','revoked'))"
    ) in sql
    assert "UPDATE vres.knowledge_items" not in sql
    # not touching earlier policy/objects, sources, sessions, retrieval or observation storage
    assert "176.e1" not in sql and "176.e2" not in sql
    assert "ALTER TABLE vres.sources" not in sql
    assert "vres.sessions" not in sql
    assert "embedding_jobs" not in sql
    assert "experience_policy_versions" not in sql
    assert "experience_transitions" not in sql and "experience_episodes" not in sql


def test_context_refresh_attestation_migration_is_additive_protected_and_hash_only():
    sql = _migration("040_context_refresh_attestation.sql")
    assert sql.count("CREATE TABLE") == 1
    assert "CREATE TABLE IF NOT EXISTS vres.context_refresh_attestations" in sql
    assert "nonce_sha256 text NOT NULL UNIQUE" in sql and "nonce text" not in sql  # only a hash of the nonce
    assert "UNIQUE (provider_session_id, tool_use_id)" in sql
    assert "interval '120 seconds'" in sql
    for fn in ("issue_context_refresh_attestation", "consume_context_refresh_attestation",
               "require_attested_context_refresh"):
        assert f"CREATE OR REPLACE FUNCTION vres.{fn}(" in sql
    assert sql.count("SECURITY DEFINER") == 3
    assert sql.count("SET search_path = pg_catalog, vres") == 3
    assert "authority_key = 'user_event_writer'" in sql and "session_user" in sql  # writer-only mint
    assert "AFTER INSERT ON vres.experience_lifecycle_events" in sql
    assert "DROP TRIGGER IF EXISTS trg_require_attested_context_refresh" in sql
    for obj in ("TABLE vres.context_refresh_attestations", "SEQUENCE vres.context_refresh_attestations_id_seq",
                "FUNCTION vres.issue_context_refresh_attestation(text,text,text,text)",
                "FUNCTION vres.consume_context_refresh_attestation(bigint,text,text,text)",
                "FUNCTION vres.require_attested_context_refresh()"):
        assert f"REVOKE ALL ON {obj} FROM PUBLIC;" in sql
    assert "GRANT " not in sql  # grants belong to database_boundary.activate_boundary
    # additive only: no sessions/metadata change, no edit to 029's protected-metadata trigger or the 039 ledger
    code = "\n".join(line for line in sql.splitlines() if not line.lstrip().startswith("--"))
    assert "ALTER TABLE" not in code and "metadata" not in code
    assert "protect_user_input_metadata" not in code and "stage_user_input" not in code
    assert "protect_experience_lifecycle_immutability" not in code
    assert "UPDATE vres.experience_lifecycle_events" not in code and "DELETE FROM" not in code
    assert "UPDATE vres.sessions" not in code and "INSERT INTO vres.sessions" not in code


def test_experience_retrieval_observability_migration_041_contract():
    sql = _migration("041_experience_retrieval_observability.sql")
    code = "\n".join(line for line in sql.splitlines() if not line.lstrip().startswith("--"))
    assert "176.e6.v1" in sql and "d61f60d31182085748bb613ef3c160274f1a1a5a2384854f36e52b4cdfecc5e5" in sql
    assert "7572cafc632d4f56571adbe5f59baceedf15c56a07d5a3ca35e4b05448a982e9" in sql
    for table in ("experience_retrieval_observations", "experience_retrieval_items", "experience_retrieval_references",
                  "experience_retrieval_replays"):
        assert f"CREATE TABLE IF NOT EXISTS vres.{table}" in code
    for event in ("UPDATE", "DELETE", "TRUNCATE"):
        assert f"BEFORE {event}" in code
    for trg in ("trg_protect_err_update", "trg_protect_err_delete", "trg_protect_err_truncate"):
        assert f"CREATE TRIGGER {trg}" in code
    assert code.count("EXECUTE FUNCTION vres.protect_experience_retrieval_immutability()") == 12
    assert "CREATE OR REPLACE FUNCTION vres.record_experience_retrieval_observation(" in code
    assert "SECURITY DEFINER" in code and "SET search_path = pg_catalog, vres" in code
    assert "authority_key = 'user_event_writer'" in code and "session_user" in code
    assert "GRANT " not in code  # grants belong to database_boundary.activate_boundary
    for forbidden in ("query_text text", "memory_text text", "raw_query", "tool_response jsonb", "premises jsonb", "text_body"):
        assert forbidden not in code
    assert "ALTER TABLE" not in code and "UPDATE vres.sessions" not in code and "DELETE FROM" not in code


def test_migration_041_work_unit_attribution_and_policy_row_are_strict():
    sql = _migration("041_experience_retrieval_observability.sql")
    code = "\n".join(line for line in sql.splitlines() if not line.lstrip().startswith("--"))
    flat = " ".join(code.split())
    predicate = "w.task_id = task_row AND w.host_agent_id = p_agent_id AND w.status = 'running'"
    assert flat.count(predicate) == 2  # the COUNT and the key lookup use the identical current-unit predicate
    assert "p_agent_id IS NOT NULL AND (p_agent_type IS NULL OR char_length(p_agent_type) NOT BETWEEN 1 AND 200)" in flat
    # the post-insert verification compares the exact frozen policy JSON, not just version/schema/digest
    verify = flat.split("DO $vres_e6$", 1)[1].split("END", 1)[0]
    assert "policy='{" in verify and '"policy_version":"176.e6.v1"' in verify


def test_migration_041_reference_ledger_and_writer_contract():
    sql = _migration("041_experience_retrieval_observability.sql")
    code = "\n".join(line for line in sql.splitlines() if not line.lstrip().startswith("--"))
    flat = " ".join(code.split())
    table = flat.split("CREATE TABLE IF NOT EXISTS vres.experience_retrieval_references", 1)[1].split(");", 1)[0]
    for column in ("reference_key", "idempotency_key", "observation_id", "memory_key", "source_kind", "host_event_digest",
                   "evidence_digest", "tool_use_id", "agent_id", "observed_at", "created_at"):
        assert column in table
    assert "'assistant_public_text','assistant_tool_input','subagent_handback'" in table.replace(" ", "")
    assert "REFERENCES vres.experience_retrieval_observations(id) ON DELETE RESTRICT" in table
    assert "UNIQUE (observation_id, memory_key, source_kind, host_event_digest)" in table
    for forbidden in (" text_body", "raw_text", "message text", "content text", "tool_input jsonb", "tool_response"):
        assert forbidden not in table
    fn = flat.split("CREATE OR REPLACE FUNCTION vres.record_experience_retrieval_references(", 1)[1]
    assert "SECURITY DEFINER SET search_path = pg_catalog, vres" in fn
    assert "authority_key = 'user_event_writer'" in fn and "session_user <> allowed::text" in fn
    # per-key attribution: same project + exact session + same agent context (NULL means NULL), prior, not self, latest
    assert "o.project_id = p_project_id AND o.session_id = sess.id" in fn
    assert "o.host_agent_id IS NOT DISTINCT FROM p_agent_id" in fn
    assert "o.observed_at < now_ts" in fn and "o.tool_use_id IS DISTINCT FROM p_tool_use_id" in fn
    assert "ORDER BY o.observed_at DESC, o.id DESC LIMIT 100" in fn and "cardinality(p_memory_keys) > 500" in fn
    for refuse in ("REVOKE ALL ON TABLE vres.experience_retrieval_references FROM PUBLIC",
                   "REVOKE ALL ON SEQUENCE vres.experience_retrieval_references_id_seq FROM PUBLIC",
                   "REVOKE ALL ON FUNCTION vres.record_experience_retrieval_references(bigint,text,text,text,text,text,text,text[]) FROM PUBLIC"):
        assert refuse in flat
    assert "GRANT " not in code and "UPDATE vres.experience_retrieval" not in code


def test_migration_041_reference_writer_orders_by_observed_at_and_locks_before_resolving_conflicts():
    sql = _migration("041_experience_retrieval_observability.sql")
    code = "\n".join(line for line in sql.splitlines() if not line.lstrip().startswith("--"))
    flat = " ".join(code.split())
    fn = flat.split("CREATE OR REPLACE FUNCTION vres.record_experience_retrieval_references(", 1)[1].split("$vres_e6$;", 1)[0]
    # the bounded candidate set keeps observed_at so the final selection can order by it (never by id alone)
    assert "SELECT o.id, o.observed_at FROM vres.experience_retrieval_observations o" in fn
    assert "ORDER BY c.observed_at DESC, c.id DESC LIMIT 1" in fn and "ORDER BY c.id DESC" not in fn
    # one stable per-reference lock identity (independent of the selected observation), taken before any duplicate check
    lock = fn.index("pg_advisory_xact_lock")
    assert lock < fn.index("FROM vres.experience_retrieval_references r")
    assert lock < fn.index("conflicting duplicate experience retrieval reference")
    identity = fn[:lock].rsplit("idem := ", 1)[1]
    for part in ("p_project_id", "sess.id", "p_agent_id", "p_source_kind", "p_host_event_digest", "'176.e6.v1'"):
        assert part in identity
    assert "obs_id" not in identity
    # no race-sensitive ON CONFLICT that could turn a conflicting digest into an ordinary duplicate
    assert "ON CONFLICT" not in fn


def test_migration_041_replay_ledger_and_writer_contract():
    sql = _migration("041_experience_retrieval_observability.sql")
    code = "\n".join(line for line in sql.splitlines() if not line.lstrip().startswith("--"))
    flat = " ".join(code.split())
    table = flat.split("CREATE TABLE IF NOT EXISTS vres.experience_retrieval_replays", 1)[1].split(");", 1)[0]
    for column in ("replay_key", "idempotency_key", "project_id", "task_id", "policy_version", "request_digest", "snapshot_at",
                   "baseline_retrieval_policy_digest", "candidate_policy", "candidate_policy_digest", "baseline_pack_digest",
                   "candidate_pack_digest", "baseline_item_keys", "candidate_item_keys", "added_keys", "removed_keys",
                   "reordered_keys", "baseline_pack_bytes", "candidate_pack_bytes", "baseline_estimated_tokens",
                   "candidate_estimated_tokens", "baseline_abstained", "candidate_abstained", "diagnostics_delta",
                   "causal_credit", "created_at"):
        assert column in table
    assert "causal_credit text NOT NULL DEFAULT 'not_established' CHECK (causal_credit = 'not_established')" in table
    assert "policy_version text NOT NULL DEFAULT '176.e6.v1' CHECK (policy_version = '176.e6.v1')" in table
    for forbidden in ("query", "premises", "memory_text", "pack_body", "transcript", "reasoning", "credential", "vector",
                      "winner", "better", "recommended", "utility_score", "success_probability", "promote", "activate"):
        assert forbidden not in table
    fn = flat.split("CREATE OR REPLACE FUNCTION vres.record_experience_retrieval_replay(", 1)[1].split("$vres_e6$;", 1)[0]
    assert fn.lstrip().startswith("p_project_id bigint, p_task_id bigint, p_replay jsonb")
    assert "SECURITY DEFINER SET search_path = pg_catalog, vres" in fn
    assert "authority_key = 'user_event_writer'" in fn and "session_user <> allowed::text" in fn
    # deterministic idempotency identity, advisory lock BEFORE the lookup, no ON CONFLICT masking, never an overwrite
    lock = fn.index("pg_advisory_xact_lock")
    assert lock < fn.index("FROM vres.experience_retrieval_replays r")
    identity = fn[:lock].rsplit("idem := ", 1)[1]
    for part in ("p_project_id", "p_task_id", "request_digest", "candidate_policy_digest", "baseline_pack_digest",
                 "candidate_pack_digest", "'176.e6.v1'"):
        assert part in identity
    assert "ON CONFLICT" not in fn and "UPDATE vres.experience_retrieval_replays" not in fn
    for refuse in ("REVOKE ALL ON TABLE vres.experience_retrieval_replays FROM PUBLIC",
                   "REVOKE ALL ON SEQUENCE vres.experience_retrieval_replays_id_seq FROM PUBLIC",
                   "REVOKE ALL ON FUNCTION vres.record_experience_retrieval_replay(bigint,bigint,jsonb) FROM PUBLIC"):
        assert refuse in flat
    assert "GRANT " not in code and "DELETE FROM" not in code and "ALTER TABLE" not in code
    assert not any(
        n.name.startswith("043")
        for n in resources.files("vres_os").joinpath("migrations").iterdir()
    )


def test_migration_042_is_the_last_and_only_replaces_the_two_041_identity_checks():
    names = sorted(
        n.name
        for n in resources.files("vres_os").joinpath("migrations").iterdir()
        if n.name.endswith(".sql")
    )
    assert names[-1] == "042_experience_retrieval_policy_v2.sql"
    sql = _migration("042_experience_retrieval_policy_v2.sql")
    code = "\n".join(line for line in sql.splitlines() if not line.lstrip().startswith("--"))
    assert code.count("DROP CONSTRAINT") == 2 and code.count("ADD CONSTRAINT") == 1
    for forbidden in (
        "CREATE TABLE",
        "ADD COLUMN",
        "UPDATE ",
        "INSERT ",
        "DELETE ",
        "TRIGGER",
        "GRANT",
        "REVOKE",
        "CREATE OR REPLACE FUNCTION",
        " IN (",
    ):
        assert forbidden not in code, forbidden
    assert "experience_retrieval_observation_retrieval_schema_version_check" in code
    assert "experience_retrieval_observations_retrieval_policy_digest_check" in code
    assert "experience_retrieval_observations_e5_identity_pair_check" in code
    assert "'176.e5.v1'" in code and "'176.e5.v2'" in code
    assert "7572cafc632d4f56571adbe5f59baceedf15c56a07d5a3ca35e4b05448a982e9" in code
    assert "0cd0f10d24e37dd7a9872eced6c18e4962d4740a2d6a8c03a38cea1d8a73d6b5" in code
    assert code.count("(retrieval_schema_version = '176.e5.v") == 2 and " OR " in code
    old = _migration("041_experience_retrieval_observability.sql")  # immutable: still pins v1 only
    assert "CHECK (retrieval_schema_version = '176.e5.v1')" in old and "176.e5.v2" not in old
