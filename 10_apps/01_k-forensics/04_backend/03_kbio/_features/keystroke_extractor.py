"""Keystroke feature extractor (V2).

Extracts a 64-dimensional feature vector from a keystroke telemetry window.
Enhanced from V1's _flatten_keystroke_features with:
  - Reduced zone transition matrix (top 30 by variance, not all 100)
  - Compressed bigram velocity histogram (5 bins, down from 10)
  - NEW trigraph timing patterns (2 values)

Dimension budget:
  zone_transition_top30  = 30
  zone_dwell_means       = 10
  zone_dwell_stdevs      = 10
  rhythm                 =  5
  error_proxy            =  2
  bigram_velocity_hist   =  5
  trigraph_timing        =  2
  TOTAL                  = 64
"""
from __future__ import annotations

from typing import Any

from ._helpers import _safe_float, _safe_list

# Dimension constant
KEYSTROKE_DIM = 64

# Indices of the 30 most discriminative zone-transition cells.
# In a 10x10 matrix (row-major), these are the positions that
# typically carry the highest inter-user variance based on
# empirical analysis of keyboard zone bigrams.  Row = from-zone,
# col = to-zone.  Diagonal + near-diagonal transitions dominate.
_TOP30_TRANSITION_INDICES: list[int] = [
    0, 1, 2, 10, 11, 12, 20, 21, 22,   # top-left 3x3
    33, 34, 43, 44,                       # middle cluster
    55, 56, 65, 66,                       # centre-right
    77, 78, 87, 88,                       # lower-right cluster
    3, 30, 45, 54, 67, 76, 89, 98,       # off-diagonal transitions
    99,                                    # bottom-right corner
]


def _select_top_transitions(
    matrix: list[float],
    indices: list[int],
) -> list[float]:
    """Pick values at *indices* from a flat 100-element matrix."""
    out: list[float] = []
    for idx in indices:
        if 0 <= idx < len(matrix):
            out.append(matrix[idx])
        else:
            out.append(0.0)
    return out


def _compress_histogram(
    bins: list[float],
    target_len: int,
) -> list[float]:
    """Compress a histogram by averaging adjacent bins to reach *target_len*.

    If *bins* is already <= *target_len*, pads with 0.0.
    """
    if len(bins) <= target_len:
        result = list(bins)
        result.extend([0.0] * (target_len - len(result)))
        return result[:target_len]

    # Average adjacent pairs to compress
    ratio = len(bins) / target_len
    compressed: list[float] = []
    for i in range(target_len):
        start = int(i * ratio)
        end = int((i + 1) * ratio)
        if end <= start:
            end = start + 1
        segment = bins[start:end]
        avg = sum(segment) / len(segment) if segment else 0.0
        compressed.append(avg)
    return compressed


def extract_keystroke_features(window: dict[str, Any]) -> list[float]:
    """Extract 64-dimensional keystroke feature vector from a window.

    Args:
        window: Raw keystroke telemetry window dict.  Expected keys:
            zone_transition_matrix (list[100]),
            zone_dwell_means (list[10]),
            zone_dwell_stdevs (list[10]),
            rhythm (dict), error_proxy (dict),
            bigram_velocity_histogram (list[>=5]),
            trigraph_timing (dict).

    Returns:
        list[float] of exactly 64 elements.  Returns all-zeros on
        missing/empty input.
    """
    if not window or not isinstance(window, dict):
        return [0.0] * KEYSTROKE_DIM

    vec: list[float] = []

    # --- Zone transition matrix: top 30 values (30) ---
    full_matrix = _safe_list(window.get("zone_transition_matrix"), 100)
    vec.extend(_select_top_transitions(full_matrix, _TOP30_TRANSITION_INDICES))

    # --- Zone dwell means (10) ---
    vec.extend(_safe_list(window.get("zone_dwell_means"), 10))

    # --- Zone dwell stdevs (10) ---
    vec.extend(_safe_list(window.get("zone_dwell_stdevs"), 10))

    # --- Rhythm features (5) ---
    rhythm = window.get("rhythm", {})
    if not isinstance(rhythm, dict):
        rhythm = {}
    vec.append(_safe_float(rhythm.get("kps_mean")))
    vec.append(_safe_float(rhythm.get("kps_stdev")))
    vec.append(_safe_float(rhythm.get("burst_count")))
    vec.append(_safe_float(rhythm.get("burst_length_mean")))
    vec.append(_safe_float(rhythm.get("pause_count")))

    # --- Error proxy (2) ---
    error = window.get("error_proxy", {})
    if not isinstance(error, dict):
        error = {}
    vec.append(_safe_float(error.get("backspace_rate")))
    vec.append(_safe_float(error.get("rapid_same_zone_count")))

    # --- Bigram velocity histogram: compressed to 5 bins (5) ---
    raw_bigram = _safe_list(window.get("bigram_velocity_histogram"), 10)
    vec.extend(_compress_histogram(raw_bigram, 5))

    # --- NEW: Trigraph timing patterns (2) ---
    # Top 2 most discriminative trigraph mean timings.
    # Expected input: trigraph_timing dict with keys like
    # "top_trigraph_1_ms", "top_trigraph_2_ms" or a list.
    trigraph = window.get("trigraph_timing", {})
    if isinstance(trigraph, dict):
        vec.append(_safe_float(trigraph.get("top_trigraph_1_ms")))
        vec.append(_safe_float(trigraph.get("top_trigraph_2_ms")))
    elif isinstance(trigraph, (list, tuple)):
        vals = _safe_list(trigraph, 2)
        vec.extend(vals)
    else:
        vec.extend([0.0, 0.0])

    # Guarantee exact dimensionality
    if len(vec) < KEYSTROKE_DIM:
        vec.extend([0.0] * (KEYSTROKE_DIM - len(vec)))
    return vec[:KEYSTROKE_DIM]
