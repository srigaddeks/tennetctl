"""kbio demo auth service.

Registration, login, and session validation for the kbio SDK demo site.
Uses kdemo schema — no tennetctl IAM, no Valkey.
Sessions are stateless JWT (HS256, 8-hour TTL).
"""
from __future__ import annotations

import importlib
import os
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

_errors = importlib.import_module("01_core.errors")

from .repository import (
    create_user,
    get_user_by_username,
    get_user_credentials,
    insert_security_question,
)
from .schemas import LoginResponse, RegisterResponse, SessionResponse

_JWT_SECRET = os.environ.get("KDEMO_JWT_SECRET", "kdemo-dev-secret-change-in-prod")
_JWT_ALGORITHM = "HS256"
_JWT_TTL_HOURS = 8


def _hash(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def _verify(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def _make_jwt(user_id: str, username: str) -> str:
    exp = datetime.now(timezone.utc) + timedelta(hours=_JWT_TTL_HOURS)
    return jwt.encode(
        {"sub": user_id, "username": username, "exp": exp},
        _JWT_SECRET,
        algorithm=_JWT_ALGORITHM,
    )


def _decode_jwt(token: str) -> dict | None:
    try:
        return jwt.decode(token, _JWT_SECRET, algorithms=[_JWT_ALGORITHM])
    except JWTError:
        return None


async def register_user(
    conn,
    *,
    username: str,
    email: str,
    password: str,
    phone_number: str | None,
    mpin: str | None,
    security_questions: list[dict],
) -> RegisterResponse:
    existing = await get_user_by_username(conn, username)
    if existing:
        raise _errors.AppError("USERNAME_TAKEN", f"Username '{username}' is already registered.", 409)

    user_id = await create_user(
        conn,
        username=username,
        email=email,
        password_hash=_hash(password),
        phone_number=phone_number,
        mpin_hash=_hash(mpin) if mpin else None,
    )

    for i, qa in enumerate(security_questions[:3], start=1):
        await insert_security_question(
            conn,
            user_id=user_id,
            position=i,
            question=qa["question"],
            answer_hash=_hash(qa["answer"].lower().strip()),
        )

    return RegisterResponse(user_id=user_id, username=username)


async def login_user(conn, *, username: str, password: str) -> LoginResponse:
    user = await get_user_credentials(conn, username)
    if not user:
        raise _errors.AppError("INVALID_CREDENTIALS", "Invalid username or password.", 401)

    if user["status"] != "active":
        raise _errors.AppError("ACCOUNT_LOCKED", "Account is locked or suspended.", 403)

    if not _verify(password, user["password_hash"]):
        raise _errors.AppError("INVALID_CREDENTIALS", "Invalid username or password.", 401)

    return LoginResponse(
        user_id=str(user["id"]),
        username=user["username"],
        access_token=_make_jwt(str(user["id"]), user["username"]),
    )


async def validate_session(conn, token: str) -> SessionResponse | None:
    payload = _decode_jwt(token)
    if not payload:
        return None

    user = await get_user_by_username(conn, payload["username"])
    if not user or user.get("status") != "active":
        return None

    return SessionResponse(
        user_id=payload["sub"],
        username=payload["username"],
        email=user["email"],
    )
