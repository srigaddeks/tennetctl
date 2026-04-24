# API Design: Delivery

Conventions: see `00_conventions.md`. Endpoints rooted at `/v1/somaerp/delivery/...`. RBAC scopes: `somaerp.delivery.read` / `.write` / `.dispatch` (start runs) / `.complete` / `.admin`. Plus rider-self-service `somaerp.delivery.rider_self` for the rider's own runs/stops. Audit emission keys mirror `01_data_model/09_delivery.md`.

## Endpoints

### Riders

| Method | Path | Scope | Audit key |
|---|---|---|---|
| GET | `/v1/somaerp/delivery/riders` | `delivery.read` | (none) |
| POST | `/v1/somaerp/delivery/riders` | `delivery.write` | `somaerp.delivery.riders.created` |
| GET | `/v1/somaerp/delivery/riders/{id}` | `delivery.read` (or rider_self if own) | (none) |
| PATCH | `/v1/somaerp/delivery/riders/{id}` | `delivery.write` (or rider_self for own profile fields) | `.updated` / `.status_changed` |
| DELETE | `/v1/somaerp/delivery/riders/{id}` | `delivery.admin` | `.deleted` |

POST body:
```python
class RiderCreate(BaseModel):
    user_id: UUID                # tennetctl IAM user; rider must have a workspace login
    role_id: int
    display_name: str
    phone: str | None = None
    vehicle_jsonb: dict = {}
    payment_per_delivery: Decimal | None = None
    currency_code: str
    status: Literal["active","paused","terminated"] = "active"
    properties: dict = {}
```

Service validates: `user_id` exists in tennetctl IAM and is a workspace member (cross-system check via tennetctl_client).

### Delivery routes

| Method | Path | Scope | Audit key |
|---|---|---|---|
| GET | `/v1/somaerp/delivery/routes` | `delivery.read` | (none) |
| POST | `/v1/somaerp/delivery/routes` | `delivery.write` | `somaerp.delivery.routes.created` |
| GET | `/v1/somaerp/delivery/routes/{id}` | `delivery.read` | (none) |
| PATCH | `/v1/somaerp/delivery/routes/{id}` | `delivery.write` | `.updated` / `.status_changed` / `.sequence_updated` |
| DELETE | `/v1/somaerp/delivery/routes/{id}` | `delivery.admin` | `.deleted` |

POST body:
```python
class RouteCreate(BaseModel):
    kitchen_id: UUID
    service_zone_id: UUID | None = None
    name: str
    slug: str
    area: str | None = None
    expected_start_time: time = "06:00:00"
    expected_end_time: time = "07:30:00"
    default_rider_id: UUID | None = None
    sequence_jsonb: list[UUID] = []     # ordered customer_ids; mirror to lnk_route_customers
    status: Literal["active","paused","archived"] = "active"
    properties: dict = {}
```

Service mirrors `sequence_jsonb` to `lnk_route_customers` rows with corresponding `sequence_position`.

PATCH `sequence_jsonb` triggers atomic resync: closes existing `lnk_route_customers` rows (sets `effective_to=today`) and inserts new rows with new positions and `effective_from=today`. Emits `.sequence_updated`.

### Route customers

| Method | Path | Scope | Audit key |
|---|---|---|---|
| GET | `/v1/somaerp/delivery/routes/{route_id}/customers` | `delivery.read` | (none) |
| POST | `/v1/somaerp/delivery/routes/{route_id}/customers` | `delivery.write` | `somaerp.delivery.route_customers.added` |
| PATCH | `/v1/somaerp/delivery/routes/{route_id}/customers/{id}` | `delivery.write` | `.resequenced` (when sequence_position changes) |
| DELETE | `/v1/somaerp/delivery/routes/{route_id}/customers/{id}` | `delivery.write` | `.removed` (closes effective_to) |

POST body:
```python
class RouteCustomerAdd(BaseModel):
    customer_id: UUID
    sequence_position: int
    effective_from: date
    notes: str | None = None
```

DELETE = soft removal (sets `effective_to = today`).

### Delivery runs (lifecycle on append-mostly table)

| Method | Path | Scope | Audit key |
|---|---|---|---|
| GET | `/v1/somaerp/delivery/runs` | `delivery.read` (or rider_self for own) | (none) |
| POST | `/v1/somaerp/delivery/runs` | `delivery.dispatch` | `somaerp.delivery.runs.planned` |
| GET | `/v1/somaerp/delivery/runs/{id}` | `delivery.read` (or rider_self) | (none) |
| PATCH | `/v1/somaerp/delivery/runs/{id}` | `delivery.dispatch` (start) / `delivery.complete` (complete) / `rider_self` (start/complete own) | `.started` / `.completed` / `.cancelled` |

POST body:
```python
class DeliveryRunCreate(BaseModel):
    route_id: UUID
    run_date: date
    rider_id: UUID
    notes: str | None = None
```

Service computes `total_stops_planned` from current `lnk_route_customers` for the route minus customers paused on that date (joined against `evt_subscription_pauses` and customer status).

PATCH transitions:
- `{"status":"in_progress"}` sets `started_at=now()`
- `{"status":"completed"}` sets `completed_at=now()`, recomputes `total_stops_completed` from `evt_delivery_stops` summary
- `{"status":"cancelled"}` allowed from `planned` only

