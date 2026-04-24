"""Reporting routes — /v1/somaerp/reports/*.

All endpoints are read-only and return the standard JSON envelope, except
/compliance/batches?format=csv which returns a raw text/csv body.
"""

from __future__ import annotations

import json
from datetime import date, datetime
from decimal import Decimal
from importlib import import_module
from typing import Any

from fastapi import APIRouter, Query, Request, Response

_service = import_module(
    "apps.somaerp.backend.02_features.99_reports.service",
)
_schemas = import_module(
    "apps.somaerp.backend.02_features.99_reports.schemas",
)
_response = import_module("apps.somaerp.backend.01_core.response")
_errors = import_module("apps.somaerp.backend.01_core.errors")


router = APIRouter(
    prefix="/v1/somaerp/reports",
    tags=["reports"],
)


def _require_workspace(request: Request) -> str:
    ws = getattr(request.state, "workspace_id", None)
    if not ws:
        raise _errors.AuthError("Authentication required (no workspace_id).")
    return ws


def _parse_date(val: str | None) -> date | None:
    if val is None or val == "":
        return None
    try:
        return date.fromisoformat(val)
    except ValueError as e:
        raise _errors.ValidationError(
            f"Invalid ISO date: {val}", code="INVALID_DATE",
        ) from e


# ── Dashboard ────────────────────────────────────────────────────────────


@router.get("/dashboard/today")
async def get_dashboard_today(
    request: Request,
    date_param: str | None = Query(default=None, alias="date"),
) -> dict:
    workspace_id = _require_workspace(request)
    as_of = _parse_date(date_param)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        row = await _service.select_dashboard_today(
            conn, tenant_id=workspace_id, as_of_date=as_of,
        )
    return _response.ok(
        _schemas.DashboardTodayOut(**row).model_dump(mode="json"),
    )


# ── Yield trends ─────────────────────────────────────────────────────────


@router.get("/yield/trends")
async def list_yield_trends(
    request: Request,
    from_date: str = Query(alias="from"),
    to_date: str = Query(alias="to"),
    kitchen_id: str | None = Query(default=None),
    product_id: str | None = Query(default=None),
    bucket: str = Query(default="daily"),
) -> dict:
    workspace_id = _require_workspace(request)
    if bucket not in ("daily", "weekly", "monthly"):
        raise _errors.ValidationError(
            f"Invalid bucket: {bucket}", code="INVALID_BUCKET",
        )
    f_date = _parse_date(from_date)
    t_date = _parse_date(to_date)
    if f_date is None or t_date is None:
        raise _errors.ValidationError(
            "`from` and `to` are required.", code="MISSING_DATE_RANGE",
        )
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        rows = await _service.list_yield_trends(
            conn,
            tenant_id=workspace_id,
            from_date=f_date,
            to_date=t_date,
            kitchen_id=kitchen_id,
            product_id=product_id,
            bucket=bucket,
        )
    data = [
        _schemas.YieldTrendPoint(**r).model_dump(mode="json") for r in rows
    ]
    return _response.ok(data)


# ── COGS trends ──────────────────────────────────────────────────────────


@router.get("/cogs/trends")
async def list_cogs_trends(
    request: Request,
    from_date: str = Query(alias="from"),
    to_date: str = Query(alias="to"),
    kitchen_id: str | None = Query(default=None),
    product_id: str | None = Query(default=None),
    bucket: str = Query(default="daily"),
) -> dict:
    workspace_id = _require_workspace(request)
    if bucket not in ("daily", "weekly", "monthly"):
        raise _errors.ValidationError(
            f"Invalid bucket: {bucket}", code="INVALID_BUCKET",
        )
    f_date = _parse_date(from_date)
    t_date = _parse_date(to_date)
    if f_date is None or t_date is None:
        raise _errors.ValidationError(
            "`from` and `to` are required.", code="MISSING_DATE_RANGE",
        )
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        rows = await _service.list_cogs_trends(
            conn,
            tenant_id=workspace_id,
            from_date=f_date,
            to_date=t_date,
            kitchen_id=kitchen_id,
            product_id=product_id,
            bucket=bucket,
        )
    data = [
        _schemas.CogsTrendPoint(**r).model_dump(mode="json") for r in rows
    ]
    return _response.ok(data)


# ── Inventory alerts ─────────────────────────────────────────────────────


