"""Pydantic request/response schemas for the comments API.

All timestamps are returned as ISO-8601 strings.  Soft-deleted comment
content is replaced with ``"[deleted]"`` by the service layer before being
placed into a response schema, so consumers never see raw deleted content.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


# ─────────────────────────────────────────────────────────────────────────────
# Request schemas
# ─────────────────────────────────────────────────────────────────────────────

class CreateCommentRequest(BaseModel):
    entity_type: str = Field(..., min_length=1, max_length=50)
    entity_id: str
    content: str = Field(..., min_length=1, max_length=50_000)
    parent_comment_id: str | None = None
    content_format: str = Field(default="markdown", pattern=r"^(plain_text|markdown)$")
    visibility: str = Field(default="external", pattern=r"^(internal|external)$")
    attachment_ids: list[str] = Field(default_factory=list)


class UpdateCommentRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=50_000)


class AddReactionRequest(BaseModel):
    reaction_code: str = Field(..., min_length=1, max_length=50)


class MarkReadRequest(BaseModel):
    """Mark all comments on an entity as read for the current user."""
    entity_type: str = Field(..., min_length=1, max_length=50)
    entity_id: str = Field(..., min_length=1)


# ─────────────────────────────────────────────────────────────────────────────
# Response schemas
# ─────────────────────────────────────────────────────────────────────────────

class ReactionSummaryResponse(BaseModel):
    reaction_code: str = Field(..., description="Reaction emoji code (e.g. thumbs_up, heart)")
    count: int = Field(..., description="Total number of users who reacted with this code")
    user_ids: list[str] = Field(default_factory=list, description="User IDs who reacted")
    user_names: list[str] = Field(default_factory=list, description="Display names of users who reacted")
    reacted_by_me: bool = Field(..., description="Whether the current user has this reaction")


class CommentEditResponse(BaseModel):
    id: str = Field(..., description="Edit history entry ID")
    comment_id: str = Field(..., description="ID of the comment that was edited")
    previous_content: str = Field(..., description="Content before this edit")
    edited_by: str = Field(..., description="User ID who made the edit")
    edited_at: str = Field(..., description="ISO-8601 timestamp of the edit")


class CommentResponse(BaseModel):
    id: str
    tenant_key: str
    entity_type: str
    entity_id: str
    parent_comment_id: str | None = None
    author_user_id: str
    # Soft-deleted comments have content replaced with "[deleted]"
    content: str
    content_format: str = "markdown"
    rendered_html: str | None = None
    visibility: str = "external"
    is_edited: bool
    is_deleted: bool
    is_locked: bool = False
    locked_by: str | None = None
    locked_at: str | None = None
    deleted_at: str | None = None
    deleted_by: str | None = None
    pinned: bool
    pinned_by: str | None = None
    pinned_at: str | None = None
    resolved: bool
    resolved_by: str | None = None
    resolved_at: str | None = None
    mention_user_ids: list[str] = []
    reply_count: int = 0
    attachment_ids: list[str] = []
    created_at: str
    updated_at: str
    author_display_name: str | None = None
    author_email: str | None = None
    author_grc_role_code: str | None = None
    author_is_external: bool = False


class CommentWithRepliesResponse(CommentResponse):
    replies: list[CommentResponse] = []
    reactions: list[ReactionSummaryResponse] = []
    edit_history: list[CommentEditResponse] = []


class CommentListResponse(BaseModel):
    items: list[CommentWithRepliesResponse]
    total: int
    # Cursor for next page: "{created_at_iso}_{id}"
    next_cursor: str | None = None
    unread_count: int = 0


class ReactionListResponse(BaseModel):
    comment_id: str
    reactions: list[ReactionSummaryResponse]


class CommentHistoryResponse(BaseModel):
    comment_id: str
    edits: list[CommentEditResponse]


class CommentCountsResponse(BaseModel):
    """Mapping of entity_id → comment count.  Used by list pages for badges."""
    counts: dict[str, int]


class MentionsListResponse(BaseModel):
    """Comments where the current user was @-mentioned."""
    items: list[CommentWithRepliesResponse]
    total: int
    next_cursor: str | None = None


class MarkReadResponse(BaseModel):
    entity_type: str = Field(..., description="Entity type that was marked as read")
    entity_id: str = Field(..., description="Entity ID that was marked as read")
    marked_at: str = Field(..., description="ISO-8601 timestamp when comments were marked read")


class AdminCommentListResponse(BaseModel):
    items: list[CommentResponse]
    total: int
    page: int
    per_page: int
    has_next: bool


class TopMentionedUser(BaseModel):
    user_id: str
    display_name: str | None = None
    mention_count: int


class CommentStatsResponse(BaseModel):
    total: int
    today: int
    deleted: int
    pinned: int
    top_mentioned: list[TopMentionedUser] = []
