"""Pydantic schemas for dashboard sharing."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CreateInternalShareRequest(BaseModel):
    """Request to grant access to an internal user."""

    scope: str = Field("internal_user", description="Must be 'internal_user'")
    granted_to_user_id: str = Field(..., description="User UUID to grant access to")
    expires_at: Optional[datetime] = Field(
        None, description="Share expiration time; NULL = no expiry"
    )


class CreatePublicShareRequest(BaseModel):
    """Request to create a public token share."""

    scope: str = Field("public_token", description="Must be 'public_token'")
    expires_at: Optional[datetime] = Field(
        None, description="Token expiration time; NULL = no expiry"
    )
    passphrase: Optional[str] = Field(
        None, description="Optional passphrase to protect the share"
    )
    recipient_email: Optional[str] = Field(
        None, description="Email address of intended recipient (for audit)"
    )


class DashboardShareResponse(BaseModel):
    """Dashboard share grant response."""

    id: str = Field(..., description="Share UUID")
    dashboard_id: str
    scope_code: str = Field(..., description="internal_user or public_token")
    granted_by_user_id: str
    granted_to_user_id: Optional[str] = None
    grantee_display: Optional[str] = None
    recipient_email: Optional[str] = None
    status: str = Field(..., description="active | expired | revoked")
    has_passphrase: bool = False
    view_count: int = 0
    last_viewed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    created_at: datetime


class DashboardShareDetailResponse(DashboardShareResponse):
    """Detailed share response (includes token for new public shares only)."""

    token: Optional[str] = Field(
        None, description="Plaintext token (returned only on creation)"
    )
    token_hash: Optional[str] = None


class DashboardShareEventResponse(BaseModel):
    """Share event from timeline."""

    id: str = Field(..., description="Event UUID")
    kind_code: str = Field(..., description="granted | viewed | token_minted | etc")
    actor_user_id: Optional[str] = None
    viewer_email: Optional[str] = None
    viewer_ip: Optional[str] = None
    viewer_ua: Optional[str] = None
    payload: dict = Field(default_factory=dict)
    occurred_at: datetime


class UpdateShareRequest(BaseModel):
    """Request to update a share (extend, rotate, passphrase, revoke)."""

    expires_at: Optional[datetime] = Field(
        None, description="Extend or clear expiration"
    )
    passphrase: Optional[str] = Field(None, description="Set or clear passphrase")
    rotate_token: bool = Field(False, description="Mint a new token (public shares only)")
    revoked_at: Optional[str] = Field(
        None, description="Set to 'now' to revoke immediately"
    )


class UnlockPublicShareRequest(BaseModel):
    """Request to unlock a passphrase-protected public share."""

    passphrase: str = Field(..., description="Passphrase to verify")
