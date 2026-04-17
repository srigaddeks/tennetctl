"""OTLP traces decoder.

Mirror of the logs decoder. Each ResourceSpans becomes one NATS message on
``monitoring.traces.otel.{service_name}``.
"""

from __future__ import annotations

import re
from typing import Any

from opentelemetry.proto.collector.trace.v1.trace_service_pb2 import (  # pyright: ignore[reportMissingImports, reportMissingTypeStubs]
    ExportTraceServiceRequest,
)
from opentelemetry.proto.trace.v1.trace_pb2 import (  # pyright: ignore[reportMissingImports, reportMissingTypeStubs]
    ResourceSpans,
)
from google.protobuf.json_format import Parse, ParseError  # pyright: ignore[reportMissingImports, reportMissingTypeStubs]

_SLUG_RE = re.compile(r"[^a-z0-9._-]+")
_SUBJECT_PREFIX = "monitoring.traces.otel."
_FALLBACK_SERVICE = "unknown"


def _slugify_service_name(name: str) -> str:
    if not name:
        return _FALLBACK_SERVICE
    slug = _SLUG_RE.sub("-", name.lower()).strip("-.")
    return slug or _FALLBACK_SERVICE


def _extract_service_name(resource_spans: Any) -> str:
    resource = getattr(resource_spans, "resource", None)
    if resource is None:
        return _FALLBACK_SERVICE
    for attr in resource.attributes:
        if attr.key == "service.name":
            v = attr.value
            if v.HasField("string_value"):
                return v.string_value
    return _FALLBACK_SERVICE


def decode_traces(body: bytes, content_type: str) -> tuple[list[tuple[str, bytes]], int]:
    """Decode an OTLP/HTTP traces body.

    Returns (batches, rejected_count).
    """
    ctype = (content_type or "").split(";")[0].strip().lower()
    req = ExportTraceServiceRequest()
    try:
        if ctype == "application/json":
            Parse(body.decode("utf-8"), req)
        else:
            req.ParseFromString(body)
    except (ParseError, ValueError, UnicodeDecodeError, Exception):  # noqa: BLE001
        return [], 1

    batches: list[tuple[str, bytes]] = []
    for rs in req.resource_spans:
        service_name = _extract_service_name(rs)
        subject = _SUBJECT_PREFIX + _slugify_service_name(service_name)
        single = ResourceSpans()
        single.CopyFrom(rs)
        batches.append((subject, single.SerializeToString()))
    return batches, 0


__all__ = ["decode_traces"]
