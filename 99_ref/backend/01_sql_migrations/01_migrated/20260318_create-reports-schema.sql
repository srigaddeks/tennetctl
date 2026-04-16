-- ── GRC Reports table ────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS "20_ai"."50_fct_reports" (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_key              TEXT NOT NULL,
    org_id                  UUID,
    workspace_id            UUID,
    report_type             TEXT NOT NULL,
    status_code             TEXT NOT NULL DEFAULT 'queued',
    title                   TEXT,
    parameters_json         JSONB NOT NULL DEFAULT '{}',
    content_markdown        TEXT,
    word_count              INTEGER,
    token_count             INTEGER,
    generated_by_user_id    UUID,
    agent_run_id            UUID,
    job_id                  UUID,
    error_message           TEXT,
    is_auto_generated       BOOLEAN NOT NULL DEFAULT FALSE,
    trigger_entity_type     TEXT,
    trigger_entity_id       UUID,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at            TIMESTAMPTZ,
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_reports_tenant_org
    ON "20_ai"."50_fct_reports" (tenant_key, org_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_reports_tenant_type
    ON "20_ai"."50_fct_reports" (tenant_key, report_type, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_reports_job_id
    ON "20_ai"."50_fct_reports" (job_id)
    WHERE job_id IS NOT NULL;

-- ── Agent type ────────────────────────────────────────────────────────────────
INSERT INTO "20_ai"."02_dim_agent_types" (code, name, description, is_active)
VALUES ('report_generator', 'Report Generator', 'Generates AI-powered GRC compliance and audit reports', true)
ON CONFLICT (code) DO NOTHING;

-- ── Feature flag ──────────────────────────────────────────────────────────────
INSERT INTO "03_auth_manage"."14_dim_feature_flags"
    (id, code, name, description, feature_scope, feature_flag_category_code,
     access_mode, lifecycle_state, initial_audience, env_dev, env_staging, env_prod,
     created_at, updated_at)
VALUES
    (gen_random_uuid(), 'reports', 'GRC Reports', 'AI-generated compliance and audit reports',
     'platform', 'grc', 'permissioned', 'active', 'all', true, true, true, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- ── Permissions ───────────────────────────────────────────────────────────────
INSERT INTO "03_auth_manage"."15_dim_feature_permissions"
    (id, code, feature_flag_code, permission_action_code, name, description, created_at, updated_at)
VALUES
    (gen_random_uuid(), 'reports.view',   'reports', 'view',   'View Reports',   'View GRC reports', NOW(), NOW()),
    (gen_random_uuid(), 'reports.create', 'reports', 'create', 'Create Reports', 'Generate GRC reports', NOW(), NOW()),
    (gen_random_uuid(), 'reports.delete', 'reports', 'delete', 'Delete Reports', 'Delete GRC reports', NOW(), NOW())
ON CONFLICT (feature_flag_code, permission_action_code) DO NOTHING;

-- ── Assign to super_admin ─────────────────────────────────────────────────────
INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
    (id, role_id, feature_permission_id, created_at, updated_at)
SELECT gen_random_uuid(), r.id, fp.id, NOW(), NOW()
FROM "03_auth_manage"."16_fct_roles" r
CROSS JOIN "03_auth_manage"."15_dim_feature_permissions" fp
WHERE r.code = 'super_admin'
  AND fp.feature_flag_code = 'reports'
ON CONFLICT DO NOTHING;
