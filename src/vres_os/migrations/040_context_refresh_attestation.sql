-- #176 E4 addendum (approved 2026-10-02): protected, host-correlated context-refresh attestations.
-- Replaces the sessions.metadata ack attestation. Only the provenance writer role mints (hook side, through
-- issue_context_refresh_attestation); the runtime role consumes only through consume_context_refresh_attestation;
-- a context_refreshed ledger row is accepted only with an 'ok' consumption in the same transaction. Only a SHA-256
-- of the single-use nonce is stored. Additive and idempotent; no existing migration, row or trigger is changed.

CREATE TABLE IF NOT EXISTS vres.context_refresh_attestations (
    id bigserial PRIMARY KEY,
    project_id bigint NOT NULL REFERENCES vres.projects(id) ON DELETE CASCADE,
    provider_session_id text NOT NULL CHECK (char_length(provider_session_id) BETWEEN 1 AND 300),
    session_key text NOT NULL CHECK (char_length(session_key) BETWEEN 1 AND 300),
    contamination_event_id bigint NOT NULL,
    contamination_event_key text NOT NULL CHECK (contamination_event_key ~ '^LCE-[0-9a-f]{32}$'),
    tool_use_id text NOT NULL CHECK (char_length(tool_use_id) BETWEEN 1 AND 300),
    nonce_sha256 text NOT NULL UNIQUE CHECK (nonce_sha256 ~ '^[0-9a-f]{64}$'),
    issued_at timestamptz NOT NULL,
    expires_at timestamptz NOT NULL,
    consumed_at timestamptz,
    consumed_xid xid8,
    outcome text CHECK (outcome IN ('ok','foreign_project','key_mismatch','expired','closed_session','stale')),
    refresh_event_key text UNIQUE,
    CONSTRAINT ck_context_refresh_attestation_window CHECK (
        expires_at > issued_at AND expires_at <= issued_at + interval '120 seconds'),
    CONSTRAINT ck_context_refresh_attestation_consumed CHECK (
        (consumed_at IS NULL AND consumed_xid IS NULL AND outcome IS NULL)
        OR (consumed_at IS NOT NULL AND consumed_xid IS NOT NULL AND outcome IS NOT NULL)),
    CONSTRAINT ck_context_refresh_attestation_refresh CHECK (refresh_event_key IS NULL OR outcome = 'ok'),
    CONSTRAINT uq_context_refresh_attestation_invocation UNIQUE (provider_session_id, tool_use_id)
);

CREATE INDEX IF NOT EXISTS idx_context_refresh_attestation_session
    ON vres.context_refresh_attestations(project_id, session_key, id DESC);

-- Hook side: mint for exactly the latest contamination of exactly this open Claude host session.
CREATE OR REPLACE FUNCTION vres.issue_context_refresh_attestation(
    p_provider_session_id text, p_contamination_event_key text, p_tool_use_id text, p_nonce_sha256 text)
RETURNS boolean
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, vres
AS $vres_e40$
DECLARE
    allowed name;
    target record;
    n integer;
    latest_id bigint;
    new_id bigint;
    now_ts timestamptz := clock_timestamp();
