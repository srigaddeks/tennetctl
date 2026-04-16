-- =============================================================================
-- Migration: 20260402_sync-role-permissions.sql
-- Description: Full upsert of all role-feature permission assignments from dev.
--              551 total links across all roles. Fully idempotent.
-- =============================================================================

-- UP ==========================================================================

DO $$
DECLARE
  v_role_id   UUID;
  v_perm_id   UUID;
BEGIN

  -- basic_user (40 permissions)
  SELECT id INTO v_role_id FROM "03_auth_manage"."16_fct_roles" WHERE code = 'basic_user' AND is_deleted = FALSE LIMIT 1;
  IF v_role_id IS NOT NULL THEN
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'agent_sandbox.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'agent_sandbox.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'ai_copilot.admin' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'ai_copilot.approve' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'ai_copilot.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'ai_copilot.execute' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'ai_copilot.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'ai_evidence_checker.trigger' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'ai_evidence_checker.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'assessments.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'assessments.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'asset_inventory.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'attachments.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'attachments.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'comments.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'comments.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'controls.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'controls.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'docs.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'feedback.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'feedback.delete' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'feedback.update' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'feedback.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'frameworks.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'frameworks.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'global_risk_library.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'global_risk_library.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'risks.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'risks.delete' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'risks.update' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'risks.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'sandbox.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'sandbox.delete' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'sandbox.execute' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'sandbox.promote' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'sandbox.update' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'sandbox.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'tasks.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'tests.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'tests.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
  END IF;

  -- external_collaborator (10 permissions)
  SELECT id INTO v_role_id FROM "03_auth_manage"."16_fct_roles" WHERE code = 'external_collaborator' AND is_deleted = FALSE LIMIT 1;
  IF v_role_id IS NOT NULL THEN
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'ai_copilot.admin' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'ai_copilot.approve' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'ai_copilot.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'ai_copilot.execute' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'ai_copilot.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'attachments.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'attachments.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'comments.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'comments.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'tasks.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
  END IF;

  -- grc_ciso (6 permissions)
  SELECT id INTO v_role_id FROM "03_auth_manage"."16_fct_roles" WHERE code = 'grc_ciso' AND is_deleted = FALSE LIMIT 1;
  IF v_role_id IS NOT NULL THEN
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'assessments.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'controls.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'frameworks.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'grc_role_management.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'risks.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'tasks.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
  END IF;

  -- grc_engineer (8 permissions)
  SELECT id INTO v_role_id FROM "03_auth_manage"."16_fct_roles" WHERE code = 'grc_engineer' AND is_deleted = FALSE LIMIT 1;
  IF v_role_id IS NOT NULL THEN
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'controls.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'frameworks.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'grc_role_management.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'risks.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'tasks.submit' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'tasks.update' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'tasks.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'tests.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
  END IF;

  -- grc_lead_auditor (26 permissions)
  SELECT id INTO v_role_id FROM "03_auth_manage"."16_fct_roles" WHERE code = 'grc_lead_auditor' AND is_deleted = FALSE LIMIT 1;
  IF v_role_id IS NOT NULL THEN
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'assessments.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'assessments.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'audit_workspace_auditor_findings.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'audit_workspace_auditor_findings.update' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'audit_workspace_auditor_findings.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'audit_workspace_auditor_portfolio.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'audit_workspace_auditor_tasks.assign' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'audit_workspace_auditor_tasks.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'audit_workspace_auditor_tasks.update' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'audit_workspace_auditor_tasks.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'audit_workspace_control_access.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'audit_workspace_engagement_membership.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'audit_workspace_evidence_requests.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'audit_workspace_evidence_requests.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'controls.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'findings.close' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'findings.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'findings.update' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'findings.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'frameworks.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'grc_role_management.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'tasks.assign' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'tasks.complete' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'tasks.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'tasks.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'tests.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
  END IF;

  -- grc_practitioner (43 permissions)
  SELECT id INTO v_role_id FROM "03_auth_manage"."16_fct_roles" WHERE code = 'grc_practitioner' AND is_deleted = FALSE LIMIT 1;
  IF v_role_id IS NOT NULL THEN
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'assessments.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'assessments.delete' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'assessments.update' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'assessments.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'controls.admin' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'controls.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'controls.delete' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'controls.edit' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'controls.update' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'controls.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'findings.close' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'findings.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'findings.delete' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'findings.respond' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'findings.update' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'findings.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'frameworks.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'frameworks.delete' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'frameworks.update' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'frameworks.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'grc_role_management.assign' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'grc_role_management.revoke' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'grc_role_management.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'invitation_management.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'invitation_management.revoke' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'invitation_management.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'risks.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'risks.delete' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'risks.update' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'risks.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'tasks.approve' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'tasks.assign' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'tasks.complete' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'tasks.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'tasks.publish' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'tasks.review' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'tasks.submit' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'tasks.update' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'tasks.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'tests.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'tests.delete' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'tests.update' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'tests.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
  END IF;

  -- grc_staff_auditor (20 permissions)
  SELECT id INTO v_role_id FROM "03_auth_manage"."16_fct_roles" WHERE code = 'grc_staff_auditor' AND is_deleted = FALSE LIMIT 1;
  IF v_role_id IS NOT NULL THEN
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'assessments.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'audit_workspace_auditor_findings.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'audit_workspace_auditor_findings.update' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'audit_workspace_auditor_findings.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'audit_workspace_auditor_portfolio.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'audit_workspace_auditor_tasks.assign' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'audit_workspace_auditor_tasks.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'audit_workspace_auditor_tasks.update' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'audit_workspace_auditor_tasks.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'audit_workspace_control_access.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'audit_workspace_engagement_membership.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'audit_workspace_evidence_requests.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'audit_workspace_evidence_requests.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'controls.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'findings.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'findings.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'frameworks.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'grc_role_management.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'tasks.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'tests.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
  END IF;

  -- grc_vendor (1 permissions)
  SELECT id INTO v_role_id FROM "03_auth_manage"."16_fct_roles" WHERE code = 'grc_vendor' AND is_deleted = FALSE LIMIT 1;
  IF v_role_id IS NOT NULL THEN
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'grc_role_management.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
  END IF;

  -- org_admin (111 permissions)
  SELECT id INTO v_role_id FROM "03_auth_manage"."16_fct_roles" WHERE code = 'org_admin' AND is_deleted = FALSE LIMIT 1;
  IF v_role_id IS NOT NULL THEN
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'ai_copilot.approve' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'ai_copilot.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'ai_copilot.execute' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'ai_copilot.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'ai_evidence_checker.trigger' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'ai_evidence_checker.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'assessments.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'assessments.delete' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'assessments.update' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'assessments.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'asset_inventory.collect' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'asset_inventory.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'asset_inventory.delete' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'asset_inventory.update' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'asset_inventory.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'attachments.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'attachments.delete' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'attachments.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'audit_logs_access.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'auth_google_login.enable' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'auth_password_login.enable' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'comments.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'comments.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'controls.admin' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'controls.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'controls.delete' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'controls.edit' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'controls.update' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'controls.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'docs.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'docs.delete' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'docs.enable' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'docs.manage' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'docs.update' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'docs.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'findings.close' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'findings.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'findings.delete' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'findings.respond' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'findings.update' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'findings.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'frameworks.approve' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'frameworks.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'frameworks.delete' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'frameworks.submit' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'frameworks.update' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'frameworks.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'global_risk_library.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'global_risk_library.delete' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'global_risk_library.update' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'global_risk_library.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'grc_role_management.assign' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'grc_role_management.revoke' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'grc_role_management.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'group_access_assignment.assign' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'group_access_assignment.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'group_access_assignment.delete' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'group_access_assignment.revoke' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'group_access_assignment.update' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'group_access_assignment.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'invitation_management.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'invitation_management.revoke' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'invitation_management.update' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'invitation_management.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'org_management.assign' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'org_management.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'org_management.revoke' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'org_management.update' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'org_management.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'policy_management.assign' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'policy_management.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'policy_management.disable' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'policy_management.enable' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'policy_management.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'product_management.assign' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'product_management.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'product_management.revoke' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'product_management.update' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'product_management.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'reports.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'reports.delete' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'reports.enable' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'reports.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'risks.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'risks.delete' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'risks.update' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'risks.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'sandbox.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'sandbox.delete' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'sandbox.execute' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'sandbox.promote' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'sandbox.update' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'sandbox.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'tasks.approve' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'tasks.assign' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'tasks.complete' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'tasks.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'tasks.publish' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'tasks.review' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'tasks.submit' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'tasks.update' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'tasks.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'tests.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'tests.delete' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'tests.update' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'tests.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'workspace_management.assign' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'workspace_management.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'workspace_management.revoke' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'workspace_management.update' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'workspace_management.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
  END IF;

  -- org_member (6 permissions)
  SELECT id INTO v_role_id FROM "03_auth_manage"."16_fct_roles" WHERE code = 'org_member' AND is_deleted = FALSE LIMIT 1;
  IF v_role_id IS NOT NULL THEN
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'org_management.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'workspace_management.assign' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'workspace_management.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'workspace_management.revoke' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'workspace_management.update' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'workspace_management.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
  END IF;

  -- org_viewer (1 permissions)
  SELECT id INTO v_role_id FROM "03_auth_manage"."16_fct_roles" WHERE code = 'org_viewer' AND is_deleted = FALSE LIMIT 1;
  IF v_role_id IS NOT NULL THEN
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'org_management.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
  END IF;

  -- platform_super_admin (165 permissions)
  SELECT id INTO v_role_id FROM "03_auth_manage"."16_fct_roles" WHERE code = 'platform_super_admin' AND is_deleted = FALSE LIMIT 1;
  IF v_role_id IS NOT NULL THEN
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'access_audit_timeline.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'access_governance_console.assign' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'access_governance_console.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'access_governance_console.delete' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'access_governance_console.update' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'access_governance_console.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'admin_console.delete' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'admin_console.update' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'admin_console.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'agent_sandbox.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'agent_sandbox.execute' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'agent_sandbox.manage' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'agent_sandbox.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'ai_copilot.admin' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'ai_copilot.approve' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'ai_copilot.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'ai_copilot.execute' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'ai_copilot.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'api_key_management.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'api_key_management.revoke' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'api_key_management.update' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'api_key_management.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'asset_inventory.collect' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'asset_inventory.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'asset_inventory.delete' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'asset_inventory.update' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'asset_inventory.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'attachments.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'attachments.delete' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'attachments.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'audit_logs_access.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'audit_workspace_auditor_findings.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'audit_workspace_auditor_findings.update' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'audit_workspace_auditor_findings.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'audit_workspace_auditor_portfolio.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'audit_workspace_auditor_tasks.assign' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'audit_workspace_auditor_tasks.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'audit_workspace_auditor_tasks.update' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'audit_workspace_auditor_tasks.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'audit_workspace_control_access.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'audit_workspace_engagement_membership.update' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'audit_workspace_engagement_membership.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'audit_workspace_evidence_requests.approve' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'audit_workspace_evidence_requests.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'audit_workspace_evidence_requests.revoke' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'audit_workspace_evidence_requests.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'auth_google_login.disable' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'auth_google_login.enable' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'auth_password_login.disable' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'auth_password_login.enable' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'comments.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'comments.delete' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'comments.manage' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'comments.resolve' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'comments.update' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'comments.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'controls.admin' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'controls.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'controls.delete' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'controls.edit' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'controls.update' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'controls.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'docs.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'docs.delete' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'docs.enable' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'docs.manage' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'docs.update' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'docs.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'feature_flag_registry.assign' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'feature_flag_registry.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'feature_flag_registry.delete' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'feature_flag_registry.disable' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'feature_flag_registry.enable' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'feature_flag_registry.update' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'feature_flag_registry.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'feedback.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'feedback.delete' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'feedback.manage' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'feedback.update' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'feedback.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'frameworks.approve' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'frameworks.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'frameworks.delete' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'frameworks.submit' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'frameworks.update' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'frameworks.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'global_risk_library.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'global_risk_library.delete' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'global_risk_library.update' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'global_risk_library.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'group_access_assignment.assign' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'group_access_assignment.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'group_access_assignment.delete' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'group_access_assignment.revoke' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'group_access_assignment.update' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'group_access_assignment.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'invitation_management.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'invitation_management.revoke' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'invitation_management.update' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'invitation_management.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'kc_data_pipeline.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'kc_data_pipeline.disable' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'kc_data_pipeline.enable' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'kc_data_pipeline.update' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'kc_data_pipeline.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'kc_report_builder.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'kc_report_builder.update' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'kc_report_builder.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'kcsb_sandbox_reset.disable' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'kcsb_sandbox_reset.enable' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'notification_broadcasts.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'notification_broadcasts.delete' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'notification_broadcasts.update' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'notification_broadcasts.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'notification_system.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'notification_system.delete' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'notification_system.update' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'notification_system.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'notification_templates.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'notification_templates.delete' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'notification_templates.update' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'notification_templates.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'org_management.assign' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'org_management.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'org_management.delete' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'org_management.revoke' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'org_management.update' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'org_management.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'policy_management.assign' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'policy_management.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'policy_management.disable' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'policy_management.enable' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'policy_management.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'product_management.assign' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'product_management.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'product_management.revoke' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'product_management.update' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'product_management.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'reports.enable' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'risks.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'risks.delete' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'risks.update' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'risks.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'sandbox.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'sandbox.delete' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'sandbox.execute' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'sandbox.promote' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'sandbox.update' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'sandbox.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'tasks.assign' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'tasks.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'tasks.update' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'tasks.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'tests.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'tests.delete' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'tests.update' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'tests.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'user_impersonation.enable' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'user_impersonation.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'workspace_management.assign' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'workspace_management.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'workspace_management.delete' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'workspace_management.revoke' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'workspace_management.update' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'workspace_management.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
  END IF;

  -- super_admin (92 permissions)
  SELECT id INTO v_role_id FROM "03_auth_manage"."16_fct_roles" WHERE code = 'super_admin' AND is_deleted = FALSE LIMIT 1;
  IF v_role_id IS NOT NULL THEN
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'access_audit_timeline.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'access_governance_console.assign' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'access_governance_console.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'access_governance_console.delete' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'access_governance_console.update' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'access_governance_console.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'admin_console.delete' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'ai_copilot.admin' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'ai_copilot.approve' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'ai_copilot.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'ai_copilot.execute' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'ai_copilot.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'ai_evidence_checker.trigger' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'assessments.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'assessments.delete' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'assessments.update' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'assessments.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'audit_workspace_auditor_findings.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'audit_workspace_auditor_findings.update' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'audit_workspace_auditor_findings.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'audit_workspace_auditor_portfolio.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'audit_workspace_auditor_tasks.assign' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'audit_workspace_auditor_tasks.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'audit_workspace_auditor_tasks.update' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'audit_workspace_auditor_tasks.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'audit_workspace_control_access.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'audit_workspace_engagement_membership.update' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'audit_workspace_engagement_membership.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'audit_workspace_evidence_requests.approve' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'audit_workspace_evidence_requests.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'audit_workspace_evidence_requests.revoke' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'audit_workspace_evidence_requests.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'auth_google_login.disable' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'auth_google_login.enable' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'auth_password_login.disable' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'auth_password_login.enable' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'controls.admin' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'controls.edit' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'feature_flag_registry.assign' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'feature_flag_registry.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'feature_flag_registry.delete' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'feature_flag_registry.disable' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'feature_flag_registry.enable' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'feature_flag_registry.update' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'feature_flag_registry.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'findings.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'findings.delete' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'findings.update' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'findings.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'global_risk_library.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'global_risk_library.delete' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'global_risk_library.update' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'global_risk_library.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'group_access_assignment.assign' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'group_access_assignment.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'group_access_assignment.delete' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'group_access_assignment.revoke' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'group_access_assignment.update' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'group_access_assignment.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'kc_data_pipeline.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'kc_data_pipeline.disable' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'kc_data_pipeline.enable' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'kc_data_pipeline.update' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'kc_data_pipeline.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'kc_report_builder.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'kc_report_builder.update' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'kc_report_builder.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'kcsb_sandbox_reset.disable' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'kcsb_sandbox_reset.enable' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'org_management.assign' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'org_management.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'org_management.delete' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'org_management.revoke' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'org_management.update' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'org_management.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'policy_management.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'policy_management.disable' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'policy_management.enable' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'product_management.assign' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'product_management.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'product_management.revoke' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'product_management.update' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'product_management.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'reports.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'reports.delete' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'reports.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'workspace_management.assign' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'workspace_management.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'workspace_management.delete' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'workspace_management.revoke' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'workspace_management.update' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'workspace_management.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
  END IF;

  -- workspace_admin (13 permissions)
  SELECT id INTO v_role_id FROM "03_auth_manage"."16_fct_roles" WHERE code = 'workspace_admin' AND is_deleted = FALSE LIMIT 1;
  IF v_role_id IS NOT NULL THEN
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'ai_copilot.approve' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'ai_copilot.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'ai_copilot.execute' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'ai_copilot.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'ai_evidence_checker.trigger' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'ai_evidence_checker.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'controls.admin' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'controls.edit' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'workspace_management.assign' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'workspace_management.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'workspace_management.revoke' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'workspace_management.update' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'workspace_management.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
  END IF;

  -- workspace_contributor (7 permissions)
  SELECT id INTO v_role_id FROM "03_auth_manage"."16_fct_roles" WHERE code = 'workspace_contributor' AND is_deleted = FALSE LIMIT 1;
  IF v_role_id IS NOT NULL THEN
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'ai_copilot.approve' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'ai_copilot.create' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'ai_copilot.execute' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'ai_copilot.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'ai_evidence_checker.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'workspace_management.update' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'workspace_management.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
  END IF;

  -- workspace_viewer (2 permissions)
  SELECT id INTO v_role_id FROM "03_auth_manage"."16_fct_roles" WHERE code = 'workspace_viewer' AND is_deleted = FALSE LIMIT 1;
  IF v_role_id IS NOT NULL THEN
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'ai_evidence_checker.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
    SELECT id INTO v_perm_id FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'workspace_management.view' LIMIT 1;
    IF v_perm_id IS NOT NULL THEN
      INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
        (id, role_id, feature_permission_id, tenant_key, is_deleted, created_at, updated_at)
      VALUES (gen_random_uuid(), v_role_id, v_perm_id, 'default', FALSE, NOW(), NOW())
      ON CONFLICT (role_id, feature_permission_id) DO UPDATE SET is_deleted = FALSE, updated_at = NOW();
    END IF;
  END IF;

END $$;

-- DOWN ========================================================================
-- No automated rollback — permission changes require manual review.