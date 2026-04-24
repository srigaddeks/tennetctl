-- UP ====================================================================

-- Recipes + Equipment vertical for somaerp (Plan 56-07).
-- Creates: fct_recipes + dtl_recipe_ingredients + dtl_recipe_steps +
--          dim_equipment_categories + fct_equipment +
--          lnk_kitchen_equipment (IMMUTABLE) +
--          lnk_recipe_step_equipment (IMMUTABLE)
-- Plus views: v_recipes, v_recipe_ingredients, v_recipe_steps,
--             v_recipe_cost_summary, v_equipment, v_kitchen_equipment
--
-- Rules:
-- * fct_recipes has partial unique on (tenant_id, product_id) WHERE
--   status='active' AND deleted_at IS NULL -> at most one active recipe
--   per product at a time. Publishing a new active recipe must atomically
--   archive the prior active one in the same tx (service layer).
-- * dtl_recipe_ingredients + dtl_recipe_steps carry full audit / soft-delete
--   (dtl_* allows this per project convention).
-- * lnk_kitchen_equipment + lnk_recipe_step_equipment are IMMUTABLE per
--   standard lnk_ rule: no updated_at, no deleted_at. Hard-delete only.

-- ── fct_recipes ────────────────────────────────────────────────────────

CREATE TABLE "11_somaerp".fct_recipes (
    id              VARCHAR(36) NOT NULL,
    tenant_id       VARCHAR(36) NOT NULL,
    product_id      VARCHAR(36) NOT NULL,
    version         INTEGER NOT NULL DEFAULT 1,
    status          TEXT NOT NULL DEFAULT 'draft',
    effective_from  DATE,
    notes           TEXT,
    properties      JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by      VARCHAR(36) NOT NULL,
    updated_by      VARCHAR(36) NOT NULL,
    deleted_at      TIMESTAMP,
    CONSTRAINT pk_somaerp_fct_recipes PRIMARY KEY (id),
    CONSTRAINT fk_somaerp_fct_recipes_product FOREIGN KEY (product_id)
        REFERENCES "11_somaerp".fct_products(id),
    CONSTRAINT chk_somaerp_fct_recipes_status
        CHECK (status IN ('draft','active','archived')),
    CONSTRAINT chk_somaerp_fct_recipes_version_pos
        CHECK (version > 0)
);
COMMENT ON TABLE  "11_somaerp".fct_recipes IS 'Versioned recipe header. At most one active recipe per product enforced by partial unique index.';
COMMENT ON COLUMN "11_somaerp".fct_recipes.id IS 'UUID v7, app-generated.';
COMMENT ON COLUMN "11_somaerp".fct_recipes.tenant_id IS 'tennetctl workspace_id.';
COMMENT ON COLUMN "11_somaerp".fct_recipes.product_id IS 'FK to fct_products.id.';
COMMENT ON COLUMN "11_somaerp".fct_recipes.version IS 'Monotonic version number per product.';
COMMENT ON COLUMN "11_somaerp".fct_recipes.status IS 'draft | active | archived.';
COMMENT ON COLUMN "11_somaerp".fct_recipes.effective_from IS 'Date this recipe becomes operational.';
COMMENT ON COLUMN "11_somaerp".fct_recipes.notes IS 'Free-text recipe notes.';
COMMENT ON COLUMN "11_somaerp".fct_recipes.properties IS 'JSONB side-channel.';
COMMENT ON COLUMN "11_somaerp".fct_recipes.created_at IS 'App-managed UTC timestamp.';
COMMENT ON COLUMN "11_somaerp".fct_recipes.updated_at IS 'App-managed UTC timestamp.';
COMMENT ON COLUMN "11_somaerp".fct_recipes.created_by IS 'Acting user_id.';
COMMENT ON COLUMN "11_somaerp".fct_recipes.updated_by IS 'Acting user_id.';
COMMENT ON COLUMN "11_somaerp".fct_recipes.deleted_at IS 'Soft-delete sentinel.';

