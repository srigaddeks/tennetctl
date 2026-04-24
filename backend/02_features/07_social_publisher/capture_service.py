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

# Deprecated `own_*` capture types — we normalize these to base + is_own=True
# so the dim table can retire those rows cleanly over time.
_REDUNDANT_TYPE_MAP = {
    "own_post_published": "feed_post_seen",
    "own_comment":        "comment_seen",
}


def _is_empty(d: dict) -> bool:
    """
    Reject captures that carry no information content. A row with no author,
    no text, no url, no engagement metrics and no extra raw_attrs is noise
    and would only show up as an empty row in the UI.

    Context-only types (hashtag_feed_seen, search_result_seen, notification_seen)
    are allowed through because their value is in raw_attrs / the URN itself.
    """
    context_only = {
        "hashtag_feed_seen", "search_result_seen", "notification_seen",
        "reaction_detail", "list_viewed", "space_seen", "community_seen",
        # Behavior signals — meaningful via their raw_attrs + platform_post_id
        "post_dwell", "post_clicked", "text_selected", "text_copied",
        "video_played", "link_hovered", "page_visit",
        "job_recommendation", "messaging_thread", "activity_item",
        "saved_item", "reactors_list", "reposters_list", "follower_item",
    }
    if d.get("type") in context_only:
        return False

    has_author  = bool(d.get("author_handle") or d.get("author_name"))
    has_text    = bool(d.get("text_excerpt"))
    has_url     = bool(d.get("url"))
    has_metric  = any(d.get(k) is not None for k in ("like_count", "reply_count", "repost_count", "view_count"))
    raw_attrs   = d.get("raw_attrs") or {}
    has_raw     = any(
        raw_attrs.get(k) for k in (
            "full_text", "title", "about", "description", "headline",
            "body_excerpt", "bio", "name", "tagline",
        )
    )
    return not (has_author or has_text or has_url or has_metric or has_raw)


def _normalise(c: dict) -> dict:
    d = dict(c)
    d["platform"] = _PLATFORM_ALIAS.get(d.get("platform", ""), d.get("platform", ""))

    # Fold deprecated types into the canonical type + is_own flag.
    t = d.get("type")
    if t in _REDUNDANT_TYPE_MAP:
        d["type"] = _REDUNDANT_TYPE_MAP[t]
        d["is_own"] = True

    if not d.get("id"):
        d["id"] = _core_id.uuid7()

    # Truncate long text fields defensively.
    if d.get("text_excerpt"):
        d["text_excerpt"] = d["text_excerpt"][:512]
    if d.get("platform_post_id") and len(d["platform_post_id"]) > 512:
        d["platform_post_id"] = d["platform_post_id"][:512]
    return d


async def ingest_batch(
    conn: Any,
    *,
    user_id: str,
    org_id: str,
    session_id: str,
    workspace_id: str | None = None,
    captures_in: list[dict],
) -> dict:
    """
    Insert up to 100 captures.

    Returns {inserted, deduped, metric_observations, ids}.

    Behaviour:
      • First sight of a post → INSERT into 62_evt_social_captures.
      • Subsequent sights → INSERT into 63_evt_capture_metrics (preserves
        engagement time-series instead of dropping the update).
      • `own_post_published` / `own_comment` are normalized to
        feed_post_seen / comment_seen + is_own=True.
    """
    normalised = [_normalise(c) for c in captures_in]

    # Drop empty captures before touching the DB. They'd only clutter the UI.
    rejected_empty = 0
    filtered: list[dict] = []
    for d in normalised:
        if _is_empty(d):
            rejected_empty += 1
            continue
        filtered.append(d)
    normalised = filtered

    inserted_ids, deduped, metric_obs = await _repo.bulk_insert(
        conn,
        user_id=user_id,
        org_id=org_id,
        workspace_id=workspace_id,
        captures=normalised,
    )

    if inserted_ids or metric_obs:
        try:
            # Count inserts per capture type so we can see extractor health
            # per type/platform in the audit log.
            by_type: dict[str, int] = {}
            for c in normalised:
                k = f"{c.get('platform','?')}.{c.get('type','?')}"
                by_type[k] = by_type.get(k, 0) + 1
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
                        "metric_observations": metric_obs,
                        "total": len(normalised),
                        "by_type": by_type,
                    },
                },
            )
        except Exception:
            pass  # audit is best-effort — never block ingest

    return {
        "inserted": len(inserted_ids),
        "deduped": deduped,
        "metric_observations": metric_obs,
        "rejected_empty": rejected_empty,
        "ids": inserted_ids,
    }


async def list_captures(
    conn: Any,
    *,
    user_id: str,
    org_id: str | None,
    workspace_id: str | None = None,
    platform: str | None = None,
    capture_type: str | None = None,
    author_handle: str | None = None,
    hashtag: str | None = None,
    mention: str | None = None,
    q: str | None = None,
    from_dt: Any = None,
    to_dt: Any = None,
    is_own: bool | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict:
    items, total = await _repo.list_captures(
        conn,
        user_id=user_id,
        org_id=org_id,
        workspace_id=workspace_id,
        platform=platform,
        capture_type=capture_type,
        author_handle=author_handle,
        hashtag=hashtag,
        mention=mention,
        q=q,
        from_dt=from_dt,
        to_dt=to_dt,
        is_own=is_own,
        limit=limit,
        offset=offset,
    )
    return {"items": items, "total": total, "limit": limit, "offset": offset}


async def metric_history(conn: Any, *, user_id: str, capture_id: str) -> list[dict]:
    return await _repo.metric_history(conn, user_id=user_id, capture_id=capture_id)


async def top_authors(conn: Any, *, user_id: str, platform: str | None = None, limit: int = 20) -> list[dict]:
    return await _repo.top_authors(conn, user_id=user_id, platform=platform, limit=limit)


async def top_hashtags(conn: Any, *, user_id: str, platform: str | None = None, limit: int = 20) -> list[dict]:
    return await _repo.top_hashtags(conn, user_id=user_id, platform=platform, limit=limit)


async def capture_counts(conn: Any, *, user_id: str) -> dict:
    return await _repo.capture_counts(conn, user_id=user_id)
