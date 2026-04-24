-- UP ====================================================================

-- Raw materials + suppliers vertical for somaerp (Plan 56-05).
-- Creates: dim_raw_material_categories + dim_units_of_measure +
--          dim_supplier_source_types + fct_raw_materials +
--          fct_raw_material_variants + fct_suppliers +
--          lnk_raw_material_suppliers
-- Plus views: v_raw_materials, v_suppliers, v_raw_material_supplier_matrix
--
-- SPEC DEVIATION: lnk_raw_material_suppliers is MUTABLE (has updated_at /
-- updated_by) to support is_primary toggle + last_known_unit_cost refresh
-- per apps/somaerp/03_docs/01_data_model/05_raw_materials.md. This diverges
-- from the project-wide immutable-lnk rule.

-- ── dim_raw_material_categories ────────────────────────────────────────

CREATE TABLE "11_somaerp".dim_raw_material_categories (
    id              SMALLINT NOT NULL,
    code            TEXT NOT NULL,
    name            TEXT NOT NULL,
    deprecated_at   TIMESTAMP,
    CONSTRAINT pk_somaerp_dim_raw_material_categories PRIMARY KEY (id),
    CONSTRAINT uq_somaerp_dim_raw_material_categories_code UNIQUE (code)
);
COMMENT ON TABLE  "11_somaerp".dim_raw_material_categories IS 'Top-level raw material category lookup (leafy_green / root / fruit / herb / spice / packaging / label / consumable). Tenant-shared seed.';
COMMENT ON COLUMN "11_somaerp".dim_raw_material_categories.id IS 'Permanent manual ID. Never renumber.';
COMMENT ON COLUMN "11_somaerp".dim_raw_material_categories.code IS 'Stable lowercase code.';
COMMENT ON COLUMN "11_somaerp".dim_raw_material_categories.name IS 'Human-readable display name.';
COMMENT ON COLUMN "11_somaerp".dim_raw_material_categories.deprecated_at IS 'Non-null when retired. Never delete.';

-- ── dim_units_of_measure ───────────────────────────────────────────────
-- Self-FK on base_unit_id enables unit conversion (g -> kg, ml -> l).

CREATE TABLE "11_somaerp".dim_units_of_measure (
    id              SMALLINT NOT NULL,
    code            TEXT NOT NULL,
    name            TEXT NOT NULL,
    dimension       TEXT NOT NULL,
    base_unit_id    SMALLINT,
    to_base_factor  NUMERIC(20,8) NOT NULL DEFAULT 1,
    deprecated_at   TIMESTAMP,
    CONSTRAINT pk_somaerp_dim_units_of_measure PRIMARY KEY (id),
    CONSTRAINT uq_somaerp_dim_units_of_measure_code UNIQUE (code),
    CONSTRAINT fk_somaerp_dim_units_of_measure_base FOREIGN KEY (base_unit_id)
        REFERENCES "11_somaerp".dim_units_of_measure(id),
    CONSTRAINT chk_somaerp_dim_units_of_measure_dimension
        CHECK (dimension IN ('mass','volume','count'))
);
COMMENT ON TABLE  "11_somaerp".dim_units_of_measure IS 'Unit of measure lookup with self-FK for conversion. Tenant-shared seed.';
COMMENT ON COLUMN "11_somaerp".dim_units_of_measure.id IS 'Permanent manual ID.';
COMMENT ON COLUMN "11_somaerp".dim_units_of_measure.code IS 'Stable code (kg / g / l / ml / count / bunch / bottle).';
COMMENT ON COLUMN "11_somaerp".dim_units_of_measure.name IS 'Human-readable name.';
COMMENT ON COLUMN "11_somaerp".dim_units_of_measure.dimension IS 'mass | volume | count.';
COMMENT ON COLUMN "11_somaerp".dim_units_of_measure.base_unit_id IS 'Self-FK — base unit for conversion. Null if this IS a base unit.';
COMMENT ON COLUMN "11_somaerp".dim_units_of_measure.to_base_factor IS 'Multiplier to convert one of this unit to the base unit (e.g. g->kg = 0.001).';
COMMENT ON COLUMN "11_somaerp".dim_units_of_measure.deprecated_at IS 'Non-null when retired.';

-- ── dim_supplier_source_types ──────────────────────────────────────────

