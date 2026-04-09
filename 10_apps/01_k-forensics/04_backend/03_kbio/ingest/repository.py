"""kbio ingest repository.

Write-path DB operations for score events, session records, and
profile updates. All writes are called from background tasks
(non-blocking to the ingest response).
"""

from __future__ import annotations

import uuid
from typing import Any

import asyncpg


async def insert_score_event(
    conn: asyncpg.Connection,
    *,
    session_id: str,
    user_hash: str,
    batch_id: str,
    batch_type_id: int,
    drift_action_id: int,
    metadata: dict[str, Any],
    actor_id: str,
) -> str:
    """Insert a score event into 60_evt_score_events."""
    event_id = str(uuid.uuid4())
    await conn.execute(
        """
        INSERT INTO "10_kbio"."60_evt_score_events"
            (id, session_id, user_hash, batch_id, batch_type_id, drift_action_id, metadata, created_by)
        VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb, $8)
        ON CONFLICT (batch_id) DO NOTHING
        """,
        event_id, session_id, user_hash, batch_id,
        batch_type_id, drift_action_id, metadata, actor_id,
    )
    return event_id


async def upsert_session(
    conn: asyncpg.Connection,
    *,
    session_id: str,
    sdk_session_id: str,
    user_hash: str,
    device_uuid: str,
    status_id: int = 1,
    trust_level_id: int = 1,
    baseline_quality_id: int = 1,
    actor_id: str,
) -> str:
    """Create or update a session record in 10_fct_sessions."""
    await conn.execute(
        """
        INSERT INTO "10_kbio"."10_fct_sessions"
            (id, sdk_session_id, user_hash, device_uuid, status_id,
             trust_level_id, baseline_quality_id, created_by, updated_by)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $8)
        ON CONFLICT (sdk_session_id) DO UPDATE SET
            status_id = EXCLUDED.status_id,
            trust_level_id = EXCLUDED.trust_level_id,
            baseline_quality_id = EXCLUDED.baseline_quality_id,
            updated_by = EXCLUDED.updated_by,
            updated_at = CURRENT_TIMESTAMP
        """,
        session_id, sdk_session_id, user_hash, device_uuid,
        status_id, trust_level_id, baseline_quality_id, actor_id,
    )
    return session_id


async def insert_bot_detection_event(
    conn: asyncpg.Connection,
    *,
    session_id: str,
    user_hash: str,
    batch_id: str,
    metadata: dict[str, Any],
    actor_id: str,
) -> str:
    """Insert a bot detection event."""
    event_id = str(uuid.uuid4())
    await conn.execute(
        """
        INSERT INTO "10_kbio"."62_evt_bot_detection_events"
            (id, session_id, user_hash, batch_id, metadata, created_by)
        VALUES ($1, $2, $3, $4, $5::jsonb, $6)
        ON CONFLICT (batch_id) DO NOTHING
        """,
        event_id, session_id, user_hash, batch_id, metadata, actor_id,
    )
    return event_id


async def insert_anomaly_event(
    conn: asyncpg.Connection,
    *,
    session_id: str,
    user_hash: str,
    severity_id: int,
    metadata: dict[str, Any],
    actor_id: str,
) -> str:
    """Insert an anomaly event."""
    event_id = str(uuid.uuid4())
    await conn.execute(
        """
        INSERT INTO "10_kbio"."61_evt_anomaly_events"
            (id, session_id, user_hash, severity_id, metadata, created_by)
        VALUES ($1, $2, $3, $4, $5::jsonb, $6)
        """,
        event_id, session_id, user_hash, severity_id, metadata, actor_id,
    )
    return event_id


async def get_session_by_sdk_id(
    conn: asyncpg.Connection,
    sdk_session_id: str,
) -> dict[str, Any] | None:
    """Look up a session by SDK session ID."""
    row = await conn.fetchrow(
        'SELECT * FROM "10_kbio".v_sessions WHERE sdk_session_id = $1',
        sdk_session_id,
    )
    return dict(row) if row else None


async def get_user_profile(
    conn: asyncpg.Connection,
    user_hash: str,
) -> dict[str, Any] | None:
    """Look up a user profile by user_hash."""
    row = await conn.fetchrow(
        'SELECT * FROM "10_kbio".v_user_profiles WHERE user_hash = $1',
        user_hash,
    )
    return dict(row) if row else None
