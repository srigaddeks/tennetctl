"""Promo service: create/list/update/delete + redeem with cap + expiry checks."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from importlib import import_module
from typing import Any

_core_id: Any = import_module("backend.01_core.id")
_errors: Any = import_module("backend.01_core.errors")
_catalog: Any = import_module("backend.01_catalog")
_repo: Any = import_module(
    "backend.02_features.10_product_ops.sub_features.05_promos.repository"
)
_eligibility: Any = import_module(
    "backend.02_features.10_product_ops.sub_features.05_promos.eligibility"
)

logger = logging.getLogger("tennetctl.product_ops.promos")


def _now_naive_utc() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ── Admin ───────────────────────────────────────────────────────────

async def create_code(
    pool: Any, conn: Any, ctx: Any, *,
    body: Any, org_id: str, workspace_id: str, created_by: str,
) -> dict:
    try:
        row = await _repo.insert_code(
            conn,
            promo_id=_core_id.uuid7(),
            code=body.code,
            org_id=org_id,
            workspace_id=workspace_id,
            redemption_kind=body.redemption_kind,
            redemption_config=body.redemption_config or {},
            description=body.description,
            max_total_uses=body.max_total_uses,
            max_uses_per_visitor=body.max_uses_per_visitor,
            starts_at=body.starts_at,
            ends_at=body.ends_at,
            eligibility=body.eligibility or {},
            created_by=created_by,
        )
    except Exception as e:
        if "uq_fct_promo_codes_workspace_code" in str(e):
            raise _errors.AppError(
                "PRODUCT_OPS.PROMO_CODE_TAKEN",
                f"Promo code {body.code!r} already exists in this workspace.",
                status_code=409,
            ) from e
        raise

    try:
        await _catalog.run_node(
            pool, "audit.events.emit", ctx,
            {"event_key": "product_ops.promos.created", "outcome": "success",
             "metadata": {"promo_id": row["id"], "code": body.code, "kind": body.redemption_kind}},
        )
    except Exception:
        logger.info("audit emit failed for promo create", exc_info=True)
    return row


async def update_code(
    pool: Any, conn: Any, ctx: Any, *, promo_id: str, body: Any,
) -> dict | None:
    fields: dict[str, Any] = {}
    for k in (
        "description", "max_total_uses", "max_uses_per_visitor",
        "starts_at", "ends_at", "eligibility", "is_active", "deleted_at",
    ):
        v = getattr(body, k)
        if v is not None:
            fields[k] = v
    row = await _repo.update_code(conn, promo_id=promo_id, fields=fields)
    if row:
        try:
            await _catalog.run_node(
                pool, "audit.events.emit", ctx,
                {"event_key": "product_ops.promos.updated", "outcome": "success",
                 "metadata": {"promo_id": promo_id, "fields": list(fields.keys())}},
            )
        except Exception:
            logger.info("audit emit failed for promo update", exc_info=True)
    return row


async def delete_code(
    pool: Any, conn: Any, ctx: Any, *, promo_id: str,
) -> bool:
    ok = await _repo.soft_delete_code(conn, promo_id)
    if ok:
        try:
            await _catalog.run_node(
                pool, "audit.events.emit", ctx,
                {"event_key": "product_ops.promos.deleted", "outcome": "success",
                 "metadata": {"promo_id": promo_id}},
            )
        except Exception:
            logger.info("audit emit failed for promo delete", exc_info=True)
    return ok


# ── Redemption ──────────────────────────────────────────────────────

async def redeem(
    pool: Any, conn: Any, ctx: Any, *, body: Any,
) -> dict:
    """
    Attempt to redeem a promo code. Always writes a redemption row (success or
    rejection) so operators can audit the funnel of redemption attempts.

    Returns {outcome, redemption_id, promo_code_id, ...}.
    """
    code = await _repo.get_code_by_code(
        conn, workspace_id=body.workspace_id, code=body.code,
    )
    now = _now_naive_utc()

    # 1. Unknown code → log a synthetic rejection (no FK, no row)
    if not code:
        try:
            await _catalog.run_node(
                pool, "audit.events.emit", ctx,
                {"event_key": "product_ops.promos.rejected_unknown",
                 "outcome": "success",
                 "metadata": {"code": body.code, "workspace_id": body.workspace_id}},
            )
        except Exception:
            pass
        return {
            "outcome": "rejected_unknown_code",
            "redemption_id": None,
            "promo_code_id": None,
            "redemption_kind": None,
            "redemption_config": None,
            "rejection_reason": f"Code {body.code!r} not found.",
        }

    # 2. Status checks (the view computes status — pre-aggregated logic)
    rejection: tuple[str, str] | None = None
    if code["status"] == "expired":
        rejection = ("rejected_expired", "Promo code has expired.")
    elif code["status"] == "scheduled":
        rejection = ("rejected_inactive", "Promo code is not yet active.")
    elif code["status"] == "inactive":
        rejection = ("rejected_inactive", "Promo code is inactive.")
    elif code["status"] == "exhausted":
        rejection = ("rejected_max_uses", "Promo code has reached its usage cap.")

    # 3. Per-visitor cap (only if visitor_id provided)
    if rejection is None and body.visitor_id:
        used = await _repo.count_redemptions_for_visitor(
            conn, promo_code_id=code["id"], visitor_id=body.visitor_id,
        )
        if used >= int(code["max_uses_per_visitor"]):
            rejection = ("rejected_per_visitor",
                         f"Visitor has already used this code {used} time(s) (cap: {code['max_uses_per_visitor']}).")

    # 3b. Eligibility rule. Empty rule = always pass. Caller passes context
    # bits via body.metadata (e.g. {"visitor": {...}, "order": {...}}); we
    # also fold the resolved promo into the context so rules can reference
    # promo.code if needed.
    if rejection is None and code.get("eligibility"):
        ctx_payload = body.metadata.get("eligibility_context") if body.metadata else None
        if not isinstance(ctx_payload, dict):
            ctx_payload = {}
        eligibility_ctx = _eligibility.build_context(
            visitor=ctx_payload.get("visitor"),
            order=ctx_payload.get("order"),
            promo={"code": body.code, "id": code["id"]},
            extra={k: v for k, v in ctx_payload.items() if k not in ("visitor", "order")},
        )
        if not _eligibility.evaluate(code["eligibility"], eligibility_ctx):
            rejection = ("rejected_eligibility",
                         "Visitor / order does not match the promo's eligibility rule.")

    # 4. Write redemption row (success OR rejection)
    redemption_id = _core_id.uuid7()
    if rejection is None:
        outcome, reason = "redeemed", None
    else:
        outcome, reason = rejection

    await _repo.insert_redemption(
        conn,
        redemption_id=redemption_id,
        promo_code_id=code["id"],
        visitor_id=body.visitor_id,
        redeemer_user_id=body.redeemer_user_id,
        org_id=code["org_id"],
        workspace_id=body.workspace_id,
        outcome=outcome,
        rejection_reason=reason,
        metadata=body.metadata or {},
        occurred_at=now,
    )

    # 5. Audit emission. One audit per redemption attempt — visibility >> volume.
    try:
        from dataclasses import replace as _replace
        audit_ctx = _replace(ctx, audit_category="setup")  # may be anonymous
        await _catalog.run_node(
            pool, "audit.events.emit", audit_ctx,
            {
                "event_key": f"product_ops.promos.{outcome}",
                "outcome": "success",
                "metadata": {
                    "promo_id": code["id"],
                    "code": body.code,
                    "redemption_id": redemption_id,
                    "rejection_reason": reason,
                },
            },
        )
    except Exception:
        logger.info("audit emit failed for redemption", exc_info=True)

    return {
        "outcome": outcome,
        "redemption_id": redemption_id,
        "promo_code_id": code["id"],
        "redemption_kind": code["redemption_kind"] if outcome == "redeemed" else None,
        "redemption_config": code["redemption_config"] if outcome == "redeemed" else None,
        "rejection_reason": reason,
    }
