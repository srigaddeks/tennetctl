"""Post service — business logic including the publish pipeline."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_repo = import_module("apps.solsocial.backend.02_features.20_posts.repository")
_channels_repo = import_module("apps.solsocial.backend.02_features.10_channels.repository")
_errors = import_module("apps.solsocial.backend.01_core.errors")


async def list_posts(
    conn: Any, *, workspace_id: str, status: str | None, channel_id: str | None,
    limit: int, offset: int,
) -> list[dict]:
    return await _repo.list_posts(
        conn, workspace_id=workspace_id, status=status, channel_id=channel_id,
        limit=limit, offset=offset,
    )


async def get_post(conn: Any, *, post_id: str, workspace_id: str) -> dict:
    row = await _repo.get(conn, post_id=post_id, workspace_id=workspace_id)
    if not row:
        raise _errors.NotFoundError(f"Post {post_id} not found.")
    return row


async def create_post(
    conn: Any,
    *,
    org_id: str,
    workspace_id: str,
    channel_id: str,
    body: str,
    media: list[dict],
    link: str | None,
    status: str,
    scheduled_at: Any,
    created_by: str,
) -> dict:
    channel = await _channels_repo.get(conn, channel_id=channel_id, workspace_id=workspace_id)
    if not channel:
        raise _errors.ValidationError(f"Channel {channel_id} not in workspace.")
    status_id = await _repo.resolve_status_id(conn, status)
    if status_id is None:
        raise _errors.ValidationError(f"Unknown status: {status}")
    if status == "scheduled" and scheduled_at is None:
        raise _errors.ValidationError("scheduled_at required when status='scheduled'.")
    post_id = await _repo.insert(
        conn,
        org_id=org_id, workspace_id=workspace_id, channel_id=channel_id,
        status_id=status_id, body=body, media=media, link=link,
        scheduled_at=scheduled_at, created_by=created_by,
    )
    row = await _repo.get(conn, post_id=post_id, workspace_id=workspace_id)
    return row or {}


async def patch_post(
    conn: Any,
    *,
    post_id: str,
    workspace_id: str,
    body: str | None,
    media: list[dict] | None,
    link: str | None,
    status: str | None,
    scheduled_at: Any,
    scheduled_at_set: bool,
) -> dict:
    existing = await _repo.get(conn, post_id=post_id, workspace_id=workspace_id)
    if not existing:
        raise _errors.NotFoundError(f"Post {post_id} not found.")
    if existing["status"] in ("publishing", "published"):
        raise _errors.ConflictError(
            f"Cannot edit a post in status={existing['status']}.",
        )
    status_id = None
    if status is not None:
        status_id = await _repo.resolve_status_id(conn, status)
        if status_id is None:
            raise _errors.ValidationError(f"Unknown status: {status}")
    await _repo.update(
        conn,
        post_id=post_id, workspace_id=workspace_id,
        body=body, media=media, link=link,
        status_id=status_id,
        scheduled_at=scheduled_at, scheduled_at_set=scheduled_at_set,
    )
    updated = await _repo.get(conn, post_id=post_id, workspace_id=workspace_id)
    return updated or existing


async def delete_post(conn: Any, *, post_id: str, workspace_id: str) -> None:
    ok = await _repo.soft_delete(conn, post_id=post_id, workspace_id=workspace_id)
    if not ok:
        raise _errors.NotFoundError(f"Post {post_id} not found.")


async def publish_now(
    conn: Any,
    *,
    post_id: str,
    workspace_id: str,
    publisher: Any,
    tennetctl: Any,
    token: str,
) -> dict:
    """Run the publish pipeline: load post → call provider → record result."""
    post = await _repo.get(conn, post_id=post_id, workspace_id=workspace_id)
    if not post:
        raise _errors.NotFoundError(f"Post {post_id} not found.")
    if post["status"] == "published":
        return post
    channel = await _channels_repo.get(
        conn, channel_id=post["channel_id"], workspace_id=workspace_id,
    )
    if not channel:
        raise _errors.ConflictError("Channel gone.")

    status_publishing = await _repo.resolve_status_id(conn, "publishing")
    status_published = await _repo.resolve_status_id(conn, "published")
    status_failed = await _repo.resolve_status_id(conn, "failed")
    assert status_publishing and status_published and status_failed

    # Flip to publishing
    await _repo.update(
        conn, post_id=post_id, workspace_id=workspace_id,
        body=None, media=None, link=None,
        status_id=status_publishing,
        scheduled_at=None, scheduled_at_set=False,
    )

    try:
        result = await publisher.publish(
            tennetctl=tennetctl, token=token, channel=channel, post=post,
        )
        await _repo.mark_published(
            conn,
            post_id=post_id,
            external_post_id=result["external_post_id"],
            external_url=result.get("external_url"),
            status_id_published=status_published,
            org_id=post["org_id"],
            actor_id=post["created_by"],
        )
    except Exception as exc:  # pragma: no cover - wraps arbitrary provider errors
        await _repo.mark_failed(
            conn, post_id=post_id, status_id_failed=status_failed,
            error_code=type(exc).__name__, error_msg=str(exc)[:500],
            org_id=post["org_id"], actor_id=post["created_by"],
        )
        raise _errors.UpstreamError(f"Publish failed: {exc}") from exc
    return await _repo.get(conn, post_id=post_id, workspace_id=workspace_id) or {}
