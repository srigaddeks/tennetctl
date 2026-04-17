"""Pydantic schemas for notify.deliveries."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class DeliveryRow(BaseModel):
    id: str
    org_id: str
    subscription_id: str | None
    template_id: str
    recipient_user_id: str
    channel_id: int
    channel_code: str
    channel_label: str
    priority_id: int
    priority_code: str
    priority_label: str
    status_id: int
    status_code: str
    status_label: str
    resolved_variables: dict
    audit_outbox_id: int | None
    failure_reason: str | None
    scheduled_at: Any = None
    attempted_at: Any = None
    delivered_at: Any = None
    created_at: Any
    updated_at: Any
