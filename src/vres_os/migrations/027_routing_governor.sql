-- Fable routing governor and observed worker-model evidence.
-- Routing authority is separate from user authority and from protected validation.
-- Legacy/unrouted tasks remain protected-validation-only at completion.

CREATE TABLE IF NOT EXISTS vres.routing_requests (
    id bigserial PRIMARY KEY,
    request_key text NOT NULL UNIQUE,
    task_id bigint NOT NULL REFERENCES vres.tasks(id) ON DELETE CASCADE,
    discovery_key text NOT NULL,
    state_digest text NOT NULL,
    risk_triggers jsonb NOT NULL DEFAULT '[]'::jsonb,
    hard_protected boolean NOT NULL DEFAULT false,
    status text NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending','routed','blocked','rejected')),
    observed_model text,
    agent_id text,
    session_id text,
    decision jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    completed_at timestamptz
);
CREATE INDEX IF NOT EXISTS idx_routing_requests_task_created
    ON vres.routing_requests(task_id,created_at DESC,id DESC);

CREATE TABLE IF NOT EXISTS vres.worker_runs (
    id bigserial PRIMARY KEY,
    task_id bigint NOT NULL REFERENCES vres.tasks(id) ON DELETE CASCADE,
    plan_key text NOT NULL,
    role text NOT NULL,
    execution_tier text NOT NULL CHECK (execution_tier IN ('sonnet','opus')),
    agent_type text NOT NULL,
    agent_id text NOT NULL,
    session_id text,
    observed_model text NOT NULL,
    status text NOT NULL DEFAULT 'observed' CHECK (status IN ('observed','rejected')),
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(agent_id,plan_key,role)
);
CREATE INDEX IF NOT EXISTS idx_worker_runs_task_plan
    ON vres.worker_runs(task_id,plan_key,role,execution_tier,status);

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
    ELSE
        IF validation IS DISTINCT FROM 'not_required' THEN
            RAISE EXCEPTION 'Routine Sonnet route must use not_required validation status';
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_enforce_routed_task_completion ON vres.tasks;
CREATE TRIGGER trg_enforce_routed_task_completion
BEFORE UPDATE OF status ON vres.tasks
FOR EACH ROW
EXECUTE FUNCTION vres.enforce_routed_task_completion();
