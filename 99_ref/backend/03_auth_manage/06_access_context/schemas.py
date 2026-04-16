from __future__ import annotations

from pydantic import BaseModel


class AccessActionResponse(BaseModel):
    feature_code: str
    feature_name: str
    action_code: str
    category_code: str
    access_mode: str
    env_dev: bool
    env_staging: bool
    env_prod: bool


class PlatformContextResponse(BaseModel):
    actions: list[AccessActionResponse]


class OrgContextResponse(BaseModel):
    org_id: str
    name: str
    slug: str
    org_type_code: str
    actions: list[AccessActionResponse]


class WorkspaceContextResponse(BaseModel):
    workspace_id: str
    org_id: str
    name: str
    slug: str
    workspace_type_code: str
    product_id: str | None = None
    product_name: str | None = None
    product_code: str | None = None
    grc_role_code: str | None = None
    actions: list[AccessActionResponse]
    product_actions: list[AccessActionResponse] = []


class AccessContextResponse(BaseModel):
    user_id: str
    tenant_key: str
    platform: PlatformContextResponse
    current_org: OrgContextResponse | None = None
    current_workspace: WorkspaceContextResponse | None = None
