from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class FeatureCategoryResponse(BaseModel):
    id: str
    code: str
    name: str
    description: str
    sort_order: int


class FeaturePermissionResponse(BaseModel):
    id: str
    code: str
    feature_flag_code: str
    permission_action_code: str
    name: str
    description: str


class FeatureFlagResponse(BaseModel):
    id: str
    code: str
    name: str
    description: str
    category_code: str
    feature_scope: str
    access_mode: str
    lifecycle_state: str
    initial_audience: str
    env_dev: bool
    env_staging: bool
    env_prod: bool
    org_visibility: str | None = None  # "hidden" | "locked" | "unlocked" — only populated for org-scoped flags
    required_license: str | None = None  # "free" | "pro" | "internal" — only populated if set
    permissions: list[FeaturePermissionResponse] = []
    created_at: datetime
    updated_at: datetime


class PermissionActionResponse(BaseModel):
    id: str
    code: str
    name: str
    description: str
    sort_order: int


class PermissionActionListResponse(BaseModel):
    actions: list[PermissionActionResponse]


class FeatureFlagListResponse(BaseModel):
    categories: list[FeatureCategoryResponse]
    flags: list[FeatureFlagResponse]


class OrgAvailableFlagResponse(BaseModel):
    """A flag visible to org admins, with its org_visibility pre-resolved."""
    id: str
    code: str
    name: str
    description: str
    category_code: str
    feature_scope: str
    lifecycle_state: str
    env_dev: bool
    env_staging: bool
    env_prod: bool
    org_visibility: str  # "locked" | "unlocked"
    required_license: str | None = None  # "free" | "pro" | "internal"
    permissions: list[FeaturePermissionResponse] = []


class OrgAvailableFlagsResponse(BaseModel):
    categories: list[FeatureCategoryResponse]
    flags: list[OrgAvailableFlagResponse]


class PermissionActionTypeResponse(BaseModel):
    code: str
    name: str
    description: str
    sort_order: int


class AddPermissionRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    action_code: str = Field(min_length=1, max_length=50, pattern=r"^[a-z_]+$")


class CreateFeatureCategoryRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    code: str = Field(min_length=2, max_length=50, pattern=r"^[a-z0-9_]+$")
    name: str = Field(min_length=2, max_length=100)
    description: str = Field(default="", max_length=500)
    sort_order: int = Field(default=100, ge=0)


class CreateFeaturePermissionRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    permission_action_code: str = Field(min_length=1, max_length=30)
    name: str = Field(min_length=2, max_length=120)
    description: str = Field(min_length=1, max_length=500)


class CreateFeatureFlagRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    code: str = Field(min_length=2, max_length=80, pattern=r"^[a-z0-9_]+$")
    name: str = Field(min_length=2, max_length=120)
    description: str = Field(min_length=1, max_length=500)
    category_code: str = Field(min_length=1, max_length=50)
    feature_scope: str = Field(default="platform", pattern=r"^(platform|org|product)$")
    access_mode: str = Field(pattern=r"^(public|authenticated|permissioned)$")
    lifecycle_state: str = Field(default="planned", pattern=r"^(planned|active|deprecated|retired)$")
    initial_audience: str = Field(default="platform_super_admin", max_length=60)
    env_dev: bool = False
    env_staging: bool = False
    env_prod: bool = False
    permissions: list[str] = Field(
        default_factory=list,
        description="Action codes to seed as permissions on creation (e.g. ['view','create','update'])",
    )


class UpdateFeatureFlagRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=2, max_length=120)
    description: str | None = Field(default=None, min_length=1, max_length=500)
    category_code: str | None = Field(default=None, min_length=1, max_length=50)
    feature_scope: str | None = Field(default=None, pattern=r"^(platform|org|product)$")
    access_mode: str | None = Field(default=None, pattern=r"^(public|authenticated|permissioned)$")
    lifecycle_state: str | None = Field(default=None, pattern=r"^(planned|active|deprecated|retired)$")
    env_dev: bool | None = None
    env_staging: bool | None = None
    env_prod: bool | None = None
    permissions: list[CreateFeaturePermissionRequest] | None = None
