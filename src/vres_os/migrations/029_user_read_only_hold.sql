-- Protect an explicit inspection/read-only user control with the same trusted-writer
-- boundary used for USER_INSTRUCTION provenance. Runtime SQL must not be able to
-- forge or clear the hold, and background/system events must not alter it.

CREATE OR REPLACE FUNCTION vres.protect_user_input_metadata()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, vres
AS $$
DECLARE
    allowed name;
    old_pending jsonb;
    new_pending jsonb;
    old_legacy jsonb;
    new_legacy jsonb;
    old_committed jsonb;
    new_committed jsonb;
    old_read_only_hold jsonb;
    new_read_only_hold jsonb;
BEGIN
    SELECT writer_role INTO allowed
      FROM vres.provenance_authority
     WHERE authority_key='user_event_writer';
    IF TG_OP = 'INSERT' THEN
        old_pending := NULL;
        old_legacy := NULL;
        old_committed := NULL;
        old_read_only_hold := NULL;
    ELSE
        old_pending := OLD.metadata->'pending_user_instructions';
        old_legacy := OLD.metadata->'pending_user_instruction';
        old_committed := OLD.metadata->'committed_user_input_tool_ids';
        old_read_only_hold := OLD.metadata->'vres_read_only_hold';
    END IF;
    new_pending := NEW.metadata->'pending_user_instructions';
    new_legacy := NEW.metadata->'pending_user_instruction';
    new_committed := NEW.metadata->'committed_user_input_tool_ids';
    new_read_only_hold := NEW.metadata->'vres_read_only_hold';
    IF (
        old_pending IS DISTINCT FROM new_pending
        OR old_legacy IS DISTINCT FROM new_legacy
        OR old_committed IS DISTINCT FROM new_committed
        OR old_read_only_hold IS DISTINCT FROM new_read_only_hold
    ) AND (allowed IS NULL OR session_user <> allowed::text) THEN
        RAISE EXCEPTION 'protected user-input session metadata requires the trusted provenance writer role'
            USING ERRCODE='P0001';
    END IF;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_protect_user_input_metadata ON vres.sessions;
CREATE TRIGGER trg_protect_user_input_metadata
BEFORE INSERT OR UPDATE OF metadata ON vres.sessions
FOR EACH ROW EXECUTE FUNCTION vres.protect_user_input_metadata();

CREATE OR REPLACE FUNCTION vres.stage_user_input(
    p_project_id bigint,
    p_provider_session_id text,
    p_text text,
    p_source text,
    p_kind text,
    p_tool_use_id text,
    p_question text,
    p_observed_at timestamptz
)
RETURNS boolean
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, vres
AS $$
DECLARE
    allowed name;
    sess record;
    entry jsonb;
    queue jsonb;
    read_only_hold boolean := false;
    effective_kind text;
    hold jsonb;
