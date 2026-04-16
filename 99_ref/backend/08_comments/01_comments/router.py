"""FastAPI router for the comments API (prefix ``/api/v1/cm``).

Endpoint summary:
  GET    /comments                        — list with threaded replies
  POST   /comments                        — create comment or reply
  GET    /comments/counts                 — batch comment counts for badges
  GET    /comments/mentions               — current user's mention inbox
  POST   /comments/mark-read             — mark entity comments as read
  GET    /comments/{id}                   — get single comment detail
  PATCH  /comments/{id}                   — edit (author only)
  DELETE /comments/{id}                   — soft delete (author; admin requires permission)
  POST   /comments/{id}/pin               — pin (requires comments.manage permission)
  DELETE /comments/{id}/pin               — unpin
  POST   /comments/{id}/resolve           — resolve
  DELETE /comments/{id}/resolve           — unresolve
  GET    /comments/{id}/history           — edit history
  GET    /comments/{id}/reactions         — reaction summary
  POST   /comments/{id}/reactions         — toggle reaction
  DELETE /comments/{id}/reactions/{code}  — explicit remove reaction

NOTE: All static sub-paths (/counts, /mentions, /mark-read) are declared
BEFORE the parameterised routes (/{id}/...) to avoid FastAPI routing
ambiguity.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from importlib import import_module
from typing import Annotated

from fastapi import Depends, HTTPException, Query, status

from .dependencies import get_comment_service
from .schemas import (
    AddReactionRequest,
    AdminCommentListResponse,
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
    UpdateCommentRequest,
)
from .service import CommentService

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")
_errors_module = import_module("backend.01_core.errors")
_perm_check_module = import_module("backend.03_auth_manage._permission_check")
_access_scope_module = import_module("backend.07_tasks.access_scope")
_rate_limit_module = import_module("backend.01_core.rate_limit")
_constants_module = import_module("backend.08_comments.constants")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims
NotFoundError = _errors_module.NotFoundError
require_permission = _perm_check_module.require_permission
is_assignee_portal_mode = _access_scope_module.is_assignee_portal_mode
SlidingWindowRateLimiter = _rate_limit_module.SlidingWindowRateLimiter
REACTION_RATE_LIMIT_PER_MINUTE = _constants_module.REACTION_RATE_LIMIT_PER_MINUTE

# Per-user rate limiter for reaction toggle endpoint
_reaction_limiter = SlidingWindowRateLimiter(
    max_requests=REACTION_RATE_LIMIT_PER_MINUTE,
    window_seconds=60,
)

router = InstrumentedAPIRouter(tags=["comments"])

# Feature flag: "comments" flag (seeded in 20260322_seed-comments-attachments-permissions.sql).
# Platform-level enforcement is done via permission checks (comments.view / comments.create).
# Org-level toggle: set org setting "feature_comments_enabled=false" to disable per org.


def _validate_cursor_params(cursor_created_at: str | None, cursor_id: str | None) -> None:
    """Validate that cursor pagination parameters are provided together and well-formed."""
    if (cursor_created_at is None) != (cursor_id is None):
        raise HTTPException(status_code=422, detail="Both cursor_created_at and cursor_id must be provided together")
    if cursor_id is not None:
        try:
            uuid.UUID(cursor_id)
        except ValueError:
            raise HTTPException(status_code=422, detail="cursor_id must be a valid UUID")
    if cursor_created_at is not None:
        try:
            datetime.fromisoformat(cursor_created_at.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(status_code=422, detail="cursor_created_at must be a valid ISO 8601 timestamp")


async def _resolve_entity_scope(
    conn,
    *,
    tenant_key: str,
    entity_type: str,
    entity_id: str,
) -> tuple[str | None, str | None]:
    """Resolve the real org/workspace scope from the underlying entity record.

    Security note: never trust client-supplied scope for tenant-scoped comment access.
    """
    row = None

    if entity_type == "risk":
        row = await conn.fetchrow(
            """
            SELECT org_id::text AS org_id, workspace_id::text AS workspace_id
            FROM "14_risk_registry"."10_fct_risks"
            WHERE id = $1::uuid AND tenant_key = $2 AND is_deleted = FALSE
            """,
            entity_id,
            tenant_key,
        )
    elif entity_type == "task":
        row = await conn.fetchrow(
            """
            SELECT org_id::text AS org_id, workspace_id::text AS workspace_id
            FROM "08_tasks"."10_fct_tasks"
            WHERE id = $1::uuid AND tenant_key = $2 AND is_deleted = FALSE
            """,
            entity_id,
            tenant_key,
        )
    elif entity_type == "framework":
        row = await conn.fetchrow(
            """
            SELECT scope_org_id::text AS org_id, scope_workspace_id::text AS workspace_id
            FROM "05_grc_library"."10_fct_frameworks"
            WHERE id = $1::uuid AND tenant_key = $2 AND is_deleted = FALSE
            """,
            entity_id,
            tenant_key,
        )
    elif entity_type == "control":
        row = await conn.fetchrow(
            """
            SELECT f.scope_org_id::text AS org_id, f.scope_workspace_id::text AS workspace_id
            FROM "05_grc_library"."13_fct_controls" c
            JOIN "05_grc_library"."10_fct_frameworks" f
              ON f.id = c.framework_id
            WHERE c.id = $1::uuid
              AND c.tenant_key = $2
              AND c.is_deleted = FALSE
              AND f.is_deleted = FALSE
            """,
            entity_id,
            tenant_key,
        )
    elif entity_type == "requirement":
        row = await conn.fetchrow(
            """
            SELECT f.scope_org_id::text AS org_id, f.scope_workspace_id::text AS workspace_id
            FROM "05_grc_library"."12_fct_requirements" r
            JOIN "05_grc_library"."10_fct_frameworks" f
              ON f.id = r.framework_id
            WHERE r.id = $1::uuid
              AND r.is_deleted = FALSE
              AND f.tenant_key = $2
              AND f.is_deleted = FALSE
            """,
            entity_id,
            tenant_key,
        )
    elif entity_type == "test":
        row = await conn.fetchrow(
            """
            SELECT scope_org_id::text AS org_id, scope_workspace_id::text AS workspace_id
            FROM "05_grc_library"."14_fct_control_tests"
            WHERE id = $1::uuid AND tenant_key = $2 AND is_deleted = FALSE
            """,
            entity_id,
            tenant_key,
        )
    elif entity_type == "feedback_ticket":
        row = await conn.fetchrow(
            """
            SELECT org_id::text AS org_id, workspace_id::text AS workspace_id
            FROM "10_feedback"."10_fct_tickets"
            WHERE id = $1::uuid AND tenant_key = $2 AND is_deleted = FALSE
            """,
            entity_id,
            tenant_key,
        )
    elif entity_type == "engagement":
        row = await conn.fetchrow(
            """
            SELECT org_id::text AS org_id, NULL::text AS workspace_id
            FROM "12_engagements"."10_fct_audit_engagements"
            WHERE id = $1::uuid AND tenant_key = $2
            """,
            entity_id,
            tenant_key,
        )
    elif entity_type == "org":
        # Entity is the org itself
        row = {"org_id": entity_id, "workspace_id": None}
    elif entity_type == "workspace":
        row = await conn.fetchrow(
            """
            SELECT org_id::text AS org_id, id::text AS workspace_id
            FROM "03_auth_manage"."34_fct_workspaces"
            WHERE id = $1::uuid AND is_deleted = FALSE
            """,
            entity_id,
        )
    elif entity_type == "comment":
        # Resolve scope from the parent comment
        parent_row = await conn.fetchrow(
            """
            SELECT entity_type, entity_id
            FROM "08_comments"."01_fct_comments"
            WHERE id = $1::uuid AND tenant_key = $2
            """,
            entity_id,
            tenant_key,
        )
        if parent_row:
            return await _resolve_entity_scope(
                conn,
                tenant_key=tenant_key,
                entity_type=parent_row["entity_type"],
                entity_id=parent_row["entity_id"],
            )
        else:
            raise NotFoundError(f"Comment '{entity_id}' not found.")
    elif entity_type == "evidence_template":
        raise NotFoundError("Evidence templates are no longer supported.")
    else:
        raise NotFoundError(f"Unsupported comment entity type '{entity_type}'.")

    if row is None:
        raise NotFoundError(f"{entity_type.replace('_', ' ').title()} '{entity_id}' not found")
    return row["org_id"], row["workspace_id"]


async def _require_entity_permission(
    conn,
    *,
    tenant_key: str,
    user_id: str,
    permission_code: str,
    entity_type: str,
    entity_id: str,
) -> tuple[str | None, str | None]:
    scope_org_id, scope_workspace_id = await _resolve_entity_scope(
        conn,
        tenant_key=tenant_key,
        entity_type=entity_type,
        entity_id=entity_id,
    )
    await require_permission(
        conn,
        user_id,
        permission_code,
        scope_org_id=scope_org_id,
        scope_workspace_id=scope_workspace_id,
    )
    return scope_org_id, scope_workspace_id


async def _get_comment_entity_reference(
    conn,
    *,
    service: CommentService,
    comment_id: str,
) -> tuple[str, str]:
    record = await service._repository.get_comment_by_id(conn, comment_id)
    if record is None:
        raise NotFoundError("Comment not found.")
    return record.entity_type, record.entity_id


async def _require_comment_permission(
    conn,
    *,
    service: CommentService,
    tenant_key: str,
    user_id: str,
    permission_code: str,
    comment_id: str,
) -> tuple[str, str, str | None, str | None]:
    entity_type, entity_id = await _get_comment_entity_reference(
        conn,
        service=service,
        comment_id=comment_id,
    )
    scope_org_id, scope_workspace_id = await _require_entity_permission(
        conn,
        tenant_key=tenant_key,
        user_id=user_id,
        permission_code=permission_code,
        entity_type=entity_type,
        entity_id=entity_id,
    )
    return entity_type, entity_id, scope_org_id, scope_workspace_id


# ─────────────────────────────────────────────────────────────────────────────
# Static sub-paths (MUST come before /{comment_id}/... routes)
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/comments/counts", response_model=dict[str, int])
async def get_comment_counts(
    service: Annotated[CommentService, Depends(get_comment_service)],
    claims=Depends(get_current_access_claims),
    entity_type: str = Query(..., description="Entity type (task, risk, control, …)"),
    entity_ids: str = Query(
        ...,
        description="Comma-separated list of entity UUIDs (max 100)",
    ),
) -> dict[str, int]:
    """Return comment counts for multiple entities in one request.

    Used by list pages to display comment count badges without loading all
    comments.  Accepts up to 100 entity IDs per call.
    """
    ids = [i.strip() for i in entity_ids.split(",") if i.strip()]
    if not is_assignee_portal_mode(claims.portal_mode):
        async with service._database_pool.acquire() as conn:
            for entity_id in ids:
                await _require_entity_permission(
                    conn,
                    tenant_key=claims.tenant_key,
                    user_id=claims.subject,
                    permission_code="comments.view",
                    entity_type=entity_type,
                    entity_id=entity_id,
                )
    result = await service.get_comment_counts(
        user_id=claims.subject,
        portal_mode=claims.portal_mode,
        entity_type=entity_type,
        entity_ids=ids,
    )
    return result.counts


@router.get("/comments/mentions", response_model=MentionsListResponse)
async def list_mentions(
    service: Annotated[CommentService, Depends(get_comment_service)],
    claims=Depends(get_current_access_claims),
    per_page: int = Query(default=25, ge=1, le=100),
    cursor_created_at: str | None = Query(default=None),
    cursor_id: str | None = Query(default=None),
) -> MentionsListResponse:
    """Return comments where the current user is @-mentioned, newest first.

    Useful for a "mentions" inbox view.  Supports cursor-based pagination.
    """
    if not is_assignee_portal_mode(claims.portal_mode):
        async with service._database_pool.acquire() as conn:
            await require_permission(conn, claims.subject, "comments.view")
    _validate_cursor_params(cursor_created_at, cursor_id)
    return await service.list_mentions(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        portal_mode=claims.portal_mode,
        per_page=per_page,
        cursor_created_at=cursor_created_at,
        cursor_id=cursor_id,
    )


@router.post(
    "/comments/mark-read",
    response_model=MarkReadResponse,
    status_code=status.HTTP_200_OK,
)
async def mark_comments_read(
    body: MarkReadRequest,
    service: Annotated[CommentService, Depends(get_comment_service)],
    claims=Depends(get_current_access_claims),
) -> MarkReadResponse:
    """Record that the current user has viewed comments for an entity.

    Subsequent calls to ``GET /comments`` will include an ``unread_count``
    reflecting only comments created after this mark-read timestamp.
    """
    if not is_assignee_portal_mode(claims.portal_mode):
        async with service._database_pool.acquire() as conn:
            await _require_entity_permission(
                conn,
                tenant_key=claims.tenant_key,
                user_id=claims.subject,
                permission_code="comments.view",
                entity_type=body.entity_type,
                entity_id=body.entity_id,
            )
    return await service.mark_read(
        user_id=claims.subject,
        request=body,
        portal_mode=claims.portal_mode,
    )


# ─────────────────────────────────────────────────────────────────────────────
# GDPR — admin user data deletion
# NOTE: static sub-path, must come before /{comment_id}
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/comments/admin/users/{user_id}/comments")
async def list_user_comments(
    user_id: str,
    service: Annotated[CommentService, Depends(get_comment_service)],
    claims=Depends(get_current_access_claims),
):
    """List all comments authored by a specific user.

    Requires the ``admin.view`` permission.  Used for GDPR data preview.
    """
    async with service._database_pool.acquire() as conn:
        await require_permission(conn, claims.subject, "admin.view")

    async with service._database_pool.acquire() as conn:
        records = await service._repository.list_comments_by_user(
            conn, user_id, claims.tenant_key
        )

    return {
        "user_id": user_id,
        "total": len(records),
        "items": [
            {
                "id": r.id,
                "entity_type": r.entity_type,
                "entity_id": r.entity_id,
                "content": r.content[:100] + "..." if len(r.content) > 100 else r.content,
                "created_at": r.created_at,
            }
            for r in records
        ],
    }


@router.delete("/comments/admin/users/{user_id}/data")
async def gdpr_delete_user_comments(
    user_id: str,
    service: Annotated[CommentService, Depends(get_comment_service)],
    claims=Depends(get_current_access_claims),
):
    """GDPR Article 17 — delete all comment data for a specific user.

    Anonymizes all comments (replaces content with placeholder), removes all
    reactions, clears mention references, and deletes view tracking data.
    Requires the ``admin.delete`` permission.
    """
    async with service._database_pool.acquire() as conn:
        await require_permission(conn, claims.subject, "admin.delete")

    result = await service.gdpr_delete_user_data(
        user_id=user_id,
        tenant_key=claims.tenant_key,
        actor_user_id=claims.subject,
    )
    return result


# ─────────────────────────────────────────────────────────────────────────────
# List / Create
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/comments", response_model=CommentListResponse)
async def list_comments(
    service: Annotated[CommentService, Depends(get_comment_service)],
    claims=Depends(get_current_access_claims),
    entity_type: str = Query(..., description="Entity type (task, risk, control, ...)"),
    entity_id: str = Query(..., description="Entity UUID"),
    include_replies: bool = Query(default=True),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=25, ge=1, le=100),
    cursor_created_at: str | None = Query(default=None),
    cursor_id: str | None = Query(default=None),
    visibility: str | None = Query(default=None, description="Filter by visibility: 'internal' or 'external'. If omitted, auto-resolves based on permissions."),
) -> CommentListResponse:
    """List top-level comments for an entity with nested replies (up to 10 per comment).

    Supports cursor-based pagination via ``next_cursor`` from the previous response.
    The ``unread_count`` field reflects how many comments were created since the
    caller's last ``POST /comments/mark-read`` call.

    Visibility filtering:
    - If ``visibility`` is not specified, users with ``comments.manage`` permission see all
      comments (internal + external). Users without that permission only see external comments.
    - If ``visibility='internal'``, only internal comments are returned (requires permission).
    - If ``visibility='external'``, only external comments are returned.
    """
    if not is_assignee_portal_mode(claims.portal_mode):
        async with service._database_pool.acquire() as conn:
            await _require_entity_permission(
                conn,
                tenant_key=claims.tenant_key,
                user_id=claims.subject,
                permission_code="comments.view",
                entity_type=entity_type,
                entity_id=entity_id,
            )
    _validate_cursor_params(cursor_created_at, cursor_id)
    return await service.list_comments(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        portal_mode=claims.portal_mode,
        entity_type=entity_type,
        entity_id=entity_id,
        include_replies=include_replies,
        page=page,
        per_page=per_page,
        cursor_created_at=cursor_created_at,
        cursor_id=cursor_id,
        visibility=visibility,
    )


@router.post("/comments", response_model=CommentWithRepliesResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(
    body: CreateCommentRequest,
    service: Annotated[CommentService, Depends(get_comment_service)],
    claims=Depends(get_current_access_claims),
) -> CommentWithRepliesResponse:
    """Create a comment on an entity.

    Optionally reply to an existing top-level comment (``parent_comment_id``).
    Replies to replies are not permitted — maximum one level of nesting.
    Mention syntax: ``@[Display Name](user-uuid)``.
    """
    if not is_assignee_portal_mode(claims.portal_mode):
        async with service._database_pool.acquire() as conn:
            await _require_entity_permission(
                conn,
                tenant_key=claims.tenant_key,
                user_id=claims.subject,
                permission_code="comments.create",
                entity_type=body.entity_type,
                entity_id=body.entity_id,
            )
    return await service.create_comment(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        request=body,
        portal_mode=claims.portal_mode,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Single comment
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/comments/{comment_id}", response_model=CommentWithRepliesResponse)
async def get_comment(
    comment_id: str,
    service: Annotated[CommentService, Depends(get_comment_service)],
    claims=Depends(get_current_access_claims),
) -> CommentWithRepliesResponse:
    """Get a single comment with all replies, reactions, and edit history."""
    if not is_assignee_portal_mode(claims.portal_mode):
        async with service._database_pool.acquire() as conn:
            await _require_comment_permission(
                conn,
                service=service,
                tenant_key=claims.tenant_key,
                user_id=claims.subject,
                permission_code="comments.view",
                comment_id=comment_id,
            )
    return await service.get_comment(
        user_id=claims.subject,
        comment_id=comment_id,
        portal_mode=claims.portal_mode,
    )


@router.patch("/comments/{comment_id}", response_model=CommentWithRepliesResponse)
async def update_comment(
    comment_id: str,
    body: UpdateCommentRequest,
    service: Annotated[CommentService, Depends(get_comment_service)],
    claims=Depends(get_current_access_claims),
) -> CommentWithRepliesResponse:
    """Edit comment content. Only the original author may edit.

    Previous content is saved to edit history automatically.
    """
    if not is_assignee_portal_mode(claims.portal_mode):
        async with service._database_pool.acquire() as conn:
            await _require_comment_permission(
                conn,
                service=service,
                tenant_key=claims.tenant_key,
                user_id=claims.subject,
                permission_code="comments.view",
                comment_id=comment_id,
            )
    return await service.update_comment(
        user_id=claims.subject,
        comment_id=comment_id,
        request=body,
        portal_mode=claims.portal_mode,
    )


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: str,
    service: Annotated[CommentService, Depends(get_comment_service)],
    claims=Depends(get_current_access_claims),
) -> None:
    """Soft-delete a comment. Content is replaced with '[deleted]' in responses.

    Replies are preserved.  The comment author may always delete their own comments.
    To delete another user's comment (admin action), the caller must hold the
    ``comments.delete`` permission — enforced here, not via a query parameter.
    """
    if not is_assignee_portal_mode(claims.portal_mode):
        async with service._database_pool.acquire() as conn:
            await _require_comment_permission(
                conn,
                service=service,
                tenant_key=claims.tenant_key,
                user_id=claims.subject,
                permission_code="comments.view",
                comment_id=comment_id,
            )
    # First attempt author-only delete; if not the author, require platform permission
    await service.delete_comment(
        user_id=claims.subject,
        comment_id=comment_id,
        is_admin=False,
        portal_mode=claims.portal_mode,
    )




# ── Admin operations ──────────────────────────────────────────────────

@router.get("/admin/comments", response_model=AdminCommentListResponse)
async def list_comments_admin(
    service: Annotated[CommentService, Depends(get_comment_service)],
    claims=Depends(get_current_access_claims),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    q: str | None = Query(None),
    entity_type: str | None = Query(None),
    is_deleted: bool | None = Query(None),
    is_pinned: bool | None = Query(None),
    resolved: bool | None = Query(None),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
) -> AdminCommentListResponse:
    """Global comment list for admins with flexible filtering.

    Requires the ``comments.view`` platform permission.
    """
    async with service._database_pool.acquire() as conn:
        await require_permission(conn, claims.subject, "comments.view")

    return await service.list_comments_admin(
        user_id=claims.subject,
        page=page,
        per_page=per_page,
        q=q,
        entity_type=entity_type,
        is_deleted=is_deleted,
        is_pinned=is_pinned,
        resolved=resolved,
        date_from=date_from,
        date_to=date_to,
    )


@router.get("/admin/comments/stats", response_model=CommentStatsResponse)
async def get_admin_stats(
    service: Annotated[CommentService, Depends(get_comment_service)],
    claims=Depends(get_current_access_claims),
) -> CommentStatsResponse:
    """Fetch system-wide statistics for the comments domain.

    Requires the ``comments.view`` platform permission.
    """
    async with service._database_pool.acquire() as conn:
        await require_permission(conn, claims.subject, "comments.view")

    return await service.get_admin_stats(user_id=claims.subject)


@router.post("/admin/comments/{comment_id}/undelete", response_model=CommentResponse)
async def undelete_comment(
    comment_id: str,
    service: Annotated[CommentService, Depends(get_comment_service)],
    claims=Depends(get_current_access_claims),
) -> CommentResponse:
    """Restore a soft-deleted comment.

    Requires the ``comments.delete`` platform permission.
    """
    async with service._database_pool.acquire() as conn:
        await require_permission(conn, claims.subject, "comments.delete")

    return await service.undelete_comment(user_id=claims.subject, comment_id=comment_id)


@router.post("/admin/comments/{comment_id}/soft-delete", status_code=status.HTTP_204_NO_CONTENT)
async def admin_soft_delete_comment(
    comment_id: str,
    service: Annotated[CommentService, Depends(get_comment_service)],
    claims=Depends(get_current_access_claims),
) -> None:
    """Admin soft-delete — bypasses author check.

    Requires the ``comments.delete`` platform permission.
    """
    async with service._database_pool.acquire() as conn:
        await require_permission(conn, claims.subject, "comments.delete")

    await service.delete_comment(
        user_id=claims.subject,
        comment_id=comment_id,
        is_admin=True,
        portal_mode=claims.portal_mode,
    )


@router.delete("/admin/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def hard_delete_comment(
    comment_id: str,
    service: Annotated[CommentService, Depends(get_comment_service)],
    claims=Depends(get_current_access_claims),
) -> None:
    """Permanently delete a comment.

    Requires the ``comments.delete`` platform permission.
    """
    async with service._database_pool.acquire() as conn:
        await require_permission(conn, claims.subject, "comments.delete")

    await service.hard_delete_comment(user_id=claims.subject, comment_id=comment_id)


# ─────────────────────────────────────────────────────────────────────────────
# Pin / Unpin
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/comments/{comment_id}/pin", response_model=CommentWithRepliesResponse)
async def pin_comment(
    comment_id: str,
    service: Annotated[CommentService, Depends(get_comment_service)],
    claims=Depends(get_current_access_claims),
) -> CommentWithRepliesResponse:
    """Pin a comment.  Requires the ``comments.manage`` permission."""
    async with service._database_pool.acquire() as conn:
        await _require_comment_permission(
            conn,
            service=service,
            tenant_key=claims.tenant_key,
            user_id=claims.subject,
            permission_code="comments.manage",
            comment_id=comment_id,
        )
    return await service.pin_comment(
        user_id=claims.subject,
        comment_id=comment_id,
        portal_mode=claims.portal_mode,
    )


@router.delete("/comments/{comment_id}/pin", response_model=CommentWithRepliesResponse)
async def unpin_comment(
    comment_id: str,
    service: Annotated[CommentService, Depends(get_comment_service)],
    claims=Depends(get_current_access_claims),
) -> CommentWithRepliesResponse:
    """Unpin a comment.  Requires the ``comments.manage`` permission."""
    async with service._database_pool.acquire() as conn:
        await _require_comment_permission(
            conn,
            service=service,
            tenant_key=claims.tenant_key,
            user_id=claims.subject,
            permission_code="comments.manage",
            comment_id=comment_id,
        )
    return await service.unpin_comment(
        user_id=claims.subject,
        comment_id=comment_id,
        portal_mode=claims.portal_mode,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Resolve / Unresolve
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/comments/{comment_id}/resolve", response_model=CommentWithRepliesResponse)
async def resolve_comment(
    comment_id: str,
    service: Annotated[CommentService, Depends(get_comment_service)],
    claims=Depends(get_current_access_claims),
) -> CommentWithRepliesResponse:
    """Mark a comment as resolved (action item completed).

    Requires the ``comments.resolve`` permission.
    """
    async with service._database_pool.acquire() as conn:
        await _require_comment_permission(
            conn,
            service=service,
            tenant_key=claims.tenant_key,
            user_id=claims.subject,
            permission_code="comments.resolve",
            comment_id=comment_id,
        )
    return await service.resolve_comment(
        user_id=claims.subject,
        comment_id=comment_id,
        portal_mode=claims.portal_mode,
    )


@router.delete("/comments/{comment_id}/resolve", response_model=CommentWithRepliesResponse)
async def unresolve_comment(
    comment_id: str,
    service: Annotated[CommentService, Depends(get_comment_service)],
    claims=Depends(get_current_access_claims),
) -> CommentWithRepliesResponse:
    """Unresolve a previously resolved comment.

    Requires the ``comments.resolve`` permission.
    """
    async with service._database_pool.acquire() as conn:
        await _require_comment_permission(
            conn,
            service=service,
            tenant_key=claims.tenant_key,
            user_id=claims.subject,
            permission_code="comments.resolve",
            comment_id=comment_id,
        )
    return await service.unresolve_comment(
        user_id=claims.subject,
        comment_id=comment_id,
        portal_mode=claims.portal_mode,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Edit history
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/comments/{comment_id}/history", response_model=CommentHistoryResponse)
async def get_comment_history(
    comment_id: str,
    service: Annotated[CommentService, Depends(get_comment_service)],
    claims=Depends(get_current_access_claims),
) -> CommentHistoryResponse:
    """Get the full edit history for a comment (all previous versions, oldest first)."""
    if not is_assignee_portal_mode(claims.portal_mode):
        async with service._database_pool.acquire() as conn:
            await _require_comment_permission(
                conn,
                service=service,
                tenant_key=claims.tenant_key,
                user_id=claims.subject,
                permission_code="comments.view",
                comment_id=comment_id,
            )
    return await service.get_edit_history(
        user_id=claims.subject,
        comment_id=comment_id,
        portal_mode=claims.portal_mode,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Reactions
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/comments/{comment_id}/reactions", response_model=ReactionListResponse)
async def get_reactions(
    comment_id: str,
    service: Annotated[CommentService, Depends(get_comment_service)],
    claims=Depends(get_current_access_claims),
) -> ReactionListResponse:
    """Get all reactions on a comment, grouped by reaction code with user lists."""
    if not is_assignee_portal_mode(claims.portal_mode):
        async with service._database_pool.acquire() as conn:
            await _require_comment_permission(
                conn,
                service=service,
                tenant_key=claims.tenant_key,
                user_id=claims.subject,
                permission_code="comments.view",
                comment_id=comment_id,
            )
    return await service.get_reactions(
        user_id=claims.subject,
        comment_id=comment_id,
        portal_mode=claims.portal_mode,
    )


@router.post("/comments/{comment_id}/reactions", response_model=ReactionListResponse)
async def toggle_reaction(
    comment_id: str,
    body: AddReactionRequest,
    service: Annotated[CommentService, Depends(get_comment_service)],
    claims=Depends(get_current_access_claims),
) -> ReactionListResponse:
    """Toggle a reaction on a comment.

    If the caller already has this reaction it is removed (toggle).
    Returns updated reaction list.
    Valid codes: ``thumbs_up``, ``thumbs_down``, ``heart``, ``laugh``,
    ``tada``, ``eyes``, ``rocket``, ``confused``.

    Rate limited to 30 requests per minute per user.
    """
    allowed, remaining, reset_after = _reaction_limiter.is_allowed(f"reaction:{claims.subject}")
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Reaction rate limit exceeded. Please try again later.",
            headers={"Retry-After": str(reset_after)},
        )
    if not is_assignee_portal_mode(claims.portal_mode):
        async with service._database_pool.acquire() as conn:
            await _require_comment_permission(
                conn,
                service=service,
                tenant_key=claims.tenant_key,
                user_id=claims.subject,
                permission_code="comments.view",
                comment_id=comment_id,
            )
    return await service.toggle_reaction(
        user_id=claims.subject,
        comment_id=comment_id,
        request=body,
        portal_mode=claims.portal_mode,
    )


@router.delete("/comments/{comment_id}/reactions/{reaction_code}", response_model=ReactionListResponse)
async def remove_reaction(
    comment_id: str,
    reaction_code: str,
    service: Annotated[CommentService, Depends(get_comment_service)],
    claims=Depends(get_current_access_claims),
) -> ReactionListResponse:
    """Explicitly remove a specific reaction from a comment for the current user."""
    if not is_assignee_portal_mode(claims.portal_mode):
        async with service._database_pool.acquire() as conn:
            await _require_comment_permission(
                conn,
                service=service,
                tenant_key=claims.tenant_key,
                user_id=claims.subject,
                permission_code="comments.view",
                comment_id=comment_id,
            )
    return await service.remove_reaction(
        user_id=claims.subject,
        comment_id=comment_id,
        reaction_code=reaction_code,
        portal_mode=claims.portal_mode,
    )
