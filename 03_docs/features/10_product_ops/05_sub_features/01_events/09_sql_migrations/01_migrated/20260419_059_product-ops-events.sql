-- UP ====

-- Product Ops events sub-feature: fct_visitors + lnk_visitor_aliases +
-- evt_product_events + evt_attribution_touches + read views + LISTEN/NOTIFY.
--
-- Reference: ADR-030 (audit-vs-product-events split).
--
-- DOCUMENTED EAV EXCEPTION on fct_visitors:
--   The pure-EAV rule (.claude/rules/common/database.md) says fct_* tables MUST
--   NOT carry business columns; everything goes through dtl_attrs. This module
--   takes a NARROW carve-out for first-touch attribution columns (first_utm_*,
--   first_referrer, first_landing_url) per ADR-030, following the same precedent
--   as Phase 13 monitoring fct_* (which keeps OTel resource identity columns
--   first-class because EAV pivot at billion-rows-per-day hot path is unworkable).
--   Justification:
--     1. Funnel + cohort queries (Phase 48) JOIN visitors → events on workspace +
--        time + first_touch — EAV pivot here would force a 6-attr LATERAL join
--        on every funnel step. Untenable as visitor count grows.
--     2. Attribution columns are write-once (first-touch is sticky); they don't
--        change after the visitor's first event. EAV's per-attr versioning
--        provides no value here.
--     3. The exception is narrow: ONLY the 7 attribution columns listed below.
--        All other visitor attrs (display_name, custom traits) go through
--        dtl_attrs via dim_attr_defs.
--   Future visitor attrs added to this carve-out require ADR amendment.
--
-- DOCUMENTED is_test/created_by/updated_by EXCEPTION on fct_visitors:
--   Phase 13 monitoring precedent: instrumentation-emitted rows have no human
--   actor. Visitors are created by anonymous browser hits; there is no user
--   to attribute the row to. is_active + deleted_at + created_at + updated_at
--   are kept (operator may soft-delete a spam visitor, audit when).
--
-- DOCUMENTED is_test/created_by EXCEPTION on lnk_visitor_aliases:
--   Same logic — alias links are written by the system on identify() merge.

-- ========================================================================
-- fct_visitors — anonymous-first identity table with hot-path attribution
-- ========================================================================

CREATE TABLE "10_product_ops"."10_fct_visitors" (
    id                      VARCHAR(36) NOT NULL,
    anonymous_id            TEXT NOT NULL,
    user_id                 VARCHAR(36),
    org_id                  VARCHAR(36) NOT NULL,
    workspace_id            VARCHAR(36) NOT NULL,
    first_seen              TIMESTAMP NOT NULL,
    last_seen               TIMESTAMP NOT NULL,

    -- Hot-path attribution (documented EAV exception, see header)
    first_utm_source_id     SMALLINT,
    first_utm_medium        TEXT,
    first_utm_campaign      TEXT,
    first_utm_term          TEXT,
    first_utm_content       TEXT,
    first_referrer          TEXT,
    first_landing_url       TEXT,

    is_active               BOOLEAN NOT NULL DEFAULT TRUE,
    deleted_at              TIMESTAMP,
    created_at              TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at              TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_fct_visitors PRIMARY KEY (id),
    CONSTRAINT uq_fct_visitors_anonymous_id UNIQUE (anonymous_id),
    CONSTRAINT fk_fct_visitors_first_utm_source
        FOREIGN KEY (first_utm_source_id)
        REFERENCES "10_product_ops"."02_dim_attribution_sources"(id)
);

CREATE INDEX idx_fct_visitors_workspace_last_seen
    ON "10_product_ops"."10_fct_visitors" (workspace_id, last_seen DESC);
CREATE INDEX idx_fct_visitors_user_id
    ON "10_product_ops"."10_fct_visitors" (user_id)
    WHERE user_id IS NOT NULL;
CREATE INDEX idx_fct_visitors_first_utm_source_id
    ON "10_product_ops"."10_fct_visitors" (first_utm_source_id)
    WHERE first_utm_source_id IS NOT NULL;

