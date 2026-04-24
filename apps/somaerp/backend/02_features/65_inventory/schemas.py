"""Pydantic v2 schemas for inventory + MRP planner."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

InventoryMovementType = Literal[
    "received", "consumed", "wasted", "adjusted", "expired"
]


# ── Current inventory (read-only) ───────────────────────────────────────


class InventoryCurrentOut(BaseModel):
    model_config = ConfigDict(extra="ignore")
    tenant_id: str
    kitchen_id: str
    kitchen_name: str | None = None
    raw_material_id: str
    raw_material_name: str | None = None
    raw_material_slug: str | None = None
    category_id: int | None = None
    category_code: str | None = None
    category_name: str | None = None
    default_unit_id: int
    default_unit_code: str | None = None
    default_unit_dimension: str | None = None
    target_unit_cost: Decimal | None = None
    currency_code: str
    qty_in_base_unit: Decimal
    qty_in_default_unit: Decimal | None = None


# ── Inventory movements ────────────────────────────────────────────────


class InventoryMovementCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kitchen_id: str
    raw_material_id: str
    movement_type: InventoryMovementType
    quantity: Decimal = Field(gt=0)
    unit_id: int
    lot_number: str | None = None
    reason: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class InventoryMovementOut(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    tenant_id: str
    kitchen_id: str
    kitchen_name: str | None = None
    raw_material_id: str
    raw_material_name: str | None = None
    raw_material_slug: str | None = None
    raw_material_category_id: int | None = None
    raw_material_category_code: str | None = None
    raw_material_category_name: str | None = None
    movement_type: InventoryMovementType
    quantity: Decimal
    unit_id: int
    unit_code: str | None = None
    unit_dimension: str | None = None
    lot_number: str | None = None
    batch_id_ref: str | None = None
    procurement_run_id: str | None = None
    reason: str | None = None
    ts: datetime
    performed_by_user_id: str
    metadata: dict[str, Any] = Field(default_factory=dict)


# ── MRP-lite planner ────────────────────────────────────────────────────


class ProcurementPlanDemand(BaseModel):
    model_config = ConfigDict(extra="forbid")
    product_id: str
    planned_qty: Decimal = Field(gt=0)
    target_date: date


class ProcurementPlanRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kitchen_id: str
    demand: list[ProcurementPlanDemand] = Field(min_length=1)


class ProcurementPlanRequirement(BaseModel):
    model_config = ConfigDict(extra="ignore")
    raw_material_id: str
    raw_material_name: str | None = None
    raw_material_slug: str | None = None
    category_name: str | None = None
    required_qty: Decimal
    required_unit_code: str | None = None
    in_stock_qty: Decimal
    gap_qty: Decimal
    primary_supplier_id: str | None = None
    primary_supplier_name: str | None = None
    last_known_unit_cost: Decimal | None = None
    target_unit_cost: Decimal | None = None
    estimated_cost: Decimal
    currency_code: str


class ProcurementPlanError(BaseModel):
    model_config = ConfigDict(extra="ignore")
    code: str
    product_id: str | None = None
    raw_material_id: str | None = None
    message: str


class ProcurementPlanResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    kitchen_id: str
    horizon_start: date
    horizon_end: date
    requirements: list[ProcurementPlanRequirement]
    unconvertible_units: list[dict[str, Any]] = Field(default_factory=list)
    errors: list[ProcurementPlanError] = Field(default_factory=list)
    total_estimated_cost: Decimal
    currency_code: str
