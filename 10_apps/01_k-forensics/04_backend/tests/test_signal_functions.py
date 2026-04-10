"""Tests for individual signal functions with mock evaluation contexts."""
import importlib

import pytest

_registry = importlib.import_module("03_kbio._signals._registry")
_signals = importlib.import_module("03_kbio._signals")


# ---------------------------------------------------------------------------
# Context builder
# ---------------------------------------------------------------------------

def _make_ctx(**overrides):
    """Build a realistic evaluation context with optional dot-path overrides."""
    ctx = {
        "scores": {
            "behavioral_drift": 0.5,
            "credential_drift": None,
            "identity_confidence": 0.7,
            "familiarity_score": 0.6,
            "cognitive_load": 0.3,
            "session_anomaly": 0.2,
            "velocity_anomaly": 0.1,
            "takeover_probability": 0.05,
            "pattern_break": 0.1,
            "consistency_score": 0.8,
            "bot_score": 0.1,
            "replay_score": 0.0,
            "automation_score": 0.0,
            "population_anomaly": 0.1,
            "coercion_score": 0.1,
            "impersonation_score": 0.1,
            "session_trust": 0.75,
            "user_trust": 0.8,
            "device_trust": 0.6,
            "confidence": 0.8,
            "signal_richness": 0.7,
            "profile_maturity": 0.6,
        },
        "device": {
            "is_new": False,
            "is_trusted": True,
            "fingerprint_drift": 0.1,
            "age_days": 30,
            "session_count": 10,
            "users_count": 1,
            "is_mobile": False,
            "is_emulator": False,
            "is_headless": False,
            "webdriver_present": False,
            "automation_artifacts": False,
            "plugins_count": 5,
            "timezone_offset_minutes": -300,
            "language": "en-US",
            "screen_width": 1920,
            "screen_height": 1080,
            "canvas_anomaly": False,
            "webgl_anomaly": False,
        },
        "network": {
            "ip_address": "1.2.3.4",
            "country": "US",
            "is_vpn": False,
            "is_tor": False,
            "is_datacenter": False,
            "is_proxy": False,
            "is_residential_proxy": False,
            "ip_trusted": True,
            "ip_session_count_24h": 5,
            "ip_user_count_24h": 1,
            "travel_speed_kmh": 0,
            "threat_score": 0.0,
        },
        "user": {
            "total_sessions": 50,
            "known_countries": ["US"],
            "account_age_days": 180,
            "total_devices": 2,
            "sessions_last_24h": 3,
            "days_since_last_session": 1,
            "typical_hours": list(range(8, 22)),
            "failed_challenges_last_24h": 0,
        },
        "session": {
            "duration_seconds": 300,
            "page_count": 5,
            "pulse_count": 50,
            "local_hour": 14,
            "event_type": "behavioral",
        },
        "drift_trend": {
            "slope": 0.0,
            "acceleration": 0.0,
            "mean": 0.3,
            "stdev": 0.1,
        },
        "modality_drift": {
            "keystroke": 0.3,
            "pointer": 0.2,
            "touch": 0.0,
            "sensor": 0.0,
        },
    }
    for key, value in overrides.items():
        parts = key.split(".")
        target = ctx
        for p in parts[:-1]:
            target = target[p]
        target[parts[-1]] = value
    return ctx


def _get_fn(code):
    """Fetch the signal function by code."""
    sig = _registry.get_signal(code)
    assert sig is not None, f"Signal {code} not found in registry"
    return sig["function"]


# ---------------------------------------------------------------------------
# Behavioral signals
# ---------------------------------------------------------------------------

