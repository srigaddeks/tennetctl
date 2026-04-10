"""Tests for the _stats Valkey-backed historical stats service.

Tests:
- fetch_user_stats: Valkey cache hit, DB fallback, empty defaults
- fetch_device_stats: Valkey cache hit, DB fallback, empty defaults
- fetch_network_stats: velocity counters + reputation cache
- increment_user_counters: INCR pipeline execution
- increment_device_counters: INCR pipeline execution
- increment_network_counters: INCR + PFADD pipeline execution
- enrich_signal_context: parallel gather, correct namespace merging
"""
from __future__ import annotations

import json
import sys
import types
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Any

import pytest

# ---------------------------------------------------------------------------
# Bootstrap import shims so numeric-prefix dirs resolve without importlib
# ---------------------------------------------------------------------------

def _make_module(name: str, **attrs) -> types.ModuleType:
    m = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(m, k, v)
    return m


# ---------------------------------------------------------------------------
# Import the modules under test after shim setup
# ---------------------------------------------------------------------------

# We need to import the _stats package; it uses relative imports internally,
# which Python resolves fine when _stats is a proper package on the path.
# The test suite runs from the backend dir, so 03_kbio._stats is reachable
# via importlib — but for direct import in tests we add the path manually.

import importlib
_stats_user = importlib.import_module("03_kbio._stats._user")
_stats_device = importlib.import_module("03_kbio._stats._device")
_stats_network = importlib.import_module("03_kbio._stats._network")
_stats_context = importlib.import_module("03_kbio._stats._context")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_valkey(cached: dict[str, str | None] | None = None) -> MagicMock:
    """Return a mock Valkey client with configurable GET responses."""
    valkey = MagicMock()
    _cache = cached or {}

    async def _get(key: str) -> str | None:
        return _cache.get(key)

    async def _set(key: str, val: str, *, ex: int | None = None, nx: bool = False) -> bool:
        return True

    async def _pfcount(key: str) -> int:
        return 0

    valkey.get = _get
    valkey.set = _set
    valkey.pfcount = _pfcount

    # Pipeline mock
    pipe = MagicMock()
    pipe.incr = MagicMock(return_value=pipe)
    pipe.expire = MagicMock(return_value=pipe)
    pipe.pfadd = MagicMock(return_value=pipe)
    pipe.get = MagicMock(return_value=pipe)
    pipe.execute = AsyncMock(return_value=[1, True, 1, True])
    valkey.pipeline = MagicMock(return_value=pipe)

    return valkey


def _make_conn(rows: dict[str, Any] | None = None) -> MagicMock:
    """Return a mock asyncpg connection."""
    conn = MagicMock()
    _rows = rows or {}

    async def _fetchrow(query: str, *args) -> dict | None:
        # Return the first matching row dict based on query content
        for key, row in _rows.items():
            if key in query:
                return row
        return None

    async def _fetch(query: str, *args) -> list:
        for key, rows in _rows.items():
            if key in query and isinstance(rows, list):
                return [MagicMock(**{k: v for k, v in r.items()}) for r in rows]
        return []

    conn.fetchrow = _fetchrow
    conn.fetch = _fetch
    return conn


# ---------------------------------------------------------------------------
# User stats tests
# ---------------------------------------------------------------------------


