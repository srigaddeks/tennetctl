from __future__ import annotations

from contextlib import nullcontext
from contextlib import asynccontextmanager
from importlib import import_module
from typing import AsyncIterator
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware


_settings_module = import_module("backend.00_config.settings")
_database_module = import_module("backend.01_core.database")
_cache_module = import_module("backend.01_core.cache")
_errors_module = import_module("backend.01_core.errors")
_logging_module = import_module("backend.01_core.logging_utils")
_rate_limit_module = import_module("backend.01_core.rate_limit")
_router_module = import_module("backend.03_auth_manage.router")
_ff_router_module = import_module("backend.03_auth_manage.03_feature_flags.router")
_roles_router_module = import_module("backend.03_auth_manage.04_roles.router")
_portal_views_router_module = import_module("backend.03_auth_manage.16_portal_views.router")
_groups_router_module = import_module("backend.03_auth_manage.05_user_groups.router")
_access_router_module = import_module("backend.03_auth_manage.06_access_context.router")
_orgs_router_module = import_module("backend.03_auth_manage.07_orgs.router")
_workspaces_router_module = import_module("backend.03_auth_manage.08_workspaces.router")
_invitations_router_module = import_module("backend.03_auth_manage.09_invitations.router")
_passwordless_router_module = import_module("backend.03_auth_manage.17_passwordless.router")
_impersonation_router_module = import_module("backend.03_auth_manage.10_impersonation.router")
_campaigns_router_module = import_module("backend.03_auth_manage.15_invite_campaigns.router")
_admin_router_module = import_module("backend.03_auth_manage.11_admin.router")
_entity_settings_router_module = import_module("backend.03_auth_manage.12_entity_settings.router")
_api_keys_router_module = import_module("backend.03_auth_manage.13_api_keys.router")
_license_profiles_router_module = import_module("backend.03_auth_manage.14_license_profiles.router")
_grc_roles_router_module = import_module("backend.03_auth_manage.18_grc_roles.router")
_notif_router_module = import_module("backend.04_notifications.router")
_notif_templates_router_module = import_module("backend.04_notifications.01_templates.router")
_notif_tracking_router_module = import_module("backend.04_notifications.05_tracking.router")
_notif_broadcasts_router_module = import_module("backend.04_notifications.06_broadcasts.router")
_notif_releases_router_module = import_module("backend.04_notifications.08_releases.router")
_notif_variable_queries_router_module = import_module("backend.04_notifications.09_variable_queries.router")
_notif_rules_router_module = import_module("backend.04_notifications.07_rules.router")
_tasks_router_module = import_module("backend.07_tasks.router")
_risk_registry_router_module = import_module("backend.06_risk_registry.router")
_grc_library_router_module = import_module("backend.05_grc_library.router")
_comments_router_module = import_module("backend.08_comments.router")
_attachments_router_module = import_module("backend.09_attachments.router")
_sandbox_router_module = import_module("backend.10_sandbox.router")
_clickhouse_module = import_module("backend.10_sandbox.11_clickhouse.client")
_feedback_router_module = import_module("backend.10_feedback.router")
_docs_router_module = import_module("backend.11_docs.router")
_engagements_router_module = import_module("backend.12_engagements.router")
_assessments_router_module = import_module("backend.09_assessments.router")
_ai_router_module = import_module("backend.20_ai.router")
_agent_sandbox_router_module = import_module("backend.25_agent_sandbox.router")

