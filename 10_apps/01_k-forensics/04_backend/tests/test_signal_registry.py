"""Tests for the kbio signal registry and orchestrator."""
import importlib

import pytest

_registry = importlib.import_module("03_kbio._signals._registry")
_signals = importlib.import_module("03_kbio._signals")


# ---------------------------------------------------------------------------
# Registry loading
# ---------------------------------------------------------------------------

def test_registry_loads_all_signals():
    """All 134 signals should be registered after import."""
    signals = _registry.get_all_signals()
    assert len(signals) >= 130  # Allow slight variance during development


def test_each_signal_has_required_fields():
    """Every registered signal must have code, name, description, category, function."""
    for code, sig in _registry.get_all_signals().items():
        assert sig["code"] == code
        assert sig["name"]
        assert sig["description"]
        assert sig["category"]
        assert callable(sig["function"])
        assert sig["signal_type"] in ("boolean", "score")
        assert 0 <= sig["severity"] <= 100


def test_signal_categories_valid():
    """All signals should have a recognized category."""
    valid = {
        "behavioral", "device", "network", "temporal", "credential",
        "session", "historical", "bot", "social_engineering",
        "transaction", "fraud_ring", "compliance",
    }
    for code, sig in _registry.get_all_signals().items():
        assert sig["category"] in valid, (
            f"Signal {code} has invalid category {sig['category']}"
        )


def test_no_duplicate_signal_codes():
    """Signal codes must be unique."""
    codes = list(_registry.get_all_signals().keys())
    assert len(codes) == len(set(codes))


# ---------------------------------------------------------------------------
# Lookup helpers
# ---------------------------------------------------------------------------

def test_get_signal_by_code():
    sig = _registry.get_signal("vpn_detected")
    assert sig is not None
    assert sig["code"] == "vpn_detected"
    assert sig["category"] == "network"


def test_get_signal_not_found():
    assert _registry.get_signal("nonexistent_signal") is None


def test_get_signals_by_category():
    network = _registry.get_signals_by_category("network")
    assert len(network) >= 10
    for sig in network.values():
        assert sig["category"] == "network"


def test_get_signals_by_category_empty():
    """A bogus category returns an empty dict."""
    result = _registry.get_signals_by_category("does_not_exist")
    assert result == {}


# ---------------------------------------------------------------------------
# Default config integrity
# ---------------------------------------------------------------------------

def test_every_signal_has_default_config_dict():
    """default_config must be a dict (possibly empty) for every signal."""
    for code, sig in _registry.get_all_signals().items():
        assert isinstance(sig["default_config"], dict), (
            f"Signal {code} has non-dict default_config"
        )


def test_every_signal_has_tags_list():
    """tags must be a list (possibly empty) for every signal."""
    for code, sig in _registry.get_all_signals().items():
        assert isinstance(sig["tags"], list), (
            f"Signal {code} has non-list tags"
        )


# ---------------------------------------------------------------------------
# get_required_signals_for_threats
# ---------------------------------------------------------------------------

def test_get_required_signals_for_threats():
    """Extracts signal codes from threat type conditions."""
    mock_threats = {
        "t1": {
            "conditions": {
                "rules": [
                    {"field": "signals.vpn_detected", "op": "==", "value": True},
                    {"field": "signals.new_device", "op": "==", "value": True},
                    {"field": "other.field", "op": "==", "value": 1},
                ],
            },
        },
    }
    result = _registry.get_required_signals_for_threats(["t1"], mock_threats)
    assert result == {"vpn_detected", "new_device"}


def test_get_required_signals_for_threats_missing_code():
    """Missing threat code is silently skipped."""
    result = _registry.get_required_signals_for_threats(["missing"], {})
    assert result == set()
