"""Tests for 03_kbio._scoring.verdict_engine — final decision layer."""
import importlib

import pytest

_verdict = importlib.import_module("03_kbio._scoring.verdict_engine")


class TestVerdict:
    def test_high_trust_allows(self):
        """trust=0.85, confidence=0.9 -> allow."""
        result = _verdict.decide(session_trust=0.85, confidence=0.9)
        assert result["action"] == "allow"
        assert result["risk_level"] == "low"

    def test_low_trust_blocks(self):
        """trust=0.05, confidence=0.9 -> block."""
        result = _verdict.decide(session_trust=0.05, confidence=0.9)
        assert result["action"] == "block"
        assert result["risk_level"] == "critical"

    def test_medium_trust_monitors(self):
        """trust=0.55, confidence=0.9 -> monitor."""
        result = _verdict.decide(session_trust=0.55, confidence=0.9)
        assert result["action"] == "monitor"
        assert result["risk_level"] == "medium"

    def test_low_trust_challenges(self):
        """trust=0.35, confidence=0.9 -> challenge."""
        result = _verdict.decide(session_trust=0.35, confidence=0.9)
        assert result["action"] == "challenge"
        assert result["risk_level"] == "high"

    def test_very_low_trust_step_up(self):
        """trust=0.20, confidence=0.9 -> step_up."""
        result = _verdict.decide(session_trust=0.20, confidence=0.9)
        assert result["action"] == "step_up"
        assert result["risk_level"] == "critical"

    def test_low_confidence_monitors(self):
        """confidence < 0.40 -> always monitor, never escalate on low confidence."""
        result = _verdict.decide(session_trust=0.05, confidence=0.3)
        assert result["action"] == "monitor"

    def test_bot_override(self):
        """bot_score > 0.85 -> escalates to block."""
        result = _verdict.decide(
            session_trust=0.6, confidence=0.9, bot_score=0.9,
        )
        assert result["action"] == "block"
        assert result["primary_reason"] == "bot_score"

    def test_replay_override(self):
        """replay_score > 0.90 -> escalates to block."""
        result = _verdict.decide(
            session_trust=0.6, confidence=0.9, replay_score=0.95,
        )
        assert result["action"] == "block"
        assert result["primary_reason"] == "replay_score"

    def test_coercion_override(self):
        """coercion_score > 0.70 -> challenge (not block)."""
        result = _verdict.decide(
            session_trust=0.85, confidence=0.9, coercion_score=0.8,
        )
        # Base would be "allow", coercion escalates to "challenge"
        assert result["action"] == "challenge"
        assert result["primary_reason"] == "coercion_score"

    def test_takeover_override(self):
        """takeover_probability > 0.75 -> block."""
        result = _verdict.decide(
            session_trust=0.85, confidence=0.9, takeover_probability=0.8,
        )
        assert result["action"] == "block"

    def test_credential_drift_override(self):
        """credential_drift > 0.80 + credential_confidence > 0.60 -> step_up."""
        result = _verdict.decide(
            session_trust=0.85, confidence=0.9,
            credential_drift=0.9, credential_confidence=0.7,
        )
        assert result["action"] in ("step_up", "block")

    def test_credential_drift_low_confidence_no_override(self):
        """credential_drift high but confidence low -> no override."""
        result = _verdict.decide(
            session_trust=0.85, confidence=0.9,
            credential_drift=0.9, credential_confidence=0.3,
        )
        assert result["action"] == "allow"

    def test_grace_period_caps(self):
        """grace_max_verdict='monitor' caps action at monitor."""
        result = _verdict.decide(
            session_trust=0.05, confidence=0.9,
            grace_max_verdict="monitor",
        )
        # Without grace, this would be "block"
        assert result["action"] == "monitor"

    def test_grace_period_does_not_escalate(self):
        """Grace period only caps; does not escalate 'allow' to 'monitor'."""
        result = _verdict.decide(
            session_trust=0.85, confidence=0.9,
            grace_max_verdict="monitor",
        )
        assert result["action"] == "allow"

    def test_result_keys(self):
        result = _verdict.decide(session_trust=0.5, confidence=0.5)
        assert "action" in result
        assert "risk_level" in result
        assert "primary_reason" in result

    def test_overrides_escalate_only(self):
        """Multiple overrides: the most severe one wins."""
        result = _verdict.decide(
            session_trust=0.85, confidence=0.9,
            bot_score=0.9, coercion_score=0.8,
        )
        # Bot escalates to block, coercion to challenge; block wins
        assert result["action"] == "block"
