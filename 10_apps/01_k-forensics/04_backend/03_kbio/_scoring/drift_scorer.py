"""kbio drift scorer.

Transforms feature vectors into per-modality drift scores by comparing
against user profile centroids. Pure computation — no I/O.

Drift scale: 0.0 (matches baseline) to 1.0 (completely different behavior).
Formula: sigmoid(z_score - 1.0)
"""

from __future__ import annotations

import math
from typing import Any


def sigmoid(x: float) -> float:
    """Standard sigmoid function, clamped to avoid overflow."""
    x = max(-10.0, min(10.0, x))
    return 1.0 / (1.0 + math.exp(-x))


def cosine_distance(a: list[float], b: list[float]) -> float:
    """Cosine distance between two L2-normalized vectors. Returns 0.0-2.0."""
    if len(a) != len(b) or len(a) == 0:
        return 1.0  # maximum ambiguity
    dot = sum(x * y for x, y in zip(a, b))
    return 1.0 - dot


def compute_modality_drift(
    feature_vec: list[float],
    centroid_vec: list[float],
    intra_mean: float,
    intra_stdev: float,
) -> float:
    """Compute drift for a single modality.

    Steps:
    1. Cosine distance between feature vector and centroid
    2. Z-score normalization using centroid's intra-class statistics
    3. Sigmoid transformation with offset of 1.0

    Returns drift score 0.0-1.0.
    """
    if not feature_vec or not centroid_vec:
        return -1.0  # insufficient data

    raw_dist = cosine_distance(feature_vec, centroid_vec)

    if intra_stdev <= 0.0:
        # No variance data — return raw distance as drift estimate
        return min(1.0, raw_dist)

    z_score = (raw_dist - intra_mean) / intra_stdev
    return sigmoid(z_score - 1.0)


def select_centroid(
    centroids: list[dict[str, Any]],
    context: dict[str, Any],
) -> dict[str, Any] | None:
    """Select the best matching centroid for the current session context.

    Matches by platform, input_method, time_of_day bucket.
    Falls back to highest-weight centroid.
    """
    if not centroids:
        return None

    platform = context.get("platform", "web")
    input_method = context.get("input_method", "keyboard_mouse")

    # Try exact context match
    for c in centroids:
        ctx = c.get("context", {})
        if ctx.get("platform") == platform and ctx.get("input_method") == input_method:
            return c

    # Fallback: highest weight
    return max(centroids, key=lambda c: c.get("weight", 0.0))


def l2_normalize(vec: list[float]) -> list[float]:
    """L2-normalize a vector. Returns zero vector if magnitude is 0."""
    magnitude = math.sqrt(sum(x * x for x in vec))
    if magnitude == 0.0:
        return vec
    return [x / magnitude for x in vec]


def normalize_features(raw_features: dict[str, Any]) -> dict[str, list[float]]:
    """Normalize raw feature windows into L2-normalized vectors per modality.

    V1: Raw feature vector flattened and L2-normalized.
    V2 (future): TCN encoder heads per modality.
    """
    result: dict[str, list[float]] = {}

    modality_keys = {
        "keystroke": _flatten_keystroke_features,
        "pointer": _flatten_pointer_features,
        "touch": _flatten_touch_features,
        "scroll": _flatten_scroll_features,
        "sensor": _flatten_sensor_features,
    }

    for modality, flatten_fn in modality_keys.items():
        windows = raw_features.get(f"{modality}_windows", [])
        if not windows:
            continue
        # Use the most recent window
        latest = windows[-1] if isinstance(windows, list) else windows
        vec = flatten_fn(latest)
        if vec and any(v != 0.0 for v in vec):
            result[modality] = l2_normalize(vec)

    return result


