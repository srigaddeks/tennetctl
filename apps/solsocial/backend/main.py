"""
SolSocial FastAPI app.

Lifespan: create asyncpg pool against the `solsocial` DB, start the
tennetctl HTTP client, build OAuth adapters + publisher, mount routers.

Auth identity is resolved by SessionProxyMiddleware via tennetctl
`/v1/auth/me`. App-level authorization is enforced by solsocial's own
RBAC tables (`10_solsocial.v_user_permissions`).
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from importlib import import_module

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

_config = import_module("apps.solsocial.backend.01_core.config")
_db = import_module("apps.solsocial.backend.01_core.database")
_middleware = import_module("apps.solsocial.backend.01_core.middleware")
_tennetctl_client = import_module("apps.solsocial.backend.01_core.tennetctl_client")
_providers = import_module("apps.solsocial.backend.02_features.60_oauth.providers")

_channels_routes = import_module("apps.solsocial.backend.02_features.10_channels.routes")
_posts_routes = import_module("apps.solsocial.backend.02_features.20_posts.routes")
_queue_routes = import_module("apps.solsocial.backend.02_features.30_queue.routes")
_calendar_routes = import_module("apps.solsocial.backend.02_features.40_calendar.routes")
_ideas_routes = import_module("apps.solsocial.backend.02_features.50_ideas.routes")
_oauth_routes = import_module("apps.solsocial.backend.02_features.60_oauth.routes")
_provider_apps_routes = import_module("apps.solsocial.backend.02_features.15_provider_apps.routes")
_media_routes = import_module("apps.solsocial.backend.02_features.70_media.routes")
_scheduler = import_module("apps.solsocial.backend.02_features.20_posts.scheduler")


@asynccontextmanager
async def lifespan(application: FastAPI):
    cfg = _config.load_config()
    application.state.config = cfg

    pool = await _db.create_pool(cfg.database_url)
    application.state.pool = pool

    client = _tennetctl_client.TennetCTLClient(
        cfg.tennetctl_url,
        service_api_key=cfg.tennetctl_service_api_key,
        application_code=cfg.application_code,
        org_id=cfg.tennetctl_org_id,
    )
    await client.start()
    application.state.tennetctl = client

    # Resolve this app's tennetctl application_id. Required — every outbound
    # call stamps this value so tennetctl can filter/audit per-app cleanly.
    if cfg.tennetctl_service_api_key and cfg.tennetctl_org_id:
        try:
            app_row = await client.resolve_application(
                code=cfg.application_code, org_id=cfg.tennetctl_org_id,
            )
            if app_row is None:
                print(
                    f"[solsocial] WARNING: application code={cfg.application_code!r} "
                    f"not registered in tennetctl org {cfg.tennetctl_org_id!r}. "
                    f"Run `python -m apps.solsocial.backend.scripts.bootstrap_tennetctl "
                    f"--org-id {cfg.tennetctl_org_id}` to register it.",
                    flush=True,
                )
            else:
                print(
                    f"[solsocial] resolved application_id={app_row['id']} "
                    f"(code={cfg.application_code!r}, org={cfg.tennetctl_org_id!r})",
                    flush=True,
                )
        except Exception as exc:
            print(f"[solsocial] WARNING: could not resolve application: {exc}", flush=True)
    application.state.application_code = cfg.application_code
    application.state.application_id = client.application_id
    application.state.tennetctl_org_id = cfg.tennetctl_org_id

    # Adapters are resolved per-workspace at request time (15_provider_apps
    # reads each workspace's credentials from tennetctl vault). Publisher gets
    # the resolver function so it can pull tokens via vault_reveal on publish.
    _prov_apps = import_module("apps.solsocial.backend.02_features.15_provider_apps.service")
    application.state.publisher = _providers.Publisher(_prov_apps.resolve_adapter)
    # No boot-time adapter inventory — all credentials are in tennetctl vault.
    for code in _providers.SUPPORTED_PROVIDERS:
        kind = "tennetctl-vault"
        print(f"[solsocial] provider {code} → {kind}", flush=True)

    scheduler_task = _scheduler.start(application)

    try:
        yield
    finally:
        await _scheduler.stop(scheduler_task)
        await client.stop()
        await _db.close_pool(pool)


def create_app() -> FastAPI:
    cfg = _config.load_config()
    app = FastAPI(
        title="SolSocial",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[cfg.frontend_origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    _middleware.register(app)

    app.include_router(_channels_routes.router)
    app.include_router(_posts_routes.router)
    app.include_router(_queue_routes.router)
    app.include_router(_calendar_routes.router)
    app.include_router(_ideas_routes.router)
    app.include_router(_oauth_routes.router)
    app.include_router(_provider_apps_routes.router)
    app.include_router(_media_routes.router)

    @app.get("/health")
    async def health() -> dict:
        return {"ok": True, "data": {"service": "solsocial", "status": "healthy"}}

    return app


app = create_app()
