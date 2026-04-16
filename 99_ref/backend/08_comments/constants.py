from __future__ import annotations

from enum import StrEnum


class CommentAuditEventType(StrEnum):
    COMMENT_CREATED = "comment_created"
    COMMENT_EDITED = "comment_edited"
    COMMENT_DELETED = "comment_deleted"
    COMMENT_PINNED = "comment_pinned"
    COMMENT_UNPINNED = "comment_unpinned"
    COMMENT_RESOLVED = "comment_resolved"
    COMMENT_UNRESOLVED = "comment_unresolved"
    REACTION_ADDED = "reaction_added"
    REACTION_REMOVED = "reaction_removed"


# Domain audit event types (written to 08_comments.04_aud_comment_events)
class CommentDomainEventType(StrEnum):
    CREATED = "created"
    EDITED = "edited"
    DELETED = "deleted"
    PINNED = "pinned"
    UNPINNED = "unpinned"
    RESOLVED = "resolved"
    UNRESOLVED = "unresolved"
    REACTION_ADDED = "reaction_added"
    REACTION_REMOVED = "reaction_removed"


# Entity types that may receive comments
VALID_ENTITY_TYPES = frozenset({
    "task",
    "risk",
    "control",
    "framework",
    "engagement",
    "evidence_template",
    "test",
    "requirement",
    "feedback_ticket",
    "org",
    "workspace",
    "comment",  # For nested/reply comments
})

# Emoji reaction codes
VALID_REACTION_CODES = frozenset({
    "thumbs_up",
    "thumbs_down",
    "heart",
    "laugh",
    "tada",
    "eyes",
    "rocket",
    "confused",
})

# Maximum replies fetched per top-level comment in list view
MAX_REPLIES_PER_COMMENT = 10

# Maximum @-mentions allowed per comment
MAX_MENTIONS_PER_COMMENT = 50

# Permission codes used by the comments domain
VALID_PERMISSION_CODES = frozenset({
    "comments.manage",
    "comments.delete",
    "comments.resolve",
})

# Content format options
VALID_CONTENT_FORMATS = frozenset({"plain_text", "markdown"})

# Visibility options for internal vs external comments
VALID_VISIBILITY_OPTIONS = frozenset({"internal", "external"})

# Rate limit for reaction toggle endpoint (per user per minute)
REACTION_RATE_LIMIT_PER_MINUTE = 30

# Cache TTL — short because comments are written frequently
CACHE_TTL_COMMENTS = 120  # 2 minutes
