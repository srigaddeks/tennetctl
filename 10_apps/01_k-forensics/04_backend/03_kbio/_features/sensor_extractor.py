"""Sensor (accelerometer/gyroscope/device) feature extractor (V2).

Extracts a 32-dimensional feature vector from a sensor telemetry window.
Enhanced from V1's _flatten_sensor_features with:
  - NEW orientation: dominant_axis, rotation_rate_mean, rotation_rate_stdev (3)
  - NEW vibration signature: frequency_peak, amplitude_peak (2)
  - NEW device hold pattern: angle_mean, angle_stdev (2)
  - NEW motion complexity (sample entropy of accelerometer signal) (1)
  - NEW stillness ratio (fraction with near-zero acceleration) (1)

Dimension budget:
  accelerometer          =  7
  gyroscope              =  6
  grasp_signature        =  2
  orientation            =  3
  vibration              =  2
  device_hold            =  2
  motion_complexity      =  1
  stillness_ratio        =  1
  padding/extended       =  8
  TOTAL                  = 32
"""
from __future__ import annotations

from typing import Any

from ._helpers import _safe_float, _safe_list

# Dimension constant
SENSOR_DIM = 32


def extract_sensor_features(window: dict[str, Any]) -> list[float]:
    """Extract 32-dimensional sensor feature vector from a window.

    Args:
        window: Raw sensor telemetry window dict.  Expected keys:
            accelerometer (dict), gyroscope (dict),
            grasp_signature (dict), orientation (dict),
            vibration (dict), device_hold (dict),
            motion_complexity (float), stillness_ratio (float),
            extended (dict|list).

    Returns:
        list[float] of exactly 32 elements.  Returns all-zeros on
        missing/empty input.
    """
    if not window or not isinstance(window, dict):
        return [0.0] * SENSOR_DIM

    vec: list[float] = []

    # --- Accelerometer (7) ---
    accel = window.get("accelerometer", {})
    if not isinstance(accel, dict):
        accel = {}
    vec.extend(_safe_list(accel.get("mean"), 3))
    vec.extend(_safe_list(accel.get("stdev"), 3))
    vec.append(_safe_float(accel.get("magnitude_mean")))

    # --- Gyroscope (6) ---
    gyro = window.get("gyroscope", {})
    if not isinstance(gyro, dict):
        gyro = {}
    vec.extend(_safe_list(gyro.get("mean"), 3))
    vec.extend(_safe_list(gyro.get("stdev"), 3))

    # --- Grasp signature (2) ---
    grasp = window.get("grasp_signature", {})
    if not isinstance(grasp, dict):
        grasp = {}
    vec.append(_safe_float(grasp.get("stability_score")))
    vec.append(_safe_float(grasp.get("tilt_during_interaction")))

    # --- NEW: Orientation (3) ---
    orientation = window.get("orientation", {})
    if not isinstance(orientation, dict):
        orientation = {}
    vec.append(_safe_float(orientation.get("dominant_axis")))
    vec.append(_safe_float(orientation.get("rotation_rate_mean")))
    vec.append(_safe_float(orientation.get("rotation_rate_stdev")))

    # --- NEW: Vibration signature (2) ---
    vibration = window.get("vibration", {})
    if not isinstance(vibration, dict):
        vibration = {}
    vec.append(_safe_float(vibration.get("frequency_peak")))
    vec.append(_safe_float(vibration.get("amplitude_peak")))

    # --- NEW: Device hold pattern (2) ---
    device_hold = window.get("device_hold", {})
    if not isinstance(device_hold, dict):
        device_hold = {}
    vec.append(_safe_float(device_hold.get("angle_mean")))
    vec.append(_safe_float(device_hold.get("angle_stdev")))

    # --- NEW: Motion complexity (1) ---
    vec.append(_safe_float(window.get("motion_complexity")))

    # --- NEW: Stillness ratio (1) ---
    vec.append(_safe_float(window.get("stillness_ratio")))

    # --- Padding / extended sensor features (8) ---
    # Pull from an extended features dict or list if available,
    # otherwise pad with zeros to reach 32 dimensions.
    extended = window.get("extended", {})
    if isinstance(extended, dict):
        ext_keys = [
            "magnetometer_magnitude",
            "barometer_delta",
            "proximity_events",
            "ambient_light_mean",
            "temperature_delta",
            "battery_drain_rate",
            "charging_state",
            "screen_brightness_mean",
        ]
        for key in ext_keys:
            vec.append(_safe_float(extended.get(key)))
    elif isinstance(extended, (list, tuple)):
        vec.extend(_safe_list(extended, 8))
    else:
        vec.extend([0.0] * 8)

    # Guarantee exact dimensionality
    if len(vec) < SENSOR_DIM:
        vec.extend([0.0] * (SENSOR_DIM - len(vec)))
    return vec[:SENSOR_DIM]