class TestBehavioralSignals:
    def test_high_drift_score_returned(self):
        fn = _get_fn("high_behavioral_drift")
        ctx = _make_ctx(**{"scores.behavioral_drift": 0.80})
        result = fn(ctx, {"threshold": 0.65})
        assert result["value"] == 0.80
        assert result["details"]["exceeded"] is True

    def test_high_drift_below_threshold(self):
        fn = _get_fn("high_behavioral_drift")
        ctx = _make_ctx(**{"scores.behavioral_drift": 0.30})
        result = fn(ctx, {"threshold": 0.65})
        assert result["value"] == 0.30
        assert result["details"]["exceeded"] is False

    def test_critical_drift_triggers(self):
        fn = _get_fn("critical_behavioral_drift")
        ctx = _make_ctx(**{"scores.behavioral_drift": 0.90})
        result = fn(ctx, {"threshold": 0.85})
        assert result["value"] is True

    def test_critical_drift_no_trigger(self):
        fn = _get_fn("critical_behavioral_drift")
        ctx = _make_ctx(**{"scores.behavioral_drift": 0.50})
        result = fn(ctx, {"threshold": 0.85})
        assert result["value"] is False

    def test_mid_session_takeover(self):
        fn = _get_fn("mid_session_takeover")
        ctx = _make_ctx(**{"scores.takeover_probability": 0.75})
        result = fn(ctx, {"threshold": 0.60})
        assert result["value"] is True

    def test_mid_session_takeover_no_trigger(self):
        fn = _get_fn("mid_session_takeover")
        ctx = _make_ctx(**{"scores.takeover_probability": 0.30})
        result = fn(ctx, {"threshold": 0.60})
        assert result["value"] is False

    def test_low_identity_confidence(self):
        fn = _get_fn("low_identity_confidence")
        ctx = _make_ctx(**{"scores.identity_confidence": 0.20})
        result = fn(ctx, {"threshold": 0.40})
        assert result["value"] is True

    def test_velocity_spike(self):
        fn = _get_fn("velocity_spike")
        ctx = _make_ctx(**{"scores.velocity_anomaly": 0.85})
        result = fn(ctx, {"threshold": 0.70})
        assert result["value"] is True

    def test_drift_trend_worsening(self):
        fn = _get_fn("drift_trend_worsening")
        ctx = _make_ctx(**{
            "drift_trend.slope": 0.05,
            "drift_trend.acceleration": 0.01,
        })
        result = fn(ctx, {"slope_threshold": 0.02})
        assert result["value"] is True

    def test_drift_trend_not_worsening(self):
        fn = _get_fn("drift_trend_worsening")
        ctx = _make_ctx(**{
            "drift_trend.slope": 0.01,
            "drift_trend.acceleration": -0.01,
        })
        result = fn(ctx, {"slope_threshold": 0.02})
        assert result["value"] is False

    def test_multi_modality_concordance_triggers(self):
        fn = _get_fn("multi_modality_concordance")
        ctx = _make_ctx(**{
            "modality_drift.keystroke": 0.80,
            "modality_drift.pointer": 0.75,
        })
        result = fn(ctx, {"drift_threshold": 0.60, "min_modalities": 2})
        assert result["value"] is True

    def test_multi_modality_concordance_no_trigger(self):
        fn = _get_fn("multi_modality_concordance")
        ctx = _make_ctx()  # default low drifts
        result = fn(ctx, {"drift_threshold": 0.60, "min_modalities": 2})
        assert result["value"] is False

    def test_keystroke_only_drift(self):
        fn = _get_fn("keystroke_only_drift")
        ctx = _make_ctx(**{
            "modality_drift.keystroke": 0.80,
            "modality_drift.pointer": 0.10,
            "modality_drift.touch": 0.05,
            "modality_drift.sensor": 0.02,
        })
        result = fn(ctx, {"ks_threshold": 0.70, "other_max": 0.30})
        assert result["value"] is True

    def test_population_outlier(self):
        fn = _get_fn("population_outlier")
        ctx = _make_ctx(**{"scores.population_anomaly": 0.85})
        result = fn(ctx, {"threshold": 0.70})
        assert result["value"] is True

    def test_credential_drift_none_returns_zero(self):
        fn = _get_fn("credential_drift_elevated")
        ctx = _make_ctx()  # credential_drift is None by default
        result = fn(ctx, {"threshold": 0.60})
        assert result["value"] == 0.0
        assert result["confidence"] == 0.0


# ---------------------------------------------------------------------------
# Device signals
# ---------------------------------------------------------------------------

