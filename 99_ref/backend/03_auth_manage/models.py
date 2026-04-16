from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class AccessTokenClaims:
    subject: str
    session_id: str
    tenant_key: str
    expires_at: datetime
    portal_mode: str | None = None
    is_impersonation: bool = False
    impersonator_id: str | None = None
    impersonator_session_id: str | None = None
    is_api_key: bool = False
    api_key_id: str | None = None
    api_key_scopes: tuple[str, ...] | None = None


@dataclass(frozen=True, slots=True)
class AuthenticatedUser:
    user_id: str
    tenant_key: str
    email: str
    username: str | None
    email_verified: bool
    account_status: str
    user_category: str = "full"


@dataclass(frozen=True, slots=True)
class UserAuthRecord:
    user_id: str
    tenant_key: str
    email: str
    username: str | None
    email_verified: bool
    account_status: str
    password_hash: str


@dataclass(frozen=True, slots=True)
class SessionRecord:
    session_id: str
    user_id: str
    tenant_key: str
    refresh_token_hash: str
    refresh_token_expires_at: datetime
    revoked_at: datetime | None
    rotation_counter: int
    portal_mode: str | None = None
    is_impersonation: bool = False
    impersonator_user_id: str | None = None


@dataclass(frozen=True, slots=True)
class AccessSessionState:
    session_id: str
    user_id: str
    tenant_key: str
    refresh_token_expires_at: datetime
    revoked_at: datetime | None
    user_is_active: bool
    user_is_disabled: bool
    user_is_deleted: bool
    user_is_locked: bool
    portal_mode: str | None = None
    user_category: str = "full"


@dataclass(frozen=True, slots=True)
class PasswordResetChallengeRecord:
    challenge_id: str
    user_id: str | None
    tenant_key: str
    target_value: str
    secret_hash: str
    expires_at: datetime
    consumed_at: datetime | None


@dataclass(frozen=True, slots=True)
class PasswordlessChallengeRecord:
    challenge_id: str
    user_id: str | None
    tenant_key: str
    challenge_type_code: str
    target_value: str
    secret_hash: str
    expires_at: datetime
    consumed_at: datetime | None


@dataclass(frozen=True, slots=True)
class UserPropertyRecord:
    id: str
    user_id: str
    property_key: str
    property_value: str


@dataclass(frozen=True, slots=True)
class UserAccountRecord:
    id: str
    user_id: str
    tenant_key: str
    account_type_code: str
    is_primary: bool
    is_active: bool
    is_disabled: bool
    is_deleted: bool
    is_locked: bool


@dataclass(frozen=True, slots=True)
class UserAccountPropertyRecord:
    id: str
    user_account_id: str
    property_key: str
    property_value: str


@dataclass(frozen=True, slots=True)
class MagicLinkUserRecord:
    """Lightweight user record used during magic link request/verify flows."""
    user_id: str
    tenant_key: str
    email: str
    username: str | None
    email_verified: bool
    account_status: str
    user_category: str
    is_active: bool
    is_disabled: bool
    is_deleted: bool
    is_locked: bool
