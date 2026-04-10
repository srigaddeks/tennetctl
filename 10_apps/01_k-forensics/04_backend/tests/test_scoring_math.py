"""Tests for 03_kbio._scoring._math — shared pure-math functions."""
import importlib
import math

import pytest

_math = importlib.import_module("03_kbio._scoring._math")


# ---------------------------------------------------------------------------
# sigmoid
# ---------------------------------------------------------------------------

class TestSigmoid:
    def test_midpoint(self):
        assert _math.sigmoid(0.0) == 0.5

    def test_positive_large(self):
        assert _math.sigmoid(10.0) > 0.99

    def test_negative_large(self):
        assert _math.sigmoid(-10.0) < 0.01

    def test_clamp_extreme_positive(self):
        """Extreme values are clamped to [-10, 10], no overflow."""
        result = _math.sigmoid(1_000_000.0)
        assert 0.0 < result <= 1.0

    def test_clamp_extreme_negative(self):
        result = _math.sigmoid(-1_000_000.0)
        assert 0.0 <= result < 1.0

    def test_monotonic(self):
        assert _math.sigmoid(-5.0) < _math.sigmoid(0.0) < _math.sigmoid(5.0)


# ---------------------------------------------------------------------------
# cosine_distance
# ---------------------------------------------------------------------------

class TestCosineDistance:
    def test_identical_vectors(self):
        assert _math.cosine_distance([1, 0], [1, 0]) == pytest.approx(0.0)

    def test_orthogonal_vectors(self):
        assert _math.cosine_distance([1, 0], [0, 1]) == pytest.approx(1.0)

    def test_opposite_vectors(self):
        assert _math.cosine_distance([1, 0], [-1, 0]) == pytest.approx(2.0)

    def test_empty_vectors(self):
        assert _math.cosine_distance([], []) == 1.0

    def test_different_lengths(self):
        assert _math.cosine_distance([1, 0], [1, 0, 0]) == 1.0

    def test_normalized_vectors(self):
        a = [1 / math.sqrt(2), 1 / math.sqrt(2)]
        assert _math.cosine_distance(a, a) == pytest.approx(0.0, abs=1e-9)


# ---------------------------------------------------------------------------
# l2_normalize
# ---------------------------------------------------------------------------

class TestL2Normalize:
    def test_unit_vector(self):
        result = _math.l2_normalize([3.0, 4.0])
        magnitude = math.sqrt(sum(x * x for x in result))
        assert magnitude == pytest.approx(1.0, abs=1e-9)

    def test_zero_vector_unchanged(self):
        assert _math.l2_normalize([0.0, 0.0, 0.0]) == [0.0, 0.0, 0.0]

    def test_already_normalized(self):
        vec = [1.0, 0.0, 0.0]
        assert _math.l2_normalize(vec) == pytest.approx(vec)


# ---------------------------------------------------------------------------
# pearson
# ---------------------------------------------------------------------------

class TestPearson:
    def test_perfect_positive_correlation(self):
        assert _math.pearson([1, 2, 3], [1, 2, 3]) == pytest.approx(1.0, abs=1e-9)

    def test_perfect_negative_correlation(self):
        assert _math.pearson([1, 2, 3], [3, 2, 1]) == pytest.approx(-1.0, abs=1e-9)

    def test_too_few_points_returns_zero(self):
        assert _math.pearson([1, 2], [1, 2]) == 0.0

    def test_single_point_returns_zero(self):
        assert _math.pearson([1], [1]) == 0.0

    def test_zero_variance_returns_zero(self):
        assert _math.pearson([5, 5, 5], [1, 2, 3]) == 0.0

    def test_different_lengths_uses_minimum(self):
        # Uses min(len(x), len(y)) = 3 elements
        result = _math.pearson([1, 2, 3, 4], [1, 2, 3])
        assert result == pytest.approx(1.0, abs=1e-9)