Settings = _settings_module.Settings
load_settings = _settings_module.load_settings
DatabasePool = _database_module.DatabasePool
apply_sql_migrations = _database_module.apply_sql_migrations
AppError = _errors_module.AppError
CacheManager = _cache_module.CacheManager
NullCacheManager = _cache_module.NullCacheManager
get_logger = _logging_module.get_logger
bind_request_context = _logging_module.bind_request_context
reset_request_context = _logging_module.reset_request_context
RateLimitMiddleware = _rate_limit_module.RateLimitMiddleware
auth_router = _router_module.router
feature_flags_router = _ff_router_module.router
roles_router = _roles_router_module.router
portal_views_router = _portal_views_router_module.router
groups_router = _groups_router_module.router
access_context_router = _access_router_module.router
orgs_router = _orgs_router_module.router
workspaces_router = _workspaces_router_module.router
invitations_router = _invitations_router_module.router
passwordless_router = _passwordless_router_module.router
impersonation_router = _impersonation_router_module.router
campaigns_router = _campaigns_router_module.router
admin_router = _admin_router_module.router
entity_settings_router = _entity_settings_router_module.router
api_keys_router = _api_keys_router_module.router
license_profiles_router = _license_profiles_router_module.router
grc_roles_router = _grc_roles_router_module.router
notification_router = _notif_router_module.router
notification_templates_router = _notif_templates_router_module.router
notification_tracking_router = _notif_tracking_router_module.router
notification_broadcasts_router = _notif_broadcasts_router_module.router
notification_org_broadcasts_router = _notif_broadcasts_router_module.org_router
notification_releases_router = _notif_releases_router_module.router
notification_variable_queries_router = _notif_variable_queries_router_module.router
notification_variable_keys_router = _notif_variable_queries_router_module._var_keys_router
notification_rules_router = _notif_rules_router_module.router
tasks_router = _tasks_router_module.router
risk_registry_router = _risk_registry_router_module.router
comments_router = _comments_router_module.router
attachments_router = _attachments_router_module.router
sandbox_dimensions_router = _sandbox_router_module.dimensions_router
sandbox_connectors_router = _sandbox_router_module.connectors_router
sandbox_datasets_router = _sandbox_router_module.datasets_router
sandbox_signals_router = _sandbox_router_module.signals_router
sandbox_threat_types_router = _sandbox_router_module.threat_types_router
sandbox_policies_router = _sandbox_router_module.policies_router
sandbox_execution_runs_router = _sandbox_router_module.execution_runs_router
sandbox_threat_eval_router = _sandbox_router_module.execution_threat_eval_router
sandbox_policy_exec_router = _sandbox_router_module.execution_policy_exec_router
sandbox_live_sessions_router = _sandbox_router_module.live_sessions_router
sandbox_libraries_router = _sandbox_router_module.libraries_router
sandbox_promotions_router = _sandbox_router_module.promotions_router
sandbox_ssf_transmitter_router = _sandbox_router_module.ssf_transmitter_router
sandbox_ssf_wellknown_router = _sandbox_router_module.ssf_wellknown_router
sandbox_assets_router = _sandbox_router_module.assets_router
sandbox_collection_runs_router = _sandbox_router_module.collection_runs_router
sandbox_providers_router = _sandbox_router_module.providers_router
sandbox_asset_connectors_router = _sandbox_router_module.asset_connectors_router
sandbox_promoted_tests_router = _sandbox_router_module.promoted_tests_router
sandbox_global_library_router = _sandbox_router_module.global_library_router
sandbox_global_datasets_router = _sandbox_router_module.global_datasets_router
sandbox_global_control_tests_router = _sandbox_router_module.global_control_tests_router
sandbox_live_test_router = _sandbox_router_module.live_test_router
ClickHouseClient = _clickhouse_module.ClickHouseClient
NullClickHouseClient = _clickhouse_module.NullClickHouseClient
feedback_router = _feedback_router_module.router
docs_router = _docs_router_module.router
engagements_router = _engagements_router_module.router
auditor_dashboard_router = _engagements_router_module.auditor_dashboard_router
assessments_router = _assessments_router_module.router
ai_dimensions_router = _ai_router_module.dimensions_router
ai_conversations_router = _ai_router_module.conversations_router
ai_memory_router = _ai_router_module.memory_router
ai_agents_router = _ai_router_module.agents_router
ai_mcp_router = _ai_router_module.mcp_router
ai_approvals_router = _ai_router_module.approvals_router
ai_reporting_router = _ai_router_module.reporting_router
ai_budgets_router = _ai_router_module.budgets_router
ai_guardrails_router = _ai_router_module.guardrails_router
ai_admin_router = _ai_router_module.admin_router
ai_agent_config_router = _ai_router_module.agent_config_router
ai_prompt_config_router = _ai_router_module.prompt_config_router
ai_job_queue_router = _ai_router_module.job_queue_router
ai_evidence_checker_router = _ai_router_module.evidence_checker_router
ai_text_enhancer_router = _ai_router_module.text_enhancer_router
ai_form_fill_router = _ai_router_module.form_fill_router
ai_attachments_router = _ai_router_module.attachments_router
ai_reports_router = _ai_router_module.reports_router
ai_framework_builder_router = _ai_router_module.framework_builder_router
ai_signal_spec_router = _ai_router_module.signal_spec_router
ai_signal_codegen_router = _ai_router_module.signal_codegen_router
ai_dataset_agent_router = _ai_router_module.dataset_agent_router
ai_pdf_templates_router = _ai_router_module.pdf_templates_router
ai_risk_advisor_router = _ai_router_module.risk_advisor_router
ai_test_linker_router = _ai_router_module.test_linker_router
ai_task_builder_router = _ai_router_module.task_builder_router
asb_dimensions_router = _agent_sandbox_router_module.dimensions_router
asb_agents_router = _agent_sandbox_router_module.agents_router
asb_tools_router = _agent_sandbox_router_module.tools_router
asb_scenarios_router = _agent_sandbox_router_module.scenarios_router
asb_execution_router = _agent_sandbox_router_module.execution_router
asb_test_runner_router = _agent_sandbox_router_module.test_runner_router
asb_registry_router = _agent_sandbox_router_module.registry_router
asb_playground_router = _agent_sandbox_router_module.playground_router
asb_tool_endpoints_router = _agent_sandbox_router_module.tool_endpoints_router
grc_dimensions_router = _grc_library_router_module.dimensions_router
grc_frameworks_router = _grc_library_router_module.frameworks_router
grc_versions_router = _grc_library_router_module.versions_router
grc_requirements_router = _grc_library_router_module.requirements_router
grc_controls_router = _grc_library_router_module.controls_router
grc_tests_router = _grc_library_router_module.tests_router
grc_test_mappings_router = _grc_library_router_module.test_mappings_router
grc_settings_router = _grc_library_router_module.settings_router
grc_test_executions_router = _grc_library_router_module.test_executions_router
grc_deployments_router = _grc_library_router_module.deployments_router
grc_global_risks_router = _grc_library_router_module.global_risks_router
grc_dashboard_router = _grc_library_router_module.dashboard_router

