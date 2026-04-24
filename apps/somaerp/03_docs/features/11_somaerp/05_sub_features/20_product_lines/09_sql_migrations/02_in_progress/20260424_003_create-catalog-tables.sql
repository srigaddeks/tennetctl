-- UP ====================================================================

-- Catalog vertical for somaerp (Plan 56-04).
-- Creates: dim_product_categories + dim_product_tags + fct_product_lines +
-- fct_products + fct_product_variants + lnk_product_tags
-- Plus views: v_product_lines, v_products, v_product_variants
--
-- Cross-layer:
--   fct_product_lines.id is referenced by fct_kitchen_capacity (56-06)
--   fct_products.id is referenced by fct_recipes (56-07), production (56-10),
--   subscriptions (56-11).

-- ── dim_product_categories ─────────────────────────────────────────────

CREATE TABLE "11_somaerp".dim_product_categories (
    id              SMALLINT NOT NULL,
    code            TEXT NOT NULL,
    name            TEXT NOT NULL,
    deprecated_at   TIMESTAMP,
    CONSTRAINT pk_somaerp_dim_product_categories PRIMARY KEY (id),
    CONSTRAINT uq_somaerp_dim_product_categories_code UNIQUE (code)
);
COMMENT ON TABLE  "11_somaerp".dim_product_categories IS 'Top-level product category lookup (beverage / shot / pulp / packaged_food). Tenant-shared seed.';
COMMENT ON COLUMN "11_somaerp".dim_product_categories.id IS 'Permanent manual ID. Never renumber.';
COMMENT ON COLUMN "11_somaerp".dim_product_categories.code IS 'Stable lowercase code (beverage / shot / pulp / packaged_food).';
COMMENT ON COLUMN "11_somaerp".dim_product_categories.name IS 'Human-readable display name.';
COMMENT ON COLUMN "11_somaerp".dim_product_categories.deprecated_at IS 'Non-null when category is retired. Never delete.';

-- ── dim_product_tags ───────────────────────────────────────────────────

CREATE TABLE "11_somaerp".dim_product_tags (
    id              SMALLINT NOT NULL,
    code            TEXT NOT NULL,
    name            TEXT NOT NULL,
    deprecated_at   TIMESTAMP,
    CONSTRAINT pk_somaerp_dim_product_tags PRIMARY KEY (id),
    CONSTRAINT uq_somaerp_dim_product_tags_code UNIQUE (code)
);
COMMENT ON TABLE  "11_somaerp".dim_product_tags IS 'Wellness benefit tag lookup (immunity / energy / detox / hydration / skin / gut / endurance). Tenant-shared seed.';
COMMENT ON COLUMN "11_somaerp".dim_product_tags.id IS 'Permanent manual ID.';
COMMENT ON COLUMN "11_somaerp".dim_product_tags.code IS 'Stable lowercase code.';
COMMENT ON COLUMN "11_somaerp".dim_product_tags.name IS 'Human-readable display name.';

-- ── fct_product_lines ──────────────────────────────────────────────────

