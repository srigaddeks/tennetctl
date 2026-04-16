-- ─────────────────────────────────────────────────────────────────────────
-- Enhancement Migration: EAV dimension tables, settings tables for
-- roles/groups/feature flags, audit indexes, session management support
-- ─────────────────────────────────────────────────────────────────────────

-- ═══════════════════════════════════════════════════════════════════════
-- 1. DIMENSION TABLES FOR EXISTING SETTINGS EAV TABLES
-- ═══════════════════════════════════════════════════════════════════════

-- Org setting keys
CREATE TABLE IF NOT EXISTS "03_auth_manage"."31_dim_org_setting_keys" (
    id          UUID         NOT NULL DEFAULT gen_random_uuid(),
    code        VARCHAR(100) NOT NULL,
    name        VARCHAR(200) NOT NULL,
    description TEXT         NOT NULL,
    data_type   VARCHAR(30)  NOT NULL DEFAULT 'string',
    is_pii      BOOLEAN      NOT NULL DEFAULT FALSE,
    is_required BOOLEAN      NOT NULL DEFAULT FALSE,
    sort_order  INTEGER      NOT NULL DEFAULT 0,
    created_at  TIMESTAMP    NOT NULL,
    updated_at  TIMESTAMP    NOT NULL,
    CONSTRAINT pk_31_dim_org_setting_keys      PRIMARY KEY (id),
    CONSTRAINT uq_31_dim_org_setting_keys_code UNIQUE (code)
);

-- Workspace setting keys
CREATE TABLE IF NOT EXISTS "03_auth_manage"."36_dim_workspace_setting_keys" (
    id          UUID         NOT NULL DEFAULT gen_random_uuid(),
    code        VARCHAR(100) NOT NULL,
    name        VARCHAR(200) NOT NULL,
    description TEXT         NOT NULL,
    data_type   VARCHAR(30)  NOT NULL DEFAULT 'string',
    is_pii      BOOLEAN      NOT NULL DEFAULT FALSE,
    is_required BOOLEAN      NOT NULL DEFAULT FALSE,
    sort_order  INTEGER      NOT NULL DEFAULT 0,
    created_at  TIMESTAMP    NOT NULL,
    updated_at  TIMESTAMP    NOT NULL,
    CONSTRAINT pk_36_dim_workspace_setting_keys      PRIMARY KEY (id),
    CONSTRAINT uq_36_dim_workspace_setting_keys_code UNIQUE (code)
);

-- Product setting keys
CREATE TABLE IF NOT EXISTS "03_auth_manage"."26_dim_product_setting_keys" (
    id          UUID         NOT NULL DEFAULT gen_random_uuid(),
    code        VARCHAR(100) NOT NULL,
    name        VARCHAR(200) NOT NULL,
    description TEXT         NOT NULL,
    data_type   VARCHAR(30)  NOT NULL DEFAULT 'string',
    is_pii      BOOLEAN      NOT NULL DEFAULT FALSE,
    is_required BOOLEAN      NOT NULL DEFAULT FALSE,
    sort_order  INTEGER      NOT NULL DEFAULT 0,
    created_at  TIMESTAMP    NOT NULL,
    updated_at  TIMESTAMP    NOT NULL,
    CONSTRAINT pk_26_dim_product_setting_keys      PRIMARY KEY (id),
    CONSTRAINT uq_26_dim_product_setting_keys_code UNIQUE (code)
);

-- ═══════════════════════════════════════════════════════════════════════
-- 2. NEW EAV SETTINGS TABLES FOR ROLES, GROUPS, FEATURE FLAGS
-- ═══════════════════════════════════════════════════════════════════════

-- Role setting keys (dimension)
CREATE TABLE IF NOT EXISTS "03_auth_manage"."22_dim_role_setting_keys" (
    id          UUID         NOT NULL DEFAULT gen_random_uuid(),
    code        VARCHAR(100) NOT NULL,
    name        VARCHAR(200) NOT NULL,
    description TEXT         NOT NULL,
    data_type   VARCHAR(30)  NOT NULL DEFAULT 'string',
    is_pii      BOOLEAN      NOT NULL DEFAULT FALSE,
    is_required BOOLEAN      NOT NULL DEFAULT FALSE,
    sort_order  INTEGER      NOT NULL DEFAULT 0,
    created_at  TIMESTAMP    NOT NULL,
    updated_at  TIMESTAMP    NOT NULL,
    CONSTRAINT pk_22_dim_role_setting_keys      PRIMARY KEY (id),
    CONSTRAINT uq_22_dim_role_setting_keys_code UNIQUE (code)
);

