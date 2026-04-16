CREATE TABLE IF NOT EXISTS "03_auth_manage"."11_dim_feature_flag_categories" (
    id UUID NOT NULL,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    sort_order INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    CONSTRAINT pk_11_dim_feature_flag_categories PRIMARY KEY (id),
    CONSTRAINT uq_11_dim_feature_flag_categories_code UNIQUE (code)
);

CREATE TABLE IF NOT EXISTS "03_auth_manage"."12_dim_feature_permission_actions" (
    id UUID NOT NULL,
    code VARCHAR(30) NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    sort_order INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    CONSTRAINT pk_12_dim_feature_permission_actions PRIMARY KEY (id),
    CONSTRAINT uq_12_dim_feature_permission_actions_code UNIQUE (code)
);

CREATE TABLE IF NOT EXISTS "03_auth_manage"."13_dim_role_levels" (
    id UUID NOT NULL,
    code VARCHAR(30) NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    sort_order INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    CONSTRAINT pk_13_dim_role_levels PRIMARY KEY (id),
    CONSTRAINT uq_13_dim_role_levels_code UNIQUE (code)
);

CREATE TABLE IF NOT EXISTS "03_auth_manage"."14_dim_feature_flags" (
    id UUID NOT NULL,
    code VARCHAR(80) NOT NULL,
    name VARCHAR(120) NOT NULL,
    description TEXT NOT NULL,
    feature_flag_category_code VARCHAR(50) NOT NULL,
    access_mode VARCHAR(30) NOT NULL,
    lifecycle_state VARCHAR(30) NOT NULL,
    initial_audience VARCHAR(60) NOT NULL,
    env_dev BOOLEAN NOT NULL DEFAULT TRUE,
    env_staging BOOLEAN NOT NULL DEFAULT FALSE,
    env_prod BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    CONSTRAINT pk_14_dim_feature_flags PRIMARY KEY (id),
    CONSTRAINT uq_14_dim_feature_flags_code UNIQUE (code),
    CONSTRAINT fk_14_dim_feature_flags_feature_flag_category_code_11_dim_feature_flag_categories FOREIGN KEY (feature_flag_category_code)
        REFERENCES "03_auth_manage"."11_dim_feature_flag_categories" (code)
        ON DELETE RESTRICT,
    CONSTRAINT ck_14_dim_feature_flags_access_mode CHECK (access_mode IN ('public', 'authenticated', 'permissioned'))
);

