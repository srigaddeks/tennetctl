"""Tests for 03_kbio._scoring.trust_scorer — session, user, device trust."""
import importlib

import pytest

_trust = importlib.import_module("03_kbio._scoring.trust_scorer")


# ---------------------------------------------------------------------------
# compute_session_trust
# ---------------------------------------------------------------------------

class TestSessionTrust:
    def test_high_identity_high_trust(self):
        """identity_confidence=0.9, no threats -> trust > 0.7."""
        result = _trust.compute_session_trust(
            identity_confidence=0.9,
            bot_score=0.0,
            replay_score=0.0,
            automation_score=0.0,
            session_anomaly=0.0,
            takeover_probability=0.0,
            profile_maturity=0.8,
        )
        assert result["session_trust"] > 0.7
        assert result["trust_level"] == "high"

    def test_impostor_low_trust(self):
        """Low identity confidence -> low trust."""
        result = _trust.compute_session_trust(
            identity_confidence=0.1,
            bot_score=0.0,
            replay_score=0.0,
            automation_score=0.0,
            session_anomaly=0.0,
            takeover_probability=0.0,
            profile_maturity=0.8,
        )
        assert result["session_trust"] < 0.3

    def test_bot_floor(self):
        """bot_score=0.9 -> trust floored at 0.1."""
        result = _trust.compute_session_trust(
            identity_confidence=0.9,
            bot_score=0.9,
            replay_score=0.0,
            automation_score=0.0,
            session_anomaly=0.0,
            takeover_probability=0.0,
            profile_maturity=0.8,
        )
        assert result["session_trust"] <= 0.1

    def test_takeover_floor(self):
        """takeover_probability=0.9 -> trust floored at 0.1."""
        result = _trust.compute_session_trust(
            identity_confidence=0.9,
            bot_score=0.0,
            replay_score=0.0,
            automation_score=0.0,
            session_anomaly=0.0,
            takeover_probability=0.9,
            profile_maturity=0.8,
        )
        assert result["session_trust"] <= 0.1

    def test_decay_mechanism(self):
        """previous_trust=0.8 with current bad -> does not snap to zero."""
        result = _trust.compute_session_trust(
            identity_confidence=0.1,
            bot_score=0.0,
            replay_score=0.0,
            automation_score=0.0,
            session_anomaly=0.5,
            takeover_probability=0.0,
            profile_maturity=0.8,
            previous_trust=0.8,
        )
        # Decay blending prevents snap to 0
        assert result["session_trust"] > 0.05
        assert result["factors"]["decay_applied"] is True

    def test_result_keys(self):
        result = _trust.compute_session_trust(
            identity_confidence=0.5,
            bot_score=0.0,
            replay_score=0.0,
            automation_score=0.0,
            session_anomaly=0.0,
            takeover_probability=0.0,
            profile_maturity=0.5,
        )
        assert "session_trust" in result
        assert "factors" in result
        assert "trust_level" in result
        assert result["trust_level"] in ("high", "medium", "low", "critical")

    def test_humanness_factor(self):
        """All humanness signals bad -> trust drops significantly."""
        result = _trust.compute_session_trust(
            identity_confidence=0.9,
            bot_score=0.5,
            replay_score=0.5,
            automation_score=0.5,
            session_anomaly=0.0,
            takeover_probability=0.0,
            profile_maturity=0.8,
        )
        assert result["factors"]["humanness"] < 0.2

    def test_low_maturity_reduces_trust(self):
        """profile_maturity=0 -> maturity_factor=0.2 (0 + 0.2)."""
        result = _trust.compute_session_trust(
            identity_confidence=0.9,
            bot_score=0.0,
            replay_score=0.0,
            automation_score=0.0,
            session_anomaly=0.0,
            takeover_probability=0.0,
            profile_maturity=0.0,
        )
        assert result["factors"]["maturity_factor"] == pytest.approx(0.2)


# ---------------------------------------------------------------------------
# compute_user_trust
# ---------------------------------------------------------------------------

