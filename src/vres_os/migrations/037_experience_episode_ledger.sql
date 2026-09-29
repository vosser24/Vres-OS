-- #176 E1: immutable, provenance-rich episodic experience ledger.
-- Existing tasks/decisions/knowledge/procedures/capabilities/relations/evidence remain authoritative.

CREATE TABLE IF NOT EXISTS vres.experience_episodes (
    id bigserial PRIMARY KEY,
    episode_key text NOT NULL UNIQUE,
    schema_version integer NOT NULL CHECK (schema_version = 1),
    policy_version text NOT NULL,
    project_id bigint NOT NULL REFERENCES vres.projects(id) ON DELETE RESTRICT,
    task_id bigint NOT NULL REFERENCES vres.tasks(id) ON DELETE RESTRICT,
    origin_kind text NOT NULL CHECK (origin_kind IN ('task','work_unit')),
    work_unit_key text,
    work_unit_attempt integer,
    report_key text,
    participation_mode text NOT NULL CHECK (participation_mode IN ('participated','observed')),
    task_family text,
    domain_keys jsonb NOT NULL DEFAULT '[]'::jsonb,
    capability_keys jsonb NOT NULL DEFAULT '[]'::jsonb,
    objective_summary text NOT NULL,
    context_summary text NOT NULL DEFAULT '',
    constraints jsonb NOT NULL DEFAULT '[]'::jsonb,
    outcome_summary text NOT NULL DEFAULT '',
    outcome_status text NOT NULL CHECK (outcome_status IN ('completed','passed','failed')),
    outcome_classification text NOT NULL CHECK (outcome_classification IN ('success','failure')),
    gotcha_signals jsonb NOT NULL DEFAULT '[]'::jsonb,
    procedure_keys jsonb NOT NULL DEFAULT '[]'::jsonb,
    decision_keys jsonb NOT NULL DEFAULT '[]'::jsonb,
    validation_request_key text,
    source_refs jsonb NOT NULL DEFAULT '[]'::jsonb,
    trust_class text NOT NULL CHECK (
        trust_class IN (
            'user_authoritative',
            'validated_runtime',
            'trusted_project_source',
            'model_inferred_from_validated_evidence',
            'external_untrusted_observation'
        )
    ),
    observed_at timestamptz NOT NULL,
    applicability_tags jsonb NOT NULL DEFAULT '[]'::jsonb,
    source_digest text NOT NULL CHECK (source_digest ~ '^[0-9a-f]{64}$'),
    payload_digest text NOT NULL CHECK (payload_digest ~ '^[0-9a-f]{64}$'),
    security_disposition text NOT NULL CHECK (
        security_disposition IN (
            'clean_data_only',
            'sensitive_sanitized_data_only',
            'flagged_data_only',
            'sensitive_sanitized_flagged_data_only'
        )
    ),
    security_flags jsonb NOT NULL DEFAULT '[]'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT experience_episode_json_contract CHECK (
        jsonb_typeof(domain_keys)='array'
        AND jsonb_typeof(capability_keys)='array'
        AND jsonb_typeof(constraints)='array'
        AND jsonb_typeof(gotcha_signals)='array'
        AND jsonb_typeof(procedure_keys)='array'
        AND jsonb_typeof(decision_keys)='array'
        AND jsonb_typeof(source_refs)='array'
        AND jsonb_typeof(applicability_tags)='array'
        AND jsonb_typeof(security_flags)='array'
    ),
    CONSTRAINT experience_episode_origin_contract CHECK (
        (
            origin_kind='task'
            AND work_unit_key IS NULL
            AND work_unit_attempt IS NULL
            AND report_key IS NULL
            AND outcome_status='completed'
            AND outcome_classification='success'
        )
        OR
        (
            origin_kind='work_unit'
            AND work_unit_key IS NOT NULL
            AND btrim(work_unit_key) <> ''
            AND work_unit_attempt IS NOT NULL
            AND work_unit_attempt > 0
            AND outcome_status IN ('passed','failed')
            AND (
                (outcome_status='passed' AND outcome_classification='success')
                OR (outcome_status='failed' AND outcome_classification='failure')
            )
        )
    )
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_experience_episode_task_origin
    ON vres.experience_episodes(task_id)
    WHERE origin_kind='task';

CREATE UNIQUE INDEX IF NOT EXISTS idx_experience_episode_work_unit_origin
    ON vres.experience_episodes(task_id,work_unit_key,work_unit_attempt)
    WHERE origin_kind='work_unit';

CREATE INDEX IF NOT EXISTS idx_experience_episode_project_observed
    ON vres.experience_episodes(project_id,observed_at DESC,id DESC);

CREATE INDEX IF NOT EXISTS idx_experience_episode_task_observed
    ON vres.experience_episodes(task_id,observed_at DESC,id DESC);

CREATE OR REPLACE FUNCTION vres.validate_experience_episode_insert()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    t record;
    w record;
    v record;
BEGIN
    SELECT id,project_id,status,completed_at
      INTO t
      FROM vres.tasks
     WHERE id=NEW.task_id;

    IF t.id IS NULL OR t.project_id IS DISTINCT FROM NEW.project_id THEN
        RAISE EXCEPTION 'experience episode task/project scope mismatch';
    END IF;

    IF NEW.origin_kind='task' THEN
        IF t.status IS DISTINCT FROM 'completed' OR t.completed_at IS NULL THEN
            RAISE EXCEPTION 'task experience requires a completed task';
        END IF;
        IF NEW.observed_at IS DISTINCT FROM t.completed_at THEN
            RAISE EXCEPTION 'task experience observed_at must equal the durable completion time';
        END IF;
    ELSE
        SELECT task_id,status,attempt_count,report_key,completed_at
          INTO w
          FROM vres.orchestration_work_units
         WHERE work_unit_key=NEW.work_unit_key;

        IF w.task_id IS NULL OR w.task_id IS DISTINCT FROM NEW.task_id THEN
            RAISE EXCEPTION 'work-unit experience scope mismatch';
        END IF;
        IF w.status NOT IN ('passed','failed') OR w.status IS DISTINCT FROM NEW.outcome_status THEN
            RAISE EXCEPTION 'work-unit experience requires the current terminal outcome';
        END IF;
        IF w.attempt_count IS DISTINCT FROM NEW.work_unit_attempt THEN
            RAISE EXCEPTION 'work-unit experience attempt does not match durable attempt_count';
        END IF;
        IF w.report_key IS DISTINCT FROM NEW.report_key THEN
            RAISE EXCEPTION 'work-unit experience report provenance mismatch';
        END IF;
        IF w.completed_at IS NULL OR NEW.observed_at IS DISTINCT FROM w.completed_at THEN
            RAISE EXCEPTION 'work-unit experience observed_at must equal the durable terminal time';
        END IF;
    END IF;

    IF NEW.validation_request_key IS NOT NULL THEN
        SELECT task_id,status
          INTO v
          FROM vres.validation_requests
         WHERE request_key=NEW.validation_request_key;
        IF v.task_id IS NULL
           OR v.task_id IS DISTINCT FROM NEW.task_id
           OR v.status IS DISTINCT FROM 'passed' THEN
            RAISE EXCEPTION 'experience validation reference must be a passed request for the same task';
        END IF;
    END IF;

    RETURN NEW;
END
$$;

DROP TRIGGER IF EXISTS trg_validate_experience_episode_insert ON vres.experience_episodes;
CREATE TRIGGER trg_validate_experience_episode_insert
BEFORE INSERT ON vres.experience_episodes
FOR EACH ROW
EXECUTE FUNCTION vres.validate_experience_episode_insert();

CREATE OR REPLACE FUNCTION vres.protect_experience_episode_history()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF current_setting('vres.allow_experience_ledger_delete', true) = 'on' THEN
        IF TG_OP='DELETE' THEN
            RETURN OLD;
        END IF;
        RETURN NEW;
    END IF;
    RAISE EXCEPTION 'experience episode history is immutable';
END
$$;

DROP TRIGGER IF EXISTS trg_protect_experience_episode_update ON vres.experience_episodes;
CREATE TRIGGER trg_protect_experience_episode_update
BEFORE UPDATE ON vres.experience_episodes
FOR EACH ROW
EXECUTE FUNCTION vres.protect_experience_episode_history();

DROP TRIGGER IF EXISTS trg_protect_experience_episode_delete ON vres.experience_episodes;
CREATE TRIGGER trg_protect_experience_episode_delete
BEFORE DELETE ON vres.experience_episodes
FOR EACH ROW
EXECUTE FUNCTION vres.protect_experience_episode_history();
