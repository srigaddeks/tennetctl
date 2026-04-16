-- Auditor engagement membership foundation
-- Adds lean engagement membership storage, user-first indexes for portfolio reads,
-- and feature flags for the first rollout slice.

CREATE SCHEMA IF NOT EXISTS "12_engagements";

-- 05_dim_engagement_membership_statuses
CREATE TABLE IF NOT EXISTS "12_engagements"."05_dim_engagement_membership_statuses" (
    code        VARCHAR(30) PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    description TEXT,
    sort_order  INTEGER DEFAULT 0,
    created_at  TIMESTAMPTZ DEFAULT now()
);

INSERT INTO "12_engagements"."05_dim_engagement_membership_statuses" (code, name, description, sort_order)
VALUES
    ('pending', 'Pending', 'Membership exists but is not yet active for workspace access', 10),
    ('active',  'Active',  'Membership grants active engagement visibility', 20),
    ('revoked', 'Revoked', 'Membership was explicitly revoked', 30),
    ('expired', 'Expired', 'Membership expired automatically', 40)
ON CONFLICT (code) DO NOTHING;

-- 06_dim_engagement_membership_types
CREATE TABLE IF NOT EXISTS "12_engagements"."06_dim_engagement_membership_types" (
    code        VARCHAR(50) PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    description TEXT,
    sort_order  INTEGER DEFAULT 0,
    created_at  TIMESTAMPTZ DEFAULT now()
);

INSERT INTO "12_engagements"."06_dim_engagement_membership_types" (code, name, description, sort_order)
VALUES
    ('external_auditor', 'External Auditor', 'External auditor invited into the engagement', 10),
    ('internal_auditor', 'Internal Auditor', 'Internal platform user acting as auditor', 20),
    ('grc_team',         'GRC Team',         'Internal GRC participant with engagement access', 30),
    ('observer',         'Observer',         'Read-only engagement participant', 40)
ON CONFLICT (code) DO NOTHING;

-- 07_dim_engagement_membership_property_keys
CREATE TABLE IF NOT EXISTS "12_engagements"."07_dim_engagement_membership_property_keys" (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code        VARCHAR(80) UNIQUE NOT NULL,
    name        VARCHAR(120) NOT NULL,
    description TEXT,
    data_type   VARCHAR(30) DEFAULT 'text',
    is_required BOOLEAN DEFAULT FALSE,
    sort_order  INTEGER DEFAULT 0,
    created_at  TIMESTAMPTZ DEFAULT now()
);

INSERT INTO "12_engagements"."07_dim_engagement_membership_property_keys" (code, name, description, data_type, is_required, sort_order)
VALUES
    ('firm_name',      'Firm Name',      'Optional external audit firm label', 'text', false, 10),
    ('role_label',     'Role Label',     'Human readable role label', 'text', false, 20),
    ('invite_source',  'Invite Source',  'Originating invite or workflow source', 'text', false, 30),
    ('invited_by',     'Invited By',     'User id or label of inviter', 'text', false, 40),
    ('accepted_at',    'Accepted At',    'Acceptance timestamp metadata', 'date', false, 50),
    ('revoked_reason', 'Revoked Reason', 'Reason the membership was revoked', 'text', false, 60),
    ('notes',          'Notes',          'Optional freeform notes', 'text', false, 70)
ON CONFLICT (code) DO NOTHING;

