"""Pydantic schemas for global library endpoints."""

from __future__ import annotations

from pydantic import BaseModel, Field


# ── Request models ─────────────────────────────────────────────────────────────

class PublishGlobalLibraryRequest(BaseModel):
    source_library_id: str = Field(..., description="UUID of the org library to publish")
    global_code: str = Field(..., min_length=1, max_length=100)
    global_name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    category_code: str | None = None
    is_featured: bool = False


class SubscribeRequest(BaseModel):
    auto_update: bool = True


# ── Response models ────────────────────────────────────────────────────────────

class GlobalLibraryResponse(BaseModel):
    id: str
    global_code: str
    global_name: str
    description: str | None = None
    category_code: str | None = None
    connector_type_codes: list[str]
    publish_status: str
    is_featured: bool
    download_count: int
    version_number: int
    signal_count: int = 0
    threat_type_count: int = 0
    policy_count: int = 0
    published_at: str | None = None
    created_at: str
    updated_at: str


class GlobalLibraryListResponse(BaseModel):
    items: list[GlobalLibraryResponse]
    total: int
    page: int
    page_size: int


class SubscriptionResponse(BaseModel):
    id: str
    org_id: str
    global_library_id: str
    global_code: str
    global_name: str
    subscribed_version: int
    latest_version: int
    has_update: bool
    local_library_id: str | None = None
    auto_update: bool
    subscribed_at: str


class SubscriptionListResponse(BaseModel):
    items: list[SubscriptionResponse]
