-- W4 R13F: SOURCE ONLY / UNREVIEWED / NOT_APPLIED.
-- Prospective ORIGINAL task-table hard hold. This does not clear the
-- LIVE_SCHEMA_048_INCIDENT or authorize SQL, migrations, release or Windows UAT.
-- Preserve existing 018 task states, 028 passed-validation guard, 036 routed
-- completion, 042-047 provenance and cancellation source.
--
-- A model/runtime connection currently holds broad table UPDATE privileges.
-- It must not be able to bypass the R13D Python cancellation denial with a
-- direct UPDATE to 'cancelled'. Nor may broad DELETE remove original task
-- state, events or checkpoints. This SQL is an additional defense only;
-- existing broad privileges on OTHER tables remain unreviewed and OPEN.
--
-- This intentionally holds even a writer-initiated cancellation until
-- independent operator-only cancellation design and a reviewed later migration.
-- Reusing the dormant 044/047 writer helper does not lift this hold.

CREATE OR REPLACE FUNCTION vres.refuse_unapproved_task_terminal_mutation()
RETURNS trigger
LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = pg_catalog, vres, pg_temp
AS $vres_r13f_terminal_hold$
BEGIN
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'VRES_W4_HELD_TASK_DELETE: original task history cannot be deleted'
            USING ERRCODE = '42501';
    END IF;

    -- Explicitly reject *all* unapproved paths into cancelled, including
    -- direct SQL UPDATE, writer functions and future model-facing callers.
    IF NEW.status = 'cancelled' AND OLD.status IS DISTINCT FROM 'cancelled' THEN
        RAISE EXCEPTION 'VRES_W4_HELD_TASK_CANCEL: operator authority is not granted'
            USING ERRCODE = '42501';
    END IF;

    -- Do not permit terminal task reopening through direct runtime UPDATE.
    -- Nonterminal active/waiting_user/blocked and governed completion remain
    -- subject to their original lifecycle and validation guards.
    IF OLD.status IN ('completed', 'cancelled')
       AND NEW.status IS DISTINCT FROM OLD.status THEN
        RAISE EXCEPTION 'VRES_W4_HELD_TASK_REOPEN: terminal task transition is not authorized'
            USING ERRCODE = '42501';
    END IF;

    RETURN NEW;
END;
$vres_r13f_terminal_hold$;

REVOKE ALL ON FUNCTION vres.refuse_unapproved_task_terminal_mutation() FROM PUBLIC;
DROP TRIGGER IF EXISTS trg_original_task_terminal_hold ON vres.tasks;
CREATE TRIGGER trg_original_task_terminal_hold
BEFORE UPDATE OF status OR DELETE ON vres.tasks
FOR EACH ROW EXECUTE FUNCTION vres.refuse_unapproved_task_terminal_mutation();
