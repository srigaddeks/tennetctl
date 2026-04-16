"""SQL repository for the document library."""
from __future__ import annotations

import json
from importlib import import_module

import asyncpg

from .models import DocCategoryRecord, DocumentRecord, DocEventRecord

SCHEMA = '"11_docs"'
instrument_class_methods = import_module("backend.01_core.telemetry").instrument_class_methods


@instrument_class_methods(
    namespace="docs.repository",
    logger_name="backend.docs.repository.instrumentation",
)
class DocumentRepository:

    async def list_categories(self, connection: asyncpg.Connection) -> list[DocCategoryRecord]:
        rows = await connection.fetch(
            f'SELECT code, name, description, sort_order, is_active'
            f' FROM {SCHEMA}."01_dim_doc_categories" WHERE is_active = TRUE ORDER BY sort_order'
        )
        return [
            DocCategoryRecord(
                code=r["code"],
                name=r["name"],
                description=r["description"],
                sort_order=r["sort_order"],
                is_active=r["is_active"],
            )
            for r in rows
        ]

    async def list_global_docs(
        self,
        connection: asyncpg.Connection,
        *,
        tenant_key: str,
        category_code: str | None = None,
        search: str | None = None,
        tags: list[str] | None = None,
        limit: int = 50,
        offset: int = 0,
        include_invisible: bool = False,
    ) -> tuple[list[DocumentRecord], int]:
        vis = [] if include_invisible else ["d.is_visible = TRUE"]
        conditions = ["d.scope = 'global'", "d.is_deleted = FALSE", *vis, "d.tenant_key = $1"]
        params: list = [tenant_key]
        p = 2

        if category_code:
            conditions.append(f"d.category_code = ${p}")
            params.append(category_code)
            p += 1

        if search:
            conditions.append(f"(d.title ILIKE ${p} OR d.description ILIKE ${p})")
            params.append(f"%{search}%")
            p += 1

        if tags:
            conditions.append(f"d.tags && ${p}::text[]")
            params.append(tags)
            p += 1

        where = " AND ".join(conditions)

        count_row = await connection.fetchrow(
            f'SELECT COUNT(*)::int AS total FROM {SCHEMA}."02_fct_documents" d WHERE {where}',
            *params,
        )
        total = count_row["total"] if count_row else 0

        rows = await connection.fetch(
            f"""
            SELECT d.id::text, d.tenant_key, d.scope, d.org_id::text,
                   d.category_code, c.name AS category_name,
                   d.title, d.description, d.tags, d.version_label,
                   d.original_filename, d.storage_key, d.storage_provider, d.storage_bucket, d.storage_url,
                   d.content_type, d.file_size_bytes, d.checksum_sha256,
                   d.virus_scan_status, d.virus_scan_at::text,
                   d.is_visible, d.uploaded_by::text, d.is_deleted, d.deleted_at::text, d.deleted_by::text,
                   d.created_at::text, d.updated_at::text,
                   up.property_value AS uploader_display_name
            FROM {SCHEMA}."02_fct_documents" d
            LEFT JOIN {SCHEMA}."01_dim_doc_categories" c ON c.code = d.category_code
            LEFT JOIN "03_auth_manage"."05_dtl_user_properties" up
                ON up.user_id = d.uploaded_by AND up.property_key = 'display_name'
            WHERE {where}
            ORDER BY d.created_at DESC
            LIMIT {limit} OFFSET {offset}
            """,
            *params,
        )
        return [_row_to_doc(r) for r in rows], total

    async def list_org_docs(
        self,
        connection: asyncpg.Connection,
        *,
        tenant_key: str,
        org_id: str,
        category_code: str | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
        include_invisible: bool = False,
    ) -> tuple[list[DocumentRecord], int]:
        vis = [] if include_invisible else ["d.is_visible = TRUE"]
        conditions = ["d.scope = 'org'", "d.is_deleted = FALSE", *vis, "d.tenant_key = $1", "d.org_id = $2::uuid"]
        params: list = [tenant_key, org_id]
        p = 3

        if category_code:
            conditions.append(f"d.category_code = ${p}")
            params.append(category_code)
            p += 1

        if search:
            conditions.append(f"(d.title ILIKE ${p} OR d.description ILIKE ${p})")
            params.append(f"%{search}%")
            p += 1

        where = " AND ".join(conditions)

        count_row = await connection.fetchrow(
            f'SELECT COUNT(*)::int AS total FROM {SCHEMA}."02_fct_documents" d WHERE {where}',
            *params,
        )
        total = count_row["total"] if count_row else 0

        rows = await connection.fetch(
            f"""
            SELECT d.id::text, d.tenant_key, d.scope, d.org_id::text,
                   d.category_code, c.name AS category_name,
                   d.title, d.description, d.tags, d.version_label,
                   d.original_filename, d.storage_key, d.storage_provider, d.storage_bucket, d.storage_url,
                   d.content_type, d.file_size_bytes, d.checksum_sha256,
                   d.virus_scan_status, d.virus_scan_at::text,
                   d.is_visible, d.uploaded_by::text, d.is_deleted, d.deleted_at::text, d.deleted_by::text,
                   d.created_at::text, d.updated_at::text,
                   up.property_value AS uploader_display_name
            FROM {SCHEMA}."02_fct_documents" d
            LEFT JOIN {SCHEMA}."01_dim_doc_categories" c ON c.code = d.category_code
            LEFT JOIN "03_auth_manage"."05_dtl_user_properties" up
                ON up.user_id = d.uploaded_by AND up.property_key = 'display_name'
            WHERE {where}
            ORDER BY d.created_at DESC
            LIMIT {limit} OFFSET {offset}
            """,
            *params,
        )
        return [_row_to_doc(r) for r in rows], total

    async def get_document_by_id(
        self,
        connection: asyncpg.Connection,
        *,
        tenant_key: str,
        doc_id: str,
    ) -> DocumentRecord | None:
        row = await connection.fetchrow(
            f"""
            SELECT d.id::text, d.tenant_key, d.scope, d.org_id::text,
                   d.category_code, c.name AS category_name,
                   d.title, d.description, d.tags, d.version_label,
                   d.original_filename, d.storage_key, d.storage_provider, d.storage_bucket, d.storage_url,
                   d.content_type, d.file_size_bytes, d.checksum_sha256,
                   d.virus_scan_status, d.virus_scan_at::text,
                   d.is_visible, d.uploaded_by::text, d.is_deleted, d.deleted_at::text, d.deleted_by::text,
                   d.created_at::text, d.updated_at::text,
                   up.property_value AS uploader_display_name
            FROM {SCHEMA}."02_fct_documents" d
            LEFT JOIN {SCHEMA}."01_dim_doc_categories" c ON c.code = d.category_code
            LEFT JOIN "03_auth_manage"."05_dtl_user_properties" up
                ON up.user_id = d.uploaded_by AND up.property_key = 'display_name'
            WHERE d.id = $1::uuid AND d.tenant_key = $2 AND d.is_deleted = FALSE
            """,
            doc_id,
            tenant_key,
        )
        return _row_to_doc(row) if row else None

    async def create_document(
        self,
        connection: asyncpg.Connection,
        *,
        tenant_key: str,
        scope: str,
        org_id: str | None,
        category_code: str,
        title: str,
        description: str | None,
        tags: list[str],
        version_label: str | None,
        original_filename: str,
        storage_key: str,
        storage_provider: str,
        storage_bucket: str,
        storage_url: str | None,
        content_type: str,
        file_size_bytes: int,
        checksum_sha256: str,
        uploaded_by: str,
        is_visible: bool = True,
    ) -> DocumentRecord:
        row = await connection.fetchrow(
            f"""
            INSERT INTO {SCHEMA}."02_fct_documents" (
                tenant_key, scope, org_id, category_code, title, description, tags, version_label,
                original_filename, storage_key, storage_provider, storage_bucket, storage_url,
                content_type, file_size_bytes, checksum_sha256, uploaded_by, is_visible
            ) VALUES ($1, $2, $3::uuid, $4, $5, $6, $7::text[], $8,
                      $9, $10, $11, $12, $13,
                      $14, $15, $16, $17::uuid, $18)
            RETURNING id::text, tenant_key, scope, org_id::text,
                      category_code, NULL::text AS category_name,
                      title, description, tags, version_label,
                      original_filename, storage_key, storage_provider, storage_bucket, storage_url,
                      content_type, file_size_bytes, checksum_sha256,
                      virus_scan_status, virus_scan_at::text,
                      is_visible, uploaded_by::text, is_deleted, deleted_at::text, deleted_by::text,
                      created_at::text, updated_at::text,
                      NULL::text AS uploader_display_name
            """,
            tenant_key, scope, org_id, category_code, title, description,
            tags, version_label,
            original_filename, storage_key, storage_provider, storage_bucket, storage_url,
            content_type, file_size_bytes, checksum_sha256, uploaded_by, is_visible,
        )
        return _row_to_doc(row)

    async def update_document(
        self,
        connection: asyncpg.Connection,
        *,
        tenant_key: str,
        doc_id: str,
        title: str | None = None,
        description: str | None = None,
        tags: list[str] | None = None,
        version_label: str | None = None,
        category_code: str | None = None,
        is_visible: bool | None = None,
    ) -> DocumentRecord | None:
        sets = []
        params: list = []
        p = 1
        if title is not None:
            sets.append(f"title = ${p}")
            params.append(title)
            p += 1
        if description is not None:
            sets.append(f"description = ${p}")
            params.append(description)
            p += 1
        if tags is not None:
            sets.append(f"tags = ${p}::text[]")
            params.append(tags)
            p += 1
        if version_label is not None:
            sets.append(f"version_label = ${p}")
            params.append(version_label)
            p += 1
        if category_code is not None:
            sets.append(f"category_code = ${p}")
            params.append(category_code)
            p += 1
        if is_visible is not None:
            sets.append(f"is_visible = ${p}")
            params.append(is_visible)
            p += 1
        if not sets:
            return await self.get_document_by_id(connection, tenant_key=tenant_key, doc_id=doc_id)
        params.append(doc_id)
        params.append(tenant_key)
        row = await connection.fetchrow(
            f"""
            UPDATE {SCHEMA}."02_fct_documents"
            SET {', '.join(sets)}
            WHERE id = ${p}::uuid AND tenant_key = ${p+1} AND is_deleted = FALSE
            RETURNING id::text, tenant_key, scope, org_id::text,
                      category_code, NULL::text AS category_name,
                      title, description, tags, version_label,
                      original_filename, storage_key, storage_provider, storage_bucket, storage_url,
                      content_type, file_size_bytes, checksum_sha256,
                      virus_scan_status, virus_scan_at::text,
                      is_visible, uploaded_by::text, is_deleted, deleted_at::text, deleted_by::text,
                      created_at::text, updated_at::text,
                      NULL::text AS uploader_display_name
            """,
            *params,
        )
        return _row_to_doc(row) if row else None
    
    async def update_document_file(
        self,
        connection: asyncpg.Connection,
        *,
        doc_id: str,
        storage_key: str,
        storage_provider: str,
        storage_bucket: str,
        original_filename: str,
        content_type: str,
        file_size_bytes: int,
        checksum_sha256: str | None = None,
    ) -> DocumentRecord | None:
        row = await connection.fetchrow(
            f"""
            UPDATE {SCHEMA}."02_fct_documents"
            SET storage_key = $1, storage_provider = $2, storage_bucket = $3,
                original_filename = $4, content_type = $5, file_size_bytes = $6,
                checksum_sha256 = $7, updated_at = NOW()
            WHERE id = $8::uuid AND is_deleted = FALSE
            RETURNING id::text, tenant_key, scope, org_id::text,
                      category_code, NULL::text AS category_name,
                      title, description, tags, version_label,
                      original_filename, storage_key, storage_provider, storage_bucket, storage_url,
                      content_type, file_size_bytes, checksum_sha256,
                      virus_scan_status, virus_scan_at::text,
                      is_visible, uploaded_by::text, is_deleted, deleted_at::text, deleted_by::text,
                      created_at::text, updated_at::text,
                      NULL::text AS uploader_display_name
            """,
            storage_key, storage_provider, storage_bucket,
            original_filename, content_type, file_size_bytes,
            checksum_sha256, doc_id
        )
        return _row_to_doc(row) if row else None

    async def soft_delete_document(
        self,
        connection: asyncpg.Connection,
        *,
        doc_id: str,
        deleted_by: str,
    ) -> bool:
        result = await connection.execute(
            f"""
            UPDATE {SCHEMA}."02_fct_documents"
            SET is_deleted = TRUE, deleted_at = NOW(), deleted_by = $2::uuid
            WHERE id = $1::uuid AND is_deleted = FALSE
            """,
            doc_id,
            deleted_by,
        )
        return result == "UPDATE 1"

    async def record_download(
        self,
        connection: asyncpg.Connection,
        *,
        doc_id: str,
        downloaded_by: str,
        client_ip: str | None,
        user_agent: str | None,
    ) -> None:
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."03_trx_doc_downloads"
                (document_id, downloaded_by, client_ip, user_agent)
            VALUES ($1::uuid, $2::uuid, $3, $4)
            """,
            doc_id,
            downloaded_by,
            client_ip,
            user_agent,
        )

    async def write_audit_event(
        self,
        connection: asyncpg.Connection,
        *,
        doc_id: str | None,
        scope: str | None,
        org_id: str | None,
        event_type: str,
        actor_user_id: str,
        tenant_key: str,
        metadata: dict,
    ) -> None:
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."04_aud_doc_events"
                (document_id, scope, org_id, event_type, actor_user_id, tenant_key, metadata)
            VALUES ($1::uuid, $2, $3::uuid, $4, $5::uuid, $6, $7::jsonb)
            """,
            doc_id,
            scope,
            org_id,
            event_type,
            actor_user_id,
            tenant_key,
            json.dumps(metadata),
        )

    async def list_document_events(
        self, connection: asyncpg.Connection, *, tenant_key: str, doc_id: str
    ) -> list[DocEventRecord]:
        rows = await connection.fetch(
            f"""
            SELECT e.id::text, e.document_id::text, e.scope, e.org_id::text, e.event_type,
                   e.actor_user_id::text, e.tenant_key, e.metadata, e.created_at::text,
                   up.property_value AS actor_display_name
            FROM {SCHEMA}."04_aud_doc_events" e
            LEFT JOIN "03_auth_manage"."05_dtl_user_properties" up
                ON up.user_id = e.actor_user_id AND up.property_key = 'display_name'
            WHERE e.document_id = $1::uuid AND e.tenant_key = $2
            ORDER BY e.created_at DESC
            """,
            doc_id,
            tenant_key,
        )
        return [
            DocEventRecord(
                id=r["id"],
                document_id=r["document_id"],
                scope=r["scope"],
                org_id=r["org_id"],
                event_type=r["event_type"],
                actor_user_id=r["actor_user_id"],
                actor_display_name=r["actor_display_name"],
                tenant_key=r["tenant_key"],
                metadata=json.loads(r["metadata"]) if isinstance(r["metadata"], str) else (r["metadata"] or {}),
                created_at=r["created_at"],
            )
            for r in rows
        ]

    async def get_audit_event(
        self, connection: asyncpg.Connection, *, tenant_key: str, event_id: str
    ) -> DocEventRecord | None:
        r = await connection.fetchrow(
            f"""
            SELECT e.id::text, e.document_id::text, e.scope, e.org_id::text, e.event_type,
                   e.actor_user_id::text, e.tenant_key, e.metadata, e.created_at::text,
                   up.property_value AS actor_display_name
            FROM {SCHEMA}."04_aud_doc_events" e
            LEFT JOIN "03_auth_manage"."05_dtl_user_properties" up
                ON up.user_id = e.actor_user_id AND up.property_key = 'display_name'
            WHERE e.id = $1::uuid AND e.tenant_key = $2
            """,
            event_id,
            tenant_key,
        )
        if not r:
            return None
        return DocEventRecord(
            id=r["id"],
            document_id=r["document_id"],
            scope=r["scope"],
            org_id=r["org_id"],
            event_type=r["event_type"],
            actor_user_id=r["actor_user_id"],
            actor_display_name=r["actor_display_name"],
            tenant_key=r["tenant_key"],
            metadata=json.loads(r["metadata"]) if isinstance(r["metadata"], str) else (r["metadata"] or {}),
            created_at=r["created_at"],
        )


def _row_to_doc(r) -> DocumentRecord:
    return DocumentRecord(
        id=r["id"],
        tenant_key=r["tenant_key"],
        scope=r["scope"],
        org_id=r.get("org_id"),
        category_code=r["category_code"],
        category_name=r.get("category_name"),
        title=r["title"],
        description=r.get("description"),
        tags=list(r["tags"]) if r["tags"] else [],
        version_label=r.get("version_label"),
        original_filename=r["original_filename"],
        storage_key=r["storage_key"],
        storage_provider=r["storage_provider"],
        storage_bucket=r["storage_bucket"],
        storage_url=r.get("storage_url"),
        content_type=r["content_type"],
        file_size_bytes=r["file_size_bytes"],
        checksum_sha256=r.get("checksum_sha256"),
        virus_scan_status=r["virus_scan_status"],
        virus_scan_at=r.get("virus_scan_at"),
        is_visible=r["is_visible"],
        uploaded_by=r["uploaded_by"],
        uploader_display_name=r.get("uploader_display_name"),
        is_deleted=r["is_deleted"],
        deleted_at=r.get("deleted_at"),
        deleted_by=r.get("deleted_by"),
        created_at=r["created_at"],
        updated_at=r["updated_at"],
    )
