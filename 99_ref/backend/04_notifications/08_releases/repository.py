from __future__ import annotations

import asyncpg
from importlib import import_module

from ..models import ReleaseRecord, IncidentRecord, IncidentUpdateRecord

SCHEMA = '"03_notifications"'
instrument_class_methods = import_module("backend.01_core.telemetry").instrument_class_methods

_RELEASE_COLS = """id, tenant_key, version, title, summary,
                   body_markdown, body_html, changelog_url, status,
                   release_date::text, published_at::text, broadcast_id,
                   is_active, is_deleted,
                   created_at::text, updated_at::text, created_by"""

_INCIDENT_COLS = """id, tenant_key, title, description, severity, status,
                    affected_components, started_at::text, resolved_at::text,
                    broadcast_id, is_active, is_deleted,
                    created_at::text, updated_at::text, created_by"""

_INCIDENT_UPDATE_COLS = """id, incident_id, status, message, is_public,
                           broadcast_id, created_at::text, created_by"""


@instrument_class_methods(namespace="releases.repository", logger_name="backend.notifications.releases.repository.instrumentation")
class ReleaseRepository:

    # ------------------------------------------------------------------ #
    # Releases
    # ------------------------------------------------------------------ #

    async def list_releases(
        self, connection: asyncpg.Connection, tenant_key: str,
        *, limit: int = 50, offset: int = 0, status: str | None = None,
    ) -> tuple[list[ReleaseRecord], int]:
        where = "WHERE tenant_key = $1 AND is_deleted = FALSE"
        params: list = [tenant_key]
        if status:
            where += " AND status = $2"
            params.append(status)

        total = await connection.fetchval(
            f'SELECT COUNT(*) FROM {SCHEMA}."25_fct_releases" {where}', *params
        )
        rows = await connection.fetch(
            f"""
            SELECT {_RELEASE_COLS}
            FROM {SCHEMA}."25_fct_releases"
            {where}
            ORDER BY created_at DESC
            LIMIT {limit} OFFSET {offset}
            """,
            *params,
        )
        return [_row_to_release(r) for r in rows], total

    async def get_release_by_id(
        self, connection: asyncpg.Connection, release_id: str
    ) -> ReleaseRecord | None:
        row = await connection.fetchrow(
            f"""
            SELECT {_RELEASE_COLS}
            FROM {SCHEMA}."25_fct_releases"
            WHERE id = $1 AND is_deleted = FALSE
            """,
            release_id,
        )
        return _row_to_release(row) if row else None

    async def create_release(
        self, connection: asyncpg.Connection, **kwargs
    ) -> ReleaseRecord:
        row = await connection.fetchrow(
            f"""
            INSERT INTO {SCHEMA}."25_fct_releases"
                (id, tenant_key, version, title, summary,
                 body_markdown, body_html, changelog_url, status,
                 release_date, published_at, broadcast_id,
                 is_active, is_deleted, created_at, updated_at, created_by)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 'draft',
                    $9, NULL, NULL, TRUE, FALSE, $10, $11, $12)
            RETURNING {_RELEASE_COLS}
            """,
            kwargs["release_id"],
            kwargs["tenant_key"],
            kwargs["version"],
            kwargs["title"],
            kwargs["summary"],
            kwargs["body_markdown"],
            kwargs["body_html"],
            kwargs["changelog_url"],
            kwargs["release_date"],
            kwargs["now"],
            kwargs["now"],
            kwargs["created_by"],
        )
        return _row_to_release(row)

    async def update_release(
        self, connection: asyncpg.Connection, release_id: str, **kwargs
    ) -> ReleaseRecord | None:
        sets = ["updated_at = $2"]
        params: list = [release_id, kwargs["now"]]
        idx = 3
        for field in ("title", "summary", "body_markdown", "body_html", "changelog_url", "release_date"):
            if field in kwargs and kwargs[field] is not None:
                sets.append(f"{field} = ${idx}")
                params.append(kwargs[field])
                idx += 1

        row = await connection.fetchrow(
            f"""
            UPDATE {SCHEMA}."25_fct_releases"
            SET {', '.join(sets)}
            WHERE id = $1 AND is_deleted = FALSE
            RETURNING {_RELEASE_COLS}
            """,
            *params,
        )
        return _row_to_release(row) if row else None

    async def publish_release(
        self, connection: asyncpg.Connection, release_id: str, broadcast_id: str | None, now
    ) -> ReleaseRecord | None:
        row = await connection.fetchrow(
            f"""
            UPDATE {SCHEMA}."25_fct_releases"
            SET status = 'published', published_at = $2, broadcast_id = $3, updated_at = $4
            WHERE id = $1 AND is_deleted = FALSE AND status = 'draft'
            RETURNING {_RELEASE_COLS}
            """,
            release_id, now, broadcast_id, now,
        )
        return _row_to_release(row) if row else None

    async def archive_release(
        self, connection: asyncpg.Connection, release_id: str, now
    ) -> ReleaseRecord | None:
        row = await connection.fetchrow(
            f"""
            UPDATE {SCHEMA}."25_fct_releases"
            SET status = 'archived', updated_at = $2
            WHERE id = $1 AND is_deleted = FALSE
            RETURNING {_RELEASE_COLS}
            """,
            release_id, now,
        )
        return _row_to_release(row) if row else None

    # ------------------------------------------------------------------ #
    # Incidents
    # ------------------------------------------------------------------ #

    async def list_incidents(
        self, connection: asyncpg.Connection, tenant_key: str,
        *, limit: int = 50, offset: int = 0, status: str | None = None,
    ) -> tuple[list[IncidentRecord], int]:
        where = "WHERE tenant_key = $1 AND is_deleted = FALSE"
        params: list = [tenant_key]
        if status:
            where += " AND status = $2"
            params.append(status)

        total = await connection.fetchval(
            f'SELECT COUNT(*) FROM {SCHEMA}."26_fct_incidents" {where}', *params
        )
        rows = await connection.fetch(
            f"""
            SELECT {_INCIDENT_COLS}
            FROM {SCHEMA}."26_fct_incidents"
            {where}
            ORDER BY created_at DESC
            LIMIT {limit} OFFSET {offset}
            """,
            *params,
        )
        return [_row_to_incident(r) for r in rows], total

    async def list_active_incidents(
        self, connection: asyncpg.Connection, tenant_key: str,
        *, limit: int = 50, offset: int = 0,
    ) -> tuple[list[IncidentRecord], int]:
        """Return incidents that are not yet resolved (investigating/identified/monitoring)."""
        where = """WHERE tenant_key = $1 AND is_deleted = FALSE
                     AND status != 'resolved'"""
        total = await connection.fetchval(
            f'SELECT COUNT(*) FROM {SCHEMA}."26_fct_incidents" {where}', tenant_key
        )
        rows = await connection.fetch(
            f"""
            SELECT {_INCIDENT_COLS}
            FROM {SCHEMA}."26_fct_incidents"
            {where}
            ORDER BY created_at DESC
            LIMIT {limit} OFFSET {offset}
            """,
            tenant_key,
        )
        return [_row_to_incident(r) for r in rows], total

    async def get_incident_by_id(
        self, connection: asyncpg.Connection, incident_id: str
    ) -> IncidentRecord | None:
        row = await connection.fetchrow(
            f"""
            SELECT {_INCIDENT_COLS}
            FROM {SCHEMA}."26_fct_incidents"
            WHERE id = $1 AND is_deleted = FALSE
            """,
            incident_id,
        )
        return _row_to_incident(row) if row else None

    async def create_incident(
        self, connection: asyncpg.Connection, **kwargs
    ) -> IncidentRecord:
        row = await connection.fetchrow(
            f"""
            INSERT INTO {SCHEMA}."26_fct_incidents"
                (id, tenant_key, title, description, severity, status,
                 affected_components, started_at, resolved_at,
                 broadcast_id, is_active, is_deleted,
                 created_at, updated_at, created_by)
            VALUES ($1, $2, $3, $4, $5, 'investigating', $6, $7, NULL,
                    $8, TRUE, FALSE, $9, $10, $11)
            RETURNING {_INCIDENT_COLS}
            """,
            kwargs["incident_id"],
            kwargs["tenant_key"],
            kwargs["title"],
            kwargs["description"],
            kwargs["severity"],
            kwargs["affected_components"],
            kwargs["started_at"],
            kwargs["broadcast_id"],
            kwargs["now"],
            kwargs["now"],
            kwargs["created_by"],
        )
        return _row_to_incident(row)

    async def update_incident(
        self, connection: asyncpg.Connection, incident_id: str, **kwargs
    ) -> IncidentRecord | None:
        sets = ["updated_at = $2"]
        params: list = [incident_id, kwargs["now"]]
        idx = 3
        for field in ("title", "description", "severity", "affected_components", "status", "resolved_at"):
            if field in kwargs and kwargs[field] is not None:
                sets.append(f"{field} = ${idx}")
                params.append(kwargs[field])
                idx += 1

        row = await connection.fetchrow(
            f"""
            UPDATE {SCHEMA}."26_fct_incidents"
            SET {', '.join(sets)}
            WHERE id = $1 AND is_deleted = FALSE
            RETURNING {_INCIDENT_COLS}
            """,
            *params,
        )
        return _row_to_incident(row) if row else None

    # ------------------------------------------------------------------ #
    # Incident Updates
    # ------------------------------------------------------------------ #

    async def list_incident_updates(
        self, connection: asyncpg.Connection, incident_id: str
    ) -> list[IncidentUpdateRecord]:
        rows = await connection.fetch(
            f"""
            SELECT {_INCIDENT_UPDATE_COLS}
            FROM {SCHEMA}."27_dtl_incident_updates"
            WHERE incident_id = $1
            ORDER BY created_at ASC
            """,
            incident_id,
        )
        return [_row_to_incident_update(r) for r in rows]

    async def create_incident_update(
        self, connection: asyncpg.Connection, **kwargs
    ) -> IncidentUpdateRecord:
        row = await connection.fetchrow(
            f"""
            INSERT INTO {SCHEMA}."27_dtl_incident_updates"
                (id, incident_id, status, message, is_public,
                 broadcast_id, created_at, created_by)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING {_INCIDENT_UPDATE_COLS}
            """,
            kwargs["update_id"],
            kwargs["incident_id"],
            kwargs["status"],
            kwargs["message"],
            kwargs["is_public"],
            kwargs["broadcast_id"],
            kwargs["now"],
            kwargs["created_by"],
        )
        return _row_to_incident_update(row)


