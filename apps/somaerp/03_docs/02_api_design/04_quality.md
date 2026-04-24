# API Design: Quality

Conventions: see `00_conventions.md`. Endpoints rooted at `/v1/somaerp/quality/...`. RBAC scopes: `somaerp.quality.read` / `.write` (define checkpoints) / `.record` (perform a check) / `.sign_off` (override a fail) / `.admin`. Audit emission keys mirror `01_data_model/04_quality.md`.

## Endpoints

### QC checkpoints (definitions)

| Method | Path | Scope | Audit key |
|---|---|---|---|
| GET | `/v1/somaerp/quality/checkpoints` | `quality.read` | (none) |
| POST | `/v1/somaerp/quality/checkpoints` | `quality.write` | `somaerp.quality.checkpoints.created` |
| GET | `/v1/somaerp/quality/checkpoints/{id}` | `quality.read` | (none) |
| PATCH | `/v1/somaerp/quality/checkpoints/{id}` | `quality.write` | `somaerp.quality.checkpoints.updated` |
| DELETE | `/v1/somaerp/quality/checkpoints/{id}` | `quality.admin` | `somaerp.quality.checkpoints.deleted` |

POST body:
```python
class CheckpointCreate(BaseModel):
    name: str
    stage_id: int                 # SMALLINT FK dim_qc_stages
    check_type_id: int            # SMALLINT FK dim_qc_check_types
    recipe_id: UUID | None = None
    recipe_step_number: int | None = None
    raw_material_id: UUID | None = None
    criteria_jsonb: dict = {}
    is_required: bool = True
    properties: dict = {}
```

Service validates: `recipe_step_number` only when `recipe_id IS NOT NULL` and stage = `in_production`; `raw_material_id` only when stage = `pre_production`. Returns 400 `VALIDATION_ERROR` otherwise.

Response: row from `v_qc_checkpoints` (resolves stage_code, check_type_code, recipe_name, raw_material_name).

### QC checks (performed events — append-only)

| Method | Path | Scope | Audit key |
|---|---|---|---|
| GET | `/v1/somaerp/quality/checks` | `quality.read` | (none) |
| POST | `/v1/somaerp/quality/checks` | `quality.record` | `somaerp.quality.checks.recorded` (+ `.failure` if result=fail) |
| GET | `/v1/somaerp/quality/checks/{id}` | `quality.read` | (none) |

No PATCH, no DELETE — `evt_qc_checks` is append-only.

POST body:
```python
class QCCheckCreate(BaseModel):
    checkpoint_id: UUID
    batch_id: UUID | None = None
    procurement_line_id: UUID | None = None
    lot_number: str | None = None
    result: Literal["pass","fail","warn"]
    result_value: Decimal | None = None
    result_scale: int | None = None
    notes: str | None = None
    photo_vault_key: str | None = None     # from prior tennetctl vault upload
```

Service validates: exactly one of `batch_id` or `procurement_line_id` is set (a check is either a production check or a pre-production raw-material check). The checkpoint's `stage_id` must be consistent (in_production checks require batch_id; pre_production checks require procurement_line_id; post_production checks require batch_id; fssai checks may have either or both).

After insert:
- Side effect 1: upsert the corresponding `dtl_batch_qc_results` row when `batch_id` is set (rebuild last_event_id, events_count++, recompute worst-case `result`).
- Side effect 2: when `procurement_line_id` is set, update that line's `qc_status` (pass/fail/pending). Emit `somaerp.procurement.lines.qc_status_changed`.
- Side effect 3: when `result='fail'`, emit additional `somaerp.quality.checks.failure` event which downstream tennetctl flow consumes for operator notification (per `04_integration/05_flows_for_workflows.md`).

Response: the inserted `evt_qc_checks` row (joined with checkpoint label).

### Sign-off / override (a documented exception, not an action endpoint)

A failed checkpoint blocks a batch from `in_progress → completed`. To override, an operator with `quality.sign_off` records a NEW `evt_qc_checks` row with `result='warn'` (or `pass` with a notes field). The service treats the latest event as authoritative for the rollup.

There is **no** `POST /v1/somaerp/quality/checks/{id}/override` action endpoint. The override is "record another check". This keeps the API shape clean while preserving auditability.

## Filter parameters

### Checkpoints list

| Param | Notes |
|---|---|
| `stage_id` | exact |
| `check_type_id` | exact |
| `recipe_id` | exact |
| `raw_material_id` | exact |
| `q` | name ILIKE |
| `is_required` | bool |

### Checks list

| Param | Notes |
|---|---|
| `checkpoint_id` | exact |
| `batch_id` | exact |
| `procurement_line_id` | exact |
| `lot_number` | exact (FSSAI traceability) |
| `performed_by_user_id` | exact |
| `result` | comma list |
| `created_after` / `created_before` | ISO timestamp |

Standard `limit`, `cursor`, `sort`.

## Bulk operations

Checkpoints POST accepts body array (bootstrap). Checks POST accepts array for batch-completion flows (operator submits 4 checks at once at end of batch). Each item evaluated independently; bulk emits one audit event per item plus failures stay inside the request envelope.

## Cross-layer behaviors

- POST checkpoint with `recipe_id` validates the recipe exists in same tenant; setting `recipe_step_number` validates it falls within `dtl_recipe_steps` count for that recipe.
- POST check with `batch_id` validates the batch exists, is in same tenant, and is `status='in_progress'` for in_production checks (post_production allowed when `status='in_progress'` or `'completed'` within last 24h).
- POST check with `procurement_line_id` updates `dtl_procurement_lines.qc_status` and may block downstream consumption (consumption of a `qc_status='failed'` lot returns 422 in production layer).
- A batch cannot transition to `status='completed'` if any required checkpoint with `result='fail'` is the latest event for that (batch, checkpoint) without a subsequent `pass`/`warn` from a `quality.sign_off` user. This is enforced by the production layer service.

## Audit scope

| Endpoint | Additional scope |
|---|---|
| Checkpoints POST/PATCH | `entity_kind="quality.checkpoint"`, `properties={stage_code, check_type_code}` |
| Checks POST | `entity_kind="quality.check"`, `properties={checkpoint_id, batch_id?, procurement_line_id?, result, lot_number?, photo_vault_key?}` |
| Failure event | duplicate emission with key `.failure` and `category="quality_alert"` for downstream notify routing |

Photo upload itself is a separate request to tennetctl `02_vault` (proxied by somaerp `/v1/somaerp/_internal/vault-upload-url`) before the check is recorded. See `04_integration/03_vault_for_secrets_and_blobs.md`.
