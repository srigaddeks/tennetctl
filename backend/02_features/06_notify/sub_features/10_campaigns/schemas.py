"""Pydantic schemas for notify.campaigns."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class AudienceQuery(BaseModel):
    """Filter DSL for campaign audience resolution.

    account_type_codes: limit to users with one of these account types.
    Empty list = no filter (all active org users).
    """
    account_type_codes: list[str] = Field(default_factory=list)


class CampaignCreate(BaseModel):
    org_id: str
    name: str = Field(..., min_length=1, max_length=200)
    template_id: str
    channel_code: str = Field(..., description="Target channel: email, webpush, in_app")
    audience_query: AudienceQuery = Field(default_factory=AudienceQuery)
    scheduled_at: str | None = Field(None, description="ISO 8601 UTC timestamp")
    throttle_per_minute: int = Field(60, ge=1, le=10000)


class CampaignPatch(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    template_id: str | None = None
    channel_code: str | None = None
    audience_query: AudienceQuery | None = None
    scheduled_at: str | None = None
    throttle_per_minute: int | None = Field(None, ge=1, le=10000)
    status: Literal["scheduled", "cancelled"] | None = None


class CampaignRow(BaseModel):
    id: str
    org_id: str
    name: str
    template_id: str
    channel_id: int
    channel_code: str
    channel_label: str
    audience_query: dict
    scheduled_at: str | None
    throttle_per_minute: int
    status_id: int
    status_code: str
    status_label: str
    created_by: str
    updated_by: str
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}
