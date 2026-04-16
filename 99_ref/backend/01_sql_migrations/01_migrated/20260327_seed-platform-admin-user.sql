-- ─────────────────────────────────────────────────────────────────────────────
-- PLATFORM ADMIN USER SEED
-- Seeds admin@kreesalis.com with:
--   - platform_super_admin group membership
--   - Kreesalis org (company type, internal license)
--   - K-Control workspace (project type)
--   - K-Control Sandbox workspace (sandbox type)
--   - Owner memberships on org + both workspaces
--   - Onboarding/OTP/email verification pre-completed
-- Idempotent: all INSERTs use ON CONFLICT DO NOTHING.
-- Runs in every environment (dev, staging, production).
-- ─────────────────────────────────────────────────────────────────────────────

-- Fixed UUIDs for deterministic, idempotent seeding
-- User:              00000000-0000-0000-0000-000000000001
-- Account:           00000000-0000-0000-0000-000000000002
-- Org:               00000000-0000-0000-0000-000000000010
-- K-Control WS:      00000000-0000-0000-0000-000000000011
-- Sandbox WS:        00000000-0000-0000-0000-000000000012

-- 1. Create the user record
INSERT INTO "03_auth_manage"."03_fct_users" (
    id, tenant_key, user_code, account_status,
    is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
    created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
) VALUES (
    '00000000-0000-0000-0000-000000000001',
    'default',
    'ADMIN-0001',
    'active',
    TRUE, FALSE, FALSE, FALSE, TRUE, FALSE,
    NOW(), NOW(), NULL, NULL, NULL, NULL
) ON CONFLICT (id) DO NOTHING;

-- 2. Seed user properties (email, username, display_name)
INSERT INTO "03_auth_manage"."05_dtl_user_properties" (id, user_id, property_key, property_value, created_at, updated_at, created_by, updated_by)
VALUES
    (gen_random_uuid(), '00000000-0000-0000-0000-000000000001', 'email',          'admin@kreesalis.com',  NOW(), NOW(), NULL, NULL),
    (gen_random_uuid(), '00000000-0000-0000-0000-000000000001', 'username',       'admin',                NOW(), NOW(), NULL, NULL),
    (gen_random_uuid(), '00000000-0000-0000-0000-000000000001', 'display_name',   'Platform Admin',       NOW(), NOW(), NULL, NULL),
    (gen_random_uuid(), '00000000-0000-0000-0000-000000000001', 'email_verified',      'true',                 NOW(), NOW(), NULL, NULL),
    (gen_random_uuid(), '00000000-0000-0000-0000-000000000001', 'otp_verified',        'true',                 NOW(), NOW(), NULL, NULL),
    (gen_random_uuid(), '00000000-0000-0000-0000-000000000001', 'onboarding_complete', 'true',                                        NOW(), NOW(), NULL, NULL),
    (gen_random_uuid(), '00000000-0000-0000-0000-000000000001', 'first_name',          'Platform',                                    NOW(), NOW(), NULL, NULL),
    (gen_random_uuid(), '00000000-0000-0000-0000-000000000001', 'last_name',           'Admin',                                       NOW(), NOW(), NULL, NULL),
    (gen_random_uuid(), '00000000-0000-0000-0000-000000000001', 'default_org_id',      '00000000-0000-0000-0000-000000000010',         NOW(), NOW(), NULL, NULL),
    (gen_random_uuid(), '00000000-0000-0000-0000-000000000001', 'default_workspace_id','00000000-0000-0000-0000-000000000011',         NOW(), NOW(), NULL, NULL)
ON CONFLICT (user_id, property_key) DO NOTHING;

-- 3. Create the local_password account
INSERT INTO "03_auth_manage"."08_dtl_user_accounts" (
    id, user_id, tenant_key, account_type_code, is_primary,
    is_active, is_disabled, is_deleted, is_locked,
    created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
) VALUES (
    '00000000-0000-0000-0000-000000000002',
    '00000000-0000-0000-0000-000000000001',
    'default',
    'local_password',
    TRUE,
    TRUE, FALSE, FALSE, FALSE,
    NOW(), NOW(), NULL, NULL, NULL, NULL
) ON CONFLICT (user_id, account_type_code) DO NOTHING;

-- 4. Store the password hash (Argon2id)
--    Password: K0ntr0l!@#2026$ecure
INSERT INTO "03_auth_manage"."09_dtl_user_account_properties" (
    id, user_account_id, property_key, property_value, created_at, updated_at
) VALUES (
    gen_random_uuid(),
    '00000000-0000-0000-0000-000000000002',
    'password_hash',
    '$argon2id$v=19$m=65536,t=3,p=4$R/qslbQMy5BHIxhSRU9LHA$fTQxzooGIhdDdDi9hAIrOXEoayXOfn4SdW5iizDqICw',
    NOW(), NOW()
) ON CONFLICT (user_account_id, property_key) DO NOTHING;

