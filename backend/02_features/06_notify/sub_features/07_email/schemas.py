"""Schemas for notify.email — bounce webhook."""

from __future__ import annotations

from pydantic import BaseModel


class BounceWebhookPayload(BaseModel):
    delivery_id: str
    reason: str | None = None
