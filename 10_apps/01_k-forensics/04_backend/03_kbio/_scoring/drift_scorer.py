"""kbio drift scorer — V2.

Transforms feature vectors into per-modality drift scores by comparing
against user profile centroids.  Pure computation — no I/O.

Drift scale: 0.0 (matches baseline) to 1.0 (completely different behavior).
Formula: sigmoid(z_score - 1.0)

V2 changes:
- Math ops imported from ``._math`` (no local duplicates).
- ``select_centroid`` removed (replaced by ``_clustering.bayesian_selector``).
- ``normalize_features`` / flatten helpers moved to ``_features/``.
- ``_safe_float`` / ``_safe_list`` moved to ``_features/_helpers.py``.
- ``store_centroid_vectors`` / ``search_nearest_centroid`` moved to future
  ``_storage`` module.
- Added ``compute_all_modality_drifts`` orchestrator.
"""
from __future__ import annotations

from typing import Any

from ._math import cosine_distance, sigmoid, z_score


# ---------------------------------------------------------------------------
# Centroid key mapping — maps modality names to cluster dict keys
# ---------------------------------------------------------------------------

CENTROID_KEYS: dict[str, str] = {
    "keystroke": "keystroke_centroid",
    "pointer": "pointer_centroid",
    "touch": "touch_centroid",
    "sensor": "sensor_centroid",
}


# ---------------------------------------------------------------------------
# Per-modality drift
# ---------------------------------------------------------------------------

def compute_modality_drift(
    feature_vec: list[float],
    centroid_vec: list[float],
    intra_mean: float,
    intra_stdev: float,
) -> dict[str, Any]:
    """Compute drift for a single modality.

    Steps:
        1. Cosine distance between feature vector and centroid.
        2. Z-score normalisation using the centroid's intra-class statistics.
        3. Sigmoid transformation with an offset of 1.0.

    Returns:
        ``{"drift": float, "z_score": float, "raw_distance": float}``

        All values rounded to 4 decimal places.
        If input data is insufficient, drift is ``-1.0``.
    """
    if not feature_vec or not centroid_vec:
        return {"drift": -1.0, "z_score": 0.0, "raw_distance": 0.0}

    raw_dist = cosine_distance(feature_vec, centroid_vec)

    if intra_stdev <= 0.0:
        # No variance data — use raw distance as drift estimate.
        drift = round(min(1.0, raw_dist), 4)
        return {
            "drift": drift,
            "z_score": 0.0,
            "raw_distance": round(raw_dist, 4),
        }

    z = z_score(raw_dist, intra_mean, intra_stdev)
    drift = round(sigmoid(z - 1.0), 4)

    return {
        "drift": drift,
        "z_score": round(z, 4),
        "raw_distance": round(raw_dist, 4),
    }


# ---------------------------------------------------------------------------
# Orchestrator — all modalities in one pass
# ---------------------------------------------------------------------------

def compute_all_modality_drifts(
    feature_vecs: dict[str, list[float]],
    cluster: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    """Compute drift for all available modalities against a cluster's centroids.

    For each modality that has *both* a feature vector **and** a centroid
    stored in *cluster*:

    1. Look up the per-modality centroid via :data:`CENTROID_KEYS`
       (e.g. ``cluster["keystroke_centroid"]``).
    2. Look up per-modality intra-class statistics from
       ``cluster["per_modality_intra"]``.
    3. Delegate to :func:`compute_modality_drift`.

    Args:
        feature_vecs: ``{modality: [float, ...]}`` — normalised feature
            vectors for the current batch.
        cluster: Cluster dict containing ``*_centroid`` vectors and a
            ``per_modality_intra`` sub-dict with ``{modality: {"mean", "stdev"}}``.

    Returns:
        ``{modality: {"drift": float, "z_score": float, "raw_distance": float}}``

        Only modalities present in **both** *feature_vecs* and *cluster*
        are included.
    """
    per_modality_intra: dict[str, dict[str, float]] = cluster.get(
        "per_modality_intra", {}
    )

    results: dict[str, dict[str, Any]] = {}

    for modality, centroid_key in CENTROID_KEYS.items():
        feature_vec = feature_vecs.get(modality)
        if not feature_vec:
            continue

        centroid_vec = cluster.get(centroid_key)
        if not centroid_vec:
            continue

        intra = per_modality_intra.get(modality, {})
        intra_mean = float(intra.get("mean", 0.0))
        intra_stdev = float(intra.get("stdev", 0.0))

        results[modality] = compute_modality_drift(
            feature_vec,
            centroid_vec,
            intra_mean,
            intra_stdev,
        )

    return results
