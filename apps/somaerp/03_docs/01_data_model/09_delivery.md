# Data Model: Delivery

## Purpose

Models the milkman-style fixed morning delivery routes from the Soma Delights delivery-routes doc: named routes anchored to a kitchen, sequenced customer stops on the route, riders (referencing tennetctl IAM users — riders are people who log in), and append-only delivery runs and stops with photo proof of delivery stored in the tennetctl vault. The delivery layer is the operational tail of every subscription: a successful delivery stop is what fulfils a subscription's daily promise.

## Tables

### dim_rider_roles

Static role taxonomy.

| Column | Type | Notes |
|---|---|---|
| `id` | SMALLINT PK | |
| `code` | TEXT NOT NULL UNIQUE | "lead" / "partner" / "backup" / "founder" |
| `name` | TEXT NOT NULL | |

### fct_delivery_routes

A named route assigned to a kitchen.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `tenant_id` | UUID NOT NULL | |
| `kitchen_id` | UUID NOT NULL REFERENCES fct_kitchens(id) | |
| `service_zone_id` | UUID REFERENCES fct_service_zones(id) | nullable; convenience link |
| `name` | TEXT NOT NULL | "Route 1 — KPHB Cluster" |
| `slug` | TEXT NOT NULL | |
| `area` | TEXT | "KPHB Colony" |
| `sequence_jsonb` | JSONB NOT NULL DEFAULT '[]' | ordered list of customer_ids; mirrored by `lnk_route_customers.sequence_position` for indexed queries |
| `expected_start_time` | TIME NOT NULL DEFAULT '06:00:00' | |
| `expected_end_time` | TIME NOT NULL DEFAULT '07:30:00' | |
| `default_rider_id` | UUID REFERENCES fct_riders(id) | nullable |
| `status` | TEXT NOT NULL DEFAULT 'active' | active / paused / archived |
| `properties` | JSONB NOT NULL DEFAULT '{}' | |
| audit/timestamp/soft-delete columns | as conventions | |

Constraint: `UNIQUE (tenant_id, slug) WHERE deleted_at IS NULL`.

### fct_riders

A rider profile. Linked to a tennetctl IAM user — riders log in and confirm deliveries.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `tenant_id` | UUID NOT NULL | |
| `user_id` | UUID NOT NULL | tennetctl user id; NOT a duplicate user record |
| `role_id` | SMALLINT NOT NULL REFERENCES dim_rider_roles(id) | |
| `display_name` | TEXT NOT NULL | |
| `phone` | TEXT | |
| `vehicle_jsonb` | JSONB NOT NULL DEFAULT '{}' | `{"type":"scooter","plate":"...","insurance_expiry":"..."}` |
| `payment_per_delivery` | NUMERIC(10,4) | |
| `currency_code` | CHAR(3) NOT NULL | |
| `status` | TEXT NOT NULL DEFAULT 'active' | active / paused / terminated |
| `properties` | JSONB NOT NULL DEFAULT '{}' | |
| audit/timestamp/soft-delete columns | as conventions | |

Constraint: `UNIQUE (tenant_id, user_id) WHERE deleted_at IS NULL` — a tennetctl user maps to at most one rider profile per tenant.

### lnk_route_customers

Many-to-many route ↔ customer with a sequence_position. Rows are mutable for `sequence_position` updates as routes are reordered.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `tenant_id` | UUID NOT NULL | |
| `route_id` | UUID NOT NULL REFERENCES fct_delivery_routes(id) | |
| `customer_id` | UUID NOT NULL REFERENCES fct_customers(id) | |
| `sequence_position` | SMALLINT NOT NULL | 1-based ordering |
| `effective_from` | DATE NOT NULL | |
| `effective_to` | DATE | NULL = current |
| `notes` | TEXT | "gate code 4521" |
| `created_at` / `updated_at` | TIMESTAMPTZ | |

Constraints: partial `UNIQUE (tenant_id, route_id, customer_id) WHERE effective_to IS NULL`. Partial `UNIQUE (tenant_id, route_id, sequence_position) WHERE effective_to IS NULL`.

### evt_delivery_runs

One run of a route on a date by a rider. Append-only.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `tenant_id` | UUID NOT NULL | |
| `route_id` | UUID NOT NULL REFERENCES fct_delivery_routes(id) | |
| `run_date` | DATE NOT NULL | |
| `rider_id` | UUID NOT NULL REFERENCES fct_riders(id) | |
| `started_at` | TIMESTAMPTZ | NULL until rider starts |
| `completed_at` | TIMESTAMPTZ | NULL until rider completes |
| `status` | TEXT NOT NULL DEFAULT 'planned' | planned / in_progress / completed / cancelled |
| `total_stops_planned` | SMALLINT NOT NULL DEFAULT 0 | snapshot at planning |
| `total_stops_completed` | SMALLINT NOT NULL DEFAULT 0 | rolled up from `evt_delivery_stops` on completion |
| `notes` | TEXT | |
| `created_at` | TIMESTAMPTZ NOT NULL DEFAULT now() | |

CHECK: `status IN ('planned','in_progress','completed','cancelled')`. Although named `evt_*`, the row carries lifecycle status because the run is the operational unit; alternative would be one event per state transition. Decision: single mutable run row + immutable `evt_delivery_stops` per stop. The `evt_*` prefix is retained because the table contributes one row per (route, date, rider) which is event-shaped.

(Note: this is the one place where `evt_*` carries `updated_at` for the lifecycle fields. If audit treats this as a violation, plan-time may split into `fct_delivery_runs` + a separate event log; deferred to plan 56-11.)

### evt_delivery_stops

