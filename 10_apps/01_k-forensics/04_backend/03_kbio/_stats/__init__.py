"""Valkey-backed historical stats service for kbio signal evaluation.

Provides three parallel-fetched stat bundles:
  - user_stats   — account age, session counts, typical hours, known countries
  - device_stats — device age, session count, multi-user indicator
  - network_stats — IP velocity counters (sliding window via Valkey INCR)

All three expose:
  fetch_*_stats(key, valkey, conn) -> dict   (Valkey-first, DB fallback, cached)
  increment_*_counters(key, valkey)          (fire-and-forget INCR with TTL)

Design principles:
  - Signal functions are pure Python — they read from ctx, never do I/O.
  - ALL I/O happens here, before signal evaluation, via asyncio.gather().
  - Valkey sliding-window counters give sub-millisecond real-time velocity.
  - DB fallback runs only on cache miss (first session or after TTL expiry).
  - TTLs are intentionally short to avoid stale data for fraud detection:
      user_stats: 60s, device_stats: 120s, network_stats: 30s
"""
from __future__ import annotations

from ._user import fetch_user_stats, increment_user_counters
from ._device import fetch_device_stats, increment_device_counters
from ._network import fetch_network_stats, increment_network_counters
from ._context import enrich_signal_context

__all__ = [
    "fetch_user_stats",
    "increment_user_counters",
    "fetch_device_stats",
    "increment_device_counters",
    "fetch_network_stats",
    "increment_network_counters",
    "enrich_signal_context",
]
