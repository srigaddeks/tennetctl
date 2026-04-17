"""Unit tests for LogsConsumer — JetStream + stores mocked."""

from __future__ import annotations

from importlib import import_module
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

pytest.importorskip("opentelemetry.proto.logs.v1.logs_pb2")

from opentelemetry.proto.logs.v1.logs_pb2 import (  # type: ignore
    LogRecord as PbLogRecord, ResourceLogs, ScopeLogs, SeverityNumber,
)
from opentelemetry.proto.common.v1.common_pb2 import AnyValue, KeyValue  # type: ignore
from opentelemetry.proto.resource.v1.resource_pb2 import Resource  # type: ignore

_consumer_mod: Any = import_module("backend.02_features.05_monitoring.workers.logs_consumer")
_redaction_mod: Any = import_module("backend.02_features.05_monitoring.workers.redaction")
LogsConsumer = _consumer_mod.LogsConsumer


def _make_resource_logs(service: str = "svc-a", body_text: str = "hello", attrs: dict[str, str] | None = None) -> bytes:
    resource = Resource()
    resource.attributes.append(KeyValue(key="service.name", value=AnyValue(string_value=service)))
    rl = ResourceLogs(resource=resource)
    sl = ScopeLogs()
    lr = PbLogRecord(
        time_unix_nano=1_700_000_000_000_000_000,
        observed_time_unix_nano=1_700_000_000_000_000_000,
        severity_number=SeverityNumber.SEVERITY_NUMBER_INFO,
        severity_text="INFO",
        body=AnyValue(string_value=body_text),
    )
    for k, v in (attrs or {}).items():
        lr.attributes.append(KeyValue(key=k, value=AnyValue(string_value=v)))
    sl.log_records.append(lr)
    rl.scope_logs.append(sl)
    return rl.SerializeToString()


class _FakeTx:
    async def __aenter__(self):
        return self
    async def __aexit__(self, exc_type, exc, tb):
        return False  # don't suppress exceptions


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
    msg.subject = "monitoring.logs.otel.svc-a"
    meta = MagicMock()
    meta.num_delivered = num_delivered
    msg.metadata = meta
    msg.ack = AsyncMock()
    msg.nak = AsyncMock()
    return msg


def _make_config(max_deliver: int = 5, batch: int = 200) -> Any:
    c = MagicMock()
    c.monitoring_consumer_batch_size = batch
    c.monitoring_consumer_max_deliver = max_deliver
    c.monitoring_store_kind = "postgres"
    return c


@pytest.fixture
def consumer_fixture(monkeypatch):
    pool = _FakePool()
    js = AsyncMock()
    js.publish = AsyncMock()
    config = _make_config()
    redaction = _redaction_mod.RedactionEngine()
    redaction.set_rules([])

    logs_store = AsyncMock()
    logs_store.insert_batch = AsyncMock(return_value=1)
    resources_store = AsyncMock()
    resources_store.upsert = AsyncMock(return_value=42)

    # Patch the store factories used at LogsConsumer __init__.
    _stores = import_module("backend.02_features.05_monitoring.stores")
    monkeypatch.setattr(_stores, "get_logs_store", lambda _p: logs_store)
    monkeypatch.setattr(_stores, "get_resources_store", lambda _p: resources_store)

    c = LogsConsumer(pool=pool, js=js, config=config, redaction=redaction)
    return c, logs_store, resources_store, js


async def test_single_resource_logs_batch_inserts_expected_record(consumer_fixture):
    c, logs_store, resources_store, _js = consumer_fixture
    msg = _make_msg(_make_resource_logs(body_text="hello"))
    await c._process_batch([msg])
    resources_store.upsert.assert_awaited()
    logs_store.insert_batch.assert_awaited()
    inserted = logs_store.insert_batch.await_args.args[1]
    assert len(inserted) == 1
    assert inserted[0].body == "hello"
    assert inserted[0].resource_id == 42
    msg.ack.assert_awaited()


async def test_batch_of_five_one_transaction(consumer_fixture):
    c, logs_store, _resources, _js = consumer_fixture
    msgs = [_make_msg(_make_resource_logs(body_text=f"msg-{i}")) for i in range(5)]
    await c._process_batch(msgs)
    # Exactly one insert_batch call with all 5 records.
    logs_store.insert_batch.assert_awaited_once()
    records = logs_store.insert_batch.await_args.args[1]
    assert len(records) == 5
    for m in msgs:
        m.ack.assert_awaited()


async def test_max_delivery_routes_to_dlq(consumer_fixture):
    c, logs_store, _resources, js = consumer_fixture
    logs_store.insert_batch = AsyncMock(side_effect=RuntimeError("boom"))
    # num_delivered=4 means this is the 4th attempt; max_deliver=5 triggers DLQ.
    msg = _make_msg(_make_resource_logs(), num_delivered=4)
    await c._process_batch([msg])
    js.publish.assert_awaited()
    args, _ = js.publish.await_args
    assert args[0] == "monitoring.dlq.logs"
    msg.ack.assert_awaited()


async def test_insert_failure_nacks_when_not_exhausted(consumer_fixture):
    c, logs_store, _resources, js = consumer_fixture
    logs_store.insert_batch = AsyncMock(side_effect=RuntimeError("transient"))
    msg = _make_msg(_make_resource_logs(), num_delivered=1)
    await c._process_batch([msg])
    msg.nak.assert_awaited()
    # DLQ must NOT be published for transient retryable failures.
    js.publish.assert_not_awaited()


async def test_decode_failure_goes_to_dlq(consumer_fixture):
    c, logs_store, _resources, js = consumer_fixture
    bad_msg = _make_msg(b"\x00\x01not-a-valid-protobuf\xff\xff", num_delivered=1)
    await c._process_batch([bad_msg])
    # Decode failures route to DLQ regardless of delivery count.
    js.publish.assert_awaited()
    bad_msg.ack.assert_awaited()
    # No insert attempted.
    logs_store.insert_batch.assert_not_awaited()
