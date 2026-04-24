# API Design: Production

Conventions: see `00_conventions.md`. Endpoints rooted at `/v1/somaerp/production/...`. RBAC scopes: `somaerp.production.read` / `.write` / `.complete` (transition to completed) / `.cancel` / `.admin`. Audit emission keys mirror `01_data_model/07_production.md`.

## Endpoints

### Production batches

| Method | Path | Scope | Audit key |
|---|---|---|---|
| GET | `/v1/somaerp/production/batches` | `production.read` | (none) |
| POST | `/v1/somaerp/production/batches` | `production.write` | `somaerp.production.batches.created` |
| GET | `/v1/somaerp/production/batches/{id}` | `production.read` | (none) |
| PATCH | `/v1/somaerp/production/batches/{id}` | `production.write` (or `.complete` / `.cancel` for status) | `.started` / `.completed` / `.cancelled` / `.updated` |
| DELETE | `/v1/somaerp/production/batches/{id}` | `production.admin` | rare; soft-delete only for accidental creations before status change |

POST body:
```python
class BatchCreate(BaseModel):
    kitchen_id: UUID
    product_id: UUID
    recipe_id: UUID | None = None    # if omitted, service resolves via v_kitchen_active_recipe
    run_date: date
    planned_qty: Decimal
    yield_unit_id: int
    properties: dict = {}
```

The service:
1. If `recipe_id` is omitted, resolves the kitchen-override-aware active recipe for `(kitchen_id, product_id)`. Returns 404 if none active.
2. Validates the resolved recipe is `status='active'`.
3. Inserts `fct_production_batches` with `status='planned'`.
4. Inserts one `dtl_batch_ingredient_consumption` row per recipe ingredient with `planned_qty` set, `actual_qty` NULL.
5. Pre-creates `dtl_batch_qc_results` rows for every required `dim_qc_checkpoints` matching this recipe.

`recipe_id` is **immutable** after insert per ADR-007; PATCH attempting to change returns 409 `IMMUTABLE_FIELD`.

PATCH transitions:
- `{"status":"in_progress"}` requires `production.write`. Sets `shift_start=now()`. Validates the resolved recipe is still active (a recipe archived between planning and start triggers 409 `INVALID_STATE_TRANSITION`).
- `{"status":"completed", "actual_qty": <decimal>}` requires `production.complete`. Validates: `actual_qty IS NOT NULL`; every required QC checkpoint has its rollup `result IN ('pass','warn')` (failures must have been overridden via a subsequent `evt_qc_check`); every `dtl_batch_ingredient_consumption.actual_qty` is set. Sets `shift_end=now()`. Triggers per-line `evt_inventory_movements` (`movement_type='consumed'`, `batch_id_ref=this.id`) for any consumption line with `actual_qty > 0` not yet posted.
- `{"status":"cancelled", "cancel_reason": "..."}` allowed from `planned` or `in_progress`. Requires `production.cancel`. If cancelled mid-run with consumption already posted, those movements are NOT auto-reversed; operator must record `wasted` movements via procurement layer with reason.

PATCH on non-status fields (`planned_qty`, `properties`) only allowed when `status='planned'`.

Response: row from `v_production_batches` plus embedded `consumption[]`, `step_logs[]`, `qc_summary` (from `v_batch_summary`).

### Batch step logs

| Method | Path | Scope | Audit key |
|---|---|---|---|
| GET | `/v1/somaerp/production/batches/{batch_id}/step-logs` | `production.read` | (none) |
| POST | `/v1/somaerp/production/batches/{batch_id}/step-logs` | `production.write` | `somaerp.production.step_logs.recorded` |
| PATCH | `/v1/somaerp/production/batches/{batch_id}/step-logs/{id}` | `production.write` | `somaerp.production.step_logs.recorded` |

POST body:
```python
class StepLogCreate(BaseModel):
    recipe_step_id: UUID
    started_at: datetime | None = None  # defaults to now()
    completed_at: datetime | None = None
    notes: str | None = None
```

PATCH normally to set `completed_at`. Both POST and PATCH only allowed when batch `status='in_progress'`. After batch completes, step logs are immutable.

