"""Tests for 03_kbio._features — keystroke, pointer, normalizer."""
import importlib
import math

import pytest

_keystroke = importlib.import_module("03_kbio._features.keystroke_extractor")
_pointer = importlib.import_module("03_kbio._features.pointer_extractor")
_normalizer = importlib.import_module("03_kbio._features.normalizer")


# ---------------------------------------------------------------------------
# Keystroke extractor
# ---------------------------------------------------------------------------

class TestKeystrokeExtractor:
    def test_empty_window_returns_64d_zeros(self):
        result = _keystroke.extract_keystroke_features({})
        assert result == [0.0] * 64

    def test_none_window_returns_64d_zeros(self):
        result = _keystroke.extract_keystroke_features(None)
        assert result == [0.0] * 64

    def test_dimension_exact(self):
        """Output is always exactly 64 dimensions."""
        window = {
            "zone_transition_matrix": [0.1] * 100,
            "zone_dwell_means": [50.0] * 10,
            "zone_dwell_stdevs": [10.0] * 10,
            "rhythm": {
                "kps_mean": 3.5, "kps_stdev": 0.5,
                "burst_count": 3, "burst_length_mean": 5,
                "pause_count": 2,
            },
            "error_proxy": {"backspace_rate": 0.05, "rapid_same_zone_count": 1},
            "bigram_velocity_histogram": [0.1] * 10,
        }
        result = _keystroke.extract_keystroke_features(window)
        assert len(result) == 64

    def test_full_window_returns_nonzero(self):
        window = {
            "zone_transition_matrix": [0.1] * 100,
            "zone_dwell_means": [50.0] * 10,
            "zone_dwell_stdevs": [10.0] * 10,
            "rhythm": {"kps_mean": 3.5, "kps_stdev": 0.5,
                        "burst_count": 3, "burst_length_mean": 5,
                        "pause_count": 2},
            "error_proxy": {"backspace_rate": 0.05, "rapid_same_zone_count": 1},
            "bigram_velocity_histogram": [0.1] * 10,
        }
        result = _keystroke.extract_keystroke_features(window)
        assert len(result) == 64
        assert any(v != 0.0 for v in result)

    def test_partial_window_pads_to_64(self):
        """Window with only some keys still produces 64d."""
        window = {"zone_dwell_means": [50.0] * 10}
        result = _keystroke.extract_keystroke_features(window)
        assert len(result) == 64

    def test_trigraph_timing_as_list(self):
        """Trigraph timing provided as list instead of dict."""
        window = {
            "zone_transition_matrix": [0.0] * 100,
            "zone_dwell_means": [0.0] * 10,
            "zone_dwell_stdevs": [0.0] * 10,
            "rhythm": {},
            "error_proxy": {},
            "bigram_velocity_histogram": [0.0] * 10,
            "trigraph_timing": [150.0, 200.0],
        }
        result = _keystroke.extract_keystroke_features(window)
        assert len(result) == 64
        # Last two values should be the trigraph timings
        assert result[62] == pytest.approx(150.0)
        assert result[63] == pytest.approx(200.0)


# ---------------------------------------------------------------------------
# Pointer extractor
# ---------------------------------------------------------------------------

class TestPointerExtractor:
    def test_empty_returns_32d(self):
        result = _pointer.extract_pointer_features({})
        assert result == [0.0] * 32

    def test_none_returns_32d(self):
        result = _pointer.extract_pointer_features(None)
        assert result == [0.0] * 32

    def test_dimension_exact(self):
        window = {
            "movement": {
                "total_distance": 500, "path_efficiency": 0.8,
                "velocity_mean": 200, "velocity_stdev": 50,
                "acceleration_mean": 100, "direction_changes": 5,
                "curvature_mean": 0.3, "angle_histogram": [0.1] * 8,
            },
            "clicks": {
                "count": 3, "hold_mean_ms": 100,
                "approach_velocity_profile": [0.1] * 5,
                "overshoot_rate": 0.1,
            },
            "idle": {
                "count": 2, "micro_movement_amplitude": 0.005,
                "micro_movement_frequency": 5,
            },
        }
        result = _pointer.extract_pointer_features(window)
        assert len(result) == 32

    def test_full_window_nonzero(self):
        window = {
            "movement": {
                "total_distance": 500, "path_efficiency": 0.8,
                "velocity_mean": 200, "velocity_stdev": 50,
                "acceleration_mean": 100, "direction_changes": 5,
                "curvature_mean": 0.3, "angle_histogram": [0.1] * 8,
            },
            "clicks": {"count": 3, "hold_mean_ms": 100,
                        "approach_velocity_profile": [0.1] * 5,
                        "overshoot_rate": 0.1},
            "idle": {"count": 2, "micro_movement_amplitude": 0.005,
                      "micro_movement_frequency": 5},
        }
        result = _pointer.extract_pointer_features(window)
        assert any(v != 0.0 for v in result)


# ---------------------------------------------------------------------------
# Normalizer
# ---------------------------------------------------------------------------

class TestNormalizer:
    def test_l2_unit_length(self):
        """Output has magnitude ~1.0."""
        vec = [3.0, 4.0, 0.0]
        result = _normalizer.l2_normalize(vec)
        magnitude = math.sqrt(sum(x * x for x in result))
        assert magnitude == pytest.approx(1.0, abs=1e-9)

    def test_zero_vector_unchanged(self):
        vec = [0.0, 0.0, 0.0]
        result = _normalizer.l2_normalize(vec)
        assert result == vec

    def test_normalize_features_routes_correctly(self):
        """normalize_features extracts and L2-normalizes per modality."""
        raw = {
            "keystroke_windows": [{
                "zone_transition_matrix": [0.1] * 100,
                "zone_dwell_means": [50.0] * 10,
                "zone_dwell_stdevs": [10.0] * 10,
                "rhythm": {"kps_mean": 3.5, "kps_stdev": 0.5,
                            "burst_count": 3, "burst_length_mean": 5,
                            "pause_count": 2},
                "error_proxy": {"backspace_rate": 0.05, "rapid_same_zone_count": 1},
                "bigram_velocity_histogram": [0.1] * 10,
            }],
            "pointer_windows": [{
                "movement": {"total_distance": 500, "path_efficiency": 0.8,
                              "velocity_mean": 200, "velocity_stdev": 50,
                              "acceleration_mean": 100, "direction_changes": 5,
                              "curvature_mean": 0.3, "angle_histogram": [0.1] * 8},
                "clicks": {"count": 3, "hold_mean_ms": 100,
                            "approach_velocity_profile": [0.1] * 5,
                            "overshoot_rate": 0.1},
                "idle": {"count": 2, "micro_movement_amplitude": 0.005,
                          "micro_movement_frequency": 5},
            }],
        }
        result = _normalizer.normalize_features(raw)
        assert "keystroke" in result
        assert "pointer" in result
        assert len(result["keystroke"]) == 64
        assert len(result["pointer"]) == 32

        # Verify L2-normalized
        for modality in result:
            mag = math.sqrt(sum(x * x for x in result[modality]))
            assert mag == pytest.approx(1.0, abs=1e-6)

    def test_empty_windows_skipped(self):
        result = _normalizer.normalize_features({"keystroke_windows": []})
        assert "keystroke" not in result

    def test_all_zero_window_skipped(self):
        """All-zero features (empty window) should be skipped."""
        raw = {"keystroke_windows": [{}]}
        result = _normalizer.normalize_features(raw)
        assert "keystroke" not in result
