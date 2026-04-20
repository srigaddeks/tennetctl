"""Test burn rate calculation logic."""

import pytest

from importlib import import_module

_burn_rate = import_module("backend.02_features.05_monitoring.sub_features.11_slo.burn_rate")


class TestBurnRateCalculation:
    """Test compute_burn_rate with AC-3 examples."""

    def test_fast_burn_exact_14_4x(self):
        """AC-3: 1h error_rate=0.0144 with target=0.001 → 14.4× burn rate."""
        # target_error_rate = 0.001 (0.1% = 99.9%)
        # observed_error_rate = 0.0144 (1.44%)
        # window = 3600s (1h), full_window = 2592000s (30d)
        result = _burn_rate.compute_burn_rate(
            error_rate_observed=0.0144,
            target_error_rate=0.001,
            window_seconds=3600,
            full_window_seconds=2592000,
        )
        assert result == pytest.approx(14.4, rel=1e-6)

    def test_on_budget(self):
        """Observed error rate exactly equals target."""
        result = _burn_rate.compute_burn_rate(
            error_rate_observed=0.001,
            target_error_rate=0.001,
            window_seconds=3600,
            full_window_seconds=2592000,
        )
        assert result == pytest.approx(1.0, rel=1e-6)

    def test_half_budget(self):
        """Observed error rate is 50% of target."""
        result = _burn_rate.compute_burn_rate(
            error_rate_observed=0.0005,
            target_error_rate=0.001,
            window_seconds=3600,
            full_window_seconds=2592000,
        )
        assert result == pytest.approx(0.5, rel=1e-6)

    def test_zero_errors_zero_burn(self):
        """No errors observed."""
        result = _burn_rate.compute_burn_rate(
            error_rate_observed=0.0,
            target_error_rate=0.001,
            window_seconds=3600,
            full_window_seconds=2592000,
        )
        assert result == pytest.approx(0.0, rel=1e-6)

    def test_multi_window_burn(self):
        """Test multi_window_burn with multiple windows."""
        result = _burn_rate.multi_window_burn(
            {
                "1h": 0.0144,
                "6h": 0.005,
                "24h": 0.0015,
                "3d": 0.0008,
            },
            target_error_rate=0.001,
            full_window_seconds=2592000,
        )

        assert result["1h"] == pytest.approx(14.4, rel=1e-6)
        assert result["6h"] == pytest.approx(5.0, rel=1e-6)
        assert result["24h"] == pytest.approx(1.5, rel=1e-6)
        assert result["3d"] == pytest.approx(0.8, rel=1e-6)
