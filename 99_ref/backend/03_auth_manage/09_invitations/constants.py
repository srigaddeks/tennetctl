from __future__ import annotations

from enum import StrEnum


class InviteScope(StrEnum):
    PLATFORM = "platform"
    ORGANIZATION = "organization"
    WORKSPACE = "workspace"


class InviteStatus(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REVOKED = "revoked"
    EXPIRED = "expired"
    DECLINED = "declined"


VALID_ORG_ROLES = {"owner", "admin", "member", "viewer", "billing"}
VALID_WORKSPACE_ROLES = {"owner", "admin", "contributor", "viewer", "readonly"}
