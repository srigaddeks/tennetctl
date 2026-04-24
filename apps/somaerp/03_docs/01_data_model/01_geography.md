# Data Model: Geography

## Purpose

Models the physical world somaerp operates in: regulatory regions, cities, kitchens, kitchen capacity (per ADR-003), and delivery service zones. Every other layer's tenant data hangs off geography (a kitchen produces, a customer lives at a location, a route ships from a kitchen). Governing ADRs: ADR-001 (tenant boundary), ADR-003 (multi-kitchen capacity).

## Tables

### dim_regions

Country/state lookup. Static seed; rare additions when entering a new country. Used for compliance anchoring (FSSAI for IN, FDA for US, EFSA for EU).

| Column | Type | Notes |
|---|---|---|
| `id` | SMALLINT PK | |
| `code` | TEXT NOT NULL UNIQUE | ISO-style: `IN-TG`, `IN-KA`, `US-CA` |
| `country_code` | CHAR(2) NOT NULL | ISO 3166-1 alpha-2 |
| `state_name` | TEXT NOT NULL | |
| `regulatory_body` | TEXT | "FSSAI" / "FDA" / "EFSA" |
| `default_currency_code` | CHAR(3) NOT NULL | "INR" / "USD" / "EUR" |
| `default_timezone` | TEXT NOT NULL | "Asia/Kolkata" |

Initial seed: `IN-TG` (Telangana, FSSAI, INR, Asia/Kolkata).

### fct_locations

City-level granularity. Tenant-scoped (every tenant defines its own list of cities it operates in).

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK DEFAULT uuid7() | |
| `tenant_id` | UUID NOT NULL | tennetctl workspace_id |
| `region_id` | SMALLINT NOT NULL REFERENCES dim_regions(id) | |
| `name` | TEXT NOT NULL | "Hyderabad" |
| `slug` | TEXT NOT NULL | "hyderabad" |
| `timezone` | TEXT NOT NULL | overrides region default if needed |
| `properties` | JSONB NOT NULL DEFAULT '{}' | |
| `created_at` | TIMESTAMPTZ NOT NULL DEFAULT now() | |
| `updated_at` | TIMESTAMPTZ NOT NULL DEFAULT now() | |
| `created_by` | UUID NOT NULL | |
| `updated_by` | UUID NOT NULL | |
| `deleted_at` | TIMESTAMPTZ | |

Constraints: `UNIQUE (tenant_id, slug) WHERE deleted_at IS NULL`.

### fct_kitchens

Physical production facility within a location.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `tenant_id` | UUID NOT NULL | |
| `location_id` | UUID NOT NULL REFERENCES fct_locations(id) | |
| `name` | TEXT NOT NULL | "KPHB Home Kitchen" |
| `slug` | TEXT NOT NULL | |
| `kitchen_type` | TEXT NOT NULL | "home" / "commissary" / "satellite" |
| `address_jsonb` | JSONB NOT NULL DEFAULT '{}' | structured address |
| `geo_lat` | NUMERIC(9,6) | |
| `geo_lng` | NUMERIC(9,6) | |
| `status` | TEXT NOT NULL DEFAULT 'active' | active / paused / decommissioned |
| `properties` | JSONB NOT NULL DEFAULT '{}' | |
| audit/timestamp/soft-delete columns | as conventions | |

Constraints: `UNIQUE (tenant_id, slug) WHERE deleted_at IS NULL`.

### fct_kitchen_capacity

Per-(kitchen × product_line × time_window × validity) capacity. Multiple rows per kitchen are normal. See ADR-003.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `tenant_id` | UUID NOT NULL | |
| `kitchen_id` | UUID NOT NULL REFERENCES fct_kitchens(id) | |
| `product_line_id` | UUID NOT NULL REFERENCES fct_product_lines(id) | cross-layer FK to catalog |
| `capacity_value` | NUMERIC(12,2) NOT NULL | e.g. 50 |
| `capacity_unit_id` | SMALLINT NOT NULL REFERENCES dim_units_of_measure(id) | "bottles" |
| `time_window_start` | TIME NOT NULL | "04:00:00" |
| `time_window_end` | TIME NOT NULL | "08:00:00" |
| `valid_from` | DATE NOT NULL | |
| `valid_to` | DATE | NULL = currently active |
| `properties` | JSONB NOT NULL DEFAULT '{}' | |
| audit/timestamp/soft-delete columns | as conventions | |

Constraints:
- `CHECK (time_window_end > time_window_start)`
- `CHECK (valid_to IS NULL OR valid_to > valid_from)`
- Partial unique index: `UNIQUE (tenant_id, kitchen_id, product_line_id, time_window_start, time_window_end) WHERE valid_to IS NULL AND deleted_at IS NULL`

