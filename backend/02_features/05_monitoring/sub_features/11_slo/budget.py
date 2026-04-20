"""Pure compute module for SLO error budget calculation.

No I/O, no side effects. Thread-safe for use in workers and routes.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class BudgetSnapshot:
    """Immutable snapshot of error budget state at a point in time."""

    attainment_pct: Decimal
    """Observed success ratio as a percentage (0-100)."""

    budget_remaining_pct: Decimal
    """Percentage of the error budget remaining. Negative = over budget."""

    budget_remaining_events: int
    """Count of events still permitted to fail within the budget."""

    is_breached: bool
    """Whether attainment_pct fell below target_pct."""


def compute_budget(
    target_pct: float,
    good_count: int,
    total_count: int,
) -> BudgetSnapshot:
    """Compute error budget state for an SLO window.

    Args:
        target_pct: Target success percentage (e.g., 99.9 for "three nines").
        good_count: Count of successful/good events.
        total_count: Total count of events.

    Returns:
        BudgetSnapshot with attainment, budget remaining, and breach status.

    Examples:
        >>> compute_budget(99.9, 999500, 1000000)
        BudgetSnapshot(
            attainment_pct=Decimal('99.95000'),
            budget_remaining_pct=Decimal('50.0'),
            budget_remaining_events=500,
            is_breached=False
        )

        >>> compute_budget(99.9, 998000, 1000000)
        BudgetSnapshot(
            attainment_pct=Decimal('99.80000'),
            budget_remaining_pct=Decimal('-100.0'),
            budget_remaining_events=-1000,
            is_breached=True
        )
    """
    # Avoid division by zero: 100% attainment if no events.
    if total_count == 0:
        return BudgetSnapshot(
            attainment_pct=Decimal("100.0"),
            budget_remaining_pct=Decimal("100.0"),
            budget_remaining_events=0,
            is_breached=False,
        )

    # Attainment: (good / total) * 100, rounded to 5 decimals.
    attainment = (Decimal(good_count) / Decimal(total_count)) * Decimal(100)
    attainment_pct = attainment.quantize(Decimal("0.00001"))

    # Error budget as a percentage of total.
    target_decimal = Decimal(str(target_pct))
    error_budget_pct = Decimal(100) - target_decimal

    # Observed error rate as a percentage.
    observed_error_pct = Decimal(100) - attainment_pct

    # How much of the error budget remains (can be negative).
    budget_remaining_pct = (
        (error_budget_pct - observed_error_pct) / error_budget_pct * Decimal(100)
    ).quantize(Decimal("0.1"))

    # Budget remaining in event count.
    # error_budget_events = total_count * (error_budget_pct / 100)
    # budget_remaining_events = error_budget_events - error_count
    error_count = total_count - good_count
    error_budget_events = int(total_count * float(error_budget_pct) / 100)
    budget_remaining_events = error_budget_events - error_count

    is_breached = attainment_pct < target_decimal

    return BudgetSnapshot(
        attainment_pct=attainment_pct,
        budget_remaining_pct=budget_remaining_pct,
        budget_remaining_events=budget_remaining_events,
        is_breached=is_breached,
    )


__all__ = ["BudgetSnapshot", "compute_budget"]
