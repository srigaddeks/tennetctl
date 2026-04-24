"""Pydantic v2 schemas for production batches + nested step_logs / consumption / qc."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

BatchStatus = Literal["planned", "in_progress", "completed", "cancelled"]


# ── Batch header ───────────────────────────────────────────────────────


class BatchCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kitchen_id: str
    product_id: str
    recipe_id: str | None = None
    run_date: date | None = None
    shift_start: datetime | None = None
    planned_qty: Decimal = Field(gt=0)
    lead_user_id: str | None = None
    notes: str | None = None
    properties: dict[str, Any] = Field(default_factory=dict)


class BatchStatePatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: BatchStatus | None = None
    actual_qty: Decimal | None = Field(default=None, ge=0)
    cancel_reason: str | None = None
    notes: str | None = None
    lead_user_id: str | None = None
    properties: dict[str, Any] | None = None


class BatchOut(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    tenant_id: str
    kitchen_id: str
    kitchen_name: str | None = None
    product_id: str
    product_name: str | None = None
    product_slug: str | None = None
    default_selling_price: Decimal | None = None
    recipe_id: str
    recipe_version: int | None = None
    recipe_status: str | None = None
    run_date: date
    planned_qty: Decimal
    actual_qty: Decimal | None = None
    status: BatchStatus
    shift_start: datetime | None = None
    shift_end: datetime | None = None
    cancel_reason: str | None = None
    currency_code: str
    lead_user_id: str | None = None
    notes: str | None = None
    properties: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str
    deleted_at: datetime | None = None


# ── Step logs ──────────────────────────────────────────────────────────


class BatchStepLogOut(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    tenant_id: str
    batch_id: str
    recipe_step_id: str | None = None
    step_number: int
    name: str
    started_at: datetime | None = None
    completed_at: datetime | None = None
    performed_by_user_id: str | None = None
    notes: str | None = None
    duration_min: Decimal | None = None
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str
    deleted_at: datetime | None = None


class BatchStepPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    started_at: datetime | None = None
    completed_at: datetime | None = None
    notes: str | None = None


# ── Consumption ────────────────────────────────────────────────────────


class BatchConsumptionLineOut(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    tenant_id: str
    batch_id: str
    raw_material_id: str
    raw_material_name: str | None = None
    raw_material_slug: str | None = None
    recipe_ingredient_id: str | None = None
    planned_qty: Decimal
    actual_qty: Decimal | None = None
    unit_id: int
    unit_code: str | None = None
    unit_dimension: str | None = None
    unit_cost_snapshot: Decimal
    currency_code: str
    lot_number: str | None = None
    line_cost_actual: Decimal | None = None
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str
    deleted_at: datetime | None = None


class BatchConsumptionPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    actual_qty: Decimal | None = Field(default=None, ge=0)
    lot_number: str | None = None
    unit_cost_snapshot: Decimal | None = Field(default=None, ge=0)


# ── QC ─────────────────────────────────────────────────────────────────


class BatchQcResultCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    checkpoint_id: str
    outcome_id: int
    measured_value: Decimal | None = None
    measured_unit_id: int | None = None
    notes: str | None = None
    photo_vault_key: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class BatchQcResultOut(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    tenant_id: str
    batch_id: str
    checkpoint_id: str
    checkpoint_name: str | None = None
    checkpoint_scope_kind: str | None = None
    outcome_id: int
    outcome_code: str | None = None
    outcome_name: str | None = None
    measured_value: Decimal | None = None
    measured_unit_id: int | None = None
    measured_unit_code: str | None = None
    notes: str | None = None
    photo_vault_key: str | None = None
    performed_by_user_id: str | None = None
    last_event_id: str | None = None
    events_count: int = 0
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str
    deleted_at: datetime | None = None


# ── Summary ────────────────────────────────────────────────────────────


class BatchSummaryOut(BaseModel):
    model_config = ConfigDict(extra="ignore")
    batch_id: str
    tenant_id: str
    kitchen_id: str
    product_id: str
    recipe_id: str
    run_date: date
    status: BatchStatus
    planned_qty: Decimal
    actual_qty: Decimal | None = None
    yield_pct: Decimal | None = None
    total_cogs: Decimal
    cogs_per_unit: Decimal | None = None
    gross_margin_pct: Decimal | None = None
    duration_min: Decimal | None = None
    ingredient_count: int = 0
    has_unconvertible_units: bool = False
    step_count_total: int = 0
    step_count_completed: int = 0
    currency_code: str
    default_selling_price: Decimal | None = None


# ── Composite Out (batch + nested collections) ─────────────────────────


class BatchDetailOut(BaseModel):
    model_config = ConfigDict(extra="ignore")
    batch: BatchOut
    steps: list[BatchStepLogOut] = Field(default_factory=list)
    consumption: list[BatchConsumptionLineOut] = Field(default_factory=list)
    qc_results: list[BatchQcResultOut] = Field(default_factory=list)
    summary: BatchSummaryOut | None = None
