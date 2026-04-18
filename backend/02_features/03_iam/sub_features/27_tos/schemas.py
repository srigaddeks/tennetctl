"""iam.tos — Pydantic schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class TosVersion(BaseModel):
    id: str
    version: str
    title: str
    body_markdown: str
    published_at: datetime | None
    effective_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TosVersionCreate(BaseModel):
    version: str
    title: str
    body_markdown: str = ""


class TosVersionPublish(BaseModel):
    effective_at: str  # ISO datetime string


class TosAcceptBody(BaseModel):
    version_id: str
