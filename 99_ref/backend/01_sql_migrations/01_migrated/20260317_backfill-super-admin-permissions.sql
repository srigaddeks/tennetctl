-- Backfill: assign ALL existing feature permissions to platform_super_admin
-- Uses ON CONFLICT DO NOTHING to be fully idempotent.
-- After this runs, every permission that exists in 15_dim_feature_permissions
-- will be linked to platform_super_admin in 20_lnk_role_feature_permissions.

DO $$
DECLARE
    v_role_id uuid;
    v_perm    record;
    v_now     timestamptz := NOW();
BEGIN
    -- Find platform_super_admin role
    SELECT id INTO v_role_id
    FROM "03_auth_manage"."16_fct_roles"
    WHERE code = 'platform_super_admin' AND is_deleted = FALSE
    LIMIT 1;

    IF v_role_id IS NULL THEN
        RAISE NOTICE 'platform_super_admin role not found — skipping backfill';
        RETURN;
    END IF;

    -- Assign every permission not yet linked
    FOR v_perm IN
        SELECT fp.id AS perm_id
        FROM "03_auth_manage"."15_dim_feature_permissions" fp
        WHERE NOT EXISTS (
            SELECT 1
            FROM "03_auth_manage"."20_lnk_role_feature_permissions" lnk
            WHERE lnk.role_id = v_role_id
              AND lnk.feature_permission_id = fp.id
              AND lnk.is_deleted = FALSE
        )
    LOOP
        INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions" (
            id, role_id, feature_permission_id,
            is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
            created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
        )
        VALUES (
            gen_random_uuid(), v_role_id, v_perm.perm_id,
            TRUE, FALSE, FALSE, FALSE, TRUE, TRUE,
            v_now, v_now, v_role_id, v_role_id, NULL, NULL
        )
        ON CONFLICT DO NOTHING;
    END LOOP;

    RAISE NOTICE 'Backfill complete for platform_super_admin (role_id=%)', v_role_id;
END;
$$;
