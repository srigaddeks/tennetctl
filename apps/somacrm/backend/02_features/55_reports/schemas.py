"""Pydantic v2 schemas for reports."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict


class PipelineSummaryStage(BaseModel):
    model_config = ConfigDict(extra="ignore")
    stage_id: str | None
    stage_name: str | None
    stage_color: str | None
    stage_order: int | None
    deal_count: int
    total_value: Decimal | None


class PipelineSummaryOut(BaseModel):
    model_config = ConfigDict(extra="ignore")
    stages: list[PipelineSummaryStage]
    total_deals: int
    total_value: Decimal | None


class LeadConversionRow(BaseModel):
    model_config = ConfigDict(extra="ignore")
    status: str | None
    lead_count: int


class LeadConversionOut(BaseModel):
    model_config = ConfigDict(extra="ignore")
    by_status: list[LeadConversionRow]
    total_leads: int


class ActivitySummaryRow(BaseModel):
    model_config = ConfigDict(extra="ignore")
    activity_type: str | None
    status: str | None
    count: int


class ActivitySummaryOut(BaseModel):
    model_config = ConfigDict(extra="ignore")
    rows: list[ActivitySummaryRow]
    total: int


class ContactGrowthRow(BaseModel):
    model_config = ConfigDict(extra="ignore")
    week: str
    new_contacts: int


class ContactGrowthOut(BaseModel):
    model_config = ConfigDict(extra="ignore")
    weeks: list[ContactGrowthRow]
