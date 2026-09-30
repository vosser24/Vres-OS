-- #176 E4 Chunk A: append-only lifecycle ledger and knowledge status vocabulary.
-- Schema only. Lifecycle history lives here; current state stays in vres.knowledge_items.status.

CREATE TABLE IF NOT EXISTS vres.experience_lifecycle_events (
    id bigserial PRIMARY KEY,
    event_key text NOT NULL UNIQUE,
    idempotency_key text NOT NULL UNIQUE CHECK (idempotency_key ~ '^[0-9a-f]{64}$'),
    project_id bigint NOT NULL REFERENCES vres.projects(id) ON DELETE RESTRICT,
    policy_version text NOT NULL CHECK (policy_version = '176.e4.v1'),
    action text NOT NULL CHECK (action IN (
        'retire','reinstate','supersede','challenge','refresh','expire_observed',
        'revoke_source','invalidate_derived','restore_derived',
        'context_contaminated','context_refreshed'
    )),
    target_kind text NOT NULL CHECK (target_kind IN ('knowledge','source','episode','session')),
    target_key text NOT NULL CHECK (char_length(target_key) BETWEEN 1 AND 300),
    prior_state text CHECK (prior_state IS NULL OR char_length(prior_state) <= 64),
    new_state text CHECK (new_state IS NULL OR char_length(new_state) <= 64),
    cause_kind text NOT NULL CHECK (cause_kind IN ('approval','source','knowledge','episode','session','time')),
    cause_key text NOT NULL CHECK (char_length(cause_key) BETWEEN 1 AND 300),
    approval_event_id bigint REFERENCES vres.approval_events(id) ON DELETE RESTRICT,
    task_id bigint REFERENCES vres.tasks(id) ON DELETE RESTRICT,
    session_key text,
    reason text NOT NULL CHECK (char_length(reason) BETWEEN 1 AND 500),
    detail jsonb NOT NULL DEFAULT '{}'::jsonb
        CHECK (jsonb_typeof(detail) = 'object' AND octet_length(detail::text) <= 8192),
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT ck_experience_lifecycle_action_target CHECK (
        (action = 'revoke_source' AND target_kind = 'source')
        OR (action IN ('retire','reinstate','supersede','challenge','refresh','expire_observed')
            AND target_kind = 'knowledge')
        OR (action IN ('invalidate_derived','restore_derived')
            AND target_kind IN ('knowledge','episode'))
        OR (action IN ('context_contaminated','context_refreshed') AND target_kind = 'session')
    ),
    CONSTRAINT ck_experience_lifecycle_approval_required CHECK (
        action NOT IN ('retire','reinstate','supersede','challenge','refresh','revoke_source','restore_derived')
        OR approval_event_id IS NOT NULL
    ),
    CONSTRAINT ck_experience_lifecycle_session_key CHECK (
        action NOT IN ('context_contaminated','context_refreshed') OR session_key IS NOT NULL
    )
);

CREATE INDEX IF NOT EXISTS idx_experience_lifecycle_project
    ON vres.experience_lifecycle_events(project_id, id DESC);
CREATE INDEX IF NOT EXISTS idx_experience_lifecycle_target
    ON vres.experience_lifecycle_events(project_id, target_kind, target_key, id DESC);
CREATE INDEX IF NOT EXISTS idx_experience_lifecycle_cause
    ON vres.experience_lifecycle_events(project_id, cause_key);
CREATE INDEX IF NOT EXISTS idx_experience_lifecycle_session
    ON vres.experience_lifecycle_events(project_id, session_key, id DESC)
    WHERE session_key IS NOT NULL;

CREATE OR REPLACE FUNCTION vres.protect_experience_lifecycle_immutability()
RETURNS trigger
LANGUAGE plpgsql
AS $vres_lifecycle$
BEGIN
    -- Append-only with no bypass setting: UPDATE and DELETE always raise.
    RAISE EXCEPTION 'experience_lifecycle_events are immutable; append a new event instead of modifying history';
END
$vres_lifecycle$;

DROP TRIGGER IF EXISTS trg_protect_experience_lifecycle_update ON vres.experience_lifecycle_events;
CREATE TRIGGER trg_protect_experience_lifecycle_update
BEFORE UPDATE ON vres.experience_lifecycle_events
FOR EACH ROW EXECUTE FUNCTION vres.protect_experience_lifecycle_immutability();

DROP TRIGGER IF EXISTS trg_protect_experience_lifecycle_delete ON vres.experience_lifecycle_events;
CREATE TRIGGER trg_protect_experience_lifecycle_delete
BEFORE DELETE ON vres.experience_lifecycle_events
FOR EACH ROW EXECUTE FUNCTION vres.protect_experience_lifecycle_immutability();

ALTER TABLE vres.knowledge_items
    DROP CONSTRAINT IF EXISTS knowledge_items_status_check;
ALTER TABLE vres.knowledge_items
    ADD CONSTRAINT knowledge_items_status_check
    CHECK (status IN ('proposed','observed','validated','canonical','challenged','superseded','rejected','retired','revoked'));
