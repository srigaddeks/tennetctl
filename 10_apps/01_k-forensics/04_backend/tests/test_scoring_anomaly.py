"""Tests for 03_kbio._scoring.anomaly_scorer — five anomaly signals."""
import importlib

import pytest

_anomaly = importlib.import_module("03_kbio._scoring.anomaly_scorer")


# ---------------------------------------------------------------------------
# consistency_score
# ---------------------------------------------------------------------------

class TestConsistencyScore:
    def test_stable_session(self):
        """Low-variance history -> consistency near 1.0."""
        result = _anomaly.compute_consistency_score([0.1, 0.12, 0.11, 0.10, 0.13])
        assert result > 0.9

    def test_erratic_session(self):
        """High-variance history -> low consistency."""
        result = _anomaly.compute_consistency_score([0.0, 1.0, 0.0, 1.0, 0.0, 1.0])
        assert result < 0.5

    def test_insufficient_data(self):
        """Single point -> 0.5 (neutral)."""
        assert _anomaly.compute_consistency_score([0.3]) == 0.5

    def test_empty_returns_neutral(self):
        assert _anomaly.compute_consistency_score([]) == 0.5

    def test_two_identical_points(self):
        """Zero variance -> consistency = 1.0."""
        result = _anomaly.compute_consistency_score([0.2, 0.2])
        assert result == pytest.approx(1.0)

    def test_window_parameter(self):
        """Only last `window` values used."""
        # Long stable prefix + erratic tail
        stable = [0.1] * 20
        erratic = [0.0, 1.0, 0.0, 1.0]
        result = _anomaly.compute_consistency_score(stable + erratic, window=4)
        assert result < 0.5


# ---------------------------------------------------------------------------
# velocity_anomaly
# ---------------------------------------------------------------------------

class TestVelocityAnomaly:
    def test_stable_history(self):
        """Flat history -> low velocity."""
        result = _anomaly.compute_velocity_anomaly([0.1, 0.1, 0.1, 0.1])
        assert result < 0.5

    def test_spike(self):
        """Sudden jump -> high velocity."""
        result = _anomaly.compute_velocity_anomaly([0.1, 0.1, 0.1, 0.8])
        assert result > 0.5

    def test_single_point(self):
        """< 2 history points -> 0.0."""
        assert _anomaly.compute_velocity_anomaly([0.5]) == 0.0

    def test_empty(self):
        assert _anomaly.compute_velocity_anomaly([]) == 0.0

    def test_result_bounded(self):
        result = _anomaly.compute_velocity_anomaly([0.0, 1.0, 0.0, 1.0])
        assert 0.0 <= result <= 1.0


# ---------------------------------------------------------------------------
# takeover_probability
# ---------------------------------------------------------------------------

class TestTakeoverProbability:
    def test_stable_session_low(self):
        """Constant drift -> low takeover."""
        history = [0.1] * 10
        result = _anomaly.compute_takeover_probability(history)
        assert result["takeover_probability"] < 0.3
        assert result["changepoint_detected"] is False

    def test_sudden_spike_high(self):
        """Step change after baseline -> high takeover."""
        history = [0.1, 0.1, 0.1, 0.1, 0.1, 0.8, 0.85, 0.9]
        result = _anomaly.compute_takeover_probability(history)
        assert result["takeover_probability"] > 0.3

    def test_insufficient_data(self):
        """< baseline_count + 1 points -> all zeros."""
        result = _anomaly.compute_takeover_probability([0.1, 0.2, 0.3])
        assert result["takeover_probability"] == 0.0
        assert result["changepoint_detected"] is False

    def test_result_keys(self):
        result = _anomaly.compute_takeover_probability([0.1] * 10)
        expected_keys = {
            "takeover_probability", "cusum_signal", "velocity_signal",
            "concordance_signal", "changepoint_detected",
        }
        assert set(result.keys()) == expected_keys

    def test_modality_concordance_boosts(self):
        """Multiple modalities spiking together -> higher takeover."""
        history = [0.1, 0.1, 0.1, 0.1, 0.1, 0.5, 0.7]
        modality_history = {
            "keystroke": [0.1, 0.1, 0.1, 0.1, 0.1, 0.6, 0.8],
            "pointer": [0.1, 0.1, 0.1, 0.1, 0.1, 0.5, 0.7],
        }
        result = _anomaly.compute_takeover_probability(history, modality_history)
        assert result["concordance_signal"] > 0.0


# ---------------------------------------------------------------------------
# pattern_break
# ---------------------------------------------------------------------------

class TestPatternBreak:
    def test_no_baseline(self):
        """No baseline features -> 0.0."""
        result = _anomaly.compute_pattern_break(
            {"keystroke": [0.1] * 64}, None,
        )
        assert result == 0.0

    def test_same_features_low(self):
        """Identical features -> JSD near 0."""
        vec = [0.1] * 64
        result = _anomaly.compute_pattern_break(
            {"keystroke": vec}, {"keystroke": vec},
        )
        assert result < 0.1

    def test_different_features_high(self):
        """Very different distribution shapes -> higher pattern break."""
        # Uniform vs ramp produces high JSD since histograms differ
        current = {"keystroke": [1.0] * 64}
        baseline = {"keystroke": [float(i) for i in range(64)]}
        result = _anomaly.compute_pattern_break(current, baseline)
        assert result > 0.0

    def test_empty_features(self):
        result = _anomaly.compute_pattern_break({}, {})
        assert result == 0.0


# ---------------------------------------------------------------------------
# compute_all_anomaly_scores (orchestrator)
# ---------------------------------------------------------------------------

class TestAllAnomalyScores:
    def test_returns_all_keys(self):
        """Verify the result has all five anomaly score keys."""
        result = _anomaly.compute_all_anomaly_scores(
            feature_vecs={"keystroke": [0.1] * 64},
            modality_drifts={"keystroke": 0.2},
            drift_history=[0.1, 0.1, 0.12, 0.11, 0.13, 0.1, 0.12],
            modality_drift_history=None,
            batch={},
            baseline_features=None,
        )
        assert "session_anomaly" in result
        assert "velocity_anomaly" in result
        assert "takeover" in result
        assert "pattern_break" in result
        assert "consistency" in result
        assert result["method"] == "v2_multi_signal"

    def test_all_scores_bounded(self):
        result = _anomaly.compute_all_anomaly_scores(
            feature_vecs={"keystroke": [0.1] * 64},
            modality_drifts={"keystroke": 0.2},
            drift_history=[0.1] * 10,
            modality_drift_history=None,
            batch={},
        )
        # session_anomaly can be -1 when insufficient modalities
        for key in ["velocity_anomaly", "pattern_break", "consistency"]:
            assert 0.0 <= result[key] <= 1.0
        assert isinstance(result["takeover"], dict)
        assert 0.0 <= result["takeover"]["takeover_probability"] <= 1.0
