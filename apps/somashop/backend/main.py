"""
somashop — customer-facing app on tennetctl backbone.

Stateless: no own DB schema. Every read/write goes through tennetctl
(IAM, mobile-OTP, audit, vault) or somaerp (catalog, subscriptions,
deliveries) over HTTP.

Boot port: 51740 (NOT 51734=tennetctl-be, 51735=tennetctl-fe,
51736=somaerp-be, 51737=somaerp-fe, 51738=somacrm-be, 51739=somacrm-fe).
"""

from __future__ import annotations

import time
from contextlib import asynccontextmanager
from importlib import import_module

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

_config = import_module("apps.somashop.backend.01_core.config")
_proxy = import_module("apps.somashop.backend.01_core.proxy")
_resp = import_module("apps.somashop.backend.01_core.response")

_health_routes = import_module("apps.somashop.backend.02_features.00_health.routes")
_products_routes = import_module("apps.somashop.backend.02_features.10_products.routes")
_orders_routes = import_module("apps.somashop.backend.02_features.20_orders.routes")


async def _mint_service_session(tnc, email: str | None,
                                 password: str | None) -> str | None:
    """Sign in the service identity to get a session token.

    somaerp's middleware only accepts session tokens (validates via
    /v1/auth/me). So somashop signs in once at boot, holds the token,
    uses it for tenant-scoped reads (catalog, plans). The session is
    long-lived (default 30 days) — we don't bother refreshing in v1.
    """
    if not email or not password:
        return None
    try:
        r = await tnc.request("POST", "/v1/auth/signin", json={"email": email, "password": password})
        return (r.get("data") or {}).get("token")
    except Exception:
        return None


@asynccontextmanager
async def lifespan(app_: FastAPI):
    import os
    cfg = _config.load_config()
    app_.state.config = cfg
    app_.state.started_at_monotonic = time.monotonic()

    tnc = _proxy.HttpProxy(
        cfg.tennetctl_base_url,
        service_api_key=cfg.tennetctl_service_api_key,
    )
    erp = _proxy.HttpProxy(
        cfg.somaerp_base_url,
        service_api_key=cfg.tennetctl_service_api_key,
    )
    crm = _proxy.HttpProxy(
        cfg.somacrm_base_url or "http://localhost:51738",
        service_api_key=cfg.tennetctl_service_api_key,
    )
    await tnc.start()
    await erp.start()
    await crm.start()

    # Sign in service identity for tenant-scoped reads on somaerp.
    service_token = await _mint_service_session(
        tnc,
        os.environ.get("SOMASHOP_SERVICE_EMAIL"),
        os.environ.get("SOMASHOP_SERVICE_PASSWORD"),
    )
    if service_token:
        erp.set_service_session_token(service_token)
        crm.set_service_session_token(service_token)
        tnc.set_service_session_token(service_token)

    app_.state.tennetctl = tnc
    app_.state.somaerp = erp
    app_.state.somacrm = crm

    try:
        yield
    finally:
        await tnc.stop()
        await erp.stop()
        await crm.stop()


def create_app() -> FastAPI:
    cfg = _config.load_config()
    app_ = FastAPI(title="somashop", version="0.1.0", lifespan=lifespan)

    app_.add_middleware(
        CORSMiddleware,
        allow_origins=[cfg.somashop_frontend_origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app_.exception_handler(RequestValidationError)
    async def _on_validation(request, exc):  # noqa: ARG001
        detail = "; ".join(
            f"{'.'.join(str(loc) for loc in e['loc'])}: {e['msg']}" for e in exc.errors()
        )
        return JSONResponse(status_code=422, content=_resp.error("VALIDATION_ERROR", detail))

    app_.include_router(_health_routes.router)
    app_.include_router(_products_routes.router)
    app_.include_router(_orders_routes.router)

    return app_


app = create_app()


if __name__ == "__main__":
    import uvicorn

    cfg = _config.load_config()
    uvicorn.run(
        "apps.somashop.backend.main:app",
        host="0.0.0.0",
        port=cfg.somashop_port,
        reload=cfg.somashop_debug,
    )
