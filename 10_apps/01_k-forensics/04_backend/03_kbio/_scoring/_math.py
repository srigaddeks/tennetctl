"""Shared pure-math functions for the kbio scoring engine.

Centralizes math utilities used across all scorers. No external
dependencies -- pure Python + stdlib math only.
"""
from __future__ import annotations

import math


def sigmoid(x: float) -> float:
    """Standard sigmoid function, clamped to avoid overflow."""
    x = max(-10.0, min(10.0, x))
    return 1.0 / (1.0 + math.exp(-x))


def cosine_distance(a: list[float], b: list[float]) -> float:
    """Cosine distance between two L2-normalized vectors.

    Returns 0.0 (identical) to 2.0 (opposite).
    Returns 1.0 (maximum ambiguity) if inputs are invalid.
    """
    if len(a) != len(b) or len(a) == 0:
        return 1.0
    dot = sum(x * y for x, y in zip(a, b))
    return 1.0 - dot


def l2_normalize(vec: list[float]) -> list[float]:
    """L2-normalize a vector. Returns zero vector if magnitude is 0."""
    magnitude = math.sqrt(sum(x * x for x in vec))
    if magnitude == 0.0:
        return vec
    return [x / magnitude for x in vec]


def pearson(x: list[float], y: list[float]) -> float:
    """Pearson correlation coefficient.

    Returns 0.0 if fewer than 3 data points or zero variance.
    """
    n = min(len(x), len(y))
    if n < 3:
        return 0.0

    x = x[:n]
    y = y[:n]

    mean_x = sum(x) / n
    mean_y = sum(y) / n

    cov = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
    std_x = math.sqrt(sum((xi - mean_x) ** 2 for xi in x))
    std_y = math.sqrt(sum((yi - mean_y) ** 2 for yi in y))

    if std_x == 0.0 or std_y == 0.0:
        return 0.0

    return cov / (std_x * std_y)


def jaccard(a: set, b: set) -> float:
    """Jaccard similarity coefficient. Both empty = 1.0."""
    if not a and not b:
        return 1.0
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)


def ema_blend(old: float, new: float, alpha: float) -> float:
    """Exponential moving average blend: alpha * new + (1 - alpha) * old."""
    return alpha * new + (1.0 - alpha) * old


def z_score(value: float, mean: float, stdev: float) -> float:
    """Z-score with stdev=0 guard (returns 0.0 when stdev is zero)."""
    if stdev <= 0.0:
        return 0.0
    return (value - mean) / stdev


def jensen_shannon(p: list[float], q: list[float]) -> float:
    """Jensen-Shannon divergence between two distributions.

    Both distributions must be the same length and non-negative.
    Returns 0.0 (identical) to 1.0 (maximally different).
    Returns 0.0 for invalid/empty inputs.
    """
    if len(p) != len(q) or len(p) == 0:
        return 0.0

    # Normalize to probability distributions
    sum_p = sum(p)
    sum_q = sum(q)
    if sum_p <= 0.0 or sum_q <= 0.0:
        return 0.0

    p_norm = [x / sum_p for x in p]
    q_norm = [x / sum_q for x in q]

    # Midpoint distribution
    m = [(pi + qi) / 2.0 for pi, qi in zip(p_norm, q_norm)]

    # KL divergence: KL(p||m) and KL(q||m)
    kl_pm = 0.0
    kl_qm = 0.0
    for pi, qi, mi in zip(p_norm, q_norm, m):
        if mi > 0.0:
            if pi > 0.0:
                kl_pm += pi * math.log2(pi / mi)
            if qi > 0.0:
                kl_qm += qi * math.log2(qi / mi)

    jsd = (kl_pm + kl_qm) / 2.0
    return clamp(jsd, 0.0, 1.0)


def clamp(value: float, lo: float, hi: float) -> float:
    """Clamp value to [lo, hi]."""
    return max(lo, min(hi, value))
