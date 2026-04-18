-- UP ====

-- Phase 23R-01: Rebase flags as capabilities — unified flag + permission model.
--
-- What this does:
--   1. Adds dim_permission_actions   (8 actions: view/create/update/delete/assign/configure/export/impersonate)
--   2. Adds dim_feature_flag_categories  (8 categories: platform/iam/vault/audit/monitoring/notify/featureflags/nodes)
--   3. Adds dim_feature_flags (SMALLINT-PK dim; one row per system capability / sub-feature)
--   4. Adds dim_feature_permissions (cross-product of flag × action)
--   5. Adds lnk_role_feature_permissions (replaces lnk_role_flag_permissions + lnk_role_scopes)
--   6. Creates v_feature_permissions and v_role_feature_permissions views
--   7. Drops old tables: 40_lnk_role_flag_permissions (09_featureflags),
--      04_dim_flag_permissions (09_featureflags),
--      44_lnk_role_scopes (03_iam),
--      03_dim_scopes (03_iam)
--   8. Drops old view: v_role_flag_permissions (09_featureflags)
--
-- Tables NOT touched: 10_fct_flags, 11_fct_flag_states, 20_fct_rules, 21_fct_overrides
-- (those remain as the advanced rollout layer).
--
-- No data migration: v0.2.0 is pre-release; grants are reseeded fresh.

-- ── Step 1: Drop dependent views before touching tables ──────────────

DROP VIEW IF EXISTS "09_featureflags"."v_role_flag_permissions";

-- ── Step 2: Drop old link and dim tables ─────────────────────────────

DROP TABLE IF EXISTS "09_featureflags"."40_lnk_role_flag_permissions";
DROP TABLE IF EXISTS "09_featureflags"."04_dim_flag_permissions";

DROP TABLE IF EXISTS "03_iam"."44_lnk_role_scopes";
DROP TABLE IF EXISTS "03_iam"."45_lnk_application_scopes";
DROP TABLE IF EXISTS "03_iam"."03_dim_scopes";
-- NOTE: applications service (repository.py) will be rewired in 23R-02 to
-- use lnk_application_feature_permissions (new). Until then, application
-- scope grants are a no-op — consistent with "no data migration" decision.

-- ── Step 3: dim_permission_actions ───────────────────────────────────

CREATE TABLE "09_featureflags"."01_dim_permission_actions" (
    id              SMALLINT NOT NULL,
    code            TEXT NOT NULL,
    label           TEXT NOT NULL,
    description     TEXT,
    sort_order      SMALLINT NOT NULL DEFAULT 0,
    deprecated_at   TIMESTAMP,
    CONSTRAINT pk_ff_dim_permission_actions PRIMARY KEY (id),
    CONSTRAINT uq_ff_dim_permission_actions_code UNIQUE (code)
);

COMMENT ON TABLE  "09_featureflags"."01_dim_permission_actions" IS 'Canonical set of actions that can be granted on a feature flag capability. Seeded; never mutated — add rows to extend.';
COMMENT ON COLUMN "09_featureflags"."01_dim_permission_actions".id IS 'Permanent manual id. Never renumber.';
COMMENT ON COLUMN "09_featureflags"."01_dim_permission_actions".code IS 'Action code used in permission checks (e.g. view, create).';
COMMENT ON COLUMN "09_featureflags"."01_dim_permission_actions".label IS 'Human-readable label.';
COMMENT ON COLUMN "09_featureflags"."01_dim_permission_actions".description IS 'What this action permits.';
COMMENT ON COLUMN "09_featureflags"."01_dim_permission_actions".sort_order IS 'Display order in the UI capability grid.';
COMMENT ON COLUMN "09_featureflags"."01_dim_permission_actions".deprecated_at IS 'Non-null when this action is no longer granted to new roles.';

INSERT INTO "09_featureflags"."01_dim_permission_actions"
    (id, code, label, description, sort_order)
VALUES
    (1, 'view',        'View',        'Read a resource or list its entries.',                       10),
    (2, 'create',      'Create',      'Create a new resource.',                                    20),
    (3, 'update',      'Update',      'Modify an existing resource.',                              30),
    (4, 'delete',      'Delete',      'Soft-delete a resource.',                                   40),
    (5, 'assign',      'Assign',      'Grant access to or link entities (e.g. assign a role).',    50),
    (6, 'configure',   'Configure',   'Modify configuration or settings for a resource.',          60),
    (7, 'export',      'Export',      'Export data outside the platform.',                         70),
    (8, 'impersonate', 'Impersonate', 'Act as another user within a session.',                     80)
ON CONFLICT (id) DO NOTHING;

-- ── Step 4: dim_feature_flag_categories ──────────────────────────────

CREATE TABLE "09_featureflags"."02_dim_feature_flag_categories" (
    id              SMALLINT NOT NULL,
    code            TEXT NOT NULL,
    label           TEXT NOT NULL,
    description     TEXT,
    sort_order      SMALLINT NOT NULL DEFAULT 0,
    deprecated_at   TIMESTAMP,
    CONSTRAINT pk_ff_dim_feature_flag_categories PRIMARY KEY (id),
    CONSTRAINT uq_ff_dim_feature_flag_categories_code UNIQUE (code)
);

COMMENT ON TABLE  "09_featureflags"."02_dim_feature_flag_categories" IS 'Grouping of feature flags by product domain. Used to cluster capabilities in the Role Designer UI.';
COMMENT ON COLUMN "09_featureflags"."02_dim_feature_flag_categories".id IS 'Permanent manual id. Never renumber.';
COMMENT ON COLUMN "09_featureflags"."02_dim_feature_flag_categories".code IS 'Category code matching the feature domain (e.g. iam, vault).';
COMMENT ON COLUMN "09_featureflags"."02_dim_feature_flag_categories".label IS 'Human-readable label.';
COMMENT ON COLUMN "09_featureflags"."02_dim_feature_flag_categories".description IS 'Description of which sub-features belong to this category.';
COMMENT ON COLUMN "09_featureflags"."02_dim_feature_flag_categories".sort_order IS 'Display order in the capability grid.';
COMMENT ON COLUMN "09_featureflags"."02_dim_feature_flag_categories".deprecated_at IS 'Non-null when this category is retired.';

INSERT INTO "09_featureflags"."02_dim_feature_flag_categories"
    (id, code, label, description, sort_order)
VALUES
    (1, 'platform',      'Platform',      'Cross-cutting platform capabilities (admin, catalog, nodes).',                 10),
    (2, 'iam',           'IAM',           'Identity & Access Management — orgs, users, roles, auth, sessions.',           20),
    (3, 'vault',         'Vault',         'Secrets and runtime configuration management.',                                30),
    (4, 'audit',         'Audit',         'Audit log explorer and saved views.',                                          40),
    (5, 'monitoring',    'Monitoring',    'Logs, metrics, traces, dashboards, and alerts.',                               50),
    (6, 'notify',        'Notify',        'Notification templates, campaigns, delivery, and preferences.',                60),
    (7, 'featureflags',  'Feature Flags', 'Flag definitions, rules, overrides, and the capability catalog itself.',       70),
    (8, 'nodes',         'Nodes',         'Node catalog — platform-level building blocks browsable by developers.',       80)
ON CONFLICT (id) DO NOTHING;

-- ── Step 5: dim_feature_flags ─────────────────────────────────────────
--
-- This is a DIM (SMALLINT PK), not an FCT, because these rows are system-
-- defined capability codes, seeded at deploy time, not user-created entities.
-- Existing fct_flags (user-defined rollout flags) are a separate layer.

