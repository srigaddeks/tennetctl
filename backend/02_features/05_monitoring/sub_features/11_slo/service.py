"""Service layer for monitoring.slos — CRUD, audit, indicator validation."""

from __future__ import annotations

import logging
from importlib import import_module
from typing import Any

_core_id: Any = import_module("backend.01_core.id")
_errors: Any = import_module("backend.01_core.errors")
_audit: Any = import_module("backend.02_features.04_audit.service")
_repo: Any = import_module("backend.02_features.05_monitoring.sub_features.11_slo.repository")
_schemas: Any = import_module("backend.02_features.05_monitoring.sub_features.11_slo.schemas")

logger = logging.getLogger("tennetctl.monitoring.slos.service")


# ── SLO CRUD ──────────────────────────────────────────────────────────────


async def create_slo(
    conn: Any,
    ctx: Any,
    *,
    org_id: str,
    name: str,
    slug: str,
    description: str | None,
    indicator_kind: str,
    indicator: dict[str, Any],
    window_kind: str,
    target_pct: float,
    severity: str,
    owner_user_id: str | None = None,
    burn_thresholds: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a new SLO with indicator and burn thresholds.

    Validates indicator_kind, window_kind, and severity exist.
    Emits monitoring.slos.created audit event.
    """
    # Check for duplicate slug within org
    existing = await conn.fetchrow(
        """
        SELECT id FROM "05_monitoring"."10_fct_monitoring_slos"
        WHERE org_id = $1 AND slug = $2 AND deleted_at IS NULL
        """,
        org_id, slug,
    )
    if existing:
        raise _errors.AppError(
            "DUPLICATE",
            f"SLO slug {slug!r} already exists in this org",
            400,
        )

    # Look up dimension IDs
    indicator_kind_id = await _repo.indicator_kind_id_by_code(conn, indicator_kind)
    if indicator_kind_id is None:
        raise _errors.AppError(
            "INVALID_INDICATOR_KIND",
            f"unknown indicator_kind {indicator_kind!r}",
            400,
        )

    window_kind_id = await _repo.window_kind_id_by_code(conn, window_kind)
    if window_kind_id is None:
        raise _errors.AppError(
            "INVALID_WINDOW_KIND",
            f"unknown window_kind {window_kind!r}",
            400,
        )

    severity_id = await _repo.severity_id_by_code(conn, severity)
    if severity_id is None:
        raise _errors.AppError(
            "INVALID_SEVERITY",
            f"unknown severity {severity!r}",
            400,
        )

    # Create SLO
    slo_id = _core_id.uuid7()
    slo_row = await _repo.create_slo(
        conn,
        id=slo_id,
        org_id=org_id,
        workspace_id=ctx.workspace_id,
        name=name,
        slug=slug,
        description=description,
        indicator_kind_id=indicator_kind_id,
        window_kind_id=window_kind_id,
        target_pct=target_pct,
        severity_id=severity_id,
        owner_user_id=owner_user_id,
        created_by=ctx.user_id,
    )

    # Create indicator detail row based on kind
    good_q = indicator.get("good_query")
    total_q = indicator.get("total_query")
    threshold_metric_id = indicator.get("threshold_metric_key")
    threshold_value = indicator.get("threshold_value")
    threshold_op = indicator.get("threshold_op")
    latency_pct = indicator.get("latency_percentile")

    await _repo.create_slo_indicator(
        conn,
        slo_id=slo_id,
        good_query=good_q,
        total_query=total_q,
        threshold_metric_id=threshold_metric_id,
        threshold_value=threshold_value,
        threshold_op=threshold_op,
        latency_percentile=latency_pct,
    )

    # Create burn thresholds (or defaults)
    bt = burn_thresholds or {}
    await _repo.create_slo_burn_thresholds(
        conn,
        slo_id=slo_id,
        fast_window_seconds=int(bt.get("fast_window_seconds", 3600)),
        fast_burn_rate=float(bt.get("fast_burn_rate", 14.4)),
        slow_window_seconds=int(bt.get("slow_window_seconds", 21600)),
        slow_burn_rate=float(bt.get("slow_burn_rate", 6.0)),
        page_on_fast=bool(bt.get("page_on_fast", True)),
        page_on_slow=bool(bt.get("page_on_slow", True)),
    )

    # Emit audit
    await _audit.emit_audit_event(
        conn,
        event_category="monitoring.slos.created",
        user_id=ctx.user_id,
        session_id=ctx.session_id,
        org_id=org_id,
        workspace_id=ctx.workspace_id,
        resource_type="SLO",
        resource_id=slo_id,
        changes={"name": name, "slug": slug, "target_pct": target_pct},
    )

    # Return full view
    return await _repo.get_slo_by_id(conn, slo_id)


async def update_slo(
    conn: Any,
    ctx: Any,
    *,
    slo_id: str,
    org_id: str,
    name: str | None = None,
    description: str | None = None,
    target_pct: float | None = None,
    is_active: bool | None = None,
    owner_user_id: str | None = None,
    severity: str | None = None,
    indicator: dict[str, Any] | None = None,
    burn_thresholds: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Partial update of an SLO. Emits monitoring.slos.updated audit."""
    # Verify ownership
    existing = await _repo.get_slo_by_id(conn, slo_id)
    if not existing:
        raise _errors.AppError("NOT_FOUND", f"SLO {slo_id!r} not found", 404)
    if existing["org_id"] != org_id:
        raise _errors.AppError("UNAUTHORIZED", "SLO not in your org", 403)

    severity_id = None
    if severity:
        severity_id = await _repo.severity_id_by_code(conn, severity)
        if severity_id is None:
            raise _errors.AppError(
                "INVALID_SEVERITY",
                f"unknown severity {severity!r}",
                400,
            )

    # Update main SLO row
    updated = await _repo.update_slo(
        conn,
        slo_id=slo_id,
        name=name,
        description=description,
        target_pct=target_pct,
        is_active=is_active,
        owner_user_id=owner_user_id,
        severity_id=severity_id,
        updated_by=ctx.user_id,
    )

    # Update indicator if provided
    if indicator:
        await conn.execute(
            """
            UPDATE "05_monitoring"."20_dtl_monitoring_slo_indicator"
            SET good_query = $2, total_query = $3,
                threshold_metric_id = $4, threshold_value = $5,
                threshold_op = $6, latency_percentile = $7,
                updated_at = NOW()
            WHERE slo_id = $1
            """,
            slo_id,
            indicator.get("good_query"),
            indicator.get("total_query"),
            indicator.get("threshold_metric_key"),
            indicator.get("threshold_value"),
            indicator.get("threshold_op"),
            indicator.get("latency_percentile"),
        )

    # Update burn thresholds if provided
    if burn_thresholds:
        await conn.execute(
            """
            UPDATE "05_monitoring"."21_dtl_monitoring_slo_burn_thresholds"
            SET fast_window_seconds = $2, fast_burn_rate = $3,
                slow_window_seconds = $4, slow_burn_rate = $5,
                page_on_fast = $6, page_on_slow = $7,
                updated_at = NOW()
            WHERE slo_id = $1
            """,
            slo_id,
            burn_thresholds.get("fast_window_seconds", 3600),
            burn_thresholds.get("fast_burn_rate", 14.4),
            burn_thresholds.get("slow_window_seconds", 21600),
            burn_thresholds.get("slow_burn_rate", 6.0),
            burn_thresholds.get("page_on_fast", True),
            burn_thresholds.get("page_on_slow", True),
        )

    # Emit audit
    changes = {}
    if name is not None:
        changes["name"] = name
    if description is not None:
        changes["description"] = description
    if target_pct is not None:
        changes["target_pct"] = target_pct
    if is_active is not None:
        changes["is_active"] = is_active

    await _audit.emit_audit_event(
        conn,
        event_category="monitoring.slos.updated",
        user_id=ctx.user_id,
        session_id=ctx.session_id,
        org_id=org_id,
        workspace_id=ctx.workspace_id,
        resource_type="SLO",
        resource_id=slo_id,
        changes=changes,
    )

    return await _repo.get_slo_by_id(conn, slo_id)


async def delete_slo(
    conn: Any,
    ctx: Any,
    *,
    slo_id: str,
    org_id: str,
) -> None:
    """Soft-delete an SLO. Emits monitoring.slos.deleted audit."""
    existing = await _repo.get_slo_by_id(conn, slo_id)
    if not existing:
        raise _errors.AppError("NOT_FOUND", f"SLO {slo_id!r} not found", 404)
    if existing["org_id"] != org_id:
        raise _errors.AppError("UNAUTHORIZED", "SLO not in your org", 403)

    await _repo.soft_delete_slo(conn, slo_id, ctx.user_id)

    await _audit.emit_audit_event(
        conn,
        event_category="monitoring.slos.deleted",
        user_id=ctx.user_id,
        session_id=ctx.session_id,
        org_id=org_id,
        workspace_id=ctx.workspace_id,
        resource_type="SLO",
        resource_id=slo_id,
        changes={"deleted_at": "NOW()"},
    )


__all__ = [
    "create_slo",
    "update_slo",
    "delete_slo",
]
