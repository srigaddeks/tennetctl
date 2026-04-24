"""Reports routes — /v1/somacrm/reports/..."""

from __future__ import annotations

from importlib import import_module

from fastapi import APIRouter, Query, Request

_service = import_module("apps.somacrm.backend.02_features.55_reports.service")
_schemas = import_module("apps.somacrm.backend.02_features.55_reports.schemas")
_response = import_module("apps.somacrm.backend.01_core.response")
_errors = import_module("apps.somacrm.backend.01_core.errors")

router = APIRouter(prefix="/v1/somacrm/reports", tags=["reports"])


def _require_workspace(request: Request) -> str:
    ws = getattr(request.state, "workspace_id", None)
    if not ws:
        raise _errors.AuthError("Authentication required (no workspace_id).")
    return ws


@router.get("/pipeline-summary")
async def pipeline_summary(request: Request) -> dict:
    workspace_id = _require_workspace(request)
    async with request.app.state.pool.acquire() as conn:
        data = await _service.pipeline_summary(conn, tenant_id=workspace_id)
    out = _schemas.PipelineSummaryOut(
        stages=[_schemas.PipelineSummaryStage(**s) for s in data["stages"]],
        total_deals=data["total_deals"],
        total_value=data["total_value"],
    )
    return _response.ok(out.model_dump(mode="json"))


@router.get("/lead-conversion")
async def lead_conversion(request: Request) -> dict:
    workspace_id = _require_workspace(request)
    async with request.app.state.pool.acquire() as conn:
        data = await _service.lead_conversion(conn, tenant_id=workspace_id)
    out = _schemas.LeadConversionOut(
        by_status=[_schemas.LeadConversionRow(**r) for r in data["by_status"]],
        total_leads=data["total_leads"],
    )
    return _response.ok(out.model_dump(mode="json"))


@router.get("/activity-summary")
async def activity_summary(request: Request) -> dict:
    workspace_id = _require_workspace(request)
    async with request.app.state.pool.acquire() as conn:
        data = await _service.activity_summary(conn, tenant_id=workspace_id)
    out = _schemas.ActivitySummaryOut(
        rows=[_schemas.ActivitySummaryRow(**r) for r in data["rows"]],
        total=data["total"],
    )
    return _response.ok(out.model_dump(mode="json"))


@router.get("/contact-growth")
async def contact_growth(
    request: Request,
    weeks: int = Query(default=12, ge=1, le=52),
) -> dict:
    workspace_id = _require_workspace(request)
    async with request.app.state.pool.acquire() as conn:
        data = await _service.contact_growth(conn, tenant_id=workspace_id, weeks=weeks)
    out = _schemas.ContactGrowthOut(
        weeks=[_schemas.ContactGrowthRow(**r) for r in data["weeks"]],
    )
    return _response.ok(out.model_dump(mode="json"))
