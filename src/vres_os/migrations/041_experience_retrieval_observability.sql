-- #176 E6 Chunk 1: host-observed experience retrieval observability.
-- Policy 176.e6.v1, append-only observation/item ledgers, and one writer-only SECURITY DEFINER recorder.
-- Structural identity only: keys, enums, counts, timestamps and SHA-256 digests. No query, premise, memory text,
-- payload, transcript or credential value is ever stored. Additive: no existing migration, row or trigger changes.

INSERT INTO vres.experience_policy_versions(policy_version,schema_version,policy_digest,policy)
VALUES (
    '176.e6.v1',
    1,
    'd61f60d31182085748bb613ef3c160274f1a1a5a2384854f36e52b4cdfecc5e5',
    '{"authority":"no_promotion","capture":"host_posttooluse_successful_experience_retrieve_only","payload":"digest_structural_no_memory_text_no_query_text_no_private_reasoning","policy_version":"176.e6.v1","reference":"exact_returned_memory_key_reference_only","replay":"same_snapshot_hard_gate_frozen_post_gate_variants_only","schema_version":1,"utility":"descriptive_join_no_causal_credit","writer":"trusted_provenance_writer"}'::jsonb
)
ON CONFLICT(policy_version) DO NOTHING;

DO $vres_e6$
BEGIN
    IF NOT EXISTS (
        SELECT 1
          FROM vres.experience_policy_versions
         WHERE policy_version='176.e6.v1'
           AND schema_version=1
           AND policy_digest='d61f60d31182085748bb613ef3c160274f1a1a5a2384854f36e52b4cdfecc5e5'
    ) THEN
        RAISE EXCEPTION 'Experience E6 policy version/digest mismatch';
    END IF;
END
$vres_e6$;

CREATE TABLE IF NOT EXISTS vres.experience_retrieval_observations (
    id bigserial PRIMARY KEY,
    observation_key text NOT NULL UNIQUE CHECK (observation_key ~ '^ERO-[0-9a-f]{32}$'),
    idempotency_key text NOT NULL UNIQUE CHECK (idempotency_key ~ '^[0-9a-f]{64}$'),
    project_id bigint NOT NULL REFERENCES vres.projects(id) ON DELETE RESTRICT,
    session_id bigint NOT NULL REFERENCES vres.sessions(id) ON DELETE RESTRICT,
    task_id bigint REFERENCES vres.tasks(id) ON DELETE RESTRICT,
    work_unit_key text CHECK (work_unit_key IS NULL OR char_length(work_unit_key) BETWEEN 1 AND 300),
    host_agent_id text CHECK (host_agent_id IS NULL OR char_length(host_agent_id) BETWEEN 1 AND 300),
    agent_type text CHECK (agent_type IS NULL OR char_length(agent_type) BETWEEN 1 AND 200),
    attribution_state text NOT NULL CHECK (attribution_state IN ('main_thread','work_unit','unattributed_host_agent')),
    provider_session_id_digest text NOT NULL CHECK (provider_session_id_digest ~ '^[0-9a-f]{64}$'),
    tool_use_id text NOT NULL CHECK (char_length(tool_use_id) BETWEEN 1 AND 300),
    policy_version text NOT NULL REFERENCES vres.experience_policy_versions(policy_version) ON DELETE RESTRICT
        CHECK (policy_version = '176.e6.v1'),
    retrieval_schema_version text NOT NULL CHECK (retrieval_schema_version = '176.e5.v1'),
    retrieval_policy_digest text NOT NULL
        CHECK (retrieval_policy_digest = '7572cafc632d4f56571adbe5f59baceedf15c56a07d5a3ca35e4b05448a982e9'),
    request_digest text NOT NULL CHECK (request_digest ~ '^[0-9a-f]{64}$'),
    query_digest text NOT NULL CHECK (query_digest ~ '^[0-9a-f]{64}$'),
    premises_digest text CHECK (premises_digest IS NULL OR premises_digest ~ '^[0-9a-f]{64}$'),
    task_key text CHECK (task_key IS NULL OR char_length(task_key) BETWEEN 1 AND 128),
    task_family text CHECK (task_family IS NULL OR char_length(task_family) BETWEEN 1 AND 128),
    capability_keys text[] NOT NULL DEFAULT '{}' CHECK (cardinality(capability_keys) <= 10),
    temporal_intent text NOT NULL CHECK (temporal_intent IN ('current','historical')),
    as_of timestamptz,
    include_candidates boolean NOT NULL,
    raw_fallback boolean NOT NULL,
    pack_digest text NOT NULL CHECK (pack_digest ~ '^[0-9a-f]{64}$'),
    pack_bytes integer NOT NULL CHECK (pack_bytes BETWEEN 1 AND 16384),
    estimated_tokens integer NOT NULL CHECK (estimated_tokens >= 0),
    item_count integer NOT NULL CHECK (item_count BETWEEN 0 AND 24),
    abstained boolean NOT NULL,
    reason text CHECK (reason IS NULL OR char_length(reason) BETWEEN 1 AND 64),
    diagnostics jsonb NOT NULL DEFAULT '{}'::jsonb
        CHECK (jsonb_typeof(diagnostics) = 'object' AND octet_length(diagnostics::text) <= 4096),
    evidence_keys text[] NOT NULL DEFAULT '{}' CHECK (cardinality(evidence_keys) <= 500),
    duration_ms integer CHECK (duration_ms IS NULL OR duration_ms BETWEEN 0 AND 86400000),
    observed_at timestamptz NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT ck_ero_as_of_historical CHECK (as_of IS NULL OR temporal_intent = 'historical'),
    CONSTRAINT ck_ero_abstention CHECK (
        (abstained AND item_count = 0 AND reason IS NOT NULL)
        OR (NOT abstained AND item_count > 0 AND reason IS NULL)),
    CONSTRAINT ck_ero_attribution CHECK (
        (attribution_state = 'main_thread' AND host_agent_id IS NULL AND agent_type IS NULL AND work_unit_key IS NULL)
        OR (attribution_state = 'work_unit' AND host_agent_id IS NOT NULL AND work_unit_key IS NOT NULL)
        OR (attribution_state = 'unattributed_host_agent' AND host_agent_id IS NOT NULL AND work_unit_key IS NULL))
);

