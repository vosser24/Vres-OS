UPDATE vres.tasks
   SET status='active', updated_at=now()
 WHERE status='new';

ALTER TABLE vres.tasks
    DROP CONSTRAINT IF EXISTS tasks_status_check;

ALTER TABLE vres.tasks
    ADD CONSTRAINT tasks_status_check
    CHECK (status IN ('active','waiting_user','blocked','completed','cancelled'));
