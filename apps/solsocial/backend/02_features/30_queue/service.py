"""Queue service."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_repo = import_module("apps.solsocial.backend.02_features.30_queue.repository")
_channels_repo = import_module("apps.solsocial.backend.02_features.10_channels.repository")
_errors = import_module("apps.solsocial.backend.01_core.errors")


async def get_queue_for_channel(conn: Any, *, channel_id: str, workspace_id: str) -> dict:
    queue = await _repo.get_by_channel(conn, channel_id=channel_id, workspace_id=workspace_id)
    if not queue:
        raise _errors.NotFoundError(f"No queue for channel {channel_id}.")
    slots = await _repo.list_slots(conn, queue_id=queue["id"])
    queue["slots"] = slots
    return queue


async def upsert_queue(
    conn: Any,
    *,
    org_id: str,
    workspace_id: str,
    channel_id: str,
    timezone: str,
    slots: list[dict],
) -> dict:
    channel = await _channels_repo.get(
        conn, channel_id=channel_id, workspace_id=workspace_id,
    )
    if not channel:
        raise _errors.ValidationError(f"Channel {channel_id} not in workspace.")
    queue = await _repo.upsert_queue(
        conn, channel_id=channel_id, workspace_id=workspace_id,
        org_id=org_id, timezone=timezone,
    )
    await _repo.replace_slots(conn, queue_id=queue["id"], slots=slots)
    return await get_queue_for_channel(
        conn, channel_id=channel_id, workspace_id=workspace_id,
    )
