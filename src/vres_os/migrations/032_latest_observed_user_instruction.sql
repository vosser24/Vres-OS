-- Expose the latest trusted user observation through the provenance-writer boundary.
-- The writer role remains denied direct table access; this SECURITY DEFINER function
-- returns only the bounded fields needed to authorize same-session cancellation.

CREATE OR REPLACE FUNCTION vres.latest_observed_user_instruction(
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
    SELECT o.id,
           o.text,
           o.source,
           o.kind,
           o.observed_at,
           o.committed_at,
           o.committed_event_id,
           t.task_key
      FROM vres.user_input_observations o
      LEFT JOIN vres.tasks t ON t.id=o.committed_task_id
     WHERE o.project_id=p_project_id
       AND o.provider_session_id=p_provider_session_id
       AND o.kind='instruction'
     ORDER BY o.observed_at DESC,o.id DESC
     LIMIT 1;
END;
$$;

REVOKE ALL ON FUNCTION vres.latest_observed_user_instruction(bigint,text) FROM PUBLIC;
