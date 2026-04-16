-- Add scope_org_id and scope_workspace_id to control tests so they are org+workspace scoped.
-- Backfills existing tests to the tenant's first real org (same as frameworks).

ALTER TABLE "05_grc_library"."14_fct_control_tests"
    ADD COLUMN IF NOT EXISTS scope_org_id UUID NULL
        REFERENCES "03_auth_manage"."29_fct_orgs" (id);

ALTER TABLE "05_grc_library"."14_fct_control_tests"
    ADD COLUMN IF NOT EXISTS scope_workspace_id UUID NULL
        REFERENCES "03_auth_manage"."34_fct_workspaces" (id);

CREATE INDEX IF NOT EXISTS idx_14_fct_control_tests_scope_org
    ON "05_grc_library"."14_fct_control_tests" (scope_org_id) WHERE is_deleted = FALSE;

CREATE INDEX IF NOT EXISTS idx_14_fct_control_tests_scope_ws
    ON "05_grc_library"."14_fct_control_tests" (scope_workspace_id) WHERE is_deleted = FALSE;

-- Backfill existing tests to first workspace of the tenant's first real org
UPDATE "05_grc_library"."14_fct_control_tests" t
SET
    scope_org_id = (
        SELECT o.id
        FROM   "03_auth_manage"."29_fct_orgs" o
        WHERE  o.tenant_key = t.tenant_key
          AND  o.is_deleted  = FALSE
        ORDER  BY o.created_at ASC
        LIMIT  1
        OFFSET 1
    ),
    scope_workspace_id = (
        SELECT w.id
        FROM   "03_auth_manage"."34_fct_workspaces" w
        JOIN   "03_auth_manage"."29_fct_orgs" o ON o.id = w.org_id
        WHERE  o.tenant_key = t.tenant_key
          AND  o.is_deleted  = FALSE
          AND  w.is_deleted  = FALSE
          AND  w.workspace_type_code != 'sandbox'
        ORDER  BY o.created_at ASC, w.created_at ASC
        LIMIT  1
        OFFSET 1
    )
WHERE  t.scope_org_id IS NULL
  AND  t.tenant_key   != '__platform__'
  AND  t.is_deleted   = FALSE;