CREATE UNIQUE INDEX idx_somaerp_fct_recipes_one_active_per_product
    ON "11_somaerp".fct_recipes(tenant_id, product_id)
    WHERE status = 'active' AND deleted_at IS NULL;
CREATE INDEX idx_somaerp_fct_recipes_tenant_product_status
    ON "11_somaerp".fct_recipes(tenant_id, product_id, status)
    WHERE deleted_at IS NULL;

-- ── dtl_recipe_ingredients ─────────────────────────────────────────────

CREATE TABLE "11_somaerp".dtl_recipe_ingredients (
    id                VARCHAR(36) NOT NULL,
    tenant_id         VARCHAR(36) NOT NULL,
    recipe_id         VARCHAR(36) NOT NULL,
    raw_material_id   VARCHAR(36) NOT NULL,
    quantity          NUMERIC(12,3) NOT NULL,
    unit_id           SMALLINT NOT NULL,
    position          INTEGER NOT NULL DEFAULT 1,
    notes             TEXT,
    created_at        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by        VARCHAR(36) NOT NULL,
    updated_by        VARCHAR(36) NOT NULL,
    deleted_at        TIMESTAMP,
    CONSTRAINT pk_somaerp_dtl_recipe_ingredients PRIMARY KEY (id),
    CONSTRAINT fk_somaerp_dtl_recipe_ingredients_recipe FOREIGN KEY (recipe_id)
        REFERENCES "11_somaerp".fct_recipes(id),
    CONSTRAINT fk_somaerp_dtl_recipe_ingredients_material FOREIGN KEY (raw_material_id)
        REFERENCES "11_somaerp".fct_raw_materials(id),
    CONSTRAINT fk_somaerp_dtl_recipe_ingredients_unit FOREIGN KEY (unit_id)
        REFERENCES "11_somaerp".dim_units_of_measure(id),
    CONSTRAINT chk_somaerp_dtl_recipe_ingredients_qty_pos
        CHECK (quantity > 0)
);
COMMENT ON TABLE  "11_somaerp".dtl_recipe_ingredients IS 'Per-ingredient line for a recipe. Soft-deletable per dtl_* convention.';
COMMENT ON COLUMN "11_somaerp".dtl_recipe_ingredients.id IS 'UUID v7.';
COMMENT ON COLUMN "11_somaerp".dtl_recipe_ingredients.tenant_id IS 'tennetctl workspace_id.';
COMMENT ON COLUMN "11_somaerp".dtl_recipe_ingredients.recipe_id IS 'FK to fct_recipes.id.';
COMMENT ON COLUMN "11_somaerp".dtl_recipe_ingredients.raw_material_id IS 'FK to fct_raw_materials.id.';
COMMENT ON COLUMN "11_somaerp".dtl_recipe_ingredients.quantity IS 'Quantity in supplied unit; must be positive.';
COMMENT ON COLUMN "11_somaerp".dtl_recipe_ingredients.unit_id IS 'FK to dim_units_of_measure.id.';
COMMENT ON COLUMN "11_somaerp".dtl_recipe_ingredients.position IS 'Display ordering.';
COMMENT ON COLUMN "11_somaerp".dtl_recipe_ingredients.notes IS 'Free-text notes.';

CREATE UNIQUE INDEX idx_somaerp_dtl_recipe_ingredients_uniq_mat_unit
    ON "11_somaerp".dtl_recipe_ingredients(recipe_id, raw_material_id, unit_id)
    WHERE deleted_at IS NULL;
CREATE INDEX idx_somaerp_dtl_recipe_ingredients_recipe
    ON "11_somaerp".dtl_recipe_ingredients(recipe_id, position)
    WHERE deleted_at IS NULL;

-- ── dtl_recipe_steps ───────────────────────────────────────────────────

