-- Add project-scoped capability acquisition without weakening company-wide catalog authority.
-- Existing shipped capabilities remain company-wide (project_id NULL). Runtime project expertise
-- must carry a project_id and cannot become global merely by reuse/proof.

ALTER TABLE vres.capabilities
    ADD COLUMN IF NOT EXISTS project_id bigint REFERENCES vres.projects(id) ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS idx_capabilities_project_status
    ON vres.capabilities(project_id,status,proven_count DESC);

-- Complete the stable executive roster with shipped capability descriptors. These are product
-- seeds, not runtime company publications, and therefore do not consume user approval events.
INSERT INTO vres.capabilities(capability_key,name,description,domain,owner_role,status,project_id)
VALUES
 ('cap.legal-risk','Legal and Risk','Legal constraints, regulatory exposure, contractual risk, controls and decision risk assessment.','legal-risk','legal-risk-director','active',NULL),
 ('cap.sales','Sales','Sales strategy, account execution, pipeline, channel economics and commercial conversion.','sales','sales-director','active',NULL),
 ('cap.marketing','Marketing','Customer proposition, campaign strategy, positioning, acquisition and marketing effectiveness.','marketing','marketing-director','active',NULL),
 ('cap.people','People and Organization','Organization design, staffing, incentives, capability building and people operating constraints.','people','people-director','active',NULL)
ON CONFLICT(capability_key) DO NOTHING;
