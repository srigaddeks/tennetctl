-- ============================================================
-- Assessment & Findings module (09_assessments schema)
-- Adapted to reference org_id/workspace_id and 05_grc_library
-- controls directly (no deployment/evidence vault prerequisite)
-- ============================================================

-- Schema created in 20260313_a_create-all-schemas.sql

-- ─────────────────────────────────────────────
-- DIMENSION: assessment types
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS "09_assessments"."02_dim_assessment_types" (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    code        VARCHAR(50) NOT NULL,
    name        VARCHAR(100) NOT NULL,
    description TEXT,
    icon        VARCHAR(50),
    sort_order  INTEGER     NOT NULL DEFAULT 0,
    is_active   BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_assessment_types_code UNIQUE (code)
);

INSERT INTO "09_assessments"."02_dim_assessment_types" (code, name, description, sort_order) VALUES
    ('internal_audit',      'Internal Audit',       'Routine internal compliance review',                      1),
    ('external_prep',       'External Audit Prep',  'Preparation session before an external audit',            2),
    ('certification_audit', 'Certification Audit',  'Formal assessment for a compliance certification',        3),
    ('gap_analysis',        'Gap Analysis',         'Identify compliance gaps across controls and frameworks',  4),
    ('readiness_review',    'Readiness Review',     'Pre-audit readiness check',                               5)
ON CONFLICT (code) DO NOTHING;

-- ─────────────────────────────────────────────
-- DIMENSION: assessment statuses
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS "09_assessments"."03_dim_assessment_statuses" (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    code        VARCHAR(50) NOT NULL,
    name        VARCHAR(100) NOT NULL,
    description TEXT,
    icon        VARCHAR(50),
    sort_order  INTEGER     NOT NULL DEFAULT 0,
    is_active   BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_assessment_statuses_code UNIQUE (code)
);

INSERT INTO "09_assessments"."03_dim_assessment_statuses" (code, name, description, sort_order) VALUES
    ('planned',     'Planned',     'Assessment is scheduled but not yet started',  1),
    ('in_progress', 'In Progress', 'Assessment is actively being conducted',       2),
    ('review',      'In Review',   'Findings are being reviewed before finalizing',3),
    ('completed',   'Completed',   'Assessment is done and findings are locked',   4),
    ('cancelled',   'Cancelled',   'Assessment was abandoned',                     5)
ON CONFLICT (code) DO NOTHING;

-- ─────────────────────────────────────────────
-- DIMENSION: finding severities
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS "09_assessments"."04_dim_finding_severities" (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    code        VARCHAR(50) NOT NULL,
    name        VARCHAR(100) NOT NULL,
    description TEXT,
    icon        VARCHAR(50),
    sort_order  INTEGER     NOT NULL DEFAULT 0,
    is_active   BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_finding_severities_code UNIQUE (code)
);

INSERT INTO "09_assessments"."04_dim_finding_severities" (code, name, description, sort_order) VALUES
    ('critical',       'Critical',      'Requires immediate remediation',              1),
    ('high',           'High',          'Must be addressed promptly',                  2),
    ('medium',         'Medium',        'Should be resolved in the next cycle',        3),
    ('low',            'Low',           'Minor issue, address at convenience',         4),
    ('informational',  'Informational', 'No action required, noted for awareness',     5)
ON CONFLICT (code) DO NOTHING;

-- ─────────────────────────────────────────────
-- DIMENSION: finding statuses
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS "09_assessments"."05_dim_finding_statuses" (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    code        VARCHAR(50) NOT NULL,
    name        VARCHAR(100) NOT NULL,
    description TEXT,
    icon        VARCHAR(50),
    sort_order  INTEGER     NOT NULL DEFAULT 0,
    is_active   BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_finding_statuses_code UNIQUE (code)
);

INSERT INTO "09_assessments"."05_dim_finding_statuses" (code, name, description, sort_order) VALUES
    ('open',             'Open',             'Finding has been recorded, not yet addressed', 1),
    ('in_remediation',   'In Remediation',   'Assignee is actively working on a fix',        2),
    ('verified_closed',  'Verified Closed',  'Remediation verified and finding resolved',    3),
    ('accepted',         'Accepted',         'Acknowledged as a known/accepted risk',        4),
    ('disputed',         'Disputed',         'Finding is being challenged by the assignee',  5)
ON CONFLICT (code) DO NOTHING;

