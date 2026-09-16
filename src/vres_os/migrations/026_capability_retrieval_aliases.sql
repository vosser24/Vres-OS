-- Retrieval-only aliases for shipped company capabilities.
-- These terms improve discovery of ordinary subproblems without changing capability scope,
-- ownership, proof history, or company publication authority.

UPDATE vres.capabilities
SET metadata = COALESCE(metadata, '{}'::jsonb) || jsonb_build_object(
    'aliases', to_jsonb(ARRAY[
        'application development', 'code implementation', 'debugging', 'refactoring'
    ]::text[])
)
WHERE capability_key='cap.software-engineering' AND project_id IS NULL;

UPDATE vres.capabilities
SET metadata = COALESCE(metadata, '{}'::jsonb) || jsonb_build_object(
    'aliases', to_jsonb(ARRAY[
        'sql database', 'database schema', 'query tuning', 'postgres database'
    ]::text[])
)
WHERE capability_key='cap.postgresql' AND project_id IS NULL;

UPDATE vres.capabilities
SET metadata = COALESCE(metadata, '{}'::jsonb) || jsonb_build_object(
    'aliases', to_jsonb(ARRAY[
        'analytics', 'quantitative analysis', 'data interpretation'
    ]::text[])
)
WHERE capability_key='cap.data-analysis' AND project_id IS NULL;

UPDATE vres.capabilities
SET metadata = COALESCE(metadata, '{}'::jsonb) || jsonb_build_object(
    'aliases', to_jsonb(ARRAY[
        'forecasting', 'demand planning', 'seasonality'
    ]::text[])
)
WHERE capability_key='cap.demand-forecasting' AND project_id IS NULL;

UPDATE vres.capabilities
SET metadata = COALESCE(metadata, '{}'::jsonb) || jsonb_build_object(
    'aliases', to_jsonb(ARRAY[
        'inventory planning', 'reorder points', 'stock availability'
    ]::text[])
)
WHERE capability_key='cap.replenishment' AND project_id IS NULL;

UPDATE vres.capabilities
SET metadata = COALESCE(metadata, '{}'::jsonb) || jsonb_build_object(
    'aliases', to_jsonb(ARRAY[
        'tier design', 'tiered pricing', 'price ladder', 'price spacing',
        'price points', 'subscription pricing', 'good better best'
    ]::text[])
)
WHERE capability_key='cap.pricing' AND project_id IS NULL;

UPDATE vres.capabilities
SET metadata = COALESCE(metadata, '{}'::jsonb) || jsonb_build_object(
    'aliases', to_jsonb(ARRAY[
        'range architecture', 'category range', 'product mix'
    ]::text[])
)
WHERE capability_key='cap.assortment' AND project_id IS NULL;

UPDATE vres.capabilities
SET metadata = COALESCE(metadata, '{}'::jsonb) || jsonb_build_object(
    'aliases', to_jsonb(ARRAY[
        'site search', 'search relevance', 'product discovery'
    ]::text[])
)
WHERE capability_key='cap.ecommerce-search' AND project_id IS NULL;

UPDATE vres.capabilities
SET metadata = COALESCE(metadata, '{}'::jsonb) || jsonb_build_object(
    'aliases', to_jsonb(ARRAY[
        'conversion rate optimization', 'funnel optimization', 'journey conversion'
    ]::text[])
)
WHERE capability_key='cap.cro' AND project_id IS NULL;

UPDATE vres.capabilities
SET metadata = COALESCE(metadata, '{}'::jsonb) || jsonb_build_object(
    'aliases', to_jsonb(ARRAY[
        'business case', 'margin analysis', 'cash flow analysis'
    ]::text[])
)
WHERE capability_key='cap.financial-analysis' AND project_id IS NULL;

UPDATE vres.capabilities
SET metadata = COALESCE(metadata, '{}'::jsonb) || jsonb_build_object(
    'aliases', to_jsonb(ARRAY[
        'knowledge governance', 'provenance management', 'deduplication'
    ]::text[])
)
WHERE capability_key='cap.knowledge-stewardship' AND project_id IS NULL;

UPDATE vres.capabilities
SET metadata = COALESCE(metadata, '{}'::jsonb) || jsonb_build_object(
    'aliases', to_jsonb(ARRAY[
        'contract risk', 'regulatory risk', 'compliance risk'
    ]::text[])
)
WHERE capability_key='cap.legal-risk' AND project_id IS NULL;

UPDATE vres.capabilities
SET metadata = COALESCE(metadata, '{}'::jsonb) || jsonb_build_object(
    'aliases', to_jsonb(ARRAY[
        'pipeline strategy', 'account strategy', 'channel sales', 'sales execution'
    ]::text[])
)
WHERE capability_key='cap.sales' AND project_id IS NULL;

UPDATE vres.capabilities
SET metadata = COALESCE(metadata, '{}'::jsonb) || jsonb_build_object(
    'aliases', to_jsonb(ARRAY[
        'positioning', 'campaign strategy', 'customer acquisition', 'brand proposition'
    ]::text[])
)
WHERE capability_key='cap.marketing' AND project_id IS NULL;

UPDATE vres.capabilities
SET metadata = COALESCE(metadata, '{}'::jsonb) || jsonb_build_object(
    'aliases', to_jsonb(ARRAY[
        'organization design', 'staffing', 'incentives', 'capability building'
    ]::text[])
)
WHERE capability_key='cap.people' AND project_id IS NULL;
