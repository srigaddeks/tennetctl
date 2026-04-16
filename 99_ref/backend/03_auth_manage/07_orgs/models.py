from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OrgTypeRecord:
    code: str
    name: str
    description: str | None


@dataclass(frozen=True)
class OrgRecord:
    id: str
    tenant_key: str
    org_type_code: str
    name: str
    slug: str
    description: str | None
    is_active: bool
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class OrgMemberRecord:
    id: str
    org_id: str
    user_id: str
    role: str
    is_active: bool
    joined_at: str
    email: str | None = None
    display_name: str | None = None
