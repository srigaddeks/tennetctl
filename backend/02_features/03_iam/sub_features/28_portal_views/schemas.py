"""iam.portal_views — Pydantic v2 schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class PortalViewOut(BaseModel):
    """Single portal view from 08_dim_portal_views."""

    id: int
    code: str
    label: str
    icon: str | None = None
    color: str | None = None
    default_route: str
    sort_order: int
    deprecated_at: datetime | None = None

    model_config = {"from_attributes": True}


class RoleViewAssignment(BaseModel):
    """A row in 46_lnk_role_views with view detail joined."""

    id: str
    role_id: str
    view_id: int
    org_id: str
    created_by: str
    created_at: datetime | None = None
    # Joined from dim
    code: str | None = None
    label: str | None = None
    icon: str | None = None
    color: str | None = None
    default_route: str | None = None
    sort_order: int | None = None

    model_config = {"from_attributes": True}


class AttachViewBody(BaseModel):
    """Request body for POST /v1/iam/roles/{role_id}/views."""

    view_id: int


class MyViewItem(BaseModel):
    """Single view item in /my-views response."""

    code: str
    label: str
    icon: str | None = None
    color: str | None = None
    default_route: str
    sort_order: int

    model_config = {"from_attributes": True}