CREATE TABLE "11_somaerp".dim_supplier_source_types (
    id              SMALLINT NOT NULL,
    code            TEXT NOT NULL,
    name            TEXT NOT NULL,
    deprecated_at   TIMESTAMP,
    CONSTRAINT pk_somaerp_dim_supplier_source_types PRIMARY KEY (id),
    CONSTRAINT uq_somaerp_dim_supplier_source_types_code UNIQUE (code)
);
COMMENT ON TABLE  "11_somaerp".dim_supplier_source_types IS 'Supplier source type lookup (wholesale_market / rythu_bazaar / farm_direct / marketplace / brand_distributor / online). Tenant-shared seed.';
COMMENT ON COLUMN "11_somaerp".dim_supplier_source_types.id IS 'Permanent manual ID.';
COMMENT ON COLUMN "11_somaerp".dim_supplier_source_types.code IS 'Stable lowercase code.';
COMMENT ON COLUMN "11_somaerp".dim_supplier_source_types.name IS 'Human-readable name.';
COMMENT ON COLUMN "11_somaerp".dim_supplier_source_types.deprecated_at IS 'Non-null when retired.';

-- ── fct_raw_materials ──────────────────────────────────────────────────

CREATE TABLE "11_somaerp".fct_raw_materials (
    id                        VARCHAR(36) NOT NULL,
    tenant_id                 VARCHAR(36) NOT NULL,
    category_id               SMALLINT NOT NULL,
    name                      TEXT NOT NULL,
    slug                      TEXT NOT NULL,
    default_unit_id           SMALLINT NOT NULL,
    default_shelf_life_hours  INTEGER,
    requires_lot_tracking     BOOLEAN NOT NULL DEFAULT TRUE,
    target_unit_cost          NUMERIC(14,4),
    currency_code             CHAR(3) NOT NULL,
    status                    TEXT NOT NULL DEFAULT 'active',
    properties                JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at                TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at                TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by                VARCHAR(36) NOT NULL,
    updated_by                VARCHAR(36) NOT NULL,
    deleted_at                TIMESTAMP,
    CONSTRAINT pk_somaerp_fct_raw_materials PRIMARY KEY (id),
    CONSTRAINT fk_somaerp_fct_raw_materials_category FOREIGN KEY (category_id)
        REFERENCES "11_somaerp".dim_raw_material_categories(id),
    CONSTRAINT fk_somaerp_fct_raw_materials_default_unit FOREIGN KEY (default_unit_id)
        REFERENCES "11_somaerp".dim_units_of_measure(id),
    CONSTRAINT chk_somaerp_fct_raw_materials_status
        CHECK (status IN ('active','paused','discontinued'))
);
COMMENT ON TABLE  "11_somaerp".fct_raw_materials IS 'Tenant-scoped raw material catalog (spinach, ginger, PET bottles, labels).';
COMMENT ON COLUMN "11_somaerp".fct_raw_materials.id IS 'UUID v7, app-generated.';
COMMENT ON COLUMN "11_somaerp".fct_raw_materials.tenant_id IS 'tennetctl workspace_id.';
COMMENT ON COLUMN "11_somaerp".fct_raw_materials.category_id IS 'FK to dim_raw_material_categories.id.';
COMMENT ON COLUMN "11_somaerp".fct_raw_materials.name IS 'Display name (e.g. Spinach).';
COMMENT ON COLUMN "11_somaerp".fct_raw_materials.slug IS 'URL-safe slug, unique per tenant.';
COMMENT ON COLUMN "11_somaerp".fct_raw_materials.default_unit_id IS 'FK to dim_units_of_measure.id — default unit for this material.';
COMMENT ON COLUMN "11_somaerp".fct_raw_materials.default_shelf_life_hours IS 'Post-procurement freshness window.';
COMMENT ON COLUMN "11_somaerp".fct_raw_materials.requires_lot_tracking IS 'FSSAI default-on — whether lot tracking is required.';
COMMENT ON COLUMN "11_somaerp".fct_raw_materials.target_unit_cost IS 'Target buying price per default_unit.';
COMMENT ON COLUMN "11_somaerp".fct_raw_materials.currency_code IS 'ISO 4217.';
COMMENT ON COLUMN "11_somaerp".fct_raw_materials.status IS 'active | paused | discontinued.';
COMMENT ON COLUMN "11_somaerp".fct_raw_materials.properties IS 'JSONB EAV side-channel (e.g. {"storage":"fridge"}).';
COMMENT ON COLUMN "11_somaerp".fct_raw_materials.created_at IS 'App-managed UTC timestamp.';
COMMENT ON COLUMN "11_somaerp".fct_raw_materials.updated_at IS 'App-managed UTC timestamp.';
COMMENT ON COLUMN "11_somaerp".fct_raw_materials.created_by IS 'Acting user_id.';
COMMENT ON COLUMN "11_somaerp".fct_raw_materials.updated_by IS 'Acting user_id.';
COMMENT ON COLUMN "11_somaerp".fct_raw_materials.deleted_at IS 'Soft-delete sentinel.';

