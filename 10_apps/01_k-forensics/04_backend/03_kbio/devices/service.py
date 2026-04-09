"""kbio devices service.

Manages the device registry: listing, registration, and trust management.
No Valkey caching in V1 — device lists are low-frequency reads.
"""
from __future__ import annotations

import importlib
import uuid
from typing import Any

import asyncpg

_errors = importlib.import_module("01_core.errors")

from .repository import (
    count_devices_by_user,
    get_device_by_id,
    get_device_by_uuid,
    link_user_device,
    list_devices_by_user,
    upsert_device,
    upsert_device_attr,
)
from .schemas import DeviceData, DeviceListData


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _row_to_device_data(row: dict[str, Any]) -> DeviceData:
    """Construct a DeviceData from a v_devices row dict."""
    return DeviceData(
        id=str(row["id"]),
        device_uuid=str(row.get("device_uuid", "")),
        trusted=bool(row.get("trusted", False)),
        platform=row.get("platform"),
        first_seen_at=str(row["first_seen_at"]) if row.get("first_seen_at") else None,
        last_seen_at=str(row["last_seen_at"]) if row.get("last_seen_at") else None,
        session_count=int(row.get("session_count", 0)),
        fingerprint_match_score=float(row.get("fingerprint_match_score", 0.0)),
        automation_risk=float(row.get("automation_risk", 0.0)),
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def list_devices(
    conn: asyncpg.Connection,
    user_hash: str,
    *,
    limit: int = 20,
    offset: int = 0,
) -> DeviceListData:
    """Return a paginated list of devices for the given user.

    Raises:
        AppError(VALIDATION_ERROR, 422) — if limit/offset are invalid.
    """
    if limit < 1 or limit > 200:
        raise _errors.AppError(
            "VALIDATION_ERROR",
            "limit must be between 1 and 200.",
            422,
        )
    if offset < 0:
        raise _errors.AppError(
            "VALIDATION_ERROR",
            "offset must be >= 0.",
            422,
        )

    rows, total = await asyncpg_gather(
        list_devices_by_user(conn, user_hash, limit=limit, offset=offset),
        count_devices_by_user(conn, user_hash),
    )

    items = [_row_to_device_data(r) for r in rows]
    return DeviceListData(items=items, total=total, limit=limit, offset=offset)


async def get_device(
    conn: asyncpg.Connection, device_id: str
) -> DeviceData:
    """Fetch a single device by ID.

    Raises:
        AppError(NOT_FOUND, 404) — if the device does not exist.
    """
    row = await get_device_by_id(conn, device_id)
    if row is None:
        raise _errors.AppError(
            "NOT_FOUND",
            f"Device '{device_id}' not found.",
            404,
        )
    return _row_to_device_data(row)


async def register_device(
    conn: asyncpg.Connection,
    *,
    device_uuid: str,
    user_hash: str,
    actor_id: str,
) -> DeviceData:
    """Create or update a device and link it to the given user.

    Idempotent: if a device with the same device_uuid already exists, the
    existing record is updated and the user↔device link is ensured.

    Raises:
        AppError(INTERNAL_ERROR, 500) — on unexpected DB failure.
    """
    # Check if device already exists so we can reuse its ID.
    existing = await get_device_by_uuid(conn, device_uuid)
    device_id = existing["id"] if existing else str(uuid.uuid4())

    try:
        await upsert_device(
            conn,
            device_id=device_id,
            device_uuid=device_uuid,
            user_hash=user_hash,
            actor_id=actor_id,
        )
        await link_user_device(
            conn,
            user_hash=user_hash,
            device_id=device_id,
            actor_id=actor_id,
        )
    except Exception as exc:
        raise _errors.AppError(
            "INTERNAL_ERROR",
            f"Failed to register device '{device_uuid}': {exc}",
            500,
        ) from exc

    row = await get_device_by_id(conn, device_id)
    if row is None:
        raise _errors.AppError(
            "INTERNAL_ERROR",
            f"Device '{device_id}' not found after upsert.",
            500,
        )
    return _row_to_device_data(row)


async def update_device_trust(
    conn: asyncpg.Connection,
    device_id: str,
    *,
    trusted: bool,
    reason: str,
    actor_id: str,
) -> DeviceData:
    """Update the trust status of a device.

    Persists the new trust value and the reason as EAV attributes.

    Raises:
        AppError(NOT_FOUND, 404)       — device does not exist.
        AppError(INTERNAL_ERROR, 500)  — unexpected DB failure.
    """
    row = await get_device_by_id(conn, device_id)
    if row is None:
        raise _errors.AppError(
            "NOT_FOUND",
            f"Device '{device_id}' not found.",
            404,
        )

    try:
        await upsert_device_attr(
            conn,
            device_id=device_id,
            attr_code="trusted",
            value="true" if trusted else "false",
            actor_id=actor_id,
        )
        await upsert_device_attr(
            conn,
            device_id=device_id,
            attr_code="trust_reason",
            value=reason,
            actor_id=actor_id,
        )
    except Exception as exc:
        raise _errors.AppError(
            "INTERNAL_ERROR",
            f"Failed to update trust for device '{device_id}': {exc}",
            500,
        ) from exc

    updated_row = await get_device_by_id(conn, device_id)
    if updated_row is None:
        raise _errors.AppError(
            "INTERNAL_ERROR",
            f"Device '{device_id}' not found after update.",
            500,
        )
    return _row_to_device_data(updated_row)


# ---------------------------------------------------------------------------
# asyncpg does not support asyncio.gather — run sequentially
# ---------------------------------------------------------------------------

async def asyncpg_gather(coro1, coro2):  # type: ignore[no-untyped-def]
    """Run two coroutines sequentially and return both results.

    asyncpg connections are not safe to use concurrently on the same conn
    object, so we run them in series rather than asyncio.gather.
    """
    result1 = await coro1
    result2 = await coro2
    return result1, result2
