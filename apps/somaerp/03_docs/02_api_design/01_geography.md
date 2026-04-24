# API Design: Geography

Conventions: see `00_conventions.md`. All endpoints rooted at `/v1/somaerp/geography/...`. RBAC scopes: `somaerp.geography.read` / `.write` / `.admin`. Audit emission is mandatory on every mutation; keys mirror `01_data_model/01_geography.md`.

## Endpoints

### Locations

| Method | Path | Scope | Audit key |
|---|---|---|---|
| GET | `/v1/somaerp/geography/locations` | `geography.read` | (none — read) |
| POST | `/v1/somaerp/geography/locations` | `geography.write` | `somaerp.geography.locations.created` |
| GET | `/v1/somaerp/geography/locations/{id}` | `geography.read` | (none) |
| PATCH | `/v1/somaerp/geography/locations/{id}` | `geography.write` | `somaerp.geography.locations.updated` |
| DELETE | `/v1/somaerp/geography/locations/{id}` | `geography.admin` | `somaerp.geography.locations.deleted` |

POST request body (Pydantic):
```python
class LocationCreate(BaseModel):
    region_id: int                      # SMALLINT FK
    name: str
    slug: str
    timezone: str
    properties: dict = {}
```

Response data: row from `v_locations` (includes `region_code`, `country_code`, `regulatory_body`, `default_currency_code`).

PATCH body: any subset of the above fields. Empty body returns 204.

### Kitchens

| Method | Path | Scope | Audit key |
|---|---|---|---|
| GET | `/v1/somaerp/geography/kitchens` | `geography.read` | (none) |
| POST | `/v1/somaerp/geography/kitchens` | `geography.write` | `somaerp.geography.kitchens.created` |
| GET | `/v1/somaerp/geography/kitchens/{id}` | `geography.read` | (none) |
| PATCH | `/v1/somaerp/geography/kitchens/{id}` | `geography.write` | `somaerp.geography.kitchens.updated` or `.status_changed` |
| DELETE | `/v1/somaerp/geography/kitchens/{id}` | `geography.admin` | `somaerp.geography.kitchens.deleted` |

POST body:
```python
class KitchenCreate(BaseModel):
    location_id: UUID
    name: str
    slug: str
    kitchen_type: Literal["home","commissary","satellite"]
    address_jsonb: dict = {}
    geo_lat: Decimal | None = None
    geo_lng: Decimal | None = None
    status: Literal["active","paused","decommissioned"] = "active"
    properties: dict = {}
```

Response data: row from `v_kitchens` (includes `location_name`, `region_code`, `currency`, `tz`).

PATCH state transition: `active ↔ paused`, `* → decommissioned` (terminal). Decommission requires `geography.admin`. Audit key on status change is `somaerp.geography.kitchens.status_changed`; on other field updates `somaerp.geography.kitchens.updated`.

### Kitchen capacity

| Method | Path | Scope | Audit key |
|---|---|---|---|
| GET | `/v1/somaerp/geography/kitchens/{kitchen_id}/capacity` | `geography.read` | (none) |
| POST | `/v1/somaerp/geography/kitchens/{kitchen_id}/capacity` | `geography.write` | `somaerp.geography.kitchen_capacity.created` |
| GET | `/v1/somaerp/geography/kitchens/{kitchen_id}/capacity/{id}` | `geography.read` | (none) |
| PATCH | `/v1/somaerp/geography/kitchens/{kitchen_id}/capacity/{id}` | `geography.write` | `somaerp.geography.kitchen_capacity.closed` (when valid_to is set) |
| DELETE | `/v1/somaerp/geography/kitchens/{kitchen_id}/capacity/{id}` | `geography.admin` | (rare; soft-delete; `.deleted`) |

POST body:
```python
class CapacityCreate(BaseModel):
    product_line_id: UUID
    capacity_value: Decimal
    capacity_unit_id: int
    time_window_start: time   # "04:00:00"
    time_window_end: time     # "08:00:00"
    valid_from: date
    valid_to: date | None = None
    properties: dict = {}
```

