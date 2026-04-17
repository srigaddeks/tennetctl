"""Pydantic schemas for notify.send (transactional API)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class TransactionalSendRequest(BaseModel):
    org_id: str
    template_key: str = Field(..., min_length=1, max_length=64)
    recipient_user_id: str = Field(..., min_length=1, description="User ID or direct email address")
    channel_code: Literal["email", "webpush", "in_app"] = "email"
    variables: dict[str, Any] = Field(default_factory=dict, description="Static variable overrides")


class TransactionalSendResponse(BaseModel):
    delivery_id: str
