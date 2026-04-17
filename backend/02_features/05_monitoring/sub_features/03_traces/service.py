"""Service layer for OTLP traces ingest."""

from __future__ import annotations

import logging
from importlib import import_module
from typing import Any

_decoder: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.03_traces.otlp_decoder"
)
decode_traces = _decoder.decode_traces

_dsl: Any = import_module("backend.02_features.05_monitoring.query_dsl")

logger = logging.getLogger("tennetctl.monitoring.traces")


async def query(
    conn: Any,
    ctx: Any,
    dsl: dict[str, Any],
) -> tuple[list[dict[str, Any]], str | None]:
    q = _dsl.validate_traces_query(dsl)
    sql, params = _dsl.compile_traces_query(q, ctx)
    rows = await conn.fetch(sql, *params)
    items = [dict(r) for r in rows]
    next_cursor = None
    if len(items) == q.limit and items:
        last = items[-1]
        next_cursor = _dsl.encode_cursor({
            "recorded_at": last.get("recorded_at"),
            "id": last.get("span_id"),
        })
    return items, next_cursor


async def get_trace(
    conn: Any,
    ctx: Any,
    trace_id: str,
) -> list[dict[str, Any]]:
    sql, params = _dsl.compile_trace_detail(trace_id, ctx)
    rows = await conn.fetch(sql, *params)
    return [dict(r) for r in rows]


async def publish_traces_batch(
    body: bytes,
    content_type: str,
    js: Any,
) -> tuple[int, int]:
    """Decode and publish each ResourceSpans to JetStream."""
    batches, rejected = decode_traces(body, content_type)
    published = 0
    for subject, payload in batches:
        try:
            await js.publish(subject, payload)
            published += 1
        except Exception as e:  # noqa: BLE001
            logger.warning("monitoring.traces publish failed: %s", e)
            rejected += 1
    return published, rejected
