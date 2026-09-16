CREATE TABLE IF NOT EXISTS vres.provenance_authority (
    authority_key text PRIMARY KEY CHECK (authority_key = 'user_event_writer'),
    writer_role name NOT NULL,
    configured_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS vres.user_input_observations (
    id bigserial PRIMARY KEY,
    project_id bigint NOT NULL REFERENCES vres.projects(id) ON DELETE CASCADE,
    provider_session_id text NOT NULL,
    text text NOT NULL,
    source text NOT NULL CHECK (source IN ('user_prompt','ask_user_question')),
    kind text NOT NULL CHECK (kind IN ('instruction','control')),
    tool_use_id text,
    question text,
    observed_at timestamptz NOT NULL,
    committed_task_id bigint REFERENCES vres.tasks(id) ON DELETE SET NULL,
    committed_event_id bigint REFERENCES vres.task_events(id) ON DELETE SET NULL,
    committed_at timestamptz,
    UNIQUE(provider_session_id, tool_use_id)
);
CREATE INDEX IF NOT EXISTS idx_user_input_observations_pending
    ON vres.user_input_observations(project_id,provider_session_id,observed_at,id)
    WHERE committed_event_id IS NULL;

INSERT INTO vres.provenance_authority(authority_key,writer_role)
VALUES ('user_event_writer', session_user)
ON CONFLICT(authority_key) DO NOTHING;

CREATE OR REPLACE FUNCTION vres.user_event_writer_role()
RETURNS name
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = pg_catalog, vres
AS $$
    SELECT writer_role FROM vres.provenance_authority WHERE authority_key='user_event_writer'
$$;

CREATE OR REPLACE FUNCTION vres.protect_user_authority_event()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, vres
AS $$
DECLARE
    allowed name;
BEGIN
    IF NEW.event_type NOT IN ('USER_INSTRUCTION','USER_CONTROL') THEN
        RETURN NEW;
    END IF;
    SELECT writer_role INTO allowed
      FROM vres.provenance_authority
     WHERE authority_key='user_event_writer';
    IF allowed IS NULL OR session_user <> allowed::text THEN
        RAISE EXCEPTION 'user-authority task events require the trusted provenance writer role'
            USING ERRCODE='P0001';
    END IF;
    IF NEW.actor <> 'user' THEN
        RAISE EXCEPTION 'user-authority task events must have actor=user'
            USING ERRCODE='P0001';
    END IF;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_protect_user_authority_event ON vres.task_events;
CREATE TRIGGER trg_protect_user_authority_event
BEFORE INSERT OR UPDATE ON vres.task_events
FOR EACH ROW EXECUTE FUNCTION vres.protect_user_authority_event();

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
BEGIN
    SELECT writer_role INTO allowed
      FROM vres.provenance_authority
     WHERE authority_key='user_event_writer';
    IF TG_OP = 'INSERT' THEN
        old_pending := NULL;
        old_legacy := NULL;
        old_committed := NULL;
    ELSE
        old_pending := OLD.metadata->'pending_user_instructions';
        old_legacy := OLD.metadata->'pending_user_instruction';
        old_committed := OLD.metadata->'committed_user_input_tool_ids';
    END IF;
    new_pending := NEW.metadata->'pending_user_instructions';
    new_legacy := NEW.metadata->'pending_user_instruction';
    new_committed := NEW.metadata->'committed_user_input_tool_ids';
    IF (
        old_pending IS DISTINCT FROM new_pending
        OR old_legacy IS DISTINCT FROM new_legacy
        OR old_committed IS DISTINCT FROM new_committed
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
        p_project_id,p_provider_session_id,p_text,p_source,p_kind,p_tool_use_id,p_question,
        COALESCE(p_observed_at,now())
    );
    entry := jsonb_build_object(
        'text',p_text,
        'observed_at',COALESCE(p_observed_at,now()),
        'source',p_source,
        'kind',p_kind
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
    UPDATE vres.sessions
       SET metadata=jsonb_set(
            (COALESCE(metadata,'{}'::jsonb) - 'pending_user_instruction'),
            '{pending_user_instructions}',queue,true
       )
     WHERE id=sess.id;
    RETURN true;
END;
$$;

CREATE OR REPLACE FUNCTION vres.latest_pending_user_instruction(
    p_project_id bigint,
    p_provider_session_id text
)
RETURNS text
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, vres
AS $$
DECLARE
    allowed name;
    value text;
BEGIN
    SELECT writer_role INTO allowed FROM vres.provenance_authority WHERE authority_key='user_event_writer';
    IF allowed IS NULL OR session_user <> allowed::text THEN
        RAISE EXCEPTION 'reading protected pending user input requires the trusted provenance writer role'
            USING ERRCODE='P0001';
    END IF;
    SELECT text INTO value
      FROM vres.user_input_observations
     WHERE project_id=p_project_id
       AND provider_session_id=p_provider_session_id
       AND committed_event_id IS NULL
       AND kind='instruction'
     ORDER BY observed_at DESC,id DESC
     LIMIT 1;
    RETURN value;
END;
$$;

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
         ORDER BY observed_at,id
         FOR UPDATE
    LOOP
        INSERT INTO vres.task_events AS inserted_event(task_id,event_type,actor,payload,session_id,created_at)
        VALUES (
            target.id,
            CASE WHEN obs.kind='control' THEN 'USER_CONTROL' ELSE 'USER_INSTRUCTION' END,
            'user',
            jsonb_strip_nulls(jsonb_build_object(
                'text',obs.text,
                'source',obs.source,
                'question',obs.question,
                'tool_use_id',obs.tool_use_id
            )),
            p_provider_session_id,
            obs.observed_at
        ) RETURNING inserted_event.id,inserted_event.created_at INTO ev;
        UPDATE vres.user_input_observations
           SET committed_task_id=target.id,committed_event_id=ev.id,committed_at=now()
         WHERE id=obs.id;
        IF obs.kind='instruction' THEN
            latest_instruction := obs.text;
        END IF;
        event_id := ev.id;
        event_type := CASE WHEN obs.kind='control' THEN 'USER_CONTROL' ELSE 'USER_INSTRUCTION' END;
        text := obs.text;
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
         ORDER BY committed_at DESC,id DESC
         LIMIT 100
      ) q;
    UPDATE vres.sessions
       SET metadata=(COALESCE(metadata,'{}'::jsonb)
                     - 'pending_user_instructions'
                     - 'pending_user_instruction')
                    || CASE WHEN jsonb_array_length(committed_ids)>0
                            THEN jsonb_build_object('committed_user_input_tool_ids',committed_ids)
                            ELSE '{}'::jsonb END
     WHERE id=sess.id;
END;
$$;

REVOKE ALL ON TABLE vres.provenance_authority FROM PUBLIC;
REVOKE ALL ON TABLE vres.user_input_observations FROM PUBLIC;
REVOKE ALL ON FUNCTION vres.user_event_writer_role() FROM PUBLIC;
REVOKE ALL ON FUNCTION vres.stage_user_input(bigint,text,text,text,text,text,text,timestamptz) FROM PUBLIC;
REVOKE ALL ON FUNCTION vres.latest_pending_user_instruction(bigint,text) FROM PUBLIC;
REVOKE ALL ON FUNCTION vres.commit_user_inputs(bigint,text,text) FROM PUBLIC;
