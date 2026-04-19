-- UP ====

-- product_ops.links — link shortener.
--
-- Slug → target URL mapping with optional UTM preset that gets stitched into
-- the redirect (so /l/launch?utm_source=email implicitly carries the link's
-- preset onward). On every redirect, we emit a `click` event into evt_product_events
-- via the shared ingest path — the link shortener has no dedicated event stream.
--
-- Slug is a user-supplied stable string (operator-curated) OR auto-minted base32
-- on POST when none is provided. UNIQUE per workspace.

CREATE TABLE "10_product_ops"."10_fct_short_links" (
    id              VARCHAR(36) NOT NULL,
    slug            TEXT NOT NULL,
    target_url      TEXT NOT NULL,
    org_id          VARCHAR(36) NOT NULL,
    workspace_id    VARCHAR(36) NOT NULL,
    -- Optional UTM preset stitched into the click event when the redirect fires
    utm_source_id   SMALLINT,
    utm_medium      TEXT,
    utm_campaign    TEXT,
    utm_term        TEXT,
    utm_content     TEXT,
    -- Operational
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_by      VARCHAR(36) NOT NULL,
    deleted_at      TIMESTAMP,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_fct_short_links PRIMARY KEY (id),
    CONSTRAINT uq_fct_short_links_workspace_slug UNIQUE (workspace_id, slug),
    CONSTRAINT fk_fct_short_links_utm_source
        FOREIGN KEY (utm_source_id)
        REFERENCES "10_product_ops"."02_dim_attribution_sources"(id)
);

CREATE INDEX idx_fct_short_links_workspace_active
    ON "10_product_ops"."10_fct_short_links" (workspace_id, is_active)
    WHERE deleted_at IS NULL;

COMMENT ON TABLE  "10_product_ops"."10_fct_short_links" IS 'Link shortener slugs. UNIQUE per workspace; case-sensitive. Click events fire via /l/{slug} redirect into evt_product_events.';
COMMENT ON COLUMN "10_product_ops"."10_fct_short_links".slug IS 'User-supplied or auto-minted base32 (8-12 chars). UNIQUE per workspace.';
COMMENT ON COLUMN "10_product_ops"."10_fct_short_links".target_url IS 'Where the redirect lands. Operator-controlled; no validation beyond non-empty.';
COMMENT ON COLUMN "10_product_ops"."10_fct_short_links".utm_source_id IS 'Optional preset stitched onto click events. FK to dim_attribution_sources.';

-- Read view exposing utm_source as TEXT (mirrors v_visitors / v_product_events pattern)
CREATE OR REPLACE VIEW "10_product_ops".v_short_links AS
SELECT
    l.id,
    l.slug,
    l.target_url,
    l.org_id,
    l.workspace_id,
    src.code AS utm_source,
    l.utm_medium,
    l.utm_campaign,
    l.utm_term,
    l.utm_content,
    l.is_active,
    (l.deleted_at IS NOT NULL) AS is_deleted,
    l.deleted_at,
    l.created_by,
    l.created_at,
    l.updated_at
  FROM "10_product_ops"."10_fct_short_links" l
  LEFT JOIN "10_product_ops"."02_dim_attribution_sources" src
         ON src.id = l.utm_source_id;

COMMENT ON VIEW "10_product_ops".v_short_links IS 'Read view. Resolves utm_source_id → utm_source TEXT, derives is_deleted.';

-- DOWN ====

DROP VIEW  IF EXISTS "10_product_ops".v_short_links;
DROP TABLE IF EXISTS "10_product_ops"."10_fct_short_links";
