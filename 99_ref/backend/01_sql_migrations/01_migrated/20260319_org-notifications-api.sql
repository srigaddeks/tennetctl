-- Migration: Org-level notifications API
-- Adds org_broadcasts feature flag so org admins can be granted broadcast permissions.
-- Seeds view/create permissions and assigns them to org owner and admin roles.

DO $$
DECLARE
    v_perm_view   UUID;
    v_perm_create UUID;
    v_cat_code    VARCHAR(50);
BEGIN
    -- ------------------------------------------------------------------ --
    -- 1. Feature flag: org_broadcasts (org-scoped)
    -- ------------------------------------------------------------------ --
    -- Find notifications category, fallback to first available
    SELECT code INTO v_cat_code
    FROM "03_auth_manage"."11_dim_feature_flag_categories"
    WHERE code = 'notifications'
    LIMIT 1;

    IF v_cat_code IS NULL THEN
        SELECT code INTO v_cat_code
        FROM "03_auth_manage"."11_dim_feature_flag_categories"
        LIMIT 1;
    END IF;

    INSERT INTO "03_auth_manage"."14_dim_feature_flags"
        (id, code, name, description, feature_scope, feature_flag_category_code,
         access_mode, lifecycle_state, initial_audience,
         env_dev, env_staging, env_prod, created_at, updated_at)
    SELECT
        '00000000-0000-0000-0000-000000002101'::uuid,
        'org_broadcasts',
        'Org Broadcasts',
        'Allows org admins to view and create broadcasts scoped to their organization.',
        'org',
        v_cat_code,
        'permissioned', 'active', 'all',
        TRUE, TRUE, TRUE,
        NOW(), NOW()
    WHERE NOT EXISTS (
        SELECT 1 FROM "03_auth_manage"."14_dim_feature_flags"
        WHERE code = 'org_broadcasts'
    );

    -- ------------------------------------------------------------------ --
    -- 2. Feature permissions: org_broadcasts.view / org_broadcasts.create
    -- ------------------------------------------------------------------ --
    INSERT INTO "03_auth_manage"."15_dim_feature_permissions"
        (id, code, feature_flag_code, permission_action_code, name, description,
         created_at, updated_at)
    SELECT
        '00000000-0000-0000-0000-000000002102'::uuid,
        'org_broadcasts.view',
        'org_broadcasts',
        'view',
        'View Org Broadcasts',
        'Can view broadcasts and incidents scoped to their organization.',
        NOW(), NOW()
    WHERE NOT EXISTS (
        SELECT 1 FROM "03_auth_manage"."15_dim_feature_permissions"
        WHERE code = 'org_broadcasts.view'
    );

    INSERT INTO "03_auth_manage"."15_dim_feature_permissions"
        (id, code, feature_flag_code, permission_action_code, name, description,
         created_at, updated_at)
    SELECT
        '00000000-0000-0000-0000-000000002103'::uuid,
        'org_broadcasts.create',
        'org_broadcasts',
        'create',
        'Create Org Broadcasts',
        'Can create and send broadcasts scoped to their organization.',
        NOW(), NOW()
    WHERE NOT EXISTS (
        SELECT 1 FROM "03_auth_manage"."15_dim_feature_permissions"
        WHERE code = 'org_broadcasts.create'
    );

    SELECT id INTO v_perm_view   FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'org_broadcasts.view';
    SELECT id INTO v_perm_create FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'org_broadcasts.create';

    -- ------------------------------------------------------------------ --
    -- 3. Assign to org-scoped built-in roles: owner + admin
    -- ------------------------------------------------------------------ --
    -- Assign view + create to org_owner
    IF v_perm_view IS NOT NULL THEN
        INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
            (id, role_id, feature_permission_id, is_active, is_disabled, is_deleted, is_test, is_system, is_locked, created_at, updated_at, created_by, updated_by)
        SELECT gen_random_uuid(), r.id, v_perm_view,
               TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, NOW(), NOW(), NULL, NULL
        FROM "03_auth_manage"."16_fct_roles" r
        WHERE r.code = 'org_owner'
        AND NOT EXISTS (
            SELECT 1 FROM "03_auth_manage"."20_lnk_role_feature_permissions"
            WHERE role_id = r.id AND feature_permission_id = v_perm_view
        );
    END IF;

    IF v_perm_create IS NOT NULL THEN
        INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
            (id, role_id, feature_permission_id, is_active, is_disabled, is_deleted, is_test, is_system, is_locked, created_at, updated_at, created_by, updated_by)
        SELECT gen_random_uuid(), r.id, v_perm_create,
               TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, NOW(), NOW(), NULL, NULL
        FROM "03_auth_manage"."16_fct_roles" r
        WHERE r.code = 'org_owner'
        AND NOT EXISTS (
            SELECT 1 FROM "03_auth_manage"."20_lnk_role_feature_permissions"
            WHERE role_id = r.id AND feature_permission_id = v_perm_create
        );
    END IF;

    -- Assign view + create to org_admin
    IF v_perm_view IS NOT NULL THEN
        INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
            (id, role_id, feature_permission_id, is_active, is_disabled, is_deleted, is_test, is_system, is_locked, created_at, updated_at, created_by, updated_by)
        SELECT gen_random_uuid(), r.id, v_perm_view,
               TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, NOW(), NOW(), NULL, NULL
        FROM "03_auth_manage"."16_fct_roles" r
        WHERE r.code = 'org_admin'
        AND NOT EXISTS (
            SELECT 1 FROM "03_auth_manage"."20_lnk_role_feature_permissions"
            WHERE role_id = r.id AND feature_permission_id = v_perm_view
        );
    END IF;

    IF v_perm_create IS NOT NULL THEN
        INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
            (id, role_id, feature_permission_id, is_active, is_disabled, is_deleted, is_test, is_system, is_locked, created_at, updated_at, created_by, updated_by)
        SELECT gen_random_uuid(), r.id, v_perm_create,
               TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, NOW(), NOW(), NULL, NULL
        FROM "03_auth_manage"."16_fct_roles" r
        WHERE r.code = 'org_admin'
        AND NOT EXISTS (
            SELECT 1 FROM "03_auth_manage"."20_lnk_role_feature_permissions"
            WHERE role_id = r.id AND feature_permission_id = v_perm_create
        );
    END IF;
END $$;
