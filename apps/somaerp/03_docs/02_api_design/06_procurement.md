# API Design: Procurement & Inventory

Conventions: see `00_conventions.md`. Endpoints rooted at `/v1/somaerp/procurement/...`. RBAC scopes: `somaerp.procurement.read` / `.write` / `.adjust` (insert adjusted movements) / `.admin`. Audit emission keys mirror `01_data_model/06_procurement.md`.

## Endpoints

### Procurement runs

| Method | Path | Scope | Audit key |
|---|---|---|---|
| GET | `/v1/somaerp/procurement/runs` | `procurement.read` | (none) |
| POST | `/v1/somaerp/procurement/runs` | `procurement.write` | `somaerp.procurement.runs.created` |
| GET | `/v1/somaerp/procurement/runs/{id}` | `procurement.read` | (none) |
| PATCH | `/v1/somaerp/procurement/runs/{id}` | `procurement.admin` | `somaerp.procurement.runs.voided` (when status: received → voided) |

No DELETE — procurement runs are not deletable; void via PATCH.

POST body (one-shot creation: header + lines + automatic `received` movements):
```python
class ProcurementRunCreate(BaseModel):
    kitchen_id: UUID
    supplier_id: UUID
    run_date: date
    performed_by_user_id: UUID | None = None  # defaults to authenticated user
    payment_method: str | None = None
    invoice_ref: str | None = None
    notes: str | None = None
    properties: dict = {}
    lines: list[ProcurementLineCreate]   # at least 1

class ProcurementLineCreate(BaseModel):
    raw_material_id: UUID
    raw_material_variant_id: UUID | None = None
    quantity: Decimal
    unit_id: int
    unit_cost: Decimal
    currency_code: str
    lot_number: str   # required (FSSAI default-on)
    expiry_date: date | None = None
    notes: str | None = None
```

The service:
1. Inserts `fct_procurement_runs` header (status='received').
2. Inserts `dtl_procurement_lines` rows.
3. Inserts one `evt_inventory_movements` per line (`movement_type='received'`, `source_procurement_line_id=line.id`).
4. Updates `lnk_raw_material_suppliers.last_known_unit_cost` per (material, supplier).
5. Computes and stores `total_cost` on the header.
6. Emits `somaerp.procurement.runs.created` once and `somaerp.inventory.movements.received` per line (or batched per the audit emission policy).

`Idempotency-Key` strongly recommended.

PATCH body (limited):
```python
class ProcurementRunUpdate(BaseModel):
    status: Literal["voided"] | None = None
    notes: str | None = None
```

Only `notes` and `status: received → voided` are allowed. Voiding inserts compensating `evt_inventory_movements` rows with `movement_type='adjusted'` and negative-equivalent quantity (per ADR-006), and emits `.voided` plus per-line `.adjusted`.

Response: row from `v_procurement_runs` with embedded `lines` array.

### Procurement lines (read + qc_status update only)

| Method | Path | Scope | Audit key |
|---|---|---|---|
| GET | `/v1/somaerp/procurement/lines` | `procurement.read` | (none) |
| GET | `/v1/somaerp/procurement/lines/{id}` | `procurement.read` | (none) |
| PATCH | `/v1/somaerp/procurement/lines/{id}` | `procurement.write` | `somaerp.procurement.lines.qc_status_changed` |

