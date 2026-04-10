"""k-protect FastAPI application factory.

Gateway that proxies IAM/auth requests to the tennetctl backend and will
serve kprotect-specific APIs directly (Phase 2: policy evaluation engine).

Run with:
    cd 10_apps/02_k-protect/04_backend
    KP_TENNETCTL_API_URL=http://localhost:58000 \
      .venv/bin/python -m uvicorn 01_core.app:app \
        --host 0.0.0.0 --port 8200 --reload
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

_config = importlib.import_module("01_core.config")
_db = importlib.import_module("01_core.db")
_valkey = importlib.import_module("01_core.valkey")
_proxy = importlib.import_module("02_proxy.middleware")
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
    await _db.init_pool(settings.database_url)
    await _valkey.init_client(settings.valkey_url)
    try:
        yield
    finally:
        await app.state.proxy_client.aclose()
        await _db.close_pool()
        await _valkey.close_client()


def create_app() -> FastAPI:
    from fastapi.middleware.cors import CORSMiddleware

    settings = get_settings()

    fastapi_app = FastAPI(
        title="k-protect",
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

    @fastapi_app.get("/healthz")
    async def healthz() -> dict:
        return {"ok": True, "data": {"status": "ok"}}

    # -- kprotect routers (mount before proxy so they take precedence) --
    _policy_selections = importlib.import_module("02_features.policy_selections.routes")
    fastapi_app.include_router(_policy_selections.router)

    _signal_selections = importlib.import_module("02_features.signal_selections.routes")
    fastapi_app.include_router(_signal_selections.router)

    _policy_sets_mod = importlib.import_module("02_features.policy_sets.routes")
    fastapi_app.include_router(_policy_sets_mod.router)

    _library = importlib.import_module("02_features.library.routes")
    fastapi_app.include_router(_library.router)

    _decisions_mod = importlib.import_module("02_features.decisions.routes")
    fastapi_app.include_router(_decisions_mod.router)

    _evaluate = importlib.import_module("02_features.evaluate.routes")
    fastapi_app.include_router(_evaluate.router)

    # Catch-all proxy to tennetctl — must be mounted LAST
    mount_proxy(fastapi_app)

    return fastapi_app


app = create_app()
