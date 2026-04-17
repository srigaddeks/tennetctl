"""Tests for JetStream bootstrap — graceful failure + idempotency."""

from __future__ import annotations

from importlib import import_module
from typing import Any
from unittest.mock import AsyncMock

import pytest

pytest.importorskip("nats")

_jsb: Any = import_module("backend.02_features.05_monitoring.bootstrap.jetstream")
_nats_core: Any = import_module("backend.01_core.nats")
from nats.js.errors import NotFoundError  # type: ignore


async def test_bootstrap_creates_when_missing():
    js = AsyncMock()
    js.update_stream = AsyncMock(side_effect=NotFoundError)
    js.add_stream = AsyncMock()
    await _jsb.bootstrap_monitoring_jetstream(js)
    # 3 streams: LOGS, SPANS, DLQ
    assert js.add_stream.await_count == 3


async def test_bootstrap_idempotent_when_present():
    js = AsyncMock()
    js.update_stream = AsyncMock(return_value=None)
    js.add_stream = AsyncMock()
    await _jsb.bootstrap_monitoring_jetstream(js)
    assert js.update_stream.await_count == 3
    assert js.add_stream.await_count == 0


async def test_bootstrap_config_update_path():
    # Mix: update succeeds for two, NotFound on third.
    js = AsyncMock()

    call_count = {"n": 0}
    async def _update(**kwargs):
        del kwargs
        call_count["n"] += 1
        if call_count["n"] == 3:
            raise NotFoundError
        return None

    js.update_stream = _update
    js.add_stream = AsyncMock()
    await _jsb.bootstrap_monitoring_jetstream(js)
    assert js.add_stream.await_count == 1


async def test_nats_connect_graceful_failure(monkeypatch):
    """If nats.connect raises, we propagate — the lifespan catches it."""
    _nats_core._reset_for_tests()
    async def _raise(*args, **kw):
        del args, kw
        raise ConnectionRefusedError("no NATS")
    monkeypatch.setattr(
        import_module("backend.01_core.nats").__dict__["nats"], "connect", _raise,
    )
    with pytest.raises(ConnectionRefusedError):
        await _nats_core.connect("nats://localhost:9999")
