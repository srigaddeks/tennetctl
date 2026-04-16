from __future__ import annotations

from pydantic import BaseModel, Field


class CreateLibraryRequest(BaseModel):
    library_code: str = Field(
        ..., min_length=2, max_length=100, pattern=r"^[a-z0-9_]{2,100}$"
    )
    library_type_code: str = Field(..., min_length=1, max_length=50)
    properties: dict[str, str] | None = None


class UpdateLibraryRequest(BaseModel):
    library_type_code: str | None = Field(None, min_length=1, max_length=50)
    properties: dict[str, str] | None = None


class AddPolicyRequest(BaseModel):
    policy_id: str = Field(..., min_length=1)
    sort_order: int = Field(default=0, ge=0)


class AddConnectorTypeMappingRequest(BaseModel):
    connector_type_code: str = Field(..., min_length=1, max_length=50)
    asset_version_id: str | None = None
    is_recommended: bool = Field(default=False)


class LibraryResponse(BaseModel):
    id: str
    tenant_key: str
    org_id: str
    library_code: str
    library_type_code: str
    library_type_name: str | None = None
    version_number: int
    is_published: bool
    is_active: bool
    created_at: str
    updated_at: str
    name: str | None = None
    description: str | None = None
    policy_count: int = 0
    properties: dict[str, str] | None = None


class LibraryListResponse(BaseModel):
    items: list[LibraryResponse]
    total: int


class LibraryPolicyResponse(BaseModel):
    id: str
    library_id: str
    policy_id: str
    policy_code: str | None = None
    policy_name: str | None = None
    sort_order: int = 0


class RecommendedLibraryResponse(BaseModel):
    library_id: str
    library_code: str
    library_name: str | None = None
    library_type_code: str
    is_recommended: bool
    connector_type_code: str
    asset_version_code: str | None = None
