-- ═══════════════════════════════════════════════════════════════════════════
-- Migration: License Profiles
--
-- License tiers: free, pro, pro_trial, enterprise, partner, internal
-- License profiles: named templates with specific limits/entitlements
--   - Each profile belongs to a tier
--   - Multiple profiles can exist per tier (e.g. "Pro Startup", "Pro Enterprise")
--   - Orgs are assigned a profile → inherit its tier + defaults
--   - Orgs can have custom overrides that take precedence
--
-- Resolution: Org custom override > Profile default > No limit
-- ═══════════════════════════════════════════════════════════════════════════

-- 1. License profiles fact table
CREATE TABLE IF NOT EXISTS "03_auth_manage"."37_fct_license_profiles" (
    id              UUID            NOT NULL DEFAULT gen_random_uuid(),
    code            VARCHAR(50)     NOT NULL,
    name            VARCHAR(120)    NOT NULL,
    description     VARCHAR(500)    NOT NULL DEFAULT '',
    tier            VARCHAR(30)     NOT NULL DEFAULT 'free',
    is_active       BOOLEAN         NOT NULL DEFAULT TRUE,
    sort_order      INTEGER         NOT NULL DEFAULT 100,
    created_at      TIMESTAMP       NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP       NOT NULL DEFAULT NOW(),

    CONSTRAINT pk_37_fct_license_profiles       PRIMARY KEY (id),
    CONSTRAINT uq_37_fct_license_profiles_code  UNIQUE (code),
    CONSTRAINT ck_37_fct_license_profiles_tier  CHECK (tier IN ('free', 'pro', 'pro_trial', 'enterprise', 'partner', 'internal'))
);

-- 2. License profile settings (EAV key-value)
CREATE TABLE IF NOT EXISTS "03_auth_manage"."38_dtl_license_profile_settings" (
    id              UUID            NOT NULL DEFAULT gen_random_uuid(),
    profile_id      UUID            NOT NULL,
    setting_key     VARCHAR(120)    NOT NULL,
    setting_value   TEXT            NOT NULL,
    created_at      TIMESTAMP       NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP       NOT NULL DEFAULT NOW(),

    CONSTRAINT pk_38_dtl_license_profile_settings       PRIMARY KEY (id),
    CONSTRAINT uq_38_dtl_license_profile_settings_key   UNIQUE (profile_id, setting_key),
    CONSTRAINT fk_38_dtl_license_profile_settings_prof  FOREIGN KEY (profile_id)
        REFERENCES "03_auth_manage"."37_fct_license_profiles" (id) ON DELETE CASCADE
);

-- 3. Seed default profiles (one per tier as starting point)
INSERT INTO "03_auth_manage"."37_fct_license_profiles"
    (code, name, description, tier, sort_order, created_at, updated_at)
VALUES
    ('free_default',       'Free',               'Default free tier profile with basic limits.',            'free',       10, NOW(), NOW()),
    ('pro_default',        'Pro',                'Default pro tier profile with advanced limits.',          'pro',        20, NOW(), NOW()),
    ('pro_trial_default',  'Pro Trial',          'Temporary pro access for evaluation.',                    'pro_trial',  30, NOW(), NOW()),
    ('enterprise_default', 'Enterprise',         'Enterprise tier with custom limits.',                     'enterprise', 40, NOW(), NOW()),
    ('partner_default',    'Partner',            'Partner organizations with special access.',              'partner',    50, NOW(), NOW()),
    ('internal_default',   'Internal',           'Kreesalis internal organizations. No limits.',            'internal',   60, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- 4. Seed free tier defaults
INSERT INTO "03_auth_manage"."38_dtl_license_profile_settings"
    (profile_id, setting_key, setting_value, created_at, updated_at)
SELECT p.id, v.key, v.value, NOW(), NOW()
FROM "03_auth_manage"."37_fct_license_profiles" p
CROSS JOIN (VALUES
    ('max_users',       '5'),
    ('max_workspaces',  '2'),
    ('max_frameworks',  '1')
) AS v(key, value)
WHERE p.code = 'free_default'
  AND NOT EXISTS (
      SELECT 1 FROM "03_auth_manage"."38_dtl_license_profile_settings"
      WHERE profile_id = p.id AND setting_key = v.key
  );

-- 5. Seed pro tier defaults
INSERT INTO "03_auth_manage"."38_dtl_license_profile_settings"
    (profile_id, setting_key, setting_value, created_at, updated_at)
SELECT p.id, v.key, v.value, NOW(), NOW()
FROM "03_auth_manage"."37_fct_license_profiles" p
CROSS JOIN (VALUES
    ('max_users',       '50'),
    ('max_workspaces',  '20'),
    ('max_frameworks',  '10')
) AS v(key, value)
WHERE p.code = 'pro_default'
  AND NOT EXISTS (
      SELECT 1 FROM "03_auth_manage"."38_dtl_license_profile_settings"
      WHERE profile_id = p.id AND setting_key = v.key
  );

-- 6. Add org setting key for assigned profile
INSERT INTO "03_auth_manage"."31_dim_org_setting_keys"
    (code, name, description, data_type, is_pii, is_required, sort_order, created_at, updated_at)
VALUES
    ('license_profile', 'License Profile',
     'Code of the license profile assigned to this organization (determines tier + defaults)',
     'string', FALSE, FALSE, 2, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;
