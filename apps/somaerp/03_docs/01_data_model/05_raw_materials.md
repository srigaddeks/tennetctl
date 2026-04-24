# Data Model: Raw Materials

## Purpose

Models the raw material catalog (spinach, beetroot, ginger, PET bottles, labels), their categorization, units of measure, supplier directory, and the raw-material-to-supplier association graph (with primary/backup designation per the Soma Delights two-vendor rule). This layer is consumed by `03_recipes` (recipes reference raw materials), `06_procurement` (procurement runs buy raw materials from suppliers), and `04_quality` (raw material acceptance checks).

## Tables

### dim_raw_material_categories

Top-level grouping. Tenant-shared seed.

| Column | Type | Notes |
|---|---|---|
| `id` | SMALLINT PK | |
| `code` | TEXT NOT NULL UNIQUE | "leafy_green" / "root" / "fruit" / "herb" / "spice" / "packaging" / "label" / "consumable" |
| `name` | TEXT NOT NULL | |

### dim_units_of_measure

Tenant-shared. Used by recipes, capacity, procurement lines, consumption, inventory.

| Column | Type | Notes |
|---|---|---|
| `id` | SMALLINT PK | |
| `code` | TEXT NOT NULL UNIQUE | "kg" / "g" / "l" / "ml" / "count" / "bunch" / "bottle" |
| `name` | TEXT NOT NULL | |
| `dimension` | TEXT NOT NULL | "mass" / "volume" / "count" |
| `base_unit_id` | SMALLINT REFERENCES dim_units_of_measure(id) | for conversion |
| `to_base_factor` | NUMERIC(20,8) | e.g. g→kg = 0.001 |

### dim_supplier_source_types

Tenant-shared.

| Column | Type | Notes |
|---|---|---|
| `id` | SMALLINT PK | |
| `code` | TEXT NOT NULL UNIQUE | "wholesale_market" / "rythu_bazaar" / "farm_direct" / "marketplace" / "brand_distributor" / "online" |
| `name` | TEXT NOT NULL | |

### fct_raw_materials

Tenant-scoped catalog of materials used in production.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `tenant_id` | UUID NOT NULL | |
| `category_id` | SMALLINT NOT NULL REFERENCES dim_raw_material_categories(id) | |
| `name` | TEXT NOT NULL | "Spinach" |
| `slug` | TEXT NOT NULL | |
| `default_unit_id` | SMALLINT NOT NULL REFERENCES dim_units_of_measure(id) | |
| `default_shelf_life_hours` | INTEGER | post-procurement freshness window |
| `requires_lot_tracking` | BOOLEAN NOT NULL DEFAULT TRUE | FSSAI default-on |
| `target_unit_cost` | NUMERIC(14,4) | target buying price |
| `currency_code` | CHAR(3) NOT NULL | |
| `status` | TEXT NOT NULL DEFAULT 'active' | |
| `properties` | JSONB NOT NULL DEFAULT '{}' | e.g. `{"storage":"fridge","quality_notes":"buy at 5-6 AM"}` |
| audit/timestamp/soft-delete columns | as conventions | |

Constraint: `UNIQUE (tenant_id, slug) WHERE deleted_at IS NULL`.

### fct_raw_material_variants

Optional. Use when the same logical material has meaningful sub-types (organic vs regular, Ooty carrot vs Delhi carrot).

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `tenant_id` | UUID NOT NULL | |
| `raw_material_id` | UUID NOT NULL REFERENCES fct_raw_materials(id) | |
| `name` | TEXT NOT NULL | "Organic Spinach" / "Regular Spinach" |
| `slug` | TEXT NOT NULL | |
| `target_unit_cost` | NUMERIC(14,4) | |
| `currency_code` | CHAR(3) NOT NULL | |
| `is_default` | BOOLEAN NOT NULL DEFAULT FALSE | |
| `status` | TEXT NOT NULL DEFAULT 'active' | |
| `properties` | JSONB NOT NULL DEFAULT '{}' | |
| audit/timestamp/soft-delete columns | as conventions | |

Constraint: `UNIQUE (tenant_id, raw_material_id, slug) WHERE deleted_at IS NULL`. Partial unique: `UNIQUE (tenant_id, raw_material_id) WHERE is_default AND deleted_at IS NULL`.

### fct_suppliers

Vendor directory.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `tenant_id` | UUID NOT NULL | |
| `name` | TEXT NOT NULL | "Bowenpally Wholesale Market" |
| `slug` | TEXT NOT NULL | |
| `source_type_id` | SMALLINT NOT NULL REFERENCES dim_supplier_source_types(id) | |
| `location_id` | UUID REFERENCES fct_locations(id) | nullable; for marketplace suppliers without a fixed location |
| `contact_jsonb` | JSONB NOT NULL DEFAULT '{}' | `{"phone":"...", "whatsapp":"...", "name":"..."}` |
| `payment_terms` | TEXT | "cash_on_delivery" / "net_7" / "prepaid" |
| `default_currency_code` | CHAR(3) NOT NULL | |
| `quality_rating` | SMALLINT | 1-5 |
| `status` | TEXT NOT NULL DEFAULT 'active' | active / paused / blacklisted |
| `properties` | JSONB NOT NULL DEFAULT '{}' | |
| audit/timestamp/soft-delete columns | as conventions | |

Constraint: `UNIQUE (tenant_id, slug) WHERE deleted_at IS NULL`.

### lnk_raw_material_suppliers

