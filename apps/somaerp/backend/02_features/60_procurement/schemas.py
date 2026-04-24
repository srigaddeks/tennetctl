"""Pydantic v2 schemas for procurement runs + lines."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

ProcurementRunStatus = Literal["active", "reconciled", "cancelled"]


# ── Procurement run ─────────────────────────────────────────────────────


class ProcurementRunCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kitchen_id: str
    supplier_id: str
    run_date: date
    currency_code: str = Field(min_length=3, max_length=3)
    notes: str | None = None
    properties: dict[str, Any] = Field(default_factory=dict)


class ProcurementRunUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: ProcurementRunStatus | None = None
    notes: str | None = None
    properties: dict[str, Any] | None = None


class ProcurementRunOut(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    tenant_id: str
    kitchen_id: str
    kitchen_name: str | None = None
    supplier_id: str
    supplier_name: str | None = None
    supplier_slug: str | None = None
    run_date: date
    performed_by_user_id: str
    total_cost: Decimal
    computed_total: Decimal | None = None
    line_count: int = 0
    currency_code: str
    notes: str | None = None
    status: ProcurementRunStatus
    properties: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str
    deleted_at: datetime | None = None


# ── Procurement line ────────────────────────────────────────────────────


class ProcurementLineCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    raw_material_id: str
    quantity: Decimal = Field(gt=0)
    unit_id: int
    unit_cost: Decimal = Field(ge=0)
    lot_number: str | None = None
    quality_grade: int | None = Field(default=None, ge=1, le=5)
    received_at: datetime | None = None


class ProcurementLineUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    quantity: Decimal | None = Field(default=None, gt=0)
    unit_id: int | None = None
    unit_cost: Decimal | None = Field(default=None, ge=0)
    lot_number: str | None = None
    quality_grade: int | None = Field(default=None, ge=1, le=5)
    received_at: datetime | None = None


class ProcurementLineOut(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    tenant_id: str
    procurement_run_id: str
    raw_material_id: str
    raw_material_name: str | None = None
    raw_material_slug: str | None = None
    quantity: Decimal
    unit_id: int
    unit_code: str | None = None
    unit_cost: Decimal
    line_cost: Decimal
    lot_number: str | None = None
    quality_grade: int | None = None
    received_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str
    deleted_at: datetime | None = None
