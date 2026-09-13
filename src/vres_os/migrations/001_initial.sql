DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_available_extensions WHERE name='pg_trgm') THEN
        BEGIN
            CREATE EXTENSION IF NOT EXISTS pg_trgm;
        EXCEPTION WHEN OTHERS THEN
            RAISE NOTICE 'pg_trgm could not be enabled; Vres will use full-text search only: %', SQLERRM;
        END;
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS vres.projects (
    id bigserial PRIMARY KEY,
    project_key text NOT NULL UNIQUE,
    name text NOT NULL,
    root_path text NOT NULL,
    remote_url text,
    current_branch text,
    first_seen_at timestamptz NOT NULL DEFAULT now(),
    last_seen_at timestamptz NOT NULL DEFAULT now(),
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS vres.tasks (
    id bigserial PRIMARY KEY,
    task_key text NOT NULL UNIQUE,
    project_id bigint REFERENCES vres.projects(id) ON DELETE SET NULL,
    title text NOT NULL,
    objective text NOT NULL,
    task_family text,
    status text NOT NULL DEFAULT 'active' CHECK (status IN ('new','active','waiting_user','blocked','completed','cancelled')),
    lead_role text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    completed_at timestamptz,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb
);
CREATE INDEX IF NOT EXISTS idx_tasks_project_status ON vres.tasks(project_id,status,updated_at DESC);

CREATE TABLE IF NOT EXISTS vres.task_state (
    task_id bigint PRIMARY KEY REFERENCES vres.tasks(id) ON DELETE CASCADE,
    current_phase text,
    current_step text,
    state_summary text NOT NULL DEFAULT '',
    next_action text NOT NULL DEFAULT '',
    latest_user_instruction text,
    open_questions jsonb NOT NULL DEFAULT '[]'::jsonb,
    assumptions jsonb NOT NULL DEFAULT '[]'::jsonb,
    constraints jsonb NOT NULL DEFAULT '[]'::jsonb,
    completed_work jsonb NOT NULL DEFAULT '[]'::jsonb,
    pending_work jsonb NOT NULL DEFAULT '[]'::jsonb,
    relevant_objects jsonb NOT NULL DEFAULT '[]'::jsonb,
    validation_status text NOT NULL DEFAULT 'not_required',
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS vres.task_events (
    id bigserial PRIMARY KEY,
    task_id bigint NOT NULL REFERENCES vres.tasks(id) ON DELETE CASCADE,
    event_type text NOT NULL,
    actor text NOT NULL,
    payload jsonb NOT NULL DEFAULT '{}'::jsonb,
    session_id text,
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_task_events_task_created ON vres.task_events(task_id,created_at DESC);

CREATE TABLE IF NOT EXISTS vres.checkpoints (
    id bigserial PRIMARY KEY,
    checkpoint_key text NOT NULL UNIQUE,
    task_id bigint NOT NULL REFERENCES vres.tasks(id) ON DELETE CASCADE,
    summary text NOT NULL,
    current_position text,
    next_action text,
    context jsonb NOT NULL DEFAULT '{}'::jsonb,
    reason text,
    created_by text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_checkpoints_task_created ON vres.checkpoints(task_id,created_at DESC);

CREATE TABLE IF NOT EXISTS vres.sources (
    id bigserial PRIMARY KEY,
    source_key text NOT NULL UNIQUE,
    source_type text NOT NULL,
    title text NOT NULL,
    origin text,
    path_or_uri text,
    content_hash text,
    version text,
    project_id bigint REFERENCES vres.projects(id) ON DELETE SET NULL,
    authority_level text,
    status text NOT NULL DEFAULT 'active',
    created_at timestamptz,
    ingested_at timestamptz NOT NULL DEFAULT now(),
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb
);
CREATE INDEX IF NOT EXISTS idx_sources_hash ON vres.sources(content_hash);

CREATE TABLE IF NOT EXISTS vres.knowledge_items (
    id bigserial PRIMARY KEY,
    knowledge_key text NOT NULL UNIQUE,
    project_id bigint REFERENCES vres.projects(id) ON DELETE SET NULL,
    knowledge_type text NOT NULL,
    title text NOT NULL,
    statement text NOT NULL,
    status text NOT NULL DEFAULT 'proposed' CHECK (status IN ('proposed','observed','validated','canonical','challenged','superseded','rejected')),
    scope jsonb NOT NULL DEFAULT '{}'::jsonb,
    confidence numeric(5,4),
    valid_from timestamptz,
    valid_to timestamptz,
    last_verified_at timestamptz,
    review_after timestamptz,
    source_owner text,
    superseded_by text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    search_vector tsvector GENERATED ALWAYS AS (
      setweight(to_tsvector('simple', coalesce(title,'')), 'A') ||
      setweight(to_tsvector('simple', coalesce(statement,'')), 'B')
    ) STORED,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb
);
CREATE INDEX IF NOT EXISTS idx_knowledge_search ON vres.knowledge_items USING GIN(search_vector);
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_extension WHERE extname='pg_trgm') THEN
        EXECUTE 'CREATE INDEX IF NOT EXISTS idx_knowledge_title_trgm ON vres.knowledge_items USING GIN(title gin_trgm_ops)';
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS vres.knowledge_evidence (
    id bigserial PRIMARY KEY,
    knowledge_id bigint NOT NULL REFERENCES vres.knowledge_items(id) ON DELETE CASCADE,
    source_id bigint REFERENCES vres.sources(id) ON DELETE SET NULL,
    evidence_type text NOT NULL,
    locator text,
    method text,
    limitations jsonb NOT NULL DEFAULT '[]'::jsonb,
    metrics jsonb NOT NULL DEFAULT '{}'::jsonb,
    reproducible boolean NOT NULL DEFAULT false,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS vres.relations (
    id bigserial PRIMARY KEY,
    source_kind text NOT NULL,
    source_key text NOT NULL,
    relation_type text NOT NULL,
    target_kind text NOT NULL,
    target_key text NOT NULL,
    provenance text,
    confidence numeric(5,4),
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(source_kind,source_key,relation_type,target_kind,target_key)
);
CREATE INDEX IF NOT EXISTS idx_relations_source ON vres.relations(source_kind,source_key);
CREATE INDEX IF NOT EXISTS idx_relations_target ON vres.relations(target_kind,target_key);

CREATE TABLE IF NOT EXISTS vres.procedures (
    id bigserial PRIMARY KEY,
    procedure_key text NOT NULL UNIQUE,
    name text NOT NULL,
    description text NOT NULL,
    task_family text,
    project_id bigint REFERENCES vres.projects(id) ON DELETE SET NULL,
    status text NOT NULL DEFAULT 'active',
    preferred_version integer,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS vres.procedure_versions (
    id bigserial PRIMARY KEY,
    procedure_id bigint NOT NULL REFERENCES vres.procedures(id) ON DELETE CASCADE,
    version_no integer NOT NULL,
    status text NOT NULL DEFAULT 'candidate' CHECK (status IN ('candidate','preferred','superseded','rejected')),
    input_contract jsonb NOT NULL DEFAULT '{}'::jsonb,
    method jsonb NOT NULL DEFAULT '[]'::jsonb,
    invariants jsonb NOT NULL DEFAULT '[]'::jsonb,
    validation_contract jsonb NOT NULL DEFAULT '[]'::jsonb,
    output_contract jsonb NOT NULL DEFAULT '{}'::jsonb,
    rejected_alternatives jsonb NOT NULL DEFAULT '[]'::jsonb,
    implementation_ref text,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(procedure_id,version_no)
);

CREATE TABLE IF NOT EXISTS vres.procedure_runs (
    id bigserial PRIMARY KEY,
    procedure_version_id bigint NOT NULL REFERENCES vres.procedure_versions(id) ON DELETE CASCADE,
    task_id bigint REFERENCES vres.tasks(id) ON DELETE SET NULL,
    accepted boolean,
    quality_score numeric(8,4),
    runtime_ms bigint,
    input_tokens bigint,
    output_tokens bigint,
    model_calls integer,
    estimated_cost numeric(14,6),
    validation jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS vres.procedure_feedback (
    id bigserial PRIMARY KEY,
    procedure_id bigint NOT NULL REFERENCES vres.procedures(id) ON DELETE CASCADE,
    task_id bigint REFERENCES vres.tasks(id) ON DELETE SET NULL,
    feedback_type text NOT NULL,
    statement text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS vres.optimization_candidates (
    id bigserial PRIMARY KEY,
    procedure_id bigint NOT NULL REFERENCES vres.procedures(id) ON DELETE CASCADE,
    baseline_version integer NOT NULL,
    candidate_version integer NOT NULL,
    quality_delta numeric(12,6),
    runtime_delta_ms bigint,
    input_token_delta bigint,
    output_token_delta bigint,
    protected_regression boolean NOT NULL DEFAULT false,
    decision text NOT NULL DEFAULT 'pending' CHECK (decision IN ('pending','auto_promoted','rejected','requires_user')),
    reason text,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS vres.model_policies (
    id bigserial PRIMARY KEY,
    policy_key text NOT NULL UNIQUE,
    task_family text,
    phase text NOT NULL,
    provider text NOT NULL,
    model text NOT NULL,
    effort text,
    status text NOT NULL DEFAULT 'active',
    priority integer NOT NULL DEFAULT 100,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS vres.model_runs (
    id bigserial PRIMARY KEY,
    task_id bigint REFERENCES vres.tasks(id) ON DELETE SET NULL,
    task_family text,
    phase text NOT NULL,
    provider text NOT NULL,
    model text NOT NULL,
    effort text,
    success boolean,
    quality_score numeric(8,4),
    runtime_ms bigint,
    input_tokens bigint,
    output_tokens bigint,
    estimated_cost numeric(14,6),
    retries integer NOT NULL DEFAULT 0,
    validator_result text,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS vres.capabilities (
    id bigserial PRIMARY KEY,
    capability_key text NOT NULL UNIQUE,
    name text NOT NULL,
    description text NOT NULL,
    domain text,
    owner_role text,
    status text NOT NULL DEFAULT 'active',
    proven_count integer NOT NULL DEFAULT 0,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS vres.onboarding_jobs (
    id bigserial PRIMARY KEY,
    job_key text NOT NULL UNIQUE,
    root_path text NOT NULL,
    status text NOT NULL DEFAULT 'new',
    files_seen bigint NOT NULL DEFAULT 0,
    unique_files bigint NOT NULL DEFAULT 0,
    duplicates bigint NOT NULL DEFAULT 0,
    knowledge_candidates bigint NOT NULL DEFAULT 0,
    review_required bigint NOT NULL DEFAULT 0,
    started_at timestamptz NOT NULL DEFAULT now(),
    completed_at timestamptz,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS vres.source_files (
    id bigserial PRIMARY KEY,
    job_id bigint REFERENCES vres.onboarding_jobs(id) ON DELETE CASCADE,
    source_id bigint REFERENCES vres.sources(id) ON DELETE SET NULL,
    absolute_path text NOT NULL,
    relative_path text NOT NULL,
    extension text,
    size_bytes bigint,
    modified_at timestamptz,
    content_hash text,
    duplicate_of bigint REFERENCES vres.source_files(id) ON DELETE SET NULL,
    extraction_status text NOT NULL DEFAULT 'pending',
    classification text,
    classification_confidence numeric(5,4),
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb
);
CREATE INDEX IF NOT EXISTS idx_source_files_hash ON vres.source_files(content_hash);

CREATE TABLE IF NOT EXISTS vres.review_queue (
    id bigserial PRIMARY KEY,
    item_kind text NOT NULL,
    item_key text NOT NULL,
    reason text NOT NULL,
    route_to text,
    priority integer NOT NULL DEFAULT 100,
    status text NOT NULL DEFAULT 'pending',
    created_at timestamptz NOT NULL DEFAULT now(),
    resolved_at timestamptz,
    resolution jsonb NOT NULL DEFAULT '{}'::jsonb
);

INSERT INTO vres.model_policies(policy_key,task_family,phase,provider,model,effort,priority)
VALUES
 ('bootstrap.plan.default',NULL,'plan','claude','best','high',100),
 ('bootstrap.build.default',NULL,'build','claude','sonnet','medium',100),
 ('bootstrap.validate.default',NULL,'validate','claude','best','high',100),
 ('bootstrap.summarize.default',NULL,'summarize','claude','haiku','low',100)
ON CONFLICT (policy_key) DO NOTHING;
