"""Tests for the kbio AI scoring pipeline."""
import pytest


class TestAnomalyScorer:
    def test_empty_features_returns_negative(self):
        import importlib
        scorer = importlib.import_module("03_kbio._scoring.anomaly_scorer")
        result = scorer.compute_anomaly_score({}, {}, {})
        assert result["anomaly_score"] == -1.0

    def test_single_modality_produces_score(self):
        import importlib
        scorer = importlib.import_module("03_kbio._scoring.anomaly_scorer")
        vecs = {"keystroke": [0.1] * 128}
        drifts = {"keystroke": 0.3}
        result = scorer.compute_anomaly_score(vecs, drifts, {})
        assert 0.0 <= result["anomaly_score"] <= 1.0
        assert "keystroke" in result["modality_anomalies"]

    def test_method_is_z_score_ensemble(self):
        import importlib
        scorer = importlib.import_module("03_kbio._scoring.anomaly_scorer")
        result = scorer.compute_anomaly_score({"keystroke": [0.1] * 10}, {"keystroke": 0.5}, {})
        assert result["method"] == "z_score_ensemble"


class TestTrustScorer:
    def test_high_trust_scenario(self):
        import importlib
        scorer = importlib.import_module("03_kbio._scoring.trust_scorer")
        result = scorer.compute_trust_score(
            drift_score=0.1, anomaly_score=0.1, bot_score=0.0,
            device_known=True, device_age_days=30,
            baseline_quality="strong", profile_maturity=0.9,
            session_state={"drift_history": [0.1, 0.1, 0.12, 0.09]},
            confidence=0.9,
        )
        assert result["trust_score"] >= 0.6
        assert result["trust_level"] in ("high", "medium")

    def test_low_trust_scenario(self):
        import importlib
        scorer = importlib.import_module("03_kbio._scoring.trust_scorer")
        result = scorer.compute_trust_score(
            drift_score=0.9, anomaly_score=0.8, bot_score=0.6,
            device_known=False, device_age_days=0,
            baseline_quality="insufficient", profile_maturity=0.1,
            session_state={"drift_history": [0.3, 0.5, 0.7, 0.9]},
            confidence=0.3,
        )
        assert result["trust_score"] <= 0.5
        assert result["trust_level"] in ("low", "critical")

    def test_neutral_when_no_data(self):
        import importlib
        scorer = importlib.import_module("03_kbio._scoring.trust_scorer")
        result = scorer.compute_trust_score(
            drift_score=-1.0, anomaly_score=-1.0, bot_score=0.0,
            device_known=True, device_age_days=0,
            baseline_quality="insufficient", profile_maturity=0.0,
            session_state={},
            confidence=0.0,
        )
        # Should be near neutral (0.5) due to low confidence
        assert 0.3 <= result["trust_score"] <= 0.7


class TestBotDetectorV2:
    def test_v2_returns_all_fields(self):
        import importlib
        detector = importlib.import_module("03_kbio._scoring.bot_detector")
        batch = {"keystroke_windows": [], "pointer_windows": [], "header": {}}
        result = detector.detect_v2(batch)
        assert "bot_score" in result
        assert "v1_score" in result
        assert "v2_score" in result
        assert "ml_features" in result
        assert "is_bot" in result
        assert "action" in result

    def test_human_batch_low_score(self):
        import importlib
        detector = importlib.import_module("03_kbio._scoring.bot_detector")
        batch = {
            "keystroke_windows": [{"zone_dwell_means": [80, 95, 110, 85, 90], "zone_dwell_stdevs": [15, 20, 12, 18, 25]}],
            "pointer_windows": [{"movement": {"velocity_mean": 200, "velocity_stdev": 80, "curvature_mean": 0.3, "total_distance": 500}, "clicks": {"count": 3, "hold_mean_ms": 120}}],
            "header": {},
            "signals": {},
            "context": {},
        }
        result = detector.detect_v2(batch, {"pulse_count": 5})
        assert result["bot_score"] < 0.7

    def test_automation_signal_high_score(self):
        import importlib
        detector = importlib.import_module("03_kbio._scoring.bot_detector")
        batch = {
            "keystroke_windows": [],
            "pointer_windows": [],
            "header": {},
            "signals": {"automation": {"webdriver": True}},
            "context": {},
        }
        result = detector.detect_v2(batch)
        assert result["bot_score"] > 0.7
        assert result["is_bot"]
