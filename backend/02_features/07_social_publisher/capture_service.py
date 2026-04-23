"""social_publisher.capture — service layer."""
from __future__ import annotations

import logging
from importlib import import_module
from typing import Any

logger = logging.getLogger("tennetctl.social.capture")

_core_id: Any = import_module("backend.01_core.id")
_repo: Any = import_module(
    "backend.02_features.07_social_publisher.capture_repository"
)
_catalog: Any = import_module("backend.01_catalog")

_PLATFORM_ALIAS = {"twitter": "x"}


async def ingest_batch(
    conn: Any,
    *,
    user_id: str,
    org_id: str,
    session_id: str,
    captures_in: list[dict],
) -> dict:
    """Insert up to 100 captures; return {inserted, deduped, ids}."""
    normalised = []
    for c in captures_in:
        d = dict(c)
        d["platform"] = _PLATFORM_ALIAS.get(d.get("platform", ""), d.get("platform", ""))
        if not d.get("id"):
            d["id"] = _core_id.uuid7()
        # Truncate text to 512 chars
        if d.get("text_excerpt"):
            d["text_excerpt"] = d["text_excerpt"][:512]
        normalised.append(d)

    inserted_ids, deduped = await _repo.bulk_insert(
        conn, user_id=user_id, org_id=org_id, captures=normalised,
    )

    if inserted_ids:
        try:
            await _catalog.run_node(
                "audit.events.emit",
                conn=conn,
                input={
                    "event_key": "social.capture.ingested",
                    "outcome": "success",
                    "user_id": user_id,
                    "session_id": session_id,
                    "org_id": org_id,
                    "metadata": {
                        "inserted": len(inserted_ids),
                        "deduped": deduped,
                        "total": len(normalised),
                    },
                },
            )
        except Exception:
            pass  # audit is best-effort — never block ingest

    return {"inserted": len(inserted_ids), "deduped": deduped, "ids": inserted_ids}


async def list_captures(
    conn: Any,
    *,
    user_id: str,
    org_id: str | None,
    platform: str | None,
    capture_type: str | None,
    from_dt: Any,
    to_dt: Any,
    is_own: bool | None,
    limit: int,
    offset: int,
) -> dict:
    items, total = await _repo.list_captures(
        conn,
        user_id=user_id,
        org_id=org_id,
        platform=platform,
        capture_type=capture_type,
        from_dt=from_dt,
        to_dt=to_dt,
        is_own=is_own,
        limit=limit,
        offset=offset,
    )
    return {"items": items, "total": total, "limit": limit, "offset": offset}