class TestUserTrust:
    def test_good_session_increases(self):
        """Good session outcome > 0.7 -> trust increases."""
        result = _trust.compute_user_trust(0.5, session_outcome=0.8)
        assert result > 0.5

    def test_bad_session_decreases(self):
        """Bad session outcome < 0.3 -> trust decreases."""
        result = _trust.compute_user_trust(0.5, session_outcome=0.1)
        assert result < 0.5

    def test_mediocre_session_slightly_decreases(self):
        """Session outcome between 0.3 and 0.5 -> slight decrease."""
        result = _trust.compute_user_trust(0.5, session_outcome=0.4)
        assert result < 0.5

    def test_challenge_passed_boost(self):
        """Challenge passed gives bigger boost than passive good session."""
        passive = _trust.compute_user_trust(0.5, session_outcome=0.8)
        challenge = _trust.compute_user_trust(
            0.5, session_outcome=0.8, challenge_passed=True,
        )
        assert challenge > passive

    def test_challenge_failed_penalty(self):
        """Challenge failed -> significant trust drop."""
        result = _trust.compute_user_trust(
            0.5, session_outcome=0.8, challenge_failed=True,
        )
        # Challenge fail penalty (-25%) should outweigh good session boost (+5%)
        assert result < 0.5

    def test_clamp_lower_bound(self):
        """Trust never drops below 0.05."""
        result = _trust.compute_user_trust(
            0.05, session_outcome=0.0, challenge_failed=True,
        )
        assert result >= 0.05

    def test_clamp_upper_bound(self):
        """Trust never exceeds 0.99."""
        result = _trust.compute_user_trust(
            0.99, session_outcome=1.0, challenge_passed=True,
        )
        assert result <= 0.99

    def test_neutral_session_no_change(self):
        """Session outcome between 0.5 and 0.7 -> no adjustment."""
        result = _trust.compute_user_trust(0.5, session_outcome=0.6)
        assert result == pytest.approx(0.5)


# ---------------------------------------------------------------------------
# compute_device_trust
# ---------------------------------------------------------------------------

class TestDeviceTrust:
    def test_new_device_low(self):
        """0 sessions -> device trust = 0.0."""
        result = _trust.compute_device_trust(
            device_sessions=0, device_age_days=0, recent_session_trusts=[],
        )
        assert result == pytest.approx(0.0)

    def test_known_device_high(self):
        """Many sessions with good trust -> approaches 1.0."""
        result = _trust.compute_device_trust(
            device_sessions=100,
            device_age_days=10,
            recent_session_trusts=[0.9] * 10,
        )
        assert result > 0.8

    def test_asymptotic_base(self):
        """sessions / (sessions + 5) formula: 5 sessions -> base=0.5."""
        result = _trust.compute_device_trust(
            device_sessions=5, device_age_days=5, recent_session_trusts=[0.8],
        )
        # base = 5/(5+5) = 0.5, consistency = 0.8, trust = 0.5*0.8 = 0.4
        assert result == pytest.approx(0.4)

    def test_old_device_decay_30_days(self):
        """Device not seen > 30 days -> trust halved."""
        fresh = _trust.compute_device_trust(
            device_sessions=20, device_age_days=10, recent_session_trusts=[0.8] * 5,
        )
        stale = _trust.compute_device_trust(
            device_sessions=20, device_age_days=50, recent_session_trusts=[0.8] * 5,
        )
        assert stale < fresh
        assert stale == pytest.approx(fresh * 0.5, abs=0.01)

    def test_very_old_device_capped(self):
        """Device > 90 days old -> trust capped at 0.3."""
        result = _trust.compute_device_trust(
            device_sessions=100,
            device_age_days=100,
            recent_session_trusts=[0.9] * 10,
        )
        assert result <= 0.3

    def test_no_recent_trusts_uses_half(self):
        """No recent session trusts -> consistency defaults to 0.5."""
        result = _trust.compute_device_trust(
            device_sessions=10, device_age_days=5, recent_session_trusts=[],
        )
        # base = 10/15 ~ 0.667, consistency = 0.5, trust ~ 0.333
        expected_base = 10 / 15
        assert result == pytest.approx(expected_base * 0.5, abs=0.01)
