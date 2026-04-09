"""kbio trust service.

Manages trusted entities with Valkey-first caching.

Cache keys:
  kbio:trust:{user_hash}   TTL 900 s  — serialised TrustProfileData
"""
from __future__ import annotations

import importlib
import json
import uuid
from typing import Any, Optional

import asyncpg

_errors = importlib.import_module("01_core.errors")
_valkey_mod = importlib.import_module("01_core.valkey")

from .repository import (
    create_trusted_entity,
    deactivate_trusted_entity,
    get_trust_profile as repo_get_trust_profile,
    get_trusted_entity,
    is_entity_trusted as repo_is_entity_trusted,
    upsert_trust_attr,
)
from .schemas import TrustProfileData, TrustedEntityData

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_CACHE_TTL = 900  # 15 minutes
_CACHE_KEY_PREFIX = "kbio:trust:"

# Valid entity types — kept as a constant for input validation.
_VALID_ENTITY_TYPES = frozenset({"device", "ip_address", "location", "network"})


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _cache_key(user_hash: str) -> str:
    return f"{_CACHE_KEY_PREFIX}{user_hash}"


def _row_to_entity(row: dict[str, Any]) -> TrustedEntityData:
    """Convert a v_trusted_entities row dict to a TrustedEntityData model."""
    return TrustedEntityData(
        id=str(row["id"]),
        user_hash=str(row.get("user_hash", "")),
        entity_type=str(row.get("entity_type", "")),
        entity_value=str(row.get("entity_value", "")),
        trust_reason=row.get("trust_reason"),
        trusted_by=row.get("trusted_by"),
        expires_at=str(row["expires_at"]) if row.get("expires_at") else None,
        is_active=bool(row.get("is_active", True)),
        created_at=str(row["created_at"]) if row.get("created_at") else None,
    )


def _build_trust_profile(
    user_hash: str, rows: list[dict[str, Any]]
) -> TrustProfileData:
    """Group entity rows by entity_type into a TrustProfileData."""
    trusted_devices: list[TrustedEntityData] = []
    trusted_ips: list[TrustedEntityData] = []
    trusted_locations: list[TrustedEntityData] = []
    trusted_networks: list[TrustedEntityData] = []

    for row in rows:
        entity = _row_to_entity(row)
        etype = entity.entity_type
        if etype == "device":
            trusted_devices.append(entity)
        elif etype == "ip_address":
            trusted_ips.append(entity)
        elif etype == "location":
            trusted_locations.append(entity)
        elif etype == "network":
            trusted_networks.append(entity)

    return TrustProfileData(
        user_hash=user_hash,
        trusted_devices=trusted_devices,
        trusted_ips=trusted_ips,
        trusted_locations=trusted_locations,
        trusted_networks=trusted_networks,
    )


async def _invalidate_cache(user_hash: str) -> None:
    """Delete the Valkey cache entry for a user's trust profile."""
    valkey = _valkey_mod.get_client()
    try:
        await valkey.delete(_cache_key(user_hash))
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def get_trust_profile(
    conn: asyncpg.Connection, user_hash: str
) -> TrustProfileData:
    """Return the full trust profile for a user.

    1. Try Valkey cache (kbio:trust:{user_hash}, TTL 900 s).
    2. On miss, query v_trusted_entities and group by type.
    3. Write result back to cache.

    An empty profile (no entities) is valid and returned with empty lists.

    Raises:
        AppError(INTERNAL_ERROR, 500) — on unexpected failure.
    """
    valkey = _valkey_mod.get_client()

    # --- cache hit? ---
    try:
        raw = await valkey.get(_cache_key(user_hash))
        if raw:
            data = json.loads(raw)
            return TrustProfileData(**data)
    except Exception:
        pass

    # --- DB fallback ---
    rows = await repo_get_trust_profile(conn, user_hash)
    profile = _build_trust_profile(user_hash, rows)

    # --- populate cache ---
    try:
        await valkey.setex(
            _cache_key(user_hash),
            _CACHE_TTL,
            profile.model_dump_json(),
        )
    except Exception:
        pass

    return profile


