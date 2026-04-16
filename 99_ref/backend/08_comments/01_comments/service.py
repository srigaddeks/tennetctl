"""Business logic for the comments domain.

Architecture:
- All DB work goes through CommentRepository.
- All mutations are wrapped in ``self._database_pool.transaction()``.
- Cache keys follow the pattern ``comments:{entity_type}:{entity_id}:{page}``.
- Unified audit entries are written to ``03_auth_manage`` via AuditWriter.
- Domain-specific audit entries are written to ``08_comments.04_aud_comment_events``.
- Mention notifications are dispatched asynchronously after transaction commit.
"""

from __future__ import annotations

import html
import re
import uuid
from importlib import import_module

import asyncpg
from opentelemetry import metrics as otel_metrics

from .repository import CommentRepository
from .schemas import (
    AddReactionRequest,
    AdminCommentListResponse,
    CommentCountsResponse,
    CommentEditResponse,
    CommentHistoryResponse,
    CommentListResponse,
    CommentResponse,
    CommentStatsResponse,
    CommentWithRepliesResponse,
    CreateCommentRequest,
    MarkReadRequest,
    MarkReadResponse,
    MentionsListResponse,
    ReactionListResponse,
    ReactionSummaryResponse,
    TopMentionedUser,
    UpdateCommentRequest,
)

_database_module = import_module("backend.01_core.database")
_cache_module = import_module("backend.01_core.cache")
_logging_module = import_module("backend.01_core.logging_utils")
_telemetry_module = import_module("backend.01_core.telemetry")
_settings_module = import_module("backend.00_config.settings")
_errors_module = import_module("backend.01_core.errors")
_audit_module = import_module("backend.01_core.audit")
_time_module = import_module("backend.01_core.time_utils")
_constants_module = import_module("backend.08_comments.constants")
_auth_constants_module = import_module("backend.03_auth_manage.constants")
_access_scope_module = import_module("backend.07_tasks.access_scope")

Settings = _settings_module.Settings
DatabasePool = _database_module.DatabasePool
CacheManager = _cache_module.CacheManager
NullCacheManager = _cache_module.NullCacheManager
get_logger = _logging_module.get_logger
instrument_class_methods = _telemetry_module.instrument_class_methods
NotFoundError = _errors_module.NotFoundError
ValidationError = _errors_module.ValidationError
AuthorizationError = _errors_module.AuthorizationError
AuditEntry = _audit_module.AuditEntry
AuditWriter = _audit_module.AuditWriter
utc_now_sql = _time_module.utc_now_sql

CommentAuditEventType = _constants_module.CommentAuditEventType
CommentDomainEventType = _constants_module.CommentDomainEventType
VALID_ENTITY_TYPES = _constants_module.VALID_ENTITY_TYPES
VALID_REACTION_CODES = _constants_module.VALID_REACTION_CODES
CACHE_TTL_COMMENTS = _constants_module.CACHE_TTL_COMMENTS
MAX_MENTIONS_PER_COMMENT = _constants_module.MAX_MENTIONS_PER_COMMENT
VALID_CONTENT_FORMATS = _constants_module.VALID_CONTENT_FORMATS
VALID_VISIBILITY_OPTIONS = _constants_module.VALID_VISIBILITY_OPTIONS
AuditEventCategory = _auth_constants_module.AuditEventCategory

_perm_check_module = import_module("backend.03_auth_manage._permission_check")
require_permission = _perm_check_module.require_permission
assert_assignee_task_entity_access = _access_scope_module.assert_assignee_task_entity_access
is_assignee_portal_mode = _access_scope_module.is_assignee_portal_mode

# ---------------------------------------------------------------------------
# OTEL Metrics
# ---------------------------------------------------------------------------

_comment_meter = otel_metrics.get_meter("kcontrol.comments")

comment_created_counter = _comment_meter.create_counter(
    "comments.created",
    description="Number of comments created",
    unit="1",
)
comment_deleted_counter = _comment_meter.create_counter(
    "comments.deleted",
    description="Number of comments deleted",
    unit="1",
)
comment_edited_counter = _comment_meter.create_counter(
    "comments.edited",
    description="Number of comments edited",
    unit="1",
)
reaction_toggled_counter = _comment_meter.create_counter(
    "comments.reactions.toggled",
    description="Number of reactions toggled",
    unit="1",
)
mention_counter = _comment_meter.create_counter(
    "comments.mentions",
    description="Number of @mentions in comments",
    unit="1",
)

# Mention pattern: @[Display Name](uuid)
_MENTION_PATTERN = re.compile(r"@\[([^\]]+)\]\(([0-9a-fA-F-]{36})\)")

# Maximum entity IDs accepted by the counts endpoint
_MAX_COUNT_ENTITY_IDS = 100


def _extract_mention_ids(content: str) -> list[str]:
    """Extract user UUIDs from @[name](uuid) mention syntax."""
    return list(dict.fromkeys(m.group(2) for m in _MENTION_PATTERN.finditer(content)))


def _mask_deleted_content(c) -> str:
    """Return '[deleted]' for soft-deleted comments."""
    return "[deleted]" if c.is_deleted else c.content


def _comment_response(c, attachment_ids: list[str] | None = None) -> CommentResponse:
    return CommentResponse(
        id=c.id,
        tenant_key=c.tenant_key,
        entity_type=c.entity_type,
        entity_id=c.entity_id,
        parent_comment_id=c.parent_comment_id,
        author_user_id=c.author_user_id,
        content=_mask_deleted_content(c),
        content_format=getattr(c, "content_format", "markdown"),
        rendered_html=getattr(c, "rendered_html", None) if not c.is_deleted else None,
        visibility=getattr(c, "visibility", "external"),
        is_edited=c.is_edited,
        is_deleted=c.is_deleted,
        is_locked=getattr(c, "is_locked", False),
        locked_by=getattr(c, "locked_by", None),
        locked_at=getattr(c, "locked_at", None),
        deleted_at=c.deleted_at,
        deleted_by=c.deleted_by,
        pinned=c.pinned,
        pinned_by=c.pinned_by,
        pinned_at=c.pinned_at,
        resolved=c.resolved,
        resolved_by=c.resolved_by,
        resolved_at=c.resolved_at,
        mention_user_ids=c.mention_user_ids,
        reply_count=getattr(c, "reply_count", 0),
        attachment_ids=attachment_ids or [],
        created_at=c.created_at,
        updated_at=c.updated_at,
        author_display_name=getattr(c, "author_display_name", None),
        author_email=getattr(c, "author_email", None),
    )


