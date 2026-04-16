from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class GroupMemberResponse(BaseModel):
    id: str
    user_id: str
    membership_status: str
    effective_from: datetime
    effective_to: datetime | None
    email: str | None = None
    display_name: str | None = None
    scope_org_id: str | None = None
    scope_org_name: str | None = None
    scope_workspace_id: str | None = None
    scope_workspace_name: str | None = None


class GroupRoleResponse(BaseModel):
    id: str
    role_id: str
    role_code: str
    role_name: str
    role_level_code: str
    assignment_status: str


class GroupResponse(BaseModel):
    id: str
    code: str
    name: str
    description: str
    role_level_code: str
    tenant_key: str
    parent_group_id: str | None
    scope_org_id: str | None
    scope_workspace_id: str | None
    is_active: bool
    is_system: bool
    is_locked: bool = False
    members: list[GroupMemberResponse] = []
    roles: list[GroupRoleResponse] = []
    member_count: int = 0
    created_at: datetime
    updated_at: datetime


class GroupListResponse(BaseModel):
    groups: list[GroupResponse]


class GroupMemberListResponse(BaseModel):
    members: list[GroupMemberResponse]
    total: int
    limit: int
    offset: int


class GroupChildListResponse(BaseModel):
    children: list[GroupResponse]
    total: int
    limit: int
    offset: int


class CreateGroupRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    code: str = Field(min_length=2, max_length=80, pattern=r"^[a-z0-9_]+$")
    name: str = Field(min_length=2, max_length=120)
    description: str = Field(min_length=1, max_length=500)
    role_level_code: str = Field(min_length=1, max_length=30)
    tenant_key: str = Field(default="default", min_length=1, max_length=100)
    parent_group_id: str | None = Field(default=None, max_length=36)
    scope_org_id: str | None = Field(default=None, max_length=36)


class UpdateGroupRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=2, max_length=120)
    description: str | None = Field(default=None, min_length=1, max_length=500)
    parent_group_id: str | None = Field(default=None, max_length=36)
    is_disabled: bool | None = Field(default=None)


class SetParentGroupRequest(BaseModel):
    parent_group_id: str | None = Field(default=None, max_length=36)


class AddMemberRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=36)


class AssignGroupRoleRequest(BaseModel):
    role_id: str = Field(min_length=1, max_length=36)
