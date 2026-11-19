-- W4 R-12: prospectively rebind ORIGINAL 042/043 writer functions by serial ID.
-- SOURCE ONLY / NOT_APPLIED / NOT_EXECUTED. No PostgreSQL even SELECT.
-- This is a single ORIGINAL task-lifecycle/writer correction, not a new store.
CREATE OR REPLACE FUNCTION vres.latest_observed_user_input(
    p_project_id bigint,
    p_provider_session_id text
)
RETURNS TABLE(
    observation_id bigint,
    text text,
    source text,
    kind text,
    observed_at timestamptz,
    committed_at timestamptz,
    committed_event_id bigint,
    committed_task_key text
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, vres
AS $$
DECLARE
    allowed name;
BEGIN
    SELECT writer_role INTO allowed
      FROM vres.provenance_authority
     WHERE authority_key='user_event_writer';
    IF allowed IS NULL OR session_user <> allowed::text THEN
        RAISE EXCEPTION 'reading protected user observation requires the trusted provenance writer role'
            USING ERRCODE='P0001';
    END IF;

    RETURN QUERY
    SELECT o.id, o.text, o.source, o.kind, o.observed_at, o.committed_at,
           o.committed_event_id, t.task_key
      FROM vres.user_input_observations o
      LEFT JOIN vres.tasks t ON t.id=o.committed_task_id
     WHERE o.project_id=p_project_id
       AND o.provider_session_id=p_provider_session_id
     ORDER BY o.id DESC
     LIMIT 1;
END;
$$;

REVOKE ALL ON FUNCTION vres.latest_observed_user_input(bigint,text) FROM PUBLIC;

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

-- ORIGINAL writer SECURITY DEFINER cancellation, not a parallel runtime.
CREATE OR REPLACE FUNCTION vres.cancel_task_from_current_observation(
    p_project_id bigint,
    p_provider_session_id text,
    p_task_key text,
    p_observation_id bigint,
    p_safe_reason text,
    p_sibling_snapshot jsonb
)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, vres
AS $$
DECLARE
    allowed name;
    sess record;
    target record;
    obs record;
    sibling record;
    canonical text;
    actual_siblings jsonb := '[]'::jsonb;
    committed_id bigint;
BEGIN
    SELECT writer_role INTO allowed FROM vres.provenance_authority
     WHERE authority_key='user_event_writer';
    IF allowed IS NULL OR session_user <> allowed::text THEN
        RAISE EXCEPTION 'atomic cancellation requires the trusted provenance writer'
            USING ERRCODE='P0001';
    END IF;
    IF p_project_id IS NULL OR p_observation_id IS NULL OR p_observation_id <= 0
       OR p_provider_session_id IS NULL OR btrim(p_provider_session_id) = ''
       OR p_task_key IS NULL OR btrim(p_task_key) = ''
       OR p_safe_reason IS NULL OR btrim(p_safe_reason) = ''
       OR length(p_safe_reason) > 4000
       OR jsonb_typeof(p_sibling_snapshot) IS DISTINCT FROM 'array' THEN
        RAISE EXCEPTION 'atomic cancellation missing validated inputs'
            USING ERRCODE='P0001';
    END IF;

    -- Original 029 staging locks this session BEFORE inserting an observation.
    -- The same lock spans provenance commit and task cancellation here.
    SELECT s.id,s.task_id INTO sess
      FROM vres.sessions s
     WHERE s.provider='claude'
       AND s.project_id=p_project_id
       AND s.provider_session_id=p_provider_session_id
       AND s.ended_at IS NULL
     ORDER BY s.started_at DESC LIMIT 1 FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'atomic cancellation requires active Claude session'
            USING ERRCODE='P0001';
    END IF;
    IF sess.task_id IS NULL THEN
        RAISE EXCEPTION 'atomic cancellation session must be task-bound'
            USING ERRCODE='P0001';
    END IF;
    SELECT t.id,t.project_id,t.task_key,t.status INTO target
      FROM vres.tasks t WHERE t.id=sess.task_id FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'atomic cancellation task is missing' USING ERRCODE='P0001';
    END IF;
    IF target.project_id IS DISTINCT FROM p_project_id
       OR target.task_key IS DISTINCT FROM p_task_key
       OR target.status NOT IN ('active','waiting_user','blocked') THEN
        RAISE EXCEPTION 'atomic cancellation task/session/status mismatch'
            USING ERRCODE='P0001';
    END IF;

    -- Writer-serialized observation ID wins; host observed_at can move backward.
    SELECT o.* INTO obs FROM vres.user_input_observations o
     WHERE o.project_id=p_project_id
       AND o.provider_session_id=p_provider_session_id
     ORDER BY o.id DESC LIMIT 1 FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'atomic cancellation has no protected observation'
            USING ERRCODE='P0001';
    END IF;
    IF obs.id IS DISTINCT FROM p_observation_id
       OR obs.strict_persistence_stage_version IS DISTINCT FROM 1
       OR obs.source IS DISTINCT FROM 'user_prompt'
       OR obs.kind IS DISTINCT FROM 'instruction'
       OR obs.committed_event_id IS NOT NULL OR obs.committed_at IS NOT NULL THEN
        RAISE EXCEPTION 'atomic cancellation requires newest uncommitted strict direct prompt'
            USING ERRCODE='P0001';
    END IF;

    -- Authority check is repeated in SQL; Python preflight cannot authorize.
    canonical := lower(regexp_replace(btrim(obs.text), '[[:space:]]+', ' ', 'g'));
    canonical := regexp_replace(canonical, '[.! ]+$', '');
    IF canonical NOT IN (
        'cancel', 'cancel it', 'cancel this', 'cancel this task',
        'cancel the task', 'cancel current task', 'cancel the current task',
        'please cancel this task', 'please cancel the task',
        'yes, cancel it', 'yes, cancel this task',
        'ακύρωση', 'ακύρωσέ το', 'ακυρωσε το',
        'ακύρωσε αυτή την εργασία', 'ακυρωσε αυτη την εργασια'
    )
    AND canonical !~ '^(please )?cancel (this|the|current) task( because .+)?$'
    AND canonical !~ '^ακύρωσε αυτή την εργασία( .+)?$'
    AND canonical !~ '^ακυρωσε αυτη την εργασια( .+)?$' THEN
        RAISE EXCEPTION 'atomic cancellation prompt is not an explicit cancellation'
            USING ERRCODE='P0001';
    END IF;

    -- Python strictly validated EVERY sibling id. Re-check entire snapshot
    -- under locks: no new, replaced, removed or unvalidated sibling can pass.
    FOR sibling IN
        SELECT s.id,s.provider_session_id FROM vres.sessions s
         WHERE s.project_id=p_project_id AND s.task_id=target.id
           AND s.ended_at IS NULL
         ORDER BY s.id FOR UPDATE
    LOOP
        actual_siblings := actual_siblings || jsonb_build_array(jsonb_build_object(
            'id',sibling.id,'provider_session_id',sibling.provider_session_id
        ));
    END LOOP;
    IF actual_siblings IS DISTINCT FROM p_sibling_snapshot THEN
        RAISE EXCEPTION 'atomic cancellation sibling identity changed or was not validated'
            USING ERRCODE='P0001';
    END IF;

    PERFORM vres.commit_user_inputs(p_project_id,p_provider_session_id,p_task_key);
    SELECT o.committed_event_id INTO committed_id
      FROM vres.user_input_observations o WHERE o.id=p_observation_id;
    IF committed_id IS NULL OR NOT EXISTS (
        SELECT 1 FROM vres.task_events e
         WHERE e.id=committed_id AND e.task_id=target.id
           AND e.session_id=p_provider_session_id
           AND e.actor='user' AND e.event_type='USER_INSTRUCTION'
           AND e.payload->>'source'='user_prompt'
           AND e.payload->>'text'=obs.text
           AND e.payload->>'legacy_unverified_held'='false'
    ) THEN
        RAISE EXCEPTION 'atomic cancellation lacks exact newly committed event'
            USING ERRCODE='P0001';
    END IF;
    UPDATE vres.validation_requests
       SET status='superseded',completed_at=COALESCE(completed_at,now())
     WHERE task_id=target.id AND status='pending';
    UPDATE vres.task_state
       SET validation_status='pending',updated_at=now() WHERE task_id=target.id;
    UPDATE vres.tasks SET status='cancelled',updated_at=now() WHERE id=target.id;
    INSERT INTO vres.task_events(task_id,event_type,actor,payload,session_id)
    VALUES (
        target.id,'TASK_STATUS_CHANGED','chairman',
        jsonb_build_object(
            'from_status',target.status,'to_status','cancelled',
            'reason',p_safe_reason,'state_preserved',true,
            'authorization','current_user_instruction'
        ),p_provider_session_id
    );
    FOR sibling IN
        SELECT s.id,s.provider_session_id FROM vres.sessions s
         WHERE s.project_id=p_project_id AND s.task_id=target.id
           AND s.ended_at IS NULL
         ORDER BY s.id FOR UPDATE
    LOOP
        INSERT INTO vres.task_events(task_id,event_type,actor,payload,session_id)
        VALUES (
            target.id,'SESSION_UNBOUND','chairman',
            jsonb_build_object(
                'source','task_cancelled','previous_task_id',target.id,
                'previous_task_key',p_task_key,
                'new_task_id',NULL::bigint,'new_task_key',NULL::text
            ),sibling.provider_session_id
        );
    END LOOP;
    UPDATE vres.sessions SET task_id=NULL
     WHERE project_id=p_project_id AND task_id=target.id AND ended_at IS NULL;
    UPDATE vres.project_focus SET task_id=NULL,updated_at=now()
     WHERE project_id=p_project_id AND task_id=target.id;
    RETURN jsonb_build_object('changed',true,'from_status',target.status,'status','cancelled');
END;
$$;
REVOKE ALL ON FUNCTION vres.cancel_task_from_current_observation(
    bigint,text,text,bigint,text,jsonb
) FROM PUBLIC;