### Delivery stops (append-only events)

| Method | Path | Scope | Audit key |
|---|---|---|---|
| GET | `/v1/somaerp/delivery/stops` | `delivery.read` (or rider_self for own runs) | (none) |
| POST | `/v1/somaerp/delivery/stops` | `delivery.complete` (or rider_self for own run) | `.delivered` / `.missed` / `.rescheduled` / `.refused` |
| GET | `/v1/somaerp/delivery/stops/{id}` | `delivery.read` (or rider_self) | (none) |

No PATCH, no DELETE — append-only. A re-attempt is a new row.

POST body:
```python
class DeliveryStopCreate(BaseModel):
    delivery_run_id: UUID
    customer_id: UUID
    subscription_id: UUID | None = None
    sequence_position: int
    scheduled_at: datetime | None = None
    actual_at: datetime | None = None
    status: Literal["delivered","missed","rescheduled","refused"]
    photo_vault_key: str | None = None
    notes: str | None = None
```

Service validates: `delivery_run_id` exists with `status='in_progress'`; rider matches the request actor (for rider_self); `customer_id` is in current `lnk_route_customers` for the run's route; `photo_vault_key` is required for `status='delivered'`.

After insert: side effect updates `evt_delivery_runs.total_stops_completed` rollup if `status='delivered'`. `status='missed'` emits high-priority audit and triggers downstream notify flow (per `04_integration/05_flows_for_workflows.md`) for customer + operator.

### Today's plan (read view)

| Method | Path | Scope | Notes |
|---|---|---|---|
| GET | `/v1/somaerp/delivery/runs/plan` | `delivery.read` | Query: `kitchen_id`, `run_date` (default today). Returns the planned runs for that kitchen+date with each run's stops list (computed from current route customers and subscription pause state). Used by morning dispatch UI. |

## Filter parameters

### Routes list

| Param | Notes |
|---|---|
| `kitchen_id` | exact |
| `service_zone_id` | exact |
| `status` | comma list |
| `q` | name/area ILIKE |

### Riders list

| Param | Notes |
|---|---|
| `role_id` | exact |
| `status` | comma list |
| `user_id` | exact (lookup by tennetctl user) |
| `q` | display_name ILIKE |

### Runs list

| Param | Notes |
|---|---|
| `route_id` | exact |
| `rider_id` | exact |
| `run_date_from` / `run_date_to` | inclusive |
| `status` | comma list |

### Stops list

| Param | Notes |
|---|---|
| `delivery_run_id` | exact |
| `customer_id` | exact |
| `subscription_id` | exact |
| `status` | comma list |
| `created_after` / `created_before` | timestamp |

Standard `limit`, `cursor`, `sort`.

## Bulk operations

POST routes accepts array (bootstrap). POST riders accepts array. POST stops accepts array (rider's batch confirmation at end of run — common UX).

PATCH route customers bulk supported (`PATCH /v1/somaerp/delivery/routes/{route_id}/customers` with `[{id, sequence_position}, ...]`) for re-sequencing.

## Cross-layer behaviors

- POST route validates `kitchen_id` is `status='active'` (geography); `service_zone_id` (if set) is owned by the same kitchen.
- POST rider validates `user_id` is a workspace member via tennetctl IAM (cross-system call).
- POST route customer validates the customer's `service_zone_id` matches the route's (warning, not block — customer may belong to multiple routes during transition).
- POST run validates the route is `status='active'`; rider is `status='active'`; no other run exists for `(route_id, run_date)` (409 `CONFLICT`).
- POST stop with `status='delivered'` requires `photo_vault_key`. Service does NOT verify the vault key (trusted upload-token round-trip); high-priority audit logs the key.
- POST stop with `status='missed'` triggers a downstream tennetctl flow that emits a customer notify + an operator alert.
- Run completion validates: every customer in current route has a stop event for this run_date with a terminal status (`delivered`/`missed`/`rescheduled`/`refused`). Otherwise 422 `DEPENDENCY_VIOLATION`.
- Subscription cancellation in 08_customers triggers async removal of customer from active routes (advisory).

## Audit scope

| Endpoint | Additional scope |
|---|---|
| Routes POST/PATCH | `entity_kind="delivery.route"`, `properties={kitchen_id, service_zone_id?}` |
| Route customer add/remove | `entity_kind="delivery.route_customer"`, `properties={route_id, customer_id, sequence_position}` |
| Route sequence_updated | `properties={route_id, prior_sequence_count, new_sequence_count}` |
| Rider POST/PATCH | `entity_kind="delivery.rider"`, `properties={user_id, role_code, status}` |
| Run POST/PATCH | `entity_kind="delivery.run"`, `properties={route_id, run_date, rider_id, prior_status?, new_status?, total_stops_planned, total_stops_completed?}` |
| Stop POST | `entity_kind="delivery.stop"`, `properties={delivery_run_id, customer_id, subscription_id?, sequence_position, status, photo_vault_key?, actual_at}` |
| Stop missed | duplicate emission with `category="delivery_alert"` for downstream notify routing |

`Idempotency-Key` required for stop POST when from rider mobile (flaky network → operator must not double-deliver).