def _flatten_keystroke_features(window: dict[str, Any]) -> list[float]:
    """Flatten keystroke window into a feature vector."""
    vec: list[float] = []
    # Zone transition matrix (100 values)
    vec.extend(_safe_list(window.get("zone_transition_matrix"), 100))
    # Zone dwell means (10 values)
    vec.extend(_safe_list(window.get("zone_dwell_means"), 10))
    # Zone dwell stdevs (10 values)
    vec.extend(_safe_list(window.get("zone_dwell_stdevs"), 10))
    # Zone hit counts (10 values)
    vec.extend(_safe_list(window.get("zone_hit_counts"), 10))
    # Rhythm features
    rhythm = window.get("rhythm", {})
    vec.append(_safe_float(rhythm.get("kps_mean")))
    vec.append(_safe_float(rhythm.get("kps_stdev")))
    vec.append(_safe_float(rhythm.get("burst_count")))
    vec.append(_safe_float(rhythm.get("burst_length_mean")))
    vec.append(_safe_float(rhythm.get("pause_count")))
    # Error proxy
    error = window.get("error_proxy", {})
    vec.append(_safe_float(error.get("backspace_rate")))
    vec.append(_safe_float(error.get("rapid_same_zone_count")))
    # Bigram velocity histogram (10 bins)
    vec.extend(_safe_list(window.get("bigram_velocity_histogram"), 10))
    return vec


def _flatten_pointer_features(window: dict[str, Any]) -> list[float]:
    """Flatten pointer window into a feature vector."""
    vec: list[float] = []
    movement = window.get("movement", {})
    vec.append(_safe_float(movement.get("total_distance")))
    vec.append(_safe_float(movement.get("path_efficiency")))
    vec.append(_safe_float(movement.get("velocity_mean")))
    vec.append(_safe_float(movement.get("velocity_stdev")))
    vec.append(_safe_float(movement.get("acceleration_mean")))
    vec.append(_safe_float(movement.get("direction_changes")))
    vec.append(_safe_float(movement.get("curvature_mean")))
    vec.extend(_safe_list(movement.get("angle_histogram"), 8))
    # Clicks
    clicks = window.get("clicks", {})
    vec.append(_safe_float(clicks.get("count")))
    vec.append(_safe_float(clicks.get("hold_mean_ms")))
    vec.extend(_safe_list(clicks.get("approach_velocity_profile"), 5))
    vec.append(_safe_float(clicks.get("overshoot_rate")))
    # Idle
    idle = window.get("idle", {})
    vec.append(_safe_float(idle.get("count")))
    vec.append(_safe_float(idle.get("micro_movement_amplitude")))
    vec.append(_safe_float(idle.get("micro_movement_frequency")))
    return vec


def _flatten_touch_features(window: dict[str, Any]) -> list[float]:
    """Flatten touch window into a feature vector."""
    vec: list[float] = []
    taps = window.get("taps", {})
    vec.append(_safe_float(taps.get("count")))
    vec.append(_safe_float(taps.get("duration_mean")))
    vec.append(_safe_float(taps.get("force_mean")))
    vec.append(_safe_float(taps.get("radius_mean")))
    swipes = window.get("swipes", {})
    vec.append(_safe_float(swipes.get("count")))
    vec.append(_safe_float(swipes.get("velocity_mean")))
    vec.append(_safe_float(swipes.get("curvature")))
    spatial = window.get("spatial", {})
    vec.extend(_safe_list(spatial.get("heatmap_zones"), 12))
    return vec


def _flatten_scroll_features(window: dict[str, Any]) -> list[float]:
    """Flatten scroll window into a feature vector."""
    vec: list[float] = []
    vec.append(_safe_float(window.get("event_count")))
    vec.append(_safe_float(window.get("total_distance")))
    vec.append(_safe_float(window.get("velocity_mean")))
    vec.append(_safe_float(window.get("velocity_stdev")))
    vec.append(_safe_float(window.get("direction_changes")))
    vec.append(_safe_float(window.get("burst_count")))
    return vec