try:
    _telemetry_module = import_module("backend.01_core.telemetry")
except ModuleNotFoundError:  # pragma: no cover
    configure_observability = lambda settings: None
    instrument_fastapi_app = lambda app: None
    start_operation_span = lambda name, attributes=None: nullcontext()
    shutdown_observability = lambda: None
else:
    configure_observability = _telemetry_module.configure_observability
    instrument_fastapi_app = _telemetry_module.instrument_fastapi_app
    start_operation_span = _telemetry_module.start_operation_span
    shutdown_observability = _telemetry_module.shutdown_observability


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    import asyncio
    logger = get_logger("backend.app")
    settings = app.state.settings
    _queue_task = None
    _campaign_task = None
    _job_worker_task = None
    _retention_task_obj = None
    cache = NullCacheManager()
    clickhouse = NullClickHouseClient()
    pool = DatabasePool(
        database_url=settings.database_url,
        min_size=settings.database_min_pool_size,
        max_size=settings.database_max_pool_size,
        command_timeout_seconds=settings.database_command_timeout_seconds,
        application_name=settings.app_name,
    )
    try:
        with start_operation_span(
            "app.lifespan.startup",
            attributes={
                "service.name": settings.app_name,
                "deployment.environment.name": settings.environment,
            },
        ):
            await pool.open()
            app.state.database_pool = pool
            if settings.cache_url:
                cache = CacheManager(
                    url=settings.cache_url,
                    key_prefix=settings.cache_key_prefix,
                    default_ttl=settings.cache_default_ttl_seconds,
                )
                logger.info(
                    "cache_pool_opened",
                    extra={
                        "action": "app.startup.cache",
                        "outcome": "success",
                        "cache_url": settings.cache_url.split("@")[-1],
                    },
                )
            else:
                cache = NullCacheManager()
                logger.info(
                    "cache_disabled",
                    extra={"action": "app.startup.cache", "outcome": "skipped"},
                )
            app.state.cache = cache
            # --- ClickHouse client for sandbox ---
            if settings.sandbox_clickhouse_url:
                clickhouse = ClickHouseClient(
                    url=settings.sandbox_clickhouse_url,
                    database=settings.sandbox_clickhouse_database,
                )
                await clickhouse.open()
                logger.info(
                    "clickhouse_client_opened",
                    extra={
                        "action": "app.startup.clickhouse",
                        "outcome": "success",
                        "database": settings.sandbox_clickhouse_database,
                    },
                )
            else:
                clickhouse = NullClickHouseClient()
                logger.info(
                    "clickhouse_disabled",
                    extra={"action": "app.startup.clickhouse", "outcome": "skipped"},
                )
            app.state.clickhouse = clickhouse
            if settings.run_migrations_on_startup:
                await apply_sql_migrations(pool, settings.migration_directory)
                logger.info(
                    "startup_migrations_applied",
                    extra={
                        "action": "app.startup.migrations",
                        "outcome": "success",
                        "service": settings.app_name,
                        "environment": settings.environment,
                    },
                )
            else:
                logger.info(
                    "startup_migrations_skipped",
                    extra={
                        "action": "app.startup.migrations",
                        "outcome": "skipped",
                        "service": settings.app_name,
                        "environment": settings.environment,
                    },
                )
            # Validate PLATFORM_BASE_URL — critical for email links, tracking, password reset
            _pbu = getattr(settings, "platform_base_url", "")
            if not _pbu and settings.environment not in ("local", "test"):
                logger.warning(
                    "platform_base_url_not_set",
                    extra={
                        "action": "app.startup.validation",
                        "outcome": "warning",
                        "hint": "Set PLATFORM_BASE_URL env var — email links, tracking, and password reset will be broken without it",
                    },
                )

            logger.info(
                "database_pool_opened",
                extra={
                    "action": "app.startup.database_pool",
                    "outcome": "success",
                    "service": settings.app_name,
                    "environment": settings.environment,
                },
            )

            # --- Notification queue processor ---
            if settings.notification_enabled:
                _queue_module = import_module("backend.04_notifications.03_queue.processor")
                _email_module = import_module("backend.04_notifications.04_channels.email_provider")
                _webpush_module = import_module("backend.04_notifications.04_channels.webpush_provider")
                email_provider = None
                # Load SMTP config: DB config takes precedence over env vars
                _db_smtp = None
                try:
                    async with pool.acquire() as _smtp_conn:
                        _db_smtp = await _smtp_conn.fetchrow(
                            'SELECT host, port, username, password, from_email, from_name, use_tls, start_tls'
                            ' FROM "03_notifications"."30_fct_smtp_config"'
                            ' WHERE tenant_key = $1 AND is_active = TRUE LIMIT 1',
                            'default',
                        )
                except Exception:
                    pass
                _smtp_host = (_db_smtp['host'] if _db_smtp else None) or settings.notification_smtp_host
                _smtp_port = (_db_smtp['port'] if _db_smtp else None) or settings.notification_smtp_port
                _smtp_user = (_db_smtp['username'] if _db_smtp else None) or settings.notification_smtp_user
                _db_raw_pass = (_db_smtp['password'] if _db_smtp else None)
                if _db_raw_pass and settings.notification_encryption_key:
                    _crypto_mod = import_module("backend.04_notifications.04_channels.crypto")
                    _enc_key = _crypto_mod.parse_encryption_key(settings.notification_encryption_key)
                    try:
                        _db_raw_pass = _crypto_mod.decrypt_value(_db_raw_pass, _enc_key)
                    except Exception:
                        pass  # legacy plaintext — use as-is
                _smtp_pass = _db_raw_pass or settings.notification_smtp_password
                _smtp_from = (_db_smtp['from_email'] if _db_smtp else None) or settings.notification_from_email
                _smtp_from_name = (_db_smtp['from_name'] if _db_smtp else None) or settings.notification_from_name
                _smtp_use_tls = (_db_smtp['use_tls'] if _db_smtp is not None else None)
                if _smtp_use_tls is None:
                    _smtp_use_tls = settings.notification_smtp_use_tls
                _smtp_start_tls = (_db_smtp['start_tls'] if _db_smtp is not None else None)
                if _smtp_start_tls is None:
                    _smtp_start_tls = settings.notification_smtp_start_tls
                if _smtp_host and _smtp_from:
                    email_provider = _email_module.EmailProvider(
                        host=_smtp_host,
                        port=_smtp_port,
                        username=_smtp_user,
                        password=_smtp_pass,
                        from_email=_smtp_from,
                        from_name=_smtp_from_name or "K-Control",
                        use_tls=_smtp_use_tls or False,
                        start_tls=_smtp_start_tls if _smtp_start_tls is not None else True,
                    )
                webpush_provider = None
                if (
                    settings.notification_vapid_private_key
                    and settings.notification_vapid_public_key
                    and settings.notification_vapid_claims_email
                ):
                    webpush_provider = _webpush_module.WebPushProvider(
                        vapid_private_key=settings.notification_vapid_private_key,
                        vapid_public_key=settings.notification_vapid_public_key,
                        vapid_claims_email=settings.notification_vapid_claims_email,
                    )
                processor = _queue_module.NotificationQueueProcessor(
                    database_pool=pool,
                    settings=settings,
                    email_provider=email_provider,
                    webpush_provider=webpush_provider,
                )
                _queue_task = asyncio.create_task(processor.run_loop())

                # Start campaign runner for inactivity/engagement-based campaigns
                _campaign_module = import_module("backend.04_notifications.03_queue.campaign_runner")
                campaign_runner = _campaign_module.CampaignRunner(
                    database_pool=pool,
                    settings=settings,
                )
                _campaign_task = asyncio.create_task(campaign_runner.run_loop())

                # Start inbox retention background task
                _retention_module = import_module("backend.04_notifications.12_retention.retention")
                _retention_task_obj = _retention_module.InboxRetentionTask(
                    database_pool=pool,
                    archive_after_days=getattr(settings, "notification_inbox_archive_after_days", 90),
                    delete_after_days=getattr(settings, "notification_inbox_delete_after_days", 365),
                )
                _retention_task_obj.start()

                logger.info(
                    "notification_queue_processor_started",
                    extra={
                        "action": "app.startup.notification_queue",
                        "outcome": "success",
                        "email_enabled": email_provider is not None,
                        "webpush_enabled": webpush_provider is not None,
                    },
                )

            # --- AI Job Queue Worker ---
            if getattr(settings, "ai_job_worker_enabled", True):
                _job_worker_module = import_module("backend.20_ai.15_job_queue.worker")
                _job_worker = _job_worker_module.JobQueueWorker(
                    pool=pool,
                    settings=settings,
                )
                await _job_worker.recover_stuck_jobs()
                _job_worker_task = asyncio.create_task(_job_worker.run_loop())
                logger.info(
                    "ai_job_queue_worker_started",
                    extra={
                        "action": "app.startup.ai_job_worker",
                        "outcome": "success",
                    },
                )

            # --- Collection Scheduler ---
            try:
                _scheduler_module = import_module("backend.10_sandbox.24_scheduler.scheduler")
                _collection_scheduler = _scheduler_module.CollectionScheduler(
                    database_pool=pool,
                    settings=settings,
                )
                _scheduler_task = asyncio.create_task(_collection_scheduler.run_loop())
                logger.info(
                    "collection_scheduler_started",
                    extra={
                        "action": "app.startup.collection_scheduler",
                        "outcome": "success",
                    },
                )
            except Exception as e:
                logger.warning(
                    f"collection_scheduler_init_failed: {e}",
                    extra={"action": "app.startup.collection_scheduler", "outcome": "error"},
                )

        yield
    finally:
        with start_operation_span(
            "app.lifespan.shutdown",
            attributes={
                "service.name": settings.app_name,
                "deployment.environment.name": settings.environment,
            },
        ):
            if _job_worker_task is not None:
                _job_worker_task.cancel()
                try:
                    await _job_worker_task
                except asyncio.CancelledError:
                    pass
            if _retention_task_obj is not None:
                await _retention_task_obj.stop()
            if _campaign_task is not None:
                _campaign_task.cancel()
                try:
                    await _campaign_task
                except asyncio.CancelledError:
                    pass
            if _queue_task is not None:
                _queue_task.cancel()
                try:
                    await _queue_task
                except asyncio.CancelledError:
                    pass
            app.state.database_pool = None
            await clickhouse.close()
            app.state.clickhouse = None
            await cache.close()
            app.state.cache = None
            await pool.close()
            logger.info(
                "database_pool_closed",
                extra={
                    "action": "app.shutdown.database_pool",
                    "outcome": "success",
                    "service": settings.app_name,
                    "environment": settings.environment,
                },
            )
            shutdown_observability()