-- 12_lnk_engagement_memberships
CREATE TABLE IF NOT EXISTS "12_engagements"."12_lnk_engagement_memberships" (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_key           TEXT NOT NULL,
    engagement_id        UUID NOT NULL
                             REFERENCES "12_engagements"."10_fct_audit_engagements"(id),
    org_id               UUID NOT NULL
                             REFERENCES "03_auth_manage"."29_fct_orgs"(id),
    workspace_id         UUID NULL
                             REFERENCES "03_auth_manage"."34_fct_workspaces"(id),
    user_id              UUID NULL
                             REFERENCES "03_auth_manage"."03_fct_users"(id),
    external_email       TEXT NULL,
    membership_type_code VARCHAR(50) NOT NULL
                             REFERENCES "12_engagements"."06_dim_engagement_membership_types"(code),
    status_code          VARCHAR(30) NOT NULL DEFAULT 'pending'
                             REFERENCES "12_engagements"."05_dim_engagement_membership_statuses"(code),
    joined_at            TIMESTAMPTZ NULL,
    expires_at           TIMESTAMPTZ NULL,
    is_active            BOOLEAN NOT NULL DEFAULT TRUE,
    is_disabled          BOOLEAN NOT NULL DEFAULT FALSE,
    is_deleted           BOOLEAN NOT NULL DEFAULT FALSE,
    is_test              BOOLEAN NOT NULL DEFAULT FALSE,
    is_system            BOOLEAN NOT NULL DEFAULT FALSE,
    is_locked            BOOLEAN NOT NULL DEFAULT FALSE,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by           UUID NULL,
    updated_by           UUID NULL,
    deleted_at           TIMESTAMPTZ NULL,
    deleted_by           UUID NULL,
    CONSTRAINT ck_12_lnk_engagement_memberships_principal
        CHECK (user_id IS NOT NULL OR external_email IS NOT NULL)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_12_lnk_engagement_memberships_engagement_user_active
    ON "12_engagements"."12_lnk_engagement_memberships" (engagement_id, user_id)
    WHERE user_id IS NOT NULL AND is_deleted = FALSE;

CREATE UNIQUE INDEX IF NOT EXISTS uq_12_lnk_engagement_memberships_engagement_email_active
    ON "12_engagements"."12_lnk_engagement_memberships" (engagement_id, external_email)
    WHERE external_email IS NOT NULL AND is_deleted = FALSE;

CREATE INDEX IF NOT EXISTS idx_12_lnk_engagement_memberships_user_status
    ON "12_engagements"."12_lnk_engagement_memberships" (user_id, status_code, is_deleted, expires_at)
    WHERE user_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_12_lnk_engagement_memberships_email_status
    ON "12_engagements"."12_lnk_engagement_memberships" (external_email, status_code, is_deleted, expires_at)
    WHERE external_email IS NOT NULL;

-- 24_dtl_engagement_membership_properties
CREATE TABLE IF NOT EXISTS "12_engagements"."24_dtl_engagement_membership_properties" (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    membership_id    UUID NOT NULL
                         REFERENCES "12_engagements"."12_lnk_engagement_memberships"(id),
    property_key     VARCHAR(80) NOT NULL
                         REFERENCES "12_engagements"."07_dim_engagement_membership_property_keys"(code),
    property_value   TEXT NOT NULL,
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_24_dtl_engagement_membership_properties_key UNIQUE (membership_id, property_key)
);

-- Backfill memberships for known users already linked to auditor tokens by email.
INSERT INTO "12_engagements"."12_lnk_engagement_memberships" (
    id, tenant_key, engagement_id, org_id, workspace_id, user_id, external_email,
    membership_type_code, status_code, joined_at,
    is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
    created_at, updated_at
)
SELECT
    gen_random_uuid(),
    e.tenant_key,
    e.id,
    e.org_id,
    fd.workspace_id,
    up.user_id,
    t.auditor_email,
    'external_auditor',
    CASE
        WHEN t.is_revoked = TRUE THEN 'revoked'
        WHEN t.expires_at <= now() THEN 'expired'
        ELSE 'active'
    END,
    t.created_at,
    CASE
        WHEN t.is_revoked = TRUE OR t.expires_at <= now() THEN FALSE
        ELSE TRUE
    END,
    FALSE,
    FALSE,
    FALSE,
    FALSE,
    FALSE,
    t.created_at,
    t.created_at
FROM "12_engagements"."11_fct_audit_access_tokens" t
JOIN "12_engagements"."10_fct_audit_engagements" e
  ON e.id = t.engagement_id
LEFT JOIN "05_grc_library"."16_fct_framework_deployments" fd
  ON fd.id = e.framework_deployment_id
JOIN "03_auth_manage"."05_dtl_user_properties" up
  ON lower(up.property_value) = lower(t.auditor_email)
 AND up.property_key = 'email'
WHERE NOT EXISTS (
    SELECT 1
    FROM "12_engagements"."12_lnk_engagement_memberships" m
    WHERE m.engagement_id = e.id
      AND m.user_id = up.user_id
      AND m.is_deleted = FALSE
);

-- Auditor workspace feature flags for the foundation slice.
INSERT INTO "03_auth_manage"."14_dim_feature_flags" (
    id, code, name, description, feature_flag_category_code, access_mode, lifecycle_state,
    initial_audience, env_dev, env_staging, env_prod, created_at, updated_at
)
VALUES
    (
        'ec07be31-5506-4a09-8f9f-7d3d402f9001',
        'audit_workspace_auditor_portfolio',
        'Audit Workspace Auditor Portfolio',
        'Multi-org auditor portfolio view for assigned engagements.',
        'access',
        'permissioned',
        'draft',
        'internal',
        TRUE, FALSE, FALSE,
        now(), now()
    ),
    (
        'ec07be31-5506-4a09-8f9f-7d3d402f9002',
        'audit_workspace_engagement_membership',
        'Audit Workspace Engagement Membership',
        'Engagement membership foundation for auditor workspace visibility and access resolution.',
        'access',
        'permissioned',
        'draft',
        'internal',
        TRUE, FALSE, FALSE,
        now(), now()
    )
ON CONFLICT (code) DO NOTHING;

INSERT INTO "03_auth_manage"."15_dim_feature_permissions" (
    id, code, feature_flag_code, permission_action_code, name, description, created_at, updated_at
)
VALUES
    (
        'ec07be31-5506-4a09-8f9f-7d3d402f9011',
        'audit_workspace_auditor_portfolio.view',
        'audit_workspace_auditor_portfolio',
        'view',
        'Audit Workspace Auditor Portfolio View',
        'View the assigned auditor portfolio across engagements.',
        now(), now()
    ),
    (
        'ec07be31-5506-4a09-8f9f-7d3d402f9012',
        'audit_workspace_engagement_membership.view',
        'audit_workspace_engagement_membership',
        'view',
        'Audit Workspace Engagement Membership View',
        'View engagement membership-backed auditor workspace data.',
        now(), now()
    ),
    (
        'ec07be31-5506-4a09-8f9f-7d3d402f9013',
        'audit_workspace_engagement_membership.update',
        'audit_workspace_engagement_membership',
        'update',
        'Audit Workspace Engagement Membership Update',
        'Manage engagement membership-backed auditor workspace access.',
        now(), now()
    )
ON CONFLICT (code) DO NOTHING;
