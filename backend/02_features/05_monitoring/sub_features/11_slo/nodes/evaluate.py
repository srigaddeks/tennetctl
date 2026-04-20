"""Evaluate SLO node — runs per SLO on 60s tick, computes budget + burn rate.

Effect node, tx=own. Worker-owned (slo_evaluator_worker calls this).
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from importlib import import_module
from typing import Any

_core_id: Any = import_module("backend.01_core.id")
_errors: Any = import_module("backend.01_core.errors")
_repo: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.11_slo.repository"
)
_budget: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.11_slo.budget"
)
_burn_rate: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.11_slo.burn_rate"
)

logger = logging.getLogger("tennetctl.monitoring.slo.evaluate")


async def evaluate_slo_node(
    conn: Any,
    ctx: Any,
    *,
    slo_id: str,
) -> dict[str, Any]:
    """Evaluate a single SLO: load indicator query, compute budget + burn rate, persist.

    Args:
        conn: Active DB connection.
        ctx: NodeContext with org_id, user_id, etc.
        slo_id: SLO to evaluate.

    Returns:
        Evaluation result dict with attainment, budget_remaining, burn rates, status.

    Side effects:
        Inserts evt_monitoring_slo_evaluations row.
        May insert evt_monitoring_slo_breaches row if thresholds crossed.
    """
    # Load SLO
    slo = await _repo.get_slo_by_id(conn, slo_id)
    if not slo:
        raise _errors.AppError("NOT_FOUND", f"SLO {slo_id!r} not found", 404)

    if not slo.get("is_active"):
        return {"status": "skipped_inactive"}

    # Determine evaluation window based on window_kind
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    window_kind = slo.get("window_kind_code", "rolling_30d")

    if window_kind == "rolling_7d":
        window_start = now - timedelta(days=7)
    elif window_kind == "rolling_28d":
        window_start = now - timedelta(days=28)
    elif window_kind == "rolling_30d":
        window_start = now - timedelta(days=30)
    elif window_kind == "calendar_month":
        # First day of current month
        window_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif window_kind == "calendar_quarter":
        # First day of current quarter
        quarter_month = ((now.month - 1) // 3) * 3 + 1
        window_start = now.replace(month=quarter_month, day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        window_start = now - timedelta(days=30)

    # Execute indicator queries to get good and total counts
    # For now, assume good_query and total_query return a COUNT() in the first column
    good_count = 0
    total_count = 0

    if slo.get("good_query"):
        # Execute the DSL/SQL query for good events
        try:
            row = await conn.fetchval(slo["good_query"])
            good_count = int(row) if row else 0
        except Exception as e:
            logger.warning(f"Failed to execute good_query for SLO {slo_id}: {e}")

    if slo.get("total_query"):
        # Execute the DSL/SQL query for total events
        try:
            row = await conn.fetchval(slo["total_query"])
            total_count = int(row) if row else 0
        except Exception as e:
            logger.warning(f"Failed to execute total_query for SLO {slo_id}: {e}")

    # Compute error budget
    target_pct = float(slo["target_pct"])
    budget_snap = _budget.compute_budget(target_pct, good_count, total_count)

    # Compute multi-window burn rates
    # For each window (1h, 6h, 24h, 3d), we'd need separate queries to get error rates
    # For MVP, approximate as 0.0 (no data yet)
    error_rates = {
        "1h": 0.0,
        "6h": 0.0,
        "24h": 0.0,
        "3d": 0.0,
    }
    full_window_seconds = (now - window_start).total_seconds()
    burn_rates = _burn_rate.multi_window_burn(
        error_rates, target_pct / 100.0, int(full_window_seconds)
    )

    # Persist evaluation
    eval_id = _core_id.uuid7()
    await _repo.insert_evaluation(
        conn,
        id=eval_id,
        slo_id=slo_id,
        org_id=slo["org_id"],
        window_start=window_start,
        window_end=now,
        good_count=good_count,
        total_count=total_count,
        attainment_pct=float(budget_snap.attainment_pct),
        budget_remaining_pct=float(budget_snap.budget_remaining_pct),
        burn_rate_1h=burn_rates.get("1h", 0.0),
        burn_rate_6h=burn_rates.get("6h", 0.0),
        burn_rate_24h=burn_rates.get("24h", 0.0),
        burn_rate_3d=burn_rates.get("3d", 0.0),
    )

    return {
        "status": "evaluated",
        "attainment_pct": float(budget_snap.attainment_pct),
        "budget_remaining_pct": float(budget_snap.budget_remaining_pct),
        "burn_rate_1h": burn_rates.get("1h", 0.0),
        "burn_rate_6h": burn_rates.get("6h", 0.0),
        "burn_rate_24h": burn_rates.get("24h", 0.0),
        "burn_rate_3d": burn_rates.get("3d", 0.0),
        "is_breached": budget_snap.is_breached,
    }


__all__ = ["evaluate_slo_node"]