CREATE TABLE "11_somaerp".dtl_recipe_steps (
    id                VARCHAR(36) NOT NULL,
    tenant_id         VARCHAR(36) NOT NULL,
    recipe_id         VARCHAR(36) NOT NULL,
    step_number       INTEGER NOT NULL,
    name              TEXT NOT NULL,
    duration_min      INTEGER,
    equipment_notes   TEXT,
    instructions      TEXT,
    created_at        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by        VARCHAR(36) NOT NULL,
    updated_by        VARCHAR(36) NOT NULL,
    deleted_at        TIMESTAMP,
    CONSTRAINT pk_somaerp_dtl_recipe_steps PRIMARY KEY (id),
    CONSTRAINT fk_somaerp_dtl_recipe_steps_recipe FOREIGN KEY (recipe_id)
        REFERENCES "11_somaerp".fct_recipes(id),
    CONSTRAINT chk_somaerp_dtl_recipe_steps_step_number_pos
        CHECK (step_number > 0)
);
COMMENT ON TABLE  "11_somaerp".dtl_recipe_steps IS 'Per-step line for a recipe. Soft-deletable per dtl_* convention.';
COMMENT ON COLUMN "11_somaerp".dtl_recipe_steps.id IS 'UUID v7.';
COMMENT ON COLUMN "11_somaerp".dtl_recipe_steps.tenant_id IS 'tennetctl workspace_id.';
COMMENT ON COLUMN "11_somaerp".dtl_recipe_steps.recipe_id IS 'FK to fct_recipes.id.';
COMMENT ON COLUMN "11_somaerp".dtl_recipe_steps.step_number IS '1-based step ordering.';
COMMENT ON COLUMN "11_somaerp".dtl_recipe_steps.name IS 'Step name (e.g. Wash).';
COMMENT ON COLUMN "11_somaerp".dtl_recipe_steps.duration_min IS 'Estimated duration in minutes.';
COMMENT ON COLUMN "11_somaerp".dtl_recipe_steps.equipment_notes IS 'Free-text equipment notes.';
COMMENT ON COLUMN "11_somaerp".dtl_recipe_steps.instructions IS 'Free-text instructions.';

CREATE UNIQUE INDEX idx_somaerp_dtl_recipe_steps_uniq_step
    ON "11_somaerp".dtl_recipe_steps(recipe_id, step_number)
    WHERE deleted_at IS NULL;

-- ── dim_equipment_categories ───────────────────────────────────────────

CREATE TABLE "11_somaerp".dim_equipment_categories (
    id              SMALLINT NOT NULL,
    code            TEXT NOT NULL,
    name            TEXT NOT NULL,
    deprecated_at   TIMESTAMP,
    CONSTRAINT pk_somaerp_dim_equipment_categories PRIMARY KEY (id),
    CONSTRAINT uq_somaerp_dim_equipment_categories_code UNIQUE (code)
);
COMMENT ON TABLE  "11_somaerp".dim_equipment_categories IS 'Equipment category lookup (juicer / fridge / cutting_board / scale / ...). Tenant-shared seed.';
COMMENT ON COLUMN "11_somaerp".dim_equipment_categories.id IS 'Permanent manual ID.';
COMMENT ON COLUMN "11_somaerp".dim_equipment_categories.code IS 'Stable lowercase code.';
COMMENT ON COLUMN "11_somaerp".dim_equipment_categories.name IS 'Human-readable name.';
COMMENT ON COLUMN "11_somaerp".dim_equipment_categories.deprecated_at IS 'Non-null when retired.';

-- ── fct_equipment ──────────────────────────────────────────────────────

