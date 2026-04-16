"""Tests for backend.01_core.node_registry."""

from __future__ import annotations

from importlib import import_module

import pytest

_registry = import_module("backend.01_core.node_registry")


@pytest.fixture(autouse=True)
def clear_registry():
    """Clear the node registry before each test."""
    _registry.clear()
    yield
    _registry.clear()


def _make_contract(key: str = "test.node", kind: str = "effect") -> _registry.NodeContract:
    return _registry.NodeContract(
        key=key,
        kind=kind,
        config_schema={},
        input_schema={},
        output_schema={},
        handler="backend.test.Handler",
    )


def test_register_and_get():
    """Register a node and retrieve it by key."""
    contract = _make_contract()
    _registry.register(contract)
    result = _registry.get("test.node")
    assert result is contract


def test_get_unknown_returns_none():
    """get() returns None for unregistered key."""
    assert _registry.get("nonexistent.key") is None


def test_list_all():
    """list_all() returns all registered contracts."""
    c1 = _make_contract("a.one")
    c2 = _make_contract("b.two")
    _registry.register(c1)
    _registry.register(c2)
    result = _registry.list_all()
    assert len(result) == 2
    assert c1 in result
    assert c2 in result


def test_rejects_key_without_namespace():
    """Keys must contain a dot (namespace separator)."""
    contract = _make_contract(key="nondotted")
    with pytest.raises(ValueError, match="namespaced"):
        _registry.register(contract)


def test_rejects_invalid_kind():
    """Kind must be request, effect, or control."""
    contract = _make_contract(kind="invalid")
    with pytest.raises(ValueError, match="kind"):
        _registry.register(contract)


def test_rejects_duplicate_key():
    """Cannot register the same key twice."""
    contract = _make_contract()
    _registry.register(contract)
    with pytest.raises(ValueError, match="already registered"):
        _registry.register(contract)


def test_clear_empties_registry():
    """clear() removes all entries."""
    _registry.register(_make_contract())
    assert len(_registry.list_all()) == 1
    _registry.clear()
    assert len(_registry.list_all()) == 0


def test_all_valid_kinds():
    """All three valid kinds are accepted."""
    for kind in ("request", "effect", "control"):
        _registry.register(_make_contract(key=f"test.{kind}", kind=kind))
    assert len(_registry.list_all()) == 3


def test_contract_is_frozen():
    """NodeContract is immutable."""
    contract = _make_contract()
    with pytest.raises(AttributeError):
        contract.key = "changed"
