from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, Query

from .dependencies import get_access_context_service
from .schemas import AccessContextResponse
from .service import AccessContextService

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims

router = InstrumentedAPIRouter(prefix="/api/v1/am", tags=["access-management"])


@router.get("/access", response_model=AccessContextResponse)
async def get_access_context(
    service: Annotated[AccessContextService, Depends(get_access_context_service)],
    claims=Depends(get_current_access_claims),
    org_id: str | None = Query(default=None),
    workspace_id: str | None = Query(default=None),
) -> AccessContextResponse:
    return await service.resolve(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        workspace_id=workspace_id,
    )
