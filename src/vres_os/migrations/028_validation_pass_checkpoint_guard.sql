-- Prevent an accidental post-validation checkpoint from invalidating a fresh PASS.
-- Genuine post-review changes must first call the explicit validation invalidation path.

CREATE OR REPLACE FUNCTION vres.protect_passed_validation_state()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    explicit_invalidation boolean :=
        COALESCE(current_setting('vres.explicit_validation_invalidation', true), '') = 'on';
BEGIN
    IF OLD.validation_status = 'passed' AND NOT explicit_invalidation THEN
        IF NEW.validation_status IS DISTINCT FROM OLD.validation_status
           OR NEW.current_phase IS DISTINCT FROM OLD.current_phase
           OR NEW.current_step IS DISTINCT FROM OLD.current_step
           OR NEW.state_summary IS DISTINCT FROM OLD.state_summary
           OR NEW.next_action IS DISTINCT FROM OLD.next_action
           OR NEW.open_questions IS DISTINCT FROM OLD.open_questions
           OR NEW.assumptions IS DISTINCT FROM OLD.assumptions
           OR NEW.constraints IS DISTINCT FROM OLD.constraints
           OR NEW.decisions IS DISTINCT FROM OLD.decisions
           OR NEW.completed_work IS DISTINCT FROM OLD.completed_work
           OR NEW.pending_work IS DISTINCT FROM OLD.pending_work
           OR NEW.relevant_objects IS DISTINCT FROM OLD.relevant_objects
        THEN
            RAISE EXCEPTION
                'Fresh passed validation is protected; complete directly or call validation_invalidate before making post-review changes';
        END IF;
    END IF;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_protect_passed_validation_state ON vres.task_state;
CREATE TRIGGER trg_protect_passed_validation_state
BEFORE UPDATE ON vres.task_state
FOR EACH ROW
EXECUTE FUNCTION vres.protect_passed_validation_state();
