"""Test error budget calculation logic."""

from decimal import Decimal
import pytest

from importlib import import_module

_budget = import_module("backend.02_features.05_monitoring.sub_features.11_slo.budget")


class TestBudgetCalculation:
    """Test compute_budget with exact AC-2 examples."""

    def test_fifty_percent_budget_remaining(self):
        """AC-2: target=99.9%, good=999500, total=1000000 → 50% budget remaining."""
        result = _budget.compute_budget(99.9, 999500, 1000000)

        assert result.attainment_pct == Decimal("99.95000")
        assert result.budget_remaining_pct == Decimal("50.0")
        assert result.budget_remaining_events == 500
        assert result.is_breached is False

    def test_over_budget_exhaustion(self):
        """AC-2: target=99.9%, good=998000, total=1000000 → over budget."""
        result = _budget.compute_budget(99.9, 998000, 1000000)

        assert result.attainment_pct == Decimal("99.80000")
        assert result.budget_remaining_pct == Decimal("-100.0")
        assert result.budget_remaining_events == -1000
        assert result.is_breached is True

    def test_perfect_attainment(self):
        """All events successful."""
        result = _budget.compute_budget(99.0, 1000, 1000)

        assert result.attainment_pct == Decimal("100.00000")
        assert result.budget_remaining_pct == Decimal("100.0")
        assert result.is_breached is False

    def test_zero_events(self):
        """No events yet (safe default)."""
        result = _budget.compute_budget(99.9, 0, 0)

        assert result.attainment_pct == Decimal("100.0")
        assert result.budget_remaining_pct == Decimal("100.0")
        assert result.is_breached is False

    def test_zero_good_events(self):
        """100% error rate."""
        result = _budget.compute_budget(99.0, 0, 1000)

        assert result.attainment_pct == Decimal("0.00000")
        assert result.is_breached is True