CREATE UNIQUE INDEX idx_somaerp_raw_materials_tenant_slug_active
    ON "11_somaerp".fct_raw_materials(tenant_id, slug)
    WHERE deleted_at IS NULL;
CREATE INDEX idx_somaerp_raw_materials_tenant_cat_status
    ON "11_somaerp".fct_raw_materials(tenant_id, category_id, status)
    WHERE deleted_at IS NULL;

-- ── fct_raw_material_variants ──────────────────────────────────────────

CREATE TABLE "11_somaerp".fct_raw_material_variants (
    id                 VARCHAR(36) NOT NULL,
    tenant_id          VARCHAR(36) NOT NULL,
    raw_material_id    VARCHAR(36) NOT NULL,
    name               TEXT NOT NULL,
    slug               TEXT NOT NULL,
    target_unit_cost   NUMERIC(14,4),
    currency_code      CHAR(3) NOT NULL,
    is_default         BOOLEAN NOT NULL DEFAULT FALSE,
    status             TEXT NOT NULL DEFAULT 'active',
    properties         JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at         TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at         TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by         VARCHAR(36) NOT NULL,
    updated_by         VARCHAR(36) NOT NULL,
    deleted_at         TIMESTAMP,
    CONSTRAINT pk_somaerp_fct_raw_material_variants PRIMARY KEY (id),
    CONSTRAINT fk_somaerp_fct_raw_material_variants_material FOREIGN KEY (raw_material_id)
        REFERENCES "11_somaerp".fct_raw_materials(id),
    CONSTRAINT chk_somaerp_fct_raw_material_variants_status
        CHECK (status IN ('active','paused'))
);
COMMENT ON TABLE  "11_somaerp".fct_raw_material_variants IS 'Optional sub-type of a raw material (Organic Spinach, Ooty Carrot). Exactly one default per material enforced by partial unique index.';
COMMENT ON COLUMN "11_somaerp".fct_raw_material_variants.id IS 'UUID v7.';
COMMENT ON COLUMN "11_somaerp".fct_raw_material_variants.tenant_id IS 'tennetctl workspace_id.';
COMMENT ON COLUMN "11_somaerp".fct_raw_material_variants.raw_material_id IS 'FK to fct_raw_materials.id.';
COMMENT ON COLUMN "11_somaerp".fct_raw_material_variants.name IS 'Display name (e.g. Organic Spinach).';
COMMENT ON COLUMN "11_somaerp".fct_raw_material_variants.slug IS 'URL-safe slug, unique per (tenant, raw_material).';
COMMENT ON COLUMN "11_somaerp".fct_raw_material_variants.target_unit_cost IS 'Variant-specific target buying price.';
COMMENT ON COLUMN "11_somaerp".fct_raw_material_variants.currency_code IS 'ISO 4217.';
COMMENT ON COLUMN "11_somaerp".fct_raw_material_variants.is_default IS 'Exactly one default per material (partial unique index).';
COMMENT ON COLUMN "11_somaerp".fct_raw_material_variants.status IS 'active | paused.';
COMMENT ON COLUMN "11_somaerp".fct_raw_material_variants.properties IS 'JSONB side-channel.';
COMMENT ON COLUMN "11_somaerp".fct_raw_material_variants.created_at IS 'App-managed UTC timestamp.';
COMMENT ON COLUMN "11_somaerp".fct_raw_material_variants.updated_at IS 'App-managed UTC timestamp.';
COMMENT ON COLUMN "11_somaerp".fct_raw_material_variants.created_by IS 'Acting user_id.';
COMMENT ON COLUMN "11_somaerp".fct_raw_material_variants.updated_by IS 'Acting user_id.';
COMMENT ON COLUMN "11_somaerp".fct_raw_material_variants.deleted_at IS 'Soft-delete sentinel.';