# ---------------------------------------------------------------------------
# Security headers middleware (ASGI)
# ---------------------------------------------------------------------------

class SecurityHeadersMiddleware:
    """Injects standard security headers on every HTTP response."""

    _HEADERS = [
        (b"x-content-type-options", b"nosniff"),
        (b"x-frame-options", b"DENY"),
        (b"referrer-policy", b"strict-origin-when-cross-origin"),
        (b"x-xss-protection", b"0"),
    ]

    def __init__(self, app, *, include_hsts: bool = False) -> None:
        self.app = app
        self._extra_headers: list[tuple[bytes, bytes]] = []
        if include_hsts:
            self._extra_headers.append(
                (b"strict-transport-security", b"max-age=31536000; includeSubDomains")
            )

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        all_headers = self._HEADERS + self._extra_headers

        async def send_wrapper(message) -> None:
            if message["type"] == "http.response.start":
                from starlette.datastructures import MutableHeaders
                mutable = MutableHeaders(raw=message["headers"])
                for name, value in all_headers:
                    mutable.append(name.decode(), value.decode())
            await send(message)

        await self.app(scope, receive, send_wrapper)


# ---------------------------------------------------------------------------
# Request body size limiter middleware (ASGI)
# ---------------------------------------------------------------------------

class RequestSizeLimitMiddleware:
    """Rejects requests with Content-Length exceeding the configured limit."""

    def __init__(self, app, *, max_bytes: int) -> None:
        self.app = app
        self._max_bytes = max_bytes

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        from starlette.datastructures import Headers
        headers = Headers(scope=scope)
        content_length = headers.get("content-length")
        if content_length is not None:
            try:
                if int(content_length) > self._max_bytes:
                    import json
                    body = json.dumps({
                        "error": {
                            "code": "request_too_large",
                            "message": f"Request body exceeds {self._max_bytes} bytes.",
                        },
                    }).encode()
                    await send({
                        "type": "http.response.start",
                        "status": 413,
                        "headers": [(b"content-type", b"application/json")],
                    })
                    await send({"type": "http.response.body", "body": body})
                    return
            except ValueError:
                pass

        await self.app(scope, receive, send)


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