CREATE INDEX IF NOT EXISTS idx_ero_project_observed
    ON vres.experience_retrieval_observations(project_id, observed_at DESC);
CREATE INDEX IF NOT EXISTS idx_ero_session
    ON vres.experience_retrieval_observations(session_id, id DESC);
CREATE INDEX IF NOT EXISTS idx_ero_task
    ON vres.experience_retrieval_observations(task_id, id DESC) WHERE task_id IS NOT NULL;

CREATE TABLE IF NOT EXISTS vres.experience_retrieval_items (
    id bigserial PRIMARY KEY,
    observation_id bigint NOT NULL REFERENCES vres.experience_retrieval_observations(id) ON DELETE RESTRICT,
    ordinal integer NOT NULL CHECK (ordinal BETWEEN 1 AND 24),
    section text NOT NULL CHECK (section IN (
        'current_decisions','accepted_procedures','validated_lessons','candidate_lessons',
        'conflicts_and_stale','precedent_episodes','low_trust_observations','raw_evidence_refs')),
    section_ordinal integer NOT NULL CHECK (section_ordinal BETWEEN 1 AND 24),
    memory_key text NOT NULL CHECK (char_length(memory_key) BETWEEN 1 AND 300),
    memory_class text NOT NULL CHECK (memory_class IN ('decision','procedural','semantic','episodic','raw_evidence')),
    authority_class text NOT NULL CHECK (char_length(authority_class) BETWEEN 1 AND 80),
    scope text NOT NULL CHECK (scope IN ('project','company_approved')),
    status text NOT NULL CHECK (char_length(status) BETWEEN 1 AND 64),
    trust_class text NOT NULL CHECK (char_length(trust_class) BETWEEN 1 AND 64),
    role text NOT NULL CHECK (role IN (
        'instruction','candidate','evidence_ref','stale_assumption','conflict','warning_example',
        'low_trust_observation')),
    why_retrieved text[] NOT NULL DEFAULT '{}' CHECK (cardinality(why_retrieved) <= 32),
    evidence text[] NOT NULL DEFAULT '{}' CHECK (cardinality(evidence) <= 200),
    applicability_digest text NOT NULL CHECK (applicability_digest ~ '^[0-9a-f]{64}$'),
    signals jsonb NOT NULL CHECK (jsonb_typeof(signals) = 'object' AND octet_length(signals::text) <= 1024),
    item_digest text NOT NULL CHECK (item_digest ~ '^[0-9a-f]{64}$'),
    UNIQUE (observation_id, memory_key),
    UNIQUE (observation_id, ordinal)
);

