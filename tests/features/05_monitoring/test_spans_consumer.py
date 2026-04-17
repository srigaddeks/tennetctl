"""Unit tests for SpansConsumer — mirror of logs_consumer tests."""

from __future__ import annotations

from importlib import import_module
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

pytest.importorskip("opentelemetry.proto.trace.v1.trace_pb2")

from opentelemetry.proto.trace.v1.trace_pb2 import (  # type: ignore
    ResourceSpans, ScopeSpans, Span, Status,
)
from opentelemetry.proto.common.v1.common_pb2 import AnyValue, KeyValue  # type: ignore
from opentelemetry.proto.resource.v1.resource_pb2 import Resource  # type: ignore

_consumer_mod: Any = import_module("backend.02_features.05_monitoring.workers.spans_consumer")
SpansConsumer = _consumer_mod.SpansConsumer


def _make_resource_spans(service: str = "svc-a", n_spans: int = 1) -> bytes:
    resource = Resource()
    resource.attributes.append(KeyValue(key="service.name", value=AnyValue(string_value=service)))
    rs = ResourceSpans(resource=resource)
    ss = ScopeSpans()
    for i in range(n_spans):
        sp = Span(
            trace_id=bytes(range(32, 48)),
            span_id=(i + 1).to_bytes(8, "big"),
            name=f"span-{i}",
            kind=Span.SpanKind.SPAN_KIND_SERVER,
            start_time_unix_nano=1_700_000_000_000_000_000,
            end_time_unix_nano=1_700_000_000_500_000_000,
            status=Status(code=Status.StatusCode.STATUS_CODE_OK),
        )
        ss.spans.append(sp)
    rs.scope_spans.append(ss)
    return rs.SerializeToString()


class _FakeTx:
    async def __aenter__(self):
        return self
    async def __aexit__(self, exc_type, exc, tb):
        return False


class _FakeConn:
    def transaction(self):
        return _FakeTx()


class _FakePool:
    def __init__(self):
        self.conn = _FakeConn()

    def acquire(self):
        class _Ctx:
            def __init__(self, conn): self.conn = conn
            async def __aenter__(self): return self.conn
            async def __aexit__(self, *a): return None
        return _Ctx(self.conn)


def _make_msg(data: bytes, num_delivered: int = 1) -> Any:
    msg = MagicMock()
    msg.data = data
    msg.subject = "monitoring.traces.otel.svc-a"
    meta = MagicMock()
    meta.num_delivered = num_delivered
    msg.metadata = meta
    msg.ack = AsyncMock()
    msg.nak = AsyncMock()
    return msg


def _make_config(max_deliver: int = 5) -> Any:
    c = MagicMock()
    c.monitoring_consumer_batch_size = 200
    c.monitoring_consumer_max_deliver = max_deliver
    c.monitoring_store_kind = "postgres"
    return c


@pytest.fixture
def consumer_fixture(monkeypatch):
    pool = _FakePool()
    js = AsyncMock()
    js.publish = AsyncMock()

    spans_store = AsyncMock()
    spans_store.insert_batch = AsyncMock(return_value=1)
    resources_store = AsyncMock()
    resources_store.upsert = AsyncMock(return_value=77)

    _stores = import_module("backend.02_features.05_monitoring.stores")
    monkeypatch.setattr(_stores, "get_spans_store", lambda _p: spans_store)
    monkeypatch.setattr(_stores, "get_resources_store", lambda _p: resources_store)

    c = SpansConsumer(pool=pool, js=js, config=_make_config())
    return c, spans_store, resources_store, js


async def test_single_resource_spans_inserts_expected_records(consumer_fixture):
    c, spans_store, resources_store, _js = consumer_fixture
    msg = _make_msg(_make_resource_spans(n_spans=3))
    await c._process_batch([msg])
    resources_store.upsert.assert_awaited()
    spans_store.insert_batch.assert_awaited_once()
    records = spans_store.insert_batch.await_args.args[1]
    assert len(records) == 3
    assert records[0].resource_id == 77
    assert records[0].status_id == 1
    msg.ack.assert_awaited()


async def test_max_delivery_routes_to_dlq(consumer_fixture):
    c, spans_store, _resources, js = consumer_fixture
    spans_store.insert_batch = AsyncMock(side_effect=RuntimeError("boom"))
    msg = _make_msg(_make_resource_spans(), num_delivered=4)
    await c._process_batch([msg])
    js.publish.assert_awaited()
    args, _ = js.publish.await_args
    assert args[0] == "monitoring.dlq.spans"
    msg.ack.assert_awaited()


async def test_insert_failure_nacks_when_not_exhausted(consumer_fixture):
    c, spans_store, _resources, js = consumer_fixture
    spans_store.insert_batch = AsyncMock(side_effect=RuntimeError("transient"))
    msg = _make_msg(_make_resource_spans(), num_delivered=1)
    await c._process_batch([msg])
    msg.nak.assert_awaited()
    js.publish.assert_not_awaited()
