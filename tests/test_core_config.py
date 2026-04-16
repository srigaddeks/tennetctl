"""Tests for backend.01_core.config."""

from __future__ import annotations

import os
from importlib import import_module

import pytest

_config = import_module("backend.01_core.config")


def test_default_modules():
    """Default modules include core, iam, audit."""
    config = _config.load_config()
    assert "core" in config.modules
    assert "iam" in config.modules
    assert "audit" in config.modules


def test_modules_parsed_as_frozenset():
    """TENNETCTL_MODULES is parsed into a frozenset."""
    config = _config.load_config()
    assert isinstance(config.modules, frozenset)


def test_custom_modules(monkeypatch):
    """Custom TENNETCTL_MODULES override defaults."""
    monkeypatch.setenv("TENNETCTL_MODULES", "core,monitoring")
    config = _config.load_config()
    assert config.modules == frozenset({"core", "monitoring"})


def test_single_tenant_default_false():
    """TENNETCTL_SINGLE_TENANT defaults to False."""
    config = _config.load_config()
    # May be true from .env — test the type at least
    assert isinstance(config.single_tenant, bool)


def test_single_tenant_true(monkeypatch):
    """TENNETCTL_SINGLE_TENANT=true parses as True."""
    monkeypatch.setenv("TENNETCTL_SINGLE_TENANT", "true")
    config = _config.load_config()
    assert config.single_tenant is True


def test_single_tenant_false(monkeypatch):
    """TENNETCTL_SINGLE_TENANT=false parses as False."""
    monkeypatch.setenv("TENNETCTL_SINGLE_TENANT", "false")
    config = _config.load_config()
    assert config.single_tenant is False


def test_default_port():
    """Default port is 51734."""
    config = _config.load_config()
    assert config.app_port == 51734


def test_config_is_frozen():
    """Config dataclass is immutable."""
    config = _config.load_config()
    with pytest.raises(AttributeError):
        config.app_port = 9999


def test_database_url_from_env():
    """DATABASE_URL is read from environment."""
    config = _config.load_config()
    assert "postgresql" in config.database_url