CREATE TABLE IF NOT EXISTS "03_auth_manage"."15_dim_feature_permissions" (
    id UUID NOT NULL,
    code VARCHAR(120) NOT NULL,
    feature_flag_code VARCHAR(80) NOT NULL,
    permission_action_code VARCHAR(30) NOT NULL,
    name VARCHAR(120) NOT NULL,
    description TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    CONSTRAINT pk_15_dim_feature_permissions PRIMARY KEY (id),
    CONSTRAINT uq_15_dim_feature_permissions_code UNIQUE (code),
    CONSTRAINT uq_15_dim_feature_permissions_feature_action UNIQUE (feature_flag_code, permission_action_code),
    CONSTRAINT fk_15_dim_feature_permissions_feature_flag_code_14_dim_feature_flags FOREIGN KEY (feature_flag_code)
        REFERENCES "03_auth_manage"."14_dim_feature_flags" (code)
        ON DELETE RESTRICT,
    CONSTRAINT fk_15_dim_feature_permissions_permission_action_code_12_dim_feature_permission_actions FOREIGN KEY (permission_action_code)
        REFERENCES "03_auth_manage"."12_dim_feature_permission_actions" (code)
        ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "03_auth_manage"."16_fct_roles" (
    id UUID NOT NULL,
    tenant_key VARCHAR(100) NOT NULL,
    role_level_code VARCHAR(30) NOT NULL,
    code VARCHAR(80) NOT NULL,
    name VARCHAR(120) NOT NULL,
    description TEXT NOT NULL,
    scope_org_id UUID NULL,
    scope_workspace_id UUID NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_disabled BOOLEAN NOT NULL DEFAULT FALSE,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    is_test BOOLEAN NOT NULL DEFAULT FALSE,
    is_system BOOLEAN NOT NULL DEFAULT FALSE,
    is_locked BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    created_by UUID NULL,
    updated_by UUID NULL,
    deleted_at TIMESTAMP NULL,
    deleted_by UUID NULL,
    CONSTRAINT pk_16_fct_roles PRIMARY KEY (id),
    CONSTRAINT uq_16_fct_roles_tenant_level_code UNIQUE (tenant_key, role_level_code, code),
    CONSTRAINT fk_16_fct_roles_role_level_code_13_dim_role_levels FOREIGN KEY (role_level_code)
        REFERENCES "03_auth_manage"."13_dim_role_levels" (code)
        ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "03_auth_manage"."17_fct_user_groups" (
    id UUID NOT NULL,
    tenant_key VARCHAR(100) NOT NULL,
    role_level_code VARCHAR(30) NOT NULL,
    code VARCHAR(80) NOT NULL,
    name VARCHAR(120) NOT NULL,
    description TEXT NOT NULL,
    scope_org_id UUID NULL,
    scope_workspace_id UUID NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_disabled BOOLEAN NOT NULL DEFAULT FALSE,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    is_test BOOLEAN NOT NULL DEFAULT FALSE,
    is_system BOOLEAN NOT NULL DEFAULT FALSE,
    is_locked BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    created_by UUID NULL,
    updated_by UUID NULL,
    deleted_at TIMESTAMP NULL,
    deleted_by UUID NULL,
    CONSTRAINT pk_17_fct_user_groups PRIMARY KEY (id),
    CONSTRAINT uq_17_fct_user_groups_tenant_level_code UNIQUE (tenant_key, role_level_code, code),
    CONSTRAINT fk_17_fct_user_groups_role_level_code_13_dim_role_levels FOREIGN KEY (role_level_code)
        REFERENCES "03_auth_manage"."13_dim_role_levels" (code)
        ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "03_auth_manage"."18_lnk_group_memberships" (
    id UUID NOT NULL,
    group_id UUID NOT NULL,
    user_id UUID NOT NULL,
    membership_status VARCHAR(30) NOT NULL,
    effective_from TIMESTAMP NOT NULL,
    effective_to TIMESTAMP NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_disabled BOOLEAN NOT NULL DEFAULT FALSE,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    is_test BOOLEAN NOT NULL DEFAULT FALSE,
    is_system BOOLEAN NOT NULL DEFAULT FALSE,
    is_locked BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    created_by UUID NULL,
    updated_by UUID NULL,
    deleted_at TIMESTAMP NULL,
    deleted_by UUID NULL,
    CONSTRAINT pk_18_lnk_group_memberships PRIMARY KEY (id),
    CONSTRAINT uq_18_lnk_group_memberships_group_user UNIQUE (group_id, user_id),
    CONSTRAINT fk_18_lnk_group_memberships_group_id_17_fct_user_groups FOREIGN KEY (group_id)
        REFERENCES "03_auth_manage"."17_fct_user_groups" (id)
        ON DELETE RESTRICT,
    CONSTRAINT fk_18_lnk_group_memberships_user_id_03_fct_users FOREIGN KEY (user_id)
        REFERENCES "03_auth_manage"."03_fct_users" (id)
        ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "03_auth_manage"."19_lnk_group_role_assignments" (
    id UUID NOT NULL,
    group_id UUID NOT NULL,
    role_id UUID NOT NULL,
    assignment_status VARCHAR(30) NOT NULL,
    effective_from TIMESTAMP NOT NULL,
    effective_to TIMESTAMP NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_disabled BOOLEAN NOT NULL DEFAULT FALSE,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    is_test BOOLEAN NOT NULL DEFAULT FALSE,
    is_system BOOLEAN NOT NULL DEFAULT FALSE,
    is_locked BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    created_by UUID NULL,
    updated_by UUID NULL,
    deleted_at TIMESTAMP NULL,
    deleted_by UUID NULL,
    CONSTRAINT pk_19_lnk_group_role_assignments PRIMARY KEY (id),
    CONSTRAINT uq_19_lnk_group_role_assignments_group_role UNIQUE (group_id, role_id),
    CONSTRAINT fk_19_lnk_group_role_assignments_group_id_17_fct_user_groups FOREIGN KEY (group_id)
        REFERENCES "03_auth_manage"."17_fct_user_groups" (id)
        ON DELETE RESTRICT,
    CONSTRAINT fk_19_lnk_group_role_assignments_role_id_16_fct_roles FOREIGN KEY (role_id)
        REFERENCES "03_auth_manage"."16_fct_roles" (id)
        ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "03_auth_manage"."20_lnk_role_feature_permissions" (
    id UUID NOT NULL,
    role_id UUID NOT NULL,
    feature_permission_id UUID NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_disabled BOOLEAN NOT NULL DEFAULT FALSE,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    is_test BOOLEAN NOT NULL DEFAULT FALSE,
    is_system BOOLEAN NOT NULL DEFAULT FALSE,
    is_locked BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    created_by UUID NULL,
    updated_by UUID NULL,
    deleted_at TIMESTAMP NULL,
    deleted_by UUID NULL,
    CONSTRAINT pk_20_lnk_role_feature_permissions PRIMARY KEY (id),
    CONSTRAINT uq_20_lnk_role_feature_permissions_role_feature UNIQUE (role_id, feature_permission_id),
    CONSTRAINT fk_20_lnk_role_feature_permissions_role_id_16_fct_roles FOREIGN KEY (role_id)
        REFERENCES "03_auth_manage"."16_fct_roles" (id)
        ON DELETE RESTRICT,
    CONSTRAINT fk_20_lnk_role_feature_permissions_feature_permission_id_15_dim_feature_permissions FOREIGN KEY (feature_permission_id)
        REFERENCES "03_auth_manage"."15_dim_feature_permissions" (id)
        ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "03_auth_manage"."21_trx_access_context_events" (
    id UUID NOT NULL,
    user_id UUID NOT NULL,
    session_id UUID NOT NULL,
    tenant_key VARCHAR(100) NOT NULL,
    scope_level_code VARCHAR(30) NOT NULL,
    scope_org_id UUID NULL,
    scope_workspace_id UUID NULL,
    refresh_reason VARCHAR(50) NOT NULL,
    outcome VARCHAR(30) NOT NULL,
    ip_address VARCHAR(64) NULL,
    occurred_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    CONSTRAINT pk_21_trx_access_context_events PRIMARY KEY (id),
    CONSTRAINT fk_21_trx_access_context_events_user_id_03_fct_users FOREIGN KEY (user_id)
        REFERENCES "03_auth_manage"."03_fct_users" (id)
        ON DELETE RESTRICT
);

INSERT INTO "03_auth_manage"."11_dim_feature_flag_categories" (id, code, name, description, sort_order, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000000101', 'auth', 'Auth', 'Feature flags related to sign-in methods and auth capabilities.', 10, TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."11_dim_feature_flag_categories" WHERE code = 'auth');

INSERT INTO "03_auth_manage"."11_dim_feature_flag_categories" (id, code, name, description, sort_order, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000000102', 'policy', 'Policy', 'Feature flags related to policy lifecycle capabilities.', 20, TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."11_dim_feature_flag_categories" WHERE code = 'policy');

INSERT INTO "03_auth_manage"."11_dim_feature_flag_categories" (id, code, name, description, sort_order, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000000103', 'access', 'Access', 'Feature flags related to access resolution and session context.', 30, TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."11_dim_feature_flag_categories" WHERE code = 'access');

INSERT INTO "03_auth_manage"."11_dim_feature_flag_categories" (id, code, name, description, sort_order, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000000104', 'admin', 'Admin', 'Feature flags related to privileged administrative consoles.', 40, TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."11_dim_feature_flag_categories" WHERE code = 'admin');

INSERT INTO "03_auth_manage"."12_dim_feature_permission_actions" (id, code, name, description, sort_order, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000000201', 'view', 'View', 'Read-only visibility of a feature or console area.', 10, TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."12_dim_feature_permission_actions" WHERE code = 'view');

INSERT INTO "03_auth_manage"."12_dim_feature_permission_actions" (id, code, name, description, sort_order, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000000202', 'create', 'Create', 'Create feature-managed state.', 20, TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."12_dim_feature_permission_actions" WHERE code = 'create');

INSERT INTO "03_auth_manage"."12_dim_feature_permission_actions" (id, code, name, description, sort_order, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000000203', 'update', 'Update', 'Update feature-managed state.', 30, TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."12_dim_feature_permission_actions" WHERE code = 'update');

INSERT INTO "03_auth_manage"."12_dim_feature_permission_actions" (id, code, name, description, sort_order, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000000204', 'enable', 'Enable', 'Enable a feature or rollout-controlled capability.', 40, TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."12_dim_feature_permission_actions" WHERE code = 'enable');

INSERT INTO "03_auth_manage"."12_dim_feature_permission_actions" (id, code, name, description, sort_order, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000000205', 'disable', 'Disable', 'Disable a feature or rollout-controlled capability.', 50, TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."12_dim_feature_permission_actions" WHERE code = 'disable');

INSERT INTO "03_auth_manage"."12_dim_feature_permission_actions" (id, code, name, description, sort_order, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000000206', 'assign', 'Assign', 'Assign groups, roles, or feature actions.', 60, TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."12_dim_feature_permission_actions" WHERE code = 'assign');

INSERT INTO "03_auth_manage"."12_dim_feature_permission_actions" (id, code, name, description, sort_order, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000000207', 'revoke', 'Revoke', 'Revoke groups, roles, or feature actions.', 70, TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."12_dim_feature_permission_actions" WHERE code = 'revoke');

INSERT INTO "03_auth_manage"."13_dim_role_levels" (id, code, name, description, sort_order, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000000301', 'super_admin', 'Super Admin', 'Platform-wide access scope.', 10, TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."13_dim_role_levels" WHERE code = 'super_admin');

INSERT INTO "03_auth_manage"."13_dim_role_levels" (id, code, name, description, sort_order, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000000302', 'org', 'Organization', 'Organization-scoped access scope.', 20, TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."13_dim_role_levels" WHERE code = 'org');

INSERT INTO "03_auth_manage"."13_dim_role_levels" (id, code, name, description, sort_order, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000000303', 'workspace', 'Workspace', 'Workspace-scoped access scope.', 30, TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."13_dim_role_levels" WHERE code = 'workspace');

INSERT INTO "03_auth_manage"."14_dim_feature_flags" (
    id, code, name, description, feature_flag_category_code, access_mode, lifecycle_state, initial_audience,
    env_dev, env_staging, env_prod, created_at, updated_at
)
SELECT '00000000-0000-0000-0000-000000000401', 'auth_password_login', 'Password Login', 'Availability of local password login endpoints.', 'auth', 'public', 'active', 'all_users',
       TRUE, FALSE, FALSE, TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."14_dim_feature_flags" WHERE code = 'auth_password_login');

INSERT INTO "03_auth_manage"."14_dim_feature_flags" (
    id, code, name, description, feature_flag_category_code, access_mode, lifecycle_state, initial_audience,
    env_dev, env_staging, env_prod, created_at, updated_at
)
SELECT '00000000-0000-0000-0000-000000000402', 'auth_google_login', 'Google Login', 'Availability of Google login when implemented.', 'auth', 'public', 'planned', 'all_users',
       FALSE, FALSE, FALSE, TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."14_dim_feature_flags" WHERE code = 'auth_google_login');

INSERT INTO "03_auth_manage"."14_dim_feature_flags" (
    id, code, name, description, feature_flag_category_code, access_mode, lifecycle_state, initial_audience,
    env_dev, env_staging, env_prod, created_at, updated_at
)
SELECT '00000000-0000-0000-0000-000000000403', 'policy_management', 'Policy Management', 'Policy creation and lifecycle controls.', 'policy', 'permissioned', 'planned', 'org_admin',
       TRUE, FALSE, FALSE, TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."14_dim_feature_flags" WHERE code = 'policy_management');

INSERT INTO "03_auth_manage"."14_dim_feature_flags" (
    id, code, name, description, feature_flag_category_code, access_mode, lifecycle_state, initial_audience,
    env_dev, env_staging, env_prod, created_at, updated_at
)
SELECT '00000000-0000-0000-0000-000000000404', 'access_governance_console', 'Access Governance Console', 'Privileged access governance console.', 'access', 'permissioned', 'active', 'platform_super_admin',
       TRUE, FALSE, FALSE, TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."14_dim_feature_flags" WHERE code = 'access_governance_console');

INSERT INTO "03_auth_manage"."14_dim_feature_flags" (
    id, code, name, description, feature_flag_category_code, access_mode, lifecycle_state, initial_audience,
    env_dev, env_staging, env_prod, created_at, updated_at
)
SELECT '00000000-0000-0000-0000-000000000405', 'feature_flag_registry', 'Feature Flag Registry', 'Feature catalog and rollout management.', 'admin', 'permissioned', 'active', 'platform_super_admin',
       TRUE, FALSE, FALSE, TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."14_dim_feature_flags" WHERE code = 'feature_flag_registry');

INSERT INTO "03_auth_manage"."14_dim_feature_flags" (
    id, code, name, description, feature_flag_category_code, access_mode, lifecycle_state, initial_audience,
    env_dev, env_staging, env_prod, created_at, updated_at
)
SELECT '00000000-0000-0000-0000-000000000406', 'group_access_assignment', 'Group Access Assignment', 'Group membership and role assignment administration.', 'admin', 'permissioned', 'active', 'platform_super_admin',
       TRUE, FALSE, FALSE, TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."14_dim_feature_flags" WHERE code = 'group_access_assignment');

INSERT INTO "03_auth_manage"."14_dim_feature_flags" (
    id, code, name, description, feature_flag_category_code, access_mode, lifecycle_state, initial_audience,
    env_dev, env_staging, env_prod, created_at, updated_at
)
SELECT '00000000-0000-0000-0000-000000000407', 'access_audit_timeline', 'Access Audit Timeline', 'Audit timeline visibility for feature and access changes.', 'admin', 'permissioned', 'active', 'platform_super_admin',
       TRUE, FALSE, FALSE, TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."14_dim_feature_flags" WHERE code = 'access_audit_timeline');

INSERT INTO "03_auth_manage"."15_dim_feature_permissions" (id, code, feature_flag_code, permission_action_code, name, description, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000000501', 'auth_password_login.enable', 'auth_password_login', 'enable', 'Enable Password Login', 'Enable local password login.', TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'auth_password_login.enable');

INSERT INTO "03_auth_manage"."15_dim_feature_permissions" (id, code, feature_flag_code, permission_action_code, name, description, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000000502', 'auth_password_login.disable', 'auth_password_login', 'disable', 'Disable Password Login', 'Disable local password login.', TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'auth_password_login.disable');

INSERT INTO "03_auth_manage"."15_dim_feature_permissions" (id, code, feature_flag_code, permission_action_code, name, description, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000000503', 'auth_google_login.enable', 'auth_google_login', 'enable', 'Enable Google Login', 'Enable Google login when implemented.', TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'auth_google_login.enable');

INSERT INTO "03_auth_manage"."15_dim_feature_permissions" (id, code, feature_flag_code, permission_action_code, name, description, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000000504', 'auth_google_login.disable', 'auth_google_login', 'disable', 'Disable Google Login', 'Disable Google login when implemented.', TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'auth_google_login.disable');

INSERT INTO "03_auth_manage"."15_dim_feature_permissions" (id, code, feature_flag_code, permission_action_code, name, description, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000000505', 'policy_management.create', 'policy_management', 'create', 'Create Policies', 'Create policies.', TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'policy_management.create');

INSERT INTO "03_auth_manage"."15_dim_feature_permissions" (id, code, feature_flag_code, permission_action_code, name, description, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000000506', 'policy_management.enable', 'policy_management', 'enable', 'Enable Policies', 'Enable policy-managed behavior.', TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'policy_management.enable');

INSERT INTO "03_auth_manage"."15_dim_feature_permissions" (id, code, feature_flag_code, permission_action_code, name, description, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000000507', 'policy_management.disable', 'policy_management', 'disable', 'Disable Policies', 'Disable policy-managed behavior.', TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'policy_management.disable');

INSERT INTO "03_auth_manage"."15_dim_feature_permissions" (id, code, feature_flag_code, permission_action_code, name, description, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000000508', 'access_governance_console.view', 'access_governance_console', 'view', 'View Access Governance Console', 'View access governance console pages.', TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'access_governance_console.view');

INSERT INTO "03_auth_manage"."15_dim_feature_permissions" (id, code, feature_flag_code, permission_action_code, name, description, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000000509', 'access_governance_console.assign', 'access_governance_console', 'assign', 'Assign Access Governance Actions', 'Assign feature permissions to roles.', TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'access_governance_console.assign');

INSERT INTO "03_auth_manage"."15_dim_feature_permissions" (id, code, feature_flag_code, permission_action_code, name, description, created_at, updated_at)
SELECT '00000000-0000-0000-0000-00000000050a', 'feature_flag_registry.view', 'feature_flag_registry', 'view', 'View Feature Registry', 'View feature catalog and rollout state.', TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'feature_flag_registry.view');

INSERT INTO "03_auth_manage"."15_dim_feature_permissions" (id, code, feature_flag_code, permission_action_code, name, description, created_at, updated_at)
SELECT '00000000-0000-0000-0000-00000000050b', 'feature_flag_registry.create', 'feature_flag_registry', 'create', 'Create Feature Flags', 'Create feature flag entries.', TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'feature_flag_registry.create');

INSERT INTO "03_auth_manage"."15_dim_feature_permissions" (id, code, feature_flag_code, permission_action_code, name, description, created_at, updated_at)
SELECT '00000000-0000-0000-0000-00000000050c', 'feature_flag_registry.update', 'feature_flag_registry', 'update', 'Update Feature Flags', 'Update feature metadata.', TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'feature_flag_registry.update');

INSERT INTO "03_auth_manage"."15_dim_feature_permissions" (id, code, feature_flag_code, permission_action_code, name, description, created_at, updated_at)
SELECT '00000000-0000-0000-0000-00000000050d', 'feature_flag_registry.enable', 'feature_flag_registry', 'enable', 'Enable Feature Flags', 'Enable feature rollout in an environment.', TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'feature_flag_registry.enable');

INSERT INTO "03_auth_manage"."15_dim_feature_permissions" (id, code, feature_flag_code, permission_action_code, name, description, created_at, updated_at)
SELECT '00000000-0000-0000-0000-00000000050e', 'feature_flag_registry.disable', 'feature_flag_registry', 'disable', 'Disable Feature Flags', 'Disable feature rollout in an environment.', TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'feature_flag_registry.disable');

INSERT INTO "03_auth_manage"."15_dim_feature_permissions" (id, code, feature_flag_code, permission_action_code, name, description, created_at, updated_at)
SELECT '00000000-0000-0000-0000-00000000050f', 'group_access_assignment.view', 'group_access_assignment', 'view', 'View Group Access Assignment', 'View groups, members, and role assignments.', TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'group_access_assignment.view');

INSERT INTO "03_auth_manage"."15_dim_feature_permissions" (id, code, feature_flag_code, permission_action_code, name, description, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000000510', 'group_access_assignment.assign', 'group_access_assignment', 'assign', 'Assign Group Access', 'Assign group members or group roles.', TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'group_access_assignment.assign');

INSERT INTO "03_auth_manage"."15_dim_feature_permissions" (id, code, feature_flag_code, permission_action_code, name, description, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000000511', 'group_access_assignment.revoke', 'group_access_assignment', 'revoke', 'Revoke Group Access', 'Revoke group members or group roles.', TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'group_access_assignment.revoke');

INSERT INTO "03_auth_manage"."15_dim_feature_permissions" (id, code, feature_flag_code, permission_action_code, name, description, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000000512', 'access_audit_timeline.view', 'access_audit_timeline', 'view', 'View Access Audit Timeline', 'View access audit events.', TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'access_audit_timeline.view');

INSERT INTO "03_auth_manage"."16_fct_roles" (
    id, tenant_key, role_level_code, code, name, description,
    scope_org_id, scope_workspace_id,
    is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
    created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
)
SELECT '00000000-0000-0000-0000-000000000601', 'default', 'super_admin', 'platform_super_admin', 'Platform Super Admin', 'System role for full platform feature governance control.',
       NULL, NULL,
       TRUE, FALSE, FALSE, FALSE, TRUE, FALSE,
       TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00', NULL, NULL, NULL, NULL
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."16_fct_roles" WHERE code = 'platform_super_admin' AND tenant_key = 'default');

INSERT INTO "03_auth_manage"."17_fct_user_groups" (
    id, tenant_key, role_level_code, code, name, description,
    scope_org_id, scope_workspace_id,
    is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
    created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
)
SELECT '00000000-0000-0000-0000-000000000701', 'default', 'super_admin', 'platform_super_admin', 'Platform Super Admin', 'System group for platform super administrators.',
       NULL, NULL,
       TRUE, FALSE, FALSE, FALSE, TRUE, FALSE,
       TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00', NULL, NULL, NULL, NULL
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."17_fct_user_groups" WHERE code = 'platform_super_admin' AND tenant_key = 'default');

INSERT INTO "03_auth_manage"."19_lnk_group_role_assignments" (
    id, group_id, role_id, assignment_status, effective_from, effective_to,
    is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
    created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
)
SELECT '00000000-0000-0000-0000-000000000801', '00000000-0000-0000-0000-000000000701', '00000000-0000-0000-0000-000000000601', 'active', TIMESTAMP '2026-03-13 00:00:00', NULL,
       TRUE, FALSE, FALSE, FALSE, TRUE, FALSE,
       TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00', NULL, NULL, NULL, NULL
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."19_lnk_group_role_assignments" WHERE group_id = '00000000-0000-0000-0000-000000000701' AND role_id = '00000000-0000-0000-0000-000000000601');

INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions" (
    id, role_id, feature_permission_id,
    is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
    created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
)
SELECT '00000000-0000-0000-0000-000000000901', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000508',
       TRUE, FALSE, FALSE, FALSE, TRUE, FALSE,
       TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00', NULL, NULL, NULL, NULL
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."20_lnk_role_feature_permissions" WHERE role_id = '00000000-0000-0000-0000-000000000601' AND feature_permission_id = '00000000-0000-0000-0000-000000000508');

INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions" (
    id, role_id, feature_permission_id,
    is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
    created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
)
SELECT '00000000-0000-0000-0000-000000000902', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000509',
       TRUE, FALSE, FALSE, FALSE, TRUE, FALSE,
       TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00', NULL, NULL, NULL, NULL
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."20_lnk_role_feature_permissions" WHERE role_id = '00000000-0000-0000-0000-000000000601' AND feature_permission_id = '00000000-0000-0000-0000-000000000509');

INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions" (
    id, role_id, feature_permission_id,
    is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
    created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
)
SELECT '00000000-0000-0000-0000-000000000903', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-00000000050a',
       TRUE, FALSE, FALSE, FALSE, TRUE, FALSE,
       TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00', NULL, NULL, NULL, NULL
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."20_lnk_role_feature_permissions" WHERE role_id = '00000000-0000-0000-0000-000000000601' AND feature_permission_id = '00000000-0000-0000-0000-00000000050a');

INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions" (
    id, role_id, feature_permission_id,
    is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
    created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
)
SELECT '00000000-0000-0000-0000-000000000904', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-00000000050b',
       TRUE, FALSE, FALSE, FALSE, TRUE, FALSE,
       TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00', NULL, NULL, NULL, NULL
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."20_lnk_role_feature_permissions" WHERE role_id = '00000000-0000-0000-0000-000000000601' AND feature_permission_id = '00000000-0000-0000-0000-00000000050b');

INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions" (
    id, role_id, feature_permission_id,
    is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
    created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
)
SELECT '00000000-0000-0000-0000-000000000905', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-00000000050c',
       TRUE, FALSE, FALSE, FALSE, TRUE, FALSE,
       TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00', NULL, NULL, NULL, NULL
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."20_lnk_role_feature_permissions" WHERE role_id = '00000000-0000-0000-0000-000000000601' AND feature_permission_id = '00000000-0000-0000-0000-00000000050c');

INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions" (
    id, role_id, feature_permission_id,
    is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
    created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
)
SELECT '00000000-0000-0000-0000-000000000906', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-00000000050d',
       TRUE, FALSE, FALSE, FALSE, TRUE, FALSE,
       TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00', NULL, NULL, NULL, NULL
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."20_lnk_role_feature_permissions" WHERE role_id = '00000000-0000-0000-0000-000000000601' AND feature_permission_id = '00000000-0000-0000-0000-00000000050d');

INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions" (
    id, role_id, feature_permission_id,
    is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
    created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
)
SELECT '00000000-0000-0000-0000-000000000907', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-00000000050e',
       TRUE, FALSE, FALSE, FALSE, TRUE, FALSE,
       TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00', NULL, NULL, NULL, NULL
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."20_lnk_role_feature_permissions" WHERE role_id = '00000000-0000-0000-0000-000000000601' AND feature_permission_id = '00000000-0000-0000-0000-00000000050e');

INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions" (
    id, role_id, feature_permission_id,
    is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
    created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
)
SELECT '00000000-0000-0000-0000-000000000908', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-00000000050f',
       TRUE, FALSE, FALSE, FALSE, TRUE, FALSE,
       TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00', NULL, NULL, NULL, NULL
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."20_lnk_role_feature_permissions" WHERE role_id = '00000000-0000-0000-0000-000000000601' AND feature_permission_id = '00000000-0000-0000-0000-00000000050f');

INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions" (
    id, role_id, feature_permission_id,
    is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
    created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
)
SELECT '00000000-0000-0000-0000-000000000909', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000510',
       TRUE, FALSE, FALSE, FALSE, TRUE, FALSE,
       TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00', NULL, NULL, NULL, NULL
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."20_lnk_role_feature_permissions" WHERE role_id = '00000000-0000-0000-0000-000000000601' AND feature_permission_id = '00000000-0000-0000-0000-000000000510');

INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions" (
    id, role_id, feature_permission_id,
    is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
    created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
)
SELECT '00000000-0000-0000-0000-00000000090a', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000511',
       TRUE, FALSE, FALSE, FALSE, TRUE, FALSE,
       TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00', NULL, NULL, NULL, NULL
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."20_lnk_role_feature_permissions" WHERE role_id = '00000000-0000-0000-0000-000000000601' AND feature_permission_id = '00000000-0000-0000-0000-000000000511');

INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions" (
    id, role_id, feature_permission_id,
    is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
    created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
)
SELECT '00000000-0000-0000-0000-00000000090b', '00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000512',
       TRUE, FALSE, FALSE, FALSE, TRUE, FALSE,
       TIMESTAMP '2026-03-13 00:00:00', TIMESTAMP '2026-03-13 00:00:00', NULL, NULL, NULL, NULL
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."20_lnk_role_feature_permissions" WHERE role_id = '00000000-0000-0000-0000-000000000601' AND feature_permission_id = '00000000-0000-0000-0000-000000000512');

