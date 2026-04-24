-- UP ====
-- Production-hardening migration for social captures:
--   1. Metric time-series observations (track engagement growth)
--   2. Workspace scoping (stamp workspace_id from session)
--   3. GIN indexes on raw_attrs for hashtag/mention queries
--   4. tsvector + GIN index for full-text search on text_excerpt
--   5. Per-type raw_attrs schema registry
--   6. Soft-deprecate redundant `own_*` types in favor of is_own flag
--   7. Author aggregate view

-- ── 1. Metric observations (append-only time-series) ───────────────────────

CREATE TABLE IF NOT EXISTS "07_social"."63_evt_capture_metrics" (
    id                 VARCHAR(36) PRIMARY KEY,
    capture_id         VARCHAR(36) NOT NULL
        REFERENCES "07_social"."62_evt_social_captures"(id) ON DELETE CASCADE,
    user_id            VARCHAR(36) NOT NULL,
    org_id             VARCHAR(36) NOT NULL,
    observed_at        TIMESTAMP NOT NULL,
    like_count         INTEGER,
    reply_count        INTEGER,
    repost_count       INTEGER,
    view_count         INTEGER,
    reactions          JSONB,
    created_at         TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_capture_metrics_capture_time
    ON "07_social"."63_evt_capture_metrics"(capture_id, observed_at DESC);

CREATE INDEX IF NOT EXISTS idx_capture_metrics_org_time
    ON "07_social"."63_evt_capture_metrics"(org_id, observed_at DESC);

COMMENT ON TABLE "07_social"."63_evt_capture_metrics" IS
    'Time-series observations of engagement metrics. Inserted every time the extension sees a capture it already has, so we track growth over time.';

-- ── 2. Workspace scoping ───────────────────────────────────────────────────

ALTER TABLE "07_social"."62_evt_social_captures"
    ADD COLUMN IF NOT EXISTS workspace_id VARCHAR(36);

CREATE INDEX IF NOT EXISTS idx_62_evt_social_captures_workspace
    ON "07_social"."62_evt_social_captures"(workspace_id, observed_at DESC)
    WHERE workspace_id IS NOT NULL;

COMMENT ON COLUMN "07_social"."62_evt_social_captures".workspace_id IS
    'Optional workspace scope. Captures made while a workspace was active are tagged so users can separate e.g. "personal" vs "competitive intel" feeds.';

-- ── 3. GIN indexes on JSONB fields users will filter by ───────────────────

-- hashtags: captures whose raw_attrs.hashtags contains a given tag
CREATE INDEX IF NOT EXISTS idx_62_evt_social_captures_hashtags
    ON "07_social"."62_evt_social_captures" USING gin ((raw_attrs -> 'hashtags'));

-- mentions: same for @mentions
CREATE INDEX IF NOT EXISTS idx_62_evt_social_captures_mentions
    ON "07_social"."62_evt_social_captures" USING gin ((raw_attrs -> 'mentions'));

-- Generic raw_attrs GIN for ad-hoc containment queries
CREATE INDEX IF NOT EXISTS idx_62_evt_social_captures_raw_attrs
    ON "07_social"."62_evt_social_captures" USING gin (raw_attrs jsonb_path_ops);

-- ── 4. Full-text search on text_excerpt ────────────────────────────────────

ALTER TABLE "07_social"."62_evt_social_captures"
    ADD COLUMN IF NOT EXISTS text_tsv tsvector
    GENERATED ALWAYS AS (
        to_tsvector(
            'simple',
            coalesce(text_excerpt, '') || ' ' || coalesce(author_name, '')
        )
    ) STORED;

CREATE INDEX IF NOT EXISTS idx_62_evt_social_captures_tsv
    ON "07_social"."62_evt_social_captures" USING gin (text_tsv);

COMMENT ON COLUMN "07_social"."62_evt_social_captures".text_tsv IS
    'Generated tsvector over text_excerpt + author_name for fast ILIKE replacement.';

-- Useful index for author-by-platform queries
CREATE INDEX IF NOT EXISTS idx_62_evt_social_captures_author
    ON "07_social"."62_evt_social_captures"(platform_id, author_handle)
    WHERE author_handle IS NOT NULL;

-- ── 5. Rebuild v_social_captures with new fields ──────────────────────────

DROP VIEW IF EXISTS "07_social"."v_social_captures";

CREATE VIEW "07_social"."v_social_captures" AS
SELECT
    c.id,
    c.user_id,
    c.org_id,
    c.workspace_id,
    p.code  AS platform,
    t.code  AS type,
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
JOIN "07_social"."01_dim_platforms" p ON p.id = c.platform_id
JOIN "07_social"."03_dim_capture_types" t ON t.id = c.type_id;

COMMENT ON VIEW "07_social"."v_social_captures" IS
    'Readable capture events with platform and type codes resolved.';

-- ── 6. Author aggregate view (entity resolution) ──────────────────────────

CREATE OR REPLACE VIEW "07_social"."v_social_authors" AS
SELECT
    c.user_id,
    c.org_id,
    p.code AS platform,
    c.author_handle AS handle,
    MAX(c.author_name) AS display_name,
    MAX((c.raw_attrs ->> 'author_headline')) AS headline,
    COUNT(*) AS capture_count,
    MIN(c.observed_at) AS first_seen_at,
    MAX(c.observed_at) AS last_seen_at,
    SUM(COALESCE(c.like_count, 0))   AS total_likes_seen,
    SUM(COALESCE(c.reply_count, 0))  AS total_replies_seen,
    SUM(COALESCE(c.repost_count, 0)) AS total_reposts_seen,
    MAX(c.like_count)   AS max_single_post_likes,
    BOOL_OR(c.is_own)   AS is_self
FROM "07_social"."62_evt_social_captures" c
JOIN "07_social"."01_dim_platforms" p ON p.id = c.platform_id
WHERE c.author_handle IS NOT NULL
GROUP BY c.user_id, c.org_id, p.code, c.author_handle;

COMMENT ON VIEW "07_social"."v_social_authors" IS
    'Author aggregate — one row per (user, platform, handle). Rollup of every capture that author appears in.';

-- ── 7. Soft-deprecate redundant capture types (prefer is_own flag) ────────

UPDATE "07_social"."03_dim_capture_types"
SET deprecated_at = CURRENT_TIMESTAMP
WHERE code IN ('own_post_published', 'own_comment')
  AND deprecated_at IS NULL;

-- Backfill is_own=true on historical rows that used these types; the service
-- layer from now on normalizes to feed_post_seen + is_own=true.
UPDATE "07_social"."62_evt_social_captures"
SET is_own = TRUE
WHERE type_id IN (
    SELECT id FROM "07_social"."03_dim_capture_types"
    WHERE code IN ('own_post_published', 'own_comment')
);

-- ── 8. Capture-type schema registry (per-type raw_attrs validation) ───────

ALTER TABLE "07_social"."03_dim_capture_types"
    ADD COLUMN IF NOT EXISTS raw_attrs_schema JSONB;

COMMENT ON COLUMN "07_social"."03_dim_capture_types".raw_attrs_schema IS
    'Optional JSON Schema (Draft-07) the raw_attrs must conform to for this capture type. NULL = anything goes.';

-- ── 9. Retention policy (per-org TTL in days) ─────────────────────────────

ALTER TABLE "07_social"."03_dim_capture_types"
    ADD COLUMN IF NOT EXISTS default_retention_days INTEGER;

-- Sensible defaults (can be overridden per-org via a future settings layer)
UPDATE "07_social"."03_dim_capture_types" SET default_retention_days = CASE
    WHEN code IN ('notification_seen')           THEN  30
    WHEN code IN ('search_result_seen')          THEN  30
    WHEN code IN ('connection_suggested')        THEN  30
    WHEN code IN ('job_post_seen')               THEN  60
    WHEN code IN ('hashtag_feed_seen')           THEN  60
    ELSE 365
END
WHERE default_retention_days IS NULL;

-- DOWN ====
ALTER TABLE "07_social"."03_dim_capture_types" DROP COLUMN IF EXISTS default_retention_days;
ALTER TABLE "07_social"."03_dim_capture_types" DROP COLUMN IF EXISTS raw_attrs_schema;

UPDATE "07_social"."03_dim_capture_types"
SET deprecated_at = NULL
WHERE code IN ('own_post_published', 'own_comment');

DROP VIEW IF EXISTS "07_social"."v_social_authors";

DROP VIEW IF EXISTS "07_social"."v_social_captures";
CREATE VIEW "07_social"."v_social_captures" AS
SELECT
    c.id, c.user_id, c.org_id,
    p.code  AS platform, t.code AS type,
    c.platform_post_id, c.observed_at, c.extractor_version,
    c.author_handle, c.author_name, c.text_excerpt, c.url,
    c.like_count, c.reply_count, c.repost_count, c.view_count,
    c.is_own, c.raw_attrs, c.created_at
FROM "07_social"."62_evt_social_captures" c
JOIN "07_social"."01_dim_platforms" p ON p.id = c.platform_id
JOIN "07_social"."03_dim_capture_types" t ON t.id = c.type_id;

DROP INDEX IF EXISTS "07_social".idx_62_evt_social_captures_author;
DROP INDEX IF EXISTS "07_social".idx_62_evt_social_captures_tsv;
ALTER TABLE "07_social"."62_evt_social_captures" DROP COLUMN IF EXISTS text_tsv;

DROP INDEX IF EXISTS "07_social".idx_62_evt_social_captures_raw_attrs;
DROP INDEX IF EXISTS "07_social".idx_62_evt_social_captures_mentions;
DROP INDEX IF EXISTS "07_social".idx_62_evt_social_captures_hashtags;

DROP INDEX IF EXISTS "07_social".idx_62_evt_social_captures_workspace;
ALTER TABLE "07_social"."62_evt_social_captures" DROP COLUMN IF EXISTS workspace_id;

DROP TABLE IF EXISTS "07_social"."63_evt_capture_metrics";