-- ─────────────────────────────────────────────
-- DIMENSION: assessment property keys (EAV)
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS "09_assessments"."06_dim_assessment_property_keys" (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    code        VARCHAR(80) NOT NULL,
    name        VARCHAR(120) NOT NULL,
    description TEXT,
    data_type   VARCHAR(30) NOT NULL DEFAULT 'text',
    is_required BOOLEAN     NOT NULL DEFAULT FALSE,
    sort_order  INTEGER     NOT NULL DEFAULT 0,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_assessment_property_keys_code UNIQUE (code)
);

INSERT INTO "09_assessments"."06_dim_assessment_property_keys" (code, name, description, data_type, is_required, sort_order) VALUES
    ('name',        'Name',        'Assessment session name',         'text', TRUE,  1),
    ('description', 'Description', 'What this assessment covers',     'text', FALSE, 2),
    ('scope_notes', 'Scope Notes', 'Scope boundaries and exclusions', 'text', FALSE, 3)
ON CONFLICT (code) DO NOTHING;

-- ─────────────────────────────────────────────
-- DIMENSION: finding property keys (EAV)
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS "09_assessments"."07_dim_finding_property_keys" (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    code        VARCHAR(80) NOT NULL,
    name        VARCHAR(120) NOT NULL,
    description TEXT,
    data_type   VARCHAR(30) NOT NULL DEFAULT 'text',
    is_required BOOLEAN     NOT NULL DEFAULT FALSE,
    sort_order  INTEGER     NOT NULL DEFAULT 0,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_finding_property_keys_code UNIQUE (code)
);

INSERT INTO "09_assessments"."07_dim_finding_property_keys" (code, name, description, data_type, is_required, sort_order) VALUES
    ('title',          'Title',          'Finding title',             'text', TRUE,  1),
    ('description',    'Description',    'Detailed finding notes',    'text', FALSE, 2),
    ('recommendation', 'Recommendation', 'Suggested remediation',     'text', FALSE, 3)
ON CONFLICT (code) DO NOTHING;

-- ─────────────────────────────────────────────
-- FACT: assessments (LEAN)
-- Scoped to org_id + workspace_id (no deployment FK needed)
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS "09_assessments"."10_fct_assessments" (
    id                      UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_key              VARCHAR(64) NOT NULL,
    assessment_code         VARCHAR(100) NOT NULL,
    org_id                  UUID        NOT NULL,
    workspace_id            UUID,
    framework_id            UUID,           -- optional scope to a specific framework
    assessment_type_code    VARCHAR(50) NOT NULL REFERENCES "09_assessments"."02_dim_assessment_types"(code),
    assessment_status_code  VARCHAR(30) NOT NULL DEFAULT 'planned' REFERENCES "09_assessments"."03_dim_assessment_statuses"(code),
    lead_assessor_id        UUID,
    scheduled_start         TIMESTAMPTZ,
    scheduled_end           TIMESTAMPTZ,
    actual_start            TIMESTAMPTZ,
    actual_end              TIMESTAMPTZ,
    is_locked               BOOLEAN     NOT NULL DEFAULT FALSE,
    is_active               BOOLEAN     NOT NULL DEFAULT TRUE,
    is_deleted              BOOLEAN     NOT NULL DEFAULT FALSE,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by              UUID,
    updated_by              UUID,
    deleted_at              TIMESTAMPTZ,
    deleted_by              UUID,
    CONSTRAINT uq_assessments_code UNIQUE (tenant_key, assessment_code)
);

CREATE INDEX IF NOT EXISTS idx_10_fct_assessments_tenant
    ON "09_assessments"."10_fct_assessments" (tenant_key)
    WHERE is_deleted = FALSE;

CREATE INDEX IF NOT EXISTS idx_10_fct_assessments_org
    ON "09_assessments"."10_fct_assessments" (org_id, workspace_id)
    WHERE is_deleted = FALSE;

CREATE INDEX IF NOT EXISTS idx_10_fct_assessments_status
    ON "09_assessments"."10_fct_assessments" (assessment_status_code)
    WHERE is_deleted = FALSE;

CREATE INDEX IF NOT EXISTS idx_10_fct_assessments_framework
    ON "09_assessments"."10_fct_assessments" (framework_id)
    WHERE is_deleted = FALSE AND framework_id IS NOT NULL;

