-- ─────────────────────────────────────────────────────────────────────────────
-- 08_COMMENTS SCHEMA
-- Enterprise-Grade Polymorphic Comments System
--
-- Design principles:
--   - Polymorphic: any entity type (task, risk, control, framework, etc.)
--   - Single level of reply nesting (replies to top-level comments only)
--   - Soft delete: is_deleted=true preserves thread structure for replies
--   - Edit history: every content change captured in 02_trx_comment_edits
--   - Reactions: emoji toggles, deduplicated by (comment_id, user_id, code)
--   - Audit: self-contained in 04_aud_comment_events (JSONB metadata)
--   - No cross-schema FKs: loose coupling — entity_type/entity_id are soft refs
--   - Unread tracking: 05_trx_comment_views records last-viewed-at per user/entity
--
-- Scoping: tenant_key on every row — all queries must include it
-- Mentions: extracted @[display_name](user_id) patterns, stored as UUID[]
--
-- RLS approach: Row-Level Security can be added when needed using tenant_key
-- and author_user_id as policy predicates.  All service-layer queries already
-- include WHERE tenant_key = $1 so RLS would be redundant but adds defence-in-depth.
-- ─────────────────────────────────────────────────────────────────────────────

-- Schema created in 20260313_a_create-all-schemas.sql

-- ─────────────────────────────────────────────────────────────────────────────
-- FACT TABLE (01) — Comments
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS "08_comments"."01_fct_comments" (
    id                  UUID         NOT NULL DEFAULT gen_random_uuid(),
    tenant_key          TEXT         NOT NULL,
    -- Polymorphic entity link (no cross-schema FK — intentional loose coupling)
    entity_type         TEXT         NOT NULL,
    entity_id           UUID         NOT NULL,
    -- Reply threading (max 1 level: parent must itself have no parent)
    parent_comment_id   UUID         NULL,
    -- Content
    author_user_id      UUID         NOT NULL,
    content             TEXT         NOT NULL,
    -- Edit state
    is_edited           BOOLEAN      NOT NULL DEFAULT FALSE,
    -- Soft delete (preserves threading — replies remain visible as "[deleted]")
    is_deleted          BOOLEAN      NOT NULL DEFAULT FALSE,
    deleted_at          TIMESTAMPTZ  NULL,
    deleted_by          UUID         NULL,
    -- Pin state (set by workspace/org admins)
    pinned              BOOLEAN      NOT NULL DEFAULT FALSE,
    pinned_by           UUID         NULL,
    pinned_at           TIMESTAMPTZ  NULL,
    -- Resolution (action item workflow)
    resolved            BOOLEAN      NOT NULL DEFAULT FALSE,
    resolved_by         UUID         NULL,
    resolved_at         TIMESTAMPTZ  NULL,
    -- Extracted @mentions: UUID array of mentioned user IDs
    mention_user_ids    UUID[]       NOT NULL DEFAULT '{}',
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    CONSTRAINT pk_01_fct_comments          PRIMARY KEY (id),
    CONSTRAINT fk_01_fct_comments_parent   FOREIGN KEY (parent_comment_id)
        REFERENCES "08_comments"."01_fct_comments" (id)
        ON DELETE SET NULL,
    -- Allowed entity types — must match VALID_ENTITY_TYPES in constants.py
    CONSTRAINT ck_01_fct_comments_entity_type CHECK (entity_type IN (
        'task', 'risk', 'control', 'framework',
        'evidence_template', 'test', 'requirement'
    )),
    -- Content must be non-empty and within the 50 000 character UI limit
    CONSTRAINT ck_01_fct_comments_content_length CHECK (
        length(content) BETWEEN 1 AND 50000
    ),
    -- Data integrity: soft-delete, pin, and resolve state coherence
    CONSTRAINT ck_01_fct_comments_deleted_coherence
        CHECK ((is_deleted = FALSE AND deleted_at IS NULL AND deleted_by IS NULL)
            OR (is_deleted = TRUE AND deleted_at IS NOT NULL AND deleted_by IS NOT NULL)),
    CONSTRAINT ck_01_fct_comments_pinned_coherence
        CHECK ((pinned = FALSE AND pinned_at IS NULL AND pinned_by IS NULL)
            OR (pinned = TRUE AND pinned_at IS NOT NULL AND pinned_by IS NOT NULL)),
    CONSTRAINT ck_01_fct_comments_resolved_coherence
        CHECK ((resolved = FALSE AND resolved_at IS NULL AND resolved_by IS NULL)
            OR (resolved = TRUE AND resolved_at IS NOT NULL AND resolved_by IS NOT NULL))
);

