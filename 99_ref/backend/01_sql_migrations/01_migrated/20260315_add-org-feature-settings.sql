-- ═══════════════════════════════════════════════════════════════════════════
-- Migration: org-level feature flag support
-- ═══════════════════════════════════════════════════════════════════════════

-- 1. Org setting key: stores which feature flags are enabled for this org
INSERT INTO "03_auth_manage"."31_dim_org_setting_keys"
    (code, name, description, data_type, is_pii, is_required, sort_order, created_at, updated_at)
VALUES
    ('enabled_features', 'Enabled Features',
     'JSON array of feature flag codes enabled for this organization (org-scoped flags only)',
     'json', FALSE, FALSE, 5, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- 2. Feature flag setting key: controls how org admins interact with this flag
--    Values: "hidden" | "locked" | "unlocked"
--      hidden   — org admins cannot see this flag at all
--      locked   — org admins can see it but cannot change it (system default applies)
--      unlocked — org admins can see it and toggle it for their org
--    Default (when not set): "hidden"
INSERT INTO "03_auth_manage"."21_dim_feature_flag_setting_keys"
    (code, name, description, data_type, is_pii, is_required, sort_order, created_at, updated_at)
VALUES
    ('org_visibility', 'Org Admin Visibility',
     'Controls whether org admins can see and/or toggle this flag: hidden, locked, or unlocked',
     'string', FALSE, FALSE, 5, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;
