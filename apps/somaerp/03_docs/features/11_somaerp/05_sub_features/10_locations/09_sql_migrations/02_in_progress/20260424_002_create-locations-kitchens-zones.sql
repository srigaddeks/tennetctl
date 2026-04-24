-- UP ====================================================================

-- Geography vertical for somaerp (Plan 56-03).
-- Creates: dim_regions + fct_locations + fct_kitchens + fct_service_zones
-- Plus views: v_regions, v_locations, v_kitchens, v_service_zones
--
-- NOTE: kitchen-capacity tables and the current-capacity view are DEFERRED
-- to Plan 56-06. Their FKs need fct_product_lines (catalog, 56-04) and
-- dim_units_of_measure (raw materials, 56-05) which do not exist yet.

-- ── dim_regions ────────────────────────────────────────────────────────

CREATE TABLE "11_somaerp".dim_regions (
    id                      SMALLINT NOT NULL,
    code                    TEXT NOT NULL,
    country_code            CHAR(2) NOT NULL,
    state_name              TEXT NOT NULL,
    regulatory_body         TEXT,
    default_currency_code   CHAR(3) NOT NULL,
    default_timezone        TEXT NOT NULL,
    deprecated_at           TIMESTAMP,
    CONSTRAINT pk_somaerp_dim_regions PRIMARY KEY (id),
    CONSTRAINT uq_somaerp_dim_regions_code UNIQUE (code)
);
COMMENT ON TABLE  "11_somaerp".dim_regions IS 'Country/state lookup — static seed, rare additions on new-country launch. Used for compliance anchoring (FSSAI for IN, FDA for US, EFSA for EU).';
COMMENT ON COLUMN "11_somaerp".dim_regions.id IS 'Permanent manual ID. Never renumber.';
COMMENT ON COLUMN "11_somaerp".dim_regions.code IS 'ISO-style code (IN-TG, IN-KA, US-CA).';
COMMENT ON COLUMN "11_somaerp".dim_regions.country_code IS 'ISO 3166-1 alpha-2 country code.';
COMMENT ON COLUMN "11_somaerp".dim_regions.state_name IS 'State or subregion name.';
COMMENT ON COLUMN "11_somaerp".dim_regions.regulatory_body IS 'Regulatory body name (FSSAI / FDA / EFSA).';
COMMENT ON COLUMN "11_somaerp".dim_regions.default_currency_code IS 'ISO 4217 currency code (INR / USD / EUR).';
COMMENT ON COLUMN "11_somaerp".dim_regions.default_timezone IS 'IANA zone (e.g. Asia/Kolkata).';
COMMENT ON COLUMN "11_somaerp".dim_regions.deprecated_at IS 'Non-null when region is retired. Never delete.';

-- ── fct_locations ──────────────────────────────────────────────────────

CREATE TABLE "11_somaerp".fct_locations (
    id              VARCHAR(36) NOT NULL,
    tenant_id       VARCHAR(36) NOT NULL,
    region_id       SMALLINT NOT NULL,
    name            TEXT NOT NULL,
    slug            TEXT NOT NULL,
    timezone        TEXT NOT NULL,
    properties      JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by      VARCHAR(36) NOT NULL,
    updated_by      VARCHAR(36) NOT NULL,
    deleted_at      TIMESTAMP,
    CONSTRAINT pk_somaerp_fct_locations PRIMARY KEY (id),
    CONSTRAINT fk_somaerp_fct_locations_region FOREIGN KEY (region_id)
        REFERENCES "11_somaerp".dim_regions(id)
);
COMMENT ON TABLE  "11_somaerp".fct_locations IS 'Tenant-scoped city-level location (Hyderabad, Bangalore, ...).';
COMMENT ON COLUMN "11_somaerp".fct_locations.id IS 'UUID v7, app-generated.';
COMMENT ON COLUMN "11_somaerp".fct_locations.tenant_id IS 'tennetctl workspace_id (Soma Delights, ...).';
COMMENT ON COLUMN "11_somaerp".fct_locations.region_id IS 'FK to dim_regions.id.';
COMMENT ON COLUMN "11_somaerp".fct_locations.name IS 'Display name (e.g. Hyderabad).';
COMMENT ON COLUMN "11_somaerp".fct_locations.slug IS 'URL-safe slug, unique per tenant.';
COMMENT ON COLUMN "11_somaerp".fct_locations.timezone IS 'IANA zone; overrides region default if set.';
COMMENT ON COLUMN "11_somaerp".fct_locations.properties IS 'JSONB EAV side-channel (future detail without DDL).';
COMMENT ON COLUMN "11_somaerp".fct_locations.created_at IS 'App-managed UTC timestamp.';
COMMENT ON COLUMN "11_somaerp".fct_locations.updated_at IS 'App-managed UTC timestamp (explicit in every UPDATE).';
COMMENT ON COLUMN "11_somaerp".fct_locations.created_by IS 'Acting tennetctl user_id; bootstrap may be a system uuid.';
COMMENT ON COLUMN "11_somaerp".fct_locations.updated_by IS 'Acting tennetctl user_id.';
COMMENT ON COLUMN "11_somaerp".fct_locations.deleted_at IS 'Soft-delete sentinel; non-null means row is logically deleted.';

