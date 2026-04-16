-- ─────────────────────────────────────────────────────────────────────────
-- Migration: add-passwordless-auth
-- Adds magic link authentication support, external_collaborator user
-- category, seeded role/group, and max_external_users license limits.
-- ─────────────────────────────────────────────────────────────────────────

-- ═══════════════════════════════════════════════════════════════════════
-- 0. Ensure 'platform' role level exists (seeded here for test environments
--    where seed-org-workspace-system-roles.sql may not be present)
-- ═══════════════════════════════════════════════════════════════════════

INSERT INTO "03_auth_manage"."13_dim_role_levels" (id, code, name, description, sort_order, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000000304', 'platform', 'Platform', 'Platform-wide non-admin scope.', 5, NOW(), NOW()
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."13_dim_role_levels" WHERE code = 'platform');

-- ═══════════════════════════════════════════════════════════════════════
-- 1. Add user_category column to 03_fct_users
-- ═══════════════════════════════════════════════════════════════════════

ALTER TABLE "03_auth_manage"."03_fct_users"
    ADD COLUMN IF NOT EXISTS user_category VARCHAR(50) NOT NULL DEFAULT 'full';

ALTER TABLE "03_auth_manage"."03_fct_users"
    DROP CONSTRAINT IF EXISTS ck_03_fct_users_user_category;

ALTER TABLE "03_auth_manage"."03_fct_users"
    ADD CONSTRAINT ck_03_fct_users_user_category
        CHECK (user_category IN ('full', 'external_collaborator'));

CREATE INDEX IF NOT EXISTS idx_03_fct_users_user_category
    ON "03_auth_manage"."03_fct_users" (tenant_key, user_category)
    WHERE is_deleted = FALSE;

-- ═══════════════════════════════════════════════════════════════════════
-- 2. Seed magic_link account type into 06_dim_account_types
-- ═══════════════════════════════════════════════════════════════════════

INSERT INTO "03_auth_manage"."06_dim_account_types"
    (id, code, name, description, sort_order, created_at, updated_at)
SELECT '00000000-0000-0000-0002-000000000007',
       'magic_link',
       'Magic Link',
       'Passwordless authentication via one-time email link',
       70,
       NOW(), NOW()
WHERE NOT EXISTS (
    SELECT 1 FROM "03_auth_manage"."06_dim_account_types" WHERE code = 'magic_link'
);

-- ═══════════════════════════════════════════════════════════════════════
-- 3. Seed magic_link challenge type into 02_dim_challenge_types
-- ═══════════════════════════════════════════════════════════════════════

