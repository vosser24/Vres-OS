ALTER TABLE vres.projects
    DROP COLUMN IF EXISTS metadata;

ALTER TABLE vres.tasks
    DROP COLUMN IF EXISTS metadata;
