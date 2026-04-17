"""OTLP logs decoder.

Decodes OTLP/HTTP bodies (protobuf or JSON) into a list of
``(subject, payload_bytes)`` tuples. Each ResourceLogs becomes one NATS
message — so the downstream consumer (13-04) sees exactly one ResourceLogs
per JetStream message and doesn't have to re-split batches.

Subject is derived from the resource's ``service.name`` attribute, slugified
to lowercase ``[a-z0-9._-]`` only. Missing service.name → ``unknown``.
"""

from __future__ import annotations

import re
from typing import Any

from opentelemetry.proto.collector.logs.v1.logs_service_pb2 import (  # pyright: ignore[reportMissingImports, reportMissingTypeStubs]
    ExportLogsServiceRequest,
)
from opentelemetry.proto.logs.v1.logs_pb2 import (  # pyright: ignore[reportMissingImports, reportMissingTypeStubs]
    ResourceLogs,
)
from google.protobuf.json_format import Parse, ParseError  # pyright: ignore[reportMissingImports, reportMissingTypeStubs]

_SLUG_RE = re.compile(r"[^a-z0-9._-]+")
_SUBJECT_PREFIX = "monitoring.logs.otel."
_FALLBACK_SERVICE = "unknown"


def _slugify_service_name(name: str) -> str:
    """Lowercase and replace any char outside [a-z0-9._-] with ``-``."""
    if not name:
        return _FALLBACK_SERVICE
    slug = _SLUG_RE.sub("-", name.lower()).strip("-.")
    return slug or _FALLBACK_SERVICE


def _extract_service_name(resource_logs: Any) -> str:
    """Pull service.name from the ResourceLogs' resource attributes."""
    resource = getattr(resource_logs, "resource", None)
    if resource is None:
        return _FALLBACK_SERVICE
    for attr in resource.attributes:
        if attr.key == "service.name":
            v = attr.value
            # OTel AnyValue supports string_value on string_value oneof
            if v.HasField("string_value"):
                return v.string_value
    return _FALLBACK_SERVICE


def decode_logs(body: bytes, content_type: str) -> tuple[list[tuple[str, bytes]], int]:
    """Decode an OTLP/HTTP logs body.

    Returns (batches, rejected_count). ``batches`` is a list of
    (subject, payload_bytes) where payload_bytes is a serialized ResourceLogs
    protobuf. ``rejected_count`` is 0 on success; on parse failure it is the
    total number of LogRecords attempted (best-effort — ``-1`` when unknown
    is normalized to ``0`` + we keep the semantic of "at least one rejected").
    """
    ctype = (content_type or "").split(";")[0].strip().lower()
    req = ExportLogsServiceRequest()
    try:
        if ctype == "application/json":
            Parse(body.decode("utf-8"), req)
        else:
            # Default to protobuf for any non-JSON content type
            req.ParseFromString(body)
    except (ParseError, ValueError, UnicodeDecodeError, Exception):  # noqa: BLE001
        # Spec: on total parse failure we can't know how many logs were in the
        # body. Report at least 1 rejected so partial_success is non-empty.
        return [], 1

    batches: list[tuple[str, bytes]] = []
    for rl in req.resource_logs:
        service_name = _extract_service_name(rl)
        subject = _SUBJECT_PREFIX + _slugify_service_name(service_name)
        # Serialize just this ResourceLogs as the payload
        single = ResourceLogs()
        single.CopyFrom(rl)
        batches.append((subject, single.SerializeToString()))
    return batches, 0


__all__ = ["decode_logs"]
