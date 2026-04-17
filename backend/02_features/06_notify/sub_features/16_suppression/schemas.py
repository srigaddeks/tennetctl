"""Pydantic schemas for notify.suppression."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field

ReasonCode = Literal["hard_bounce", "complaint", "manual", "unsubscribe"]


class SuppressionAdd(BaseModel):
    org_id: str
    email: EmailStr
    reason_code: ReasonCode = "manual"
    notes: str | None = Field(default=None, max_length=500)


class SuppressionRow(BaseModel):
    id: str
    org_id: str
    email: str
    reason_code: str
    delivery_id: str | None = None
    notes: str | None = None
    created_by: str
    created_at: datetime
