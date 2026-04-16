"""SQL repository for the attachments domain.

All SQL is fully parameterised — no f-string interpolation of user-supplied
values.  Table name constants and integer LIMIT/OFFSET values (which are
Python-controlled integers, never user strings) are the only f-string usage.
"""

from __future__ import annotations

import json
from importlib import import_module

import asyncpg

from .models import AttachmentRecord, DownloadRecord

SCHEMA = '"09_attachments"'
instrument_class_methods = import_module(
    "backend.01_core.telemetry"
).instrument_class_methods


@instrument_class_methods(
    namespace="attachments.repository",
    logger_name="backend.attachments.repository.instrumentation",
)
class AttachmentRepository:
    # ------------------------------------------------------------------
    # Reads
    # ------------------------------------------------------------------

    async def list_attachments(
        self,
        connection: asyncpg.Connection,
        *,
        tenant_key: str,
        entity_type: str | None = None,
        entity_id: str | None = None,
        engagement_id: str | None = None,
        auditor_only: bool = False,
        viewer_membership_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[AttachmentRecord], int]:
        filters = ["tenant_key = $1", "is_deleted = FALSE"]
        values: list[object] = [tenant_key]
        idx = 2

        if entity_type and entity_id:
            filters.append(f"entity_type = ${idx}")
            values.append(entity_type)
            idx += 1
            filters.append(f"entity_id = ${idx}::uuid")
            values.append(entity_id)
            idx += 1
        if engagement_id:
            # Complex filter for engagement-related items
            filters.append(
                f"""
                (
                    (entity_type = 'engagement' AND entity_id = ${idx}::uuid)
                    OR (entity_type = 'control' AND entity_id IN (
                         SELECT c.id FROM "05_grc_library"."13_fct_controls" c
                         JOIN "12_engagements"."10_fct_audit_engagements" eng ON eng.framework_id = c.framework_id
                         WHERE eng.id = ${idx}::uuid
                    ))
                    OR (entity_type = 'task' AND entity_id IN (
                         SELECT t.id FROM "08_tasks"."10_fct_tasks" t
                         LEFT JOIN "12_engagements"."10_fct_audit_engagements" eng ON (
                            (t.entity_type = 'engagement' AND t.entity_id = eng.id) OR
                            (t.entity_type = 'framework' AND t.entity_id = eng.framework_id) OR
                            (t.entity_type = 'control' AND t.entity_id IN (SELECT id FROM "05_grc_library"."13_fct_controls" WHERE framework_id = eng.framework_id))
                         )
                         WHERE eng.id = ${idx}::uuid
                    ))
                )
                """
            )
            values.append(engagement_id)
            idx += 1

        if auditor_only:
            filters.append(
                f"""
                EXISTS (
                    SELECT 1
                    FROM "12_engagements"."13_lnk_evidence_access_grants" g
                    WHERE g.attachment_id = {SCHEMA}."01_fct_attachments".id
                      AND g.membership_id = ${idx}::uuid
                      AND g.revoked_at IS NULL
                      AND g.is_active = TRUE
                      AND g.is_deleted = FALSE
                      AND (g.expires_at IS NULL OR g.expires_at > NOW())
                )
                """
            )
            values.append(viewer_membership_id)
            idx += 1

        where_clause = " AND ".join(filters)

        count_row = await connection.fetchrow(
            f'SELECT COUNT(*)::int AS total FROM {SCHEMA}."01_fct_attachments" WHERE {where_clause}',
            *values,
        )
        total = count_row["total"] if count_row else 0

        rows = await connection.fetch(
            f"""
            SELECT
                id::text, tenant_key, entity_type, entity_id::text,
                uploaded_by::text, original_filename,
                storage_key, storage_provider, storage_bucket, storage_url,
                content_type, file_size_bytes, checksum_sha256,
                is_deleted, deleted_at::text, deleted_by::text,
                virus_scan_status, virus_scan_at::text,
                description, auditor_access,
                published_for_audit_by::text, published_for_audit_at::text,
                created_at::text, updated_at::text
            FROM {SCHEMA}."01_fct_attachments"
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT {limit} OFFSET {offset}
            """,
            *values,
        )
        return [_row_to_attachment(r) for r in rows], total

    async def get_attachment_by_id(
        self,
        connection: asyncpg.Connection,
        attachment_id: str,
    ) -> AttachmentRecord | None:
        row = await connection.fetchrow(
            f"""
            SELECT
                id::text, tenant_key, entity_type, entity_id::text,
                uploaded_by::text, original_filename,
                storage_key, storage_provider, storage_bucket, storage_url,
                content_type, file_size_bytes, checksum_sha256,
                is_deleted, deleted_at::text, deleted_by::text,
                virus_scan_status, virus_scan_at::text,
                description, auditor_access,
                published_for_audit_by::text, published_for_audit_at::text,
                created_at::text, updated_at::text
            FROM {SCHEMA}."01_fct_attachments"
            WHERE id = $1::uuid AND is_deleted = FALSE
            """,
            attachment_id,
        )
        return _row_to_attachment(row) if row else None

    async def list_attachment_engagement_contexts(
        self,
        connection: asyncpg.Connection,
        attachment_id: str,
    ) -> list[dict[str, str]]:
        rows = await connection.fetch(
            f"""
            WITH attachment_context AS (
                SELECT entity_type, entity_id
                FROM {SCHEMA}."01_fct_attachments"
                WHERE id = $1::uuid
                  AND is_deleted = FALSE
            )
            SELECT DISTINCT engagement_id::text, tenant_key, org_id::text
            FROM (
                SELECT e.id AS engagement_id, e.tenant_key, e.org_id
                FROM attachment_context ac
                JOIN "12_engagements"."10_fct_audit_engagements" e
                  ON ac.entity_type = 'engagement'
                 AND e.id = ac.entity_id
                 AND e.is_deleted = FALSE

                UNION

                SELECT e.id AS engagement_id, e.tenant_key, e.org_id
                FROM attachment_context ac
                JOIN "12_engagements"."10_fct_audit_engagements" e
                  ON ac.entity_type = 'control'
                 AND e.is_deleted = FALSE
                JOIN "05_grc_library"."16_fct_framework_deployments" fd
                  ON fd.id = e.framework_deployment_id
                JOIN "05_grc_library"."31_lnk_framework_version_controls" lvc
                  ON lvc.framework_version_id = fd.deployed_version_id
                 AND lvc.control_id = ac.entity_id

                UNION

                SELECT e.id AS engagement_id, e.tenant_key, e.org_id
                FROM attachment_context ac
                JOIN "08_tasks"."10_fct_tasks" t
                  ON ac.entity_type = 'task'
                 AND t.id = ac.entity_id
                 AND t.is_deleted = FALSE
                JOIN "12_engagements"."10_fct_audit_engagements" e
                  ON e.is_deleted = FALSE
                 AND (
                        (t.entity_type = 'engagement' AND t.entity_id = e.id)
                     OR (t.entity_type = 'framework' AND t.entity_id = e.framework_id)
                     OR (
                            t.entity_type = 'control'
                        AND EXISTS (
                            SELECT 1
                            FROM "05_grc_library"."16_fct_framework_deployments" fd
                            JOIN "05_grc_library"."31_lnk_framework_version_controls" lvc
                              ON lvc.framework_version_id = fd.deployed_version_id
                            WHERE fd.id = e.framework_deployment_id
                              AND lvc.control_id = t.entity_id
                        )
                     )
                 )
            ) contexts
            """,
            attachment_id,
        )
        return [dict(r) for r in rows]

    async def has_active_evidence_grant(
        self,
        connection: asyncpg.Connection,
        *,
        engagement_id: str,
        membership_id: str,
        attachment_id: str,
    ) -> bool:
        return bool(
            await connection.fetchval(
                """
                SELECT 1
                FROM "12_engagements"."13_lnk_evidence_access_grants"
                WHERE engagement_id = $1::uuid
                  AND membership_id = $2::uuid
                  AND attachment_id = $3::uuid
                  AND revoked_at IS NULL
                  AND is_active = TRUE
                  AND is_deleted = FALSE
                  AND (expires_at IS NULL OR expires_at > NOW())
                LIMIT 1
                """,
                engagement_id,
                membership_id,
                attachment_id,
            )
        )

    async def has_active_creator_approved_evidence_grant(
        self,
        connection: asyncpg.Connection,
        *,
        engagement_id: str,
        membership_id: str,
        attachment_id: str,
    ) -> bool:
        return bool(
            await connection.fetchval(
                """
                SELECT 1
                FROM "12_engagements"."13_lnk_evidence_access_grants" g
                JOIN "12_engagements"."10_fct_audit_engagements" e
                  ON e.id = g.engagement_id
                WHERE g.engagement_id = $1::uuid
                  AND g.membership_id = $2::uuid
                  AND g.attachment_id = $3::uuid
                  AND g.created_by = e.created_by
                  AND g.revoked_at IS NULL
                  AND g.is_active = TRUE
                  AND g.is_deleted = FALSE
                  AND (g.expires_at IS NULL OR g.expires_at > NOW())
                LIMIT 1
                """,
                engagement_id,
                membership_id,
                attachment_id,
            )
        )

    async def get_attachment_including_deleted(
        self,
        connection: asyncpg.Connection,
        attachment_id: str,
    ) -> AttachmentRecord | None:
        row = await connection.fetchrow(
            f"""
            SELECT
                id::text, tenant_key, entity_type, entity_id::text,
                uploaded_by::text, original_filename,
                storage_key, storage_provider, storage_bucket, storage_url,
                content_type, file_size_bytes, checksum_sha256,
                is_deleted, deleted_at::text, deleted_by::text,
                virus_scan_status, virus_scan_at::text,
                description, auditor_access,
                published_for_audit_by::text, published_for_audit_at::text,
                created_at::text, updated_at::text
            FROM {SCHEMA}."01_fct_attachments"
            WHERE id = $1::uuid
            """,
            attachment_id,
        )
        return _row_to_attachment(row) if row else None

    async def get_attachment_counts_batch(
        self,
        connection: asyncpg.Connection,
        *,
        entity_type: str,
        entity_ids: list[str],
    ) -> dict[str, int]:
        """Return a mapping of entity_id → non-deleted attachment count."""
        if not entity_ids:
            return {}
        placeholders = ", ".join(f"${i + 2}::uuid" for i in range(len(entity_ids)))
        rows = await connection.fetch(
            f"""
            SELECT entity_id::text, COUNT(*)::int AS cnt
            FROM {SCHEMA}."01_fct_attachments"
            WHERE entity_type = $1
              AND entity_id IN ({placeholders})
              AND is_deleted = FALSE
            GROUP BY entity_id
            """,
            entity_type,
            *entity_ids,
        )
        counts = {r["entity_id"]: r["cnt"] for r in rows}
        for eid in entity_ids:
            counts.setdefault(eid, 0)
        return counts

    # ------------------------------------------------------------------
    # Storage quota
    # ------------------------------------------------------------------

    async def get_org_storage_usage(
        self,
        connection: asyncpg.Connection,
        tenant_key: str,
    ) -> dict:
        """Get current storage usage for a tenant."""
        row = await connection.fetchrow(
            f"""
            SELECT COALESCE(SUM(file_size_bytes), 0) AS total_bytes,
                   COUNT(*)::int AS total_files
            FROM {SCHEMA}."01_fct_attachments"
            WHERE tenant_key = $1 AND is_deleted = FALSE
            """,
            tenant_key,
        )
        return {"total_bytes": row["total_bytes"], "total_files": row["total_files"]}

    # ------------------------------------------------------------------
    # GDPR — user-level queries
    # ------------------------------------------------------------------

    async def list_attachments_by_user(
        self,
        connection: asyncpg.Connection,
        user_id: str,
        tenant_key: str,
    ) -> list[AttachmentRecord]:
        """List all non-deleted attachments uploaded by a specific user."""
        rows = await connection.fetch(
            f"""
            SELECT
                id::text, tenant_key, entity_type, entity_id::text,
                uploaded_by::text, original_filename,
                storage_key, storage_provider, storage_bucket, storage_url,
                content_type, file_size_bytes, checksum_sha256,
                is_deleted, deleted_at::text, deleted_by::text,
                virus_scan_status, virus_scan_at::text,
                description, auditor_access,
                published_for_audit_by::text, published_for_audit_at::text,
                created_at::text, updated_at::text
            FROM {SCHEMA}."01_fct_attachments"
            WHERE uploaded_by = $1::uuid AND tenant_key = $2
              AND is_deleted = FALSE
            ORDER BY created_at DESC
            """,
            user_id,
            tenant_key,
        )
        return [_row_to_attachment(r) for r in rows]

    async def soft_delete_user_attachments(
        self,
        connection: asyncpg.Connection,
        user_id: str,
        tenant_key: str,
        deleted_by: str,
        now: object,
    ) -> int:
        """Soft-delete all attachments uploaded by a user (GDPR)."""
        result = await connection.execute(
            f"""
            UPDATE {SCHEMA}."01_fct_attachments"
            SET is_deleted = TRUE, deleted_at = $3, deleted_by = $4::uuid, updated_at = $5
            WHERE uploaded_by = $1::uuid AND tenant_key = $2
              AND is_deleted = FALSE
            """,
            user_id,
            tenant_key,
            now,
            deleted_by,
            now,
        )
        return int(result.split()[-1])

    # ------------------------------------------------------------------
    # Writes
    # ------------------------------------------------------------------

    async def create_attachment(
        self,
        connection: asyncpg.Connection,
        *,
        attachment_id: str,
        tenant_key: str,
        entity_type: str,
        entity_id: str,
        uploaded_by: str,
        original_filename: str,
        storage_key: str,
        storage_provider: str,
        storage_bucket: str,
        storage_url: str | None,
        content_type: str,
        file_size_bytes: int,
        checksum_sha256: str,
        description: str | None,
        now: object,
    ) -> AttachmentRecord:
        row = await connection.fetchrow(
            f"""
            INSERT INTO {SCHEMA}."01_fct_attachments" (
                id, tenant_key, entity_type, entity_id,
                uploaded_by, original_filename,
                storage_key, storage_provider, storage_bucket, storage_url,
                content_type, file_size_bytes, checksum_sha256,
                is_deleted, virus_scan_status, description,
                created_at, updated_at
            )
            VALUES (
                $1::uuid, $2, $3, $4::uuid,
                $5::uuid, $6,
                $7, $8, $9, $10,
                $11, $12, $13,
                FALSE, 'pending', $14,
                $15, $16
            )
            RETURNING
                id::text, tenant_key, entity_type, entity_id::text,
                uploaded_by::text, original_filename,
                storage_key, storage_provider, storage_bucket, storage_url,
                content_type, file_size_bytes, checksum_sha256,
                is_deleted, deleted_at::text, deleted_by::text,
                virus_scan_status, virus_scan_at::text,
                description, auditor_access,
                published_for_audit_by::text, published_for_audit_at::text,
                created_at::text, updated_at::text
            """,
            attachment_id,
            tenant_key,
            entity_type,
            entity_id,
            uploaded_by,
            original_filename,
            storage_key,
            storage_provider,
            storage_bucket,
            storage_url,
            content_type,
            file_size_bytes,
            checksum_sha256,
            description,
            now,
            now,
        )
        return _row_to_attachment(row)

    async def update_description(
        self,
        connection: asyncpg.Connection,
        attachment_id: str,
        *,
        description: str | None,
        now: object,
    ) -> AttachmentRecord | None:
        """Update attachment description.

        Args:
            connection: Active asyncpg database connection.
            attachment_id: UUID of the attachment to update.
            description: New description text.
            now: Current timestamp.

        Returns:
            Updated AttachmentRecord or None if not found.
        """
        row = await connection.fetchrow(
            f"""
            UPDATE {SCHEMA}."01_fct_attachments"
            SET description = $1, updated_at = $2
            WHERE id = $3::uuid AND is_deleted = FALSE
            RETURNING
                id::text, tenant_key, entity_type, entity_id::text,
                uploaded_by::text, original_filename,
                storage_key, storage_provider, storage_bucket, storage_url,
                content_type, file_size_bytes, checksum_sha256,
                is_deleted, deleted_at::text, deleted_by::text,
                virus_scan_status, virus_scan_at::text,
                description, auditor_access,
                published_for_audit_by::text, published_for_audit_at::text,
                created_at::text, updated_at::text
            """,
            description,
            now,
            attachment_id,
        )
        return _row_to_attachment(row) if row else None

    async def set_auditor_access(
        self,
        connection: asyncpg.Connection,
        attachment_id: str,
        *,
        auditor_access: bool,
        actor_id: str,
        now: object,
    ) -> AttachmentRecord | None:
        """Set or clear auditor visibility on an attachment.

        Args:
            connection: Active asyncpg database connection.
            attachment_id: UUID of the attachment.
            auditor_access: True to make visible to auditors, False to hide.
            actor_id: UUID of the user making the change.
            now: Current timestamp.

        Returns:
            Updated AttachmentRecord or None if not found.
        """
        row = await connection.fetchrow(
            f"""
            UPDATE {SCHEMA}."01_fct_attachments"
            SET auditor_access = $1,
                published_for_audit_by = CASE WHEN $1 THEN $2::uuid ELSE NULL END,
                published_for_audit_at = CASE WHEN $1 THEN $3::timestamp ELSE NULL END,
                updated_at = $3::timestamp
            WHERE id = $4::uuid AND is_deleted = FALSE
            RETURNING
                id::text, tenant_key, entity_type, entity_id::text,
                uploaded_by::text, original_filename,
                storage_key, storage_provider, storage_bucket, storage_url,
                content_type, file_size_bytes, checksum_sha256,
                is_deleted, deleted_at::text, deleted_by::text,
                virus_scan_status, virus_scan_at::text,
                description, auditor_access,
                published_for_audit_by::text, published_for_audit_at::text,
                created_at::text, updated_at::text
            """,
            auditor_access,
            actor_id,
            now,
            attachment_id,
        )
        return _row_to_attachment(row) if row else None

    async def soft_delete_attachment(
        self,
        connection: asyncpg.Connection,
        attachment_id: str,
        *,
        deleted_by: str,
        now: object,
    ) -> bool:
        result = await connection.execute(
            f"""
            UPDATE {SCHEMA}."01_fct_attachments"
            SET is_deleted = TRUE, deleted_at = $1, deleted_by = $2::uuid, updated_at = $3
            WHERE id = $4::uuid AND is_deleted = FALSE
            """,
            now,
            deleted_by,
            now,
            attachment_id,
        )
        return result != "UPDATE 0"

    # ------------------------------------------------------------------
    # Download tracking
    # ------------------------------------------------------------------

    async def record_download(
        self,
        connection: asyncpg.Connection,
        *,
        download_id: str,
        attachment_id: str,
        downloaded_by: str,
        client_ip: str | None,
        user_agent: str | None,
        now: object,
    ) -> None:
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."02_trx_attachment_downloads" (
                id, attachment_id, downloaded_by, downloaded_at, client_ip, user_agent
            )
            VALUES (
                $1::uuid, $2::uuid, $3::uuid, $4, $5, $6
            )
            """,
            download_id,
            attachment_id,
            downloaded_by,
            now,
            client_ip,
            user_agent,
        )

    async def list_downloads(
        self,
        connection: asyncpg.Connection,
        attachment_id: str,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[DownloadRecord], int]:
        count_row = await connection.fetchrow(
            f"""
            SELECT COUNT(*)::int AS total
            FROM {SCHEMA}."02_trx_attachment_downloads"
            WHERE attachment_id = $1::uuid
            """,
            attachment_id,
        )
        total = count_row["total"] if count_row else 0

        rows = await connection.fetch(
            f"""
            SELECT
                id::text, attachment_id::text, downloaded_by::text,
                downloaded_at::text, client_ip, user_agent
            FROM {SCHEMA}."02_trx_attachment_downloads"
            WHERE attachment_id = $1::uuid
            ORDER BY downloaded_at DESC
            LIMIT {limit} OFFSET {offset}
            """,
            attachment_id,
        )
        return [_row_to_download(r) for r in rows], total

    # ------------------------------------------------------------------
    # Audit events
    # ------------------------------------------------------------------

    async def write_audit_event(
        self,
        connection: asyncpg.Connection,
        *,
        event_id: str,
        attachment_id: str | None,
        entity_type: str,
        entity_id: str,
        event_type: str,
        actor_user_id: str,
        tenant_key: str,
        metadata: dict,
        now: object,
    ) -> None:
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."03_aud_attachment_events" (
                id, attachment_id, entity_type, entity_id,
                event_type, actor_user_id, tenant_key, metadata, created_at
            )
            VALUES (
                $1::uuid,
                $2::uuid,
                $3, $4::uuid,
                $5, $6::uuid, $7, $8::jsonb, $9
            )
            """,
            event_id,
            attachment_id,
            entity_type,
            entity_id,
            event_type,
            actor_user_id,
            tenant_key,
            json.dumps(metadata),
            now,
        )

    # ------------------------------------------------------------------
    # User display name lookup
    # ------------------------------------------------------------------

    async def get_user_display_name(
        self, connection: asyncpg.Connection, user_id: str
    ) -> str | None:
        row = await connection.fetchrow(
            """
            SELECT property_value
            FROM "03_auth_manage"."05_dtl_user_properties"
            WHERE user_id = $1::uuid AND property_key = 'display_name'
            LIMIT 1
            """,
            user_id,
        )
        return row["property_value"] if row else None

    async def get_user_display_names_batch(
        self, connection: asyncpg.Connection, user_ids: list[str]
    ) -> dict[str, str]:
        if not user_ids:
            return {}
        rows = await connection.fetch(
            """
            SELECT user_id::text, property_value
            FROM "03_auth_manage"."05_dtl_user_properties"
            WHERE user_id = ANY($1::uuid[]) AND property_key = 'display_name'
            """,
            user_ids,
        )
        return {r["user_id"]: r["property_value"] for r in rows}


