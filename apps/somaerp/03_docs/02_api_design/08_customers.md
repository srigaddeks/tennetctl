# API Design: Customers & Subscriptions

Conventions: see `00_conventions.md`. Endpoints rooted at `/v1/somaerp/customers/...`. RBAC scopes: `somaerp.customers.read` / `.write` / `.cancel` / `.admin`. Plus customer-self-service scopes `somaerp.customers.self_read` / `.self_write` for the customer portal (forwards as the customer's own user). Audit emission keys mirror `01_data_model/08_customers.md`.

## Endpoints

### Subscription plans (templates)

| Method | Path | Scope | Audit key |
|---|---|---|---|
| GET | `/v1/somaerp/customers/plans` | `customers.read` | (none) |
| POST | `/v1/somaerp/customers/plans` | `customers.write` | `somaerp.customers.plans.created` |
| GET | `/v1/somaerp/customers/plans/{id}` | `customers.read` | (none) |
| PATCH | `/v1/somaerp/customers/plans/{id}` | `customers.write` | `.updated` / `.status_changed` |
| DELETE | `/v1/somaerp/customers/plans/{id}` | `customers.admin` | `.deleted` |

POST body:
```python
class PlanCreate(BaseModel):
    name: str
    slug: str
    description: str | None = None
    delivery_frequency: Literal["daily","6_per_week","weekly","monthly"]
    delivery_days_jsonb: list[str]
    delivery_window_start: time
    delivery_window_end: time
    weekly_price: Decimal | None = None
    monthly_price: Decimal | None = None
    currency_code: str
    max_pause_days_per_month: int = 2
    status: Literal["active","paused","discontinued"] = "active"
    properties: dict = {}
    items: list[PlanItem] = []

class PlanItem(BaseModel):
    product_id: UUID
    product_variant_id: UUID | None = None
    qty_per_delivery: int = 1
    weekday: int | None = None   # 0=Sun..6=Sat or None for every-day
    display_order: int = 0
```

Service inserts plan + items in one transaction.

### Plan items (sub-resource)

| Method | Path | Scope | Audit key |
|---|---|---|---|
| GET | `/v1/somaerp/customers/plans/{plan_id}/items` | `customers.read` | (none) |
| POST | `/v1/somaerp/customers/plans/{plan_id}/items` | `customers.write` | `somaerp.customers.plan_items.added` |
| PATCH | `/v1/somaerp/customers/plans/{plan_id}/items/{id}` | `customers.write` | `somaerp.customers.plan_items.updated` |
| DELETE | `/v1/somaerp/customers/plans/{plan_id}/items/{id}` | `customers.write` | `somaerp.customers.plan_items.removed` |

Plan-item edits propagate to existing subscriptions on next billing cycle (no in-flight subscription is mutated).

### Customers

| Method | Path | Scope | Audit key |
|---|---|---|---|
| GET | `/v1/somaerp/customers/customers` | `customers.read` | (none) |
| POST | `/v1/somaerp/customers/customers` | `customers.write` | `somaerp.customers.customers.created` |
| GET | `/v1/somaerp/customers/customers/{id}` | `customers.read` (or `customers.self_read` if id == own) | (none) |
| PATCH | `/v1/somaerp/customers/customers/{id}` | `customers.write` (or `customers.self_write` if id == own) | `.updated` / `.status_changed` |
| DELETE | `/v1/somaerp/customers/customers/{id}` | `customers.admin` | `.deleted` |

POST body:
```python
class CustomerCreate(BaseModel):
    location_id: UUID
    service_zone_id: UUID | None = None
    name: str
    phone: str | None = None
    whatsapp: str | None = None
    email: str | None = None
    address_jsonb: dict = {}
    geo_lat: Decimal | None = None
    geo_lng: Decimal | None = None
    preferred_language: str | None = None
    dietary_jsonb: dict = {}
    properties: dict = {}
```

Service auto-assigns `service_zone_id` if omitted by matching `address_jsonb.pincode` against `fct_service_zones.polygon_jsonb.pincodes`.

### Subscriptions

| Method | Path | Scope | Audit key |
|---|---|---|---|
| GET | `/v1/somaerp/customers/subscriptions` | `customers.read` | (none) |
| POST | `/v1/somaerp/customers/subscriptions` | `customers.write` | `somaerp.customers.subscriptions.created` |
| GET | `/v1/somaerp/customers/subscriptions/{id}` | `customers.read` (or self) | (none) |
| PATCH | `/v1/somaerp/customers/subscriptions/{id}` | `customers.write` (or `.cancel` for cancellation, or self for pause) | `.status_changed` / `.kitchen_reassigned` / `.cancelled` |

No DELETE — subscriptions are soft-cancelled via PATCH `status='cancelled'`.

POST body:
```python
class SubscriptionCreate(BaseModel):
    customer_id: UUID
    plan_id: UUID
    serving_kitchen_id: UUID | None = None  # if omitted, resolved from customer's service_zone_id
    start_date: date
    end_date: date | None = None
    billing_cycle: Literal["weekly","monthly"] = "weekly"
    properties: dict = {}
```

Service resolves `serving_kitchen_id` if omitted: customer.service_zone.kitchen.

PATCH body (subset of mutable fields):
```python
class SubscriptionUpdate(BaseModel):
    status: Literal["active","paused","cancelled","expired"] | None = None
    serving_kitchen_id: UUID | None = None
    end_date: date | None = None
    cancel_reason: str | None = None
    plan_id: UUID | None = None      # plan change; effective next billing cycle
    billing_cycle: Literal["weekly","monthly"] | None = None
    properties: dict = {}
```

Allowed transitions: `active ↔ paused`, `* → cancelled` (terminal), automated `active → expired` when `end_date` passes (background job).

Cancellation requires `customers.cancel` scope (or `customers.self_write` for customer-driven cancel) plus `cancel_reason`.

Pause via PATCH `status='paused'` is paired with a separate POST to `/subscription-pauses` to record the pause window. The PATCH alone marks the subscription paused indefinitely; the pause-event POST is the structured pause window. (Same-call convenience: if PATCH body includes `pause: {from_date, to_date, reason}` the service does both atomically.)

### Subscription pauses (append-only events)

| Method | Path | Scope | Audit key |
|---|---|---|---|
| GET | `/v1/somaerp/customers/subscription-pauses` | `customers.read` | (none) |
| POST | `/v1/somaerp/customers/subscription-pauses` | `customers.write` (or `customers.self_write` for own) | `somaerp.customers.subscription_pauses.created` |
| GET | `/v1/somaerp/customers/subscription-pauses/{id}` | `customers.read` (or self) | (none) |

No PATCH, no DELETE — append-only.

POST body:
```python
class SubscriptionPauseCreate(BaseModel):
    subscription_id: UUID
    from_date: date
    to_date: date
    reason: str | None = None
    notes: str | None = None
```

Service validates: `to_date >= from_date`; total active pause days in current month ≤ `plan.max_pause_days_per_month`.

## Filter parameters

### Plans list

| Param | Notes |
|---|---|
| `status` | comma list |
| `delivery_frequency` | comma list |
| `q` | name ILIKE |

### Customers list

| Param | Notes |
|---|---|
| `location_id` | exact |
| `service_zone_id` | exact |
| `status` | comma list |
| `q` | name/phone/email ILIKE |
| `created_after` / `created_before` | timestamp |

### Subscriptions list

| Param | Notes |
|---|---|
| `customer_id` | exact |
| `plan_id` | exact |
| `serving_kitchen_id` | exact |
| `status` | comma list |
| `start_date_from` / `start_date_to` | inclusive |
| `next_billing_date_from` / `_to` | inclusive |
| `active_on` | ISO date — returns subs with `start_date <= date AND (end_date IS NULL OR end_date >= date) AND status IN ('active','paused')` |

### Pauses list

| Param | Notes |
|---|---|
| `subscription_id` | exact |
| `from_date_from` / `from_date_to` | inclusive |
| `to_date_from` / `to_date_to` | inclusive |
| `active_on` | ISO date — returns pauses where `from_date <= active_on <= to_date` |

Standard `limit`, `cursor`, `sort`, `include_deleted`.

## Bulk operations

Plans POST accepts array (bootstrap). Customers POST accepts array (CSV import). Subscriptions POST accepts array. Pauses POST accepts array.

`Idempotency-Key` recommended for all bulk POSTs.

## Cross-layer behaviors

- POST customer auto-resolves `service_zone_id` from `address_jsonb.pincode` if omitted.
- POST subscription auto-resolves `serving_kitchen_id` from customer's service_zone if omitted; 404 if not resolvable.
- POST subscription validates plan `status='active'`; 422 if discontinued.
- Subscription `serving_kitchen_id` change is a "kitchen reassignment" — emits `.kitchen_reassigned` and is consumed by 09_delivery to re-route customer.
- Pause window POST validates the window doesn't overlap existing active pauses for the same subscription (409 `CONFLICT`).
- Daily delivery planner (09_delivery layer) reads `v_subscriptions_active` minus `v_subscription_today_paused` to compute the day's stops.
- Cancelling a subscription emits a downstream event consumed by `09_delivery` to remove the customer from active routes.

## Audit scope

| Endpoint | Additional scope |
|---|---|
| Plans POST/PATCH | `entity_kind="customers.plan"`, `properties={delivery_frequency, currency_code, item_count}` |
| Plan items add/remove | `entity_kind="customers.plan_item"`, `properties={plan_id, product_id, weekday}` |
| Customers POST/PATCH | `entity_kind="customers.customer"`, `properties={location_id, service_zone_id?}` |
| Subscriptions POST | `entity_kind="customers.subscription"`, `properties={customer_id, plan_id, serving_kitchen_id, start_date, billing_cycle}` |
| Subscriptions PATCH | `properties={prior_status?, new_status?, prior_kitchen_id?, new_kitchen_id?, cancel_reason?}` |
| Pauses POST | `entity_kind="customers.subscription_pause"`, `properties={subscription_id, from_date, to_date, reason}` |

Customer self-service mutations carry the customer's own `user_id` as actor (the customer must have a tennetctl IAM user account in the same workspace).