class TestFetchUserStats:
    """Tests for _user.fetch_user_stats."""

    def test_empty_user_hash_returns_defaults(self):
        result = asyncio.run(
            _stats_user.fetch_user_stats("", MagicMock(), MagicMock())
        )
        assert result["account_age_days"] == 0
        assert result["sessions_last_24h"] == 0
        assert result["known_countries"] == []
        assert result["typical_hours"] == []

    def test_cache_hit_returns_cached_data(self):
        cached_data = {
            "account_age_days": 365,
            "total_sessions": 100,
            "sessions_last_24h": 0,
            "days_since_last_session": 1,
            "typical_hours": [9, 10, 11],
            "known_countries": ["US", "GB"],
            "total_devices": 2,
            "failed_challenges_24h": 0,
            "trust_level": "high",
            "last_session_country": "US",
        }
        valkey = _make_valkey({"kbio:stats:user:abc123": json.dumps(cached_data)})
        conn = _make_conn()

        result = asyncio.run(
            _stats_user.fetch_user_stats("abc123", valkey, conn)
        )
        assert result["account_age_days"] == 365
        assert result["known_countries"] == ["US", "GB"]
        assert result["trust_level"] == "high"
        # sessions_last_24h comes from velocity counter (0 since no counter set)
        assert result["sessions_last_24h"] == 0

    def test_db_fallback_when_cache_miss(self):
        # No cache hit
        valkey = _make_valkey({})
        conn = _make_conn({
            "30_fct_user_profiles": {
                "account_age_days": 90.0,
                "trust_level": "trusted",
                "last_seen_country": "DE",
                "total_sessions": 50,
            }
        })

        result = asyncio.run(
            _stats_user.fetch_user_stats("user_xyz", valkey, conn)
        )
        assert result["account_age_days"] == 90
        assert result["trust_level"] == "trusted"
        assert result["last_session_country"] == "DE"
        assert result["total_sessions"] == 50

    def test_db_error_returns_empty_defaults(self):
        valkey = _make_valkey({})
        # conn.fetchrow raises
        conn = MagicMock()
        conn.fetchrow = AsyncMock(side_effect=Exception("DB down"))
        conn.fetch = AsyncMock(return_value=[])

        result = asyncio.run(
            _stats_user.fetch_user_stats("user_fail", valkey, conn)
        )
        assert result["account_age_days"] == 0
        assert result["trust_level"] == "trusted"

    def test_velocity_counter_overlaid_on_cache(self):
        # Cache has 0 for sessions_last_24h; velocity counter has 5
        cached_data = {
            "account_age_days": 30,
            "total_sessions": 10,
            "sessions_last_24h": 0,
            "days_since_last_session": 0,
            "typical_hours": [],
            "known_countries": [],
            "total_devices": 1,
            "failed_challenges_24h": 0,
            "trust_level": "trusted",
            "last_session_country": "",
        }
        valkey = _make_valkey({
            "kbio:stats:user:vel_user": json.dumps(cached_data),
            "kbio:vel:user:vel_user:sessions_24h": "5",
        })
        conn = _make_conn()

        result = asyncio.run(
            _stats_user.fetch_user_stats("vel_user", valkey, conn)
        )
        assert result["sessions_last_24h"] == 5


# ---------------------------------------------------------------------------
# Device stats tests
# ---------------------------------------------------------------------------


class TestFetchDeviceStats:
    """Tests for _device.fetch_device_stats."""

    def test_empty_device_uuid_returns_defaults(self):
        result = asyncio.run(
            _stats_device.fetch_device_stats("", MagicMock(), MagicMock())
        )
        assert result["age_days"] == 0
        assert result["session_count"] == 0
        assert result["is_trusted"] is False

    def test_cache_hit(self):
        cached = {
            "age_days": 45,
            "session_count": 20,
            "sessions_last_24h": 0,
            "user_count": 1,
            "is_trusted": True,
            "is_emulator": False,
            "fingerprint_drift": 0.1,
            "platform": "web",
            "last_seen_country": "US",
        }
        valkey = _make_valkey({"kbio:stats:device:dev-001": json.dumps(cached)})
        conn = _make_conn()

        result = asyncio.run(
            _stats_device.fetch_device_stats("dev-001", valkey, conn)
        )
        assert result["age_days"] == 45
        assert result["is_trusted"] is True
        assert result["platform"] == "web"

    def test_multi_user_device_flag(self):
        cached = {
            "age_days": 10,
            "session_count": 5,
            "sessions_last_24h": 0,
            "user_count": 3,  # multi-user
            "is_trusted": False,
            "is_emulator": False,
            "fingerprint_drift": 0.0,
            "platform": "android",
            "last_seen_country": "",
        }
        valkey = _make_valkey({"kbio:stats:device:shared-dev": json.dumps(cached)})

        result = asyncio.run(
            _stats_device.fetch_device_stats("shared-dev", valkey, MagicMock())
        )
        assert result["user_count"] == 3


# ---------------------------------------------------------------------------
# Network stats tests
# ---------------------------------------------------------------------------


