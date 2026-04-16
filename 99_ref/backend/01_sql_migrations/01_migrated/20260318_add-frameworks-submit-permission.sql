-- ─────────────────────────────────────────────────────────────────────────────
-- FRAMEWORKS.SUBMIT PERMISSION
-- Adds a dedicated `frameworks.submit` permission that controls who can push a
-- framework (or risk) for approval review.
-- Initially restricted to platform_super_admin only — no regular user or org
-- admin can submit to the global marketplace.
-- ─────────────────────────────────────────────────────────────────────────────

-- 0. Add 'submit' to the permission actions dimension (if not already present)
INSERT INTO "03_auth_manage"."12_dim_feature_permission_actions"
    (id, code, name, description, sort_order, created_at, updated_at)
VALUES
    ('00000000-0000-0000-0000-000000000099',
     'submit', 'Submit', 'Submit an entity for review or approval.',
     11, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- 1. Add the frameworks.submit permission
INSERT INTO "03_auth_manage"."15_dim_feature_permissions"
    (id, code, permission_action_code, feature_flag_code, name, description, created_at, updated_at)
VALUES
    ('00000000-0000-0000-0000-000000003015',
     'frameworks.submit', 'submit', 'framework_management',
     'Submit Frameworks for Approval',
     'Can push a framework to pending_review for marketplace approval. '
     'Restricted to super admins — regular org users cannot submit to the global library.',
     NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- 2. Grant frameworks.submit to platform_super_admin only
INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
    (id, role_id, feature_permission_id,
     is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
     created_at, updated_at, created_by, updated_by)
SELECT
    gen_random_uuid(),
    r.id,
    fp.id,
    TRUE, FALSE, FALSE, FALSE, FALSE, FALSE,
    NOW(), NOW(), NULL, NULL
FROM "03_auth_manage"."16_fct_roles" r
CROSS JOIN "03_auth_manage"."15_dim_feature_permissions" fp
WHERE r.code = 'platform_super_admin'
  AND fp.code = 'frameworks.submit'
  AND NOT EXISTS (
    SELECT 1 FROM "03_auth_manage"."20_lnk_role_feature_permissions" lnk
    WHERE lnk.role_id = r.id AND lnk.feature_permission_id = fp.id
  );

-- NOTE: library_curator does NOT get frameworks.submit by design.
-- Curators can approve/reject but not initiate submissions themselves.
-- To enable a future "org author can submit their own frameworks", grant
-- frameworks.submit to the appropriate org-scoped role at that time.