COMMENT ON TABLE  "10_product_ops"."10_fct_visitors" IS 'Anonymous-first visitor identity. user_id resolves on SDK identify(). First-touch attribution columns are a documented EAV exception (ADR-030 + Phase 13 monitoring precedent).';
COMMENT ON COLUMN "10_product_ops"."10_fct_visitors".id IS 'UUID v7 (VARCHAR(36) per project convention).';
COMMENT ON COLUMN "10_product_ops"."10_fct_visitors".anonymous_id IS 'Stable visitor cookie ID set by browser SDK before identify(). Mixpanel-style two-pointer model.';
COMMENT ON COLUMN "10_product_ops"."10_fct_visitors".user_id IS 'Resolves to fct_users.id after identify(). NULL for anonymous-only visitors.';
COMMENT ON COLUMN "10_product_ops"."10_fct_visitors".workspace_id IS 'Resolved from project_key at ingest. Ingest contract requires workspace; org_id derived from workspace.';
COMMENT ON COLUMN "10_product_ops"."10_fct_visitors".first_utm_source_id IS 'EAV exception (ADR-030): hot-path first-touch attribution. FK to dim_attribution_sources.';
COMMENT ON COLUMN "10_product_ops"."10_fct_visitors".first_landing_url IS 'EAV exception (ADR-030): the URL the visitor first landed on. Useful for entry-page funnels.';

-- ========================================================================
-- lnk_visitor_aliases — many-to-one alias graph
-- ========================================================================
-- A visitor may be seen across multiple devices/cookies. On identify(userId),
-- we merge: keep the existing visitor row, add an alias row pointing the
-- secondary anonymous_id at the canonical visitor.

CREATE TABLE "10_product_ops"."40_lnk_visitor_aliases" (
    id                      VARCHAR(36) NOT NULL,
    visitor_id              VARCHAR(36) NOT NULL,
    alias_anonymous_id      TEXT NOT NULL,
    org_id                  VARCHAR(36) NOT NULL,
    linked_at               TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at              TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_lnk_visitor_aliases PRIMARY KEY (id),
    CONSTRAINT uq_lnk_visitor_aliases_alias UNIQUE (alias_anonymous_id),
    CONSTRAINT fk_lnk_visitor_aliases_visitor
        FOREIGN KEY (visitor_id)
        REFERENCES "10_product_ops"."10_fct_visitors"(id)
        ON DELETE CASCADE
);

CREATE INDEX idx_lnk_visitor_aliases_visitor_id
    ON "10_product_ops"."40_lnk_visitor_aliases" (visitor_id);

COMMENT ON TABLE  "10_product_ops"."40_lnk_visitor_aliases" IS 'Many-to-one alias graph. On identify() race (two anonymous_ids resolve to same user nearly simultaneously), both stay aliased to the user — no canonical-resolution worker needed.';
COMMENT ON COLUMN "10_product_ops"."40_lnk_visitor_aliases".alias_anonymous_id IS 'Secondary anonymous_id; the canonical anonymous_id stays in fct_visitors.anonymous_id.';

-- ========================================================================
-- evt_product_events — RANGE-partitioned by occurred_at daily
-- ========================================================================
-- Composite PK (id, occurred_at) is required by Postgres for partitioned tables
-- (the partition key must be part of the PK / unique constraints).

CREATE TABLE "10_product_ops"."60_evt_product_events" (
    id                      VARCHAR(36) NOT NULL,
    visitor_id              VARCHAR(36) NOT NULL,
    user_id                 VARCHAR(36),
    session_id              VARCHAR(36),
    org_id                  VARCHAR(36) NOT NULL,
    workspace_id            VARCHAR(36) NOT NULL,
    event_kind_id           SMALLINT NOT NULL,
    event_name              TEXT,
    occurred_at             TIMESTAMP NOT NULL,
    page_url                TEXT,
    referrer                TEXT,
    metadata                JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at              TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_evt_product_events PRIMARY KEY (id, occurred_at),
    CONSTRAINT chk_evt_product_events_custom_has_name
        CHECK (event_kind_id <> 2 OR event_name IS NOT NULL),
    CONSTRAINT fk_evt_product_events_event_kind
        FOREIGN KEY (event_kind_id)
        REFERENCES "10_product_ops"."01_dim_event_kinds"(id)
) PARTITION BY RANGE (occurred_at);

-- Pre-create today + tomorrow partitions; daily pg_cron rollover is a 45-x follow-up.
-- (Phase 13 Plan 13-07 deferred its partition manager too.)
CREATE TABLE "10_product_ops"."60_evt_product_events_p_20260419"
    PARTITION OF "10_product_ops"."60_evt_product_events"
    FOR VALUES FROM ('2026-04-19 00:00:00') TO ('2026-04-20 00:00:00');
