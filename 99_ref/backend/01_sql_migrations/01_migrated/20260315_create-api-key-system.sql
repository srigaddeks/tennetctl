-- ─────────────────────────────────────────────────────────────────────────
-- API Key Management System
-- Tables: 45_dim_api_key_statuses, 46_fct_api_keys
-- Seeds: feature flag, permissions, role-permission links
-- ─────────────────────────────────────────────────────────────────────────

-- ═══════════════════════════════════════════════════════════════════════
-- 1. DIMENSION TABLE: API KEY STATUSES
-- ═══════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS "03_auth_manage"."45_dim_api_key_statuses" (
    id          UUID         NOT NULL DEFAULT gen_random_uuid(),
    code        VARCHAR(50)  NOT NULL,
    name        VARCHAR(100) NOT NULL,
    description TEXT         NOT NULL DEFAULT '',
    sort_order  INTEGER      NOT NULL DEFAULT 0,
    created_at  TIMESTAMP    NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMP    NOT NULL DEFAULT NOW(),
    CONSTRAINT pk_45_dim_api_key_statuses      PRIMARY KEY (id),
    CONSTRAINT uq_45_dim_api_key_statuses_code UNIQUE (code)
);

INSERT INTO "03_auth_manage"."45_dim_api_key_statuses" (id, code, name, description, sort_order, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000004501', 'active', 'Active', 'API key is active and can authenticate requests.', 1,
       TIMESTAMP '2026-03-15 00:00:00', TIMESTAMP '2026-03-15 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."45_dim_api_key_statuses" WHERE code = 'active');

INSERT INTO "03_auth_manage"."45_dim_api_key_statuses" (id, code, name, description, sort_order, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000004502', 'revoked', 'Revoked', 'API key has been manually revoked.', 2,
       TIMESTAMP '2026-03-15 00:00:00', TIMESTAMP '2026-03-15 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."45_dim_api_key_statuses" WHERE code = 'revoked');

INSERT INTO "03_auth_manage"."45_dim_api_key_statuses" (id, code, name, description, sort_order, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000004503', 'expired', 'Expired', 'API key has passed its expiration date.', 3,
       TIMESTAMP '2026-03-15 00:00:00', TIMESTAMP '2026-03-15 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."45_dim_api_key_statuses" WHERE code = 'expired');

-- ═══════════════════════════════════════════════════════════════════════
-- 2. FACT TABLE: API KEYS
-- ═══════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS "03_auth_manage"."46_fct_api_keys" (
    id              UUID          NOT NULL DEFAULT gen_random_uuid(),
    user_id         UUID          NOT NULL,
    tenant_key      VARCHAR(100)  NOT NULL,
    name            VARCHAR(255)  NOT NULL,
    key_prefix      VARCHAR(16)   NOT NULL,
    key_hash        VARCHAR(128)  NOT NULL,
    status_id       UUID          NOT NULL,
    scopes          TEXT[]        NULL,
    expires_at      TIMESTAMP     NULL,
    last_used_at    TIMESTAMP     NULL,
    last_used_ip    VARCHAR(45)   NULL,
    revoked_at      TIMESTAMP     NULL,
    revoked_by      UUID          NULL,
    revoke_reason   VARCHAR(500)  NULL,
    is_deleted      BOOLEAN       NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMP     NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP     NOT NULL DEFAULT NOW(),
    created_by      UUID          NULL,
    CONSTRAINT pk_46_fct_api_keys          PRIMARY KEY (id),
    CONSTRAINT uq_46_fct_api_keys_key_hash UNIQUE (key_hash),
    CONSTRAINT fk_46_fct_api_keys_user_id
        FOREIGN KEY (user_id) REFERENCES "03_auth_manage"."03_fct_users" (id)
        ON DELETE RESTRICT,
    CONSTRAINT fk_46_fct_api_keys_status_id
        FOREIGN KEY (status_id) REFERENCES "03_auth_manage"."45_dim_api_key_statuses" (id)
        ON DELETE RESTRICT,
    CONSTRAINT fk_46_fct_api_keys_revoked_by
        FOREIGN KEY (revoked_by) REFERENCES "03_auth_manage"."03_fct_users" (id)
        ON DELETE RESTRICT
);

-- Index: lookup by hash (primary auth path)
CREATE INDEX IF NOT EXISTS idx_46_fct_api_keys_key_hash
    ON "03_auth_manage"."46_fct_api_keys" (key_hash)
    WHERE is_deleted = FALSE;

-- Index: list keys by user + tenant
CREATE INDEX IF NOT EXISTS idx_46_fct_api_keys_user_tenant
    ON "03_auth_manage"."46_fct_api_keys" (user_id, tenant_key)
    WHERE is_deleted = FALSE;

-- Index: find expiring keys for cleanup
CREATE INDEX IF NOT EXISTS idx_46_fct_api_keys_expires
    ON "03_auth_manage"."46_fct_api_keys" (expires_at)
    WHERE expires_at IS NOT NULL AND revoked_at IS NULL AND is_deleted = FALSE;

-- ═══════════════════════════════════════════════════════════════════════
-- 3. FEATURE FLAG: api_key_management
-- ═══════════════════════════════════════════════════════════════════════

INSERT INTO "03_auth_manage"."14_dim_feature_flags" (
    id, code, name, description, feature_flag_category_code, access_mode, lifecycle_state, initial_audience,
    env_dev, env_staging, env_prod, created_at, updated_at
)
SELECT '00000000-0000-0000-0000-000000000430', 'api_key_management',
       'API Key Management',
       'Enterprise API key creation, rotation, revocation, and authentication for programmatic access.',
       'admin', 'permissioned', 'active', 'platform_super_admin',
       TRUE, FALSE, FALSE,
       TIMESTAMP '2026-03-15 00:00:00', TIMESTAMP '2026-03-15 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."14_dim_feature_flags" WHERE code = 'api_key_management');

-- ═══════════════════════════════════════════════════════════════════════
-- 4. FEATURE PERMISSIONS: api_key_management.{view,create,update,revoke}
-- ═══════════════════════════════════════════════════════════════════════

INSERT INTO "03_auth_manage"."15_dim_feature_permissions" (
    id, code, feature_flag_code, permission_action_code, name, description, created_at, updated_at
)
SELECT '00000000-0000-0000-0000-000000000530', 'api_key_management.view',
       'api_key_management', 'view',
       'View API Keys', 'View and list API keys.',
       TIMESTAMP '2026-03-15 00:00:00', TIMESTAMP '2026-03-15 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'api_key_management.view');

INSERT INTO "03_auth_manage"."15_dim_feature_permissions" (
    id, code, feature_flag_code, permission_action_code, name, description, created_at, updated_at
)
SELECT '00000000-0000-0000-0000-000000000531', 'api_key_management.create',
       'api_key_management', 'create',
       'Create API Keys', 'Create new API keys.',
       TIMESTAMP '2026-03-15 00:00:00', TIMESTAMP '2026-03-15 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'api_key_management.create');

INSERT INTO "03_auth_manage"."15_dim_feature_permissions" (
    id, code, feature_flag_code, permission_action_code, name, description, created_at, updated_at
)
SELECT '00000000-0000-0000-0000-000000000532', 'api_key_management.update',
       'api_key_management', 'update',
       'Update API Keys', 'Update API key metadata.',
       TIMESTAMP '2026-03-15 00:00:00', TIMESTAMP '2026-03-15 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'api_key_management.update');

INSERT INTO "03_auth_manage"."15_dim_feature_permissions" (
    id, code, feature_flag_code, permission_action_code, name, description, created_at, updated_at
)
SELECT '00000000-0000-0000-0000-000000000533', 'api_key_management.revoke',
       'api_key_management', 'revoke',
       'Revoke API Keys', 'Revoke active API keys.',
       TIMESTAMP '2026-03-15 00:00:00', TIMESTAMP '2026-03-15 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'api_key_management.revoke');

-- ═══════════════════════════════════════════════════════════════════════
-- 5. GRANT ALL API KEY PERMISSIONS TO platform_super_admin ROLE
-- ═══════════════════════════════════════════════════════════════════════

INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions" (
    id, role_id, feature_permission_id,
    is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
    created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
)
SELECT '00000000-0000-0000-0000-000000000930', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000530',
       TRUE, FALSE, FALSE, FALSE, TRUE, FALSE,
       TIMESTAMP '2026-03-15 00:00:00', TIMESTAMP '2026-03-15 00:00:00', NULL, NULL, NULL, NULL
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."20_lnk_role_feature_permissions" WHERE role_id = '00000000-0000-0000-0000-000000000601' AND feature_permission_id = '00000000-0000-0000-0000-000000000530');

INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions" (
    id, role_id, feature_permission_id,
    is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
    created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
)
SELECT '00000000-0000-0000-0000-000000000931', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000531',
       TRUE, FALSE, FALSE, FALSE, TRUE, FALSE,
       TIMESTAMP '2026-03-15 00:00:00', TIMESTAMP '2026-03-15 00:00:00', NULL, NULL, NULL, NULL
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."20_lnk_role_feature_permissions" WHERE role_id = '00000000-0000-0000-0000-000000000601' AND feature_permission_id = '00000000-0000-0000-0000-000000000531');

INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions" (
    id, role_id, feature_permission_id,
    is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
    created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
)
SELECT '00000000-0000-0000-0000-000000000932', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000532',
       TRUE, FALSE, FALSE, FALSE, TRUE, FALSE,
       TIMESTAMP '2026-03-15 00:00:00', TIMESTAMP '2026-03-15 00:00:00', NULL, NULL, NULL, NULL
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."20_lnk_role_feature_permissions" WHERE role_id = '00000000-0000-0000-0000-000000000601' AND feature_permission_id = '00000000-0000-0000-0000-000000000532');

INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions" (
    id, role_id, feature_permission_id,
    is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
    created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
)
SELECT '00000000-0000-0000-0000-000000000933', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000533',
       TRUE, FALSE, FALSE, FALSE, TRUE, FALSE,
       TIMESTAMP '2026-03-15 00:00:00', TIMESTAMP '2026-03-15 00:00:00', NULL, NULL, NULL, NULL
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."20_lnk_role_feature_permissions" WHERE role_id = '00000000-0000-0000-0000-000000000601' AND feature_permission_id = '00000000-0000-0000-0000-000000000533');