CREATE UNIQUE INDEX idx_somaerp_locations_tenant_slug_active
    ON "11_somaerp".fct_locations(tenant_id, slug)
    WHERE deleted_at IS NULL;
CREATE INDEX idx_somaerp_locations_tenant_region
    ON "11_somaerp".fct_locations(tenant_id, region_id)
    WHERE deleted_at IS NULL;

-- ── fct_kitchens ───────────────────────────────────────────────────────

CREATE TABLE "11_somaerp".fct_kitchens (
    id              VARCHAR(36) NOT NULL,
    tenant_id       VARCHAR(36) NOT NULL,
    location_id     VARCHAR(36) NOT NULL,
    name            TEXT NOT NULL,
    slug            TEXT NOT NULL,
    kitchen_type    TEXT NOT NULL,
    address_jsonb   JSONB NOT NULL DEFAULT '{}'::jsonb,
    geo_lat         NUMERIC(9,6),
    geo_lng         NUMERIC(9,6),
    status          TEXT NOT NULL DEFAULT 'active',
    properties      JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by      VARCHAR(36) NOT NULL,
    updated_by      VARCHAR(36) NOT NULL,
    deleted_at      TIMESTAMP,
    CONSTRAINT pk_somaerp_fct_kitchens PRIMARY KEY (id),
    CONSTRAINT fk_somaerp_fct_kitchens_location FOREIGN KEY (location_id)
        REFERENCES "11_somaerp".fct_locations(id),
    CONSTRAINT chk_somaerp_fct_kitchens_type
        CHECK (kitchen_type IN ('home','commissary','satellite')),
    CONSTRAINT chk_somaerp_fct_kitchens_status
        CHECK (status IN ('active','paused','decommissioned'))
);
COMMENT ON TABLE  "11_somaerp".fct_kitchens IS 'Physical production facility within a location. One kitchen = one owner of production batches and inventory.';
COMMENT ON COLUMN "11_somaerp".fct_kitchens.id IS 'UUID v7, app-generated.';
COMMENT ON COLUMN "11_somaerp".fct_kitchens.tenant_id IS 'tennetctl workspace_id.';
COMMENT ON COLUMN "11_somaerp".fct_kitchens.location_id IS 'FK to fct_locations.id.';
COMMENT ON COLUMN "11_somaerp".fct_kitchens.name IS 'Display name (e.g. KPHB Home Kitchen).';
COMMENT ON COLUMN "11_somaerp".fct_kitchens.slug IS 'URL-safe slug, unique per tenant.';
COMMENT ON COLUMN "11_somaerp".fct_kitchens.kitchen_type IS 'home | commissary | satellite — enforced by CHECK constraint.';
COMMENT ON COLUMN "11_somaerp".fct_kitchens.address_jsonb IS 'Structured address (street, city, postal_code, ...).';
COMMENT ON COLUMN "11_somaerp".fct_kitchens.geo_lat IS 'WGS84 latitude (9,6).';
COMMENT ON COLUMN "11_somaerp".fct_kitchens.geo_lng IS 'WGS84 longitude (9,6).';
COMMENT ON COLUMN "11_somaerp".fct_kitchens.status IS 'active | paused | decommissioned. State machine: active<->paused, *->decommissioned (terminal).';
COMMENT ON COLUMN "11_somaerp".fct_kitchens.properties IS 'JSONB EAV side-channel.';
COMMENT ON COLUMN "11_somaerp".fct_kitchens.created_at IS 'App-managed UTC timestamp.';
COMMENT ON COLUMN "11_somaerp".fct_kitchens.updated_at IS 'App-managed UTC timestamp.';
COMMENT ON COLUMN "11_somaerp".fct_kitchens.created_by IS 'Acting user_id.';
COMMENT ON COLUMN "11_somaerp".fct_kitchens.updated_by IS 'Acting user_id.';
COMMENT ON COLUMN "11_somaerp".fct_kitchens.deleted_at IS 'Soft-delete sentinel.';

