"""Device historical stats — Valkey-first, DB fallback.

Cache key : kbio:stats:device:{device_uuid}   TTL: 120s
Velocity  : kbio:vel:device:{uuid}:sessions_24h  (sliding INCR counter)

Device data changes slowly (trusted status, age) so a longer TTL is safe.
"""
from __future__ import annotations

import json
import logging
from typing import Any

_log = logging.getLogger("kbio.stats.device")

_DEVICE_STATS_TTL = 120  # seconds


async def fetch_device_stats(
    device_uuid: str,
    valkey: Any,
    conn: Any,
) -> dict[str, Any]:
    """Return device historical stats.

    Fields:
        age_days            int   — days since device first seen
        session_count       int   — total sessions from this device
        sessions_last_24h   int   — from sliding Valkey counter
        user_count          int   — distinct users seen on this device
        is_trusted          bool  — from device trust table
        is_emulator         bool  — emulator/simulator flag
        fingerprint_drift   float — fingerprint change vs initial enrollment
        platform            str   — ios | android | web | desktop
        last_seen_country   str   — most recent country from this device
    """
    if not device_uuid:
        return _empty_device_stats()

    cache_key = f"kbio:stats:device:{device_uuid}"

    cached = await valkey.get(cache_key)
    if cached:
        stats = json.loads(cached)
        stats["sessions_last_24h"] = await _get_counter(
            valkey, f"kbio:vel:device:{device_uuid}:sessions_24h"
        )
        return stats

    stats = await _fetch_device_stats_from_db(device_uuid, conn)
    stats["sessions_last_24h"] = await _get_counter(
        valkey, f"kbio:vel:device:{device_uuid}:sessions_24h"
    )

    await valkey.set(
        cache_key, json.dumps(stats, default=str), ex=_DEVICE_STATS_TTL
    )
    return stats


async def increment_device_counters(device_uuid: str, valkey: Any) -> None:
    """Increment device sliding-window session counter. Fire-and-forget."""
    if not device_uuid:
        return
    try:
        key = f"kbio:vel:device:{device_uuid}:sessions_24h"
        pipe = valkey.pipeline()
        pipe.incr(key)
        pipe.expire(key, 86400)
        await pipe.execute()
    except Exception as exc:  # noqa: BLE001
        _log.warning("Failed to increment device velocity counter: %s", exc)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


async def _get_counter(valkey: Any, key: str) -> int:
    try:
        val = await valkey.get(key)
        return int(val) if val else 0
    except Exception:  # noqa: BLE001
        return 0


async def _fetch_device_stats_from_db(
    device_uuid: str, conn: Any
) -> dict[str, Any]:
    try:
        row = await conn.fetchrow(
            """
            SELECT
                EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - d.created_at)) / 86400 AS age_days,
                d.session_count,
                d.user_count,
                d.is_trusted,
                d.is_emulator,
                d.fingerprint_drift,
                d.platform,
                d.last_seen_country
            FROM "10_kbio"."31_fct_devices" d
            WHERE d.device_uuid = $1 AND d.deleted_at IS NULL
            LIMIT 1
            """,
            device_uuid,
        )

        if not row:
            return _empty_device_stats()

        return {
            "age_days": int(row["age_days"] or 0),
            "session_count": int(row["session_count"] or 0),
            "sessions_last_24h": 0,   # overwritten from Valkey counter
            "user_count": int(row["user_count"] or 1),
            "is_trusted": bool(row["is_trusted"]),
            "is_emulator": bool(row["is_emulator"]),
            "fingerprint_drift": float(row["fingerprint_drift"] or 0.0),
            "platform": row["platform"] or "",
            "last_seen_country": row["last_seen_country"] or "",
        }

    except Exception as exc:  # noqa: BLE001
        _log.warning("DB device stats failed for %s: %s", device_uuid, exc)
        return _empty_device_stats()


def _empty_device_stats() -> dict[str, Any]:
    return {
        "age_days": 0,
        "session_count": 0,
        "sessions_last_24h": 0,
        "user_count": 1,
        "is_trusted": False,
        "is_emulator": False,
        "fingerprint_drift": 0.0,
        "platform": "",
        "last_seen_country": "",
    }