CREATE TABLE "11_somaerp".fct_product_lines (
    id              VARCHAR(36) NOT NULL,
    tenant_id       VARCHAR(36) NOT NULL,
    category_id     SMALLINT NOT NULL,
    name            TEXT NOT NULL,
    slug            TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'active',
    properties      JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by      VARCHAR(36) NOT NULL,
    updated_by      VARCHAR(36) NOT NULL,
    deleted_at      TIMESTAMP,
    CONSTRAINT pk_somaerp_fct_product_lines PRIMARY KEY (id),
    CONSTRAINT fk_somaerp_fct_product_lines_category FOREIGN KEY (category_id)
        REFERENCES "11_somaerp".dim_product_categories(id),
    CONSTRAINT chk_somaerp_fct_product_lines_status
        CHECK (status IN ('active','paused','discontinued'))
);
COMMENT ON TABLE  "11_somaerp".fct_product_lines IS 'Tenant-scoped grouping of products sharing production characteristics. Capacity lives per-line, not per-product.';
COMMENT ON COLUMN "11_somaerp".fct_product_lines.id IS 'UUID v7, app-generated.';
COMMENT ON COLUMN "11_somaerp".fct_product_lines.tenant_id IS 'tennetctl workspace_id.';
COMMENT ON COLUMN "11_somaerp".fct_product_lines.category_id IS 'FK to dim_product_categories.id.';
COMMENT ON COLUMN "11_somaerp".fct_product_lines.name IS 'Display name (e.g. Cold-Pressed Drinks).';
COMMENT ON COLUMN "11_somaerp".fct_product_lines.slug IS 'URL-safe slug, unique per tenant.';
COMMENT ON COLUMN "11_somaerp".fct_product_lines.status IS 'active | paused | discontinued.';
COMMENT ON COLUMN "11_somaerp".fct_product_lines.properties IS 'JSONB EAV side-channel (e.g. default_shelf_life_hours).';
COMMENT ON COLUMN "11_somaerp".fct_product_lines.created_at IS 'App-managed UTC timestamp.';
COMMENT ON COLUMN "11_somaerp".fct_product_lines.updated_at IS 'App-managed UTC timestamp.';
COMMENT ON COLUMN "11_somaerp".fct_product_lines.created_by IS 'Acting user_id.';
COMMENT ON COLUMN "11_somaerp".fct_product_lines.updated_by IS 'Acting user_id.';
COMMENT ON COLUMN "11_somaerp".fct_product_lines.deleted_at IS 'Soft-delete sentinel.';

CREATE UNIQUE INDEX idx_somaerp_product_lines_tenant_slug_active
    ON "11_somaerp".fct_product_lines(tenant_id, slug)
    WHERE deleted_at IS NULL;
CREATE INDEX idx_somaerp_product_lines_tenant_status
    ON "11_somaerp".fct_product_lines(tenant_id, status)
    WHERE deleted_at IS NULL;

-- ── fct_products ───────────────────────────────────────────────────────