def _comment_with_replies_response(c, attachment_ids: list[str] | None = None) -> CommentWithRepliesResponse:
    return CommentWithRepliesResponse(
        id=c.id,
        tenant_key=c.tenant_key,
        entity_type=c.entity_type,
        entity_id=c.entity_id,
        parent_comment_id=c.parent_comment_id,
        author_user_id=c.author_user_id,
        content=_mask_deleted_content(c),
        content_format=c.content_format,
        rendered_html=c.rendered_html if not c.is_deleted else None,
        visibility=c.visibility,
        is_edited=c.is_edited,
        is_deleted=c.is_deleted,
        is_locked=c.is_locked,
        locked_by=c.locked_by,
        locked_at=c.locked_at,
        deleted_at=c.deleted_at,
        deleted_by=c.deleted_by,
        pinned=c.pinned,
        pinned_by=c.pinned_by,
        pinned_at=c.pinned_at,
        resolved=c.resolved,
        resolved_by=c.resolved_by,
        resolved_at=c.resolved_at,
        mention_user_ids=c.mention_user_ids,
        reply_count=c.reply_count,
        attachment_ids=attachment_ids or [],
        created_at=c.created_at,
        updated_at=c.updated_at,
        author_display_name=c.author_display_name,
        author_email=c.author_email,
        replies=[_comment_response(r) for r in c.replies],
        reactions=[
            ReactionSummaryResponse(
                reaction_code=rx.reaction_code,
                count=rx.count,
                user_ids=rx.user_ids,
                user_names=rx.user_names,
                reacted_by_me=rx.reacted_by_me,
            )
            for rx in c.reactions
        ],
        edit_history=[
            CommentEditResponse(
                id=e.id,
                comment_id=e.comment_id,
                previous_content=e.previous_content,
                edited_by=e.edited_by,
                edited_at=e.edited_at,
            )
            for e in c.edit_history
        ],
    )


