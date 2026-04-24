# Data Model: Catalog

## Purpose

Models what the tenant sells: product lines (Cold-Pressed Drinks, Fermented Drinks, Dehydrated Pulp), products (SKUs like Green Morning, Citrus Immunity), product variants (size/packaging), and wellness tags (immunity, energy, detox, hydration). The catalog is what every recipe, batch, subscription, and delivery is ultimately about. Governing ADRs: ADR-002 (hybrid EAV — properties JSONB carries tenant-specific SKU attributes like serving_size_ml, shelf_life_hours, shape_descriptor).

## Tables

### dim_product_categories

Top-level categorization. Tenant-shared seed since beverage/pulp/shot/packaged-food applies to any product business.

| Column | Type | Notes |
|---|---|---|
| `id` | SMALLINT PK | |
| `code` | TEXT NOT NULL UNIQUE | "beverage" / "shot" / "pulp" / "packaged_food" |
| `name` | TEXT NOT NULL | |

### dim_product_tags

Wellness benefit tags. Tenant-shared seed; tenant-specific tags go via `lnk_product_tags.properties`.

| Column | Type | Notes |
|---|---|---|
| `id` | SMALLINT PK | |
| `code` | TEXT NOT NULL UNIQUE | "immunity" / "energy" / "detox" / "hydration" / "skin" / "gut" / "endurance" |
| `name` | TEXT NOT NULL | |

### fct_product_lines

A grouping of products that share production characteristics (same equipment, similar capacity envelope, similar shelf life). Capacity in `fct_kitchen_capacity` is per-product-line, not per-product.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `tenant_id` | UUID NOT NULL | |
| `category_id` | SMALLINT NOT NULL REFERENCES dim_product_categories(id) | |
| `name` | TEXT NOT NULL | "Cold-Pressed Drinks" |
| `slug` | TEXT NOT NULL | |
| `status` | TEXT NOT NULL DEFAULT 'active' | active / paused / discontinued |
| `properties` | JSONB NOT NULL DEFAULT '{}' | e.g. `{"default_shelf_life_hours": 24}` |
| audit/timestamp/soft-delete columns | as conventions | |

Constraint: `UNIQUE (tenant_id, slug) WHERE deleted_at IS NULL`.

### fct_products

The SKU. One row per saleable product.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `tenant_id` | UUID NOT NULL | |
| `product_line_id` | UUID NOT NULL REFERENCES fct_product_lines(id) | |
| `name` | TEXT NOT NULL | "Green Morning" |
| `slug` | TEXT NOT NULL | |
| `description` | TEXT | |
| `target_benefit` | TEXT | "Morning hydration, micronutrient loading" |
| `default_serving_size_ml` | NUMERIC(8,2) | nullable for non-beverage |
| `default_shelf_life_hours` | INTEGER | |
| `target_cogs_amount` | NUMERIC(14,4) | |
| `default_selling_price` | NUMERIC(14,4) | |
| `currency_code` | CHAR(3) NOT NULL | |
| `status` | TEXT NOT NULL DEFAULT 'active' | active / paused / discontinued |
| `properties` | JSONB NOT NULL DEFAULT '{}' | tenant-specific SKU attrs |
| audit/timestamp/soft-delete columns | as conventions | |

Constraint: `UNIQUE (tenant_id, slug) WHERE deleted_at IS NULL`.

### fct_product_variants

Size or packaging variant. Optional — most v0.9.0 SKUs ship with a single default variant.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `tenant_id` | UUID NOT NULL | |
| `product_id` | UUID NOT NULL REFERENCES fct_products(id) | |
| `name` | TEXT NOT NULL | "300ml PET" / "500ml glass" |
| `slug` | TEXT NOT NULL | |
| `serving_size_ml` | NUMERIC(8,2) | |
| `selling_price` | NUMERIC(14,4) | |
| `currency_code` | CHAR(3) NOT NULL | |
| `is_default` | BOOLEAN NOT NULL DEFAULT FALSE | exactly one per product |
| `status` | TEXT NOT NULL DEFAULT 'active' | |
| `properties` | JSONB NOT NULL DEFAULT '{}' | |
| audit/timestamp/soft-delete columns | as conventions | |

Constraint: `UNIQUE (tenant_id, product_id, slug) WHERE deleted_at IS NULL`. Partial index `UNIQUE (tenant_id, product_id) WHERE is_default AND deleted_at IS NULL`.

### lnk_product_tags

Many-to-many product ↔ tag. Immutable rows; deletion is hard delete since this is a join.

