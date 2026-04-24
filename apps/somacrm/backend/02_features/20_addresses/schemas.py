"""Pydantic v2 schemas for addresses."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class AddressCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    entity_type: Literal["contact", "organization"]
    entity_id: str
    address_type_id: int
    is_primary: bool = False
    street: str | None = Field(default=None, max_length=500)
    city: str | None = Field(default=None, max_length=200)
    state: str | None = Field(default=None, max_length=200)
    country: str | None = Field(default=None, max_length=200)
    postal_code: str | None = Field(default=None, max_length=50)
    properties: dict[str, Any] = Field(default_factory=dict)


class AddressUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    address_type_id: int | None = None
    is_primary: bool | None = None
    street: str | None = Field(default=None, max_length=500)
    city: str | None = Field(default=None, max_length=200)
    state: str | None = Field(default=None, max_length=200)
    country: str | None = Field(default=None, max_length=200)
    postal_code: str | None = Field(default=None, max_length=50)
    properties: dict[str, Any] | None = None


class AddressOut(BaseModel):
    """Mirror of v_addresses row."""

    model_config = ConfigDict(extra="ignore")
    id: str
    tenant_id: str
    entity_type: str
    entity_id: str
    address_type_id: int
    address_type: str | None = None
    is_primary: bool
    street: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    postal_code: str | None = None
    full_address: str | None = None
    properties: dict[str, Any] = Field(default_factory=dict)
    deleted_at: datetime | None = None
    created_by: str | None = None
    updated_by: str | None = None
    created_at: datetime
    updated_at: datetime
