# Data Model: Procurement & Inventory

## Purpose

Models the buying process and the resulting stock state. Per ADR-006: procurement runs (one shopping trip = one header row with N line items) are immutable; inventory state is an append-only event log of movements (received / consumed / wasted / returned / adjusted) with current quantity exposed via a derived view. Lot numbers flow from receipt through consumption into a specific batch_id_ref for FSSAI traceability.

## Tables

### fct_procurement_runs

The header for one shopping trip or wholesale order. Immutable after creation (no field updates); to correct, insert adjustment movements.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `tenant_id` | UUID NOT NULL | |
| `kitchen_id` | UUID NOT NULL REFERENCES fct_kitchens(id) | receiving kitchen |
| `supplier_id` | UUID NOT NULL REFERENCES fct_suppliers(id) | |
| `run_date` | DATE NOT NULL | |
| `run_started_at` | TIMESTAMPTZ NOT NULL DEFAULT now() | |
| `performed_by_user_id` | UUID NOT NULL | tennetctl user id |
| `total_cost` | NUMERIC(14,4) NOT NULL DEFAULT 0 | sum of line costs; computed at finalize |
| `currency_code` | CHAR(3) NOT NULL | |
| `status` | TEXT NOT NULL DEFAULT 'received' | "received" / "voided" |
| `payment_method` | TEXT | "cash" / "upi" / "credit" |
| `invoice_ref` | TEXT | optional supplier invoice number |
| `notes` | TEXT | |
| `properties` | JSONB NOT NULL DEFAULT '{}' | |
| `created_at` / `updated_at` | TIMESTAMPTZ | |
| `created_by` / `updated_by` | UUID | |
| `deleted_at` | TIMESTAMPTZ | soft-delete only when `status='voided'` and operator chooses |

Note: although `fct_*` rows normally have full mutation semantics, procurement headers are conceptually immutable for FSSAI. The service layer rejects any update other than `status: received → voided` (which also requires inserting compensating `adjusted` movements).

### dtl_procurement_lines

Per-material line item on a procurement run. Carries the lot number that becomes the FSSAI traceability anchor.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `tenant_id` | UUID NOT NULL | |
| `procurement_run_id` | UUID NOT NULL REFERENCES fct_procurement_runs(id) | |
| `raw_material_id` | UUID NOT NULL REFERENCES fct_raw_materials(id) | |
| `raw_material_variant_id` | UUID REFERENCES fct_raw_material_variants(id) | nullable |
| `quantity` | NUMERIC(14,4) NOT NULL | |
| `unit_id` | SMALLINT NOT NULL REFERENCES dim_units_of_measure(id) | |
| `unit_cost` | NUMERIC(14,4) NOT NULL | |
| `currency_code` | CHAR(3) NOT NULL | |
| `lot_number` | TEXT NOT NULL | tenant-generated, e.g. `KPHB-20260424-001-spinach` |
| `expiry_date` | DATE | when known |
| `qc_status` | TEXT NOT NULL DEFAULT 'pending' | "pending" / "passed" / "failed" — set by `evt_qc_checks` for pre_production |
| `notes` | TEXT | |
| `created_at` | TIMESTAMPTZ NOT NULL DEFAULT now() | |

No `updated_at` — once a line is recorded, only `qc_status` is updatable via the service layer (which logs an audit event).

Constraint: `UNIQUE (tenant_id, procurement_run_id, raw_material_id, lot_number)`.

### evt_inventory_movements

The append-only stock event log. Every change to physical inventory is one row. Current state is `v_inventory_current`.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `tenant_id` | UUID NOT NULL | |
| `kitchen_id` | UUID NOT NULL REFERENCES fct_kitchens(id) | inventory holder |
| `raw_material_id` | UUID NOT NULL REFERENCES fct_raw_materials(id) | |
| `raw_material_variant_id` | UUID REFERENCES fct_raw_material_variants(id) | nullable |
| `lot_number` | TEXT NOT NULL | empty string allowed only for legacy `adjusted` rows that consolidate untracked stock |
| `movement_type` | TEXT NOT NULL | "received" / "consumed" / "wasted" / "returned" / "adjusted" |
| `quantity` | NUMERIC(14,4) NOT NULL | signed by `movement_type` semantics (received/adjusted+ → positive; consumed/wasted/returned → positive numbers but interpreted as outflow). The `v_inventory_current` view applies sign based on type. |
| `unit_id` | SMALLINT NOT NULL REFERENCES dim_units_of_measure(id) | |
| `source_procurement_line_id` | UUID REFERENCES dtl_procurement_lines(id) | populated for `received` |
| `batch_id_ref` | UUID REFERENCES fct_production_batches(id) | populated for `consumed` (FSSAI link) |
| `reason` | TEXT | required for `wasted` / `adjusted` ("spoiled overnight", "stocktake correction") |
| `actor_user_id` | UUID NOT NULL | tennetctl user id |
| `unit_cost_at_event` | NUMERIC(14,4) | snapshot for COGS |
| `currency_code` | CHAR(3) NOT NULL | |
| `created_at` | TIMESTAMPTZ NOT NULL DEFAULT now() | |

