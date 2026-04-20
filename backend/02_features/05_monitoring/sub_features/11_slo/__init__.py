"""SLO (Service Level Objective) sub-feature.

Operators define SLOs with target attainment (e.g., 99.9%) over a window
(rolling 30d, calendar month, etc.). The platform continuously evaluates
indicator queries (good/total success counts), derives attainment and error
budget remaining, and computes multi-window burn rate (1h, 6h, 24h, 3d).

When a fast-burn or slow-burn threshold is crossed, a synthetic alert is
emitted, reusing the existing alert → incident → escalation chain from Plan 40-03.
"""

from __future__ import annotations

__all__ = [
    "budget",
    "burn_rate",
    "schemas",
    "repository",
    "service",
    "routes",
]
