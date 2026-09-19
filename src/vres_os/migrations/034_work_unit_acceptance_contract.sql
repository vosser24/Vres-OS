-- Durable acceptance contracts for governed work units.
-- Criteria stay on the work unit; results stay on expert-report events.
-- No separate acceptance-management subsystem is introduced.

ALTER TABLE vres.orchestration_work_units
    ADD COLUMN IF NOT EXISTS acceptance_criteria jsonb NOT NULL DEFAULT '[]'::jsonb,
    ADD COLUMN IF NOT EXISTS verifies jsonb NOT NULL DEFAULT '[]'::jsonb;

ALTER TABLE vres.orchestration_work_units
    DROP CONSTRAINT IF EXISTS chk_orchestration_work_units_acceptance_criteria_array,
    ADD CONSTRAINT chk_orchestration_work_units_acceptance_criteria_array
        CHECK (jsonb_typeof(acceptance_criteria) = 'array');

ALTER TABLE vres.orchestration_work_units
    DROP CONSTRAINT IF EXISTS chk_orchestration_work_units_verifies_array,
    ADD CONSTRAINT chk_orchestration_work_units_verifies_array
        CHECK (jsonb_typeof(verifies) = 'array');
