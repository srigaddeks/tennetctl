-- UP ====
-- Social captures — append-only event log of everything a user sees/posts
-- on LinkedIn and Twitter/X, collected by the SolSocial browser extension.
-- Reuses 01_dim_platforms (id 1=x, 2=linkedin).

SET search_path TO "07_social", public;

-- Capture type dim (what kind of interaction was captured)
CREATE TABLE IF NOT EXISTS "07_social"."03_dim_capture_types" (
    id          SMALLINT PRIMARY KEY,
    code        TEXT NOT NULL,
    label       TEXT NOT NULL,
    deprecated_at TIMESTAMP,
    CONSTRAINT uq_capture_types_code UNIQUE (code)
);
COMMENT ON TABLE "07_social"."03_dim_capture_types" IS 'Capture event kinds — feed post seen, own post, comments, profile views.';
INSERT INTO "07_social"."03_dim_capture_types" (id, code, label) VALUES
    (1, 'feed_post_seen',     'Feed post seen'),
    (2, 'own_post_published', 'Own post published'),
    (3, 'comment_seen',       'Comment seen'),
    (4, 'own_comment',        'Own comment posted'),
    (5, 'profile_viewed',     'Profile viewed')
ON CONFLICT (id) DO NOTHING;

-- Main capture event table
CREATE TABLE IF NOT EXISTS "07_social"."62_evt_social_captures" (
    id                  VARCHAR(36) NOT NULL,
    user_id             VARCHAR(36) NOT NULL,
    org_id              VARCHAR(36) NOT NULL,
    platform_id         SMALLINT    NOT NULL REFERENCES "07_social"."01_dim_platforms"(id),
    type_id             SMALLINT    NOT NULL REFERENCES "07_social"."03_dim_capture_types"(id),
    platform_post_id    TEXT        NOT NULL,
    observed_at         TIMESTAMP   NOT NULL,
    extractor_version   TEXT        NOT NULL DEFAULT 'v1',
    author_handle       TEXT,
    author_name         TEXT,
    text_excerpt        TEXT,
    url                 TEXT,
    like_count          INTEGER,
    reply_count         INTEGER,
    repost_count        INTEGER,
    view_count          INTEGER,
    is_own              BOOLEAN     NOT NULL DEFAULT FALSE,
    raw_attrs           JSONB,
    created_at          TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_62_evt_social_captures PRIMARY KEY (id)
);

COMMENT ON TABLE "07_social"."62_evt_social_captures" IS
    'Append-only log of social content captured by the browser extension. One row per user×platform×type×post_id.';
COMMENT ON COLUMN "07_social"."62_evt_social_captures".platform_post_id IS
    'Platform-native stable ID: LinkedIn URN (urn:li:activity:...) or Twitter numeric tweet ID.';
COMMENT ON COLUMN "07_social"."62_evt_social_captures".raw_attrs IS
    'Catch-all JSONB for extractor-specific fields not in fixed columns.';

-- Dedup: one row per (user, platform, type, post_id)
CREATE UNIQUE INDEX IF NOT EXISTS uq_62_evt_social_captures_dedup
    ON "07_social"."62_evt_social_captures"
    (user_id, platform_id, type_id, platform_post_id);

-- Fast lookup by user + time
CREATE INDEX IF NOT EXISTS idx_62_evt_social_captures_user_time
    ON "07_social"."62_evt_social_captures" (user_id, observed_at DESC);

-- Fast lookup by org
CREATE INDEX IF NOT EXISTS idx_62_evt_social_captures_org
    ON "07_social"."62_evt_social_captures" (org_id, created_at DESC);

-- Read view
CREATE OR REPLACE VIEW "07_social"."v_social_captures" AS
SELECT
    c.id,
    c.user_id,
    c.org_id,
    p.code   AS platform,
    t.code   AS type,
    c.platform_post_id,
    c.observed_at,
    c.extractor_version,
    c.author_handle,
    c.author_name,
    c.text_excerpt,
    c.url,
    c.like_count,
    c.reply_count,
    c.repost_count,
    c.view_count,
    c.is_own,
    c.raw_attrs,
    c.created_at
FROM "07_social"."62_evt_social_captures" c
JOIN "07_social"."01_dim_platforms"     p ON p.id = c.platform_id
JOIN "07_social"."03_dim_capture_types" t ON t.id = c.type_id;

COMMENT ON VIEW "07_social"."v_social_captures" IS
    'Readable capture events with platform and type codes resolved.';

-- DOWN ====
DROP VIEW  IF EXISTS "07_social"."v_social_captures";
DROP TABLE IF EXISTS "07_social"."62_evt_social_captures";
DROP TABLE IF EXISTS "07_social"."03_dim_capture_types";
