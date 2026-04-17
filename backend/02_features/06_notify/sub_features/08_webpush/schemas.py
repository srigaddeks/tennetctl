"""Pydantic schemas for notify.webpush sub-feature."""

from __future__ import annotations

from pydantic import BaseModel


class WebpushSubscriptionCreate(BaseModel):
    endpoint: str
    p256dh: str
    auth: str
    device_label: str | None = None


class WebpushSubscriptionOut(BaseModel):
    id: str
    org_id: str
    user_id: str
    endpoint: str
    p256dh: str
    auth: str
    device_label: str | None
    is_active: bool
    created_by: str
    updated_by: str
    created_at: str
    updated_at: str


class VapidPublicKeyOut(BaseModel):
    public_key: str