CREATE TABLE "09_featureflags"."03_dim_feature_flags" (
    id                  SMALLINT NOT NULL,
    code                TEXT NOT NULL,
    name                TEXT NOT NULL,
    description         TEXT,
    category_id         SMALLINT NOT NULL,
    feature_scope       TEXT NOT NULL,
    access_mode         TEXT NOT NULL DEFAULT 'permissioned',
    lifecycle_state     TEXT NOT NULL DEFAULT 'active',
    env_dev             BOOLEAN NOT NULL DEFAULT false,
    env_staging         BOOLEAN NOT NULL DEFAULT false,
    env_prod            BOOLEAN NOT NULL DEFAULT false,
    rollout_mode        TEXT NOT NULL DEFAULT 'simple',
    required_license    TEXT,
    deprecated_at       TIMESTAMP,
    CONSTRAINT pk_ff_dim_feature_flags PRIMARY KEY (id),
    CONSTRAINT uq_ff_dim_feature_flags_code UNIQUE (code),
    CONSTRAINT fk_ff_dim_feature_flags_category FOREIGN KEY (category_id)
        REFERENCES "09_featureflags"."02_dim_feature_flag_categories"(id),
    CONSTRAINT chk_ff_dim_feature_flags_scope CHECK (
        feature_scope IN ('platform', 'org', 'workspace', 'product')
    ),
    CONSTRAINT chk_ff_dim_feature_flags_access_mode CHECK (
        access_mode IN ('public', 'authenticated', 'permissioned')
    ),
    CONSTRAINT chk_ff_dim_feature_flags_lifecycle CHECK (
        lifecycle_state IN ('planned', 'active', 'deprecated', 'retired')
    ),
    CONSTRAINT chk_ff_dim_feature_flags_rollout_mode CHECK (
        rollout_mode IN ('simple', 'targeted')
    )
);

CREATE INDEX idx_ff_dim_feature_flags_category
    ON "09_featureflags"."03_dim_feature_flags" (category_id);

COMMENT ON TABLE  "09_featureflags"."03_dim_feature_flags" IS 'System capability catalog. One row per sub-feature. Seeded at deploy time; never user-created. A feature flag IS a capability — roles are granted (flag, action) pairs from this table.';
COMMENT ON COLUMN "09_featureflags"."03_dim_feature_flags".id IS 'Permanent manual id. Never renumber.';
COMMENT ON COLUMN "09_featureflags"."03_dim_feature_flags".code IS 'Stable capability code used in require_permission() calls (e.g. orgs, vault_secrets).';
COMMENT ON COLUMN "09_featureflags"."03_dim_feature_flags".name IS 'Human-readable name for the capability.';
COMMENT ON COLUMN "09_featureflags"."03_dim_feature_flags".description IS 'What this capability controls.';
COMMENT ON COLUMN "09_featureflags"."03_dim_feature_flags".category_id IS 'FK to dim_feature_flag_categories — product domain grouping.';
COMMENT ON COLUMN "09_featureflags"."03_dim_feature_flags".feature_scope IS 'Where this capability applies: platform (cross-org), org (tenant), workspace, or product (billing-tier).';
COMMENT ON COLUMN "09_featureflags"."03_dim_feature_flags".access_mode IS 'public = no auth required; authenticated = any logged-in user; permissioned = role grant required.';
COMMENT ON COLUMN "09_featureflags"."03_dim_feature_flags".lifecycle_state IS 'planned | active | deprecated | retired. Resolver rejects retired capabilities.';
COMMENT ON COLUMN "09_featureflags"."03_dim_feature_flags".env_dev IS 'Whether this capability is available in dev environments.';
COMMENT ON COLUMN "09_featureflags"."03_dim_feature_flags".env_staging IS 'Whether this capability is available in staging environments.';
COMMENT ON COLUMN "09_featureflags"."03_dim_feature_flags".env_prod IS 'Whether this capability is available in production environments.';
COMMENT ON COLUMN "09_featureflags"."03_dim_feature_flags".rollout_mode IS 'simple = env + access_mode + role grant. targeted = also evaluate fct_rules/fct_overrides for this flag code.';
COMMENT ON COLUMN "09_featureflags"."03_dim_feature_flags".required_license IS 'License tier required to use this capability. NULL = no billing gate.';
COMMENT ON COLUMN "09_featureflags"."03_dim_feature_flags".deprecated_at IS 'Non-null when the capability is deprecated. Resolver warns callers.';

-- Seeded below in one batch. Ordered by category then sub-feature number.
-- All rows: lifecycle_state='active', env_dev/staging/prod=true, rollout_mode='simple', required_license=null.

INSERT INTO "09_featureflags"."03_dim_feature_flags"
    (id, code, name, description, category_id, feature_scope, access_mode, lifecycle_state,
     env_dev, env_staging, env_prod, rollout_mode, required_license)
