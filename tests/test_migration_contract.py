from importlib import resources


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


def test_initial_migration_does_not_make_pg_trgm_a_hard_requirement():
    sql = _migration("001_initial.sql")
    assert "pg_available_extensions" in sql
    assert "pg_trgm could not be enabled" in sql
