"""kprotect policy_selections service — CRUD + cache invalidation."""

from __future__ import annotations

import importlib
import uuid
from typing import Any

_repo = importlib.import_module("02_features.policy_selections.repository")
_errors_mod = importlib.import_module("01_core.errors")
_valkey_mod = importlib.import_module("01_core.valkey")

AppError = _errors_mod.AppError


def _cache_client():
    return _valkey_mod.get_client()


async def _invalidate_policy_set_cache(org_id: str) -> None:
    """Invalidate all policy-set cache keys for this org."""
    try:
        client = _cache_client()
        pattern = f"kp:policyset:{org_id}:*"
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


async def list_selections(
    conn: object,
    org_id: str,
    *,
    limit: int,
    offset: int,
) -> dict:
    items = await _repo.list_selections(conn, org_id, limit=limit, offset=offset)
    total = await _repo.count_selections(conn, org_id)
    return {"items": items, "total": total, "limit": limit, "offset": offset}


async def get_selection(conn: object, selection_id: str) -> dict:
    row = await _repo.get_selection(conn, selection_id)
    if row is None:
        raise AppError("SELECTION_NOT_FOUND", f"Policy selection '{selection_id}' not found.", 404)
    return row


async def create_selection(
    conn: object,
    *,
    org_id: str,
    predefined_policy_code: str | None,
    priority: int,
    config_overrides: dict[str, Any] | None,
    notes: str | None,
    policy_category: str | None,
    policy_name: str | None,
    threat_type_code: str | None = None,
    signal_overrides: dict[str, Any] | None = None,
    action_override: str | None = None,
    actor_id: str,
) -> dict:
    # At least one of predefined_policy_code or threat_type_code is required
    if not predefined_policy_code and not threat_type_code:
        raise AppError(
            "VALIDATION_ERROR",
            "Either 'predefined_policy_code' or 'threat_type_code' is required.",
            400,
        )

    # Validate threat_type_code against kbio registry
    if threat_type_code:
        _threats_registry = importlib.import_module("03_kbio._threats._registry")
        if not _threats_registry.get_threat_type(threat_type_code):
            raise AppError("NOT_FOUND", f"Threat type '{threat_type_code}' not found.", 404)

    selection_id = str(uuid.uuid4())

    async with conn.transaction():  # type: ignore[union-attr]
        await _repo.create_selection(
            conn,
            selection_id=selection_id,
            org_id=org_id,
            predefined_policy_code=predefined_policy_code or "",
            priority=priority,
            actor_id=actor_id,
        )
        # Store copied-from-kbio metadata as EAV attrs
        if policy_category is not None:
            await _repo.upsert_selection_attr(
                conn,
                selection_id=selection_id,
                attr_code="policy_category",
                value=policy_category,
                actor_id=actor_id,
            )
        if policy_name is not None:
            await _repo.upsert_selection_attr(
                conn,
                selection_id=selection_id,
                attr_code="policy_name",
                value=policy_name,
                actor_id=actor_id,
            )
        if config_overrides is not None:
            await _repo.upsert_selection_attr(
                conn,
                selection_id=selection_id,
                attr_code="config_overrides",
                value=config_overrides,
                actor_id=actor_id,
            )
        if notes is not None:
            await _repo.upsert_selection_attr(
                conn,
                selection_id=selection_id,
                attr_code="notes",
                value=notes,
                actor_id=actor_id,
            )
        if threat_type_code is not None:
            await _repo.upsert_selection_attr(
                conn,
                selection_id=selection_id,
                attr_code="threat_type_code",
                value=threat_type_code,
                actor_id=actor_id,
            )
        if signal_overrides is not None:
            await _repo.upsert_selection_attr(
                conn,
                selection_id=selection_id,
                attr_code="signal_overrides",
                value=signal_overrides,
                actor_id=actor_id,
            )
        if action_override is not None:
            await _repo.upsert_selection_attr(
                conn,
                selection_id=selection_id,
                attr_code="action_override",
                value=action_override,
                actor_id=actor_id,
            )

    await _invalidate_policy_set_cache(org_id)
    return await _repo.get_selection(conn, selection_id)


async def patch_selection(
    conn: object,
    selection_id: str,
    *,
    priority: int | None,
    config_overrides: dict[str, Any] | None,
    notes: str | None,
    is_active: bool | None,
    threat_type_code: str | None = None,
    signal_overrides: dict[str, Any] | None = None,
    action_override: str | None = None,
    actor_id: str,
) -> dict:
    existing = await _repo.get_selection(conn, selection_id)
    if existing is None:
        raise AppError("SELECTION_NOT_FOUND", f"Policy selection '{selection_id}' not found.", 404)

    # Validate threat_type_code against kbio registry
    if threat_type_code is not None:
        _threats_registry = importlib.import_module("03_kbio._threats._registry")
        if not _threats_registry.get_threat_type(threat_type_code):
            raise AppError("NOT_FOUND", f"Threat type '{threat_type_code}' not found.", 404)

    async with conn.transaction():  # type: ignore[union-attr]
        await _repo.patch_selection(
            conn,
            selection_id,
            priority=priority,
            is_active=is_active,
            actor_id=actor_id,
        )
        if config_overrides is not None:
            await _repo.upsert_selection_attr(
                conn,
                selection_id=selection_id,
                attr_code="config_overrides",
                value=config_overrides,
                actor_id=actor_id,
            )
        if notes is not None:
            await _repo.upsert_selection_attr(
                conn,
                selection_id=selection_id,
                attr_code="notes",
                value=notes,
                actor_id=actor_id,
            )
        if threat_type_code is not None:
            await _repo.upsert_selection_attr(
                conn,
                selection_id=selection_id,
                attr_code="threat_type_code",
                value=threat_type_code,
                actor_id=actor_id,
            )
        if signal_overrides is not None:
            await _repo.upsert_selection_attr(
                conn,
                selection_id=selection_id,
                attr_code="signal_overrides",
                value=signal_overrides,
                actor_id=actor_id,
            )
        if action_override is not None:
            await _repo.upsert_selection_attr(
                conn,
                selection_id=selection_id,
                attr_code="action_override",
                value=action_override,
                actor_id=actor_id,
            )

    org_id = existing["org_id"]
    await _invalidate_policy_set_cache(org_id)
    return await _repo.get_selection(conn, selection_id)


async def delete_selection(
    conn: object,
    selection_id: str,
    *,
    actor_id: str,
) -> None:
    existing = await _repo.get_selection(conn, selection_id)
    if existing is None:
        raise AppError("SELECTION_NOT_FOUND", f"Policy selection '{selection_id}' not found.", 404)

    await _repo.soft_delete_selection(conn, selection_id, actor_id=actor_id)
    org_id = existing["org_id"]
    await _invalidate_policy_set_cache(org_id)
