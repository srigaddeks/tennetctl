from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WorkspaceTypeRecord:
    code: str
    name: str
    description: str | None
    is_infrastructure_type: bool


@dataclass(frozen=True)
class WorkspaceRecord:
    id: str
    org_id: str
    workspace_type_code: str
    product_id: str | None
    name: str
    slug: str
    description: str | None
    is_active: bool
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class WorkspaceMemberRecord:
    id: str
    workspace_id: str
    user_id: str
    role: str
    is_active: bool
    joined_at: str
    email: str | None = None
    display_name: str | None = None
    grc_role_code: str | None = None