@instrument_class_methods(
    namespace="comments.service",
    logger_name="backend.comments.instrumentation",
)
class CommentService:
    def __init__(
        self,
        *,
        settings: Settings,
        database_pool: DatabasePool,
        cache: CacheManager | NullCacheManager,
    ) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._cache = cache
        self._repository = CommentRepository()
        # Unified audit writer — comments use 03_auth_manage schema for audit
        self._audit_writer = AuditWriter(schema_name="03_auth_manage")
        self._logger = get_logger("backend.comments")

    def _cache_key(self, entity_type: str, entity_id: str, page: int = 1) -> str:
        return f"comments:{entity_type}:{entity_id}:{page}"

    async def _invalidate_entity_cache(self, entity_type: str, entity_id: str) -> None:
        await self._cache.delete_pattern(f"comments:{entity_type}:{entity_id}:*")

    _EXTERNAL_GRC_ROLES = frozenset({"grc_lead_auditor", "grc_staff_auditor", "grc_vendor"})

    async def _enrich_grc_roles(self, items: list) -> None:
        """Batch-resolve GRC roles for comment authors and set external badge.

        Mutates items in place, setting author_grc_role_code and author_is_external.

        Args:
            items: List of CommentResponse or CommentWithRepliesResponse.
        """
        # Collect all unique author user IDs (including replies)
        author_ids: set[str] = set()
        for item in items:
            author_ids.add(item.author_user_id)
            for reply in getattr(item, "replies", []):
                author_ids.add(reply.author_user_id)

        if not author_ids:
            return

        # Batch fetch GRC roles from DB
        try:
            async with self._database_pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT user_id::text, grc_role_code
                    FROM "03_auth_manage"."47_lnk_grc_role_assignments"
                    WHERE user_id = ANY($1::uuid[]) AND revoked_at IS NULL
                    """,
                    list(author_ids),
                )
            role_map = {r["user_id"]: r["grc_role_code"] for r in rows}
        except Exception:
            return  # Non-critical — don't break comment listing

        # Apply to items
        for item in items:
            role = role_map.get(item.author_user_id)
            if role:
                item.author_grc_role_code = role
                item.author_is_external = role in self._EXTERNAL_GRC_ROLES
            for reply in getattr(item, "replies", []):
                r_role = role_map.get(reply.author_user_id)
                if r_role:
                    reply.author_grc_role_code = r_role
                    reply.author_is_external = r_role in self._EXTERNAL_GRC_ROLES

    async def _assert_entity_access_for_portal(
        self,
        conn,
        *,
        portal_mode: str | None,
        user_id: str,
        entity_type: str,
        entity_id: str,
    ) -> None:
        await assert_assignee_task_entity_access(
            conn,
            portal_mode=portal_mode,
            user_id=user_id,
            entity_type=entity_type,
            entity_id=entity_id,
        )

    # ── Markdown rendering & XSS sanitization ────────────────────────────

    def _render_markdown(self, content: str) -> str:
        """Convert markdown to safe HTML. Sanitize all output."""
        # First, HTML-escape the input to prevent injection
        safe = html.escape(content)

        # Then apply markdown transformations on the escaped content
        # Code blocks (triple backtick)
        safe = re.sub(
            r'```(\w*)\n(.*?)```',
            lambda m: f'<pre><code class="language-{html.escape(m.group(1))}">{m.group(2)}</code></pre>',
            safe, flags=re.DOTALL,
        )
        # Inline code
        safe = re.sub(r'`([^`]+)`', r'<code>\1</code>', safe)
        # Bold
        safe = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', safe)
        # Italic
        safe = re.sub(r'\*(.+?)\*', r'<em>\1</em>', safe)
        # Strikethrough
        safe = re.sub(r'~~(.+?)~~', r'<del>\1</del>', safe)
        # Links (but sanitize href - only allow http/https)
        safe = re.sub(
            r'\[([^\]]+)\]\((https?://[^\)]+)\)',
            r'<a href="\2" rel="noopener noreferrer" target="_blank">\1</a>',
            safe,
        )
        # Headers (h1-h3)
        safe = re.sub(r'^### (.+)$', r'<h3>\1</h3>', safe, flags=re.MULTILINE)
        safe = re.sub(r'^## (.+)$', r'<h2>\1</h2>', safe, flags=re.MULTILINE)
        safe = re.sub(r'^# (.+)$', r'<h1>\1</h1>', safe, flags=re.MULTILINE)
        # Unordered lists
        safe = re.sub(r'^[*-] (.+)$', r'<li>\1</li>', safe, flags=re.MULTILINE)
        # Blockquotes
        safe = re.sub(r'^&gt; (.+)$', r'<blockquote>\1</blockquote>', safe, flags=re.MULTILINE)
        # Line breaks
        safe = safe.replace('\n\n', '</p><p>').replace('\n', '<br/>')
        safe = f'<p>{safe}</p>'

        return safe

    def _sanitize_content(self, content: str) -> str:
        """Strip dangerous HTML patterns from content to prevent XSS.

        Content is stored as-is but rendered_html is sanitized.
        Users should use markdown, not raw HTML.
        """
        sanitized = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
        sanitized = re.sub(r'<iframe[^>]*>.*?</iframe>', '', sanitized, flags=re.DOTALL | re.IGNORECASE)
        sanitized = re.sub(r'on\w+\s*=\s*["\'][^"\']*["\']', '', sanitized, flags=re.IGNORECASE)
        sanitized = re.sub(r'javascript:', '', sanitized, flags=re.IGNORECASE)
        return sanitized

    def _render_and_sanitize(self, content: str, content_format: str) -> tuple[str, str | None]:
        """Sanitize content and optionally render markdown to HTML.

        Returns (sanitized_content, rendered_html).
        """
        sanitized = self._sanitize_content(content)
        rendered_html = None
        if content_format == "markdown":
            rendered_html = self._render_markdown(sanitized)
        return sanitized, rendered_html

    # ── List ──────────────────────────────────────────────────────────────

    async def list_comments(
        self,
        *,
        user_id: str,
        tenant_key: str,
        portal_mode: str | None = None,
        entity_type: str,
        entity_id: str,
        include_replies: bool = True,
        page: int = 1,
        per_page: int = 25,
        cursor_created_at: str | None = None,
        cursor_id: str | None = None,
        visibility: str | None = None,
    ) -> CommentListResponse:
        if entity_type not in VALID_ENTITY_TYPES:
            raise ValidationError(
                f"Invalid entity_type '{entity_type}'. Must be one of: {sorted(VALID_ENTITY_TYPES)}"
            )

        # Determine effective visibility filter based on permissions
        effective_visibility = visibility
        if effective_visibility is None:
            async with self._database_pool.acquire() as conn:
                try:
                    await require_permission(conn, user_id, "comments.manage")
                    effective_visibility = None  # show all (internal + external)
                except Exception:
                    effective_visibility = "external"  # only show external

        cache_key = self._cache_key(entity_type, entity_id, page)
        if cursor_created_at is None and effective_visibility != "internal":
            # Only cache non-cursor requests (first page) for non-internal views
            cached = await self._cache.get(cache_key)
            if cached is not None:
                return CommentListResponse.model_validate_json(cached)

        async with self._database_pool.acquire() as conn:
            await self._assert_entity_access_for_portal(
                conn,
                portal_mode=portal_mode,
                user_id=user_id,
                entity_type=entity_type,
                entity_id=entity_id,
            )
            comments, total = await self._repository.list_comments(
                conn,
                tenant_key=tenant_key,
                entity_type=entity_type,
                entity_id=entity_id,
                current_user_id=user_id,
                include_replies=include_replies,
                limit=per_page,
                cursor_created_at=cursor_created_at,
                cursor_id=cursor_id,
                visibility=effective_visibility,
            )
            # Compute unread count using last-viewed timestamp
            last_viewed_at = await self._repository.get_last_viewed_at(
                conn,
                user_id=user_id,
                entity_type=entity_type,
                entity_id=entity_id,
            )
            unread_count = await self._repository.get_unread_count(
                conn,
                user_id=user_id,
                entity_type=entity_type,
                entity_id=entity_id,
                last_viewed_at=last_viewed_at,
            )

        items = [_comment_with_replies_response(c) for c in comments]

        # Enrich with GRC role info for external auditor badges
        await self._enrich_grc_roles(items)

        # Compute next cursor from last item
        next_cursor: str | None = None
        if len(comments) == per_page and comments:
            last = comments[-1]
            next_cursor = f"{last.created_at}_{last.id}"

        result = CommentListResponse(
            items=items,
            total=total,
            next_cursor=next_cursor,
            unread_count=unread_count,
        )

        if cursor_created_at is None:
            await self._cache.set(cache_key, result.model_dump_json(), CACHE_TTL_COMMENTS)

        return result

    # ── Get single ────────────────────────────────────────────────────────

    async def get_comment(
        self,
        *,
        user_id: str,
        comment_id: str,
        portal_mode: str | None = None,
    ) -> CommentWithRepliesResponse:
        async with self._database_pool.acquire() as conn:
            record = await self._repository.get_comment_with_replies(
                conn, comment_id, current_user_id=user_id
            )
            if record is not None:
                await self._assert_entity_access_for_portal(
                    conn,
                    portal_mode=portal_mode,
                    user_id=user_id,
                    entity_type=record.entity_type,
                    entity_id=record.entity_id,
                )
        if record is None:
            raise NotFoundError(f"Comment not found.")
        return _comment_with_replies_response(record)

    # ── Create ────────────────────────────────────────────────────────────

    async def create_comment(
        self,
        *,
        user_id: str,
        tenant_key: str,
        request: CreateCommentRequest,
        portal_mode: str | None = None,
    ) -> CommentWithRepliesResponse:
        if request.entity_type not in VALID_ENTITY_TYPES:
            raise ValidationError(
                f"Invalid entity_type '{request.entity_type}'. "
                f"Must be one of: {sorted(VALID_ENTITY_TYPES)}"
            )

        now = utc_now_sql()
        comment_id = str(uuid.uuid4())

        # Sanitize content and render markdown
        content_format = getattr(request, "content_format", "markdown")
        visibility = getattr(request, "visibility", "external")
        attachment_ids = getattr(request, "attachment_ids", [])

        sanitized_content, rendered_html = self._render_and_sanitize(
            request.content, content_format
        )

        mention_ids = _extract_mention_ids(sanitized_content)

        if len(mention_ids) > MAX_MENTIONS_PER_COMMENT:
            raise ValidationError(
                f"Maximum {MAX_MENTIONS_PER_COMMENT} mentions per comment."
            )

        async with self._database_pool.transaction() as conn:
            await self._assert_entity_access_for_portal(
                conn,
                portal_mode=portal_mode,
                user_id=user_id,
                entity_type=request.entity_type,
                entity_id=request.entity_id,
            )
            # Internal visibility requires comments.manage permission
            if visibility == "internal":
                try:
                    await require_permission(conn, user_id, "comments.manage")
                except Exception:
                    raise AuthorizationError(
                        "Creating internal comments requires the comments.manage permission."
                    )

            # Validate that all mentioned user IDs are real users
            if mention_ids:
                valid_ids = await self._repository.validate_user_ids(conn, mention_ids)
                invalid_ids = set(mention_ids) - valid_ids
                if invalid_ids:
                    raise ValidationError(
                        f"Invalid user IDs in mentions: {sorted(invalid_ids)}"
                    )
            # Validate parent_comment_id if replying
            if request.parent_comment_id is not None:
                parent = await self._repository.get_comment_by_id(
                    conn, request.parent_comment_id
                )
                if parent is None:
                    raise NotFoundError("Parent comment not found.")
                if parent.entity_type != request.entity_type or parent.entity_id != request.entity_id:
                    raise ValidationError(
                        "Parent comment does not belong to the same entity."
                    )
                if parent.parent_comment_id is not None:
                    raise ValidationError(
                        "Cannot reply to a reply — maximum one level of nesting is allowed."
                    )

            try:
                comment = await self._repository.create_comment(
                    conn,
                    comment_id=comment_id,
                    tenant_key=tenant_key,
                    entity_type=request.entity_type,
                    entity_id=request.entity_id,
                    parent_comment_id=request.parent_comment_id,
                    author_user_id=user_id,
                    content=sanitized_content,
                    content_format=content_format,
                    rendered_html=rendered_html,
                    visibility=visibility,
                    mention_user_ids=mention_ids,
                    now=now,
                )
            except asyncpg.CheckViolationError as exc:
                if "entity_type" in str(exc):
                    raise ValidationError(
                        f"Comment entity type '{request.entity_type}' is not enabled in the current database schema."
                    ) from exc
                raise

            # Link attachments
            if attachment_ids:
                await self._repository.link_attachments_to_comment(
                    conn, comment_id, attachment_ids
                )

            # Domain audit
            await self._repository.write_comment_audit(
                conn,
                event_id=str(uuid.uuid4()),
                comment_id=comment_id,
                entity_type=request.entity_type,
                entity_id=request.entity_id,
                event_type=CommentDomainEventType.CREATED.value,
                actor_user_id=user_id,
                tenant_key=tenant_key,
                metadata={
                    "parent_comment_id": request.parent_comment_id,
                    "mention_count": len(mention_ids),
                    "content_length": len(request.content),
                },
                now=now,
            )

            # Unified audit
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="comment",
                    entity_id=comment_id,
                    event_type=CommentAuditEventType.COMMENT_CREATED.value,
                    event_category=AuditEventCategory.COMMENT.value,
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={
                        "entity_type": request.entity_type,
                        "entity_id": request.entity_id,
                        "parent_comment_id": request.parent_comment_id or "",
                    },
                ),
            )

        await self._invalidate_entity_cache(request.entity_type, request.entity_id)

        # OTEL metrics
        comment_created_counter.add(1, {"entity_type": request.entity_type, "tenant_key": tenant_key})
        if mention_ids:
            mention_counter.add(len(mention_ids), {"entity_type": request.entity_type, "tenant_key": tenant_key})

        # Send mention notifications outside the transaction — failure is non-fatal
        if mention_ids:
            await self._send_mention_notifications(
                comment_id=comment_id,
                tenant_key=tenant_key,
                entity_type=request.entity_type,
                entity_id=request.entity_id,
                author_user_id=user_id,
                mention_user_ids=mention_ids,
                comment_body=request.content or "",
            )

        # Re-fetch with full joins
        async with self._database_pool.acquire() as conn:
            record = await self._repository.get_comment_with_replies(
                conn, comment_id, current_user_id=user_id
            )
        return _comment_with_replies_response(record)

    # ── Mention notifications ──────────────────────────────────────────────

    async def _send_mention_notifications(
        self,
        *,
        comment_id: str,
        tenant_key: str,
        entity_type: str,
        entity_id: str,
        author_user_id: str,
        mention_user_ids: list[str],
        comment_body: str = "",
    ) -> None:
        """Enqueue notifications for each @-mentioned user.

        Failures are logged but do not propagate — notifications are best-effort.
        The notification system may not be configured in all environments; we
        guard with ``notification_enabled`` before attempting to use the dispatcher.
        """
        if not self._settings.notification_enabled:
            return
        if not mention_user_ids:
            return

        try:
            _dispatcher_module = import_module(
                "backend.04_notifications.02_dispatcher.dispatcher"
            )
            NotificationDispatcher = _dispatcher_module.NotificationDispatcher
            dispatcher = NotificationDispatcher(
                database_pool=self._database_pool,
                settings=self._settings,
            )
            import asyncio as _asyncio

            _base_url = (
                getattr(self._settings, "notification_tracking_base_url", "") or
                getattr(self._settings, "platform_base_url", "") or ""
            ).rstrip("/")
            _entity_url = f"{_base_url}/{entity_type}s/{entity_id}" if _base_url else ""

            # Strip markdown/mentions from comment body for the email snippet
            _plain_body = re.sub(r"@\w+", "", comment_body).strip()[:300]

            for mentioned_user_id in mention_user_ids:
                if mentioned_user_id == author_user_id:
                    # Do not notify users about their own mentions
                    continue
                _asyncio.create_task(dispatcher.dispatch_direct(
                    AuditEntry(
                        id=str(uuid.uuid4()),
                        tenant_key=tenant_key,
                        entity_type="comment",
                        entity_id=comment_id,
                        event_type="comment_mention",
                        event_category="comment",
                        occurred_at=utc_now_sql(),
                        actor_id=author_user_id,
                        actor_type="user",
                        properties={
                            "mentioned_user_id": mentioned_user_id,
                            "mention.entity_type": entity_type,
                            "mention.entity_url": _entity_url,
                            "mention.comment_body": _plain_body,
                        },
                    ),
                    target_user_id=mentioned_user_id,
                    template_code="comment_mention_email",
                    notification_type_code="comment_mention",
                ))
        except Exception as exc:
            self._logger.warning(
                "mention_notification_failed",
                extra={
                    "action": "comments.mention_notifications",
                    "outcome": "error",
                    "comment_id": comment_id,
                    "mention_count": len(mention_user_ids),
                    "error": str(exc),
                },
            )

    # ── Edit ──────────────────────────────────────────────────────────────

    async def update_comment(
        self,
        *,
        user_id: str,
        comment_id: str,
        request: UpdateCommentRequest,
        portal_mode: str | None = None,
    ) -> CommentWithRepliesResponse:
        now = utc_now_sql()

        async with self._database_pool.transaction() as conn:
            existing = await self._repository.get_comment_by_id(conn, comment_id)
            if existing is None:
                raise NotFoundError("Comment not found.")
            await self._assert_entity_access_for_portal(
                conn,
                portal_mode=portal_mode,
                user_id=user_id,
                entity_type=existing.entity_type,
                entity_id=existing.entity_id,
            )
            if existing.is_deleted:
                raise ValidationError("Cannot edit a deleted comment.")
            if existing.author_user_id != user_id:
                raise AuthorizationError("Only the comment author can edit this comment.")

            # Save previous content to history
            await self._repository.record_edit_history(
                conn,
                edit_id=str(uuid.uuid4()),
                comment_id=comment_id,
                previous_content=existing.content,
                edited_by=user_id,
                now=now,
            )

            # Sanitize and re-render markdown
            sanitized_content, rendered_html = self._render_and_sanitize(
                request.content, existing.content_format
            )

            mention_ids = _extract_mention_ids(sanitized_content)
            updated = await self._repository.update_comment_content(
                conn,
                comment_id,
                content=sanitized_content,
                rendered_html=rendered_html,
                mention_user_ids=mention_ids,
                now=now,
            )
            if updated is None:
                raise NotFoundError("Comment not found.")

            await self._repository.write_comment_audit(
                conn,
                event_id=str(uuid.uuid4()),
                comment_id=comment_id,
                entity_type=existing.entity_type,
                entity_id=existing.entity_id,
                event_type=CommentDomainEventType.EDITED.value,
                actor_user_id=user_id,
                tenant_key=existing.tenant_key,
                metadata={"content_length": len(request.content)},
                now=now,
            )
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=existing.tenant_key,
                    entity_type="comment",
                    entity_id=comment_id,
                    event_type=CommentAuditEventType.COMMENT_EDITED.value,
                    event_category=AuditEventCategory.COMMENT.value,
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={
                        "entity_type": existing.entity_type,
                        "entity_id": existing.entity_id,
                    },
                ),
            )

        await self._invalidate_entity_cache(existing.entity_type, existing.entity_id)

        # OTEL metrics
        comment_edited_counter.add(1, {"entity_type": existing.entity_type, "tenant_key": existing.tenant_key})
        new_mention_ids = _extract_mention_ids(request.content)
        if new_mention_ids:
            mention_counter.add(len(new_mention_ids), {"entity_type": existing.entity_type, "tenant_key": existing.tenant_key})

        async with self._database_pool.acquire() as conn:
            record = await self._repository.get_comment_with_replies(
                conn, comment_id, current_user_id=user_id
            )
        return _comment_with_replies_response(record)

    # ── Delete (soft) ─────────────────────────────────────────────────────

    async def delete_comment(
        self,
        *,
        user_id: str,
        comment_id: str,
        is_admin: bool = False,
        portal_mode: str | None = None,
    ) -> None:
        now = utc_now_sql()

        async with self._database_pool.transaction() as conn:
            existing = await self._repository.get_comment_by_id(conn, comment_id)
            if existing is None:
                raise NotFoundError("Comment not found.")
            await self._assert_entity_access_for_portal(
                conn,
                portal_mode=portal_mode,
                user_id=user_id,
                entity_type=existing.entity_type,
                entity_id=existing.entity_id,
            )
            if existing.is_deleted:
                raise ValidationError("Comment has already been deleted.")
            if not is_admin and existing.author_user_id != user_id:
                raise AuthorizationError(
                    "Only the comment author or an admin can delete this comment."
                )

            deleted = await self._repository.soft_delete_comment(
                conn, comment_id, deleted_by=user_id, now=now
            )
            if not deleted:
                raise NotFoundError("Comment not found.")

            await self._repository.write_comment_audit(
                conn,
                event_id=str(uuid.uuid4()),
                comment_id=comment_id,
                entity_type=existing.entity_type,
                entity_id=existing.entity_id,
                event_type=CommentDomainEventType.DELETED.value,
                actor_user_id=user_id,
                tenant_key=existing.tenant_key,
                metadata={"deleted_by_admin": is_admin},
                now=now,
            )
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=existing.tenant_key,
                    entity_type="comment",
                    entity_id=comment_id,
                    event_type=CommentAuditEventType.COMMENT_DELETED.value,
                    event_category=AuditEventCategory.COMMENT.value,
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={
                        "entity_type": existing.entity_type,
                        "entity_id": existing.entity_id,
                        "deleted_by_admin": str(is_admin),
                    },
                ),
            )

        await self._invalidate_entity_cache(existing.entity_type, existing.entity_id)

        # OTEL metrics
        comment_deleted_counter.add(1, {"entity_type": existing.entity_type, "tenant_key": existing.tenant_key})

    # ── Pin ───────────────────────────────────────────────────────────────

    async def pin_comment(
        self,
        *,
        user_id: str,
        comment_id: str,
        portal_mode: str | None = None,
    ) -> CommentWithRepliesResponse:
        now = utc_now_sql()

        async with self._database_pool.transaction() as conn:
            existing = await self._repository.get_comment_by_id(conn, comment_id)
            if existing is None:
                raise NotFoundError("Comment not found.")
            await self._assert_entity_access_for_portal(
                conn,
                portal_mode=portal_mode,
                user_id=user_id,
                entity_type=existing.entity_type,
                entity_id=existing.entity_id,
            )
            if existing.is_deleted:
                raise ValidationError("Cannot pin a deleted comment.")

            pinned = await self._repository.pin_comment(
                conn, comment_id, pinned_by=user_id, now=now
            )
            if not pinned:
                raise ValidationError("Comment is already pinned.")

            await self._repository.write_comment_audit(
                conn,
                event_id=str(uuid.uuid4()),
                comment_id=comment_id,
                entity_type=existing.entity_type,
                entity_id=existing.entity_id,
                event_type=CommentDomainEventType.PINNED.value,
                actor_user_id=user_id,
                tenant_key=existing.tenant_key,
                metadata={},
                now=now,
            )
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=existing.tenant_key,
                    entity_type="comment",
                    entity_id=comment_id,
                    event_type=CommentAuditEventType.COMMENT_PINNED.value,
                    event_category=AuditEventCategory.COMMENT.value,
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={"entity_type": existing.entity_type, "entity_id": existing.entity_id},
                ),
            )

        await self._invalidate_entity_cache(existing.entity_type, existing.entity_id)

        async with self._database_pool.acquire() as conn:
            record = await self._repository.get_comment_with_replies(
                conn, comment_id, current_user_id=user_id
            )
        return _comment_with_replies_response(record)

    async def unpin_comment(
        self,
        *,
        user_id: str,
        comment_id: str,
        portal_mode: str | None = None,
    ) -> CommentWithRepliesResponse:
        now = utc_now_sql()

        async with self._database_pool.transaction() as conn:
            existing = await self._repository.get_comment_by_id(conn, comment_id)
            if existing is None:
                raise NotFoundError("Comment not found.")
            await self._assert_entity_access_for_portal(
                conn,
                portal_mode=portal_mode,
                user_id=user_id,
                entity_type=existing.entity_type,
                entity_id=existing.entity_id,
            )

            unpinned = await self._repository.unpin_comment(conn, comment_id, now=now)
            if not unpinned:
                raise ValidationError("Comment is not currently pinned.")

            await self._repository.write_comment_audit(
                conn,
                event_id=str(uuid.uuid4()),
                comment_id=comment_id,
                entity_type=existing.entity_type,
                entity_id=existing.entity_id,
                event_type=CommentDomainEventType.UNPINNED.value,
                actor_user_id=user_id,
                tenant_key=existing.tenant_key,
                metadata={},
                now=now,
            )
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=existing.tenant_key,
                    entity_type="comment",
                    entity_id=comment_id,
                    event_type=CommentAuditEventType.COMMENT_UNPINNED.value,
                    event_category=AuditEventCategory.COMMENT.value,
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={"entity_type": existing.entity_type, "entity_id": existing.entity_id},
                ),
            )

        await self._invalidate_entity_cache(existing.entity_type, existing.entity_id)

        async with self._database_pool.acquire() as conn:
            record = await self._repository.get_comment_with_replies(
                conn, comment_id, current_user_id=user_id
            )
        return _comment_with_replies_response(record)

    # ── Resolve ───────────────────────────────────────────────────────────

    async def resolve_comment(
        self,
        *,
        user_id: str,
        comment_id: str,
        portal_mode: str | None = None,
    ) -> CommentWithRepliesResponse:
        now = utc_now_sql()

        async with self._database_pool.transaction() as conn:
            existing = await self._repository.get_comment_by_id(conn, comment_id)
            if existing is None:
                raise NotFoundError("Comment not found.")
            await self._assert_entity_access_for_portal(
                conn,
                portal_mode=portal_mode,
                user_id=user_id,
                entity_type=existing.entity_type,
                entity_id=existing.entity_id,
            )
            if existing.is_deleted:
                raise ValidationError("Cannot resolve a deleted comment.")

            resolved = await self._repository.resolve_comment(
                conn, comment_id, resolved_by=user_id, now=now
            )
            if not resolved:
                raise ValidationError("Comment is already resolved.")

            await self._repository.write_comment_audit(
                conn,
                event_id=str(uuid.uuid4()),
                comment_id=comment_id,
                entity_type=existing.entity_type,
                entity_id=existing.entity_id,
                event_type=CommentDomainEventType.RESOLVED.value,
                actor_user_id=user_id,
                tenant_key=existing.tenant_key,
                metadata={},
                now=now,
            )
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=existing.tenant_key,
                    entity_type="comment",
                    entity_id=comment_id,
                    event_type=CommentAuditEventType.COMMENT_RESOLVED.value,
                    event_category=AuditEventCategory.COMMENT.value,
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={"entity_type": existing.entity_type, "entity_id": existing.entity_id},
                ),
            )

        await self._invalidate_entity_cache(existing.entity_type, existing.entity_id)

        async with self._database_pool.acquire() as conn:
            record = await self._repository.get_comment_with_replies(
                conn, comment_id, current_user_id=user_id
            )
        return _comment_with_replies_response(record)

    async def unresolve_comment(
        self,
        *,
        user_id: str,
        comment_id: str,
        portal_mode: str | None = None,
    ) -> CommentWithRepliesResponse:
        now = utc_now_sql()

        async with self._database_pool.transaction() as conn:
            existing = await self._repository.get_comment_by_id(conn, comment_id)
            if existing is None:
                raise NotFoundError("Comment not found.")
            await self._assert_entity_access_for_portal(
                conn,
                portal_mode=portal_mode,
                user_id=user_id,
                entity_type=existing.entity_type,
                entity_id=existing.entity_id,
            )

            unresolved = await self._repository.unresolve_comment(conn, comment_id, now=now)
            if not unresolved:
                raise ValidationError("Comment is not currently resolved.")

            await self._repository.write_comment_audit(
                conn,
                event_id=str(uuid.uuid4()),
                comment_id=comment_id,
                entity_type=existing.entity_type,
                entity_id=existing.entity_id,
                event_type=CommentDomainEventType.UNRESOLVED.value,
                actor_user_id=user_id,
                tenant_key=existing.tenant_key,
                metadata={},
                now=now,
            )
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=existing.tenant_key,
                    entity_type="comment",
                    entity_id=comment_id,
                    event_type=CommentAuditEventType.COMMENT_UNRESOLVED.value,
                    event_category=AuditEventCategory.COMMENT.value,
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={"entity_type": existing.entity_type, "entity_id": existing.entity_id},
                ),
            )

        await self._invalidate_entity_cache(existing.entity_type, existing.entity_id)

        async with self._database_pool.acquire() as conn:
            record = await self._repository.get_comment_with_replies(
                conn, comment_id, current_user_id=user_id
            )
        return _comment_with_replies_response(record)

    # ── Reactions ─────────────────────────────────────────────────────────

    async def toggle_reaction(
        self,
        *,
        user_id: str,
        comment_id: str,
        request: AddReactionRequest,
        portal_mode: str | None = None,
    ) -> ReactionListResponse:
        if request.reaction_code not in VALID_REACTION_CODES:
            raise ValidationError(
                f"Invalid reaction code. Must be one of: {sorted(VALID_REACTION_CODES)}"
            )

        now = utc_now_sql()

        async with self._database_pool.transaction() as conn:
            existing = await self._repository.get_comment_by_id(conn, comment_id)
            if existing is None:
                raise NotFoundError("Comment not found.")
            await self._assert_entity_access_for_portal(
                conn,
                portal_mode=portal_mode,
                user_id=user_id,
                entity_type=existing.entity_type,
                entity_id=existing.entity_id,
            )
            if existing.is_deleted:
                raise ValidationError("Cannot react to a deleted comment.")

            already_reacted = await self._repository.reaction_exists(
                conn, comment_id, user_id, request.reaction_code
            )

            if already_reacted:
                await self._repository.remove_reaction(
                    conn, comment_id, user_id, request.reaction_code
                )
                event_type = CommentDomainEventType.REACTION_REMOVED.value
                audit_event = CommentAuditEventType.REACTION_REMOVED.value
            else:
                await self._repository.add_reaction(
                    conn,
                    reaction_id=str(uuid.uuid4()),
                    comment_id=comment_id,
                    user_id=user_id,
                    reaction_code=request.reaction_code,
                    now=now,
                )
                event_type = CommentDomainEventType.REACTION_ADDED.value
                audit_event = CommentAuditEventType.REACTION_ADDED.value

            await self._repository.write_comment_audit(
                conn,
                event_id=str(uuid.uuid4()),
                comment_id=comment_id,
                entity_type=existing.entity_type,
                entity_id=existing.entity_id,
                event_type=event_type,
                actor_user_id=user_id,
                tenant_key=existing.tenant_key,
                metadata={"reaction_code": request.reaction_code},
                now=now,
            )
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=existing.tenant_key,
                    entity_type="comment",
                    entity_id=comment_id,
                    event_type=audit_event,
                    event_category=AuditEventCategory.COMMENT.value,
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={"reaction_code": request.reaction_code},
                ),
            )

        await self._invalidate_entity_cache(existing.entity_type, existing.entity_id)

        # OTEL metrics
        action = "remove" if already_reacted else "add"
        reaction_toggled_counter.add(1, {"reaction_code": request.reaction_code, "action": action})

        async with self._database_pool.acquire() as conn:
            reactions = await self._repository.get_reactions_for_comment(
                conn, comment_id, current_user_id=user_id
            )
        return ReactionListResponse(
            comment_id=comment_id,
            reactions=[
                ReactionSummaryResponse(
                    reaction_code=rx.reaction_code,
                    count=rx.count,
                    user_ids=rx.user_ids,
                    reacted_by_me=rx.reacted_by_me,
                )
                for rx in reactions
            ],
        )

    async def remove_reaction(
        self,
        *,
        user_id: str,
        comment_id: str,
        reaction_code: str,
        portal_mode: str | None = None,
    ) -> ReactionListResponse:
        if reaction_code not in VALID_REACTION_CODES:
            raise ValidationError(
                f"Invalid reaction code. Must be one of: {sorted(VALID_REACTION_CODES)}"
            )

        now = utc_now_sql()

        async with self._database_pool.transaction() as conn:
            existing = await self._repository.get_comment_by_id(conn, comment_id)
            if existing is None:
                raise NotFoundError("Comment not found.")
            await self._assert_entity_access_for_portal(
                conn,
                portal_mode=portal_mode,
                user_id=user_id,
                entity_type=existing.entity_type,
                entity_id=existing.entity_id,
            )

            removed = await self._repository.remove_reaction(
                conn, comment_id, user_id, reaction_code
            )
            if not removed:
                raise NotFoundError("Reaction not found for this user on this comment.")

            await self._repository.write_comment_audit(
                conn,
                event_id=str(uuid.uuid4()),
                comment_id=comment_id,
                entity_type=existing.entity_type,
                entity_id=existing.entity_id,
                event_type=CommentDomainEventType.REACTION_REMOVED.value,
                actor_user_id=user_id,
                tenant_key=existing.tenant_key,
                metadata={"reaction_code": reaction_code},
                now=now,
            )

        await self._invalidate_entity_cache(existing.entity_type, existing.entity_id)

        async with self._database_pool.acquire() as conn:
            reactions = await self._repository.get_reactions_for_comment(
                conn, comment_id, current_user_id=user_id
            )
        return ReactionListResponse(
            comment_id=comment_id,
            reactions=[
                ReactionSummaryResponse(
                    reaction_code=rx.reaction_code,
                    count=rx.count,
                    user_ids=rx.user_ids,
                    reacted_by_me=rx.reacted_by_me,
                )
                for rx in reactions
            ],
        )

    # ── Reactions (read) ──────────────────────────────────────────────────

    async def get_reactions(
        self,
        *,
        user_id: str,
        comment_id: str,
        portal_mode: str | None = None,
    ) -> ReactionListResponse:
        async with self._database_pool.acquire() as conn:
            existing = await self._repository.get_comment_by_id(conn, comment_id)
            if existing is None:
                raise NotFoundError("Comment not found.")
            await self._assert_entity_access_for_portal(
                conn,
                portal_mode=portal_mode,
                user_id=user_id,
                entity_type=existing.entity_type,
                entity_id=existing.entity_id,
            )
            reactions = await self._repository.get_reactions_for_comment(
                conn, comment_id, current_user_id=user_id
            )
        return ReactionListResponse(
            comment_id=comment_id,
            reactions=[
                ReactionSummaryResponse(
                    reaction_code=rx.reaction_code,
                    count=rx.count,
                    user_ids=rx.user_ids,
                    reacted_by_me=rx.reacted_by_me,
                )
                for rx in reactions
            ],
        )

    # ── Edit history (read) ───────────────────────────────────────────────

    async def get_edit_history(
        self,
        *,
        user_id: str,
        comment_id: str,
        portal_mode: str | None = None,
    ) -> CommentHistoryResponse:
        async with self._database_pool.acquire() as conn:
            existing = await self._repository.get_comment_by_id(conn, comment_id)
            if existing is None:
                raise NotFoundError("Comment not found.")
            await self._assert_entity_access_for_portal(
                conn,
                portal_mode=portal_mode,
                user_id=user_id,
                entity_type=existing.entity_type,
                entity_id=existing.entity_id,
            )
            edits = await self._repository.get_edit_history(conn, comment_id)
        return CommentHistoryResponse(
            comment_id=comment_id,
            edits=[
                CommentEditResponse(
                    id=e.id,
                    comment_id=e.comment_id,
                    previous_content=e.previous_content,
                    edited_by=e.edited_by,
                    edited_at=e.edited_at,
                )
                for e in edits
            ],
        )

    # ── Comment counts (for list-page badges) ─────────────────────────────

    async def get_comment_counts(
        self,
        *,
        user_id: str,
        portal_mode: str | None = None,
        entity_type: str,
        entity_ids: list[str],
    ) -> CommentCountsResponse:
        """Return comment counts for up to 100 entity IDs in one DB round-trip."""
        if entity_type not in VALID_ENTITY_TYPES:
            raise ValidationError(
                f"Invalid entity_type '{entity_type}'. Must be one of: {sorted(VALID_ENTITY_TYPES)}"
            )
        if not entity_ids:
            return CommentCountsResponse(counts={})
        if len(entity_ids) > _MAX_COUNT_ENTITY_IDS:
            raise ValidationError(
                f"Too many entity IDs requested. Maximum is {_MAX_COUNT_ENTITY_IDS}."
            )

        async with self._database_pool.acquire() as conn:
            if is_assignee_portal_mode(portal_mode):
                if entity_type != "task":
                    raise AuthorizationError("Assignee portal can only access task entities.")
                for entity_id in entity_ids:
                    await self._assert_entity_access_for_portal(
                        conn,
                        portal_mode=portal_mode,
                        user_id=user_id,
                        entity_type=entity_type,
                        entity_id=entity_id,
                    )
            counts = await self._repository.get_comment_counts_batch(
                conn,
                entity_type=entity_type,
                entity_ids=entity_ids,
            )
        return CommentCountsResponse(counts=counts)

    # ── Mark comments as read ─────────────────────────────────────────────

    async def mark_read(
        self,
        *,
        user_id: str,
        request: MarkReadRequest,
        portal_mode: str | None = None,
    ) -> MarkReadResponse:
        if request.entity_type not in VALID_ENTITY_TYPES:
            raise ValidationError(
                f"Invalid entity_type '{request.entity_type}'. Must be one of: {sorted(VALID_ENTITY_TYPES)}"
            )

        now = utc_now_sql()
        view_id = str(uuid.uuid4())

        async with self._database_pool.transaction() as conn:
            await self._assert_entity_access_for_portal(
                conn,
                portal_mode=portal_mode,
                user_id=user_id,
                entity_type=request.entity_type,
                entity_id=request.entity_id,
            )
            marked_at = await self._repository.upsert_comment_view(
                conn,
                view_id=view_id,
                user_id=user_id,
                entity_type=request.entity_type,
                entity_id=request.entity_id,
                now=now,
            )

            # Domain audit
            await self._repository.write_comment_audit(
                conn,
                event_id=str(uuid.uuid4()),
                comment_id=view_id,  # use view_id as the related entity
                entity_type=request.entity_type,
                entity_id=request.entity_id,
                event_type="mark_read",
                actor_user_id=user_id,
                tenant_key="system",  # mark_read is user-scoped, no tenant context
                metadata={},
                now=now,
            )

            # Unified audit
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key="system",
                    entity_type="comment_view",
                    entity_id=view_id,
                    event_type="comments_marked_read",
                    event_category=AuditEventCategory.COMMENT.value,
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={
                        "entity_type": request.entity_type,
                        "entity_id": request.entity_id,
                    },
                ),
            )

        return MarkReadResponse(
            entity_type=request.entity_type,
            entity_id=request.entity_id,
            marked_at=marked_at,
        )

    # ── Mentions inbox ────────────────────────────────────────────────────

    async def list_mentions(
        self,
        *,
        user_id: str,
        tenant_key: str,
        portal_mode: str | None = None,
        per_page: int = 25,
        cursor_created_at: str | None = None,
        cursor_id: str | None = None,
    ) -> MentionsListResponse:
        """Return comments where the current user is @-mentioned."""
        if is_assignee_portal_mode(portal_mode):
            raise AuthorizationError("Mentions inbox is not available in assignee mode.")
        async with self._database_pool.acquire() as conn:
            records, total = await self._repository.list_mentions(
                conn,
                user_id=user_id,
                tenant_key=tenant_key,
                limit=per_page,
                cursor_created_at=cursor_created_at,
                cursor_id=cursor_id,
            )

        items = [_comment_with_replies_response(c) for c in records]

        next_cursor: str | None = None
        if len(records) == per_page and records:
            last = records[-1]
            next_cursor = f"{last.created_at}_{last.id}"

        return MentionsListResponse(items=items, total=total, next_cursor=next_cursor)

    # ── GDPR — user data deletion ──────────────────────────────────────

    async def gdpr_delete_user_data(
        self,
        *,
        user_id: str,
        tenant_key: str,
        actor_user_id: str,
    ) -> dict:
        """GDPR right to be forgotten — anonymize all user comments and reactions."""
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            # Anonymize comments
            comment_count = await self._repository.anonymize_user_comments(
                conn, user_id, tenant_key
            )

            # Remove all reactions by user
            reaction_count = await self._repository.delete_user_reactions(conn, user_id)

            # Remove from mention arrays
            await self._repository.remove_user_from_mentions(conn, user_id, tenant_key)

            # Clear view tracking
            await self._repository.delete_user_views(conn, user_id)

            # Unified audit
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="user",
                    entity_id=user_id,
                    event_type="comment_gdpr_data_deleted",
                    event_category=AuditEventCategory.COMMENT.value,
                    occurred_at=now,
                    actor_id=actor_user_id,
                    actor_type="user",
                    properties={
                        "comments_anonymized": str(comment_count),
                        "reactions_deleted": str(reaction_count),
                        "compliance": "GDPR Article 17",
                    },
                ),
            )

        return {
            "comments_anonymized": comment_count,
            "reactions_deleted": reaction_count,
            "user_id": user_id,
        }

    # ── Admin operations ──────────────────────────────────────────────────

    async def list_comments_admin(
        self,
        *,
        user_id: str,
        page: int = 1,
        per_page: int = 50,
        q: str | None = None,
        entity_type: str | None = None,
        is_deleted: bool | None = None,
        is_pinned: bool | None = None,
        resolved: bool | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> AdminCommentListResponse:
        """List comments across all entities, with admin-level filtering."""
        offset = (page - 1) * per_page
        async with self._database_pool.acquire() as conn:
            records, total = await self._repository.list_comments_admin(
                conn,
                limit=per_page,
                offset=offset,
                q=q,
                entity_type=entity_type,
                is_deleted=is_deleted,
                is_pinned=is_pinned,
                resolved=resolved,
                date_from=date_from,
                date_to=date_to,
            )

        items = [_comment_response(r) for r in records]
        has_next = total > (page * per_page)

        return AdminCommentListResponse(
            items=items,
            total=total,
            page=page,
            per_page=per_page,
            has_next=has_next,
        )

    async def get_admin_stats(self, *, user_id: str) -> CommentStatsResponse:
        """Fetch system-wide statistics for the comments domain."""
        async with self._database_pool.acquire() as conn:
            stats = await self._repository.get_admin_stats(conn)

        return CommentStatsResponse(
            total=stats["total"],
            today=stats["today"],
            deleted=stats["deleted"],
            pinned=stats["pinned"],
            top_mentioned=[
                TopMentionedUser(
                    user_id=r["user_id"],
                    display_name=r["display_name"],
                    mention_count=r["mention_count"],
                )
                for r in stats["top_mentioned"]
            ],
        )

    async def undelete_comment(
        self,
        *,
        user_id: str,
        comment_id: str,
    ) -> CommentResponse:
        """Restore a soft-deleted comment."""
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            # Domain audit
            existing = await self._repository.get_comment_by_id(conn, comment_id)
            if existing is None:
                raise NotFoundError("Comment not found.")

            success = await self._repository.undelete_comment(conn, comment_id, now=now)
            if not success:
                raise ValidationError("Comment is not deleted or could not be restored.")

            await self._repository.write_comment_audit(
                conn,
                event_id=str(uuid.uuid4()),
                comment_id=comment_id,
                entity_type=existing.entity_type,
                entity_id=existing.entity_id,
                event_type=CommentDomainEventType.EDITED.value,
                actor_user_id=user_id,
                tenant_key=existing.tenant_key,
                metadata={"admin_action": "undelete"},
                now=now,
            )

            # Re-fetch the restored comment
            restored = await self._repository.get_comment_by_id(conn, comment_id)

        await self._invalidate_entity_cache(existing.entity_type, existing.entity_id)
        return _comment_response(restored)

    async def hard_delete_comment(
        self,
        *,
        user_id: str,
        comment_id: str,
    ) -> None:
        """Permanently delete a comment."""
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            existing = await self._repository.get_comment_by_id(conn, comment_id)
            if existing is None:
                raise NotFoundError("Comment not found.")

            # Audit before deletion
            await self._repository.write_comment_audit(
                conn,
                event_id=str(uuid.uuid4()),
                comment_id=comment_id,
                entity_type=existing.entity_type,
                entity_id=existing.entity_id,
                event_type=CommentDomainEventType.DELETED.value,
                actor_user_id=user_id,
                tenant_key=existing.tenant_key,
                metadata={"admin_action": "hard_delete"},
                now=now,
            )

            success = await self._repository.hard_delete_comment(conn, comment_id)
            if not success:
                raise NotFoundError("Comment could not be permanently deleted.")

        await self._invalidate_entity_cache(existing.entity_type, existing.entity_id)
