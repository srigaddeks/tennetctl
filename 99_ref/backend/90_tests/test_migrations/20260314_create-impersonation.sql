-- ============================================================================
-- Migration: User Impersonation Support
-- Date: 2026-03-14
-- Description: Adds impersonation columns to auth sessions and seeds
--              the user_impersonation feature flag with permissions.
-- ============================================================================

-- ---------------------------------------------------------------------------
-- 1. Extend 10_trx_auth_sessions with impersonation columns
-- ---------------------------------------------------------------------------

ALTER TABLE "03_auth_manage"."10_trx_auth_sessions"
    ADD COLUMN IF NOT EXISTS is_impersonation BOOLEAN NOT NULL DEFAULT FALSE;

ALTER TABLE "03_auth_manage"."10_trx_auth_sessions"
    ADD COLUMN IF NOT EXISTS impersonator_user_id UUID NULL;

ALTER TABLE "03_auth_manage"."10_trx_auth_sessions"
    ADD COLUMN IF NOT EXISTS impersonation_reason VARCHAR(500) NULL;

-- FK: impersonator must be a valid user
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'fk_10_trx_auth_sessions_impersonator_user_id'
    ) THEN
        ALTER TABLE "03_auth_manage"."10_trx_auth_sessions"
            ADD CONSTRAINT fk_10_trx_auth_sessions_impersonator_user_id
                FOREIGN KEY (impersonator_user_id)
                REFERENCES "03_auth_manage"."03_fct_users" (id)
                ON DELETE RESTRICT;
    END IF;
END
$$;

-- Partial index: fast lookup of active impersonation sessions by impersonator
CREATE INDEX IF NOT EXISTS idx_10_trx_auth_sessions_impersonator
    ON "03_auth_manage"."10_trx_auth_sessions" (impersonator_user_id)
    WHERE impersonator_user_id IS NOT NULL AND revoked_at IS NULL;

-- ---------------------------------------------------------------------------
-- 2. Seed feature flag: user_impersonation (admin category, dev-only)
-- ---------------------------------------------------------------------------

INSERT INTO "03_auth_manage"."14_dim_feature_flags" (
    id, code, name, description, feature_flag_category_code, access_mode, lifecycle_state, initial_audience,
    env_dev, env_staging, env_prod, created_at, updated_at
)
SELECT '00000000-0000-0000-0000-000000000410', 'user_impersonation',
       'User Impersonation',
       'Allow privileged admins to impersonate other users for support and debugging.',
       'admin', 'permissioned', 'active', 'platform_super_admin',
       TRUE, FALSE, FALSE,
       TIMESTAMP '2026-03-14 00:00:00', TIMESTAMP '2026-03-14 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."14_dim_feature_flags" WHERE code = 'user_impersonation');

-- ---------------------------------------------------------------------------
-- 3. Seed feature permissions: enable + view
-- ---------------------------------------------------------------------------

INSERT INTO "03_auth_manage"."15_dim_feature_permissions" (
    id, code, feature_flag_code, permission_action_code, name, description, created_at, updated_at
)
SELECT '00000000-0000-0000-0000-000000000520', 'user_impersonation.enable',
       'user_impersonation', 'enable',
       'Start Impersonation', 'Start impersonating another user.',
       TIMESTAMP '2026-03-14 00:00:00', TIMESTAMP '2026-03-14 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'user_impersonation.enable');

INSERT INTO "03_auth_manage"."15_dim_feature_permissions" (
    id, code, feature_flag_code, permission_action_code, name, description, created_at, updated_at
)
SELECT '00000000-0000-0000-0000-000000000521', 'user_impersonation.view',
       'user_impersonation', 'view',
       'View Impersonation Sessions', 'View active impersonation sessions.',
       TIMESTAMP '2026-03-14 00:00:00', TIMESTAMP '2026-03-14 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'user_impersonation.view');
