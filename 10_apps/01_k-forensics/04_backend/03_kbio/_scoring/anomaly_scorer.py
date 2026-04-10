"""kbio anomaly scorer — V2.

Five per-session anomaly signals (all 0.0-1.0):
  1. session_anomaly    — z-score ensemble across feature dims (V1).
  2. velocity_anomaly   — rate of behavioural change within session.
  3. takeover_probability — CUSUM-based account-takeover detector.
  4. pattern_break      — structural change via Jensen-Shannon divergence.
  5. consistency_score  — intra-session self-consistency (inverse variance).
"""
from __future__ import annotations

import math
from typing import Any

from ._math import clamp, jensen_shannon, sigmoid, z_score


# Population baselines (bootstrapped; production loads from Valkey cache)
_POPULATION_STATS: dict[str, dict[str, float]] = {
    "keystroke": {"mean_drift": 0.25, "stdev_drift": 0.15, "mean_kps": 3.5, "stdev_kps": 1.2},
    "pointer": {"mean_drift": 0.20, "stdev_drift": 0.18, "mean_velocity": 200.0, "stdev_velocity": 80.0},
    "touch": {"mean_drift": 0.22, "stdev_drift": 0.16, "mean_force": 0.5, "stdev_force": 0.15},
    "scroll": {"mean_drift": 0.18, "stdev_drift": 0.14, "mean_velocity": 150.0, "stdev_velocity": 60.0},
    "sensor": {"mean_drift": 0.15, "stdev_drift": 0.12, "mean_magnitude": 9.8, "stdev_magnitude": 0.5},
}

_WEIGHT_MAP: dict[str, float] = {
    "keystroke": 0.35,
    "pointer": 0.25,
    "touch": 0.20,
    "scroll": 0.10,
    "sensor": 0.10,
}

MIN_MODALITIES_FOR_SCORE = 1


# -- 1. Session anomaly (V1 — z-score ensemble) ---------------------------

def compute_anomaly_score(
    feature_vecs: dict[str, list[float]],
    modality_drifts: dict[str, float],
    batch: dict[str, Any],
) -> dict[str, Any]:
    """Z-score ensemble anomaly: max z per modality, sigmoid, weighted avg."""
    modality_anomalies: dict[str, dict[str, Any]] = {}
    scores: list[float] = []
    weights: list[float] = []

    for modality, vec in feature_vecs.items():
        pop_stats = _POPULATION_STATS.get(modality)
        if not pop_stats or not vec:
            continue

        z_scores = _compute_feature_z_scores(vec, modality, batch)
        if not z_scores:
            continue

        max_z = max(abs(z) for z in z_scores)
        top_dim_idx = max(range(len(z_scores)), key=lambda i: abs(z_scores[i]))

        # Factor in drift deviation from population
        drift = modality_drifts.get(modality, -1.0)
        if drift >= 0:
            drift_mean = pop_stats.get("mean_drift", 0.25)
            drift_stdev = pop_stats.get("stdev_drift", 0.15)
            drift_z = z_score(drift, drift_mean, drift_stdev)
            max_z = max(max_z, abs(drift_z))

        anomaly = sigmoid(max_z - 1.5)

        modality_anomalies[modality] = {
            "score": round(anomaly, 4),
            "top_dimension": top_dim_idx,
            "z_score": round(max_z, 4),
        }
        scores.append(anomaly)
        weights.append(_WEIGHT_MAP.get(modality, 0.1))

    if len(scores) < MIN_MODALITIES_FOR_SCORE:
        return {
            "anomaly_score": -1.0,
            "modality_anomalies": {},
            "method": "z_score_ensemble",
        }

    total_weight = sum(weights)
    if total_weight <= 0:
        return {"anomaly_score": -1.0, "modality_anomalies": {}, "method": "z_score_ensemble"}

    composite = sum(s * w for s, w in zip(scores, weights)) / total_weight

    return {
        "anomaly_score": round(clamp(composite, 0.0, 1.0), 4),
        "modality_anomalies": modality_anomalies,
        "method": "z_score_ensemble",
    }


