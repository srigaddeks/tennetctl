"""Service layer for OTLP logs ingest.

Takes a decoded batch list and publishes each to JetStream. No DB writes.
"""

from __future__ import annotations

import logging
from importlib import import_module
from typing import Any

_decoder: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.01_logs.otlp_decoder"
)
decode_logs = _decoder.decode_logs

_dsl: Any = import_module("backend.02_features.05_monitoring.query_dsl")

logger = logging.getLogger("tennetctl.monitoring.logs")


async def query(
    conn: Any,
    ctx: Any,
    dsl: dict[str, Any],
) -> tuple[list[dict[str, Any]], str | None]:
    """Validate + compile + execute a logs DSL query. Returns (rows, next_cursor)."""
    q = _dsl.validate_logs_query(dsl)
    sql, params = _dsl.compile_logs_query(q, ctx)
    rows = await conn.fetch(sql, *params)
    items = [dict(r) for r in rows]
    next_cursor = None
    if len(items) == q.limit and items:
        last = items[-1]
        next_cursor = _dsl.encode_cursor({
            "recorded_at": last.get("recorded_at"),
            "id": last.get("id"),
        })
    return items, next_cursor


async def publish_logs_batch(
    body: bytes,
    content_type: str,
    js: Any,
) -> tuple[int, int]:
    """Decode body, publish every ResourceLogs to JetStream.

    Returns (published_count, rejected_count).
    """
    batches, rejected = decode_logs(body, content_type)
    published = 0
    for subject, payload in batches:
        try:
            await js.publish(subject, payload)
            published += 1
        except Exception as e:  # noqa: BLE001
            logger.warning("monitoring.logs publish failed: %s", e)
            rejected += 1
    return published, rejected