CREATE TABLE "11_somaerp".fct_equipment (
    id                         VARCHAR(36) NOT NULL,
    tenant_id                  VARCHAR(36) NOT NULL,
    category_id                SMALLINT NOT NULL,
    name                       TEXT NOT NULL,
    slug                       TEXT NOT NULL,
    status                     TEXT NOT NULL DEFAULT 'active',
    purchase_cost              NUMERIC(14,4),
    currency_code              CHAR(3),
    purchase_date              DATE,
    expected_lifespan_months   INTEGER,
    properties                 JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at                 TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at                 TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by                 VARCHAR(36) NOT NULL,
    updated_by                 VARCHAR(36) NOT NULL,
    deleted_at                 TIMESTAMP,
    CONSTRAINT pk_somaerp_fct_equipment PRIMARY KEY (id),
    CONSTRAINT fk_somaerp_fct_equipment_category FOREIGN KEY (category_id)
        REFERENCES "11_somaerp".dim_equipment_categories(id),
    CONSTRAINT chk_somaerp_fct_equipment_status
        CHECK (status IN ('active','maintenance','retired')),
    CONSTRAINT chk_somaerp_fct_equipment_lifespan_nonneg
        CHECK (expected_lifespan_months IS NULL OR expected_lifespan_months >= 0)
);
COMMENT ON TABLE  "11_somaerp".fct_equipment IS 'Tenant-scoped equipment inventory.';
COMMENT ON COLUMN "11_somaerp".fct_equipment.id IS 'UUID v7.';
COMMENT ON COLUMN "11_somaerp".fct_equipment.tenant_id IS 'tennetctl workspace_id.';
COMMENT ON COLUMN "11_somaerp".fct_equipment.category_id IS 'FK to dim_equipment_categories.id.';
COMMENT ON COLUMN "11_somaerp".fct_equipment.name IS 'Display name.';
COMMENT ON COLUMN "11_somaerp".fct_equipment.slug IS 'URL-safe slug, unique per tenant.';
COMMENT ON COLUMN "11_somaerp".fct_equipment.status IS 'active | maintenance | retired.';
COMMENT ON COLUMN "11_somaerp".fct_equipment.purchase_cost IS 'Purchase cost amount.';
COMMENT ON COLUMN "11_somaerp".fct_equipment.currency_code IS 'ISO 4217.';
COMMENT ON COLUMN "11_somaerp".fct_equipment.purchase_date IS 'Date of purchase.';
COMMENT ON COLUMN "11_somaerp".fct_equipment.expected_lifespan_months IS 'Expected useful lifespan in months.';
COMMENT ON COLUMN "11_somaerp".fct_equipment.properties IS 'JSONB side-channel.';

CREATE UNIQUE INDEX idx_somaerp_fct_equipment_tenant_slug_active
    ON "11_somaerp".fct_equipment(tenant_id, slug)
    WHERE deleted_at IS NULL;
CREATE INDEX idx_somaerp_fct_equipment_tenant_cat_status
    ON "11_somaerp".fct_equipment(tenant_id, category_id, status)
    WHERE deleted_at IS NULL;

-- ── lnk_kitchen_equipment (IMMUTABLE) ─────────────────────────────────