CREATE INDEX IF NOT EXISTS idx_03_auth_manage_14_dim_feature_flags_category
    ON "03_auth_manage"."14_dim_feature_flags" (feature_flag_category_code, code);

CREATE INDEX IF NOT EXISTS idx_03_auth_manage_15_dim_feature_permissions_feature
    ON "03_auth_manage"."15_dim_feature_permissions" (feature_flag_code, permission_action_code);

CREATE INDEX IF NOT EXISTS idx_03_auth_manage_18_lnk_group_memberships_user
    ON "03_auth_manage"."18_lnk_group_memberships" (user_id, is_deleted, is_disabled);

CREATE INDEX IF NOT EXISTS idx_03_auth_manage_19_lnk_group_role_assignments_group
    ON "03_auth_manage"."19_lnk_group_role_assignments" (group_id, is_deleted, is_disabled);

CREATE INDEX IF NOT EXISTS idx_03_auth_manage_20_lnk_role_feature_permissions_role
    ON "03_auth_manage"."20_lnk_role_feature_permissions" (role_id, is_deleted, is_disabled);

CREATE INDEX IF NOT EXISTS idx_03_auth_manage_21_trx_access_context_events_user_session
    ON "03_auth_manage"."21_trx_access_context_events" (user_id, session_id, occurred_at);

