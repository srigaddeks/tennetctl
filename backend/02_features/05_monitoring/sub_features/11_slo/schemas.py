"""Pydantic schemas for monitoring.slos — CRUD + indicator + evaluations."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


IndicatorKind = Literal["ratio", "threshold", "latency_pct"]
WindowKind = Literal["rolling_7d", "rolling_28d", "rolling_30d", "calendar_month", "calendar_quarter"]


class SloIndicatorRatio(BaseModel):
    """Indicator config for ratio-based SLO."""

    model_config = ConfigDict(extra="forbid")

    good_query: str = Field(min_length=1, description="DSL or SQL for success events")
    total_query: str = Field(min_length=1, description="DSL or SQL for total events")


class SloIndicatorThreshold(BaseModel):
    """Indicator config for threshold-based SLO."""

    model_config = ConfigDict(extra="forbid")

    threshold_metric_key: str = Field(min_length=1, description="Metric key to compare")
    threshold_value: float = Field(gt=0, description="Threshold value")
    threshold_op: Literal["lt", "lte", "gt", "gte", "eq"] = Field(
        description="Comparison operator"
    )


class SloIndicatorLatencyPct(BaseModel):
    """Indicator config for latency percentile SLO."""

    model_config = ConfigDict(extra="forbid")

    good_query: str = Field(
        min_length=1,
        description="DSL or SQL that counts requests meeting latency SLO",
    )
    total_query: str = Field(min_length=1, description="DSL or SQL for total requests")
    latency_percentile: float = Field(
        ge=0, le=100, description="Percentile (e.g., 99 for p99)"
    )


class SloBurnThresholds(BaseModel):
    """Google SRE multi-window burn rate thresholds."""

    model_config = ConfigDict(extra="forbid")

    fast_window_seconds: int = Field(default=3600, ge=60)
    fast_burn_rate: float = Field(default=14.4, gt=1)
    slow_window_seconds: int = Field(default=21600, ge=60)
    slow_burn_rate: float = Field(default=6.0, gt=1)
    page_on_fast: bool = Field(default=True)
    page_on_slow: bool = Field(default=True)


class SloCreateRequest(BaseModel):
    """Create a new SLO."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=200)
    slug: str = Field(min_length=1, max_length=100, pattern=r"^[a-z0-9_-]+$")
    description: str = Field(default="", max_length=1000)
    indicator_kind: IndicatorKind
    # Union without a Pydantic discriminator: each variant lacks a literal `kind`
    # field, and `indicator_kind` already carries the tag at the top level for
    # the service to branch on.
    indicator: SloIndicatorRatio | SloIndicatorThreshold | SloIndicatorLatencyPct
    window_kind: WindowKind
    target_pct: float = Field(gt=0, lt=100, description="Target attainment percentage")
    severity: str = Field(default="warning", description="Alert severity code")
    owner_user_id: str | None = Field(default=None)
    burn_thresholds: SloBurnThresholds | None = Field(default=None)


class SloUpdateRequest(BaseModel):
    """Partial update of an SLO."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    target_pct: float | None = Field(default=None, gt=0, lt=100)
    is_active: bool | None = Field(default=None)
    owner_user_id: str | None = Field(default=None)
    severity: str | None = Field(default=None)
    indicator: (
        SloIndicatorRatio | SloIndicatorThreshold | SloIndicatorLatencyPct | None
    ) = Field(default=None)
    burn_thresholds: SloBurnThresholds | None = Field(default=None)


class SloEvaluationResponse(BaseModel):
    """A single SLO evaluation snapshot."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: str
    slo_id: str
    window_start: datetime
    window_end: datetime
    good_count: int
    total_count: int
    attainment_pct: float
    budget_remaining_pct: float
    burn_rate_1h: float
    burn_rate_6h: float
    burn_rate_24h: float
    burn_rate_3d: float
    evaluated_at: datetime


class SloResponse(BaseModel):
    """Full SLO with latest evaluation and computed status."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: str
    org_id: str
    workspace_id: str | None
    name: str
    slug: str
    description: str
    indicator_kind_code: str
    window_kind_code: str
    target_pct: float
    severity_code: str
    owner_user_id: str | None
    is_active: bool
    status: Literal["healthy", "warning", "breaching"]
    attainment_pct: float
    budget_remaining_pct: float
    burn_rate_1h: float
    burn_rate_6h: float
    burn_rate_24h: float
    burn_rate_3d: float
    created_at: datetime
    updated_at: datetime

    # Indicator details
    good_query: str | None
    total_query: str | None
    threshold_metric_id: str | None
    threshold_value: float | None
    threshold_op: str | None
    latency_percentile: float | None

    # Burn thresholds
    fast_window_seconds: int
    fast_burn_rate: float
    slow_window_seconds: int
    slow_burn_rate: float
    page_on_fast: bool
    page_on_slow: bool

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> SloResponse:
        """Convert DB row to response model."""
        return cls(
            id=row["id"],
            org_id=row["org_id"],
            workspace_id=row.get("workspace_id"),
            name=row["name"],
            slug=row["slug"],
            description=row.get("description", ""),
            indicator_kind_code=row["indicator_kind_code"],
            window_kind_code=row["window_kind_code"],
            target_pct=float(row["target_pct"]),
            severity_code=row["severity_code"],
            owner_user_id=row.get("owner_user_id"),
            is_active=row["is_active"],
            status=row.get("status", "healthy"),
            attainment_pct=float(row.get("attainment_pct", 0)),
            budget_remaining_pct=float(row.get("budget_remaining_pct", 100)),
            burn_rate_1h=float(row.get("burn_rate_1h", 0)),
            burn_rate_6h=float(row.get("burn_rate_6h", 0)),
            burn_rate_24h=float(row.get("burn_rate_24h", 0)),
            burn_rate_3d=float(row.get("burn_rate_3d", 0)),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            good_query=row.get("good_query"),
            total_query=row.get("total_query"),
            threshold_metric_id=row.get("threshold_metric_id"),
            threshold_value=float(row["threshold_value"]) if row.get("threshold_value") else None,
            threshold_op=row.get("threshold_op"),
            latency_percentile=float(row["latency_percentile"]) if row.get("latency_percentile") else None,
            fast_window_seconds=int(row.get("fast_window_seconds", 3600)),
            fast_burn_rate=float(row.get("fast_burn_rate", 14.4)),
            slow_window_seconds=int(row.get("slow_window_seconds", 21600)),
            slow_burn_rate=float(row.get("slow_burn_rate", 6.0)),
            page_on_fast=bool(row.get("page_on_fast", True)),
            page_on_slow=bool(row.get("page_on_slow", True)),
        )


__all__ = [
    "IndicatorKind",
    "WindowKind",
    "SloIndicatorRatio",
    "SloIndicatorThreshold",
    "SloIndicatorLatencyPct",
    "SloBurnThresholds",
    "SloCreateRequest",
    "SloUpdateRequest",
    "SloEvaluationResponse",
    "SloResponse",
]
