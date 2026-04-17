"""JetStream → Postgres logs consumer.

Pull-subscribes to ``MONITORING_LOGS`` with durable ``monitoring-logs-postgres``.
Each JetStream message carries exactly one serialized ResourceLogs protobuf
(see sub_features/01_logs/otlp_decoder.py).

Flow per batch:
1. fetch(batch=N, timeout=1s)
2. For each msg: decode ResourceLogs, upsert resource, extract LogRecords,
   apply redaction, collect into LogsStore.insert_batch payload.
3. Single DB transaction per batch. ack all on success.
4. On insert failure: nack all (up to max_deliver-1 times); on the final
   delivery, publish original payload to monitoring.dlq.logs then ack.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from importlib import import_module
from typing import Any

from opentelemetry.proto.logs.v1.logs_pb2 import (  # pyright: ignore[reportMissingImports, reportMissingTypeStubs]
    ResourceLogs,
)

_core_id: Any = import_module("backend.01_core.id")
_stores: Any = import_module("backend.02_features.05_monitoring.stores")
_types: Any = import_module("backend.02_features.05_monitoring.stores.types")

logger = logging.getLogger("tennetctl.monitoring.logs_consumer")

_DURABLE = "monitoring-logs-postgres"
_SUBJECT_FILTER = "monitoring.logs.otel.>"
_DLQ_SUBJECT = "monitoring.dlq.logs"


def _any_value_to_py(v: Any) -> Any:
    """Convert OTel AnyValue proto to Python-native."""
    if v.HasField("string_value"):
        return v.string_value
    if v.HasField("bool_value"):
        return v.bool_value
    if v.HasField("int_value"):
        return int(v.int_value)
    if v.HasField("double_value"):
        return float(v.double_value)
    if v.HasField("array_value"):
        return [_any_value_to_py(x) for x in v.array_value.values]
    if v.HasField("kvlist_value"):
        return {kv.key: _any_value_to_py(kv.value) for kv in v.kvlist_value.values}
    if v.HasField("bytes_value"):
        return v.bytes_value.hex()
    return None


def _kvs_to_dict(kvs: Any) -> dict[str, Any]:
    return {kv.key: _any_value_to_py(kv.value) for kv in kvs}


def _extract_resource(rl: Any, org_id: str) -> Any:
    attrs = _kvs_to_dict(rl.resource.attributes) if rl.HasField("resource") else {}
    service_name = str(attrs.pop("service.name", "unknown") or "unknown")
    service_instance_id = attrs.pop("service.instance.id", None)
    service_version = attrs.pop("service.version", None)
    return _types.ResourceRecord(
        org_id=org_id,
        service_name=service_name,
        service_instance_id=str(service_instance_id) if service_instance_id is not None else None,
        service_version=str(service_version) if service_version is not None else None,
        attributes=attrs,
    )


def _body_to_str(body: Any) -> str:
    if body is None:
        return ""
    try:
        return str(_any_value_to_py(body) or "")
    except Exception:  # noqa: BLE001
        return ""


def _nanos_to_dt(nanos: int) -> datetime:
    if not nanos:
        return datetime.now(timezone.utc).replace(tzinfo=None)
    return datetime.fromtimestamp(nanos / 1_000_000_000, tz=timezone.utc).replace(tzinfo=None)


def _hex(bs: bytes) -> str | None:
    if not bs:
        return None
    return bs.hex()


def _build_log_records(
    rl: Any,
    resource_id: int,
    org_id: str,
    redaction: Any,
) -> list[Any]:
    records: list[Any] = []
    for scope_logs in rl.scope_logs:
        scope_name = scope_logs.scope.name if scope_logs.HasField("scope") else None
        scope_version = scope_logs.scope.version if scope_logs.HasField("scope") else None
        for lr in scope_logs.log_records:
            raw = {
                "id": _core_id.uuid7(),
                "org_id": org_id,
                "workspace_id": None,
                "resource_id": resource_id,
                "recorded_at": _nanos_to_dt(lr.time_unix_nano),
                "observed_at": _nanos_to_dt(lr.observed_time_unix_nano or lr.time_unix_nano),
                "severity_id": int(lr.severity_number) if lr.severity_number else 0,
                "severity_text": lr.severity_text or None,
                "body": _body_to_str(lr.body),
                "trace_id": _hex(lr.trace_id),
                "span_id": _hex(lr.span_id),
                "trace_flags": int(lr.flags) if lr.flags else None,
                "scope_name": scope_name or None,
                "scope_version": scope_version or None,
                "attributes": _kvs_to_dict(lr.attributes),
                "dropped_attributes_count": int(lr.dropped_attributes_count or 0),
            }
            result = redaction.apply(raw)
            r = result.record
            records.append(
                _types.LogRecord(
                    id=r["id"],
                    org_id=r["org_id"],
                    workspace_id=r["workspace_id"],
                    resource_id=r["resource_id"],
                    recorded_at=r["recorded_at"],
                    observed_at=r["observed_at"],
                    severity_id=r["severity_id"],
                    severity_text=r["severity_text"],
                    body=r["body"],
                    trace_id=r["trace_id"],
                    span_id=r["span_id"],
                    trace_flags=r["trace_flags"],
                    scope_name=r["scope_name"],
                    scope_version=r["scope_version"],
                    attributes=r["attributes"],
                    dropped_attributes_count=r["dropped_attributes_count"],
                )
            )
    return records


class LogsConsumer:
    """Pull-subscribe consumer draining MONITORING_LOGS into Postgres."""

    def __init__(
        self,
        pool: Any,
        js: Any,
        config: Any,
        redaction: Any,
        org_id: str = "tennetctl",
    ) -> None:
        self._pool = pool
        self._js = js
        self._config = config
        self._redaction = redaction
        self._org_id = org_id
        self._stop = asyncio.Event()
        self._sub: Any = None
        self._logs_store = _stores.get_logs_store(pool)
        self._resources_store = _stores.get_resources_store(pool)
        self.heartbeat_at: datetime | None = None

    async def _ensure_subscription(self) -> None:
        if self._sub is not None:
            return
        self._sub = await self._js.pull_subscribe(
            subject=_SUBJECT_FILTER,
            durable=_DURABLE,
            stream="MONITORING_LOGS",
        )

    async def _dlq(self, msg: Any, reason: str) -> None:
        try:
            headers = {"tennetctl-dlq-reason": reason[:200], "tennetctl-dlq-subject": getattr(msg, "subject", "")}
            await self._js.publish(_DLQ_SUBJECT, msg.data, headers=headers)
            logger.warning("logs_consumer: message routed to DLQ (%s)", reason)
        except Exception as e:  # noqa: BLE001
            logger.error("logs_consumer: DLQ publish failed: %s", e)

    async def _process_batch(self, msgs: list[Any]) -> None:
        # Decode + build records across the whole batch.
        parsed: list[tuple[Any, list[Any]]] = []  # (msg, records)
        skipped: list[tuple[Any, str]] = []
        async with self._pool.acquire() as conn:
            for msg in msgs:
                try:
                    rl = ResourceLogs()
                    rl.ParseFromString(msg.data)
                    resource_rec = _extract_resource(rl, self._org_id)
                    resource_id = await self._resources_store.upsert(conn, resource_rec)
                    records = _build_log_records(rl, resource_id, self._org_id, self._redaction)
                    parsed.append((msg, records))
                except Exception as e:  # noqa: BLE001
                    skipped.append((msg, f"decode_error: {e}"))

            # Batched insert.
            all_records = [r for _, recs in parsed for r in recs]
            try:
                if all_records:
                    async with conn.transaction():
                        await self._logs_store.insert_batch(conn, all_records)
            except Exception as e:  # noqa: BLE001
                logger.warning("logs_consumer: insert_batch failed, will nack batch: %s", e)
                # nack everything in parsed (skipped already bad)
                for msg, _ in parsed:
                    await self._handle_failure(msg, f"insert_error: {e}")
                for msg, reason in skipped:
                    await self._handle_failure(msg, reason)
                return

        # Success — ack all parsed; decode-failures go to DLQ immediately.
        for msg, _ in parsed:
            try:
                await msg.ack()
            except Exception as e:  # noqa: BLE001
                logger.warning("logs_consumer: ack failed: %s", e)
        for msg, reason in skipped:
            await self._dlq(msg, reason)
            try:
                await msg.ack()
            except Exception:  # noqa: BLE001
                pass

    async def _handle_failure(self, msg: Any, reason: str) -> None:
        """On insert failure: nack (redeliver) unless max_deliver exhausted."""
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
                logger.warning("logs_consumer: nak failed: %s", e)

    async def run_once(self) -> int:
        """Single fetch cycle. Returns number of messages processed."""
        await self._ensure_subscription()
        batch_size = int(getattr(self._config, "monitoring_consumer_batch_size", 200))
        try:
            msgs = await self._sub.fetch(batch=batch_size, timeout=1.0)
        except asyncio.TimeoutError:
            return 0
        except Exception as e:  # noqa: BLE001
            # nats-py raises its own TimeoutError; tolerate any fetch exception.
            if "timeout" in str(e).lower():
                return 0
            logger.warning("logs_consumer: fetch error: %s", e)
            return 0
        if not msgs:
            return 0
        await self._process_batch(msgs)
        self.heartbeat_at = datetime.now(timezone.utc).replace(tzinfo=None)
        return len(msgs)

    async def start(self) -> None:
        """Main loop — exits only on stop() or unhandled exception."""
        # Best-effort: load rules once. maybe_reload covers TTL refresh.
        try:
            await self._redaction.load(self._pool)
        except Exception as e:  # noqa: BLE001
            logger.warning("logs_consumer: initial redaction load failed: %s", e)
        while not self._stop.is_set():
            try:
                await self._redaction.maybe_reload(self._pool)
                await self.run_once()
            except asyncio.CancelledError:
                raise
            except Exception as e:  # noqa: BLE001
                logger.exception("logs_consumer: unexpected error: %s", e)
                raise

    async def stop(self) -> None:
        self._stop.set()
        if self._sub is not None:
            try:
                await self._sub.unsubscribe()
            except Exception:  # noqa: BLE001
                pass


__all__ = ["LogsConsumer"]
