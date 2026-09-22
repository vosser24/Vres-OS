-- Widen validation_ingestion_attempts.disposition to allow a durable 'deferred'
-- outcome for a demonstrably interim validator SubagentStop (live background task),
-- distinct from accepted/rejected/stale/unobserved. This event must never mutate
-- vres.validation_requests.status or vres.task_state.validation_status.

ALTER TABLE vres.validation_ingestion_attempts
    DROP CONSTRAINT IF EXISTS validation_ingestion_attempts_disposition_check;

ALTER TABLE vres.validation_ingestion_attempts
    ADD CONSTRAINT validation_ingestion_attempts_disposition_check
    CHECK (disposition IN ('accepted','rejected','stale','unobserved','deferred'));
