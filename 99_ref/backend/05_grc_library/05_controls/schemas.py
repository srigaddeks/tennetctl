from __future__ import annotations

from pydantic import BaseModel, Field


class CreateControlRequest(BaseModel):
    control_code: str = Field(..., min_length=1, max_length=100)
    control_category_code: str = Field(..., min_length=1, max_length=50)
    criticality_code: str = Field(default="medium", min_length=1, max_length=50)
    control_type: str = Field(default="preventive", pattern=r"^(preventive|detective|corrective|compensating)$")
    automation_potential: str = Field(default="manual", pattern=r"^(full|partial|manual)$")
    requirement_id: str | None = None
    sort_order: int = Field(default=0)
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    guidance: str | None = None
    implementation_notes: str | None = None
    # Rich properties — stored as EAV, JSON-encoded where needed
    implementation_guidance: list[str] | None = None  # bullet points, stored as JSON
    owner_user_id: str | None = None                  # control owner (user UUID)
    responsible_teams: list[str] | None = None         # group/team IDs, stored as JSON
    tags: list[str] | None = None                      # tag strings, stored as JSON
    properties: dict[str, str] | None = None           # additional arbitrary EAV


class UpdateControlRequest(BaseModel):
    control_category_code: str | None = Field(None, min_length=1, max_length=50)
    criticality_code: str | None = Field(None, min_length=1, max_length=50)
    control_type: str | None = Field(None, pattern=r"^(preventive|detective|corrective|compensating)$")
    automation_potential: str | None = Field(None, pattern=r"^(full|partial|manual)$")
    requirement_id: str | None = None
    sort_order: int | None = None
    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    guidance: str | None = None
    implementation_notes: str | None = None
    implementation_guidance: list[str] | None = None
    owner_user_id: str | None = None
    responsible_teams: list[str] | None = None
    tags: list[str] | None = None
    properties: dict[str, str] | None = None


class ControlResponse(BaseModel):
    id: str
    framework_id: str
    requirement_id: str | None = None
    tenant_key: str
    control_code: str
    control_category_code: str
    category_name: str | None = None
    criticality_code: str
    criticality_name: str | None = None
    control_type: str
    automation_potential: str
    sort_order: int
    version: int = 1
    is_active: bool
    created_at: str
    updated_at: str
    # EAV-flattened properties
    name: str | None = None
    description: str | None = None
    guidance: str | None = None
    implementation_notes: str | None = None
    implementation_guidance: list[str] | None = None
    owner_user_id: str | None = None
    owner_display_name: str | None = None
    owner_email: str | None = None
    responsible_teams: list[str] | None = None
    tags: list[str] | None = None
    # Framework/requirement context
    framework_code: str | None = None
    framework_name: str | None = None
    requirement_code: str | None = None
    requirement_name: str | None = None
    test_count: int = 0
    # All raw EAV properties (for extensibility)
    properties: dict[str, str] | None = None


class ControlListResponse(BaseModel):
    items: list[ControlResponse]
    total: int


class ImportControlError(BaseModel):
    row: int
    key: str | None = None
    field: str | None = None
    message: str


class ImportControlsResult(BaseModel):
    created: int
    updated: int
    skipped: int = 0
    warnings: list[str] = []
    errors: list[ImportControlError] = []
    dry_run: bool = False