CREATE INDEX IF NOT EXISTS idx_eri_memory_key ON vres.experience_retrieval_items(memory_key);

-- Append-only with no bypass setting: UPDATE, DELETE and TRUNCATE always raise.
CREATE OR REPLACE FUNCTION vres.protect_experience_retrieval_immutability()
RETURNS trigger
LANGUAGE plpgsql
AS $vres_e6$
BEGIN
    RAISE EXCEPTION 'experience retrieval observability ledgers are immutable; append new evidence instead of modifying history';
END
$vres_e6$;

DROP TRIGGER IF EXISTS trg_protect_ero_update ON vres.experience_retrieval_observations;
CREATE TRIGGER trg_protect_ero_update BEFORE UPDATE ON vres.experience_retrieval_observations
FOR EACH ROW EXECUTE FUNCTION vres.protect_experience_retrieval_immutability();
DROP TRIGGER IF EXISTS trg_protect_ero_delete ON vres.experience_retrieval_observations;
CREATE TRIGGER trg_protect_ero_delete BEFORE DELETE ON vres.experience_retrieval_observations
FOR EACH ROW EXECUTE FUNCTION vres.protect_experience_retrieval_immutability();
DROP TRIGGER IF EXISTS trg_protect_ero_truncate ON vres.experience_retrieval_observations;
CREATE TRIGGER trg_protect_ero_truncate BEFORE TRUNCATE ON vres.experience_retrieval_observations
FOR EACH STATEMENT EXECUTE FUNCTION vres.protect_experience_retrieval_immutability();

DROP TRIGGER IF EXISTS trg_protect_eri_update ON vres.experience_retrieval_items;
CREATE TRIGGER trg_protect_eri_update BEFORE UPDATE ON vres.experience_retrieval_items
FOR EACH ROW EXECUTE FUNCTION vres.protect_experience_retrieval_immutability();
DROP TRIGGER IF EXISTS trg_protect_eri_delete ON vres.experience_retrieval_items;
CREATE TRIGGER trg_protect_eri_delete BEFORE DELETE ON vres.experience_retrieval_items
FOR EACH ROW EXECUTE FUNCTION vres.protect_experience_retrieval_immutability();
DROP TRIGGER IF EXISTS trg_protect_eri_truncate ON vres.experience_retrieval_items;
CREATE TRIGGER trg_protect_eri_truncate BEFORE TRUNCATE ON vres.experience_retrieval_items
FOR EACH STATEMENT EXECUTE FUNCTION vres.protect_experience_retrieval_immutability();

-- Writer-only recorder. The host hook passes structural digests only; the project is resolved by the hook from the host
-- cwd and the open Claude session is matched EXACTLY by (project, provider, provider_session_id). The task comes only
-- from sessions.task_id (NULL when unbound); a work unit is attributed only when exactly one work unit of that task is
-- bound to the host agent id. Duplicate delivery is idempotent; a duplicate with different digests fails closed.
CREATE OR REPLACE FUNCTION vres.record_experience_retrieval_observation(
    p_project_id bigint, p_provider_session_id text, p_agent_id text, p_agent_type text, p_tool_use_id text,
    p_observation jsonb, p_items jsonb)
RETURNS TABLE(outcome text, observation_key text, attribution_state text)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, vres
AS $vres_e6$
DECLARE
    allowed name;
    n integer;
    sess record;
    task_row bigint;
    wu_count integer;
    wu_key text;
    attribution text;
    idem text;
    existing record;
    new_id bigint;
    new_key text;
    item_total integer;
