"""Reporting service — read-only pass-throughs to repository.

Audit emission is intentionally skipped on read endpoints to avoid audit
noise. This follows the read-path precedent set by vault.
"""

from __future__ import annotations

import csv
import io
import json
from datetime import date
from decimal import Decimal
from importlib import import_module
from typing import Any

_repo = import_module(
    "apps.somaerp.backend.02_features.99_reports.repository",
)


async def select_dashboard_today(
    conn: Any, *, tenant_id: str, as_of_date: date | None = None,
) -> dict:
    return await _repo.select_dashboard_today(
        conn, tenant_id=tenant_id, as_of_date=as_of_date,
    )


async def list_yield_trends(conn: Any, **kwargs: Any) -> list[dict]:
    return await _repo.list_yield_trends(conn, **kwargs)


async def list_cogs_trends(conn: Any, **kwargs: Any) -> list[dict]:
    return await _repo.list_cogs_trends(conn, **kwargs)


async def list_inventory_alerts(conn: Any, **kwargs: Any) -> list[dict]:
    return await _repo.list_inventory_alerts(conn, **kwargs)


async def list_procurement_spend(conn: Any, **kwargs: Any) -> list[dict]:
    return await _repo.list_procurement_spend(conn, **kwargs)


async def list_revenue_projection(conn: Any, **kwargs: Any) -> list[dict]:
    return await _repo.list_revenue_projection(conn, **kwargs)


async def list_compliance_batches(conn: Any, **kwargs: Any) -> list[dict]:
    return await _repo.list_compliance_batches(conn, **kwargs)


# ── CSV export ───────────────────────────────────────────────────────────


def _stringify(val: Any) -> str:
    if val is None:
        return ""
    if isinstance(val, (list, dict)):
        return json.dumps(val, default=str, separators=(",", ":"))
    if isinstance(val, Decimal):
        return str(val)
    if isinstance(val, date):
        return val.isoformat()
    return str(val)


def compliance_rows_to_csv(rows: list[dict]) -> str:
    """Serialize compliance rows to FSSAI-friendly CSV."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "batch_id",
        "run_date",
        "kitchen_name",
        "product_name",
        "recipe_version",
        "planned_qty",
        "actual_qty",
        "completed_by",
        "lot_numbers",
        "qc_results",
    ])
    for r in rows:
        writer.writerow([
            _stringify(r.get("batch_id")),
            _stringify(r.get("run_date")),
            _stringify(r.get("kitchen_name")),
            _stringify(r.get("product_name")),
            _stringify(r.get("recipe_version")),
            _stringify(r.get("planned_qty")),
            _stringify(r.get("actual_qty")),
            _stringify(r.get("completed_by")),
            _stringify(r.get("lot_numbers")),
            _stringify(r.get("qc_results")),
        ])
    return buf.getvalue()
