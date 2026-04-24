"""Pydantic v2 schemas for reporting views (read-only)."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


Bucket = Literal["daily", "weekly", "monthly"]
AlertLevel = Literal["critical", "low", "ok"]


# ── v_dashboard_today ────────────────────────────────────────────────────


class DashboardTodayOut(BaseModel):
    model_config = ConfigDict(extra="ignore")
    tenant_id: str
    date: date
    active_batches: int = 0
    completed_batches: int = 0
    in_transit_runs: int = 0
    completed_runs: int = 0
    scheduled_deliveries: int = 0
    completed_deliveries: int = 0
    active_subscriptions: int = 0


# ── Yield / COGS trends ──────────────────────────────────────────────────


class YieldTrendPoint(BaseModel):
    model_config = ConfigDict(extra="ignore")
    date: date
    kitchen_id: str
    kitchen_name: str | None = None
    product_id: str
    product_name: str | None = None
    planned_qty: Decimal
    actual_qty: Decimal
    yield_pct: Decimal | None = None
    batch_count: int


class CogsTrendPoint(BaseModel):
    model_config = ConfigDict(extra="ignore")
    date: date
    kitchen_id: str
    kitchen_name: str | None = None
    product_id: str
    product_name: str | None = None
    total_cogs: Decimal
    cogs_per_unit: Decimal | None = None
    batch_count: int
    currency_code: str | None = None


# ── Inventory reorder alerts ─────────────────────────────────────────────


class InventoryAlertOut(BaseModel):
    model_config = ConfigDict(extra="ignore")
    kitchen_id: str
    kitchen_name: str | None = None
    raw_material_id: str
    raw_material_name: str | None = None
    category_name: str | None = None
    current_qty: Decimal
    unit_code: str | None = None
    reorder_point_qty: Decimal | None = None
    alert_level: AlertLevel
    primary_supplier_id: str | None = None
    primary_supplier_name: str | None = None


# ── Procurement spend ────────────────────────────────────────────────────


class ProcurementSpendPoint(BaseModel):
    model_config = ConfigDict(extra="ignore")
    year_month: str
    kitchen_id: str
    kitchen_name: str | None = None
    supplier_id: str
    supplier_name: str | None = None
    total_spend: Decimal
    currency_code: str | None = None
    run_count: int
    line_count: int


# ── Revenue projection ───────────────────────────────────────────────────


class RevenueProjection(BaseModel):
    model_config = ConfigDict(extra="ignore")
    subscription_id: str
    customer_name: str | None = None
    plan_name: str | None = None
    frequency_code: str | None = None
    price_per_delivery: Decimal | None = None
    deliveries_per_week: Decimal | None = None
    weekly_projected: Decimal | None = None
    daily_projected: Decimal | None = None
    monthly_projected: Decimal | None = None
    currency_code: str | None = None


# ── Compliance ───────────────────────────────────────────────────────────


class ComplianceBatchRow(BaseModel):
    model_config = ConfigDict(extra="ignore")
    batch_id: str
    run_date: date
    product_name: str | None = None
    recipe_version: int | None = None
    kitchen_name: str | None = None
    planned_qty: Decimal
    actual_qty: Decimal | None = None
    lot_numbers: list[str] = Field(default_factory=list)
    qc_results: list[dict[str, Any]] = Field(default_factory=list)
    completed_by: str | None = None