-- ─────────────────────────────────────────────────────────────────────────────
-- TRANSACTION TABLE (02) — Edit history
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS "08_comments"."02_trx_comment_edits" (
    id               UUID        NOT NULL DEFAULT gen_random_uuid(),
    comment_id       UUID        NOT NULL,
    previous_content TEXT        NOT NULL,
    edited_by        UUID        NOT NULL,
    edited_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT pk_02_trx_comment_edits          PRIMARY KEY (id),
    CONSTRAINT fk_02_trx_comment_edits_comment  FOREIGN KEY (comment_id)
        REFERENCES "08_comments"."01_fct_comments" (id)
        ON DELETE CASCADE
);

-- ─────────────────────────────────────────────────────────────────────────────
-- TRANSACTION TABLE (03) — Emoji reactions
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS "08_comments"."03_trx_comment_reactions" (
    id            UUID        NOT NULL DEFAULT gen_random_uuid(),
    comment_id    UUID        NOT NULL,
    user_id       UUID        NOT NULL,
    reaction_code TEXT        NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT pk_03_trx_comment_reactions              PRIMARY KEY (id),
    CONSTRAINT uq_03_trx_comment_reactions_dedup        UNIQUE (comment_id, user_id, reaction_code),
    CONSTRAINT fk_03_trx_comment_reactions_comment      FOREIGN KEY (comment_id)
        REFERENCES "08_comments"."01_fct_comments" (id)
        ON DELETE CASCADE,
    CONSTRAINT ck_03_trx_comment_reactions_code         CHECK (reaction_code IN (
        'thumbs_up', 'thumbs_down', 'heart', 'laugh',
        'tada', 'eyes', 'rocket', 'confused'
    ))
);

-- ─────────────────────────────────────────────────────────────────────────────
-- AUDIT TABLE (04) — Comment domain audit log
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS "08_comments"."04_aud_comment_events" (
    id            UUID        NOT NULL DEFAULT gen_random_uuid(),
    comment_id    UUID        NOT NULL,
    entity_type   TEXT        NOT NULL,
    entity_id     UUID        NOT NULL,
    event_type    TEXT        NOT NULL,
    actor_user_id UUID        NOT NULL,
    tenant_key    TEXT        NOT NULL,
    metadata      JSONB       NOT NULL DEFAULT '{}',
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT pk_04_aud_comment_events      PRIMARY KEY (id),
    CONSTRAINT ck_04_aud_event_type          CHECK (event_type IN (
        'created', 'edited', 'deleted',
        'pinned', 'unpinned',
        'resolved', 'unresolved',
        'reaction_added', 'reaction_removed'
    ))
);

-- ─────────────────────────────────────────────────────────────────────────────
-- TRANSACTION TABLE (05) — Comment read-tracking (unread badge support)
--
-- Records the last timestamp at which each user viewed comments for a given
-- entity.  Used to compute unread_count in list responses.
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS "08_comments"."05_trx_comment_views" (
    id              UUID        NOT NULL DEFAULT gen_random_uuid(),
    user_id         UUID        NOT NULL,
    entity_type     TEXT        NOT NULL,
    entity_id       UUID        NOT NULL,
    last_viewed_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT pk_05_trx_comment_views          PRIMARY KEY (id),
    CONSTRAINT uq_05_trx_comment_views_user_entity
        UNIQUE (user_id, entity_type, entity_id),
    CONSTRAINT ck_05_trx_comment_views_entity_type CHECK (entity_type IN (
        'task', 'risk', 'control', 'framework',
        'evidence_template', 'test', 'requirement'
    ))
);

-- ─────────────────────────────────────────────────────────────────────────────
-- TRIGGER — auto-update updated_at on 01_fct_comments
-- ─────────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION "08_comments"."fn_update_comment_timestamp"()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