CREATE TABLE "11_somaerp".lnk_kitchen_equipment (
    id              VARCHAR(36) NOT NULL,
    tenant_id       VARCHAR(36) NOT NULL,
    kitchen_id      VARCHAR(36) NOT NULL,
    equipment_id    VARCHAR(36) NOT NULL,
    quantity        INTEGER NOT NULL DEFAULT 1,
    notes           TEXT,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by      VARCHAR(36) NOT NULL,
    CONSTRAINT pk_somaerp_lnk_kitchen_equipment PRIMARY KEY (id),
    CONSTRAINT fk_somaerp_lnk_kitchen_equipment_kitchen FOREIGN KEY (kitchen_id)
        REFERENCES "11_somaerp".fct_kitchens(id),
    CONSTRAINT fk_somaerp_lnk_kitchen_equipment_equipment FOREIGN KEY (equipment_id)
        REFERENCES "11_somaerp".fct_equipment(id),
    CONSTRAINT uq_somaerp_lnk_kitchen_equipment
        UNIQUE (tenant_id, kitchen_id, equipment_id),
    CONSTRAINT chk_somaerp_lnk_kitchen_equipment_qty_pos
        CHECK (quantity > 0)
);
COMMENT ON TABLE  "11_somaerp".lnk_kitchen_equipment IS 'Immutable many-to-many kitchen <-> equipment link.';
COMMENT ON COLUMN "11_somaerp".lnk_kitchen_equipment.id IS 'UUID v7.';
COMMENT ON COLUMN "11_somaerp".lnk_kitchen_equipment.tenant_id IS 'tennetctl workspace_id.';
COMMENT ON COLUMN "11_somaerp".lnk_kitchen_equipment.kitchen_id IS 'FK to fct_kitchens.id.';
COMMENT ON COLUMN "11_somaerp".lnk_kitchen_equipment.equipment_id IS 'FK to fct_equipment.id.';
COMMENT ON COLUMN "11_somaerp".lnk_kitchen_equipment.quantity IS 'Quantity attached; must be positive.';
COMMENT ON COLUMN "11_somaerp".lnk_kitchen_equipment.notes IS 'Free-text notes.';

CREATE INDEX idx_somaerp_lnk_kitchen_equipment_tenant_kitchen
    ON "11_somaerp".lnk_kitchen_equipment(tenant_id, kitchen_id);
CREATE INDEX idx_somaerp_lnk_kitchen_equipment_tenant_equipment
    ON "11_somaerp".lnk_kitchen_equipment(tenant_id, equipment_id);

-- ── lnk_recipe_step_equipment (IMMUTABLE) ─────────────────────────────

CREATE TABLE "11_somaerp".lnk_recipe_step_equipment (
    id              VARCHAR(36) NOT NULL,
    tenant_id       VARCHAR(36) NOT NULL,
    step_id         VARCHAR(36) NOT NULL,
    equipment_id    VARCHAR(36) NOT NULL,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by      VARCHAR(36) NOT NULL,
    CONSTRAINT pk_somaerp_lnk_recipe_step_equipment PRIMARY KEY (id),
    CONSTRAINT fk_somaerp_lnk_recipe_step_equipment_step FOREIGN KEY (step_id)
        REFERENCES "11_somaerp".dtl_recipe_steps(id),
    CONSTRAINT fk_somaerp_lnk_recipe_step_equipment_equipment FOREIGN KEY (equipment_id)
        REFERENCES "11_somaerp".fct_equipment(id),
    CONSTRAINT uq_somaerp_lnk_recipe_step_equipment
        UNIQUE (step_id, equipment_id)
);
COMMENT ON TABLE  "11_somaerp".lnk_recipe_step_equipment IS 'Immutable many-to-many recipe_step <-> equipment link.';
COMMENT ON COLUMN "11_somaerp".lnk_recipe_step_equipment.id IS 'UUID v7.';
COMMENT ON COLUMN "11_somaerp".lnk_recipe_step_equipment.tenant_id IS 'tennetctl workspace_id.';
COMMENT ON COLUMN "11_somaerp".lnk_recipe_step_equipment.step_id IS 'FK to dtl_recipe_steps.id.';
COMMENT ON COLUMN "11_somaerp".lnk_recipe_step_equipment.equipment_id IS 'FK to fct_equipment.id.';

CREATE INDEX idx_somaerp_lnk_recipe_step_equipment_step
    ON "11_somaerp".lnk_recipe_step_equipment(step_id);
CREATE INDEX idx_somaerp_lnk_recipe_step_equipment_equipment
    ON "11_somaerp".lnk_recipe_step_equipment(equipment_id);

-- ── Views ──────────────────────────────────────────────────────────────

CREATE VIEW "11_somaerp".v_recipes AS
SELECT
    r.id,
    r.tenant_id,
    r.product_id,
    p.name              AS product_name,
    p.slug              AS product_slug,
    p.category_code     AS product_category_code,
    r.version,
    r.status,
    r.effective_from,
    r.notes,
    r.properties,
    r.created_at,
    r.updated_at,
    r.created_by,
    r.updated_by,
    r.deleted_at
