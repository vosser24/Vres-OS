CREATE TABLE IF NOT EXISTS vres.source_locations (
    id bigserial PRIMARY KEY,
    source_id bigint NOT NULL REFERENCES vres.sources(id) ON DELETE CASCADE,
    project_id bigint REFERENCES vres.projects(id) ON DELETE SET NULL,
    path_or_uri text NOT NULL,
    first_seen_at timestamptz NOT NULL DEFAULT now(),
    last_seen_at timestamptz NOT NULL DEFAULT now(),
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    UNIQUE(source_id, path_or_uri)
);
CREATE INDEX IF NOT EXISTS idx_source_locations_project ON vres.source_locations(project_id,source_id);