INSERT INTO "03_auth_manage"."02_dim_challenge_types"
    (id, code, name, description, sort_order, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000000013',
       'magic_link',
       'Magic Link',
       'One-time passwordless login challenge sent via email',
       30,
       NOW(), NOW()
WHERE NOT EXISTS (
    SELECT 1 FROM "03_auth_manage"."02_dim_challenge_types" WHERE code = 'magic_link'
);

-- ═══════════════════════════════════════════════════════════════════════
-- 4. Seed user_category_source property key into 04_dim_user_property_keys
-- ═══════════════════════════════════════════════════════════════════════

INSERT INTO "03_auth_manage"."04_dim_user_property_keys"
    (id, code, name, description, data_type, is_pii, is_required, sort_order, created_at, updated_at)
SELECT '00000000-0000-0000-0001-000000000020',
       'user_category_source',
       'User Category Source',
       'Indicates how the user''s category was determined (e.g. magic_link_invite, manual)',
       'string',
       FALSE,
       FALSE,
       200,
       NOW(), NOW()
WHERE NOT EXISTS (
    SELECT 1 FROM "03_auth_manage"."04_dim_user_property_keys" WHERE code = 'user_category_source'
);

-- ═══════════════════════════════════════════════════════════════════════
-- 5. Seed external_collaborator role into 16_fct_roles
-- ═══════════════════════════════════════════════════════════════════════

INSERT INTO "03_auth_manage"."16_fct_roles" (
    id, tenant_key, role_level_code, code, name, description,
    scope_org_id, scope_workspace_id,
    is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
    created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
)
SELECT
    gen_random_uuid(), 'default', 'platform', 'external_collaborator',
    'External Collaborator',
    'Limited platform role for external users who authenticate via magic link. Grants read-only access to tasks, comments, and attachments.',
    NULL, NULL,
    TRUE, FALSE, FALSE, FALSE, TRUE, TRUE,
    NOW(), NOW(), NULL, NULL, NULL, NULL
WHERE NOT EXISTS (
    SELECT 1 FROM "03_auth_manage"."16_fct_roles"
    WHERE code = 'external_collaborator' AND tenant_key = 'default'
);

-- ═══════════════════════════════════════════════════════════════════════
-- 6. Seed external_collaborators group into 17_fct_user_groups
-- ═══════════════════════════════════════════════════════════════════════

INSERT INTO "03_auth_manage"."17_fct_user_groups" (
    id, tenant_key, role_level_code, code, name, description,
    scope_org_id, scope_workspace_id,
    is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
    created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
)
SELECT
    gen_random_uuid(), 'default', 'platform', 'external_collaborators',
    'External Collaborators',
    'System group for all external collaborator users. Automatically enrolled when a user authenticates via magic link for the first time.',
    NULL, NULL,
    TRUE, FALSE, FALSE, FALSE, TRUE, TRUE,
    NOW(), NOW(), NULL, NULL, NULL, NULL
WHERE NOT EXISTS (
    SELECT 1 FROM "03_auth_manage"."17_fct_user_groups"
    WHERE code = 'external_collaborators' AND tenant_key = 'default'
);

-- ═══════════════════════════════════════════════════════════════════════
-- 7. Link external_collaborators group → external_collaborator role
-- ═══════════════════════════════════════════════════════════════════════

INSERT INTO "03_auth_manage"."19_lnk_group_role_assignments" (
    id, group_id, role_id,
    assignment_status, effective_from, effective_to,
    is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
    created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
)
SELECT
    gen_random_uuid(),
    g.id,
    r.id,
    'active', NOW(), NULL,
    TRUE, FALSE, FALSE, FALSE, TRUE, TRUE,
    NOW(), NOW(), NULL, NULL, NULL, NULL
FROM "03_auth_manage"."17_fct_user_groups" g
CROSS JOIN "03_auth_manage"."16_fct_roles" r
WHERE g.code = 'external_collaborators' AND g.tenant_key = 'default'
  AND r.code = 'external_collaborator'  AND r.tenant_key = 'default'
  AND NOT EXISTS (
      SELECT 1
      FROM "03_auth_manage"."19_lnk_group_role_assignments" lnk
      WHERE lnk.group_id = g.id AND lnk.role_id = r.id
  );

-- ═══════════════════════════════════════════════════════════════════════
-- 8. Assign permissions to external_collaborator role
--    tasks.view, comments.view, comments.create, attachments.view, attachments.create
-- ═══════════════════════════════════════════════════════════════════════

INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions" (
    id, role_id, feature_permission_id, created_at, updated_at
)
SELECT
    gen_random_uuid(),
    r.id,
    fp.id,
    NOW(), NOW()
FROM "03_auth_manage"."16_fct_roles" r
CROSS JOIN "03_auth_manage"."15_dim_feature_permissions" fp
WHERE r.code = 'external_collaborator' AND r.tenant_key = 'default'
  AND fp.code IN (
      'tasks.view',
      'comments.view',
      'comments.create',
      'attachments.view',
      'attachments.create'
  )
ON CONFLICT DO NOTHING;

-- ═══════════════════════════════════════════════════════════════════════
-- 9. Seed max_external_users into 38_dtl_license_profile_settings
-- ═══════════════════════════════════════════════════════════════════════

-- free_default: 10 external users
INSERT INTO "03_auth_manage"."38_dtl_license_profile_settings"
    (profile_id, setting_key, setting_value, created_at, updated_at)
SELECT p.id, 'max_external_users', '10', NOW(), NOW()
FROM "03_auth_manage"."37_fct_license_profiles" p
WHERE p.code = 'free_default'
  AND NOT EXISTS (
      SELECT 1 FROM "03_auth_manage"."38_dtl_license_profile_settings"
      WHERE profile_id = p.id AND setting_key = 'max_external_users'
  );

