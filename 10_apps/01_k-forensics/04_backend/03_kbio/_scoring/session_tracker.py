"""Session trend tracking and CUSUM changepoint detection.

Maintains a sliding window of drift scores per session and computes:
- Slope (OLS on last 10 batches)
- Acceleration (change in slope)
- CUSUM changepoint detection for session takeover
"""

from __future__ import annotations

import math
from typing import Any


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
        { slope, acceleration, mean, stdev, count }
    """
    if len(drift_history) < 2:
        return {
            "slope": 0.0,
            "acceleration": 0.0,
            "mean": drift_history[0] if drift_history else 0.0,
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

    # Acceleration: slope of the last 3 slopes (computed from overlapping windows)
    acceleration = 0.0
    if len(drift_history) >= 6:
        slopes = []
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
                s = (sub_n * sub_sum_xy - sub_sum_x * sub_sum_y) / sub_denom if sub_denom != 0 else 0.0
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


def detect_changepoint(
    drift_history: list[float],
    *,
    baseline_count: int = 5,
    h_multiplier: float = 4.0,
) -> dict[str, Any]:
    """CUSUM changepoint detection for session takeover.

    Uses the first `baseline_count` scores as the reference distribution.
    Detects if cumulative deviation exceeds h = h_multiplier * baseline_stdev.

    Returns:
        { detected: bool, cusum_value: float, threshold: float, baseline_mean: float }
    """
    if len(drift_history) < baseline_count + 1:
        return {
            "detected": False,
            "cusum_value": 0.0,
            "threshold": 0.0,
            "baseline_mean": 0.0,
        }

    baseline = drift_history[:baseline_count]
    baseline_mean = sum(baseline) / len(baseline)
    baseline_var = sum((x - baseline_mean) ** 2 for x in baseline) / len(baseline)
    baseline_stdev = math.sqrt(baseline_var) if baseline_var > 0 else 0.01

    threshold = h_multiplier * baseline_stdev

    # One-sided CUSUM (detect upward shift = worsening drift)
    cusum = 0.0
    max_cusum = 0.0
    for score in drift_history[baseline_count:]:
        cusum = max(0.0, cusum + (score - baseline_mean) - baseline_stdev * 0.5)
        max_cusum = max(max_cusum, cusum)

    return {
        "detected": max_cusum > threshold,
        "cusum_value": round(max_cusum, 4),
        "threshold": round(threshold, 4),
        "baseline_mean": round(baseline_mean, 4),
    }
