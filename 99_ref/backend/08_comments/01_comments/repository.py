"""SQL repository for the comments domain.

All SQL is fully parameterised — no f-string interpolation of user-supplied
values.  Schema and table names are hard-coded constants.
"""

from __future__ import annotations

import json
from importlib import import_module

import asyncpg

from .models import (
    CommentDetailRecord,
    CommentEditRecord,
    CommentRecord,
    CommentWithRepliesRecord,
    ReactionSummaryRecord,
)

SCHEMA = '"08_comments"'
AUTH_SCHEMA = '"03_auth_manage"'

instrument_class_methods = import_module("backend.01_core.telemetry").instrument_class_methods

# ─────────────────────────────────────────────────────────────────────────────
# Row mappers
# ─────────────────────────────────────────────────────────────────────────────

def _parse_uuid_array(raw) -> list[str]:
    """Normalise asyncpg UUID[] into a list[str], handling all wire formats."""
    if raw is None:
        return []
    if isinstance(raw, (list, tuple)):
        return [str(x) for x in raw]
    if isinstance(raw, str):
        stripped = raw.strip("{}")
        return [x.strip() for x in stripped.split(",") if x.strip()] if stripped else []
    return []


def _row_to_comment(r) -> CommentRecord:
    return CommentRecord(
        id=r["id"],
        tenant_key=r["tenant_key"],
        entity_type=r["entity_type"],
        entity_id=r["entity_id"],
        parent_comment_id=r["parent_comment_id"],
        author_user_id=r["author_user_id"],
        content=r["content"],
        is_edited=r["is_edited"],
        is_deleted=r["is_deleted"],
        deleted_at=r["deleted_at"],
        deleted_by=r["deleted_by"],
        pinned=r["pinned"],
        pinned_by=r["pinned_by"],
        pinned_at=r["pinned_at"],
        resolved=r["resolved"],
        resolved_by=r["resolved_by"],
        resolved_at=r["resolved_at"],
        content_format=r.get("content_format", "markdown") if hasattr(r, "get") else (r["content_format"] if "content_format" in r.keys() else "markdown"),
        rendered_html=r.get("rendered_html") if hasattr(r, "get") else (r["rendered_html"] if "rendered_html" in r.keys() else None),
        visibility=r.get("visibility", "external") if hasattr(r, "get") else (r["visibility"] if "visibility" in r.keys() else "external"),
        is_locked=r.get("is_locked", False) if hasattr(r, "get") else (r["is_locked"] if "is_locked" in r.keys() else False),
        locked_by=r.get("locked_by") if hasattr(r, "get") else (r["locked_by"] if "locked_by" in r.keys() else None),
        locked_at=r.get("locked_at") if hasattr(r, "get") else (r["locked_at"] if "locked_at" in r.keys() else None),
        mention_user_ids=_parse_uuid_array(r["mention_user_ids"]),
        created_at=r["created_at"],
        updated_at=r["updated_at"],
    )


def _row_to_comment_detail(r) -> CommentDetailRecord:
    return CommentDetailRecord(
        id=r["id"],
        tenant_key=r["tenant_key"],
        entity_type=r["entity_type"],
        entity_id=r["entity_id"],
        parent_comment_id=r["parent_comment_id"],
        author_user_id=r["author_user_id"],
        content=r["content"],
        is_edited=r["is_edited"],
        is_deleted=r["is_deleted"],
        deleted_at=r["deleted_at"],
        deleted_by=r["deleted_by"],
        pinned=r["pinned"],
        pinned_by=r["pinned_by"],
        pinned_at=r["pinned_at"],
        resolved=r["resolved"],
        resolved_by=r["resolved_by"],
        resolved_at=r["resolved_at"],
        content_format=r.get("content_format", "markdown") if hasattr(r, "get") else (r["content_format"] if "content_format" in r.keys() else "markdown"),
        rendered_html=r.get("rendered_html") if hasattr(r, "get") else (r["rendered_html"] if "rendered_html" in r.keys() else None),
        visibility=r.get("visibility", "external") if hasattr(r, "get") else (r["visibility"] if "visibility" in r.keys() else "external"),
        is_locked=r.get("is_locked", False) if hasattr(r, "get") else (r["is_locked"] if "is_locked" in r.keys() else False),
        locked_by=r.get("locked_by") if hasattr(r, "get") else (r["locked_by"] if "locked_by" in r.keys() else None),
        locked_at=r.get("locked_at") if hasattr(r, "get") else (r["locked_at"] if "locked_at" in r.keys() else None),
        mention_user_ids=_parse_uuid_array(r["mention_user_ids"]),
        reply_count=r["reply_count"] or 0,
        created_at=r["created_at"],
        updated_at=r["updated_at"],
        author_display_name=r["author_display_name"],
        author_email=r["author_email"],
    )


def _row_to_edit(r) -> CommentEditRecord:
    return CommentEditRecord(
        id=r["id"],
        comment_id=r["comment_id"],
        previous_content=r["previous_content"],
        edited_by=r["edited_by"],
        edited_at=r["edited_at"],
    )


# ─────────────────────────────────────────────────────────────────────────────
# Repository
# ─────────────────────────────────────────────────────────────────────────────

