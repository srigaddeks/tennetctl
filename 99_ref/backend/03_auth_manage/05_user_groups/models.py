from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class GroupRecord:
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
    is_locked: bool
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class GroupMemberRecord:
    id: str
    group_id: str
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


@dataclass(frozen=True, slots=True)
class GroupRoleRecord:
    id: str
    group_id: str
    role_id: str
    role_code: str
    role_name: str
    role_level_code: str
    assignment_status: str