def _row_to_release(r) -> ReleaseRecord:
    return ReleaseRecord(
        id=r["id"],
        tenant_key=r["tenant_key"],
        version=r["version"],
        title=r["title"],
        summary=r["summary"],
        body_markdown=r["body_markdown"],
        body_html=r["body_html"],
        changelog_url=r["changelog_url"],
        status=r["status"],
        release_date=r["release_date"],
        published_at=r["published_at"],
        broadcast_id=r["broadcast_id"],
        is_active=r["is_active"],
        is_deleted=r["is_deleted"],
        created_at=r["created_at"],
        updated_at=r["updated_at"],
        created_by=r["created_by"],
    )


def _row_to_incident(r) -> IncidentRecord:
    return IncidentRecord(
        id=r["id"],
        tenant_key=r["tenant_key"],
        title=r["title"],
        description=r["description"],
        severity=r["severity"],
        status=r["status"],
        affected_components=r["affected_components"],
        started_at=r["started_at"],
        resolved_at=r["resolved_at"],
        broadcast_id=r["broadcast_id"],
        is_active=r["is_active"],
        is_deleted=r["is_deleted"],
        created_at=r["created_at"],
        updated_at=r["updated_at"],
        created_by=r["created_by"],
    )


def _row_to_incident_update(r) -> IncidentUpdateRecord:
    return IncidentUpdateRecord(
        id=r["id"],
        incident_id=r["incident_id"],
        status=r["status"],
        message=r["message"],
        is_public=r["is_public"],
        broadcast_id=r["broadcast_id"],
        created_at=r["created_at"],
        created_by=r["created_by"],
    )
