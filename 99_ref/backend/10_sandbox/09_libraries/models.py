from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LibraryRecord:
    id: str
    tenant_key: str
    org_id: str
    library_code: str
    library_type_code: str
    library_type_name: str | None
    version_number: int
    is_published: bool
    is_active: bool
    created_at: str
    updated_at: str
    name: str | None
    description: str | None
    policy_count: int


@dataclass(frozen=True)
class LibraryPolicyRecord:
    id: str
    library_id: str
    policy_id: str
    policy_code: str | None
    policy_name: str | None
    sort_order: int


@dataclass(frozen=True)
class RecommendedLibraryRecord:
    library_id: str
    library_code: str
    library_name: str | None
    library_type_code: str
    is_recommended: bool
    connector_type_code: str
    asset_version_code: str | None
