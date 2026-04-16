-- Audit Engagement Module
-- Schema: 12_engagements
-- Status: In Progress

CREATE SCHEMA IF NOT EXISTS "12_engagements";

-- ─────────────────────────────────────────────────────────────────────────────
-- 1. DIMENSION TABLES
-- ─────────────────────────────────────────────────────────────────────────────

-- 02_dim_engagement_statuses: lifecycle states
CREATE TABLE IF NOT EXISTS "12_engagements"."02_dim_engagement_statuses" (
    code        VARCHAR(30) PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    description TEXT,
    sort_order  INTEGER DEFAULT 0,
    created_at  TIMESTAMPTZ DEFAULT now()
);

INSERT INTO "12_engagements"."02_dim_engagement_statuses" (code, name, description, sort_order)
VALUES 
    ('setup',     'Setup',     'Initial configuration phase', 10),
    ('active',    'Active',    'Execution and evidence review', 20),
    ('review',    'Review',    'Drafting report and remediation', 30),
    ('completed', 'Completed', 'Final report issued', 40),
    ('closed',    'Closed',    'Archived and read-only', 50)
ON CONFLICT (code) DO NOTHING;

-- 03_dim_engagement_property_keys: valid EAV keys for engagement metadata
CREATE TABLE IF NOT EXISTS "12_engagements"."03_dim_engagement_property_keys" (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code        VARCHAR(80) UNIQUE NOT NULL,
    name        VARCHAR(120) NOT NULL,
    description TEXT,
    data_type   VARCHAR(30) DEFAULT 'text',
    is_required BOOLEAN DEFAULT FALSE,
    sort_order  INTEGER DEFAULT 0,
    created_at  TIMESTAMPTZ DEFAULT now()
);

INSERT INTO "12_engagements"."03_dim_engagement_property_keys" (code, name, data_type, is_required, sort_order)
VALUES 
    ('engagement_name',    'Engagement Name',     'text', true,  10),
    ('auditor_firm',       'Auditor Firm',        'text', true,  20),
    ('scope_description',  'Scope Description',   'text', false, 30),
    ('audit_period_start', 'Audit Period Start',  'date', false, 40),
    ('audit_period_end',   'Audit Period End',    'date', false, 50),
    ('report_type',        'Report Type',         'text', false, 60),
    ('lead_grc_sme',       'Lead GRC SME',        'text', false, 70)
ON CONFLICT (code) DO NOTHING;

-- 04_dim_request_property_keys: valid EAV keys for auditor requests
CREATE TABLE IF NOT EXISTS "12_engagements"."04_dim_request_property_keys" (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code        VARCHAR(80) UNIQUE NOT NULL,
    name        VARCHAR(120) NOT NULL,
    data_type   VARCHAR(30) DEFAULT 'text',
    is_required BOOLEAN DEFAULT FALSE,
    created_at  TIMESTAMPTZ DEFAULT now()
);

INSERT INTO "12_engagements"."04_dim_request_property_keys" (code, name, is_required)
VALUES 
    ('request_description', 'Description', true),
    ('response_notes',       'Notes',       false)
ON CONFLICT (code) DO NOTHING;

-- ─────────────────────────────────────────────────────────────────────────────
-- 2. FACT TABLES (LEAN)
-- ─────────────────────────────────────────────────────────────────────────────

