-- Bind paired host-observed model runs to one frozen protected validation result.
-- This is evidence only: it does not mutate model_policies.
CREATE TABLE IF NOT EXISTS vres.model_experiment_attestations (
    id bigserial PRIMARY KEY,
    experiment_key text NOT NULL UNIQUE,
    phase text NOT NULL,
    task_family text,
    baseline_run_id bigint NOT NULL REFERENCES vres.model_runs(id) ON DELETE RESTRICT,
    candidate_run_id bigint NOT NULL REFERENCES vres.model_runs(id) ON DELETE RESTRICT,
    validation_request_id bigint NOT NULL REFERENCES vres.validation_requests(id) ON DELETE RESTRICT,
    input_digest text NOT NULL,
    baseline_output_digest text NOT NULL,
    candidate_output_digest text NOT NULL,
    baseline_identity jsonb NOT NULL,
    candidate_identity jsonb NOT NULL,
    candidate_quality_not_worse boolean NOT NULL,
    protected_regression boolean NOT NULL DEFAULT false,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(baseline_run_id,candidate_run_id,validation_request_id),
    CHECK (candidate_run_id <> baseline_run_id)
);

CREATE INDEX IF NOT EXISTS idx_model_experiment_phase
    ON vres.model_experiment_attestations(phase,task_family,created_at DESC);
