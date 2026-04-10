"""Tests for 03_kbio._scoring.drift_scorer — per-modality drift computation."""
import importlib

import pytest

_drift = importlib.import_module("03_kbio._scoring.drift_scorer")
_math = importlib.import_module("03_kbio._scoring._math")


# ---------------------------------------------------------------------------
# compute_modality_drift
# ---------------------------------------------------------------------------

class TestModalityDrift:
    def test_identical_vectors_zero_drift(self):
        """Same L2-normalized vector as centroid -> drift near 0."""
        vec = _math.l2_normalize([0.1] * 64)
        result = _drift.compute_modality_drift(vec, vec, 0.15, 0.05)
        assert result["drift"] >= 0.0
        assert result["drift"] < 0.1
        assert result["raw_distance"] == pytest.approx(0.0, abs=0.01)

    def test_orthogonal_vectors_high_drift(self):
        """Orthogonal L2-normalized vectors -> raw_distance=1.0 -> high drift."""
        a = _math.l2_normalize([1.0] + [0.0] * 63)
        b = _math.l2_normalize([0.0] + [1.0] + [0.0] * 62)
        result = _drift.compute_modality_drift(a, b, 0.15, 0.05)
        assert result["drift"] > 0.5
        assert result["raw_distance"] == pytest.approx(1.0)

    def test_missing_centroid_returns_negative(self):
        """Empty centroid -> drift == -1.0."""
        result = _drift.compute_modality_drift([0.1] * 64, [], 0.15, 0.05)
        assert result["drift"] == -1.0

    def test_missing_feature_vec_returns_negative(self):
        result = _drift.compute_modality_drift([], [0.1] * 64, 0.15, 0.05)
        assert result["drift"] == -1.0

    def test_zero_stdev_fallback(self):
        """stdev=0 -> raw distance used directly, clamped to [0, 1]."""
        vec = _math.l2_normalize([0.1] * 64)
        centroid = _math.l2_normalize([0.2] * 64)
        result = _drift.compute_modality_drift(vec, centroid, 0.15, 0.0)
        assert result["z_score"] == 0.0
        assert result["drift"] >= 0.0
        assert result["drift"] <= 1.0

    def test_result_keys(self):
        result = _drift.compute_modality_drift([0.1] * 32, [0.1] * 32, 0.1, 0.05)
        assert "drift" in result
        assert "z_score" in result
        assert "raw_distance" in result


# ---------------------------------------------------------------------------
# compute_all_modality_drifts
# ---------------------------------------------------------------------------

class TestAllModalityDrifts:
    def test_computes_all_available_modalities(self):
        """Cluster with keystroke + pointer centroids -> both get drift scores."""
        feature_vecs = {
            "keystroke": [0.1] * 64,
            "pointer": [0.1] * 32,
        }
        cluster = {
            "keystroke_centroid": [0.1] * 64,
            "pointer_centroid": [0.1] * 32,
            "per_modality_intra": {
                "keystroke": {"mean": 0.15, "stdev": 0.05},
                "pointer": {"mean": 0.12, "stdev": 0.04},
            },
        }
        results = _drift.compute_all_modality_drifts(feature_vecs, cluster)
        assert "keystroke" in results
        assert "pointer" in results
        assert results["keystroke"]["drift"] >= 0.0
        assert results["pointer"]["drift"] >= 0.0

    def test_missing_modality_skipped(self):
        """Cluster has keystroke centroid but batch only has pointer -> keystroke skipped."""
        feature_vecs = {
            "pointer": [0.1] * 32,
        }
        cluster = {
            "keystroke_centroid": [0.1] * 64,
            "pointer_centroid": [0.1] * 32,
            "per_modality_intra": {
                "keystroke": {"mean": 0.15, "stdev": 0.05},
                "pointer": {"mean": 0.12, "stdev": 0.04},
            },
        }
        results = _drift.compute_all_modality_drifts(feature_vecs, cluster)
        assert "keystroke" not in results
        assert "pointer" in results

    def test_missing_centroid_skipped(self):
        """Feature vec present but centroid missing -> that modality is skipped."""
        feature_vecs = {"keystroke": [0.1] * 64}
        cluster = {"per_modality_intra": {}}
        results = _drift.compute_all_modality_drifts(feature_vecs, cluster)
        assert len(results) == 0

    def test_empty_inputs(self):
        results = _drift.compute_all_modality_drifts({}, {})
        assert results == {}

    def test_missing_intra_stats_defaults(self):
        """No per_modality_intra -> uses mean=0, stdev=0 (zero stdev fallback)."""
        feature_vecs = {"keystroke": [0.1] * 64}
        cluster = {"keystroke_centroid": [0.2] * 64}
        results = _drift.compute_all_modality_drifts(feature_vecs, cluster)
        assert "keystroke" in results
        # zero stdev fallback -> z_score=0
        assert results["keystroke"]["z_score"] == 0.0
