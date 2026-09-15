UPDATE vres.task_state
   SET validation_status='pending', updated_at=now()
 WHERE validation_status='not_required';

ALTER TABLE vres.task_state
    ALTER COLUMN validation_status SET DEFAULT 'pending';

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
          FROM pg_constraint
         WHERE conrelid='vres.task_state'::regclass
           AND conname='task_state_validation_status_check'
    ) THEN
        ALTER TABLE vres.task_state
            ADD CONSTRAINT task_state_validation_status_check
            CHECK (validation_status IN ('pending','passed','failed'));
    END IF;
END $$;
