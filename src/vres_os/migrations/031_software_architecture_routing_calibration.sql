-- Extend retrieval-only aliases for shipped software-engineering capability.
-- This improves discovery of architecture/design subproblems without changing scope,
-- ownership, proof history, or company publication authority.

UPDATE vres.capabilities
SET metadata = COALESCE(metadata, '{}'::jsonb) || jsonb_build_object(
    'aliases',
    COALESCE(metadata->'aliases', '[]'::jsonb) ||
    to_jsonb(ARRAY[
        'software architecture',
        'system architecture',
        'systems architecture',
        'architecture design',
        'migration architecture',
        'software engineering architecture'
    ]::text[])
)
WHERE capability_key='cap.software-engineering' AND project_id IS NULL;