PATCH only allows `qc_status` mutation (and is normally driven by the quality layer's `evt_qc_checks` insert side effect; direct PATCH allowed for manual override with audit).

### Inventory movements (read + manual adjustments)

| Method | Path | Scope | Audit key |
|---|---|---|---|
| GET | `/v1/somaerp/procurement/movements` | `procurement.read` | (none) |
| POST | `/v1/somaerp/procurement/movements` | `procurement.adjust` | `somaerp.inventory.movements.{movement_type}` |
| GET | `/v1/somaerp/procurement/movements/{id}` | `procurement.read` | (none) |

No PATCH, no DELETE — append-only.

POST body (manual adjustment / waste recording — `received` and `consumed` should normally come from procurement-run creation and production-batch completion respectively, not from this endpoint):

```python
class InventoryMovementCreate(BaseModel):
    kitchen_id: UUID
    raw_material_id: UUID
    raw_material_variant_id: UUID | None = None
    lot_number: str
    movement_type: Literal["wasted","returned","adjusted"]   # received/consumed forbidden here
    quantity: Decimal
    unit_id: int
    reason: str            # required for wasted/adjusted
    unit_cost_at_event: Decimal | None = None
    currency_code: str
```

Service rejects `movement_type` of `received` or `consumed` with 400 (those flow from procurement-run and production-batch endpoints to keep traceability). For exceptional cases (legacy import), a `procurement.admin`-only endpoint `POST /v1/somaerp/procurement/movements/import` accepts arbitrary types — flagged but considered out of v0.9.0.

### Current inventory (read view)

| Method | Path | Scope | Notes |
|---|---|---|---|
| GET | `/v1/somaerp/procurement/inventory` | `procurement.read` | Reads `v_inventory_current`. Filters: `kitchen_id`, `raw_material_id`, `lot_number`, `min_qty`. Returns rows with positive current_qty by default. |

This is a derived read; it is not a new entity. Keeping it under `/procurement/` rather than its own `/inventory/` path because it is the read surface of `evt_inventory_movements`.

### Lot traceability (read view)

| Method | Path | Scope | Notes |
|---|---|---|---|
| GET | `/v1/somaerp/procurement/lots/{lot_number}` | `procurement.read` | Returns the full event chain: source procurement line + supplier + all movements + batches consumed into. FSSAI traceability single endpoint. |

## Filter parameters

### Runs list

| Param | Notes |
|---|---|
| `kitchen_id` | exact |
| `supplier_id` | exact |
| `status` | comma list |
| `run_date_from` / `run_date_to` | inclusive |
| `performed_by_user_id` | exact |

### Lines list

| Param | Notes |
|---|---|
| `procurement_run_id` | exact |
| `raw_material_id` | exact |
| `lot_number` | exact |
| `qc_status` | comma list |

### Movements list

| Param | Notes |
|---|---|
| `kitchen_id` | exact |
| `raw_material_id` | exact |
| `lot_number` | exact |
| `movement_type` | comma list |
| `batch_id_ref` | exact |
| `source_procurement_line_id` | exact |
| `created_after` / `created_before` | timestamp |

Standard `limit`, `cursor`, `sort`.

## Bulk operations

Procurement runs POST does not use bulk array (one run = one shopping trip). However, lines within a run are inherently bulk (the body's `lines` array).

Manual movements POST accepts an array (e.g. end-of-day waste batch entry).

## Cross-layer behaviors

- Procurement run POST validates supplier `status != 'blacklisted'` → otherwise 422.
- Each line's `raw_material_id` must exist in the same tenant.
- Per ADR-006, `received` movements are only emitted via run creation; `consumed` movements are only emitted via production batch completion (07_production layer); `wasted/returned/adjusted` are emitted here.
- A consumption attempt against a `lot_number` whose `dtl_procurement_lines.qc_status='failed'` is rejected at production layer with 422.
- Voiding a run that has any `consumed` downstream movements requires `procurement.admin` AND emits a high-priority audit event (`category=fssai_alert`).
- `v_inventory_current` is the read source; writes never touch it.

## Audit scope

| Endpoint | Additional scope |
|---|---|
| Run POST | `entity_kind="procurement.run"`, `properties={kitchen_id, supplier_id, run_date, total_cost, currency_code, line_count}` |
| Run PATCH (void) | `properties={voided_reason, line_ids}` — high priority |
| Movement POST | `entity_kind="inventory.movement"`, `properties={kitchen_id, raw_material_id, lot_number, movement_type, quantity, reason}` |
| Adjusted movement | always emits with `category="fssai_alert"` for FSSAI traceability surfacing |

Idempotency-Key on procurement run POST is required for production use. The service stores the response keyed on `(tenant_id, kitchen_id, run_date, idempotency_key)` for 24 hours.
