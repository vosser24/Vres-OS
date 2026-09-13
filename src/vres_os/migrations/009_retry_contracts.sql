-- Additive fingerprints; old baseline approvals must be renewed rather than falsely certified.
ALTER TABLE vres.procedure_versions ADD COLUMN contract_fingerprint text;
ALTER TABLE vres.refresh_runs ADD COLUMN project_id bigint REFERENCES vres.projects(id) ON DELETE RESTRICT;
