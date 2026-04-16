from __future__ import annotations
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Annotated

class RequestMagicLinkRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    email: Annotated[EmailStr, Field(min_length=3, max_length=320)]

class RequestMagicLinkResponse(BaseModel):
    message: str
    magic_link_token: str | None = None
