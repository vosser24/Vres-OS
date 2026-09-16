-- Close the remaining direct-INSERT provenance gap discovered by physical acceptance.
-- Migration 020 backfilled legacy strings before this trigger exists; future callers may
-- create only active Chairman- or event-backed decisions with mechanically coherent origin.

CREATE OR REPLACE FUNCTION vres.validate_task_decision_insert()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    event_row record;
    prior_row record;
    task_row record;
    session_row record;
BEGIN
    IF NEW.status <> 'active'
       OR NEW.superseded_at IS NOT NULL
       OR NEW.retired_at IS NOT NULL
       OR NEW.retirement_reason IS NOT NULL THEN
        RAISE EXCEPTION 'new task decisions must begin active without terminal lifecycle fields';
    END IF;

    SELECT id,project_id,status
      INTO task_row
      FROM vres.tasks
     WHERE id=NEW.task_id;
    IF NOT FOUND OR task_row.status NOT IN ('active','waiting_user','blocked') THEN
        RAISE EXCEPTION 'new task decisions require an unfinished task';
    END IF;

    IF NEW.source_kind = 'legacy_unstructured' THEN
        RAISE EXCEPTION 'legacy_unstructured decisions may only originate from migration 020';
    ELSIF NEW.source_kind = 'user_instruction' THEN
        IF NEW.source_event_id IS NULL THEN
            RAISE EXCEPTION 'user_instruction decision requires source_event_id';
        END IF;
        SELECT id,task_id,event_type,actor,session_id,created_at
          INTO event_row
          FROM vres.task_events
         WHERE id=NEW.source_event_id;
        IF NOT FOUND
           OR event_row.task_id IS DISTINCT FROM NEW.task_id
           OR event_row.event_type <> 'USER_INSTRUCTION'
           OR event_row.actor <> 'user' THEN
            RAISE EXCEPTION 'user_instruction decision must reference a USER_INSTRUCTION event on the same task';
        END IF;
        IF NEW.source_session_id IS DISTINCT FROM event_row.session_id
           OR NEW.decided_at IS DISTINCT FROM event_row.created_at THEN
            RAISE EXCEPTION 'user_instruction decision source session/time must match its source event';
        END IF;
    ELSIF NEW.source_kind = 'chairman' THEN
        IF NEW.source_event_id IS NOT NULL
           OR NEW.source_session_id IS NULL
           OR btrim(NEW.source_session_id) = ''
           OR NEW.decided_at IS NULL THEN
            RAISE EXCEPTION 'chairman decision requires session/time and no source event';
        END IF;
        SELECT id,task_id
          INTO session_row
          FROM vres.sessions
         WHERE provider='claude'
           AND provider_session_id=NEW.source_session_id
           AND project_id=task_row.project_id
           AND ended_at IS NULL
         ORDER BY started_at DESC
         LIMIT 1;
        IF NOT FOUND OR session_row.task_id IS DISTINCT FROM NEW.task_id THEN
            RAISE EXCEPTION 'chairman decision source session must be open and bound to the task';
        END IF;
    ELSE
        RAISE EXCEPTION 'unsupported task decision source kind';
    END IF;

    IF NEW.supersedes_decision_id IS NOT NULL THEN
        SELECT id,task_id,status
          INTO prior_row
          FROM vres.task_decisions
         WHERE id=NEW.supersedes_decision_id;
        IF NOT FOUND
           OR prior_row.task_id IS DISTINCT FROM NEW.task_id
           OR prior_row.status <> 'active' THEN
            RAISE EXCEPTION 'replacement decision must supersede an active decision on the same task';
        END IF;
    END IF;

    RETURN NEW;
END
$$;

DROP TRIGGER IF EXISTS trg_validate_task_decision_insert ON vres.task_decisions;
CREATE TRIGGER trg_validate_task_decision_insert
BEFORE INSERT ON vres.task_decisions
FOR EACH ROW
EXECUTE FUNCTION vres.validate_task_decision_insert();
