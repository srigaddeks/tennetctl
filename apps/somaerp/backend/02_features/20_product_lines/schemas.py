"""Pydantic v2 schemas for catalog.product_lines + categories (read-only)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

ProductLineStatus = Literal["active", "paused", "discontinued"]


class ProductCategoryOut(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: int
    code: str
    name: str
    deprecated_at: datetime | None = None


class ProductLineCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    category_id: int
    name: str = Field(min_length=1, max_length=200)
    slug: str = Field(min_length=1, max_length=200, pattern=r"^[a-z0-9][a-z0-9-]*$")
    status: ProductLineStatus = "active"
    properties: dict[str, Any] = Field(default_factory=dict)


class ProductLineUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    category_id: int | None = None
    name: str | None = Field(default=None, min_length=1, max_length=200)
    slug: str | None = Field(
        default=None, min_length=1, max_length=200, pattern=r"^[a-z0-9][a-z0-9-]*$",
    )
    status: ProductLineStatus | None = None
    properties: dict[str, Any] | None = None


class ProductLineOut(BaseModel):
    """Mirror of v_product_lines row."""

    model_config = ConfigDict(extra="ignore")
    id: str
    tenant_id: str
    category_id: int
    category_code: str | None = None
    category_name: str | None = None
    name: str
    slug: str
    status: ProductLineStatus
    properties: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str
    deleted_at: datetime | None = None


class ProductLineListFilters(BaseModel):
    model_config = ConfigDict(extra="forbid")
    category_id: int | None = None
    status: ProductLineStatus | None = None
    q: str | None = None
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)
    include_deleted: bool = False