| Column | Type | Notes |
|---|---|---|
| `tenant_id` | UUID NOT NULL | |
| `product_id` | UUID NOT NULL REFERENCES fct_products(id) | |
| `tag_id` | SMALLINT NOT NULL REFERENCES dim_product_tags(id) | |
| `created_at` | TIMESTAMPTZ NOT NULL DEFAULT now() | |
| `created_by` | UUID NOT NULL | |
| PRIMARY KEY | `(tenant_id, product_id, tag_id)` | |

No `updated_at`, no `deleted_at` (immutable join per database conventions).

## Views (v_*)

- `v_product_lines` — `fct_product_lines` joined with `dim_product_categories` (exposes category code/name).
- `v_products` — `fct_products` joined with `fct_product_lines` and `dim_product_categories`. Aggregates tags via `array_agg(tag_code)`.
- `v_product_variants` — `fct_product_variants` joined with `fct_products` for product_name.

Pattern (illustrative):
```
CREATE VIEW v_products AS
SELECT p.id, p.tenant_id, p.name, p.slug, p.target_benefit,
       p.default_serving_size_ml, p.default_shelf_life_hours,
       p.target_cogs_amount, p.default_selling_price, p.currency_code,
       p.status, pl.id AS product_line_id, pl.name AS product_line_name,
       cat.code AS category_code, cat.name AS category_name,
       (SELECT array_agg(t.code)
          FROM lnk_product_tags lt JOIN dim_product_tags t ON t.id = lt.tag_id
         WHERE lt.product_id = p.id AND lt.tenant_id = p.tenant_id) AS tag_codes,
       p.properties, p.created_at, p.updated_at
FROM fct_products p
JOIN fct_product_lines pl ON pl.id = p.product_line_id
JOIN dim_product_categories cat ON cat.id = pl.category_id
WHERE p.deleted_at IS NULL;
```

## Indexes

- `fct_product_lines (tenant_id, status) WHERE deleted_at IS NULL`
- `fct_products (tenant_id, product_line_id, status) WHERE deleted_at IS NULL`
- `fct_products (tenant_id, slug) WHERE deleted_at IS NULL`
- `fct_product_variants (tenant_id, product_id) WHERE deleted_at IS NULL`
- `lnk_product_tags (tenant_id, tag_id, product_id)` — for "list products by tag" queries

## Audit emission keys

- `somaerp.catalog.product_lines.created` / `.updated` / `.status_changed` / `.deleted`
- `somaerp.catalog.products.created` / `.updated` / `.status_changed` / `.deleted`
- `somaerp.catalog.product_variants.created` / `.updated` / `.deleted`
- `somaerp.catalog.product_tags.attached` / `.detached`

## Cross-layer relationships

- `fct_product_lines.id` ← `01_geography.fct_kitchen_capacity.product_line_id`
- `fct_products.id` ← `03_recipes.fct_recipes.product_id`, `07_production.fct_production_batches.product_id`, `08_customers.dtl_subscription_plan_items.product_id`
- `fct_product_variants.id` ← optional reference from `08_customers.dtl_subscription_plan_items.variant_id` (nullable; defaults to product's default variant)

## Soma Delights tenant seed examples

| Table | Row |
|---|---|
| `dim_product_categories` | `(beverage, Beverage)`, `(shot, Shot)`, `(pulp, Dehydrated Pulp)` |
| `dim_product_tags` | `(immunity)`, `(energy)`, `(detox)`, `(hydration)`, `(skin)`, `(gut)` |
| `fct_product_lines` | `(Cold-Pressed Drinks, beverage, default_shelf_life_hours=24)` |
| `fct_products` | `(Green Morning, line=Cold-Pressed Drinks, serving=300ml, shelf=24h, cogs=38.30, price=99.00, INR)`; `(Beetroot Recharge, ...)`; `(Citrus Immunity)`; `(Hydration Cooler)`; `(Tropical Detox)`; `(Turmeric Ginger Shot)` |
| `lnk_product_tags` | `(Green Morning ↔ hydration)`, `(Green Morning ↔ detox)`, `(Citrus Immunity ↔ immunity)`, `(Beetroot Recharge ↔ energy)` |
| `fct_product_variants` | `(Green Morning, 300ml PET, is_default=true)` |

## Open questions

- Whether `fct_product_lines` should also carry a default_capacity_unit_id to default capacity rows — deferred; service layer handles.
- Multi-currency price tables for international tenants — deferred to plan that adds first non-INR tenant; current model carries `currency_code` per row.
- Whether bundles (Family Plan ships 3 SKUs together) belong here as a synthetic SKU or live entirely in `08_customers.dtl_subscription_plan_items` — currently the latter; revisit if bundles get sold one-off.
