from __future__ import annotations

import asyncpg
from importlib import import_module

from .models import VersionRecord

SCHEMA = '"05_grc_library"'
instrument_class_methods = import_module(
    "backend.01_core.telemetry"
).instrument_class_methods


@instrument_class_methods(
    namespace="grc.versions.repository",
    logger_name="backend.grc.versions.repository.instrumentation",
)
class VersionRepository:
    async def list_versions(
        self, connection: asyncpg.Connection, *, framework_id: str
    ) -> list[VersionRecord]:
        rows = await connection.fetch(
            f"""
            SELECT v.id, v.framework_id, v.version_code, v.change_severity,
                   v.lifecycle_state, v.control_count, v.previous_version_id::text,
                   v.is_active, v.created_at::text, v.updated_at::text, v.created_by::text,
                   p_label.property_value AS version_label,
                   p_notes.property_value AS release_notes,
                   p_summary.property_value AS change_summary
            FROM {SCHEMA}."11_fct_framework_versions" v
            LEFT JOIN {SCHEMA}."21_dtl_version_properties" p_label
                ON p_label.framework_version_id = v.id AND p_label.property_key = 'version_label'
            LEFT JOIN {SCHEMA}."21_dtl_version_properties" p_notes
                ON p_notes.framework_version_id = v.id AND p_notes.property_key = 'release_notes'
            LEFT JOIN {SCHEMA}."21_dtl_version_properties" p_summary
                ON p_summary.framework_version_id = v.id AND p_summary.property_key = 'change_summary'
            WHERE v.framework_id = $1 AND v.is_deleted = FALSE
            ORDER BY v.created_at DESC
            """,
            framework_id,
        )
        return [_row_to_version(r) for r in rows]

    async def get_version_by_id(
        self, connection: asyncpg.Connection, version_id: str
    ) -> VersionRecord | None:
        row = await connection.fetchrow(
            f"""
            SELECT v.id, v.framework_id, v.version_code, v.change_severity,
                   v.lifecycle_state, v.control_count, v.previous_version_id::text,
                   v.is_active, v.created_at::text, v.updated_at::text, v.created_by::text,
                   p_label.property_value AS version_label,
                   p_notes.property_value AS release_notes,
                   p_summary.property_value AS change_summary
            FROM {SCHEMA}."11_fct_framework_versions" v
            LEFT JOIN {SCHEMA}."21_dtl_version_properties" p_label
                ON p_label.framework_version_id = v.id AND p_label.property_key = 'version_label'
            LEFT JOIN {SCHEMA}."21_dtl_version_properties" p_notes
                ON p_notes.framework_version_id = v.id AND p_notes.property_key = 'release_notes'
            LEFT JOIN {SCHEMA}."21_dtl_version_properties" p_summary
                ON p_summary.framework_version_id = v.id AND p_summary.property_key = 'change_summary'
            WHERE v.id = $1 AND v.is_deleted = FALSE
            """,
            version_id,
        )
        return _row_to_version(row) if row else None

    async def next_version_number(
        self, connection: asyncpg.Connection, *, framework_id: str
    ) -> str:
        """Return the next semantic version number for a framework.

        Version scheme: v0.1 -> v0.2 -> ... -> v0.9 -> v1.0 -> v1.1 -> v1.2...
        - First version starts at v0.1
        - Minor increments up to v0.9, then bumps to v1.0
        - Major increments when minor reaches 9

        Excludes soft-deleted versions to avoid conflicts with the unique constraint.
        """
        rows = await connection.fetch(
            f"""
            SELECT version_code FROM {SCHEMA}."11_fct_framework_versions"
            WHERE framework_id = $1 AND is_deleted = FALSE
            ORDER BY created_at DESC
            """,
            framework_id,
        )

        if not rows:
            return "v0.1"

        def parse_version(vcode: str) -> tuple[int, int]:
            if vcode.startswith("v") or vcode.startswith("V"):
                vcode = vcode[1:]
            if "." in vcode:
                parts = vcode.split(".")
                try:
                    return int(parts[0]), int(parts[1])
                except (ValueError, IndexError):
                    pass
            try:
                return 0, int(vcode)
            except ValueError:
                return 0, 0

        max_major = 0
        max_minor = 0
        for row in rows:
            major, minor = parse_version(row["version_code"])
            if major > max_major or (major == max_major and minor > max_minor):
                max_major = major
                max_minor = minor

        if max_minor >= 9:
            new_major = max_major + 1
            new_minor = 0
        else:
            new_major = max_major
            new_minor = max_minor + 1

        candidate = f"v{new_major}.{new_minor}"

        while True:
            exists = await connection.fetchval(
                f"""
                SELECT 1 FROM {SCHEMA}."11_fct_framework_versions"
                WHERE framework_id = $1 AND version_code = $2 AND is_deleted = FALSE
                LIMIT 1
                """,
                framework_id,
                candidate,
            )
            if not exists:
                return candidate
            if new_minor >= 9:
                new_major += 1
                new_minor = 0
            else:
                new_minor += 1
            candidate = f"v{new_major}.{new_minor}"

    async def create_version(
        self,
        connection: asyncpg.Connection,
        *,
        version_id: str,
        framework_id: str,
        version_code: str,
        change_severity: str,
        previous_version_id: str | None,
        created_by: str,
        now: object,
    ) -> VersionRecord:
        row = await connection.fetchrow(
            f"""
            INSERT INTO {SCHEMA}."11_fct_framework_versions"
                (id, framework_id, version_code, change_severity, lifecycle_state,
                 control_count, previous_version_id,
                 is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
                 created_at, updated_at, created_by, updated_by, deleted_at, deleted_by)
            VALUES
                ($1, $2, $3, $4, 'draft',
                 0, $5,
                 TRUE, FALSE, FALSE, FALSE, FALSE, FALSE,
                 $6, $7, $8, $9, NULL, NULL)
            RETURNING id, framework_id, version_code, change_severity,
                      lifecycle_state, control_count, previous_version_id::text,
                      is_active, created_at::text, updated_at::text, created_by::text
            """,
            version_id,
            framework_id,
            version_code,
            change_severity,
            previous_version_id,
            now,
            now,
            created_by,
            created_by,
        )
        return VersionRecord(
            id=row["id"],
            framework_id=row["framework_id"],
            version_code=row["version_code"],
            change_severity=row["change_severity"],
            lifecycle_state=row["lifecycle_state"],
            control_count=row["control_count"],
            previous_version_id=row["previous_version_id"],
            is_active=row["is_active"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            created_by=row["created_by"],
        )

    async def update_lifecycle_state(
        self,
        connection: asyncpg.Connection,
        version_id: str,
        *,
        lifecycle_state: str,
        updated_by: str,
        now: object,
    ) -> VersionRecord | None:
        # NOTE: Do NOT update control_count here — it is set explicitly by
        # update_version_control_count() to reflect the selective snapshot count.
        # Recounting all framework controls here would overwrite that value.
        row = await connection.fetchrow(
            f"""
            UPDATE {SCHEMA}."11_fct_framework_versions"
            SET lifecycle_state = $1, updated_at = $2, updated_by = $3
            WHERE id = $4 AND is_deleted = FALSE
            RETURNING id, framework_id, version_code, change_severity,
                      lifecycle_state, control_count, previous_version_id::text,
                      is_active, created_at::text, updated_at::text, created_by::text
            """,
            lifecycle_state,
            now,
            updated_by,
            version_id,
        )
        if row is None:
            return None
        return VersionRecord(
            id=row["id"],
            framework_id=row["framework_id"],
            version_code=row["version_code"],
            change_severity=row["change_severity"],
            lifecycle_state=row["lifecycle_state"],
            control_count=row["control_count"],
            previous_version_id=row["previous_version_id"],
            is_active=row["is_active"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            created_by=row["created_by"],
        )

    async def upsert_version_properties(
        self,
        connection: asyncpg.Connection,
        *,
        version_id: str,
        properties: dict[str, str],
        created_by: str,
        now: object,
    ) -> None:
        if not properties:
            return
        rows = [
            (version_id, key, value, now, now, created_by, created_by)
            for key, value in properties.items()
        ]
        await connection.executemany(
            f"""
                INSERT INTO {SCHEMA}."21_dtl_version_properties"
                    (id, framework_version_id, property_key, property_value, created_at, updated_at, created_by, updated_by)
                VALUES (gen_random_uuid(), $1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (framework_version_id, property_key) DO UPDATE
                SET property_value = EXCLUDED.property_value,
                    updated_at = EXCLUDED.updated_at,
                    updated_by = EXCLUDED.updated_by
                """,
            rows,
        )

    async def snapshot_controls_to_version(
        self,
        connection: asyncpg.Connection,
        *,
        framework_id: str,
        version_id: str,
        created_by: str,
        now: object,
        control_ids: list[str] | None = None,
    ) -> int:
        """Link controls to the version snapshot.

        If control_ids is provided, only those controls are snapshotted.
        Otherwise, all framework controls are snapshotted.
        """
        if control_ids:
            # Only snapshot specific controls
            result = await connection.execute(
                f"""
                INSERT INTO {SCHEMA}."31_lnk_framework_version_controls"
                    (id, framework_version_id, control_id, sort_order, created_at, created_by)
                SELECT gen_random_uuid(), $1, c.id, c.sort_order, $2, $3
                FROM {SCHEMA}."13_fct_controls" c
                WHERE c.framework_id = $4 AND c.is_deleted = FALSE AND c.id = ANY($5)
                ON CONFLICT (framework_version_id, control_id) DO NOTHING
                """,
                version_id,
                now,
                created_by,
                framework_id,
                control_ids,
            )
        else:
            # Snapshot all controls
            result = await connection.execute(
                f"""
                INSERT INTO {SCHEMA}."31_lnk_framework_version_controls"
                    (id, framework_version_id, control_id, sort_order, created_at, created_by)
                SELECT gen_random_uuid(), $1, c.id, c.sort_order, $2, $3
                FROM {SCHEMA}."13_fct_controls" c
                WHERE c.framework_id = $4 AND c.is_deleted = FALSE
                ON CONFLICT (framework_version_id, control_id) DO NOTHING
                """,
                version_id,
                now,
                created_by,
                framework_id,
            )
        # Parse "INSERT 0 N" to get count
        parts = result.split()
        return int(parts[-1]) if parts else 0

    async def has_draft_version(
        self, connection: asyncpg.Connection, *, framework_id: str
    ) -> VersionRecord | None:
        """Check if a framework has an existing draft version.

        Returns the draft version record if one exists, None otherwise.
        Used to prevent duplicate auto-versions from rapid successive changes.
        """
        row = await connection.fetchrow(
            f"""
            SELECT v.id, v.framework_id, v.version_code, v.change_severity,
                   v.lifecycle_state, v.control_count, v.previous_version_id::text,
                   v.is_active, v.created_at::text, v.updated_at::text, v.created_by::text,
                   p_label.property_value AS version_label,
                   p_notes.property_value AS release_notes,
                   p_summary.property_value AS change_summary
            FROM {SCHEMA}."11_fct_framework_versions" v
            LEFT JOIN {SCHEMA}."21_dtl_version_properties" p_label
                ON p_label.framework_version_id = v.id AND p_label.property_key = 'version_label'
            LEFT JOIN {SCHEMA}."21_dtl_version_properties" p_notes
                ON p_notes.framework_version_id = v.id AND p_notes.property_key = 'release_notes'
            LEFT JOIN {SCHEMA}."21_dtl_version_properties" p_summary
                ON p_summary.framework_version_id = v.id AND p_summary.property_key = 'change_summary'
            WHERE v.framework_id = $1
              AND v.lifecycle_state = 'draft'
              AND v.is_deleted = FALSE
            ORDER BY v.created_at DESC
            LIMIT 1
            """,
            framework_id,
        )
        return _row_to_version(row) if row else None

    async def update_version_control_count(
        self,
        connection: asyncpg.Connection,
        version_id: str,
        control_count: int,
    ) -> None:
        """Update the control_count for a version."""
        await connection.execute(
            f"""
            UPDATE {SCHEMA}."11_fct_framework_versions"
            SET control_count = $1
            WHERE id = $2 AND is_deleted = FALSE
            """,
            control_count,
            version_id,
        )


def _row_to_version(r) -> VersionRecord:
    return VersionRecord(
        id=r["id"],
        framework_id=r["framework_id"],
        version_code=r["version_code"],
        change_severity=r["change_severity"],
        lifecycle_state=r["lifecycle_state"],
        control_count=r["control_count"],
        previous_version_id=r["previous_version_id"],
        is_active=r["is_active"],
        created_at=r["created_at"],
        updated_at=r["updated_at"],
        created_by=r["created_by"],
        version_label=r.get("version_label"),
        release_notes=r.get("release_notes"),
        change_summary=r.get("change_summary"),
    )
