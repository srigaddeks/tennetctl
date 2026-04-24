"""
somaerp FastAPI app.

Lifespan creates the asyncpg pool against `tennetctl` Postgres (schema
"11_somaerp"), starts the tennetctl HTTP client, and mounts sub-feature
routers. Auth identity is resolved by SessionProxyMiddleware via
tennetctl `/v1/auth/me`.

Boot port: 51736 (NOT 51734 = tennetctl backend, NOT 51735 = tennetctl
frontend, NOT 51737 = somaerp frontend).
"""

from __future__ import annotations

import time
from contextlib import asynccontextmanager
from importlib import import_module

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

_config = import_module("apps.somaerp.backend.01_core.config")
_db = import_module("apps.somaerp.backend.01_core.database")
_middleware = import_module("apps.somaerp.backend.01_core.middleware")
_tennetctl = import_module("apps.somaerp.backend.01_core.tennetctl_client")

_health_routes = import_module("apps.somaerp.backend.02_features.00_health.routes")
_locations_routes = import_module(
    "apps.somaerp.backend.02_features.10_locations.routes",
)
_kitchens_routes = import_module(
    "apps.somaerp.backend.02_features.15_kitchens.routes",
)
_service_zones_routes = import_module(
    "apps.somaerp.backend.02_features.17_service_zones.routes",
)
_kitchen_capacity_routes = import_module(
    "apps.somaerp.backend.02_features.16_kitchen_capacity.routes",
)
_product_lines_routes = import_module(
    "apps.somaerp.backend.02_features.20_product_lines.routes",
)
_products_routes = import_module(
    "apps.somaerp.backend.02_features.25_products.routes",
)
_raw_materials_routes = import_module(
    "apps.somaerp.backend.02_features.30_raw_materials.routes",
)
_suppliers_routes = import_module(
    "apps.somaerp.backend.02_features.35_suppliers.routes",
)
_recipes_routes = import_module(
    "apps.somaerp.backend.02_features.40_recipes.routes",
)
_equipment_routes = import_module(
    "apps.somaerp.backend.02_features.45_equipment.routes",
)
_quality_routes = import_module(
    "apps.somaerp.backend.02_features.50_quality.routes",
)
_procurement_routes = import_module(
    "apps.somaerp.backend.02_features.60_procurement.routes",
)
_inventory_routes = import_module(
    "apps.somaerp.backend.02_features.65_inventory.routes",
)
_production_batches_routes = import_module(
    "apps.somaerp.backend.02_features.70_production_batches.routes",
)
_customers_routes = import_module(
    "apps.somaerp.backend.02_features.80_customers.routes",
)
_subscriptions_routes = import_module(
    "apps.somaerp.backend.02_features.85_subscriptions.routes",
)
_delivery_routes_routes = import_module(
    "apps.somaerp.backend.02_features.90_delivery_routes.routes",
)
_riders_routes = import_module(
    "apps.somaerp.backend.02_features.93_riders.routes",
)
_delivery_runs_routes = import_module(
    "apps.somaerp.backend.02_features.95_delivery_runs.routes",
)
_reports_routes = import_module(
    "apps.somaerp.backend.02_features.99_reports.routes",
)


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
        title="somaerp",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[cfg.somaerp_frontend_origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    _middleware.register(app)

    app.include_router(_health_routes.router)
    app.include_router(_locations_routes.router)
    app.include_router(_kitchens_routes.router)
    app.include_router(_service_zones_routes.router)
    app.include_router(_kitchen_capacity_routes.router)
    app.include_router(_product_lines_routes.router)
    app.include_router(_products_routes.router)
    app.include_router(_raw_materials_routes.router)
    app.include_router(_suppliers_routes.router)
    app.include_router(_recipes_routes.router)
    app.include_router(_equipment_routes.router)
    app.include_router(_equipment_routes.kitchen_equipment_router)
    app.include_router(_quality_routes.router)
    app.include_router(_procurement_routes.router)
    app.include_router(_inventory_routes.router)
    app.include_router(_production_batches_routes.router)
    app.include_router(_customers_routes.router)
    app.include_router(_subscriptions_routes.router)
    app.include_router(_delivery_routes_routes.router)
    app.include_router(_riders_routes.router)
    app.include_router(_delivery_runs_routes.router)
    app.include_router(_reports_routes.router)

    @app.get("/health")
    async def health() -> dict:
        return {"ok": True, "data": {"service": "somaerp", "status": "healthy"}}

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    cfg = _config.load_config()
    uvicorn.run(
        "apps.somaerp.backend.main:app",
        host="0.0.0.0",
        port=cfg.somaerp_port,
        reload=cfg.somaerp_debug,
    )
