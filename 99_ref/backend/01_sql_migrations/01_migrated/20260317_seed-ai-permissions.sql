-- ============================================================
-- 20260317_seed-ai-permissions.sql
-- AI Copilot Platform — feature flag category, flag, permissions, role assignments
-- ============================================================

-- 0. Ensure 'ai' feature flag category exists
INSERT INTO "03_auth_manage"."11_dim_feature_flag_categories" (id, code, name, description, sort_order, created_at, updated_at)
VALUES (gen_random_uuid(), 'ai', 'AI', 'AI and agent platform features', 11, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- 1. Ensure 'approve' and 'admin' permission actions exist
INSERT INTO "03_auth_manage"."12_dim_feature_permission_actions" (id, code, name, description, sort_order, created_at, updated_at)
VALUES
    (gen_random_uuid(), 'approve', 'Approve', 'Approve or reject pending actions.', 100, NOW(), NOW()),
    (gen_random_uuid(), 'admin',   'Admin',   'Full administrative access to a feature.', 110, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- 2. Feature flag
INSERT INTO "03_auth_manage"."14_dim_feature_flags"
    (id, code, name, description, feature_scope, feature_flag_category_code,
     access_mode, lifecycle_state, initial_audience,
     env_dev, env_staging, env_prod, created_at, updated_at)
VALUES
    (gen_random_uuid(), 'ai_copilot', 'AI Copilot Platform',
     'Enterprise AI copilot, MCP tools, approval workflows, agent swarm',
     'platform', 'ai', 'permissioned', 'active', 'all',
     TRUE, TRUE, FALSE, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- 3. Permissions
INSERT INTO "03_auth_manage"."15_dim_feature_permissions"
    (id, code, feature_flag_code, permission_action_code, name, description, created_at, updated_at)
VALUES
    (gen_random_uuid(), 'ai_copilot.view',    'ai_copilot', 'view',    'View AI Copilot',         'Access conversations, memory, tool history, agent runs', NOW(), NOW()),
    (gen_random_uuid(), 'ai_copilot.create',  'ai_copilot', 'create',  'Create AI Conversations', 'Start new conversations, archive, manage own history',   NOW(), NOW()),
    (gen_random_uuid(), 'ai_copilot.execute', 'ai_copilot', 'execute', 'Execute AI Agents',       'Send messages, trigger agent runs, invoke read tools',   NOW(), NOW()),
    (gen_random_uuid(), 'ai_copilot.approve', 'ai_copilot', 'approve', 'Approve AI Actions',      'Approve or reject pending write tool approval requests', NOW(), NOW()),
    (gen_random_uuid(), 'ai_copilot.admin',   'ai_copilot', 'admin',   'AI Admin',                'View all users conversations, manage budgets, configure guardrails, kill agents', NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- 4. Grant all AI permissions to platform_super_admin role
INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
    (id, role_id, feature_permission_id,
     is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
     created_at, updated_at)
SELECT
    gen_random_uuid(),
    '00000000-0000-0000-0000-000000000601',
    fp.id,
    TRUE, FALSE, FALSE, FALSE, TRUE, FALSE,
    NOW(), NOW()
FROM "03_auth_manage"."15_dim_feature_permissions" fp
WHERE fp.feature_flag_code = 'ai_copilot'
AND NOT EXISTS (
    SELECT 1 FROM "03_auth_manage"."20_lnk_role_feature_permissions" rlp
    WHERE rlp.role_id = '00000000-0000-0000-0000-000000000601'
      AND rlp.feature_permission_id = fp.id
);