CREATE UNIQUE INDEX idx_somaerp_kitchens_tenant_slug_active
    ON "11_somaerp".fct_kitchens(tenant_id, slug)
    WHERE deleted_at IS NULL;
CREATE INDEX idx_somaerp_kitchens_tenant_location
    ON "11_somaerp".fct_kitchens(tenant_id, location_id)
    WHERE deleted_at IS NULL;
CREATE INDEX idx_somaerp_kitchens_tenant_status
    ON "11_somaerp".fct_kitchens(tenant_id, status)
    WHERE deleted_at IS NULL;

-- ── fct_service_zones ──────────────────────────────────────────────────

CREATE TABLE "11_somaerp".fct_service_zones (
    id              VARCHAR(36) NOT NULL,
    tenant_id       VARCHAR(36) NOT NULL,
    kitchen_id      VARCHAR(36) NOT NULL,
    name            TEXT NOT NULL,
    polygon_jsonb   JSONB NOT NULL DEFAULT '{}'::jsonb,
    status          TEXT NOT NULL DEFAULT 'active',
    properties      JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by      VARCHAR(36) NOT NULL,
    updated_by      VARCHAR(36) NOT NULL,
    deleted_at      TIMESTAMP,
    CONSTRAINT pk_somaerp_fct_service_zones PRIMARY KEY (id),
    CONSTRAINT fk_somaerp_fct_service_zones_kitchen FOREIGN KEY (kitchen_id)
        REFERENCES "11_somaerp".fct_kitchens(id),
    CONSTRAINT chk_somaerp_fct_service_zones_status
        CHECK (status IN ('active','paused'))
);
COMMENT ON TABLE  "11_somaerp".fct_service_zones IS 'Delivery polygon mapped to the kitchen that serves it (KPHB Cluster 1 -> KPHB Home Kitchen).';
COMMENT ON COLUMN "11_somaerp".fct_service_zones.id IS 'UUID v7, app-generated.';
COMMENT ON COLUMN "11_somaerp".fct_service_zones.tenant_id IS 'tennetctl workspace_id.';
COMMENT ON COLUMN "11_somaerp".fct_service_zones.kitchen_id IS 'FK to fct_kitchens.id.';
COMMENT ON COLUMN "11_somaerp".fct_service_zones.name IS 'Display name (e.g. KPHB Cluster 1).';
COMMENT ON COLUMN "11_somaerp".fct_service_zones.polygon_jsonb IS 'GeoJSON polygon OR pincode list ({"pincodes":["500072","500085"]}).';
COMMENT ON COLUMN "11_somaerp".fct_service_zones.status IS 'active | paused. No decommissioned state — zones are soft-deleted instead.';
COMMENT ON COLUMN "11_somaerp".fct_service_zones.properties IS 'JSONB side-channel.';
COMMENT ON COLUMN "11_somaerp".fct_service_zones.created_at IS 'App-managed UTC timestamp.';
COMMENT ON COLUMN "11_somaerp".fct_service_zones.updated_at IS 'App-managed UTC timestamp.';
COMMENT ON COLUMN "11_somaerp".fct_service_zones.created_by IS 'Acting user_id.';
COMMENT ON COLUMN "11_somaerp".fct_service_zones.updated_by IS 'Acting user_id.';
COMMENT ON COLUMN "11_somaerp".fct_service_zones.deleted_at IS 'Soft-delete sentinel.';