VALUES
    -- ── Platform ──────────────────────────────────────────────────────
    (1,  'platform_admin',          'Platform Admin',             'Super-admin access across all orgs and platform settings.',               1, 'platform', 'permissioned', 'active', true, true, true, 'simple', null),
    (2,  'node_catalog',            'Node Catalog',               'Browse and inspect the platform node registry.',                          8, 'platform', 'authenticated', 'active', true, true, true, 'simple', null),

    -- ── IAM: Org-level ────────────────────────────────────────────────
    (3,  'orgs',                    'Organisations',              'Manage org identity and settings.',                                       2, 'org',      'permissioned', 'active', true, true, true, 'simple', null),
    (4,  'workspaces',              'Workspaces',                 'Manage workspaces within an org.',                                        2, 'org',      'permissioned', 'active', true, true, true, 'simple', null),
    (5,  'users',                   'Users',                      'Manage user accounts within an org.',                                     2, 'org',      'permissioned', 'active', true, true, true, 'simple', null),
    (6,  'memberships',             'Memberships',                'Manage org membership (add/remove members).',                             2, 'org',      'permissioned', 'active', true, true, true, 'simple', null),
    (7,  'roles',                   'Roles',                      'Manage roles and their capability grants.',                               2, 'org',      'permissioned', 'active', true, true, true, 'simple', null),
    (8,  'groups',                  'Groups',                     'Manage user groups within an org.',                                       2, 'org',      'permissioned', 'active', true, true, true, 'simple', null),
    (9,  'applications',            'Applications',               'Manage client applications registered to an org.',                        2, 'org',      'permissioned', 'active', true, true, true, 'simple', null),

    -- ── IAM: Auth & security ──────────────────────────────────────────
    (10, 'api_keys',                'API Keys',                   'Manage API keys for programmatic access.',                                2, 'org',      'permissioned', 'active', true, true, true, 'simple', null),
    (11, 'sessions',                'Sessions',                   'View and revoke user sessions.',                                          2, 'org',      'permissioned', 'active', true, true, true, 'simple', null),
    (12, 'credentials',             'Credentials',                'Manage user credentials (passwords, passkeys, TOTP).',                    2, 'org',      'permissioned', 'active', true, true, true, 'simple', null),
    (13, 'auth_policy',             'Auth Policy',                'Configure org-wide authentication policy (MFA, password strength).',      2, 'org',      'permissioned', 'active', true, true, true, 'simple', null),
    (14, 'portal_views',            'Portal Views',               'Manage which portal views are exposed to each role.',                     2, 'org',      'permissioned', 'active', true, true, true, 'simple', null),

    -- ── IAM: Enterprise SSO / provisioning ───────────────────────────
    (15, 'oidc_sso',                'OIDC SSO',                   'Configure OIDC single-sign-on providers.',                               2, 'org',      'permissioned', 'active', true, true, true, 'simple', null),
    (16, 'saml_sso',                'SAML SSO',                   'Configure SAML single-sign-on providers.',                               2, 'org',      'permissioned', 'active', true, true, true, 'simple', null),
    (17, 'scim',                    'SCIM Provisioning',          'Configure SCIM tokens for automated user provisioning.',                  2, 'org',      'permissioned', 'active', true, true, true, 'simple', null),
    (18, 'mfa_policy',              'MFA Policy',                 'Enforce and configure multi-factor authentication requirements.',         2, 'org',      'permissioned', 'active', true, true, true, 'simple', null),
    (19, 'ip_allowlist',            'IP Allowlist',               'Restrict org access to specific IP ranges.',                             2, 'org',      'permissioned', 'active', true, true, true, 'simple', null),
    (20, 'impersonation',           'Impersonation',              'Allow admins to act as another user for support purposes.',              2, 'org',      'permissioned', 'active', true, true, true, 'simple', null),
    (21, 'siem_export',             'SIEM Export',                'Configure export of audit events to an external SIEM.',                  2, 'org',      'permissioned', 'active', true, true, true, 'simple', null),
    (22, 'tos',                     'Terms of Service',           'Manage terms-of-service acceptance for org members.',                    2, 'org',      'permissioned', 'active', true, true, true, 'simple', null),

    -- ── Vault ─────────────────────────────────────────────────────────
    (23, 'vault_secrets',           'Vault Secrets',              'Manage secrets stored in the vault.',                                     3, 'org',      'permissioned', 'active', true, true, true, 'simple', null),
    (24, 'vault_configs',           'Vault Configs',              'Manage runtime configuration entries in the vault.',                      3, 'org',      'permissioned', 'active', true, true, true, 'simple', null),

    -- ── Audit ─────────────────────────────────────────────────────────
    (25, 'audit_explorer',          'Audit Explorer',             'Browse and search the org audit log.',                                    4, 'org',      'permissioned', 'active', true, true, true, 'simple', null),
    (26, 'audit_saved_views',       'Audit Saved Views',          'Create and manage saved audit filter views.',                             4, 'org',      'permissioned', 'active', true, true, true, 'simple', null),

    -- ── Monitoring ────────────────────────────────────────────────────
    (27, 'monitoring_logs',         'Monitoring: Logs',           'View and search application logs.',                                       5, 'org',      'permissioned', 'active', true, true, true, 'simple', null),
    (28, 'monitoring_metrics',      'Monitoring: Metrics',        'View metric charts and time-series data.',                                5, 'org',      'permissioned', 'active', true, true, true, 'simple', null),
    (29, 'monitoring_traces',       'Monitoring: Traces',         'View distributed traces.',                                                5, 'org',      'permissioned', 'active', true, true, true, 'simple', null),
    (30, 'monitoring_dashboards',   'Monitoring: Dashboards',     'Create and manage monitoring dashboards.',                                5, 'org',      'permissioned', 'active', true, true, true, 'simple', null),
    (31, 'monitoring_alerts',       'Monitoring: Alerts',         'Configure alerting rules and notification channels.',                     5, 'org',      'permissioned', 'active', true, true, true, 'simple', null),

    -- ── Notify ────────────────────────────────────────────────────────
    (32, 'notify_templates',        'Notify: Templates',          'Manage notification message templates.',                                  6, 'org',      'permissioned', 'active', true, true, true, 'simple', null),
    (33, 'notify_deliveries',       'Notify: Deliveries',         'View notification delivery history and status.',                          6, 'org',      'permissioned', 'active', true, true, true, 'simple', null),
    (34, 'notify_send',             'Notify: Send',               'Trigger notification sends manually or via API.',                         6, 'org',      'permissioned', 'active', true, true, true, 'simple', null),
    (35, 'notify_preferences',      'Notify: Preferences',        'Manage per-user notification preferences.',                               6, 'org',      'permissioned', 'active', true, true, true, 'simple', null),
    (36, 'notify_campaigns',        'Notify: Campaigns',          'Create and schedule bulk notification campaigns.',                        6, 'org',      'permissioned', 'active', true, true, true, 'simple', null),
    (37, 'notify_webpush',          'Notify: Web Push',           'Manage web push notification subscriptions and sends.',                   6, 'org',      'permissioned', 'active', true, true, true, 'simple', null),

    -- ── Feature Flags ─────────────────────────────────────────────────
    (38, 'feature_flags',           'Feature Flags',              'Manage feature flag definitions and their capability metadata.',          7, 'org',      'permissioned', 'active', true, true, true, 'simple', null),
    (39, 'feature_flag_rules',      'Feature Flag Rules',         'Manage targeting rules for flags with rollout_mode=targeted.',           7, 'org',      'permissioned', 'active', true, true, true, 'simple', null),
    (40, 'feature_flag_overrides',  'Feature Flag Overrides',     'Manage per-entity force-value overrides for targeted flags.',            7, 'org',      'permissioned', 'active', true, true, true, 'simple', null)
ON CONFLICT (id) DO NOTHING;

-- ── Step 6: dim_feature_permissions ──────────────────────────────────
--
-- Cross-product of (flag × action). Code = flag.code + '.' + action.code.
-- One permission per flag × action pair — UNIQUE enforced at the constraint level.

CREATE TABLE "09_featureflags"."04_dim_feature_permissions" (
    id              SMALLINT NOT NULL,
    flag_id         SMALLINT NOT NULL,
    action_id       SMALLINT NOT NULL,
    code            TEXT NOT NULL,
    name            TEXT NOT NULL,
    description     TEXT,
    deprecated_at   TIMESTAMP,
    CONSTRAINT pk_ff_dim_feature_permissions PRIMARY KEY (id),
    CONSTRAINT uq_ff_dim_feature_permissions_code UNIQUE (code),
    CONSTRAINT uq_ff_dim_feature_permissions_pair UNIQUE (flag_id, action_id),
    CONSTRAINT fk_ff_dim_feature_permissions_flag FOREIGN KEY (flag_id)
        REFERENCES "09_featureflags"."03_dim_feature_flags"(id),
    CONSTRAINT fk_ff_dim_feature_permissions_action FOREIGN KEY (action_id)
        REFERENCES "09_featureflags"."01_dim_permission_actions"(id)
);

CREATE INDEX idx_ff_dim_feature_permissions_flag
    ON "09_featureflags"."04_dim_feature_permissions" (flag_id);
CREATE INDEX idx_ff_dim_feature_permissions_action
    ON "09_featureflags"."04_dim_feature_permissions" (action_id);

COMMENT ON TABLE  "09_featureflags"."04_dim_feature_permissions" IS 'Cross-product of capability flag × action. Each row is a grantable permission (e.g. orgs.view, vault_secrets.delete). Roles reference rows from this table via lnk_role_feature_permissions.';
COMMENT ON COLUMN "09_featureflags"."04_dim_feature_permissions".id IS 'Permanent manual id. Never renumber.';
COMMENT ON COLUMN "09_featureflags"."04_dim_feature_permissions".flag_id IS 'FK to dim_feature_flags.';
COMMENT ON COLUMN "09_featureflags"."04_dim_feature_permissions".action_id IS 'FK to dim_permission_actions.';
COMMENT ON COLUMN "09_featureflags"."04_dim_feature_permissions".code IS 'Dot-notation permission code: {flag.code}.{action.code} (e.g. orgs.view).';
COMMENT ON COLUMN "09_featureflags"."04_dim_feature_permissions".name IS 'Human-readable name (e.g. "Organisations — View").';
COMMENT ON COLUMN "09_featureflags"."04_dim_feature_permissions".description IS 'What this permission grants.';
COMMENT ON COLUMN "09_featureflags"."04_dim_feature_permissions".deprecated_at IS 'Non-null when this permission should no longer be granted.';

-- Seed: generate (flag × action) pairs.
--
-- Action map:  1=view 2=create 3=update 4=delete 5=assign 6=configure 7=export 8=impersonate
--
-- Default grid:
--   most capabilities → view + create + update + delete  (actions 1-4)
--   platform_admin   → all 8 actions
--   impersonation    → view + impersonate (1, 8)
--   siem_export      → view + configure + export (1, 6, 7)
--   node_catalog     → view only (1)
--   sessions         → view + delete (revoke) (1, 4)
--   notify_send      → view + create (trigger a send) (1, 2)
--   notify_deliveries → view + export (1, 7)
--   auth_policy      → view + configure (1, 6)
--   mfa_policy       → view + configure (1, 6)
--   ip_allowlist     → view + create + update + delete + configure (1-4, 6)
--   roles            → view + create + update + delete + assign (1-5)
--   memberships      → view + create + delete + assign (1, 2, 4, 5)
--   portal_views     → view + configure (1, 6)
--   tos              → view + configure (1, 6)
--   audit_*          → view + export (1, 7)