-- Role settings (EAV detail)
CREATE TABLE IF NOT EXISTS "03_auth_manage"."22_dtl_role_settings" (
    id            UUID         NOT NULL DEFAULT gen_random_uuid(),
    role_id       UUID         NOT NULL,
    setting_key   VARCHAR(100) NOT NULL,
    setting_value TEXT         NOT NULL,
    created_at    TIMESTAMP    NOT NULL,
    updated_at    TIMESTAMP    NOT NULL,
    created_by    UUID         NULL,
    updated_by    UUID         NULL,
    CONSTRAINT pk_22_dtl_role_settings      PRIMARY KEY (id),
    CONSTRAINT uq_22_dtl_role_settings_key  UNIQUE (role_id, setting_key),
    CONSTRAINT fk_22_dtl_role_settings_role FOREIGN KEY (role_id)
        REFERENCES "03_auth_manage"."16_fct_roles" (id) ON DELETE CASCADE,
    CONSTRAINT fk_22_dtl_role_settings_key  FOREIGN KEY (setting_key)
        REFERENCES "03_auth_manage"."22_dim_role_setting_keys" (code) ON DELETE RESTRICT
);

-- Group setting keys (dimension)
CREATE TABLE IF NOT EXISTS "03_auth_manage"."27_dim_group_setting_keys" (
    id          UUID         NOT NULL DEFAULT gen_random_uuid(),
    code        VARCHAR(100) NOT NULL,
    name        VARCHAR(200) NOT NULL,
    description TEXT         NOT NULL,
    data_type   VARCHAR(30)  NOT NULL DEFAULT 'string',
    is_pii      BOOLEAN      NOT NULL DEFAULT FALSE,
    is_required BOOLEAN      NOT NULL DEFAULT FALSE,
    sort_order  INTEGER      NOT NULL DEFAULT 0,
    created_at  TIMESTAMP    NOT NULL,
    updated_at  TIMESTAMP    NOT NULL,
    CONSTRAINT pk_27_dim_group_setting_keys      PRIMARY KEY (id),
    CONSTRAINT uq_27_dim_group_setting_keys_code UNIQUE (code)
);

-- Group settings (EAV detail)
CREATE TABLE IF NOT EXISTS "03_auth_manage"."27_dtl_group_settings" (
    id            UUID         NOT NULL DEFAULT gen_random_uuid(),
    group_id      UUID         NOT NULL,
    setting_key   VARCHAR(100) NOT NULL,
    setting_value TEXT         NOT NULL,
    created_at    TIMESTAMP    NOT NULL,
    updated_at    TIMESTAMP    NOT NULL,
    created_by    UUID         NULL,
    updated_by    UUID         NULL,
    CONSTRAINT pk_27_dtl_group_settings       PRIMARY KEY (id),
    CONSTRAINT uq_27_dtl_group_settings_key   UNIQUE (group_id, setting_key),
    CONSTRAINT fk_27_dtl_group_settings_group FOREIGN KEY (group_id)
        REFERENCES "03_auth_manage"."17_fct_user_groups" (id) ON DELETE CASCADE,
    CONSTRAINT fk_27_dtl_group_settings_key   FOREIGN KEY (setting_key)
        REFERENCES "03_auth_manage"."27_dim_group_setting_keys" (code) ON DELETE RESTRICT
);

-- Feature flag setting keys (dimension)
CREATE TABLE IF NOT EXISTS "03_auth_manage"."21_dim_feature_flag_setting_keys" (
    id          UUID         NOT NULL DEFAULT gen_random_uuid(),
    code        VARCHAR(100) NOT NULL,
    name        VARCHAR(200) NOT NULL,
    description TEXT         NOT NULL,
    data_type   VARCHAR(30)  NOT NULL DEFAULT 'string',
    is_pii      BOOLEAN      NOT NULL DEFAULT FALSE,
    is_required BOOLEAN      NOT NULL DEFAULT FALSE,
    sort_order  INTEGER      NOT NULL DEFAULT 0,
    created_at  TIMESTAMP    NOT NULL,
    updated_at  TIMESTAMP    NOT NULL,
    CONSTRAINT pk_21_dim_feature_flag_setting_keys      PRIMARY KEY (id),
    CONSTRAINT uq_21_dim_feature_flag_setting_keys_code UNIQUE (code)
);

