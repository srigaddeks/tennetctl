from __future__ import annotations

from pydantic import BaseModel, Field


class CreateWorkspaceRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    slug: str = Field(..., pattern=r"^[a-z0-9][a-z0-9\-]{1,60}[a-z0-9]$")
    workspace_type_code: str = Field(..., min_length=1, max_length=50)
    product_id: str | None = None
    description: str | None = None


class UpdateWorkspaceRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=120)
    description: str | None = None
    product_id: str | None = None
    is_disabled: bool | None = None


class AddWorkspaceMemberRequest(BaseModel):
    user_id: str
    role: str = Field(default="contributor", pattern=r"^(owner|admin|contributor|viewer|readonly)$")


class UpdateWorkspaceMemberRequest(BaseModel):
    """Update a workspace member's GRC role assignment.

    Set grc_role_code to a valid GRC role code to assign the role, or None
    to remove the user from all GRC role groups.
    """

    grc_role_code: str | None = Field(
        default=None,
        description="GRC workspace role to assign. None removes all GRC role assignments.",
    )


class WorkspaceTypeResponse(BaseModel):
    code: str
    name: str
    description: str | None = None
    is_infrastructure_type: bool


class WorkspaceMemberResponse(BaseModel):
    id: str
    workspace_id: str
    user_id: str
    role: str
    is_active: bool
    joined_at: str
    email: str | None = None
    display_name: str | None = None
    grc_role_code: str | None = None


class WorkspaceResponse(BaseModel):
    id: str
    org_id: str
    workspace_type_code: str
    product_id: str | None = None
    name: str
    slug: str
    description: str | None = None
    is_active: bool
    created_at: str
    updated_at: str


class WorkspaceListResponse(BaseModel):
    items: list[WorkspaceResponse]
    total: int
