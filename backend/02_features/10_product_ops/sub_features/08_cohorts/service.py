"""Cohort service: CRUD + materialize + refresh."""

from __future__ import annotations

import logging
import time
from importlib import import_module
from typing import Any

_core_id: Any = import_module("backend.01_core.id")
_errors: Any = import_module("backend.01_core.errors")
_catalog: Any = import_module("backend.01_catalog")
_repo: Any = import_module(
    "backend.02_features.10_product_ops.sub_features.08_cohorts.repository"
)
_eligibility: Any = import_module(
    "backend.02_features.10_product_ops.sub_features.05_promos.eligibility"
)

logger = logging.getLogger("tennetctl.product_ops.cohorts")


async def create_cohort(
    pool: Any, conn: Any, ctx: Any, *,
    body: Any, org_id: str, workspace_id: str, created_by: str,
) -> dict:
    try:
        row = await _repo.insert_cohort(
            conn,
            cohort_id=_core_id.uuid7(),
            slug=body.slug, name=body.name, description=body.description,
            org_id=org_id, workspace_id=workspace_id,
            kind=body.kind, definition=body.definition or {},
            created_by=created_by,
        )
    except Exception as e:
        if "uq_fct_cohorts_workspace_slug" in str(e):
            raise _errors.AppError(
                "PRODUCT_OPS.COHORT_SLUG_TAKEN",
                f"Cohort slug {body.slug!r} already exists.",
                status_code=409,
            ) from e
        raise

    # Static cohort with initial members → seed lnk + count
    if body.kind == "static" and body.visitor_ids:
        new_set = set(body.visitor_ids)
        await _repo.replace_membership(
            conn, cohort_id=row["id"], org_id=org_id,
            new_member_ids=new_set, to_add=new_set, to_remove=set(),
        )
        row = await _repo.get_cohort_by_id(conn, row["id"])

    try:
        await _catalog.run_node(
            pool, "audit.events.emit", ctx,
            {"event_key": "product_ops.cohorts.created", "outcome": "success",
             "metadata": {"cohort_id": row["id"], "slug": body.slug, "kind": body.kind}},
        )
    except Exception:
        logger.info("audit emit failed for cohort create", exc_info=True)
    return row


async def update_cohort(
    pool: Any, conn: Any, ctx: Any, *, cohort_id: str, body: Any,
) -> dict | None:
    fields: dict[str, Any] = {}
    for k in ("name", "description", "definition", "is_active", "deleted_at"):
        v = getattr(body, k)
        if v is not None:
            fields[k] = v
    row = await _repo.update_cohort(conn, cohort_id=cohort_id, fields=fields)
    if row:
        try:
            await _catalog.run_node(
                pool, "audit.events.emit", ctx,
                {"event_key": "product_ops.cohorts.updated", "outcome": "success",
                 "metadata": {"cohort_id": cohort_id, "fields": list(fields.keys())}},
            )
        except Exception:
            logger.info("audit emit failed for cohort update", exc_info=True)
    return row


async def delete_cohort(pool: Any, conn: Any, ctx: Any, *, cohort_id: str) -> bool:
    ok = await _repo.soft_delete_cohort(conn, cohort_id)
    if ok:
        try:
            await _catalog.run_node(
                pool, "audit.events.emit", ctx,
                {"event_key": "product_ops.cohorts.deleted", "outcome": "success",
                 "metadata": {"cohort_id": cohort_id}},
            )
        except Exception:
            logger.info("audit emit failed for cohort delete", exc_info=True)
    return ok


# ── Refresh / materialize ──────────────────────────────────────────