-- Feature flag settings (EAV detail)
CREATE TABLE IF NOT EXISTS "03_auth_manage"."21_dtl_feature_flag_settings" (
    id              UUID         NOT NULL DEFAULT gen_random_uuid(),
    feature_flag_id UUID         NOT NULL,
    setting_key     VARCHAR(100) NOT NULL,
    setting_value   TEXT         NOT NULL,
    created_at      TIMESTAMP    NOT NULL,
    updated_at      TIMESTAMP    NOT NULL,
    created_by      UUID         NULL,
    updated_by      UUID         NULL,
    CONSTRAINT pk_21_dtl_feature_flag_settings      PRIMARY KEY (id),
    CONSTRAINT uq_21_dtl_feature_flag_settings_key  UNIQUE (feature_flag_id, setting_key),
    CONSTRAINT fk_21_dtl_feature_flag_settings_flag FOREIGN KEY (feature_flag_id)
        REFERENCES "03_auth_manage"."14_dim_feature_flags" (id) ON DELETE CASCADE,
    CONSTRAINT fk_21_dtl_feature_flag_settings_key  FOREIGN KEY (setting_key)
        REFERENCES "03_auth_manage"."21_dim_feature_flag_setting_keys" (code) ON DELETE RESTRICT
);

-- ═══════════════════════════════════════════════════════════════════════
-- 3. FK CONSTRAINTS ON EXISTING SETTINGS TABLES (add dimension key FK)
-- ═══════════════════════════════════════════════════════════════════════

-- Org settings → dimension key FK
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_30_dtl_org_settings_key'
          AND table_schema = '03_auth_manage'
    ) THEN
        ALTER TABLE "03_auth_manage"."30_dtl_org_settings"
            ADD CONSTRAINT fk_30_dtl_org_settings_key
                FOREIGN KEY (setting_key)
                REFERENCES "03_auth_manage"."31_dim_org_setting_keys" (code)
                ON DELETE RESTRICT;
    END IF;
END $$;

-- Workspace settings → dimension key FK
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_35_dtl_workspace_settings_key'
          AND table_schema = '03_auth_manage'
    ) THEN
        ALTER TABLE "03_auth_manage"."35_dtl_workspace_settings"
            ADD CONSTRAINT fk_35_dtl_workspace_settings_key
                FOREIGN KEY (setting_key)
                REFERENCES "03_auth_manage"."36_dim_workspace_setting_keys" (code)
                ON DELETE RESTRICT;
    END IF;
END $$;

-- Product settings → dimension key FK
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_25_dtl_product_settings_key'
          AND table_schema = '03_auth_manage'
    ) THEN
        ALTER TABLE "03_auth_manage"."25_dtl_product_settings"
            ADD CONSTRAINT fk_25_dtl_product_settings_key
                FOREIGN KEY (setting_key)
                REFERENCES "03_auth_manage"."26_dim_product_setting_keys" (code)
                ON DELETE RESTRICT;
    END IF;
END $$;

-- ═══════════════════════════════════════════════════════════════════════
-- 4. SEED INITIAL SETTING KEYS
-- ═══════════════════════════════════════════════════════════════════════

-- Org setting keys
INSERT INTO "03_auth_manage"."31_dim_org_setting_keys"
    (code, name, description, data_type, is_pii, is_required, sort_order, created_at, updated_at)
