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


def test_initial_migration_does_not_make_pg_trgm_a_hard_requirement():
    sql = _migration("001_initial.sql")
    assert "pg_available_extensions" in sql
    assert "pg_trgm could not be enabled" in sql