@instrument_class_methods(
    namespace="comments.repository",
    logger_name="backend.comments.repository.instrumentation",
)
class CommentRepository:

    # ── List (threaded, paginated) ─────────────────────────────────────────

    async def list_comments(
        self,
        connection: asyncpg.Connection,
        *,
        tenant_key: str,
        entity_type: str,
        entity_id: str,
        current_user_id: str,
        include_replies: bool = True,
        limit: int = 25,
        cursor_created_at: str | None = None,
        cursor_id: str | None = None,
        visibility: str | None = None,
    ) -> tuple[list[CommentWithRepliesRecord], int]:
        """Fetch top-level comments (parent IS NULL) for an entity with:

        - Up to 10 most-recent replies per comment
        - Reaction counts grouped by reaction_code
        - Author display_name and email joined from 03_auth_manage
        - Stable cursor-based pagination via (created_at DESC, id)
        - Count excludes soft-deleted top-level comments
        """
        # Build visibility filter
        visibility_filter = ""
        visibility_values: list[object] = [tenant_key, entity_type, entity_id]
        idx = 4
        if visibility is not None:
            visibility_filter = f"AND visibility = ${idx}"
            visibility_values.append(visibility)
            idx += 1

        # Count non-deleted top-level comments for this entity
        count_row = await connection.fetchrow(
            f"""
            SELECT COUNT(*)::int AS total
            FROM {SCHEMA}."01_fct_comments"
            WHERE tenant_key = $1
              AND entity_type = $2
              AND entity_id   = $3::uuid
              AND parent_comment_id IS NULL
              AND is_deleted = FALSE
              {visibility_filter}
            """,
            *visibility_values,
        )
        total = count_row["total"] if count_row else 0

        # Build cursor filter for stable pagination — values are already
        # typed by the DB cast so no user input reaches SQL structure.
        cursor_filter = ""
        cursor_values: list[object] = list(visibility_values)
        if cursor_created_at is not None and cursor_id is not None:
            cursor_filter = f"AND (c.created_at, c.id::text) < (${idx}::timestamptz, ${idx+1})"
            cursor_values.append(cursor_created_at)
            cursor_values.append(cursor_id)
            idx += 2

        # Main CTE query — top-level comments with reply counts and author info
        rows = await connection.fetch(
            f"""
            WITH top_comments AS (
                SELECT c.id
                FROM {SCHEMA}."01_fct_comments" c
                WHERE c.tenant_key = $1
                  AND c.entity_type = $2
                  AND c.entity_id   = $3::uuid
                  AND c.parent_comment_id IS NULL
                  AND c.is_deleted = FALSE
                  {visibility_filter}
                  {cursor_filter}
                ORDER BY c.created_at DESC, c.id
                LIMIT {limit}
            ),
            reply_counts AS (
                SELECT r.parent_comment_id, COUNT(*)::int AS cnt
                FROM {SCHEMA}."01_fct_comments" r
                WHERE r.parent_comment_id IN (SELECT id FROM top_comments)
                GROUP BY r.parent_comment_id
            ),
            author_display_names AS (
                SELECT p.user_id::text, p.property_value AS display_name
                FROM {AUTH_SCHEMA}."05_dtl_user_properties" p
                WHERE p.property_key = 'display_name'
            ),
            author_emails AS (
                SELECT p.user_id::text, p.property_value AS email
                FROM {AUTH_SCHEMA}."05_dtl_user_properties" p
                WHERE p.property_key = 'email'
            )
            SELECT
                c.id::text,
                c.tenant_key,
                c.entity_type,
                c.entity_id::text,
                c.parent_comment_id::text,
                c.author_user_id::text,
                c.content,
                c.is_edited,
                c.is_deleted,
                c.deleted_at::text,
                c.deleted_by::text,
                c.pinned,
                c.pinned_by::text,
                c.pinned_at::text,
                c.resolved,
                c.resolved_by::text,
                c.resolved_at::text,
                c.content_format,
                c.rendered_html,
                c.visibility,
                c.is_locked,
                c.locked_by::text,
                c.locked_at::text,
                c.mention_user_ids::text[],
                c.created_at::text,
                c.updated_at::text,
                COALESCE(rc.cnt, 0)::int AS reply_count,
                adn.display_name          AS author_display_name,
                ae.email                  AS author_email
            FROM {SCHEMA}."01_fct_comments" c
            JOIN top_comments tc ON tc.id = c.id
            LEFT JOIN reply_counts rc ON rc.parent_comment_id = c.id
            LEFT JOIN author_display_names adn ON adn.user_id = c.author_user_id::text
            LEFT JOIN author_emails ae ON ae.user_id = c.author_user_id::text
            ORDER BY c.created_at DESC, c.id
            """,
            *cursor_values,
        )

        top_level = [_row_to_comment_detail(r) for r in rows]
        if not top_level:
            return [], total

        top_ids = [c.id for c in top_level]

        # Fetch replies for all top-level comments (window function for top-10 per parent)
        reply_rows: list = []
        if include_replies and top_ids:
            id_placeholders = ", ".join(f"${i+1}::uuid" for i in range(len(top_ids)))
            reply_rows = await connection.fetch(
                f"""
                WITH ranked_replies AS (
                    SELECT
                        r.id::text,
                        r.tenant_key,
                        r.entity_type,
                        r.entity_id::text,
                        r.parent_comment_id::text,
                        r.author_user_id::text,
                        r.content,
                        r.is_edited,
                        r.is_deleted,
                        r.deleted_at::text,
                        r.deleted_by::text,
                        r.pinned,
                        r.pinned_by::text,
                        r.pinned_at::text,
                        r.resolved,
                        r.resolved_by::text,
                        r.resolved_at::text,
                        r.content_format,
                        r.rendered_html,
                        r.visibility,
                        r.is_locked,
                        r.locked_by::text,
                        r.locked_at::text,
                        r.mention_user_ids::text[],
                        r.created_at::text,
                        r.updated_at::text,
                        0::int AS reply_count,
                        adn.display_name AS author_display_name,
                        ae.email         AS author_email,
                        ROW_NUMBER() OVER (
                            PARTITION BY r.parent_comment_id
                            ORDER BY r.created_at ASC, r.id
                        ) AS rn
                    FROM {SCHEMA}."01_fct_comments" r
                    LEFT JOIN (
                        SELECT p.user_id::text, p.property_value AS display_name
                        FROM {AUTH_SCHEMA}."05_dtl_user_properties" p
                        WHERE p.property_key = 'display_name'
                    ) adn ON adn.user_id = r.author_user_id::text
                    LEFT JOIN (
                        SELECT p.user_id::text, p.property_value AS email
                        FROM {AUTH_SCHEMA}."05_dtl_user_properties" p
                        WHERE p.property_key = 'email'
                    ) ae ON ae.user_id = r.author_user_id::text
                    WHERE r.parent_comment_id IN ({id_placeholders})
                )
                SELECT * FROM ranked_replies
                WHERE rn <= 10
                ORDER BY parent_comment_id, created_at ASC
                """,
                *top_ids,
            )

        # Fetch reactions for all fetched comment IDs
        all_ids = top_ids + [r["id"] for r in reply_rows]
        reaction_map: dict[str, list[ReactionSummaryRecord]] = {}
        if all_ids:
            rx_placeholders = ", ".join(f"${i+1}::uuid" for i in range(len(all_ids)))
            rx_rows = await connection.fetch(
                f"""
                SELECT
                    rx.comment_id::text,
                    rx.reaction_code,
                    COUNT(*)::int                                     AS cnt,
                    ARRAY_AGG(rx.user_id::text ORDER BY rx.created_at) AS user_ids,
                    ARRAY_AGG(
                        COALESCE(adn.display_name, '')
                        ORDER BY rx.created_at
                    ) AS user_names
                FROM {SCHEMA}."03_trx_comment_reactions" rx
                LEFT JOIN (
                    SELECT p.user_id::text, p.property_value AS display_name
                    FROM {AUTH_SCHEMA}."05_dtl_user_properties" p
                    WHERE p.property_key = 'display_name'
                ) adn ON adn.user_id = rx.user_id::text
                WHERE rx.comment_id IN ({rx_placeholders})
                GROUP BY rx.comment_id, rx.reaction_code
                ORDER BY rx.comment_id, cnt DESC
                """,
                *all_ids,
            )
            for rx in rx_rows:
                cid = rx["comment_id"]
                reaction_map.setdefault(cid, []).append(
                    ReactionSummaryRecord(
                        reaction_code=rx["reaction_code"],
                        count=rx["cnt"],
                        user_ids=list(rx["user_ids"] or []),
                        user_names=[n for n in (rx["user_names"] or []) if n],
                        reacted_by_me=current_user_id in (rx["user_ids"] or []),
                    )
                )

        # Build reply lookup
        replies_by_parent: dict[str, list[CommentDetailRecord]] = {}
        for r in reply_rows:
            rec = _row_to_comment_detail(r)
            replies_by_parent.setdefault(rec.parent_comment_id, []).append(rec)

        # Assemble final result
        results: list[CommentWithRepliesRecord] = []
        for c in top_level:
            results.append(
                CommentWithRepliesRecord(
                    id=c.id,
                    tenant_key=c.tenant_key,
                    entity_type=c.entity_type,
                    entity_id=c.entity_id,
                    parent_comment_id=c.parent_comment_id,
                    author_user_id=c.author_user_id,
                    content=c.content,
                    is_edited=c.is_edited,
                    is_deleted=c.is_deleted,
                    deleted_at=c.deleted_at,
                    deleted_by=c.deleted_by,
                    pinned=c.pinned,
                    pinned_by=c.pinned_by,
                    pinned_at=c.pinned_at,
                    resolved=c.resolved,
                    resolved_by=c.resolved_by,
                    resolved_at=c.resolved_at,
                    content_format=c.content_format,
                    rendered_html=c.rendered_html,
                    visibility=c.visibility,
                    is_locked=c.is_locked,
                    locked_by=c.locked_by,
                    locked_at=c.locked_at,
                    mention_user_ids=c.mention_user_ids,
                    reply_count=c.reply_count,
                    created_at=c.created_at,
                    updated_at=c.updated_at,
                    author_display_name=c.author_display_name,
                    author_email=c.author_email,
                    replies=replies_by_parent.get(c.id, []),
                    reactions=reaction_map.get(c.id, []),
                    edit_history=[],
                )
            )
        return results, total

    # ── Get single comment (with replies, reactions, history) ─────────────

    async def get_comment_with_replies(
        self,
        connection: asyncpg.Connection,
        comment_id: str,
        *,
        current_user_id: str,
    ) -> CommentWithRepliesRecord | None:
        row = await connection.fetchrow(
            f"""
            WITH reply_counts AS (
                SELECT parent_comment_id, COUNT(*)::int AS cnt
                FROM {SCHEMA}."01_fct_comments"
                WHERE parent_comment_id = $1::uuid
                GROUP BY parent_comment_id
            ),
            adn AS (
                SELECT p.user_id::text, p.property_value AS display_name
                FROM {AUTH_SCHEMA}."05_dtl_user_properties" p
                WHERE p.property_key = 'display_name'
            ),
            ae AS (
                SELECT p.user_id::text, p.property_value AS email
                FROM {AUTH_SCHEMA}."05_dtl_user_properties" p
                WHERE p.property_key = 'email'
            )
            SELECT
                c.id::text,
                c.tenant_key,
                c.entity_type,
                c.entity_id::text,
                c.parent_comment_id::text,
                c.author_user_id::text,
                c.content,
                c.is_edited,
                c.is_deleted,
                c.deleted_at::text,
                c.deleted_by::text,
                c.pinned,
                c.pinned_by::text,
                c.pinned_at::text,
                c.resolved,
                c.resolved_by::text,
                c.resolved_at::text,
                c.content_format,
                c.rendered_html,
                c.visibility,
                c.is_locked,
                c.locked_by::text,
                c.locked_at::text,
                c.mention_user_ids::text[],
                c.created_at::text,
                c.updated_at::text,
                COALESCE(rc.cnt, 0)::int AS reply_count,
                adn.display_name          AS author_display_name,
                ae.email                  AS author_email
            FROM {SCHEMA}."01_fct_comments" c
            LEFT JOIN reply_counts rc ON rc.parent_comment_id = c.id
            LEFT JOIN adn ON adn.user_id = c.author_user_id::text
            LEFT JOIN ae ON ae.user_id = c.author_user_id::text
            WHERE c.id = $1::uuid
            """,
            comment_id,
        )
        if not row:
            return None

        detail = _row_to_comment_detail(row)

        # Replies (all of them for single-comment detail view)
        reply_rows = await connection.fetch(
            f"""
            SELECT
                r.id::text, r.tenant_key, r.entity_type, r.entity_id::text,
                r.parent_comment_id::text, r.author_user_id::text,
                r.content, r.is_edited, r.is_deleted,
                r.deleted_at::text, r.deleted_by::text,
                r.pinned, r.pinned_by::text, r.pinned_at::text,
                r.resolved, r.resolved_by::text, r.resolved_at::text,
                r.content_format, r.rendered_html, r.visibility, r.is_locked,
                r.locked_by::text, r.locked_at::text,
                r.mention_user_ids::text[],
                r.created_at::text, r.updated_at::text,
                0::int AS reply_count,
                adn.display_name AS author_display_name,
                ae.email         AS author_email
            FROM {SCHEMA}."01_fct_comments" r
            LEFT JOIN (
                SELECT p.user_id::text, p.property_value AS display_name
                FROM {AUTH_SCHEMA}."05_dtl_user_properties" p
                WHERE p.property_key = 'display_name'
            ) adn ON adn.user_id = r.author_user_id::text
            LEFT JOIN (
                SELECT p.user_id::text, p.property_value AS email
                FROM {AUTH_SCHEMA}."05_dtl_user_properties" p
                WHERE p.property_key = 'email'
            ) ae ON ae.user_id = r.author_user_id::text
            WHERE r.parent_comment_id = $1::uuid
            ORDER BY r.created_at ASC, r.id
            """,
            comment_id,
        )
        replies = [_row_to_comment_detail(r) for r in reply_rows]

        # Reactions for this comment and its replies
        all_ids = [comment_id] + [r.id for r in replies]
        rx_placeholders = ", ".join(f"${i+1}::uuid" for i in range(len(all_ids)))
        rx_rows = await connection.fetch(
            f"""
            SELECT
                rx.comment_id::text,
                rx.reaction_code,
                COUNT(*)::int                                     AS cnt,
                ARRAY_AGG(rx.user_id::text ORDER BY rx.created_at) AS user_ids,
                ARRAY_AGG(
                    COALESCE(adn.display_name, '')
                    ORDER BY rx.created_at
                ) AS user_names
            FROM {SCHEMA}."03_trx_comment_reactions" rx
            LEFT JOIN (
                SELECT p.user_id::text, p.property_value AS display_name
                FROM {AUTH_SCHEMA}."05_dtl_user_properties" p
                WHERE p.property_key = 'display_name'
            ) adn ON adn.user_id = rx.user_id::text
            WHERE rx.comment_id IN ({rx_placeholders})
            GROUP BY rx.comment_id, rx.reaction_code
            ORDER BY rx.comment_id, cnt DESC
            """,
            *all_ids,
        )
        reaction_map: dict[str, list[ReactionSummaryRecord]] = {}
        for rx in rx_rows:
            cid = rx["comment_id"]
            reaction_map.setdefault(cid, []).append(
                ReactionSummaryRecord(
                    reaction_code=rx["reaction_code"],
                    count=rx["cnt"],
                    user_ids=list(rx["user_ids"] or []),
                    user_names=[n for n in (rx["user_names"] or []) if n],
                    reacted_by_me=current_user_id in (rx["user_ids"] or []),
                )
            )

        # Edit history
        edit_rows = await connection.fetch(
            f"""
            SELECT id::text, comment_id::text, previous_content, edited_by::text, edited_at::text
            FROM {SCHEMA}."02_trx_comment_edits"
            WHERE comment_id = $1::uuid
            ORDER BY edited_at ASC
            """,
            comment_id,
        )
        edits = [_row_to_edit(r) for r in edit_rows]

        return CommentWithRepliesRecord(
            id=detail.id,
            tenant_key=detail.tenant_key,
            entity_type=detail.entity_type,
            entity_id=detail.entity_id,
            parent_comment_id=detail.parent_comment_id,
            author_user_id=detail.author_user_id,
            content=detail.content,
            is_edited=detail.is_edited,
            is_deleted=detail.is_deleted,
            deleted_at=detail.deleted_at,
            deleted_by=detail.deleted_by,
            pinned=detail.pinned,
            pinned_by=detail.pinned_by,
            pinned_at=detail.pinned_at,
            resolved=detail.resolved,
            resolved_by=detail.resolved_by,
            resolved_at=detail.resolved_at,
            content_format=detail.content_format,
            rendered_html=detail.rendered_html,
            visibility=detail.visibility,
            is_locked=detail.is_locked,
            locked_by=detail.locked_by,
            locked_at=detail.locked_at,
            mention_user_ids=detail.mention_user_ids,
            reply_count=detail.reply_count,
            created_at=detail.created_at,
            updated_at=detail.updated_at,
            author_display_name=detail.author_display_name,
            author_email=detail.author_email,
            replies=replies,
            reactions=reaction_map.get(comment_id, []),
            edit_history=edits,
        )

    # ── Get raw comment (for mutation checks) ─────────────────────────────

    async def get_comment_by_id(
        self, connection: asyncpg.Connection, comment_id: str
    ) -> CommentRecord | None:
        row = await connection.fetchrow(
            f"""
            SELECT
                id::text, tenant_key, entity_type, entity_id::text,
                parent_comment_id::text, author_user_id::text,
                content, is_edited, is_deleted,
                deleted_at::text, deleted_by::text,
                pinned, pinned_by::text, pinned_at::text,
                resolved, resolved_by::text, resolved_at::text,
                content_format, rendered_html, visibility, is_locked,
                locked_by::text, locked_at::text,
                mention_user_ids::text[],
                created_at::text, updated_at::text
            FROM {SCHEMA}."01_fct_comments"
            WHERE id = $1::uuid
            """,
            comment_id,
        )
        return _row_to_comment(row) if row else None

    # ── Create ────────────────────────────────────────────────────────────

    async def create_comment(
        self,
        connection: asyncpg.Connection,
        *,
        comment_id: str,
        tenant_key: str,
        entity_type: str,
        entity_id: str,
        parent_comment_id: str | None,
        author_user_id: str,
        content: str,
        content_format: str = "markdown",
        rendered_html: str | None = None,
        visibility: str = "external",
        mention_user_ids: list[str],
        now: object,
    ) -> CommentRecord:
        row = await connection.fetchrow(
            f"""
            INSERT INTO {SCHEMA}."01_fct_comments" (
                id, tenant_key, entity_type, entity_id,
                parent_comment_id, author_user_id, content,
                content_format, rendered_html, visibility,
                mention_user_ids, created_at, updated_at
            )
            VALUES (
                $1::uuid, $2, $3, $4::uuid,
                $5::uuid, $6::uuid, $7,
                $8, $9, $10,
                $11::uuid[], $12, $13
            )
            RETURNING
                id::text, tenant_key, entity_type, entity_id::text,
                parent_comment_id::text, author_user_id::text,
                content, is_edited, is_deleted,
                deleted_at::text, deleted_by::text,
                pinned, pinned_by::text, pinned_at::text,
                resolved, resolved_by::text, resolved_at::text,
                content_format, rendered_html, visibility, is_locked,
                locked_by::text, locked_at::text,
                mention_user_ids::text[],
                created_at::text, updated_at::text
            """,
            comment_id, tenant_key, entity_type, entity_id,
            parent_comment_id, author_user_id, content,
            content_format, rendered_html, visibility,
            mention_user_ids, now, now,
        )
        return _row_to_comment(row)

    # ── Edit (with history) ───────────────────────────────────────────────

    async def update_comment_content(
        self,
        connection: asyncpg.Connection,
        comment_id: str,
        *,
        content: str,
        rendered_html: str | None = None,
        mention_user_ids: list[str],
        now: object,
    ) -> CommentRecord | None:
        row = await connection.fetchrow(
            f"""
            UPDATE {SCHEMA}."01_fct_comments"
            SET content = $2, rendered_html = $3, mention_user_ids = $4::uuid[],
                is_edited = TRUE, updated_at = $5
            WHERE id = $1::uuid AND is_deleted = FALSE
            RETURNING
                id::text, tenant_key, entity_type, entity_id::text,
                parent_comment_id::text, author_user_id::text,
                content, is_edited, is_deleted,
                deleted_at::text, deleted_by::text,
                pinned, pinned_by::text, pinned_at::text,
                resolved, resolved_by::text, resolved_at::text,
                content_format, rendered_html, visibility, is_locked,
                locked_by::text, locked_at::text,
                mention_user_ids::text[],
                created_at::text, updated_at::text
            """,
            comment_id, content, rendered_html, mention_user_ids, now,
        )
        return _row_to_comment(row) if row else None

    async def record_edit_history(
        self,
        connection: asyncpg.Connection,
        *,
        edit_id: str,
        comment_id: str,
        previous_content: str,
        edited_by: str,
        now: object,
    ) -> None:
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."02_trx_comment_edits" (
                id, comment_id, previous_content, edited_by, edited_at
            )
            VALUES ($1::uuid, $2::uuid, $3, $4::uuid, $5)
            """,
            edit_id, comment_id, previous_content, edited_by, now,
        )

    # ── Soft delete ───────────────────────────────────────────────────────

    async def soft_delete_comment(
        self,
        connection: asyncpg.Connection,
        comment_id: str,
        *,
        deleted_by: str,
        now: object,
    ) -> bool:
        result = await connection.execute(
            f"""
            UPDATE {SCHEMA}."01_fct_comments"
            SET is_deleted = TRUE, deleted_at = $2, deleted_by = $3::uuid, updated_at = $4
            WHERE id = $1::uuid AND is_deleted = FALSE
            """,
            comment_id, now, deleted_by, now,
        )
        return result != "UPDATE 0"

    # ── Pin / Unpin ───────────────────────────────────────────────────────

    async def pin_comment(
        self,
        connection: asyncpg.Connection,
        comment_id: str,
        *,
        pinned_by: str,
        now: object,
    ) -> bool:
        result = await connection.execute(
            f"""
            UPDATE {SCHEMA}."01_fct_comments"
            SET pinned = TRUE, pinned_by = $2::uuid, pinned_at = $3, updated_at = $4
            WHERE id = $1::uuid AND is_deleted = FALSE AND pinned = FALSE
            """,
            comment_id, pinned_by, now, now,
        )
        return result != "UPDATE 0"

    async def unpin_comment(
        self,
        connection: asyncpg.Connection,
        comment_id: str,
        *,
        now: object,
    ) -> bool:
        result = await connection.execute(
            f"""
            UPDATE {SCHEMA}."01_fct_comments"
            SET pinned = FALSE, pinned_by = NULL, pinned_at = NULL, updated_at = $2
            WHERE id = $1::uuid AND is_deleted = FALSE AND pinned = TRUE
            """,
            comment_id, now,
        )
        return result != "UPDATE 0"

    # ── Resolve / Unresolve ───────────────────────────────────────────────

    async def resolve_comment(
        self,
        connection: asyncpg.Connection,
        comment_id: str,
        *,
        resolved_by: str,
        now: object,
    ) -> bool:
        result = await connection.execute(
            f"""
            UPDATE {SCHEMA}."01_fct_comments"
            SET resolved = TRUE, resolved_by = $2::uuid, resolved_at = $3, updated_at = $4
            WHERE id = $1::uuid AND is_deleted = FALSE AND resolved = FALSE
            """,
            comment_id, resolved_by, now, now,
        )
        return result != "UPDATE 0"

    async def unresolve_comment(
        self,
        connection: asyncpg.Connection,
        comment_id: str,
        *,
        now: object,
    ) -> bool:
        result = await connection.execute(
            f"""
            UPDATE {SCHEMA}."01_fct_comments"
            SET resolved = FALSE, resolved_by = NULL, resolved_at = NULL, updated_at = $2
            WHERE id = $1::uuid AND is_deleted = FALSE AND resolved = TRUE
            """,
            comment_id, now,
        )
        return result != "UPDATE 0"

    # ── Reactions ─────────────────────────────────────────────────────────

    async def add_reaction(
        self,
        connection: asyncpg.Connection,
        *,
        reaction_id: str,
        comment_id: str,
        user_id: str,
        reaction_code: str,
        now: object,
    ) -> bool:
        """Upsert a reaction. Returns True always (ON CONFLICT DO NOTHING is safe)."""
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."03_trx_comment_reactions"
                (id, comment_id, user_id, reaction_code, created_at)
            VALUES ($1::uuid, $2::uuid, $3::uuid, $4, $5)
            ON CONFLICT (comment_id, user_id, reaction_code) DO NOTHING
            """,
            reaction_id, comment_id, user_id, reaction_code, now,
        )
        return True

    async def remove_reaction(
        self,
        connection: asyncpg.Connection,
        comment_id: str,
        user_id: str,
        reaction_code: str,
    ) -> bool:
        result = await connection.execute(
            f"""
            DELETE FROM {SCHEMA}."03_trx_comment_reactions"
            WHERE comment_id = $1::uuid AND user_id = $2::uuid AND reaction_code = $3
            """,
            comment_id, user_id, reaction_code,
        )
        return result != "DELETE 0"

    async def get_reactions_for_comment(
        self,
        connection: asyncpg.Connection,
        comment_id: str,
        *,
        current_user_id: str,
    ) -> list[ReactionSummaryRecord]:
        rows = await connection.fetch(
            f"""
            SELECT
                rx.reaction_code,
                COUNT(*)::int                                     AS cnt,
                ARRAY_AGG(rx.user_id::text ORDER BY rx.created_at) AS user_ids,
                ARRAY_AGG(
                    COALESCE(adn.display_name, '')
                    ORDER BY rx.created_at
                ) AS user_names
            FROM {SCHEMA}."03_trx_comment_reactions" rx
            LEFT JOIN (
                SELECT p.user_id::text, p.property_value AS display_name
                FROM {AUTH_SCHEMA}."05_dtl_user_properties" p
                WHERE p.property_key = 'display_name'
            ) adn ON adn.user_id = rx.user_id::text
            WHERE rx.comment_id = $1::uuid
            GROUP BY rx.reaction_code
            ORDER BY cnt DESC
            """,
            comment_id,
        )
        return [
            ReactionSummaryRecord(
                reaction_code=r["reaction_code"],
                count=r["cnt"],
                user_ids=list(r["user_ids"] or []),
                user_names=[n for n in (r["user_names"] or []) if n],
                reacted_by_me=current_user_id in (r["user_ids"] or []),
            )
            for r in rows
        ]

    async def reaction_exists(
        self,
        connection: asyncpg.Connection,
        comment_id: str,
        user_id: str,
        reaction_code: str,
    ) -> bool:
        row = await connection.fetchrow(
            f"""
            SELECT 1 FROM {SCHEMA}."03_trx_comment_reactions"
            WHERE comment_id = $1::uuid AND user_id = $2::uuid AND reaction_code = $3
            """,
            comment_id, user_id, reaction_code,
        )
        return row is not None

    # ── Edit history ──────────────────────────────────────────────────────

    async def get_edit_history(
        self,
        connection: asyncpg.Connection,
        comment_id: str,
    ) -> list[CommentEditRecord]:
        rows = await connection.fetch(
            f"""
            SELECT id::text, comment_id::text, previous_content, edited_by::text, edited_at::text
            FROM {SCHEMA}."02_trx_comment_edits"
            WHERE comment_id = $1::uuid
            ORDER BY edited_at ASC
            """,
            comment_id,
        )
        return [_row_to_edit(r) for r in rows]

    # ── Batch comment counts ───────────────────────────────────────────────

    async def get_comment_counts_batch(
        self,
        connection: asyncpg.Connection,
        *,
        entity_type: str,
        entity_ids: list[str],
    ) -> dict[str, int]:
        """Return a mapping of entity_id → non-deleted top-level comment count.

        Handles up to 100 entity IDs in one query.
        """
        if not entity_ids:
            return {}
        placeholders = ", ".join(f"${i+2}::uuid" for i in range(len(entity_ids)))
        rows = await connection.fetch(
            f"""
            SELECT entity_id::text, COUNT(*)::int AS cnt
            FROM {SCHEMA}."01_fct_comments"
            WHERE entity_type = $1
              AND entity_id IN ({placeholders})
              AND parent_comment_id IS NULL
              AND is_deleted = FALSE
            GROUP BY entity_id
            """,
            entity_type, *entity_ids,
        )
        counts = {r["entity_id"]: r["cnt"] for r in rows}
        # Ensure all requested IDs are represented
        for eid in entity_ids:
            counts.setdefault(eid, 0)
        return counts

    # ── Mentions query ─────────────────────────────────────────────────────

    async def list_mentions(
        self,
        connection: asyncpg.Connection,
        *,
        user_id: str,
        tenant_key: str,
        limit: int = 25,
        cursor_created_at: str | None = None,
        cursor_id: str | None = None,
    ) -> tuple[list[CommentWithRepliesRecord], int]:
        """Return comments where the given user is in mention_user_ids."""
        count_row = await connection.fetchrow(
            f"""
            SELECT COUNT(*)::int AS total
            FROM {SCHEMA}."01_fct_comments"
            WHERE tenant_key = $1
              AND $2::uuid = ANY(mention_user_ids)
              AND is_deleted = FALSE
            """,
            tenant_key, user_id,
        )
        total = count_row["total"] if count_row else 0

        cursor_filter = ""
        cursor_values: list[object] = [tenant_key, user_id]
        idx = 3
        if cursor_created_at is not None and cursor_id is not None:
            cursor_filter = f"AND (c.created_at, c.id::text) < (${idx}::timestamptz, ${idx+1})"
            cursor_values.append(cursor_created_at)
            cursor_values.append(cursor_id)
            idx += 2

        rows = await connection.fetch(
            f"""
            SELECT
                c.id::text,
                c.tenant_key,
                c.entity_type,
                c.entity_id::text,
                c.parent_comment_id::text,
                c.author_user_id::text,
                c.content,
                c.is_edited,
                c.is_deleted,
                c.deleted_at::text,
                c.deleted_by::text,
                c.pinned,
                c.pinned_by::text,
                c.pinned_at::text,
                c.resolved,
                c.resolved_by::text,
                c.resolved_at::text,
                c.content_format,
                c.rendered_html,
                c.visibility,
                c.is_locked,
                c.locked_by::text,
                c.locked_at::text,
                c.mention_user_ids::text[],
                c.created_at::text,
                c.updated_at::text,
                0::int AS reply_count,
                adn.display_name AS author_display_name,
                ae.email         AS author_email
            FROM {SCHEMA}."01_fct_comments" c
            LEFT JOIN (
                SELECT p.user_id::text, p.property_value AS display_name
                FROM {AUTH_SCHEMA}."05_dtl_user_properties" p
                WHERE p.property_key = 'display_name'
            ) adn ON adn.user_id = c.author_user_id::text
            LEFT JOIN (
                SELECT p.user_id::text, p.property_value AS email
                FROM {AUTH_SCHEMA}."05_dtl_user_properties" p
                WHERE p.property_key = 'email'
            ) ae ON ae.user_id = c.author_user_id::text
            WHERE c.tenant_key = $1
              AND $2::uuid = ANY(c.mention_user_ids)
              AND c.is_deleted = FALSE
              {cursor_filter}
            ORDER BY c.created_at DESC, c.id
            LIMIT {limit}
            """,
            *cursor_values,
        )

        records = []
        for r in rows:
            detail = _row_to_comment_detail(r)
            records.append(
                CommentWithRepliesRecord(
                    id=detail.id,
                    tenant_key=detail.tenant_key,
                    entity_type=detail.entity_type,
                    entity_id=detail.entity_id,
                    parent_comment_id=detail.parent_comment_id,
                    author_user_id=detail.author_user_id,
                    content=detail.content,
                    is_edited=detail.is_edited,
                    is_deleted=detail.is_deleted,
                    deleted_at=detail.deleted_at,
                    deleted_by=detail.deleted_by,
                    pinned=detail.pinned,
                    pinned_by=detail.pinned_by,
                    pinned_at=detail.pinned_at,
                    resolved=detail.resolved,
                    resolved_by=detail.resolved_by,
                    resolved_at=detail.resolved_at,
                    content_format=detail.content_format,
                    rendered_html=detail.rendered_html,
                    visibility=detail.visibility,
                    is_locked=detail.is_locked,
                    locked_by=detail.locked_by,
                    locked_at=detail.locked_at,
                    mention_user_ids=detail.mention_user_ids,
                    reply_count=detail.reply_count,
                    created_at=detail.created_at,
                    updated_at=detail.updated_at,
                    author_display_name=detail.author_display_name,
                    author_email=detail.author_email,
                    replies=[],
                    reactions=[],
                    edit_history=[],
                )
            )
        return records, total

    # ── Unread / view tracking ─────────────────────────────────────────────

    async def get_last_viewed_at(
        self,
        connection: asyncpg.Connection,
        *,
        user_id: str,
        entity_type: str,
        entity_id: str,
    ) -> str | None:
        """Return the ISO timestamp of the user's last view, or None."""
        row = await connection.fetchrow(
            f"""
            SELECT last_viewed_at::text
            FROM {SCHEMA}."05_trx_comment_views"
            WHERE user_id = $1::uuid
              AND entity_type = $2
              AND entity_id = $3::uuid
            """,
            user_id, entity_type, entity_id,
        )
        return row["last_viewed_at"] if row else None

    async def get_unread_count(
        self,
        connection: asyncpg.Connection,
        *,
        user_id: str,
        entity_type: str,
        entity_id: str,
        last_viewed_at: str | None,
    ) -> int:
        """Count comments created after last_viewed_at (0 if never viewed)."""
        if last_viewed_at is None:
            # Never viewed — all non-deleted comments are "unread"
            row = await connection.fetchrow(
                f"""
                SELECT COUNT(*)::int AS cnt
                FROM {SCHEMA}."01_fct_comments"
                WHERE entity_type = $1
                  AND entity_id = $2::uuid
                  AND is_deleted = FALSE
                  AND author_user_id != $3::uuid
                """,
                entity_type, entity_id, user_id,
            )
        else:
            row = await connection.fetchrow(
                f"""
                SELECT COUNT(*)::int AS cnt
                FROM {SCHEMA}."01_fct_comments"
                WHERE entity_type = $1
                  AND entity_id = $2::uuid
                  AND is_deleted = FALSE
                  AND author_user_id != $3::uuid
                  AND created_at > $4::timestamptz
                """,
                entity_type, entity_id, user_id, last_viewed_at,
            )
        return row["cnt"] if row else 0

    async def upsert_comment_view(
        self,
        connection: asyncpg.Connection,
        *,
        view_id: str,
        user_id: str,
        entity_type: str,
        entity_id: str,
        now: object,
    ) -> str:
        """Upsert the last-viewed timestamp. Returns the new timestamp as text."""
        row = await connection.fetchrow(
            f"""
            INSERT INTO {SCHEMA}."05_trx_comment_views"
                (id, user_id, entity_type, entity_id, last_viewed_at)
            VALUES ($1::uuid, $2::uuid, $3, $4::uuid, $5)
            ON CONFLICT (user_id, entity_type, entity_id)
            DO UPDATE SET last_viewed_at = EXCLUDED.last_viewed_at
            RETURNING last_viewed_at::text
            """,
            view_id, user_id, entity_type, entity_id, now,
        )
        return row["last_viewed_at"]

    # ── Attachment linking ──────────────────────────────────────────────────

    async def link_attachments_to_comment(
        self,
        connection: asyncpg.Connection,
        comment_id: str,
        attachment_ids: list[str],
    ) -> None:
        """Link attachment IDs to a comment via the 06_lnk_comment_attachments table."""
        if not attachment_ids:
            return
        for idx, aid in enumerate(attachment_ids):
            await connection.execute(
                f"""
                INSERT INTO {SCHEMA}."06_lnk_comment_attachments"
                    (comment_id, attachment_id, sort_order)
                VALUES ($1::uuid, $2::uuid, $3)
                ON CONFLICT (comment_id, attachment_id) DO NOTHING
                """,
                comment_id, aid, idx,
            )

    async def get_comment_attachment_ids(
        self,
        connection: asyncpg.Connection,
        comment_id: str,
    ) -> list[str]:
        """Return attachment IDs linked to a single comment."""
        rows = await connection.fetch(
            f"""
            SELECT attachment_id::text
            FROM {SCHEMA}."06_lnk_comment_attachments"
            WHERE comment_id = $1::uuid
            ORDER BY sort_order
            """,
            comment_id,
        )
        return [r["attachment_id"] for r in rows]

    async def get_comment_attachment_ids_batch(
        self,
        connection: asyncpg.Connection,
        comment_ids: list[str],
    ) -> dict[str, list[str]]:
        """Return a mapping of comment_id -> list[attachment_id] for batch queries."""
        if not comment_ids:
            return {}
        placeholders = ", ".join(f"${i+1}::uuid" for i in range(len(comment_ids)))
        rows = await connection.fetch(
            f"""
            SELECT comment_id::text, attachment_id::text
            FROM {SCHEMA}."06_lnk_comment_attachments"
            WHERE comment_id IN ({placeholders})
            ORDER BY comment_id, sort_order
            """,
            *comment_ids,
        )
        result: dict[str, list[str]] = {}
        for r in rows:
            result.setdefault(r["comment_id"], []).append(r["attachment_id"])
        return result

    # ── User ID validation ─────────────────────────────────────────────────

    async def validate_user_ids(
        self,
        connection: asyncpg.Connection,
        user_ids: list[str],
    ) -> set[str]:
        """Return the subset of user_ids that exist in 03_auth_manage.03_fct_users."""
        if not user_ids:
            return set()
        rows = await connection.fetch(
            f"""
            SELECT id::text
            FROM {AUTH_SCHEMA}."03_fct_users"
            WHERE id = ANY($1::uuid[])
            """,
            user_ids,
        )
        return {r["id"] for r in rows}

    # ── GDPR — user-level operations ──────────────────────────────────────

    async def list_comments_by_user(
        self,
        connection: asyncpg.Connection,
        user_id: str,
        tenant_key: str,
    ) -> list[CommentRecord]:
        """List all non-deleted comments authored by a specific user."""
        rows = await connection.fetch(
            f"""
            SELECT
                id::text, tenant_key, entity_type, entity_id::text,
                parent_comment_id::text, author_user_id::text,
                content, is_edited, is_deleted,
                deleted_at::text, deleted_by::text,
                pinned, pinned_by::text, pinned_at::text,
                resolved, resolved_by::text, resolved_at::text,
                content_format, rendered_html, visibility, is_locked,
                locked_by::text, locked_at::text,
                mention_user_ids::text[],
                created_at::text, updated_at::text
            FROM {SCHEMA}."01_fct_comments"
            WHERE author_user_id = $1::uuid AND tenant_key = $2
              AND is_deleted = FALSE
            ORDER BY created_at DESC
            """,
            user_id, tenant_key,
        )
        return [_row_to_comment(r) for r in rows]

    async def anonymize_user_comments(
        self,
        connection: asyncpg.Connection,
        user_id: str,
        tenant_key: str,
    ) -> int:
        """Anonymize all comments by a user (GDPR right to be forgotten).

        Replaces content with '[content removed - GDPR]', clears mentions,
        but preserves the record for thread integrity.
        """
        result = await connection.execute(
            f"""
            UPDATE {SCHEMA}."01_fct_comments"
            SET content = '[content removed - GDPR]',
                rendered_html = NULL,
                mention_user_ids = '{{}}'::uuid[],
                is_edited = TRUE,
                updated_at = NOW()
            WHERE author_user_id = $1::uuid AND tenant_key = $2
              AND is_deleted = FALSE
            """,
            user_id, tenant_key,
        )
        return int(result.split()[-1])

    async def delete_user_reactions(
        self,
        connection: asyncpg.Connection,
        user_id: str,
    ) -> int:
        """Remove all reactions by a user."""
        result = await connection.execute(
            f"""
            DELETE FROM {SCHEMA}."03_trx_comment_reactions"
            WHERE user_id = $1::uuid
            """,
            user_id,
        )
        return int(result.split()[-1])

    async def remove_user_from_mentions(
        self,
        connection: asyncpg.Connection,
        user_id: str,
        tenant_key: str,
    ) -> None:
        """Remove a user from all mention arrays."""
        await connection.execute(
            f"""
            UPDATE {SCHEMA}."01_fct_comments"
            SET mention_user_ids = array_remove(mention_user_ids, $1::uuid)
            WHERE $1::uuid = ANY(mention_user_ids) AND tenant_key = $2
            """,
            user_id, tenant_key,
        )

    async def delete_user_views(
        self,
        connection: asyncpg.Connection,
        user_id: str,
    ) -> None:
        """Clear all comment view tracking for a user."""
        await connection.execute(
            f"""
            DELETE FROM {SCHEMA}."05_trx_comment_views"
            WHERE user_id = $1::uuid
            """,
            user_id,
        )

    # ── Domain audit ──────────────────────────────────────────────────────

    async def write_comment_audit(
        self,
        connection: asyncpg.Connection,
        *,
        event_id: str,
        comment_id: str,
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
            INSERT INTO {SCHEMA}."04_aud_comment_events" (
                id, comment_id, entity_type, entity_id,
                event_type, actor_user_id, tenant_key, metadata, created_at
            )
            VALUES (
                $1::uuid, $2::uuid, $3, $4::uuid,
                $5, $6::uuid, $7, $8::jsonb, $9
            )
            """,
            event_id, comment_id, entity_type, entity_id,
            event_type, actor_user_id, tenant_key,
            json.dumps(metadata), now,
        )

    # ── Admin operations ──────────────────────────────────────────────────

    async def list_comments_admin(
        self,
        connection: asyncpg.Connection,
        *,
        limit: int = 50,
        offset: int = 0,
        q: str | None = None,
        entity_type: str | None = None,
        is_deleted: bool | None = None,
        is_pinned: bool | None = None,
        resolved: bool | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> tuple[list[CommentRecord], int]:
        """Global comment list for admins with flexible filtering."""
        filters = []
        values = []
        idx = 1

        if q:
            filters.append(f"content ILIKE ${idx}")
            values.append(f"%{q}%")
            idx += 1
        if entity_type:
            filters.append(f"entity_type = ${idx}")
            values.append(entity_type)
            idx += 1
        if is_deleted is not None:
            filters.append(f"is_deleted = ${idx}")
            values.append(is_deleted)
            idx += 1
        if is_pinned is not None:
            filters.append(f"pinned = ${idx}")
            values.append(is_pinned)
            idx += 1
        if resolved is not None:
            filters.append(f"resolved = ${idx}")
            values.append(resolved)
            idx += 1
        if date_from:
            filters.append(f"created_at >= ${idx}::timestamptz")
            values.append(date_from)
            idx += 1
        if date_to:
            filters.append(f"created_at <= ${idx}::timestamptz")
            values.append(date_to)
            idx += 1

        where_clause = "WHERE " + " AND ".join(filters) if filters else ""

        count_row = await connection.fetchrow(
            f"SELECT COUNT(*)::int FROM {SCHEMA}.\"01_fct_comments\" {where_clause}",
            *values
        )
        total = count_row[0] if count_row else 0

        rows = await connection.fetch(
            f"""
            SELECT
                id::text, tenant_key, entity_type, entity_id::text,
                parent_comment_id::text, author_user_id::text,
                content, is_edited, is_deleted,
                deleted_at::text, deleted_by::text,
                pinned, pinned_by::text, pinned_at::text,
                resolved, resolved_by::text, resolved_at::text,
                content_format, rendered_html, visibility, is_locked,
                locked_by::text, locked_at::text,
                mention_user_ids::text[],
                created_at::text, updated_at::text
            FROM {SCHEMA}."01_fct_comments"
            {where_clause}
            ORDER BY created_at DESC
            LIMIT {limit} OFFSET {offset}
            """,
            *values
        )
        return [_row_to_comment(r) for r in rows], total

    async def get_admin_stats(self, connection: asyncpg.Connection) -> dict:
        """Fetch system-wide comment statistics."""
        stats = await connection.fetchrow(
            f"""
            SELECT
                COUNT(*)::int AS total,
                COUNT(*) FILTER (WHERE created_at >= CURRENT_DATE)::int AS today,
                COUNT(*) FILTER (WHERE is_deleted = TRUE)::int AS deleted,
                COUNT(*) FILTER (WHERE pinned = TRUE)::int AS pinned
            FROM {SCHEMA}."01_fct_comments"
            """
        )

        mention_rows = await connection.fetch(
            f"""
            WITH unnested_mentions AS (
                SELECT UNNEST(mention_user_ids) AS user_id
                FROM {SCHEMA}."01_fct_comments"
                WHERE is_deleted = FALSE
            ),
            author_display_names AS (
                SELECT p.user_id::text, p.property_value AS display_name
                FROM {AUTH_SCHEMA}."05_dtl_user_properties" p
                WHERE p.property_key = 'display_name'
            )
            SELECT
                m.user_id::text,
                adn.display_name,
                COUNT(*)::int AS mention_count
            FROM unnested_mentions m
            LEFT JOIN author_display_names adn ON adn.user_id = m.user_id::text
            GROUP BY m.user_id, adn.display_name
            ORDER BY mention_count DESC
            LIMIT 10
            """
        )

        return {
            "total": stats["total"],
            "today": stats["today"],
            "deleted": stats["deleted"],
            "pinned": stats["pinned"],
            "top_mentioned": [dict(r) for r in mention_rows]
        }

    async def undelete_comment(
        self,
        connection: asyncpg.Connection,
        comment_id: str,
        *,
        now: object,
    ) -> bool:
        """Restore a soft-deleted comment."""
        result = await connection.execute(
            f"""
            UPDATE {SCHEMA}."01_fct_comments"
            SET is_deleted = FALSE, deleted_at = NULL, deleted_by = NULL, updated_at = $2
            WHERE id = $1::uuid AND is_deleted = TRUE
            """,
            comment_id, now
        )
        return result != "UPDATE 0"

    async def hard_delete_comment(self, connection: asyncpg.Connection, comment_id: str) -> bool:
        """Permanently delete a comment and its related data."""
        # Clean up related data first (optional if CASCADE is used, but safer to be explicit)
        await connection.execute(f"DELETE FROM {SCHEMA}.\"02_trx_comment_edits\" WHERE comment_id = $1::uuid", comment_id)
        await connection.execute(f"DELETE FROM {SCHEMA}.\"03_trx_comment_reactions\" WHERE comment_id = $1::uuid", comment_id)
        await connection.execute(f"DELETE FROM {SCHEMA}.\"06_lnk_comment_attachments\" WHERE comment_id = $1::uuid", comment_id)

        result = await connection.execute(
            f"DELETE FROM {SCHEMA}.\"01_fct_comments\" WHERE id = $1::uuid",
            comment_id
        )
        return result != "DELETE 0"
