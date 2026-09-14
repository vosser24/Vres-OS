-- Distinguish caller-reported model telemetry from future host-observed experiment evidence.
-- Existing rows are grandfathered as reported and remain advisory.
ALTER TABLE vres.model_runs
    ADD COLUMN IF NOT EXISTS measurement_source text NOT NULL DEFAULT 'reported'
    CHECK (measurement_source IN ('reported','host'));
ALTER TABLE vres.model_runs
    ADD COLUMN IF NOT EXISTS input_digest text;
ALTER TABLE vres.model_runs
    ADD COLUMN IF NOT EXISTS output_digest text;
ALTER TABLE vres.model_runs
    ADD COLUMN IF NOT EXISTS execution_evidence jsonb NOT NULL DEFAULT '{}'::jsonb;

CREATE INDEX IF NOT EXISTS idx_model_runs_measurement_source
    ON vres.model_runs(measurement_source,phase,task_family,created_at DESC);