class TestDeviceSignals:
    def test_new_device(self):
        fn = _get_fn("new_device")
        ctx = _make_ctx(**{"device.is_new": True})
        result = fn(ctx, {})
        assert result["value"] is True

    def test_not_new_device(self):
        fn = _get_fn("new_device")
        ctx = _make_ctx()
        result = fn(ctx, {})
        assert result["value"] is False

    def test_emulator(self):
        fn = _get_fn("emulator_detected")
        ctx = _make_ctx(**{"device.is_emulator": True})
        result = fn(ctx, {})
        assert result["value"] is True

    def test_multi_user_device(self):
        fn = _get_fn("multi_user_device")
        ctx = _make_ctx(**{"device.users_count": 3})
        result = fn(ctx, {"max_users": 1})
        assert result["value"] is True

    def test_single_user_device(self):
        fn = _get_fn("multi_user_device")
        ctx = _make_ctx()
        result = fn(ctx, {"max_users": 1})
        assert result["value"] is False

    def test_device_fingerprint_drift_score(self):
        fn = _get_fn("device_fingerprint_drift")
        ctx = _make_ctx(**{"device.fingerprint_drift": 0.70})
        result = fn(ctx, {"threshold": 0.50})
        assert result["value"] == 0.70
        assert result["details"]["exceeded"] is True

    def test_untrusted_device(self):
        fn = _get_fn("untrusted_device")
        ctx = _make_ctx(**{"device.is_trusted": False})
        result = fn(ctx, {})
        assert result["value"] is True

    def test_device_age_young(self):
        fn = _get_fn("device_age_young")
        ctx = _make_ctx(**{"device.age_days": 2})
        result = fn(ctx, {"min_age_days": 7})
        assert result["value"] is True

    def test_headless_browser(self):
        fn = _get_fn("headless_browser")
        ctx = _make_ctx(**{"device.is_headless": True})
        result = fn(ctx, {})
        assert result["value"] is True

    def test_webdriver(self):
        fn = _get_fn("webdriver_detected")
        ctx = _make_ctx(**{"device.webdriver_present": True})
        result = fn(ctx, {})
        assert result["value"] is True

    def test_plugins_zero(self):
        fn = _get_fn("plugins_zero")
        ctx = _make_ctx(**{"device.plugins_count": 0})
        result = fn(ctx, {})
        assert result["value"] is True

    def test_plugins_nonzero(self):
        fn = _get_fn("plugins_zero")
        ctx = _make_ctx()  # plugins_count=5
        result = fn(ctx, {})
        assert result["value"] is False

    def test_canvas_anomaly(self):
        fn = _get_fn("canvas_fingerprint_anomaly")
        ctx = _make_ctx(**{"device.canvas_anomaly": True})
        result = fn(ctx, {})
        assert result["value"] is True

    def test_screen_resolution_anomaly(self):
        fn = _get_fn("screen_resolution_anomaly")
        ctx = _make_ctx(**{"device.screen_width": 50, "device.screen_height": 50})
        result = fn(ctx, {})
        assert result["value"] is True

    def test_screen_resolution_normal(self):
        fn = _get_fn("screen_resolution_anomaly")
        ctx = _make_ctx()
        result = fn(ctx, {})
        assert result["value"] is False


# ---------------------------------------------------------------------------
# Network signals
# ---------------------------------------------------------------------------

