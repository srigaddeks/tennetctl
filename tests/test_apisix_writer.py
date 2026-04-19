"""Unit tests for featureflags.apisix_writer — pure compilation + file I/O.

Integration (worker polling, audit emit, route lookup against Postgres) is
out of scope here; this suite validates the deterministic pieces only.
"""

from __future__ import annotations

from importlib import import_module
from pathlib import Path
from typing import Any

import pytest

_writer: Any = import_module("backend.02_features.09_featureflags.apisix_writer")


# ------------------------------------------------------------- build_apisix_yaml


def test_build_yaml_emits_routes_and_end_sentinel():
    configs = [
        {
            "id": "flag-new-onboarding",
            "uri": "/v1/flags/gateway/new-onboarding",
            "plugins": {"traffic-split": {"rules": []}},
        }
    ]
    body = _writer.build_apisix_yaml(configs)
    assert body.endswith("#END\n")
    assert "flag-new-onboarding" in body
    assert "/v1/flags/gateway/new-onboarding" in body
    assert "traffic-split" in body


def test_build_yaml_empty_list_still_valid():
    body = _writer.build_apisix_yaml([])
    assert "routes" in body
    assert body.endswith("#END\n")


def test_build_yaml_methods_present_on_every_route():
    configs = [{"id": "a", "uri": "/a", "plugins": {}}, {"id": "b", "uri": "/b", "plugins": {}}]
    body = _writer.build_apisix_yaml(configs)
    # Each route gets methods — GET + POST
    assert body.count("- GET") == 2
    assert body.count("- POST") == 2


# ------------------------------------------------------------- digest


def test_digest_stable_across_calls():
    body = "routes:\n- id: x\n#END\n"
    assert _writer.digest(body) == _writer.digest(body)


def test_digest_differs_for_different_content():
    assert _writer.digest("a") != _writer.digest("b")


# ------------------------------------------------------------- write_yaml


def test_write_yaml_creates_file(tmp_path: Path):
    target = tmp_path / "apisix.yaml"
    body = "routes: []\n#END\n"

    changed = _writer.write_yaml(body, target)

    assert changed is True
    assert target.read_text() == body


def test_write_yaml_skips_unchanged(tmp_path: Path):
    target = tmp_path / "apisix.yaml"
    body = "routes: []\n#END\n"

    _writer.write_yaml(body, target)
    mtime1 = target.stat().st_mtime

    # Force a different time resolution pass
    import time as _t
    _t.sleep(0.01)

    changed = _writer.write_yaml(body, target)

    assert changed is False
    assert target.stat().st_mtime == mtime1  # untouched


def test_write_yaml_rewrites_when_changed(tmp_path: Path):
    target = tmp_path / "apisix.yaml"
    _writer.write_yaml("a\n", target)

    changed = _writer.write_yaml("b\n", target)

    assert changed is True
    assert target.read_text() == "b\n"


def test_write_yaml_atomic_via_tempfile(tmp_path: Path):
    """After write_yaml the .tmp sibling must not leak on disk."""
    target = tmp_path / "nested" / "apisix.yaml"
    _writer.write_yaml("routes: []\n#END\n", target)

    stray_tmp = list(tmp_path.rglob("*.tmp"))
    assert stray_tmp == [], f"stray tempfile left behind: {stray_tmp}"


def test_write_yaml_creates_parent_dirs(tmp_path: Path):
    target = tmp_path / "deep" / "nested" / "apisix.yaml"
    _writer.write_yaml("routes: []\n#END\n", target)
    assert target.exists()


# ------------------------------------------------------------- config


def test_config_from_env_defaults(monkeypatch):
    for var in ("APISIX_YAML_PATH", "APISIX_ADMIN_URL", "APISIX_ADMIN_KEY", "APISIX_ADMIN_ENABLED"):
        monkeypatch.delenv(var, raising=False)
    cfg = _writer.ApisixWriterConfig.from_env()
    assert cfg.yaml_path == _writer.DEFAULT_YAML_PATH
    assert cfg.admin_enabled is False


def test_config_admin_enabled_toggle(monkeypatch):
    monkeypatch.setenv("APISIX_ADMIN_ENABLED", "true")
    cfg = _writer.ApisixWriterConfig.from_env()
    assert cfg.admin_enabled is True


def test_config_custom_yaml_path(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("APISIX_YAML_PATH", str(tmp_path / "out.yaml"))
    cfg = _writer.ApisixWriterConfig.from_env()
    assert cfg.yaml_path == str(tmp_path / "out.yaml")


# ------------------------------------------------------------- publish


class _FakeConn:
    """Minimal stub — apisix_sync.compile_all_request_flags iterates over
    `conn.fetch` returning flag rows, then calls `fetchrow` for states.
    We override compile_all_request_flags in a test module instead to keep
    this simple."""

    async def fetch(self, *_args, **_kwargs):
        return []

    async def fetchrow(self, *_args, **_kwargs):
        return None


@pytest.mark.asyncio
async def test_publish_with_empty_flag_set(tmp_path: Path, monkeypatch):
    target = tmp_path / "apisix.yaml"
    monkeypatch.setenv("APISIX_YAML_PATH", str(target))
    monkeypatch.setenv("APISIX_ADMIN_ENABLED", "false")

    result = await _writer.publish(_FakeConn())

    assert result.error is None
    assert result.configs_compiled == 0
    assert result.yaml_written is True
    assert result.content_digest != ""
    assert target.exists()
    assert "#END\n" in target.read_text()


@pytest.mark.asyncio
async def test_publish_idempotent_second_call(tmp_path: Path, monkeypatch):
    target = tmp_path / "apisix.yaml"
    monkeypatch.setenv("APISIX_YAML_PATH", str(target))
    monkeypatch.setenv("APISIX_ADMIN_ENABLED", "false")

    r1 = await _writer.publish(_FakeConn())
    r2 = await _writer.publish(_FakeConn())

    assert r1.content_digest == r2.content_digest
    assert r2.yaml_written is False  # unchanged content — skip write


@pytest.mark.asyncio
async def test_publish_records_compile_error(tmp_path: Path, monkeypatch):
    """If apisix_sync.compile_all_request_flags raises, publish reports error."""
    monkeypatch.setenv("APISIX_YAML_PATH", str(tmp_path / "out.yaml"))

    _apisix_sync = import_module("backend.02_features.09_featureflags.apisix_sync")

    async def boom(*_args, **_kwargs):
        raise RuntimeError("catalog offline")

    monkeypatch.setattr(_apisix_sync, "compile_all_request_flags", boom)

    result = await _writer.publish(_FakeConn())
    assert result.error is not None
    assert "catalog offline" in result.error
    assert result.yaml_written is False
