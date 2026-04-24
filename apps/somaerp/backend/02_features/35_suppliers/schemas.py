"""Pydantic v2 schemas for suppliers + source_types + material<->supplier links."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

SupplierStatus = Literal["active", "paused", "blacklisted"]


class SupplierSourceTypeOut(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: int
    code: str
    name: str
    deprecated_at: datetime | None = None


# ── Suppliers ────────────────────────────────────────────────────────────


class SupplierCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=200)
    slug: str = Field(min_length=1, max_length=200, pattern=r"^[a-z0-9][a-z0-9-]*$")
    source_type_id: int
    location_id: str | None = None
    contact_jsonb: dict[str, Any] = Field(default_factory=dict)
    payment_terms: str | None = None
    default_currency_code: str = Field(min_length=3, max_length=3)
    quality_rating: int | None = Field(default=None, ge=1, le=5)
    status: SupplierStatus = "active"
    properties: dict[str, Any] = Field(default_factory=dict)


class SupplierUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = Field(default=None, min_length=1, max_length=200)
    slug: str | None = Field(
        default=None, min_length=1, max_length=200, pattern=r"^[a-z0-9][a-z0-9-]*$",
    )
    source_type_id: int | None = None
    location_id: str | None = None
    contact_jsonb: dict[str, Any] | None = None
    payment_terms: str | None = None
    default_currency_code: str | None = Field(default=None, min_length=3, max_length=3)
    quality_rating: int | None = Field(default=None, ge=1, le=5)
    status: SupplierStatus | None = None
    properties: dict[str, Any] | None = None


class SupplierOut(BaseModel):
    """Mirror of v_suppliers row."""

    model_config = ConfigDict(extra="ignore")
    id: str
    tenant_id: str
    name: str
    slug: str
    source_type_id: int
    source_type_code: str | None = None
    source_type_name: str | None = None
    location_id: str | None = None
    location_name: str | None = None
    contact_jsonb: dict[str, Any] = Field(default_factory=dict)
    payment_terms: str | None = None
    default_currency_code: str
    quality_rating: int | None = None
    status: SupplierStatus
    properties: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str
    deleted_at: datetime | None = None


# ── Material <-> Supplier link ───────────────────────────────────────────


class SupplierMaterialLinkCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    supplier_id: str
    is_primary: bool = False
    last_known_unit_cost: Decimal | None = None
    currency_code: str = Field(min_length=3, max_length=3)
    notes: str | None = None


class SupplierMaterialLinkUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    is_primary: bool | None = None
    last_known_unit_cost: Decimal | None = None
    currency_code: str | None = Field(default=None, min_length=3, max_length=3)
    notes: str | None = None


class SupplierMaterialLinkOut(BaseModel):
    """Mirror of v_raw_material_supplier_matrix row."""

    model_config = ConfigDict(extra="ignore")
    id: str
    tenant_id: str
    raw_material_id: str
    material_name: str | None = None
    material_slug: str | None = None
    supplier_id: str
    supplier_name: str | None = None
    supplier_slug: str | None = None
    source_type_code: str | None = None
    is_primary: bool
    last_known_unit_cost: Decimal | None = None
    currency_code: str
    notes: str | None = None
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str
