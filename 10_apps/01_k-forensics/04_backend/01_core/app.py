"""k-forensics FastAPI application factory.

Gateway that proxies IAM/auth requests to the tennetctl backend and will
serve forensics-specific APIs directly (Phase 2).

Run with:
    cd 10_apps/01_k-forensics/04_backend
    KF_TENNETCTL_API_URL=http://localhost:58000 \
      .venv/bin/python -m uvicorn 01_core.app:app \
        --host 0.0.0.0 --port 8100 --reload
"""

from __future__ import annotations

import sys
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

import httpx
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware

# Ensure the backend root is on sys.path so 02_proxy can be imported.
_backend_root = Path(__file__).resolve().parent.parent
if str(_backend_root) not in sys.path:
    sys.path.insert(0, str(_backend_root))

import importlib

from fastapi.responses import JSONResponse

_config = importlib.import_module("01_core.config")
_db = importlib.import_module("01_core.db")
_valkey = importlib.import_module("01_core.valkey")
_qdrant = importlib.import_module("01_core.qdrant")
_proxy = importlib.import_module("02_proxy.middleware")
_errors = importlib.import_module("01_core.errors")
_ingest_routes = importlib.import_module("03_kbio.ingest.routes")
_drift_routes = importlib.import_module("03_kbio.drift.routes")
_profile_routes = importlib.import_module("03_kbio.profile.routes")
_challenge_routes = importlib.import_module("03_kbio.challenge.routes")
_devices_routes = importlib.import_module("03_kbio.devices.routes")
_trust_routes = importlib.import_module("03_kbio.trust.routes")
_policies_routes = importlib.import_module("03_kbio.policies.routes")
_api_keys_routes = importlib.import_module("03_kbio.api_keys.routes")
_signals_routes = importlib.import_module("03_kbio.signals.routes")
_threat_types_routes = importlib.import_module("03_kbio.threat_types.routes")
_demo_auth_routes = importlib.import_module("03_kbio.demo_auth.routes")
get_settings = _config.get_settings
mount_proxy = _proxy.mount_proxy


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    app.state.upstream_url = settings.tennetctl_api_url.rstrip("/")
    app.state.proxy_client = httpx.AsyncClient(
        timeout=httpx.Timeout(connect=10.0, read=60.0, write=30.0, pool=10.0),
        limits=httpx.Limits(max_connections=50, max_keepalive_connections=20),
        follow_redirects=False,
    )
    await _db.init_pool(settings.kbio_database_url)
    await _valkey.init_client(settings.valkey_url)
    await _qdrant.init_client(settings.qdrant_url)
    try:
        yield
    finally:
        await app.state.proxy_client.aclose()
        await _db.close_pool()
        await _valkey.close_client()
        await _qdrant.close_client()


def create_app() -> FastAPI:
    from fastapi.middleware.cors import CORSMiddleware

    settings = get_settings()

    fastapi_app = FastAPI(
        title="k-forensics",
        version="0.0.1",
        lifespan=lifespan,
    )

    fastapi_app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    fastapi_app.add_middleware(RequestIdMiddleware)

    @fastapi_app.exception_handler(_errors.AppError)
    async def app_error_handler(request: Request, exc: _errors.AppError):
        return JSONResponse(
            status_code=exc.status_code,
            content={"ok": False, "error": {"code": exc.code, "message": exc.message}},
        )

    @fastapi_app.get("/healthz")
    async def healthz() -> dict:
        return {"ok": True, "data": {"status": "ok"}}

    # -- kbio routers (must be before proxy catch-all) --
    fastapi_app.include_router(_ingest_routes.router)
    fastapi_app.include_router(_drift_routes.router)
    fastapi_app.include_router(_profile_routes.router)
    fastapi_app.include_router(_challenge_routes.router)
    fastapi_app.include_router(_devices_routes.router)
    fastapi_app.include_router(_trust_routes.router)
    fastapi_app.include_router(_policies_routes.router)
    fastapi_app.include_router(_api_keys_routes.router)
    fastapi_app.include_router(_signals_routes.router)
    fastapi_app.include_router(_threat_types_routes.router)
    fastapi_app.include_router(_demo_auth_routes.router)

    # Catch-all proxy to tennetctl — must be mounted LAST
    mount_proxy(fastapi_app)

    return fastapi_app


app = create_app()
