-- UP ====
CREATE SCHEMA IF NOT EXISTS "07_social";

-- dim: platforms
CREATE TABLE "07_social"."01_dim_platforms" (
    id SMALLINT PRIMARY KEY,
    code VARCHAR(20) UNIQUE NOT NULL,
    label VARCHAR(50) NOT NULL,
    char_limit INTEGER NOT NULL,
    supports_media BOOLEAN NOT NULL DEFAULT true,
    api_version VARCHAR(10) NOT NULL,
    deprecated_at TIMESTAMP
);
INSERT INTO "07_social"."01_dim_platforms" VALUES
  (1, 'x',        'X (Twitter)',  280,   true, 'v2',    null),
  (2, 'linkedin', 'LinkedIn',     3000,  true, 'v202306', null),
  (3, 'instagram','Instagram',    2200,  true, 'v18',   null),
  (4, 'facebook', 'Facebook',     63206, true, 'v18',   null),
  (5, 'tiktok',   'TikTok',       2200,  true, 'v2',    null);

-- dim: post statuses
CREATE TABLE "07_social"."02_dim_post_statuses" (
    id SMALLINT PRIMARY KEY,
    code VARCHAR(20) UNIQUE NOT NULL,
    label VARCHAR(50) NOT NULL
);
INSERT INTO "07_social"."02_dim_post_statuses" VALUES
  (1, 'draft',       'Draft'),
  (2, 'scheduled',   'Scheduled'),
  (3, 'publishing',  'Publishing'),
  (4, 'published',   'Published'),
  (5, 'failed',      'Failed'),
  (6, 'cancelled',   'Cancelled');

-- fct: connected social accounts (tokens stored in vault)
CREATE TABLE "07_social"."10_fct_social_accounts" (
    id VARCHAR(36) PRIMARY KEY,
    org_id VARCHAR(36) NOT NULL REFERENCES "03_iam"."10_fct_orgs"(id) ON DELETE CASCADE,
    workspace_id VARCHAR(36),
    platform_id SMALLINT NOT NULL REFERENCES "07_social"."01_dim_platforms"(id),
    account_name VARCHAR(255) NOT NULL,
    account_handle VARCHAR(255),
    account_id_on_platform VARCHAR(255),
    vault_key VARCHAR(255) NOT NULL,
    token_scope VARCHAR(500),
    profile_image_url VARCHAR(500),
    follower_count INTEGER,
    is_active BOOLEAN NOT NULL DEFAULT true,
    is_test BOOLEAN NOT NULL DEFAULT false,
    deleted_at TIMESTAMP,
    created_by VARCHAR(36) NOT NULL,
    updated_by VARCHAR(36) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_social_account_platform UNIQUE (org_id, platform_id, account_id_on_platform)
);
CREATE INDEX idx_social_accounts_org ON "07_social"."10_fct_social_accounts"(org_id);

