-- Global Control Test Library + Clone-on-Subscribe
-- Migration: 20260320_global-library.sql

-- Global library catalog (platform-admin managed)
CREATE TABLE "15_sandbox"."80_fct_global_libraries" (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_library_id   UUID NOT NULL REFERENCES "15_sandbox"."29_fct_libraries"(id),
    source_org_id       UUID NOT NULL,
    global_code         VARCHAR(100) UNIQUE NOT NULL,
    global_name         VARCHAR(255) NOT NULL,
    description         TEXT,
    category_code       VARCHAR(50),
    connector_type_codes TEXT[] NOT NULL DEFAULT '{}',
    curator_user_id     UUID NOT NULL,
    publish_status      VARCHAR(20) NOT NULL DEFAULT 'draft',
    is_featured         BOOLEAN NOT NULL DEFAULT FALSE,
    download_count      INT NOT NULL DEFAULT 0,
    version_number      INT NOT NULL DEFAULT 1,
    published_at        TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_publish_status CHECK (publish_status IN ('draft', 'review', 'published', 'deprecated'))
);

-- Org subscriptions
CREATE TABLE "15_sandbox"."81_lnk_org_library_subscriptions" (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id              UUID NOT NULL,
    global_library_id   UUID NOT NULL REFERENCES "15_sandbox"."80_fct_global_libraries"(id),
    subscribed_by       UUID NOT NULL,
    subscribed_version  INT NOT NULL,
    local_library_id    UUID REFERENCES "15_sandbox"."29_fct_libraries"(id),
    auto_update         BOOLEAN NOT NULL DEFAULT TRUE,
    subscribed_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(org_id, global_library_id)
);

CREATE INDEX idx_global_libraries_status ON "15_sandbox"."80_fct_global_libraries" (publish_status);
CREATE INDEX idx_global_libraries_category ON "15_sandbox"."80_fct_global_libraries" (category_code);
CREATE INDEX idx_org_subscriptions_org ON "15_sandbox"."81_lnk_org_library_subscriptions" (org_id);
CREATE INDEX idx_org_subscriptions_global ON "15_sandbox"."81_lnk_org_library_subscriptions" (global_library_id);

-- Add sandbox.publish_global permission
-- sandbox flag already seeded in seed-sandbox-permissions.sql; ensure it exists
INSERT INTO "03_auth_manage"."14_dim_feature_flags"
    (id, code, name, description, feature_scope, feature_flag_category_code,
     access_mode, lifecycle_state, initial_audience,
     env_dev, env_staging, env_prod, created_at, updated_at)
SELECT gen_random_uuid(), 'sandbox', 'Sandbox', 'K-Control Sandbox', 'platform', 'grc',
       'permissioned', 'active', 'all', TRUE, TRUE, FALSE, NOW(), NOW()
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."14_dim_feature_flags" WHERE code = 'sandbox');

-- Seed 'promote_global' action if not exists
INSERT INTO "03_auth_manage"."12_dim_feature_permission_actions" (id, code, name, description, sort_order, created_at, updated_at)
VALUES ('00000000-0000-0000-0000-000000005010', 'promote_global', 'Promote Global', 'Publish to global catalog.', 50, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

INSERT INTO "03_auth_manage"."15_dim_feature_permissions"
    (id, code, feature_flag_code, permission_action_code, name, description, created_at, updated_at)
SELECT gen_random_uuid(), 'sandbox.publish_global', 'sandbox', 'promote_global',
       'Publish Global Library', 'Publish org library to global catalog (platform admin only)',
       NOW(), NOW()
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'sandbox.publish_global');
