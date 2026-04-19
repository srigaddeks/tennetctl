"""Campaign service: CRUD + promo linkage + weighted promo picker."""

from __future__ import annotations

import logging
import random
from datetime import datetime, timezone
from importlib import import_module
from typing import Any

_core_id: Any = import_module("backend.01_core.id")
_errors: Any = import_module("backend.01_core.errors")
_catalog: Any = import_module("backend.01_catalog")
_repo: Any = import_module(
    "backend.02_features.10_product_ops.sub_features.07_campaigns.repository"
)
_eligibility: Any = import_module(
    "backend.02_features.10_product_ops.sub_features.05_promos.eligibility"
)
_events_repo: Any = import_module(
    "backend.02_features.10_product_ops.sub_features.01_events.repository"
)

logger = logging.getLogger("tennetctl.product_ops.campaigns")


def _now_naive_utc() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ── CRUD ───────────────────────────────────────────────────────────

async def create_campaign(
    pool: Any, conn: Any, ctx: Any, *,
    body: Any, org_id: str, workspace_id: str, created_by: str,
) -> dict:
    try:
        row = await _repo.insert_campaign(
            conn,
            campaign_id=_core_id.uuid7(),
            slug=body.slug,
            name=body.name,
            description=body.description,
            org_id=org_id,
            workspace_id=workspace_id,
            starts_at=body.starts_at,
            ends_at=body.ends_at,
            audience_rule=body.audience_rule or {},
            goals=body.goals or {},
            created_by=created_by,
        )
    except Exception as e:
        if "uq_fct_promo_campaigns_workspace_slug" in str(e):
            raise _errors.AppError(
                "PRODUCT_OPS.CAMPAIGN_SLUG_TAKEN",
                f"Campaign slug {body.slug!r} already exists.",
                status_code=409,
            ) from e
        raise

    try:
        await _catalog.run_node(
            pool, "audit.events.emit", ctx,
            {"event_key": "product_ops.campaigns.created", "outcome": "success",
             "metadata": {"campaign_id": row["id"], "slug": body.slug}},
        )
    except Exception:
        logger.info("audit emit failed for campaign create", exc_info=True)
    return row


async def update_campaign(
    pool: Any, conn: Any, ctx: Any, *, campaign_id: str, body: Any,
) -> dict | None:
    fields: dict[str, Any] = {}
    for k in ("name", "description", "starts_at", "ends_at",
              "audience_rule", "goals", "is_active", "deleted_at"):
        v = getattr(body, k)
        if v is not None:
            fields[k] = v
    row = await _repo.update_campaign(conn, campaign_id=campaign_id, fields=fields)
    if row:
        try:
            await _catalog.run_node(
                pool, "audit.events.emit", ctx,
                {"event_key": "product_ops.campaigns.updated", "outcome": "success",
                 "metadata": {"campaign_id": campaign_id, "fields": list(fields.keys())}},
            )
        except Exception:
            logger.info("audit emit failed for campaign update", exc_info=True)
    return row


async def delete_campaign(
    pool: Any, conn: Any, ctx: Any, *, campaign_id: str,
) -> bool:
    ok = await _repo.soft_delete_campaign(conn, campaign_id)
    if ok:
        try:
            await _catalog.run_node(
                pool, "audit.events.emit", ctx,
                {"event_key": "product_ops.campaigns.deleted", "outcome": "success",
                 "metadata": {"campaign_id": campaign_id}},
            )
        except Exception:
            logger.info("audit emit failed for campaign delete", exc_info=True)
    return ok


# ── Promo linkage ───────────────────────────────────────────────────

async def link_promo_to_campaign(
    pool: Any, conn: Any, ctx: Any, *,
    campaign_id: str, body: Any, org_id: str, created_by: str,
) -> dict:
    link_id = _core_id.uuid7()
    try:
        await _repo.link_promo(
            conn,
            link_id=link_id,
            campaign_id=campaign_id,
            promo_code_id=body.promo_code_id,
            weight=body.weight,
            audience_rule_override=body.audience_rule_override,
            org_id=org_id,
            created_by=created_by,
        )
    except Exception as e:
        if "uq_lnk_campaign_promos_campaign_promo" in str(e):
            raise _errors.AppError(
                "PRODUCT_OPS.PROMO_ALREADY_LINKED",
                "Promo is already linked to this campaign.",
                status_code=409,
            ) from e
        raise

    try:
        await _catalog.run_node(
            pool, "audit.events.emit", ctx,
            {"event_key": "product_ops.campaigns.promo_linked", "outcome": "success",
             "metadata": {"campaign_id": campaign_id, "promo_code_id": body.promo_code_id,
                          "weight": body.weight}},
        )
    except Exception:
        logger.info("audit emit failed for promo link", exc_info=True)
    return {"link_id": link_id, "campaign_id": campaign_id, "promo_code_id": body.promo_code_id}


# ── Weighted promo picker (the configurability payoff) ─────────────

