-- UP ====
-- Plan 20-06: Add last_used_at tracking to API keys.

ALTER TABLE "03_iam"."28_fct_iam_api_keys"
    ADD COLUMN IF NOT EXISTS last_used_at TIMESTAMP NULL;

COMMENT ON COLUMN "03_iam"."28_fct_iam_api_keys".last_used_at IS 'Timestamp of the last successful Bearer-token authentication. Updated fire-and-forget by middleware. NULL = never used since this migration.';

CREATE INDEX IF NOT EXISTS idx_28_fct_iam_api_keys_last_used
    ON "03_iam"."28_fct_iam_api_keys" (last_used_at)
    WHERE last_used_at IS NOT NULL;

-- DOWN ====
DROP INDEX IF EXISTS "03_iam".idx_28_fct_iam_api_keys_last_used;
ALTER TABLE "03_iam"."28_fct_iam_api_keys" DROP COLUMN IF EXISTS last_used_at;
