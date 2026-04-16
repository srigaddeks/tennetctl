-- Additive migration for dedicated assignee passwordless portal.
-- 1) New challenge type: magic_link_assignee
-- 2) Session scope claim persistence: portal_mode on auth sessions
-- 3) Task assignment soft-delete flag for scoped assignee visibility filters

-- 1) Challenge type seed
INSERT INTO "03_auth_manage"."02_dim_challenge_types"
    (id, code, name, description, sort_order, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000000014',
       'magic_link_assignee',
       'Magic Link (Assignee)',
       'One-time assignee portal login challenge sent via email',
       31,
       NOW(), NOW()
WHERE NOT EXISTS (
    SELECT 1 FROM "03_auth_manage"."02_dim_challenge_types" WHERE code = 'magic_link_assignee'
);

-- 2) Auth session portal mode column
ALTER TABLE "03_auth_manage"."10_trx_auth_sessions"
    ADD COLUMN IF NOT EXISTS portal_mode VARCHAR(50) NULL;

ALTER TABLE "03_auth_manage"."10_trx_auth_sessions"
    DROP CONSTRAINT IF EXISTS ck_10_trx_auth_sessions_portal_mode;

ALTER TABLE "03_auth_manage"."10_trx_auth_sessions"
    ADD CONSTRAINT ck_10_trx_auth_sessions_portal_mode
        CHECK (portal_mode IS NULL OR portal_mode IN ('assignee'));

CREATE INDEX IF NOT EXISTS idx_10_trx_auth_sessions_portal_mode
    ON "03_auth_manage"."10_trx_auth_sessions" (portal_mode)
    WHERE portal_mode IS NOT NULL AND revoked_at IS NULL;

-- 3) Task assignment is_deleted flag (guarded: tasks schema may not exist in minimal test stacks)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = '08_tasks'
          AND table_name = '31_lnk_task_assignments'
    ) THEN
        ALTER TABLE "08_tasks"."31_lnk_task_assignments"
            ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN NOT NULL DEFAULT FALSE;

        CREATE INDEX IF NOT EXISTS idx_31_lnk_task_assignments_active_user
            ON "08_tasks"."31_lnk_task_assignments" (user_id)
            WHERE is_deleted = FALSE;
    END IF;
END $$;
