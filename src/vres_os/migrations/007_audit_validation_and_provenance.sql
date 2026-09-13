-- Additive audit migration. Released 001..006 remain byte-identical to the recovered source.
CREATE TABLE vres.validation_requests (
    id bigserial PRIMARY KEY,
    request_key text NOT NULL UNIQUE,
    task_id bigint NOT NULL REFERENCES vres.tasks(id) ON DELETE CASCADE,
    state_digest text NOT NULL,
    artifact_manifest jsonb NOT NULL DEFAULT '{}'::jsonb,
    status text NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','passed','failed')),
    observed_model text,
    agent_id text,
    session_id text,
    report jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    completed_at timestamptz
);
CREATE INDEX idx_validation_task ON vres.validation_requests(task_id,created_at DESC);
CREATE TABLE vres.relation_evidence (
    id bigserial PRIMARY KEY,
    relation_id bigint NOT NULL REFERENCES vres.relations(id) ON DELETE CASCADE,
    provenance text NOT NULL,
    confidence numeric(5,4),
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(relation_id,provenance)
);
INSERT INTO vres.relation_evidence(relation_id,provenance,confidence)
SELECT id,provenance,confidence FROM vres.relations WHERE provenance IS NOT NULL;
ALTER TABLE vres.optimization_candidates ADD COLUMN experiment_key text;
CREATE UNIQUE INDEX idx_optimization_experiment ON vres.optimization_candidates(procedure_id,experiment_key)
WHERE experiment_key IS NOT NULL;
ALTER TABLE vres.preferences ADD COLUMN source_event_id bigint REFERENCES vres.task_events(id) ON DELETE RESTRICT;
ALTER TABLE vres.preference_history ADD COLUMN source_event_id bigint REFERENCES vres.task_events(id) ON DELETE RESTRICT;
