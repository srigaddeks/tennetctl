from __future__ import annotations

import json

import asyncpg
from importlib import import_module

from .models import (
    SSFStreamRecord,
    SSFStreamSubjectRecord,
    SSFOutboxRecord,
    SSFDeliveryLogRecord,
)

SCHEMA = '"15_sandbox"'
instrument_class_methods = import_module("backend.01_core.telemetry").instrument_class_methods


@instrument_class_methods(namespace="sandbox.ssf_transmitter.repository", logger_name="backend.sandbox.ssf_transmitter.repository.instrumentation")
class SSFTransmitterRepository:

    # ── Streams ──────────────────────────────────────────────────────────

    async def create_stream(
        self,
        connection: asyncpg.Connection,
        *,
        id: str,
        tenant_key: str,
        org_id: str,
        stream_description: str | None,
        receiver_url: str | None,
        delivery_method: str,
        events_requested: list[str],
        authorization_header: str | None,
        created_by: str,
        now: object,
    ) -> str:
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."70_fct_ssf_streams"
                (id, tenant_key, org_id, stream_description, receiver_url,
                 delivery_method, events_requested, authorization_header,
                 events_delivered, stream_status, is_active,
                 created_at, updated_at, created_by, updated_by)
            VALUES
                ($1, $2, $3, $4, $5,
                 $6, $7, $8,
                 0, 'enabled', TRUE,
                 $9, $10, $11, $12)
            """,
            id,
            tenant_key,
            org_id,
            stream_description,
            receiver_url,
            delivery_method,
            json.dumps(events_requested),
            authorization_header,
            now,
            now,
            created_by,
            created_by,
        )
        return id

    async def list_streams(
        self,
        connection: asyncpg.Connection,
        org_id: str,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[SSFStreamRecord]:
        rows = await connection.fetch(
            f"""
            SELECT id, tenant_key, org_id, stream_description, receiver_url,
                   delivery_method, events_requested, events_delivered,
                   stream_status, is_active,
                   created_at::text, updated_at::text
            FROM {SCHEMA}."70_fct_ssf_streams"
            WHERE org_id = $1
            ORDER BY created_at DESC
            LIMIT {limit} OFFSET {offset}
            """,
            org_id,
        )
        return [_row_to_stream(r) for r in rows]

    async def count_streams(
        self,
        connection: asyncpg.Connection,
        org_id: str,
    ) -> int:
        row = await connection.fetchrow(
            f'SELECT COUNT(*)::int AS total FROM {SCHEMA}."70_fct_ssf_streams" WHERE org_id = $1',
            org_id,
        )
        return row["total"] if row else 0

    async def get_stream(
        self,
        connection: asyncpg.Connection,
        stream_id: str,
    ) -> SSFStreamRecord | None:
        row = await connection.fetchrow(
            f"""
            SELECT id, tenant_key, org_id, stream_description, receiver_url,
                   delivery_method, events_requested, events_delivered,
                   stream_status, is_active,
                   created_at::text, updated_at::text
            FROM {SCHEMA}."70_fct_ssf_streams"
            WHERE id = $1
            """,
            stream_id,
        )
        return _row_to_stream(row) if row else None

    async def get_stream_authorization_header(
        self,
        connection: asyncpg.Connection,
        stream_id: str,
    ) -> str | None:
        row = await connection.fetchrow(
            f'SELECT authorization_header FROM {SCHEMA}."70_fct_ssf_streams" WHERE id = $1',
            stream_id,
        )
        return row["authorization_header"] if row else None

    async def update_stream(
        self,
        connection: asyncpg.Connection,
        stream_id: str,
        *,
        events_requested: list[str] | None = None,
        receiver_url: str | None = None,
        stream_description: str | None = None,
        updated_by: str,
        now: object,
    ) -> bool:
        fields: list[str] = ["updated_at = $1", "updated_by = $2"]
        values: list[object] = [now, updated_by]
        idx = 3

        if events_requested is not None:
            fields.append(f"events_requested = ${idx}")
            values.append(json.dumps(events_requested))
            idx += 1
        if receiver_url is not None:
            fields.append(f"receiver_url = ${idx}")
            values.append(receiver_url)
            idx += 1
        if stream_description is not None:
            fields.append(f"stream_description = ${idx}")
            values.append(stream_description)
            idx += 1

        values.append(stream_id)
        set_clause = ", ".join(fields)

        result = await connection.execute(
            f"""
            UPDATE {SCHEMA}."70_fct_ssf_streams"
            SET {set_clause}
            WHERE id = ${idx}
            """,
            *values,
        )
        return result != "UPDATE 0"

    async def update_stream_status(
        self,
        connection: asyncpg.Connection,
        stream_id: str,
        status: str,
        *,
        updated_by: str,
        now: object,
    ) -> bool:
        is_active = status == "enabled"
        result = await connection.execute(
            f"""
            UPDATE {SCHEMA}."70_fct_ssf_streams"
            SET stream_status = $1, is_active = $2, updated_at = $3, updated_by = $4
            WHERE id = $5
            """,
            status,
            is_active,
            now,
            updated_by,
            stream_id,
        )
        return result != "UPDATE 0"

    async def delete_stream(
        self,
        connection: asyncpg.Connection,
        stream_id: str,
    ) -> bool:
        result = await connection.execute(
            f'DELETE FROM {SCHEMA}."70_fct_ssf_streams" WHERE id = $1',
            stream_id,
        )
        return result != "DELETE 0"

    async def increment_events_delivered(
        self,
        connection: asyncpg.Connection,
        stream_id: str,
    ) -> None:
        await connection.execute(
            f"""
            UPDATE {SCHEMA}."70_fct_ssf_streams"
            SET events_delivered = events_delivered + 1
            WHERE id = $1
            """,
            stream_id,
        )

    async def find_active_streams_for_event(
        self,
        connection: asyncpg.Connection,
        org_id: str,
        event_uri: str,
    ) -> list[SSFStreamRecord]:
        rows = await connection.fetch(
            f"""
            SELECT id, tenant_key, org_id, stream_description, receiver_url,
                   delivery_method, events_requested, events_delivered,
                   stream_status, is_active,
                   created_at::text, updated_at::text
            FROM {SCHEMA}."70_fct_ssf_streams"
            WHERE org_id = $1
              AND is_active = TRUE
              AND stream_status = 'enabled'
              AND events_requested::jsonb ? $2
            """,
            org_id,
            event_uri,
        )
        return [_row_to_stream(r) for r in rows]

    # ── Subjects ─────────────────────────────────────────────────────────

    async def add_subject(
        self,
        connection: asyncpg.Connection,
        *,
        id: str,
        stream_id: str,
        subject_type: str,
        subject_format: str,
        subject_id_data: dict,
        created_by: str,
        now: object,
    ) -> str:
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."71_dtl_ssf_stream_subjects"
                (id, stream_id, subject_type, subject_format, subject_id_data,
                 created_at, created_by)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
            id,
            stream_id,
            subject_type,
            subject_format,
            json.dumps(subject_id_data),
            now,
            created_by,
        )
        return id

    async def remove_subject(
        self,
        connection: asyncpg.Connection,
        stream_id: str,
        subject_id: str,
    ) -> bool:
        result = await connection.execute(
            f'DELETE FROM {SCHEMA}."71_dtl_ssf_stream_subjects" WHERE id = $1 AND stream_id = $2',
            subject_id,
            stream_id,
        )
        return result != "DELETE 0"

    async def list_subjects(
        self,
        connection: asyncpg.Connection,
        stream_id: str,
    ) -> list[SSFStreamSubjectRecord]:
        rows = await connection.fetch(
            f"""
            SELECT id, stream_id, subject_type, subject_format, subject_id_data,
                   created_at::text
            FROM {SCHEMA}."71_dtl_ssf_stream_subjects"
            WHERE stream_id = $1
            ORDER BY created_at ASC
            """,
            stream_id,
        )
        return [_row_to_subject(r) for r in rows]

    # ── Outbox (poll delivery) ───────────────────────────────────────────

    async def enqueue_set(
        self,
        connection: asyncpg.Connection,
        *,
        id: str,
        stream_id: str,
        set_jwt: str,
        jti: str,
        now: object,
    ) -> str:
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."72_trx_ssf_outbox"
                (id, stream_id, set_jwt, jti, acknowledged, created_at, acknowledged_at)
            VALUES ($1, $2, $3, $4, FALSE, $5, NULL)
            """,
            id,
            stream_id,
            set_jwt,
            jti,
            now,
        )
        return id

    async def poll_sets(
        self,
        connection: asyncpg.Connection,
        stream_id: str,
        *,
        limit: int = 25,
    ) -> list[SSFOutboxRecord]:
        rows = await connection.fetch(
            f"""
            SELECT id, stream_id, set_jwt, jti, acknowledged,
                   created_at::text, acknowledged_at::text
            FROM {SCHEMA}."72_trx_ssf_outbox"
            WHERE stream_id = $1 AND acknowledged = FALSE
            ORDER BY created_at ASC
            LIMIT {limit}
            """,
            stream_id,
        )
        return [_row_to_outbox(r) for r in rows]

    async def acknowledge_sets(
        self,
        connection: asyncpg.Connection,
        stream_id: str,
        jtis: list[str],
        *,
        now: object,
    ) -> int:
        if not jtis:
            return 0
        result = await connection.execute(
            f"""
            UPDATE {SCHEMA}."72_trx_ssf_outbox"
            SET acknowledged = TRUE, acknowledged_at = $1
            WHERE stream_id = $2 AND jti = ANY($3) AND acknowledged = FALSE
            """,
            now,
            stream_id,
            jtis,
        )
        # Parse "UPDATE N" to get count
        try:
            return int(result.split()[-1])
        except (ValueError, IndexError):
            return 0

    async def count_pending_sets(
        self,
        connection: asyncpg.Connection,
        stream_id: str,
    ) -> int:
        row = await connection.fetchrow(
            f"""
            SELECT COUNT(*)::int AS total
            FROM {SCHEMA}."72_trx_ssf_outbox"
            WHERE stream_id = $1 AND acknowledged = FALSE
            """,
            stream_id,
        )
        return row["total"] if row else 0

    # ── Delivery logs ────────────────────────────────────────────────────

    async def insert_delivery_log(
        self,
        connection: asyncpg.Connection,
        *,
        id: str,
        stream_id: str,
        jti: str,
        delivery_method: str,
        http_status: int | None,
        error_message: str | None,
        now: object,
    ) -> str:
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."73_trx_ssf_delivery_log"
                (id, stream_id, jti, delivery_method, http_status, error_message, delivered_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
            id,
            stream_id,
            jti,
            delivery_method,
            http_status,
            error_message,
            now,
        )
        return id


