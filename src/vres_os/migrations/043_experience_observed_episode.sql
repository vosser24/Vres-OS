-- #176 E7 authority closure: E1 v2 external-observation representation.
-- Additive: no new table, no backfill. A true observed external episode has no task.

DO $vres$
BEGIN
    IF EXISTS (
        SELECT 1
          FROM vres.experience_episodes
         WHERE participation_class = 'observed'
           AND NOT (
                project_id IS NOT NULL
            AND task_id IS NULL
            AND work_unit_key IS NULL
            AND report_key IS NULL
            AND trust_class = 'external_untrusted_observation'
            AND policy_version = '176.e1.v2'
            AND outcome_status IN ('completed','failed')
           )
    ) THEN
        RAISE EXCEPTION 'Unexpected pre-existing observed experience episode does not conform to E1 v2';
    END IF;
END
$vres$;

INSERT INTO vres.experience_policy_versions(policy_version,schema_version,policy_digest,policy)
VALUES (
    '176.e1.v2',
    2,
    '66e11e1319dd85b6d01fc74e4ad3f2fa4a7ee9857ab5d72fe5016e781b88efa0',
    '{"authority":"no_promotion","capture":"external_source_observation_only","participation":"observed_only","payload":"bounded_sanitized_no_private_reasoning","policy_version":"176.e1.v2","provenance":"active_project_source_required","relations":"existing_relations_and_relation_evidence","schema_version":2,"trust":"external_untrusted_observation_only"}'::jsonb
)
ON CONFLICT(policy_version) DO NOTHING;

DO $vres$
BEGIN
    IF NOT EXISTS (
        SELECT 1
          FROM vres.experience_policy_versions
         WHERE policy_version='176.e1.v2'
           AND schema_version=2
           AND policy_digest='66e11e1319dd85b6d01fc74e4ad3f2fa4a7ee9857ab5d72fe5016e781b88efa0'
           AND policy='{"authority":"no_promotion","capture":"external_source_observation_only","participation":"observed_only","payload":"bounded_sanitized_no_private_reasoning","policy_version":"176.e1.v2","provenance":"active_project_source_required","relations":"existing_relations_and_relation_evidence","schema_version":2,"trust":"external_untrusted_observation_only"}'::jsonb
    ) THEN
        RAISE EXCEPTION 'Experience E1 v2 policy version/digest mismatch';
    END IF;
END
$vres$;

ALTER TABLE vres.experience_episodes ALTER COLUMN task_id DROP NOT NULL;

ALTER TABLE vres.experience_episodes
    DROP CONSTRAINT IF EXISTS ck_experience_episode_participation_provenance;
ALTER TABLE vres.experience_episodes
    ADD CONSTRAINT ck_experience_episode_participation_provenance CHECK (
        (
            participation_class = 'participated'
            AND task_id IS NOT NULL
            AND policy_version <> '176.e1.v2'
        )
        OR (
            participation_class = 'observed'
            AND project_id IS NOT NULL
            AND task_id IS NULL
            AND work_unit_key IS NULL
            AND report_key IS NULL
            AND trust_class = 'external_untrusted_observation'
            AND policy_version = '176.e1.v2'
            AND outcome_status IN ('completed','failed')
        )
    );
