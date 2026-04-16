from __future__ import annotations

from pydantic import BaseModel


class DeployFrameworkRequest(BaseModel):
    framework_id: str
    version_id: str
    workspace_id: str | None = None


class UpdateDeploymentRequest(BaseModel):
    version_id: str | None = None
    deployment_status: str | None = None  # active | paused | removed


class FrameworkDeploymentResponse(BaseModel):
    id: str
    tenant_key: str
    org_id: str
    framework_id: str
    deployed_version_id: str
    deployment_status: str
    workspace_id: str | None = None
    is_active: bool
    created_at: str
    updated_at: str
    created_by: str | None = None
    framework_code: str | None = None
    framework_name: str | None = None
    framework_description: str | None = None
    publisher_name: str | None = None
    logo_url: str | None = None
    approval_status: str | None = None
    is_marketplace_visible: bool = False
    deployed_version_code: str | None = None
    deployed_lifecycle_state: str | None = None
    latest_version_id: str | None = None
    latest_version_code: str | None = None
    has_update: bool = False
    source_framework_id: str | None = None
    source_version_id: str | None = None
    latest_release_notes: str | None = None
    latest_change_severity: str | None = None
    latest_change_summary: str | None = None


class FrameworkDeploymentListResponse(BaseModel):
    items: list[FrameworkDeploymentResponse]
    total: int
