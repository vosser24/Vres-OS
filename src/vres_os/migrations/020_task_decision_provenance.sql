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