async def pick_promo(
    pool: Any, conn: Any, ctx: Any, *, body: Any,
) -> dict:
    del pool, ctx  # kept for signature uniformity; future audit emit may use
    """
    Given (campaign, visitor), return which promo to expose:
      1. Resolve campaign by id or slug.
      2. Check campaign-level audience_rule against visitor context.
         Miss → log exposure {decision=eligibility_miss, promo=NULL}, return.
      3. Pull all linked promos (with their statuses + per-link overrides).
      4. Filter to ones that are "active" status AND pass the per-link
         audience_rule_override (if present) OR the campaign rule (already
         passed).
      5. Weighted random pick. Log exposure with the picked promo. Return.

    Always logs an exposure row (success or miss) for funnel analysis.
    """
    # 1. Resolve campaign
    if body.campaign_id:
        campaign = await _repo.get_campaign_by_id(conn, body.campaign_id)
        if not campaign or not campaign.get("id"):
            raise _errors.AppError(
                "PRODUCT_OPS.CAMPAIGN_NOT_FOUND",
                "Campaign not found.", status_code=404,
            )
    elif body.campaign_slug:
        campaign = await _repo.get_campaign_by_slug(
            conn, workspace_id=body.workspace_id, slug=body.campaign_slug,
        )
        if not campaign:
            raise _errors.AppError(
                "PRODUCT_OPS.CAMPAIGN_NOT_FOUND",
                f"Campaign slug {body.campaign_slug!r} not found.", status_code=404,
            )
    else:
        raise _errors.AppError(
            "PRODUCT_OPS.CAMPAIGN_REF_REQUIRED",
            "Either campaign_id or campaign_slug is required.", status_code=400,
        )

    # Resolve / upsert visitor (so we have a stable id for exposure log)
    visitor_id = body.visitor_id
    if not visitor_id and body.anonymous_id:
        visitor_id = await _events_repo.upsert_visitor(
            conn,
            visitor_id=_core_id.uuid7(),
            anonymous_id=body.anonymous_id,
            workspace_id=body.workspace_id,
            org_id=campaign["org_id"],
            occurred_at=_now_naive_utc(),
            first_touch=None,
        )
    if not visitor_id:
        raise _errors.AppError(
            "PRODUCT_OPS.VISITOR_REF_REQUIRED",
            "visitor_id or anonymous_id is required.", status_code=400,
        )

    eligibility_ctx = _eligibility.build_context(
        visitor=body.eligibility_context.get("visitor"),
        order=body.eligibility_context.get("order"),
        promo=None,
        extra={k: v for k, v in body.eligibility_context.items()
               if k not in ("visitor", "order")},
    )

    # 2. Campaign-level audience check
    now = _now_naive_utc()
    if campaign["status"] != "active":
        await _repo.insert_exposure(
            conn,
            exposure_id=_core_id.uuid7(),
            campaign_id=campaign["id"],
            promo_code_id=None,
            visitor_id=visitor_id,
            org_id=campaign["org_id"],
            workspace_id=body.workspace_id,
            decision="no_active_promos",
            metadata={"reason": f"campaign status: {campaign['status']}"},
            occurred_at=now,
        )
        return {
            "decision": "no_active_promos",
            "campaign_id": campaign["id"],
            "promo_code_id": None,
            "promo_code": None,
            "redemption_kind": None,
            "redemption_config": None,
            "rejection_reason": f"Campaign is {campaign['status']}.",
        }

    if not _eligibility.evaluate(campaign["audience_rule"], eligibility_ctx):
        await _repo.insert_exposure(
            conn,
            exposure_id=_core_id.uuid7(),
            campaign_id=campaign["id"],
            promo_code_id=None,
            visitor_id=visitor_id,
            org_id=campaign["org_id"],
            workspace_id=body.workspace_id,
            decision="eligibility_miss",
            metadata={"rule": campaign["audience_rule"]},
            occurred_at=now,
        )
        return {
            "decision": "eligibility_miss",
            "campaign_id": campaign["id"],
            "promo_code_id": None,
            "promo_code": None,
            "redemption_kind": None,
            "redemption_config": None,
            "rejection_reason": "Visitor does not match campaign audience rule.",
        }

    # 3. Pull linked promos
    candidates_raw = await _repo.list_campaign_promos(conn, campaign["id"])
    # 4. Filter to active + per-link rule passing
    candidates = []
    for c in candidates_raw:
        if c["status"] != "active":
            continue
        per_link_rule = c.get("audience_rule_override")
        if per_link_rule and not _eligibility.evaluate(per_link_rule, eligibility_ctx):
            continue
        candidates.append(c)

    if not candidates:
        await _repo.insert_exposure(
            conn,
            exposure_id=_core_id.uuid7(),
            campaign_id=campaign["id"],
            promo_code_id=None,
            visitor_id=visitor_id,
            org_id=campaign["org_id"],
            workspace_id=body.workspace_id,
            decision="no_active_promos",
            metadata={"linked_count": len(candidates_raw)},
            occurred_at=now,
        )
        return {
            "decision": "no_active_promos",
            "campaign_id": campaign["id"],
            "promo_code_id": None,
            "promo_code": None,
            "redemption_kind": None,
            "redemption_config": None,
            "rejection_reason": "No active promos in campaign for this visitor.",
        }

    # 5. Weighted random pick
    weights = [int(c["weight"]) for c in candidates]
    pick = random.choices(candidates, weights=weights, k=1)[0]
    await _repo.insert_exposure(
        conn,
        exposure_id=_core_id.uuid7(),
        campaign_id=campaign["id"],
        promo_code_id=pick["promo_code_id"],
        visitor_id=visitor_id,
        org_id=campaign["org_id"],
        workspace_id=body.workspace_id,
        decision="weighted_pick",
        metadata={"weight": pick["weight"], "candidate_count": len(candidates)},
        occurred_at=now,
    )
    return {
        "decision": "weighted_pick",
        "campaign_id": campaign["id"],
        "promo_code_id": pick["promo_code_id"],
        "promo_code": pick["code"],
        "redemption_kind": pick["redemption_kind"],
        "redemption_config": pick["redemption_config"],
        "rejection_reason": None,
    }
