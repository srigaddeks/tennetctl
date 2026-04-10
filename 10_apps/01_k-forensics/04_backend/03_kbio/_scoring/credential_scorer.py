"""Credential field drift scoring.

Compares credential typing patterns (zone sequences, timing) against
enrolled credential profiles. Used for login/password behavioral verification.

Separate from general drift -- uses 64d embedding space vs 128d for general.

V2: 6-signal formula with zone sequence similarity, duration deviation,
    and trend deviation.
"""

from __future__ import annotations

from typing import Any

from ._math import jaccard, pearson, sigmoid


def score_credential_drift(
    observed: dict[str, Any],
    enrolled: dict[str, Any],
    *,
    recent_drifts: list[float] | None = None,
    overall_drift_mean: float | None = None,
    overall_drift_stdev: float | None = None,
) -> dict[str, float]:
    """Compute credential drift from observed vs enrolled typing patterns.

    V2 Formula (6 signals):
        cred_drift = 0.35*(1-timing_corr) + 0.20*(1-dwell_corr)
                   + 0.15*(1-zone_sim) + 0.15*(1-hesitation_overlap)
                   + 0.10*duration_sigmoid + 0.05*trend_deviation

    Args:
        observed: Credential field features from current batch.
        enrolled: Credential profile from user profile.
        recent_drifts: Last 5 credential drift scores for trend analysis.
        overall_drift_mean: Long-term mean of credential drifts.
        overall_drift_stdev: Long-term stdev of credential drifts.

    Returns:
        {
            drift: float,
            timing_corr: float,
            dwell_corr: float,
            zone_sequence_similarity: float,
            hesitation_overlap: float,
            duration_deviation: float,
            trend_deviation: float,
        }
    """
    empty_result: dict[str, float] = {
        "drift": -1.0,
        "timing_corr": 0.0,
        "dwell_corr": 0.0,
        "zone_sequence_similarity": 0.0,
        "hesitation_overlap": 0.0,
        "duration_deviation": 0.0,
        "trend_deviation": 0.0,
    }

    if not observed or not enrolled:
        return empty_result

    # Extract zone sequences
    obs_seq = observed.get("zone_sequence", [])
    enr_seq = enrolled.get("zone_sequence_template", [])

    if not obs_seq or not enr_seq:
        return empty_result

    # Signal 1: Flight time correlation (weight 0.35)
    obs_flights = [z.get("flight_ms", 0) for z in obs_seq if "flight_ms" in z]
    enr_flights = [z.get("flight_mean", 0) for z in enr_seq if "flight_mean" in z]
    timing_corr = pearson(obs_flights, enr_flights)

    # Signal 2: Dwell time correlation (weight 0.20)
    obs_dwells = [z.get("dwell_ms", 0) for z in obs_seq if "dwell_ms" in z]
    enr_dwells = [z.get("dwell_mean", 0) for z in enr_seq if "dwell_mean" in z]
    dwell_corr = pearson(obs_dwells, enr_dwells)

    # Signal 3: Zone sequence similarity (weight 0.15)
    # Jaccard on zone ID sets -- if < 0.8, password may have changed
    obs_zone_ids = set(z.get("zone_id") for z in obs_seq if "zone_id" in z)
    enr_zone_ids = set(z.get("zone_id") for z in enr_seq if "zone_id" in z)
    zone_sim = jaccard(obs_zone_ids, enr_zone_ids)

    # Signal 4: Hesitation overlap (weight 0.15)
    obs_hesitations = set(observed.get("hesitation_points", []))
    enr_hesitations = set(enrolled.get("hesitation_pattern", []))
    hesit_overlap = jaccard(obs_hesitations, enr_hesitations)

    # Signal 5: Duration deviation (weight 0.10)
    # sigmoid((|obs_duration - enr_duration| / enr_stdev) - 1.0)
    obs_duration = observed.get("timing_summary", {}).get("total_duration_ms", 0)
    enr_duration = enrolled.get("timing_stats", {}).get("total_duration_mean", 0)
    enr_duration_stdev = enrolled.get("timing_stats", {}).get("total_duration_stdev", 1)
    duration_z = abs(obs_duration - enr_duration) / max(enr_duration_stdev, 1.0)
    duration_dev = sigmoid(duration_z - 1.0)

    # Signal 6: Trend deviation (weight 0.05)
    # |mean(last_5_cred_drifts) - overall_mean| / overall_stdev
    trend_dev = _compute_trend_deviation(
        recent_drifts=recent_drifts,
        overall_mean=overall_drift_mean,
        overall_stdev=overall_drift_stdev,
    )

    # V2 composite drift
    drift = (
        0.35 * (1.0 - max(0.0, timing_corr))
        + 0.20 * (1.0 - max(0.0, dwell_corr))
        + 0.15 * (1.0 - zone_sim)
        + 0.15 * (1.0 - hesit_overlap)
        + 0.10 * duration_dev
        + 0.05 * trend_dev
    )

    return {
        "drift": round(min(1.0, max(0.0, drift)), 4),
        "timing_corr": round(timing_corr, 4),
        "dwell_corr": round(dwell_corr, 4),
        "zone_sequence_similarity": round(zone_sim, 4),
        "hesitation_overlap": round(hesit_overlap, 4),
        "duration_deviation": round(duration_dev, 4),
        "trend_deviation": round(trend_dev, 4),
    }


def _compute_trend_deviation(
    *,
    recent_drifts: list[float] | None,
    overall_mean: float | None,
    overall_stdev: float | None,
) -> float:
    """Compute trend deviation from recent credential drifts.

    |mean(last_5_cred_drifts) - overall_mean| / overall_stdev

    Returns 0.0 if insufficient data. Clamped to [0.0, 1.0].
    """
    if not recent_drifts or overall_mean is None or overall_stdev is None:
        return 0.0

    valid = [d for d in recent_drifts if d >= 0]
    if not valid:
        return 0.0

    recent_mean = sum(valid) / len(valid)

    if overall_stdev <= 0.0:
        return 0.0

    deviation = abs(recent_mean - overall_mean) / overall_stdev
    return round(min(1.0, max(0.0, deviation)), 4)