CREATE TABLE "11_somaerp".fct_products (
    id                           VARCHAR(36) NOT NULL,
    tenant_id                    VARCHAR(36) NOT NULL,
    product_line_id              VARCHAR(36) NOT NULL,
    name                         TEXT NOT NULL,
    slug                         TEXT NOT NULL,
    description                  TEXT,
    target_benefit               TEXT,
    default_serving_size_ml      NUMERIC(8,2),
    default_shelf_life_hours     INTEGER,
    target_cogs_amount           NUMERIC(14,4),
    default_selling_price        NUMERIC(14,4),
    currency_code                CHAR(3) NOT NULL,
    status                       TEXT NOT NULL DEFAULT 'active',
    properties                   JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at                   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at                   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by                   VARCHAR(36) NOT NULL,
    updated_by                   VARCHAR(36) NOT NULL,
    deleted_at                   TIMESTAMP,
    CONSTRAINT pk_somaerp_fct_products PRIMARY KEY (id),
    CONSTRAINT fk_somaerp_fct_products_product_line FOREIGN KEY (product_line_id)
        REFERENCES "11_somaerp".fct_product_lines(id),
    CONSTRAINT chk_somaerp_fct_products_status
        CHECK (status IN ('active','paused','discontinued'))
);
COMMENT ON TABLE  "11_somaerp".fct_products IS 'Tenant-scoped SKU — one saleable product (e.g. Green Morning 300ml).';
COMMENT ON COLUMN "11_somaerp".fct_products.id IS 'UUID v7.';
COMMENT ON COLUMN "11_somaerp".fct_products.tenant_id IS 'tennetctl workspace_id.';
COMMENT ON COLUMN "11_somaerp".fct_products.product_line_id IS 'FK to fct_product_lines.id.';
COMMENT ON COLUMN "11_somaerp".fct_products.name IS 'Display name.';
COMMENT ON COLUMN "11_somaerp".fct_products.slug IS 'URL-safe slug, unique per tenant.';
COMMENT ON COLUMN "11_somaerp".fct_products.description IS 'Longer description / ingredients.';
COMMENT ON COLUMN "11_somaerp".fct_products.target_benefit IS 'Marketing benefit statement.';
COMMENT ON COLUMN "11_somaerp".fct_products.default_serving_size_ml IS 'Default bottle size in ml; nullable for non-liquid.';
COMMENT ON COLUMN "11_somaerp".fct_products.default_shelf_life_hours IS 'Default shelf life in hours.';
COMMENT ON COLUMN "11_somaerp".fct_products.target_cogs_amount IS 'Target cost of goods, tenant currency.';
COMMENT ON COLUMN "11_somaerp".fct_products.default_selling_price IS 'Default selling price, tenant currency.';
COMMENT ON COLUMN "11_somaerp".fct_products.currency_code IS 'ISO 4217 currency code (INR/USD/EUR).';
COMMENT ON COLUMN "11_somaerp".fct_products.status IS 'active | paused | discontinued.';
COMMENT ON COLUMN "11_somaerp".fct_products.properties IS 'JSONB EAV side-channel for tenant-specific SKU attributes.';
COMMENT ON COLUMN "11_somaerp".fct_products.created_at IS 'App-managed UTC timestamp.';
COMMENT ON COLUMN "11_somaerp".fct_products.updated_at IS 'App-managed UTC timestamp.';
COMMENT ON COLUMN "11_somaerp".fct_products.created_by IS 'Acting user_id.';
COMMENT ON COLUMN "11_somaerp".fct_products.updated_by IS 'Acting user_id.';
COMMENT ON COLUMN "11_somaerp".fct_products.deleted_at IS 'Soft-delete sentinel.';

CREATE UNIQUE INDEX idx_somaerp_products_tenant_slug_active
    ON "11_somaerp".fct_products(tenant_id, slug)
    WHERE deleted_at IS NULL;
CREATE INDEX idx_somaerp_products_tenant_line_status
    ON "11_somaerp".fct_products(tenant_id, product_line_id, status)
    WHERE deleted_at IS NULL;

-- ── fct_product_variants ───────────────────────────────────────────────