class TestFetchNetworkStats:
    """Tests for _network.fetch_network_stats."""

    def test_empty_ip_returns_defaults(self):
        result = asyncio.run(
            _stats_network.fetch_network_stats("", MagicMock(), MagicMock())
        )
        assert result["ip_sessions_1h"] == 0
        assert result["is_vpn"] is False

    def test_localhost_returns_defaults(self):
        result = asyncio.run(
            _stats_network.fetch_network_stats("127.0.0.1", MagicMock(), MagicMock())
        )
        assert result["ip_sessions_1h"] == 0

    def test_velocity_counters_read_correctly(self):
        valkey = _make_valkey({
            "kbio:vel:ip:1.2.3.4:sessions_1h": "12",
            "kbio:vel:ip:1.2.3.4:sessions_24h": "150",
        })
        conn = _make_conn()

        result = asyncio.run(
            _stats_network.fetch_network_stats("1.2.3.4", valkey, conn)
        )
        assert result["ip_sessions_1h"] == 12
        assert result["ip_sessions_24h"] == 150

    def test_reputation_cache_used_when_available(self):
        rep_data = {
            "is_vpn": True,
            "is_tor": False,
            "is_proxy": False,
            "is_datacenter": False,
            "is_residential_proxy": False,
            "ip_reputation_score": 0.75,
            "asn": "AS12345",
            "country": "RU",
            "city": "Moscow",
        }
        valkey = _make_valkey({"kbio:stats:net:5.6.7.8": json.dumps(rep_data)})

        result = asyncio.run(
            _stats_network.fetch_network_stats("5.6.7.8", valkey, MagicMock())
        )
        assert result["is_vpn"] is True
        assert result["ip_reputation_score"] == 0.75
        assert result["country"] == "RU"


# ---------------------------------------------------------------------------
# Counter increment tests
# ---------------------------------------------------------------------------


class TestIncrementCounters:
    """Tests for fire-and-forget counter increments."""

    def test_increment_user_counters(self):
        valkey = _make_valkey()
        asyncio.run(_stats_user.increment_user_counters("user_abc", valkey))
        valkey.pipeline().incr.assert_called()

    def test_increment_device_counters(self):
        valkey = _make_valkey()
        asyncio.run(_stats_device.increment_device_counters("dev-123", valkey))
        valkey.pipeline().incr.assert_called()

    def test_increment_network_counters(self):
        valkey = _make_valkey()
        asyncio.run(
            _stats_network.increment_network_counters("10.0.0.1", "user_xyz", valkey)
        )
        valkey.pipeline().incr.assert_called()

    def test_increment_empty_inputs_no_error(self):
        # Empty inputs should not raise, just return early
        valkey = _make_valkey()
        asyncio.run(_stats_user.increment_user_counters("", valkey))
        asyncio.run(_stats_device.increment_device_counters("", valkey))
        asyncio.run(_stats_network.increment_network_counters("", "", valkey))
        # Should complete without error

    def test_increment_error_is_swallowed(self):
        """Errors in counter increments must not propagate (fire-and-forget)."""
        valkey = MagicMock()
        pipe = MagicMock()
        pipe.incr = MagicMock(return_value=pipe)
        pipe.expire = MagicMock(return_value=pipe)
        pipe.execute = AsyncMock(side_effect=Exception("Valkey down"))
        valkey.pipeline = MagicMock(return_value=pipe)

        # Must not raise
        asyncio.run(_stats_user.increment_user_counters("user_fail", valkey))
        asyncio.run(_stats_device.increment_device_counters("dev_fail", valkey))


# ---------------------------------------------------------------------------
# Context enrichment tests
# ---------------------------------------------------------------------------


