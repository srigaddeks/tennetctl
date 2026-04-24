"""Pydantic v2 schemas for delivery routes + route<->customer link."""

from __future__ import annotations

from datetime import datetime, time
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

RouteStatus = Literal["active", "paused", "decommissioned"]


class RouteCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kitchen_id: str
    name: str = Field(min_length=1, max_length=200)
    slug: str = Field(min_length=1, max_length=200, pattern=r"^[a-z0-9][a-z0-9-]*$")
    area: str | None = None
    target_window_start: time | None = None
    target_window_end: time | None = None
    status: RouteStatus = "active"
    properties: dict[str, Any] = Field(default_factory=dict)


class RouteUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kitchen_id: str | None = None
    name: str | None = Field(default=None, min_length=1, max_length=200)
    slug: str | None = Field(
        default=None, min_length=1, max_length=200, pattern=r"^[a-z0-9][a-z0-9-]*$",
    )
    area: str | None = None
    target_window_start: time | None = None
    target_window_end: time | None = None
    status: RouteStatus | None = None
    properties: dict[str, Any] | None = None


class RouteOut(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    tenant_id: str
    kitchen_id: str
    kitchen_name: str | None = None
    name: str
    slug: str
    area: str | None = None
    target_window_start: time | None = None
    target_window_end: time | None = None
    status: RouteStatus
    properties: dict[str, Any] = Field(default_factory=dict)
    customer_count: int = 0
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str
    deleted_at: datetime | None = None


class RouteCustomerAttach(BaseModel):
    model_config = ConfigDict(extra="forbid")
    customer_id: str
    sequence_position: int | None = Field(default=None, ge=1)


class RouteCustomerReorder(BaseModel):
    model_config = ConfigDict(extra="forbid")
    customer_ids: list[str] = Field(min_length=1)


class RouteCustomerLinkOut(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    tenant_id: str
    route_id: str
    customer_id: str
    customer_name: str | None = None
    customer_phone: str | None = None
    customer_address: dict[str, Any] | None = None
    sequence_position: int
    created_at: datetime
    created_by: str
