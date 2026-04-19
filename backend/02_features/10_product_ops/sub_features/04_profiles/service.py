"""Profile service: set traits + read profiles."""

from __future__ import annotations

import logging
from importlib import import_module
from typing import Any

_core_id: Any = import_module("backend.01_core.id")
_errors: Any = import_module("backend.01_core.errors")
_catalog: Any = import_module("backend.01_catalog")
_repo: Any = import_module(
    "backend.02_features.10_product_ops.sub_features.04_profiles.repository"
)

logger = logging.getLogger("tennetctl.product_ops.profiles")


async def set_traits(
    pool: Any, conn: Any, ctx: Any, *,
    body: Any,  # SetTraitsBody
) -> dict:
    """Apply a flat dict of trait_code → value. Unknown codes are silently
    dropped (with a debug log) — operators register them via dim_attr_defs first.

    Resolves visitor_id via: (1) explicit visitor_id, (2) anonymous_id lookup
    in fct_visitors, (3) reject if neither.
    """
    visitor_id = body.visitor_id
    if not visitor_id:
        if not body.anonymous_id:
            raise _errors.AppError(
                "PRODUCT_OPS.VISITOR_OR_ANONYMOUS_REQUIRED",
                "Either visitor_id or anonymous_id is required.",
                status_code=400,
            )
        row = await conn.fetchrow(
            'SELECT id FROM "10_product_ops"."10_fct_visitors" WHERE anonymous_id = $1',
            body.anonymous_id,
        )
        if not row:
            raise _errors.AppError(
                "PRODUCT_OPS.VISITOR_NOT_FOUND",
                f"No visitor for anonymous_id {body.anonymous_id!r}. Send a track() event first.",
                status_code=404,
            )
        visitor_id = row["id"]

    defs = await _repo.get_attr_defs(conn)

    applied = 0
    skipped: list[str] = []
    for code, value in (body.traits or {}).items():
        d = defs.get(code)
        if d is None:
            skipped.append(code)
            continue
        await _repo.upsert_visitor_attr(
            conn,
            attr_id=_core_id.uuid7(),
            visitor_id=visitor_id,
            attr_def_id=d["id"],
            value_type=d["value_type"],
            value=value,
            source=body.source,
        )
        applied += 1

    # Audit summary (one per call, not per trait — keeps audit volume bounded)
    try:
        from dataclasses import replace as _replace
        audit_ctx = _replace(ctx, audit_category="setup")
        await _catalog.run_node(
            pool, "audit.events.emit", audit_ctx,
            {
                "event_key": "product_ops.profiles.traits_set",
                "outcome": "success",
                "metadata": {
                    "visitor_id": visitor_id,
                    "applied": applied,
                    "skipped_codes": skipped,
                },
            },
        )
    except Exception:
        logger.info("audit emit failed for traits_set", exc_info=True)

    return {
        "visitor_id": visitor_id,
        "applied": applied,
        "skipped": skipped,
    }


async def get_profile_full(conn: Any, visitor_id: str) -> dict | None:
    profile = await _repo.get_profile(conn, visitor_id)
    if not profile:
        return None
    profile["traits"] = await _repo.get_visitor_attrs(conn, visitor_id)
    return profile
