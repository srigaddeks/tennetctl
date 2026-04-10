"""kbio rolling baseline updater.

Adaptive baseline updates with grace period management.
Ensures behavioral profiles evolve naturally while remaining
resistant to adversarial drift.

Pure computation -- no I/O, no external dependencies beyond stdlib.
"""

from __future__ import annotations

from typing import Any

from . import cluster_manager


# Trust and drift thresholds for genuine session identification
_TRUST_THRESHOLD = 0.70
_DRIFT_THRESHOLD = 0.30

# EMA alpha values
_BASE_ALPHA = 0.10
_FAST_ALPHA = 0.15
_TREND_THRESHOLD = 0.01

# Minimum recent drifts needed for trend detection
_MIN_TREND_SAMPLES = 5

# Grace period settings
_GRACE_SESSIONS = 3


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def update_baseline(
    cluster: dict[str, Any],
    new_embedding: list[float],
    session_trust: float,
    drift_score: float,
    recent_drifts: list[float],
) -> dict[str, Any]:
    """Update cluster baseline with adaptive EMA rate.

    Only updates if session is genuine (trust > 0.70, drift < 0.30).

    Adaptive alpha:
    - Normal: alpha = 0.10
    - Directional trend detected (OLS slope > 0.01 on last 5 genuine): alpha = 0.15

    Returns updated cluster (new object, immutable).
    """
    # Do not update if session is not genuine
    if session_trust < _TRUST_THRESHOLD or drift_score >= _DRIFT_THRESHOLD:
        return dict(cluster)

    alpha = compute_adaptive_alpha(recent_drifts)

    updated = cluster_manager.update_cluster_centroid(
        cluster,
        new_embedding,
        alpha=alpha,
    )

    return updated


def compute_adaptive_alpha(
    recent_drifts: list[float],
    *,
    base_alpha: float = _BASE_ALPHA,
    fast_alpha: float = _FAST_ALPHA,
    trend_threshold: float = _TREND_THRESHOLD,
) -> float:
    """Compute adaptive EMA alpha based on drift trend.

    If last 5 genuine sessions show consistent directional shift,
    increase alpha to adapt faster to genuine behavioral evolution.
    """
    if len(recent_drifts) < _MIN_TREND_SAMPLES:
        return round(base_alpha, 4)

    # Use the last 5 values for trend detection
    tail = recent_drifts[-_MIN_TREND_SAMPLES:]
    slope = _compute_ols_slope(tail)

    if abs(slope) > trend_threshold:
        return round(fast_alpha, 4)

    return round(base_alpha, 4)


def check_grace_period(
    _cluster: dict[str, Any],
    session_count_in_cluster: int,
    *,
    grace_sessions: int = _GRACE_SESSIONS,
) -> dict[str, Any]:
    """Check and manage new-context grace period.

    New clusters get a 3-session grace period where:
    - Maximum verdict is "monitor" (never challenge/block)
    - Drift scores are reported but not escalated

    Returns:
        {
            "in_grace_period": bool,
            "remaining_sessions": int,
            "max_verdict": str,  # "monitor" during grace, None after
        }
    """
    remaining = max(0, grace_sessions - session_count_in_cluster)
    in_grace = remaining > 0

    return {
        "in_grace_period": in_grace,
        "remaining_sessions": remaining,
        "max_verdict": "monitor" if in_grace else None,
    }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _compute_ols_slope(values: list[float]) -> float:
    """OLS slope for trend detection. Pure Python.

    Fits y = a + b*x to the values where x = 0, 1, 2, ...
    Returns the slope b.
    """
    n = len(values)
    if n < 2:
        return 0.0

    # x = 0, 1, 2, ..., n-1
    sum_x = n * (n - 1) / 2.0
    sum_y = sum(values)
    sum_xy = sum(i * values[i] for i in range(n))
    sum_x2 = n * (n - 1) * (2 * n - 1) / 6.0

    denominator = n * sum_x2 - sum_x * sum_x
    if denominator == 0.0:
        return 0.0

    slope = (n * sum_xy - sum_x * sum_y) / denominator
    return round(slope, 4)
