"""Reports service — delegates to repository analytics queries."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_repo = import_module("apps.somacrm.backend.02_features.55_reports.repository")


async def pipeline_summary(conn: Any, *, tenant_id: str) -> dict:
    return await _repo.pipeline_summary(conn, tenant_id=tenant_id)


async def lead_conversion(conn: Any, *, tenant_id: str) -> dict:
    return await _repo.lead_conversion(conn, tenant_id=tenant_id)


async def activity_summary(conn: Any, *, tenant_id: str) -> dict:
    return await _repo.activity_summary(conn, tenant_id=tenant_id)


async def contact_growth(conn: Any, *, tenant_id: str, weeks: int = 12) -> dict:
    return await _repo.contact_growth(conn, tenant_id=tenant_id, weeks=weeks)
