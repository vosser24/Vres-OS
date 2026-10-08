-- #176 E7 Boundary 3: allow E5 176.e5.v3 identities in the E6 observation ledger.
-- Only the 042 paired identity check on experience_retrieval_observations is replaced (same name),
-- now with three valid (schema version, policy digest) pairs: v1, v2, v3.
-- No new table/column, no backfill, no UPDATE, no trigger/privilege/writer change. Migration 042 stays immutable.
ALTER TABLE vres.experience_retrieval_observations
    DROP CONSTRAINT experience_retrieval_observations_e5_identity_pair_check;

ALTER TABLE vres.experience_retrieval_observations
    ADD CONSTRAINT experience_retrieval_observations_e5_identity_pair_check CHECK (
        (retrieval_schema_version = '176.e5.v1'
            AND retrieval_policy_digest = '7572cafc632d4f56571adbe5f59baceedf15c56a07d5a3ca35e4b05448a982e9')
        OR (retrieval_schema_version = '176.e5.v2'
            AND retrieval_policy_digest = '0cd0f10d24e37dd7a9872eced6c18e4962d4740a2d6a8c03a38cea1d8a73d6b5')
        OR (retrieval_schema_version = '176.e5.v3'
            AND retrieval_policy_digest = '272b10b6042a77bb79812ec637ec9296e28867628285165775c5aeee4af1a4ad'));