Many-to-many raw_material ↔ supplier with primary/backup designation. Mutable for `is_primary` flag (so technically mutable; the row itself is not immutable like a pure event).

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `tenant_id` | UUID NOT NULL | |
| `raw_material_id` | UUID NOT NULL REFERENCES fct_raw_materials(id) | |
| `supplier_id` | UUID NOT NULL REFERENCES fct_suppliers(id) | |
| `is_primary` | BOOLEAN NOT NULL DEFAULT FALSE | |
| `last_known_unit_cost` | NUMERIC(14,4) | refreshed by procurement |
| `currency_code` | CHAR(3) NOT NULL | |
| `notes` | TEXT | |
| `created_at` / `updated_at` | TIMESTAMPTZ | (link table is mutable for `is_primary` and `last_known_unit_cost`) |
| `created_by` / `updated_by` | UUID | |

Constraints: `UNIQUE (tenant_id, raw_material_id, supplier_id)`. Partial unique: `UNIQUE (tenant_id, raw_material_id) WHERE is_primary` — exactly one primary supplier per material.

## Views (v_*)

- `v_raw_materials` — `fct_raw_materials` joined with `dim_raw_material_categories` and `dim_units_of_measure` for default_unit_code.
- `v_suppliers` — `fct_suppliers` joined with `dim_supplier_source_types` and `fct_locations` (nullable).
- `v_raw_material_supplier_matrix` — for each (raw_material, supplier) pair: material name, supplier name, is_primary, last_known_unit_cost, source_type_code. Used by procurement planner.

## Indexes

- `fct_raw_materials (tenant_id, category_id, status) WHERE deleted_at IS NULL`
- `fct_raw_materials (tenant_id, slug) WHERE deleted_at IS NULL`
- `fct_suppliers (tenant_id, source_type_id, status) WHERE deleted_at IS NULL`
- `lnk_raw_material_suppliers (tenant_id, raw_material_id, is_primary DESC)` — primary lookup
- `lnk_raw_material_suppliers (tenant_id, supplier_id, raw_material_id)` — "what does this supplier carry?"

## Audit emission keys

- `somaerp.raw_materials.materials.created` / `.updated` / `.status_changed` / `.deleted`
- `somaerp.raw_materials.variants.created` / `.updated` / `.deleted`
- `somaerp.raw_materials.suppliers.created` / `.updated` / `.status_changed` / `.deleted`
- `somaerp.raw_materials.material_supplier.linked` / `.unlinked` / `.primary_changed`

## Cross-layer relationships

- `fct_raw_materials.id` ← `03_recipes.dtl_recipe_ingredients.raw_material_id`, `06_procurement.dtl_procurement_lines.raw_material_id`, `06_procurement.evt_inventory_movements.raw_material_id`, `07_production.dtl_batch_ingredient_consumption.raw_material_id`, `04_quality.dim_qc_checkpoints.raw_material_id`
- `fct_suppliers.id` ← `06_procurement.fct_procurement_runs.supplier_id`
- `fct_suppliers.location_id` → `01_geography.fct_locations.id`
- `dim_units_of_measure.id` ← used by recipes, capacity, procurement, consumption, inventory across layers

## Soma Delights tenant seed examples

| Table | Row |
|---|---|
| `dim_raw_material_categories` | `(leafy_green)`, `(root)`, `(fruit)`, `(herb)`, `(spice)`, `(packaging)`, `(label)` |
| `dim_units_of_measure` | `(g, mass, base=kg, factor=0.001)`, `(kg, mass, base=kg, factor=1)`, `(ml, volume, base=l, factor=0.001)`, `(l, volume, base=l, factor=1)`, `(count, count)`, `(bunch, count)`, `(bottle, count)` |
| `dim_supplier_source_types` | `(wholesale_market)`, `(rythu_bazaar)`, `(farm_direct)`, `(marketplace)`, `(brand_distributor)`, `(online)` |
| `fct_raw_materials` | spinach, mint, coriander, celery, carrot, beetroot, ginger, fresh turmeric, green apple, lemon, cucumber, orange, pineapple, black pepper, 300ml PET bottle, tamper-evident cap, branded label |
| `fct_raw_material_variants` | `(spinach: regular, organic)` (organic has higher target_unit_cost); `(carrot: Ooty, Delhi)` |
| `fct_suppliers` | `(Bowenpally Wholesale Market, wholesale_market, location=Hyderabad)`; `(Rythu Bazaar Kukatpally, rythu_bazaar)`; `(Erragadda Market, wholesale_market)`; `(BigBasket, marketplace)` (backup) |
| `lnk_raw_material_suppliers` | `(spinach ↔ Bowenpally, is_primary=true, cost=20/kg)`; `(spinach ↔ Rythu Bazaar, is_primary=false)`; `(carrot ↔ Bowenpally, primary)`; `(beetroot ↔ Bowenpally, primary)` |

## Open questions

- Sub-supplier (the specific palak vendor at Bowenpally that sets aside best bunches for you) — currently carried in `fct_suppliers.contact_jsonb`. Promote to `dtl_supplier_contacts` if multi-vendor-per-market becomes important.
- Seasonal pricing tables (ginger Rs 80-150/kg seasonal swing) — currently `last_known_unit_cost` on the link table. Promote to `evt_supplier_price_history` if procurement planner needs trend.
- Packaging unit conversions (palak 1 bunch ≈ 250g) — carry in `properties.bunch_to_g_factor` on the lnk row; promote when bunch-based procurement is common.
