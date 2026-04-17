"""Tests for OTLP traces receiver — mirror of logs receiver tests."""

from __future__ import annotations

from importlib import import_module
from typing import Any
from unittest.mock import AsyncMock

import pytest

pytest.importorskip("opentelemetry.proto.collector.trace.v1.trace_service_pb2")

from opentelemetry.proto.collector.trace.v1.trace_service_pb2 import (  # type: ignore
    ExportTraceServiceRequest,
)
from opentelemetry.proto.trace.v1.trace_pb2 import ResourceSpans, ScopeSpans, Span  # type: ignore
from opentelemetry.proto.common.v1.common_pb2 import AnyValue, KeyValue  # type: ignore
from opentelemetry.proto.resource.v1.resource_pb2 import Resource  # type: ignore
from google.protobuf.json_format import MessageToJson  # type: ignore

_decoder: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.03_traces.otlp_decoder"
)
_service: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.03_traces.service"
)


def _build_request(service_name: str, n_spans: int = 1) -> ExportTraceServiceRequest:
    resource = Resource()
    resource.attributes.append(
        KeyValue(key="service.name", value=AnyValue(string_value=service_name))
    )
    rs = ResourceSpans(resource=resource)
    ss = ScopeSpans()
    for i in range(n_spans):
        ss.spans.append(
            Span(
                trace_id=bytes(16),
                span_id=bytes(8),
                name=f"s-{i}",
                kind=Span.SPAN_KIND_INTERNAL,
                start_time_unix_nano=1_700_000_000_000_000_000,
                end_time_unix_nano=1_700_000_000_000_000_100,
            )
        )
    rs.scope_spans.append(ss)
    req = ExportTraceServiceRequest()
    req.resource_spans.append(rs)
    return req


def test_decode_protobuf_single_resourcespans():
    req = _build_request("orders")
    batches, rejected = _decoder.decode_traces(
        req.SerializeToString(), "application/x-protobuf"
    )
    assert rejected == 0
    assert len(batches) == 1
    assert batches[0][0] == "monitoring.traces.otel.orders"


def test_decode_json_body():
    req = _build_request("orders")
    body = MessageToJson(req).encode("utf-8")
    batches, rejected = _decoder.decode_traces(body, "application/json")
    assert rejected == 0
    assert batches[0][0] == "monitoring.traces.otel.orders"


def test_decode_malformed_returns_rejected():
    batches, rejected = _decoder.decode_traces(b"not-valid\xff", "application/json")
    assert batches == []
    assert rejected >= 1


def test_decode_multiple_resource_spans():
    req = ExportTraceServiceRequest()
    for name in ["a", "b"]:
        r = Resource()
        r.attributes.append(
            KeyValue(key="service.name", value=AnyValue(string_value=name))
        )
        rs = ResourceSpans(resource=r)
        ss = ScopeSpans()
        ss.spans.append(
            Span(trace_id=bytes(16), span_id=bytes(8), name=f"s-{name}",
                 start_time_unix_nano=1, end_time_unix_nano=2)
        )
        rs.scope_spans.append(ss)
        req.resource_spans.append(rs)
    batches, rejected = _decoder.decode_traces(
        req.SerializeToString(), "application/x-protobuf"
    )
    assert rejected == 0
    assert {b[0] for b in batches} == {
        "monitoring.traces.otel.a", "monitoring.traces.otel.b",
    }


def test_decode_slugifies_service_name():
    req = _build_request("My Service/v2")
    batches, _ = _decoder.decode_traces(
        req.SerializeToString(), "application/x-protobuf"
    )
    tail = batches[0][0].removeprefix("monitoring.traces.otel.")
    assert all(c.islower() or c.isdigit() or c in ".-_" for c in tail)


async def test_publish_traces_batch_calls_jetstream():
    req = _build_request("orders")
    js = AsyncMock()
    published, rejected = await _service.publish_traces_batch(
        req.SerializeToString(), "application/x-protobuf", js,
    )
    assert published == 1
    assert rejected == 0
    js.publish.assert_awaited_once()
    args, _ = js.publish.await_args
    assert args[0] == "monitoring.traces.otel.orders"
