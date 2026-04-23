"""
social_publisher — Pydantic v2 schemas.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class SocialAccountCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    platform: str
    account_name: str
    account_handle: str
    account_id_on_platform: str
    bearer_token: str  # raw token — vaulted on write, never returned


class SocialAccountRow(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    org_id: str
    platform: str
    platform_label: str
    char_limit: int
    account_name: str
    account_handle: str | None
    account_id_on_platform: str | None
    vault_key: str
    is_active: bool
    follower_count: int | None
    profile_image_url: str | None
    created_at: datetime


class PostCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content_text: str
    media_urls: list[str] = []
    first_comment: str | None = None
    scheduled_at: datetime | None = None
    account_ids: list[str]


class PostUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content_text: str | None = None
    scheduled_at: datetime | None = None
    account_ids: list[str] | None = None
    status: str | None = None


class TargetAccount(BaseModel):
    model_config = ConfigDict(extra="ignore")

    account_id: str
    platform: str
    account_name: str
    account_handle: str | None


class PostRow(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    org_id: str
    workspace_id: str | None
    status: str
    status_label: str
    content_text: str
    media_urls: Any  # list[str] from JSONB
    first_comment: str | None
    scheduled_at: datetime | None
    published_at: datetime | None
    platform_post_ids: Any  # dict from JSONB
    error_message: str | None
    campaign_id: str | None
    author_user_id: str | None
    approved_by_user_id: str | None
    approved_at: datetime | None
    target_accounts: Any  # list[TargetAccount] from JSONB
    created_by: str
    updated_by: str
    created_at: datetime
    updated_at: datetime
