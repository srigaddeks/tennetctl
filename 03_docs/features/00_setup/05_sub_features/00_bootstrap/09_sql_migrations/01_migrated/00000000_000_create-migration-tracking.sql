-- UP ====

-- Migration tracking table bootstrap
-- The migrator creates this schema/table via bootstrap logic.
-- This file exists so the migration is recorded for consistency.
SELECT 1;

-- DOWN ====

-- Cannot roll back the tracking table — it would destroy all migration history.
-- This is intentionally a no-op.
SELECT 1;
