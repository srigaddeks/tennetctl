"""Pydantic v2 schemas for riders + rider roles."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

RiderStatus = Literal["active", "inactive", "suspended"]


class RiderRoleOut(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: int
    code: str
    name: str
    deprecated_at: datetime | None = None


class RiderCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=200)
    phone: str | None = None
    role_id: int
    vehicle_type: str | None = None
    license_number: str | None = None
    user_id: str | None = None
    status: RiderStatus = "active"
    properties: dict[str, Any] = Field(default_factory=dict)


class RiderUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = Field(default=None, min_length=1, max_length=200)
    phone: str | None = None
    role_id: int | None = None
    vehicle_type: str | None = None
    license_number: str | None = None
    user_id: str | None = None
    status: RiderStatus | None = None
    properties: dict[str, Any] | None = None


class RiderOut(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    tenant_id: str
    user_id: str | None = None
    name: str
    phone: str | None = None
    role_id: int
    role_name: str | None = None
    role_code: str | None = None
    vehicle_type: str | None = None
    license_number: str | None = None
    status: RiderStatus
    properties: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str
    deleted_at: datetime | None = None