-- 10_fct_audit_engagements: core engagement record
CREATE TABLE IF NOT EXISTS "12_engagements"."10_fct_audit_engagements" (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_key           TEXT NOT NULL,
    org_id               UUID NOT NULL,
    engagement_code      VARCHAR(100) NOT NULL,
    framework_id         UUID NOT NULL
                             REFERENCES "05_grc_library"."10_fct_frameworks"(id),
    framework_deployment_id UUID NOT NULL
                             REFERENCES "05_grc_library"."16_fct_framework_deployments"(id),
    status_code          VARCHAR(30) NOT NULL DEFAULT 'setup'
                             REFERENCES "12_engagements"."02_dim_engagement_statuses"(code),
    target_completion_date DATE,
    -- tracking
    is_active            BOOLEAN NOT NULL DEFAULT TRUE,
    is_deleted           BOOLEAN NOT NULL DEFAULT FALSE,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by           UUID,
    updated_by           UUID,
    deleted_at           TIMESTAMPTZ
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_audit_eng_code_org_unique 
    ON "12_engagements"."10_fct_audit_engagements" (org_id, engagement_code) 
    WHERE is_deleted = FALSE;

-- 11_fct_audit_access_tokens: hashed tokens for external auditors
CREATE TABLE IF NOT EXISTS "12_engagements"."11_fct_audit_access_tokens" (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    engagement_id     UUID NOT NULL
                          REFERENCES "12_engagements"."10_fct_audit_engagements"(id),
    auditor_user_id   UUID, -- link if they have platform account
    auditor_email     TEXT NOT NULL,
    token_hash        TEXT NOT NULL UNIQUE, -- SHA-256
    expires_at        TIMESTAMPTZ NOT NULL,
    last_accessed_at  TIMESTAMPTZ,
    is_revoked        BOOLEAN NOT NULL DEFAULT FALSE,
    revoked_at        TIMESTAMPTZ,
    revoked_by        UUID,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ─────────────────────────────────────────────────────────────────────────────
-- 3. TRANSACTION TABLES (LEAN)
-- ─────────────────────────────────────────────────────────────────────────────

-- 20_trx_auditor_requests: documentation requests from auditors
CREATE TABLE IF NOT EXISTS "12_engagements"."20_trx_auditor_requests" (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    engagement_id    UUID NOT NULL
                         REFERENCES "12_engagements"."10_fct_audit_engagements"(id),
    requested_by_token_id UUID NOT NULL
                         REFERENCES "12_engagements"."11_fct_audit_access_tokens"(id),
    control_id       UUID, -- optional specific control reference
    request_status   VARCHAR(30) NOT NULL DEFAULT 'open'
                         CHECK (request_status IN ('open', 'fulfilled', 'dismissed')),
    fulfilled_at     TIMESTAMPTZ,
    fulfilled_by     UUID,
    attachment_id    UUID, -- link to artifact once fulfilled
    is_deleted       BOOLEAN NOT NULL DEFAULT FALSE,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 21_trx_auditor_verifications: auditor verification of controls
CREATE TABLE IF NOT EXISTS "12_engagements"."21_trx_auditor_verifications" (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    engagement_id    UUID NOT NULL
                         REFERENCES "12_engagements"."10_fct_audit_engagements"(id),
    control_id       UUID NOT NULL,
    verified_by_token_id UUID NOT NULL
                         REFERENCES "12_engagements"."11_fct_audit_access_tokens"(id),
    outcome          VARCHAR(30) NOT NULL DEFAULT 'verified'
                         CHECK (outcome IN ('verified', 'qualified', 'failed')),
    observations     TEXT,
    finding_details  TEXT,
    verified_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    
    UNIQUE (engagement_id, control_id)
);

-- ─────────────────────────────────────────────────────────────────────────────
-- 4. DETAIL TABLES (EAV)
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS "12_engagements"."22_dtl_engagement_properties" (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    engagement_id    UUID NOT NULL
                         REFERENCES "12_engagements"."10_fct_audit_engagements"(id),
    property_key     VARCHAR(80) NOT NULL
                         REFERENCES "12_engagements"."03_dim_engagement_property_keys"(code),
    property_value   TEXT NOT NULL,
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (engagement_id, property_key)
);

CREATE TABLE IF NOT EXISTS "12_engagements"."23_dtl_request_properties" (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id       UUID NOT NULL
                         REFERENCES "12_engagements"."20_trx_auditor_requests"(id),
    property_key     VARCHAR(80) NOT NULL
                         REFERENCES "12_engagements"."04_dim_request_property_keys"(code),
    property_value   TEXT NOT NULL,
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (request_id, property_key)
);

-- ─────────────────────────────────────────────────────────────────────────────
-- 5. VIEWS
-- ─────────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE VIEW "12_engagements"."40_vw_engagement_detail" AS
SELECT
    e.id,
    e.tenant_key,
    e.org_id,
    o.name                       AS org_name,
    e.engagement_code,
    e.framework_id,
    e.framework_deployment_id,
    e.status_code,
    s.name                       AS status_name,
    e.target_completion_date,
    name_prop.property_value     AS engagement_name,
    firm_prop.property_value     AS auditor_firm,
    scope_prop.property_value    AS scope_description,
    p_start.property_value       AS audit_period_start,
    p_end.property_value         AS audit_period_end,
    p_sme.property_value         AS lead_grc_sme,
    (SELECT count(*) FROM "12_engagements"."20_trx_auditor_requests" r 
     WHERE r.engagement_id = e.id AND r.request_status = 'open') AS open_requests_count,
    (SELECT count(*)::int FROM "05_grc_library"."31_lnk_framework_version_controls" lvc
     JOIN "05_grc_library"."16_fct_framework_deployments" fd ON fd.id = e.framework_deployment_id
     WHERE lvc.framework_version_id = fd.deployed_version_id) AS total_controls_count,
    (SELECT count(*) FROM "12_engagements"."21_trx_auditor_verifications" v 
     WHERE v.engagement_id = e.id) AS verified_controls_count,
    e.is_active,
    e.created_at,
    e.updated_at
FROM "12_engagements"."10_fct_audit_engagements" e
JOIN "03_auth_manage"."29_fct_orgs" o ON o.id = e.org_id
JOIN "12_engagements"."02_dim_engagement_statuses" s ON s.code = e.status_code
LEFT JOIN "12_engagements"."22_dtl_engagement_properties" name_prop
    ON name_prop.engagement_id = e.id AND name_prop.property_key = 'engagement_name'
LEFT JOIN "12_engagements"."22_dtl_engagement_properties" firm_prop
    ON firm_prop.engagement_id = e.id AND firm_prop.property_key = 'auditor_firm'
LEFT JOIN "12_engagements"."22_dtl_engagement_properties" scope_prop
    ON scope_prop.engagement_id = e.id AND scope_prop.property_key = 'scope_description'
LEFT JOIN "12_engagements"."22_dtl_engagement_properties" p_start
    ON p_start.engagement_id = e.id AND p_start.property_key = 'audit_period_start'
LEFT JOIN "12_engagements"."22_dtl_engagement_properties" p_end
    ON p_end.engagement_id = e.id AND p_end.property_key = 'audit_period_end'
LEFT JOIN "12_engagements"."22_dtl_engagement_properties" p_sme
    ON p_sme.engagement_id = e.id AND p_sme.property_key = 'lead_grc_sme'
WHERE e.is_deleted = FALSE;
