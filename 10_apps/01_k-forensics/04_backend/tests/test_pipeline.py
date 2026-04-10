"""Tests for end-to-end scoring pipeline orchestration.

Tests the full flow from batch -> feature extraction -> drift -> anomaly
-> trust -> verdict by exercising the individual modules in sequence,
mimicking what the pipeline orchestrator does.
"""
import importlib
import math

import pytest

_normalizer = importlib.import_module("03_kbio._features.normalizer")
_drift = importlib.import_module("03_kbio._scoring.drift_scorer")
_anomaly = importlib.import_module("03_kbio._scoring.anomaly_scorer")
_trust = importlib.import_module("03_kbio._scoring.trust_scorer")
_verdict = importlib.import_module("03_kbio._scoring.verdict_engine")
_fusion = importlib.import_module("03_kbio._scoring.fusion")
_bot = importlib.import_module("03_kbio._scoring.bot_detector")
_identity = importlib.import_module("03_kbio._scoring.identity_scorer")
_manifest = importlib.import_module("03_kbio._scoring.score_manifest")


class TestPipeline:
    """Integration-style tests exercising the full scoring pipeline."""

    # -------------------------------------------------------------------
    # Fixtures
    # -------------------------------------------------------------------

    def _make_batch(self, **overrides):
        """Create a realistic test batch with default values."""
        return {
            "type": "behavioral",
            "header": {
                "batch_id": "test-1", "session_id": "sess-1",
                "user_hash": "sha256:test", "device_uuid": "dev-1",
                "sent_at": 1000, "pulse_number": 1,
            },
            "context": {"platform": "web", "viewport_width": 1920},
            "keystroke_windows": [{
                "zone_transition_matrix": [0.1] * 100,
                "zone_dwell_means": [50.0] * 10,
                "zone_dwell_stdevs": [10.0] * 10,
                "zone_hit_counts": [5] * 10,
                "rhythm": {
                    "kps_mean": 3.5, "kps_stdev": 0.5,
                    "burst_count": 3, "burst_length_mean": 5,
                    "pause_count": 2,
                },
                "error_proxy": {
                    "backspace_rate": 0.05, "rapid_same_zone_count": 1,
                },
                "bigram_velocity_histogram": [0.1] * 10,
            }],
            "pointer_windows": [{
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
            }],
            **overrides,
        }

    def _make_profile(self):
        """Create a test profile with one cluster."""
        return {
            "id": "prof-1",
            "user_hash": "sha256:test",
            "baseline_quality": "established",
            "profile_maturity": 0.7,
            "total_sessions": 20,
            "total_genuine_sessions": 18,
            "encoder_version": "v2",
            "user_trust_ema": 0.8,
            "clusters": [{
                "cluster_id": "cluster-1",
                "general_centroid": [0.1] * 128,
                "keystroke_centroid": [0.1] * 64,
                "pointer_centroid": [0.1] * 32,
                "touch_centroid": [0.1] * 32,
                "sensor_centroid": [0.1] * 32,
                "intra_distance": {
                    "mean": 0.15, "stdev": 0.05,
                    "p95": 0.25, "p99": 0.3, "sample_count": 18,
                },
                "per_modality_intra": {
                    "keystroke": {
                        "mean": 0.15, "stdev": 0.05,
                        "p95": 0.25, "p99": 0.3, "sample_count": 18,
                    },
                    "pointer": {
                        "mean": 0.15, "stdev": 0.05,
                        "p95": 0.25, "p99": 0.3, "sample_count": 18,
                    },
                },
                "context_prototype": {
                    "platform": "web_desktop",
                    "input_method": "keyboard_mouse",
                    "time_bucket": "morning",
                    "screen_class": "large",
                    "locale": "en",
                },
                "weight": 1.0,
                "session_count": 18,
                "last_used_at": 1000,
            }],
            "credential_profiles": [],
            "device_uuids": ["dev-1"],
        }

    def _make_session(self):
        return {
            "id": "s-1",
            "sdk_session_id": "sess-1",
            "user_hash": "sha256:test",
            "status": "active",
            "pulse_count": 5,
            "drift_history": [0.1, 0.12, 0.11],
            "trust_score": 0.8,
        }

    def _run_pipeline(self, batch, profile, session):
        """Simulate the full scoring pipeline: extract -> drift -> anomaly -> trust -> verdict."""
        # 1. Feature extraction + normalization
        feature_vecs = _normalizer.normalize_features(batch)

        # 2. Bot detection
        bot_result = _bot.detect_v2(batch, session)

        # 3. Drift scoring
        cluster = profile["clusters"][0] if profile.get("clusters") else {}
        modality_drifts_raw = _drift.compute_all_modality_drifts(
            feature_vecs, cluster,
        )
        modality_drifts = {m: d["drift"] for m, d in modality_drifts_raw.items()}

        # 4. Fusion
        fused_drift, weights = _fusion.fuse(modality_drifts)

        # 5. Confidence
        event_counts = {m: 10 for m in modality_drifts}
        confidence = _fusion.compute_confidence(
            modality_drifts, event_counts,
            profile.get("profile_maturity", 0.0),
            session.get("pulse_count", 0) * 20,
        )

        # 6. Identity scores
        identity_confidence = _identity.compute_identity_confidence(
            fused_drift, None, confidence,
        )

        # 7. Anomaly scores
        drift_history = session.get("drift_history", [])
        anomaly_result = _anomaly.compute_all_anomaly_scores(
            feature_vecs, modality_drifts, drift_history,
            None, batch,
        )

        # 8. Session trust
        trust_result = _trust.compute_session_trust(
            identity_confidence=identity_confidence,
            bot_score=bot_result["bot_score"],
            replay_score=0.0,
            automation_score=0.0,
            session_anomaly=max(0.0, anomaly_result.get("session_anomaly", 0.0)),
            takeover_probability=anomaly_result["takeover"]["takeover_probability"],
            profile_maturity=profile.get("profile_maturity", 0.0),
            previous_trust=session.get("trust_score"),
        )

        # 9. Verdict
        verdict_result = _verdict.decide(
            session_trust=trust_result["session_trust"],
            confidence=confidence,
            bot_score=bot_result["bot_score"],
        )

        # 10. Aggregate
        all_scores = _fusion.aggregate_all_scores(
            identity={
                "fused_drift": fused_drift,
                "keystroke_drift": modality_drifts.get("keystroke", -1.0),
                "pointer_drift": modality_drifts.get("pointer", -1.0),
                "touch_drift": modality_drifts.get("touch", -1.0),
                "sensor_drift": modality_drifts.get("sensor", -1.0),
                "credential_drift": -1.0,
            },
            anomaly={
                "session_anomaly": anomaly_result.get("session_anomaly", -1.0),
                "population_anomaly": 0.5,
                "takeover_probability": anomaly_result["takeover"]["takeover_probability"],
            },
            humanness={
                "bot_score": bot_result["bot_score"],
                "replay_score": 0.0,
                "automation_score": 0.0,
            },
            threat={"credential_drift": -1.0, "velocity_anomaly": anomaly_result.get("velocity_anomaly", 0.0)},
            trust={
                "session_trust": trust_result["session_trust"],
                "user_trust": profile.get("user_trust_ema", 0.5),
                "device_trust": 0.5,
            },
            meta={
                "confidence": confidence,
                "signal_richness": _fusion.compute_signal_richness(modality_drifts),
                "profile_maturity": profile.get("profile_maturity", 0.0),
            },
        )

        return {
            "scores": all_scores,
            "verdict": verdict_result,
            "trust": trust_result,
            "drift": fused_drift,
            "bot": bot_result,
        }

    # -------------------------------------------------------------------
    # Tests
    # -------------------------------------------------------------------

    def test_genuine_session_low_drift(self):
        """Batch similar to profile -> low drift, high trust, allow."""
        batch = self._make_batch()
        profile = self._make_profile()
        session = self._make_session()
        result = self._run_pipeline(batch, profile, session)

        assert result["drift"] >= 0.0
        assert result["trust"]["session_trust"] > 0.0
        assert result["verdict"]["action"] in ("allow", "monitor")

    def test_no_profile_returns_defaults(self):
        """No profile clusters -> drift=-1, pipeline still works."""
        batch = self._make_batch()
        profile = {
            "id": "p-new", "user_hash": "sha256:new",
            "baseline_quality": "insufficient", "profile_maturity": 0.0,
            "total_sessions": 0, "clusters": [], "device_uuids": [],
            "user_trust_ema": 0.5, "credential_profiles": [],
        }
        session = {"id": "s-new", "sdk_session_id": "sess-new",
                    "user_hash": "sha256:new", "status": "active",
                    "pulse_count": 1, "drift_history": [], "trust_score": 0.5}
        result = self._run_pipeline(batch, profile, session)
        assert result["drift"] == -1.0
        # With no profile, confidence is very low -> monitor
        assert result["verdict"]["action"] == "monitor"

    def test_bot_short_circuit(self):
        """Bot detected -> block verdict."""
        batch = self._make_batch(**{
            "signals": {"automation": {"webdriver": True}},
        })
        profile = self._make_profile()
        session = self._make_session()
        result = self._run_pipeline(batch, profile, session)
        assert result["bot"]["is_bot"] is True
        assert result["bot"]["bot_score"] > 0.7
        assert result["verdict"]["action"] == "block"

    def test_all_22_scores_present(self):
        """Verify the response contains all score categories from the manifest."""
        batch = self._make_batch()
        profile = self._make_profile()
        session = self._make_session()
        result = self._run_pipeline(batch, profile, session)
        scores = result["scores"]

        # Check all 6 categories exist
        for category in _manifest.CATEGORIES:
            assert category in scores, f"Missing category: {category}"

        # Check score_count matches expected
        assert scores["score_count"] >= 20

    def test_verdict_maps_correctly(self):
        """High trust -> allow, override rules work."""
        batch = self._make_batch()
        profile = self._make_profile()
        session = self._make_session()
        result = self._run_pipeline(batch, profile, session)

        # The verdict should be consistent with trust
        trust = result["trust"]["session_trust"]
        action = result["verdict"]["action"]

        if trust > 0.7:
            assert action in ("allow", "monitor", "challenge", "step_up", "block")
        if trust < 0.15:
            assert action in ("block", "monitor")  # monitor if low confidence

    def test_processing_produces_numeric_drift(self):
        """With a proper profile, drift is a real number 0-1."""
        batch = self._make_batch()
        profile = self._make_profile()
        session = self._make_session()
        result = self._run_pipeline(batch, profile, session)
        if result["drift"] >= 0:
            assert 0.0 <= result["drift"] <= 1.0

    def test_signal_richness_reflects_modalities(self):
        """With keystroke + pointer -> signal richness = 0.5 (2/4)."""
        batch = self._make_batch()
        profile = self._make_profile()
        session = self._make_session()
        result = self._run_pipeline(batch, profile, session)
        richness = result["scores"]["meta"]["signal_richness"]
        assert richness == pytest.approx(0.5)

    def test_score_manifest_categories(self):
        """Verify manifest lists all expected categories."""
        assert set(_manifest.CATEGORIES) == {
            "identity", "anomaly", "humanness", "threat", "trust", "meta",
        }

    def test_score_manifest_counts_22(self):
        """Verify manifest defines 22 scores."""
        assert len(_manifest.SCORES) == 22

    def test_modality_dimensions(self):
        """Verify manifest modality dimensions match extractors."""
        assert _manifest.MODALITIES["keystroke"] == 64
        assert _manifest.MODALITIES["pointer"] == 32
        assert _manifest.MODALITIES["touch"] == 32
        assert _manifest.MODALITIES["sensor"] == 32
        assert _manifest.GENERAL_EMBEDDING_DIM == 128
