"""Session trend tracking and CUSUM changepoint detection — V2.

Maintains a sliding window of drift scores per session and computes:

- Slope (OLS on last N batches).
- Acceleration (change in slope).
- CUSUM changepoint detection for session takeover.
- Full session timeline summary (V2).
"""
from __future__ import annotations

import math
from typing import Any

from ._math import clamp


# ---------------------------------------------------------------------------
# Trend — OLS slope + acceleration
# ---------------------------------------------------------------------------

def compute_trend(
    drift_history: list[float],
    *,
    window_size: int = 10,
) -> dict[str, Any]:
    """Compute session drift trend from recent scores.

    Args:
        drift_history: List of drift scores in chronological order.
        window_size: Number of recent scores to use for OLS.

    Returns:
        ``{ slope, acceleration, mean, stdev, count }``
    """
    if len(drift_history) < 2:
        return {
            "slope": 0.0,
            "acceleration": 0.0,
            "mean": round(drift_history[0], 4) if drift_history else 0.0,
            "stdev": 0.0,
            "count": len(drift_history),
        }

    recent = drift_history[-window_size:]
    n = len(recent)

    # OLS slope: slope = (n*Σxy - Σx*Σy) / (n*Σx² - (Σx)²)
    sum_x = sum(range(n))
    sum_y = sum(recent)
    sum_xy = sum(i * y for i, y in enumerate(recent))
    sum_x2 = sum(i * i for i in range(n))

    denom = n * sum_x2 - sum_x * sum_x
    slope = (n * sum_xy - sum_x * sum_y) / denom if denom != 0 else 0.0

    mean = sum_y / n
    variance = sum((y - mean) ** 2 for y in recent) / n if n > 1 else 0.0
    stdev = math.sqrt(variance)

    # Acceleration: slope of the last 3 slopes (overlapping windows)
    acceleration = 0.0
    if len(drift_history) >= 6:
        slopes: list[float] = []
        for i in range(min(3, len(drift_history) - window_size + 1)):
            start = max(0, len(drift_history) - window_size - i)
            end = len(drift_history) - i
            sub = drift_history[start:end]
            if len(sub) >= 2:
                sub_n = len(sub)
                sub_sum_x = sum(range(sub_n))
                sub_sum_y = sum(sub)
                sub_sum_xy = sum(j * y for j, y in enumerate(sub))
                sub_sum_x2 = sum(j * j for j in range(sub_n))
                sub_denom = sub_n * sub_sum_x2 - sub_sum_x * sub_sum_x
                s = (
                    (sub_n * sub_sum_xy - sub_sum_x * sub_sum_y) / sub_denom
                    if sub_denom != 0
                    else 0.0
                )
                slopes.append(s)
        if len(slopes) >= 2:
            acceleration = slopes[0] - slopes[-1]

    return {
        "slope": round(slope, 6),
        "acceleration": round(acceleration, 6),
        "mean": round(mean, 4),
        "stdev": round(stdev, 4),
        "count": n,
    }


# ---------------------------------------------------------------------------
# CUSUM changepoint detection
# ---------------------------------------------------------------------------

