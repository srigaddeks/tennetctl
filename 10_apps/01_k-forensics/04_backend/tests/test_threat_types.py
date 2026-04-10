"""Tests for the kbio threat type registry and evaluation.

The evaluate_threats() function depends on the kprotect rule engine
(02_features.evaluate.rule_engine). Since that module may not yet
exist, we test evaluation by installing a lightweight mock that
implements the same interface.
"""
import importlib
import sys
import types
from unittest.mock import MagicMock

import pytest

_threat_registry = importlib.import_module("03_kbio._threats._registry")
# Force-import category modules via the package init
_threats_pkg = importlib.import_module("03_kbio._threats")


# ---------------------------------------------------------------------------
# Mock rule engine — installed before evaluate_threats runs
# ---------------------------------------------------------------------------

def _mock_evaluate_policy(conditions, ctx, config):
    """Simple condition evaluator matching the kprotect rule engine interface.

    Supports AND/OR operators with == and > comparisons on signal values.
    Returns (action, reason, extra_dict).
    """
    rules = conditions.get("rules", [])
    operator = conditions.get("operator", "AND")
    action = conditions.get("action", "block")
    reason = conditions.get("reason_template", "")

    results = []
    for rule in rules:
        field = rule.get("field", "")
        op = rule.get("op", "==")
        expected = rule.get("value")

        # Resolve field from ctx (e.g. "signals.vpn_detected" -> ctx["signals"]["vpn_detected"]["value"])
        parts = field.split(".")
        val = ctx
        for p in parts:
            if isinstance(val, dict):
                val = val.get(p)
            else:
                val = None
                break

        # Signal results are dicts with "value" key
        if isinstance(val, dict) and "value" in val:
            val = val["value"]

        if val is None:
            results.append(False)
            continue

        if op == "==":
            results.append(val == expected)
        elif op == ">":
            results.append(val > expected)
        elif op == "<":
            results.append(val < expected)
        elif op == ">=":
            results.append(val >= expected)
        elif op == "!=":
            results.append(val != expected)
        else:
            results.append(False)

    if operator == "AND":
        matched = all(results) if results else False
    elif operator == "OR":
        matched = any(results) if results else False
    else:
        matched = False

    if matched:
        return (action, reason, {})
    return ("allow", "", {})


def _install_mock_rule_engine():
    """Install a mock rule engine module at 02_features.evaluate.rule_engine."""
    mod = types.ModuleType("02_features.evaluate.rule_engine")
    mod.evaluate_policy = _mock_evaluate_policy
    sys.modules["02_features.evaluate.rule_engine"] = mod
    # Also create parent modules so importlib.import_module works
    if "02_features" not in sys.modules:
        parent = types.ModuleType("02_features")
        sys.modules["02_features"] = parent
    if "02_features.evaluate" not in sys.modules:
        evaluate = types.ModuleType("02_features.evaluate")
        sys.modules["02_features.evaluate"] = evaluate


_install_mock_rule_engine()


# ---------------------------------------------------------------------------
# Registry tests
# ---------------------------------------------------------------------------

def test_registry_loads_all_threats():
    threats = _threat_registry.get_all_threat_types()
    assert len(threats) >= 50


def test_each_threat_has_required_fields():
    for code, t in _threat_registry.get_all_threat_types().items():
        assert t["code"] == code
        assert t["name"]
        assert t["description"]
        assert t["category"]
        assert t["severity"] >= 0
        assert t["default_action"] in (
            "allow", "monitor", "flag", "throttle", "challenge", "block",
        )
        assert "rules" in t["conditions"]
        assert "action" in t["conditions"]


def test_threat_categories_valid():
    valid = {
        "account_takeover", "bot_attacks", "identity_fraud",
        "social_engineering", "network_threats", "transaction_fraud",
        "fraud_ring", "compliance",
    }
    for code, t in _threat_registry.get_all_threat_types().items():
        assert t["category"] in valid, (
            f"Threat {code} has invalid category {t['category']}"
        )