async def create_trusted_entity_svc(
    conn: asyncpg.Connection,
    *,
    user_hash: str,
    entity_type: str,
    entity_value: str,
    trust_reason: str,
    expires_at: Optional[str],
    actor_id: str,
) -> TrustedEntityData:
    """Create a new trusted entity and invalidate the user's trust cache.

    The entity_type_id is resolved from dim_entity_types via the
    kbio_trusted_entity + entity_type subtype convention.

    Raises:
        AppError(VALIDATION_ERROR, 422) — unknown entity_type.
        AppError(INTERNAL_ERROR, 500)   — unexpected DB failure.
    """
    if entity_type not in _VALID_ENTITY_TYPES:
        raise _errors.AppError(
            "VALIDATION_ERROR",
            f"Unknown entity_type '{entity_type}'. "
            f"Must be one of: {', '.join(sorted(_VALID_ENTITY_TYPES))}.",
            422,
        )

    entity_id = str(uuid.uuid4())

    try:
        # Resolve entity_type_id inline — relies on a dim row with
        # code = 'kbio_trusted_entity_{entity_type}'.
        entity_type_id = await conn.fetchval(
            """
            SELECT id FROM "10_kbio"."06_dim_entity_types"
            WHERE code = $1 LIMIT 1
            """,
            f"kbio_trusted_entity_{entity_type}",
        )
        if entity_type_id is None:
            # Fall back to generic trusted_entity type if subtype not registered.
            entity_type_id = await conn.fetchval(
                """
                SELECT id FROM "10_kbio"."06_dim_entity_types"
                WHERE code = 'kbio_trusted_entity' LIMIT 1
                """,
            )

        await create_trusted_entity(
            conn,
            entity_id=entity_id,
            user_hash=user_hash,
            entity_type_id=str(entity_type_id) if entity_type_id else entity_id,
            actor_id=actor_id,
        )

        # Store core attributes in EAV.
        for attr_code, value in [
            ("entity_type", entity_type),
            ("entity_value", entity_value),
            ("trust_reason", trust_reason),
            ("trusted_by", actor_id),
        ]:
            await upsert_trust_attr(
                conn,
                entity_id=entity_id,
                attr_code=attr_code,
                value=value,
                actor_id=actor_id,
            )

        if expires_at:
            await upsert_trust_attr(
                conn,
                entity_id=entity_id,
                attr_code="expires_at",
                value=expires_at,
                actor_id=actor_id,
            )

    except _errors.AppError:
        raise
    except Exception as exc:
        raise _errors.AppError(
            "INTERNAL_ERROR",
            f"Failed to create trusted entity: {exc}",
            500,
        ) from exc

    await _invalidate_cache(user_hash)

    row = await get_trusted_entity(conn, entity_id)
    if row is None:
        # Fallback: return a synthetic data object from the inputs.
        return TrustedEntityData(
            id=entity_id,
            user_hash=user_hash,
            entity_type=entity_type,
            entity_value=entity_value,
            trust_reason=trust_reason,
            trusted_by=actor_id,
            expires_at=expires_at,
            is_active=True,
        )
    return _row_to_entity(row)


async def revoke_trusted_entity(
    conn: asyncpg.Connection,
    entity_id: str,
    *,
    actor_id: str,
) -> None:
    """Soft-delete a trusted entity and invalidate the user's trust cache.

    Raises:
        AppError(NOT_FOUND, 404) — entity does not exist or already deleted.
    """
    row = await get_trusted_entity(conn, entity_id)
    if row is None:
        raise _errors.AppError(
            "NOT_FOUND",
            f"Trusted entity '{entity_id}' not found.",
            404,
        )

    user_hash: str = str(row.get("user_hash", ""))

    await deactivate_trusted_entity(conn, entity_id, actor_id=actor_id)
    await _invalidate_cache(user_hash)


async def is_trusted(
    conn: asyncpg.Connection,
    user_hash: str,
    entity_type: str,
    entity_value: str,
) -> bool:
    """Quick check whether a specific entity is trusted for a user.

    Tries the Valkey cache first; falls back to a point-in-time DB query.

    Returns True if trusted, False otherwise.
    """
    valkey = _valkey_mod.get_client()

    # Fast cache path — deserialise full profile and scan in memory.
    try:
        raw = await valkey.get(_cache_key(user_hash))
        if raw:
            data = json.loads(raw)
            profile = TrustProfileData(**data)
            bucket_map: dict[str, list[TrustedEntityData]] = {
                "device": profile.trusted_devices,
                "ip_address": profile.trusted_ips,
                "location": profile.trusted_locations,
                "network": profile.trusted_networks,
            }
            bucket = bucket_map.get(entity_type, [])
            return any(
                e.entity_value == entity_value and e.is_active
                for e in bucket
            )
    except Exception:
        pass

    # DB fallback.
    return await repo_is_entity_trusted(conn, user_hash, entity_type, entity_value)