-- pro_default: 100 external users
INSERT INTO "03_auth_manage"."38_dtl_license_profile_settings"
    (profile_id, setting_key, setting_value, created_at, updated_at)
SELECT p.id, 'max_external_users', '100', NOW(), NOW()
FROM "03_auth_manage"."37_fct_license_profiles" p
WHERE p.code = 'pro_default'
  AND NOT EXISTS (
      SELECT 1 FROM "03_auth_manage"."38_dtl_license_profile_settings"
      WHERE profile_id = p.id AND setting_key = 'max_external_users'
  );

-- pro_trial_default: 100 external users
INSERT INTO "03_auth_manage"."38_dtl_license_profile_settings"
    (profile_id, setting_key, setting_value, created_at, updated_at)
SELECT p.id, 'max_external_users', '100', NOW(), NOW()
FROM "03_auth_manage"."37_fct_license_profiles" p
WHERE p.code = 'pro_trial_default'
  AND NOT EXISTS (
      SELECT 1 FROM "03_auth_manage"."38_dtl_license_profile_settings"
      WHERE profile_id = p.id AND setting_key = 'max_external_users'
  );

-- enterprise_default: 500 external users
INSERT INTO "03_auth_manage"."38_dtl_license_profile_settings"
    (profile_id, setting_key, setting_value, created_at, updated_at)
SELECT p.id, 'max_external_users', '500', NOW(), NOW()
FROM "03_auth_manage"."37_fct_license_profiles" p
WHERE p.code = 'enterprise_default'
  AND NOT EXISTS (
      SELECT 1 FROM "03_auth_manage"."38_dtl_license_profile_settings"
      WHERE profile_id = p.id AND setting_key = 'max_external_users'
  );

-- partner_default: 50 external users
INSERT INTO "03_auth_manage"."38_dtl_license_profile_settings"
    (profile_id, setting_key, setting_value, created_at, updated_at)
SELECT p.id, 'max_external_users', '50', NOW(), NOW()
FROM "03_auth_manage"."37_fct_license_profiles" p
WHERE p.code = 'partner_default'
  AND NOT EXISTS (
      SELECT 1 FROM "03_auth_manage"."38_dtl_license_profile_settings"
      WHERE profile_id = p.id AND setting_key = 'max_external_users'
  );

-- internal_default: no limit (999999)
INSERT INTO "03_auth_manage"."38_dtl_license_profile_settings"
    (profile_id, setting_key, setting_value, created_at, updated_at)
SELECT p.id, 'max_external_users', '999999', NOW(), NOW()
FROM "03_auth_manage"."37_fct_license_profiles" p
WHERE p.code = 'internal_default'
  AND NOT EXISTS (
      SELECT 1 FROM "03_auth_manage"."38_dtl_license_profile_settings"
      WHERE profile_id = p.id AND setting_key = 'max_external_users'
  );

-- ═══════════════════════════════════════════════════════════════════════
-- 10. Update 42_vw_auth_users view to include user_category
-- ═══════════════════════════════════════════════════════════════════════

CREATE OR REPLACE VIEW "03_auth_manage"."42_vw_auth_users" AS
SELECT
    u.id AS user_id,
    u.tenant_key AS tenant_key,
    email_prop.property_value AS email,
    username_prop.property_value AS username,
    COALESCE(email_verified_prop.property_value, 'false') AS email_verified,
    u.account_status AS account_status,
    u.user_category AS user_category
FROM "03_auth_manage"."03_fct_users" AS u
LEFT JOIN "03_auth_manage"."05_dtl_user_properties" AS email_prop
    ON email_prop.user_id = u.id AND email_prop.property_key = 'email'
LEFT JOIN "03_auth_manage"."05_dtl_user_properties" AS username_prop
    ON username_prop.user_id = u.id AND username_prop.property_key = 'username'
LEFT JOIN "03_auth_manage"."05_dtl_user_properties" AS email_verified_prop
    ON email_verified_prop.user_id = u.id AND email_verified_prop.property_key = 'email_verified'
WHERE u.is_deleted = FALSE
  AND u.is_test = FALSE;

COMMENT ON VIEW "03_auth_manage"."42_vw_auth_users" IS 'Read view for the current user profile built from EAV user properties.';