CREATE OR REPLACE VIEW "03_auth_manage"."23_vw_feature_flag_catalog" AS
SELECT
    flag.id AS feature_flag_id,
    flag.code AS feature_flag_code,
    flag.name AS feature_flag_name,
    flag.description AS feature_flag_description,
    flag.feature_flag_category_code,
    category.name AS feature_flag_category_name,
    flag.access_mode,
    flag.lifecycle_state,
    flag.initial_audience,
    flag.env_dev,
    flag.env_staging,
    flag.env_prod,
    flag.created_at,
    flag.updated_at
FROM "03_auth_manage"."14_dim_feature_flags" AS flag
JOIN "03_auth_manage"."11_dim_feature_flag_categories" AS category
  ON category.code = flag.feature_flag_category_code;

CREATE OR REPLACE VIEW "03_auth_manage"."24_vw_role_feature_action_matrix" AS
SELECT
    role_row.id AS role_id,
    role_row.tenant_key,
    role_row.role_level_code,
    role_row.code AS role_code,
    role_row.name AS role_name,
    role_row.description AS role_description,
    role_row.is_active,
    role_row.is_disabled,
    role_row.is_deleted,
    permission_row.id AS feature_permission_id,
    permission_row.code AS feature_permission_code,
    permission_row.feature_flag_code,
    permission_row.permission_action_code
