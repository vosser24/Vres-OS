-- First-class project-agent work units for governed fan-out/fan-in.
-- Dependencies are the source of truth for readiness; no separate phase or parallel-group state is stored.

ALTER TABLE vres.worker_runs
    ADD COLUMN IF NOT EXISTS work_unit_key text,
    ADD COLUMN IF NOT EXISTS project_agent_key text;

CREATE TABLE IF NOT EXISTS vres.orchestration_work_units (
    id bigserial PRIMARY KEY,
    work_unit_key text NOT NULL UNIQUE,
    task_id bigint NOT NULL REFERENCES vres.tasks(id) ON DELETE CASCADE,
    plan_key text NOT NULL,
    role text NOT NULL,
    project_agent_key text REFERENCES vres.registry_objects(object_key) ON DELETE RESTRICT,
    execution_tier text NOT NULL CHECK (execution_tier IN ('sonnet','opus')),
    covers jsonb NOT NULL DEFAULT '[]'::jsonb,
    capability_keys jsonb NOT NULL DEFAULT '[]'::jsonb,
    depends_on jsonb NOT NULL DEFAULT '[]'::jsonb,
    write_scope jsonb NOT NULL DEFAULT '[]'::jsonb,
    status text NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending','running','passed','failed')),
    attempt_count integer NOT NULL DEFAULT 0 CHECK (attempt_count >= 0),
    report_key text,
    last_error text,
    started_at timestamptz,
    completed_at timestamptz,
    host_agent_id text,
    observed_model text,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(task_id,plan_key,role)
);
CREATE INDEX IF NOT EXISTS idx_orchestration_work_units_task_plan_status
    ON vres.orchestration_work_units(task_id,plan_key,status);

CREATE OR REPLACE FUNCTION vres.enforce_current_work_graph_completion()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    plan jsonb;
BEGIN
    IF NEW.status <> 'completed' OR OLD.status = 'completed' THEN
        RETURN NEW;
    END IF;

    SELECT e.payload INTO plan
      FROM vres.task_events e
     WHERE e.task_id=NEW.id AND e.event_type='ORCHESTRATION_PLAN'
     ORDER BY e.id DESC LIMIT 1;

    IF plan IS NULL THEN
        RETURN NEW;
    END IF;

    IF EXISTS (
        SELECT 1
          FROM vres.orchestration_work_units w
         WHERE w.task_id=NEW.id
           AND w.plan_key=plan->>'plan_key'
           AND w.status <> 'passed'
    ) THEN
        RAISE EXCEPTION 'Task completion requires every current orchestration work unit to pass';
    END IF;

    IF EXISTS (
        SELECT 1
          FROM jsonb_array_elements(COALESCE(plan->'selected_experts','[]'::jsonb)) expert
         WHERE NULLIF(expert->>'agent_key','') IS NOT NULL
           AND NOT EXISTS (
               SELECT 1
                 FROM vres.worker_runs wr
                WHERE wr.task_id=NEW.id
                  AND wr.plan_key=plan->>'plan_key'
                  AND wr.role=expert->>'role'
                  AND wr.project_agent_key=expert->>'agent_key'
                  AND wr.status='observed'
           )
    ) THEN
        RAISE EXCEPTION 'Task completion requires host-observed execution of every routed project agent';
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_enforce_current_work_graph_completion ON vres.tasks;
CREATE TRIGGER trg_enforce_current_work_graph_completion
BEFORE UPDATE OF status ON vres.tasks
FOR EACH ROW EXECUTE FUNCTION vres.enforce_current_work_graph_completion();