INSERT INTO "09_featureflags"."04_dim_feature_permissions"
    (id, flag_id, action_id, code, name, description)
VALUES
    -- ── platform_admin (flag 1) — all 8 actions ──────────────────────
    (1,   1, 1, 'platform_admin.view',        'Platform Admin — View',        'View platform-level configuration and all orgs.'),
    (2,   1, 2, 'platform_admin.create',      'Platform Admin — Create',      'Create platform-level resources.'),
    (3,   1, 3, 'platform_admin.update',      'Platform Admin — Update',      'Modify platform-level configuration.'),
    (4,   1, 4, 'platform_admin.delete',      'Platform Admin — Delete',      'Delete platform-level resources.'),
    (5,   1, 5, 'platform_admin.assign',      'Platform Admin — Assign',      'Assign platform roles and grants.'),
    (6,   1, 6, 'platform_admin.configure',   'Platform Admin — Configure',   'Configure platform-wide settings.'),
    (7,   1, 7, 'platform_admin.export',      'Platform Admin — Export',      'Export platform data.'),
    (8,   1, 8, 'platform_admin.impersonate', 'Platform Admin — Impersonate', 'Impersonate any user platform-wide.'),

    -- ── node_catalog (flag 2) — view only ────────────────────────────
    (9,   2, 1, 'node_catalog.view',          'Node Catalog — View',          'Browse and inspect the platform node registry.'),

    -- ── orgs (flag 3) — view + create + update + delete ──────────────
    (10,  3, 1, 'orgs.view',                  'Organisations — View',         'List and read org details.'),
    (11,  3, 2, 'orgs.create',                'Organisations — Create',       'Create a new organisation.'),
    (12,  3, 3, 'orgs.update',                'Organisations — Update',       'Modify org settings and metadata.'),
    (13,  3, 4, 'orgs.delete',                'Organisations — Delete',       'Soft-delete an organisation.'),

    -- ── workspaces (flag 4) — view + create + update + delete ────────
    (14,  4, 1, 'workspaces.view',             'Workspaces — View',           'List and read workspace details.'),
    (15,  4, 2, 'workspaces.create',           'Workspaces — Create',         'Create a new workspace.'),
    (16,  4, 3, 'workspaces.update',           'Workspaces — Update',         'Modify workspace settings.'),
    (17,  4, 4, 'workspaces.delete',           'Workspaces — Delete',         'Soft-delete a workspace.'),

    -- ── users (flag 5) — view + create + update + delete ─────────────
    (18,  5, 1, 'users.view',                  'Users — View',                'List and read user profiles.'),
    (19,  5, 2, 'users.create',                'Users — Create',              'Create a new user account.'),
    (20,  5, 3, 'users.update',                'Users — Update',              'Modify user profile and metadata.'),
    (21,  5, 4, 'users.delete',                'Users — Delete',              'Soft-delete a user account.'),

    -- ── memberships (flag 6) — view + create + delete + assign ───────
    (22,  6, 1, 'memberships.view',            'Memberships — View',          'List org membership.'),
    (23,  6, 2, 'memberships.create',          'Memberships — Create',        'Add a member to the org.'),
    (24,  6, 4, 'memberships.delete',          'Memberships — Delete',        'Remove a member from the org.'),
    (25,  6, 5, 'memberships.assign',          'Memberships — Assign',        'Assign a role to an org member.'),

    -- ── roles (flag 7) — view + create + update + delete + assign ────
    (26,  7, 1, 'roles.view',                  'Roles — View',                'List and read role definitions.'),
    (27,  7, 2, 'roles.create',                'Roles — Create',              'Create a new role.'),
    (28,  7, 3, 'roles.update',                'Roles — Update',              'Modify role name and description.'),
    (29,  7, 4, 'roles.delete',                'Roles — Delete',              'Soft-delete a role.'),
    (30,  7, 5, 'roles.assign',                'Roles — Assign',              'Grant capability permissions to a role.'),

    -- ── groups (flag 8) — view + create + update + delete ────────────
    (31,  8, 1, 'groups.view',                 'Groups — View',               'List and read groups.'),
    (32,  8, 2, 'groups.create',               'Groups — Create',             'Create a group.'),
    (33,  8, 3, 'groups.update',               'Groups — Update',             'Modify group name and membership.'),
    (34,  8, 4, 'groups.delete',               'Groups — Delete',             'Soft-delete a group.'),

    -- ── applications (flag 9) — view + create + update + delete ──────
    (35,  9, 1, 'applications.view',           'Applications — View',         'List and read client applications.'),
    (36,  9, 2, 'applications.create',         'Applications — Create',       'Register a new client application.'),
    (37,  9, 3, 'applications.update',         'Applications — Update',       'Modify application settings.'),
    (38,  9, 4, 'applications.delete',         'Applications — Delete',       'Soft-delete an application.'),

    -- ── api_keys (flag 10) — view + create + update + delete ─────────
    (39, 10, 1, 'api_keys.view',               'API Keys — View',             'List API keys (secrets not shown).'),
    (40, 10, 2, 'api_keys.create',             'API Keys — Create',           'Issue a new API key.'),
    (41, 10, 3, 'api_keys.update',             'API Keys — Update',           'Modify API key label or expiry.'),
    (42, 10, 4, 'api_keys.delete',             'API Keys — Delete',           'Revoke an API key.'),

    -- ── sessions (flag 11) — view + delete (revoke) ───────────────────
    (43, 11, 1, 'sessions.view',               'Sessions — View',             'List active user sessions.'),
    (44, 11, 4, 'sessions.delete',             'Sessions — Delete',           'Revoke a user session.'),

    -- ── credentials (flag 12) — view + create + update + delete ──────
    (45, 12, 1, 'credentials.view',            'Credentials — View',          'View credential metadata (not raw secrets).'),
    (46, 12, 2, 'credentials.create',          'Credentials — Create',        'Add a credential (set password, register passkey).'),
    (47, 12, 3, 'credentials.update',          'Credentials — Update',        'Change a credential (reset password).'),
    (48, 12, 4, 'credentials.delete',          'Credentials — Delete',        'Revoke a credential.'),

    -- ── auth_policy (flag 13) — view + configure ──────────────────────
    (49, 13, 1, 'auth_policy.view',            'Auth Policy — View',          'Read the org authentication policy.'),
    (50, 13, 6, 'auth_policy.configure',       'Auth Policy — Configure',     'Modify authentication policy settings.'),

    -- ── portal_views (flag 14) — view + configure ────────────────────
    (51, 14, 1, 'portal_views.view',           'Portal Views — View',         'List portal views assigned to roles.'),
    (52, 14, 6, 'portal_views.configure',      'Portal Views — Configure',    'Assign or remove portal views from roles.'),

    -- ── oidc_sso (flag 15) — view + create + update + delete ─────────
    (53, 15, 1, 'oidc_sso.view',               'OIDC SSO — View',             'Read OIDC provider configuration.'),
    (54, 15, 2, 'oidc_sso.create',             'OIDC SSO — Create',           'Register an OIDC provider.'),
    (55, 15, 3, 'oidc_sso.update',             'OIDC SSO — Update',           'Modify an OIDC provider configuration.'),
    (56, 15, 4, 'oidc_sso.delete',             'OIDC SSO — Delete',           'Remove an OIDC provider.'),

    -- ── saml_sso (flag 16) — view + create + update + delete ─────────
    (57, 16, 1, 'saml_sso.view',               'SAML SSO — View',             'Read SAML provider configuration.'),
    (58, 16, 2, 'saml_sso.create',             'SAML SSO — Create',           'Register a SAML provider.'),
    (59, 16, 3, 'saml_sso.update',             'SAML SSO — Update',           'Modify a SAML provider configuration.'),
    (60, 16, 4, 'saml_sso.delete',             'SAML SSO — Delete',           'Remove a SAML provider.'),

    -- ── scim (flag 17) — view + create + update + delete ─────────────
    (61, 17, 1, 'scim.view',                   'SCIM — View',                 'Read SCIM token configuration.'),
    (62, 17, 2, 'scim.create',                 'SCIM — Create',               'Issue a SCIM token.'),
    (63, 17, 3, 'scim.update',                 'SCIM — Update',               'Modify SCIM token settings.'),
    (64, 17, 4, 'scim.delete',                 'SCIM — Delete',               'Revoke a SCIM token.'),

    -- ── mfa_policy (flag 18) — view + configure ───────────────────────
    (65, 18, 1, 'mfa_policy.view',             'MFA Policy — View',           'Read the org MFA enforcement policy.'),
    (66, 18, 6, 'mfa_policy.configure',        'MFA Policy — Configure',      'Enable or modify the org MFA enforcement policy.'),

    -- ── ip_allowlist (flag 19) — view + create + update + delete + configure
    (67, 19, 1, 'ip_allowlist.view',           'IP Allowlist — View',         'List IP allowlist entries.'),
    (68, 19, 2, 'ip_allowlist.create',         'IP Allowlist — Create',       'Add an IP allowlist entry.'),
    (69, 19, 3, 'ip_allowlist.update',         'IP Allowlist — Update',       'Modify an IP allowlist entry.'),
    (70, 19, 4, 'ip_allowlist.delete',         'IP Allowlist — Delete',       'Remove an IP allowlist entry.'),
    (71, 19, 6, 'ip_allowlist.configure',      'IP Allowlist — Configure',    'Toggle IP allowlist enforcement on or off.'),

    -- ── impersonation (flag 20) — view + impersonate ──────────────────
    (72, 20, 1, 'impersonation.view',          'Impersonation — View',        'List active impersonation sessions.'),
    (73, 20, 8, 'impersonation.impersonate',   'Impersonation — Impersonate', 'Start an impersonation session as another user.'),

    -- ── siem_export (flag 21) — view + configure + export ────────────
    (74, 21, 1, 'siem_export.view',            'SIEM Export — View',          'Read SIEM export configuration.'),
    (75, 21, 6, 'siem_export.configure',       'SIEM Export — Configure',     'Configure SIEM export endpoint and filters.'),
    (76, 21, 7, 'siem_export.export',          'SIEM Export — Export',        'Trigger a manual SIEM data export.'),

    -- ── tos (flag 22) — view + configure ─────────────────────────────
    (77, 22, 1, 'tos.view',                    'Terms of Service — View',     'Read ToS acceptance status for org members.'),
    (78, 22, 6, 'tos.configure',               'Terms of Service — Configure','Publish or update the org ToS and configure enforcement.'),

    -- ── vault_secrets (flag 23) — view + create + update + delete ────
    (79, 23, 1, 'vault_secrets.view',          'Vault Secrets — View',        'List secret keys (values never exposed via API).'),
    (80, 23, 2, 'vault_secrets.create',        'Vault Secrets — Create',      'Create a new secret entry.'),
    (81, 23, 3, 'vault_secrets.update',        'Vault Secrets — Update',      'Update a secret value.'),
    (82, 23, 4, 'vault_secrets.delete',        'Vault Secrets — Delete',      'Delete a secret.'),

    -- ── vault_configs (flag 24) — view + create + update + delete ────
    (83, 24, 1, 'vault_configs.view',          'Vault Configs — View',        'List configuration entries.'),
    (84, 24, 2, 'vault_configs.create',        'Vault Configs — Create',      'Create a configuration entry.'),
    (85, 24, 3, 'vault_configs.update',        'Vault Configs — Update',      'Update a configuration entry.'),
    (86, 24, 4, 'vault_configs.delete',        'Vault Configs — Delete',      'Delete a configuration entry.'),

    -- ── audit_explorer (flag 25) — view + export ──────────────────────
    (87, 25, 1, 'audit_explorer.view',         'Audit Explorer — View',       'Browse and search the audit log.'),
    (88, 25, 7, 'audit_explorer.export',       'Audit Explorer — Export',     'Export audit log entries.'),

    -- ── audit_saved_views (flag 26) — view + create + update + delete
    (89, 26, 1, 'audit_saved_views.view',      'Audit Saved Views — View',    'List saved audit filter views.'),
    (90, 26, 2, 'audit_saved_views.create',    'Audit Saved Views — Create',  'Create a saved audit filter view.'),
    (91, 26, 3, 'audit_saved_views.update',    'Audit Saved Views — Update',  'Rename or modify a saved view.'),
    (92, 26, 4, 'audit_saved_views.delete',    'Audit Saved Views — Delete',  'Delete a saved view.'),

    -- ── monitoring_logs (flag 27) — view + export ────────────────────
    (93, 27, 1, 'monitoring_logs.view',        'Monitoring: Logs — View',     'View application logs.'),
    (94, 27, 7, 'monitoring_logs.export',      'Monitoring: Logs — Export',   'Export log entries.'),

    -- ── monitoring_metrics (flag 28) — view + export ─────────────────
    (95, 28, 1, 'monitoring_metrics.view',     'Monitoring: Metrics — View',  'View metric charts and time-series.'),
    (96, 28, 7, 'monitoring_metrics.export',   'Monitoring: Metrics — Export','Export metric data.'),

    -- ── monitoring_traces (flag 29) — view + export ──────────────────
    (97, 29, 1, 'monitoring_traces.view',      'Monitoring: Traces — View',   'View distributed traces.'),
    (98, 29, 7, 'monitoring_traces.export',    'Monitoring: Traces — Export', 'Export trace data.'),

    -- ── monitoring_dashboards (flag 30) — view + create + update + delete
    (99,  30, 1, 'monitoring_dashboards.view',   'Monitoring: Dashboards — View',   'View monitoring dashboards.'),
    (100, 30, 2, 'monitoring_dashboards.create', 'Monitoring: Dashboards — Create', 'Create a monitoring dashboard.'),
    (101, 30, 3, 'monitoring_dashboards.update', 'Monitoring: Dashboards — Update', 'Modify a monitoring dashboard.'),
    (102, 30, 4, 'monitoring_dashboards.delete', 'Monitoring: Dashboards — Delete', 'Delete a monitoring dashboard.'),

    -- ── monitoring_alerts (flag 31) — view + create + update + delete
    (103, 31, 1, 'monitoring_alerts.view',      'Monitoring: Alerts — View',   'View alerting rules.'),
    (104, 31, 2, 'monitoring_alerts.create',    'Monitoring: Alerts — Create', 'Create an alerting rule.'),
    (105, 31, 3, 'monitoring_alerts.update',    'Monitoring: Alerts — Update', 'Modify an alerting rule.'),
    (106, 31, 4, 'monitoring_alerts.delete',    'Monitoring: Alerts — Delete', 'Delete an alerting rule.'),

    -- ── notify_templates (flag 32) — view + create + update + delete ─
    (107, 32, 1, 'notify_templates.view',       'Notify: Templates — View',    'List and read notification templates.'),
    (108, 32, 2, 'notify_templates.create',     'Notify: Templates — Create',  'Create a notification template.'),
    (109, 32, 3, 'notify_templates.update',     'Notify: Templates — Update',  'Edit a notification template.'),
    (110, 32, 4, 'notify_templates.delete',     'Notify: Templates — Delete',  'Delete a notification template.'),

    -- ── notify_deliveries (flag 33) — view + export ───────────────────
    (111, 33, 1, 'notify_deliveries.view',      'Notify: Deliveries — View',   'View notification delivery history.'),
    (112, 33, 7, 'notify_deliveries.export',    'Notify: Deliveries — Export', 'Export delivery history.'),

    -- ── notify_send (flag 34) — view + create ─────────────────────────
    (113, 34, 1, 'notify_send.view',            'Notify: Send — View',         'View send history and queue.'),
    (114, 34, 2, 'notify_send.create',          'Notify: Send — Create',       'Trigger a notification send.'),

    -- ── notify_preferences (flag 35) — view + create + update + delete
    (115, 35, 1, 'notify_preferences.view',     'Notify: Preferences — View',  'View user notification preferences.'),
    (116, 35, 2, 'notify_preferences.create',   'Notify: Preferences — Create','Set notification preferences for a user.'),
    (117, 35, 3, 'notify_preferences.update',   'Notify: Preferences — Update','Modify notification preferences.'),
    (118, 35, 4, 'notify_preferences.delete',   'Notify: Preferences — Delete','Reset notification preferences.'),

    -- ── notify_campaigns (flag 36) — view + create + update + delete ─
    (119, 36, 1, 'notify_campaigns.view',       'Notify: Campaigns — View',    'List and read campaign definitions.'),
    (120, 36, 2, 'notify_campaigns.create',     'Notify: Campaigns — Create',  'Create a notification campaign.'),
    (121, 36, 3, 'notify_campaigns.update',     'Notify: Campaigns — Update',  'Modify a campaign.'),
    (122, 36, 4, 'notify_campaigns.delete',     'Notify: Campaigns — Delete',  'Delete a campaign.'),

    -- ── notify_webpush (flag 37) — view + create + update + delete ───
    (123, 37, 1, 'notify_webpush.view',         'Notify: Web Push — View',     'View web push subscriptions.'),
    (124, 37, 2, 'notify_webpush.create',       'Notify: Web Push — Create',   'Register a web push subscription.'),
    (125, 37, 3, 'notify_webpush.update',       'Notify: Web Push — Update',   'Modify a web push subscription.'),
    (126, 37, 4, 'notify_webpush.delete',       'Notify: Web Push — Delete',   'Revoke a web push subscription.'),

    -- ── feature_flags (flag 38) — view + create + update + delete ────
    (127, 38, 1, 'feature_flags.view',          'Feature Flags — View',        'List and read feature flag definitions.'),
    (128, 38, 2, 'feature_flags.create',        'Feature Flags — Create',      'Create a feature flag.'),
    (129, 38, 3, 'feature_flags.update',        'Feature Flags — Update',      'Modify a feature flag definition.'),
    (130, 38, 4, 'feature_flags.delete',        'Feature Flags — Delete',      'Soft-delete a feature flag.'),

    -- ── feature_flag_rules (flag 39) — view + create + update + delete
    (131, 39, 1, 'feature_flag_rules.view',     'Feature Flag Rules — View',   'List targeting rules for a flag.'),
    (132, 39, 2, 'feature_flag_rules.create',   'Feature Flag Rules — Create', 'Create a targeting rule.'),
    (133, 39, 3, 'feature_flag_rules.update',   'Feature Flag Rules — Update', 'Modify a targeting rule.'),
    (134, 39, 4, 'feature_flag_rules.delete',   'Feature Flag Rules — Delete', 'Delete a targeting rule.'),

    -- ── feature_flag_overrides (flag 40) — view + create + update + delete
    (135, 40, 1, 'feature_flag_overrides.view',   'Feature Flag Overrides — View',   'List per-entity overrides.'),
    (136, 40, 2, 'feature_flag_overrides.create', 'Feature Flag Overrides — Create', 'Create a force-value override.'),
    (137, 40, 3, 'feature_flag_overrides.update', 'Feature Flag Overrides — Update', 'Modify an override value.'),
    (138, 40, 4, 'feature_flag_overrides.delete', 'Feature Flag Overrides — Delete', 'Remove an override.')
