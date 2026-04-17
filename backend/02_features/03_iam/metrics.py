"""
iam.metrics — best-effort IAM counter emissions via monitoring.metrics.increment.

All functions are fire-and-forget: they swallow any exception and never block
the caller. Wrap every call with asyncio.create_task() or await directly —
both work because the functions catch all exceptions internally.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

_catalog: Any = import_module("backend.01_catalog")

_NODE = "monitoring.metrics.increment"


async def _increment(pool: Any, ctx: Any, metric_key: str, labels: dict, value: float = 1.0) -> None:
    try:
        org_id = getattr(ctx, "org_id", None) or ""
        await _catalog.run_node(pool, _NODE, ctx, {
            "org_id": org_id,
            "metric_key": metric_key,
            "labels": labels,
            "value": value,
        })
    except Exception:
        pass  # best-effort — never raise


async def failed_auth(pool: Any, ctx: Any, *, reason: str, source: str = "password") -> None:
    """iam_failed_auth_total{reason, source}"""
    await _increment(pool, ctx, "iam_failed_auth_total", {"reason": reason, "source": source})


async def lockout_triggered(pool: Any, ctx: Any) -> None:
    """iam_lockouts_triggered_total"""
    await _increment(pool, ctx, "iam_lockouts_triggered_total", {})


async def session_evicted(pool: Any, ctx: Any, *, reason: str) -> None:
    """iam_sessions_evicted_total{reason}"""
    await _increment(pool, ctx, "iam_sessions_evicted_total", {"reason": reason})


async def otp_verify(pool: Any, ctx: Any, *, kind: str, outcome: str) -> None:
    """iam_otp_verify_total{kind, outcome}"""
    await _increment(pool, ctx, "iam_otp_verify_total", {"kind": kind, "outcome": outcome})


async def password_reset(pool: Any, ctx: Any, *, outcome: str) -> None:
    """iam_password_reset_total{outcome}"""
    await _increment(pool, ctx, "iam_password_reset_total", {"outcome": outcome})