CREATE UNIQUE INDEX idx_somaerp_rm_variants_tenant_rm_slug_active
    ON "11_somaerp".fct_raw_material_variants(tenant_id, raw_material_id, slug)
    WHERE deleted_at IS NULL;
CREATE UNIQUE INDEX idx_somaerp_rm_variants_one_default_per_material
    ON "11_somaerp".fct_raw_material_variants(tenant_id, raw_material_id)
    WHERE is_default AND deleted_at IS NULL;
CREATE INDEX idx_somaerp_rm_variants_tenant_material
    ON "11_somaerp".fct_raw_material_variants(tenant_id, raw_material_id)
    WHERE deleted_at IS NULL;

-- ── fct_suppliers ──────────────────────────────────────────────────────

CREATE TABLE "11_somaerp".fct_suppliers (
    id                     VARCHAR(36) NOT NULL,
    tenant_id              VARCHAR(36) NOT NULL,
    name                   TEXT NOT NULL,
    slug                   TEXT NOT NULL,
    source_type_id         SMALLINT NOT NULL,
    location_id            VARCHAR(36),
    contact_jsonb          JSONB NOT NULL DEFAULT '{}'::jsonb,
    payment_terms          TEXT,
    default_currency_code  CHAR(3) NOT NULL,
    quality_rating         SMALLINT,
    status                 TEXT NOT NULL DEFAULT 'active',
    properties             JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at             TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at             TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by             VARCHAR(36) NOT NULL,
    updated_by             VARCHAR(36) NOT NULL,
    deleted_at             TIMESTAMP,
    CONSTRAINT pk_somaerp_fct_suppliers PRIMARY KEY (id),
    CONSTRAINT fk_somaerp_fct_suppliers_source_type FOREIGN KEY (source_type_id)
        REFERENCES "11_somaerp".dim_supplier_source_types(id),
    CONSTRAINT fk_somaerp_fct_suppliers_location FOREIGN KEY (location_id)
        REFERENCES "11_somaerp".fct_locations(id),
    CONSTRAINT chk_somaerp_fct_suppliers_status
        CHECK (status IN ('active','paused','blacklisted')),
    CONSTRAINT chk_somaerp_fct_suppliers_quality_rating
        CHECK (quality_rating IS NULL OR (quality_rating BETWEEN 1 AND 5))
);
COMMENT ON TABLE  "11_somaerp".fct_suppliers IS 'Tenant-scoped vendor directory.';
COMMENT ON COLUMN "11_somaerp".fct_suppliers.id IS 'UUID v7.';
COMMENT ON COLUMN "11_somaerp".fct_suppliers.tenant_id IS 'tennetctl workspace_id.';
COMMENT ON COLUMN "11_somaerp".fct_suppliers.name IS 'Display name (e.g. Bowenpally Wholesale Market).';
COMMENT ON COLUMN "11_somaerp".fct_suppliers.slug IS 'URL-safe slug, unique per tenant.';
COMMENT ON COLUMN "11_somaerp".fct_suppliers.source_type_id IS 'FK to dim_supplier_source_types.id.';
COMMENT ON COLUMN "11_somaerp".fct_suppliers.location_id IS 'FK to fct_locations.id — nullable for marketplace / online suppliers.';
COMMENT ON COLUMN "11_somaerp".fct_suppliers.contact_jsonb IS 'Contact payload {"phone","whatsapp","name"}.';
COMMENT ON COLUMN "11_somaerp".fct_suppliers.payment_terms IS 'Free-text terms (cash_on_delivery / net_7 / prepaid / net_30).';
COMMENT ON COLUMN "11_somaerp".fct_suppliers.default_currency_code IS 'ISO 4217.';
COMMENT ON COLUMN "11_somaerp".fct_suppliers.quality_rating IS '1-5 subjective rating.';
COMMENT ON COLUMN "11_somaerp".fct_suppliers.status IS 'active | paused | blacklisted.';
COMMENT ON COLUMN "11_somaerp".fct_suppliers.properties IS 'JSONB side-channel.';
COMMENT ON COLUMN "11_somaerp".fct_suppliers.created_at IS 'App-managed UTC timestamp.';
COMMENT ON COLUMN "11_somaerp".fct_suppliers.updated_at IS 'App-managed UTC timestamp.';
COMMENT ON COLUMN "11_somaerp".fct_suppliers.created_by IS 'Acting user_id.';
COMMENT ON COLUMN "11_somaerp".fct_suppliers.updated_by IS 'Acting user_id.';
COMMENT ON COLUMN "11_somaerp".fct_suppliers.deleted_at IS 'Soft-delete sentinel.';