BEGIN
    SELECT writer_role INTO allowed FROM vres.provenance_authority WHERE authority_key = 'user_event_writer';
    IF allowed IS NULL OR session_user <> allowed::text THEN
        RAISE EXCEPTION 'experience retrieval observations may be recorded only by the trusted provenance writer role'
            USING ERRCODE = 'P0001';
    END IF;
    IF p_project_id IS NULL OR p_provider_session_id IS NULL
       OR char_length(p_provider_session_id) NOT BETWEEN 1 AND 300
       OR p_tool_use_id IS NULL OR char_length(p_tool_use_id) NOT BETWEEN 1 AND 300
       OR (p_agent_id IS NOT NULL AND char_length(p_agent_id) NOT BETWEEN 1 AND 300)
       OR (p_agent_type IS NOT NULL AND (p_agent_id IS NULL OR char_length(p_agent_type) NOT BETWEEN 1 AND 200))
       OR p_observation IS NULL OR jsonb_typeof(p_observation) <> 'object'
       OR p_items IS NULL OR jsonb_typeof(p_items) <> 'array' THEN
        RAISE EXCEPTION 'invalid experience retrieval observation arguments' USING ERRCODE = 'P0001';
    END IF;

    SELECT count(*) INTO n FROM vres.sessions s
     WHERE s.project_id = p_project_id AND s.provider = 'claude'
       AND s.provider_session_id = p_provider_session_id AND s.ended_at IS NULL;
    IF n = 0 THEN
        RETURN QUERY SELECT 'session_not_found'::text, NULL::text, NULL::text;
        RETURN;
    ELSIF n > 1 THEN
        RETURN QUERY SELECT 'session_ambiguous'::text, NULL::text, NULL::text;
        RETURN;
    END IF;
    SELECT s.id, s.task_id INTO sess FROM vres.sessions s
     WHERE s.project_id = p_project_id AND s.provider = 'claude'
       AND s.provider_session_id = p_provider_session_id AND s.ended_at IS NULL;

    task_row := NULL;
    IF sess.task_id IS NOT NULL THEN
        SELECT t.id INTO task_row FROM vres.tasks t WHERE t.id = sess.task_id AND t.project_id = p_project_id;
    END IF;

    wu_key := NULL;
    IF p_agent_id IS NULL THEN
        attribution := 'main_thread';
    ELSE
        attribution := 'unattributed_host_agent';
        IF task_row IS NOT NULL THEN
            SELECT count(*) INTO wu_count FROM vres.orchestration_work_units w
             WHERE w.task_id = task_row AND w.host_agent_id = p_agent_id;
            IF wu_count = 1 THEN
                SELECT w.work_unit_key INTO wu_key FROM vres.orchestration_work_units w
                 WHERE w.task_id = task_row AND w.host_agent_id = p_agent_id;
                attribution := 'work_unit';
            END IF;
        END IF;
    END IF;

    idem := encode(sha256(convert_to(
        jsonb_build_array(p_project_id, sess.id, coalesce(p_agent_id, ''), p_tool_use_id, '176.e6.v1')::text,
        'UTF8')), 'hex');
    PERFORM pg_advisory_xact_lock(hashtextextended(idem, 0));
    SELECT o.id, o.observation_key, o.request_digest, o.pack_digest, o.attribution_state INTO existing
      FROM vres.experience_retrieval_observations o WHERE o.idempotency_key = idem;
    IF FOUND THEN
        IF existing.request_digest IS DISTINCT FROM p_observation->>'request_digest'
           OR existing.pack_digest IS DISTINCT FROM p_observation->>'pack_digest' THEN
            RAISE EXCEPTION 'conflicting duplicate experience retrieval observation' USING ERRCODE = 'P0001';
        END IF;
        RETURN QUERY SELECT 'duplicate'::text, existing.observation_key, existing.attribution_state;
        RETURN;
    END IF;

    item_total := jsonb_array_length(p_items);
    IF item_total <> (p_observation->>'item_count')::integer THEN
        RAISE EXCEPTION 'item_count does not match returned items' USING ERRCODE = 'P0001';
    END IF;

    new_key := 'ERO-' || replace(gen_random_uuid()::text, '-', '');
    INSERT INTO vres.experience_retrieval_observations(
        observation_key, idempotency_key, project_id, session_id, task_id, work_unit_key, host_agent_id, agent_type,
        attribution_state, provider_session_id_digest, tool_use_id, policy_version, retrieval_schema_version,
        retrieval_policy_digest, request_digest, query_digest, premises_digest, task_key, task_family,
        capability_keys, temporal_intent, as_of, include_candidates, raw_fallback, pack_digest, pack_bytes,
        estimated_tokens, item_count, abstained, reason, diagnostics, evidence_keys, duration_ms, observed_at)
    VALUES (
        new_key, idem, p_project_id, sess.id, task_row, wu_key, p_agent_id, p_agent_type,
        attribution,
        encode(sha256(convert_to(p_provider_session_id, 'UTF8')), 'hex'), p_tool_use_id,
        '176.e6.v1', p_observation->>'retrieval_schema_version',
        p_observation->>'retrieval_policy_digest', p_observation->>'request_digest', p_observation->>'query_digest',
        p_observation->>'premises_digest', p_observation->>'task_key', p_observation->>'task_family',
        ARRAY(SELECT jsonb_array_elements_text(coalesce(p_observation->'capability_keys', '[]'::jsonb))),
        p_observation->>'temporal_intent', (p_observation->>'as_of')::timestamptz,
        (p_observation->>'include_candidates')::boolean, (p_observation->>'raw_fallback')::boolean,
        p_observation->>'pack_digest', (p_observation->>'pack_bytes')::integer,
        (p_observation->>'estimated_tokens')::integer, item_total, (p_observation->>'abstained')::boolean,
        p_observation->>'reason', coalesce(p_observation->'diagnostics', '{}'::jsonb),
        ARRAY(SELECT jsonb_array_elements_text(coalesce(p_observation->'evidence_keys', '[]'::jsonb))),
        (p_observation->>'duration_ms')::integer, clock_timestamp())
    RETURNING id INTO new_id;

    INSERT INTO vres.experience_retrieval_items(
        observation_id, ordinal, section, section_ordinal, memory_key, memory_class, authority_class, scope, status,
        trust_class, role, why_retrieved, evidence, applicability_digest, signals, item_digest)
    SELECT new_id, (e.ord)::integer, e.item->>'section', (e.item->>'section_ordinal')::integer,
           e.item->>'memory_key', e.item->>'memory_class', e.item->>'authority_class', e.item->>'scope',
           e.item->>'status', e.item->>'trust_class', e.item->>'role',
           ARRAY(SELECT jsonb_array_elements_text(coalesce(e.item->'why_retrieved', '[]'::jsonb))),
           ARRAY(SELECT jsonb_array_elements_text(coalesce(e.item->'evidence', '[]'::jsonb))),
           e.item->>'applicability_digest', e.item->'signals', e.item->>'item_digest'
      FROM jsonb_array_elements(p_items) WITH ORDINALITY AS e(item, ord);

    RETURN QUERY SELECT 'recorded'::text, new_key, attribution;