-- ─────────────────────────────────────────────
-- FACT: findings (LEAN)
-- References control from 05_grc_library (no deployment FK)
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS "09_assessments"."11_fct_findings" (
    id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id       UUID        NOT NULL REFERENCES "09_assessments"."10_fct_assessments"(id),
    control_id          UUID,           -- optional ref to "05_grc_library"."13_fct_controls"
    risk_id             UUID,           -- optional ref to "14_risk_registry"."10_fct_risks"
    severity_code       VARCHAR(20) NOT NULL REFERENCES "09_assessments"."04_dim_finding_severities"(code),
    finding_type        VARCHAR(30) NOT NULL DEFAULT 'observation'
                        CHECK (finding_type IN ('non_conformity','observation','opportunity','recommendation')),
    finding_status_code VARCHAR(30) NOT NULL DEFAULT 'open' REFERENCES "09_assessments"."05_dim_finding_statuses"(code),
    assigned_to         UUID,
    remediation_due_date TIMESTAMPTZ,
    is_active           BOOLEAN     NOT NULL DEFAULT TRUE,
    is_deleted          BOOLEAN     NOT NULL DEFAULT FALSE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by          UUID,
    updated_by          UUID,
    deleted_at          TIMESTAMPTZ,
    deleted_by          UUID
);

CREATE INDEX IF NOT EXISTS idx_11_fct_findings_assessment_severity
    ON "09_assessments"."11_fct_findings" (assessment_id, severity_code)
    WHERE is_deleted = FALSE;

CREATE INDEX IF NOT EXISTS idx_11_fct_findings_status
    ON "09_assessments"."11_fct_findings" (finding_status_code)
    WHERE is_deleted = FALSE;

CREATE INDEX IF NOT EXISTS idx_11_fct_findings_assigned
    ON "09_assessments"."11_fct_findings" (assigned_to)
    WHERE is_deleted = FALSE;

-- ─────────────────────────────────────────────
-- TRANSACTION: finding responses (append-only)
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS "09_assessments"."20_trx_finding_responses" (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    finding_id      UUID        NOT NULL REFERENCES "09_assessments"."11_fct_findings"(id),
    responder_id    UUID        NOT NULL,
    responded_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
    -- no soft-delete: responses are immutable
);

CREATE INDEX IF NOT EXISTS idx_20_trx_responses_finding
    ON "09_assessments"."20_trx_finding_responses" (finding_id, responded_at);

-- ─────────────────────────────────────────────
-- DETAIL: assessment properties (EAV)
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS "09_assessments"."21_dtl_assessment_properties" (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id   UUID        NOT NULL REFERENCES "09_assessments"."10_fct_assessments"(id),
    property_key    VARCHAR(80) NOT NULL REFERENCES "09_assessments"."06_dim_assessment_property_keys"(code),
    property_value  TEXT        NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      UUID,
    updated_by      UUID,
    CONSTRAINT uq_assessment_properties UNIQUE (assessment_id, property_key)
);

CREATE INDEX IF NOT EXISTS idx_21_dtl_assessment_props
    ON "09_assessments"."21_dtl_assessment_properties" (assessment_id);

-- ─────────────────────────────────────────────
-- DETAIL: finding properties (EAV)
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS "09_assessments"."22_dtl_finding_properties" (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    finding_id      UUID        NOT NULL REFERENCES "09_assessments"."11_fct_findings"(id),
    property_key    VARCHAR(80) NOT NULL REFERENCES "09_assessments"."07_dim_finding_property_keys"(code),
    property_value  TEXT        NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      UUID,
    updated_by      UUID,
    CONSTRAINT uq_finding_properties UNIQUE (finding_id, property_key)
);

CREATE INDEX IF NOT EXISTS idx_22_dtl_finding_props
    ON "09_assessments"."22_dtl_finding_properties" (finding_id);

-- ─────────────────────────────────────────────
-- DETAIL: finding response properties (EAV, immutable)
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS "09_assessments"."23_dtl_finding_response_properties" (
    id                   UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    finding_response_id  UUID        NOT NULL REFERENCES "09_assessments"."20_trx_finding_responses"(id),
    property_key         VARCHAR(80) NOT NULL DEFAULT 'response_text',
    property_value       TEXT        NOT NULL,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_response_properties UNIQUE (finding_response_id, property_key)
);

CREATE INDEX IF NOT EXISTS idx_23_dtl_response_props
    ON "09_assessments"."23_dtl_finding_response_properties" (finding_response_id);

