-- UP ====
-- fct_monitoring_dashboards — user/org-scoped dashboard containers.
-- fct_monitoring_panels     — visualization panels owned by a dashboard.
-- Carve-out: JSONB for `layout`, `dsl`, `grid_pos`, `display_opts` follows the
-- monitoring-saved-queries precedent (catalog-style fct_* with JSON body).
-- TIMESTAMP (UTC) per project convention.

CREATE TABLE IF NOT EXISTS "05_monitoring"."10_fct_monitoring_dashboards" (
    id              VARCHAR(36) NOT NULL,
    org_id          VARCHAR(36) NOT NULL,
    owner_user_id   VARCHAR(36) NOT NULL,
    name            TEXT        NOT NULL,
    description     TEXT        NULL,
    layout          JSONB       NOT NULL DEFAULT '{}'::jsonb,
    shared          BOOLEAN     NOT NULL DEFAULT FALSE,
    is_active       BOOLEAN     NOT NULL DEFAULT TRUE,
    deleted_at      TIMESTAMP   NULL,
    created_at      TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_fct_monitoring_dashboards PRIMARY KEY (id),
    CONSTRAINT chk_fct_monitoring_dashboards_name_nonempty
        CHECK (length(name) >= 1)
);

COMMENT ON TABLE  "05_monitoring"."10_fct_monitoring_dashboards" IS 'Dashboard containers (owner-scoped). shared=true -> same-org visibility.';
COMMENT ON COLUMN "05_monitoring"."10_fct_monitoring_dashboards".id IS 'UUID v7.';
COMMENT ON COLUMN "05_monitoring"."10_fct_monitoring_dashboards".org_id IS 'Scope owner.';
COMMENT ON COLUMN "05_monitoring"."10_fct_monitoring_dashboards".owner_user_id IS 'User who created the dashboard.';
COMMENT ON COLUMN "05_monitoring"."10_fct_monitoring_dashboards".name IS 'Display name. Unique per (org, owner).';
COMMENT ON COLUMN "05_monitoring"."10_fct_monitoring_dashboards".description IS 'Free-form description.';
COMMENT ON COLUMN "05_monitoring"."10_fct_monitoring_dashboards".layout IS 'Dashboard-level layout JSON (grid breakpoints, theme, etc.).';
COMMENT ON COLUMN "05_monitoring"."10_fct_monitoring_dashboards".shared IS 'When true, visible to all users in the same org.';
COMMENT ON COLUMN "05_monitoring"."10_fct_monitoring_dashboards".is_active IS 'Soft-disable flag.';
COMMENT ON COLUMN "05_monitoring"."10_fct_monitoring_dashboards".deleted_at IS 'Soft-delete marker. NULL = live.';
COMMENT ON COLUMN "05_monitoring"."10_fct_monitoring_dashboards".created_at IS 'Creation timestamp (UTC).';
COMMENT ON COLUMN "05_monitoring"."10_fct_monitoring_dashboards".updated_at IS 'Last-update timestamp (UTC).';

CREATE UNIQUE INDEX uq_fct_monitoring_dashboards_owner_name
    ON "05_monitoring"."10_fct_monitoring_dashboards" (org_id, owner_user_id, name)
    WHERE deleted_at IS NULL;

CREATE INDEX idx_fct_monitoring_dashboards_org_active
    ON "05_monitoring"."10_fct_monitoring_dashboards" (org_id, is_active)
    WHERE deleted_at IS NULL;

CREATE INDEX idx_fct_monitoring_dashboards_owner
    ON "05_monitoring"."10_fct_monitoring_dashboards" (owner_user_id)
    WHERE deleted_at IS NULL;


CREATE TABLE IF NOT EXISTS "05_monitoring"."11_fct_monitoring_panels" (
    id              VARCHAR(36) NOT NULL,
    dashboard_id    VARCHAR(36) NOT NULL,
    title           TEXT        NOT NULL,
    panel_type      TEXT        NOT NULL,
    dsl             JSONB       NOT NULL,
    grid_pos        JSONB       NOT NULL DEFAULT '{"x":0,"y":0,"w":6,"h":4}'::jsonb,
    display_opts    JSONB       NOT NULL DEFAULT '{}'::jsonb,
    created_at      TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_fct_monitoring_panels PRIMARY KEY (id),
    CONSTRAINT fk_fct_monitoring_panels_dashboard
        FOREIGN KEY (dashboard_id)
        REFERENCES "05_monitoring"."10_fct_monitoring_dashboards"(id)
        ON DELETE CASCADE,
    CONSTRAINT chk_fct_monitoring_panels_type
        CHECK (panel_type IN ('timeseries','stat','table','log_stream','trace_list')),
    CONSTRAINT chk_fct_monitoring_panels_title_nonempty
        CHECK (length(title) >= 1)
);