def create_app(settings: Settings | None = None) -> FastAPI:
    resolved_settings = settings or load_settings()
    with start_operation_span(
        "app.create",
        attributes={
            "service.name": resolved_settings.app_name,
            "deployment.environment.name": resolved_settings.environment,
        },
    ):
        configure_observability(resolved_settings)
        app = FastAPI(title=resolved_settings.app_name, lifespan=_lifespan)
        app.state.settings = resolved_settings
        app.state.database_pool = None
        app.state.cache = NullCacheManager()
        app.state.clickhouse = NullClickHouseClient()
        get_logger("backend.app").info(
            "app_created",
            extra={
                "action": "app.create",
                "outcome": "success",
                "service": resolved_settings.app_name,
                "environment": resolved_settings.environment,
            },
        )

    # --- Request ID middleware ---
    @app.middleware("http")
    async def inject_request_id(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid4()))
        request.state.request_id = request_id
        request_token = bind_request_context(request_id)
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            if request.url.path.startswith("/api/v1/auth/local/"):
                response.headers["Cache-Control"] = "no-store"
                response.headers["Pragma"] = "no-cache"
            if getattr(request.state, "is_api_key", False):
                response.headers["X-Auth-Type"] = "api_key"
                response.headers["X-Api-Key-Id"] = getattr(
                    request.state, "api_key_id", ""
                )
            if getattr(request.state, "is_impersonation", False):
                response.headers["X-Impersonation-Active"] = "true"
                response.headers["X-Impersonator-Id"] = getattr(
                    request.state, "impersonator_id", ""
                )
            return response
        finally:
            reset_request_context(request_token)

    # --- Exception handlers ---
    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        with start_operation_span(
            "app.error.response",
            attributes={
                "error.code": exc.code,
                "http.response.status_code": exc.status_code,
            },
        ):
            get_logger("backend.app").info(
                "app_error_response",
                extra={
                    "action": "app.error.response",
                    "outcome": "error",
                    "error_code": exc.code,
                    "http_status_code": exc.status_code,
                },
            )
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "error": {"code": exc.code, "message": exc.message},
                    "request_id": getattr(request.state, "request_id", None),
                },
            )

    @app.exception_handler(Exception)
    async def handle_unhandled_exception(request: Request, exc: Exception) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        logger = get_logger("backend.app")
        logger.error(
            "unhandled_exception",
            extra={
                "action": "app.error.unhandled",
                "outcome": "error",
                "exception_type": type(exc).__name__,
                "request_id": request_id,
                "http_method": request.method,
                "http_path": str(request.url.path),
            },
            exc_info=exc,
        )
        # Send to GlitchTip/Sentry if configured
        try:
            import sentry_sdk
            sentry_sdk.capture_exception(exc)
        except ImportError:
            pass
        return JSONResponse(
            status_code=500,
            content={
                "error": {"code": "internal_error", "message": "An internal error occurred."},
                "request_id": request_id,
            },
        )

    # --- Health check endpoints ---
    @app.get("/livez", tags=["system"])
    async def liveness() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/readyz", tags=["system"])
    async def readiness(request: Request) -> JSONResponse:
        with start_operation_span("app.health.readiness"):
            pool = getattr(request.app.state, "database_pool", None)
            if pool is None:
                return JSONResponse(status_code=503, content={"status": "not_ready"})
            try:
                await pool.ping()
            except Exception:
                return JSONResponse(status_code=503, content={"status": "not_ready"})
            return JSONResponse(status_code=200, content={"status": "ok"})

    @app.get("/healthz", tags=["system"])
    async def healthcheck(request: Request) -> JSONResponse:
        return await readiness(request)

    # --- Routers ---
    app.include_router(auth_router)
    app.include_router(feature_flags_router)
    app.include_router(roles_router)
    app.include_router(portal_views_router)
    app.include_router(groups_router)
    app.include_router(access_context_router)
    app.include_router(orgs_router)
    app.include_router(workspaces_router)
    app.include_router(invitations_router)
    app.include_router(passwordless_router)
    app.include_router(campaigns_router)
    app.include_router(impersonation_router)
    app.include_router(admin_router)
    app.include_router(entity_settings_router)
    app.include_router(api_keys_router)
    app.include_router(license_profiles_router)
    app.include_router(grc_roles_router)
    app.include_router(notification_router)
    app.include_router(notification_templates_router)
    app.include_router(notification_tracking_router)
    app.include_router(notification_broadcasts_router)
    app.include_router(notification_org_broadcasts_router)
    app.include_router(notification_releases_router)
    app.include_router(notification_variable_queries_router)
    app.include_router(notification_variable_keys_router)
    app.include_router(notification_rules_router)
    app.include_router(tasks_router)
    app.include_router(risk_registry_router)
    app.include_router(comments_router)
    app.include_router(attachments_router)
    app.include_router(grc_dimensions_router)
    app.include_router(grc_frameworks_router)
    app.include_router(grc_versions_router)
    app.include_router(grc_requirements_router)
    app.include_router(grc_controls_router)
    app.include_router(grc_tests_router)
    app.include_router(grc_test_mappings_router)
    app.include_router(grc_settings_router)
    app.include_router(grc_test_executions_router)
    app.include_router(grc_deployments_router)
    app.include_router(grc_global_risks_router)
    app.include_router(grc_dashboard_router)
    app.include_router(sandbox_dimensions_router)
    app.include_router(sandbox_connectors_router)
    app.include_router(sandbox_datasets_router)
    app.include_router(sandbox_signals_router)
    app.include_router(sandbox_threat_types_router)
    app.include_router(sandbox_policies_router)
    app.include_router(sandbox_execution_runs_router)
    app.include_router(sandbox_threat_eval_router)
    app.include_router(sandbox_policy_exec_router)
    app.include_router(sandbox_live_sessions_router)
    app.include_router(sandbox_libraries_router)
    app.include_router(sandbox_promotions_router)
    app.include_router(sandbox_ssf_transmitter_router)
    app.include_router(sandbox_ssf_wellknown_router)
    app.include_router(sandbox_assets_router)
    app.include_router(sandbox_collection_runs_router)
    app.include_router(sandbox_providers_router)
    app.include_router(sandbox_asset_connectors_router)
    app.include_router(sandbox_promoted_tests_router)
    app.include_router(sandbox_global_library_router)
    app.include_router(sandbox_global_datasets_router)
    app.include_router(sandbox_global_control_tests_router)
    app.include_router(sandbox_live_test_router)
    app.include_router(feedback_router)
    app.include_router(docs_router)
    app.include_router(auditor_dashboard_router)
    app.include_router(engagements_router)
    app.include_router(assessments_router)
    # AI Copilot Platform (20_ai)
    app.include_router(ai_dimensions_router)
    app.include_router(ai_conversations_router)
    app.include_router(ai_memory_router)
    app.include_router(ai_agents_router)
    app.include_router(ai_mcp_router)
    app.include_router(ai_approvals_router)
    app.include_router(ai_reporting_router)
    app.include_router(ai_budgets_router)
    app.include_router(ai_guardrails_router)
    app.include_router(ai_admin_router)
    app.include_router(ai_agent_config_router)
    app.include_router(ai_prompt_config_router)
    app.include_router(ai_job_queue_router)
    app.include_router(ai_evidence_checker_router)
    app.include_router(ai_text_enhancer_router)
    app.include_router(ai_form_fill_router)
    app.include_router(ai_attachments_router)
    app.include_router(ai_reports_router)
    app.include_router(ai_framework_builder_router)
    app.include_router(ai_signal_spec_router)
    app.include_router(ai_signal_codegen_router)
    app.include_router(ai_dataset_agent_router)
    app.include_router(ai_pdf_templates_router)
    app.include_router(ai_risk_advisor_router)
    app.include_router(ai_test_linker_router)
    app.include_router(ai_task_builder_router)
    # Agent Sandbox
    app.include_router(asb_dimensions_router)
    app.include_router(asb_agents_router)
    app.include_router(asb_tools_router)
    app.include_router(asb_scenarios_router)
    app.include_router(asb_execution_router)
    app.include_router(asb_test_runner_router)
    app.include_router(asb_registry_router)
    app.include_router(asb_playground_router)
    app.include_router(asb_tool_endpoints_router)

    # --- Issues ---
    _issues_router_module = import_module("backend.09_issues.router")
    app.include_router(_issues_router_module.router)

    # --- ASGI middleware stack (applied in reverse order) ---
    # Telemetry wraps everything (outermost)
    instrument_fastapi_app(app)

    # Security headers on every response
    include_hsts = resolved_settings.environment not in {"local", "development", "dev", "test"}
    app.add_middleware(SecurityHeadersMiddleware, include_hsts=include_hsts)

    # Request body size limit
    app.add_middleware(RequestSizeLimitMiddleware, max_bytes=resolved_settings.max_request_body_bytes)

    # Rate limiting (before CORS so preflight isn't rate-limited via exclude)
    if resolved_settings.rate_limit_enabled:
        app.add_middleware(
            RateLimitMiddleware,
            max_requests=resolved_settings.rate_limit_requests_per_minute,
            window_seconds=60,
            exclude_paths=resolved_settings.rate_limit_exclude_paths,
        )

    # CORS (outermost after telemetry — runs first for preflight)
    if resolved_settings.cors_allowed_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(resolved_settings.cors_allowed_origins),
            allow_methods=list(resolved_settings.cors_allowed_methods),
            allow_headers=list(resolved_settings.cors_allowed_headers),
            allow_credentials=resolved_settings.cors_allow_credentials,
            max_age=resolved_settings.cors_max_age_seconds,
        )

    return app
