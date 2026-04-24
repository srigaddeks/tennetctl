"""Pydantic v2 schemas for catalog.products + variants + tags (read-only)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

ProductStatus = Literal["active", "paused", "discontinued"]
ProductVariantStatus = Literal["active", "paused"]


class ProductTagOut(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: int
    code: str
    name: str
    deprecated_at: datetime | None = None


# ── Products ─────────────────────────────────────────────────────────────

class ProductCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    product_line_id: str
    name: str = Field(min_length=1, max_length=200)
    slug: str = Field(min_length=1, max_length=200, pattern=r"^[a-z0-9][a-z0-9-]*$")
    description: str | None = None
    target_benefit: str | None = None
    default_serving_size_ml: Decimal | None = None
    default_shelf_life_hours: int | None = Field(default=None, ge=0)
    target_cogs_amount: Decimal | None = None
    default_selling_price: Decimal | None = None
    currency_code: str = Field(min_length=3, max_length=3)
    status: ProductStatus = "active"
    tag_codes: list[str] = Field(default_factory=list)
    properties: dict[str, Any] = Field(default_factory=dict)


class ProductUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    product_line_id: str | None = None
    name: str | None = Field(default=None, min_length=1, max_length=200)
    slug: str | None = Field(
        default=None, min_length=1, max_length=200, pattern=r"^[a-z0-9][a-z0-9-]*$",
    )
    description: str | None = None
    target_benefit: str | None = None
    default_serving_size_ml: Decimal | None = None
    default_shelf_life_hours: int | None = Field(default=None, ge=0)
    target_cogs_amount: Decimal | None = None
    default_selling_price: Decimal | None = None
    currency_code: str | None = Field(default=None, min_length=3, max_length=3)
    status: ProductStatus | None = None
    tag_codes: list[str] | None = None
    properties: dict[str, Any] | None = None


class ProductOut(BaseModel):
    """Mirror of v_products row."""

    model_config = ConfigDict(extra="ignore")
    id: str
    tenant_id: str
    product_line_id: str
    product_line_name: str | None = None
    product_line_slug: str | None = None
    category_id: int | None = None
    category_code: str | None = None
    category_name: str | None = None
    name: str
    slug: str
    description: str | None = None
    target_benefit: str | None = None
    default_serving_size_ml: Decimal | None = None
    default_shelf_life_hours: int | None = None
    target_cogs_amount: Decimal | None = None
    default_selling_price: Decimal | None = None
    currency_code: str
    status: ProductStatus
    tag_codes: list[str] = Field(default_factory=list)
    properties: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str
    deleted_at: datetime | None = None


class ProductListFilters(BaseModel):
    model_config = ConfigDict(extra="forbid")
    product_line_id: str | None = None
    tag_code: str | None = None
    status: ProductStatus | None = None
    currency_code: str | None = None
    q: str | None = None
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)
    include_deleted: bool = False


# ── Product variants ─────────────────────────────────────────────────────

class ProductVariantCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=200)
    slug: str = Field(min_length=1, max_length=200, pattern=r"^[a-z0-9][a-z0-9-]*$")
    serving_size_ml: Decimal | None = None
    selling_price: Decimal
    currency_code: str = Field(min_length=3, max_length=3)
    is_default: bool = False
    status: ProductVariantStatus = "active"
    properties: dict[str, Any] = Field(default_factory=dict)


class ProductVariantUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = Field(default=None, min_length=1, max_length=200)
    slug: str | None = Field(
        default=None, min_length=1, max_length=200, pattern=r"^[a-z0-9][a-z0-9-]*$",
    )
    serving_size_ml: Decimal | None = None
    selling_price: Decimal | None = None
    currency_code: str | None = Field(default=None, min_length=3, max_length=3)
    is_default: bool | None = None
    status: ProductVariantStatus | None = None
    properties: dict[str, Any] | None = None


class ProductVariantOut(BaseModel):
    """Mirror of v_product_variants row."""

    model_config = ConfigDict(extra="ignore")
    id: str
    tenant_id: str
    product_id: str
    product_name: str | None = None
    product_slug: str | None = None
    name: str
    slug: str
    serving_size_ml: Decimal | None = None
    selling_price: Decimal | None = None
    currency_code: str
    is_default: bool
    status: ProductVariantStatus
    properties: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str
    deleted_at: datetime | None = None
