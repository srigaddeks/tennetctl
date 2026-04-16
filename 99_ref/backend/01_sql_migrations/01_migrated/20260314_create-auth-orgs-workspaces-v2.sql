
-- ─────────────────────────────────────────────────────────────────────────
-- PRODUCT CATALOG  (23 → 26)
-- Products are standalone catalog entities. Workspaces reference them.
-- They are NOT a level in the access hierarchy.
-- ─────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS "03_auth_manage"."23_dim_product_types" (
    id          UUID  NOT NULL,
    code        VARCHAR(30)  NOT NULL,
    name        VARCHAR(100) NOT NULL,
    description TEXT         NOT NULL,
    sort_order  INTEGER      NOT NULL,
    created_at  TIMESTAMP    NOT NULL,
    updated_at  TIMESTAMP    NOT NULL,
    CONSTRAINT pk_23_dim_product_types    PRIMARY KEY (id),
    CONSTRAINT uq_23_dim_product_types_code UNIQUE (code)
);

CREATE TABLE IF NOT EXISTS "03_auth_manage"."24_fct_products" (
    id                UUID  NOT NULL,
    tenant_key        VARCHAR(100) NOT NULL,
    product_type_code VARCHAR(30)  NOT NULL,
    code              VARCHAR(80)  NOT NULL,
    name              VARCHAR(120) NOT NULL,
    description       TEXT         NOT NULL,
    is_active         BOOLEAN      NOT NULL DEFAULT TRUE,
    is_disabled       BOOLEAN      NOT NULL DEFAULT FALSE,
    is_deleted        BOOLEAN      NOT NULL DEFAULT FALSE,
    is_test           BOOLEAN      NOT NULL DEFAULT FALSE,
    is_system         BOOLEAN      NOT NULL DEFAULT FALSE,
    is_locked         BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at        TIMESTAMP    NOT NULL,
    updated_at        TIMESTAMP    NOT NULL,
    created_by        UUID  NULL,
    updated_by        UUID  NULL,
    deleted_at        TIMESTAMP    NULL,
    deleted_by        UUID  NULL,
    CONSTRAINT pk_24_fct_products PRIMARY KEY (id),
    CONSTRAINT uq_24_fct_products_tenant_code UNIQUE (tenant_key, code),
    CONSTRAINT fk_24_fct_products_type_23_dim_product_types
        FOREIGN KEY (product_type_code)
        REFERENCES "03_auth_manage"."23_dim_product_types" (code)
        ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "03_auth_manage"."25_dtl_product_settings" (
    id            UUID  NOT NULL,
    product_id    UUID  NOT NULL,
    setting_key   VARCHAR(100) NOT NULL,
    setting_value TEXT         NOT NULL,
    created_at    TIMESTAMP    NOT NULL,
    updated_at    TIMESTAMP    NOT NULL,
    created_by    UUID  NULL,
    updated_by    UUID  NULL,
    CONSTRAINT pk_25_dtl_product_settings     PRIMARY KEY (id),
    CONSTRAINT uq_25_dtl_product_settings_key UNIQUE (product_id, setting_key),
    CONSTRAINT fk_25_dtl_product_settings_product_id_24_fct_products
        FOREIGN KEY (product_id)
        REFERENCES "03_auth_manage"."24_fct_products" (id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS "03_auth_manage"."26_lnk_product_memberships" (
    id                UUID NOT NULL,
    product_id        UUID NOT NULL,
    user_id           UUID NOT NULL,
    membership_type   VARCHAR(30) NOT NULL,
    membership_status VARCHAR(30) NOT NULL,
    effective_from    TIMESTAMP   NOT NULL,
    effective_to      TIMESTAMP   NULL,
    is_active         BOOLEAN     NOT NULL DEFAULT TRUE,
    is_disabled       BOOLEAN     NOT NULL DEFAULT FALSE,
    is_deleted        BOOLEAN     NOT NULL DEFAULT FALSE,
    is_test           BOOLEAN     NOT NULL DEFAULT FALSE,
    is_system         BOOLEAN     NOT NULL DEFAULT FALSE,
    is_locked         BOOLEAN     NOT NULL DEFAULT FALSE,
    created_at        TIMESTAMP   NOT NULL,
    updated_at        TIMESTAMP   NOT NULL,
    created_by        UUID NULL,
    updated_by        UUID NULL,
    deleted_at        TIMESTAMP   NULL,
    deleted_by        UUID NULL,
    CONSTRAINT pk_26_lnk_product_memberships          PRIMARY KEY (id),
    CONSTRAINT uq_26_lnk_product_memberships_pid_uid  UNIQUE (product_id, user_id),
    CONSTRAINT fk_26_lnk_product_memberships_product_id_24_fct_products
        FOREIGN KEY (product_id)
        REFERENCES "03_auth_manage"."24_fct_products" (id)
        ON DELETE RESTRICT,
    CONSTRAINT fk_26_lnk_product_memberships_user_id_03_fct_users
        FOREIGN KEY (user_id)
        REFERENCES "03_auth_manage"."03_fct_users" (id)
        ON DELETE RESTRICT,
    CONSTRAINT ck_26_lnk_product_memberships_type
        CHECK (membership_type IN ('owner', 'admin', 'member', 'viewer'))
);

-- ─────────────────────────────────────────────────────────────────────────
-- ORG TABLES  (28 → 31)
-- Orgs belong directly to a tenant. They are the first level below platform.
-- ─────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS "03_auth_manage"."28_dim_org_types" (
    id          UUID  NOT NULL,
    code        VARCHAR(30)  NOT NULL,
    name        VARCHAR(100) NOT NULL,
    description TEXT         NOT NULL,
    sort_order  INTEGER      NOT NULL,
    created_at  TIMESTAMP    NOT NULL,
    updated_at  TIMESTAMP    NOT NULL,
    CONSTRAINT pk_28_dim_org_types    PRIMARY KEY (id),
    CONSTRAINT uq_28_dim_org_types_code UNIQUE (code)
);

CREATE TABLE IF NOT EXISTS "03_auth_manage"."29_fct_orgs" (
    id            UUID  NOT NULL,
    tenant_key    VARCHAR(100) NOT NULL,
    org_type_code VARCHAR(30)  NOT NULL,
    code          VARCHAR(80)  NOT NULL,
    name          VARCHAR(120) NOT NULL,
    description   TEXT         NOT NULL,
    is_active     BOOLEAN      NOT NULL DEFAULT TRUE,
    is_disabled   BOOLEAN      NOT NULL DEFAULT FALSE,
    is_deleted    BOOLEAN      NOT NULL DEFAULT FALSE,
    is_test       BOOLEAN      NOT NULL DEFAULT FALSE,
    is_system     BOOLEAN      NOT NULL DEFAULT FALSE,
    is_locked     BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at    TIMESTAMP    NOT NULL,
    updated_at    TIMESTAMP    NOT NULL,
    created_by    UUID  NULL,
    updated_by    UUID  NULL,
    deleted_at    TIMESTAMP    NULL,
    deleted_by    UUID  NULL,
    CONSTRAINT pk_29_fct_orgs PRIMARY KEY (id),
    CONSTRAINT uq_29_fct_orgs_tenant_code UNIQUE (tenant_key, code),
    CONSTRAINT fk_29_fct_orgs_org_type_code_28_dim_org_types
        FOREIGN KEY (org_type_code)
        REFERENCES "03_auth_manage"."28_dim_org_types" (code)
        ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "03_auth_manage"."30_dtl_org_settings" (
    id            UUID  NOT NULL,
    org_id        UUID  NOT NULL,
    setting_key   VARCHAR(100) NOT NULL,
    setting_value TEXT         NOT NULL,
    created_at    TIMESTAMP    NOT NULL,
    updated_at    TIMESTAMP    NOT NULL,
    created_by    UUID  NULL,
    updated_by    UUID  NULL,
    CONSTRAINT pk_30_dtl_org_settings     PRIMARY KEY (id),
    CONSTRAINT uq_30_dtl_org_settings_key UNIQUE (org_id, setting_key),
    CONSTRAINT fk_30_dtl_org_settings_org_id_29_fct_orgs
        FOREIGN KEY (org_id)
        REFERENCES "03_auth_manage"."29_fct_orgs" (id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS "03_auth_manage"."31_lnk_org_memberships" (
    id                UUID NOT NULL,
    org_id            UUID NOT NULL,
    user_id           UUID NOT NULL,
    membership_type   VARCHAR(30) NOT NULL,
    membership_status VARCHAR(30) NOT NULL,
    effective_from    TIMESTAMP   NOT NULL,
    effective_to      TIMESTAMP   NULL,
    is_active         BOOLEAN     NOT NULL DEFAULT TRUE,
    is_disabled       BOOLEAN     NOT NULL DEFAULT FALSE,
    is_deleted        BOOLEAN     NOT NULL DEFAULT FALSE,
    is_test           BOOLEAN     NOT NULL DEFAULT FALSE,
    is_system         BOOLEAN     NOT NULL DEFAULT FALSE,
    is_locked         BOOLEAN     NOT NULL DEFAULT FALSE,
    created_at        TIMESTAMP   NOT NULL,
    updated_at        TIMESTAMP   NOT NULL,
    created_by        UUID NULL,
    updated_by        UUID NULL,
    deleted_at        TIMESTAMP   NULL,
    deleted_by        UUID NULL,
    CONSTRAINT pk_31_lnk_org_memberships          PRIMARY KEY (id),
    CONSTRAINT uq_31_lnk_org_memberships_org_user UNIQUE (org_id, user_id),
    CONSTRAINT fk_31_lnk_org_memberships_org_id_29_fct_orgs
        FOREIGN KEY (org_id)
        REFERENCES "03_auth_manage"."29_fct_orgs" (id)
        ON DELETE RESTRICT,
    CONSTRAINT fk_31_lnk_org_memberships_user_id_03_fct_users
        FOREIGN KEY (user_id)
        REFERENCES "03_auth_manage"."03_fct_users" (id)
        ON DELETE RESTRICT,
    CONSTRAINT ck_31_lnk_org_memberships_type
        CHECK (membership_type IN ('owner', 'admin', 'member', 'viewer', 'billing'))
);

-- ─────────────────────────────────────────────────────────────────────────
-- WORKSPACE TABLES  (33 → 36)
-- Workspaces belong to an org. They can optionally reference a product,
-- allowing the same product to appear in multiple workspace contexts
-- (e.g. K-Control project workspace, K-Control Sandbox dev workspace).
-- ─────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS "03_auth_manage"."33_dim_workspace_types" (
    id                     UUID  NOT NULL,
    code                   VARCHAR(30)  NOT NULL,
    name                   VARCHAR(100) NOT NULL,
    description            TEXT         NOT NULL,
    sort_order             INTEGER      NOT NULL,
    is_infrastructure_type BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at             TIMESTAMP    NOT NULL,
    updated_at             TIMESTAMP    NOT NULL,
    CONSTRAINT pk_33_dim_workspace_types    PRIMARY KEY (id),
    CONSTRAINT uq_33_dim_workspace_types_code UNIQUE (code)
);

CREATE TABLE IF NOT EXISTS "03_auth_manage"."34_fct_workspaces" (
    id                  UUID  NOT NULL,
    org_id              UUID  NOT NULL,
    workspace_type_code VARCHAR(30)  NOT NULL,
    product_id          UUID  NULL,
    code                VARCHAR(80)  NOT NULL,
    name                VARCHAR(120) NOT NULL,
    description         TEXT         NOT NULL,
    is_active           BOOLEAN      NOT NULL DEFAULT TRUE,
    is_disabled         BOOLEAN      NOT NULL DEFAULT FALSE,
    is_deleted          BOOLEAN      NOT NULL DEFAULT FALSE,
    is_test             BOOLEAN      NOT NULL DEFAULT FALSE,
    is_system           BOOLEAN      NOT NULL DEFAULT FALSE,
    is_locked           BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at          TIMESTAMP    NOT NULL,
    updated_at          TIMESTAMP    NOT NULL,
    created_by          UUID  NULL,
    updated_by          UUID  NULL,
    deleted_at          TIMESTAMP    NULL,
    deleted_by          UUID  NULL,
    CONSTRAINT pk_34_fct_workspaces PRIMARY KEY (id),
    CONSTRAINT uq_34_fct_workspaces_org_code UNIQUE (org_id, code),
    CONSTRAINT fk_34_fct_workspaces_org_id_29_fct_orgs
        FOREIGN KEY (org_id)
        REFERENCES "03_auth_manage"."29_fct_orgs" (id)
        ON DELETE RESTRICT,
    CONSTRAINT fk_34_fct_workspaces_workspace_type_code_33_dim_workspace_types
        FOREIGN KEY (workspace_type_code)
        REFERENCES "03_auth_manage"."33_dim_workspace_types" (code)
        ON DELETE RESTRICT,
    CONSTRAINT fk_34_fct_workspaces_product_id_24_fct_products
        FOREIGN KEY (product_id)
        REFERENCES "03_auth_manage"."24_fct_products" (id)
        ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS "03_auth_manage"."35_dtl_workspace_settings" (
    id            UUID  NOT NULL,
    workspace_id  UUID  NOT NULL,
    setting_key   VARCHAR(100) NOT NULL,
    setting_value TEXT         NOT NULL,
    created_at    TIMESTAMP    NOT NULL,
    updated_at    TIMESTAMP    NOT NULL,
    created_by    UUID  NULL,
    updated_by    UUID  NULL,
    CONSTRAINT pk_35_dtl_workspace_settings     PRIMARY KEY (id),
    CONSTRAINT uq_35_dtl_workspace_settings_key UNIQUE (workspace_id, setting_key),
    CONSTRAINT fk_35_dtl_workspace_settings_workspace_id_34_fct_workspaces
        FOREIGN KEY (workspace_id)
        REFERENCES "03_auth_manage"."34_fct_workspaces" (id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS "03_auth_manage"."36_lnk_workspace_memberships" (
    id                UUID NOT NULL,
    workspace_id      UUID NOT NULL,
    user_id           UUID NOT NULL,
    membership_type   VARCHAR(30) NOT NULL,
    membership_status VARCHAR(30) NOT NULL,
    effective_from    TIMESTAMP   NOT NULL,
    effective_to      TIMESTAMP   NULL,
    is_active         BOOLEAN     NOT NULL DEFAULT TRUE,
    is_disabled       BOOLEAN     NOT NULL DEFAULT FALSE,
    is_deleted        BOOLEAN     NOT NULL DEFAULT FALSE,
    is_test           BOOLEAN     NOT NULL DEFAULT FALSE,
    is_system         BOOLEAN     NOT NULL DEFAULT FALSE,
    is_locked         BOOLEAN     NOT NULL DEFAULT FALSE,
    created_at        TIMESTAMP   NOT NULL,
    updated_at        TIMESTAMP   NOT NULL,
    created_by        UUID NULL,
    updated_by        UUID NULL,
    deleted_at        TIMESTAMP   NULL,
    deleted_by        UUID NULL,
    CONSTRAINT pk_36_lnk_workspace_memberships             PRIMARY KEY (id),
    CONSTRAINT uq_36_lnk_workspace_memberships_ws_user     UNIQUE (workspace_id, user_id),
    CONSTRAINT fk_36_lnk_workspace_memberships_workspace_id_34_fct_workspaces
        FOREIGN KEY (workspace_id)
        REFERENCES "03_auth_manage"."34_fct_workspaces" (id)
        ON DELETE RESTRICT,
    CONSTRAINT fk_36_lnk_workspace_memberships_user_id_03_fct_users
        FOREIGN KEY (user_id)
        REFERENCES "03_auth_manage"."03_fct_users" (id)
        ON DELETE RESTRICT,
    CONSTRAINT ck_36_lnk_workspace_memberships_type
        CHECK (membership_type IN ('owner', 'admin', 'contributor', 'viewer', 'readonly'))
);

-- ─────────────────────────────────────────────────────────────────────────
-- ALTER EXISTING TABLES
-- ─────────────────────────────────────────────────────────────────────────

-- Add feature_scope to feature flags (platform | org | workspace | product)
ALTER TABLE "03_auth_manage"."14_dim_feature_flags"
    ADD COLUMN IF NOT EXISTS feature_scope VARCHAR(30) NOT NULL DEFAULT 'platform';

-- Add product_id FK so flags can be tied to a specific product
ALTER TABLE "03_auth_manage"."14_dim_feature_flags"
    ADD COLUMN IF NOT EXISTS product_id UUID NULL;

DO $$ BEGIN
    ALTER TABLE "03_auth_manage"."14_dim_feature_flags"
        ADD CONSTRAINT ck_14_dim_feature_flags_feature_scope
        CHECK (feature_scope IN ('platform', 'org', 'workspace', 'product'));
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    ALTER TABLE "03_auth_manage"."14_dim_feature_flags"
        ADD CONSTRAINT fk_14_dim_feature_flags_product_id_24_fct_products
        FOREIGN KEY (product_id)
        REFERENCES "03_auth_manage"."24_fct_products" (id) ON DELETE SET NULL;
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- Add FK constraints on role/group scope columns now that org/workspace tables exist
DO $$ BEGIN
    ALTER TABLE "03_auth_manage"."16_fct_roles"
        ADD CONSTRAINT fk_16_fct_roles_scope_org_id_29_fct_orgs
        FOREIGN KEY (scope_org_id)
        REFERENCES "03_auth_manage"."29_fct_orgs" (id) ON DELETE RESTRICT;
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    ALTER TABLE "03_auth_manage"."16_fct_roles"
        ADD CONSTRAINT fk_16_fct_roles_scope_workspace_id_34_fct_workspaces
        FOREIGN KEY (scope_workspace_id)
        REFERENCES "03_auth_manage"."34_fct_workspaces" (id) ON DELETE RESTRICT;
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    ALTER TABLE "03_auth_manage"."17_fct_user_groups"
        ADD CONSTRAINT fk_17_fct_user_groups_scope_org_id_29_fct_orgs
        FOREIGN KEY (scope_org_id)
        REFERENCES "03_auth_manage"."29_fct_orgs" (id) ON DELETE RESTRICT;
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    ALTER TABLE "03_auth_manage"."17_fct_user_groups"
        ADD CONSTRAINT fk_17_fct_user_groups_scope_workspace_id_34_fct_workspaces
        FOREIGN KEY (scope_workspace_id)
        REFERENCES "03_auth_manage"."34_fct_workspaces" (id) ON DELETE RESTRICT;
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- ─────────────────────────────────────────────────────────────────────────
-- SEED: product types
-- ─────────────────────────────────────────────────────────────────────────

INSERT INTO "03_auth_manage"."23_dim_product_types" (id, code, name, description, sort_order, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000001101', 'saas_platform', 'SaaS Platform', 'Full SaaS product instance.', 10, TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."23_dim_product_types" WHERE code = 'saas_platform');

INSERT INTO "03_auth_manage"."23_dim_product_types" (id, code, name, description, sort_order, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000001102', 'sandbox', 'Sandbox', 'Sandboxed testing or preview instance.', 20, TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."23_dim_product_types" WHERE code = 'sandbox');

INSERT INTO "03_auth_manage"."23_dim_product_types" (id, code, name, description, sort_order, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000001103', 'developer_tool', 'Developer Tool', 'Developer tooling product.', 30, TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."23_dim_product_types" WHERE code = 'developer_tool');

INSERT INTO "03_auth_manage"."23_dim_product_types" (id, code, name, description, sort_order, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000001104', 'data_platform', 'Data Platform', 'Data and analytics product.', 40, TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."23_dim_product_types" WHERE code = 'data_platform');

-- ─────────────────────────────────────────────────────────────────────────
-- SEED: default products (K-Control + K-Control Sandbox)
-- ─────────────────────────────────────────────────────────────────────────

INSERT INTO "03_auth_manage"."24_fct_products" (
    id, tenant_key, product_type_code, code, name, description,
    is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
    created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
)
SELECT '00000000-0000-0000-0000-000000001201', 'default', 'saas_platform', 'kcontrol', 'K-Control',
       'Primary K-Control SaaS platform.',
       TRUE, FALSE, FALSE, FALSE, TRUE, FALSE,
       TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00', NULL, NULL, NULL, NULL
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."24_fct_products" WHERE code = 'kcontrol' AND tenant_key = 'default');

INSERT INTO "03_auth_manage"."24_fct_products" (
    id, tenant_key, product_type_code, code, name, description,
    is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
    created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
)
SELECT '00000000-0000-0000-0000-000000001202', 'default', 'sandbox', 'kcontrol_sandbox', 'K-Control Sandbox',
       'Sandboxed testing instance of K-Control.',
       TRUE, FALSE, FALSE, TRUE, TRUE, FALSE,
       TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00', NULL, NULL, NULL, NULL
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."24_fct_products" WHERE code = 'kcontrol_sandbox' AND tenant_key = 'default');

-- ─────────────────────────────────────────────────────────────────────────
-- SEED: org types
-- ─────────────────────────────────────────────────────────────────────────

INSERT INTO "03_auth_manage"."28_dim_org_types" (id, code, name, description, sort_order, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000001301',   'company',   'Company',   'Commercial company or enterprise.',    10, TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."28_dim_org_types" WHERE code = 'company');

INSERT INTO "03_auth_manage"."28_dim_org_types" (id, code, name, description, sort_order, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000001302', 'community', 'Community', 'Open community or non-profit.',        20, TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."28_dim_org_types" WHERE code = 'community');

INSERT INTO "03_auth_manage"."28_dim_org_types" (id, code, name, description, sort_order, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000001303',  'personal',  'Personal',  'Personal org for solo users.',         30, TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."28_dim_org_types" WHERE code = 'personal');

INSERT INTO "03_auth_manage"."28_dim_org_types" (id, code, name, description, sort_order, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000001304',   'partner',   'Partner',   'Partner or reseller organization.',    40, TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."28_dim_org_types" WHERE code = 'partner');

INSERT INTO "03_auth_manage"."28_dim_org_types" (id, code, name, description, sort_order, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000001305',  'internal',  'Internal',  'Internal team or department.',         50, TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."28_dim_org_types" WHERE code = 'internal');

-- ─────────────────────────────────────────────────────────────────────────
-- SEED: workspace types
-- ─────────────────────────────────────────────────────────────────────────

INSERT INTO "03_auth_manage"."33_dim_workspace_types" (id, code, name, description, sort_order, is_infrastructure_type, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000001401',  'project',             'Project',              'A software project or product initiative.',    10, FALSE, TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."33_dim_workspace_types" WHERE code = 'project');

INSERT INTO "03_auth_manage"."33_dim_workspace_types" (id, code, name, description, sort_order, is_infrastructure_type, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000001402',     'team',                'Team',                 'A team collaboration workspace.',              20, FALSE, TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."33_dim_workspace_types" WHERE code = 'team');

INSERT INTO "03_auth_manage"."33_dim_workspace_types" (id, code, name, description, sort_order, is_infrastructure_type, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000001403',  'environment_dev',     'Dev Environment',      'Development deployment environment.',          30, TRUE,  TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."33_dim_workspace_types" WHERE code = 'environment_dev');

INSERT INTO "03_auth_manage"."33_dim_workspace_types" (id, code, name, description, sort_order, is_infrastructure_type, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000001404',  'environment_staging', 'Staging Environment',  'Pre-production staging environment.',          40, TRUE,  TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."33_dim_workspace_types" WHERE code = 'environment_staging');

INSERT INTO "03_auth_manage"."33_dim_workspace_types" (id, code, name, description, sort_order, is_infrastructure_type, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000001405', 'environment_prod',    'Prod Environment',     'Production deployment environment.',           50, TRUE,  TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."33_dim_workspace_types" WHERE code = 'environment_prod');

INSERT INTO "03_auth_manage"."33_dim_workspace_types" (id, code, name, description, sort_order, is_infrastructure_type, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000001406',  'sandbox',             'Sandbox',              'Sandbox or experimental workspace.',           60, FALSE, TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."33_dim_workspace_types" WHERE code = 'sandbox');

INSERT INTO "03_auth_manage"."33_dim_workspace_types" (id, code, name, description, sort_order, is_infrastructure_type, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000001407',   'shared',              'Shared Resources',     'Shared cross-team resources workspace.',       70, FALSE, TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."33_dim_workspace_types" WHERE code = 'shared');

-- ─────────────────────────────────────────────────────────────────────────
-- SEED: new feature categories
-- ─────────────────────────────────────────────────────────────────────────

INSERT INTO "03_auth_manage"."11_dim_feature_flag_categories" (id, code, name, description, sort_order, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000001501',   'product',   'Product',   'Product catalog administration.',     50, TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."11_dim_feature_flag_categories" WHERE code = 'product');

INSERT INTO "03_auth_manage"."11_dim_feature_flag_categories" (id, code, name, description, sort_order, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000001502',       'org',       'Organization', 'Org management capabilities.',    60, TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."11_dim_feature_flag_categories" WHERE code = 'org');

INSERT INTO "03_auth_manage"."11_dim_feature_flag_categories" (id, code, name, description, sort_order, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000001503', 'workspace', 'Workspace',  'Workspace management capabilities.', 70, TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."11_dim_feature_flag_categories" WHERE code = 'workspace');

-- ─────────────────────────────────────────────────────────────────────────
-- UPDATE: set feature_scope on existing seeded flags
-- ─────────────────────────────────────────────────────────────────────────

UPDATE "03_auth_manage"."14_dim_feature_flags"
SET feature_scope = 'platform'
WHERE code IN ('auth_password_login', 'auth_google_login',
               'access_governance_console', 'feature_flag_registry',
               'group_access_assignment', 'access_audit_timeline');

UPDATE "03_auth_manage"."14_dim_feature_flags"
SET feature_scope = 'org'
WHERE code = 'policy_management';

-- ─────────────────────────────────────────────────────────────────────────
-- SEED: new feature flags
--   product_management → platform scope (platform admins manage the product catalog)
--   org_management     → platform scope (platform admins create/remove orgs)
--   workspace_management → org scope  (org admins manage workspaces within their org)
-- ─────────────────────────────────────────────────────────────────────────

INSERT INTO "03_auth_manage"."14_dim_feature_flags" (
    id, code, name, description, feature_flag_category_code, feature_scope,
    access_mode, lifecycle_state, initial_audience,
    env_dev, env_staging, env_prod, created_at, updated_at
)
SELECT '00000000-0000-0000-0000-000000001601', 'product_management', 'Product Management',
       'Product catalog and environment controls.', 'product', 'platform',
       'permissioned', 'active', 'platform_super_admin',
       TRUE, FALSE, FALSE, TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."14_dim_feature_flags" WHERE code = 'product_management');

INSERT INTO "03_auth_manage"."14_dim_feature_flags" (
    id, code, name, description, feature_flag_category_code, feature_scope,
    access_mode, lifecycle_state, initial_audience,
    env_dev, env_staging, env_prod, created_at, updated_at
)
SELECT '00000000-0000-0000-0000-000000001602', 'org_management', 'Org Management',
       'Organization creation and membership administration.', 'org', 'platform',
       'permissioned', 'active', 'platform_super_admin',
       TRUE, FALSE, FALSE, TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."14_dim_feature_flags" WHERE code = 'org_management');

INSERT INTO "03_auth_manage"."14_dim_feature_flags" (
    id, code, name, description, feature_flag_category_code, feature_scope,
    access_mode, lifecycle_state, initial_audience,
    env_dev, env_staging, env_prod, created_at, updated_at
)
SELECT '00000000-0000-0000-0000-000000001603', 'workspace_management', 'Workspace Management',
       'Workspace creation and membership administration.', 'workspace', 'org',
       'permissioned', 'active', 'platform_super_admin',
       TRUE, FALSE, FALSE, TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."14_dim_feature_flags" WHERE code = 'workspace_management');

-- ─────────────────────────────────────────────────────────────────────────
-- SEED: feature permissions for new flags
-- ─────────────────────────────────────────────────────────────────────────

INSERT INTO "03_auth_manage"."15_dim_feature_permissions" (id, code, feature_flag_code, permission_action_code, name, description, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000001701',   'product_management.view',   'product_management', 'view',   'View Products',          'View product catalog.',            TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'product_management.view');

INSERT INTO "03_auth_manage"."15_dim_feature_permissions" (id, code, feature_flag_code, permission_action_code, name, description, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000001702', 'product_management.create', 'product_management', 'create', 'Create Products',        'Create new product instances.',    TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'product_management.create');

INSERT INTO "03_auth_manage"."15_dim_feature_permissions" (id, code, feature_flag_code, permission_action_code, name, description, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000001703', 'product_management.update', 'product_management', 'update', 'Update Products',        'Update product metadata.',         TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'product_management.update');

INSERT INTO "03_auth_manage"."15_dim_feature_permissions" (id, code, feature_flag_code, permission_action_code, name, description, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000001704', 'product_management.assign', 'product_management', 'assign', 'Assign Product Members', 'Add users to a product.',          TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'product_management.assign');

INSERT INTO "03_auth_manage"."15_dim_feature_permissions" (id, code, feature_flag_code, permission_action_code, name, description, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000001705', 'product_management.revoke', 'product_management', 'revoke', 'Revoke Product Members', 'Remove users from a product.',     TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'product_management.revoke');

INSERT INTO "03_auth_manage"."15_dim_feature_permissions" (id, code, feature_flag_code, permission_action_code, name, description, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000001711',   'org_management.view',   'org_management', 'view',   'View Orgs',          'View organization list.',          TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'org_management.view');

INSERT INTO "03_auth_manage"."15_dim_feature_permissions" (id, code, feature_flag_code, permission_action_code, name, description, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000001712', 'org_management.create', 'org_management', 'create', 'Create Orgs',        'Create new organizations.',        TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'org_management.create');

INSERT INTO "03_auth_manage"."15_dim_feature_permissions" (id, code, feature_flag_code, permission_action_code, name, description, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000001713', 'org_management.update', 'org_management', 'update', 'Update Orgs',        'Update org details.',              TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'org_management.update');

INSERT INTO "03_auth_manage"."15_dim_feature_permissions" (id, code, feature_flag_code, permission_action_code, name, description, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000001714', 'org_management.assign', 'org_management', 'assign', 'Assign Org Members', 'Add users to an organization.',    TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'org_management.assign');

INSERT INTO "03_auth_manage"."15_dim_feature_permissions" (id, code, feature_flag_code, permission_action_code, name, description, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000001715', 'org_management.revoke', 'org_management', 'revoke', 'Revoke Org Members', 'Remove users from an organization.', TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'org_management.revoke');

INSERT INTO "03_auth_manage"."15_dim_feature_permissions" (id, code, feature_flag_code, permission_action_code, name, description, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000001721',   'workspace_management.view',   'workspace_management', 'view',   'View Workspaces',          'View workspace list.',              TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'workspace_management.view');

INSERT INTO "03_auth_manage"."15_dim_feature_permissions" (id, code, feature_flag_code, permission_action_code, name, description, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000001722', 'workspace_management.create', 'workspace_management', 'create', 'Create Workspaces',        'Create new workspaces.',            TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'workspace_management.create');

INSERT INTO "03_auth_manage"."15_dim_feature_permissions" (id, code, feature_flag_code, permission_action_code, name, description, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000001723', 'workspace_management.update', 'workspace_management', 'update', 'Update Workspaces',        'Update workspace details.',         TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'workspace_management.update');

INSERT INTO "03_auth_manage"."15_dim_feature_permissions" (id, code, feature_flag_code, permission_action_code, name, description, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000001724', 'workspace_management.assign', 'workspace_management', 'assign', 'Assign Workspace Members', 'Add users to a workspace.',         TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'workspace_management.assign');

INSERT INTO "03_auth_manage"."15_dim_feature_permissions" (id, code, feature_flag_code, permission_action_code, name, description, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000001725', 'workspace_management.revoke', 'workspace_management', 'revoke', 'Revoke Workspace Members', 'Remove users from a workspace.',    TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'workspace_management.revoke');

-- ─────────────────────────────────────────────────────────────────────────
-- SEED: assign all new permissions to platform_super_admin role
-- ─────────────────────────────────────────────────────────────────────────

INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions" (
    id, role_id, feature_permission_id,
    is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
    created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
)
SELECT fp.id, '00000000-0000-0000-0000-000000000601', fp.id,
       TRUE, FALSE, FALSE, FALSE, TRUE, FALSE,
       TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00', NULL, NULL, NULL, NULL
FROM "03_auth_manage"."15_dim_feature_permissions" fp
WHERE fp.code IN (
    'product_management.view', 'product_management.create', 'product_management.update',
    'product_management.assign', 'product_management.revoke',
    'org_management.view', 'org_management.create', 'org_management.update',
    'org_management.assign', 'org_management.revoke',
    'workspace_management.view', 'workspace_management.create', 'workspace_management.update',
    'workspace_management.assign', 'workspace_management.revoke'
)
AND NOT EXISTS (
    SELECT 1 FROM "03_auth_manage"."20_lnk_role_feature_permissions" rfp2
    WHERE rfp2.role_id = '00000000-0000-0000-0000-000000000601' AND rfp2.feature_permission_id = fp.id
);

-- ─────────────────────────────────────────────────────────────────────────
-- SEED: product-scoped feature flags (tied to specific products)
-- feature_scope='product' means the flag only activates for workspaces
-- linked to the referenced product.
-- ─────────────────────────────────────────────────────────────────────────

-- K-Control specific: data pipeline management
INSERT INTO "03_auth_manage"."14_dim_feature_flags" (
    id, code, name, description, feature_flag_category_code, feature_scope,
    access_mode, lifecycle_state, initial_audience,
    env_dev, env_staging, env_prod, product_id, created_at, updated_at
)
SELECT '00000000-0000-0000-0000-000000001801', 'kc_data_pipeline', 'Data Pipeline Management',
       'Controls access to data pipeline creation and execution within K-Control workspaces.',
       'admin', 'product', 'permissioned', 'active', 'workspace_admin',
       TRUE, FALSE, FALSE, '00000000-0000-0000-0000-000000001201',
       TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."14_dim_feature_flags" WHERE code = 'kc_data_pipeline');

-- K-Control specific: report builder
INSERT INTO "03_auth_manage"."14_dim_feature_flags" (
    id, code, name, description, feature_flag_category_code, feature_scope,
    access_mode, lifecycle_state, initial_audience,
    env_dev, env_staging, env_prod, product_id, created_at, updated_at
)
SELECT '00000000-0000-0000-0000-000000001802', 'kc_report_builder', 'Report Builder',
       'Controls access to the visual report builder within K-Control workspaces.',
       'admin', 'product', 'permissioned', 'active', 'workspace_admin',
       TRUE, FALSE, FALSE, '00000000-0000-0000-0000-000000001201',
       TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."14_dim_feature_flags" WHERE code = 'kc_report_builder');

-- K-Control Sandbox specific: sandbox reset
INSERT INTO "03_auth_manage"."14_dim_feature_flags" (
    id, code, name, description, feature_flag_category_code, feature_scope,
    access_mode, lifecycle_state, initial_audience,
    env_dev, env_staging, env_prod, product_id, created_at, updated_at
)
SELECT '00000000-0000-0000-0000-000000001803', 'kcsb_sandbox_reset', 'Sandbox Reset',
       'Allows resetting workspace data to the sandbox baseline state.',
       'admin', 'product', 'permissioned', 'active', 'workspace_admin',
       TRUE, FALSE, FALSE, '00000000-0000-0000-0000-000000001202',
       TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."14_dim_feature_flags" WHERE code = 'kcsb_sandbox_reset');

-- ─────────────────────────────────────────────────────────────────────────
-- SEED: permissions for product-scoped feature flags
-- ─────────────────────────────────────────────────────────────────────────

INSERT INTO "03_auth_manage"."15_dim_feature_permissions" (id, code, feature_flag_code, permission_action_code, name, description, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000001811',   'kc_data_pipeline.view',   'kc_data_pipeline', 'view',   'View Pipelines',   'View data pipeline list.',         TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'kc_data_pipeline.view');

INSERT INTO "03_auth_manage"."15_dim_feature_permissions" (id, code, feature_flag_code, permission_action_code, name, description, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000001812', 'kc_data_pipeline.create', 'kc_data_pipeline', 'create', 'Create Pipelines', 'Create new data pipelines.',       TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'kc_data_pipeline.create');

INSERT INTO "03_auth_manage"."15_dim_feature_permissions" (id, code, feature_flag_code, permission_action_code, name, description, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000001813', 'kc_data_pipeline.update', 'kc_data_pipeline', 'update', 'Update Pipelines', 'Update pipeline configuration.',   TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'kc_data_pipeline.update');

INSERT INTO "03_auth_manage"."15_dim_feature_permissions" (id, code, feature_flag_code, permission_action_code, name, description, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000001814',  'kc_data_pipeline.enable',  'kc_data_pipeline', 'enable',  'Enable Pipelines',  'Enable a data pipeline.',          TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'kc_data_pipeline.enable');

INSERT INTO "03_auth_manage"."15_dim_feature_permissions" (id, code, feature_flag_code, permission_action_code, name, description, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000001815', 'kc_data_pipeline.disable', 'kc_data_pipeline', 'disable', 'Disable Pipelines', 'Disable a data pipeline.',         TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'kc_data_pipeline.disable');

INSERT INTO "03_auth_manage"."15_dim_feature_permissions" (id, code, feature_flag_code, permission_action_code, name, description, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000001816',   'kc_report_builder.view',   'kc_report_builder', 'view',   'View Reports',   'View saved reports.',              TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'kc_report_builder.view');

INSERT INTO "03_auth_manage"."15_dim_feature_permissions" (id, code, feature_flag_code, permission_action_code, name, description, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000001817', 'kc_report_builder.create', 'kc_report_builder', 'create', 'Create Reports', 'Create new reports.',              TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'kc_report_builder.create');

INSERT INTO "03_auth_manage"."15_dim_feature_permissions" (id, code, feature_flag_code, permission_action_code, name, description, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000001818', 'kc_report_builder.update', 'kc_report_builder', 'update', 'Update Reports', 'Edit report configuration.',       TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'kc_report_builder.update');

INSERT INTO "03_auth_manage"."15_dim_feature_permissions" (id, code, feature_flag_code, permission_action_code, name, description, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000001819',  'kcsb_sandbox_reset.enable',  'kcsb_sandbox_reset', 'enable',  'Enable Sandbox Reset',  'Enable sandbox reset capability.', TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'kcsb_sandbox_reset.enable');

INSERT INTO "03_auth_manage"."15_dim_feature_permissions" (id, code, feature_flag_code, permission_action_code, name, description, created_at, updated_at)
SELECT '00000000-0000-0000-0000-00000000181a', 'kcsb_sandbox_reset.disable', 'kcsb_sandbox_reset', 'disable', 'Disable Sandbox Reset', 'Disable sandbox reset capability.', TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'kcsb_sandbox_reset.disable');

-- Assign all product-scoped flag permissions to platform_super_admin
INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions" (
    id, role_id, feature_permission_id,
    is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
    created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
)
SELECT fp.id, '00000000-0000-0000-0000-000000000601', fp.id,
       TRUE, FALSE, FALSE, FALSE, TRUE, FALSE,
       TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00', NULL, NULL, NULL, NULL
FROM "03_auth_manage"."15_dim_feature_permissions" fp
WHERE fp.code IN (
    'kc_data_pipeline.view', 'kc_data_pipeline.create', 'kc_data_pipeline.update',
    'kc_data_pipeline.enable', 'kc_data_pipeline.disable',
    'kc_report_builder.view', 'kc_report_builder.create', 'kc_report_builder.update',
    'kcsb_sandbox_reset.enable', 'kcsb_sandbox_reset.disable'
)
AND NOT EXISTS (
    SELECT 1 FROM "03_auth_manage"."20_lnk_role_feature_permissions" rfp2
    WHERE rfp2.role_id = '00000000-0000-0000-0000-000000000601' AND rfp2.feature_permission_id = fp.id
);
