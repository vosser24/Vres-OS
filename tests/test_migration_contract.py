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


def test_initial_migration_does_not_make_pg_trgm_a_hard_requirement():
    sql = _migration("001_initial.sql")
    assert "pg_available_extensions" in sql
    assert "pg_trgm could not be enabled" in sql