Per-customer stop. Append-only.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `tenant_id` | UUID NOT NULL | |
| `delivery_run_id` | UUID NOT NULL REFERENCES evt_delivery_runs(id) | |
| `customer_id` | UUID NOT NULL REFERENCES fct_customers(id) | |
| `subscription_id` | UUID REFERENCES fct_subscriptions(id) | nullable for one-off |
| `sequence_position` | SMALLINT NOT NULL | snapshot of route ordering |
| `scheduled_at` | TIMESTAMPTZ | |
| `actual_at` | TIMESTAMPTZ | |
| `status` | TEXT NOT NULL | "delivered" / "missed" / "rescheduled" / "refused" |
| `photo_vault_key` | TEXT | tennetctl vault key — proof of delivery |
| `notes` | TEXT | |
| `actor_user_id` | UUID NOT NULL | rider's user id |
| `created_at` | TIMESTAMPTZ NOT NULL DEFAULT now() | |

CHECK: `status IN ('delivered','missed','rescheduled','refused')`. No `updated_at`, no `deleted_at`. A re-attempt is a new row with `status='delivered'` referencing same customer + same run_date via a new `evt_delivery_runs` if needed.

## Views (v_*)

- `v_delivery_routes` — `fct_delivery_routes` joined with `fct_kitchens` (kitchen_name) and `fct_riders` (default_rider_name). Aggregates `lnk_route_customers` count.
- `v_route_customers_current` — `lnk_route_customers` filtered to `effective_to IS NULL`, joined with `fct_customers` for name/address.
- `v_riders` — `fct_riders` joined with `dim_rider_roles` and (cross-system, by id only) the tennetctl user display_name resolved at read time by service.
- `v_delivery_runs` — `evt_delivery_runs` joined with `fct_delivery_routes` and `fct_riders`.
- `v_delivery_stops` — `evt_delivery_stops` joined with `evt_delivery_runs`, `fct_customers`, `fct_subscriptions`.
- `v_subscription_delivery_health` — for each active subscription: count of `delivered` vs `missed` over last 7/30 days.

## Indexes

- `fct_delivery_routes (tenant_id, kitchen_id, status) WHERE deleted_at IS NULL`
- `fct_riders (tenant_id, user_id) WHERE deleted_at IS NULL`
- `lnk_route_customers (tenant_id, route_id, sequence_position) WHERE effective_to IS NULL`
- `lnk_route_customers (tenant_id, customer_id) WHERE effective_to IS NULL`
- `evt_delivery_runs (tenant_id, route_id, run_date DESC)`
- `evt_delivery_runs (tenant_id, rider_id, run_date DESC)`
- `evt_delivery_stops (tenant_id, delivery_run_id, sequence_position)`
- `evt_delivery_stops (tenant_id, customer_id, created_at DESC)` — customer history
- `evt_delivery_stops (tenant_id, subscription_id, created_at DESC) WHERE subscription_id IS NOT NULL`

## Audit emission keys

- `somaerp.delivery.routes.created` / `.updated` / `.status_changed` / `.deleted`
- `somaerp.delivery.routes.sequence_updated`
- `somaerp.delivery.riders.created` / `.updated` / `.status_changed` / `.deleted`
- `somaerp.delivery.route_customers.added` / `.removed` / `.resequenced`
- `somaerp.delivery.runs.planned`
- `somaerp.delivery.runs.started`
- `somaerp.delivery.runs.completed`
- `somaerp.delivery.runs.cancelled`
- `somaerp.delivery.stops.delivered`
- `somaerp.delivery.stops.missed` (high-priority — triggers customer notify flow)
- `somaerp.delivery.stops.rescheduled`
- `somaerp.delivery.stops.refused`

## Cross-layer relationships

- `fct_delivery_routes.kitchen_id` → `01_geography.fct_kitchens.id`
- `fct_delivery_routes.service_zone_id` → `01_geography.fct_service_zones.id`
- `fct_riders.user_id` → tennetctl `03_iam` user id (no FK — cross-system)
- `lnk_route_customers.customer_id` → `08_customers.fct_customers.id`
- `evt_delivery_stops.customer_id` → `08_customers.fct_customers.id`
- `evt_delivery_stops.subscription_id` → `08_customers.fct_subscriptions.id`
- `evt_delivery_stops.photo_vault_key` → tennetctl `02_vault` key (no FK; cross-system)

## Soma Delights tenant seed examples

| Table | Row |
|---|---|
| `dim_rider_roles` | `(lead)`, `(partner)`, `(backup)`, `(founder)` |
| `fct_riders` | `(user_id=founder_user, role=founder, display_name="Sri", payment_per_delivery=0, INR, status=active)` (Stage 1 the founder is the rider) |
| `fct_delivery_routes` | `(Route 1 — KPHB Cluster, kitchen=KPHB Home Kitchen, area="KPHB Colony", expected 06:00-07:30, default_rider=founder)` |
| `lnk_route_customers` | empty until customers exist |
| `evt_delivery_runs` | empty at bootstrap |
| `evt_delivery_stops` | empty at bootstrap |

Stage 2+ adds Miyapur Cluster route, Chandanagar Cluster route, hires first lead rider.

## Open questions

- Whether `evt_delivery_runs` should split into `fct_delivery_runs` (lifecycle) + `evt_delivery_run_events` (state-change log) — flagged above; deferred to plan 56-11.
- Real-time GPS tracking of rider — out of v0.9.0; carry as `properties.gps_track_url` if integrating later.
- Dynamic re-routing mid-run — out of v0.9.0; route is fixed for a given run_date.
- Rider compensation calculation rolled up over a period — view `v_rider_payouts` to be defined when payout workflow ships.
- Photo storage choice (raw blob in vault vs signed URL ref) — captured in `04_integration/03_vault_for_secrets_and_blobs.md`.
