"""Channel service — thin business orchestration."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_repo = import_module("apps.solsocial.backend.02_features.10_channels.repository")
_errors = import_module("apps.solsocial.backend.01_core.errors")


async def list_channels(conn: Any, *, workspace_id: str, limit: int, offset: int) -> list[dict]:
    return await _repo.list_for_workspace(
        conn, workspace_id=workspace_id, limit=limit, offset=offset,
    )


async def get_channel(conn: Any, *, channel_id: str, workspace_id: str) -> dict:
    row = await _repo.get(conn, channel_id=channel_id, workspace_id=workspace_id)
    if not row:
        raise _errors.NotFoundError(f"Channel {channel_id} not found.")
    return row


async def find_by_external_id(
    conn: Any, *, workspace_id: str, provider_code: str, external_id: str,
) -> dict | None:
    """Reconnect lookup: find an existing channel for this (workspace, provider,
    external_id) tuple. Returns None if not found."""
    return await _repo.get_by_external_id(
        conn, workspace_id=workspace_id,
        provider_code=provider_code, external_id=external_id,
    )


async def connect_channel(
    conn: Any,
    *,
    channel_id: str | None = None,
    org_id: str,
    workspace_id: str,
    provider_code: str,
    handle: str,
    display_name: str | None,
    avatar_url: str | None,
    external_id: str | None,
    vault_key: str,
    created_by: str,
) -> dict:
    provider_id = await _repo.resolve_provider_id(conn, provider_code)
    if provider_id is None:
        raise _errors.ValidationError(f"Unknown provider: {provider_code}")
    return await _repo.insert(
        conn,
        channel_id=channel_id,
        org_id=org_id, workspace_id=workspace_id, provider_id=provider_id,
        handle=handle, display_name=display_name, avatar_url=avatar_url,
        external_id=external_id, vault_key=vault_key,
        created_by=created_by,
    )


async def disconnect_channel(conn: Any, *, channel_id: str, workspace_id: str) -> None:
    ok = await _repo.soft_delete(conn, channel_id=channel_id, workspace_id=workspace_id)
    if not ok:
        raise _errors.NotFoundError(f"Channel {channel_id} not found.")


async def patch_channel(
    conn: Any,
    *,
    channel_id: str,
    workspace_id: str,
    display_name: str | None,
    avatar_url: str | None,
) -> dict:
    existing = await _repo.get(conn, channel_id=channel_id, workspace_id=workspace_id)
    if not existing:
        raise _errors.NotFoundError(f"Channel {channel_id} not found.")
    await _repo.update_meta(
        conn, channel_id=channel_id, display_name=display_name, avatar_url=avatar_url,
    )
    updated = await _repo.get(conn, channel_id=channel_id, workspace_id=workspace_id)
    return updated or existing