COMMENT ON TABLE  "05_monitoring"."11_fct_monitoring_panels" IS 'Panels (tiles) inside a dashboard. Cascade-deletes with parent dashboard.';
COMMENT ON COLUMN "05_monitoring"."11_fct_monitoring_panels".id IS 'UUID v7.';
COMMENT ON COLUMN "05_monitoring"."11_fct_monitoring_panels".dashboard_id IS 'FK -> fct_monitoring_dashboards(id). ON DELETE CASCADE.';
COMMENT ON COLUMN "05_monitoring"."11_fct_monitoring_panels".title IS 'Panel title.';
COMMENT ON COLUMN "05_monitoring"."11_fct_monitoring_panels".panel_type IS 'timeseries | stat | table | log_stream | trace_list.';
COMMENT ON COLUMN "05_monitoring"."11_fct_monitoring_panels".dsl IS 'Query DSL for the panel. JSONB.';
COMMENT ON COLUMN "05_monitoring"."11_fct_monitoring_panels".grid_pos IS 'Grid position {x,y,w,h}. JSONB.';
COMMENT ON COLUMN "05_monitoring"."11_fct_monitoring_panels".display_opts IS 'Per-panel display options (legend, thresholds, colors). JSONB.';
COMMENT ON COLUMN "05_monitoring"."11_fct_monitoring_panels".created_at IS 'Creation timestamp (UTC).';
COMMENT ON COLUMN "05_monitoring"."11_fct_monitoring_panels".updated_at IS 'Last-update timestamp (UTC).';

CREATE INDEX idx_fct_monitoring_panels_dashboard
    ON "05_monitoring"."11_fct_monitoring_panels" (dashboard_id);


CREATE OR REPLACE VIEW "05_monitoring"."v_monitoring_panels" AS
SELECT
    p.id,
    p.dashboard_id,
    p.title,
    p.panel_type,
    p.dsl,
    p.grid_pos,
    p.display_opts,
    p.created_at,
    p.updated_at
FROM "05_monitoring"."11_fct_monitoring_panels" p;

COMMENT ON VIEW "05_monitoring"."v_monitoring_panels" IS 'Read-model for monitoring dashboard panels.';


CREATE OR REPLACE VIEW "05_monitoring"."v_monitoring_dashboards" AS
SELECT
    d.id,
    d.org_id,
    d.owner_user_id,
    d.name,
    d.description,
    d.layout,
    d.shared,
    d.is_active,
    COALESCE(pc.panel_count, 0) AS panel_count,
    d.created_at,
    d.updated_at
FROM "05_monitoring"."10_fct_monitoring_dashboards" d
LEFT JOIN (
    SELECT dashboard_id, COUNT(*)::int AS panel_count
    FROM "05_monitoring"."11_fct_monitoring_panels"
    GROUP BY dashboard_id
) pc ON pc.dashboard_id = d.id
WHERE d.deleted_at IS NULL;

COMMENT ON VIEW "05_monitoring"."v_monitoring_dashboards" IS 'Read-model for monitoring dashboards (excludes soft-deleted). Derives panel_count.';

-- DOWN ====
DROP VIEW  IF EXISTS "05_monitoring"."v_monitoring_dashboards";
DROP VIEW  IF EXISTS "05_monitoring"."v_monitoring_panels";
DROP INDEX IF EXISTS "05_monitoring"."idx_fct_monitoring_panels_dashboard";
DROP TABLE IF EXISTS "05_monitoring"."11_fct_monitoring_panels";
DROP INDEX IF EXISTS "05_monitoring"."idx_fct_monitoring_dashboards_owner";
DROP INDEX IF EXISTS "05_monitoring"."idx_fct_monitoring_dashboards_org_active";
DROP INDEX IF EXISTS "05_monitoring"."uq_fct_monitoring_dashboards_owner_name";
DROP TABLE IF EXISTS "05_monitoring"."10_fct_monitoring_dashboards";