FROM "03_auth_manage"."16_fct_roles" AS role_row
LEFT JOIN "03_auth_manage"."20_lnk_role_feature_permissions" AS role_permission
  ON role_permission.role_id = role_row.id
 AND role_permission.is_deleted = FALSE
 AND role_permission.is_disabled = FALSE
LEFT JOIN "03_auth_manage"."15_dim_feature_permissions" AS permission_row
  ON permission_row.id = role_permission.feature_permission_id
WHERE role_row.is_deleted = FALSE;

CREATE OR REPLACE VIEW "03_auth_manage"."25_vw_group_membership_directory" AS
SELECT
    group_row.id AS group_id,
    group_row.tenant_key,
    group_row.role_level_code,
    group_row.code AS group_code,
    group_row.name AS group_name,
    group_row.description AS group_description,
    group_row.is_active,
    group_row.is_disabled,
    group_row.is_deleted,
    membership.id AS membership_id,
    membership.user_id,
    membership.membership_status,
    role_assignment.id AS group_role_assignment_id,
    role_assignment.role_id
FROM "03_auth_manage"."17_fct_user_groups" AS group_row
LEFT JOIN "03_auth_manage"."18_lnk_group_memberships" AS membership
  ON membership.group_id = group_row.id
 AND membership.is_deleted = FALSE
 AND membership.is_disabled = FALSE
