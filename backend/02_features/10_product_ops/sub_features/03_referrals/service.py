"""Referral service: create code, attach to visitor, record conversion."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from importlib import import_module
from typing import Any

_core_id: Any = import_module("backend.01_core.id")
_errors: Any = import_module("backend.01_core.errors")
_catalog: Any = import_module("backend.01_catalog")
_repo: Any = import_module(
    "backend.02_features.10_product_ops.sub_features.03_referrals.repository"
)
_events_repo: Any = import_module(
    "backend.02_features.10_product_ops.sub_features.01_events.repository"
)

logger = logging.getLogger("tennetctl.product_ops.referrals")


async def create_code(
    pool: Any, conn: Any, ctx: Any, *,
    body: Any, org_id: str, workspace_id: str, created_by: str,
) -> dict:
    try:
        row = await _repo.insert_code(
            conn,
            code_id=_core_id.uuid7(),
            code=body.code,
            referrer_user_id=body.referrer_user_id,
            org_id=org_id,
            workspace_id=workspace_id,
            reward_config=body.reward_config or {},
            created_by=created_by,
        )
    except Exception as e:
        if "uq_fct_referral_codes_workspace_code" in str(e):
            raise _errors.AppError(
                "PRODUCT_OPS.REFERRAL_CODE_TAKEN",
                f"Referral code {body.code!r} already exists in this workspace.",
                status_code=409,
            ) from e
        raise

    try:
        await _catalog.run_node(
            pool, "audit.events.emit", ctx,
            {"event_key": "product_ops.referrals.code_created",
             "outcome": "success",
             "metadata": {"code_id": row["id"], "code": body.code}},
        )
    except Exception:
        logger.info("audit emit failed for referral code create", exc_info=True)
    return row


async def attach_referral(
    pool: Any,
    conn: Any,
    ctx: Any,
    *,
    body: Any,
) -> dict:
    # pool/ctx kept for signature uniformity with other services + future audit emit
    del pool, ctx
    """
    Visitor lands with ?ref=<code>. Resolve the code, ensure the visitor row
    exists, and emit a synthetic touch + referral_attached event so:
      - The referral shows up in standard UTM funnels (utm_source=referral, utm_campaign=<code>)
      - A `referral_attached` event lands in evt_product_events for the funnel engine
    """
    code = await _repo.get_code_by_code(
        conn, workspace_id=body.workspace_id, code=body.code,
    )
    if not code:
        raise _errors.AppError(
            "PRODUCT_OPS.REFERRAL_CODE_NOT_FOUND",
            f"Referral code {body.code!r} not found or inactive.",
            status_code=404,
        )

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    visitor_id = await _events_repo.upsert_visitor(
        conn,
        visitor_id=_core_id.uuid7(),
        anonymous_id=body.anonymous_id,
        workspace_id=body.workspace_id,
        org_id=code["org_id"],
        occurred_at=now,
        first_touch=None,
    )

    # Auto-create utm_source='referral' touch carrying the code as utm_campaign.
    # This is the integration mechanism that lets referral conversions appear in
    # standard UTM funnels with no special-case UI (CONTEXT.md decision).
    referral_source_id = await _events_repo.intern_attribution_source(conn, "referral")
    await _events_repo.bulk_insert_touches(conn, [{
        "id": _core_id.uuid7(),
        "visitor_id": visitor_id,
        "org_id": code["org_id"],
        "workspace_id": body.workspace_id,
        "occurred_at": now,
        "utm_source_id": referral_source_id,
        "utm_medium": "referral",
        "utm_campaign": body.code,
        "utm_term": None,
        "utm_content": None,
        "referrer": None,
        "landing_url": body.landing_url,
    }])
    # And a referral_attached event so funnels can see the touch as a discrete step.
    await _events_repo.bulk_insert_events(conn, [{
        "id": _core_id.uuid7(),
        "visitor_id": visitor_id,
        "user_id": None,
        "session_id": None,
        "org_id": code["org_id"],
        "workspace_id": body.workspace_id,
        "event_kind_id": 6,  # referral_attached (per dim_event_kinds seed)
        "event_name": "referral_attached",
        "occurred_at": now,
        "page_url": body.landing_url,
        "referrer": None,
        "metadata": {
            "referral_code_id": code["id"],
            "code": body.code,
            "referrer_user_id": code["referrer_user_id"],
        },
    }])

    return {
        "visitor_id": visitor_id,
        "referral_code_id": code["id"],
        "code": body.code,
        "referrer_user_id": code["referrer_user_id"],
    }


async def record_conversion(
    pool: Any, conn: Any, ctx: Any, *,
    body: Any,
) -> dict:
    # Resolve code by id or by code
    if body.referral_code_id:
        code = await _repo.get_code_by_id(conn, body.referral_code_id)
    elif body.code:
        code = await _repo.get_code_by_code(
            conn, workspace_id=body.workspace_id, code=body.code,
        )
    else:
        raise _errors.AppError(
            "PRODUCT_OPS.REFERRAL_CODE_REQUIRED",
            "Either referral_code_id or code must be provided.",
            status_code=400,
        )

    if not code or not code.get("id"):
        raise _errors.AppError(
            "PRODUCT_OPS.REFERRAL_CODE_NOT_FOUND",
            "Referral code not found.",
            status_code=404,
        )

    visitor_id = body.visitor_id
    if not visitor_id:
        # Best-effort: synthesize a visitor row keyed on converted_user_id
        if not body.converted_user_id:
            raise _errors.AppError(
                "PRODUCT_OPS.VISITOR_OR_USER_REQUIRED",
                "Either visitor_id or converted_user_id must be provided.",
                status_code=400,
            )
        visitor_id = await _events_repo.upsert_visitor(
            conn,
            visitor_id=_core_id.uuid7(),
            anonymous_id=f"v_user_{body.converted_user_id}",
            workspace_id=body.workspace_id,
            org_id=code["org_id"],
            occurred_at=datetime.now(timezone.utc).replace(tzinfo=None),
            first_touch=None,
        )

    occurred = body.occurred_at or datetime.now(timezone.utc)
    if occurred.tzinfo is not None:
        occurred = occurred.astimezone(timezone.utc).replace(tzinfo=None)

    conv_id = await _repo.insert_conversion(
        conn,
        conv_id=_core_id.uuid7(),
        referral_code_id=code["id"],
        visitor_id=visitor_id,
        converted_user_id=body.converted_user_id,
        org_id=code["org_id"],
        workspace_id=body.workspace_id,
        conversion_kind=body.conversion_kind,
        conversion_value_cents=body.conversion_value_cents,
        metadata=body.metadata or {},
        occurred_at=occurred,
    )

    try:
        await _catalog.run_node(
            pool, "audit.events.emit", ctx,
            {
                "event_key": "product_ops.referrals.converted",
                "outcome": "success",
                "metadata": {
                    "conversion_id": conv_id,
                    "referral_code_id": code["id"],
                    "kind": body.conversion_kind,
                    "value_cents": body.conversion_value_cents,
                },
            },
        )
    except Exception:
        logger.info("audit emit failed for referral conversion", exc_info=True)

    return {
        "conversion_id": conv_id,
        "referral_code_id": code["id"],
        "visitor_id": visitor_id,
    }