-- 5. Add to platform_super_admin group
INSERT INTO "03_auth_manage"."18_lnk_group_memberships" (
    id, user_id, group_id,
    membership_status, effective_from, effective_to,
    is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
    created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
)
SELECT
    gen_random_uuid(),
    '00000000-0000-0000-0000-000000000001',
    '00000000-0000-0000-0000-000000000701',
    'active', NOW(), NULL,
    TRUE, FALSE, FALSE, FALSE, TRUE, FALSE,
    NOW(), NOW(), NULL, NULL, NULL, NULL
WHERE NOT EXISTS (
    SELECT 1 FROM "03_auth_manage"."18_lnk_group_memberships"
    WHERE user_id = '00000000-0000-0000-0000-000000000001'
      AND group_id = '00000000-0000-0000-0000-000000000701'
      AND is_deleted = FALSE
);

-- 6. Create Kreesalis org
INSERT INTO "03_auth_manage"."29_fct_orgs" (
    id, tenant_key, org_type_code, code, name, description,
    is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
    created_at, updated_at, created_by, updated_by
) VALUES (
    '00000000-0000-0000-0000-000000000010',
    'default', 'company', 'kreesalis', 'Kreesalis', 'Platform admin organization',
    TRUE, FALSE, FALSE, FALSE, TRUE, FALSE,
    NOW(), NOW(), '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000001'
) ON CONFLICT (id) DO NOTHING;

-- 7. Org membership (owner)
INSERT INTO "03_auth_manage"."31_lnk_org_memberships" (
    id, user_id, org_id, membership_type, membership_status, effective_from,
    is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
    created_at, updated_at, created_by, updated_by
)
SELECT
    gen_random_uuid(),
    '00000000-0000-0000-0000-000000000001',
    '00000000-0000-0000-0000-000000000010',
    'owner', 'active', NOW(),
    TRUE, FALSE, FALSE, FALSE, TRUE, FALSE,
    NOW(), NOW(), '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000001'
WHERE NOT EXISTS (
    SELECT 1 FROM "03_auth_manage"."31_lnk_org_memberships"
    WHERE user_id = '00000000-0000-0000-0000-000000000001'
      AND org_id = '00000000-0000-0000-0000-000000000010'
      AND is_deleted = FALSE
);

-- 8. K-Control workspace (project type)
INSERT INTO "03_auth_manage"."34_fct_workspaces" (
    id, org_id, workspace_type_code, product_id, code, name, description,
    is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
    created_at, updated_at, created_by, updated_by
) VALUES (
    '00000000-0000-0000-0000-000000000011',
    '00000000-0000-0000-0000-000000000010',
    'project',
    '00000000-0000-0000-0000-000000001201',
    'kreesalis-kcontrol', 'K-Control', 'Primary K-Control compliance workspace',
    TRUE, FALSE, FALSE, FALSE, TRUE, FALSE,
    NOW(), NOW(), '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000001'
) ON CONFLICT (id) DO NOTHING;

-- 9. K-Control Sandbox workspace (sandbox type)
INSERT INTO "03_auth_manage"."34_fct_workspaces" (
    id, org_id, workspace_type_code, product_id, code, name, description,
    is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
    created_at, updated_at, created_by, updated_by
) VALUES (
    '00000000-0000-0000-0000-000000000012',
    '00000000-0000-0000-0000-000000000010',
    'sandbox',
    '00000000-0000-0000-0000-000000001202',
    'kreesalis-sandbox', 'K-Control Sandbox', 'Sandboxed testing instance of K-Control',
    TRUE, FALSE, FALSE, FALSE, TRUE, FALSE,
    NOW(), NOW(), '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000001'
) ON CONFLICT (id) DO NOTHING;

-- 10. Workspace memberships (owner on both)
INSERT INTO "03_auth_manage"."36_lnk_workspace_memberships" (
    id, user_id, workspace_id, membership_type, membership_status, effective_from,
    is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
    created_at, updated_at, created_by, updated_by
)
SELECT
    gen_random_uuid(),
    '00000000-0000-0000-0000-000000000001',
    ws.id,
    'owner', 'active', NOW(),
    TRUE, FALSE, FALSE, FALSE, TRUE, FALSE,
    NOW(), NOW(), '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000001'
FROM (VALUES
    ('00000000-0000-0000-0000-000000000011'::uuid),
    ('00000000-0000-0000-0000-000000000012'::uuid)
) AS ws(id)
WHERE NOT EXISTS (
    SELECT 1 FROM "03_auth_manage"."36_lnk_workspace_memberships" m
    WHERE m.user_id = '00000000-0000-0000-0000-000000000001'
      AND m.workspace_id = ws.id
      AND m.is_deleted = FALSE
);

-- 11. Org license tier (internal = no limits)
INSERT INTO "03_auth_manage"."30_dtl_org_settings" (
    id, org_id, setting_key, setting_value, created_at, updated_at
) VALUES (
    gen_random_uuid(),
    '00000000-0000-0000-0000-000000000010',
    'license_tier', 'internal',
    NOW(), NOW()
) ON CONFLICT ON CONSTRAINT uq_30_dtl_org_settings_key DO UPDATE
  SET setting_value = 'internal', updated_at = NOW();
