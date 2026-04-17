"""Pydantic schemas for notify.templates."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class TemplateBodyInput(BaseModel):
    channel_id: int = Field(..., ge=1, le=4, description="1=email, 2=webpush, 3=in_app, 4=sms")
    body_html: str = Field(..., min_length=1)
    body_text: str = ""
    preheader: str | None = None


class TemplateBodiesUpsert(BaseModel):
    bodies: list[TemplateBodyInput] = Field(..., min_length=1)


class TemplateCreate(BaseModel):
    org_id: str
    key: str = Field(..., min_length=1, max_length=64, pattern=r"^[a-z0-9_-]+$")
    group_id: str
    subject: str = Field(..., min_length=1)
    reply_to: str | None = None
    priority_id: int = Field(default=2, ge=1, le=4)
    bodies: list[TemplateBodyInput] | None = None


class TemplateUpdate(BaseModel):
    subject: str | None = Field(default=None, min_length=1)
    reply_to: str | None = None
    priority_id: int | None = Field(default=None, ge=1, le=4)
    group_id: str | None = None
    is_active: bool | None = None


class TemplateBodyRow(BaseModel):
    id: str
    template_id: str
    channel_id: int
    body_html: str
    body_text: str
    preheader: str | None


class TestSendRequest(BaseModel):
    to_email: str = Field(..., description="Recipient email for test send")
    context: dict = Field(default_factory=dict)


class TemplateRow(BaseModel):
    id: str
    org_id: str
    key: str
    group_id: str
    group_key: str
    category_id: int
    category_code: str
    category_label: str
    subject: str
    reply_to: str | None
    priority_id: int
    priority_code: str
    priority_label: str
    is_active: bool
    created_by: str
    updated_by: str
    created_at: datetime
    updated_at: datetime
    bodies: list[Any] = []
