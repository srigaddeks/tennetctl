from __future__ import annotations

from pydantic import BaseModel, Field


class CreateRequirementRequest(BaseModel):
    requirement_code: str = Field(..., min_length=1, max_length=100)
    sort_order: int = Field(default=0)
    parent_requirement_id: str | None = None
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None


class UpdateRequirementRequest(BaseModel):
    requirement_code: str | None = Field(None, min_length=1, max_length=100)
    sort_order: int | None = None
    parent_requirement_id: str | None = None
    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None


class RequirementResponse(BaseModel):
    id: str
    framework_id: str
    requirement_code: str
    sort_order: int
    parent_requirement_id: str | None = None
    is_active: bool
    created_at: str
    updated_at: str
    name: str | None = None
    description: str | None = None


class RequirementListResponse(BaseModel):
    items: list[RequirementResponse]
    total: int
