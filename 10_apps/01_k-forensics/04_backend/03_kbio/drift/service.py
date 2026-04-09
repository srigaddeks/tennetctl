"""kbio drift service.

Provides session drift state with a Valkey-first, DB-fallback lookup pattern.
Cache key: kbio:drift:{sdk_session_id}  TTL: 60 s.
"""
from __future__ import annotations

import importlib
import json
from typing import Any

import asyncpg

_errors = importlib.import_module("01_core.errors")
_valkey_mod = importlib.import_module("01_core.valkey")

from .repository import get_session_drift, get_recent_score_events
from .schemas import DriftState

_CACHE_TTL = 60  # seconds
_CACHE_KEY_PREFIX = "kbio:drift:"


def _cache_key(sdk_session_id: str) -> str:
    return f"{_CACHE_KEY_PREFIX}{sdk_session_id}"


def _build_drift_state(row: dict[str, Any]) -> DriftState:
    """Construct a DriftState from a v_sessions row dict."""
    return DriftState(
        session_id=row.get("sdk_session_id", row.get("id", "")),
        user_hash=row.get("user_hash", ""),
        current_drift_score=float(row.get("current_drift_score", -1.0)),
        confidence=float(row.get("confidence", 0.0)),
        session_trust=row.get("session_trust", "trusted"),
        drift_trend=row.get("drift_trend") or {},
        signal_scores=row.get("signal_scores") or {},
        pulse_count=int(row.get("pulse_count", 0)),
        baseline_quality=row.get("baseline_quality", "insufficient"),
        active=bool(row.get("is_active", True)),
    )


async def get_drift_state(
    conn: asyncpg.Connection, sdk_session_id: str
) -> DriftState:
    """Return the current drift state for a session.

    1. Try Valkey hot cache (kbio:drift:{sdk_session_id}).
    2. On cache miss, query the DB via v_sessions.
    3. Write the DB result back to cache with a 60 s TTL.

    Raises:
        AppError(NOT_FOUND, 404) — if the session does not exist.
    """
    valkey = _valkey_mod.get_client()

    # --- cache hit? ---
    raw = await valkey.get(_cache_key(sdk_session_id))
    if raw:
        try:
            data = json.loads(raw)
            return DriftState(**data)
        except Exception:
            # Corrupted cache entry — fall through to DB.
            pass

    # --- DB fallback ---
    row = await get_session_drift(conn, sdk_session_id)
    if row is None:
        raise _errors.AppError(
            "NOT_FOUND",
            f"Session '{sdk_session_id}' not found.",
            404,
        )

    state = _build_drift_state(row)

    # --- populate cache ---
    try:
        await valkey.setex(
            _cache_key(sdk_session_id),
            _CACHE_TTL,
            state.model_dump_json(),
        )
    except Exception:
        # Non-fatal — cache write failure should never break the response.
        pass

    return state


async def get_drift_trend(
    conn: asyncpg.Connection, sdk_session_id: str, *, limit: int = 20
) -> list[dict[str, Any]]:
    """Return the most recent score events for a session (newest first).

    Uses sdk_session_id to resolve the internal session_id first.

    Raises:
        AppError(NOT_FOUND, 404) — if the session does not exist.
    """
    row = await get_session_drift(conn, sdk_session_id)
    if row is None:
        raise _errors.AppError(
            "NOT_FOUND",
            f"Session '{sdk_session_id}' not found.",
            404,
        )

    session_id: str = row.get("id", sdk_session_id)
    return await get_recent_score_events(conn, session_id, limit=limit)
