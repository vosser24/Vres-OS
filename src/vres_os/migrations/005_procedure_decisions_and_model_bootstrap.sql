-- Optimization trade-offs can be decided explicitly by the user while preserving history.
ALTER TABLE vres.optimization_candidates
    DROP CONSTRAINT IF EXISTS optimization_candidates_decision_check;
ALTER TABLE vres.optimization_candidates
    ADD CONSTRAINT optimization_candidates_decision_check
    CHECK (decision IN ('pending','auto_promoted','rejected','requires_user','user_promoted','user_rejected'));

-- Bootstrap model choices reflect the user's initial proven preference. They are priors only;
-- Vres model telemetry may later select a Pareto-superior policy.
UPDATE vres.model_policies
   SET model='fable', effort='high', metadata=metadata || '{"bootstrap":"user-preferred"}'::jsonb
 WHERE phase IN ('plan','design') AND task_family IS NULL AND provider='claude';
UPDATE vres.model_policies
   SET model='opus', effort='high', metadata=metadata || '{"bootstrap":"user-preferred"}'::jsonb
 WHERE phase='build' AND task_family IS NULL AND provider='claude';
UPDATE vres.model_policies
   SET model='fable', effort='high', metadata=metadata || '{"bootstrap":"user-preferred"}'::jsonb
 WHERE phase='validate' AND task_family IS NULL AND provider='claude';

-- Ensure required global bootstrap rows exist even for databases created by early release candidates.
INSERT INTO vres.model_policies(policy_key,task_family,phase,provider,model,effort,status,priority,metadata)
VALUES
 ('bootstrap.plan',NULL,'plan','claude','fable','high','active',100,'{"bootstrap":"user-preferred"}'::jsonb),
 ('bootstrap.design',NULL,'design','claude','fable','high','active',100,'{"bootstrap":"user-preferred"}'::jsonb),
 ('bootstrap.build',NULL,'build','claude','opus','high','active',100,'{"bootstrap":"user-preferred"}'::jsonb),
 ('bootstrap.validate',NULL,'validate','claude','fable','high','active',100,'{"bootstrap":"user-preferred"}'::jsonb),
 ('bootstrap.summarize',NULL,'summarize','claude','haiku','low','active',100,'{"bootstrap":"efficient"}'::jsonb)
ON CONFLICT(policy_key) DO UPDATE SET
 provider=excluded.provider,model=excluded.model,effort=excluded.effort,status='active',metadata=excluded.metadata;
