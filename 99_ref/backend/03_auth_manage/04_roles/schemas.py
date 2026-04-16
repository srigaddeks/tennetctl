from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RoleLevelResponse(BaseModel):
    id: str
    code: str
    name: str
    description: str
    sort_order: int


class RolePermissionResponse(BaseModel):
    id: str
    feature_permission_id: str
    feature_permission_code: str
    feature_flag_code: str
    permission_action_code: str
    permission_name: str


class RoleResponse(BaseModel):
    id: str
    code: str
    name: str
    description: str
    role_level_code: str
    tenant_key: str
    scope_org_id: str | None = None
    scope_workspace_id: str | None = None
    is_active: bool
    is_disabled: bool
    is_system: bool
    permissions: list[RolePermissionResponse] = []
    created_at: datetime
    updated_at: datetime


class RoleListResponse(BaseModel):
    levels: list[RoleLevelResponse]
    roles: list[RoleResponse]


class CreateRoleRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    code: str = Field(min_length=2, max_length=80, pattern=r"^[a-z0-9_]+$")
    name: str = Field(min_length=2, max_length=120)
    description: str = Field(min_length=1, max_length=500)
    role_level_code: str = Field(min_length=1, max_length=30)
    tenant_key: str = Field(default="default", min_length=1, max_length=100)
    scope_org_id: str | None = Field(default=None, max_length=36)
    scope_workspace_id: str | None = Field(default=None, max_length=36)


class UpdateRoleRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=2, max_length=120)
    description: str | None = Field(default=None, min_length=1, max_length=500)
    is_disabled: bool | None = None


class RoleGroupResponse(BaseModel):
    id: str
    code: str
    name: str
    role_level_code: str
    is_system: bool
    is_active: bool
    member_count: int = 0


class RoleGroupListResponse(BaseModel):
    groups: list[RoleGroupResponse]


class AssignPermissionRequest(BaseModel):
    feature_permission_id: str = Field(min_length=1, max_length=36)
