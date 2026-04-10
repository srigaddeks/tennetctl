"""kbio signal catalog repository.

Reads from the in-memory Python signal registry. No DB queries.
"""
from __future__ import annotations
import importlib


def list_signals(
    *, limit: int, offset: int,
    category: str | None = None, tag: str | None = None,
) -> tuple[list[dict], int]:
    """Return paginated signal definitions from the registry."""
    _signals = importlib.import_module("03_kbio._signals._registry")
    all_sigs = list(_signals.get_all_signals().values())

    # Filter
    if category:
        all_sigs = [s for s in all_sigs if s["category"] == category]
    if tag:
        all_sigs = [s for s in all_sigs if tag in s["tags"]]

    total = len(all_sigs)
    # Sort by severity desc, then code asc
    all_sigs.sort(key=lambda s: (-s["severity"], s["code"]))
    page = all_sigs[offset:offset + limit]

    # Strip function from output
    return [_strip_function(s) for s in page], total


def get_signal_by_code(code: str) -> dict | None:
    _signals = importlib.import_module("03_kbio._signals._registry")
    sig = _signals.get_signal(code)
    if sig is None:
        return None
    return _strip_function(sig)


def _strip_function(sig: dict) -> dict:
    """Remove the function reference from signal defs for serialization."""
    return {k: v for k, v in sig.items() if k != "function"}
