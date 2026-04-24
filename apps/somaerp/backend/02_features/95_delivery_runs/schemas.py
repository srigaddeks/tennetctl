"""Pydantic v2 schemas for delivery runs + stops + board."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

RunStatus = Literal["planned", "in_transit", "completed", "cancelled"]
StopStatus = Literal[
    "pending",
    "delivered",
    "missed",
    "customer_unavailable",
    "cancelled",
    "rescheduled",
]


class RunCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    route_id: str
    rider_id: str
    run_date: date
    notes: str | None = None
    properties: dict[str, Any] = Field(default_factory=dict)


class RunUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: RunStatus | None = None
    rider_id: str | None = None
    notes: str | None = None
    properties: dict[str, Any] | None = None
    allow_incomplete_completion: bool = False


class RunOut(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    tenant_id: str
    route_id: str
    route_name: str | None = None
    route_slug: str | None = None
    kitchen_id: str | None = None
    kitchen_name: str | None = None
    rider_id: str
    rider_name: str | None = None
    rider_phone: str | None = None
    run_date: date
    status: RunStatus
    started_at: datetime | None = None
    completed_at: datetime | None = None
    total_stops: int = 0
    completed_stops: int = 0
    missed_stops: int = 0
    completion_pct: float | None = None
    notes: str | None = None
    properties: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str
    deleted_at: datetime | None = None


class StopUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: StopStatus | None = None
    notes: str | None = None
    photo_vault_key: str | None = None
    signature_vault_key: str | None = None
    actual_at: datetime | None = None


class StopOut(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    tenant_id: str
    delivery_run_id: str
    customer_id: str
    customer_name: str | None = None
    customer_phone: str | None = None
    customer_address: dict[str, Any] | None = None
    sequence_position: int
    scheduled_at: datetime | None = None
    actual_at: datetime | None = None
    status: StopStatus
    photo_vault_key: str | None = None
    signature_vault_key: str | None = None
    notes: str | None = None
    properties: dict[str, Any] = Field(default_factory=dict)
    delay_sec: int | None = None
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str
    deleted_at: datetime | None = None


class RunBoardKitchen(BaseModel):
    kitchen_id: str
    kitchen_name: str | None = None
    runs: list[RunOut] = Field(default_factory=list)


class RunBoardOut(BaseModel):
    date: date
    kitchens: list[RunBoardKitchen] = Field(default_factory=list)
