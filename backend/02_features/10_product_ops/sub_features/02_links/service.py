"""Link shortener service: create/list/get/update/soft-delete + redirect resolution."""

from __future__ import annotations

import logging
import secrets
from importlib import import_module
from typing import Any

_core_id: Any = import_module("backend.01_core.id")
_errors: Any = import_module("backend.01_core.errors")
_catalog: Any = import_module("backend.01_catalog")
_repo: Any = import_module(
    "backend.02_features.10_product_ops.sub_features.02_links.repository"
)
_events_repo: Any = import_module(
    "backend.02_features.10_product_ops.sub_features.01_events.repository"
)

logger = logging.getLogger("tennetctl.product_ops.links")

_SLUG_ALPHABET = "abcdefghijkmnopqrstuvwxyz23456789"  # exclude 0, 1, l for legibility
_SLUG_LEN = 8
_SLUG_MAX_RETRIES = 5


def _mint_slug() -> str:
    return "".join(secrets.choice(_SLUG_ALPHABET) for _ in range(_SLUG_LEN))


async def _intern_utm_source(conn: Any, code: str | None) -> int | None:
    if not code:
        return None
    return await _events_repo.intern_attribution_source(conn, code)


async def create_link(
    pool: Any,
    conn: Any,
    ctx: Any,
    *,
    body: Any,  # CreateShortLinkBody
    org_id: str,
    workspace_id: str,
    created_by: str,
) -> dict:
    """Create a new short link. Auto-mint slug if absent. Retries on collision."""
    slug = body.slug
    utm_source_id = await _intern_utm_source(conn, body.utm_source)

    for attempt in range(_SLUG_MAX_RETRIES + 1):
        candidate = slug or _mint_slug()
        try:
            row = await _repo.insert_short_link(
                conn,
                link_id=_core_id.uuid7(),
                slug=candidate,
                target_url=body.target_url,
                org_id=org_id,
                workspace_id=workspace_id,
                created_by=created_by,
                utm_source_id=utm_source_id,
                utm_medium=body.utm_medium,
                utm_campaign=body.utm_campaign,
                utm_term=body.utm_term,
                utm_content=body.utm_content,
            )
            # Audit emission via run_node (NCP v1)
            try:
                await _catalog.run_node(
                    pool, "audit.events.emit", ctx,
                    {
                        "event_key": "product_ops.links.created",
                        "outcome": "success",
                        "metadata": {"link_id": row["id"], "slug": row["slug"]},
                    },
                )
            except Exception:
                logger.info("audit emit failed for link create", exc_info=True)
            return row
        except Exception as e:
            # On unique violation, retry with a fresh mint (only if slug was auto)
            if slug is not None or attempt == _SLUG_MAX_RETRIES:
                if "uq_fct_short_links_workspace_slug" in str(e):
                    raise _errors.AppError(
                        "PRODUCT_OPS.SLUG_TAKEN",
                        f"Slug {candidate!r} is already in use in this workspace.",
                        status_code=409,
                    ) from e
                raise

    raise _errors.AppError(
        "PRODUCT_OPS.SLUG_MINT_FAILED",
        "Could not mint a unique slug after retries; try again or supply one explicitly.",
        status_code=500,
    )


