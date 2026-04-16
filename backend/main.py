"""
TennetCTL — FastAPI application entry point.

Start: cd tennetctl && .venv/bin/python -m uvicorn backend.main:app --port 51734 --host 0.0.0.0 --reload
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from importlib import import_module

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

_config = import_module("backend.01_core.config")
_db = import_module("backend.01_core.database")
_response = import_module("backend.01_core.response")
_middleware = import_module("backend.01_core.middleware")
_catalog = import_module("backend.01_catalog")

logger = logging.getLogger("tennetctl")

# Module name → router import path mapping
# Populated as features are built. Module gating checks config.modules
# before importing/mounting each router.
MODULE_ROUTERS: dict[str, str] = {
    # "iam": "backend.02_features.iam.routes",
    # "audit": "backend.02_features.audit.routes",
    # "monitoring": "backend.02_features.monitoring.routes",
}


@asynccontextmanager
async def lifespan(application: FastAPI):
    """App lifespan — create DB pool on startup, close on shutdown."""
    config = _config.load_config()

    pool = await _db.create_pool(config.database_url)
    application.state.pool = pool
    application.state.config = config

    logger.info(
        "TennetCTL started — modules: %s, single_tenant: %s",
        ",".join(sorted(config.modules)),
        config.single_tenant,
    )

    # Boot catalog: discover feature manifests, validate, upsert into 01_catalog.
    # See NCP v1 §11 (boot sequence). Failure raises — uvicorn exits.
    report = await _catalog.upsert_all(pool, config.modules)
    logger.info(
        "Catalog upsert: %d features, %d sub-features, %d nodes (%d deprecated)",
        report.features_upserted,
        report.sub_features_upserted,
        report.nodes_upserted,
        report.deprecated,
    )

    yield

    await _db.close_pool(pool)
    logger.info("TennetCTL stopped.")


app = FastAPI(
    title="TennetCTL",
    version="0.0.0",
    lifespan=lifespan,
)

# CORS — allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:51735"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register middleware (error handler + request ID)
_middleware.register_middleware(app)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return _response.success({"status": "healthy"})


def _mount_module_routers(application: FastAPI, modules: frozenset[str]) -> None:
    """Mount routers only for enabled modules."""
    for module_name, router_path in MODULE_ROUTERS.items():
        if module_name in modules:
            try:
                router_module = import_module(router_path)
                application.include_router(router_module.router)
                logger.info("Mounted module: %s", module_name)
            except ImportError:
                logger.warning("Module %s not found at %s — skipping", module_name, router_path)


# Mount module routers based on config
# Done at import time so uvicorn picks up all routes
_startup_config = _config.load_config()
_mount_module_routers(app, _startup_config.modules)
