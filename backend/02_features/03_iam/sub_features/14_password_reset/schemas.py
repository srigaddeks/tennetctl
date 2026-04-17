"""Pydantic schemas for iam.password_reset."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr


class PasswordResetRequestBody(BaseModel):
    email: EmailStr


class PasswordResetCompleteBody(BaseModel):
    token: str
    new_password: str