CREATE UNIQUE INDEX idx_somaerp_suppliers_tenant_slug_active
    ON "11_somaerp".fct_suppliers(tenant_id, slug)
    WHERE deleted_at IS NULL;
CREATE INDEX idx_somaerp_suppliers_tenant_source_status
    ON "11_somaerp".fct_suppliers(tenant_id, source_type_id, status)
    WHERE deleted_at IS NULL;

-- ── lnk_raw_material_suppliers ─────────────────────────────────────────
-- NOTE: SPEC DEVIATION — this link is MUTABLE (has updated_at / updated_by)
-- to support is_primary toggle + last_known_unit_cost refresh. Hard-delete
-- only (no deleted_at). See data-model spec § lnk_raw_material_suppliers.

CREATE TABLE "11_somaerp".lnk_raw_material_suppliers (
    id                     VARCHAR(36) NOT NULL,
    tenant_id              VARCHAR(36) NOT NULL,
    raw_material_id        VARCHAR(36) NOT NULL,
    supplier_id            VARCHAR(36) NOT NULL,
    is_primary             BOOLEAN NOT NULL DEFAULT FALSE,
    last_known_unit_cost   NUMERIC(14,4),
    currency_code          CHAR(3) NOT NULL,
    notes                  TEXT,
    created_at             TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at             TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by             VARCHAR(36) NOT NULL,
    updated_by             VARCHAR(36) NOT NULL,
    CONSTRAINT pk_somaerp_lnk_raw_material_suppliers PRIMARY KEY (id),
    CONSTRAINT fk_somaerp_lnk_rms_material FOREIGN KEY (raw_material_id)
        REFERENCES "11_somaerp".fct_raw_materials(id),
    CONSTRAINT fk_somaerp_lnk_rms_supplier FOREIGN KEY (supplier_id)
        REFERENCES "11_somaerp".fct_suppliers(id),
    CONSTRAINT uq_somaerp_lnk_rms_tenant_material_supplier
        UNIQUE (tenant_id, raw_material_id, supplier_id)
);
COMMENT ON TABLE  "11_somaerp".lnk_raw_material_suppliers IS 'Many-to-many raw_material <-> supplier with primary/backup designation. MUTABLE (spec deviation) for is_primary + last_known_unit_cost.';
COMMENT ON COLUMN "11_somaerp".lnk_raw_material_suppliers.id IS 'UUID v7.';
COMMENT ON COLUMN "11_somaerp".lnk_raw_material_suppliers.tenant_id IS 'tennetctl workspace_id.';
COMMENT ON COLUMN "11_somaerp".lnk_raw_material_suppliers.raw_material_id IS 'FK to fct_raw_materials.id.';
COMMENT ON COLUMN "11_somaerp".lnk_raw_material_suppliers.supplier_id IS 'FK to fct_suppliers.id.';
COMMENT ON COLUMN "11_somaerp".lnk_raw_material_suppliers.is_primary IS 'Exactly one primary per material enforced by partial unique index.';
COMMENT ON COLUMN "11_somaerp".lnk_raw_material_suppliers.last_known_unit_cost IS 'Refreshed by procurement layer after received movements.';
COMMENT ON COLUMN "11_somaerp".lnk_raw_material_suppliers.currency_code IS 'ISO 4217.';
COMMENT ON COLUMN "11_somaerp".lnk_raw_material_suppliers.notes IS 'Free-text notes.';
COMMENT ON COLUMN "11_somaerp".lnk_raw_material_suppliers.created_at IS 'App-managed UTC timestamp.';
COMMENT ON COLUMN "11_somaerp".lnk_raw_material_suppliers.updated_at IS 'App-managed UTC timestamp.';
COMMENT ON COLUMN "11_somaerp".lnk_raw_material_suppliers.created_by IS 'Acting user_id.';
COMMENT ON COLUMN "11_somaerp".lnk_raw_material_suppliers.updated_by IS 'Acting user_id.';

CREATE UNIQUE INDEX idx_somaerp_lnk_rms_one_primary_per_material
    ON "11_somaerp".lnk_raw_material_suppliers(tenant_id, raw_material_id)
    WHERE is_primary;
CREATE INDEX idx_somaerp_lnk_rms_tenant_material_primary
    ON "11_somaerp".lnk_raw_material_suppliers(tenant_id, raw_material_id, is_primary DESC);
