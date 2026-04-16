-- ─────────────────────────────────────────────────────────────────────────────
-- GRC LIBRARY ENHANCEMENTS
-- 1. Risk library deployments table — orgs deploy global risks as workspace instances
-- 2. Framework deployment upgrade events — track per-control change on upgrade
-- ─────────────────────────────────────────────────────────────────────────────

-- ── 1. Risk library deployments ──────────────────────────────────────────────
-- When an org deploys global risks to a workspace, we record which global risks
-- were instantiated and can later query/sync them.

CREATE TABLE IF NOT EXISTS "05_grc_library"."17_fct_risk_library_deployments" (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_key          TEXT NOT NULL,
    org_id              UUID NOT NULL,
    workspace_id        UUID NOT NULL,
    global_risk_id      UUID NOT NULL
                            REFERENCES "05_grc_library"."50_fct_global_risks"(id),
    -- optional link to the workspace risk that was created from this global risk
    workspace_risk_id   UUID,   -- FK to 14_risk_registry.10_fct_risks once created
    deployment_status   TEXT NOT NULL DEFAULT 'active'
                            CHECK (deployment_status IN ('active', 'removed')),
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by          UUID,
    updated_by          UUID,
    -- one active deployment per workspace+global_risk
    UNIQUE (org_id, workspace_id, global_risk_id)
);

CREATE INDEX IF NOT EXISTS idx_risk_lib_deploys_org
    ON "05_grc_library"."17_fct_risk_library_deployments" (org_id);
CREATE INDEX IF NOT EXISTS idx_risk_lib_deploys_workspace
    ON "05_grc_library"."17_fct_risk_library_deployments" (workspace_id);
CREATE INDEX IF NOT EXISTS idx_risk_lib_deploys_global_risk
    ON "05_grc_library"."17_fct_risk_library_deployments" (global_risk_id);

-- ── 2. View: risk library deployments enriched ───────────────────────────────
CREATE OR REPLACE VIEW "05_grc_library"."45_vw_risk_library_deployments" AS
SELECT
    d.id,
    d.tenant_key,
    d.org_id::text,
    d.workspace_id::text,
    d.global_risk_id::text,
    d.workspace_risk_id::text,
    d.deployment_status,
    d.is_active,
    d.created_at::text,
    d.updated_at::text,
    d.created_by::text,
    -- global risk fields
    gr.risk_code,
    gr.risk_category_code,
    gr.inherent_likelihood,
    gr.inherent_impact,
    gr.inherent_risk_score,
    gr.is_active AS global_risk_is_active,
    -- global risk properties
    p_title.property_value          AS title,
    p_desc.property_value           AS short_description,
    p_mit.property_value            AS mitigation_guidance,
    -- dimensions
    rc.name                         AS risk_category_name,
    rl.name                         AS risk_level_name,
    rl.color_hex                    AS risk_level_color,
    gr.risk_level_code,
    -- linked controls count
    (SELECT COUNT(*) FROM "05_grc_library"."61_lnk_global_risk_control_mappings" cm
     WHERE cm.global_risk_id = gr.id)::int AS linked_control_count
FROM "05_grc_library"."17_fct_risk_library_deployments" d
JOIN "05_grc_library"."50_fct_global_risks" gr
    ON gr.id = d.global_risk_id AND gr.is_deleted = FALSE
LEFT JOIN "05_grc_library"."56_dtl_global_risk_properties" p_title
    ON p_title.global_risk_id = gr.id AND p_title.property_key = 'title'
LEFT JOIN "05_grc_library"."56_dtl_global_risk_properties" p_desc
    ON p_desc.global_risk_id = gr.id AND p_desc.property_key = 'short_description'
LEFT JOIN "05_grc_library"."56_dtl_global_risk_properties" p_mit
    ON p_mit.global_risk_id = gr.id AND p_mit.property_key = 'mitigation_guidance'
LEFT JOIN "14_risk_registry"."02_dim_risk_categories" rc
    ON rc.code = gr.risk_category_code
LEFT JOIN "14_risk_registry"."04_dim_risk_levels" rl
    ON rl.code = gr.risk_level_code;

-- ── 3. Permissions for risk library deployment ────────────────────────────────
INSERT INTO "03_auth_manage"."15_dim_feature_permissions"
    (id, code, permission_action_code, feature_flag_code, name, description, created_at, updated_at)
VALUES
    (gen_random_uuid(), 'global_risk_library.create', 'create', 'global_risk_library',
     'Deploy Risk Library',
     'Can deploy global risks from the library into workspace risk registries.',
     NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- Assign to platform_super_admin
INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
    (id, role_id, feature_permission_id,
     is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
     created_at, updated_at, created_by, updated_by)
SELECT gen_random_uuid(), r.id, fp.id,
       TRUE, FALSE, FALSE, FALSE, FALSE, FALSE,
       NOW(), NOW(), NULL, NULL
FROM "03_auth_manage"."16_fct_roles" r
CROSS JOIN "03_auth_manage"."15_dim_feature_permissions" fp
WHERE r.code = 'platform_super_admin' AND fp.code = 'global_risk_library.create'
  AND NOT EXISTS (
    SELECT 1 FROM "03_auth_manage"."20_lnk_role_feature_permissions" lnk
    WHERE lnk.role_id = r.id AND lnk.feature_permission_id = fp.id
  );
