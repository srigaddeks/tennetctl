from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from ..schemas import AuthUserResponse


class StartImpersonationRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    target_user_id: Annotated[str, Field(min_length=1, max_length=64)]
    reason: Annotated[str, Field(min_length=5, max_length=500)]


class StartImpersonationResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    refresh_token: str
    refresh_expires_in: int
    target_user: AuthUserResponse
    impersonation_session_id: str


class EndImpersonationResponse(BaseModel):
    message: str
    impersonator_user_id: str


class ImpersonationStatusResponse(BaseModel):
    is_impersonating: bool
    impersonator_id: str | None = None
    target_user_id: str | None = None
    session_id: str | None = None
    expires_at: str | None = None