# ── Row mappers ──────────────────────────────────────────────────────────

def _row_to_stream(r) -> SSFStreamRecord:
    return SSFStreamRecord(
        id=r["id"],
        tenant_key=r["tenant_key"],
        org_id=r["org_id"],
        stream_description=r["stream_description"],
        receiver_url=r["receiver_url"],
        delivery_method=r["delivery_method"],
        events_requested=r["events_requested"],
        events_delivered=r["events_delivered"],
        stream_status=r["stream_status"],
        is_active=r["is_active"],
        created_at=r["created_at"],
        updated_at=r["updated_at"],
    )


def _row_to_subject(r) -> SSFStreamSubjectRecord:
    return SSFStreamSubjectRecord(
        id=r["id"],
        stream_id=r["stream_id"],
        subject_type=r["subject_type"],
        subject_format=r["subject_format"],
        subject_id_data=r["subject_id_data"],
        created_at=r["created_at"],
    )


def _row_to_outbox(r) -> SSFOutboxRecord:
    return SSFOutboxRecord(
        id=r["id"],
        stream_id=r["stream_id"],
        set_jwt=r["set_jwt"],
        jti=r["jti"],
        acknowledged=r["acknowledged"],
        created_at=r["created_at"],
        acknowledged_at=r["acknowledged_at"],
    )
