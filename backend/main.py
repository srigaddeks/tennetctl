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
    "vault": "backend.02_features.02_vault.routes",
    "iam": "backend.02_features.03_iam.routes",
    "featureflags": "backend.02_features.09_featureflags.routes",
    "audit": "backend.02_features.04_audit.routes",
    "notify": "backend.02_features.06_notify.routes",
    # "monitoring": "backend.02_features.05_monitoring.routes",
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

    # Vault lifespan — only when the module is enabled. Blocks startup if the
    # root key is missing (ADR-028).
    if "vault" in config.modules:
        _vault_crypto = import_module("backend.02_features.02_vault.crypto")
        _vault_client_mod = import_module("backend.02_features.02_vault.client")
        _vault_bootstrap = import_module("backend.02_features.02_vault.bootstrap")

        root_key = _vault_crypto.load_root_key()
        vault = _vault_client_mod.VaultClient(pool, root_key)
        application.state.vault = vault

        inserted = await _vault_bootstrap.ensure_bootstrap_secrets(pool, vault)
        if inserted > 0:
            logger.info("Vault bootstrap: %d new secret(s) seeded.", inserted)

    # Notify workers — only when the module is enabled.
    _notify_worker_task = None
    _notify_email_task = None
    _notify_webpush_task = None
    _notify_campaign_task = None
    if "notify" in config.modules:
        _notify_worker = import_module("backend.02_features.06_notify.worker")
        _notify_worker_task = _notify_worker.start_worker(pool)
        logger.info("Notify subscription worker started.")

        _notify_email_svc = import_module(
            "backend.02_features.06_notify.sub_features.07_email.service"
        )
        _base_tracking_url = f"http://localhost:{config.app_port}"
        _notify_email_task = _notify_email_svc.start_email_sender(
            pool, application.state.vault, _base_tracking_url
        )
        logger.info("Notify email sender started.")

        _notify_webpush_svc = import_module(
            "backend.02_features.06_notify.sub_features.08_webpush.service"
        )
        await _notify_webpush_svc.ensure_vapid_keys(pool, application.state.vault)
        logger.info("VAPID keys ready.")
        _notify_webpush_task = _notify_webpush_svc.start_webpush_sender(
            pool, application.state.vault
        )
        logger.info("Notify webpush sender started.")

        _campaign_runner = import_module(
            "backend.02_features.06_notify.campaign_runner"
        )
        _notify_campaign_task = _campaign_runner.start_campaign_runner(pool)
        logger.info("Notify campaign runner started.")

    yield

    if _notify_worker_task is not None:
        _notify_worker_task.cancel()
        import asyncio as _asyncio
        await _asyncio.gather(_notify_worker_task, return_exceptions=True)
        logger.info("Notify subscription worker stopped.")

    if _notify_email_task is not None:
        _notify_email_task.cancel()
        import asyncio as _asyncio
        await _asyncio.gather(_notify_email_task, return_exceptions=True)
        logger.info("Notify email sender stopped.")

    if _notify_webpush_task is not None:
        _notify_webpush_task.cancel()
        import asyncio as _asyncio
        await _asyncio.gather(_notify_webpush_task, return_exceptions=True)
        logger.info("Notify webpush sender stopped.")

    if _notify_campaign_task is not None:
        _notify_campaign_task.cancel()
        import asyncio as _asyncio
        await _asyncio.gather(_notify_campaign_task, return_exceptions=True)
        logger.info("Notify campaign runner stopped.")

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


_catalog_routes = import_module("backend.01_catalog.routes")
app.include_router(_catalog_routes.router)


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