FROM "11_somaerp".fct_recipes r
LEFT JOIN "11_somaerp".v_products p ON p.id = r.product_id;
COMMENT ON VIEW "11_somaerp".v_recipes IS 'fct_recipes joined with v_products for product_name + category_code.';

CREATE VIEW "11_somaerp".v_recipe_ingredients AS
SELECT
    i.id,
    i.tenant_id,
    i.recipe_id,
    i.raw_material_id,
    rm.name                 AS raw_material_name,
    rm.slug                 AS raw_material_slug,
    rm.default_unit_id      AS raw_material_default_unit_id,
    def_u.code              AS raw_material_default_unit_code,
    def_u.dimension         AS raw_material_default_unit_dimension,
    def_u.to_base_factor    AS raw_material_default_to_base_factor,
    rm.target_unit_cost     AS raw_material_target_unit_cost,
    rm.currency_code        AS raw_material_currency_code,
    i.quantity,
    i.unit_id,
    u.code                  AS unit_code,
    u.dimension             AS unit_dimension,
    u.to_base_factor        AS unit_to_base_factor,
    i.position,
    i.notes,
    i.created_at,
    i.updated_at,
    i.created_by,
    i.updated_by,
    i.deleted_at
FROM "11_somaerp".dtl_recipe_ingredients i
LEFT JOIN "11_somaerp".fct_raw_materials rm ON rm.id = i.raw_material_id
LEFT JOIN "11_somaerp".dim_units_of_measure u ON u.id = i.unit_id
LEFT JOIN "11_somaerp".dim_units_of_measure def_u ON def_u.id = rm.default_unit_id;
COMMENT ON VIEW "11_somaerp".v_recipe_ingredients IS 'dtl_recipe_ingredients joined with fct_raw_materials + dim_units_of_measure.';

CREATE VIEW "11_somaerp".v_recipe_steps AS
SELECT
    s.id,
    s.tenant_id,
    s.recipe_id,
    s.step_number,
    s.name,
    s.duration_min,
    s.equipment_notes,
    s.instructions,
    s.created_at,
    s.updated_at,
    s.created_by,
    s.updated_by,
    s.deleted_at
FROM "11_somaerp".dtl_recipe_steps s;
COMMENT ON VIEW "11_somaerp".v_recipe_steps IS 'Thin view of dtl_recipe_steps for read-side consistency.';

CREATE VIEW "11_somaerp".v_recipe_cost_summary AS
WITH lines AS (
    SELECT
        i.recipe_id,
        i.tenant_id,
        i.raw_material_target_unit_cost,
        i.raw_material_currency_code,
        i.quantity,
        i.unit_dimension,
        i.unit_to_base_factor,
        i.raw_material_default_unit_dimension,
        i.raw_material_default_to_base_factor,
        CASE
            WHEN i.raw_material_target_unit_cost IS NULL THEN NULL
            WHEN i.unit_dimension = i.raw_material_default_unit_dimension
              AND i.raw_material_default_to_base_factor IS NOT NULL
              AND i.raw_material_default_to_base_factor > 0
            THEN i.quantity
                 * (i.unit_to_base_factor / i.raw_material_default_to_base_factor)
                 * i.raw_material_target_unit_cost
            ELSE NULL
        END AS line_cost,
        CASE
            WHEN i.unit_dimension = i.raw_material_default_unit_dimension
              AND i.raw_material_default_to_base_factor IS NOT NULL
              AND i.raw_material_default_to_base_factor > 0
            THEN FALSE
            ELSE TRUE
        END AS is_unconvertible
    FROM "11_somaerp".v_recipe_ingredients i
    WHERE i.deleted_at IS NULL
)
SELECT
    r.id                                           AS recipe_id,
    r.tenant_id                                    AS tenant_id,
    r.product_name                                 AS product_name,
    COALESCE(SUM(l.line_cost), 0)::NUMERIC(14,4)   AS total_cost,
    COALESCE(
        MAX(l.raw_material_currency_code),
        'INR'
    )                                              AS currency_code,
    COUNT(l.recipe_id)                             AS ingredient_count,
    COALESCE(BOOL_OR(l.is_unconvertible), FALSE)   AS has_unconvertible_units