PATCH only allows setting `valid_to` (closing an active row). Per ADR-003, capacity is replaced via close-old + insert-new, not in-place update of `capacity_value`.

Service-layer convenience wrapper: `POST /v1/somaerp/geography/kitchens/{kitchen_id}/capacity/replace` is **NOT** added (would be an action endpoint). Instead, the client makes two calls (PATCH the old row's `valid_to`, POST the new row). Plan-time may consider an idempotent two-step transactional helper inside service.py without exposing a new endpoint.

### Service zones

| Method | Path | Scope | Audit key |
|---|---|---|---|
| GET | `/v1/somaerp/geography/service-zones` | `geography.read` | (none) |
| POST | `/v1/somaerp/geography/service-zones` | `geography.write` | `somaerp.geography.service_zones.created` |
| GET | `/v1/somaerp/geography/service-zones/{id}` | `geography.read` | (none) |
| PATCH | `/v1/somaerp/geography/service-zones/{id}` | `geography.write` | `somaerp.geography.service_zones.updated` |
| DELETE | `/v1/somaerp/geography/service-zones/{id}` | `geography.admin` | `somaerp.geography.service_zones.deleted` |

POST body:
```python
class ServiceZoneCreate(BaseModel):
    kitchen_id: UUID
    name: str
    polygon_jsonb: dict   # GeoJSON polygon or {"pincodes":[...]}
    status: Literal["active","paused"] = "active"
    properties: dict = {}
```

## Filter parameters

| Param | Endpoints | Notes |
|---|---|---|
| `region_id` | locations list | |
| `q` | locations, kitchens | matches name (ILIKE) |
| `location_id` | kitchens list, service-zones list | |
| `status` | kitchens, service-zones list | |
| `kitchen_id` | service-zones list | |
| `product_line_id` | kitchen capacity list | |
| `valid_on` | kitchen capacity list | ISO date — returns rows where `valid_from <= valid_on AND (valid_to IS NULL OR valid_to > valid_on)` |
| `include_history` | kitchen capacity list | bool; default false (active only) |

Standard `limit`, `cursor`, `sort`, `include_deleted`.

## Bulk operations

POST accepts an array body for `/locations`, `/kitchens`, `/kitchens/{id}/capacity`, `/service-zones`. Useful for tenant-bootstrap seeding. Idempotency-Key recommended.

PATCH bulk supported as `PATCH /v1/somaerp/geography/kitchens` with body `[{id, ...patch}, ...]`.

## Cross-layer behaviors

- Creating a `kitchen_capacity` row validates `product_line_id` exists in the catalog layer for the same `tenant_id`. Cross-tenant FK → 422 `CROSS_TENANT_REFERENCE`.
- Creating a `service_zone` validates the `kitchen_id` is `status='active'`. Decommissioned kitchens reject new zones with 409.
- DELETE on a kitchen with active production batches in the last 30 days returns 422 `DEPENDENCY_VIOLATION` — operator must decommission via PATCH `status` first.
- Creating a kitchen auto-emits a downstream event consumed by `09_delivery` to suggest a default route (advisory; not auto-created).

## Audit scope

Every mutation populates the four-tuple `(user_id, session_id, org_id, workspace_id)` from the resolved session, plus:

| Endpoint | Additional scope fields |
|---|---|
| Kitchens POST/PATCH/DELETE | `entity_id = kitchen_id`, `entity_kind = "geography.kitchen"`, `properties.location_id` |
| Capacity POST/PATCH | `entity_id = capacity_row_id`, `entity_kind = "geography.kitchen_capacity"`, `properties = {kitchen_id, product_line_id, time_window_start, time_window_end, valid_from, valid_to}` |
| Service zones POST/PATCH | `entity_id = zone_id`, `entity_kind = "geography.service_zone"`, `properties.kitchen_id` |

Bootstrap-mode seeding (no user context yet) emits with `category=setup` per the documented bypass in `02_tenant_model.md`.