BEGIN
    SELECT writer_role INTO allowed FROM vres.provenance_authority WHERE authority_key = 'user_event_writer';
    IF allowed IS NULL OR session_user <> allowed::text THEN
        RAISE EXCEPTION 'context refresh attestations may be minted only by the trusted provenance writer role'
            USING ERRCODE = 'P0001';
    END IF;
    IF p_provider_session_id IS NULL OR char_length(p_provider_session_id) NOT BETWEEN 1 AND 300
       OR p_tool_use_id IS NULL OR char_length(p_tool_use_id) NOT BETWEEN 1 AND 300
       OR p_contamination_event_key IS NULL OR p_contamination_event_key !~ '^LCE-[0-9a-f]{32}$'
       OR p_nonce_sha256 IS NULL OR p_nonce_sha256 !~ '^[0-9a-f]{64}$' THEN
        RETURN false;
    END IF;
    SELECT count(*) INTO n
      FROM vres.experience_lifecycle_events e
      JOIN vres.sessions s ON s.project_id = e.project_id AND s.session_key = e.session_key
     WHERE e.event_key = p_contamination_event_key AND e.action = 'context_contaminated'
       AND e.target_kind = 'session' AND s.provider = 'claude'
       AND s.provider_session_id = p_provider_session_id AND s.ended_at IS NULL;
    IF n <> 1 THEN
        RETURN false;
    END IF;
    SELECT e.id, e.project_id, e.session_key INTO target
      FROM vres.experience_lifecycle_events e
      JOIN vres.sessions s ON s.project_id = e.project_id AND s.session_key = e.session_key
     WHERE e.event_key = p_contamination_event_key AND e.action = 'context_contaminated'
       AND e.target_kind = 'session' AND s.provider = 'claude'
       AND s.provider_session_id = p_provider_session_id AND s.ended_at IS NULL;
    SELECT max(id) INTO latest_id FROM vres.experience_lifecycle_events
     WHERE project_id = target.project_id AND target_kind = 'session' AND session_key = target.session_key
       AND action = 'context_contaminated';
    IF latest_id IS DISTINCT FROM target.id THEN
        RETURN false;
    END IF;
    INSERT INTO vres.context_refresh_attestations(
        project_id, provider_session_id, session_key, contamination_event_id, contamination_event_key,
        tool_use_id, nonce_sha256, issued_at, expires_at)
    VALUES (target.project_id, p_provider_session_id, target.session_key, target.id, p_contamination_event_key,
            p_tool_use_id, p_nonce_sha256, now_ts, now_ts + interval '120 seconds')
    ON CONFLICT DO NOTHING
    RETURNING id INTO new_id;
    RETURN new_id IS NOT NULL;
END
$vres_e40$;

-- Tool side: single-use consumption by (nonce hash, host tool_use_id); every presented attestation is burned.
CREATE OR REPLACE FUNCTION vres.consume_context_refresh_attestation(
    p_project_id bigint, p_tool_use_id text, p_nonce_sha256 text, p_contamination_event_key text)
RETURNS TABLE(attestation_outcome text, attested_session_key text)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, vres
AS $vres_e40$
DECLARE
    a vres.context_refresh_attestations%ROWTYPE;
    verdict text;
    now_ts timestamptz := clock_timestamp();
    latest_id bigint;
BEGIN
    IF p_tool_use_id IS NULL OR p_nonce_sha256 IS NULL OR p_nonce_sha256 !~ '^[0-9a-f]{64}$' THEN
        RETURN QUERY SELECT 'not_attested'::text, NULL::text;
        RETURN;
    END IF;
    SELECT * INTO a FROM vres.context_refresh_attestations
     WHERE nonce_sha256 = p_nonce_sha256 AND tool_use_id = p_tool_use_id
     FOR UPDATE;
    IF NOT FOUND THEN
        RETURN QUERY SELECT 'not_attested'::text, NULL::text;
        RETURN;
    END IF;
    IF a.consumed_at IS NOT NULL THEN
        RETURN QUERY SELECT 'consumed'::text, NULL::text;
        RETURN;
    END IF;
    SELECT max(id) INTO latest_id FROM vres.experience_lifecycle_events
     WHERE project_id = a.project_id AND target_kind = 'session' AND session_key = a.session_key
       AND action = 'context_contaminated';
    verdict := CASE
        WHEN p_project_id IS DISTINCT FROM a.project_id THEN 'foreign_project'
        WHEN p_contamination_event_key IS DISTINCT FROM a.contamination_event_key THEN 'key_mismatch'
        WHEN now_ts >= a.expires_at OR now_ts < a.issued_at THEN 'expired'
        WHEN NOT EXISTS (SELECT 1 FROM vres.sessions s
                          WHERE s.project_id = a.project_id AND s.session_key = a.session_key
                            AND s.provider = 'claude' AND s.provider_session_id = a.provider_session_id
                            AND s.ended_at IS NULL) THEN 'closed_session'
        WHEN latest_id IS DISTINCT FROM a.contamination_event_id THEN 'stale'
        ELSE 'ok' END;
    UPDATE vres.context_refresh_attestations
       SET consumed_at = now_ts, consumed_xid = pg_current_xact_id(), outcome = verdict
     WHERE id = a.id;
    RETURN QUERY SELECT verdict, CASE WHEN verdict = 'ok' THEN a.session_key END;
