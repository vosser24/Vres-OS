-- #176 E7 G7 Chunk 1 (design: EXPERIENCE-INTELLIGENCE-E7-G7-DESIGN-FREEZE-ERRATA-2026-10-09, policy 176.g7.v1).
-- Append-only source-trust ledger plus the single protected write function. Additive and idempotent; nothing
-- existing is changed. Chunk 1 creates the ledger and the write path only: no reader (source_effective_trust,
-- Chunk 2), no Python/MCP surface (Chunk 3) and no change to E1/E2 semantics.
--
-- Authority: the immutable USER_INSTRUCTION event (typed prompt, provenance-writer only, migrations 023/024) must be
-- the task's newest user-authority event BY ID and its whole trimmed text must equal 'I authorize ' || subject_key,
-- where the subject key embeds digests the database has just recomputed. approval_events is neither read nor written.
-- Residual (G8, not solved here): a same-user process able to invoke the prompt hook can forge such an event.

CREATE TABLE IF NOT EXISTS vres.source_trust_events (
    id bigserial PRIMARY KEY,
    event_key text NOT NULL UNIQUE CHECK (event_key ~ '^STE-[0-9a-f]{32}$'),
    project_id bigint NOT NULL REFERENCES vres.projects(id),
    source_id bigint NOT NULL REFERENCES vres.sources(id),
    source_key text NOT NULL,
    action text NOT NULL CHECK (action IN ('grant','revoke')),
    basis text NOT NULL CHECK (basis = 'user_approval'),
    policy_version text NOT NULL CHECK (policy_version = '176.g7.v1'),
    policy_digest text NOT NULL
        CHECK (policy_digest = 'f20b037b00d0a5711666fd6c1d98538101708d99e7f6f32cf5a490ff6b96cf03'),
    content_digest text NOT NULL CHECK (content_digest ~ '^[0-9a-f]{64}$'),
    descriptor_digest text NOT NULL CHECK (descriptor_digest ~ '^[0-9a-f]{64}$'),
    subject_key text NOT NULL,
    task_id bigint NOT NULL REFERENCES vres.tasks(id),
    user_event_id bigint NOT NULL REFERENCES vres.task_events(id),
    supersedes_event_id bigint REFERENCES vres.source_trust_events(id),
    expires_at timestamptz CHECK (expires_at IS NULL),
    idempotency_key text NOT NULL UNIQUE CHECK (idempotency_key ~ '^[0-9a-f]{64}$'),
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_source_trust_user_event_subject UNIQUE (user_event_id, subject_key),
    CONSTRAINT ck_source_trust_subject CHECK (
        subject_key = 'source_trust:' || action || ':' || project_id::text || ':' || source_key || ':'
                      || content_digest || ':' || descriptor_digest),
    CONSTRAINT ck_source_trust_revoke_supersedes CHECK ((action = 'revoke') = (supersedes_event_id IS NOT NULL))
);
CREATE INDEX IF NOT EXISTS idx_source_trust_events_source ON vres.source_trust_events(source_id, id DESC);

-- Immutability for every role (UPDATE / DELETE / TRUNCATE).
CREATE OR REPLACE FUNCTION vres.protect_source_trust_immutability()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog, vres
AS $vres_g7$
BEGIN
    RAISE EXCEPTION 'source trust ledger is append-only' USING ERRCODE = 'P0001';
END
$vres_g7$;

DROP TRIGGER IF EXISTS trg_source_trust_no_update_delete ON vres.source_trust_events;
CREATE TRIGGER trg_source_trust_no_update_delete
BEFORE UPDATE OR DELETE ON vres.source_trust_events
FOR EACH ROW EXECUTE FUNCTION vres.protect_source_trust_immutability();

DROP TRIGGER IF EXISTS trg_source_trust_no_truncate ON vres.source_trust_events;
CREATE TRIGGER trg_source_trust_no_truncate
BEFORE TRUNCATE ON vres.source_trust_events
FOR EACH STATEMENT EXECUTE FUNCTION vres.protect_source_trust_immutability();

