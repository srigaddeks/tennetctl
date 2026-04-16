from __future__ import annotations

from pydantic import BaseModel, Field


class CreateOrgRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    slug: str = Field(..., pattern=r"^[a-z0-9][a-z0-9\-]{1,60}[a-z0-9]$")
    org_type_code: str = Field(..., min_length=1, max_length=50)
    description: str | None = None


class UpdateOrgRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=120)
    description: str | None = None
    is_disabled: bool | None = None


class AddOrgMemberRequest(BaseModel):
    user_id: str
    role: str = Field(default="member", pattern=r"^(owner|admin|member|viewer|billing)$")


class UpdateOrgMemberRequest(BaseModel):
    role: str = Field(..., pattern=r"^(owner|admin|member|viewer|billing)$")


class OrgTypeResponse(BaseModel):
    code: str
    name: str
    description: str | None = None


class OrgMemberResponse(BaseModel):
    id: str
    org_id: str
    user_id: str
    role: str
    is_active: bool
    joined_at: str
    email: str | None = None
    display_name: str | None = None


class OrgResponse(BaseModel):
    id: str
    tenant_key: str
    org_type_code: str
    name: str
    slug: str
    description: str | None = None
    is_active: bool
    created_at: str
    updated_at: str


class OrgListResponse(BaseModel):
    items: list[OrgResponse]
    total: int
