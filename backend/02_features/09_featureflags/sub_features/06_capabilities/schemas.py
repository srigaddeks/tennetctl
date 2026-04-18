"""Schemas for the capabilities API — unified flag + permission catalog."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class PermissionAction(BaseModel):
    id: int
    code: str
    label: str
    description: str | None
    sort_order: int


class FeatureFlagCategory(BaseModel):
    id: int
    code: str
    label: str
    description: str | None
    sort_order: int


class FeaturePermission(BaseModel):
    id: int
    code: str
    flag_id: int
    flag_code: str
    action_id: int
    action_code: str
    name: str
    description: str | None


class Capability(BaseModel):
    """A feature flag as a capability — with its permissions and rollout state."""
    id: int
    code: str
    name: str
    description: str | None
    category_id: int
    category_code: str
    feature_scope: str
    access_mode: str
    lifecycle_state: str
    env_dev: bool
    env_staging: bool
    env_prod: bool
    rollout_mode: str
    required_license: str | None
    permissions: list[FeaturePermission]


class CapabilityCatalog(BaseModel):
    categories: list[FeatureFlagCategory]
    actions: list[PermissionAction]
    capabilities: list[Capability]


class RoleGrant(BaseModel):
    id: str
    role_id: str
    feature_permission_id: int
    permission_code: str
    flag_code: str
    action_code: str
    created_at: str


class RoleGrants(BaseModel):
    role_id: str
    role_code: str | None
    grants: list[RoleGrant]


class GrantRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    permission_codes: list[str] = Field(min_length=1)
