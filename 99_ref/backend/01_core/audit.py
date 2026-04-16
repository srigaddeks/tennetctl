from __future__ import annotations

from dataclasses import dataclass, field
from importlib import import_module
import re
from uuid import UUID, uuid4

import asyncpg


_logging_module = import_module("backend.01_core.logging_utils")
_telemetry_module = import_module("backend.01_core.telemetry")

get_logger = _logging_module.get_logger
start_operation_span = _telemetry_module.start_operation_span

_IDENTIFIER_PATTERN = re.compile(r"^[a-z0-9_]+$")
_LOGGER = get_logger("backend.audit")


def _to_uuid(v: str | None) -> UUID | None:
    if v is None:
        return None
    try:
        return UUID(v) if not isinstance(v, UUID) else v
    except (ValueError, AttributeError):
        return None


@dataclass(frozen=True, slots=True)
class AuditEntry:
    id: str
    tenant_key: str
    entity_type: str
    entity_id: str
    event_type: str
    event_category: str
    occurred_at: object
    actor_id: str | None = None
    actor_type: str | None = None
    ip_address: str | None = None
    session_id: str | None = None
    properties: dict[str, str | None] = field(default_factory=dict)


class AuditWriter:
    def __init__(self, *, schema_name: str) -> None:
        if not _IDENTIFIER_PATTERN.fullmatch(schema_name):
            raise ValueError("Invalid schema name.")
        self._schema_name = schema_name
        self._events_table = f'"{schema_name}"."40_aud_events"'
        self._properties_table = f'"{schema_name}"."41_dtl_audit_event_properties"'

    async def write_entry(self, connection: asyncpg.Connection, entry: AuditEntry) -> None:
        with start_operation_span(
            "audit.write_entry",
            attributes={
                "audit.schema": self._schema_name,
                "audit.entity_type": entry.entity_type,
                "audit.event_type": entry.event_type,
                "audit.event_category": entry.event_category,
            },
        ):
            now = entry.occurred_at
            await connection.execute(
                f"""
                INSERT INTO {self._events_table} (
                    id, tenant_key, entity_type, entity_id, event_type,
                    event_category, actor_id, actor_type, ip_address,
                    session_id, occurred_at, created_at
                )
                VALUES (
                    $1, $2, $3, $4, $5,
                    $6, $7, $8, $9,
                    $10, $11, $12
                )
                """,
                _to_uuid(entry.id),
                entry.tenant_key,
                entry.entity_type,
                _to_uuid(entry.entity_id),
                entry.event_type,
                entry.event_category,
                _to_uuid(entry.actor_id),
                entry.actor_type,
                entry.ip_address,
                _to_uuid(entry.session_id),
                entry.occurred_at,
                now,
            )

            if entry.properties:
                rows = [
                    (uuid4(), _to_uuid(entry.id), key, value)
                    for key, value in entry.properties.items()
                ]
                await connection.executemany(
                    f"""
                    INSERT INTO {self._properties_table} (id, event_id, meta_key, meta_value)
                    VALUES ($1, $2, $3, $4)
                    """,
                    rows,
                )

            _LOGGER.info(
                "audit_entry_written",
                extra={
                    "action": "audit.write_entry",
                    "outcome": "success",
                    "audit_schema": self._schema_name,
                    "entity_type": entry.entity_type,
                    "entity_id": entry.entity_id,
                    "event_type": entry.event_type,
                    "event_category": entry.event_category,
                    "audit_entry_id": entry.id,
                    "property_count": len(entry.properties),
                },
            )