@router.get("/inventory/alerts")
async def list_inventory_alerts(
    request: Request,
    kitchen_id: str | None = Query(default=None),
    severity: str = Query(default="all"),
) -> dict:
    workspace_id = _require_workspace(request)
    if severity not in ("critical", "low", "all"):
        raise _errors.ValidationError(
            f"Invalid severity: {severity}", code="INVALID_SEVERITY",
        )
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        rows = await _service.list_inventory_alerts(
            conn,
            tenant_id=workspace_id,
            kitchen_id=kitchen_id,
            severity=severity,
        )
    data = [
        _schemas.InventoryAlertOut(**r).model_dump(mode="json") for r in rows
    ]
    return _response.ok(data)


# ── Procurement spend ────────────────────────────────────────────────────


@router.get("/procurement/spend")
async def list_procurement_spend(
    request: Request,
    from_date: str = Query(alias="from"),
    to_date: str = Query(alias="to"),
    kitchen_id: str | None = Query(default=None),
    supplier_id: str | None = Query(default=None),
    bucket: str = Query(default="monthly"),
) -> dict:
    workspace_id = _require_workspace(request)
    if bucket != "monthly":
        raise _errors.ValidationError(
            "Only bucket=monthly supported in v0.",
            code="UNSUPPORTED_BUCKET",
        )
    f_date = _parse_date(from_date)
    t_date = _parse_date(to_date)
    if f_date is None or t_date is None:
        raise _errors.ValidationError(
            "`from` and `to` are required.", code="MISSING_DATE_RANGE",
        )
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        rows = await _service.list_procurement_spend(
            conn,
            tenant_id=workspace_id,
            from_date=f_date,
            to_date=t_date,
            kitchen_id=kitchen_id,
            supplier_id=supplier_id,
        )
    data = [
        _schemas.ProcurementSpendPoint(**r).model_dump(mode="json") for r in rows
    ]
    return _response.ok(data)


# ── Revenue projection ───────────────────────────────────────────────────


@router.get("/revenue/projection")
async def list_revenue_projection(
    request: Request,
    status: str | None = Query(default="active"),
    as_of: str | None = Query(default=None),
) -> dict:
    workspace_id = _require_workspace(request)
    as_of_date = _parse_date(as_of)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        rows = await _service.list_revenue_projection(
            conn,
            tenant_id=workspace_id,
            status=status,
            as_of_date=as_of_date,
        )
    data = [
        _schemas.RevenueProjection(**r).model_dump(mode="json") for r in rows
    ]
    return _response.ok(data)


# ── Compliance ───────────────────────────────────────────────────────────


def _normalize_qc_results(val: Any) -> list[dict]:
    if val is None:
        return []
    if isinstance(val, list):
        return val
    if isinstance(val, str):
        try:
            parsed = json.loads(val)
        except json.JSONDecodeError:
            return []
        return parsed if isinstance(parsed, list) else []
    return []


@router.get("/compliance/batches")
async def list_compliance_batches(
    request: Request,
    from_date: str = Query(alias="from"),
    to_date: str = Query(alias="to"),
    product_id: str | None = Query(default=None),
    fmt: str = Query(default="json", alias="format"),
) -> Any:
    workspace_id = _require_workspace(request)
    if fmt not in ("json", "csv"):
        raise _errors.ValidationError(
            f"Invalid format: {fmt}", code="INVALID_FORMAT",
        )
    f_date = _parse_date(from_date)
    t_date = _parse_date(to_date)
    if f_date is None or t_date is None:
        raise _errors.ValidationError(
            "`from` and `to` are required.", code="MISSING_DATE_RANGE",
        )
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        rows = await _service.list_compliance_batches(
            conn,
            tenant_id=workspace_id,
            from_date=f_date,
            to_date=t_date,
            product_id=product_id,
        )

    # Normalize qc_results which arrive as JSONB (asyncpg returns them as
    # strings unless a codec is set).
    normalized: list[dict] = []
    for r in rows:
        out = dict(r)
        out["qc_results"] = _normalize_qc_results(out.get("qc_results"))
        out["lot_numbers"] = list(out.get("lot_numbers") or [])
        normalized.append(out)

    if fmt == "csv":
        csv_body = _service.compliance_rows_to_csv(normalized)
        filename = f"fssai-compliance-{f_date.isoformat()}-{t_date.isoformat()}.csv"
        return Response(
            content=csv_body,
            media_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
            },
        )

    data = [
        _schemas.ComplianceBatchRow(**r).model_dump(mode="json")
        for r in normalized
    ]
    return _response.ok(data)