-- fct: scheduled posts
CREATE TABLE "07_social"."11_fct_posts" (
    id VARCHAR(36) PRIMARY KEY,
    org_id VARCHAR(36) NOT NULL REFERENCES "03_iam"."10_fct_orgs"(id) ON DELETE CASCADE,
    workspace_id VARCHAR(36),
    status_id SMALLINT NOT NULL REFERENCES "07_social"."02_dim_post_statuses"(id) DEFAULT 1,
    content_text TEXT NOT NULL DEFAULT '',
    media_urls JSONB NOT NULL DEFAULT '[]',
    first_comment TEXT,
    scheduled_at TIMESTAMP,
    published_at TIMESTAMP,
    platform_post_ids JSONB NOT NULL DEFAULT '{}',
    error_message TEXT,
    campaign_id VARCHAR(36),
    author_user_id VARCHAR(36),
    approved_by_user_id VARCHAR(36),
    approved_at TIMESTAMP,
    is_test BOOLEAN NOT NULL DEFAULT false,
    deleted_at TIMESTAMP,
    created_by VARCHAR(36) NOT NULL,
    updated_by VARCHAR(36) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_posts_org_status ON "07_social"."11_fct_posts"(org_id, status_id);
CREATE INDEX idx_posts_scheduled_at ON "07_social"."11_fct_posts"(scheduled_at) WHERE scheduled_at IS NOT NULL;

-- lnk: post <-> account (which accounts to post to)
CREATE TABLE "07_social"."40_lnk_post_accounts" (
    id VARCHAR(36) PRIMARY KEY,
    post_id VARCHAR(36) NOT NULL REFERENCES "07_social"."11_fct_posts"(id) ON DELETE CASCADE,
    account_id VARCHAR(36) NOT NULL REFERENCES "07_social"."10_fct_social_accounts"(id) ON DELETE CASCADE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_post_account UNIQUE (post_id, account_id)
);

-- evt: delivery log per post per account
CREATE TABLE "07_social"."60_evt_post_deliveries" (
    id VARCHAR(36) PRIMARY KEY,
    org_id VARCHAR(36) NOT NULL,
    post_id VARCHAR(36) NOT NULL REFERENCES "07_social"."11_fct_posts"(id) ON DELETE CASCADE,
    account_id VARCHAR(36) NOT NULL REFERENCES "07_social"."10_fct_social_accounts"(id),
    platform_id SMALLINT NOT NULL,
    platform_post_id VARCHAR(255),
    outcome VARCHAR(20) NOT NULL,
    error_detail TEXT,
    published_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- evt: post metrics (polled from platform APIs)
CREATE TABLE "07_social"."61_evt_post_metrics" (
    id VARCHAR(36) PRIMARY KEY,
    org_id VARCHAR(36) NOT NULL,
    post_id VARCHAR(36) NOT NULL REFERENCES "07_social"."11_fct_posts"(id) ON DELETE CASCADE,
    account_id VARCHAR(36) NOT NULL,
    platform_id SMALLINT NOT NULL,
    platform_post_id VARCHAR(255) NOT NULL,
    fetched_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    impressions INTEGER NOT NULL DEFAULT 0,
    engagements INTEGER NOT NULL DEFAULT 0,
    likes INTEGER NOT NULL DEFAULT 0,
    reposts INTEGER NOT NULL DEFAULT 0,
    replies INTEGER NOT NULL DEFAULT 0,
    bookmarks INTEGER NOT NULL DEFAULT 0,
    clicks INTEGER NOT NULL DEFAULT 0,
    reach INTEGER NOT NULL DEFAULT 0,
    raw_data JSONB NOT NULL DEFAULT '{}'
);
CREATE INDEX idx_post_metrics_post ON "07_social"."61_evt_post_metrics"(post_id);

-- Views
CREATE OR REPLACE VIEW "07_social"."v_posts" AS
SELECT
    p.id, p.org_id, p.workspace_id,
    s.code AS status, s.label AS status_label,
    p.content_text, p.media_urls, p.first_comment,
    p.scheduled_at, p.published_at, p.platform_post_ids,
    p.error_message, p.campaign_id,
    p.author_user_id, p.approved_by_user_id, p.approved_at,
    p.deleted_at, p.created_by, p.updated_by, p.created_at, p.updated_at,
    COALESCE(
        (SELECT json_agg(json_build_object(
            'account_id', la.account_id,
            'platform', pl.code,
            'account_name', sa.account_name,
            'account_handle', sa.account_handle
        ))
        FROM "07_social"."40_lnk_post_accounts" la
        JOIN "07_social"."10_fct_social_accounts" sa ON sa.id = la.account_id
        JOIN "07_social"."01_dim_platforms" pl ON pl.id = sa.platform_id
        WHERE la.post_id = p.id),
        '[]'
    ) AS target_accounts
FROM "07_social"."11_fct_posts" p
JOIN "07_social"."02_dim_post_statuses" s ON s.id = p.status_id
WHERE p.deleted_at IS NULL;

CREATE OR REPLACE VIEW "07_social"."v_social_accounts" AS
SELECT
    sa.id, sa.org_id, sa.workspace_id,
    pl.code AS platform, pl.label AS platform_label,
    pl.char_limit,
    sa.account_name, sa.account_handle, sa.account_id_on_platform,
    sa.vault_key, sa.token_scope, sa.profile_image_url,
    sa.follower_count, sa.is_active,
    sa.deleted_at, sa.created_by, sa.updated_by, sa.created_at, sa.updated_at
FROM "07_social"."10_fct_social_accounts" sa
JOIN "07_social"."01_dim_platforms" pl ON pl.id = sa.platform_id
WHERE sa.deleted_at IS NULL;

-- DOWN ====
DROP VIEW IF EXISTS "07_social"."v_social_accounts";
DROP VIEW IF EXISTS "07_social"."v_posts";
DROP TABLE IF EXISTS "07_social"."61_evt_post_metrics";
DROP TABLE IF EXISTS "07_social"."60_evt_post_deliveries";
DROP TABLE IF EXISTS "07_social"."40_lnk_post_accounts";
DROP TABLE IF EXISTS "07_social"."11_fct_posts";
DROP TABLE IF EXISTS "07_social"."10_fct_social_accounts";
DROP TABLE IF EXISTS "07_social"."02_dim_post_statuses";
DROP TABLE IF EXISTS "07_social"."01_dim_platforms";
DROP SCHEMA IF EXISTS "07_social";
