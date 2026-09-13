-- Vres governance/continuity hardening. Additive only.

ALTER TABLE vres.sessions ADD COLUMN IF NOT EXISTS task_id bigint REFERENCES vres.tasks(id) ON DELETE SET NULL;
CREATE INDEX IF NOT EXISTS idx_sessions_project_active ON vres.sessions(project_id, ended_at, started_at DESC);

CREATE TABLE IF NOT EXISTS vres.registry_objects (
    id bigserial PRIMARY KEY,
    object_key text NOT NULL UNIQUE,
    object_type text NOT NULL,
    project_id bigint REFERENCES vres.projects(id) ON DELETE SET NULL,
    name text NOT NULL,
    description text NOT NULL DEFAULT '',
    status text NOT NULL DEFAULT 'active',
    version text,
    owner_role text,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_registry_project_type ON vres.registry_objects(project_id,object_type,status);

CREATE TABLE IF NOT EXISTS vres.capability_proofs (
    id bigserial PRIMARY KEY,
    capability_id bigint NOT NULL REFERENCES vres.capabilities(id) ON DELETE CASCADE,
    task_id bigint NOT NULL REFERENCES vres.tasks(id) ON DELETE CASCADE,
    accepted boolean NOT NULL,
    evidence jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(capability_id,task_id)
);

CREATE TABLE IF NOT EXISTS vres.preference_history (
    id bigserial PRIMARY KEY,
    preference_key text NOT NULL,
    statement text NOT NULL,
    source text,
    confidence numeric(5,4),
    status text NOT NULL,
    changed_at timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE vres.refresh_runs ADD COLUMN IF NOT EXISTS validation jsonb NOT NULL DEFAULT '{}'::jsonb;
ALTER TABLE vres.refresh_runs ADD COLUMN IF NOT EXISTS validated_by text;

ALTER TABLE vres.onboarding_jobs ADD COLUMN IF NOT EXISTS project_id bigint REFERENCES vres.projects(id) ON DELETE SET NULL;
ALTER TABLE vres.review_queue ADD COLUMN IF NOT EXISTS status text NOT NULL DEFAULT 'pending';
ALTER TABLE vres.review_queue ADD COLUMN IF NOT EXISTS resolution text;
ALTER TABLE vres.review_queue ADD COLUMN IF NOT EXISTS resolved_at timestamptz;
ALTER TABLE vres.review_queue ADD COLUMN IF NOT EXISTS resolved_by text;

-- Canonical model authority: preserve old policies but make only the intended bootstrap rows active.
UPDATE vres.model_policies
   SET status='superseded'
 WHERE phase IN ('plan','design','build','validate','summarize')
   AND policy_key NOT IN ('bootstrap.plan','bootstrap.design','bootstrap.build','bootstrap.validate','bootstrap.summarize')
   AND task_family IS NULL;

UPDATE vres.model_policies SET status='active', model='fable', effort='high', priority=100,
 metadata=metadata || '{"protected":true,"bootstrap":"user-preferred"}'::jsonb
 WHERE policy_key='bootstrap.validate';

CREATE TABLE IF NOT EXISTS vres.project_focus (
    project_id bigint PRIMARY KEY REFERENCES vres.projects(id) ON DELETE CASCADE,
    task_id bigint REFERENCES vres.tasks(id) ON DELETE SET NULL,
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS vres.approval_events (
    id bigserial PRIMARY KEY,
    approval_key text NOT NULL UNIQUE,
    project_id bigint REFERENCES vres.projects(id) ON DELETE SET NULL,
    task_id bigint REFERENCES vres.tasks(id) ON DELETE SET NULL,
    source_event_id bigint NOT NULL REFERENCES vres.task_events(id) ON DELETE RESTRICT,
    approval_type text NOT NULL,
    subject_key text,
    statement text NOT NULL,
    user_text text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(source_event_id,approval_type,subject_key)
);
ALTER TABLE vres.knowledge_items ADD COLUMN IF NOT EXISTS approval_event_id bigint REFERENCES vres.approval_events(id) ON DELETE SET NULL;
ALTER TABLE vres.procedure_versions ADD COLUMN IF NOT EXISTS approval_event_id bigint REFERENCES vres.approval_events(id) ON DELETE SET NULL;
