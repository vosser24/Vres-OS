-- Scope identifiers are security/meaning boundaries, never NULL-on-delete promotion.
ALTER TABLE vres.review_queue ADD COLUMN project_id bigint REFERENCES vres.projects(id) ON DELETE RESTRICT;
CREATE INDEX idx_review_project_pending ON vres.review_queue(project_id,status,priority);
ALTER TABLE vres.preferences ADD COLUMN project_id bigint REFERENCES vres.projects(id) ON DELETE RESTRICT;
ALTER TABLE vres.preference_history ADD COLUMN project_id bigint REFERENCES vres.projects(id) ON DELETE RESTRICT;
ALTER TABLE vres.refresh_runs ADD COLUMN validation_request_id bigint REFERENCES vres.validation_requests(id) ON DELETE RESTRICT;
UPDATE vres.preferences SET status='unverified' WHERE source_event_id IS NULL;
-- Rebuild only project foreign keys that could silently globalize a scoped record.
DO $$
DECLARE r record;
BEGIN
 FOR r IN
   SELECT c.conrelid::regclass AS tbl,c.conname,a.attname
   FROM pg_constraint c JOIN pg_attribute a ON a.attrelid=c.conrelid AND a.attnum=c.conkey[1]
   WHERE c.contype='f' AND c.confrelid='vres.projects'::regclass
     AND c.confdeltype='n' AND array_length(c.conkey,1)=1 AND a.attname='project_id'
 LOOP
   EXECUTE format('ALTER TABLE %s DROP CONSTRAINT %I',r.tbl,r.conname);
   EXECUTE format('ALTER TABLE %s ADD CONSTRAINT %I FOREIGN KEY (%I) REFERENCES vres.projects(id) ON DELETE RESTRICT',r.tbl,r.conname,r.attname);
 END LOOP;
END $$;
