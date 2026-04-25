-- UP ====

-- product_ops schema + evt_product_events table.
-- Extremely simple Mixpanel/OpenPanel-lite event tracking. Append-only.
-- distinct_id is the caller-supplied stable identifier (anonymous device or
-- user-bound) — Mixpanel convention. actor_user_id is the linked tennetctl
-- user when the caller can resolve one; NULL for anonymous traffic.

CREATE SCHEMA IF NOT EXISTS "10_product_ops";
COMMENT ON SCHEMA "10_product_ops" IS 'Product analytics — append-only event ingestion (Mixpanel/OpenPanel-lite). distinct_id-keyed, JSONB properties.';

CREATE TABLE "10_product_ops"."60_evt_product_events" (
    id              VARCHAR(36)  NOT NULL,
    org_id          VARCHAR(36)  NOT NULL,
    workspace_id    VARCHAR(36)  NULL,
    actor_user_id   VARCHAR(36)  NULL,
    distinct_id     TEXT         NOT NULL,
    event_name      TEXT         NOT NULL,
    session_id      TEXT         NULL,
    source          TEXT         NOT NULL DEFAULT 'web',
    url             TEXT         NULL,
    user_agent      TEXT         NULL,
    ip_addr         INET         NULL,
    properties      JSONB        NOT NULL DEFAULT '{}'::jsonb,
    created_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_evt_product_events      PRIMARY KEY (id),
    CONSTRAINT chk_evt_product_events_src CHECK (source IN ('web','mobile','server','backend','other')),
    CONSTRAINT chk_evt_product_events_event_name_nonempty CHECK (length(event_name) > 0),
    CONSTRAINT chk_evt_product_events_distinct_nonempty   CHECK (length(distinct_id) > 0)
);

CREATE INDEX idx_evt_product_events_org_created         ON "10_product_ops"."60_evt_product_events" (org_id, created_at DESC);
CREATE INDEX idx_evt_product_events_org_event_created   ON "10_product_ops"."60_evt_product_events" (org_id, event_name, created_at DESC);
CREATE INDEX idx_evt_product_events_org_distinct        ON "10_product_ops"."60_evt_product_events" (org_id, distinct_id, created_at DESC);
CREATE INDEX idx_evt_product_events_org_actor_created   ON "10_product_ops"."60_evt_product_events" (org_id, actor_user_id, created_at DESC) WHERE actor_user_id IS NOT NULL;
CREATE INDEX idx_evt_product_events_props_gin           ON "10_product_ops"."60_evt_product_events" USING GIN (properties jsonb_path_ops);

COMMENT ON TABLE  "10_product_ops"."60_evt_product_events" IS 'Append-only product analytics events. distinct_id is the canonical Mixpanel-style identifier; actor_user_id links to fct_users when resolvable. No updated_at, no deleted_at.';
COMMENT ON COLUMN "10_product_ops"."60_evt_product_events".id IS 'UUID v7 of this event.';
COMMENT ON COLUMN "10_product_ops"."60_evt_product_events".org_id IS 'Owning org. Always set; multi-tenant scope.';
COMMENT ON COLUMN "10_product_ops"."60_evt_product_events".workspace_id IS 'Optional workspace scope.';
COMMENT ON COLUMN "10_product_ops"."60_evt_product_events".actor_user_id IS 'Tennetctl user UUID when known; NULL for anonymous events.';
COMMENT ON COLUMN "10_product_ops"."60_evt_product_events".distinct_id IS 'Caller-supplied stable identifier (anonymous device id or user id). Drives grouping (DAU, retention).';
COMMENT ON COLUMN "10_product_ops"."60_evt_product_events".event_name IS 'Free-form event key. e.g. "page.viewed", "button.clicked", "checkout.completed".';
COMMENT ON COLUMN "10_product_ops"."60_evt_product_events".session_id IS 'Caller-supplied session identifier.';
COMMENT ON COLUMN "10_product_ops"."60_evt_product_events".source IS 'web | mobile | server | backend | other.';
COMMENT ON COLUMN "10_product_ops"."60_evt_product_events".url IS 'Page URL at event-time, when applicable.';
COMMENT ON COLUMN "10_product_ops"."60_evt_product_events".user_agent IS 'HTTP User-Agent string.';
COMMENT ON COLUMN "10_product_ops"."60_evt_product_events".ip_addr IS 'Client IP (INET).';
COMMENT ON COLUMN "10_product_ops"."60_evt_product_events".properties IS 'Free-form event payload. JSONB.';
COMMENT ON COLUMN "10_product_ops"."60_evt_product_events".created_at IS 'Event-time at server. Append-only — no updated_at.';

CREATE OR REPLACE VIEW "10_product_ops"."v_product_events" AS
SELECT
    e.id,
    e.org_id,
    e.workspace_id,
    e.actor_user_id,
    e.distinct_id,
    e.event_name,
    e.session_id,
    e.source,
    e.url,
    e.user_agent,
    host(e.ip_addr) AS ip_addr,
    e.properties,
    e.created_at
FROM "10_product_ops"."60_evt_product_events" e;
COMMENT ON VIEW "10_product_ops"."v_product_events" IS 'Read-model for product events. host() drops the /32 CIDR mask from INET when serializing.';

-- DOWN ====

DROP VIEW  IF EXISTS "10_product_ops"."v_product_events";
DROP TABLE IF EXISTS "10_product_ops"."60_evt_product_events";
DROP SCHEMA IF EXISTS "10_product_ops";
