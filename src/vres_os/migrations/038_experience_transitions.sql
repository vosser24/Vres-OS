-- #176 E2: append-only audit of verified experience -> knowledge transitions.
-- Not a memory store: lessons live only in vres.knowledge_items; evidence links only in vres.relations.

INSERT INTO vres.experience_policy_versions(policy_version,schema_version,policy_digest,policy)
VALUES (
    '176.e2.v1',
    1,
    '619b101c46ea19a7e32396f6cab8b5d503671790af1310f7a1379e3d5535a6f8',
    '{"authority":"no_promotion","conflicts":"preserved_related_to_no_merge","consolidation":"proposed_project_local_lesson_only","max_open_proposed":20,"policy_version":"176.e2.v1","recurrence_calibration":"required_before_acceptance","recurrence_min_tasks":null,"schema_version":1,"triggers":["failure_gotcha","validated_novel","recurrence"],"verifier":"deterministic_literal_support_fail_closed"}'::jsonb
)
ON CONFLICT(policy_version) DO NOTHING;

DO $vres$
BEGIN
    IF NOT EXISTS (
        SELECT 1
          FROM vres.experience_policy_versions
         WHERE policy_version='176.e2.v1'
           AND schema_version=1
           AND policy_digest='619b101c46ea19a7e32396f6cab8b5d503671790af1310f7a1379e3d5535a6f8'
    ) THEN
        RAISE EXCEPTION 'Experience E2 policy version/digest mismatch';
    END IF;
END
$vres$;

CREATE TABLE IF NOT EXISTS vres.experience_transitions (
    id bigserial PRIMARY KEY,
    transition_key text NOT NULL UNIQUE,
    project_id bigint NOT NULL REFERENCES vres.projects(id) ON DELETE RESTRICT,
    policy_version text NOT NULL REFERENCES vres.experience_policy_versions(policy_version) ON DELETE RESTRICT,
    policy_digest text NOT NULL CHECK (policy_digest ~ '^[0-9a-f]{64}$'),
    kind text NOT NULL CHECK (kind = 'lesson'),
    polarity text NOT NULL CHECK (polarity IN ('positive','negative')),
    trigger text NOT NULL CHECK (trigger IN ('failure_gotcha','validated_novel','recurrence')),
    subject_key text NOT NULL,
    verdict text NOT NULL CHECK (verdict IN ('accepted','deduplicated','quarantined')),
    reason_codes jsonb NOT NULL CHECK (jsonb_typeof(reason_codes) = 'array'),
    candidate jsonb NOT NULL CHECK (jsonb_typeof(candidate) = 'object'),
    candidate_digest text NOT NULL CHECK (candidate_digest ~ '^[0-9a-f]{64}$'),
    before_digest text NOT NULL CHECK (before_digest ~ '^[0-9a-f]{64}$'),
    after_digest text NOT NULL CHECK (after_digest ~ '^[0-9a-f]{64}$'),
    source_episodes jsonb NOT NULL CHECK (jsonb_typeof(source_episodes) = 'array'),
    knowledge_key text,
    conflicts jsonb NOT NULL CHECK (jsonb_typeof(conflicts) = 'array'),
    checks jsonb NOT NULL CHECK (jsonb_typeof(checks) = 'object'),
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_experience_transition_candidate UNIQUE (project_id, candidate_digest),
    CONSTRAINT ck_experience_transition_knowledge CHECK (
        (verdict = 'quarantined' AND knowledge_key IS NULL)
        OR (verdict <> 'quarantined' AND knowledge_key IS NOT NULL)
    )
);

CREATE INDEX IF NOT EXISTS idx_experience_transitions_project
    ON vres.experience_transitions(project_id,id DESC);

CREATE OR REPLACE FUNCTION vres.protect_experience_transition_immutability()
RETURNS trigger
LANGUAGE plpgsql
AS $vres_transition$
BEGIN
    IF TG_OP = 'DELETE'
       AND current_setting('vres.allow_experience_ledger_delete', true) = 'on' THEN
        RETURN OLD;
    END IF;
    RAISE EXCEPTION 'experience_transitions are immutable; append a new transition instead of modifying history';
END
$vres_transition$;

DROP TRIGGER IF EXISTS trg_protect_experience_transition_update ON vres.experience_transitions;
CREATE TRIGGER trg_protect_experience_transition_update
BEFORE UPDATE ON vres.experience_transitions
FOR EACH ROW EXECUTE FUNCTION vres.protect_experience_transition_immutability();

DROP TRIGGER IF EXISTS trg_protect_experience_transition_delete ON vres.experience_transitions;
CREATE TRIGGER trg_protect_experience_transition_delete
BEFORE DELETE ON vres.experience_transitions
FOR EACH ROW EXECUTE FUNCTION vres.protect_experience_transition_immutability();