CREATE OR REPLACE TRIGGER trg_01_fct_comments_updated_at
    BEFORE UPDATE ON "08_comments"."01_fct_comments"
    FOR EACH ROW
    EXECUTE FUNCTION "08_comments"."fn_update_comment_timestamp"();

-- ─────────────────────────────────────────────────────────────────────────────
-- INDEXES
-- ─────────────────────────────────────────────────────────────────────────────

-- ── 01_fct_comments ──────────────────────────────────────────────────────────

-- Primary lookup: entity comments (most critical path for list query)
-- Composite covers entity filter + is_deleted guard + sort in one index scan
CREATE INDEX IF NOT EXISTS idx_01_fct_comments_entity_active
    ON "08_comments"."01_fct_comments" (entity_type, entity_id, is_deleted, created_at DESC)
    WHERE is_deleted = FALSE;

-- Tenant scoping (for admin / cross-entity queries)
CREATE INDEX IF NOT EXISTS idx_01_fct_comments_tenant
    ON "08_comments"."01_fct_comments" (tenant_key)
    WHERE is_deleted = FALSE;

-- "My comments" query: author + tenant
CREATE INDEX IF NOT EXISTS idx_01_fct_comments_author_tenant
    ON "08_comments"."01_fct_comments" (author_user_id, tenant_key)
    WHERE is_deleted = FALSE;

-- Reply threading — partial on non-null parent only
CREATE INDEX IF NOT EXISTS idx_01_fct_comments_parent
    ON "08_comments"."01_fct_comments" (parent_comment_id)
    WHERE parent_comment_id IS NOT NULL;

-- Cursor-based pagination (created_at + id for stable ordering)
CREATE INDEX IF NOT EXISTS idx_01_fct_comments_pagination
    ON "08_comments"."01_fct_comments" (created_at DESC, id)
    WHERE is_deleted = FALSE;

-- @mention lookups (GIN on UUID array column)
CREATE INDEX IF NOT EXISTS idx_01_fct_comments_mentions
    ON "08_comments"."01_fct_comments" USING GIN (mention_user_ids)
    WHERE is_deleted = FALSE;

-- Pinned comments (sparse — most comments not pinned)
CREATE INDEX IF NOT EXISTS idx_01_fct_comments_pinned
    ON "08_comments"."01_fct_comments" (entity_type, entity_id)
    WHERE pinned = TRUE AND is_deleted = FALSE;

-- BRIN index on created_at for time-range queries on large tables (very low write overhead)
CREATE INDEX IF NOT EXISTS idx_01_fct_comments_created_at_brin
    ON "08_comments"."01_fct_comments" USING BRIN (created_at);

-- ── 02_trx_comment_edits ────────────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_02_trx_comment_edits_comment
    ON "08_comments"."02_trx_comment_edits" (comment_id, edited_at DESC);

-- ── 03_trx_comment_reactions ────────────────────────────────────────────────

-- Reactions lookup by comment
CREATE INDEX IF NOT EXISTS idx_03_trx_comment_reactions_comment
    ON "08_comments"."03_trx_comment_reactions" (comment_id);

-- "Did I react?" lookup
CREATE INDEX IF NOT EXISTS idx_03_trx_comment_reactions_user
    ON "08_comments"."03_trx_comment_reactions" (user_id, comment_id);

-- ── 04_aud_comment_events ───────────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_04_aud_comment_events_comment
    ON "08_comments"."04_aud_comment_events" (comment_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_04_aud_comment_events_entity
    ON "08_comments"."04_aud_comment_events" (entity_type, entity_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_04_aud_comment_events_tenant
    ON "08_comments"."04_aud_comment_events" (tenant_key, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_04_aud_comment_events_event_type
    ON "08_comments"."04_aud_comment_events" (event_type, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_04_aud_comment_events_actor
    ON "08_comments"."04_aud_comment_events" (actor_user_id, created_at DESC);

-- NOTE: 04_aud_comment_events intentionally has NO FK to 01_fct_comments.
-- Audit records must persist independently for compliance, even after hard deletes.

-- ── 05_trx_comment_views ────────────────────────────────────────────────────

-- Covered by the UNIQUE constraint (user_id, entity_type, entity_id) which
-- is used for both the upsert and the read.  No additional index needed.
