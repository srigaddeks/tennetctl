"""Tests for OTLP logs receiver — protobuf + JSON + partial_success + subject routing."""

from __future__ import annotations

from importlib import import_module
from typing import Any
from unittest.mock import AsyncMock

import pytest

pytest.importorskip("opentelemetry.proto.collector.logs.v1.logs_service_pb2")

from opentelemetry.proto.collector.logs.v1.logs_service_pb2 import (  # type: ignore
    ExportLogsServiceRequest,
)
from opentelemetry.proto.logs.v1.logs_pb2 import LogRecord, ResourceLogs, ScopeLogs, SeverityNumber  # type: ignore
from opentelemetry.proto.common.v1.common_pb2 import AnyValue, KeyValue  # type: ignore
from opentelemetry.proto.resource.v1.resource_pb2 import Resource  # type: ignore
from google.protobuf.json_format import MessageToJson  # type: ignore

_decoder: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.01_logs.otlp_decoder"
)
_service: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.01_logs.service"
)


def _build_request(service_name: str, n_records: int = 1) -> ExportLogsServiceRequest:
    resource = Resource()
    resource.attributes.append(
        KeyValue(key="service.name", value=AnyValue(string_value=service_name))
    )
    rl = ResourceLogs(resource=resource)
    sl = ScopeLogs()
    for i in range(n_records):
        sl.log_records.append(
            LogRecord(
                time_unix_nano=1_700_000_000_000_000_000 + i,
                severity_number=SeverityNumber.SEVERITY_NUMBER_INFO,
                severity_text="INFO",
                body=AnyValue(string_value=f"msg-{i}"),
            )
        )
    rl.scope_logs.append(sl)
    req = ExportLogsServiceRequest()
    req.resource_logs.append(rl)
    return req


def test_decode_protobuf_batches_by_resource():
    req = _build_request("orders")
    payload = req.SerializeToString()
    batches, rejected = _decoder.decode_logs(payload, "application/x-protobuf")
    assert rejected == 0
    assert len(batches) == 1
    subject, _ = batches[0]
    assert subject == "monitoring.logs.otel.orders"


def test_decode_json_body_same_subject():
    req = _build_request("orders")
    body = MessageToJson(req).encode("utf-8")
    batches, rejected = _decoder.decode_logs(body, "application/json")
    assert rejected == 0
    assert len(batches) == 1
    assert batches[0][0] == "monitoring.logs.otel.orders"


def test_decode_malformed_protobuf_returns_rejected():
    batches, rejected = _decoder.decode_logs(b"not-a-proto\xff\xff\xff", "application/json")
    assert batches == []
    assert rejected >= 1


def test_decode_multiple_resource_logs_produces_multiple_publishes():
    req = ExportLogsServiceRequest()
    for name in ["svc-a", "svc-b", "svc-c"]:
        r = Resource()
        r.attributes.append(
            KeyValue(key="service.name", value=AnyValue(string_value=name))
        )
        rl = ResourceLogs(resource=r)
        sl = ScopeLogs()
        sl.log_records.append(LogRecord(severity_number=SeverityNumber.SEVERITY_NUMBER_INFO, severity_text="INFO"))
        rl.scope_logs.append(sl)
        req.resource_logs.append(rl)
    batches, rejected = _decoder.decode_logs(
        req.SerializeToString(), "application/x-protobuf"
    )
    assert rejected == 0
    assert {b[0] for b in batches} == {
        "monitoring.logs.otel.svc-a",
        "monitoring.logs.otel.svc-b",
        "monitoring.logs.otel.svc-c",
    }


def test_decode_slugifies_service_name():
    req = _build_request("My Service/v2")
    batches, rejected = _decoder.decode_logs(
        req.SerializeToString(), "application/x-protobuf"
    )
    assert rejected == 0
    subj = batches[0][0]
    assert subj.startswith("monitoring.logs.otel.")
    tail = subj.removeprefix("monitoring.logs.otel.")
    # Only lowercase alnum, dot, dash, underscore allowed
    assert all(c.islower() or c.isdigit() or c in ".-_" for c in tail)
    assert "my" in tail and "service" in tail


async def test_publish_logs_batch_calls_jetstream_publish():
    req = _build_request("orders", n_records=2)
    js = AsyncMock()
    published, rejected = await _service.publish_logs_batch(
        req.SerializeToString(), "application/x-protobuf", js,
    )
    assert published == 1
    assert rejected == 0
    js.publish.assert_awaited_once()
    args, kwargs = js.publish.await_args
    del kwargs
    assert args[0] == "monitoring.logs.otel.orders"
    assert isinstance(args[1], bytes)


async def test_publish_logs_batch_malformed_returns_rejected():
    js = AsyncMock()
    published, rejected = await _service.publish_logs_batch(
        b"\xff\xff\xff", "application/x-protobuf", js,
    )
    assert published == 0
    assert rejected >= 1
    js.publish.assert_not_awaited()