END
$vres_e40$;

-- Ledger side: a context_refreshed row needs one unused 'ok' consumption from this same transaction.
CREATE OR REPLACE FUNCTION vres.require_attested_context_refresh()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, vres
AS $vres_e40$
DECLARE
    used_id bigint;
BEGIN
    IF NEW.action IS DISTINCT FROM 'context_refreshed' THEN
        RETURN NULL;
    END IF;
    SELECT id INTO used_id FROM vres.context_refresh_attestations
     WHERE outcome = 'ok' AND consumed_xid = pg_current_xact_id() AND refresh_event_key IS NULL
       AND project_id = NEW.project_id AND session_key = NEW.session_key
       AND contamination_event_key = NEW.detail->>'acknowledged_event_key'
     ORDER BY id
     LIMIT 1
     FOR UPDATE;
    IF used_id IS NULL THEN
        RAISE EXCEPTION 'context_refreshed requires a consumed host-correlated attestation in this transaction'
            USING ERRCODE = 'P0001';
    END IF;
    UPDATE vres.context_refresh_attestations SET refresh_event_key = NEW.event_key WHERE id = used_id;
    RETURN NULL;
END
$vres_e40$;

-- AFTER (not BEFORE) so the ledger's own NOT NULL/CHECK/FK/unique rules still report first; raising here still
-- aborts the insert.
DROP TRIGGER IF EXISTS trg_require_attested_context_refresh ON vres.experience_lifecycle_events;
CREATE TRIGGER trg_require_attested_context_refresh
AFTER INSERT ON vres.experience_lifecycle_events
FOR EACH ROW EXECUTE FUNCTION vres.require_attested_context_refresh();

-- Privileges: nobody but the owner by default (activate_boundary then grants mint to the writer and consume to the
-- runtime). Default privileges may have granted the runtime role table/sequence/function rights at creation;
-- revoke every non-owner grant explicitly.
REVOKE ALL ON TABLE vres.context_refresh_attestations FROM PUBLIC;
REVOKE ALL ON SEQUENCE vres.context_refresh_attestations_id_seq FROM PUBLIC;
REVOKE ALL ON FUNCTION vres.issue_context_refresh_attestation(text,text,text,text) FROM PUBLIC;
REVOKE ALL ON FUNCTION vres.consume_context_refresh_attestation(bigint,text,text,text) FROM PUBLIC;
REVOKE ALL ON FUNCTION vres.require_attested_context_refresh() FROM PUBLIC;

DO $vres_e40$
DECLARE
    g record;
BEGIN
    FOR g IN
        SELECT DISTINCT format('TABLE %s', c.oid::regclass) AS obj, a.grantee
          FROM pg_class c, aclexplode(c.relacl) a
         WHERE c.oid IN ('vres.context_refresh_attestations'::regclass,
                         'vres.context_refresh_attestations_id_seq'::regclass)
           AND a.grantee <> c.relowner AND a.grantee <> 0
        UNION
        SELECT DISTINCT format('FUNCTION %s', p.oid::regprocedure), a.grantee
          FROM pg_proc p, aclexplode(p.proacl) a
         WHERE p.oid IN ('vres.issue_context_refresh_attestation(text,text,text,text)'::regprocedure,
                         'vres.consume_context_refresh_attestation(bigint,text,text,text)'::regprocedure,
                         'vres.require_attested_context_refresh()'::regprocedure)
           AND a.grantee <> p.proowner AND a.grantee <> 0
    LOOP
        EXECUTE format('REVOKE ALL ON %s FROM %I', g.obj, pg_get_userbyid(g.grantee));
    END LOOP;
END
$vres_e40$;
