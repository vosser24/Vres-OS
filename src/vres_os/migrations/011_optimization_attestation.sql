-- Separate caller-reported telemetry from runtime-measured replay evidence.
ALTER TABLE vres.procedure_runs
    ADD COLUMN IF NOT EXISTS measurement_source text NOT NULL DEFAULT 'reported'
    CHECK (measurement_source IN ('reported','runtime'));

CREATE TABLE IF NOT EXISTS vres.procedure_replay_attestations (
    id bigserial PRIMARY KEY,
    replay_key text NOT NULL UNIQUE,
    procedure_id bigint NOT NULL REFERENCES vres.procedures(id) ON DELETE CASCADE,
    baseline_version integer NOT NULL,
    candidate_version integer NOT NULL,
    baseline_run_id bigint NOT NULL REFERENCES vres.procedure_runs(id) ON DELETE RESTRICT,
    candidate_run_id bigint NOT NULL REFERENCES vres.procedure_runs(id) ON DELETE RESTRICT,
    validation_request_id bigint NOT NULL REFERENCES vres.validation_requests(id) ON DELETE RESTRICT,
    baseline_contract_fingerprint text NOT NULL,
    candidate_contract_fingerprint text NOT NULL,
    output_equivalent boolean NOT NULL,
    protected_regression boolean NOT NULL DEFAULT false,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(procedure_id,candidate_version,validation_request_id),
    CHECK (candidate_version <> baseline_version)
);

ALTER TABLE vres.optimization_candidates
    ADD COLUMN IF NOT EXISTS replay_attestation_id bigint
    REFERENCES vres.procedure_replay_attestations(id) ON DELETE RESTRICT;

CREATE INDEX IF NOT EXISTS idx_procedure_replay_candidate
    ON vres.procedure_replay_attestations(procedure_id,candidate_version,created_at DESC);