CREATE TABLE "11_somaerp".fct_product_variants (
    id                  VARCHAR(36) NOT NULL,
    tenant_id           VARCHAR(36) NOT NULL,
    product_id          VARCHAR(36) NOT NULL,
    name                TEXT NOT NULL,
    slug                TEXT NOT NULL,
    serving_size_ml     NUMERIC(8,2),
    selling_price       NUMERIC(14,4),
    currency_code       CHAR(3) NOT NULL,
    is_default          BOOLEAN NOT NULL DEFAULT FALSE,
    status              TEXT NOT NULL DEFAULT 'active',
    properties          JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by          VARCHAR(36) NOT NULL,
    updated_by          VARCHAR(36) NOT NULL,
    deleted_at          TIMESTAMP,
    CONSTRAINT pk_somaerp_fct_product_variants PRIMARY KEY (id),
    CONSTRAINT fk_somaerp_fct_product_variants_product FOREIGN KEY (product_id)
        REFERENCES "11_somaerp".fct_products(id),
    CONSTRAINT chk_somaerp_fct_product_variants_status
        CHECK (status IN ('active','paused'))
);
COMMENT ON TABLE  "11_somaerp".fct_product_variants IS 'Size / packaging variant of a product. Exactly one default per product enforced by partial unique index.';
COMMENT ON COLUMN "11_somaerp".fct_product_variants.id IS 'UUID v7.';
COMMENT ON COLUMN "11_somaerp".fct_product_variants.tenant_id IS 'tennetctl workspace_id.';
COMMENT ON COLUMN "11_somaerp".fct_product_variants.product_id IS 'FK to fct_products.id.';
COMMENT ON COLUMN "11_somaerp".fct_product_variants.name IS 'Display name (e.g. 300ml PET).';
COMMENT ON COLUMN "11_somaerp".fct_product_variants.slug IS 'URL-safe slug, unique per (tenant, product).';
COMMENT ON COLUMN "11_somaerp".fct_product_variants.serving_size_ml IS 'Variant-specific serving size (ml).';
COMMENT ON COLUMN "11_somaerp".fct_product_variants.selling_price IS 'Variant-specific selling price.';
COMMENT ON COLUMN "11_somaerp".fct_product_variants.currency_code IS 'ISO 4217.';
COMMENT ON COLUMN "11_somaerp".fct_product_variants.is_default IS 'Exactly one default per product (enforced by partial unique index).';
COMMENT ON COLUMN "11_somaerp".fct_product_variants.status IS 'active | paused.';
COMMENT ON COLUMN "11_somaerp".fct_product_variants.properties IS 'JSONB side-channel.';
COMMENT ON COLUMN "11_somaerp".fct_product_variants.created_at IS 'App-managed UTC timestamp.';
COMMENT ON COLUMN "11_somaerp".fct_product_variants.updated_at IS 'App-managed UTC timestamp.';
COMMENT ON COLUMN "11_somaerp".fct_product_variants.created_by IS 'Acting user_id.';
COMMENT ON COLUMN "11_somaerp".fct_product_variants.updated_by IS 'Acting user_id.';
COMMENT ON COLUMN "11_somaerp".fct_product_variants.deleted_at IS 'Soft-delete sentinel.';

CREATE UNIQUE INDEX idx_somaerp_product_variants_tenant_prod_slug_active
    ON "11_somaerp".fct_product_variants(tenant_id, product_id, slug)
    WHERE deleted_at IS NULL;
CREATE UNIQUE INDEX idx_somaerp_product_variants_one_default_per_product
    ON "11_somaerp".fct_product_variants(tenant_id, product_id)
    WHERE is_default AND deleted_at IS NULL;
CREATE INDEX idx_somaerp_product_variants_tenant_product
    ON "11_somaerp".fct_product_variants(tenant_id, product_id)
    WHERE deleted_at IS NULL;

-- ── lnk_product_tags ───────────────────────────────────────────────────
-- Immutable join per database conventions: no updated_at, no deleted_at.

CREATE TABLE "11_somaerp".lnk_product_tags (
    tenant_id       VARCHAR(36) NOT NULL,
    product_id      VARCHAR(36) NOT NULL,
    tag_id          SMALLINT NOT NULL,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by      VARCHAR(36) NOT NULL,
    CONSTRAINT pk_somaerp_lnk_product_tags PRIMARY KEY (tenant_id, product_id, tag_id),
    CONSTRAINT fk_somaerp_lnk_product_tags_product FOREIGN KEY (product_id)
        REFERENCES "11_somaerp".fct_products(id),
    CONSTRAINT fk_somaerp_lnk_product_tags_tag FOREIGN KEY (tag_id)
        REFERENCES "11_somaerp".dim_product_tags(id)
);
COMMENT ON TABLE  "11_somaerp".lnk_product_tags IS 'Immutable product ↔ tag join. Hard-delete only.';
COMMENT ON COLUMN "11_somaerp".lnk_product_tags.tenant_id IS 'tennetctl workspace_id.';
COMMENT ON COLUMN "11_somaerp".lnk_product_tags.product_id IS 'FK to fct_products.id.';
COMMENT ON COLUMN "11_somaerp".lnk_product_tags.tag_id IS 'FK to dim_product_tags.id.';
COMMENT ON COLUMN "11_somaerp".lnk_product_tags.created_at IS 'App-managed UTC timestamp.';
COMMENT ON COLUMN "11_somaerp".lnk_product_tags.created_by IS 'Acting user_id.';

