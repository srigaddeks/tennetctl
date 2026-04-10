"""Pointer (mouse/trackpad) feature extractor (V2).

Extracts a 32-dimensional feature vector from a pointer telemetry window.
Enhanced from V1's _flatten_pointer_features with:
  - NEW jerk (derivative of acceleration) mean + stdev (2)
  - NEW direct-vs-search movement ratio (1)
  - NEW path curvature variance (1)
  - NEW click-to-movement delay mean (1)
  - NEW hover duration before click mean (1)

Dimension budget:
  movement_scalars       =  7
  angle_histogram        =  8
  clicks                 =  8
  idle                   =  3
  jerk                   =  2
  direct_search_ratio    =  1
  curvature_variance     =  1
  click_movement_delay   =  1
  hover_before_click     =  1
  TOTAL                  = 32
"""
from __future__ import annotations

from typing import Any

from ._helpers import _safe_float, _safe_list

# Dimension constant
POINTER_DIM = 32


def extract_pointer_features(window: dict[str, Any]) -> list[float]:
    """Extract 32-dimensional pointer feature vector from a window.

    Args:
        window: Raw pointer telemetry window dict.  Expected keys:
            movement (dict), clicks (dict), idle (dict),
            jerk (dict), path_analysis (dict).

    Returns:
        list[float] of exactly 32 elements.  Returns all-zeros on
        missing/empty input.
    """
    if not window or not isinstance(window, dict):
        return [0.0] * POINTER_DIM

    vec: list[float] = []

    # --- Movement scalars (7) ---
    movement = window.get("movement", {})
    if not isinstance(movement, dict):
        movement = {}
    vec.append(_safe_float(movement.get("total_distance")))
    vec.append(_safe_float(movement.get("path_efficiency")))
    vec.append(_safe_float(movement.get("velocity_mean")))
    vec.append(_safe_float(movement.get("velocity_stdev")))
    vec.append(_safe_float(movement.get("acceleration_mean")))
    vec.append(_safe_float(movement.get("direction_changes")))
    vec.append(_safe_float(movement.get("curvature_mean")))

    # --- Angle histogram (8) ---
    vec.extend(_safe_list(movement.get("angle_histogram"), 8))

    # --- Clicks (8) ---
    clicks = window.get("clicks", {})
    if not isinstance(clicks, dict):
        clicks = {}
    vec.append(_safe_float(clicks.get("count")))
    vec.append(_safe_float(clicks.get("hold_mean_ms")))
    vec.extend(_safe_list(clicks.get("approach_velocity_profile"), 5))
    vec.append(_safe_float(clicks.get("overshoot_rate")))

    # --- Idle (3) ---
    idle = window.get("idle", {})
    if not isinstance(idle, dict):
        idle = {}
    vec.append(_safe_float(idle.get("count")))
    vec.append(_safe_float(idle.get("micro_movement_amplitude")))
    vec.append(_safe_float(idle.get("micro_movement_frequency")))

    # --- NEW: Jerk — derivative of acceleration (2) ---
    jerk = window.get("jerk", {})
    if not isinstance(jerk, dict):
        jerk = {}
    vec.append(_safe_float(jerk.get("mean")))
    vec.append(_safe_float(jerk.get("stdev")))

    # --- NEW: Direct-vs-search movement ratio (1) ---
    path_analysis = window.get("path_analysis", {})
    if not isinstance(path_analysis, dict):
        path_analysis = {}
    vec.append(_safe_float(path_analysis.get("direct_search_ratio")))

    # --- NEW: Path curvature variance (1) ---
    vec.append(_safe_float(path_analysis.get("curvature_variance")))

    # --- NEW: Click-to-movement delay mean (1) ---
    vec.append(_safe_float(clicks.get("click_to_movement_delay_mean")))

    # --- NEW: Hover duration before click mean (1) ---
    vec.append(_safe_float(clicks.get("hover_before_click_mean")))

    # Guarantee exact dimensionality
    if len(vec) < POINTER_DIM:
        vec.extend([0.0] * (POINTER_DIM - len(vec)))
    return vec[:POINTER_DIM]
