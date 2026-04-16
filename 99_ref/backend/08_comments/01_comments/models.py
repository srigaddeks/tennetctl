"""Internal dataclass models for the comments domain.

These are pure Python dataclasses used internally by the repository and service
layers.  They are **not** exposed to the API directly — Pydantic schemas in
``schemas.py`` serve that role.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class CommentRecord:
    """Raw comment row — no joins, used for mutation checks."""
    id: str
    tenant_key: str
    entity_type: str
    entity_id: str
    parent_comment_id: str | None
    author_user_id: str
    content: str
    is_edited: bool
    is_deleted: bool
    deleted_at: str | None
    deleted_by: str | None
    pinned: bool
    pinned_by: str | None
    pinned_at: str | None
    resolved: bool
    resolved_by: str | None
    resolved_at: str | None
    content_format: str  # 'plain_text' or 'markdown'
    rendered_html: str | None  # pre-rendered HTML (sanitized)
    visibility: str  # 'internal' or 'external'
    is_locked: bool
    locked_by: str | None
    locked_at: str | None
    mention_user_ids: list[str]
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class CommentDetailRecord:
    """Comment with joined author info and counts — used for API responses."""
    id: str
    tenant_key: str
    entity_type: str
    entity_id: str
    parent_comment_id: str | None
    author_user_id: str
    content: str
    is_edited: bool
    is_deleted: bool
    deleted_at: str | None
    deleted_by: str | None
    pinned: bool
    pinned_by: str | None
    pinned_at: str | None
    resolved: bool
    resolved_by: str | None
    resolved_at: str | None
    content_format: str
    rendered_html: str | None
    visibility: str
    is_locked: bool
    locked_by: str | None
    locked_at: str | None
    mention_user_ids: list[str]
    reply_count: int
    created_at: str
    updated_at: str
    # Joined from 03_auth_manage.05_dtl_user_properties
    author_display_name: str | None
    author_email: str | None


@dataclass(frozen=True)
class ReactionSummaryRecord:
    """Aggregated reaction counts for a comment."""
    reaction_code: str
    count: int
    user_ids: list[str]
    reacted_by_me: bool
    user_names: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class CommentEditRecord:
    """Single edit history entry."""
    id: str
    comment_id: str
    previous_content: str
    edited_by: str
    edited_at: str


@dataclass(frozen=True)
class CommentWithRepliesRecord:
    """Top-level comment plus its replies and reactions (for detail view)."""
    id: str
    tenant_key: str
    entity_type: str
    entity_id: str
    parent_comment_id: str | None
    author_user_id: str
    content: str
    is_edited: bool
    is_deleted: bool
    deleted_at: str | None
    deleted_by: str | None
    pinned: bool
    pinned_by: str | None
    pinned_at: str | None
    resolved: bool
    resolved_by: str | None
    resolved_at: str | None
    content_format: str
    rendered_html: str | None
    visibility: str
    is_locked: bool
    locked_by: str | None
    locked_at: str | None
    mention_user_ids: list[str]
    reply_count: int
    created_at: str
    updated_at: str
    author_display_name: str | None
    author_email: str | None
    replies: list[CommentDetailRecord]
    reactions: list[ReactionSummaryRecord]
    edit_history: list[CommentEditRecord]