-- ─────────────────────────────────────────────
-- VIEW: assessment detail
-- ─────────────────────────────────────────────
CREATE OR REPLACE VIEW "09_assessments"."40_vw_assessment_detail" AS
SELECT
    a.id,
    a.tenant_key,
    a.assessment_code,
    a.org_id,
    a.workspace_id,
    a.framework_id,
    a.assessment_type_code,
    a.assessment_status_code,
    a.lead_assessor_id,
    a.scheduled_start,
    a.scheduled_end,
    a.actual_start,
    a.actual_end,
    a.is_locked,
    at_.name                            AS assessment_type_name,
    ast.name                            AS assessment_status_name,
    name_p.property_value               AS name,
    desc_p.property_value               AS description,
    scope_p.property_value              AS scope_notes,
    (SELECT COUNT(*) FROM "09_assessments"."11_fct_findings" f
     WHERE f.assessment_id = a.id AND f.is_deleted = FALSE) AS finding_count,
    a.is_active,
    a.is_deleted,
    a.created_at,
    a.updated_at,
    a.created_by
FROM "09_assessments"."10_fct_assessments" a
LEFT JOIN "09_assessments"."02_dim_assessment_types" at_  ON at_.code  = a.assessment_type_code
LEFT JOIN "09_assessments"."03_dim_assessment_statuses" ast ON ast.code = a.assessment_status_code
LEFT JOIN "09_assessments"."21_dtl_assessment_properties" name_p
    ON name_p.assessment_id = a.id AND name_p.property_key = 'name'
LEFT JOIN "09_assessments"."21_dtl_assessment_properties" desc_p
    ON desc_p.assessment_id = a.id AND desc_p.property_key = 'description'
LEFT JOIN "09_assessments"."21_dtl_assessment_properties" scope_p
    ON scope_p.assessment_id = a.id AND scope_p.property_key = 'scope_notes'
WHERE a.is_deleted = FALSE;

-- ─────────────────────────────────────────────
-- VIEW: finding detail
-- ─────────────────────────────────────────────
CREATE OR REPLACE VIEW "09_assessments"."41_vw_finding_detail" AS
SELECT
    f.id,
    f.assessment_id,
    f.control_id,
    f.risk_id,
    f.severity_code,
    f.finding_type,
    f.finding_status_code,
    f.assigned_to,
    f.remediation_due_date,
    sev.name                        AS severity_name,
    fs.name                         AS finding_status_name,
    title_p.property_value          AS title,
    desc_p.property_value           AS description,
    rec_p.property_value            AS recommendation,
    f.is_active,
    f.is_deleted,
    f.created_at,
    f.updated_at,
    f.created_by
FROM "09_assessments"."11_fct_findings" f
LEFT JOIN "09_assessments"."04_dim_finding_severities"  sev ON sev.code = f.severity_code
LEFT JOIN "09_assessments"."05_dim_finding_statuses"     fs  ON fs.code  = f.finding_status_code
LEFT JOIN "09_assessments"."22_dtl_finding_properties"  title_p
    ON title_p.finding_id = f.id AND title_p.property_key = 'title'
LEFT JOIN "09_assessments"."22_dtl_finding_properties"  desc_p
    ON desc_p.finding_id = f.id AND desc_p.property_key = 'description'
LEFT JOIN "09_assessments"."22_dtl_finding_properties"  rec_p
    ON rec_p.finding_id = f.id AND rec_p.property_key = 'recommendation'
WHERE f.is_deleted = FALSE;

-- ─────────────────────────────────────────────
-- PERMISSIONS & FEATURE FLAGS in 03_auth_manage
-- ─────────────────────────────────────────────

-- Feature flags
INSERT INTO "03_auth_manage"."14_dim_feature_flags"
    (id, code, name, description, feature_scope, feature_flag_category_code,
     access_mode, lifecycle_state, initial_audience,
     env_dev, env_staging, env_prod, created_at, updated_at)