def detect_changepoint(
    drift_history: list[float],
    *,
    baseline_count: int = 5,
    h_multiplier: float = 4.0,
) -> dict[str, Any]:
    """CUSUM changepoint detection for session takeover.

    Uses the first *baseline_count* scores as the reference distribution.
    Detects if cumulative deviation exceeds ``h = h_multiplier * baseline_stdev``.

    Returns:
        ``{ detected, cusum_value, threshold, baseline_mean, changepoint_batch_seq }``

        ``changepoint_batch_seq`` is the index (0-based, relative to
        *drift_history*) of the batch where the CUSUM first exceeded the
        threshold, or ``-1`` if no changepoint was detected.
    """
    if len(drift_history) < baseline_count + 1:
        return {
            "detected": False,
            "cusum_value": 0.0,
            "threshold": 0.0,
            "baseline_mean": 0.0,
            "changepoint_batch_seq": -1,
        }

    baseline = drift_history[:baseline_count]
    baseline_mean = sum(baseline) / len(baseline)
    baseline_var = sum((x - baseline_mean) ** 2 for x in baseline) / len(baseline)
    baseline_stdev = math.sqrt(baseline_var) if baseline_var > 0 else 0.01

    threshold = h_multiplier * baseline_stdev

    # One-sided CUSUM (detect upward shift = worsening drift)
    cusum = 0.0
    max_cusum = 0.0
    changepoint_seq = -1
    for idx, score in enumerate(drift_history[baseline_count:], start=baseline_count):
        cusum = max(0.0, cusum + (score - baseline_mean) - baseline_stdev * 0.5)
        if cusum > max_cusum:
            max_cusum = cusum
        if changepoint_seq == -1 and cusum > threshold:
            changepoint_seq = idx

    return {
        "detected": max_cusum > threshold,
        "cusum_value": round(max_cusum, 4),
        "threshold": round(threshold, 4),
        "baseline_mean": round(baseline_mean, 4),
        "changepoint_batch_seq": changepoint_seq,
    }


# ---------------------------------------------------------------------------
# Session timeline summary (V2)
# ---------------------------------------------------------------------------

def compute_session_timeline(
    drift_history: list[float],
    batch_seq: int,
) -> dict[str, Any]:
    """Build a complete session timeline summary.

    Combines trend analysis, changepoint detection, and descriptive
    statistics into a single dict suitable for the scoring pipeline
    output.

    Args:
        drift_history: Full drift history for the session so far.
        batch_seq: Current batch sequence number (0-based).

    Returns::

        {
            "drift_current": float,
            "drift_mean": float,
            "drift_max": float,
            "drift_stdev": float,
            "batches_processed": int,
            "trend": {
                "direction": "increasing"|"decreasing"|"stable"|"volatile",
                "slope": float,
                "acceleration": float,
                "changepoint_detected": bool,
                "changepoint_batch_seq": int | -1,
            },
            "stability_score": float,
        }
    """
    n = len(drift_history)

    # --- Descriptive statistics ------------------------------------------
    drift_current = round(drift_history[-1], 4) if drift_history else 0.0
    drift_mean = round(sum(drift_history) / n, 4) if n > 0 else 0.0
    drift_max = round(max(drift_history), 4) if drift_history else 0.0

    if n > 1:
        variance = sum((x - (sum(drift_history) / n)) ** 2 for x in drift_history) / n
        drift_stdev = round(math.sqrt(variance), 4)
    else:
        variance = 0.0
        drift_stdev = 0.0

    # --- Trend -----------------------------------------------------------
    trend = compute_trend(drift_history)

    # --- Changepoint -----------------------------------------------------
    changepoint = detect_changepoint(drift_history)

    # --- Direction classification ----------------------------------------
    slope = trend["slope"]
    stdev = trend["stdev"]

    if n < 3:
        direction = "stable"
    elif stdev > 0.10 and abs(slope) < stdev * 0.5:
        direction = "volatile"
    elif slope > 0.005:
        direction = "increasing"
    elif slope < -0.005:
        direction = "decreasing"
    else:
        direction = "stable"

    # --- Stability score -------------------------------------------------
    # 0.0 = extremely unstable, 1.0 = rock solid
    stability = 1.0 / (1.0 + 5.0 * variance)
    stability_score = round(clamp(stability, 0.0, 1.0), 4)

    return {
        "drift_current": drift_current,
        "drift_mean": drift_mean,
        "drift_max": drift_max,
        "drift_stdev": drift_stdev,
        "batches_processed": batch_seq + 1,
        "trend": {
            "direction": direction,
            "slope": trend["slope"],
            "acceleration": trend["acceleration"],
            "changepoint_detected": changepoint["detected"],
            "changepoint_batch_seq": changepoint["changepoint_batch_seq"],
        },
        "stability_score": stability_score,
    }
