-- Preserve explicit provenance for newly authorized company-wide writes.
-- Existing global seed rows are grandfathered and remain readable; new service writes require this approval.

ALTER TABLE vres.sources
    ADD COLUMN IF NOT EXISTS scope_approval_event_id bigint
    REFERENCES vres.approval_events(id) ON DELETE RESTRICT;

ALTER TABLE vres.knowledge_items
    ADD COLUMN IF NOT EXISTS scope_approval_event_id bigint
    REFERENCES vres.approval_events(id) ON DELETE RESTRICT;

ALTER TABLE vres.procedures
    ADD COLUMN IF NOT EXISTS scope_approval_event_id bigint
    REFERENCES vres.approval_events(id) ON DELETE RESTRICT;

ALTER TABLE vres.registry_objects
    ADD COLUMN IF NOT EXISTS scope_approval_event_id bigint
    REFERENCES vres.approval_events(id) ON DELETE RESTRICT;

ALTER TABLE vres.capabilities
    ADD COLUMN IF NOT EXISTS scope_approval_event_id bigint
    REFERENCES vres.approval_events(id) ON DELETE RESTRICT;

CREATE INDEX IF NOT EXISTS idx_approval_events_type_subject
    ON vres.approval_events(approval_type, subject_key);
