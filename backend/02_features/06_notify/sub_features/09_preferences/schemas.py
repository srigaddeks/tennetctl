"""Pydantic schemas for notify.preferences."""

from __future__ import annotations

from pydantic import BaseModel, Field


class PreferencePatchItem(BaseModel):
    channel_code: str = Field(..., description="Channel code: email, webpush, in_app, sms")
    category_code: str = Field(..., description="Category code: transactional, critical, marketing, digest")
    is_opted_in: bool = Field(..., description="TRUE = opted in; FALSE = opted out")


class PreferencePatchBody(BaseModel):
    preferences: list[PreferencePatchItem] = Field(..., min_length=1, max_length=16)


class PreferenceRow(BaseModel):
    channel_id: int
    channel_code: str
    channel_label: str
    category_id: int
    category_code: str
    category_label: str
    is_opted_in: bool
    is_locked: bool  # True when category=critical — cannot opt out
