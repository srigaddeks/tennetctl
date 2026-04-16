from __future__ import annotations

from pydantic import BaseModel, Field


class CreateVersionRequest(BaseModel):
    # version_code is auto-generated server-side as the next sequential integer
    change_severity: str = Field(default="minor", pattern=r"^(breaking|major|minor|patch)$")
    source_version_id: str | None = None
    version_label: str | None = None
    release_notes: str | None = None
    change_summary: str | None = None


class VersionResponse(BaseModel):
    id: str
    framework_id: str
    version_code: str
    change_severity: str
    lifecycle_state: str
    control_count: int
    previous_version_id: str | None = None
    is_active: bool
    created_at: str
    updated_at: str
    created_by: str | None = None
    version_label: str | None = None
    release_notes: str | None = None
    change_summary: str | None = None


class VersionListResponse(BaseModel):
    items: list[VersionResponse]
    total: int