-- INSERT guard. SECURITY INVOKER on purpose: inside the SECURITY DEFINER writer below current_user is the table
-- owner (the legitimate case); a direct INSERT by any other role has current_user = that role and is refused.
CREATE OR REPLACE FUNCTION vres.require_source_trust_owner_insert()
RETURNS trigger
LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = pg_catalog, vres
AS $vres_g7$
BEGIN
    IF current_user::text IS DISTINCT FROM (SELECT pg_get_userbyid(c.relowner)::text
                                              FROM pg_class c WHERE c.oid = TG_RELID) THEN
        RAISE EXCEPTION 'source trust ledger rows may be written only by record_source_trust_decision'
            USING ERRCODE = 'P0001';
    END IF;
    RETURN NEW;
END
$vres_g7$;

DROP TRIGGER IF EXISTS trg_source_trust_owner_insert ON vres.source_trust_events;
CREATE TRIGGER trg_source_trust_owner_insert
BEFORE INSERT ON vres.source_trust_events
FOR EACH ROW EXECUTE FUNCTION vres.require_source_trust_owner_insert();

-- Internal digest helper (policy 176.g7.v1 serializations); also reused by the Chunk 2 reader.
-- content_digest   = sha256 hex of the LF-joined lines '<ordinal>:<sha256_hex(content)>' over the persisted chunks of
--                    the source, ordered by ordinal then chunk hash (C collation).
-- descriptor_digest = sha256 hex of 'source_type=..\norigin=..\nversion=..\nproject_id=..' (NULL as empty).
CREATE OR REPLACE FUNCTION vres.source_trust_digests(p_source_id bigint)
RETURNS TABLE(chunk_count bigint, content_digest text, descriptor_digest text)
LANGUAGE sql
STABLE
SET search_path = pg_catalog, vres
AS $vres_g7$
    SELECT
        (SELECT count(*) FROM vres.knowledge_chunks k WHERE k.source_id = s.id),
        (SELECT encode(sha256(convert_to(string_agg(h.ordinal::text || ':' || h.hash, E'\n'
                                                    ORDER BY h.ordinal, h.hash COLLATE "C"), 'UTF8')), 'hex')
           FROM (SELECT k.ordinal,
                        encode(sha256(convert_to(k.content, 'UTF8')), 'hex') AS hash
                   FROM vres.knowledge_chunks k WHERE k.source_id = s.id) h),
        encode(sha256(convert_to(
            'source_type=' || coalesce(s.source_type, '') || E'\norigin=' || coalesce(s.origin, '')
            || E'\nversion=' || coalesce(s.version, '') || E'\nproject_id=' || coalesce(s.project_id::text, ''),
            'UTF8')), 'hex')
      FROM vres.sources s WHERE s.id = p_source_id
$vres_g7$;

-- The single write path (grant and revoke). Value-free errors: fixed reason codes only.
CREATE OR REPLACE FUNCTION vres.record_source_trust_decision(
    p_task_key text, p_project_id bigint, p_source_key text, p_action text, p_user_event_id bigint,
    p_expected_content_digest text, p_expected_descriptor_digest text)
RETURNS TABLE(ledger_event_key text, ledger_action text, ledger_subject_key text, replayed boolean)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, vres
AS $vres_g7$
DECLARE
    t record;
    s record;
    ev record;
    d record;
    g record;
    existing record;
    subject text;
    newest_id bigint;
    new_key text;
    idem text;