ON CONFLICT (id) DO NOTHING;

-- ── Step 7: lnk_role_feature_permissions ─────────────────────────────

CREATE TABLE "09_featureflags"."40_lnk_role_feature_permissions" (
    id                      VARCHAR(36) NOT NULL,
    role_id                 VARCHAR(36) NOT NULL,
    feature_permission_id   SMALLINT NOT NULL,
    created_by              VARCHAR(36) NOT NULL,
    created_at              TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_ff_lnk_role_feature_permissions PRIMARY KEY (id),
    CONSTRAINT fk_ff_lnk_rfp_role FOREIGN KEY (role_id)
        REFERENCES "03_iam"."13_fct_roles"(id) ON DELETE CASCADE,
    CONSTRAINT fk_ff_lnk_rfp_feature_permission FOREIGN KEY (feature_permission_id)
        REFERENCES "09_featureflags"."04_dim_feature_permissions"(id)
);

CREATE UNIQUE INDEX uq_ff_lnk_role_feature_permissions
    ON "09_featureflags"."40_lnk_role_feature_permissions" (role_id, feature_permission_id);
CREATE INDEX idx_ff_lnk_rfp_role
    ON "09_featureflags"."40_lnk_role_feature_permissions" (role_id);
CREATE INDEX idx_ff_lnk_rfp_feature_permission
    ON "09_featureflags"."40_lnk_role_feature_permissions" (feature_permission_id);

