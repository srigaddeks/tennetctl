from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FrameworkRecord:
    id: str
    tenant_key: str
    framework_code: str
    framework_type_code: str
    framework_category_code: str
    scope_org_id: str | None
    scope_workspace_id: str | None
    approval_status: str
    is_marketplace_visible: bool
    is_active: bool
    created_at: str
    updated_at: str
    created_by: str | None


@dataclass(frozen=True)
class FrameworkCatalogRecord:
    id: str
    tenant_key: str
    framework_code: str
    framework_type_code: str
    type_name: str | None
    framework_category_code: str
    category_name: str | None
    scope_org_id: str | None
    scope_workspace_id: str | None
    approval_status: str
    is_marketplace_visible: bool
    is_active: bool
    created_at: str
    updated_at: str
    created_by: str | None
    name: str | None
    description: str | None
    short_description: str | None
    publisher_type: str | None
    publisher_name: str | None
    logo_url: str | None
    documentation_url: str | None
    latest_version_code: str | None
    control_count: int
    working_control_count: int = 0
    has_pending_changes: bool = False