def _compute_feature_z_scores(
    vec: list[float],
    _modality: str,
    _batch: dict[str, Any],
) -> list[float]:
    """Z-scores of vector statistics against expected L2-normalised norms."""
    if not vec or len(vec) < 2:
        return []

    n = len(vec)
    vec_mean = sum(vec) / n
    vec_var = sum((x - vec_mean) ** 2 for x in vec) / n if n > 1 else 0.0

    expected_mean = 1.0 / math.sqrt(n) if n > 0 else 0.1
    expected_stdev = 0.08

    z_scores: list[float] = []

    # Z-score of vector mean
    if expected_stdev > 0:
        z_scores.append((vec_mean - expected_mean) / expected_stdev)

    # Z-score of vector variance
    expected_var = expected_stdev ** 2
    var_stdev = expected_var * 0.5
    if var_stdev > 0:
        z_scores.append((vec_var - expected_var) / var_stdev)

    # Sparsity check
    near_zero = sum(1 for x in vec if abs(x) < 0.001) / n if n > 0 else 0
    z_scores.append((near_zero - 0.3) / 0.15)

    # Max-value concentration check
    max_val = max(abs(x) for x in vec)
    z_scores.append((max_val - 0.3) / 0.1)

    return z_scores



# -- 2. Velocity anomaly --------------------------------------------------

def compute_velocity_anomaly(
    drift_history: list[float],
    expected_velocity_stdev: float = 0.02,
) -> float:
    """Rate of behavioural change.  Normal < 0.02/batch, spike > 0.05.

    Returns 0.0-1.0.  Returns 0.0 if < 2 history points.
    """
    if len(drift_history) < 2:
        return 0.0

    velocities = [
        abs(drift_history[i] - drift_history[i - 1])
        for i in range(1, len(drift_history))
    ]
    mean_velocity = sum(velocities) / len(velocities)

    if expected_velocity_stdev <= 0.0:
        return 0.0

    raw = mean_velocity / expected_velocity_stdev - 1.0
    return round(clamp(sigmoid(raw), 0.0, 1.0), 4)



# -- 3. Takeover probability (CUSUM-based — the money score) ---------------

def compute_takeover_probability(
    drift_history: list[float],
    modality_drift_history: dict[str, list[float]] | None = None,
    *,
    baseline_count: int = 5,
    h_multiplier: float = 4.0,
) -> dict[str, Any]:
    """CUSUM-based takeover detection — three detectors fused.

    Weights: CUSUM 0.40, velocity spike 0.30, modality concordance 0.30.
    """
    result_default: dict[str, Any] = {
        "takeover_probability": 0.0,
        "cusum_signal": 0.0,
        "velocity_signal": 0.0,
        "concordance_signal": 0.0,
        "changepoint_detected": False,
    }

    if len(drift_history) < baseline_count + 1:
        return result_default

    # ---- 1. CUSUM signal ------------------------------------------------
    baseline = drift_history[:baseline_count]
    baseline_mean = sum(baseline) / len(baseline)
    baseline_var = sum((x - baseline_mean) ** 2 for x in baseline) / len(baseline)
    baseline_stdev = math.sqrt(baseline_var) if baseline_var > 0 else 0.01

    threshold = h_multiplier * baseline_stdev

    cusum = 0.0
    max_cusum = 0.0
    for score in drift_history[baseline_count:]:
        cusum = max(0.0, cusum + (score - baseline_mean) - baseline_stdev * 0.5)
        max_cusum = max(max_cusum, cusum)

    cusum_signal = clamp(max_cusum / threshold, 0.0, 1.0) if threshold > 0 else 0.0
    changepoint_detected = max_cusum > threshold

    # ---- 2. Velocity spike signal ---------------------------------------
    velocity_signal = 0.0
    if len(drift_history) >= 2:
        drift_delta = abs(drift_history[-1] - drift_history[-2])
        velocity_signal = clamp((drift_delta - 0.15) / 0.35, 0.0, 1.0)

    # ---- 3. Multi-modality concordance ----------------------------------
    concordance_signal = 0.0
    if modality_drift_history:
        concordance_signal = _compute_concordance(modality_drift_history)

    # ---- Fuse -----------------------------------------------------------
    takeover = (
        0.40 * cusum_signal
        + 0.30 * velocity_signal
        + 0.30 * concordance_signal
    )

    return {
        "takeover_probability": round(clamp(takeover, 0.0, 1.0), 4),
        "cusum_signal": round(cusum_signal, 4),
        "velocity_signal": round(velocity_signal, 4),
        "concordance_signal": round(concordance_signal, 4),
        "changepoint_detected": changepoint_detected,
    }


