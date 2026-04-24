# API Design: Raw Materials

Conventions: see `00_conventions.md`. Endpoints rooted at `/v1/somaerp/raw-materials/...`. RBAC scopes: `somaerp.raw_materials.read` / `.write` / `.admin`. Audit emission keys mirror `01_data_model/05_raw_materials.md`.

## Endpoints

### Raw materials

| Method | Path | Scope | Audit key |
|---|---|---|---|
| GET | `/v1/somaerp/raw-materials/materials` | `raw_materials.read` | (none) |
| POST | `/v1/somaerp/raw-materials/materials` | `raw_materials.write` | `somaerp.raw_materials.materials.created` |
| GET | `/v1/somaerp/raw-materials/materials/{id}` | `raw_materials.read` | (none) |
| PATCH | `/v1/somaerp/raw-materials/materials/{id}` | `raw_materials.write` | `.updated` / `.status_changed` |
| DELETE | `/v1/somaerp/raw-materials/materials/{id}` | `raw_materials.admin` | `somaerp.raw_materials.materials.deleted` |

POST body:
```python
class RawMaterialCreate(BaseModel):
    category_id: int
    name: str
    slug: str
    default_unit_id: int
    default_shelf_life_hours: int | None = None
    requires_lot_tracking: bool = True
    target_unit_cost: Decimal | None = None
    currency_code: str
    status: Literal["active","paused","discontinued"] = "active"
    properties: dict = {}
```

Response: row from `v_raw_materials`.

### Raw material variants

| Method | Path | Scope | Audit key |
|---|---|---|---|
| GET | `/v1/somaerp/raw-materials/materials/{material_id}/variants` | `raw_materials.read` | (none) |
| POST | `/v1/somaerp/raw-materials/materials/{material_id}/variants` | `raw_materials.write` | `somaerp.raw_materials.variants.created` |
| PATCH | `/v1/somaerp/raw-materials/materials/{material_id}/variants/{id}` | `raw_materials.write` | `.updated` |
| DELETE | `/v1/somaerp/raw-materials/materials/{material_id}/variants/{id}` | `raw_materials.admin` | `.deleted` |

POST body:
```python
class RawMaterialVariantCreate(BaseModel):
    name: str
    slug: str
    target_unit_cost: Decimal | None = None
    currency_code: str
    is_default: bool = False
    status: Literal["active","paused"] = "active"
    properties: dict = {}
```

`is_default=true` atomically clears prior default for the material.

### Suppliers

| Method | Path | Scope | Audit key |
|---|---|---|---|
| GET | `/v1/somaerp/raw-materials/suppliers` | `raw_materials.read` | (none) |
| POST | `/v1/somaerp/raw-materials/suppliers` | `raw_materials.write` | `somaerp.raw_materials.suppliers.created` |
| GET | `/v1/somaerp/raw-materials/suppliers/{id}` | `raw_materials.read` | (none) |
| PATCH | `/v1/somaerp/raw-materials/suppliers/{id}` | `raw_materials.write` | `.updated` / `.status_changed` |
| DELETE | `/v1/somaerp/raw-materials/suppliers/{id}` | `raw_materials.admin` | `.deleted` |

POST body:
```python
class SupplierCreate(BaseModel):
    name: str
    slug: str
    source_type_id: int
    location_id: UUID | None = None
    contact_jsonb: dict = {}
    payment_terms: str | None = None
    default_currency_code: str
    quality_rating: int | None = None
    status: Literal["active","paused","blacklisted"] = "active"
    properties: dict = {}
```

PATCH `status='blacklisted'` blocks future procurement runs against this supplier.

### Material ↔ supplier associations

| Method | Path | Scope | Audit key |
|---|---|---|---|
| GET | `/v1/somaerp/raw-materials/material-suppliers` | `raw_materials.read` | (none) |
| POST | `/v1/somaerp/raw-materials/material-suppliers` | `raw_materials.write` | `somaerp.raw_materials.material_supplier.linked` |
| PATCH | `/v1/somaerp/raw-materials/material-suppliers/{id}` | `raw_materials.write` | `.primary_changed` (when is_primary toggled) or `.updated` |
| DELETE | `/v1/somaerp/raw-materials/material-suppliers/{id}` | `raw_materials.write` | `somaerp.raw_materials.material_supplier.unlinked` |

POST body:
```python
class MaterialSupplierLink(BaseModel):
    raw_material_id: UUID
    supplier_id: UUID
    is_primary: bool = False
    last_known_unit_cost: Decimal | None = None
    currency_code: str
    notes: str | None = None
```

`is_primary=true` atomically clears prior primary for the material in a single PATCH transaction.

## Filter parameters

### Materials list

| Param | Notes |
|---|---|
| `category_id` | exact |
| `status` | comma list |
| `q` | name/slug ILIKE |
| `requires_lot_tracking` | bool |

### Suppliers list

| Param | Notes |
|---|---|
| `source_type_id` | exact |
| `location_id` | exact |
| `status` | comma list |
| `quality_rating_min` | numeric |
| `q` | name ILIKE |

### Material-suppliers list

| Param | Notes |
|---|---|
| `raw_material_id` | exact |
| `supplier_id` | exact |
| `is_primary` | bool |

Standard `limit`, `cursor`, `sort`, `include_deleted`.

## Bulk operations

POST array supported on `/materials`, `/suppliers`, `/material-suppliers` for bootstrap. Variants: not bulked.

## Cross-layer behaviors

- POST material with `default_unit_id` validates the unit exists in `dim_units_of_measure`.
- POST supplier with `location_id` validates location exists in same tenant.
- POST material-supplier validates both FKs in same tenant; partial unique on `(tenant_id, raw_material_id) WHERE is_primary` enforced atomically.
- DELETE on a material referenced by any active recipe ingredient → 422 `DEPENDENCY_VIOLATION`.
- DELETE on a material with positive `v_inventory_current` quantity → 422.
- DELETE on a supplier with non-voided procurement runs in last 90 days → 422.
- PATCH supplier `status='blacklisted'` triggers an advisory event consumed by procurement layer (warn on next run attempt).
- `last_known_unit_cost` on the link table is auto-updated by the procurement layer service after each `received` movement (not via this API directly).

## Audit scope

| Endpoint | Additional scope |
|---|---|
| Materials POST/PATCH | `entity_kind="raw_materials.material"`, `properties={category_code, default_unit_code}` |
| Suppliers POST/PATCH | `entity_kind="raw_materials.supplier"`, `properties={source_type_code, location_id?}` |
| Material-supplier link | `entity_kind="raw_materials.material_supplier"`, `properties={raw_material_id, supplier_id, is_primary}` |

Bootstrap-time tenant seeding (Soma Delights initial supplier + materials list) emits with `category=setup`.
