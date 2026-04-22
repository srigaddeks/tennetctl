"""Backwards-compat shim for callers that import
``backend.02_features.04_audit.service`` and call ``emit_audit_event(...)``.

The canonical path is ``_catalog.run_node(pool, "audit.events.emit", ctx, payload)``,
but a handful of monitoring sub-features (escalation, incidents, slo, action
templates) import this older module by name. Keeping the shim lets those
modules load without a sweeping rewrite; new code should use the node runner
directly.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

_catalog = import_module("backend.01_catalog")
_core_id = import_module("backend.01_core.id")
_ctx_mod = import_module("backend.01_catalog.context")


async def emit_audit_event(
    conn: Any,
    *,
    event_category: str | None = None,
    category: str | None = None,
    user_id: str | None = None,
    actor_id: str | None = None,
    session_id: str | None = None,
    org_id: str | None = None,
    workspace_id: str | None = None,
    resource_type: str | None = None,
    object_type: str | None = None,
    resource_id: str | None = None,
    object_id: str | None = None,
    changes: dict[str, Any] | None = None,
    outcome: str = "success",
    pool: Any = None,
    **extra: Any,
) -> None:
    """Route a legacy-shaped audit call through ``audit.events.emit``.

    Accepts the union of kwargs used across the pre-existing call sites:
    ``event_category``/``category`` for the event key, ``actor_id``/``user_id``
    as the actor, ``object_type``/``resource_type`` + ``object_id``/``resource_id``
    for the target. Never raises — audit failure does not break mutations.
    """
    event_key = event_category or category or "unknown"
    effective_user = user_id or actor_id
    effective_obj_type = resource_type or object_type
    effective_obj_id = resource_id or object_id

    metadata: dict[str, Any] = dict(changes or {})
    if effective_obj_type:
        metadata.setdefault("resource_type", effective_obj_type)
    if effective_obj_id:
        metadata.setdefault("resource_id", effective_obj_id)
    for k, v in extra.items():
        metadata.setdefault(k, v)

    ctx = _ctx_mod.NodeContext(
        user_id=effective_user,
        session_id=session_id,
        org_id=org_id,
        workspace_id=workspace_id,
        audit_category="user",
        trace_id=_core_id.uuid7(),
        span_id=_core_id.uuid7(),
        request_id=_core_id.uuid7(),
        conn=conn,
    )
    try:
        await _catalog.run_node(
            pool,
            "audit.events.emit",
            ctx,
            {"event_key": event_key, "outcome": outcome, "metadata": metadata},
        )
    except Exception:  # noqa: BLE001
        # Audit failures must never propagate.
        pass
