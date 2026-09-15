-- Structured decision provenance without conflating descriptive decisions with approvals.

CREATE TABLE IF NOT EXISTS vres.task_decisions (
    id bigserial PRIMARY KEY,
    decision_key text NOT NULL UNIQUE,
    task_id bigint NOT NULL REFERENCES vres.tasks(id) ON DELETE CASCADE,
    text text NOT NULL,
    rationale text,
    status text NOT NULL DEFAULT 'active' CHECK (status IN ('active','superseded','retired')),
    source_kind text NOT NULL CHECK (source_kind IN ('chairman','user_instruction','legacy_unstructured')),
    source_event_id bigint REFERENCES vres.task_events(id) ON DELETE SET NULL,
    source_session_id text,
    decided_at timestamptz,
    recorded_at timestamptz NOT NULL DEFAULT now(),
    supersedes_decision_id bigint REFERENCES vres.task_decisions(id) ON DELETE SET NULL,
    superseded_at timestamptz,
    retired_at timestamptz,
    retirement_reason text,
    CONSTRAINT task_decisions_time_contract CHECK (
        (source_kind='legacy_unstructured' AND decided_at IS NULL)
        OR (source_kind<>'legacy_unstructured' AND decided_at IS NOT NULL)
    )
);
CREATE INDEX IF NOT EXISTS idx_task_decisions_task_status
    ON vres.task_decisions(task_id,status,id);
CREATE INDEX IF NOT EXISTS idx_task_decisions_source_event
    ON vres.task_decisions(source_event_id) WHERE source_event_id IS NOT NULL;

-- Preserve existing first-class decision strings without inventing rationale, source event, or decision time.
INSERT INTO vres.task_decisions(
    decision_key,task_id,text,rationale,status,source_kind,source_event_id,source_session_id,decided_at
)
SELECT
    'DEC-LEGACY-' || s.task_id::text || '-' || lpad(d.ordinality::text,3,'0'),
    s.task_id,
    d.value,
    NULL,
    'active',
    'legacy_unstructured',
    NULL,
    NULL,
    NULL
FROM vres.task_state s
CROSS JOIN LATERAL jsonb_array_elements_text(s.decisions) WITH ORDINALITY AS d(value, ordinality)
ON CONFLICT(decision_key) DO NOTHING;

-- Keep task_state.decisions as the compatibility projection of active ledger rows.
CREATE OR REPLACE FUNCTION vres.enforce_task_decision_projection()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    expected jsonb;
BEGIN
    SELECT COALESCE(jsonb_agg(to_jsonb(d.text) ORDER BY d.id), '[]'::jsonb)
      INTO expected
      FROM vres.task_decisions d
     WHERE d.task_id=NEW.task_id AND d.status='active';
    IF NEW.decisions IS DISTINCT FROM expected THEN
        RAISE EXCEPTION 'task_state.decisions is managed by structured task decision provenance';
    END IF;
    RETURN NEW;
END
$$;

DROP TRIGGER IF EXISTS trg_enforce_task_decision_projection ON vres.task_state;
CREATE TRIGGER trg_enforce_task_decision_projection
BEFORE UPDATE OF decisions ON vres.task_state
FOR EACH ROW
EXECUTE FUNCTION vres.enforce_task_decision_projection();

-- Every checkpoint snapshots exactly which immutable decision records were active at that point.
CREATE TABLE IF NOT EXISTS vres.checkpoint_decisions (
    checkpoint_id bigint NOT NULL REFERENCES vres.checkpoints(id) ON DELETE CASCADE,
    decision_id bigint NOT NULL REFERENCES vres.task_decisions(id) ON DELETE RESTRICT,
    position integer NOT NULL CHECK (position >= 0),
    PRIMARY KEY(checkpoint_id,decision_id),
    UNIQUE(checkpoint_id,position)
);
CREATE INDEX IF NOT EXISTS idx_checkpoint_decisions_decision
    ON vres.checkpoint_decisions(decision_id,checkpoint_id);

CREATE OR REPLACE FUNCTION vres.capture_checkpoint_decisions()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    plain jsonb;
    records jsonb;
BEGIN
    INSERT INTO vres.checkpoint_decisions(checkpoint_id,decision_id,position)
    SELECT NEW.id,d.id,(row_number() OVER (ORDER BY d.id)-1)::integer
      FROM vres.task_decisions d
     WHERE d.task_id=NEW.task_id AND d.status='active'
     ORDER BY d.id;

    SELECT
        COALESCE(jsonb_agg(to_jsonb(d.text) ORDER BY d.id), '[]'::jsonb),
        COALESCE(
            jsonb_agg(
                jsonb_build_object(
                    'decision_key',d.decision_key,
                    'text',d.text,
                    'rationale',d.rationale,
                    'source_kind',d.source_kind,
                    'source_event_id',d.source_event_id,
                    'source_session_id',d.source_session_id,
                    'decided_at',d.decided_at,
                    'recorded_at',d.recorded_at
                ) ORDER BY d.id
            ),
            '[]'::jsonb
        )
      INTO plain,records
      FROM vres.task_decisions d
     WHERE d.task_id=NEW.task_id AND d.status='active';

    UPDATE vres.checkpoints
       SET context=COALESCE(context,'{}'::jsonb)
                   || jsonb_build_object('decisions',plain,'decision_records',records)
     WHERE id=NEW.id;
    RETURN NEW;
END
$$;

DROP TRIGGER IF EXISTS trg_capture_checkpoint_decisions ON vres.checkpoints;
CREATE TRIGGER trg_capture_checkpoint_decisions
AFTER INSERT ON vres.checkpoints
FOR EACH ROW
EXECUTE FUNCTION vres.capture_checkpoint_decisions();
