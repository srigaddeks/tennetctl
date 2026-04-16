from __future__ import annotations

import asyncpg
from importlib import import_module

from .models import ReviewEventRecord

SCHEMA = '"14_risk_registry"'
instrument_class_methods = import_module("backend.01_core.telemetry").instrument_class_methods


@instrument_class_methods(namespace="risk.review_events.repository", logger_name="backend.risk.review_events.repository.instrumentation")
class ReviewEventRepository:
    async def list_review_events(
        self, connection: asyncpg.Connection, risk_id: str
    ) -> list[ReviewEventRecord]:
        rows = await connection.fetch(
            f"""
            SELECT id::text, risk_id::text, event_type,
                   old_status, new_status, actor_id::text,
                   comment, occurred_at::text
            FROM {SCHEMA}."33_trx_risk_review_events"
            WHERE risk_id = $1::uuid
            ORDER BY occurred_at DESC
            """,
            risk_id,
        )
        return [_row_to_event(r) for r in rows]

    async def create_review_event(
        self,
        connection: asyncpg.Connection,
        *,
        event_id: str,
        risk_id: str,
        event_type: str,
        old_status: str | None,
        new_status: str | None,
        actor_id: str,
        comment: str | None,
        now: datetime,
    ) -> ReviewEventRecord:
        row = await connection.fetchrow(
            f"""
            INSERT INTO {SCHEMA}."33_trx_risk_review_events" (
                id, risk_id, event_type, old_status, new_status,
                actor_id, comment, occurred_at
            )
            VALUES ($1::uuid, $2::uuid, $3, $4, $5, $6::uuid, $7, $8)
            RETURNING id::text, risk_id::text, event_type,
                      old_status, new_status, actor_id::text,
                      comment, occurred_at::text
            """,
            event_id,
            risk_id,
            event_type,
            old_status,
            new_status,
            actor_id,
            comment,
            now,
        )
        return _row_to_event(row)


def _row_to_event(r) -> ReviewEventRecord:
    return ReviewEventRecord(
        id=r["id"],
        risk_id=r["risk_id"],
        event_type=r["event_type"],
        old_status=r["old_status"],
        new_status=r["new_status"],
        actor_id=r["actor_id"],
        comment=r["comment"],
        occurred_at=r["occurred_at"],
    )
