"""User historical stats — Valkey-first, DB fallback.

Cache key : kbio:stats:user:{user_hash}   TTL: 60s
Velocity  : kbio:vel:user:{hash}:sessions_24h   (sliding INCR counter)
            kbio:vel:user:{hash}:failed_challenges_24h
"""
from __future__ import annotations

import json
import logging
from typing import Any

_log = logging.getLogger("kbio.stats.user")

# Valkey TTL for full user stats blob
_USER_STATS_TTL = 60  # seconds — short enough to catch rapid takeover


async def fetch_user_stats(
    user_hash: str,
    valkey: Any,
    conn: Any,
) -> dict[str, Any]:
    """Return historical user stats, from Valkey cache or DB.

    Fields:
        account_age_days        int   — days since account creation
        total_sessions          int   — lifetime session count
        sessions_last_24h       int   — from sliding Valkey counter
        days_since_last_session int   — days of inactivity
        typical_hours           list  — hours [0-23] typically active
        known_countries         list  — ISO-2 country codes seen before
        total_devices           int   — distinct devices registered
        failed_challenges_24h   int   — from sliding Valkey counter
        trust_level             str   — current trust level code
        last_session_country    str   — country from most recent session
    """
    if not user_hash:
        return _empty_user_stats()

    cache_key = f"kbio:stats:user:{user_hash}"

    # 1. Try Valkey cache
    cached = await valkey.get(cache_key)
    if cached:
        stats = json.loads(cached)
        # Overlay live velocity counters (always fresh from Valkey)
        stats["sessions_last_24h"] = await _get_velocity_counter(
            valkey, f"kbio:vel:user:{user_hash}:sessions_24h"
        )
        stats["failed_challenges_24h"] = await _get_velocity_counter(
            valkey, f"kbio:vel:user:{user_hash}:failed_challenges_24h"
        )
        return stats

    # 2. DB fallback
    stats = await _fetch_user_stats_from_db(user_hash, conn)

    # Overlay velocity counters even on DB fetch (counter is source of truth)
    stats["sessions_last_24h"] = await _get_velocity_counter(
        valkey, f"kbio:vel:user:{user_hash}:sessions_24h"
    )
    stats["failed_challenges_24h"] = await _get_velocity_counter(
        valkey, f"kbio:vel:user:{user_hash}:failed_challenges_24h"
    )

    # Cache the DB result (minus live counters — those come from Valkey always)
    cacheable = {**stats}
    await valkey.set(cache_key, json.dumps(cacheable, default=str), ex=_USER_STATS_TTL)

    return stats


async def increment_user_counters(user_hash: str, valkey: Any) -> None:
    """Increment sliding-window counters after a successful ingest.

    Uses Valkey INCR + EXPIRE.  The key expires at the end of the 24h window.
    This is a fire-and-forget operation — errors are logged, not raised.
    """
    if not user_hash:
        return
    try:
        sessions_key = f"kbio:vel:user:{user_hash}:sessions_24h"
        pipe = valkey.pipeline()
        pipe.incr(sessions_key)
        pipe.expire(sessions_key, 86400)  # 24h rolling
        await pipe.execute()
    except Exception as exc:  # noqa: BLE001
        _log.warning("Failed to increment user velocity counters: %s", exc)


async def increment_failed_challenge(user_hash: str, valkey: Any) -> None:
    """Increment failed challenge counter (24h window)."""
    if not user_hash:
        return
    try:
        key = f"kbio:vel:user:{user_hash}:failed_challenges_24h"
        pipe = valkey.pipeline()
        pipe.incr(key)
        pipe.expire(key, 86400)
        await pipe.execute()
    except Exception as exc:  # noqa: BLE001
        _log.warning("Failed to increment challenge counter: %s", exc)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


async def _get_velocity_counter(valkey: Any, key: str) -> int:
    """Read a Valkey INCR counter, returning 0 on miss or error."""
    try:
        val = await valkey.get(key)
        return int(val) if val else 0
    except Exception:  # noqa: BLE001
        return 0


async def _fetch_user_stats_from_db(
    user_hash: str, conn: Any
) -> dict[str, Any]:
    """Query DB for user historical stats."""
    try:
        # Account age and trust level from user profile
        profile_row = await conn.fetchrow(
            """
            SELECT
                EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - p.created_at)) / 86400 AS account_age_days,
                tl.code AS trust_level,
                p.last_seen_country,
                p.total_sessions
            FROM "10_kbio"."30_fct_user_profiles" p
            LEFT JOIN "10_kbio"."03_dim_trust_levels" tl ON tl.id = p.trust_level_id
            WHERE p.user_hash = $1 AND p.deleted_at IS NULL
            LIMIT 1
            """,
            user_hash,
        )

        if not profile_row:
            return _empty_user_stats()

        account_age_days = int(profile_row["account_age_days"] or 0)
        trust_level = profile_row["trust_level"] or "trusted"
        total_sessions = profile_row["total_sessions"] or 0
        last_session_country = profile_row["last_seen_country"] or ""

        # Days since last session
        last_session_row = await conn.fetchrow(
            """
            SELECT EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - MAX(created_at))) / 86400
                AS days_since_last
            FROM "10_kbio"."60_evt_scoring_results"
            WHERE user_hash = $1
            """,
            user_hash,
        )
        days_since_last = int(
            last_session_row["days_since_last"] or 0
        ) if last_session_row else 0

        # Typical active hours (last 30 days)
        hour_rows = await conn.fetch(
            """
            SELECT DISTINCT EXTRACT(HOUR FROM created_at)::int AS h
            FROM "10_kbio"."60_evt_scoring_results"
            WHERE user_hash = $1
              AND created_at > CURRENT_TIMESTAMP - INTERVAL '30 days'
            ORDER BY h
            """,
            user_hash,
        )
        typical_hours = [r["h"] for r in hour_rows]

        # Known countries (last 90 days)
        country_rows = await conn.fetch(
            """
            SELECT DISTINCT country_code
            FROM "10_kbio"."60_evt_scoring_results"
            WHERE user_hash = $1
              AND created_at > CURRENT_TIMESTAMP - INTERVAL '90 days'
              AND country_code IS NOT NULL AND country_code != ''
            """,
            user_hash,
        )
        known_countries = [r["country_code"] for r in country_rows]

        # Total distinct devices
        device_row = await conn.fetchrow(
            """
            SELECT COUNT(DISTINCT device_uuid) AS total_devices
            FROM "10_kbio"."60_evt_scoring_results"
            WHERE user_hash = $1
            """,
            user_hash,
        )
        total_devices = int(device_row["total_devices"] or 0) if device_row else 0

        return {
            "account_age_days": account_age_days,
            "total_sessions": total_sessions,
            "sessions_last_24h": 0,       # always overwritten from Valkey counter
            "days_since_last_session": days_since_last,
            "typical_hours": typical_hours,
            "known_countries": known_countries,
            "total_devices": total_devices,
            "failed_challenges_24h": 0,   # always overwritten from Valkey counter
            "trust_level": trust_level,
            "last_session_country": last_session_country,
        }

    except Exception as exc:  # noqa: BLE001
        _log.warning("DB user stats failed for %s: %s", user_hash, exc)
        return _empty_user_stats()


def _empty_user_stats() -> dict[str, Any]:
    return {
        "account_age_days": 0,
        "total_sessions": 0,
        "sessions_last_24h": 0,
        "days_since_last_session": 0,
        "typical_hours": [],
        "known_countries": [],
        "total_devices": 0,
        "failed_challenges_24h": 0,
        "trust_level": "trusted",
        "last_session_country": "",
    }