### Batch ingredient consumption

| Method | Path | Scope | Audit key |
|---|---|---|---|
| GET | `/v1/somaerp/production/batches/{batch_id}/consumption` | `production.read` | (none) |
| PATCH | `/v1/somaerp/production/batches/{batch_id}/consumption/{id}` | `production.write` | `somaerp.production.consumption.recorded` |

No POST (rows pre-created at batch creation). No DELETE.

PATCH body:
```python
class ConsumptionUpdate(BaseModel):
    actual_qty: Decimal
    lot_number: str          # required when actual_qty > 0 (FSSAI)
    raw_material_variant_id: UUID | None = None
    unit_cost_at_consumption: Decimal | None = None  # if omitted, service pulls from lnk_raw_material_suppliers.last_known_unit_cost
```

Service validates: lot exists in `v_inventory_current` for the same kitchen with sufficient quantity; lot's `qc_status != 'failed'`. Successful PATCH inserts (or updates pending) `evt_inventory_movements` row.

### Batch QC results (read-only)

| Method | Path | Scope | Notes |
|---|---|---|---|
| GET | `/v1/somaerp/production/batches/{batch_id}/qc` | `production.read` | Returns `dtl_batch_qc_results` joined with checkpoint info and the `last_event_id` pointer. Recording an actual check is via `04_quality` POST `/checks`. |

## Filter parameters

### Batches list

| Param | Notes |
|---|---|
| `kitchen_id` | exact |
| `product_id` | exact |
| `recipe_id` | exact |
| `status` | comma list (planned / in_progress / completed / cancelled) |
| `run_date_from` / `run_date_to` | inclusive |
| `created_by` | exact |
| `q` | matches `properties->>'shift'` etc. (service-defined) |

Standard `limit`, `cursor`, `sort` (`-run_date,-created_at` default).

## Bulk operations

POST batches accepts a body array — typical use case is morning planning ("create 5 planned batches for today's production schedule"). `Idempotency-Key` recommended.

PATCH batches bulk supported (`PATCH /v1/somaerp/production/batches` with `[{id, status}, ...]`) for end-of-shift completions.

## Cross-layer behaviors

- POST batch validates `kitchen_id` is `status='active'` (geography); `product_id` is `status='active'` (catalog); resolved `recipe_id` is `status='active'` (recipes); kitchen has a current `fct_kitchen_capacity` row for the product's `product_line_id` covering today's planned production window (advisory warning, not block).
- PATCH `status: in_progress → completed` triggers consumption-driven `evt_inventory_movements` with `movement_type='consumed'` and `batch_id_ref` (06_procurement layer, ADR-006).
- A batch cannot complete while any required QC checkpoint shows `fail` as latest result — must have a subsequent override check.
- Cancelling a started batch does NOT auto-revert consumption movements; operator records compensating `wasted` movements via procurement layer.
- Completion emits `somaerp.production.batches.completed` which downstream tennetctl flow (per `04_integration/05_flows_for_workflows.md`) consumes to schedule delivery for tomorrow's subscriptions.
- Consumption PATCH validates the lot's current_qty (from `v_inventory_current`) ≥ `actual_qty` and the lot's `qc_status != 'failed'`.

## Audit scope

| Endpoint | Additional scope |
|---|---|
| Batch POST | `entity_kind="production.batch"`, `properties={kitchen_id, product_id, recipe_id, run_date, planned_qty}` |
| Batch PATCH (status) | `properties={prior_status, new_status, actual_qty?, cancel_reason?}` — high-importance for completed/cancelled |
| Step log POST/PATCH | `entity_kind="production.step_log"`, `properties={batch_id, recipe_step_id, started_at, completed_at?}` |
| Consumption PATCH | `entity_kind="production.consumption"`, `properties={batch_id, raw_material_id, lot_number, planned_qty, actual_qty, unit_cost_at_consumption}` |

Idempotency-Key on batch POST is required for production use (operator hitting "create today's batches" twice from a flaky network must not double-create).

Completion event is also emitted with `category="production_milestone"` for downstream notify routing (operator dashboard refresh, inventory recount alerts).