LEFT JOIN "03_auth_manage"."19_lnk_group_role_assignments" AS role_assignment
  ON role_assignment.group_id = group_row.id
 AND role_assignment.is_deleted = FALSE
 AND role_assignment.is_disabled = FALSE
WHERE group_row.is_deleted = FALSE;

CREATE OR REPLACE VIEW "03_auth_manage"."26_vw_effective_user_feature_access" AS
SELECT
    membership.user_id,
    group_row.tenant_key,
    role_row.role_level_code,
    permission_row.feature_flag_code,
    permission_row.permission_action_code
FROM "03_auth_manage"."18_lnk_group_memberships" AS membership
JOIN "03_auth_manage"."17_fct_user_groups" AS group_row
  ON group_row.id = membership.group_id
 AND group_row.is_deleted = FALSE
 AND group_row.is_disabled = FALSE
JOIN "03_auth_manage"."19_lnk_group_role_assignments" AS group_role
  ON group_role.group_id = group_row.id
 AND group_role.is_deleted = FALSE
 AND group_role.is_disabled = FALSE
JOIN "03_auth_manage"."16_fct_roles" AS role_row
  ON role_row.id = group_role.role_id
 AND role_row.is_deleted = FALSE
 AND role_row.is_disabled = FALSE
JOIN "03_auth_manage"."20_lnk_role_feature_permissions" AS role_permission
  ON role_permission.role_id = role_row.id
 AND role_permission.is_deleted = FALSE
 AND role_permission.is_disabled = FALSE
JOIN "03_auth_manage"."15_dim_feature_permissions" AS permission_row
  ON permission_row.id = role_permission.feature_permission_id
WHERE membership.is_deleted = FALSE
  AND membership.is_disabled = FALSE;
