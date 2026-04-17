"""JetStream → Postgres spans consumer.

Parallel to logs_consumer — drains MONITORING_SPANS stream. No redaction on
spans (per 13-04 scope; defer to v0.2).
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from importlib import import_module
from typing import Any

from opentelemetry.proto.trace.v1.trace_pb2 import (  # pyright: ignore[reportMissingImports, reportMissingTypeStubs]
    ResourceSpans,
)

_stores: Any = import_module("backend.02_features.05_monitoring.stores")
_types: Any = import_module("backend.02_features.05_monitoring.stores.types")
_logs_consumer: Any = import_module("backend.02_features.05_monitoring.workers.logs_consumer")

logger = logging.getLogger("tennetctl.monitoring.spans_consumer")

_DURABLE = "monitoring-spans-postgres"
_SUBJECT_FILTER = "monitoring.traces.otel.>"
_DLQ_SUBJECT = "monitoring.dlq.spans"


def _hex(bs: bytes) -> str | None:
    if not bs:
        return None
    return bs.hex()


def _nanos_to_dt(nanos: int) -> datetime:
    if not nanos:
        return datetime.now(timezone.utc).replace(tzinfo=None)
    return datetime.fromtimestamp(nanos / 1_000_000_000, tz=timezone.utc).replace(tzinfo=None)


def _build_span_records(rs: Any, resource_id: int, org_id: str) -> list[Any]:
    records: list[Any] = []
    for scope_spans in rs.scope_spans:
        for sp in scope_spans.spans:
            status_id = int(sp.status.code) if sp.HasField("status") else 0
            trace_id = _hex(sp.trace_id) or ""
            span_id = _hex(sp.span_id) or ""
            if not trace_id or not span_id:
                continue
            records.append(
                _types.SpanRecord(
                    trace_id=trace_id,
                    span_id=span_id,
                    parent_span_id=_hex(sp.parent_span_id),
                    org_id=org_id,
                    workspace_id=None,
                    resource_id=resource_id,
                    name=sp.name or "unknown",
                    kind_id=int(sp.kind) if sp.kind else 0,
                    status_id=status_id,
                    status_message=sp.status.message if sp.HasField("status") and sp.status.message else None,
                    recorded_at=_nanos_to_dt(sp.start_time_unix_nano),
                    start_time_unix_nano=int(sp.start_time_unix_nano or 0),
                    end_time_unix_nano=int(sp.end_time_unix_nano or 0),
                    attributes=_logs_consumer._kvs_to_dict(sp.attributes),
                    events=[],
                    links=[],
                )
            )
    return records


class SpansConsumer:
    """Pull-subscribe consumer draining MONITORING_SPANS into Postgres."""

    def __init__(
        self,
        pool: Any,
        js: Any,
        config: Any,
        org_id: str = "tennetctl",
    ) -> None:
        self._pool = pool
        self._js = js
        self._config = config
        self._org_id = org_id
        self._stop = asyncio.Event()
        self._sub: Any = None
        self._spans_store = _stores.get_spans_store(pool)
        self._resources_store = _stores.get_resources_store(pool)
        self.heartbeat_at: datetime | None = None

    async def _ensure_subscription(self) -> None:
        if self._sub is not None:
            return
        self._sub = await self._js.pull_subscribe(
            subject=_SUBJECT_FILTER,
            durable=_DURABLE,
            stream="MONITORING_SPANS",
        )

    async def _dlq(self, msg: Any, reason: str) -> None:
        try:
            headers = {"tennetctl-dlq-reason": reason[:200], "tennetctl-dlq-subject": getattr(msg, "subject", "")}
            await self._js.publish(_DLQ_SUBJECT, msg.data, headers=headers)
            logger.warning("spans_consumer: message routed to DLQ (%s)", reason)
        except Exception as e:  # noqa: BLE001
            logger.error("spans_consumer: DLQ publish failed: %s", e)

    async def _handle_failure(self, msg: Any, reason: str) -> None:
        try:
            num_delivered = getattr(msg.metadata, "num_delivered", 1) if hasattr(msg, "metadata") else 1
        except Exception:  # noqa: BLE001
            num_delivered = 1
        max_deliver = int(getattr(self._config, "monitoring_consumer_max_deliver", 5))
        if num_delivered >= max_deliver - 1:
            await self._dlq(msg, reason)
            try:
                await msg.ack()
            except Exception:  # noqa: BLE001
                pass
        else:
            try:
                await msg.nak()
            except Exception as e:  # noqa: BLE001
                logger.warning("spans_consumer: nak failed: %s", e)

    async def _extract_resource(self, rs: Any) -> Any:
        attrs = _logs_consumer._kvs_to_dict(rs.resource.attributes) if rs.HasField("resource") else {}
        service_name = str(attrs.pop("service.name", "unknown") or "unknown")
        service_instance_id = attrs.pop("service.instance.id", None)
        service_version = attrs.pop("service.version", None)
        return _types.ResourceRecord(
            org_id=self._org_id,
            service_name=service_name,
            service_instance_id=str(service_instance_id) if service_instance_id is not None else None,
            service_version=str(service_version) if service_version is not None else None,
            attributes=attrs,
        )

    async def _process_batch(self, msgs: list[Any]) -> None:
        parsed: list[tuple[Any, list[Any]]] = []
        skipped: list[tuple[Any, str]] = []
        async with self._pool.acquire() as conn:
            for msg in msgs:
                try:
                    rs = ResourceSpans()
                    rs.ParseFromString(msg.data)
                    resource_rec = await self._extract_resource(rs)
                    resource_id = await self._resources_store.upsert(conn, resource_rec)
                    parsed.append((msg, _build_span_records(rs, resource_id, self._org_id)))
                except Exception as e:  # noqa: BLE001
                    skipped.append((msg, f"decode_error: {e}"))

            all_records = [r for _, recs in parsed for r in recs]
            try:
                if all_records:
                    async with conn.transaction():
                        await self._spans_store.insert_batch(conn, all_records)
            except Exception as e:  # noqa: BLE001
                logger.warning("spans_consumer: insert_batch failed, will nack batch: %s", e)
                for msg, _ in parsed:
                    await self._handle_failure(msg, f"insert_error: {e}")
                for msg, reason in skipped:
                    await self._handle_failure(msg, reason)
                return

        for msg, _ in parsed:
            try:
                await msg.ack()
            except Exception as e:  # noqa: BLE001
                logger.warning("spans_consumer: ack failed: %s", e)
        for msg, reason in skipped:
            await self._dlq(msg, reason)
            try:
                await msg.ack()
            except Exception:  # noqa: BLE001
                pass

    async def run_once(self) -> int:
        await self._ensure_subscription()
        batch_size = int(getattr(self._config, "monitoring_consumer_batch_size", 200))
        try:
            msgs = await self._sub.fetch(batch=batch_size, timeout=1.0)
        except asyncio.TimeoutError:
            return 0
        except Exception as e:  # noqa: BLE001
            if "timeout" in str(e).lower():
                return 0
            logger.warning("spans_consumer: fetch error: %s", e)
            return 0
        if not msgs:
            return 0
        await self._process_batch(msgs)
        self.heartbeat_at = datetime.now(timezone.utc).replace(tzinfo=None)
        return len(msgs)

    async def start(self) -> None:
        while not self._stop.is_set():
            try:
                await self.run_once()
            except asyncio.CancelledError:
                raise
            except Exception as e:  # noqa: BLE001
                logger.exception("spans_consumer: unexpected error: %s", e)
                raise

    async def stop(self) -> None:
        self._stop.set()
        if self._sub is not None:
            try:
                await self._sub.unsubscribe()
            except Exception:  # noqa: BLE001
                pass


__all__ = ["SpansConsumer"]
