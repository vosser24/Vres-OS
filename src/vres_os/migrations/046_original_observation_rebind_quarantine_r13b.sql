-- W4 R13B: ORIGINAL 043/044 user-event writer and session task rebind gate.
-- SOURCE ONLY / NOT_APPLIED / NOT_TESTED. P0 Schema048: NO PostgreSQL even SELECT.
-- Requires prospective 042/043/044/045 in order; no past migration was edited.
-- Same-task unobserved-turn freshness (C-3) is NOT solved.
--
-- A -> B -> A session rebinding must not resurrect the original strict marker.
-- This acts on an ORIGINAL session task change or its closure; no new data store.
CREATE OR REPLACE FUNCTION vres.invalidate_strict_observations_on_rebind()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, vres
AS $$
BEGIN
    IF OLD.task_id IS DISTINCT FROM NEW.task_id
       OR (OLD.ended_at IS NULL AND NEW.ended_at IS NOT NULL) THEN
        UPDATE vres.user_input_observations
           SET strict_persistence_stage_version=NULL
         WHERE observed_session_id=OLD.id
           AND committed_event_id IS NULL
           AND committed_at IS NULL
           AND strict_persistence_stage_version=1;
    END IF;
    RETURN NEW;
END;
$$;
REVOKE ALL ON FUNCTION vres.invalidate_strict_observations_on_rebind() FROM PUBLIC;

DROP TRIGGER IF EXISTS trg_invalidate_strict_observations_on_rebind ON vres.sessions;
CREATE TRIGGER trg_invalidate_strict_observations_on_rebind
AFTER UPDATE OF task_id, ended_at ON vres.sessions
FOR EACH ROW EXECUTE FUNCTION vres.invalidate_strict_observations_on_rebind();

-- The SAME original writer is redefined to commit ONLY observations staged
-- under the locked current session AND task. Unbound/historical/old-task rows
-- remain pending without being projected into another task's events or state.
-- Original row locks and metadata update are otherwise unchanged.
CREATE OR REPLACE FUNCTION vres.commit_user_inputs(
    p_project_id bigint,
    p_provider_session_id text,
    p_task_key text DEFAULT NULL
)
RETURNS TABLE(event_id bigint,event_type text,text text,source text,created_at timestamptz)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, vres
AS $$
DECLARE
    allowed name;
    sess record;
    target record;
    obs record;
    ev record;
    latest_instruction text;
    committed_ids jsonb;
BEGIN
    SELECT writer_role INTO allowed FROM vres.provenance_authority WHERE authority_key='user_event_writer';
    IF allowed IS NULL OR session_user <> allowed::text THEN
        RAISE EXCEPTION 'committing user input requires the trusted provenance writer role'
            USING ERRCODE='P0001';
    END IF;
    SELECT id,task_id,metadata INTO sess
      FROM vres.sessions
     WHERE provider='claude'
       AND provider_session_id=p_provider_session_id
       AND project_id=p_project_id
       AND ended_at IS NULL
     ORDER BY started_at DESC
     LIMIT 1
     FOR UPDATE;
    IF sess.id IS NULL OR sess.task_id IS NULL THEN
        RETURN;
    END IF;
    SELECT id,task_key,project_id,status INTO target
      FROM vres.tasks
     WHERE id=sess.task_id
     FOR UPDATE;
    IF target.id IS NULL
       OR target.project_id <> p_project_id
       OR target.status NOT IN ('active','waiting_user','blocked') THEN
        RAISE EXCEPTION 'staged user input target is not an unfinished task in this project'
            USING ERRCODE='P0001';
    END IF;
    IF p_task_key IS NOT NULL AND target.task_key <> p_task_key THEN
        RAISE EXCEPTION 'staged user input target does not match the bound unfinished task'
            USING ERRCODE='P0001';
    END IF;
    FOR obs IN
        SELECT * FROM vres.user_input_observations
         WHERE project_id=p_project_id
           AND provider_session_id=p_provider_session_id
           AND committed_event_id IS NULL
           AND committed_at IS NULL
           AND observed_session_id=sess.id
           AND observed_task_id=target.id
           AND strict_persistence_stage_version=1
         ORDER BY id
         FOR UPDATE
    LOOP
        INSERT INTO vres.task_events AS inserted_event(task_id,event_type,actor,payload,session_id,created_at)
        VALUES (
            target.id,
            CASE WHEN obs.kind='control' THEN 'USER_CONTROL' ELSE 'USER_INSTRUCTION' END,
            'user',
            jsonb_strip_nulls(jsonb_build_object(
                'text',CASE WHEN obs.strict_persistence_stage_version=1
                            THEN obs.text ELSE '[UNVERIFIED_LEGACY_USER_INPUT_HELD]' END,
                'source',obs.source,
                'question',CASE WHEN obs.strict_persistence_stage_version=1
                                THEN obs.question ELSE NULL END,
                'tool_use_id',CASE WHEN obs.strict_persistence_stage_version=1
                                   THEN obs.tool_use_id ELSE NULL END,
                'legacy_unverified_held',(obs.strict_persistence_stage_version IS DISTINCT FROM 1)
            )),
            p_provider_session_id,
            obs.observed_at
        ) RETURNING inserted_event.id,inserted_event.created_at INTO ev;
        UPDATE vres.user_input_observations
           SET committed_task_id=target.id,committed_event_id=ev.id,committed_at=now()
         WHERE id=obs.id;
        IF obs.kind='instruction' THEN
            latest_instruction := CASE WHEN obs.strict_persistence_stage_version=1
                THEN obs.text ELSE '[UNVERIFIED_LEGACY_USER_INPUT_HELD]' END;
        END IF;
        event_id := ev.id;
        event_type := CASE WHEN obs.kind='control' THEN 'USER_CONTROL' ELSE 'USER_INSTRUCTION' END;
        text := CASE WHEN obs.strict_persistence_stage_version=1
            THEN obs.text ELSE '[UNVERIFIED_LEGACY_USER_INPUT_HELD]' END;
        source := obs.source;
        created_at := ev.created_at;
        RETURN NEXT;
    END LOOP;
    IF latest_instruction IS NOT NULL THEN
        UPDATE vres.task_state
           SET latest_user_instruction=latest_instruction,updated_at=now()
         WHERE task_id=target.id;
    END IF;
    UPDATE vres.tasks SET updated_at=now() WHERE id=target.id;
    SELECT COALESCE(jsonb_agg(tool_use_id ORDER BY committed_at,id),'[]'::jsonb) INTO committed_ids
      FROM (
        SELECT tool_use_id,committed_at,id
          FROM vres.user_input_observations
         WHERE provider_session_id=p_provider_session_id
           AND tool_use_id IS NOT NULL
           AND committed_event_id IS NOT NULL
           AND strict_persistence_stage_version=1
         ORDER BY committed_at DESC,id DESC
         LIMIT 100
      ) q;
    UPDATE vres.sessions
       SET metadata=(COALESCE(metadata,'{}'::jsonb)
                     - 'pending_user_instructions'
                     - 'pending_user_instruction'
                     - 'committed_user_input_tool_ids')
                    || CASE WHEN jsonb_array_length(committed_ids)>0
                            THEN jsonb_build_object('committed_user_input_tool_ids',committed_ids)
                            ELSE '{}'::jsonb END
     WHERE id=sess.id;
END;
$$;

REVOKE ALL ON FUNCTION vres.stage_strict_user_input(
    bigint,text,text,text,text,text,text,timestamptz,text
) FROM PUBLIC;
REVOKE ALL ON FUNCTION vres.commit_user_inputs(bigint,text,text) FROM PUBLIC;