def test_no_duplicate_threat_codes():
    codes = list(_threat_registry.get_all_threat_types().keys())
    assert len(codes) == len(set(codes))


def test_every_threat_has_default_config_dict():
    for code, t in _threat_registry.get_all_threat_types().items():
        assert isinstance(t["default_config"], dict), (
            f"Threat {code} has non-dict default_config"
        )


def test_every_threat_has_tags_list():
    for code, t in _threat_registry.get_all_threat_types().items():
        assert isinstance(t["tags"], list), (
            f"Threat {code} has non-list tags"
        )


def test_every_threat_has_reason_template():
    for code, t in _threat_registry.get_all_threat_types().items():
        assert isinstance(t["reason_template"], str), (
            f"Threat {code} has non-str reason_template"
        )


# ---------------------------------------------------------------------------
# Lookup helpers
# ---------------------------------------------------------------------------

def test_get_threat_type_by_code():
    t = _threat_registry.get_threat_type("ato-new-device-high-drift")
    assert t is not None
    assert t["code"] == "ato-new-device-high-drift"
    assert t["category"] == "account_takeover"


def test_get_threat_type_not_found():
    assert _threat_registry.get_threat_type("nonexistent") is None


def test_get_threat_types_by_category():
    ato = _threat_registry.get_threat_types_by_category("account_takeover")
    assert len(ato) >= 5
    for t in ato.values():
        assert t["category"] == "account_takeover"


def test_get_threat_types_by_category_empty():
    result = _threat_registry.get_threat_types_by_category("does_not_exist")
    assert result == {}


# ---------------------------------------------------------------------------
# Evaluation tests (using mock rule engine)
# ---------------------------------------------------------------------------

