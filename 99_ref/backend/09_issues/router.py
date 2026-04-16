from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, Query, Request

from .schemas import IssueListResponse, IssueResponse, IssueStatsResponse, UpdateIssueRequest
from .service import IssueService

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims

router = InstrumentedAPIRouter(prefix="/api/v1/issues", tags=["issues"])


def _get_service(request: Request) -> IssueService:
    return IssueService(database_pool=request.app.state.database_pool)


@router.get("", response_model=IssueListResponse)
async def list_issues(
    request: Request,
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
    status_code: str | None = Query(None),
    severity_code: str | None = Query(None),
    connector_id: str | None = Query(None),
    search: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    service = _get_service(request)
    return await service.list_issues(
        org_id=org_id, status_code=status_code, severity_code=severity_code,
        connector_id=connector_id, search=search, limit=limit, offset=offset,
    )


@router.get("/stats", response_model=IssueStatsResponse)
async def get_issue_stats(
    request: Request,
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
):
    service = _get_service(request)
    return await service.get_stats(org_id)


@router.get("/{issue_id}", response_model=IssueResponse)
async def get_issue(
    issue_id: str,
    request: Request,
    claims=Depends(get_current_access_claims),
):
    service = _get_service(request)
    return await service.get_issue(issue_id)


@router.patch("/{issue_id}", response_model=IssueResponse)
async def update_issue(
    issue_id: str,
    body: UpdateIssueRequest,
    request: Request,
    claims=Depends(get_current_access_claims),
):
    service = _get_service(request)
    return await service.update_issue(issue_id, body, claims.subject)