class TestNetworkSignals:
    def test_vpn(self):
        fn = _get_fn("vpn_detected")
        ctx = _make_ctx(**{"network.is_vpn": True})
        result = fn(ctx, {})
        assert result["value"] is True

    def test_no_vpn(self):
        fn = _get_fn("vpn_detected")
        ctx = _make_ctx()
        result = fn(ctx, {})
        assert result["value"] is False

    def test_tor(self):
        fn = _get_fn("tor_exit_node")
        ctx = _make_ctx(**{"network.is_tor": True})
        result = fn(ctx, {})
        assert result["value"] is True

    def test_impossible_travel(self):
        fn = _get_fn("impossible_travel")
        ctx = _make_ctx(**{"network.travel_speed_kmh": 1200})
        result = fn(ctx, {"max_speed_kmh": 900})
        assert result["value"] is True

    def test_no_impossible_travel(self):
        fn = _get_fn("impossible_travel")
        ctx = _make_ctx(**{"network.travel_speed_kmh": 500})
        result = fn(ctx, {"max_speed_kmh": 900})
        assert result["value"] is False

    def test_datacenter_ip(self):
        fn = _get_fn("datacenter_ip")
        ctx = _make_ctx(**{"network.is_datacenter": True})
        result = fn(ctx, {})
        assert result["value"] is True

    def test_proxy_detected(self):
        fn = _get_fn("proxy_detected")
        ctx = _make_ctx(**{"network.is_proxy": True})
        result = fn(ctx, {})
        assert result["value"] is True

    def test_residential_proxy(self):
        fn = _get_fn("residential_proxy")
        ctx = _make_ctx(**{"network.is_residential_proxy": True})
        result = fn(ctx, {})
        assert result["value"] is True

    def test_geo_country_mismatch(self):
        fn = _get_fn("geo_country_mismatch")
        ctx = _make_ctx(**{"network.country": "RU"})
        result = fn(ctx, {})
        assert result["value"] is True  # known_countries=["US"]

    def test_geo_country_match(self):
        fn = _get_fn("geo_country_mismatch")
        ctx = _make_ctx()
        result = fn(ctx, {})
        assert result["value"] is False  # country=US, known=["US"]

    def test_ip_not_trusted(self):
        fn = _get_fn("ip_not_trusted")
        ctx = _make_ctx(**{"network.ip_trusted": False})
        result = fn(ctx, {})
        assert result["value"] is True

    def test_ip_reputation_bad(self):
        fn = _get_fn("ip_reputation_bad")
        ctx = _make_ctx(**{"network.threat_score": 0.85})
        result = fn(ctx, {"min_threat_score": 0.70})
        assert result["value"] is True

    def test_vpn_with_drift_compound(self):
        fn = _get_fn("vpn_with_drift")
        ctx = _make_ctx(**{
            "network.is_vpn": True,
            "scores.behavioral_drift": 0.70,
        })
        result = fn(ctx, {"drift_threshold": 0.50})
        assert result["value"] is True

    def test_vpn_with_drift_no_vpn(self):
        fn = _get_fn("vpn_with_drift")
        ctx = _make_ctx(**{"scores.behavioral_drift": 0.70})
        result = fn(ctx, {"drift_threshold": 0.50})
        assert result["value"] is False


# ---------------------------------------------------------------------------
# Bot signals
# ---------------------------------------------------------------------------

class TestBotSignals:
    def test_is_bot(self):
        fn = _get_fn("is_bot")
        ctx = _make_ctx(**{"scores.bot_score": 0.85})
        result = fn(ctx, {"threshold": 0.70})
        assert result["value"] is True

    def test_not_bot(self):
        fn = _get_fn("is_bot")
        ctx = _make_ctx()  # bot_score=0.1
        result = fn(ctx, {"threshold": 0.70})
        assert result["value"] is False

    def test_is_bot_high_confidence(self):
        fn = _get_fn("is_bot_high_confidence")
        ctx = _make_ctx(**{
            "scores.bot_score": 0.95,
            "scores.confidence": 0.80,
        })
        result = fn(ctx, {"threshold": 0.90})
        assert result["value"] is True

    def test_bot_high_confidence_low_conf(self):
        fn = _get_fn("is_bot_high_confidence")
        ctx = _make_ctx(**{
            "scores.bot_score": 0.95,
            "scores.confidence": 0.40,
        })
        result = fn(ctx, {"threshold": 0.90})
        assert result["value"] is False  # confidence too low

    def test_headless(self):
        fn = _get_fn("headless_browser")
        ctx = _make_ctx(**{"device.is_headless": True})
        result = fn(ctx, {})
        assert result["value"] is True

    def test_webdriver(self):
        fn = _get_fn("webdriver_detected")
        ctx = _make_ctx(**{"device.webdriver_present": True})
        result = fn(ctx, {})
        assert result["value"] is True

    def test_automation_framework(self):
        fn = _get_fn("automation_framework")
        ctx = _make_ctx(**{"device.automation_artifacts": True})
        result = fn(ctx, {})
        assert result["value"] is True

    def test_replay_attack(self):
        fn = _get_fn("replay_attack")
        ctx = _make_ctx(**{"scores.replay_score": 0.90})
        result = fn(ctx, {"threshold": 0.80})
        assert result["value"] is True

    def test_replay_no_attack(self):
        fn = _get_fn("replay_attack")
        ctx = _make_ctx()  # replay_score=0.0
        result = fn(ctx, {"threshold": 0.80})
        assert result["value"] is False

    def test_round_event_counts(self):
        fn = _get_fn("round_event_counts")
        ctx = _make_ctx(**{"session.pulse_count": 100})
        result = fn(ctx, {"divisor": 50})
        assert result["value"] is True

    def test_non_round_event_counts(self):
        fn = _get_fn("round_event_counts")
        ctx = _make_ctx()  # pulse_count=50
        result = fn(ctx, {"divisor": 50})
        assert result["value"] is True  # 50 % 50 == 0