COMMENT ON TABLE  "09_featureflags"."40_lnk_role_feature_permissions" IS 'Role-to-capability grant table. Each row grants a role one (flag, action) permission. Immutable rows — revoke = DELETE. Scope is inherited from the role row (fct_roles.scope_org_id / scope_workspace_id).';
COMMENT ON COLUMN "09_featureflags"."40_lnk_role_feature_permissions".id IS 'UUID v7.';
COMMENT ON COLUMN "09_featureflags"."40_lnk_role_feature_permissions".role_id IS 'FK to fct_roles. CASCADE delete removes grants when a role is hard-deleted.';
COMMENT ON COLUMN "09_featureflags"."40_lnk_role_feature_permissions".feature_permission_id IS 'FK to dim_feature_permissions — the specific (flag, action) pair being granted.';
COMMENT ON COLUMN "09_featureflags"."40_lnk_role_feature_permissions".created_by IS 'UUID of the actor who created this grant.';
COMMENT ON COLUMN "09_featureflags"."40_lnk_role_feature_permissions".created_at IS 'Insert timestamp.';

-- ── Step 8: System role grants ────────────────────────────────────────
--
-- Grants are seeded using the EAV-stored role code in dtl_attrs (attr code='code',
-- entity_type_id=4 for role). This JOIN is stable because role codes are immutable
-- once seeded by app init.
--
-- If the system roles have not yet been seeded by app init (fresh install path),
-- this block inserts zero rows and is safe. Grants will be applied by re-running
-- the seeder after app init creates the role rows.
--
-- Grant policy:
--   platform_super_admin → every permission on every flag (all 138 rows)
--   org_admin            → all CRUD on org-scoped flags (flags 3-40, excl platform flags 1-2)
--   org_member           → view + create + update on org-scoped flags
--   org_viewer           → view-only on org-scoped flags
--   workspace_admin      → CRUD on workspace-scoped flags (none seeded yet — empty grant)
--   workspace_contributor → view + create + update on workspace-scoped flags (empty)
--   workspace_viewer     → view-only on workspace-scoped flags (empty)

-- Resolve role IDs once into a temp table for clarity.
CREATE TEMP TABLE _23r_system_roles ON COMMIT DROP AS
SELECT
    a.key_text AS role_code,
    r.id AS role_id
FROM "03_iam"."13_fct_roles" r
JOIN "03_iam"."21_dtl_attrs" a
    ON a.entity_type_id = 4 AND a.entity_id = r.id
JOIN "03_iam"."20_dtl_attr_defs" ad
    ON ad.id = a.attr_def_id AND ad.code = 'code'
WHERE a.key_text IN (
    'platform_super_admin',
    'org_admin', 'org_member', 'org_viewer',
    'workspace_admin', 'workspace_contributor', 'workspace_viewer'
)
AND r.deleted_at IS NULL;

