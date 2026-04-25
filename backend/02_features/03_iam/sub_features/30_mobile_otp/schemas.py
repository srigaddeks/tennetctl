"""IAM mobile-OTP — Pydantic v2 schemas."""

from __future__ import annotations

import re
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator

E164_RE = re.compile(r"^\+\d{7,15}$")


class MobileOtpRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    phone_e164: Annotated[str, Field(min_length=8, max_length=16)]

    @field_validator("phone_e164")
    @classmethod
    def _check_phone(cls, v: str) -> str:
        v = v.strip().replace(" ", "").replace("-", "")
        if not E164_RE.match(v):
            raise ValueError("phone must be in E.164 format (e.g. +919876543210)")
        return v


class MobileOtpVerify(BaseModel):
    model_config = ConfigDict(extra="forbid")
    phone_e164: Annotated[str, Field(min_length=8, max_length=16)]
    code: Annotated[str, Field(min_length=4, max_length=10)]
    display_name: Annotated[str | None, Field(max_length=120)] = None
    account_type: Annotated[str, Field(max_length=40)] = "soma_delights_customer"

    @field_validator("phone_e164")
    @classmethod
    def _check_phone(cls, v: str) -> str:
        v = v.strip().replace(" ", "").replace("-", "")
        if not E164_RE.match(v):
            raise ValueError("phone must be in E.164 format (e.g. +919876543210)")
        return v

    @field_validator("code")
    @classmethod
    def _digits(cls, v: str) -> str:
        if not v.isdigit():
            raise ValueError("code must be numeric")
        return v


class MobileOtpRequestResponse(BaseModel):
    sent: bool
    message: str
    debug_code: str | None = None  # Only populated when SMS sender is in stub mode.