BEGIN
    SELECT writer_role INTO allowed
      FROM vres.provenance_authority
     WHERE authority_key='user_event_writer';
    IF allowed IS NULL OR session_user <> allowed::text THEN
        RAISE EXCEPTION 'staging user input requires the trusted provenance writer role'
            USING ERRCODE='P0001';
    END IF;
    IF p_text IS NULL OR btrim(p_text) = '' THEN
        RETURN false;
    END IF;
    IF p_source NOT IN ('user_prompt','ask_user_question') OR p_kind NOT IN ('instruction','control') THEN
        RAISE EXCEPTION 'unsupported user-input source or kind' USING ERRCODE='P0001';
    END IF;

    -- This classifier is intentionally narrow and authority-bearing. It recognizes
    -- a direct line-start directive such as "Inspection only. Do not ..." or an
    -- explicit "Treat this as read-only" phrase, but not prose merely discussing
    -- inspection/read-only behavior.
    IF p_source = 'user_prompt' THEN
        read_only_hold :=
            p_text ~* E'(^|\\n)[[:space:]]*(inspection[[:space:]]+only|read[- ]only([[:space:]]+(inspection|mode))?)([[:space:]]*[.!:;\\-]|[[:space:]]*(\\n|$))'
            OR p_text ~* '(this[[:space:]]+is|treat[[:space:]]+this[[:space:]]+as|for[[:space:]]+this[[:space:]]+turn[, ]*)[[:space:]]+(an?[[:space:]]+)?(inspection[- ]only|read[- ]only)';
    END IF;
    effective_kind := CASE
        WHEN p_source='user_prompt' AND read_only_hold THEN 'control'
        ELSE p_kind
    END;

    SELECT id,metadata INTO sess
      FROM vres.sessions
     WHERE provider='claude'
       AND provider_session_id=p_provider_session_id
       AND project_id=p_project_id
       AND ended_at IS NULL
     ORDER BY started_at DESC
     LIMIT 1
     FOR UPDATE;
    IF sess.id IS NULL THEN
        RAISE EXCEPTION 'cannot stage user input for an unregistered or closed session'
            USING ERRCODE='P0001';
    END IF;
    IF p_tool_use_id IS NOT NULL AND EXISTS (
        SELECT 1 FROM vres.user_input_observations
         WHERE provider_session_id=p_provider_session_id AND tool_use_id=p_tool_use_id
    ) THEN
        RETURN false;
    END IF;
    INSERT INTO vres.user_input_observations(
        project_id,provider_session_id,text,source,kind,tool_use_id,question,observed_at
    ) VALUES (
        p_project_id,p_provider_session_id,p_text,p_source,effective_kind,p_tool_use_id,p_question,
        COALESCE(p_observed_at,now())
    );
    entry := jsonb_build_object(
        'text',p_text,
        'observed_at',COALESCE(p_observed_at,now()),
        'source',p_source,
        'kind',effective_kind
    );
    IF p_tool_use_id IS NOT NULL THEN
        entry := entry || jsonb_build_object('tool_use_id',p_tool_use_id);
    END IF;
    IF p_question IS NOT NULL AND btrim(p_question) <> '' THEN
        entry := entry || jsonb_build_object('question',p_question);
    END IF;
    queue := COALESCE(sess.metadata->'pending_user_instructions','[]'::jsonb) || jsonb_build_array(entry);
    IF jsonb_array_length(queue) > 20 THEN
        SELECT COALESCE(jsonb_agg(value ORDER BY ord),'[]'::jsonb) INTO queue
          FROM jsonb_array_elements(queue) WITH ORDINALITY x(value,ord)
         WHERE ord > jsonb_array_length(queue) - 20;
    END IF;

    -- Only a real UserPromptSubmit may set or clear the hold. AskUserQuestion answers
    -- are authoritative user input too, but they do not implicitly resume a task that
    -- the user's latest direct prompt explicitly placed in inspection-only mode.
    IF p_source = 'user_prompt' THEN
        hold := jsonb_build_object(
            'active',read_only_hold,
            'observed_at',COALESCE(p_observed_at,now()),
            'reason',CASE WHEN read_only_hold
                          THEN 'explicit_read_only_user_instruction'
                          ELSE 'later_user_prompt' END
        );
        UPDATE vres.sessions
           SET metadata=jsonb_set(
                jsonb_set(
                    (COALESCE(metadata,'{}'::jsonb) - 'pending_user_instruction'),
                    '{pending_user_instructions}',queue,true
                ),
                '{vres_read_only_hold}',hold,true
           )
         WHERE id=sess.id;
    ELSE
        UPDATE vres.sessions
           SET metadata=jsonb_set(
                (COALESCE(metadata,'{}'::jsonb) - 'pending_user_instruction'),
                '{pending_user_instructions}',queue,true
           )
         WHERE id=sess.id;
    END IF;
    RETURN true;
END;
$$;

REVOKE ALL ON FUNCTION vres.stage_user_input(bigint,text,text,text,text,text,text,timestamptz) FROM PUBLIC;