-- platform_super_admin: every permission
INSERT INTO "09_featureflags"."40_lnk_role_feature_permissions"
    (id, role_id, feature_permission_id, created_by, created_at)
SELECT
    gen_random_uuid()::VARCHAR(36),
    sr.role_id,
    fp.id,
    sr.role_id,
    CURRENT_TIMESTAMP
FROM _23r_system_roles sr
JOIN "09_featureflags"."04_dim_feature_permissions" fp ON true
WHERE sr.role_code = 'platform_super_admin'
ON CONFLICT DO NOTHING;

-- org_admin: all permissions on org-scoped flags (feature_scope = 'org')
INSERT INTO "09_featureflags"."40_lnk_role_feature_permissions"
    (id, role_id, feature_permission_id, created_by, created_at)
SELECT
    gen_random_uuid()::VARCHAR(36),
    sr.role_id,
    fp.id,
    sr.role_id,
    CURRENT_TIMESTAMP
FROM _23r_system_roles sr
JOIN "09_featureflags"."04_dim_feature_permissions" fp
    ON fp.flag_id IN (
        SELECT id FROM "09_featureflags"."03_dim_feature_flags"
        WHERE feature_scope = 'org'
    )
WHERE sr.role_code = 'org_admin'
ON CONFLICT DO NOTHING;

-- org_member: view + create + update on org-scoped flags
INSERT INTO "09_featureflags"."40_lnk_role_feature_permissions"
    (id, role_id, feature_permission_id, created_by, created_at)
SELECT
    gen_random_uuid()::VARCHAR(36),
    sr.role_id,
    fp.id,
    sr.role_id,
    CURRENT_TIMESTAMP
FROM _23r_system_roles sr
JOIN "09_featureflags"."04_dim_feature_permissions" fp
    ON fp.flag_id IN (
        SELECT id FROM "09_featureflags"."03_dim_feature_flags"
        WHERE feature_scope = 'org'
    )
    AND fp.action_id IN (1, 2, 3)  -- view, create, update
WHERE sr.role_code = 'org_member'
ON CONFLICT DO NOTHING;

-- org_viewer: view-only on org-scoped flags
INSERT INTO "09_featureflags"."40_lnk_role_feature_permissions"
    (id, role_id, feature_permission_id, created_by, created_at)
SELECT
    gen_random_uuid()::VARCHAR(36),
    sr.role_id,
    fp.id,
    sr.role_id,
    CURRENT_TIMESTAMP
FROM _23r_system_roles sr
JOIN "09_featureflags"."04_dim_feature_permissions" fp
    ON fp.flag_id IN (
        SELECT id FROM "09_featureflags"."03_dim_feature_flags"
        WHERE feature_scope = 'org'
    )
    AND fp.action_id = 1  -- view only
WHERE sr.role_code = 'org_viewer'
ON CONFLICT DO NOTHING;

-- workspace_admin / workspace_contributor / workspace_viewer:
-- No workspace-scoped flags are seeded yet. These roles receive zero grants here.
-- When workspace-scoped flags are added, a follow-up migration seeds their grants.

DROP TABLE IF EXISTS _23r_system_roles;

-- ── Step 9: Views ─────────────────────────────────────────────────────

CREATE VIEW "09_featureflags"."v_feature_permissions" AS
SELECT
    fp.id,
    fp.code,
    fp.name,
    fp.description,
    fp.deprecated_at,
    df.id           AS flag_id,
    df.code         AS flag_code,
    df.name         AS flag_name,
    df.feature_scope,
    df.access_mode,
    df.lifecycle_state,
    cat.code        AS category_code,
    cat.label       AS category_label,
    act.id          AS action_id,
    act.code        AS action_code,
    act.label       AS action_label,
    act.sort_order  AS action_sort_order
FROM "09_featureflags"."04_dim_feature_permissions" fp
JOIN "09_featureflags"."03_dim_feature_flags"         df  ON df.id  = fp.flag_id
JOIN "09_featureflags"."02_dim_feature_flag_categories" cat ON cat.id = df.category_id
JOIN "09_featureflags"."01_dim_permission_actions"    act ON act.id = fp.action_id;

COMMENT ON VIEW "09_featureflags"."v_feature_permissions" IS 'Flat denormalized shape for the capability catalog. Joins flag + action + category so callers never see SMALLINT ids.';

CREATE VIEW "09_featureflags"."v_role_feature_permissions" AS
SELECT
    lnk.id          AS grant_id,
    lnk.role_id,
    lnk.created_by,
    lnk.created_at,
    vfp.code        AS permission_code,
    vfp.name        AS permission_name,
    vfp.flag_id,
    vfp.flag_code,
    vfp.flag_name,
    vfp.feature_scope,
    vfp.access_mode,
    vfp.lifecycle_state,
    vfp.category_code,
    vfp.category_label,
    vfp.action_id,
    vfp.action_code,
    vfp.action_label
FROM "09_featureflags"."40_lnk_role_feature_permissions" lnk
JOIN "09_featureflags"."v_feature_permissions" vfp
    ON vfp.id = lnk.feature_permission_id;

COMMENT ON VIEW "09_featureflags"."v_role_feature_permissions" IS 'Resolves role_id to the full set of (flag, action) grants. Used by the resolver to answer require_permission("flag.action") for a given role set. One row per grant.';

-- DOWN ====

-- Drop new views
DROP VIEW IF EXISTS "09_featureflags"."v_role_feature_permissions";
DROP VIEW IF EXISTS "09_featureflags"."v_feature_permissions";

-- Drop new link table
DROP TABLE IF EXISTS "09_featureflags"."40_lnk_role_feature_permissions";

-- Drop new dim tables
DROP TABLE IF EXISTS "09_featureflags"."04_dim_feature_permissions";
DROP TABLE IF EXISTS "09_featureflags"."03_dim_feature_flags";
DROP TABLE IF EXISTS "09_featureflags"."02_dim_feature_flag_categories";
DROP TABLE IF EXISTS "09_featureflags"."01_dim_permission_actions";

-- Restore dim_scopes in 03_iam (structure only — no seed data; pre-release)
CREATE TABLE "03_iam"."03_dim_scopes" (
    id              SMALLINT NOT NULL,
    code            TEXT NOT NULL,
    label           TEXT NOT NULL,
    scope_level     TEXT NOT NULL,
    description     TEXT,
    deprecated_at   TIMESTAMP,
    CONSTRAINT pk_iam_dim_scopes PRIMARY KEY (id),
    CONSTRAINT uq_iam_dim_scopes_code UNIQUE (code),
    CONSTRAINT chk_iam_dim_scopes_level CHECK (scope_level IN ('global','org'))
);
COMMENT ON TABLE  "03_iam"."03_dim_scopes" IS 'Restored empty by DOWN migration. Was the old permission scope catalog before 23R unified model.';
COMMENT ON COLUMN "03_iam"."03_dim_scopes".id IS 'Permanent manual ID.';
COMMENT ON COLUMN "03_iam"."03_dim_scopes".code IS 'Scope code.';
COMMENT ON COLUMN "03_iam"."03_dim_scopes".label IS 'Human-readable label.';
COMMENT ON COLUMN "03_iam"."03_dim_scopes".scope_level IS 'global or org.';
COMMENT ON COLUMN "03_iam"."03_dim_scopes".description IS 'Free-text description.';
COMMENT ON COLUMN "03_iam"."03_dim_scopes".deprecated_at IS 'Non-null when deprecated.';

