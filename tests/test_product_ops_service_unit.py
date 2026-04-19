"""
Pure unit tests for product_ops.events.service helpers (no DB).
Covers the privacy/UTM helpers that don't touch the catalog or repo.
"""

from __future__ import annotations

from datetime import datetime, timezone
from importlib import import_module
from typing import Any

_service: Any = import_module(
    "backend.02_features.10_product_ops.sub_features.01_events.service"
)


# ── _truncate_ip ────────────────────────────────────────────────────

def test_truncate_ipv4_to_24() -> None:
    assert _service._truncate_ip("203.0.113.42") == "203.0.113.0/24"


def test_truncate_ipv4_zero_octet() -> None:
    assert _service._truncate_ip("10.0.0.1") == "10.0.0.0/24"


def test_truncate_ipv4_malformed_returns_none() -> None:
    assert _service._truncate_ip("not-an-ip") is None


def test_truncate_ipv6_keeps_first_three_hextets() -> None:
    out = _service._truncate_ip("2001:db8:1234:5678:9abc:def0:1234:5678")
    assert out is not None
    assert out.startswith("2001:db8:1234:")
    assert "9abc" not in out
    assert "def0" not in out


def test_truncate_none_returns_none() -> None:
    assert _service._truncate_ip(None) is None


def test_truncate_empty_returns_none() -> None:
    assert _service._truncate_ip("") is None


# ── _strip_tz ───────────────────────────────────────────────────────

def test_strip_tz_from_utc_aware() -> None:
    aware = datetime(2026, 4, 19, 10, 0, 0, tzinfo=timezone.utc)
    naive = _service._strip_tz(aware)
    assert naive.tzinfo is None
    assert naive == datetime(2026, 4, 19, 10, 0, 0)


def test_strip_tz_already_naive_unchanged() -> None:
    naive_in = datetime(2026, 4, 19, 10, 0, 0)
    naive_out = _service._strip_tz(naive_in)
    assert naive_out is naive_in or naive_out == naive_in


# ── _extract_utm_from_url ───────────────────────────────────────────

def test_extract_utm_full_set() -> None:
    url = "https://example.com/landing?utm_source=twitter&utm_medium=social&utm_campaign=launch&utm_term=ai&utm_content=hero"
    utm = _service._extract_utm_from_url(url)
    assert utm == {
        "source": "twitter",
        "medium": "social",
        "campaign": "launch",
        "term": "ai",
        "content": "hero",
    }


def test_extract_utm_partial() -> None:
    url = "https://example.com/x?utm_source=twitter&utm_campaign=launch"
    utm = _service._extract_utm_from_url(url)
    assert utm["source"] == "twitter"
    assert utm["campaign"] == "launch"
    assert utm["medium"] is None


def test_extract_utm_no_query_string() -> None:
    utm = _service._extract_utm_from_url("https://example.com/landing")
    assert all(v is None for v in utm.values())


def test_extract_utm_none_input() -> None:
    utm = _service._extract_utm_from_url(None)
    assert all(v is None for v in utm.values())


def test_extract_utm_malformed_url_returns_nones() -> None:
    # parse_qs is forgiving — empty result on broken input, doesn't raise.
    utm = _service._extract_utm_from_url("not://a-real-url@@")
    assert all(v is None for v in utm.values())
