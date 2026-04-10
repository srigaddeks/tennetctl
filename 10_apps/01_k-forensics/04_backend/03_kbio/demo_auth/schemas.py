"""kbio demo auth schemas.

Pydantic v2 models for demo site registration, login, session, and logout.
Uses kdemo schema — no tennetctl IAM dependency. JWT-based, stateless.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class SecurityQA(BaseModel):
    question: str = Field(..., min_length=5)
    answer: str = Field(..., min_length=1)


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., min_length=5, max_length=100)
    password: str = Field(..., min_length=6, max_length=128)
    phone_number: str | None = Field(default=None, max_length=20)
    mpin: str | None = Field(default=None, min_length=4, max_length=6, pattern=r"^\d{4,6}$")
    security_questions: list[SecurityQA] = Field(
        default_factory=list,
        description="Up to 3 security Q+A pairs",
    )


class RegisterResponse(BaseModel):
    user_id: str
    username: str


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    user_id: str
    username: str
    access_token: str
    token_type: str = "bearer"


class SessionResponse(BaseModel):
    user_id: str
    username: str
    email: str
