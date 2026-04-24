# Data Model: Customers & Subscriptions

## Purpose

Models who the tenant sells to and the subscription plans those customers follow. Subscriptions are the business per the Soma Delights subscription-plans doc — one-time orders are out of scope for v0.9.0 (deferred). Plans are tenant-defined templates (`dim_subscription_plans`) with a product mix (`dtl_subscription_plan_items`) and a delivery cadence. A `fct_subscriptions` row instantiates a plan for a customer with start/end dates and current status. Pause events are append-only (`evt_subscription_pauses`).

## Tables

### dim_subscription_plans

A plan template. Tenant-scoped (each tenant defines its own plan menu) so `dim_*` here carries `tenant_id` + UUID PK. Per the overview's open question, named `dim` because it functions as a per-tenant catalog of plan definitions; revisit at audit time.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK DEFAULT uuid7() | |
| `tenant_id` | UUID NOT NULL | |
| `name` | TEXT NOT NULL | "Morning Glow Plan" |
| `slug` | TEXT NOT NULL | |
| `description` | TEXT | |
| `delivery_frequency` | TEXT NOT NULL | "daily" / "6_per_week" / "weekly" / "monthly" |
| `delivery_days_jsonb` | JSONB NOT NULL DEFAULT '[]' | `["mon","tue","wed","thu","fri","sat"]` |
| `delivery_window_start` | TIME | "06:00:00" |
| `delivery_window_end` | TIME | "07:30:00" |
| `weekly_price` | NUMERIC(14,4) | |
| `monthly_price` | NUMERIC(14,4) | |
| `currency_code` | CHAR(3) NOT NULL | |
| `max_pause_days_per_month` | SMALLINT NOT NULL DEFAULT 2 | |
| `status` | TEXT NOT NULL DEFAULT 'active' | active / paused / discontinued |
| `properties` | JSONB NOT NULL DEFAULT '{}' | |
| audit/timestamp/soft-delete columns | as conventions | |

Constraint: `UNIQUE (tenant_id, slug) WHERE deleted_at IS NULL`.

### dtl_subscription_plan_items

The product mix for a plan. Supports weekday-rotation via `weekday` column.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `tenant_id` | UUID NOT NULL | |
| `plan_id` | UUID NOT NULL REFERENCES dim_subscription_plans(id) | |
| `product_id` | UUID NOT NULL REFERENCES fct_products(id) | |
| `product_variant_id` | UUID REFERENCES fct_product_variants(id) | nullable; defaults to product's default variant |
| `qty_per_delivery` | SMALLINT NOT NULL DEFAULT 1 | |
| `weekday` | SMALLINT | NULL = every delivery day; otherwise 0=Sun..6=Sat |
| `display_order` | SMALLINT NOT NULL DEFAULT 0 | |
| `created_at` / `updated_at` | TIMESTAMPTZ | |

Constraint: `UNIQUE (tenant_id, plan_id, product_id, weekday)` — service handles NULL weekday with a partial index.

### fct_customers

The end customer of the tenant.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `tenant_id` | UUID NOT NULL | |
| `location_id` | UUID NOT NULL REFERENCES fct_locations(id) | which city; drives kitchen routing |
| `service_zone_id` | UUID REFERENCES fct_service_zones(id) | nullable; assigned at signup or first delivery |
| `name` | TEXT NOT NULL | |
| `phone` | TEXT | |
| `whatsapp` | TEXT | |
| `email` | TEXT | |
| `address_jsonb` | JSONB NOT NULL DEFAULT '{}' | `{"line1":"...", "apartment":"...", "landmark":"...", "pincode":"500072"}` |
| `geo_lat` | NUMERIC(9,6) | |
| `geo_lng` | NUMERIC(9,6) | |
| `preferred_language` | TEXT | "en" / "hi" / "te" |
| `dietary_jsonb` | JSONB NOT NULL DEFAULT '{}' | `{"vegan":true,"diabetic":false,"allergies":[]}` |
| `status` | TEXT NOT NULL DEFAULT 'active' | active / paused / churned |
| `properties` | JSONB NOT NULL DEFAULT '{}' | tenant-specific custom fields |
| audit/timestamp/soft-delete columns | as conventions | |

Constraint: `UNIQUE (tenant_id, phone) WHERE deleted_at IS NULL AND phone IS NOT NULL`.

### fct_subscriptions

A customer's active or historic subscription.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `tenant_id` | UUID NOT NULL | |
| `customer_id` | UUID NOT NULL REFERENCES fct_customers(id) | |
| `plan_id` | UUID NOT NULL REFERENCES dim_subscription_plans(id) | |
| `serving_kitchen_id` | UUID NOT NULL REFERENCES fct_kitchens(id) | resolved at signup; can change on relocation |
| `start_date` | DATE NOT NULL | |
| `end_date` | DATE | NULL = open-ended |
| `status` | TEXT NOT NULL DEFAULT 'active' | active / paused / cancelled / expired |
| `billing_cycle` | TEXT NOT NULL DEFAULT 'weekly' | weekly / monthly |
| `next_billing_date` | DATE | |
| `cancel_reason` | TEXT | |
| `properties` | JSONB NOT NULL DEFAULT '{}' | |
| audit/timestamp/soft-delete columns | as conventions | |

