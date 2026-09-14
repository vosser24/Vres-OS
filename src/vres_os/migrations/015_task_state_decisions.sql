ALTER TABLE vres.task_state
    ADD COLUMN IF NOT EXISTS decisions jsonb NOT NULL DEFAULT '[]'::jsonb;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
          FROM information_schema.columns
         WHERE table_schema='vres'
           AND table_name='task_state'
           AND column_name='decisions'
           AND data_type <> 'jsonb'
    ) THEN
        RAISE EXCEPTION 'vres.task_state.decisions must be jsonb';
    END IF;
END $$;
