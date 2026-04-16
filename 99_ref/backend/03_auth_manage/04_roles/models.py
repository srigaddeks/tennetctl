from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class RoleLevelRecord:
    id: str
    code: str
    name: str
    description: str
    sort_order: int


@dataclass(frozen=True, slots=True)
class RoleRecord:
    id: str
    code: str
    name: str
    description: str
    role_level_code: str
    tenant_key: str
    scope_org_id: str | None
    scope_workspace_id: str | None
    is_active: bool
    is_disabled: bool
    is_system: bool
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class RolePermissionLinkRecord:
    id: str
    role_id: str
    feature_permission_id: str
    feature_permission_code: str
    feature_flag_code: str
    permission_action_code: str
    permission_name: str
