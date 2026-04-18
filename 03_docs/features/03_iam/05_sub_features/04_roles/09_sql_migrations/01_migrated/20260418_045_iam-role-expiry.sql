-- UP ====

ALTER TABLE "03_iam"."42_lnk_user_roles"
    ADD COLUMN IF NOT EXISTS expires_at  TIMESTAMP NULL,
    ADD COLUMN IF NOT EXISTS revoked_at  TIMESTAMP NULL;

CREATE INDEX IF NOT EXISTS idx_iam_lnk_user_roles_expires
    ON "03_iam"."42_lnk_user_roles" (expires_at)
    WHERE expires_at IS NOT NULL;

COMMENT ON COLUMN "03_iam"."42_lnk_user_roles".expires_at IS 'Optional expiry; NULL = permanent.';
COMMENT ON COLUMN "03_iam"."42_lnk_user_roles".revoked_at IS 'Set by expiry sweeper when expires_at < now().';

-- DOWN ====

DROP INDEX IF EXISTS "03_iam".idx_iam_lnk_user_roles_expires;

ALTER TABLE "03_iam"."42_lnk_user_roles"
    DROP COLUMN IF EXISTS expires_at,
    DROP COLUMN IF EXISTS revoked_at;