CREATE INDEX idx_somaerp_lnk_rms_tenant_supplier_material
    ON "11_somaerp".lnk_raw_material_suppliers(tenant_id, supplier_id, raw_material_id);

-- ── Views ──────────────────────────────────────────────────────────────

CREATE VIEW "11_somaerp".v_raw_materials AS
SELECT
    rm.id,
    rm.tenant_id,
    rm.category_id,
    cat.code            AS category_code,
    cat.name            AS category_name,
    rm.name,
    rm.slug,
    rm.default_unit_id,
    u.code              AS default_unit_code,
    u.name              AS default_unit_name,
    u.dimension         AS default_unit_dimension,
    rm.default_shelf_life_hours,
    rm.requires_lot_tracking,
    rm.target_unit_cost,
    rm.currency_code,
    rm.status,
    rm.properties,
    rm.created_at,
    rm.updated_at,
    rm.created_by,
    rm.updated_by,
    rm.deleted_at
FROM "11_somaerp".fct_raw_materials rm
LEFT JOIN "11_somaerp".dim_raw_material_categories cat ON cat.id = rm.category_id
LEFT JOIN "11_somaerp".dim_units_of_measure u ON u.id = rm.default_unit_id;
COMMENT ON VIEW "11_somaerp".v_raw_materials IS 'fct_raw_materials joined with dim_raw_material_categories + dim_units_of_measure.';

CREATE VIEW "11_somaerp".v_suppliers AS
SELECT
    s.id,
    s.tenant_id,
    s.name,
    s.slug,
    s.source_type_id,
    st.code             AS source_type_code,
    st.name             AS source_type_name,
    s.location_id,
    loc.name            AS location_name,
    s.contact_jsonb,
    s.payment_terms,
    s.default_currency_code,
    s.quality_rating,
    s.status,
    s.properties,
    s.created_at,
    s.updated_at,
    s.created_by,
    s.updated_by,
    s.deleted_at
FROM "11_somaerp".fct_suppliers s
LEFT JOIN "11_somaerp".dim_supplier_source_types st ON st.id = s.source_type_id
LEFT JOIN "11_somaerp".fct_locations loc ON loc.id = s.location_id;
COMMENT ON VIEW "11_somaerp".v_suppliers IS 'fct_suppliers joined with dim_supplier_source_types + fct_locations (nullable).';

CREATE VIEW "11_somaerp".v_raw_material_supplier_matrix AS
SELECT
    lnk.id,
    lnk.tenant_id,
    lnk.raw_material_id,
    rm.name             AS material_name,
    rm.slug             AS material_slug,
    lnk.supplier_id,
    s.name              AS supplier_name,
    s.slug              AS supplier_slug,
    st.code             AS source_type_code,
    lnk.is_primary,
    lnk.last_known_unit_cost,
    lnk.currency_code,
    lnk.notes,
    lnk.created_at,
    lnk.updated_at,
    lnk.created_by,
    lnk.updated_by
FROM "11_somaerp".lnk_raw_material_suppliers lnk
LEFT JOIN "11_somaerp".fct_raw_materials rm ON rm.id = lnk.raw_material_id
LEFT JOIN "11_somaerp".fct_suppliers s ON s.id = lnk.supplier_id
LEFT JOIN "11_somaerp".dim_supplier_source_types st ON st.id = s.source_type_id;
COMMENT ON VIEW "11_somaerp".v_raw_material_supplier_matrix IS 'Per-(material, supplier) pair view for procurement planner.';


-- DOWN ==================================================================

DROP VIEW IF EXISTS "11_somaerp".v_raw_material_supplier_matrix;
DROP VIEW IF EXISTS "11_somaerp".v_suppliers;
DROP VIEW IF EXISTS "11_somaerp".v_raw_materials;

DROP TABLE IF EXISTS "11_somaerp".lnk_raw_material_suppliers;
DROP TABLE IF EXISTS "11_somaerp".fct_raw_material_variants;
DROP TABLE IF EXISTS "11_somaerp".fct_suppliers;
DROP TABLE IF EXISTS "11_somaerp".fct_raw_materials;
DROP TABLE IF EXISTS "11_somaerp".dim_supplier_source_types;
DROP TABLE IF EXISTS "11_somaerp".dim_units_of_measure;
DROP TABLE IF EXISTS "11_somaerp".dim_raw_material_categories;