VALUES
    ('logo_url',    'Logo URL',        'Organization logo image URL',          'url',    FALSE, FALSE, 10, NOW(), NOW()),
    ('website',     'Website',         'Organization website URL',             'url',    FALSE, FALSE, 20, NOW(), NOW()),
    ('industry',    'Industry',        'Industry or sector',                   'string', FALSE, FALSE, 30, NOW(), NOW()),
    ('address',     'Address',         'Primary business address',             'string', TRUE,  FALSE, 40, NOW(), NOW()),
    ('phone',       'Phone',           'Organization phone number',            'phone',  TRUE,  FALSE, 50, NOW(), NOW()),
    ('tax_id',      'Tax ID',          'Tax identification number',            'string', TRUE,  FALSE, 60, NOW(), NOW()),
    ('description', 'Description',     'Organization description',             'string', FALSE, FALSE, 70, NOW(), NOW()),
    ('country',     'Country',         'Country code (ISO 3166-1 alpha-2)',    'string', FALSE, FALSE, 80, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- Workspace setting keys
INSERT INTO "03_auth_manage"."36_dim_workspace_setting_keys"
    (code, name, description, data_type, is_pii, is_required, sort_order, created_at, updated_at)
VALUES
    ('color',        'Color',          'Workspace accent color (hex)',         'string',  FALSE, FALSE, 10, NOW(), NOW()),
    ('icon',         'Icon',           'Workspace icon name or URL',          'string',  FALSE, FALSE, 20, NOW(), NOW()),
    ('description',  'Description',    'Workspace description',               'string',  FALSE, FALSE, 30, NOW(), NOW()),
    ('max_members',  'Max Members',    'Maximum member count',                'integer', FALSE, FALSE, 40, NOW(), NOW()),
    ('timezone',     'Timezone',       'Workspace default timezone (IANA)',    'string',  FALSE, FALSE, 50, NOW(), NOW()),
    ('notification_email', 'Notification Email', 'Email for workspace notifications', 'email', FALSE, FALSE, 60, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- Product setting keys
INSERT INTO "03_auth_manage"."26_dim_product_setting_keys"
    (code, name, description, data_type, is_pii, is_required, sort_order, created_at, updated_at)
VALUES
    ('tier',            'Tier',            'Product tier (free, pro, enterprise)',  'string',  FALSE, FALSE, 10, NOW(), NOW()),
    ('pricing_model',   'Pricing Model',   'Pricing model (per_seat, flat, usage)','string',  FALSE, FALSE, 20, NOW(), NOW()),
    ('trial_days',      'Trial Days',      'Number of trial days',                 'integer', FALSE, FALSE, 30, NOW(), NOW()),
    ('max_users',       'Max Users',       'Maximum users per subscription',       'integer', FALSE, FALSE, 40, NOW(), NOW()),
    ('logo_url',        'Logo URL',        'Product logo URL',                     'url',     FALSE, FALSE, 50, NOW(), NOW()),
    ('support_email',   'Support Email',   'Product support email',                'email',   FALSE, FALSE, 60, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- Role setting keys
INSERT INTO "03_auth_manage"."22_dim_role_setting_keys"
    (code, name, description, data_type, is_pii, is_required, sort_order, created_at, updated_at)
VALUES
    ('color',           'Color',           'Role badge color (hex)',               'string',  FALSE, FALSE, 10, NOW(), NOW()),
    ('icon',            'Icon',            'Role icon name',                       'string',  FALSE, FALSE, 20, NOW(), NOW()),
    ('priority',        'Priority',        'Role display priority (lower = first)','integer', FALSE, FALSE, 30, NOW(), NOW()),
    ('description_long','Long Description','Extended role description',            'string',  FALSE, FALSE, 40, NOW(), NOW()),
    ('max_assignments', 'Max Assignments', 'Maximum users that can hold this role','integer', FALSE, FALSE, 50, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- Group setting keys
INSERT INTO "03_auth_manage"."27_dim_group_setting_keys"
    (code, name, description, data_type, is_pii, is_required, sort_order, created_at, updated_at)
VALUES
    ('color',        'Color',          'Group badge color (hex)',              'string',  FALSE, FALSE, 10, NOW(), NOW()),
    ('icon',         'Icon',           'Group icon name',                     'string',  FALSE, FALSE, 20, NOW(), NOW()),
    ('max_members',  'Max Members',    'Maximum member count',                'integer', FALSE, FALSE, 30, NOW(), NOW()),
    ('description_long', 'Long Description', 'Extended group description',   'string',  FALSE, FALSE, 40, NOW(), NOW()),
    ('auto_join',    'Auto Join',      'Automatically join new users',        'boolean', FALSE, FALSE, 50, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- Feature flag setting keys
INSERT INTO "03_auth_manage"."21_dim_feature_flag_setting_keys"
    (code, name, description, data_type, is_pii, is_required, sort_order, created_at, updated_at)
VALUES
    ('rollout_percentage', 'Rollout Percentage', 'Percentage of users who see this flag', 'integer', FALSE, FALSE, 10, NOW(), NOW()),
    ('sunset_date',        'Sunset Date',        'Planned removal date (ISO 8601)',       'string',  FALSE, FALSE, 20, NOW(), NOW()),
    ('owner_team',         'Owner Team',         'Team responsible for this flag',         'string',  FALSE, FALSE, 30, NOW(), NOW()),
    ('jira_ticket',        'Jira Ticket',        'Linked Jira/issue tracker ticket',      'string',  FALSE, FALSE, 40, NOW(), NOW()),
    ('notes',              'Notes',              'Internal notes about this flag',         'string',  FALSE, FALSE, 50, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- ═══════════════════════════════════════════════════════════════════════
-- 5. NEW AUDIT EVENT TYPES + FEATURE PERMISSIONS
-- ═══════════════════════════════════════════════════════════════════════

-- Seed 'platform_admin' category (referenced by admin_console flag below)
INSERT INTO "03_auth_manage"."11_dim_feature_flag_categories" (id, code, name, description, sort_order, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000000105', 'platform_admin', 'Platform Admin', 'Feature flags for platform-level admin capabilities.', 45, NOW(), NOW()
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."11_dim_feature_flag_categories" WHERE code = 'platform_admin');

-- Feature flag: admin_console (for user listing, audit log, session management)
INSERT INTO "03_auth_manage"."14_dim_feature_flags"
    (id, code, name, description, feature_flag_category_code, access_mode, lifecycle_state,
     initial_audience, env_dev, env_staging, env_prod, created_at, updated_at)
VALUES
    ('00000000-0000-0000-0000-000000000420', 'admin_console', 'Admin Console',
     'Administrative operations: user listing, audit log, session management',
     'platform_admin', 'permissioned', 'active', 'internal', TRUE, TRUE, TRUE, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- Permissions for admin_console
INSERT INTO "03_auth_manage"."15_dim_feature_permissions"
    (id, code, feature_flag_code, permission_action_code, name, description, created_at, updated_at)
VALUES
    ('00000000-0000-0000-0000-000000000421', 'admin_console.view', 'admin_console', 'view',
     'View Admin Console', 'View users, audit log, and sessions', NOW(), NOW()),
    ('00000000-0000-0000-0000-000000000422', 'admin_console.update', 'admin_console', 'update',
     'Update via Admin Console', 'Manage sessions and user states', NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- ═══════════════════════════════════════════════════════════════════════
-- 6. INDEXES FOR AUDIT LOG QUERIES AND SESSION MANAGEMENT
-- ═══════════════════════════════════════════════════════════════════════

-- Audit events: index for querying by entity
CREATE INDEX IF NOT EXISTS idx_40_aud_events_entity
    ON "03_auth_manage"."40_aud_events" (entity_type, entity_id);

-- Audit events: index for querying by actor
CREATE INDEX IF NOT EXISTS idx_40_aud_events_actor
    ON "03_auth_manage"."40_aud_events" (actor_id)
    WHERE actor_id IS NOT NULL;

-- Audit events: index for querying by time range
CREATE INDEX IF NOT EXISTS idx_40_aud_events_occurred_at
    ON "03_auth_manage"."40_aud_events" (occurred_at DESC);

-- Audit events: index for querying by event type
CREATE INDEX IF NOT EXISTS idx_40_aud_events_event_type
    ON "03_auth_manage"."40_aud_events" (event_type);

-- Sessions: index for listing active sessions by user
CREATE INDEX IF NOT EXISTS idx_10_trx_auth_sessions_user_active
    ON "03_auth_manage"."10_trx_auth_sessions" (user_id, created_at DESC)
    WHERE revoked_at IS NULL;

-- Audit event properties: index for event lookup
CREATE INDEX IF NOT EXISTS idx_41_dtl_audit_event_properties_event
    ON "03_auth_manage"."41_dtl_audit_event_properties" (event_id);
