"""kprotect signal_selections service -- CRUD + cache invalidation."""

from __future__ import annotations

import importlib
import uuid
from typing import Any

_repo = importlib.import_module("02_features.signal_selections.repository")
_errors_mod = importlib.import_module("01_core.errors")
_valkey_mod = importlib.import_module("01_core.valkey")

# kbio signal catalog for validation
_kbio_signals = importlib.import_module("03_kbio._signals._registry")

AppError = _errors_mod.AppError


def _cache_client():
    return _valkey_mod.get_client()


async def _invalidate_signal_selection_cache(org_id: str) -> None:
    """Invalidate all signal-selection cache keys for this org."""
    try:
        client = _cache_client()
        pattern = f"kp:signalsel:{org_id}:*"
        cursor = 0
        while True:
            cursor, keys = await client.scan(cursor, match=pattern, count=100)
            if keys:
                await client.delete(*keys)
            if cursor == 0:
                break
    except Exception:
        # Cache invalidation errors must never break mutations
        pass


def _validate_signal_code(signal_code: str) -> None:
    """Ensure signal_code exists in the kbio signal registry."""
    sig = _kbio_signals.get_signal(signal_code)
    if sig is None:
        raise AppError(
            "INVALID_SIGNAL_CODE",
            f"Signal code '{signal_code}' not found in kbio registry.",
            400,
        )


async def list_selections(
    conn: object,
    org_id: str,
    *,
    limit: int,
    offset: int,
) -> dict:
    items = await _repo.list_signal_selections(conn, org_id, limit=limit, offset=offset)
    total = await _repo.count_signal_selections(conn, org_id)
    return {"items": items, "total": total, "limit": limit, "offset": offset}


async def get_selection(conn: object, selection_id: str) -> dict:
    row = await _repo.get_signal_selection(conn, selection_id)
    if row is None:
        raise AppError("SELECTION_NOT_FOUND", f"Signal selection '{selection_id}' not found.", 404)
    return row


async def create_selection(
    conn: object,
    *,
    org_id: str,
    signal_code: str,
    config_overrides: dict[str, Any] | None,
    notes: str | None,
    actor_id: str,
) -> dict:
    _validate_signal_code(signal_code)

    selection_id = str(uuid.uuid4())

    async with conn.transaction():  # type: ignore[union-attr]
        await _repo.create_signal_selection(
            conn,
            selection_id=selection_id,
            org_id=org_id,
            actor_id=actor_id,
        )
        await _repo.upsert_signal_selection_attr(
            conn,
            selection_id=selection_id,
            attr_code="signal_code",
            value=signal_code,
            actor_id=actor_id,
        )
        if config_overrides is not None:
            await _repo.upsert_signal_selection_attr(
                conn,
                selection_id=selection_id,
                attr_code="config_overrides",
                value=config_overrides,
                actor_id=actor_id,
            )
        if notes is not None:
            await _repo.upsert_signal_selection_attr(
                conn,
                selection_id=selection_id,
                attr_code="notes",
                value=notes,
                actor_id=actor_id,
            )

    await _invalidate_signal_selection_cache(org_id)
    return await _repo.get_signal_selection(conn, selection_id)


async def update_selection(
    conn: object,
    selection_id: str,
    *,
    config_overrides: dict[str, Any] | None,
    notes: str | None,
    is_active: bool | None,
    actor_id: str,
) -> dict:
    existing = await _repo.get_signal_selection(conn, selection_id)
    if existing is None:
        raise AppError("SELECTION_NOT_FOUND", f"Signal selection '{selection_id}' not found.", 404)

    async with conn.transaction():  # type: ignore[union-attr]
        await _repo.patch_signal_selection(
            conn,
            selection_id,
            is_active=is_active,
            actor_id=actor_id,
        )
        if config_overrides is not None:
            await _repo.upsert_signal_selection_attr(
                conn,
                selection_id=selection_id,
                attr_code="config_overrides",
                value=config_overrides,
                actor_id=actor_id,
            )
        if notes is not None:
            await _repo.upsert_signal_selection_attr(
                conn,
                selection_id=selection_id,
                attr_code="notes",
                value=notes,
                actor_id=actor_id,
            )

    org_id = existing["org_id"]
    await _invalidate_signal_selection_cache(org_id)
    return await _repo.get_signal_selection(conn, selection_id)


async def delete_selection(
    conn: object,
    selection_id: str,
    *,
    actor_id: str,
) -> None:
    existing = await _repo.get_signal_selection(conn, selection_id)
    if existing is None:
        raise AppError("SELECTION_NOT_FOUND", f"Signal selection '{selection_id}' not found.", 404)

    await _repo.soft_delete_signal_selection(conn, selection_id, actor_id=actor_id)
    org_id = existing["org_id"]
    await _invalidate_signal_selection_cache(org_id)


async def bulk_create(
    conn: object,
    *,
    org_id: str,
    signal_codes: list[str],
    config_overrides: dict[str, dict[str, Any]] | None,
    actor_id: str,
) -> list[dict]:
    """Create multiple signal selections at once."""
    # Validate all signal codes upfront
    for code in signal_codes:
        _validate_signal_code(code)

    created_ids: list[str] = []

    async with conn.transaction():  # type: ignore[union-attr]
        for code in signal_codes:
            selection_id = str(uuid.uuid4())
            created_ids.append(selection_id)

            await _repo.create_signal_selection(
                conn,
                selection_id=selection_id,
                org_id=org_id,
                actor_id=actor_id,
            )
            await _repo.upsert_signal_selection_attr(
                conn,
                selection_id=selection_id,
                attr_code="signal_code",
                value=code,
                actor_id=actor_id,
            )
            # Per-signal config overrides
            code_overrides = (config_overrides or {}).get(code)
            if code_overrides is not None:
                await _repo.upsert_signal_selection_attr(
                    conn,
                    selection_id=selection_id,
                    attr_code="config_overrides",
                    value=code_overrides,
                    actor_id=actor_id,
                )

    await _invalidate_signal_selection_cache(org_id)

    results = []
    for sid in created_ids:
        row = await _repo.get_signal_selection(conn, sid)
        if row is not None:
            results.append(row)
    return results