CREATE TABLE "10_product_ops"."60_evt_product_events_p_20260420"
    PARTITION OF "10_product_ops"."60_evt_product_events"
    FOR VALUES FROM ('2026-04-20 00:00:00') TO ('2026-04-21 00:00:00');

CREATE INDEX idx_evt_product_events_workspace_occurred
    ON "10_product_ops"."60_evt_product_events" (workspace_id, occurred_at DESC);
CREATE INDEX idx_evt_product_events_visitor_occurred
    ON "10_product_ops"."60_evt_product_events" (visitor_id, occurred_at DESC);
CREATE INDEX idx_evt_product_events_user_occurred
    ON "10_product_ops"."60_evt_product_events" (user_id, occurred_at DESC)
    WHERE user_id IS NOT NULL;
CREATE INDEX idx_evt_product_events_event_name_workspace
    ON "10_product_ops"."60_evt_product_events" (workspace_id, event_name)
    WHERE event_name IS NOT NULL;

COMMENT ON TABLE  "10_product_ops"."60_evt_product_events" IS 'Append-only product analytics events. RANGE-partitioned daily by occurred_at. NO updated_at, NO deleted_at (evt convention). One audit row per ingest BATCH (per-event audit bypassed per ADR-030 hot-path bypass).';
COMMENT ON COLUMN "10_product_ops"."60_evt_product_events".visitor_id IS 'Anonymous visitor (the actor for this event).';
COMMENT ON COLUMN "10_product_ops"."60_evt_product_events".event_kind_id IS 'FK to dim_event_kinds. Hides categorical type behind a stable SMALLINT.';
COMMENT ON COLUMN "10_product_ops"."60_evt_product_events".event_name IS 'Required only when event_kind_id = 2 (custom). Cardinality capped at 500 distinct/workspace/day (vault-tunable).';
COMMENT ON COLUMN "10_product_ops"."60_evt_product_events".metadata IS 'Caller-supplied event payload (the SDK''s "properties" argument). JSONB.';
COMMENT ON COLUMN "10_product_ops"."60_evt_product_events".occurred_at IS 'Partition key. Client-side timestamp (occurrence in the browser); created_at is server-side ingest timestamp.';

-- ========================================================================
-- evt_attribution_touches — every UTM/referrer hit
-- ========================================================================

CREATE TABLE "10_product_ops"."60_evt_attribution_touches" (
    id                      VARCHAR(36) NOT NULL,
    visitor_id              VARCHAR(36) NOT NULL,
    org_id                  VARCHAR(36) NOT NULL,
    workspace_id            VARCHAR(36) NOT NULL,
    occurred_at             TIMESTAMP NOT NULL,
    utm_source_id           SMALLINT,
    utm_medium              TEXT,
    utm_campaign            TEXT,
    utm_term                TEXT,
    utm_content             TEXT,
    referrer                TEXT,
    landing_url             TEXT,
    metadata                JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at              TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_evt_attribution_touches PRIMARY KEY (id, occurred_at),
    CONSTRAINT fk_evt_attribution_touches_utm_source
        FOREIGN KEY (utm_source_id)
        REFERENCES "10_product_ops"."02_dim_attribution_sources"(id)
) PARTITION BY RANGE (occurred_at);

CREATE TABLE "10_product_ops"."60_evt_attribution_touches_p_20260419"
    PARTITION OF "10_product_ops"."60_evt_attribution_touches"
    FOR VALUES FROM ('2026-04-19 00:00:00') TO ('2026-04-20 00:00:00');
CREATE TABLE "10_product_ops"."60_evt_attribution_touches_p_20260420"
    PARTITION OF "10_product_ops"."60_evt_attribution_touches"
    FOR VALUES FROM ('2026-04-20 00:00:00') TO ('2026-04-21 00:00:00');

CREATE INDEX idx_evt_attribution_touches_visitor_occurred
    ON "10_product_ops"."60_evt_attribution_touches" (visitor_id, occurred_at DESC);
CREATE INDEX idx_evt_attribution_touches_utm_source_occurred
    ON "10_product_ops"."60_evt_attribution_touches" (utm_source_id, occurred_at DESC)
    WHERE utm_source_id IS NOT NULL;
CREATE INDEX idx_evt_attribution_touches_workspace_occurred
    ON "10_product_ops"."60_evt_attribution_touches" (workspace_id, occurred_at DESC);

COMMENT ON TABLE "10_product_ops"."60_evt_attribution_touches" IS 'Every UTM/referrer touch. Append-only, daily-partitioned. fct_visitors.first_* gets the first row''s values (sticky); subsequent rows update last_seen + last_* on visitors via service logic.';