CHECK: `movement_type IN ('received','consumed','wasted','returned','adjusted')`. CHECK: `quantity > 0`.

No `updated_at`, no `deleted_at`. Corrections = a new `adjusted` row.

## Views (v_*)

- `v_procurement_runs` — `fct_procurement_runs` joined with `fct_suppliers` for supplier_name, `fct_kitchens` for kitchen_name. Aggregates `dtl_procurement_lines` count and total_cost.
- `v_procurement_lines` — `dtl_procurement_lines` joined with `fct_raw_materials` for material_name, `dim_units_of_measure` for unit_code.
- `v_inventory_current` — per (tenant, kitchen, raw_material, lot_number): current quantity by summing signed movements.

Pattern (illustrative):
```
CREATE VIEW v_inventory_current AS
SELECT tenant_id, kitchen_id, raw_material_id, lot_number,
       sum(CASE
             WHEN movement_type IN ('received','adjusted') THEN quantity
             ELSE -quantity
           END) AS current_qty,
       max(unit_id) AS unit_id  -- assume single unit per material; service enforces
FROM evt_inventory_movements
GROUP BY tenant_id, kitchen_id, raw_material_id, lot_number
HAVING sum(CASE
             WHEN movement_type IN ('received','adjusted') THEN quantity
             ELSE -quantity
           END) > 0;
```

Plus `v_inventory_current_by_material` (rolled up across lots per material) and `v_lot_traceability` (materials' full event history per lot).

## Indexes

- `fct_procurement_runs (tenant_id, kitchen_id, run_date DESC) WHERE deleted_at IS NULL`
- `fct_procurement_runs (tenant_id, supplier_id, run_date DESC) WHERE deleted_at IS NULL`
- `dtl_procurement_lines (tenant_id, procurement_run_id)` — header join
- `dtl_procurement_lines (tenant_id, raw_material_id, lot_number)` — lot lookup
- `evt_inventory_movements (tenant_id, kitchen_id, raw_material_id, lot_number, created_at)` — covers `v_inventory_current` aggregation
- `evt_inventory_movements (tenant_id, batch_id_ref) WHERE batch_id_ref IS NOT NULL` — batch consumption lookup
- `evt_inventory_movements (tenant_id, source_procurement_line_id) WHERE source_procurement_line_id IS NOT NULL` — lot traceability

## Audit emission keys

- `somaerp.procurement.runs.created` (initial insert)
- `somaerp.procurement.runs.voided` (status: received → voided)
- `somaerp.procurement.lines.qc_status_changed`
- `somaerp.inventory.movements.received` (one per `received` insert; can also be batched into one event per run)
- `somaerp.inventory.movements.consumed` (typically batched per batch completion)
- `somaerp.inventory.movements.wasted`
- `somaerp.inventory.movements.returned`
- `somaerp.inventory.movements.adjusted` — high-priority audit for FSSAI

## Cross-layer relationships

- `fct_procurement_runs.kitchen_id` → `01_geography.fct_kitchens.id`
- `fct_procurement_runs.supplier_id` → `05_raw_materials.fct_suppliers.id`
- `dtl_procurement_lines.raw_material_id` → `05_raw_materials.fct_raw_materials.id`
- `evt_inventory_movements.batch_id_ref` → `07_production.fct_production_batches.id` (consumption linkage)
- `evt_inventory_movements.source_procurement_line_id` → `dtl_procurement_lines.id` (receipt linkage)
- `dtl_procurement_lines.id` ← `04_quality.evt_qc_checks.procurement_line_id` (pre-production QC ties result to the lot)

## Soma Delights tenant seed examples

| Table | Row |
|---|---|
| `fct_procurement_runs` | seed-time empty; first row at first Bowenpally run |
| Example post-bootstrap row | `(kitchen=KPHB Home Kitchen, supplier=Bowenpally Wholesale Market, run_date=2026-04-25, total_cost=850.00, INR, payment_method=cash)` |
| `dtl_procurement_lines` example | `(spinach, 1.5 kg, unit_cost=20.00, lot=KPHB-20260425-001-spinach)`, `(carrot, 2 kg, 30.00, lot=KPHB-20260425-001-carrot)`, etc. |
| `evt_inventory_movements` example | `(received, kitchen=KPHB, spinach, 1.5 kg, lot=KPHB-20260425-001-spinach, source_procurement_line_id=...)`; later `(consumed, spinach, 0.5 kg, lot=...-spinach, batch_id_ref=batch-001-greenmorning-am)`; later `(wasted, spinach, 0.2 kg, reason="overnight wilting")` |

## Open questions

- Periodic snapshot table `dtl_inventory_snapshots` for very high movement volume — not v0.9.0; revisit at >10k movements/day.
- Multi-currency procurement (rare for v0.9.0) — `currency_code` is per-row; service layer enforces single-currency-per-run.
- Returns workflow nuance (return to supplier vs internal credit) — currently `returned` movement_type with `reason`; promote if returns become a workflow.
- Whether to FK-enforce `lot_number` against `dtl_procurement_lines` for `consumed`/`wasted`/`returned` movements — currently service-validated; promote to FK when stable (constraint is multi-column composite, harder to enforce in SQL but doable).
