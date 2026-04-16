"""Lifecycle event helper for sandbox entities."""
from __future__ import annotations

import uuid
from importlib import import_module

_time_module = import_module("backend.01_core.time_utils")
utc_now_sql = _time_module.utc_now_sql

SCHEMA = '"15_sandbox"'


async def write_lifecycle_event(
    connection,
    *,
    tenant_key: str,
    org_id: str,
    entity_type: str,
    entity_id: str,
    event_type: str,
    actor_id: str,
    old_value: str | None = None,
    new_value: str | None = None,
    comment: str | None = None,
    properties: dict[str, str] | None = None,
) -> None:
    """Write an immutable lifecycle event to 31_trx_entity_lifecycle_events."""
    event_id = str(uuid.uuid4())
    now = utc_now_sql()
    await connection.execute(
        f'''INSERT INTO {SCHEMA}."31_trx_entity_lifecycle_events"
            (id, tenant_key, org_id, entity_type, entity_id, event_type,
             old_value, new_value, actor_id, comment, occurred_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)''',
        event_id, tenant_key, org_id, entity_type, entity_id, event_type,
        old_value, new_value, actor_id, comment, now,
    )
    if properties:
        for key, value in properties.items():
            await connection.execute(
                f'''INSERT INTO {SCHEMA}."32_dtl_lifecycle_event_properties"
                    (event_id, meta_key, meta_value, created_at)
                    VALUES ($1, $2, $3, $4)''',
                event_id, key, value, now,
            )
