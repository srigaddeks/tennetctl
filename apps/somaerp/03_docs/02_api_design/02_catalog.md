# API Design: Catalog

Conventions: see `00_conventions.md`. Endpoints rooted at `/v1/somaerp/catalog/...`. RBAC scopes: `somaerp.catalog.read` / `.write` / `.admin`. Audit emission keys mirror `01_data_model/02_catalog.md`.

## Endpoints

### Product lines

| Method | Path | Scope | Audit key |
|---|---|---|---|
| GET | `/v1/somaerp/catalog/product-lines` | `catalog.read` | (none) |
| POST | `/v1/somaerp/catalog/product-lines` | `catalog.write` | `somaerp.catalog.product_lines.created` |
| GET | `/v1/somaerp/catalog/product-lines/{id}` | `catalog.read` | (none) |
| PATCH | `/v1/somaerp/catalog/product-lines/{id}` | `catalog.write` | `somaerp.catalog.product_lines.updated` or `.status_changed` |
| DELETE | `/v1/somaerp/catalog/product-lines/{id}` | `catalog.admin` | `somaerp.catalog.product_lines.deleted` |

POST body:
```python
class ProductLineCreate(BaseModel):
    category_id: int   # SMALLINT FK
    name: str
    slug: str
    status: Literal["active","paused","discontinued"] = "active"
    properties: dict = {}
```

Response: row from `v_product_lines`.

### Products

| Method | Path | Scope | Audit key |
|---|---|---|---|
| GET | `/v1/somaerp/catalog/products` | `catalog.read` | (none) |
| POST | `/v1/somaerp/catalog/products` | `catalog.write` | `somaerp.catalog.products.created` |
| GET | `/v1/somaerp/catalog/products/{id}` | `catalog.read` | (none) |
| PATCH | `/v1/somaerp/catalog/products/{id}` | `catalog.write` | `somaerp.catalog.products.updated` or `.status_changed` |
| DELETE | `/v1/somaerp/catalog/products/{id}` | `catalog.admin` | `somaerp.catalog.products.deleted` |

POST body:
```python
class ProductCreate(BaseModel):
    product_line_id: UUID
    name: str
    slug: str
    description: str | None = None
    target_benefit: str | None = None
    default_serving_size_ml: Decimal | None = None
    default_shelf_life_hours: int | None = None
    target_cogs_amount: Decimal | None = None
    default_selling_price: Decimal | None = None
    currency_code: str   # ISO 4217
    status: Literal["active","paused","discontinued"] = "active"
    tag_codes: list[str] = []
    properties: dict = {}
```

Response: row from `v_products` (includes `product_line_name`, `category_code`, `tag_codes` array).

PATCH allows `tag_codes` replacement (service computes diff and emits one `product_tags.attached` / `.detached` per change).

### Product variants

| Method | Path | Scope | Audit key |
|---|---|---|---|
| GET | `/v1/somaerp/catalog/products/{product_id}/variants` | `catalog.read` | (none) |
| POST | `/v1/somaerp/catalog/products/{product_id}/variants` | `catalog.write` | `somaerp.catalog.product_variants.created` |
| PATCH | `/v1/somaerp/catalog/products/{product_id}/variants/{id}` | `catalog.write` | `somaerp.catalog.product_variants.updated` |
| DELETE | `/v1/somaerp/catalog/products/{product_id}/variants/{id}` | `catalog.admin` | `somaerp.catalog.product_variants.deleted` |

POST body:
```python
class ProductVariantCreate(BaseModel):
    name: str
    slug: str
    serving_size_ml: Decimal | None = None
    selling_price: Decimal
    currency_code: str
    is_default: bool = False
    status: Literal["active","paused"] = "active"
    properties: dict = {}
```

Setting `is_default=true` via POST or PATCH atomically clears the previous default for that product (single PATCH transaction).

### Tags (read-only API; tag attachment is via product PATCH)

| Method | Path | Scope | Audit key |
|---|---|---|---|
| GET | `/v1/somaerp/catalog/tags` | `catalog.read` | (none) |

Returns the seeded `dim_product_tags` rows. Tag definitions are seeded; per-tenant addition via `properties.custom_tags` until promoted.

## Filter parameters

| Param | Endpoints | Notes |
|---|---|---|
| `q` | product-lines, products | name ILIKE |
| `category_id` | product-lines list | |
| `product_line_id` | products list | |
| `tag_code` | products list | comma-separated; matches any |
| `status` | all lists | |
| `currency_code` | products list | |

Standard `limit`, `cursor`, `sort`, `include_deleted`.

## Bulk operations

POST and PATCH accept body arrays for `/products` and `/product-lines` (tenant bootstrap). Variants are not bulked (low volume).

## Cross-layer behaviors

- Creating a product requires `product_line_id` exists in the same tenant. Cross-tenant → 422.
- DELETE on a product line with active products → 422 `DEPENDENCY_VIOLATION`.
- DELETE on a product with active recipes (any status != archived) or referenced by an active subscription plan item → 422.
- Setting product `status='discontinued'` triggers an advisory event consumed by `08_customers` (warn on subscription plans containing the product).
- Capacity rows in `01_geography` reference product_line_id; deleting a product_line requires zero non-deleted capacity rows.

## Audit scope

Mutation events carry the four-tuple plus:

| Endpoint | Additional scope |
|---|---|
| Products POST | `entity_kind="catalog.product"`, `properties = {product_line_id, currency_code}` |
| Products PATCH | `properties = {changed_fields:[...]}` |
| Variants POST/PATCH | `entity_kind="catalog.product_variant"`, `properties.product_id` |
| Tag attach/detach | `entity_kind="catalog.product_tag"`, `properties = {product_id, tag_code}` |

Bulk operations emit one audit event per item (not one per request).