CREATE INDEX idx_somaerp_service_zones_tenant_kitchen
    ON "11_somaerp".fct_service_zones(tenant_id, kitchen_id)
    WHERE deleted_at IS NULL;

-- ── Views ──────────────────────────────────────────────────────────────

CREATE VIEW "11_somaerp".v_regions AS
SELECT
    r.id,
    r.code,
    r.country_code,
    r.state_name,
    r.regulatory_body,
    r.default_currency_code,
    r.default_timezone,
    r.deprecated_at
FROM "11_somaerp".dim_regions r;
COMMENT ON VIEW "11_somaerp".v_regions IS 'Passthrough of dim_regions.';

CREATE VIEW "11_somaerp".v_locations AS
SELECT
    l.id,
    l.tenant_id,
    l.region_id,
    r.code            AS region_code,
    r.country_code    AS country_code,
    r.regulatory_body AS regulatory_body,
    r.default_currency_code,
    r.default_timezone,
    l.name,
    l.slug,
    l.timezone,
    l.properties,
    l.created_at,
    l.updated_at,
    l.created_by,
    l.updated_by,
    l.deleted_at
FROM "11_somaerp".fct_locations l
LEFT JOIN "11_somaerp".dim_regions r ON r.id = l.region_id;
COMMENT ON VIEW "11_somaerp".v_locations IS 'fct_locations joined with dim_regions for region_code / country_code / regulatory_body / currency / tz.';

CREATE VIEW "11_somaerp".v_kitchens AS
SELECT
    k.id,
    k.tenant_id,
    k.location_id,
    l.name            AS location_name,
    l.slug            AS location_slug,
    r.code            AS region_code,
    r.default_currency_code AS currency,
    COALESCE(l.timezone, r.default_timezone) AS tz,
    k.name,
    k.slug,
    k.kitchen_type,
    k.address_jsonb,
    k.geo_lat,
    k.geo_lng,
    k.status,
    k.properties,
    k.created_at,
    k.updated_at,
    k.created_by,
    k.updated_by,
    k.deleted_at
FROM "11_somaerp".fct_kitchens k
LEFT JOIN "11_somaerp".fct_locations l ON l.id = k.location_id
LEFT JOIN "11_somaerp".dim_regions r ON r.id = l.region_id;
COMMENT ON VIEW "11_somaerp".v_kitchens IS 'fct_kitchens joined with fct_locations and dim_regions for location_name, region_code, currency, tz.';

CREATE VIEW "11_somaerp".v_service_zones AS
SELECT
    z.id,
    z.tenant_id,
    z.kitchen_id,
    k.name AS kitchen_name,
    z.name,
    z.polygon_jsonb,
    z.status,
    z.properties,
    z.created_at,
    z.updated_at,
    z.created_by,
    z.updated_by,
    z.deleted_at
FROM "11_somaerp".fct_service_zones z
LEFT JOIN "11_somaerp".fct_kitchens k ON k.id = z.kitchen_id;
COMMENT ON VIEW "11_somaerp".v_service_zones IS 'fct_service_zones joined with fct_kitchens for kitchen_name.';


-- DOWN ==================================================================

-- Drop views first (dependents before dependencies), then tables in
-- reverse-FK order (zones -> kitchens -> locations -> dim_regions).

DROP VIEW IF EXISTS "11_somaerp".v_service_zones;
DROP VIEW IF EXISTS "11_somaerp".v_kitchens;
DROP VIEW IF EXISTS "11_somaerp".v_locations;
DROP VIEW IF EXISTS "11_somaerp".v_regions;

DROP TABLE IF EXISTS "11_somaerp".fct_service_zones;
DROP TABLE IF EXISTS "11_somaerp".fct_kitchens;
DROP TABLE IF EXISTS "11_somaerp".fct_locations;
DROP TABLE IF EXISTS "11_somaerp".dim_regions;
