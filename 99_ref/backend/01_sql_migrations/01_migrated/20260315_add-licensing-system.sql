-- ═══════════════════════════════════════════════════════════════════════════
-- Migration: Licensing / tier system
--
-- License tiers are stored as an org setting, not a separate table.
-- This keeps the system flexible and uses existing EAV infrastructure.
--
-- Tiers: free (default), pro, pro_trial, internal
--   free       — basic features, resource limits apply
--   pro        — all features, higher limits
--   pro_trial  — temporary pro access, super admin sets custom limits
--   internal   — Kreesalis internal orgs, no limits
--
-- Resource limits are org settings that can be overridden per-org.
-- Feature flag gating by tier is a feature flag setting.
-- ═══════════════════════════════════════════════════════════════════════════

-- 1. Org setting keys for license tier and resource limits
INSERT INTO "03_auth_manage"."31_dim_org_setting_keys"
    (code, name, description, data_type, is_pii, is_required, sort_order, created_at, updated_at)
VALUES
    ('license_tier', 'License Tier',
     'Organization license tier: free, pro, pro_trial, or internal',
     'string', FALSE, FALSE, 1, NOW(), NOW()),

    ('license_expires_at', 'License Expiry',
     'ISO 8601 date when pro_trial expires (only relevant for pro_trial tier)',
     'string', FALSE, FALSE, 2, NOW(), NOW()),

    ('max_users', 'Max Users',
     'Maximum number of users allowed in this organization',
     'integer', FALSE, FALSE, 3, NOW(), NOW()),

    ('max_workspaces', 'Max Workspaces',
     'Maximum number of workspaces allowed in this organization',
     'integer', FALSE, FALSE, 4, NOW(), NOW()),

    ('max_frameworks', 'Max Frameworks',
     'Maximum number of compliance frameworks this organization can enable',
     'integer', FALSE, FALSE, 6, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- 2. Feature flag setting key: which license tier is required for this flag
--    Values: "free", "pro", "internal" (or empty = available to all tiers)
INSERT INTO "03_auth_manage"."21_dim_feature_flag_setting_keys"
    (code, name, description, data_type, is_pii, is_required, sort_order, created_at, updated_at)
VALUES
    ('required_license', 'Required License Tier',
     'Minimum license tier required to use this feature: free, pro, or internal. Empty = available to all.',
     'string', FALSE, FALSE, 6, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;
