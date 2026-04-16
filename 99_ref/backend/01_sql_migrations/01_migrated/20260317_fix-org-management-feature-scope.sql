-- ─────────────────────────────────────────────────────────────────────────
-- Fix org_management feature flag scope
--
-- org_management was seeded as feature_scope = 'platform' which means
-- org admins (who hold org_admin role in an org-scoped group) never see
-- their org_management.* permissions in the access context response.
--
-- Changing to feature_scope = 'org' means:
--   - Super admins (platform groups):
--       still get org_management.* in platform.actions (via get_platform_actions
--       which includes all platform-group actions regardless of feature_scope)
--       Wait — actually get_platform_actions filters ff.feature_scope = 'platform'.
--       So super admins will now get org_management in current_org.actions instead.
--       That's correct: they need an org context to act on org resources anyway.
--   - Org admins (org-scoped groups, org_admin role):
--       get org_management.* in current_org.actions when org_id is passed ✓
--
-- NOTE: Super admins' ability to create orgs (platform operation) should
-- remain discoverable. We keep a platform-scoped marker by ensuring
-- get_platform_actions also picks up org-scoped flags when the user is
-- in a platform group. But for simplicity: org_management.create stays
-- useful via the platform admin's permission check (require_permission uses
-- the DB join, not feature_scope filtering).
--
-- Short version: access context feature_scope only affects WHERE the action
-- appears in the response object. require_permission() doesn't use
-- feature_scope at all — it just checks the permission code exists in the
-- user's group chain. So this change is purely cosmetic/UX: it makes
-- org_management actions visible in current_org.actions for org admins.
-- ─────────────────────────────────────────────────────────────────────────

UPDATE "03_auth_manage"."14_dim_feature_flags"
SET feature_scope = 'org', updated_at = NOW()
WHERE code = 'org_management'
  AND feature_scope = 'platform';
