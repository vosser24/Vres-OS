CREATE OR REPLACE FUNCTION vres.protect_user_authority_event()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, vres
AS $$
DECLARE
    allowed name;
    touches_user_authority boolean;
BEGIN
    SELECT writer_role INTO allowed
      FROM vres.provenance_authority
     WHERE authority_key='user_event_writer';

    IF TG_OP = 'DELETE' THEN
        touches_user_authority := OLD.event_type IN ('USER_INSTRUCTION','USER_CONTROL');
        IF touches_user_authority AND (allowed IS NULL OR session_user <> allowed::text) THEN
            RAISE EXCEPTION 'user-authority task events require the trusted provenance writer role'
                USING ERRCODE='P0001';
        END IF;
        RETURN OLD;
    END IF;

    touches_user_authority := NEW.event_type IN ('USER_INSTRUCTION','USER_CONTROL');
    IF TG_OP = 'UPDATE' THEN
        touches_user_authority := touches_user_authority
            OR OLD.event_type IN ('USER_INSTRUCTION','USER_CONTROL');
    END IF;

    IF touches_user_authority AND (allowed IS NULL OR session_user <> allowed::text) THEN
        RAISE EXCEPTION 'user-authority task events require the trusted provenance writer role'
            USING ERRCODE='P0001';
    END IF;
    IF NEW.event_type IN ('USER_INSTRUCTION','USER_CONTROL') AND NEW.actor <> 'user' THEN
        RAISE EXCEPTION 'user-authority task events must have actor=user'
            USING ERRCODE='P0001';
    END IF;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_protect_user_authority_event ON vres.task_events;
CREATE TRIGGER trg_protect_user_authority_event
BEFORE INSERT OR UPDATE OR DELETE ON vres.task_events
FOR EACH ROW EXECUTE FUNCTION vres.protect_user_authority_event();
