"""Pydantic v2 schemas for IAM applications endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, field_validator


class CreateApplicationRequest(BaseModel):
    code: str
    name: str
    category_id: int
    description: str | None = None
    slug: str | None = None
    icon_url: str | None = None
    redirect_uris: list[str] | None = None
    owner_user_id: str | None = None

    @field_validator("code", "name")
    @classmethod
    def not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Must not be empty.")
        return v


class UpdateApplicationRequest(BaseModel):
    name: str | None = None
    is_active: bool | None = None
    description: str | None = None
    slug: str | None = None
    icon_url: str | None = None
    redirect_uris: list[str] | None = None
    owner_user_id: str | None = None


class LinkApplicationProductRequest(BaseModel):
    product_id: str

    @field_validator("product_id")
    @classmethod
    def not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Must not be empty.")
        return v


class CreateApplicationTokenRequest(BaseModel):
    name: str
    expires_at: datetime | None = None

    @field_validator("name")
    @classmethod
    def not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Must not be empty.")
        return v


class RotateApplicationTokenRequest(BaseModel):
    name: str | None = None


class ResolveAccessRequest(BaseModel):
    environment: Literal["dev", "staging", "prod"] | None = None