END
$vres_e6$;

-- Privileges: nobody but the owner by default (activate_boundary grants the writer EXECUTE and the runtime SELECT).
REVOKE ALL ON TABLE vres.experience_retrieval_observations FROM PUBLIC;
REVOKE ALL ON TABLE vres.experience_retrieval_items FROM PUBLIC;
REVOKE ALL ON SEQUENCE vres.experience_retrieval_observations_id_seq FROM PUBLIC;
REVOKE ALL ON SEQUENCE vres.experience_retrieval_items_id_seq FROM PUBLIC;
REVOKE ALL ON FUNCTION vres.record_experience_retrieval_observation(bigint,text,text,text,text,jsonb,jsonb) FROM PUBLIC;
REVOKE ALL ON FUNCTION vres.protect_experience_retrieval_immutability() FROM PUBLIC;

DO $vres_e6$
DECLARE
    g record;
BEGIN
    FOR g IN
        SELECT DISTINCT format('TABLE %s', c.oid::regclass) AS obj, a.grantee
          FROM pg_class c, aclexplode(c.relacl) a
         WHERE c.oid IN ('vres.experience_retrieval_observations'::regclass,
                         'vres.experience_retrieval_items'::regclass,
                         'vres.experience_retrieval_observations_id_seq'::regclass,
                         'vres.experience_retrieval_items_id_seq'::regclass)
           AND a.grantee <> c.relowner AND a.grantee <> 0
        UNION
        SELECT DISTINCT format('FUNCTION %s', p.oid::regprocedure), a.grantee
          FROM pg_proc p, aclexplode(p.proacl) a
         WHERE p.oid IN (
                 'vres.record_experience_retrieval_observation(bigint,text,text,text,text,jsonb,jsonb)'::regprocedure,
                 'vres.protect_experience_retrieval_immutability()'::regprocedure)
           AND a.grantee <> p.proowner AND a.grantee <> 0
    LOOP
        EXECUTE format('REVOKE ALL ON %s FROM %I', g.obj, pg_get_userbyid(g.grantee));
    END LOOP;
END
$vres_e6$;
