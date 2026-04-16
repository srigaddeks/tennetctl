-- Assign user_impersonation.enable and user_impersonation.view permissions
-- to the platform_super_admin role so super admins can use impersonation.

INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions" (
    id, role_id, feature_permission_id, created_at, updated_at
)
SELECT
    gen_random_uuid(),
    '00000000-0000-0000-0000-000000000601',
    '00000000-0000-0000-0000-000000000520',
    NOW(), NOW()
WHERE NOT EXISTS (
    SELECT 1 FROM "03_auth_manage"."20_lnk_role_feature_permissions"
    WHERE role_id = '00000000-0000-0000-0000-000000000601'
      AND feature_permission_id = '00000000-0000-0000-0000-000000000520'
);

INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions" (
    id, role_id, feature_permission_id, created_at, updated_at
)
SELECT
    gen_random_uuid(),
    '00000000-0000-0000-0000-000000000601',
    '00000000-0000-0000-0000-000000000521',
    NOW(), NOW()
WHERE NOT EXISTS (
    SELECT 1 FROM "03_auth_manage"."20_lnk_role_feature_permissions"
    WHERE role_id = '00000000-0000-0000-0000-000000000601'
      AND feature_permission_id = '00000000-0000-0000-0000-000000000521'
);