BEGIN
    IF p_task_key IS NULL OR p_project_id IS NULL OR p_source_key IS NULL OR p_user_event_id IS NULL
       OR p_action IS NULL OR p_action NOT IN ('grant', 'revoke')
       OR p_expected_content_digest IS NULL OR p_expected_content_digest !~ '^[0-9a-f]{64}$'
       OR p_expected_descriptor_digest IS NULL OR p_expected_descriptor_digest !~ '^[0-9a-f]{64}$' THEN
        RAISE EXCEPTION 'source trust refused: invalid_request' USING ERRCODE = 'P0001';
    END IF;

    SELECT id, project_id INTO t FROM vres.tasks WHERE task_key = p_task_key;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'source trust refused: unknown_task' USING ERRCODE = 'P0001';
    END IF;
    IF t.project_id IS DISTINCT FROM p_project_id THEN
        RAISE EXCEPTION 'source trust refused: project_mismatch' USING ERRCODE = 'P0001';
    END IF;

    SELECT id, project_id, status, source_type, origin, version INTO s
      FROM vres.sources WHERE source_key = p_source_key FOR UPDATE;
    IF NOT FOUND OR s.project_id IS DISTINCT FROM p_project_id THEN
        RAISE EXCEPTION 'source trust refused: unknown_source' USING ERRCODE = 'P0001';
    END IF;
    PERFORM pg_advisory_xact_lock(hashtextextended('source-trust:' || s.id::text, 0));

    subject := 'source_trust:' || p_action || ':' || p_project_id::text || ':' || p_source_key || ':'
               || p_expected_content_digest || ':' || p_expected_descriptor_digest;

    -- Exact replay: an existing (user_event_id, subject_key) row was validated when written.
    SELECT * INTO existing FROM vres.source_trust_events
     WHERE user_event_id = p_user_event_id AND subject_key = subject;
    IF FOUND THEN
        RETURN QUERY SELECT existing.event_key, existing.action, existing.subject_key, true;
        RETURN;
    END IF;

    IF p_action = 'grant' THEN
        IF s.status IS DISTINCT FROM 'active' THEN
            RAISE EXCEPTION 'source trust refused: source_not_active' USING ERRCODE = 'P0001';
        END IF;
        SELECT * INTO d FROM vres.source_trust_digests(s.id);
        IF d.chunk_count = 0 THEN
            RAISE EXCEPTION 'source trust refused: no_content' USING ERRCODE = 'P0001';
        END IF;
        IF d.content_digest IS DISTINCT FROM p_expected_content_digest
           OR d.descriptor_digest IS DISTINCT FROM p_expected_descriptor_digest THEN
            RAISE EXCEPTION 'source trust refused: digest_mismatch' USING ERRCODE = 'P0001';
        END IF;
    END IF;

    -- Authority anchor: genuine typed user instruction of this task, newest user-authority event by ID.
    SELECT id, task_id, event_type, actor, payload INTO ev FROM vres.task_events WHERE id = p_user_event_id;
    IF NOT FOUND OR ev.task_id IS DISTINCT FROM t.id OR ev.event_type IS DISTINCT FROM 'USER_INSTRUCTION'
       OR ev.actor IS DISTINCT FROM 'user' OR ev.payload ->> 'source' IS DISTINCT FROM 'user_prompt' THEN
        RAISE EXCEPTION 'source trust refused: anchor_invalid' USING ERRCODE = 'P0001';
    END IF;
    SELECT max(id) INTO newest_id FROM vres.task_events
     WHERE task_id = t.id AND event_type IN ('USER_INSTRUCTION', 'USER_CONTROL');
    IF newest_id IS DISTINCT FROM ev.id THEN
        RAISE EXCEPTION 'source trust refused: anchor_stale' USING ERRCODE = 'P0001';
    END IF;
    IF ev.payload ->> 'text' IS NULL
       OR btrim(ev.payload ->> 'text', E' \t\r\n') IS DISTINCT FROM 'I authorize ' || subject THEN
        RAISE EXCEPTION 'source trust refused: not_authorized' USING ERRCODE = 'P0001';
    END IF;

    idem := encode(sha256(convert_to(p_user_event_id::text || ':' || subject, 'UTF8')), 'hex');
    new_key := 'STE-' || replace(gen_random_uuid()::text, '-', '');

    IF p_action = 'grant' THEN
        -- Same identity already actively granted: return it (no duplicate).
        SELECT g1.* INTO g FROM vres.source_trust_events g1
         WHERE g1.source_id = s.id AND g1.action = 'grant'
           AND g1.content_digest = p_expected_content_digest
           AND g1.descriptor_digest = p_expected_descriptor_digest
           AND NOT EXISTS (SELECT 1 FROM vres.source_trust_events r
                            WHERE r.action = 'revoke' AND r.supersedes_event_id = g1.id)
         ORDER BY g1.id DESC LIMIT 1;
        IF FOUND THEN
            RETURN QUERY SELECT g.event_key, g.action, g.subject_key, true;
            RETURN;
        END IF;
        INSERT INTO vres.source_trust_events(
            event_key, project_id, source_id, source_key, action, basis, policy_version, policy_digest,
            content_digest, descriptor_digest, subject_key, task_id, user_event_id, supersedes_event_id,
            idempotency_key)
        VALUES (new_key, p_project_id, s.id, p_source_key, 'grant', 'user_approval', '176.g7.v1',
                'f20b037b00d0a5711666fd6c1d98538101708d99e7f6f32cf5a490ff6b96cf03',
                p_expected_content_digest, p_expected_descriptor_digest, subject, t.id, ev.id, NULL, idem);
    ELSE
        -- Revoke matches the active grant row's recorded digests, not the source's current state.
        SELECT g1.* INTO g FROM vres.source_trust_events g1
         WHERE g1.source_id = s.id AND g1.action = 'grant'
           AND g1.content_digest = p_expected_content_digest
           AND g1.descriptor_digest = p_expected_descriptor_digest
           AND NOT EXISTS (SELECT 1 FROM vres.source_trust_events r
                            WHERE r.action = 'revoke' AND r.supersedes_event_id = g1.id)
         ORDER BY g1.id DESC LIMIT 1;
        IF NOT FOUND THEN
            RAISE EXCEPTION 'source trust refused: no_active_grant' USING ERRCODE = 'P0001';
        END IF;
        INSERT INTO vres.source_trust_events(
            event_key, project_id, source_id, source_key, action, basis, policy_version, policy_digest,
            content_digest, descriptor_digest, subject_key, task_id, user_event_id, supersedes_event_id,
            idempotency_key)
        VALUES (new_key, p_project_id, s.id, p_source_key, 'revoke', 'user_approval', '176.g7.v1',
                'f20b037b00d0a5711666fd6c1d98538101708d99e7f6f32cf5a490ff6b96cf03',
                p_expected_content_digest, p_expected_descriptor_digest, subject, t.id, ev.id, g.id, idem);
    END IF;
    RETURN QUERY SELECT new_key, p_action, subject, false;