-- ========================================================================
-- v_visitors — read view (EAV pivot for non-attribution attrs)
-- ========================================================================
-- Phase 3 Plan 04 precedent: MAX(...) FILTER pivot. Single GROUP BY, no LATERAL.
-- Hides internal FK columns (first_utm_source_id → attribution_source TEXT).

CREATE OR REPLACE VIEW "10_product_ops".v_visitors AS
SELECT
    v.id,
    v.anonymous_id,
    v.user_id,
    v.org_id,
    v.workspace_id,
    v.first_seen,
    v.last_seen,
    src.code AS first_utm_source,
    v.first_utm_medium,
    v.first_utm_campaign,
    v.first_utm_term,
    v.first_utm_content,
    v.first_referrer,
    v.first_landing_url,
    v.is_active,
    (v.deleted_at IS NOT NULL) AS is_deleted,
    v.deleted_at,
    v.created_at,
    v.updated_at
FROM "10_product_ops"."10_fct_visitors" v
LEFT JOIN "10_product_ops"."02_dim_attribution_sources" src
       ON src.id = v.first_utm_source_id;

COMMENT ON VIEW "10_product_ops".v_visitors IS 'Read view. Resolves first_utm_source_id → first_utm_source TEXT and exposes is_deleted derived from deleted_at. Hides internal FK columns. Add MAX(...) FILTER EAV pivot here as dtl_attrs grows.';

-- ========================================================================
-- v_product_events — read view
-- ========================================================================

CREATE OR REPLACE VIEW "10_product_ops".v_product_events AS
SELECT
    e.id,
    e.visitor_id,
    e.user_id,
    e.session_id,
    e.org_id,
    e.workspace_id,
    k.code AS event_kind,
    e.event_name,
    e.occurred_at,
    e.page_url,
    e.referrer,
    e.metadata,
    e.created_at
FROM "10_product_ops"."60_evt_product_events" e
JOIN "10_product_ops"."01_dim_event_kinds" k ON k.id = e.event_kind_id;

COMMENT ON VIEW "10_product_ops".v_product_events IS 'Read view. Resolves event_kind_id → event_kind TEXT. Hides internal FK column.';

-- ========================================================================
-- LISTEN/NOTIFY trigger — feeds the admin live-tail UI
-- ========================================================================
-- Phase 10 audit explorer precedent. Payload is a small JSON object so the
-- frontend can render the row optimistically without a follow-up fetch.

CREATE OR REPLACE FUNCTION "10_product_ops".notify_product_event() RETURNS TRIGGER AS $$
BEGIN
    PERFORM pg_notify(
        'product_events',
        json_build_object(
            'id',           NEW.id,
            'visitor_id',   NEW.visitor_id,
            'workspace_id', NEW.workspace_id,
            'event_kind_id',NEW.event_kind_id,
            'event_name',   NEW.event_name,
            'occurred_at',  NEW.occurred_at
        )::text
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_evt_product_events_notify
    AFTER INSERT ON "10_product_ops"."60_evt_product_events"
    FOR EACH ROW EXECUTE FUNCTION "10_product_ops".notify_product_event();

COMMENT ON FUNCTION "10_product_ops".notify_product_event() IS 'Emits pg_notify on channel "product_events" for live-tail UI. Phase 10 audit explorer precedent.';

-- DOWN ====

DROP TRIGGER  IF EXISTS trg_evt_product_events_notify ON "10_product_ops"."60_evt_product_events";
DROP FUNCTION IF EXISTS "10_product_ops".notify_product_event();
DROP VIEW     IF EXISTS "10_product_ops".v_product_events;
DROP VIEW     IF EXISTS "10_product_ops".v_visitors;
DROP TABLE    IF EXISTS "10_product_ops"."60_evt_attribution_touches_p_20260420";
DROP TABLE    IF EXISTS "10_product_ops"."60_evt_attribution_touches_p_20260419";
DROP TABLE    IF EXISTS "10_product_ops"."60_evt_attribution_touches";
DROP TABLE    IF EXISTS "10_product_ops"."60_evt_product_events_p_20260420";
DROP TABLE    IF EXISTS "10_product_ops"."60_evt_product_events_p_20260419";
DROP TABLE    IF EXISTS "10_product_ops"."60_evt_product_events";
DROP TABLE    IF EXISTS "10_product_ops"."40_lnk_visitor_aliases";
DROP TABLE    IF EXISTS "10_product_ops"."10_fct_visitors";
