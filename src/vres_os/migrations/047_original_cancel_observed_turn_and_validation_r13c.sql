-- W4 R13C: ORIGINAL host-turn staging and atomic cancellation correction (prospective).
-- SOURCE ONLY, NOT_APPLIED / NOT_RUN. NO PostgreSQL even SELECT (schema048 incident).
-- 023/028/029/032/042-046 remain immutable; no second task/session/event store.
-- C-3 when later host turns were not observed is NOT fully solved.
-- reply_guard provides an additional recorded-turn consistency fence, not
-- cryptographic authority or evidence of a host prompt that was never observed.
-- First prompts unbound at staging are NOT later re-attributed.

ALTER TABLE vres.user_input_observations ADD COLUMN observed_turn_id text;

-- Redefine existing 045 strict stage; capture observed original reply turn.
CREATE OR REPLACE FUNCTION vres.stage_strict_user_input(
    p_project_id bigint,
    p_provider_session_id text,
    p_text text,
    p_source text,
    p_kind text,
    p_tool_use_id text,
    p_question text,
    p_observed_at timestamptz,
    p_strict_stage_contract text
)
RETURNS boolean
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, vres
AS $$
DECLARE
    allowed name;
    staged boolean;
    staged_id bigint;
    observed_binding record;
BEGIN
    SELECT writer_role INTO allowed FROM vres.provenance_authority
     WHERE authority_key='user_event_writer';
    IF allowed IS NULL OR session_user <> allowed::text THEN
        RAISE EXCEPTION 'strict staging requires trusted provenance writer'
            USING ERRCODE='P0001';
    END IF;
    IF p_strict_stage_contract IS DISTINCT FROM 'vres-python-strict-v1' THEN
        RAISE EXCEPTION 'strict stage contract mismatch' USING ERRCODE='P0001';
    END IF;
    -- Capture the original task and provider-session identity at prompt staging.
    SELECT s.id,s.task_id,s.metadata INTO observed_binding FROM vres.sessions s
     WHERE s.provider='claude' AND s.project_id=p_project_id
       AND s.provider_session_id=p_provider_session_id AND s.ended_at IS NULL
     ORDER BY s.started_at DESC,s.id DESC LIMIT 1 FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'strict staging requires an active original session'
            USING ERRCODE='P0001';
    END IF;
    -- Original 029 stage obtains a FOR UPDATE session lock. This marks only
    -- the just-inserted same-session row in the same database transaction.
    SELECT vres.stage_user_input(
        p_project_id,p_provider_session_id,p_text,p_source,p_kind,
        p_tool_use_id,p_question,p_observed_at
    ) INTO staged;
    IF NOT staged THEN RETURN false; END IF;
    SELECT id INTO staged_id FROM vres.user_input_observations
     WHERE project_id=p_project_id
       AND provider_session_id=p_provider_session_id
       AND committed_event_id IS NULL
     ORDER BY id DESC LIMIT 1 FOR UPDATE;
    IF staged_id IS NULL THEN
        RAISE EXCEPTION 'strict stage cannot locate new observation'
            USING ERRCODE='P0001';
    END IF;
    UPDATE vres.user_input_observations
       SET strict_persistence_stage_version=1,
           observed_session_id=observed_binding.id,
           observed_task_id=observed_binding.task_id,
           observed_turn_id=NULLIF(btrim(observed_binding.metadata->'reply_guard'->>'turn_id'), '')
     WHERE id=staged_id;
    RETURN true;
END;
$$;

REVOKE ALL ON FUNCTION vres.stage_strict_user_input(
    bigint,text,text,text,text,text,text,timestamptz,text
) FROM PUBLIC;

-- Redefine existing 045 atomic cancellation in the ORIGINAL provenance writer.
-- Maintain session/task/observation locks and NOWAIT sibling snapshot.
-- Reject ambiguous cancellation and preserve passed-validation evidence.
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
    SELECT s.id,s.task_id,s.metadata INTO sess
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
       OR obs.observed_session_id IS DISTINCT FROM sess.id
       OR obs.observed_task_id IS DISTINCT FROM target.id
       OR obs.observed_turn_id IS NULL
       OR obs.observed_turn_id IS DISTINCT FROM NULLIF(btrim(sess.metadata->'reply_guard'->>'turn_id'), '')
       OR (sess.metadata->'reply_guard'->>'gate') IS NOT NULL
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
        'cancel', 'cancel it', 'cancel this task',
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

    -- Sibling NOWAIT failures abort atomically instead of deadlocking a binder.
    -- Python strictly validated EVERY sibling id. Re-check entire snapshot
    -- under locks: no new, replaced, removed or unvalidated sibling can pass.
    FOR sibling IN
        SELECT s.id,s.provider_session_id FROM vres.sessions s
         WHERE s.project_id=p_project_id AND s.task_id=target.id
           AND s.ended_at IS NULL
         ORDER BY s.id FOR UPDATE NOWAIT
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
    -- Terminal cancellation preserves prior task_state.validation_status (including passed).
    -- Migration 028 forbids implicit rollback of validated task_state; do not bypass it.
    -- Existing pending validation_requests were superseded above in this transaction.
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
         ORDER BY s.id FOR UPDATE NOWAIT
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