### fct_service_zones

Delivery polygon mapped to the kitchen that serves it.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `tenant_id` | UUID NOT NULL | |
| `kitchen_id` | UUID NOT NULL REFERENCES fct_kitchens(id) | |
| `name` | TEXT NOT NULL | "KPHB Cluster 1" |
| `polygon_jsonb` | JSONB NOT NULL DEFAULT '{}' | GeoJSON polygon or pincode list |
| `status` | TEXT NOT NULL DEFAULT 'active' | |
| `properties` | JSONB NOT NULL DEFAULT '{}' | |
| audit/timestamp/soft-delete columns | as conventions | |

## Views (v_*)

- `v_locations` — `fct_locations` joined with `dim_regions` (exposes region_code, country_code, regulatory_body).
- `v_kitchens` — `fct_kitchens` joined with `fct_locations` and `dim_regions` (exposes location_name, region_code, currency, tz).
- `v_kitchen_current_capacity` — `fct_kitchen_capacity` filtered on `valid_to IS NULL AND deleted_at IS NULL`, joined with `fct_product_lines` for label and `dim_units_of_measure` for unit symbol.
- `v_service_zones` — `fct_service_zones` joined with `fct_kitchens` for kitchen_name.

Pattern (illustrative):
```
CREATE VIEW v_kitchen_current_capacity AS
SELECT c.id, c.tenant_id, c.kitchen_id, k.name AS kitchen_name,
       c.product_line_id, pl.name AS product_line_name,
       c.capacity_value, u.code AS capacity_unit,
       c.time_window_start, c.time_window_end, c.valid_from, c.properties
FROM fct_kitchen_capacity c
JOIN fct_kitchens k ON k.id = c.kitchen_id
JOIN fct_product_lines pl ON pl.id = c.product_line_id
JOIN dim_units_of_measure u ON u.id = c.capacity_unit_id
WHERE c.valid_to IS NULL AND c.deleted_at IS NULL;
```

## Indexes

- `fct_locations (tenant_id, region_id) WHERE deleted_at IS NULL`
- `fct_kitchens (tenant_id, location_id) WHERE deleted_at IS NULL`
- `fct_kitchens (tenant_id, status) WHERE deleted_at IS NULL`
- `fct_kitchen_capacity (tenant_id, kitchen_id, product_line_id, valid_from, valid_to)` — covers active + historical lookups
- `fct_service_zones (tenant_id, kitchen_id) WHERE deleted_at IS NULL`

## Audit emission keys

- `somaerp.geography.locations.created` / `.updated` / `.deleted`
- `somaerp.geography.kitchens.created` / `.updated` / `.status_changed` / `.deleted`
- `somaerp.geography.kitchen_capacity.created` / `.closed` (closed = `valid_to` set)
- `somaerp.geography.service_zones.created` / `.updated` / `.deleted`

## Cross-layer relationships

- `fct_kitchen_capacity.product_line_id` → `02_catalog.fct_product_lines.id`
- `fct_kitchens` is referenced by `06_procurement.fct_procurement_runs`, `06_procurement.evt_inventory_movements`, `07_production.fct_production_batches`, `09_delivery.fct_delivery_routes`, `09_delivery.evt_inventory_movements` (kitchen owns inventory)
- `fct_locations` is referenced by `08_customers.fct_customers`
- `fct_service_zones.kitchen_id` is the routing target for customer→kitchen assignment in `08_customers`

## Soma Delights tenant seed examples

| Table | Row |
|---|---|
| `dim_regions` | `(IN-TG, IN, Telangana, FSSAI, INR, Asia/Kolkata)` |
| `fct_locations` | `(Hyderabad, hyderabad, region IN-TG)` |
| `fct_kitchens` | `(KPHB Home Kitchen, kphb-home, kitchen_type=home, status=active)` |
| `fct_kitchen_capacity` | `(KPHB Home Kitchen, Cold-Pressed Drinks, capacity=50, unit=bottles, 04:00-08:00, valid_from=2026-04-24, valid_to=NULL)` |
| `fct_service_zones` | `(KPHB Cluster 1, kitchen=KPHB Home Kitchen, polygon=KPHB Colony pincodes 500072/500085)` |

## Open questions

- Multi-kitchen Stage-2 expansion (Miyapur satellite kitchen) — capacity row(s) added when satellite is provisioned; no schema change needed.
- PostGIS adoption for true polygon ops vs JSONB pincode list — deferred until route optimization workflow is built.
- Per-kitchen working hours / shift schedule — currently stored in `properties.shifts` JSONB; promote to a `dtl_kitchen_shifts` table if routing/HR ever needs it.
