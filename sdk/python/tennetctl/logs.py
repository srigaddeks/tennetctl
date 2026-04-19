from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ._transport import Transport


class Logs:
    """Log emission (OTLP) + query + tail.

    Emission uses OTLP JSON format over HTTP to /v1/monitoring/otlp/v1/logs.
    Query + tail return records from the configured logs store.
    """

    def __init__(self, transport: Transport) -> None:
        self._t = transport

    async def emit(
        self,
        *,
        severity: str,
        body: str,
        attributes: dict[str, Any] | None = None,
        service_name: str | None = None,
        trace_id: str | None = None,
        span_id: str | None = None,
    ) -> dict:
        """Emit a single log record via OTLP JSON."""
        resource_attrs: dict[str, Any] = {}
        if service_name:
            resource_attrs["service.name"] = service_name

        log_record: dict[str, Any] = {
            "severityText": severity,
            "body": {"stringValue": body},
        }
        if attributes:
            log_record["attributes"] = [
                {"key": k, "value": _otlp_value(v)} for k, v in attributes.items()
            ]
        if trace_id:
            log_record["traceId"] = trace_id
        if span_id:
            log_record["spanId"] = span_id

        payload: dict[str, Any] = {
            "resourceLogs": [
                {
                    "resource": {
                        "attributes": [
                            {"key": k, "value": _otlp_value(v)}
                            for k, v in resource_attrs.items()
                        ]
                    },
                    "scopeLogs": [{"logRecords": [log_record]}],
                }
            ]
        }
        return await self._t.request(
            "POST", "/v1/monitoring/otlp/v1/logs", json=payload
        )

    async def emit_batch(self, records: list[dict]) -> dict:
        """Emit pre-built OTLP logs payload. Caller is responsible for
        constructing the OTLP `resourceLogs` envelope correctly."""
        return await self._t.request(
            "POST", "/v1/monitoring/otlp/v1/logs", json={"resourceLogs": records}
        )

    async def query(self, body: dict) -> dict:
        return await self._t.request("POST", "/v1/monitoring/logs/query", json=body)

    async def tail(self, **filters: Any) -> dict:
        params = {k: v for k, v in filters.items() if v is not None}
        return await self._t.request(
            "GET", "/v1/monitoring/logs/tail", params=params or None
        )


def _otlp_value(v: Any) -> dict:
    if isinstance(v, bool):
        return {"boolValue": v}
    if isinstance(v, int):
        return {"intValue": str(v)}
    if isinstance(v, float):
        return {"doubleValue": v}
    return {"stringValue": str(v)}
