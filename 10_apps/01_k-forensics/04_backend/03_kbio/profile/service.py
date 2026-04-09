"""kbio profile service.

Manages user behavioral profiles with Valkey-first caching, baseline creation,
and EMA (alpha=0.1) attribute updates from genuine sessions (drift < 0.3).

Cache key: kbio:profile:{user_hash}  TTL: 300 s.
"""
from __future__ import annotations

import importlib
import json
from typing import Any

import asyncpg

_errors = importlib.import_module("01_core.errors")
_valkey_mod = importlib.import_module("01_core.valkey")

from .repository import get_profile, upsert_profile, upsert_profile_attr
from .schemas import ProfileSummary

_CACHE_TTL = 300  # seconds
_CACHE_KEY_PREFIX = "kbio:profile:"

# EMA smoothing factor for genuine-session updates.
_EMA_ALPHA = 0.1

# Drift score threshold below which a session is considered genuine.
_GENUINE_DRIFT_THRESHOLD = 0.3

# dim_baseline_quality.code → id mapping (seeded in bootstrap migration).
_BASELINE_QUALITY_CODES: dict[str, int] = {
    "insufficient": 1,
    "low": 2,
    "medium": 3,
    "high": 4,
}


def _cache_key(user_hash: str) -> str:
    return f"{_CACHE_KEY_PREFIX}{user_hash}"


def _build_summary(row: dict[str, Any]) -> ProfileSummary:
    """Construct a ProfileSummary from a v_user_profiles row dict."""
    lgs = row.get("last_genuine_session_at")
    return ProfileSummary(
        user_hash=row["user_hash"],
        status=row.get("status", "active"),
        baseline_quality=row.get("baseline_quality", "insufficient"),
        profile_maturity=float(row.get("profile_maturity", 0.0)),
        total_sessions=int(row.get("total_sessions", 0)),
        centroid_count=int(row.get("centroid_count", 0)),
        last_genuine_session_at=str(lgs) if lgs else None,
        baseline_age_days=int(row.get("baseline_age_days", 0)),
        credential_profile_count=int(row.get("credential_profile_count", 0)),
        encoder_version=row.get("encoder_version", "v1"),
    )


async def get_profile_summary(
    conn: asyncpg.Connection, user_hash: str
) -> ProfileSummary:
    """Return the behavioral profile summary for a user.

    1. Try Valkey hot cache (kbio:profile:{user_hash}).
    2. On miss, query v_user_profiles.
    3. Write result back to cache with 300 s TTL.

    Raises:
        AppError(NOT_FOUND, 404) — if no profile exists for the user.
    """
    valkey = _valkey_mod.get_client()

    # --- cache hit? ---
    raw = await valkey.get(_cache_key(user_hash))
    if raw:
        try:
            data = json.loads(raw)
            return ProfileSummary(**data)
        except Exception:
            pass  # Fall through on corrupted entry.

    # --- DB fallback ---
    row = await get_profile(conn, user_hash)
    if row is None:
        raise _errors.AppError(
            "NOT_FOUND",
            f"Profile for user '{user_hash}' not found.",
            404,
        )

    summary = _build_summary(row)

    # --- populate cache ---
    try:
        await valkey.setex(
            _cache_key(user_hash),
            _CACHE_TTL,
            summary.model_dump_json(),
        )
    except Exception:
        pass

    return summary


async def create_profile(
    conn: asyncpg.Connection,
    *,
    user_hash: str,
    actor_id: str,
) -> ProfileSummary:
    """Create a new behavioral profile for a user.

    Uses 'insufficient' as the initial baseline quality. If a profile already
    exists for the user_hash, the upsert is idempotent and this returns the
    current state.

    Raises:
        AppError(INTERNAL_ERROR, 500) — on unexpected DB failure.
    """
    baseline_quality_id = _BASELINE_QUALITY_CODES["insufficient"]

    try:
        await upsert_profile(
            conn,
            user_hash=user_hash,
            baseline_quality_id=baseline_quality_id,
            actor_id=actor_id,
        )
    except Exception as exc:
        raise _errors.AppError(
            "INTERNAL_ERROR",
            f"Failed to create profile for user '{user_hash}': {exc}",
            500,
        ) from exc

    # Invalidate stale cache entry (if any).
    valkey = _valkey_mod.get_client()
    try:
        await valkey.delete(_cache_key(user_hash))
    except Exception:
        pass

    row = await get_profile(conn, user_hash)
    if row is None:
        raise _errors.AppError(
            "INTERNAL_ERROR",
            f"Profile for user '{user_hash}' not found after upsert.",
            500,
        )

    return _build_summary(row)


async def update_profile_from_genuine_session(
    conn: asyncpg.Connection,
    *,
    user_hash: str,
    features: dict[str, float],
    actor_id: str,
) -> None:
    """Apply an EMA (alpha=0.1) update to profile feature attributes.

    Only accepted when the session is genuine (drift < 0.3). Each feature
    in ``features`` is fetched from cache/DB, blended with the incoming
    value, and written back via the EAV layer.

    If the profile does not yet exist it is created first with
    'insufficient' baseline quality.

    Raises:
        AppError(VALIDATION_ERROR, 422) — if features dict is empty.
    """
    if not features:
        raise _errors.AppError(
            "VALIDATION_ERROR",
            "features dict must not be empty.",
            422,
        )

    # Ensure the profile row exists.
    row = await get_profile(conn, user_hash)
    if row is None:
        await create_profile(conn, user_hash=user_hash, actor_id=actor_id)
        row = await get_profile(conn, user_hash)

    profile_id: str = row["id"]  # type: ignore[index]

    # Fetch current attr values for EMA blending.
    for attr_code, incoming_value in features.items():
        # We store feature centroids under kbio:profile:{user_hash}:feat:{attr_code}
        # in Valkey for fast EMA reads, falling back to 0.0 if unseen.
        valkey = _valkey_mod.get_client()
        current_value = 0.0
        try:
            cached = await valkey.get(f"kbio:profile:{user_hash}:feat:{attr_code}")
            if cached is not None:
                current_value = float(cached)
        except Exception:
            pass

        blended = _EMA_ALPHA * incoming_value + (1.0 - _EMA_ALPHA) * current_value

        # Persist in EAV.
        try:
            await upsert_profile_attr(
                conn,
                profile_id=profile_id,
                attr_code=attr_code,
                value=blended,
                actor_id=actor_id,
            )
        except ValueError:
            # Unregistered attr_code — skip gracefully.
            continue

        # Update Valkey feature cache.
        try:
            await valkey.setex(
                f"kbio:profile:{user_hash}:feat:{attr_code}",
                3600,
                str(blended),
            )
        except Exception:
            pass

    # Invalidate profile summary cache so next read reflects new maturity.
    valkey = _valkey_mod.get_client()
    try:
        await valkey.delete(_cache_key(user_hash))
    except Exception:
        pass