CREATE INDEX idx_somaerp_lnk_product_tags_tenant_tag_product
    ON "11_somaerp".lnk_product_tags(tenant_id, tag_id, product_id);

-- ── Views ──────────────────────────────────────────────────────────────

CREATE VIEW "11_somaerp".v_product_lines AS
SELECT
    pl.id,
    pl.tenant_id,
    pl.category_id,
    cat.code        AS category_code,
    cat.name        AS category_name,
    pl.name,
    pl.slug,
    pl.status,
    pl.properties,
    pl.created_at,
    pl.updated_at,
    pl.created_by,
    pl.updated_by,
    pl.deleted_at
FROM "11_somaerp".fct_product_lines pl
LEFT JOIN "11_somaerp".dim_product_categories cat ON cat.id = pl.category_id;
COMMENT ON VIEW "11_somaerp".v_product_lines IS 'fct_product_lines joined with dim_product_categories for category_code / category_name.';

CREATE VIEW "11_somaerp".v_products AS
SELECT
    p.id,
    p.tenant_id,
    p.product_line_id,
    pl.name          AS product_line_name,
    pl.slug          AS product_line_slug,
    cat.id           AS category_id,
    cat.code         AS category_code,
    cat.name         AS category_name,
    p.name,
    p.slug,
    p.description,
    p.target_benefit,
    p.default_serving_size_ml,
    p.default_shelf_life_hours,
    p.target_cogs_amount,
    p.default_selling_price,
    p.currency_code,
    p.status,
    COALESCE(
        (SELECT array_agg(t.code ORDER BY t.code)
           FROM "11_somaerp".lnk_product_tags lt
           JOIN "11_somaerp".dim_product_tags t ON t.id = lt.tag_id
          WHERE lt.product_id = p.id AND lt.tenant_id = p.tenant_id),
        ARRAY[]::text[]
    ) AS tag_codes,
    p.properties,
    p.created_at,
    p.updated_at,
    p.created_by,
    p.updated_by,
    p.deleted_at
FROM "11_somaerp".fct_products p
LEFT JOIN "11_somaerp".fct_product_lines pl ON pl.id = p.product_line_id
LEFT JOIN "11_somaerp".dim_product_categories cat ON cat.id = pl.category_id;
COMMENT ON VIEW "11_somaerp".v_products IS 'fct_products joined with fct_product_lines + dim_product_categories + aggregated tag_codes.';

CREATE VIEW "11_somaerp".v_product_variants AS
SELECT
    v.id,
    v.tenant_id,
    v.product_id,
    p.name          AS product_name,
    p.slug          AS product_slug,
    v.name,
    v.slug,
    v.serving_size_ml,
    v.selling_price,
    v.currency_code,
    v.is_default,
    v.status,
    v.properties,
    v.created_at,
    v.updated_at,
    v.created_by,
    v.updated_by,
    v.deleted_at
FROM "11_somaerp".fct_product_variants v
LEFT JOIN "11_somaerp".fct_products p ON p.id = v.product_id;
COMMENT ON VIEW "11_somaerp".v_product_variants IS 'fct_product_variants joined with fct_products for product_name.';


-- DOWN ==================================================================

DROP VIEW IF EXISTS "11_somaerp".v_product_variants;
DROP VIEW IF EXISTS "11_somaerp".v_products;
DROP VIEW IF EXISTS "11_somaerp".v_product_lines;

DROP TABLE IF EXISTS "11_somaerp".lnk_product_tags;
DROP TABLE IF EXISTS "11_somaerp".fct_product_variants;
DROP TABLE IF EXISTS "11_somaerp".fct_products;
DROP TABLE IF EXISTS "11_somaerp".fct_product_lines;
DROP TABLE IF EXISTS "11_somaerp".dim_product_tags;
DROP TABLE IF EXISTS "11_somaerp".dim_product_categories;
