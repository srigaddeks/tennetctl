from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, Query, Request, status

from .dependencies import get_deployment_service
from .schemas import (
    DeployFrameworkRequest,
    FrameworkDeploymentListResponse,
    FrameworkDeploymentResponse,
    UpdateDeploymentRequest,
)
from .service import DeploymentService

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")
_grc_access_module = import_module("backend.03_auth_manage.18_grc_roles.access_check")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims
get_allowed_scope_ids = _grc_access_module.get_allowed_scope_ids

router = InstrumentedAPIRouter(prefix="/api/v1/fr", tags=["grc-deployments"])


@router.get("/deployments", response_model=FrameworkDeploymentListResponse)
async def list_deployments(
    request: Request,
    service: Annotated[DeploymentService, Depends(get_deployment_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
    workspace_id: str | None = Query(None),
    has_update: bool | None = Query(None),
) -> FrameworkDeploymentListResponse:
    """List framework deployments filtered by GRC access grants.

    Users with 'All Frameworks' access see everything.
    Users with specific framework grants only see those deployments.
    """
    result = await service.list_deployments(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        workspace_id=workspace_id,
        has_update=has_update,
    )
    # Apply GRC access grant filtering
    if result.items:
        async with request.app.state.database_pool.acquire() as conn:
            allowed = await get_allowed_scope_ids(
                conn, user_id=str(claims.subject), org_id=org_id, scope_type="framework",
            )
        if allowed is not None:
            result.items = [d for d in result.items if d.id in allowed]
            result.total = len(result.items)
    return result


@router.get("/deployments/{deployment_id}", response_model=FrameworkDeploymentResponse)
async def get_deployment(
    deployment_id: str,
    service: Annotated[DeploymentService, Depends(get_deployment_service)],
    claims=Depends(get_current_access_claims),
) -> FrameworkDeploymentResponse:
    return await service.get_deployment(user_id=claims.subject, deployment_id=deployment_id)


@router.post("/deployments", response_model=FrameworkDeploymentResponse, status_code=status.HTTP_201_CREATED)
async def deploy_framework(
    body: DeployFrameworkRequest,
    service: Annotated[DeploymentService, Depends(get_deployment_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
) -> FrameworkDeploymentResponse:
    """Deploy (install) a marketplace framework for an org."""
    return await service.deploy_framework(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        request=body,
    )


@router.patch("/deployments/{deployment_id}", response_model=FrameworkDeploymentResponse)
async def update_deployment(
    deployment_id: str,
    body: UpdateDeploymentRequest,
    service: Annotated[DeploymentService, Depends(get_deployment_service)],
    claims=Depends(get_current_access_claims),
) -> FrameworkDeploymentResponse:
    """Update deployment version (upgrade) or status."""
    return await service.update_deployment(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        deployment_id=deployment_id,
        request=body,
    )


@router.get("/deployments/{deployment_id}/controls")
async def list_deployment_controls(
    deployment_id: str,
    service: Annotated[DeploymentService, Depends(get_deployment_service)],
    claims=Depends(get_current_access_claims),
) -> dict:
    """List controls included in a deployment (from the version snapshot)."""
    return await service.list_deployment_controls(user_id=claims.subject, deployment_id=deployment_id)


@router.get("/deployments/{deployment_id}/upgrade-diff")
async def get_upgrade_diff(
    deployment_id: str,
    service: Annotated[DeploymentService, Depends(get_deployment_service)],
    claims=Depends(get_current_access_claims),
    new_version_id: str = Query(...),
) -> dict:
    """Get control diff between currently deployed version and a new version."""
    return await service.get_upgrade_diff(
        user_id=claims.subject,
        deployment_id=deployment_id,
        new_version_id=new_version_id,
    )


@router.delete("/deployments/{deployment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_deployment(
    deployment_id: str,
    service: Annotated[DeploymentService, Depends(get_deployment_service)],
    claims=Depends(get_current_access_claims),
) -> None:
    """Remove (uninstall) a framework deployment."""
    await service.remove_deployment(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        deployment_id=deployment_id,
    )
