from __future__ import annotations

MAGIC_LINK_DEFAULT_TTL_HOURS: int = 24
MAGIC_LINK_MAX_TTL_HOURS: int = 168   # 7 days
MAGIC_LINK_MIN_TTL_HOURS: int = 1
MAGIC_LINK_RATE_LIMIT_PER_HOUR: int = 5  # max requests per email per hour
MAGIC_LINK_CHALLENGE_TYPE: str = "magic_link"
MAGIC_LINK_ASSIGNEE_CHALLENGE_TYPE: str = "magic_link_assignee"
ASSIGNEE_PORTAL_MODE: str = "assignee"
