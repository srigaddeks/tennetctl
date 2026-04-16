from __future__ import annotations

from pydantic import BaseModel, Field


class PortalViewResponse(BaseModel):
    code: str
    name: str
    description: str | None = None
    color: str | None = None
    icon: str | None = None
    sort_order: int = 0
    is_active: bool = True
    default_route: str | None = None


class ViewRouteResponse(BaseModel):
    view_code: str
    route_prefix: str
    is_read_only: bool = False
    sort_order: int = 0
    sidebar_label: str | None = None
    sidebar_icon: str | None = None
    sidebar_section: str | None = None


class PortalViewDetailResponse(PortalViewResponse):
    routes: list[ViewRouteResponse] = []


class PortalViewListResponse(BaseModel):
    views: list[PortalViewDetailResponse]


class RoleViewAssignment(BaseModel):
    role_id: str
    view_code: str


class RoleViewListResponse(BaseModel):
    assignments: list[RoleViewAssignment]


class AssignViewToRoleRequest(BaseModel):
    view_code: str


class UserViewsResponse(BaseModel):
    """Views available to the current user (derived from role chain)."""
    views: list[PortalViewDetailResponse]


# ── CRUD request schemas ──────────────────────────────────────────────────────

class CreatePortalViewRequest(BaseModel):
    code: str = Field(..., pattern=r"^[a-z0-9_]+$", max_length=64)
    name: str = Field(..., max_length=128)
    description: str | None = None
    color: str | None = None          # hex e.g. "#2878ff"
    icon: str | None = None           # icon name string
    sort_order: int = 50
    default_route: str | None = "/dashboard"


class UpdatePortalViewRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    color: str | None = None
    icon: str | None = None
    sort_order: int | None = None
    is_active: bool | None = None
    default_route: str | None = None


class AddViewRouteRequest(BaseModel):
    route_prefix: str = Field(..., pattern=r"^/", max_length=256)
    is_read_only: bool = False
    sort_order: int = 0
    sidebar_label: str | None = None
    sidebar_icon: str | None = None
    sidebar_section: str | None = None