-- Restore lnk_role_scopes in 03_iam (structure only)
CREATE TABLE "03_iam"."44_lnk_role_scopes" (
    id              VARCHAR(36) NOT NULL,
    role_id         VARCHAR(36) NOT NULL,
    scope_id        SMALLINT NOT NULL,
    created_by      VARCHAR(36) NOT NULL,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_iam_lnk_role_scopes PRIMARY KEY (id),
    CONSTRAINT fk_iam_lnk_role_scopes_role FOREIGN KEY (role_id)
        REFERENCES "03_iam"."13_fct_roles"(id),
    CONSTRAINT fk_iam_lnk_role_scopes_scope FOREIGN KEY (scope_id)
        REFERENCES "03_iam"."03_dim_scopes"(id),
    CONSTRAINT uq_iam_lnk_role_scope UNIQUE (role_id, scope_id)
);
CREATE INDEX idx_iam_lnk_role_scopes_role ON "03_iam"."44_lnk_role_scopes" (role_id);
COMMENT ON TABLE  "03_iam"."44_lnk_role_scopes" IS 'Restored empty by DOWN migration. Was role-scope assignment before 23R.';
COMMENT ON COLUMN "03_iam"."44_lnk_role_scopes".id IS 'UUID v7.';
COMMENT ON COLUMN "03_iam"."44_lnk_role_scopes".role_id IS 'FK to fct_roles.';
COMMENT ON COLUMN "03_iam"."44_lnk_role_scopes".scope_id IS 'FK to dim_scopes.';
COMMENT ON COLUMN "03_iam"."44_lnk_role_scopes".created_by IS 'UUID of creator.';
COMMENT ON COLUMN "03_iam"."44_lnk_role_scopes".created_at IS 'Insert timestamp.';

-- Restore lnk_application_scopes in 03_iam (structure only)
CREATE TABLE "03_iam"."45_lnk_application_scopes" (
    id              VARCHAR(36) NOT NULL,
    org_id          VARCHAR(36) NOT NULL,
    application_id  VARCHAR(36) NOT NULL,
    scope_id        SMALLINT NOT NULL,
    created_by      VARCHAR(36) NOT NULL,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_iam_lnk_application_scopes PRIMARY KEY (id),
    CONSTRAINT fk_iam_lnk_application_scopes_app FOREIGN KEY (application_id)
        REFERENCES "03_iam"."15_fct_applications"(id) ON DELETE CASCADE,
    CONSTRAINT fk_iam_lnk_application_scopes_scope FOREIGN KEY (scope_id)
        REFERENCES "03_iam"."03_dim_scopes"(id),
    CONSTRAINT fk_iam_lnk_application_scopes_org FOREIGN KEY (org_id)
        REFERENCES "03_iam"."10_fct_orgs"(id),
    CONSTRAINT uq_iam_lnk_application_scope UNIQUE (application_id, scope_id)
);
CREATE INDEX idx_iam_lnk_application_scopes_app
    ON "03_iam"."45_lnk_application_scopes" (application_id);
COMMENT ON TABLE  "03_iam"."45_lnk_application_scopes" IS 'Restored empty by DOWN migration. Was application-scope assignment before 23R.';
COMMENT ON COLUMN "03_iam"."45_lnk_application_scopes".id IS 'UUID v7.';
COMMENT ON COLUMN "03_iam"."45_lnk_application_scopes".org_id IS 'FK to fct_orgs.';
COMMENT ON COLUMN "03_iam"."45_lnk_application_scopes".application_id IS 'FK to fct_applications.';
COMMENT ON COLUMN "03_iam"."45_lnk_application_scopes".scope_id IS 'FK to dim_scopes.';
COMMENT ON COLUMN "03_iam"."45_lnk_application_scopes".created_by IS 'UUID of creator.';
COMMENT ON COLUMN "03_iam"."45_lnk_application_scopes".created_at IS 'Insert timestamp.';

-- Restore old flag-permission dim in 09_featureflags (structure only)
CREATE TABLE "09_featureflags"."04_dim_flag_permissions" (
    id              SMALLINT NOT NULL,
    code            TEXT NOT NULL,
    label           TEXT NOT NULL,
    rank            SMALLINT NOT NULL,
    description     TEXT,
    deprecated_at   TIMESTAMP,
    CONSTRAINT pk_ff_dim_flag_permissions PRIMARY KEY (id),
    CONSTRAINT uq_ff_dim_flag_permissions_code UNIQUE (code),
    CONSTRAINT chk_ff_dim_flag_permissions_rank CHECK (rank BETWEEN 1 AND 4)
);
COMMENT ON TABLE  "09_featureflags"."04_dim_flag_permissions" IS 'Restored empty by DOWN migration. Was the old per-flag permission level (view/toggle/write/admin) before 23R.';
COMMENT ON COLUMN "09_featureflags"."04_dim_flag_permissions".id IS 'Permanent manual id.';
COMMENT ON COLUMN "09_featureflags"."04_dim_flag_permissions".code IS 'Permission code.';
COMMENT ON COLUMN "09_featureflags"."04_dim_flag_permissions".label IS 'Human-readable label.';
COMMENT ON COLUMN "09_featureflags"."04_dim_flag_permissions".rank IS 'Hierarchy rank.';
COMMENT ON COLUMN "09_featureflags"."04_dim_flag_permissions".description IS 'What this permission grants.';
COMMENT ON COLUMN "09_featureflags"."04_dim_flag_permissions".deprecated_at IS 'Non-null when deprecated.';

-- Restore old lnk_role_flag_permissions (structure only)
CREATE TABLE "09_featureflags"."40_lnk_role_flag_permissions" (
    id              VARCHAR(36) NOT NULL,
    role_id         VARCHAR(36) NOT NULL,
    flag_id         VARCHAR(36) NOT NULL,
    permission_id   SMALLINT NOT NULL,
    created_by      VARCHAR(36) NOT NULL,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_ff_lnk_role_flag_permissions PRIMARY KEY (id),
    CONSTRAINT fk_ff_lnk_rfp_role FOREIGN KEY (role_id)
        REFERENCES "03_iam"."13_fct_roles"(id),
    CONSTRAINT fk_ff_lnk_rfp_flag FOREIGN KEY (flag_id)
        REFERENCES "09_featureflags"."10_fct_flags"(id),
    CONSTRAINT fk_ff_lnk_rfp_permission FOREIGN KEY (permission_id)
        REFERENCES "09_featureflags"."04_dim_flag_permissions"(id),
    CONSTRAINT uq_ff_lnk_rfp UNIQUE (role_id, flag_id, permission_id)
);
CREATE INDEX idx_ff_lnk_rfp_role ON "09_featureflags"."40_lnk_role_flag_permissions" (role_id);
CREATE INDEX idx_ff_lnk_rfp_flag ON "09_featureflags"."40_lnk_role_flag_permissions" (flag_id);
COMMENT ON TABLE  "09_featureflags"."40_lnk_role_flag_permissions" IS 'Restored empty by DOWN migration. Was per-flag role permission grants before 23R.';
COMMENT ON COLUMN "09_featureflags"."40_lnk_role_flag_permissions".id IS 'UUID v7.';
COMMENT ON COLUMN "09_featureflags"."40_lnk_role_flag_permissions".role_id IS 'FK to fct_roles.';
COMMENT ON COLUMN "09_featureflags"."40_lnk_role_flag_permissions".flag_id IS 'FK to fct_flags.';
COMMENT ON COLUMN "09_featureflags"."40_lnk_role_flag_permissions".permission_id IS 'FK to dim_flag_permissions.';
COMMENT ON COLUMN "09_featureflags"."40_lnk_role_flag_permissions".created_by IS 'UUID of creator.';
COMMENT ON COLUMN "09_featureflags"."40_lnk_role_flag_permissions".created_at IS 'Insert timestamp.';

-- Restore old view
CREATE VIEW "09_featureflags"."v_role_flag_permissions" AS
SELECT
    l.id,
    l.role_id,
    l.flag_id,
    fp.code AS permission,
    fp.rank AS permission_rank,
    l.created_by,
    l.created_at
FROM "09_featureflags"."40_lnk_role_flag_permissions" l
JOIN "09_featureflags"."04_dim_flag_permissions" fp ON fp.id = l.permission_id;
COMMENT ON VIEW "09_featureflags"."v_role_flag_permissions" IS 'Restored empty by DOWN migration. Old flat read shape for role-flag permission grants.';