def _flatten_sensor_features(window: dict[str, Any]) -> list[float]:
    """Flatten sensor window into a feature vector."""
    vec: list[float] = []
    accel = window.get("accelerometer", {})
    vec.extend(_safe_list(accel.get("mean"), 3))
    vec.extend(_safe_list(accel.get("stdev"), 3))
    vec.append(_safe_float(accel.get("magnitude_mean")))
    gyro = window.get("gyroscope", {})
    vec.extend(_safe_list(gyro.get("mean"), 3))
    vec.extend(_safe_list(gyro.get("stdev"), 3))
    grasp = window.get("grasp_signature", {})
    vec.append(_safe_float(grasp.get("stability_score")))
    vec.append(_safe_float(grasp.get("tilt_during_interaction")))
    return vec


def _safe_float(val: Any, default: float = 0.0) -> float:
    """Convert to float, replacing None/-1 with default."""
    if val is None or val == -1:
        return default
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def _safe_list(val: Any, expected_len: int, default: float = 0.0) -> list[float]:
    """Convert to list of floats with expected length."""
    if not isinstance(val, (list, tuple)):
        return [default] * expected_len
    result = [_safe_float(v, default) for v in val]
    # Pad or truncate to expected length
    if len(result) < expected_len:
        result.extend([default] * (expected_len - len(result)))
    return result[:expected_len]


# ---------------------------------------------------------------------------
# Qdrant centroid operations
# ---------------------------------------------------------------------------

# Target vector dimensionality for the kbio_user_centroids collection
CENTROID_VECTOR_DIM = 128


async def store_centroid_vectors(
    qdrant_client: object,
    user_hash: str,
    centroid_id: str,
    modality_vectors: dict[str, list[float]],
    context: dict[str, Any],
) -> None:
    """Store centroid vectors in Qdrant for fast similarity search.

    Each modality's centroid embedding is stored as a separate point.
    Payload includes user_hash, modality, context for filtering.

    Args:
        qdrant_client: AsyncQdrantClient instance from 01_core.qdrant.
    """
    from qdrant_client.models import PointStruct  # type: ignore[import-untyped]
    import uuid as _uuid

    points: list[PointStruct] = []
    for modality, vec in modality_vectors.items():
        # Pad or truncate to CENTROID_VECTOR_DIM dimensions
        padded = (vec + [0.0] * CENTROID_VECTOR_DIM)[:CENTROID_VECTOR_DIM]
        points.append(PointStruct(
            id=str(_uuid.uuid4()),
            vector=padded,
            payload={
                "user_hash": user_hash,
                "centroid_id": centroid_id,
                "modality": modality,
                "platform": context.get("platform", "web"),
                "input_method": context.get("input_method", "keyboard_mouse"),
            },
        ))

    if points:
        await qdrant_client.upsert(
            collection_name="kbio_user_centroids",
            points=points,
        )


async def search_nearest_centroid(
    qdrant_client: object,
    user_hash: str,
    modality: str,
    query_vector: list[float],
    *,
    limit: int = 1,
) -> list[dict[str, Any]]:
    """Search for the nearest centroid for a user+modality in Qdrant.

    Args:
        qdrant_client: AsyncQdrantClient instance from 01_core.qdrant.

    Returns list of {id, score, payload} dicts.
    """
    from qdrant_client.models import Filter, FieldCondition, MatchValue  # type: ignore[import-untyped]

    # Pad or truncate to CENTROID_VECTOR_DIM dimensions
    padded = (query_vector + [0.0] * CENTROID_VECTOR_DIM)[:CENTROID_VECTOR_DIM]

    results = await qdrant_client.search(
        collection_name="kbio_user_centroids",
        query_vector=padded,
        query_filter=Filter(
            must=[
                FieldCondition(key="user_hash", match=MatchValue(value=user_hash)),
                FieldCondition(key="modality", match=MatchValue(value=modality)),
            ]
        ),
        limit=limit,
    )

    return [
        {"id": str(r.id), "score": r.score, "payload": r.payload}
        for r in results
    ]
