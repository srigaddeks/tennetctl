from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, Query, status

from .dependencies import get_live_test_service
from .schemas import LiveTestRequest, LiveTestResponse
from .service import LiveTestService

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims

router = InstrumentedAPIRouter(prefix="/api/v1/sb/live-test", tags=["sandbox-live-test"])


@router.post("", response_model=LiveTestResponse, status_code=status.HTTP_200_OK)
async def run_live_test(
    body: LiveTestRequest,
    service: Annotated[LiveTestService, Depends(get_live_test_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
    workspace_id: str = Query(...),
) -> LiveTestResponse:
    """Collect the latest assets from a connector and run selected signals against each one."""
    return await service.run_live_test(
        user_id=claims.subject,
        org_id=org_id,
        workspace_id=workspace_id,
        connector_id=body.connector_id,
        signal_ids=body.signal_ids,
    )
