"""
somacrm FastAPI app.

Lifespan creates the asyncpg pool against `tennetctl` Postgres (schema
"12_somacrm"), starts the tennetctl HTTP client, and mounts sub-feature
routers. Auth identity is resolved by SessionProxyMiddleware via
tennetctl `/v1/auth/me`.

Boot port: 51738 (NOT 51734 = tennetctl backend, NOT 51735 = tennetctl
frontend, NOT 51736 = somaerp backend, NOT 51737 = somaerp frontend,
NOT 51739 = somacrm frontend).
"""

from __future__ import annotations

import time
from contextlib import asynccontextmanager
from importlib import import_module

import asyncpg
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

_config = import_module("apps.somacrm.backend.01_core.config")
_db = import_module("apps.somacrm.backend.01_core.database")
_middleware = import_module("apps.somacrm.backend.01_core.middleware")
_tennetctl = import_module("apps.somacrm.backend.01_core.tennetctl_client")

_health_routes = import_module("apps.somacrm.backend.02_features.00_health.routes")
_contacts_routes = import_module("apps.somacrm.backend.02_features.10_contacts.routes")
_organizations_routes = import_module("apps.somacrm.backend.02_features.15_organizations.routes")
_addresses_routes = import_module("apps.somacrm.backend.02_features.20_addresses.routes")
_leads_routes = import_module("apps.somacrm.backend.02_features.25_leads.routes")
_pipeline_stages_routes = import_module("apps.somacrm.backend.02_features.30_pipeline_stages.routes")
_deals_routes = import_module("apps.somacrm.backend.02_features.35_deals.routes")
_activities_routes = import_module("apps.somacrm.backend.02_features.40_activities.routes")
_notes_routes = import_module("apps.somacrm.backend.02_features.45_notes.routes")
_tags_routes = import_module("apps.somacrm.backend.02_features.50_tags.routes")
_reports_routes = import_module("apps.somacrm.backend.02_features.55_reports.routes")


@asynccontextmanager
async def lifespan(application: FastAPI):
    cfg = _config.load_config()
    application.state.config = cfg
    application.state.started_at_monotonic = time.monotonic()

    pool = await _db.create_pool(cfg.database_url)
    application.state.pool = pool

    client = _tennetctl.TennetctlClient(
        cfg.tennetctl_base_url,
        service_api_key=cfg.tennetctl_service_api_key,
    )
    await client.start()
    application.state.tennetctl = client

    try:
        yield
    finally:
        await client.stop()
        await _db.close_pool(pool)


def create_app() -> FastAPI:
    cfg = _config.load_config()
    app = FastAPI(
        title="somacrm",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[cfg.somacrm_frontend_origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    _middleware.register(app)

    _resp = import_module("apps.somacrm.backend.01_core.response")

    @app.exception_handler(asyncpg.exceptions.UniqueViolationError)
    async def _handle_unique(request, exc):
        return JSONResponse(status_code=409, content=_resp.error("CONFLICT", "A record with that value already exists."))

    @app.exception_handler(RequestValidationError)
    async def _handle_validation(request, exc):
        detail = "; ".join(f"{'.'.join(str(l) for l in e['loc'])}: {e['msg']}" for e in exc.errors())
        return JSONResponse(status_code=422, content=_resp.error("VALIDATION_ERROR", detail))

    app.include_router(_health_routes.router)
    app.include_router(_contacts_routes.router)
    app.include_router(_organizations_routes.router)
    app.include_router(_addresses_routes.router)
    app.include_router(_leads_routes.router)
    app.include_router(_pipeline_stages_routes.router)
    app.include_router(_deals_routes.router)
    app.include_router(_activities_routes.router)
    app.include_router(_notes_routes.router)
    app.include_router(_tags_routes.router)
    app.include_router(_tags_routes.entity_tags_router)
    app.include_router(_reports_routes.router)

    @app.get("/health")
    async def health() -> dict:
        return {"ok": True, "data": {"service": "somacrm", "status": "healthy"}}

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    cfg = _config.load_config()
    uvicorn.run(
        "apps.somacrm.backend.main:app",
        host="0.0.0.0",
        port=cfg.somacrm_port,
        reload=cfg.somacrm_debug,
    )
