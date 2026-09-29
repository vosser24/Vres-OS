-- #176 E1: immutable bounded episodic experience ledger.
-- Reuses existing tasks/decisions/procedures/capabilities/validation/relations as truth owners.

CREATE TABLE IF NOT EXISTS vres.experience_policy_versions (
    policy_version text PRIMARY KEY,
    schema_version integer NOT NULL CHECK (schema_version > 0),
    policy_digest text NOT NULL CHECK (policy_digest ~ '^[0-9a-f]{64}$'),
    policy jsonb NOT NULL CHECK (jsonb_typeof(policy) = 'object'),
    created_at timestamptz NOT NULL DEFAULT now()
);

INSERT INTO vres.experience_policy_versions(policy_version,schema_version,policy_digest,policy)
VALUES (
    '176.e1.v1',
    1,
    '49e5d6eb17940baf5e1d9c239f9355dd8a65bab60e62e30c81787334ddda519a',
    '{"authority":"no_promotion","capture":"mechanically_known_terminal_task_or_work_unit_only","payload":"bounded_sanitized_no_private_reasoning","policy_version":"176.e1.v1","relations":"existing_relations_and_relation_evidence","schema_version":1}'::jsonb
)
ON CONFLICT(policy_version) DO NOTHING;

DO $
BEGIN
    IF NOT EXISTS (
        SELECT 1
          FROM vres.experience_policy_versions
         WHERE policy_version='176.e1.v1'
           AND schema_version=1
           AND policy_digest='49e5d6eb17940baf5e1d9c239f9355dd8a65bab60e62e30c81787334ddda519a'
    ) THEN
        RAISE EXCEPTION 'Experience E1 policy version/digest mismatch';
    END IF;
END $;

CREATE TABLE IF NOT EXISTS vres.experience_episodes (
    id bigserial PRIMARY KEY,
    episode_key text NOT NULL UNIQUE,
    project_id bigint REFERENCES vres.projects(id) ON DELETE RESTRICT,
    task_id bigint NOT NULL REFERENCES vres.tasks(id) ON DELETE RESTRICT,
    work_unit_key text,
    report_key text,
    task_family text,
    policy_version text NOT NULL REFERENCES vres.experience_policy_versions(policy_version) ON DELETE RESTRICT,
    participation_class text NOT NULL CHECK (participation_class IN ('participated','observed')),
    trust_class text NOT NULL CHECK (
        trust_class IN (
            'user_authoritative',
            'validated_runtime',
            'trusted_project_source',
            'model_inferred_from_validated_evidence',
            'external_untrusted_observation'
        )
    ),
    outcome_status text NOT NULL CHECK (outcome_status IN ('completed','cancelled','passed','failed')),
    payload jsonb NOT NULL CHECK (jsonb_typeof(payload) = 'object'),
    source_digest text NOT NULL CHECK (source_digest ~ '^[0-9a-f]{64}$'),
    payload_digest text NOT NULL CHECK (payload_digest ~ '^[0-9a-f]{64}$'),
    security_disposition text NOT NULL CHECK (security_disposition IN ('sanitized','sensitive_sanitized')),
    observed_at timestamptz NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_experience_episode_task
    ON vres.experience_episodes(task_id)
    WHERE work_unit_key IS NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_experience_episode_work_unit
    ON vres.experience_episodes(task_id,work_unit_key)
    WHERE work_unit_key IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_experience_episode_project_observed
    ON vres.experience_episodes(project_id,observed_at DESC,id DESC);

CREATE OR REPLACE FUNCTION vres.protect_experience_episode_immutability()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF current_setting('vres.allow_experience_ledger_delete', true) = 'on' THEN
        IF TG_OP = 'DELETE' THEN
            RETURN OLD;
        END IF;
        RETURN NEW;
    END IF;
    RAISE EXCEPTION 'experience_episodes are immutable; append new evidence instead of modifying history';
END
$$;

DROP TRIGGER IF EXISTS trg_protect_experience_episode_update ON vres.experience_episodes;
CREATE TRIGGER trg_protect_experience_episode_update
BEFORE UPDATE ON vres.experience_episodes
FOR EACH ROW EXECUTE FUNCTION vres.protect_experience_episode_immutability();

DROP TRIGGER IF EXISTS trg_protect_experience_episode_delete ON vres.experience_episodes;
CREATE TRIGGER trg_protect_experience_episode_delete
BEFORE DELETE ON vres.experience_episodes
FOR EACH ROW EXECUTE FUNCTION vres.protect_experience_episode_immutability();