# ---------------------------------------------------------------------------
# jaccard
# ---------------------------------------------------------------------------

class TestJaccard:
    def test_identical_sets(self):
        assert _math.jaccard({1, 2}, {1, 2}) == pytest.approx(1.0)

    def test_disjoint_sets(self):
        assert _math.jaccard({1, 2}, {3, 4}) == pytest.approx(0.0)

    def test_both_empty(self):
        assert _math.jaccard(set(), set()) == 1.0

    def test_partial_overlap(self):
        # intersection={2}, union={1,2,3} -> 1/3
        assert _math.jaccard({1, 2}, {2, 3}) == pytest.approx(1.0 / 3.0)

    def test_subset(self):
        # intersection={1}, union={1,2} -> 0.5
        assert _math.jaccard({1}, {1, 2}) == pytest.approx(0.5)


# ---------------------------------------------------------------------------
# jensen_shannon
# ---------------------------------------------------------------------------

class TestJensenShannon:
    def test_identical_distributions(self):
        assert _math.jensen_shannon([0.5, 0.5], [0.5, 0.5]) == pytest.approx(0.0)

    def test_opposite_distributions(self):
        result = _math.jensen_shannon([1, 0], [0, 1])
        assert result == pytest.approx(1.0, abs=0.01)

    def test_empty_returns_zero(self):
        assert _math.jensen_shannon([], []) == 0.0

    def test_different_lengths_returns_zero(self):
        assert _math.jensen_shannon([1, 0], [1]) == 0.0

    def test_zero_sum_returns_zero(self):
        assert _math.jensen_shannon([0, 0], [1, 0]) == 0.0

    def test_similar_distributions_low(self):
        result = _math.jensen_shannon([0.5, 0.3, 0.2], [0.48, 0.32, 0.20])
        assert result < 0.1


# ---------------------------------------------------------------------------
# z_score
# ---------------------------------------------------------------------------

class TestZScore:
    def test_at_mean(self):
        assert _math.z_score(5.0, 5.0, 1.0) == pytest.approx(0.0)

    def test_one_sigma_above(self):
        assert _math.z_score(6.0, 5.0, 1.0) == pytest.approx(1.0)

    def test_two_sigma_below(self):
        assert _math.z_score(3.0, 5.0, 1.0) == pytest.approx(-2.0)

    def test_zero_stdev_returns_zero(self):
        assert _math.z_score(10.0, 5.0, 0.0) == 0.0

    def test_negative_stdev_returns_zero(self):
        assert _math.z_score(10.0, 5.0, -1.0) == 0.0


# ---------------------------------------------------------------------------
# ema_blend
# ---------------------------------------------------------------------------

class TestEmaBlend:
    def test_alpha_zero_keeps_old(self):
        assert _math.ema_blend(0.8, 0.2, 0.0) == pytest.approx(0.8)

    def test_alpha_one_takes_new(self):
        assert _math.ema_blend(0.8, 0.2, 1.0) == pytest.approx(0.2)

    def test_half_alpha_averages(self):
        assert _math.ema_blend(0.8, 0.2, 0.5) == pytest.approx(0.5)

    def test_typical_blend(self):
        result = _math.ema_blend(0.5, 1.0, 0.1)
        assert result == pytest.approx(0.55)


# ---------------------------------------------------------------------------
# clamp
# ---------------------------------------------------------------------------

class TestClamp:
    def test_within_range(self):
        assert _math.clamp(0.5, 0.0, 1.0) == 0.5

    def test_below_range(self):
        assert _math.clamp(-5.0, 0.0, 1.0) == 0.0

    def test_above_range(self):
        assert _math.clamp(99.0, 0.0, 1.0) == 1.0

    def test_at_boundary(self):
        assert _math.clamp(0.0, 0.0, 1.0) == 0.0
        assert _math.clamp(1.0, 0.0, 1.0) == 1.0
