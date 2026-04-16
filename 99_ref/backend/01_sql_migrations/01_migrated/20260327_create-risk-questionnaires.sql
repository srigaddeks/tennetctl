-- ─────────────────────────────────────────────────────────────────────────────
-- 37_FCT_RISK_QUESTIONNAIRES
-- Master questionnaire template registry
--
-- Scope: Platform-level templates (tenant_key scoped)
--   - One record per questionnaire type (e.g. "Standard Risk Business Context")
--   - Tracks current_status lifecycle: draft → published → archived
--   - active_version_id points to the currently live version
--
-- Versioning: Immutable once published. Each new publish creates a new
--   record in 38_vrs_risk_questionnaire_versions.
--
-- Schema: 14_risk_registry
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS "14_risk_registry"."37_fct_risk_questionnaires" (
    id                      UUID         NOT NULL,
    tenant_key              VARCHAR(100) NOT NULL,
    questionnaire_code      VARCHAR(100) NOT NULL,   -- unique slug: e.g. "global-risk-v1"
    name                    VARCHAR(255) NOT NULL,
    description             TEXT         NULL,
    intended_scope          VARCHAR(50)  NOT NULL DEFAULT 'platform',  -- platform, org, workspace
    current_status          VARCHAR(50)  NOT NULL DEFAULT 'draft',     -- draft, published, archived
    latest_version_number   INTEGER      NOT NULL DEFAULT 0,
    active_version_id       UUID         NULL,       -- FK to 38_vrs; NULL until first publish
    is_active               BOOLEAN      NOT NULL DEFAULT TRUE,
    is_disabled             BOOLEAN      NOT NULL DEFAULT FALSE,
    is_deleted              BOOLEAN      NOT NULL DEFAULT FALSE,
    is_test                 BOOLEAN      NOT NULL DEFAULT FALSE,
    is_system               BOOLEAN      NOT NULL DEFAULT FALSE,
    is_locked               BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at              TIMESTAMP    NOT NULL,
    updated_at              TIMESTAMP    NOT NULL,
    created_by              UUID         NULL,
    updated_by              UUID         NULL,
    deleted_at              TIMESTAMP    NULL,
    deleted_by              UUID         NULL,
    CONSTRAINT pk_37_fct_risk_questionnaires              PRIMARY KEY (id),
    CONSTRAINT uq_37_fct_risk_questionnaires_code         UNIQUE (tenant_key, questionnaire_code),
    CONSTRAINT ck_37_fct_risk_questionnaires_scope        CHECK (intended_scope IN ('platform', 'org', 'workspace')),
    CONSTRAINT ck_37_fct_risk_questionnaires_status       CHECK (current_status IN ('draft', 'published', 'archived'))
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_37_fct_risk_questionnaires_tenant
    ON "14_risk_registry"."37_fct_risk_questionnaires" (tenant_key)
    WHERE is_deleted = FALSE;

CREATE INDEX IF NOT EXISTS idx_37_fct_risk_questionnaires_status
    ON "14_risk_registry"."37_fct_risk_questionnaires" (current_status)
    WHERE is_deleted = FALSE;

CREATE INDEX IF NOT EXISTS idx_37_fct_risk_questionnaires_active_version
    ON "14_risk_registry"."37_fct_risk_questionnaires" (active_version_id)
    WHERE active_version_id IS NOT NULL AND is_deleted = FALSE;

COMMENT ON TABLE "14_risk_registry"."37_fct_risk_questionnaires"
    IS 'Master questionnaire template registry. One row per questionnaire type. Versioned via 38_vrs_risk_questionnaire_versions.';
COMMENT ON COLUMN "14_risk_registry"."37_fct_risk_questionnaires".questionnaire_code
    IS 'Unique slug used to identify this questionnaire in code and assignments.';
COMMENT ON COLUMN "14_risk_registry"."37_fct_risk_questionnaires".active_version_id
    IS 'Points to the currently active published version. NULL if never published.';
