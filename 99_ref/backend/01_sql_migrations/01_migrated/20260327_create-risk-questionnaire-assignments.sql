-- ─────────────────────────────────────────────────────────────────────────────
-- 39_LNK_RISK_QUESTIONNAIRE_ASSIGNMENTS
-- Links a specific questionnaire version to an org or workspace
--
-- Scope: Tenant-scoped; assignment_scope determines level
--   - 'platform'  → org_id IS NULL, workspace_id IS NULL  (global default)
--   - 'org'       → org_id SET,    workspace_id IS NULL
--   - 'workspace' → org_id SET,    workspace_id SET
--
-- Resolution order (most specific wins):
--   workspace → org → platform
--
-- Only ONE active assignment per (tenant_key, assignment_scope, org_id, workspace_id).
-- Older assignments are deactivated (is_active = FALSE) on upsert.
--
-- Schema: 14_risk_registry
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS "14_risk_registry"."39_lnk_risk_questionnaire_assignments" (
    id                          UUID         NOT NULL,
    tenant_key                  VARCHAR(100) NOT NULL,
    assignment_scope            VARCHAR(50)  NOT NULL,   -- platform, org, workspace
    org_id                      UUID         NULL,
    workspace_id                UUID         NULL,
    questionnaire_version_id    UUID         NOT NULL,   -- FK to 38_vrs_risk_questionnaire_versions
    is_active                   BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at                  TIMESTAMP    NOT NULL,
    updated_at                  TIMESTAMP    NOT NULL,
    created_by                  UUID         NULL,
    updated_by                  UUID         NULL,
    CONSTRAINT pk_39_lnk_risk_questionnaire_assignments               PRIMARY KEY (id),
    CONSTRAINT ck_39_lnk_risk_questionnaire_assignments_scope         CHECK (assignment_scope IN ('platform', 'org', 'workspace')),
    CONSTRAINT fk_39_lnk_risk_questionnaire_assignments_version       FOREIGN KEY (questionnaire_version_id)
        REFERENCES "14_risk_registry"."38_vrs_risk_questionnaire_versions" (id),
    CONSTRAINT fk_39_lnk_risk_questionnaire_assignments_org           FOREIGN KEY (org_id)
        REFERENCES "03_auth_manage"."29_fct_orgs" (id),
    CONSTRAINT fk_39_lnk_risk_questionnaire_assignments_workspace     FOREIGN KEY (workspace_id)
        REFERENCES "03_auth_manage"."34_fct_workspaces" (id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_39_lnk_risk_questionnaire_assignments_tenant
    ON "14_risk_registry"."39_lnk_risk_questionnaire_assignments" (tenant_key)
    WHERE is_active = TRUE;

CREATE INDEX IF NOT EXISTS idx_39_lnk_risk_questionnaire_assignments_scope
    ON "14_risk_registry"."39_lnk_risk_questionnaire_assignments" (tenant_key, assignment_scope)
    WHERE is_active = TRUE;

CREATE INDEX IF NOT EXISTS idx_39_lnk_risk_questionnaire_assignments_org
    ON "14_risk_registry"."39_lnk_risk_questionnaire_assignments" (org_id)
    WHERE is_active = TRUE AND org_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_39_lnk_risk_questionnaire_assignments_workspace
    ON "14_risk_registry"."39_lnk_risk_questionnaire_assignments" (workspace_id)
    WHERE is_active = TRUE AND workspace_id IS NOT NULL;

COMMENT ON TABLE "14_risk_registry"."39_lnk_risk_questionnaire_assignments"
    IS 'Links a published questionnaire version to a scope (platform/org/workspace). Resolution order: workspace > org > platform.';
COMMENT ON COLUMN "14_risk_registry"."39_lnk_risk_questionnaire_assignments".assignment_scope
    IS 'Scope level: platform (global default), org (org-wide), workspace (workspace-specific).';
COMMENT ON COLUMN "14_risk_registry"."39_lnk_risk_questionnaire_assignments".is_active
    IS 'Only one active assignment per scope+org+workspace at a time. Old ones are deactivated on upsert.';