def _compute_concordance(
    modality_drift_history: dict[str, list[float]],
) -> float:
    """Multi-modality concordance: are multiple modalities spiking together?"""
    deltas: list[float] = []
    for _modality, history in modality_drift_history.items():
        if len(history) >= 2:
            deltas.append(history[-1] - history[-2])

    if len(deltas) < 2:
        return 0.0

    # Count how many modalities show a positive (worsening) drift delta
    positive_deltas = [d for d in deltas if d > 0.0]
    if len(positive_deltas) < 2:
        return 0.0

    # Concordance = fraction of modalities spiking * magnitude of spikes
    fraction_spiking = len(positive_deltas) / len(deltas)
    max_delta = max(positive_deltas)
    mean_delta = sum(positive_deltas) / len(positive_deltas)

    concordance = fraction_spiking * clamp(max_delta + mean_delta, 0.0, 1.0)
    return round(clamp(concordance, 0.0, 1.0), 4)



# -- 4. Pattern break (Jensen-Shannon divergence) --------------------------

def compute_pattern_break(
    current_features: dict[str, list[float]],
    baseline_features: dict[str, list[float]] | None = None,
) -> float:
    """JS-divergence on feature histograms — did behaviour *shape* change?

    Returns 0.0-1.0.  Returns 0.0 if no baseline.
    """
    if not baseline_features:
        return 0.0

    jsd_scores: list[float] = []
    weights: list[float] = []

    for modality, current_vec in current_features.items():
        baseline_vec = baseline_features.get(modality)
        if not baseline_vec or not current_vec:
            continue

        # Convert raw feature vectors to non-negative histograms for JS-div.
        # Shift by min value so all bins are >= 0.
        current_hist = _to_histogram(current_vec)
        baseline_hist = _to_histogram(baseline_vec)

        # Pad / truncate to same length
        max_len = max(len(current_hist), len(baseline_hist))
        current_padded = current_hist + [0.0] * (max_len - len(current_hist))
        baseline_padded = baseline_hist + [0.0] * (max_len - len(baseline_hist))

        jsd = jensen_shannon(current_padded, baseline_padded)
        jsd_scores.append(jsd)
        weights.append(_WEIGHT_MAP.get(modality, 0.1))

    if not jsd_scores:
        return 0.0

    total_weight = sum(weights)
    if total_weight <= 0:
        return 0.0

    weighted = sum(s * w for s, w in zip(jsd_scores, weights)) / total_weight
    return round(clamp(weighted, 0.0, 1.0), 4)


def _to_histogram(vec: list[float], bins: int = 20) -> list[float]:
    """Bin feature values into equal-width buckets (counts per bucket)."""
    if not vec:
        return [0.0] * bins

    lo = min(vec)
    hi = max(vec)
    span = hi - lo if hi > lo else 1.0

    hist = [0.0] * bins
    for v in vec:
        idx = int((v - lo) / span * (bins - 1))
        idx = max(0, min(bins - 1, idx))
        hist[idx] += 1.0

    return hist



# -- 5. Consistency score --------------------------------------------------

def compute_consistency_score(
    drift_history: list[float],
    *,
    window: int = 10,
) -> float:
    """1 / (1 + 5*var). Returns 0.0 (erratic) to 1.0 (consistent), 0.5 if < 2 pts."""
    if len(drift_history) < 2:
        return 0.5

    recent = drift_history[-window:]
    n = len(recent)
    mean = sum(recent) / n
    variance = sum((x - mean) ** 2 for x in recent) / n

    consistency = 1.0 / (1.0 + 5.0 * variance)
    return round(clamp(consistency, 0.0, 1.0), 4)



# -- Orchestrator ----------------------------------------------------------

def compute_all_anomaly_scores(
    feature_vecs: dict[str, list[float]],
    modality_drifts: dict[str, float],
    drift_history: list[float],
    modality_drift_history: dict[str, list[float]] | None,
    batch: dict[str, Any],
    baseline_features: dict[str, list[float]] | None = None,
) -> dict[str, Any]:
    """Compute all five anomaly scores.  Returns AnomalyScores shape."""
    session_result = compute_anomaly_score(feature_vecs, modality_drifts, batch)
    velocity = compute_velocity_anomaly(drift_history)
    takeover = compute_takeover_probability(
        drift_history,
        modality_drift_history,
    )
    pattern = compute_pattern_break(feature_vecs, baseline_features)
    consistency = compute_consistency_score(drift_history)

    return {
        "session_anomaly": session_result["anomaly_score"],
        "modality_anomalies": session_result["modality_anomalies"],
        "velocity_anomaly": velocity,
        "takeover": takeover,
        "pattern_break": pattern,
        "consistency": consistency,
        "method": "v2_multi_signal",
    }
