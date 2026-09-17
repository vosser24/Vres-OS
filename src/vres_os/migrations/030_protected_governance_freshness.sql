-- Freeze material routing/orchestration evidence while protected review is pending or passed.
-- A genuine post-review change must first use the explicit validation invalidation path.
-- Defense in depth at completion also proves the latest PASS post-dates final governed evidence.

CREATE OR REPLACE FUNCTION vres.assert_governance_mutation_allowed(
    p_task_id bigint,
    p_kind text
)
RETURNS void
LANGUAGE plpgsql
AS $$
DECLARE
    validation text;
BEGIN
    SELECT validation_status INTO validation
      FROM vres.task_state
     WHERE task_id=p_task_id;

    IF validation = 'passed' THEN
        RAISE EXCEPTION
            'Fresh passed validation is protected; call validation_invalidate before material governance change (%)',
            p_kind;
    END IF;

    IF EXISTS (
        SELECT 1
          FROM vres.validation_requests
         WHERE task_id=p_task_id AND status='pending'
    ) THEN
        RAISE EXCEPTION
            'Material governance is frozen while protected validation is pending (%)',
            p_kind;
    END IF;
END;
$$;

CREATE OR REPLACE FUNCTION vres.guard_material_task_event()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.event_type IN (
        'ORCHESTRATION_DISCOVERY',
        'ORCHESTRATION_CAPABILITY_ACQUIRED',
        'ORCHESTRATION_PLAN',
        'ORCHESTRATION_EXPERT_REPORT',
        'ORCHESTRATION_ARBITRATION',
        'ORCHESTRATION_FINAL',
        'ROUTING_DECISION'
    ) THEN
        PERFORM vres.assert_governance_mutation_allowed(NEW.task_id, NEW.event_type);
    END IF;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_guard_material_task_event ON vres.task_events;
CREATE TRIGGER trg_guard_material_task_event
BEFORE INSERT ON vres.task_events
FOR EACH ROW
EXECUTE FUNCTION vres.guard_material_task_event();

CREATE OR REPLACE FUNCTION vres.guard_worker_run_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    PERFORM vres.assert_governance_mutation_allowed(NEW.task_id, 'WORKER_RUN');
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_guard_worker_run_mutation ON vres.worker_runs;
CREATE TRIGGER trg_guard_worker_run_mutation
BEFORE INSERT ON vres.worker_runs
FOR EACH ROW
EXECUTE FUNCTION vres.guard_worker_run_mutation();

CREATE OR REPLACE FUNCTION vres.guard_routing_request_insert()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    PERFORM vres.assert_governance_mutation_allowed(NEW.task_id, 'ROUTING_REQUEST');
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_guard_routing_request_insert ON vres.routing_requests;
CREATE TRIGGER trg_guard_routing_request_insert
BEFORE INSERT ON vres.routing_requests
FOR EACH ROW
EXECUTE FUNCTION vres.guard_routing_request_insert();

CREATE OR REPLACE FUNCTION vres.guard_routing_request_decision()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    -- Rejection is hygiene for a stale pending request and cannot become a completion route.
    -- Routed/blocked decisions and any decision rewrite are material governance mutations.
    IF NEW.status IN ('routed','blocked')
       AND (
           NEW.status IS DISTINCT FROM OLD.status
           OR NEW.decision IS DISTINCT FROM OLD.decision
           OR NEW.observed_model IS DISTINCT FROM OLD.observed_model
           OR NEW.agent_id IS DISTINCT FROM OLD.agent_id
       ) THEN
        PERFORM vres.assert_governance_mutation_allowed(NEW.task_id, 'ROUTING_DECISION');
    END IF;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_guard_routing_request_decision ON vres.routing_requests;
CREATE TRIGGER trg_guard_routing_request_decision
BEFORE UPDATE ON vres.routing_requests
FOR EACH ROW
EXECUTE FUNCTION vres.guard_routing_request_decision();

CREATE OR REPLACE FUNCTION vres.enforce_routed_task_completion()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    validation text;
    route record;
    plan jsonb;
    final jsonb;
    plan_roles text[];
    route_roles text[];
    expert jsonb;
    latest_passed_at timestamptz;
    latest_material_at timestamptz;
