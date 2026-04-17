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
_nats_core = import_module("backend.01_core.nats")

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
    "monitoring": "backend.02_features.05_monitoring.routes",
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

    # IAM auth policy — always-on. Registers AuthPolicy on app.state and seeds
    # iam.policy.* defaults into vault.configs on first boot (idempotent).
    _auth_policy_mod = import_module("backend.02_features.03_iam.auth_policy")
    _auth_policy_bootstrap = import_module(
        "backend.02_features.03_iam.auth_policy_bootstrap"
    )
    auth_policy = _auth_policy_mod.AuthPolicy(pool)
    application.state.auth_policy = auth_policy

    if "vault" in config.modules:
        _ap_inserted = await _auth_policy_bootstrap.ensure_policy_defaults(pool)
        if _ap_inserted > 0:
            logger.info("Auth policy bootstrap: %d default(s) seeded.", _ap_inserted)
        # Wire invalidation: vault.configs writes that touch iam.policy.* bust cache.
        _vault_configs_svc = import_module(
            "backend.02_features.02_vault.sub_features.02_configs.service"
        )
        _vault_configs_svc.set_auth_policy_ref(auth_policy)

    # Monitoring — JetStream bootstrap (best-effort; optional module).
    _monitoring_worker_pool = None
    if "monitoring" in config.modules and config.monitoring_enabled:
        _nats_ok = False
        try:
            await _nats_core.connect(config.nats_url)
            _jetstream_bootstrap = import_module(
                "backend.02_features.05_monitoring.bootstrap.jetstream"
            )
            await _jetstream_bootstrap.bootstrap_monitoring_jetstream(
                _nats_core.get_js()
            )
            _nats_ok = True
            logger.info(
                "monitoring: jetstream streams MONITORING_LOGS + MONITORING_SPANS + MONITORING_DLQ ready"
            )
        except Exception as e:  # noqa: BLE001
            logger.warning(
                "monitoring: jetstream bootstrap failed, continuing without it: %s", e
            )

        # Start WorkerPool — supervised consumers + APISIX scraper.
        try:
            _worker_runner = import_module(
                "backend.02_features.05_monitoring.workers.runner"
            )
            _monitoring_worker_pool = _worker_runner.WorkerPool()
            js_ref = _nats_core.get_js() if _nats_ok else None
            await _monitoring_worker_pool.start(pool, js_ref, config)
            application.state.monitoring_worker_pool = _monitoring_worker_pool
            logger.info("monitoring: worker pool started")
        except Exception as e:  # noqa: BLE001
            logger.warning("monitoring: worker pool start failed: %s", e)
            _monitoring_worker_pool = None

        # Auto-instrumentation: asyncpg + log bridge (FastAPI middleware is
        # registered at import time further below).
        if getattr(config, "monitoring_auto_instrument", False):
            try:
                _mon_asyncpg = import_module(
                    "backend.02_features.05_monitoring.instrumentation.asyncpg"
                )
                _mon_bridge = import_module(
                    "backend.02_features.05_monitoring.instrumentation.structlog_bridge"
                )
                _mon_asyncpg.install(pool)
                _mon_bridge.install()
                logger.info(
                    "monitoring: auto-instrumentation installed (asyncpg + log bridge)"
                )
            except Exception as e:  # noqa: BLE001
                logger.warning("monitoring: auto-instrumentation failed: %s", e)

    # Notify workers — only when the module is enabled.
    _notify_worker_task = None
    _notify_email_task = None
    _notify_webpush_task = None
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

    # GDPR worker — processes queued export + erasure jobs every 60 s.
    _gdpr_worker_task = None
    if "iam" in config.modules:
        import asyncio as _asyncio_gdpr
        _gdpr_service = import_module(
            "backend.02_features.03_iam.sub_features.19_gdpr.service"
        )
        _gdpr_worker_task = _asyncio_gdpr.create_task(
            _gdpr_service.gdpr_worker_loop(pool)
        )
        logger.info("GDPR worker started.")

    # IAM active-sessions gauge — emitted every 30 s as best-effort background task.
    _iam_gauge_task = None
    if "iam" in config.modules:
        import asyncio as _asyncio

        async def _iam_active_sessions_loop() -> None:
            _catalog_local = import_module("backend.01_catalog")
            _catalog_ctx_local = import_module("backend.01_catalog.context")
            _id_local = import_module("backend.01_core.id")
            while True:
                try:
                    await _asyncio.sleep(30)
                    async with pool.acquire() as _gauge_conn:
                        count = await _gauge_conn.fetchval(
                            'SELECT COUNT(*) FROM "03_iam"."16_fct_sessions" '
                            'WHERE revoked_at IS NULL AND deleted_at IS NULL '
                            '  AND expires_at > CURRENT_TIMESTAMP'
                        )
                    _gauge_ctx = _catalog_ctx_local.NodeContext(
                        audit_category="setup",
                        trace_id=_id_local.uuid7(),
                        span_id=_id_local.uuid7(),
                        extras={"pool": pool},
                    )
                    await _catalog_local.run_node(
                        pool, "monitoring.metrics.increment", _gauge_ctx,
                        {
                            "org_id": "system",
                            "metric_key": "iam_active_sessions",
                            "labels": {},
                            "value": float(count or 0),
                        },
                    )
                except _asyncio.CancelledError:
                    break
                except Exception:
                    pass  # Best-effort; never crash the server

        _iam_gauge_task = _asyncio.create_task(_iam_active_sessions_loop())

    yield

    if _gdpr_worker_task is not None:
        _gdpr_worker_task.cancel()
        import asyncio as _asyncio_gdpr2
        await _asyncio_gdpr2.gather(_gdpr_worker_task, return_exceptions=True)
        logger.info("GDPR worker stopped.")

    if _iam_gauge_task is not None:
        _iam_gauge_task.cancel()
        import asyncio as _asyncio2
        await _asyncio2.gather(_iam_gauge_task, return_exceptions=True)

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

    # Shut down monitoring worker pool before NATS close.
    if _monitoring_worker_pool is not None:
        try:
            await _monitoring_worker_pool.stop(timeout=10.0)
            logger.info("monitoring: worker pool stopped")
        except Exception as e:  # noqa: BLE001
            logger.warning("monitoring: worker pool stop failed: %s", e)

    # Shut down NATS client if connected.
    try:
        if _nats_core._client is not None:
            await _nats_core.close()
            logger.info("NATS connection closed.")
    except Exception as e:  # noqa: BLE001
        logger.warning("NATS close failed: %s", e)

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

# Setup routes — always mounted, unauthenticated, bypassed by SetupModeMiddleware.
_setup_routes = import_module(
    "backend.02_features.03_iam.sub_features.18_setup.routes"
)
app.include_router(_setup_routes.router)


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


# Monitoring FastAPI middleware — register at import time (middleware cannot
# be added once the app has started). asyncpg + log bridge instrumentation is
# installed in lifespan above (needs pool/config).
if (
    "monitoring" in _startup_config.modules
    and _startup_config.monitoring_enabled
    and getattr(_startup_config, "monitoring_auto_instrument", False)
):
    try:
        _mon_fastapi = import_module(
            "backend.02_features.05_monitoring.instrumentation.fastapi"
        )
        _mon_fastapi.install(app, _startup_config)
        logger.info("monitoring: fastapi middleware installed")
    except Exception as e:  # noqa: BLE001
        logger.warning("monitoring: fastapi middleware install failed: %s", e)