class TestEvaluateThreats:
    def test_ato_new_device_high_drift_fires(self):
        """ATO threat fires when critical drift + new device + not bot."""
        ctx = {
            "signals": {
                "critical_behavioral_drift": {"value": True, "confidence": 0.9, "details": {}},
                "new_device": {"value": True, "confidence": 1.0, "details": {}},
                "is_bot": {"value": False, "confidence": 0.9, "details": {}},
            },
        }
        threats = _threats_pkg.evaluate_threats(
            ctx, include={"ato-new-device-high-drift"},
        )
        assert len(threats) == 1
        assert threats[0]["code"] == "ato-new-device-high-drift"
        assert threats[0]["default_action"] == "block"
        assert threats[0]["severity"] == 90

    def test_ato_no_match_when_drift_false(self):
        """Threat should not fire when signals don't match."""
        ctx = {
            "signals": {
                "critical_behavioral_drift": {"value": False, "confidence": 0.9, "details": {}},
                "new_device": {"value": True, "confidence": 1.0, "details": {}},
                "is_bot": {"value": False, "confidence": 0.9, "details": {}},
            },
        }
        threats = _threats_pkg.evaluate_threats(
            ctx, include={"ato-new-device-high-drift"},
        )
        assert len(threats) == 0

    def test_bot_high_confidence(self):
        ctx = {
            "signals": {
                "is_bot_high_confidence": {"value": True, "confidence": 0.95, "details": {}},
            },
        }
        threats = _threats_pkg.evaluate_threats(
            ctx, include={"bot-high-confidence"},
        )
        assert len(threats) == 1
        assert threats[0]["default_action"] == "block"
        assert threats[0]["severity"] == 95

    def test_bot_high_confidence_no_match(self):
        ctx = {
            "signals": {
                "is_bot_high_confidence": {"value": False, "confidence": 0.95, "details": {}},
            },
        }
        threats = _threats_pkg.evaluate_threats(
            ctx, include={"bot-high-confidence"},
        )
        assert len(threats) == 0

    def test_empty_signals_no_threats(self):
        """With no signals firing, no threats should match."""
        ctx = {"signals": {}}
        threats = _threats_pkg.evaluate_threats(ctx)
        assert len(threats) == 0

    def test_selective_evaluation(self):
        """Only evaluate the specified threats."""
        ctx = {
            "signals": {
                "is_bot_high_confidence": {"value": True, "confidence": 0.95, "details": {}},
                "critical_behavioral_drift": {"value": True, "confidence": 0.9, "details": {}},
                "new_device": {"value": True, "confidence": 1.0, "details": {}},
                "is_bot": {"value": True, "confidence": 0.9, "details": {}},
            },
        }
        # Only evaluate bot threats, not ATO
        threats = _threats_pkg.evaluate_threats(
            ctx, include={"bot-high-confidence"},
        )
        assert len(threats) == 1
        assert threats[0]["code"] == "bot-high-confidence"

    def test_threat_result_has_required_fields(self):
        ctx = {
            "signals": {
                "is_bot_high_confidence": {"value": True, "confidence": 0.95, "details": {}},
            },
        }
        threats = _threats_pkg.evaluate_threats(
            ctx, include={"bot-high-confidence"},
        )
        assert len(threats) == 1
        t = threats[0]
        assert "code" in t
        assert "name" in t
        assert "category" in t
        assert "severity" in t
        assert "default_action" in t
        assert "reason" in t
        assert "matched_signals" in t
        assert "execution_ms" in t

    def test_ato_session_hijack(self):
        ctx = {
            "signals": {
                "mid_session_takeover": {"value": True, "confidence": 0.9, "details": {}},
                "velocity_spike": {"value": True, "confidence": 0.85, "details": {}},
            },
        }
        threats = _threats_pkg.evaluate_threats(
            ctx, include={"ato-session-hijack"},
        )
        assert len(threats) == 1
        assert threats[0]["code"] == "ato-session-hijack"
        assert threats[0]["default_action"] == "block"

    def test_bot_headless(self):
        ctx = {
            "signals": {
                "headless_browser": {"value": True, "confidence": 0.95, "details": {}},
            },
        }
        threats = _threats_pkg.evaluate_threats(
            ctx, include={"bot-headless"},
        )
        assert len(threats) == 1
        assert threats[0]["default_action"] == "block"
        assert threats[0]["severity"] == 85

    def test_bot_replay(self):
        ctx = {
            "signals": {
                "replay_attack": {"value": True, "confidence": 0.85, "details": {}},
            },
        }
        threats = _threats_pkg.evaluate_threats(
            ctx, include={"bot-replay"},
        )
        assert len(threats) == 1
        assert threats[0]["severity"] == 90

    def test_matched_signals_populated(self):
        """matched_signals should list the signal codes from the conditions."""
        ctx = {
            "signals": {
                "critical_behavioral_drift": {"value": True, "confidence": 0.9, "details": {}},
                "new_device": {"value": True, "confidence": 1.0, "details": {}},
                "is_bot": {"value": False, "confidence": 0.9, "details": {}},
            },
        }
        threats = _threats_pkg.evaluate_threats(
            ctx, include={"ato-new-device-high-drift"},
        )
        assert len(threats) == 1
        assert set(threats[0]["matched_signals"]) == {
            "critical_behavioral_drift", "new_device", "is_bot",
        }

    def test_execution_ms_positive(self):
        ctx = {
            "signals": {
                "is_bot_high_confidence": {"value": True, "confidence": 0.95, "details": {}},
            },
        }
        threats = _threats_pkg.evaluate_threats(
            ctx, include={"bot-high-confidence"},
        )
        assert threats[0]["execution_ms"] >= 0

    def test_multiple_threats_can_fire(self):
        """Multiple threats can match simultaneously."""
        ctx = {
            "signals": {
                "is_bot_high_confidence": {"value": True, "confidence": 0.95, "details": {}},
                "headless_browser": {"value": True, "confidence": 0.95, "details": {}},
            },
        }
        threats = _threats_pkg.evaluate_threats(
            ctx, include={"bot-high-confidence", "bot-headless"},
        )
        assert len(threats) == 2
        codes = {t["code"] for t in threats}
        assert "bot-high-confidence" in codes
        assert "bot-headless" in codes
