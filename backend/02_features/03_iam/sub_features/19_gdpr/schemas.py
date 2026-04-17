"""
iam.gdpr — Pydantic v2 schemas.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ExportRequestIn(BaseModel):
    """POST /v1/account/data-export"""
    # No body required — authenticated user's own data.


class EraseRequestIn(BaseModel):
    """POST /v1/account/delete-me"""
    password: str = Field(..., description="Current password for re-authentication")
    totp_code: str | None = Field(None, description="TOTP code if enrolled")
    confirm: Literal["DELETE"] = Field(..., description='Must be the literal string "DELETE"')


class GdprJobOut(BaseModel):
    id: str
    user_id: str
    kind: str
    status: str
    requested_at: datetime
    completed_at: datetime | None
    hard_erase_at: datetime | None


class GdprStatusOut(BaseModel):
    export: GdprJobOut | None
    erase: GdprJobOut | None
