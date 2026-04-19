"""Partner service: CRUD + code linkage + payout recording."""

from __future__ import annotations

import logging
from importlib import import_module
from typing import Any

_core_id: Any = import_module("backend.01_core.id")
_errors: Any = import_module("backend.01_core.errors")
_catalog: Any = import_module("backend.01_catalog")
_repo: Any = import_module(
    "backend.02_features.10_product_ops.sub_features.06_partners.repository"
)

logger = logging.getLogger("tennetctl.product_ops.partners")


async def create_partner(
    pool: Any, conn: Any, ctx: Any, *,
    body: Any, org_id: str, workspace_id: str, created_by: str,
) -> dict:
    try:
        row = await _repo.insert_partner(
            conn,
            partner_id=_core_id.uuid7(),
            slug=body.slug,
            display_name=body.display_name,
            contact_email=body.contact_email,
            org_id=org_id,
            workspace_id=workspace_id,
            user_id=body.user_id,
            tier_id=body.tier_id,
            created_by=created_by,
        )
    except Exception as e:
        if "uq_fct_partners_workspace_slug" in str(e):
            raise _errors.AppError(
                "PRODUCT_OPS.PARTNER_SLUG_TAKEN",
                f"Partner slug {body.slug!r} already exists.",
                status_code=409,
            ) from e
        raise

    try:
        await _catalog.run_node(
            pool, "audit.events.emit", ctx,
            {"event_key": "product_ops.partners.created", "outcome": "success",
             "metadata": {"partner_id": row["id"], "slug": body.slug}},
        )
    except Exception:
        logger.info("audit emit failed for partner create", exc_info=True)
    return row


async def update_partner(
    pool: Any, conn: Any, ctx: Any, *, partner_id: str, body: Any,
) -> dict | None:
    fields: dict[str, Any] = {}
    for k in ("display_name", "contact_email", "user_id", "tier_id", "is_active", "deleted_at"):
        v = getattr(body, k)
        if v is not None:
            fields[k] = v
    row = await _repo.update_partner(conn, partner_id=partner_id, fields=fields)
    if row:
        try:
            await _catalog.run_node(
                pool, "audit.events.emit", ctx,
                {"event_key": "product_ops.partners.updated", "outcome": "success",
                 "metadata": {"partner_id": partner_id, "fields": list(fields.keys())}},
            )
        except Exception:
            logger.info("audit emit failed for partner update", exc_info=True)
    return row


async def delete_partner(
    pool: Any, conn: Any, ctx: Any, *, partner_id: str,
) -> bool:
    ok = await _repo.soft_delete_partner(conn, partner_id)
    if ok:
        try:
            await _catalog.run_node(
                pool, "audit.events.emit", ctx,
                {"event_key": "product_ops.partners.deleted", "outcome": "success",
                 "metadata": {"partner_id": partner_id}},
            )
        except Exception:
            logger.info("audit emit failed for partner delete", exc_info=True)
    return ok


# ── Code linkage ────────────────────────────────────────────────────

async def link_code_to_partner(
    pool: Any, conn: Any, ctx: Any, *,
    partner_id: str, body: Any, org_id: str, created_by: str,
) -> dict:
    if body.code_kind == "referral" and not body.referral_code_id:
        raise _errors.AppError(
            "PRODUCT_OPS.REFERRAL_CODE_ID_REQUIRED",
            "code_kind=referral requires referral_code_id",
            status_code=400,
        )
    if body.code_kind == "promo" and not body.promo_code_id:
        raise _errors.AppError(
            "PRODUCT_OPS.PROMO_CODE_ID_REQUIRED",
            "code_kind=promo requires promo_code_id",
            status_code=400,
        )

    result = await _repo.link_code(
        conn,
        link_id=_core_id.uuid7(),
        partner_id=partner_id,
        code_kind=body.code_kind,
        referral_code_id=body.referral_code_id,
        promo_code_id=body.promo_code_id,
        payout_bp_override=body.payout_bp_override,
        org_id=org_id,
        created_by=created_by,
    )
    try:
        await _catalog.run_node(
            pool, "audit.events.emit", ctx,
            {"event_key": "product_ops.partners.code_linked", "outcome": "success",
             "metadata": {"partner_id": partner_id, "code_kind": body.code_kind}},
        )
    except Exception:
        logger.info("audit emit failed for code link", exc_info=True)
    return result


# ── Payout ──────────────────────────────────────────────────────────

async def record_payout(
    pool: Any, conn: Any, ctx: Any, *,
    partner_id: str, body: Any, org_id: str, workspace_id: str, created_by: str,
) -> dict:
    payout_id = _core_id.uuid7()
    await _repo.insert_payout(
        conn,
        payout_id=payout_id,
        partner_id=partner_id,
        org_id=org_id,
        workspace_id=workspace_id,
        period_start=body.period_start,
        period_end=body.period_end,
        amount_cents=body.amount_cents,
        currency=body.currency,
        status=body.status,
        paid_at=body.paid_at,
        external_ref=body.external_ref,
        metadata=body.metadata or {},
        created_by=created_by,
    )
    try:
        await _catalog.run_node(
            pool, "audit.events.emit", ctx,
            {"event_key": "product_ops.partners.payout_recorded", "outcome": "success",
             "metadata": {
                 "partner_id": partner_id,
                 "payout_id": payout_id,
                 "amount_cents": body.amount_cents,
                 "status": body.status,
             }},
        )
    except Exception:
        logger.info("audit emit failed for payout", exc_info=True)
    return {"payout_id": payout_id, "partner_id": partner_id, "status": body.status}
