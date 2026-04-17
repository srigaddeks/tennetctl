"""
iam.credentials — Pydantic v2 API models.

One endpoint today (PATCH /v1/credentials/me). Body carries the current
password so the operation is authenticated twice: once by session, once by
password knowledge. Cleartext never propagates beyond the service.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class PasswordChangeBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    current_password: str = Field(min_length=1, max_length=512)
    new_password: str = Field(min_length=8, max_length=512)
