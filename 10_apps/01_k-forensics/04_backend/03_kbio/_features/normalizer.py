"""Feature normalizer (V2).

Replaces the V1 normalize_features and l2_normalize from drift_scorer.py.
Uses the dedicated per-modality extractors, then L2-normalizes each vector.

No external dependencies.
"""
from __future__ import annotations

import math
from typing import Any

from .keystroke_extractor import extract_keystroke_features
from .pointer_extractor import extract_pointer_features
from .touch_extractor import extract_touch_features
from .sensor_extractor import extract_sensor_features


def l2_normalize(vec: list[float]) -> list[float]:
    """L2-normalize a vector.  Returns zero vector if magnitude is 0."""
    magnitude = math.sqrt(sum(x * x for x in vec))
    if magnitude == 0.0:
        return vec
    return [x / magnitude for x in vec]


# Map modality names to their extractor functions.
_MODALITY_EXTRACTORS: dict[str, Any] = {
    "keystroke": extract_keystroke_features,
    "pointer": extract_pointer_features,
    "touch": extract_touch_features,
    "sensor": extract_sensor_features,
}


def normalize_features(raw_features: dict[str, Any]) -> dict[str, list[float]]:
    """Normalize raw feature windows into L2-normalized vectors per modality.

    For each modality present in *raw_features*, extracts the feature
    vector from the most recent window, then L2-normalizes it.

    Args:
        raw_features: Dict keyed by ``{modality}_windows`` containing
            lists of window dicts.

    Returns:
        ``{modality: normalized_vector}`` for every modality that
        produced a non-zero vector.
    """
    result: dict[str, list[float]] = {}

    for modality, extract_fn in _MODALITY_EXTRACTORS.items():
        windows = raw_features.get(f"{modality}_windows", [])
        if not windows:
            continue
        # Use the most recent window
        latest = windows[-1] if isinstance(windows, list) else windows
        vec = extract_fn(latest)
        if vec and any(v != 0.0 for v in vec):
            result[modality] = l2_normalize(vec)

    return result