FROM "11_somaerp".v_recipes r
LEFT JOIN lines l ON l.recipe_id = r.id
WHERE r.deleted_at IS NULL
GROUP BY r.id, r.tenant_id, r.product_name;
COMMENT ON VIEW "11_somaerp".v_recipe_cost_summary IS 'Per-recipe BOM cost rollup. total_cost sums quantity*target_unit_cost with unit conversion via dim_units_of_measure.to_base_factor when dimensions match; else line omitted and has_unconvertible_units is true.';

CREATE VIEW "11_somaerp".v_equipment AS
SELECT
    e.id,
    e.tenant_id,
    e.category_id,
    c.code                  AS category_code,
    c.name                  AS category_name,
    e.name,
    e.slug,
    e.status,
    e.purchase_cost,
    e.currency_code,
    e.purchase_date,
    e.expected_lifespan_months,
    e.properties,
    e.created_at,
    e.updated_at,
    e.created_by,
    e.updated_by,
    e.deleted_at
FROM "11_somaerp".fct_equipment e
LEFT JOIN "11_somaerp".dim_equipment_categories c ON c.id = e.category_id;
COMMENT ON VIEW "11_somaerp".v_equipment IS 'fct_equipment joined with dim_equipment_categories.';

CREATE VIEW "11_somaerp".v_kitchen_equipment AS
SELECT
    lnk.id,
    lnk.tenant_id,
    lnk.kitchen_id,
    k.name                  AS kitchen_name,
    lnk.equipment_id,
    e.name                  AS equipment_name,
    e.slug                  AS equipment_slug,
    e.status                AS equipment_status,
    c.code                  AS equipment_category_code,
    c.name                  AS equipment_category_name,
    lnk.quantity,
    lnk.notes,
    lnk.created_at,
    lnk.created_by
FROM "11_somaerp".lnk_kitchen_equipment lnk
LEFT JOIN "11_somaerp".fct_kitchens k ON k.id = lnk.kitchen_id
LEFT JOIN "11_somaerp".fct_equipment e ON e.id = lnk.equipment_id
LEFT JOIN "11_somaerp".dim_equipment_categories c ON c.id = e.category_id;
COMMENT ON VIEW "11_somaerp".v_kitchen_equipment IS 'Per-kitchen equipment matrix view.';


-- DOWN ==================================================================

DROP VIEW IF EXISTS "11_somaerp".v_kitchen_equipment;
DROP VIEW IF EXISTS "11_somaerp".v_equipment;
DROP VIEW IF EXISTS "11_somaerp".v_recipe_cost_summary;
DROP VIEW IF EXISTS "11_somaerp".v_recipe_steps;
DROP VIEW IF EXISTS "11_somaerp".v_recipe_ingredients;
DROP VIEW IF EXISTS "11_somaerp".v_recipes;

DROP TABLE IF EXISTS "11_somaerp".lnk_recipe_step_equipment;
DROP TABLE IF EXISTS "11_somaerp".lnk_kitchen_equipment;
DROP TABLE IF EXISTS "11_somaerp".fct_equipment;
DROP TABLE IF EXISTS "11_somaerp".dim_equipment_categories;
DROP TABLE IF EXISTS "11_somaerp".dtl_recipe_steps;
DROP TABLE IF EXISTS "11_somaerp".dtl_recipe_ingredients;
DROP TABLE IF EXISTS "11_somaerp".fct_recipes;
