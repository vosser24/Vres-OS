CREATE TABLE IF NOT EXISTS vres.sessions (
    id bigserial PRIMARY KEY,
    session_key text NOT NULL UNIQUE,
    provider text NOT NULL,
    provider_session_id text,
    project_id bigint REFERENCES vres.projects(id) ON DELETE SET NULL,
    task_id bigint REFERENCES vres.tasks(id) ON DELETE SET NULL,
    started_at timestamptz NOT NULL DEFAULT now(),
    ended_at timestamptz,
    end_reason text,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb
);
CREATE INDEX IF NOT EXISTS idx_sessions_project_started ON vres.sessions(project_id, started_at DESC);

CREATE TABLE IF NOT EXISTS vres.artifacts (
    id bigserial PRIMARY KEY,
    artifact_key text NOT NULL UNIQUE,
    project_id bigint REFERENCES vres.projects(id) ON DELETE SET NULL,
    task_id bigint REFERENCES vres.tasks(id) ON DELETE SET NULL,
    source_id bigint REFERENCES vres.sources(id) ON DELETE SET NULL,
    artifact_type text NOT NULL,
    title text NOT NULL,
    canonical_path text,
    content_hash text,
    media_type text,
    status text NOT NULL DEFAULT 'active',
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_artifacts_hash ON vres.artifacts(content_hash);

CREATE TABLE IF NOT EXISTS vres.knowledge_chunks (
    id bigserial PRIMARY KEY,
    chunk_key text NOT NULL UNIQUE,
    source_id bigint REFERENCES vres.sources(id) ON DELETE CASCADE,
    knowledge_id bigint REFERENCES vres.knowledge_items(id) ON DELETE CASCADE,
    ordinal integer NOT NULL DEFAULT 0,
    section text,
    content text NOT NULL,
    content_hash text NOT NULL,
    token_estimate integer,
    embedding_model text,
    embedding_dimensions integer,
    embedding jsonb,
    embedded_at timestamptz,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    search_vector tsvector GENERATED ALWAYS AS (to_tsvector('simple', coalesce(content,''))) STORED,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(source_id, content_hash),
    UNIQUE(knowledge_id, content_hash)
);
CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_search ON vres.knowledge_chunks USING GIN(search_vector);
CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_source ON vres.knowledge_chunks(source_id, ordinal);

CREATE TABLE IF NOT EXISTS vres.embedding_jobs (
    id bigserial PRIMARY KEY,
    chunk_id bigint NOT NULL REFERENCES vres.knowledge_chunks(id) ON DELETE CASCADE,
    model text NOT NULL,
    status text NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','running','completed','failed','skipped')),
    attempts integer NOT NULL DEFAULT 0,
    error text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(chunk_id, model)
);
CREATE INDEX IF NOT EXISTS idx_embedding_jobs_pending ON vres.embedding_jobs(status, created_at);

-- If pgvector is installed on the PostgreSQL server, enable it. Vres remains fully
-- operational without it; embedding JSON is the portable fallback.
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_available_extensions WHERE name = 'vector') THEN
        BEGIN
            CREATE EXTENSION IF NOT EXISTS vector;
        EXCEPTION WHEN OTHERS THEN
            RAISE NOTICE 'pgvector is available but could not be enabled; JSON embedding fallback remains active: %', SQLERRM;
        END;
        IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector') AND NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema='vres' AND table_name='knowledge_chunks' AND column_name='embedding_vector'
        ) THEN
            EXECUTE 'ALTER TABLE vres.knowledge_chunks ADD COLUMN embedding_vector vector';
        END IF;
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS vres.preferences (
    id bigserial PRIMARY KEY,
    preference_key text NOT NULL UNIQUE,
    scope text NOT NULL DEFAULT 'user',
    statement text NOT NULL,
    status text NOT NULL DEFAULT 'active',
    source text,
    confidence numeric(5,4),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS vres.domain_manifests (
    id bigserial PRIMARY KEY,
    domain_key text NOT NULL UNIQUE,
    name text NOT NULL,
    owner_role text,
    review_interval_days integer NOT NULL DEFAULT 365,
    last_reviewed_at timestamptz,
    review_due_at timestamptz,
    knowledge_version text,
    critical_topics jsonb NOT NULL DEFAULT '[]'::jsonb,
    source_policy jsonb NOT NULL DEFAULT '[]'::jsonb,
    status text NOT NULL DEFAULT 'active',
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS vres.refresh_runs (
    id bigserial PRIMARY KEY,
    refresh_key text NOT NULL UNIQUE,
    domain_key text REFERENCES vres.domain_manifests(domain_key) ON DELETE SET NULL,
    trigger text NOT NULL,
    status text NOT NULL DEFAULT 'new',
    delta_summary jsonb NOT NULL DEFAULT '{}'::jsonb,
    started_at timestamptz NOT NULL DEFAULT now(),
    completed_at timestamptz,
    created_by text
);

ALTER TABLE vres.procedure_versions
    ADD COLUMN IF NOT EXISTS accepted_by text,
    ADD COLUMN IF NOT EXISTS accepted_at timestamptz;

ALTER TABLE vres.procedure_runs
    ADD COLUMN IF NOT EXISTS provider text,
    ADD COLUMN IF NOT EXISTS model text,
    ADD COLUMN IF NOT EXISTS effort text;

INSERT INTO vres.domain_manifests(domain_key,name,owner_role,review_interval_days,critical_topics,source_policy)
VALUES
 ('technology','Technology','cto',90,'["software engineering","AI tooling","security","architecture"]'::jsonb,'["official docs","standards","primary vendor docs","reputable research"]'::jsonb),
 ('digital','Digital & Ecommerce','digital-director',180,'["search","CRO","SEO","product discovery","analytics"]'::jsonb,'["official platform docs","primary research","major retailer evidence"]'::jsonb),
 ('commercial','Commercial','commercial-director',180,'["pricing","assortment","supplier terms","promotions","category strategy"]'::jsonb,'["company data","primary market evidence","credible industry research"]'::jsonb),
 ('supply-chain','Supply Chain','supply-chain-director',180,'["forecasting","replenishment","availability","logistics"]'::jsonb,'["company data","standards","credible operations research"]'::jsonb),
 ('finance','Finance','finance-director',365,'["margin","cash flow","business cases","controls"]'::jsonb,'["company data","accounting standards","primary regulatory sources"]'::jsonb)
ON CONFLICT(domain_key) DO NOTHING;