CHECK: `status IN ('active','paused','cancelled','expired')`.

### evt_subscription_pauses

Append-only pause record. Tracks every pause window the subscription has had.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `tenant_id` | UUID NOT NULL | |
| `subscription_id` | UUID NOT NULL REFERENCES fct_subscriptions(id) | |
| `from_date` | DATE NOT NULL | |
| `to_date` | DATE NOT NULL | |
| `reason` | TEXT | "travel" / "vacation" / "medical" / "other" |
| `notes` | TEXT | |
| `actor_user_id` | UUID NOT NULL | who triggered (customer self-service writes the customer's own user_id) |
| `created_at` | TIMESTAMPTZ NOT NULL DEFAULT now() | |

CHECK: `to_date >= from_date`. No `updated_at`, no `deleted_at`.

## Views (v_*)

- `v_subscription_plans` — `dim_subscription_plans` with aggregated item count and product list.
- `v_subscription_plan_items` — `dtl_subscription_plan_items` joined with `fct_products` for product_name.
- `v_customers` — `fct_customers` joined with `fct_locations` and `fct_service_zones`.
- `v_subscriptions` — `fct_subscriptions` joined with `fct_customers`, `dim_subscription_plans`, `fct_kitchens` (serving kitchen).
- `v_subscriptions_active` — `v_subscriptions` filtered to `status='active' AND (end_date IS NULL OR end_date >= today)`.
- `v_subscription_today_paused` — for a date, returns subscriptions paused on that date by joining `evt_subscription_pauses` ranges.

## Indexes

- `dim_subscription_plans (tenant_id, status) WHERE deleted_at IS NULL`
- `dtl_subscription_plan_items (tenant_id, plan_id, weekday)`
- `fct_customers (tenant_id, location_id, status) WHERE deleted_at IS NULL`
- `fct_customers (tenant_id, service_zone_id) WHERE deleted_at IS NULL`
- `fct_subscriptions (tenant_id, customer_id, status) WHERE deleted_at IS NULL`
- `fct_subscriptions (tenant_id, serving_kitchen_id, status, next_billing_date) WHERE deleted_at IS NULL` — daily delivery planning
- `evt_subscription_pauses (tenant_id, subscription_id, from_date, to_date)`

## Audit emission keys

- `somaerp.customers.plans.created` / `.updated` / `.status_changed` / `.deleted`
- `somaerp.customers.plan_items.added` / `.updated` / `.removed`
- `somaerp.customers.customers.created` / `.updated` / `.status_changed` / `.deleted`
- `somaerp.customers.subscriptions.created`
- `somaerp.customers.subscriptions.status_changed` (status transitions)
- `somaerp.customers.subscriptions.kitchen_reassigned`
- `somaerp.customers.subscriptions.cancelled`
- `somaerp.customers.subscription_pauses.created`

## Cross-layer relationships

- `fct_customers.location_id` → `01_geography.fct_locations.id`
- `fct_customers.service_zone_id` → `01_geography.fct_service_zones.id`
- `fct_subscriptions.serving_kitchen_id` → `01_geography.fct_kitchens.id`
- `dtl_subscription_plan_items.product_id` → `02_catalog.fct_products.id`
- `dtl_subscription_plan_items.product_variant_id` → `02_catalog.fct_product_variants.id`
- `fct_customers.id` ← `09_delivery.lnk_route_customers.customer_id`, `09_delivery.evt_delivery_stops.customer_id`

## Soma Delights tenant seed examples

| Table | Row |
|---|---|
| `dim_subscription_plans` | `(Morning Glow Plan, 6_per_week, Mon-Sat, 06:00-07:30, weekly_price=549, monthly_price=2099, INR, max_pause_days=2)`; `(Hydration Habit Plan)`; `(Family Wellness Plan)` |
| `dtl_subscription_plan_items` (Morning Glow) | `(Green Morning, qty=1, weekday=mon)`, `(Green Morning, weekday=wed)`, `(Green Morning, weekday=fri)`, `(Citrus Immunity, weekday=tue)`, `(Citrus Immunity, weekday=thu)`, `(Beetroot Recharge, weekday=sat)` |
| `fct_customers` | empty at bootstrap (no real customers seeded — placeholder shape only) |
| `fct_subscriptions` | empty at bootstrap |
| `evt_subscription_pauses` | empty |

## Open questions

- Whether to ship one-off order entity (`fct_orders`) for non-subscription sales — out of v0.9.0 scope per phase boundaries.
- Customer wallet / pre-pay credit — explicitly rejected in subscription-plans.md ("anti-habit"); not modeled.
- Multi-recipient households (one customer pays, multiple recipients receive) — currently one customer = one delivery. Promote to a `dtl_customer_recipients` table when family plans need split delivery.
- Billing actually charging the customer — out of v0.9.0 scope; tennetctl 07_billing primitive will handle when ready. Subscription `next_billing_date` is the integration anchor.
- Loyalty / referral tracking — carry in `properties.referral_source` until promoted.
