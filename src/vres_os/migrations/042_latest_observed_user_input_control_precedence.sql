-- W4 R-10: original trusted-writer cancellation precedence, source authored NOT_RUN.
-- Migration 032 stays immutable; the existing instruction-only reader remains
-- unchanged for callers that truly need substantive instruction filtering.
-- This additional read-only function gives task cancellation the LATEST
-- observation of ANY kind so later controls supersede earlier instructions.
-- This migration must NOT be applied while PostgreSQL is held.
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
     ORDER BY o.observed_at DESC,o.id DESC
     LIMIT 1;
END;
$$;

REVOKE ALL ON FUNCTION vres.latest_observed_user_input(bigint,text) FROM PUBLIC;