VALUES
    (gen_random_uuid(), 'assessments', 'Assessments', 'Assessment & Findings module', 'platform', 'grc', 'permissioned', 'active', 'all', TRUE, TRUE, FALSE, NOW(), NOW()),
    (gen_random_uuid(), 'findings',    'Findings',    'Finding management within assessments', 'platform', 'grc', 'permissioned', 'active', 'all', TRUE, TRUE, FALSE, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- Feature permissions
INSERT INTO "03_auth_manage"."15_dim_feature_permissions"
    (id, code, feature_flag_code, permission_action_code, name, description, created_at, updated_at)
VALUES
    (gen_random_uuid(), 'assessments.view',   'assessments', 'view',   'View Assessments',   'View assessments and findings',      NOW(), NOW()),
    (gen_random_uuid(), 'assessments.create', 'assessments', 'create', 'Create Assessments', 'Create assessment sessions',          NOW(), NOW()),
    (gen_random_uuid(), 'assessments.update', 'assessments', 'update', 'Update Assessments', 'Update assessments and complete them',NOW(), NOW()),
    (gen_random_uuid(), 'assessments.delete', 'assessments', 'delete', 'Delete Assessments', 'Delete (soft) assessments',           NOW(), NOW()),
    (gen_random_uuid(), 'findings.view',      'findings',    'view',   'View Findings',      'View finding details and responses',  NOW(), NOW()),
    (gen_random_uuid(), 'findings.create',    'findings',    'create', 'Create Findings',    'Create findings in an assessment',    NOW(), NOW()),
    (gen_random_uuid(), 'findings.update',    'findings',    'update', 'Update Findings',    'Update finding status and respond',   NOW(), NOW()),
    (gen_random_uuid(), 'findings.delete', 'findings', 'delete', 'Delete Findings', 'Delete (soft) findings', NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- GRC assessor role
INSERT INTO "03_auth_manage"."16_fct_roles"
    (id, tenant_key, role_level_code, code, name, description,
     scope_org_id, scope_workspace_id,
     is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
     created_at, updated_at, created_by, updated_by)
VALUES
    (gen_random_uuid(), '__platform__', 'platform', 'grc_assessor', 'GRC Assessor',
     'Can conduct assessments, create and manage findings',
     NULL, NULL, TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, NOW(), NOW(), NULL, NULL),
    (gen_random_uuid(), '__platform__', 'platform', 'grc_finding_responder', 'GRC Finding Responder',
     'Can view assessments and respond to assigned findings',
     NULL, NULL, TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, NOW(), NOW(), NULL, NULL)
ON CONFLICT DO NOTHING;

-- Assign permissions to grc_assessor role
INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
    (id, role_id, feature_permission_id, is_active, is_disabled, is_deleted, is_test, is_system, is_locked, created_at, updated_at, created_by, updated_by)
SELECT gen_random_uuid(), r.id, fp.id,
    TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, NOW(), NOW(), NULL, NULL
FROM "03_auth_manage"."16_fct_roles" r
CROSS JOIN "03_auth_manage"."15_dim_feature_permissions" fp
WHERE r.code = 'grc_assessor'
  AND fp.feature_flag_code IN ('assessments', 'findings')
AND NOT EXISTS (
    SELECT 1 FROM "03_auth_manage"."20_lnk_role_feature_permissions" lnk
    WHERE lnk.role_id = r.id AND lnk.feature_permission_id = fp.id
);

-- Assign limited permissions to grc_finding_responder
INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
    (id, role_id, feature_permission_id, is_active, is_disabled, is_deleted, is_test, is_system, is_locked, created_at, updated_at, created_by, updated_by)
SELECT gen_random_uuid(), r.id, fp.id,
    TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, NOW(), NOW(), NULL, NULL
FROM "03_auth_manage"."16_fct_roles" r
CROSS JOIN "03_auth_manage"."15_dim_feature_permissions" fp
WHERE r.code = 'grc_finding_responder'
  AND fp.feature_flag_code IN ('assessments', 'findings')
  AND fp.permission_action_code IN ('view', 'update')
AND NOT EXISTS (
    SELECT 1 FROM "03_auth_manage"."20_lnk_role_feature_permissions" lnk
    WHERE lnk.role_id = r.id AND lnk.feature_permission_id = fp.id
);

-- Grant assessments permissions to existing super_admin / grc_admin roles
INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
    (id, role_id, feature_permission_id, is_active, is_disabled, is_deleted, is_test, is_system, is_locked, created_at, updated_at, created_by, updated_by)
SELECT gen_random_uuid(), r.id, fp.id,
    TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, NOW(), NOW(), NULL, NULL
FROM "03_auth_manage"."16_fct_roles" r
CROSS JOIN "03_auth_manage"."15_dim_feature_permissions" fp
WHERE r.code IN ('super_admin', 'grc_admin', 'grc_manager')
  AND fp.feature_flag_code IN ('assessments', 'findings')
AND NOT EXISTS (
    SELECT 1 FROM "03_auth_manage"."20_lnk_role_feature_permissions" lnk
    WHERE lnk.role_id = r.id AND lnk.feature_permission_id = fp.id
);
