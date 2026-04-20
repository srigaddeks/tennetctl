"""Pure compute module for SLO multi-window burn rate calculation.

Google SRE burn rate: how fast the error budget is being consumed.
Multiplier > 1.0 means exceeding the budget allocation for the given window.

No I/O, no side effects. Thread-safe for use in workers and routes.
"""

from __future__ import annotations


def compute_burn_rate(
    error_rate_observed: float,
    target_error_rate: float,
    window_seconds: int,
    full_window_seconds: int,
) -> float:
    """Compute burn rate multiplier for an observation window.

    Burn rate = how many times faster than budget the SLO is consuming error budget.
    Formula: (observed_error_rate / target_error_rate) * (full_window_seconds / window_seconds)

    Args:
        error_rate_observed: Fraction of errors observed in the window (0.0–1.0).
        target_error_rate: Allowed error fraction for the full SLO window (0.001 for 99.9%).
        window_seconds: Seconds of observation (e.g., 3600 for 1h).
        full_window_seconds: Full SLO window in seconds (e.g., 2592000 for 30d).

    Returns:
        Burn rate multiplier. 1.0 = on budget, 14.4 = 14.4× budget, 0.5 = half budget.

    Examples:
        >>> compute_burn_rate(0.0144, 0.001, 3600, 2592000)
        14.4

        >>> compute_burn_rate(0.001, 0.001, 3600, 2592000)
        1.0

        >>> compute_burn_rate(0.0006, 0.001, 3600, 2592000)
        0.6
    """
    if target_error_rate <= 0:
        return 0.0
    if window_seconds <= 0:
        return 0.0

    # Burn rate = (observed / target) scaled to full window.
    # Scaling: if we observe at rate X for Y seconds in a Z-second window,
    # we'd observe at rate X * (Z/Y) for the full window.
    burn = (error_rate_observed / target_error_rate) * (full_window_seconds / window_seconds)
    return float(burn)


def multi_window_burn(
    error_rates_by_window: dict[str, float],
    target_error_rate: float,
    full_window_seconds: int,
) -> dict[str, float]:
    """Compute burn rate multipliers across multiple observation windows.

    Args:
        error_rates_by_window: Dict of window name to observed error rate.
            Expected keys: "1h", "6h", "24h", "3d".
        target_error_rate: Allowed error fraction (0.001 for 99.9%).
        full_window_seconds: Full SLO window in seconds (e.g., 2592000 for 30d).

    Returns:
        Dict mapping window name to burn rate multiplier.
    """
    window_to_seconds = {
        "1h": 3600,
        "6h": 21600,
        "24h": 86400,
        "3d": 259200,
    }

    return {
        window: compute_burn_rate(
            error_rates_by_window[window],
            target_error_rate,
            window_to_seconds[window],
            full_window_seconds,
        )
        for window in ["1h", "6h", "24h", "3d"]
        if window in error_rates_by_window
    }


__all__ = ["compute_burn_rate", "multi_window_burn"]
