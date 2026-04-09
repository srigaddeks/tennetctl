"""kbio anomaly scorer.

Computes per-session anomaly scores using statistical outlier detection.
How unusual is this session's behavior compared to the global population?

Anomaly scale: 0.0 (perfectly normal) to 1.0 (extreme outlier).

V1: Z-score ensemble across feature dimensions with sigmoid normalization.
V2 (future): Isolation Forest trained on population data.
"""
from __future__ import annotations

import math
from typing import Any


# Global population statistics (bootstrapped, updated periodically)
# These represent the expected distribution of feature values across ALL users.
# In production, these would be computed from the population and cached in Valkey.
_POPULATION_STATS: dict[str, dict[str, float]] = {
    "keystroke": {"mean_drift": 0.25, "stdev_drift": 0.15, "mean_kps": 3.5, "stdev_kps": 1.2},
    "pointer": {"mean_drift": 0.20, "stdev_drift": 0.18, "mean_velocity": 200.0, "stdev_velocity": 80.0},
    "touch": {"mean_drift": 0.22, "stdev_drift": 0.16, "mean_force": 0.5, "stdev_force": 0.15},
    "scroll": {"mean_drift": 0.18, "stdev_drift": 0.14, "mean_velocity": 150.0, "stdev_velocity": 60.0},
    "sensor": {"mean_drift": 0.15, "stdev_drift": 0.12, "mean_magnitude": 9.8, "stdev_magnitude": 0.5},
}

# Minimum modalities with anomaly signals to produce a score
MIN_MODALITIES_FOR_SCORE = 1


def compute_anomaly_score(
    feature_vecs: dict[str, list[float]],
    modality_drifts: dict[str, float],
    batch: dict[str, Any],
) -> dict[str, Any]:
    """Compute anomaly score for a behavioral batch.

    Strategy (V1 — z-score ensemble):
    1. For each modality, compute z-scores across multiple feature dimensions
    2. Take the max z-score per modality (most anomalous dimension)
    3. Sigmoid-normalize each modality z-score
    4. Weighted average across modalities

    Args:
        feature_vecs: Normalized feature vectors per modality.
        modality_drifts: Drift scores per modality (from drift_scorer).
        batch: Raw batch data for extracting additional signals.

    Returns:
        {
            anomaly_score: float (0.0-1.0),
            modality_anomalies: {modality: {score, top_dimension, z_score}},
            method: "z_score_ensemble",
        }
    """
    modality_anomalies: dict[str, dict[str, Any]] = {}
    scores: list[float] = []
    weights: list[float] = []

    weight_map = {"keystroke": 0.35, "pointer": 0.25, "touch": 0.20, "scroll": 0.10, "sensor": 0.10}

    for modality, vec in feature_vecs.items():
        pop_stats = _POPULATION_STATS.get(modality)
        if not pop_stats or not vec:
            continue

        # Compute z-scores across feature dimensions
        z_scores = _compute_feature_z_scores(vec, modality, batch)

        if not z_scores:
            continue

        max_z = max(abs(z) for z in z_scores)
        top_dim_idx = max(range(len(z_scores)), key=lambda i: abs(z_scores[i]))

        # Also factor in drift deviation from population
        drift = modality_drifts.get(modality, -1.0)
        if drift >= 0:
            drift_mean = pop_stats.get("mean_drift", 0.25)
            drift_stdev = pop_stats.get("stdev_drift", 0.15)
            if drift_stdev > 0:
                drift_z = (drift - drift_mean) / drift_stdev
                max_z = max(max_z, abs(drift_z))

        # Sigmoid normalization: map z-score to 0-1
        anomaly = _sigmoid(max_z - 1.5)  # offset so z=1.5 maps to ~0.5

        modality_anomalies[modality] = {
            "score": round(anomaly, 4),
            "top_dimension": top_dim_idx,
            "z_score": round(max_z, 4),
        }
        scores.append(anomaly)
        weights.append(weight_map.get(modality, 0.1))

    if len(scores) < MIN_MODALITIES_FOR_SCORE:
        return {
            "anomaly_score": -1.0,
            "modality_anomalies": {},
            "method": "z_score_ensemble",
        }

    # Weighted average
    total_weight = sum(weights)
    if total_weight <= 0:
        return {"anomaly_score": -1.0, "modality_anomalies": {}, "method": "z_score_ensemble"}

    composite = sum(s * w for s, w in zip(scores, weights)) / total_weight

    return {
        "anomaly_score": round(min(1.0, max(0.0, composite)), 4),
        "modality_anomalies": modality_anomalies,
        "method": "z_score_ensemble",
    }


def _compute_feature_z_scores(
    vec: list[float],
    _modality: str,
    _batch: dict[str, Any],
) -> list[float]:
    """Compute z-scores for feature vector dimensions against population norms.

    V1: Uses simple statistical properties of the vector itself
    (mean, variance, kurtosis) compared to expected distributions.
    """
    if not vec or len(vec) < 2:
        return []

    # Compute vector statistics
    n = len(vec)
    vec_mean = sum(vec) / n
    vec_var = sum((x - vec_mean) ** 2 for x in vec) / n if n > 1 else 0.0
    vec_stdev = math.sqrt(vec_var)

    # Expected statistics for this modality (from population)
    # Typical L2-normalized vectors have mean ~0.08 and stdev ~0.08 for 128d
    expected_mean = 1.0 / math.sqrt(n) if n > 0 else 0.1
    expected_stdev = 0.08

    z_scores: list[float] = []

    # Z-score of the vector mean
    if expected_stdev > 0:
        z_scores.append((vec_mean - expected_mean) / expected_stdev)

    # Z-score of the vector variance (too uniform or too concentrated?)
    expected_var = expected_stdev ** 2
    var_stdev = expected_var * 0.5  # rough estimate
    if var_stdev > 0:
        z_scores.append((vec_var - expected_var) / var_stdev)

    # Sparsity check: fraction of near-zero values
    near_zero = sum(1 for x in vec if abs(x) < 0.001) / n if n > 0 else 0
    expected_sparsity = 0.3
    sparsity_stdev = 0.15
    if sparsity_stdev > 0:
        z_scores.append((near_zero - expected_sparsity) / sparsity_stdev)

    # Max value check (overly concentrated vectors are suspicious)
    max_val = max(abs(x) for x in vec)
    expected_max = 0.3
    max_stdev = 0.1
    if max_stdev > 0:
        z_scores.append((max_val - expected_max) / max_stdev)

    return z_scores


def _sigmoid(x: float) -> float:
    """Standard sigmoid, clamped to avoid overflow."""
    x = max(-10.0, min(10.0, x))
    return 1.0 / (1.0 + math.exp(-x))