BEGIN
    IF NEW.status <> 'completed' OR OLD.status = 'completed' THEN
        RETURN NEW;
    END IF;

    SELECT validation_status INTO validation
      FROM vres.task_state
     WHERE task_id=NEW.id;

    SELECT r.* INTO route
      FROM vres.routing_requests r
     WHERE r.task_id=NEW.id AND r.status='routed'
     ORDER BY r.id DESC
     LIMIT 1;

    -- Existing tasks that did not use routed expertise retain the original
    -- protected-validation completion contract.
    IF route.id IS NULL THEN
        IF validation IS DISTINCT FROM 'passed' THEN
            RAISE EXCEPTION 'Unrouted task completion requires protected validation';
        END IF;
        RETURN NEW;
    END IF;

    SELECT e.payload INTO plan
      FROM vres.task_events e
     WHERE e.task_id=NEW.id AND e.event_type='ORCHESTRATION_PLAN'
     ORDER BY e.id DESC LIMIT 1;
    SELECT e.payload INTO final
      FROM vres.task_events e
     WHERE e.task_id=NEW.id AND e.event_type='ORCHESTRATION_FINAL'
     ORDER BY e.id DESC LIMIT 1;

    IF plan IS NULL OR final IS NULL THEN
        RAISE EXCEPTION 'Routed task completion requires orchestration plan and final evidence';
    END IF;
    IF final->>'plan_key' IS DISTINCT FROM plan->>'plan_key'
       OR COALESCE((final->>'decision_ready')::boolean,false) IS NOT TRUE THEN
        RAISE EXCEPTION 'Routed task completion requires a decision-ready final for the active plan';
    END IF;
    IF plan->>'discovery_key' IS DISTINCT FROM route.discovery_key THEN
        RAISE EXCEPTION 'Orchestration plan does not match the governed discovery';
    END IF;
    IF plan->>'lead_role' IS DISTINCT FROM route.decision->>'lead_role' THEN
        RAISE EXCEPTION 'Orchestration lead does not match the Fable routing decision';
    END IF;

    SELECT COALESCE(array_agg(x->>'role' ORDER BY x->>'role'),ARRAY[]::text[])
      INTO plan_roles
      FROM jsonb_array_elements(COALESCE(plan->'selected_experts','[]'::jsonb)) x;
    SELECT COALESCE(array_agg(x->>'role' ORDER BY x->>'role'),ARRAY[]::text[])
      INTO route_roles
      FROM jsonb_array_elements(COALESCE(route.decision->'experts','[]'::jsonb)) x;
    IF plan_roles IS DISTINCT FROM route_roles THEN
        RAISE EXCEPTION 'Orchestration team does not match the Fable routing decision';
    END IF;

    FOR expert IN
        SELECT value FROM jsonb_array_elements(COALESCE(route.decision->'experts','[]'::jsonb))
    LOOP
        IF NOT EXISTS (
            SELECT 1 FROM vres.worker_runs w
             WHERE w.task_id=NEW.id
               AND w.plan_key=plan->>'plan_key'
               AND w.role=expert->>'role'
               AND w.execution_tier=expert->>'execution_tier'
               AND w.status='observed'
        ) THEN
            RAISE EXCEPTION 'Missing host-observed worker model evidence for role %', expert->>'role';
        END IF;
    END LOOP;

    IF route.hard_protected
       OR route.decision->>'assurance' = 'protected'
       OR EXISTS (
           SELECT 1
             FROM jsonb_array_elements(COALESCE(route.decision->'experts','[]'::jsonb)) x
            WHERE x->>'execution_tier'='opus'
       ) THEN
        IF validation IS DISTINCT FROM 'passed' THEN
            RAISE EXCEPTION 'Protected routed task requires fresh protected validation';
        END IF;

        SELECT max(completed_at) INTO latest_passed_at
          FROM vres.validation_requests
         WHERE task_id=NEW.id AND status='passed';

        SELECT max(ts) INTO latest_material_at
          FROM (
              SELECT max(created_at) AS ts
                FROM vres.task_events
               WHERE task_id=NEW.id
                 AND event_type IN (
                     'ORCHESTRATION_DISCOVERY',
                     'ORCHESTRATION_CAPABILITY_ACQUIRED',
                     'ORCHESTRATION_PLAN',
                     'ORCHESTRATION_EXPERT_REPORT',
                     'ORCHESTRATION_ARBITRATION',
                     'ORCHESTRATION_FINAL',
                     'ROUTING_DECISION'
                 )
              UNION ALL
              SELECT max(COALESCE(completed_at,created_at)) AS ts
                FROM vres.routing_requests
               WHERE task_id=NEW.id AND status IN ('routed','blocked')
              UNION ALL
              SELECT max(created_at) AS ts
                FROM vres.worker_runs
               WHERE task_id=NEW.id AND status='observed'
          ) material;

        IF latest_passed_at IS NULL
           OR (latest_material_at IS NOT NULL AND latest_passed_at < latest_material_at) THEN
            RAISE EXCEPTION 'Protected validation is stale relative to final governed orchestration; invalidate and revalidate';
        END IF;
    ELSE
        IF validation IS DISTINCT FROM 'not_required' THEN
            RAISE EXCEPTION 'Routine Sonnet route must use governed not_required validation status';
        END IF;
    END IF;

    RETURN NEW;
END;
$$;