# ---------------------------------------------------------------------------
# Row mappers
# ---------------------------------------------------------------------------


def _row_to_attachment(r) -> AttachmentRecord:
    return AttachmentRecord(
        id=r["id"],
        tenant_key=r["tenant_key"],
        entity_type=r["entity_type"],
        entity_id=r["entity_id"],
        uploaded_by=r["uploaded_by"],
        original_filename=r["original_filename"],
        storage_key=r["storage_key"],
        storage_provider=r["storage_provider"],
        storage_bucket=r["storage_bucket"],
        storage_url=r["storage_url"],
        content_type=r["content_type"],
        file_size_bytes=r["file_size_bytes"],
        checksum_sha256=r["checksum_sha256"],
        is_deleted=r["is_deleted"],
        deleted_at=r["deleted_at"],
        deleted_by=r["deleted_by"],
        virus_scan_status=r["virus_scan_status"],
        virus_scan_at=r["virus_scan_at"],
        description=r["description"],
        auditor_access=r.get("auditor_access", False),
        published_for_audit_by=r.get("published_for_audit_by"),
        published_for_audit_at=r.get("published_for_audit_at"),
        created_at=r["created_at"],
        updated_at=r["updated_at"],
    )


def _row_to_download(r) -> DownloadRecord:
    return DownloadRecord(
        id=r["id"],
        attachment_id=r["attachment_id"],
        downloaded_by=r["downloaded_by"],
        downloaded_at=r["downloaded_at"],
        client_ip=r["client_ip"],
        user_agent=r["user_agent"],
    )
