INSERT INTO vres.capabilities(capability_key,name,description,domain,owner_role,status)
VALUES
 ('cap.software-engineering','Software Engineering','Design, implement, debug, refactor and validate production software.','technology','cto','active'),
 ('cap.postgresql','PostgreSQL','Schema design, SQL, query tuning, migrations and operational database work.','data','data-director','active'),
 ('cap.data-analysis','Data Analysis','Reproducible analysis of company data with explicit evidence, limitations and validation.','data','data-director','active'),
 ('cap.demand-forecasting','Demand Forecasting','Forecast demand using history, seasonality, causal signals and error validation.','supply-chain','supply-chain-director','active'),
 ('cap.replenishment','Replenishment','Inventory/reorder/min-max/availability decision support.','supply-chain','supply-chain-director','active'),
 ('cap.pricing','Pricing','Pricing architecture, competitiveness, elasticity, promotion and margin reasoning.','commercial','commercial-director','active'),
 ('cap.assortment','Assortment Strategy','Range/category structure, product roles, lifecycle and category economics.','commercial','commercial-director','active'),
 ('cap.ecommerce-search','Ecommerce Search','Search relevance, query understanding, lexical/semantic retrieval and product discovery.','digital','digital-director','active'),
 ('cap.cro','Conversion Optimization','Evidence-driven ecommerce conversion and journey optimization.','digital','digital-director','active'),
 ('cap.financial-analysis','Financial Analysis','Margin, cash flow, investment cases and financial control.','finance','finance-director','active'),
 ('cap.knowledge-stewardship','Knowledge Stewardship','Provenance, deduplication, conflict detection, freshness and knowledge lifecycle.','knowledge','knowledge-steward','active')
ON CONFLICT(capability_key) DO NOTHING;
