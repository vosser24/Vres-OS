-- Harden structured decision provenance after physical Windows acceptance.
-- Provenance/identity fields are immutable after insert. Only the service's intended
-- active -> superseded / active -> retired lifecycle mutations remain legal.

ALTER TABLE vres.task_decisions
    DROP CONSTRAINT IF EXISTS task_decisions_lifecycle_contract;
ALTER TABLE vres.task_decisions
    ADD CONSTRAINT task_decisions_lifecycle_contract CHECK (
        (status='active' AND superseded_at IS NULL AND retired_at IS NULL AND retirement_reason IS NULL)
        OR
        (status='superseded' AND superseded_at IS NOT NULL AND retired_at IS NULL AND retirement_reason IS NULL)
        OR
        (status='retired' AND superseded_at IS NULL AND retired_at IS NOT NULL
            AND retirement_reason IS NOT NULL AND btrim(retirement_reason) <> '')
    );

CREATE OR REPLACE FUNCTION vres.protect_task_decision_update()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.decision_key IS DISTINCT FROM OLD.decision_key
       OR NEW.task_id IS DISTINCT FROM OLD.task_id
       OR NEW.text IS DISTINCT FROM OLD.text
       OR NEW.rationale IS DISTINCT FROM OLD.rationale
       OR NEW.source_kind IS DISTINCT FROM OLD.source_kind
       OR NEW.source_event_id IS DISTINCT FROM OLD.source_event_id
       OR NEW.source_session_id IS DISTINCT FROM OLD.source_session_id
       OR NEW.decided_at IS DISTINCT FROM OLD.decided_at
       OR NEW.recorded_at IS DISTINCT FROM OLD.recorded_at
       OR NEW.supersedes_decision_id IS DISTINCT FROM OLD.supersedes_decision_id THEN
        RAISE EXCEPTION 'task decision provenance fields are immutable after insert';
    END IF;

    IF OLD.status <> 'active' THEN
        RAISE EXCEPTION 'terminal task decision history is immutable';
    END IF;

    IF NEW.status = 'superseded' THEN
        IF NEW.superseded_at IS NULL
           OR NEW.retired_at IS NOT NULL
           OR NEW.retirement_reason IS NOT NULL THEN
            RAISE EXCEPTION 'superseded decision requires superseded_at only';
        END IF;
        RETURN NEW;
    END IF;

    IF NEW.status = 'retired' THEN
        IF NEW.retired_at IS NULL
           OR NEW.retirement_reason IS NULL
           OR btrim(NEW.retirement_reason) = ''
           OR NEW.superseded_at IS NOT NULL THEN
            RAISE EXCEPTION 'retired decision requires retired_at and retirement_reason only';
        END IF;
        RETURN NEW;
    END IF;

    RAISE EXCEPTION 'task decision update must be active -> superseded or active -> retired';
END
$$;

DROP TRIGGER IF EXISTS trg_protect_task_decision_update ON vres.task_decisions;
CREATE TRIGGER trg_protect_task_decision_update
BEFORE UPDATE ON vres.task_decisions
FOR EACH ROW
EXECUTE FUNCTION vres.protect_task_decision_update();

CREATE OR REPLACE FUNCTION vres.protect_decision_ledger_delete()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF current_setting('vres.allow_decision_ledger_delete', true) = 'on' THEN
        RETURN OLD;
    END IF;
    RAISE EXCEPTION 'decision provenance history cannot be deleted';
END
$$;

DROP TRIGGER IF EXISTS trg_protect_task_decision_delete ON vres.task_decisions;
CREATE TRIGGER trg_protect_task_decision_delete
BEFORE DELETE ON vres.task_decisions
FOR EACH ROW
EXECUTE FUNCTION vres.protect_decision_ledger_delete();

CREATE OR REPLACE FUNCTION vres.protect_checkpoint_decision_history()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'DELETE' AND current_setting('vres.allow_decision_ledger_delete', true) = 'on' THEN
        RETURN OLD;
    END IF;
    RAISE EXCEPTION 'checkpoint decision snapshots are immutable';
END
$$;

DROP TRIGGER IF EXISTS trg_protect_checkpoint_decision_update ON vres.checkpoint_decisions;
CREATE TRIGGER trg_protect_checkpoint_decision_update
BEFORE UPDATE ON vres.checkpoint_decisions
FOR EACH ROW
EXECUTE FUNCTION vres.protect_checkpoint_decision_history();

DROP TRIGGER IF EXISTS trg_protect_checkpoint_decision_delete ON vres.checkpoint_decisions;
CREATE TRIGGER trg_protect_checkpoint_decision_delete
BEFORE DELETE ON vres.checkpoint_decisions
FOR EACH ROW
EXECUTE FUNCTION vres.protect_checkpoint_decision_history();
