"""Credential field drift scoring.

Compares credential typing patterns (zone sequences, timing) against
enrolled credential profiles. Used for login/password behavioral verification.

Separate from general drift — uses 64d embedding space vs 128d for general.
"""

from __future__ import annotations

import math
from typing import Any


def score_credential_drift(
    observed: dict[str, Any],
    enrolled: dict[str, Any],
) -> dict[str, float]:
    """Compute credential drift from observed vs enrolled typing patterns.

    Formula:
        cred_drift = 0.4*(1-timing_corr) + 0.3*(1-dwell_corr)
                   + 0.2*(1-hesit_overlap) + 0.1*speed_dev

    Args:
        observed: Credential field features from current batch.
        enrolled: Credential profile from user profile.

    Returns:
        { drift: float, timing_corr: float, dwell_corr: float,
          hesitation_overlap: float, speed_deviation: float }
    """
    if not observed or not enrolled:
        return {"drift": -1.0, "timing_corr": 0.0, "dwell_corr": 0.0,
                "hesitation_overlap": 0.0, "speed_deviation": 0.0}

    # Extract zone sequences
    obs_seq = observed.get("zone_sequence", [])
    enr_seq = enrolled.get("zone_sequence_template", [])

    if not obs_seq or not enr_seq:
        return {"drift": -1.0, "timing_corr": 0.0, "dwell_corr": 0.0,
                "hesitation_overlap": 0.0, "speed_deviation": 0.0}

    # Flight time correlation
    obs_flights = [z.get("flight_ms", 0) for z in obs_seq if "flight_ms" in z]
    enr_flights = [z.get("flight_mean", 0) for z in enr_seq if "flight_mean" in z]
    timing_corr = _pearson(obs_flights, enr_flights)

    # Dwell time correlation
    obs_dwells = [z.get("dwell_ms", 0) for z in obs_seq if "dwell_ms" in z]
    enr_dwells = [z.get("dwell_mean", 0) for z in enr_seq if "dwell_mean" in z]
    dwell_corr = _pearson(obs_dwells, enr_dwells)

    # Hesitation overlap (Jaccard)
    obs_hesitations = set(observed.get("hesitation_points", []))
    enr_hesitations = set(enrolled.get("hesitation_pattern", []))
    hesit_overlap = _jaccard(obs_hesitations, enr_hesitations)

    # Speed deviation
    obs_speed = observed.get("timing_summary", {}).get("flight_mean", 0)
    enr_speed = enrolled.get("timing_stats", {}).get("flight_mean", 0)
    enr_stdev = enrolled.get("timing_stats", {}).get("flight_stdev", 1)
    speed_dev = abs(obs_speed - enr_speed) / max(enr_stdev, 1.0)
    speed_dev = min(1.0, speed_dev / 3.0)  # normalize to 0-1 range

    # Composite drift
    drift = (
        0.4 * (1.0 - max(0.0, timing_corr))
        + 0.3 * (1.0 - max(0.0, dwell_corr))
        + 0.2 * (1.0 - hesit_overlap)
        + 0.1 * speed_dev
    )

    return {
        "drift": round(min(1.0, max(0.0, drift)), 4),
        "timing_corr": round(timing_corr, 4),
        "dwell_corr": round(dwell_corr, 4),
        "hesitation_overlap": round(hesit_overlap, 4),
        "speed_deviation": round(speed_dev, 4),
    }


def _pearson(x: list[float], y: list[float]) -> float:
    """Pearson correlation coefficient. Returns 0.0 if insufficient data."""
    n = min(len(x), len(y))
    if n < 3:
        return 0.0

    x = x[:n]
    y = y[:n]

    mean_x = sum(x) / n
    mean_y = sum(y) / n

    cov = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
    std_x = math.sqrt(sum((xi - mean_x) ** 2 for xi in x))
    std_y = math.sqrt(sum((yi - mean_y) ** 2 for yi in y))

    if std_x == 0 or std_y == 0:
        return 0.0

    return cov / (std_x * std_y)


def _jaccard(a: set, b: set) -> float:
    """Jaccard similarity coefficient."""
    if not a and not b:
        return 1.0  # both empty = identical
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)
