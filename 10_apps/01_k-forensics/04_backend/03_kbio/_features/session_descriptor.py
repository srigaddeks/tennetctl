"""Session context descriptor for cluster assignment (V2 - NEW).

Computes a structured descriptor from session context and optional
feature vectors.  Used by the profile engine to select or create
the appropriate behavioral cluster/centroid for comparison.

No external dependencies.  All percentiles use heuristic ranges
derived from population-level observations (no historical DB queries).
"""
from __future__ import annotations

from typing import Any

from ._helpers import _safe_float


# ---------------------------------------------------------------------------
# Heuristic ranges for percentile estimation
# ---------------------------------------------------------------------------

# Typing speed (keys per second) — population distribution heuristics
_KPS_P10 = 1.5   # slow typist
_KPS_P90 = 7.0   # fast typist

# Backspace rate — fraction of total keystrokes
_ERR_P10 = 0.01
_ERR_P90 = 0.15

# Mouse path efficiency — 1.0 = perfectly straight, lower = less precise
_PRECISION_P10 = 0.3
_PRECISION_P90 = 0.95


def _to_percentile(value: float, p10: float, p90: float) -> float:
    """Map a raw value to an approximate 0-1 percentile using linear interpolation.

    Values below p10 map to 0.0, above p90 map to 1.0.
    """
    if p90 <= p10:
        return 0.5
    clamped = max(p10, min(p90, value))
    return (clamped - p10) / (p90 - p10)


def _classify_time_bucket(hour: int) -> str:
    """Classify hour (0-23) into a time-of-day bucket."""
    if 6 <= hour <= 11:
        return "morning"
    if 12 <= hour <= 17:
        return "afternoon"
    if 18 <= hour <= 22:
        return "evening"
    return "night"


def _classify_screen(width: int) -> str:
    """Classify screen width into a size class."""
    if width < 768:
        return "small"
    if width <= 1024:
        return "medium"
    if width <= 1440:
        return "large"
    return "xlarge"


def compute_session_descriptor(
    context: dict[str, Any],
    keystroke_features: list[float] | None = None,
    pointer_features: list[float] | None = None,
) -> dict[str, Any]:
    """Compute session context descriptor for cluster matching.

    Args:
        context: Session context dict with keys like platform,
            input_method, hour, screen_width, locale.
        keystroke_features: Optional 64-dim keystroke vector (output of
            extract_keystroke_features).  Used for typing_speed and
            error_rate percentile estimation.
        pointer_features: Optional 32-dim pointer vector (output of
            extract_pointer_features).  Used for mouse_precision
            percentile estimation.

    Returns:
        Dict with keys: platform, input_method, time_bucket,
        screen_class, locale, typing_speed_percentile,
        error_rate_percentile, mouse_precision_percentile.
    """
    if not context or not isinstance(context, dict):
        context = {}

    # --- Platform ---
    platform = str(context.get("platform", "web_desktop"))
    valid_platforms = {"web_desktop", "web_mobile", "web_tablet"}
    if platform not in valid_platforms:
        platform = "web_desktop"

    # --- Input method ---
    input_method = str(context.get("input_method", "keyboard_mouse"))
    valid_methods = {"keyboard_mouse", "touch", "mixed"}
    if input_method not in valid_methods:
        input_method = "keyboard_mouse"

    # --- Time bucket ---
    raw_hour = context.get("hour", context.get("time_hour", 12))
    try:
        hour = int(raw_hour) % 24
    except (TypeError, ValueError):
        hour = 12
    time_bucket = _classify_time_bucket(hour)

    # --- Screen class ---
    raw_width = context.get("screen_width", context.get("viewport_width", 1280))
    try:
        screen_width = int(raw_width)
    except (TypeError, ValueError):
        screen_width = 1280
    screen_class = _classify_screen(screen_width)

    # --- Locale ---
    locale = str(context.get("locale", "en-US"))

    # --- Typing speed percentile (from keystroke features) ---
    typing_speed_pct = 0.5  # default midpoint
    if keystroke_features and len(keystroke_features) >= 51:
        # Rhythm features start at index 50 in the 64-dim vector.
        # Index 50 = kps_mean.
        kps_mean = _safe_float(keystroke_features[50])
        if kps_mean > 0.0:
            typing_speed_pct = _to_percentile(kps_mean, _KPS_P10, _KPS_P90)

    # --- Error rate percentile (from keystroke features) ---
    error_rate_pct = 0.5
    if keystroke_features and len(keystroke_features) >= 56:
        # Index 55 = backspace_rate (first error_proxy value).
        backspace_rate = _safe_float(keystroke_features[55])
        if backspace_rate > 0.0:
            error_rate_pct = _to_percentile(backspace_rate, _ERR_P10, _ERR_P90)

    # --- Mouse precision percentile (from pointer features) ---
    mouse_precision_pct = 0.5
    if pointer_features and len(pointer_features) >= 2:
        # Index 1 = path_efficiency in the 32-dim vector.
        path_efficiency = _safe_float(pointer_features[1])
        if path_efficiency > 0.0:
            mouse_precision_pct = _to_percentile(
                path_efficiency, _PRECISION_P10, _PRECISION_P90,
            )

    return {
        "platform": platform,
        "input_method": input_method,
        "time_bucket": time_bucket,
        "screen_class": screen_class,
        "locale": locale,
        "typing_speed_percentile": round(typing_speed_pct, 4),
        "error_rate_percentile": round(error_rate_pct, 4),
        "mouse_precision_percentile": round(mouse_precision_pct, 4),
    }
