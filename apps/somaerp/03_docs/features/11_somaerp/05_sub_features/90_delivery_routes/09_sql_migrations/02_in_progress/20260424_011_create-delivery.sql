-- UP ====

-- Delivery layer for somaerp (Plan 56-12).
-- Creates:
--   dim_rider_roles         (universal seeded lookup)
--   fct_delivery_routes     (tenant-scoped named routes anchored to a kitchen)
--   lnk_route_customers     (IMMUTABLE sequence of customers on a route)
--   fct_riders              (rider profiles; optional tennetctl user link)
--   fct_delivery_runs       (a route's run on a specific day by a rider)
--   dtl_delivery_stops      (per-customer stop on a run; status machine)
-- Plus views:
--   v_delivery_routes       (JOIN kitchen + computed customer_count)
--   v_delivery_runs         (JOIN route + rider + computed completion_pct)
--   v_delivery_stops        (JOIN customer + computed delay_sec)
--
-- Rules:
-- * lnk_route_customers is immutable per lnk_ convention (no updated_at/deleted_at).
--   Reorder = DELETE all for route + INSERT new rows in a transaction.
-- * fct_delivery_runs carries mutable lifecycle status (documented deviation
--   per 56-03 SUMMARY — operational unit; stops are the atomic log).
-- * dtl_delivery_stops is soft-delete (dtl_* convention).

-- ── dim_rider_roles ───────────────────────────────────────────────────────

CREATE TABLE "11_somaerp".dim_rider_roles (
    id              SMALLINT NOT NULL,
    code            TEXT NOT NULL,
    name            TEXT NOT NULL,
    deprecated_at   TIMESTAMP,
    CONSTRAINT pk_somaerp_dim_rider_roles PRIMARY KEY (id),
    CONSTRAINT uq_somaerp_dim_rider_roles_code UNIQUE (code)
);
COMMENT ON TABLE  "11_somaerp".dim_rider_roles IS 'Universal rider role taxonomy (owner / contractor / employee / partner / gig).';
COMMENT ON COLUMN "11_somaerp".dim_rider_roles.id IS 'SMALLINT PK, hand-assigned.';
COMMENT ON COLUMN "11_somaerp".dim_rider_roles.code IS 'Stable machine code.';
COMMENT ON COLUMN "11_somaerp".dim_rider_roles.name IS 'Display name.';
COMMENT ON COLUMN "11_somaerp".dim_rider_roles.deprecated_at IS 'Soft-deprecation sentinel.';

-- ── fct_delivery_routes ──────────────────────────────────────────────────

CREATE TABLE "11_somaerp".fct_delivery_routes (
    id                    VARCHAR(36) NOT NULL,
    tenant_id             VARCHAR(36) NOT NULL,
    kitchen_id            VARCHAR(36) NOT NULL,
    name                  TEXT NOT NULL,
    slug                  TEXT NOT NULL,
    area                  TEXT,
    target_window_start   TIME,
    target_window_end     TIME,
    status                TEXT NOT NULL DEFAULT 'active',
    properties            JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at            TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at            TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by            VARCHAR(36) NOT NULL,
    updated_by            VARCHAR(36) NOT NULL,
    deleted_at            TIMESTAMP,
    CONSTRAINT pk_somaerp_fct_delivery_routes PRIMARY KEY (id),
    CONSTRAINT fk_somaerp_fct_delivery_routes_kitchen FOREIGN KEY (kitchen_id)
        REFERENCES "11_somaerp".fct_kitchens(id),
    CONSTRAINT chk_somaerp_fct_delivery_routes_status
        CHECK (status IN ('active','paused','decommissioned')),
    CONSTRAINT chk_somaerp_fct_delivery_routes_window
        CHECK (target_window_end IS NULL OR target_window_start IS NULL
               OR target_window_end > target_window_start)
);
COMMENT ON TABLE  "11_somaerp".fct_delivery_routes IS 'Tenant-scoped named delivery route anchored to a kitchen.';
COMMENT ON COLUMN "11_somaerp".fct_delivery_routes.id IS 'UUID v7.';
COMMENT ON COLUMN "11_somaerp".fct_delivery_routes.tenant_id IS 'tennetctl workspace_id.';
COMMENT ON COLUMN "11_somaerp".fct_delivery_routes.kitchen_id IS 'FK to fct_kitchens.id.';
COMMENT ON COLUMN "11_somaerp".fct_delivery_routes.name IS 'Display name.';
COMMENT ON COLUMN "11_somaerp".fct_delivery_routes.slug IS 'URL-safe slug, unique per tenant.';
COMMENT ON COLUMN "11_somaerp".fct_delivery_routes.area IS 'Free-text area description (e.g. "KPHB Colony").';
COMMENT ON COLUMN "11_somaerp".fct_delivery_routes.target_window_start IS 'Target delivery window start time (local to kitchen).';
COMMENT ON COLUMN "11_somaerp".fct_delivery_routes.target_window_end IS 'Target delivery window end time (local to kitchen).';
COMMENT ON COLUMN "11_somaerp".fct_delivery_routes.status IS 'active | paused | decommissioned.';
COMMENT ON COLUMN "11_somaerp".fct_delivery_routes.properties IS 'JSONB side-channel.';
COMMENT ON COLUMN "11_somaerp".fct_delivery_routes.created_at IS 'App-managed UTC timestamp.';
COMMENT ON COLUMN "11_somaerp".fct_delivery_routes.updated_at IS 'App-managed UTC timestamp.';
COMMENT ON COLUMN "11_somaerp".fct_delivery_routes.created_by IS 'Acting user_id.';
COMMENT ON COLUMN "11_somaerp".fct_delivery_routes.updated_by IS 'Acting user_id.';
COMMENT ON COLUMN "11_somaerp".fct_delivery_routes.deleted_at IS 'Soft-delete sentinel.';

CREATE UNIQUE INDEX idx_somaerp_fct_delivery_routes_tenant_slug
    ON "11_somaerp".fct_delivery_routes(tenant_id, slug)
    WHERE deleted_at IS NULL;
CREATE INDEX idx_somaerp_fct_delivery_routes_tenant_kitchen_status
    ON "11_somaerp".fct_delivery_routes(tenant_id, kitchen_id, status)
    WHERE deleted_at IS NULL;

-- ── lnk_route_customers (IMMUTABLE) ──────────────────────────────────────

CREATE TABLE "11_somaerp".lnk_route_customers (
    id                   VARCHAR(36) NOT NULL,
    tenant_id            VARCHAR(36) NOT NULL,
    route_id             VARCHAR(36) NOT NULL,
    customer_id          VARCHAR(36) NOT NULL,
    sequence_position    INTEGER NOT NULL,
    created_at           TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by           VARCHAR(36) NOT NULL,
    CONSTRAINT pk_somaerp_lnk_route_customers PRIMARY KEY (id),
    CONSTRAINT fk_somaerp_lnk_route_customers_route FOREIGN KEY (route_id)
        REFERENCES "11_somaerp".fct_delivery_routes(id),
    CONSTRAINT fk_somaerp_lnk_route_customers_customer FOREIGN KEY (customer_id)
        REFERENCES "11_somaerp".fct_customers(id)
);
COMMENT ON TABLE  "11_somaerp".lnk_route_customers IS 'IMMUTABLE many-to-many: customer in route sequence. Reorder = DELETE all + INSERT new in tx.';
COMMENT ON COLUMN "11_somaerp".lnk_route_customers.id IS 'UUID v7.';
COMMENT ON COLUMN "11_somaerp".lnk_route_customers.tenant_id IS 'tennetctl workspace_id.';
COMMENT ON COLUMN "11_somaerp".lnk_route_customers.route_id IS 'FK to fct_delivery_routes.id.';
COMMENT ON COLUMN "11_somaerp".lnk_route_customers.customer_id IS 'FK to fct_customers.id.';
COMMENT ON COLUMN "11_somaerp".lnk_route_customers.sequence_position IS '1-based stop ordering on the route.';
COMMENT ON COLUMN "11_somaerp".lnk_route_customers.created_at IS 'App-managed UTC timestamp.';
COMMENT ON COLUMN "11_somaerp".lnk_route_customers.created_by IS 'Acting user_id.';

CREATE UNIQUE INDEX idx_somaerp_lnk_route_customers_route_customer
    ON "11_somaerp".lnk_route_customers(route_id, customer_id);
CREATE UNIQUE INDEX idx_somaerp_lnk_route_customers_route_sequence
    ON "11_somaerp".lnk_route_customers(route_id, sequence_position);
CREATE INDEX idx_somaerp_lnk_route_customers_tenant_customer
    ON "11_somaerp".lnk_route_customers(tenant_id, customer_id);

-- ── fct_riders ───────────────────────────────────────────────────────────

CREATE TABLE "11_somaerp".fct_riders (
    id              VARCHAR(36) NOT NULL,
    tenant_id       VARCHAR(36) NOT NULL,
    user_id         VARCHAR(36),
    name            TEXT NOT NULL,
    phone           TEXT,
    role_id         SMALLINT NOT NULL,
    vehicle_type    TEXT,
    license_number  TEXT,
    status          TEXT NOT NULL DEFAULT 'active',
    properties      JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by      VARCHAR(36) NOT NULL,
    updated_by      VARCHAR(36) NOT NULL,
    deleted_at      TIMESTAMP,
    CONSTRAINT pk_somaerp_fct_riders PRIMARY KEY (id),
    CONSTRAINT fk_somaerp_fct_riders_role FOREIGN KEY (role_id)
        REFERENCES "11_somaerp".dim_rider_roles(id),
    CONSTRAINT chk_somaerp_fct_riders_status
        CHECK (status IN ('active','inactive','suspended'))
);
COMMENT ON TABLE  "11_somaerp".fct_riders IS 'Tenant-scoped rider profiles. user_id links to a tennetctl iam user when present.';
COMMENT ON COLUMN "11_somaerp".fct_riders.id IS 'UUID v7.';
COMMENT ON COLUMN "11_somaerp".fct_riders.tenant_id IS 'tennetctl workspace_id.';
COMMENT ON COLUMN "11_somaerp".fct_riders.user_id IS 'Optional tennetctl iam user_id (cross-system, no FK).';
COMMENT ON COLUMN "11_somaerp".fct_riders.name IS 'Display name.';
COMMENT ON COLUMN "11_somaerp".fct_riders.phone IS 'Contact phone.';
COMMENT ON COLUMN "11_somaerp".fct_riders.role_id IS 'FK to dim_rider_roles.id.';
COMMENT ON COLUMN "11_somaerp".fct_riders.vehicle_type IS 'bike | scooter | van | walking | car | other (free text).';
COMMENT ON COLUMN "11_somaerp".fct_riders.license_number IS 'Driver license number.';
COMMENT ON COLUMN "11_somaerp".fct_riders.status IS 'active | inactive | suspended.';
COMMENT ON COLUMN "11_somaerp".fct_riders.properties IS 'JSONB side-channel.';
COMMENT ON COLUMN "11_somaerp".fct_riders.created_at IS 'App-managed UTC timestamp.';
COMMENT ON COLUMN "11_somaerp".fct_riders.updated_at IS 'App-managed UTC timestamp.';
COMMENT ON COLUMN "11_somaerp".fct_riders.created_by IS 'Acting user_id.';
COMMENT ON COLUMN "11_somaerp".fct_riders.updated_by IS 'Acting user_id.';
COMMENT ON COLUMN "11_somaerp".fct_riders.deleted_at IS 'Soft-delete sentinel.';

CREATE INDEX idx_somaerp_fct_riders_tenant_status
    ON "11_somaerp".fct_riders(tenant_id, status)
    WHERE deleted_at IS NULL;
CREATE INDEX idx_somaerp_fct_riders_tenant_user
    ON "11_somaerp".fct_riders(tenant_id, user_id)
    WHERE deleted_at IS NULL AND user_id IS NOT NULL;

-- ── fct_delivery_runs ────────────────────────────────────────────────────

CREATE TABLE "11_somaerp".fct_delivery_runs (
    id                VARCHAR(36) NOT NULL,
    tenant_id         VARCHAR(36) NOT NULL,
    route_id          VARCHAR(36) NOT NULL,
    rider_id          VARCHAR(36) NOT NULL,
    run_date          DATE NOT NULL,
    status            TEXT NOT NULL DEFAULT 'planned',
    started_at        TIMESTAMP,
    completed_at      TIMESTAMP,
    total_stops       INTEGER NOT NULL DEFAULT 0,
    completed_stops   INTEGER NOT NULL DEFAULT 0,
    missed_stops      INTEGER NOT NULL DEFAULT 0,
    notes             TEXT,
    properties        JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by        VARCHAR(36) NOT NULL,
    updated_by        VARCHAR(36) NOT NULL,
    deleted_at        TIMESTAMP,
    CONSTRAINT pk_somaerp_fct_delivery_runs PRIMARY KEY (id),
    CONSTRAINT fk_somaerp_fct_delivery_runs_route FOREIGN KEY (route_id)
        REFERENCES "11_somaerp".fct_delivery_routes(id),
    CONSTRAINT fk_somaerp_fct_delivery_runs_rider FOREIGN KEY (rider_id)
        REFERENCES "11_somaerp".fct_riders(id),
    CONSTRAINT chk_somaerp_fct_delivery_runs_status
        CHECK (status IN ('planned','in_transit','completed','cancelled')),
    CONSTRAINT chk_somaerp_fct_delivery_runs_dates
        CHECK (completed_at IS NULL OR started_at IS NULL
               OR completed_at >= started_at)
);
COMMENT ON TABLE  "11_somaerp".fct_delivery_runs IS 'A run of a route on a date by a rider. Mutable lifecycle status (documented deviation — operational unit).';
COMMENT ON COLUMN "11_somaerp".fct_delivery_runs.id IS 'UUID v7.';
COMMENT ON COLUMN "11_somaerp".fct_delivery_runs.tenant_id IS 'tennetctl workspace_id.';
COMMENT ON COLUMN "11_somaerp".fct_delivery_runs.route_id IS 'FK to fct_delivery_routes.id.';
COMMENT ON COLUMN "11_somaerp".fct_delivery_runs.rider_id IS 'FK to fct_riders.id.';
COMMENT ON COLUMN "11_somaerp".fct_delivery_runs.run_date IS 'Date of the run (local to kitchen).';
COMMENT ON COLUMN "11_somaerp".fct_delivery_runs.status IS 'planned | in_transit | completed | cancelled.';
COMMENT ON COLUMN "11_somaerp".fct_delivery_runs.started_at IS 'When the rider marked the run as started.';
COMMENT ON COLUMN "11_somaerp".fct_delivery_runs.completed_at IS 'When the run was completed.';
COMMENT ON COLUMN "11_somaerp".fct_delivery_runs.total_stops IS 'Count of dtl_delivery_stops generated at plan time.';
COMMENT ON COLUMN "11_somaerp".fct_delivery_runs.completed_stops IS 'Running count of delivered stops.';
COMMENT ON COLUMN "11_somaerp".fct_delivery_runs.missed_stops IS 'Running count of missed / customer_unavailable stops.';
COMMENT ON COLUMN "11_somaerp".fct_delivery_runs.notes IS 'Operator / rider notes.';
COMMENT ON COLUMN "11_somaerp".fct_delivery_runs.properties IS 'JSONB side-channel.';
COMMENT ON COLUMN "11_somaerp".fct_delivery_runs.created_at IS 'App-managed UTC timestamp.';
COMMENT ON COLUMN "11_somaerp".fct_delivery_runs.updated_at IS 'App-managed UTC timestamp.';
COMMENT ON COLUMN "11_somaerp".fct_delivery_runs.created_by IS 'Acting user_id.';
COMMENT ON COLUMN "11_somaerp".fct_delivery_runs.updated_by IS 'Acting user_id.';
COMMENT ON COLUMN "11_somaerp".fct_delivery_runs.deleted_at IS 'Soft-delete sentinel.';

CREATE UNIQUE INDEX idx_somaerp_fct_delivery_runs_route_date_active
    ON "11_somaerp".fct_delivery_runs(tenant_id, route_id, run_date)
    WHERE deleted_at IS NULL AND status <> 'cancelled';
CREATE INDEX idx_somaerp_fct_delivery_runs_tenant_rider_date
    ON "11_somaerp".fct_delivery_runs(tenant_id, rider_id, run_date DESC)
    WHERE deleted_at IS NULL;
CREATE INDEX idx_somaerp_fct_delivery_runs_tenant_date_status
    ON "11_somaerp".fct_delivery_runs(tenant_id, run_date DESC, status)
    WHERE deleted_at IS NULL;

-- ── dtl_delivery_stops ───────────────────────────────────────────────────

CREATE TABLE "11_somaerp".dtl_delivery_stops (
    id                     VARCHAR(36) NOT NULL,
    tenant_id              VARCHAR(36) NOT NULL,
    delivery_run_id        VARCHAR(36) NOT NULL,
    customer_id            VARCHAR(36) NOT NULL,
    sequence_position      INTEGER NOT NULL,
    scheduled_at           TIMESTAMP,
    actual_at              TIMESTAMP,
    status                 TEXT NOT NULL DEFAULT 'pending',
    photo_vault_key        TEXT,
    signature_vault_key    TEXT,
    notes                  TEXT,
    properties             JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at             TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at             TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by             VARCHAR(36) NOT NULL,
    updated_by             VARCHAR(36) NOT NULL,
    deleted_at             TIMESTAMP,
    CONSTRAINT pk_somaerp_dtl_delivery_stops PRIMARY KEY (id),
    CONSTRAINT fk_somaerp_dtl_delivery_stops_run FOREIGN KEY (delivery_run_id)
        REFERENCES "11_somaerp".fct_delivery_runs(id),
    CONSTRAINT fk_somaerp_dtl_delivery_stops_customer FOREIGN KEY (customer_id)
        REFERENCES "11_somaerp".fct_customers(id),
    CONSTRAINT chk_somaerp_dtl_delivery_stops_status
        CHECK (status IN ('pending','delivered','missed','customer_unavailable','cancelled','rescheduled'))
);
COMMENT ON TABLE  "11_somaerp".dtl_delivery_stops IS 'Per-customer stop on a delivery run. Status machine driven by rider mobile UI.';
COMMENT ON COLUMN "11_somaerp".dtl_delivery_stops.id IS 'UUID v7.';
COMMENT ON COLUMN "11_somaerp".dtl_delivery_stops.tenant_id IS 'tennetctl workspace_id.';
COMMENT ON COLUMN "11_somaerp".dtl_delivery_stops.delivery_run_id IS 'FK to fct_delivery_runs.id.';
COMMENT ON COLUMN "11_somaerp".dtl_delivery_stops.customer_id IS 'FK to fct_customers.id.';
COMMENT ON COLUMN "11_somaerp".dtl_delivery_stops.sequence_position IS 'Snapshot of the route ordering at plan time.';
COMMENT ON COLUMN "11_somaerp".dtl_delivery_stops.scheduled_at IS 'Target timestamp (run_date + route window_start).';
COMMENT ON COLUMN "11_somaerp".dtl_delivery_stops.actual_at IS 'Actual delivery timestamp (set on status=delivered).';
COMMENT ON COLUMN "11_somaerp".dtl_delivery_stops.status IS 'pending | delivered | missed | customer_unavailable | cancelled | rescheduled.';
COMMENT ON COLUMN "11_somaerp".dtl_delivery_stops.photo_vault_key IS 'tennetctl vault key — proof of delivery photo.';
COMMENT ON COLUMN "11_somaerp".dtl_delivery_stops.signature_vault_key IS 'tennetctl vault key — signature blob.';
COMMENT ON COLUMN "11_somaerp".dtl_delivery_stops.notes IS 'Free-text rider notes.';
COMMENT ON COLUMN "11_somaerp".dtl_delivery_stops.properties IS 'JSONB side-channel.';
COMMENT ON COLUMN "11_somaerp".dtl_delivery_stops.created_at IS 'App-managed UTC timestamp.';
COMMENT ON COLUMN "11_somaerp".dtl_delivery_stops.updated_at IS 'App-managed UTC timestamp.';
COMMENT ON COLUMN "11_somaerp".dtl_delivery_stops.created_by IS 'Acting user_id.';
COMMENT ON COLUMN "11_somaerp".dtl_delivery_stops.updated_by IS 'Acting user_id.';
COMMENT ON COLUMN "11_somaerp".dtl_delivery_stops.deleted_at IS 'Soft-delete sentinel.';

CREATE UNIQUE INDEX idx_somaerp_dtl_delivery_stops_run_customer
    ON "11_somaerp".dtl_delivery_stops(delivery_run_id, customer_id)
    WHERE deleted_at IS NULL;
CREATE INDEX idx_somaerp_dtl_delivery_stops_run_seq
    ON "11_somaerp".dtl_delivery_stops(delivery_run_id, sequence_position)
    WHERE deleted_at IS NULL;
CREATE INDEX idx_somaerp_dtl_delivery_stops_tenant_customer
    ON "11_somaerp".dtl_delivery_stops(tenant_id, customer_id, created_at DESC)
    WHERE deleted_at IS NULL;

-- ── Views ────────────────────────────────────────────────────────────────

CREATE VIEW "11_somaerp".v_delivery_routes AS
SELECT
    r.id,
    r.tenant_id,
    r.kitchen_id,
    k.name                          AS kitchen_name,
    r.name,
    r.slug,
    r.area,
    r.target_window_start,
    r.target_window_end,
    r.status,
    r.properties,
    r.created_at,
    r.updated_at,
    r.created_by,
    r.updated_by,
    r.deleted_at,
    COALESCE((
        SELECT COUNT(*)::INT
        FROM "11_somaerp".lnk_route_customers lrc
        WHERE lrc.route_id = r.id
          AND lrc.tenant_id = r.tenant_id
    ), 0)                           AS customer_count
FROM "11_somaerp".fct_delivery_routes r
LEFT JOIN "11_somaerp".fct_kitchens k ON k.id = r.kitchen_id;
COMMENT ON VIEW "11_somaerp".v_delivery_routes IS 'fct_delivery_routes JOIN kitchen + computed customer_count from lnk_route_customers.';

CREATE VIEW "11_somaerp".v_delivery_runs AS
SELECT
    run.id,
    run.tenant_id,
    run.route_id,
    route.name                       AS route_name,
    route.slug                       AS route_slug,
    route.kitchen_id                 AS kitchen_id,
    k.name                           AS kitchen_name,
    run.rider_id,
    rid.name                         AS rider_name,
    rid.phone                        AS rider_phone,
    run.run_date,
    run.status,
    run.started_at,
    run.completed_at,
    run.total_stops,
    run.completed_stops,
    run.missed_stops,
    CASE
        WHEN run.total_stops IS NULL OR run.total_stops = 0 THEN NULL
        ELSE (run.completed_stops::float / run.total_stops::float) * 100.0
    END                              AS completion_pct,
    run.notes,
    run.properties,
    run.created_at,
    run.updated_at,
    run.created_by,
    run.updated_by,
    run.deleted_at
FROM "11_somaerp".fct_delivery_runs run
LEFT JOIN "11_somaerp".fct_delivery_routes route ON route.id = run.route_id
LEFT JOIN "11_somaerp".fct_kitchens         k     ON k.id = route.kitchen_id
LEFT JOIN "11_somaerp".fct_riders           rid   ON rid.id = run.rider_id;
COMMENT ON VIEW "11_somaerp".v_delivery_runs IS 'fct_delivery_runs JOIN route + rider + kitchen + computed completion_pct.';

CREATE VIEW "11_somaerp".v_delivery_stops AS
SELECT
    s.id,
    s.tenant_id,
    s.delivery_run_id,
    s.customer_id,
    c.name                           AS customer_name,
    c.phone                          AS customer_phone,
    c.address_jsonb                  AS customer_address,
    s.sequence_position,
    s.scheduled_at,
    s.actual_at,
    s.status,
    s.photo_vault_key,
    s.signature_vault_key,
    s.notes,
    s.properties,
    CASE
        WHEN s.actual_at IS NULL OR s.scheduled_at IS NULL THEN NULL
        ELSE EXTRACT(EPOCH FROM (s.actual_at - s.scheduled_at))::INT
    END                              AS delay_sec,
    s.created_at,
    s.updated_at,
    s.created_by,
    s.updated_by,
    s.deleted_at
FROM "11_somaerp".dtl_delivery_stops s
LEFT JOIN "11_somaerp".fct_customers c ON c.id = s.customer_id;
COMMENT ON VIEW "11_somaerp".v_delivery_stops IS 'dtl_delivery_stops JOIN customer + computed delay_sec.';


-- DOWN ====

DROP VIEW  IF EXISTS "11_somaerp".v_delivery_stops;
DROP VIEW  IF EXISTS "11_somaerp".v_delivery_runs;
DROP VIEW  IF EXISTS "11_somaerp".v_delivery_routes;

DROP TABLE IF EXISTS "11_somaerp".dtl_delivery_stops;
DROP TABLE IF EXISTS "11_somaerp".fct_delivery_runs;
DROP TABLE IF EXISTS "11_somaerp".fct_riders;
DROP TABLE IF EXISTS "11_somaerp".lnk_route_customers;
DROP TABLE IF EXISTS "11_somaerp".fct_delivery_routes;
DROP TABLE IF EXISTS "11_somaerp".dim_rider_roles;
