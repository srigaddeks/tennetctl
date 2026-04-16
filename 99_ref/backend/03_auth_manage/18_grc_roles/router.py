"""FastAPI router for GRC role management endpoints."""
from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, Query, Request, status

from .dependencies import get_grc_role_service
from .schemas import (
    AssignGrcRoleRequest,
    CreateAccessGrantRequest,
    GrcAccessGrantListResponse,
    GrcAccessGrantResponse,
    GrcRoleAssignmentListResponse,
    GrcRoleAssignmentResponse,
    GrcTeamResponse,
)
from .service import GrcRoleService

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims

router = InstrumentedAPIRouter(
    prefix="/api/v1/am/orgs/{org_id}/grc-roles",
    tags=["grc-role-management"],
)


# ── Role assignments ───────────────────────────────────────────────────────────


@router.get("", response_model=GrcRoleAssignmentListResponse)
async def list_grc_role_assignments(
    org_id: str,
    service: Annotated[GrcRoleService, Depends(get_grc_role_service)],
    claims=Depends(get_current_access_claims),
    grc_role_code: str | None = Query(default=None, description="Filter by GRC role code"),
    user_id: str | None = Query(default=None, description="Filter by user ID"),
) -> GrcRoleAssignmentListResponse:
    """List GRC role assignments for an org.

    Returns all active org-level GRC role assignments with optional filters.
    """
    return await service.list_assignments(
        actor_id=claims.subject,
        org_id=org_id,
        grc_role_code=grc_role_code,
        user_id=user_id,
    )


@router.post("", status_code=status.HTTP_201_CREATED, response_model=GrcRoleAssignmentResponse)
async def assign_grc_role(
    org_id: str,
    payload: AssignGrcRoleRequest,
    service: Annotated[GrcRoleService, Depends(get_grc_role_service)],
    claims=Depends(get_current_access_claims),
) -> GrcRoleAssignmentResponse:
    """Assign an org-level GRC role to a user.

    Idempotent: returns existing assignment if already active.
    """
    return await service.assign_role(
        actor_id=claims.subject,
        org_id=org_id,
        body=payload,
    )


@router.delete("/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_grc_role(
    org_id: str,
    assignment_id: str,
    service: Annotated[GrcRoleService, Depends(get_grc_role_service)],
    claims=Depends(get_current_access_claims),
) -> None:
    """Revoke a GRC role assignment and all its access grants."""
    await service.revoke_role(
        actor_id=claims.subject,
        org_id=org_id,
        assignment_id=assignment_id,
    )


# ── Access grants ──────────────────────────────────────────────────────────────


@router.get("/{assignment_id}/grants", response_model=GrcAccessGrantListResponse)
async def list_access_grants(
    org_id: str,
    assignment_id: str,
    service: Annotated[GrcRoleService, Depends(get_grc_role_service)],
    claims=Depends(get_current_access_claims),
) -> GrcAccessGrantListResponse:
    """List access grants for a GRC role assignment."""
    return await service.list_grants(
        actor_id=claims.subject,
        org_id=org_id,
        assignment_id=assignment_id,
    )


@router.post(
    "/{assignment_id}/grants",
    status_code=status.HTTP_201_CREATED,
    response_model=GrcAccessGrantResponse,
)
async def create_access_grant(
    org_id: str,
    assignment_id: str,
    payload: CreateAccessGrantRequest,
    service: Annotated[GrcRoleService, Depends(get_grc_role_service)],
    claims=Depends(get_current_access_claims),
) -> GrcAccessGrantResponse:
    """Grant scope access (workspace/framework/engagement) to a role assignment.

    Idempotent: returns existing grant if already active.
    """
    return await service.create_grant(
        actor_id=claims.subject,
        org_id=org_id,
        assignment_id=assignment_id,
        body=payload,
    )


@router.delete(
    "/{assignment_id}/grants/{grant_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def revoke_access_grant(
    org_id: str,
    assignment_id: str,
    grant_id: str,
    service: Annotated[GrcRoleService, Depends(get_grc_role_service)],
    claims=Depends(get_current_access_claims),
) -> None:
    """Revoke an access grant."""
    await service.revoke_grant(
        actor_id=claims.subject,
        org_id=org_id,
        assignment_id=assignment_id,
        grant_id=grant_id,
    )


# ── Team view ──────────────────────────────────────────────────────────────────


@router.get("/team", response_model=GrcTeamResponse)
async def get_grc_team(
    org_id: str,
    service: Annotated[GrcRoleService, Depends(get_grc_role_service)],
    claims=Depends(get_current_access_claims),
    workspace_id: str | None = Query(default=None, description="Filter by workspace"),
    engagement_id: str | None = Query(default=None, description="Filter by engagement"),
) -> GrcTeamResponse:
    """Get the full GRC team for an org, grouped by role category.

    When workspace_id or engagement_id is provided, shows only team members
    with access to that scope (plus org-wide members).
    """
    return await service.get_team(
        actor_id=claims.subject,
        org_id=org_id,
        workspace_id=workspace_id,
        engagement_id=engagement_id,
    )
