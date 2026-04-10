"""Signal context enrichment — parallel Valkey + DB stat pre-fetch.

Runs user_stats, device_stats, and network_stats concurrently via
asyncio.gather() then merges them into the signal evaluation context.

This is the ONLY I/O that happens before signal evaluation.
Signal functions are pure Python — they only read from the returned ctx.
"""
from __future__ import annotations

import asyncio
from typing import Any

from ._user import fetch_user_stats
from ._device import fetch_device_stats
from ._network import fetch_network_stats


async def enrich_signal_context(
    ctx: dict[str, Any],
    *,
    user_hash: str,
    device_uuid: str,
    ip_address: str,
    valkey: Any,
    conn: Any,
) -> dict[str, Any]:
    """Enrich signal evaluation context with real historical stats.

    Runs all three stat lookups concurrently via asyncio.gather().
    Expected latency: <1ms Valkey hit, <5ms DB fallback.

    Args:
        ctx:        Base signal context from _build_signal_context()
        user_hash:  User identifier
        device_uuid: Device identifier
        ip_address: Client IP
        valkey:     Valkey client
        conn:       DB connection (asyncpg)

    Returns:
        New dict with ctx base + enriched user/device/network namespaces.
        Never mutates ctx.
    """
    user_stats, device_stats, network_stats = await asyncio.gather(
        fetch_user_stats(user_hash, valkey, conn),
        fetch_device_stats(device_uuid, valkey, conn),
        fetch_network_stats(ip_address, valkey, conn),
    )

    # Build enriched user namespace (merge with existing ctx.user)
    existing_user = ctx.get("user", {})
    enriched_user = {
        **existing_user,
        # Historical
        "account_age_days": user_stats["account_age_days"],
        "total_sessions": user_stats["total_sessions"],
        "sessions_last_24h": user_stats["sessions_last_24h"],
        "days_since_last_session": user_stats["days_since_last_session"],
        "typical_hours": user_stats["typical_hours"],
        "known_countries": user_stats["known_countries"],
        "total_devices": user_stats["total_devices"],
        "failed_challenges_24h": user_stats["failed_challenges_24h"],
        "trust_level": user_stats["trust_level"],
        "last_session_country": user_stats["last_session_country"],
    }

    # Build enriched device namespace (merge with existing ctx.device)
    existing_device = ctx.get("device", {})
    enriched_device = {
        **existing_device,
        "age_days": device_stats["age_days"],
        "session_count": device_stats["session_count"],
        "sessions_last_24h": device_stats["sessions_last_24h"],
        "user_count": device_stats["user_count"],
        "is_trusted": device_stats["is_trusted"],
        "is_emulator": device_stats["is_emulator"],
        "fingerprint_drift": device_stats["fingerprint_drift"],
        "platform": device_stats["platform"],
        # Derived
        "is_new": device_stats["session_count"] < 2,
        "is_multi_user": device_stats["user_count"] > 1,
    }

    # Build enriched network namespace (merge + check impossible travel)
    existing_network = ctx.get("network", {})
    current_country = existing_network.get("country", "")
    known_countries = user_stats["known_countries"]
    last_country = user_stats["last_session_country"]

    enriched_network = {
        **existing_network,
        # Override with real reputation data where available
        "is_vpn": (
            network_stats["is_vpn"]
            or existing_network.get("is_vpn", False)
        ),
        "is_tor": (
            network_stats["is_tor"]
            or existing_network.get("is_tor", False)
        ),
        "is_proxy": (
            network_stats["is_proxy"]
            or existing_network.get("is_proxy", False)
        ),
        "is_datacenter": (
            network_stats["is_datacenter"]
            or existing_network.get("is_datacenter", False)
        ),
        "is_residential_proxy": network_stats["is_residential_proxy"],
        "ip_reputation_score": network_stats["ip_reputation_score"],
        "ip_sessions_1h": network_stats["ip_sessions_1h"],
        "ip_users_1h": network_stats["ip_users_1h"],
        "ip_sessions_24h": network_stats["ip_sessions_24h"],
        "asn": network_stats["asn"] or existing_network.get("asn", ""),
        # Derived from historical comparison
        "is_new_country": (
            bool(current_country)
            and bool(known_countries)
            and current_country not in known_countries
        ),
        "known_countries": known_countries,
        # Impossible travel: if last country differs and it's a new session
        # The actual speed calculation requires timestamps; signal fn does that.
        "last_session_country": last_country,
    }

    return {
        **ctx,
        "user": enriched_user,
        "device": enriched_device,
        "network": enriched_network,
    }
