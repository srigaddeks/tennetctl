"""Network / IP velocity stats — Valkey sliding-window counters.

For network stats we prioritise real-time velocity over historical DB data.
IP velocity (sessions per hour, distinct users per IP) is computed entirely
from Valkey INCR counters — no DB needed for the hot path.

Cache key : kbio:stats:net:{ip}   TTL: 30s  (very short — IP data is volatile)
Velocity  : kbio:vel:ip:{ip}:sessions_1h    (INCR, 3600s expiry)
            kbio:vel:ip:{ip}:users_1h       (HyperLogLog PF for unique users)
            kbio:vel:ip:{ip}:sessions_24h   (INCR, 86400s expiry)
"""
from __future__ import annotations

import json
import logging
from typing import Any

_log = logging.getLogger("kbio.stats.network")

_NET_STATS_TTL = 30  # seconds — IP risk data is highly volatile


async def fetch_network_stats(
    ip_address: str,
    valkey: Any,
    conn: Any,
) -> dict[str, Any]:
    """Return network / IP velocity stats.

    Fields:
        ip_sessions_1h      int   — sessions from this IP in last hour (Valkey INCR)
        ip_users_1h         int   — distinct users from this IP (HyperLogLog)
        ip_sessions_24h     int   — sessions from this IP in last 24h
        is_vpn              bool  — from batch context (passed through)
        is_tor              bool  — from batch context
        is_proxy            bool  — from batch context
        is_datacenter       bool  — from batch context
        is_residential_proxy bool — from IP reputation data if available
        ip_reputation_score float — threat score from IP reputation cache
        asn                 str   — autonomous system number
        country             str   — ISO-2 country
        city                str   — city name
    """
    if not ip_address or ip_address in ("", "127.0.0.1", "::1"):
        return _empty_network_stats()

    # Velocity counters are always fresh — don't cache them in the blob
    ip_sessions_1h = await _get_counter(
        valkey, f"kbio:vel:ip:{ip_address}:sessions_1h"
    )
    ip_sessions_24h = await _get_counter(
        valkey, f"kbio:vel:ip:{ip_address}:sessions_24h"
    )
    ip_users_1h = await _get_pfcount(
        valkey, f"kbio:vel:ip:{ip_address}:users_1h"
    )

    # Reputation data (cached, rarely changes)
    rep_key = f"kbio:stats:net:{ip_address}"
    cached = await valkey.get(rep_key)
    if cached:
        rep_data = json.loads(cached)
    else:
        rep_data = await _fetch_ip_reputation(ip_address, conn)
        await valkey.set(
            rep_key, json.dumps(rep_data, default=str), ex=_NET_STATS_TTL
        )

    return {
        "ip_sessions_1h": ip_sessions_1h,
        "ip_users_1h": ip_users_1h,
        "ip_sessions_24h": ip_sessions_24h,
        "is_vpn": rep_data.get("is_vpn", False),
        "is_tor": rep_data.get("is_tor", False),
        "is_proxy": rep_data.get("is_proxy", False),
        "is_datacenter": rep_data.get("is_datacenter", False),
        "is_residential_proxy": rep_data.get("is_residential_proxy", False),
        "ip_reputation_score": rep_data.get("ip_reputation_score", 0.0),
        "asn": rep_data.get("asn", ""),
        "country": rep_data.get("country", ""),
        "city": rep_data.get("city", ""),
    }


async def increment_network_counters(
    ip_address: str, user_hash: str, valkey: Any
) -> None:
    """Increment IP velocity counters after each ingest. Fire-and-forget.

    - sessions_1h: INCR + EXPIRE 3600
    - sessions_24h: INCR + EXPIRE 86400
    - users_1h: PFADD (HyperLogLog) + EXPIRE 3600
    """
    if not ip_address or ip_address in ("", "127.0.0.1", "::1"):
        return
    try:
        sessions_1h_key = f"kbio:vel:ip:{ip_address}:sessions_1h"
        sessions_24h_key = f"kbio:vel:ip:{ip_address}:sessions_24h"
        users_1h_key = f"kbio:vel:ip:{ip_address}:users_1h"

        pipe = valkey.pipeline()
        pipe.incr(sessions_1h_key)
        pipe.expire(sessions_1h_key, 3600)
        pipe.incr(sessions_24h_key)
        pipe.expire(sessions_24h_key, 86400)
        if user_hash:
            pipe.pfadd(users_1h_key, user_hash)
            pipe.expire(users_1h_key, 3600)
        await pipe.execute()
    except Exception as exc:  # noqa: BLE001
        _log.warning("Failed to increment network velocity counters: %s", exc)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


async def _get_counter(valkey: Any, key: str) -> int:
    try:
        val = await valkey.get(key)
        return int(val) if val else 0
    except Exception:  # noqa: BLE001
        return 0


async def _get_pfcount(valkey: Any, key: str) -> int:
    """Get HyperLogLog cardinality estimate."""
    try:
        return int(await valkey.pfcount(key) or 0)
    except Exception:  # noqa: BLE001
        return 0


async def _fetch_ip_reputation(ip_address: str, conn: Any) -> dict[str, Any]:
    """Query IP reputation from kbio dim table (pre-loaded threat intel)."""
    try:
        row = await conn.fetchrow(
            """
            SELECT
                is_vpn, is_tor, is_proxy, is_datacenter,
                is_residential_proxy, threat_score, asn,
                country_code, city
            FROM "10_kbio"."20_dim_ip_reputation"
            WHERE ip_address = $1
              AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
            LIMIT 1
            """,
            ip_address,
        )

        if not row:
            return _empty_reputation()

        return {
            "is_vpn": bool(row["is_vpn"]),
            "is_tor": bool(row["is_tor"]),
            "is_proxy": bool(row["is_proxy"]),
            "is_datacenter": bool(row["is_datacenter"]),
            "is_residential_proxy": bool(row["is_residential_proxy"]),
            "ip_reputation_score": float(row["threat_score"] or 0.0),
            "asn": row["asn"] or "",
            "country": row["country_code"] or "",
            "city": row["city"] or "",
        }

    except Exception as exc:  # noqa: BLE001
        _log.debug("IP reputation DB miss for %s: %s", ip_address, exc)
        return _empty_reputation()


def _empty_reputation() -> dict[str, Any]:
    return {
        "is_vpn": False,
        "is_tor": False,
        "is_proxy": False,
        "is_datacenter": False,
        "is_residential_proxy": False,
        "ip_reputation_score": 0.0,
        "asn": "",
        "country": "",
        "city": "",
    }


def _empty_network_stats() -> dict[str, Any]:
    return {
        "ip_sessions_1h": 0,
        "ip_users_1h": 0,
        "ip_sessions_24h": 0,
        "is_vpn": False,
        "is_tor": False,
        "is_proxy": False,
        "is_datacenter": False,
        "is_residential_proxy": False,
        "ip_reputation_score": 0.0,
        "asn": "",
        "country": "",
        "city": "",
    }
