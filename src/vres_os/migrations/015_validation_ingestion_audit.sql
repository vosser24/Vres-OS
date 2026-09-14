-- Durable validator-ingestion provenance and stale/superseded request states.

ALTER TABLE vres.validation_requests
    DROP CONSTRAINT IF EXISTS validation_requests_status_check;

ALTER TABLE vres.validation_requests
    ADD CONSTRAINT validation_requests_status_check
    CHECK (status IN ('pending','passed','failed','rejected','stale','superseded'));

CREATE TABLE IF NOT EXISTS vres.validation_ingestion_attempts (
    id bigserial PRIMARY KEY,
    attempt_key text NOT NULL UNIQUE,
    validation_request_id bigint REFERENCES vres.validation_requests(id) ON DELETE SET NULL,
    request_key text,
    project_id bigint REFERENCES vres.projects(id) ON DELETE RESTRICT,
    task_id bigint REFERENCES vres.tasks(id) ON DELETE SET NULL,
    disposition text NOT NULL CHECK (disposition IN ('accepted','rejected','stale','unobserved')),
    reason text NOT NULL,
    agent_type text,
    agent_id text,
    provider_session_id text,
    payload_keys jsonb NOT NULL DEFAULT '[]'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_validation_ingestion_request
    ON vres.validation_ingestion_attempts(validation_request_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_validation_ingestion_project
    ON vres.validation_ingestion_attempts(project_id, created_at DESC);

CREATE OR REPLACE FUNCTION vres.supersede_pending_validation_requests()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE vres.validation_requests
       SET status='superseded', completed_at=COALESCE(completed_at, now())
     WHERE task_id=NEW.task_id
       AND status='pending';
    RETURN NEW;
END
$$;

DROP TRIGGER IF EXISTS trg_supersede_pending_validation_requests
    ON vres.validation_requests;
CREATE TRIGGER trg_supersede_pending_validation_requests
BEFORE INSERT ON vres.validation_requests
FOR EACH ROW
EXECUTE FUNCTION vres.supersede_pending_validation_requests();