class TestEnrichSignalContext:
    """Tests for _context.enrich_signal_context."""

    def _base_ctx(self) -> dict:
        return {
            "scores": {"behavioral_drift": 0.3},
            "device": {"is_emulator": False},
            "network": {"ip": "1.2.3.4", "is_vpn": False, "country": "US"},
            "user": {"user_hash": "u1", "user_trust": 0.8},
            "session": {"pulse_count": 10},
        }

    def test_enriched_user_stats_merged(self):
        user_cached = {
            "account_age_days": 180,
            "total_sessions": 50,
            "sessions_last_24h": 3,
            "days_since_last_session": 0,
            "typical_hours": [9, 10, 11],
            "known_countries": ["US"],
            "total_devices": 1,
            "failed_challenges_24h": 0,
            "trust_level": "trusted",
            "last_session_country": "US",
        }
        valkey = _make_valkey({
            "kbio:stats:user:u1": json.dumps(user_cached),
        })
        conn = _make_conn()

        result = asyncio.run(
            _stats_context.enrich_signal_context(
                self._base_ctx(),
                user_hash="u1",
                device_uuid="d1",
                ip_address="1.2.3.4",
                valkey=valkey,
                conn=conn,
            )
        )
        assert result["user"]["account_age_days"] == 180
        assert result["user"]["typical_hours"] == [9, 10, 11]
        assert result["user"]["known_countries"] == ["US"]

    def test_enriched_network_is_new_country(self):
        user_cached = {
            "account_age_days": 100,
            "total_sessions": 20,
            "sessions_last_24h": 1,
            "days_since_last_session": 1,
            "typical_hours": [],
            "known_countries": ["US", "CA"],
            "total_devices": 1,
            "failed_challenges_24h": 0,
            "trust_level": "trusted",
            "last_session_country": "US",
        }
        # Current request from RU — new country
        ctx = {
            **self._base_ctx(),
            "network": {"ip": "5.6.7.8", "is_vpn": False, "country": "RU"},
        }
        valkey = _make_valkey({"kbio:stats:user:u2": json.dumps(user_cached)})
        conn = _make_conn()

        result = asyncio.run(
            _stats_context.enrich_signal_context(
                ctx,
                user_hash="u2",
                device_uuid="d2",
                ip_address="5.6.7.8",
                valkey=valkey,
                conn=conn,
            )
        )
        assert result["network"]["is_new_country"] is True
        assert result["network"]["known_countries"] == ["US", "CA"]

    def test_device_multi_user_flag_set(self):
        device_cached = {
            "age_days": 10,
            "session_count": 5,
            "sessions_last_24h": 0,
            "user_count": 3,
            "is_trusted": False,
            "is_emulator": False,
            "fingerprint_drift": 0.0,
            "platform": "web",
            "last_seen_country": "",
        }
        valkey = _make_valkey({"kbio:stats:device:d3": json.dumps(device_cached)})
        conn = _make_conn()

        result = asyncio.run(
            _stats_context.enrich_signal_context(
                self._base_ctx(),
                user_hash="u3",
                device_uuid="d3",
                ip_address="",
                valkey=valkey,
                conn=conn,
            )
        )
        assert result["device"]["user_count"] == 3
        assert result["device"]["is_multi_user"] is True

    def test_original_ctx_not_mutated(self):
        ctx = self._base_ctx()
        original_user = dict(ctx["user"])
        valkey = _make_valkey({})
        conn = _make_conn()

        result = asyncio.run(
            _stats_context.enrich_signal_context(
                ctx,
                user_hash="u4",
                device_uuid="d4",
                ip_address="",
                valkey=valkey,
                conn=conn,
            )
        )
        # Original ctx must not be mutated
        assert ctx["user"] == original_user
        # Result is a new dict
        assert result is not ctx

    def test_runs_three_fetches_concurrently(self):
        """Verify gather is used (all three fetches complete even if slow)."""
        call_order = []

        async def slow_user(*_):
            call_order.append("user_start")
            await asyncio.sleep(0.01)
            call_order.append("user_end")
            return _stats_user._empty_user_stats()

        async def slow_device(*_):
            call_order.append("device_start")
            await asyncio.sleep(0.005)
            call_order.append("device_end")
            return _stats_device._empty_device_stats()

        async def slow_network(*_):
            call_order.append("net_start")
            await asyncio.sleep(0.001)
            call_order.append("net_end")
            return _stats_network._empty_network_stats()

        with (
            patch.object(_stats_context, "fetch_user_stats", slow_user),
            patch.object(_stats_context, "fetch_device_stats", slow_device),
            patch.object(_stats_context, "fetch_network_stats", slow_network),
        ):
            asyncio.run(
                _stats_context.enrich_signal_context(
                    self._base_ctx(),
                    user_hash="u5",
                    device_uuid="d5",
                    ip_address="1.1.1.1",
                    valkey=MagicMock(),
                    conn=MagicMock(),
                )
            )

        # With gather, all three start before any ends
        assert call_order.index("device_start") < call_order.index("user_end")
        assert call_order.index("net_start") < call_order.index("device_end")
