-- Separate authority for creating a company-wide optimization candidate from
-- the later authority to make an attested candidate globally preferred.

ALTER TABLE vres.procedure_versions
    ADD COLUMN IF NOT EXISTS scope_approval_event_id bigint
    REFERENCES vres.approval_events(id) ON DELETE RESTRICT;

ALTER TABLE vres.optimization_candidates
    ADD COLUMN IF NOT EXISTS candidate_approval_event_id bigint
    REFERENCES vres.approval_events(id) ON DELETE RESTRICT;

ALTER TABLE vres.optimization_candidates
    ADD COLUMN IF NOT EXISTS promotion_approval_event_id bigint
    REFERENCES vres.approval_events(id) ON DELETE RESTRICT;

ALTER TABLE vres.optimization_candidates
    DROP CONSTRAINT IF EXISTS optimization_candidates_decision_check;
ALTER TABLE vres.optimization_candidates
    ADD CONSTRAINT optimization_candidates_decision_check
    CHECK (
        decision IN (
            'pending',
            'auto_promoted',
            'company_promoted',
            'rejected',
            'requires_user',
            'user_promoted',
            'user_rejected'
        )
    );

CREATE INDEX IF NOT EXISTS idx_optimization_candidate_approvals
    ON vres.optimization_candidates(candidate_approval_event_id,promotion_approval_event_id);
