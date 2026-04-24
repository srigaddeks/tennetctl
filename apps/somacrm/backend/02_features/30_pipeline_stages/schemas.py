"""Pydantic v2 schemas for pipeline stages."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PipelineStageCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=200)
    order_position: int = Field(default=0, ge=0)
    probability_pct: int = Field(default=0, ge=0, le=100)
    color: str = Field(default="#6366f1", max_length=20)
    is_won: bool = False
    is_lost: bool = False
    properties: dict[str, Any] = Field(default_factory=dict)


class PipelineStageUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = Field(default=None, min_length=1, max_length=200)
    order_position: int | None = Field(default=None, ge=0)
    probability_pct: int | None = Field(default=None, ge=0, le=100)
    color: str | None = Field(default=None, max_length=20)
    is_won: bool | None = None
    is_lost: bool | None = None
    properties: dict[str, Any] | None = None


class PipelineStageOut(BaseModel):
    """Mirror of v_pipeline_stages row."""

    model_config = ConfigDict(extra="ignore")
    id: str
    tenant_id: str
    name: str
    order_position: int
    probability_pct: int
    color: str
    is_won: bool
    is_lost: bool
    deals_count: int = 0
    properties: dict[str, Any] = Field(default_factory=dict)
    deleted_at: datetime | None = None
    created_by: str | None = None
    updated_by: str | None = None
    created_at: datetime
    updated_at: datetime