async def resolve_redirect(
    pool: Any,  # noqa: ARG001 — kept for signature uniformity with other services
    conn: Any,
    ctx: Any,  # noqa: ARG001 — kept for trace propagation by future Phase 48 callers
    *,
    workspace_id: str,
    slug: str,
    visitor_anonymous_id: str | None,
) -> dict | None:
    """
    Look up a slug → target. On hit, fire-and-forget a click event into the
    ingest pipeline (so the click flows through evt_product_events with the
    link's UTM preset stitched on).

    Returns the link row on hit, None on miss.
    """
    link = await _repo.get_short_link_by_slug(conn, workspace_id=workspace_id, slug=slug)
    if not link:
        return None

    # Fire-and-forget click event written directly into evt_product_events.
    # Going through product_ops.events.ingest would require a project_key dance
    # (the link already knows its workspace). Direct repo write keeps the redirect
    # path fast and decoupled from vault. Audit-of-clicks is intentionally skipped
    # (audit amplification at click hot-path; vault precedent).
    if visitor_anonymous_id:
        try:
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc).replace(tzinfo=None)
            # Resolve / upsert visitor row for this anonymous_id
            visitor_id = await _events_repo.upsert_visitor(
                conn,
                visitor_id=_core_id.uuid7(),
                anonymous_id=visitor_anonymous_id,
                workspace_id=workspace_id,
                org_id=link["org_id"],
                occurred_at=now,
                first_touch=None,
            )
            # Intern the link's UTM source so click events match the dim
            utm_source_id = None
            if link.get("utm_source"):
                utm_source_id = await _events_repo.intern_attribution_source(
                    conn, link["utm_source"],
                )
            await _events_repo.bulk_insert_events(conn, [{
                "id": _core_id.uuid7(),
                "visitor_id": visitor_id,
                "user_id": None,
                "session_id": None,
                "org_id": link["org_id"],
                "workspace_id": workspace_id,
                "event_kind_id": 3,  # click (stable; per dim_event_kinds seed)
                "event_name": "link_click",
                "occurred_at": now,
                "page_url": link.get("target_url"),
                "referrer": None,
                "metadata": {"slug": slug, "link_id": link["id"]},
            }])
            if utm_source_id is not None or link.get("utm_campaign"):
                await _events_repo.bulk_insert_touches(conn, [{
                    "id": _core_id.uuid7(),
                    "visitor_id": visitor_id,
                    "org_id": link["org_id"],
                    "workspace_id": workspace_id,
                    "occurred_at": now,
                    "utm_source_id": utm_source_id,
                    "utm_medium": link.get("utm_medium"),
                    "utm_campaign": link.get("utm_campaign"),
                    "utm_term": link.get("utm_term"),
                    "utm_content": link.get("utm_content"),
                    "referrer": None,
                    "landing_url": link.get("target_url"),
                }])
        except Exception:
            logger.info("link click event write failed", exc_info=True)

    return link


async def update_link(
    pool: Any, conn: Any, ctx: Any, *, link_id: str, body: Any,
) -> dict | None:
    fields: dict[str, Any] = {}
    if body.target_url is not None:
        fields["target_url"] = body.target_url
    if body.is_active is not None:
        fields["is_active"] = body.is_active
    if body.deleted_at is not None:
        fields["deleted_at"] = body.deleted_at
    if body.utm_source is not None:
        fields["utm_source_id"] = await _intern_utm_source(conn, body.utm_source)
    for k in ("utm_medium", "utm_campaign", "utm_term", "utm_content"):
        v = getattr(body, k)
        if v is not None:
            fields[k] = v

    row = await _repo.update_short_link(conn, link_id=link_id, fields=fields)
    if row:
        try:
            await _catalog.run_node(
                pool, "audit.events.emit", ctx,
                {
                    "event_key": "product_ops.links.updated",
                    "outcome": "success",
                    "metadata": {"link_id": link_id, "fields": list(fields.keys())},
                },
            )
        except Exception:
            logger.info("audit emit failed for link update", exc_info=True)
    return row


async def delete_link(pool: Any, conn: Any, ctx: Any, *, link_id: str) -> bool:
    ok = await _repo.soft_delete_short_link(conn, link_id)
    if ok:
        try:
            await _catalog.run_node(
                pool, "audit.events.emit", ctx,
                {
                    "event_key": "product_ops.links.deleted",
                    "outcome": "success",
                    "metadata": {"link_id": link_id},
                },
            )
        except Exception:
            logger.info("audit emit failed for link delete", exc_info=True)
    return ok
