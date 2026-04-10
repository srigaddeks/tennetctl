"""kbio demo auth routes.

Demo site registration, login, session validation, and logout.
All endpoints require X-API-Key header for app-level auth.
JWT is passed via Authorization: Bearer <token>.
No Valkey — sessions are stateless.
"""
from __future__ import annotations

import importlib

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, Response

_db = importlib.import_module("01_core.db")
_resp = importlib.import_module("01_core.response")
_errors = importlib.import_module("01_core.errors")
_auth = importlib.import_module("01_core.api_key_auth")

from .schemas import LoginRequest, RegisterRequest
from .service import login_user, register_user, validate_session

router = APIRouter(prefix="/v1/demo-auth", tags=["kbio-demo-auth"])


@router.post("/register", status_code=201, summary="Register a demo user")
async def register_endpoint(body: RegisterRequest, request: Request):
    await _auth.validate_api_key(request)

    pool = _db.get_pool()
    async with pool.acquire() as conn:
        try:
            result = await register_user(
                conn,
                username=body.username,
                email=body.email,
                password=body.password,
                phone_number=body.phone_number,
                mpin=body.mpin,
                security_questions=[qa.model_dump() for qa in body.security_questions],
            )
        except _errors.AppError as exc:
            return JSONResponse(
                status_code=exc.status_code,
                content={"ok": False, "error": {"code": exc.code, "message": exc.message}},
            )

    return _resp.success_response(result.model_dump())


@router.post("/login", summary="Authenticate a demo user — returns JWT")
async def login_endpoint(body: LoginRequest, request: Request):
    await _auth.validate_api_key(request)

    pool = _db.get_pool()
    async with pool.acquire() as conn:
        try:
            result = await login_user(conn, username=body.username, password=body.password)
        except _errors.AppError as exc:
            return JSONResponse(
                status_code=exc.status_code,
                content={"ok": False, "error": {"code": exc.code, "message": exc.message}},
            )

    return _resp.success_response(result.model_dump())


@router.get("/session", summary="Validate JWT and return session info")
async def session_endpoint(request: Request):
    await _auth.validate_api_key(request)

    token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
    pool = _db.get_pool()
    async with pool.acquire() as conn:
        result = await validate_session(conn, token)

    if not result:
        return JSONResponse(
            status_code=401,
            content={"ok": False, "error": {"code": "INVALID_TOKEN", "message": "Token invalid or expired."}},
        )

    return _resp.success_response(result.model_dump())


@router.post("/logout", status_code=204, summary="Logout — client should discard the JWT")
async def logout_endpoint(request: Request) -> Response:
    await _auth.validate_api_key(request)
    # Stateless JWT — nothing to invalidate server-side.
    return Response(status_code=204)