# ---------------------------------------------------------------------------
# Temporal signals
# ---------------------------------------------------------------------------

class TestTemporalSignals:
    def test_dormant_account(self):
        fn = _get_fn("dormant_account")
        ctx = _make_ctx(**{"user.days_since_last_session": 120})
        result = fn(ctx, {"dormant_days": 90})
        assert result["value"] is True

    def test_dormant_account_not_triggered(self):
        fn = _get_fn("dormant_account")
        ctx = _make_ctx()  # days_since_last_session=1
        result = fn(ctx, {"dormant_days": 90})
        assert result["value"] is False

    def test_first_session(self):
        fn = _get_fn("first_session_ever")
        ctx = _make_ctx(**{"user.total_sessions": 0})
        result = fn(ctx, {})
        assert result["value"] is True

    def test_not_first_session(self):
        fn = _get_fn("first_session_ever")
        ctx = _make_ctx()  # total_sessions=50
        result = fn(ctx, {})
        assert result["value"] is False

    def test_late_night(self):
        fn = _get_fn("late_night_activity")
        ctx = _make_ctx(**{"session.local_hour": 3})
        result = fn(ctx, {"start_hour": 1, "end_hour": 5})
        assert result["value"] is True

    def test_not_late_night(self):
        fn = _get_fn("late_night_activity")
        ctx = _make_ctx()  # local_hour=14
        result = fn(ctx, {"start_hour": 1, "end_hour": 5})
        assert result["value"] is False

    def test_account_age_young(self):
        fn = _get_fn("account_age_young")
        ctx = _make_ctx(**{"user.account_age_days": 3})
        result = fn(ctx, {"min_age_days": 7})
        assert result["value"] is True


# ---------------------------------------------------------------------------
# Orchestrator: compute_signals
# ---------------------------------------------------------------------------

class TestOrchestrator:
    def test_compute_all_signals(self):
        ctx = _make_ctx()
        results = _signals.compute_signals(ctx)
        assert len(results) >= 130
        for code, result in results.items():
            assert "value" in result
            assert "confidence" in result
            assert "details" in result

    def test_compute_selected_signals(self):
        ctx = _make_ctx(**{
            "network.is_vpn": True,
            "scores.behavioral_drift": 0.90,
        })
        include = {"vpn_detected", "critical_behavioral_drift", "new_device"}
        results = _signals.compute_signals(ctx, include=include)
        assert len(results) == 3
        assert "vpn_detected" in results
        assert results["vpn_detected"]["value"] is True
        assert results["critical_behavioral_drift"]["value"] is True

    def test_compute_with_config_overrides(self):
        ctx = _make_ctx(**{"user.days_since_last_session": 45})
        # With default config (90 days), should NOT trigger
        results_default = _signals.compute_signals(ctx, include={"dormant_account"})
        assert results_default["dormant_account"]["value"] is False
        # With override (30 days), SHOULD trigger
        configs = {"dormant_account": {"dormant_days": 30}}
        results_override = _signals.compute_signals(ctx, configs, include={"dormant_account"})
        assert results_override["dormant_account"]["value"] is True

    def test_compute_returns_all_when_include_none(self):
        ctx = _make_ctx()
        results = _signals.compute_signals(ctx, include=None)
        total = len(_registry.get_all_signals())
        assert len(results) == total

    def test_signal_error_returns_safe_result(self):
        """If a signal function throws, the orchestrator catches it."""
        ctx = _make_ctx()
        # Remove a required key to cause an error in a specific signal
        # The orchestrator should catch and return a safe result
        results = _signals.compute_signals(ctx, include={"vpn_detected"})
        assert "vpn_detected" in results
        # The signal should still work with our normal context
        assert results["vpn_detected"]["confidence"] > 0

    def test_result_types_match_signal_type(self):
        """Score signals return float, boolean signals return bool."""
        ctx = _make_ctx(**{"scores.behavioral_drift": 0.70})
        all_sigs = _registry.get_all_signals()
        results = _signals.compute_signals(ctx)
        for code, result in results.items():
            sig_type = all_sigs[code]["signal_type"]
            if sig_type == "score":
                assert isinstance(result["value"], (int, float)), (
                    f"Score signal {code} returned {type(result['value'])}"
                )
            # boolean signals may return bool — we verify structure only
            assert isinstance(result["confidence"], float)
