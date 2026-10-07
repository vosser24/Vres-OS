-- #176 E7 Chunk 5 continuation: allow E5 176.e5.v2 identities in the E6 observation ledger.
-- Only the two 041 equality checks on experience_retrieval_observations are replaced by ONE paired check.
-- (PostgreSQL truncated the first auto-generated name to 63 bytes.)
-- No new table/column, no backfill, no trigger/privilege/writer change. Migration 041 stays immutable.
ALTER TABLE vres.experience_retrieval_observations
    DROP CONSTRAINT experience_retrieval_observation_retrieval_schema_version_check,
    DROP CONSTRAINT experience_retrieval_observations_retrieval_policy_digest_check;

ALTER TABLE vres.experience_retrieval_observations
    ADD CONSTRAINT experience_retrieval_observations_e5_identity_pair_check CHECK (
        (retrieval_schema_version = '176.e5.v1'
            AND retrieval_policy_digest = '7572cafc632d4f56571adbe5f59baceedf15c56a07d5a3ca35e4b05448a982e9')
        OR (retrieval_schema_version = '176.e5.v2'
            AND retrieval_policy_digest = '0cd0f10d24e37dd7a9872eced6c18e4962d4740a2d6a8c03a38cea1d8a73d6b5'));
