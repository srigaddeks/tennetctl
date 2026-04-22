-- UP ====
-- Plan 20-04: Session limits — add last_activity_at for idle timeout enforcement.

ALTER TABLE "03_iam"."16_fct_sessions"
    ADD COLUMN IF NOT EXISTS last_activity_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP;

-- Backfill existing rows to created_at.
UPDATE "03_iam"."16_fct_sessions"
    SET last_activity_at = created_at
    WHERE last_activity_at = CURRENT_TIMESTAMP
      AND created_at < CURRENT_TIMESTAMP;

CREATE INDEX IF NOT EXISTS idx_16_fct_sessions_last_activity
    ON "03_iam"."16_fct_sessions" (last_activity_at)
    WHERE deleted_at IS NULL AND revoked_at IS NULL;

COMMENT ON COLUMN "03_iam"."16_fct_sessions".last_activity_at IS
    'Updated by middleware on each authenticated request. Used for idle timeout enforcement.';

-- DOWN ====
DROP INDEX IF EXISTS "03_iam".idx_16_fct_sessions_last_activity;
ALTER TABLE "03_iam"."16_fct_sessions" DROP COLUMN IF EXISTS last_activity_at;
