"""Touch feature extractor (V2).

Extracts a 32-dimensional feature vector from a touch telemetry window.
Enhanced from V1's _flatten_touch_features with:
  - NEW pinch gestures: count, scale_mean (2)
  - NEW touch pressure variance (1)
  - NEW multi-touch frequency (1)
  - NEW swipe direction histogram (4 bins)
  - NEW tap rhythm regularity (1)
  - NEW touch area consistency (1)
  - NEW gesture transition patterns (3)

Dimension budget:
  taps                   =  4
  swipes                 =  3
  spatial_heatmap        = 12
  pinch_gestures         =  2
  pressure_variance      =  1
  multi_touch_freq       =  1
  swipe_direction_hist   =  4
  tap_rhythm_regularity  =  1
  touch_area_consistency =  1
  gesture_transitions    =  3
  TOTAL                  = 32
"""
from __future__ import annotations

from typing import Any

from ._helpers import _safe_float, _safe_list

# Dimension constant
TOUCH_DIM = 32


def extract_touch_features(window: dict[str, Any]) -> list[float]:
    """Extract 32-dimensional touch feature vector from a window.

    Args:
        window: Raw touch telemetry window dict.  Expected keys:
            taps (dict), swipes (dict), spatial (dict),
            pinch (dict), multi_touch (dict), gestures (dict).

    Returns:
        list[float] of exactly 32 elements.  Returns all-zeros on
        missing/empty input.
    """
    if not window or not isinstance(window, dict):
        return [0.0] * TOUCH_DIM

    vec: list[float] = []

    # --- Taps (4) ---
    taps = window.get("taps", {})
    if not isinstance(taps, dict):
        taps = {}
    vec.append(_safe_float(taps.get("count")))
    vec.append(_safe_float(taps.get("duration_mean")))
    vec.append(_safe_float(taps.get("force_mean")))
    vec.append(_safe_float(taps.get("radius_mean")))

    # --- Swipes (3) ---
    swipes = window.get("swipes", {})
    if not isinstance(swipes, dict):
        swipes = {}
    vec.append(_safe_float(swipes.get("count")))
    vec.append(_safe_float(swipes.get("velocity_mean")))
    vec.append(_safe_float(swipes.get("curvature")))

    # --- Spatial heatmap zones (12) ---
    spatial = window.get("spatial", {})
    if not isinstance(spatial, dict):
        spatial = {}
    vec.extend(_safe_list(spatial.get("heatmap_zones"), 12))

    # --- NEW: Pinch gestures (2) ---
    pinch = window.get("pinch", {})
    if not isinstance(pinch, dict):
        pinch = {}
    vec.append(_safe_float(pinch.get("count")))
    vec.append(_safe_float(pinch.get("scale_mean")))

    # --- NEW: Touch pressure variance (1) ---
    vec.append(_safe_float(taps.get("pressure_variance")))

    # --- NEW: Multi-touch frequency (1) ---
    multi_touch = window.get("multi_touch", {})
    if not isinstance(multi_touch, dict):
        multi_touch = {}
    vec.append(_safe_float(multi_touch.get("frequency")))

    # --- NEW: Swipe direction histogram (4 bins: up/down/left/right) ---
    vec.extend(_safe_list(swipes.get("direction_histogram"), 4))

    # --- NEW: Tap rhythm regularity (inter-tap timing stdev) (1) ---
    vec.append(_safe_float(taps.get("inter_tap_timing_stdev")))

    # --- NEW: Touch area consistency (1) ---
    vec.append(_safe_float(taps.get("area_consistency")))

    # --- NEW: Gesture transition patterns (3) ---
    # tap-to-swipe rate, swipe-to-tap rate, double-tap rate
    gestures = window.get("gestures", {})
    if not isinstance(gestures, dict):
        gestures = {}
    vec.append(_safe_float(gestures.get("tap_to_swipe_rate")))
    vec.append(_safe_float(gestures.get("swipe_to_tap_rate")))
    vec.append(_safe_float(gestures.get("double_tap_rate")))

    # Guarantee exact dimensionality
    if len(vec) < TOUCH_DIM:
        vec.extend([0.0] * (TOUCH_DIM - len(vec)))
    return vec[:TOUCH_DIM]