async def refresh_cohort(
    pool: Any, conn: Any, ctx: Any, *,
    cohort_id: str, triggered_by: str | None,
) -> dict:
    """Re-evaluate a dynamic cohort's definition against all visitors and
    diff-apply membership. Static cohorts: no-op (return current snapshot).

    Returns: {cohort_id, members_added, members_removed, final_count, duration_ms}
    """
    started = time.perf_counter()

    cohort = await _repo.get_cohort_by_id(conn, cohort_id)
    if not cohort or not cohort.get("id"):
        raise _errors.AppError(
            "PRODUCT_OPS.COHORT_NOT_FOUND", "cohort not found", status_code=404,
        )

    if cohort["kind"] == "static":
        return {
            "cohort_id": cohort_id, "members_added": 0, "members_removed": 0,
            "final_count": int(cohort.get("member_count") or 0),
            "duration_ms": int((time.perf_counter() - started) * 1000),
        }

    # Dynamic: pull all visitor profiles, evaluate rule, compute new set
    visitors = await _repo.get_all_visitors_in_workspace(conn, cohort["workspace_id"])
    rule = cohort["definition"] or {}

    new_member_ids: set[str] = set()
    for v in visitors:
        # Build evaluator context. visitor.* keys are exposed flat; allow
        # rules like {"op":"eq","field":"visitor.plan","value":"pro"}.
        eligibility_ctx = _eligibility.build_context(
            visitor=v,
        )
        if _eligibility.evaluate(rule, eligibility_ctx):
            new_member_ids.add(v["id"])

    current = await _repo.get_current_member_ids(conn, cohort_id)
    to_add = new_member_ids - current
    to_remove = current - new_member_ids

    await _repo.replace_membership(
        conn, cohort_id=cohort_id, org_id=cohort["org_id"],
        new_member_ids=new_member_ids, to_add=to_add, to_remove=to_remove,
    )

    duration_ms = int((time.perf_counter() - started) * 1000)
    await _repo.insert_computation(
        conn,
        comp_id=_core_id.uuid7(),
        cohort_id=cohort_id, org_id=cohort["org_id"], workspace_id=cohort["workspace_id"],
        triggered_by=triggered_by, duration_ms=duration_ms,
        members_added=len(to_add), members_removed=len(to_remove),
        final_count=len(new_member_ids),
        metadata={"visitor_pool": len(visitors)},
    )

    try:
        await _catalog.run_node(
            pool, "audit.events.emit", ctx,
            {"event_key": "product_ops.cohorts.refreshed", "outcome": "success",
             "metadata": {
                 "cohort_id": cohort_id, "added": len(to_add),
                 "removed": len(to_remove), "final": len(new_member_ids),
                 "duration_ms": duration_ms,
             }},
        )
    except Exception:
        logger.info("audit emit failed for cohort refresh", exc_info=True)

    return {
        "cohort_id": cohort_id,
        "members_added": len(to_add),
        "members_removed": len(to_remove),
        "final_count": len(new_member_ids),
        "duration_ms": duration_ms,
    }


async def add_static_members(
    pool: Any, conn: Any, ctx: Any, *,
    cohort_id: str, visitor_ids: list[str],
) -> dict:
    cohort = await _repo.get_cohort_by_id(conn, cohort_id)
    if not cohort or not cohort.get("id"):
        raise _errors.AppError("PRODUCT_OPS.COHORT_NOT_FOUND", "cohort not found", status_code=404)
    if cohort["kind"] != "static":
        raise _errors.AppError(
            "PRODUCT_OPS.COHORT_NOT_STATIC",
            "Only static cohorts accept manual member additions; refresh dynamic ones instead.",
            status_code=400,
        )

    current = await _repo.get_current_member_ids(conn, cohort_id)
    new_set = current | set(visitor_ids)
    to_add = new_set - current

    await _repo.replace_membership(
        conn, cohort_id=cohort_id, org_id=cohort["org_id"],
        new_member_ids=new_set, to_add=to_add, to_remove=set(),
    )
    try:
        await _catalog.run_node(
            pool, "audit.events.emit", ctx,
            {"event_key": "product_ops.cohorts.members_added", "outcome": "success",
             "metadata": {"cohort_id": cohort_id, "added": len(to_add)}},
        )
    except Exception:
        logger.info("audit emit failed for static add", exc_info=True)
    return {"cohort_id": cohort_id, "members_added": len(to_add), "final_count": len(new_set)}
