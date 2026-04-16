-- Add org/workspace scoping to framework builder sessions.
-- This ensures builder create/enhance/apply flows are bound to the current org/workspace context.

ALTER TABLE "20_ai"."60_fct_builder_sessions"
    ADD COLUMN IF NOT EXISTS scope_org_id UUID NULL
        REFERENCES "03_auth_manage"."29_fct_orgs"(id);

ALTER TABLE "20_ai"."60_fct_builder_sessions"
    ADD COLUMN IF NOT EXISTS scope_workspace_id UUID NULL
        REFERENCES "03_auth_manage"."34_fct_workspaces"(id);

CREATE INDEX IF NOT EXISTS idx_builder_sessions_scope
    ON "20_ai"."60_fct_builder_sessions" (tenant_key, scope_org_id, scope_workspace_id, created_at DESC);
