-- #176 E7 G7 Chunk 2: the single effective-trust read contract for policy 176.g7.v1 (additive; 047 is immutable).
--
-- vres.source_effective_trust(source_id) returns exactly 'verified_trusted' or 'unverified'. It returns
-- 'verified_trusted' only when ALL of the following hold, evaluated in one statement (one snapshot):
--   * the source exists, status = 'active', and has a project scope (company-scope / NULL project never qualifies);
--   * the NEWEST ledger event for the source (by id, never created_at) is an unexpired user_approval 'grant' under
--     policy 176.g7.v1 with the pinned policy digest, and no revoke supersedes it;
--   * the ledger row is consistent with the source (project_id, source_key) and with its own subject_key;
--   * its authority anchor still is a typed USER_INSTRUCTION of the same task whose whole text is
--     'I authorize <subject_key>' (a corrupt or forged row can only turn the result into 'unverified');
--   * the freshly recomputed owner digests (vres.source_trust_digests) have chunk_count > 0 and equal the granted
--     content_digest and descriptor_digest;
--   * the declared label authority_level is not 'external_untrusted_observation' (a label can only restrict).
-- Everything else, including unknown or NULL ids and any contradictory evidence, is 'unverified'.
-- authority_level, metadata and content_hash are never positive trust evidence. The function writes nothing.
--
-- SECURITY DEFINER is required because the runtime role has no EXECUTE on the digest owner function and no direct
-- right to the evidence it must recompute; STABLE makes the read-only property engine-enforced.
CREATE OR REPLACE FUNCTION vres.source_effective_trust(p_source_id bigint)
RETURNS text
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = pg_catalog, vres
AS $vres_g7$
    SELECT CASE WHEN EXISTS (
        SELECT 1
          FROM vres.sources s
          CROSS JOIN LATERAL (SELECT e.* FROM vres.source_trust_events e
                               WHERE e.source_id = s.id ORDER BY e.id DESC LIMIT 1) l
          CROSS JOIN LATERAL vres.source_trust_digests(s.id) d
         WHERE s.id = p_source_id
           AND s.status = 'active'
           AND s.project_id IS NOT NULL
           AND coalesce(s.source_type, '') !~ E'[\r\n]'
           AND coalesce(s.origin, '') !~ E'[\r\n]'
           AND coalesce(s.version, '') !~ E'[\r\n]'
           AND s.authority_level IS DISTINCT FROM 'external_untrusted_observation'
           AND l.action = 'grant'
           AND l.basis = 'user_approval'
           AND l.expires_at IS NULL
           AND l.policy_version = '176.g7.v1'
           AND l.policy_digest = 'f20b037b00d0a5711666fd6c1d98538101708d99e7f6f32cf5a490ff6b96cf03'
           AND l.project_id = s.project_id
           AND l.source_key = s.source_key
           AND l.subject_key = 'source_trust:grant:' || l.project_id::text || ':' || l.source_key || ':'
                               || l.content_digest || ':' || l.descriptor_digest
           AND d.chunk_count > 0
           AND d.content_digest = l.content_digest
           AND d.descriptor_digest = l.descriptor_digest
           AND NOT EXISTS (SELECT 1 FROM vres.source_trust_events r
                            WHERE r.action = 'revoke' AND r.supersedes_event_id = l.id)
           AND EXISTS (SELECT 1
                         FROM vres.task_events a
                         JOIN vres.tasks t ON t.id = a.task_id
                        WHERE a.id = l.user_event_id
                          AND a.task_id = l.task_id
                          AND t.project_id = l.project_id
                          AND a.event_type = 'USER_INSTRUCTION'
                          AND a.actor = 'user'
                          AND a.payload ->> 'source' = 'user_prompt'
                          AND btrim(a.payload ->> 'text', E' \t\r\n') = 'I authorize ' || l.subject_key)
    ) THEN 'verified_trusted' ELSE 'unverified' END
$vres_g7$;

-- Privileges: nobody but the owner by default; activate_boundary grants EXECUTE to the runtime role only.
-- Same sweep as migrations 040/047: default privileges may have granted the reader to non-owner roles.
REVOKE ALL ON FUNCTION vres.source_effective_trust(bigint) FROM PUBLIC;

DO $vres_g7$
DECLARE
    g record;
BEGIN
    FOR g IN
        SELECT DISTINCT a.grantee
          FROM pg_proc p, aclexplode(p.proacl) a
         WHERE p.oid = 'vres.source_effective_trust(bigint)'::regprocedure
           AND a.grantee <> p.proowner AND a.grantee <> 0
    LOOP
        EXECUTE format('REVOKE ALL ON FUNCTION vres.source_effective_trust(bigint) FROM %I', g.grantee::regrole::text);
    END LOOP;
END
$vres_g7$;
