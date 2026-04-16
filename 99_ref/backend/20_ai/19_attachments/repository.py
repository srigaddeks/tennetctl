from __future__ import annotations
import json as _json
from .models import AttachmentRecord


def _row(r) -> AttachmentRecord:
    # pageindex_tree comes back as a string from asyncpg JSONB columns
    raw_tree = r["pageindex_tree"] if "pageindex_tree" in r.keys() else None
    if isinstance(raw_tree, str):
        try:
            raw_tree = _json.loads(raw_tree)
        except Exception:
            raw_tree = None

    return AttachmentRecord(
        id=str(r["id"]),
        conversation_id=str(r["conversation_id"]),
        tenant_key=r["tenant_key"],
        user_id=str(r["user_id"]),
        filename=r["filename"],
        content_type=r["content_type"],
        file_size_bytes=r["file_size_bytes"],
        chunk_count=r["chunk_count"],
        ingest_status=r["ingest_status"],
        error_message=r["error_message"],
        qdrant_collection=r["qdrant_collection"],
        created_at=r["created_at"].isoformat(),
        updated_at=r["updated_at"].isoformat(),
        pageindex_status=r["pageindex_status"] if "pageindex_status" in r.keys() else "none",
        pageindex_tree=raw_tree,
        pageindex_error=r["pageindex_error"] if "pageindex_error" in r.keys() else None,
    )


class AttachmentRepository:

    async def create(
        self,
        conn,
        *,
        conversation_id: str,
        tenant_key: str,
        user_id: str,
        filename: str,
        content_type: str,
        file_size_bytes: int,
    ) -> AttachmentRecord:
        row = await conn.fetchrow(
            """
            INSERT INTO "20_ai"."44_fct_conversation_attachments"
                (conversation_id, tenant_key, user_id, filename, content_type, file_size_bytes)
            VALUES ($1::uuid, $2, $3::uuid, $4, $5, $6)
            RETURNING *
            """,
            conversation_id, tenant_key, user_id, filename, content_type, file_size_bytes,
        )
        return _row(row)

    async def update_ingest_status(
        self,
        conn,
        *,
        attachment_id: str,
        ingest_status: str,
        chunk_count: int | None = None,
        error_message: str | None = None,
    ) -> None:
        await conn.execute(
            """
            UPDATE "20_ai"."44_fct_conversation_attachments"
            SET ingest_status = $1,
                chunk_count   = COALESCE($2, chunk_count),
                error_message = $3,
                updated_at    = NOW()
            WHERE id = $4::uuid
            """,
            ingest_status, chunk_count, error_message, attachment_id,
        )

    async def list_by_conversation(self, conn, *, conversation_id: str) -> list[AttachmentRecord]:
        rows = await conn.fetch(
            """
            SELECT * FROM "20_ai"."44_fct_conversation_attachments"
            WHERE conversation_id = $1::uuid
            ORDER BY created_at
            """,
            conversation_id,
        )
        return [_row(r) for r in rows]

    async def get(self, conn, *, attachment_id: str, user_id: str) -> AttachmentRecord | None:
        row = await conn.fetchrow(
            """
            SELECT * FROM "20_ai"."44_fct_conversation_attachments"
            WHERE id = $1::uuid AND user_id = $2::uuid
            """,
            attachment_id, user_id,
        )
        return _row(row) if row else None

    async def update_pageindex_status(
        self,
        conn,
        *,
        attachment_id: str,
        pageindex_status: str,
        pageindex_tree: dict | None = None,
        pageindex_error: str | None = None,
    ) -> None:
        import json as _json_inner
        tree_json = _json_inner.dumps(pageindex_tree) if pageindex_tree is not None else None
        await conn.execute(
            """
            UPDATE "20_ai"."44_fct_conversation_attachments"
            SET pageindex_status = $1,
                pageindex_tree   = $2::jsonb,
                pageindex_error  = $3,
                updated_at       = NOW()
            WHERE id = $4::uuid
            """,
            pageindex_status, tree_json, pageindex_error, attachment_id,
        )

    async def get_by_id(self, conn, *, attachment_id: str) -> AttachmentRecord | None:
        """Fetch without user_id check — for background task use only."""
        row = await conn.fetchrow(
            """
            SELECT * FROM "20_ai"."44_fct_conversation_attachments"
            WHERE id = $1::uuid
            """,
            attachment_id,
        )
        return _row(row) if row else None

    async def list_ready_for_pageindex(
        self, conn, *, conversation_id: str
    ) -> list[AttachmentRecord]:
        """Return attachments where pageindex_status='ready' (tree is available)."""
        rows = await conn.fetch(
            """
            SELECT * FROM "20_ai"."44_fct_conversation_attachments"
            WHERE conversation_id = $1::uuid
              AND pageindex_status = 'ready'
            ORDER BY created_at
            """,
            conversation_id,
        )
        return [_row(r) for r in rows]

    async def delete(self, conn, *, attachment_id: str, user_id: str) -> bool:
        result = await conn.execute(
            """
            DELETE FROM "20_ai"."44_fct_conversation_attachments"
            WHERE id = $1::uuid AND user_id = $2::uuid
            """,
            attachment_id, user_id,
        )
        return result == "DELETE 1"