END
$vres_g7$;

-- Privileges: nobody but the owner by default; activate_boundary re-applies the final runtime grants.
-- Default privileges may have granted the runtime role table/sequence/function rights at creation: revoke every
-- non-owner grant explicitly (same sweep as migration 040).
REVOKE ALL ON TABLE vres.source_trust_events FROM PUBLIC;
REVOKE ALL ON SEQUENCE vres.source_trust_events_id_seq FROM PUBLIC;
REVOKE ALL ON FUNCTION vres.protect_source_trust_immutability() FROM PUBLIC;
REVOKE ALL ON FUNCTION vres.require_source_trust_owner_insert() FROM PUBLIC;
REVOKE ALL ON FUNCTION vres.source_trust_digests(bigint) FROM PUBLIC;
REVOKE ALL ON FUNCTION vres.record_source_trust_decision(text,bigint,text,text,bigint,text,text) FROM PUBLIC;

DO $vres_g7$
DECLARE
    g record;
BEGIN
    FOR g IN
        SELECT DISTINCT format('TABLE %s', c.oid::regclass) AS obj, a.grantee
          FROM pg_class c, aclexplode(c.relacl) a
         WHERE c.oid IN ('vres.source_trust_events'::regclass, 'vres.source_trust_events_id_seq'::regclass)
           AND a.grantee <> c.relowner AND a.grantee <> 0
        UNION
        SELECT DISTINCT format('FUNCTION %s', p.oid::regprocedure), a.grantee
          FROM pg_proc p, aclexplode(p.proacl) a
         WHERE p.oid IN ('vres.protect_source_trust_immutability()'::regprocedure,
                         'vres.require_source_trust_owner_insert()'::regprocedure,
                         'vres.source_trust_digests(bigint)'::regprocedure,
                         'vres.record_source_trust_decision(text,bigint,text,text,bigint,text,text)'::regprocedure)
           AND a.grantee <> p.proowner AND a.grantee <> 0
    LOOP
        EXECUTE format('REVOKE ALL ON %s FROM %I', g.obj, g.grantee::regrole::text);
    END LOOP;
END
$vres_g7$;
