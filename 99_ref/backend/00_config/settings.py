from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from urllib.parse import quote_plus
import os


BACKEND_DIR = Path(__file__).resolve().parents[1]


def _load_dotenv() -> None:
    # Load base .env first
    env_path = BACKEND_DIR / ".env"
    if env_path.exists():
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())
            
    # Load .env.local second (overrides .env)
    env_local_path = BACKEND_DIR / ".env.local"
    if env_local_path.exists():
        for raw_line in env_local_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            # Use os.environ[...] = ... to overwrite
            os.environ[key.strip()] = value.strip()


def _read_bool(name: str, *, default: bool) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    value = raw_value.strip().lower()
    if value in {"1", "true", "yes", "on"}:
        return True
    if value in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{name} must be boolean-like.")


def _read_int(name: str, *, default: int, minimum: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    value = int(raw_value)
    if value < minimum:
        raise ValueError(f"{name} must be >= {minimum}.")
    return value


def _read_float(name: str, *, default: float, minimum: float, maximum: float) -> float:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    value = float(raw_value)
    if value < minimum or value > maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}.")
    return value


def _read_csv(name: str, *, default: tuple[str, ...] = ()) -> tuple[str, ...]:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    values = tuple(item.strip() for item in raw_value.split(",") if item.strip())
    return values or default


def _read_log_level(name: str, *, default: str) -> str:
    value = os.getenv(name, default).strip().upper()
    valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
    if value not in valid_levels:
        raise ValueError(f"{name} must be one of {', '.join(sorted(valid_levels))}.")
    return value


_SUPPORTED_LOG_FORMATS = {"json", "text", "ecs", "cef", "syslog"}


def _read_log_format(name: str, *, default: str) -> str:
    value = os.getenv(name, default).strip().lower()
    if value not in _SUPPORTED_LOG_FORMATS:
        raise ValueError(f"{name} must be one of {', '.join(sorted(_SUPPORTED_LOG_FORMATS))}.")
    return value


def _read_log_level_overrides(name: str) -> dict[str, str]:
    raw_value = os.getenv(name)
    if not raw_value:
        return {}
    valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
    overrides: dict[str, str] = {}
    for item in raw_value.split(","):
        item = item.strip()
        if not item or "=" not in item:
            continue
        logger_name, level = item.split("=", 1)
        level = level.strip().upper()
        if level not in valid_levels:
            raise ValueError(f"Invalid log level '{level}' for logger '{logger_name.strip()}' in {name}.")
        overrides[logger_name.strip()] = level
    return overrides


_SUPPORTED_TOKEN_ALGORITHMS = {"HS256", "RS256", "ES256"}


def _read_access_token_algorithm(name: str, *, default: str) -> str:
    value = os.getenv(name, default).strip().upper()
    if value not in _SUPPORTED_TOKEN_ALGORITHMS:
        raise ValueError(f"{name} must be one of {', '.join(sorted(_SUPPORTED_TOKEN_ALGORITHMS))}.")
    return value


def _read_json_dict(name: str) -> dict[str, str] | None:
    """Read a JSON object from an env var. Returns None if not set."""
    import json as _json
    raw = os.getenv(name)
    if not raw:
        return None
    try:
        parsed = _json.loads(raw)
    except _json.JSONDecodeError as exc:
        raise ValueError(f"{name} must be valid JSON.") from exc
    if not isinstance(parsed, dict):
        raise ValueError(f"{name} must be a JSON object.")
    return parsed


def _build_database_url() -> str:
    explicit_url = os.getenv("AUTH_DATABASE_URL") or os.getenv("DATABASE_URL")
    if explicit_url:
        return explicit_url.strip()

    host = os.getenv("DB_HOST", "").strip()
    port = os.getenv("DB_PORT", "5432").strip()
    database_name = os.getenv("DATABASE_NAME", "").strip()
    username = os.getenv("WRITE_USER", "").strip()
    password = os.getenv("WRITE_PASSWORD", "").strip()
    ssl_mode = os.getenv("SSL_MODE", "disable").strip()

    if not all([host, port, database_name, username, password]):
        raise ValueError(
            "Postgres configuration is incomplete. Set AUTH_DATABASE_URL or DB_HOST/DB_PORT/"
            "DATABASE_NAME/WRITE_USER/WRITE_PASSWORD."
        )

    return (
        f"postgresql://{quote_plus(username)}:{quote_plus(password)}@{host}:{port}/"
        f"{quote_plus(database_name)}?sslmode={quote_plus(ssl_mode)}"
    )


@dataclass(frozen=True, slots=True)
class Settings:
    environment: str
    app_name: str
    auth_local_core_enabled: bool
    run_migrations_on_startup: bool
    database_url: str
    database_min_pool_size: int
    database_max_pool_size: int
    database_command_timeout_seconds: int
    access_token_secret: str
    access_token_algorithm: str
    access_token_issuer: str
    access_token_audience: str
    access_token_ttl_seconds: int
    refresh_token_ttl_seconds: int
    brute_force_window_seconds: int
    brute_force_max_attempts: int
    default_tenant_key: str
    trust_proxy_headers: bool
    trusted_proxy_depth: int
    migration_directory: Path
    access_token_signing_key_id: str | None = None
    access_token_keys: dict[str, str] | None = None
    access_token_private_key: str | None = None
    access_token_public_key: str | None = None
    access_token_jti_blocklist_enabled: bool = False
    log_level: str = "INFO"
    log_format: str = "json"
    log_level_overrides: dict[str, str] | None = None
    cors_allowed_origins: tuple[str, ...] = ()
    cors_allowed_methods: tuple[str, ...] = ("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS")
    cors_allowed_headers: tuple[str, ...] = ("Authorization", "Content-Type", "X-Request-ID")
    cors_allow_credentials: bool = False
    cors_max_age_seconds: int = 600
    rate_limit_enabled: bool = True
    rate_limit_requests_per_minute: int = 60
    rate_limit_burst: int = 10
    rate_limit_exclude_paths: tuple[str, ...] = ("/livez", "/readyz", "/healthz")
    # Default allows a 100 MB file plus multipart/form-data overhead.
    max_request_body_bytes: int = 115_343_360
    app_version: str = "0.1.0"
    otel_enabled: bool = False
    otel_metrics_enabled: bool = False
    otel_service_name: str | None = None
    otel_exporter_otlp_protocol: str = "http/protobuf"
    otel_exporter_otlp_endpoint: str | None = None
    otel_exporter_otlp_traces_endpoint: str | None = None
    otel_exporter_otlp_logs_endpoint: str | None = None
    otel_exporter_otlp_headers: tuple[str, ...] = ()
    otel_exporter_otlp_timeout_seconds: int = 10
    otel_exporter_otlp_insecure: bool = True
    otel_traces_enabled: bool = False
    otel_logs_enabled: bool = False
    otel_sample_ratio: float = 1.0
    otel_function_trace_enabled: bool = False
    otel_function_trace_include_args: bool = True
    otel_function_trace_include_return: bool = True
    otel_function_trace_include_exceptions: bool = True
    otel_function_trace_max_value_length: int = 256
    otel_function_trace_max_collection_items: int = 10
    otel_function_trace_excluded_module_prefixes: tuple[str, ...] = (
        "backend.01_core.telemetry",
        "backend.01_core.logging_utils",
        "backend.90_tests",
    )
    otel_function_trace_excluded_path_fragments: tuple[str, ...] = ("/__pycache__/",)
    otel_function_metrics_enabled: bool = False
    otel_function_metrics_flush_interval_seconds: int = 15
    glitchtip_dsn: str | None = None
    glitchtip_traces_sample_rate: float = 0.1
    cache_url: str | None = None
    cache_key_prefix: str = "kcontrol:"
    cache_default_ttl_seconds: int = 300
    impersonation_enabled: bool = False
    impersonation_access_token_ttl_seconds: int = 900
    impersonation_refresh_token_ttl_seconds: int = 1800
    api_key_enabled: bool = True
    api_key_max_per_user: int = 10
    api_key_default_ttl_days: int | None = None
    api_key_rate_limit_requests_per_minute: int = 120
    # Platform base URL — used as fallback for all deep links, tracking, and frontend URLs.
    # Set PLATFORM_BASE_URL to your deployed frontend URL (e.g. https://k-control-dev.kreesalis.com).
    # Individual *_frontend_url settings override this for specific flows.
    platform_base_url: str = ""
    # Magic link (passwordless)
    magic_link_enabled: bool = True
    magic_link_default_ttl_hours: int = 24
    magic_link_frontend_verify_url: str = ""
    magic_link_assignee_frontend_verify_url: str = ""
    password_reset_frontend_url: str = ""
    password_reset_expiry_minutes: int = 30  # configurable password reset token TTL
    otp_expiry_minutes: int = 10              # configurable OTP code TTL
    # Notifications — email provider
    notification_enabled: bool = False
    notification_email_provider: str | None = None
    notification_smtp_host: str | None = None
    notification_smtp_port: int = 587
    notification_smtp_user: str | None = None
    notification_smtp_password: str | None = None
    notification_smtp_use_tls: bool = False   # True = implicit TLS (port 465)
    notification_smtp_start_tls: bool = True  # True = STARTTLS (port 587, Gmail)
    notification_from_email: str | None = None
    notification_from_name: str = "kcontrol"
    # Platform branding — used in email templates as {{ platform.* }} variables
    platform_company: str = "Kreesalis"
    platform_support_url: str = "https://kreesalis.com/support"
    platform_privacy_url: str = "https://kreesalis.com/privacy"
    platform_tagline: str = "Continuous Compliance"
    platform_year: str = ""  # set at construction time to current year
    # Notifications — web push
    notification_vapid_private_key: str | None = None
    notification_vapid_public_key: str | None = None
    notification_vapid_app_server_key: str | None = None  # URL-safe base64 for frontend applicationServerKey
    notification_vapid_claims_email: str | None = None
    # Notifications — queue
    notification_queue_poll_interval_seconds: int = 5
    notification_queue_batch_size: int = 50
    notification_email_rate_limit_per_minute: int = 100
    notification_push_rate_limit_per_minute: int = 200
    # Notifications — tracking
    notification_tracking_base_url: str | None = None
    notification_encryption_key: str | None = None  # base64-encoded 32-byte key for SMTP password at rest
    notification_unsubscribe_secret: str = "change-me-in-production"  # HMAC secret for email unsubscribe tokens
    notification_inbox_archive_after_days: int = 90   # archive delivered notifications after N days
    notification_inbox_delete_after_days: int = 365   # hard-delete archived notifications after N days
    # Storage — object storage for attachments
    storage_provider: str = "minio"                  # s3, gcs, azure, minio
    storage_max_file_size_mb: int = 100
    # S3 / MinIO shared settings
    storage_s3_bucket: str = ""
    storage_s3_region: str = "us-east-1"
    storage_s3_access_key_id: str = ""
    storage_s3_secret_access_key: str = ""
    storage_s3_endpoint_url: str = ""               # For MinIO: http://localhost:9000
    # MinIO-specific overrides (optional — falls back to S3 values if not set)
    storage_minio_endpoint_url: str = ""
    storage_minio_bucket: str = ""
    # GCS
    storage_gcs_bucket: str = ""
    storage_gcs_project: str = ""
    storage_gcs_credentials_json: str = ""          # JSON string of service account credentials
    # Azure
    storage_azure_container: str = ""
    storage_azure_account_name: str = ""
    storage_azure_account_key: str = ""
    storage_azure_connection_string: str = ""
    # Sandbox
    sandbox_encryption_key: str | None = None
    sandbox_ai_provider_url: str | None = None
    sandbox_ai_api_key: str | None = None
    sandbox_ai_model: str = "gpt-4o"
    sandbox_execution_timeout_ms: int = 10000
    sandbox_execution_max_memory_mb: int = 256
    sandbox_live_session_max_minutes: int = 30
    sandbox_live_session_max_per_workspace: int = 5
    sandbox_live_poll_interval_seconds: int = 10
    sandbox_clickhouse_url: str | None = None
    sandbox_clickhouse_database: str = "kcontrol_sandbox"
    sandbox_clickhouse_log_retention_days: int = 30
    sandbox_clickhouse_result_retention_days: int = 90
    # Agent Sandbox
    agent_sandbox_max_concurrent_runs: int = 5
    agent_sandbox_default_max_iterations: int = 20
    agent_sandbox_default_max_tokens: int = 50000
    agent_sandbox_default_max_duration_ms: int = 300000
    agent_sandbox_default_max_cost_usd: float = 1.00
    # Asset Inventory
    asset_inventory_steampipe_binary: str | None = None
    asset_inventory_steampipe_plugin_dir: str | None = None
    asset_inventory_collection_max_concurrent: int = 3
    asset_inventory_collection_timeout_seconds: int = 300
    asset_inventory_collection_default_schedule_hours: int = 24
    asset_inventory_stale_after_misses: int = 1
    asset_inventory_deleted_after_misses: int = 3
    # Google OAuth
    google_oauth_client_id: str | None = None
    google_oauth_client_secret: str | None = None
    # AI Copilot Platform
    ai_provider_url: str | None = None            # LiteLLM / OpenAI-compatible base URL
    ai_provider_type: str = "openai_compatible"   # Provider type fallback: openai | anthropic | azure_openai | openai_compatible
    ai_api_key: str | None = None                 # Default LLM API key (fallback if no DB config)
    ai_model: str = "gpt-5.3-chat"               # Default model (fallback)
    ai_embedding_model: str = "text-embedding-3-small"
    ai_embedding_url: str | None = None           # Embedding endpoint (defaults to ai_provider_url if None)
    ai_embedding_api_key: str | None = None       # Embedding API key (defaults to ai_api_key if None)
    ai_max_tokens: int = 4096
    ai_temperature: float = 0.3
    ai_streaming_enabled: bool = True
    ai_encryption_key: str | None = None          # AES-256-GCM base64 key for API key encryption
    ai_qdrant_url: str | None = None              # Qdrant REST URL (None = NullQdrantMemoryStore)
    ai_qdrant_api_key: str | None = None
    ai_langfuse_enabled: bool = False
    ai_langfuse_public_key: str | None = None
    ai_langfuse_secret_key: str | None = None
    ai_langfuse_host: str | None = None
    ai_approval_expiry_hours: int = 72            # Pending approval TTL
    ai_job_worker_enabled: bool = True            # Enable the background AI job queue worker
    ai_job_worker_poll_interval_seconds: int = 5  # Polling interval for the job worker
    ai_job_worker_max_concurrent: int = 3         # Max concurrent AI jobs (legacy; used as global fallback)
    ai_job_global_max_concurrent: int = 5         # Global max concurrent AI jobs (all types combined)
    ai_job_type_concurrency: str = ""             # JSON dict: {"signal_codegen": 2, "threat_composer": 1, ...}
    signal_store_root: str = ""                   # Root dir for signal file store (default: ./signal_store)
    # Qdrant (evidence checker + memory RAG)
    qdrant_url: str | None = None                 # Qdrant REST URL (alias: ai_qdrant_url)
    qdrant_api_key: str | None = None             # Qdrant API key (alias: ai_qdrant_api_key)
    # PageIndex hierarchical RAG
    framework_builder_batch_size: int = 8         # Number of requirements per LLM call in framework builder
    framework_builder_concurrency: int = 3        # Max concurrent LLM calls for framework builder control batches
    task_builder_batch_size: int = 8              # Number of controls per LLM call in task builder preview
    task_builder_concurrency: int = 5             # Max concurrent LLM calls for task builder preview chunks
    ai_pageindex_enabled: bool = False            # Enable two-phase TOC-based RAG for PDF/DOCX
    ai_pageindex_model: str | None = None         # Override model for PageIndex (defaults to ai_model)


@lru_cache(maxsize=1)
def load_settings() -> Settings:
    _load_dotenv()
    environment = os.getenv("APP_ENV", "local").strip().lower()
    app_name = os.getenv("APP_NAME", "kcontrol-auth").strip() or "kcontrol-auth"
    otel_defaults_enabled = environment in {"local", "development", "dev", "test"}
    access_token_secret = os.getenv("AUTH_ACCESS_TOKEN_SECRET", "").strip()
    if not access_token_secret and environment != "test":
        raise ValueError("AUTH_ACCESS_TOKEN_SECRET is required outside tests.")
    if not access_token_secret:
        access_token_secret = "test-only-secret-change-me"
    otel_protocol = os.getenv("OTEL_EXPORTER_OTLP_PROTOCOL", "http/protobuf").strip() or "http/protobuf"
    if otel_protocol != "http/protobuf":
        raise ValueError("OTEL_EXPORTER_OTLP_PROTOCOL must be http/protobuf.")

    log_format_default = "text" if environment in {"local", "development", "dev"} else "json"

    return Settings(
        environment=environment,
        app_name=app_name,
        log_level=_read_log_level("LOG_LEVEL", default="INFO"),
        log_format=_read_log_format("LOG_FORMAT", default=log_format_default),
        log_level_overrides=_read_log_level_overrides("LOG_LEVEL_OVERRIDES") or None,
        cors_allowed_origins=_read_csv(
            "CORS_ALLOWED_ORIGINS",
            default=("*",) if environment in {"local", "development", "dev", "test"} else (),
        ),
        cors_allowed_methods=_read_csv(
            "CORS_ALLOWED_METHODS",
            default=("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"),
        ),
        cors_allowed_headers=_read_csv(
            "CORS_ALLOWED_HEADERS",
            default=("Authorization", "Content-Type", "X-Request-ID"),
        ),
        cors_allow_credentials=_read_bool("CORS_ALLOW_CREDENTIALS", default=False),
        cors_max_age_seconds=_read_int("CORS_MAX_AGE_SECONDS", default=600, minimum=0),
        rate_limit_enabled=_read_bool("RATE_LIMIT_ENABLED", default=True),
        rate_limit_requests_per_minute=_read_int("RATE_LIMIT_REQUESTS_PER_MINUTE", default=60, minimum=1),
        rate_limit_burst=_read_int("RATE_LIMIT_BURST", default=10, minimum=1),
        rate_limit_exclude_paths=_read_csv(
            "RATE_LIMIT_EXCLUDE_PATHS",
            default=("/livez", "/readyz", "/healthz"),
        ),
        max_request_body_bytes=_read_int("MAX_REQUEST_BODY_BYTES", default=115_343_360, minimum=1024),
        auth_local_core_enabled=_read_bool(
            "AUTH_LOCAL_CORE_ENABLED",
            default=environment in {"local", "development", "dev", "test"},
        ),
        run_migrations_on_startup=_read_bool("APP_RUN_MIGRATIONS_ON_STARTUP", default=False),
        database_url=_build_database_url(),
        database_min_pool_size=_read_int("DB_POOL_MIN_SIZE", default=1, minimum=1),
        database_max_pool_size=_read_int("DB_POOL_MAX_SIZE", default=10, minimum=1),
        database_command_timeout_seconds=_read_int("DB_COMMAND_TIMEOUT_SECONDS", default=30, minimum=1),
        access_token_secret=access_token_secret,
        access_token_algorithm=_read_access_token_algorithm("AUTH_ACCESS_TOKEN_ALGORITHM", default="HS256"),
        access_token_issuer=os.getenv("AUTH_ACCESS_TOKEN_ISSUER", app_name),
        access_token_audience=os.getenv("AUTH_ACCESS_TOKEN_AUDIENCE", f"{app_name}-api"),
        access_token_ttl_seconds=_read_int("AUTH_ACCESS_TOKEN_TTL_SECONDS", default=900, minimum=60),
        access_token_signing_key_id=os.getenv("AUTH_ACCESS_TOKEN_SIGNING_KEY_ID", "").strip() or None,
        access_token_keys=_read_json_dict("AUTH_ACCESS_TOKEN_KEYS"),
        access_token_private_key=os.getenv("AUTH_ACCESS_TOKEN_PRIVATE_KEY", "").strip() or None,
        access_token_public_key=os.getenv("AUTH_ACCESS_TOKEN_PUBLIC_KEY", "").strip() or None,
        access_token_jti_blocklist_enabled=_read_bool("AUTH_JTI_BLOCKLIST_ENABLED", default=False),
        refresh_token_ttl_seconds=_read_int(
            "AUTH_REFRESH_TOKEN_TTL_SECONDS",
            default=60 * 60 * 24 * 30,
            minimum=300,
        ),
        brute_force_window_seconds=_read_int(
            "AUTH_BRUTE_FORCE_WINDOW_SECONDS",
            default=900,
            minimum=60,
        ),
        brute_force_max_attempts=_read_int(
            "AUTH_BRUTE_FORCE_MAX_ATTEMPTS",
            default=5,
            minimum=1,
        ),
        default_tenant_key=os.getenv("AUTH_DEFAULT_TENANT_KEY", "default").strip() or "default",
        trust_proxy_headers=_read_bool("TRUST_PROXY_HEADERS", default=False),
        trusted_proxy_depth=_read_int("TRUSTED_PROXY_DEPTH", default=1, minimum=1),
        migration_directory=BACKEND_DIR / "01_sql_migrations" / "01_migrated",
        app_version=os.getenv("APP_VERSION", "0.1.0").strip() or "0.1.0",
        otel_enabled=_read_bool("OTEL_ENABLED", default=otel_defaults_enabled),
        otel_metrics_enabled=_read_bool("OTEL_METRICS_ENABLED", default=otel_defaults_enabled),
        otel_service_name=os.getenv("OTEL_SERVICE_NAME", "").strip() or None,
        otel_exporter_otlp_protocol=otel_protocol,
        otel_exporter_otlp_endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "").strip() or None,
        otel_exporter_otlp_traces_endpoint=os.getenv("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT", "").strip() or None,
        otel_exporter_otlp_logs_endpoint=os.getenv("OTEL_EXPORTER_OTLP_LOGS_ENDPOINT", "").strip() or None,
        otel_exporter_otlp_headers=_read_csv("OTEL_EXPORTER_OTLP_HEADERS"),
        otel_exporter_otlp_timeout_seconds=_read_int(
            "OTEL_EXPORTER_OTLP_TIMEOUT_SECONDS",
            default=10,
            minimum=1,
        ),
        otel_exporter_otlp_insecure=_read_bool("OTEL_EXPORTER_OTLP_INSECURE", default=True),
        otel_traces_enabled=_read_bool("OTEL_TRACES_ENABLED", default=otel_defaults_enabled),
        otel_logs_enabled=_read_bool("OTEL_LOGS_ENABLED", default=False),
        otel_sample_ratio=_read_float("OTEL_SAMPLE_RATIO", default=1.0, minimum=0.0, maximum=1.0),
        otel_function_trace_enabled=_read_bool(
            "OTEL_FUNCTION_TRACE_ENABLED",
            default=otel_defaults_enabled,
        ),
        otel_function_trace_include_args=_read_bool("OTEL_FUNCTION_TRACE_INCLUDE_ARGS", default=True),
        otel_function_trace_include_return=_read_bool("OTEL_FUNCTION_TRACE_INCLUDE_RETURN", default=True),
        otel_function_trace_include_exceptions=_read_bool(
            "OTEL_FUNCTION_TRACE_INCLUDE_EXCEPTIONS",
            default=True,
        ),
        otel_function_trace_max_value_length=_read_int(
            "OTEL_FUNCTION_TRACE_MAX_VALUE_LENGTH",
            default=256,
            minimum=32,
        ),
        otel_function_trace_max_collection_items=_read_int(
            "OTEL_FUNCTION_TRACE_MAX_COLLECTION_ITEMS",
            default=10,
            minimum=1,
        ),
        otel_function_trace_excluded_module_prefixes=_read_csv(
            "OTEL_FUNCTION_TRACE_EXCLUDED_MODULE_PREFIXES",
            default=(
                "backend.01_core.telemetry",
                "backend.01_core.logging_utils",
                "backend.90_tests",
            ),
        ),
        otel_function_trace_excluded_path_fragments=_read_csv(
            "OTEL_FUNCTION_TRACE_EXCLUDED_PATH_FRAGMENTS",
            default=("/__pycache__/",),
        ),
        otel_function_metrics_enabled=_read_bool(
            "OTEL_FUNCTION_METRICS_ENABLED",
            default=otel_defaults_enabled,
        ),
        otel_function_metrics_flush_interval_seconds=_read_int(
            "OTEL_FUNCTION_METRICS_FLUSH_INTERVAL_SECONDS",
            default=15,
            minimum=1,
        ),
        glitchtip_dsn=os.getenv("GLITCHTIP_DSN", "").strip() or None,
        glitchtip_traces_sample_rate=_read_float(
            "GLITCHTIP_TRACES_SAMPLE_RATE",
            default=0.1,
            minimum=0.0,
            maximum=1.0,
        ),
        cache_url=os.getenv("CACHE_URL", "").strip() or None,
        cache_key_prefix=os.getenv("CACHE_KEY_PREFIX", "kcontrol:").strip() or "kcontrol:",
        cache_default_ttl_seconds=_read_int("CACHE_DEFAULT_TTL_SECONDS", default=300, minimum=1),
        impersonation_enabled=_read_bool("IMPERSONATION_ENABLED", default=False),
        impersonation_access_token_ttl_seconds=_read_int(
            "IMPERSONATION_ACCESS_TOKEN_TTL_SECONDS", default=900, minimum=60,
        ),
        impersonation_refresh_token_ttl_seconds=_read_int(
            "IMPERSONATION_REFRESH_TOKEN_TTL_SECONDS", default=1800, minimum=300,
        ),
        api_key_enabled=_read_bool("API_KEY_ENABLED", default=True),
        api_key_max_per_user=_read_int("API_KEY_MAX_PER_USER", default=10, minimum=1),
        api_key_default_ttl_days=_read_int("API_KEY_DEFAULT_TTL_DAYS", default=0, minimum=0) or None,
        api_key_rate_limit_requests_per_minute=_read_int(
            "API_KEY_RATE_LIMIT_REQUESTS_PER_MINUTE", default=120, minimum=1,
        ),
        platform_base_url=os.getenv("PLATFORM_BASE_URL", "").strip(),
        magic_link_enabled=_read_bool("MAGIC_LINK_ENABLED", default=True),
        magic_link_default_ttl_hours=_read_int("MAGIC_LINK_DEFAULT_TTL_HOURS", default=24, minimum=1),
        magic_link_frontend_verify_url=(
            os.getenv("MAGIC_LINK_FRONTEND_VERIFY_URL", "").strip()
            or (os.getenv("PLATFORM_BASE_URL", "").strip().rstrip("/") + "/magic-link/verify"
                if os.getenv("PLATFORM_BASE_URL", "").strip() else "")
        ),
        magic_link_assignee_frontend_verify_url=(
            os.getenv("MAGIC_LINK_ASSIGNEE_FRONTEND_VERIFY_URL", "").strip()
            or (os.getenv("PLATFORM_BASE_URL", "").strip().rstrip("/") + "/magic-link/verify"
                if os.getenv("PLATFORM_BASE_URL", "").strip() else "")
        ),
        password_reset_frontend_url=(
            os.getenv("PASSWORD_RESET_FRONTEND_URL", "").strip()
            or (os.getenv("PLATFORM_BASE_URL", "").strip().rstrip("/") + "/reset-password"
                if os.getenv("PLATFORM_BASE_URL", "").strip() else "")
        ),
        password_reset_expiry_minutes=_read_int("PASSWORD_RESET_EXPIRY_MINUTES", default=30, minimum=5),
        otp_expiry_minutes=_read_int("OTP_EXPIRY_MINUTES", default=10, minimum=1),
        notification_enabled=_read_bool("NOTIFICATION_ENABLED", default=False),
        notification_email_provider=os.getenv("NOTIFICATION_EMAIL_PROVIDER", "").strip() or None,
        notification_smtp_host=os.getenv("NOTIFICATION_SMTP_HOST", "").strip() or None,
        notification_smtp_port=_read_int("NOTIFICATION_SMTP_PORT", default=587, minimum=1),
        notification_smtp_user=os.getenv("NOTIFICATION_SMTP_USER", "").strip() or None,
        notification_smtp_password=os.getenv("NOTIFICATION_SMTP_PASSWORD", "").strip() or None,
        notification_smtp_use_tls=_read_bool("NOTIFICATION_SMTP_USE_TLS", default=False),
        notification_smtp_start_tls=_read_bool("NOTIFICATION_SMTP_START_TLS", default=True),
        notification_from_email=os.getenv("NOTIFICATION_FROM_EMAIL", "").strip() or None,
        notification_from_name=(
            os.getenv("NOTIFICATION_FROM_NAME", "").strip()
            or (
                "K-Control"
                if os.getenv("APP_ENV", "development").strip().lower() in ("production", "prod")
                else f"K-Control {os.getenv('APP_ENV', 'dev').strip().capitalize()}"
            )
        ),
        notification_vapid_private_key=os.getenv("NOTIFICATION_VAPID_PRIVATE_KEY", "").strip() or None,
        notification_vapid_public_key=os.getenv("NOTIFICATION_VAPID_PUBLIC_KEY", "").strip() or None,
        notification_vapid_app_server_key=os.getenv("NOTIFICATION_VAPID_APP_SERVER_KEY", "").strip() or None,
        notification_vapid_claims_email=os.getenv("NOTIFICATION_VAPID_CLAIMS_EMAIL", "").strip() or None,
        notification_queue_poll_interval_seconds=_read_int(
            "NOTIFICATION_QUEUE_POLL_INTERVAL_SECONDS", default=5, minimum=1,
        ),
        notification_queue_batch_size=_read_int(
            "NOTIFICATION_QUEUE_BATCH_SIZE", default=50, minimum=1,
        ),
        notification_email_rate_limit_per_minute=_read_int(
            "NOTIFICATION_EMAIL_RATE_LIMIT_PER_MINUTE", default=100, minimum=1,
        ),
        notification_push_rate_limit_per_minute=_read_int(
            "NOTIFICATION_PUSH_RATE_LIMIT_PER_MINUTE", default=200, minimum=1,
        ),
        notification_tracking_base_url=(
            os.getenv("NOTIFICATION_TRACKING_BASE_URL", "").strip()
            or os.getenv("PLATFORM_BASE_URL", "").strip()
            or None
        ),
        notification_encryption_key=os.getenv("NOTIFICATION_ENCRYPTION_KEY", "").strip() or None,
        notification_unsubscribe_secret=os.getenv("NOTIFICATION_UNSUBSCRIBE_SECRET", "change-me-in-production").strip() or "change-me-in-production",
        notification_inbox_archive_after_days=_read_int("NOTIFICATION_INBOX_ARCHIVE_AFTER_DAYS", default=90, minimum=1),
        notification_inbox_delete_after_days=_read_int("NOTIFICATION_INBOX_DELETE_AFTER_DAYS", default=365, minimum=1),
        # Platform branding (env-overridable, used in email templates)
        platform_company=os.getenv("PLATFORM_COMPANY", "Kreesalis").strip() or "Kreesalis",
        platform_support_url=os.getenv("PLATFORM_SUPPORT_URL", "https://kreesalis.com/support").strip(),
        platform_privacy_url=os.getenv("PLATFORM_PRIVACY_URL", "https://kreesalis.com/privacy").strip(),
        platform_tagline=os.getenv("PLATFORM_TAGLINE", "Continuous Compliance").strip(),
        platform_year=str(__import__("datetime").datetime.utcnow().year),
        # Storage
        storage_provider=os.getenv("STORAGE_PROVIDER", "minio").strip().lower() or "minio",
        storage_max_file_size_mb=_read_int("STORAGE_MAX_FILE_SIZE_MB", default=100, minimum=1),
        storage_s3_bucket=os.getenv("STORAGE_S3_BUCKET", "").strip(),
        storage_s3_region=os.getenv("STORAGE_S3_REGION", "us-east-1").strip() or "us-east-1",
        storage_s3_access_key_id=os.getenv("STORAGE_S3_ACCESS_KEY_ID", "").strip(),
        storage_s3_secret_access_key=os.getenv("STORAGE_S3_SECRET_ACCESS_KEY", "").strip(),
        storage_s3_endpoint_url=os.getenv("STORAGE_S3_ENDPOINT_URL", "").strip(),
        storage_minio_endpoint_url=os.getenv("STORAGE_MINIO_ENDPOINT_URL", "").strip(),
        storage_minio_bucket=os.getenv("STORAGE_MINIO_BUCKET", "").strip(),
        storage_gcs_bucket=os.getenv("STORAGE_GCS_BUCKET", "").strip(),
        storage_gcs_project=os.getenv("STORAGE_GCS_PROJECT", "").strip(),
        storage_gcs_credentials_json=os.getenv("STORAGE_GCS_CREDENTIALS_JSON", "").strip(),
        storage_azure_container=os.getenv("STORAGE_AZURE_CONTAINER", "").strip(),
        storage_azure_account_name=os.getenv("STORAGE_AZURE_ACCOUNT_NAME", "").strip(),
        storage_azure_account_key=os.getenv("STORAGE_AZURE_ACCOUNT_KEY", "").strip(),
        storage_azure_connection_string=os.getenv("STORAGE_AZURE_CONNECTION_STRING", "").strip(),
        # Sandbox
        sandbox_encryption_key=os.getenv("SANDBOX_ENCRYPTION_KEY", "").strip() or None,
        sandbox_ai_provider_url=os.getenv("SANDBOX_AI_PROVIDER_URL", "").strip() or None,
        sandbox_ai_api_key=os.getenv("SANDBOX_AI_API_KEY", "").strip() or None,
        sandbox_ai_model=os.getenv("SANDBOX_AI_MODEL", "gpt-4o").strip() or "gpt-4o",
        sandbox_execution_timeout_ms=_read_int("SANDBOX_EXECUTION_TIMEOUT_MS", default=10000, minimum=1000),
        sandbox_execution_max_memory_mb=_read_int("SANDBOX_EXECUTION_MAX_MEMORY_MB", default=256, minimum=64),
        sandbox_live_session_max_minutes=_read_int("SANDBOX_LIVE_SESSION_MAX_MINUTES", default=30, minimum=1),
        sandbox_live_session_max_per_workspace=_read_int("SANDBOX_LIVE_SESSION_MAX_PER_WORKSPACE", default=5, minimum=1),
        sandbox_live_poll_interval_seconds=_read_int("SANDBOX_LIVE_POLL_INTERVAL_SECONDS", default=10, minimum=1),
        sandbox_clickhouse_url=os.getenv("SANDBOX_CLICKHOUSE_URL", "").strip() or None,
        sandbox_clickhouse_database=os.getenv("SANDBOX_CLICKHOUSE_DATABASE", "kcontrol_sandbox").strip() or "kcontrol_sandbox",
        sandbox_clickhouse_log_retention_days=_read_int("SANDBOX_CLICKHOUSE_LOG_RETENTION_DAYS", default=30, minimum=1),
        sandbox_clickhouse_result_retention_days=_read_int("SANDBOX_CLICKHOUSE_RESULT_RETENTION_DAYS", default=90, minimum=1),
        # Agent Sandbox
        agent_sandbox_max_concurrent_runs=_read_int("AGENT_SANDBOX_MAX_CONCURRENT", default=5, minimum=1),
        agent_sandbox_default_max_iterations=_read_int("AGENT_SANDBOX_DEFAULT_MAX_ITERATIONS", default=20, minimum=1),
        agent_sandbox_default_max_tokens=_read_int("AGENT_SANDBOX_DEFAULT_MAX_TOKENS", default=50000, minimum=100),
        agent_sandbox_default_max_duration_ms=_read_int("AGENT_SANDBOX_DEFAULT_MAX_DURATION_MS", default=300000, minimum=1000),
        agent_sandbox_default_max_cost_usd=float(os.getenv("AGENT_SANDBOX_DEFAULT_MAX_COST_USD", "1.00")),
        # Asset Inventory
        asset_inventory_steampipe_binary=os.getenv("ASSET_INVENTORY_STEAMPIPE_BINARY", "").strip() or None,
        asset_inventory_steampipe_plugin_dir=os.getenv("ASSET_INVENTORY_STEAMPIPE_PLUGIN_DIR", "").strip() or None,
        asset_inventory_collection_max_concurrent=_read_int("ASSET_INVENTORY_COLLECTION_MAX_CONCURRENT", default=3, minimum=1),
        asset_inventory_collection_timeout_seconds=_read_int("ASSET_INVENTORY_COLLECTION_TIMEOUT_SECONDS", default=300, minimum=10),
        asset_inventory_collection_default_schedule_hours=_read_int("ASSET_INVENTORY_COLLECTION_DEFAULT_SCHEDULE_HOURS", default=24, minimum=1),
        asset_inventory_stale_after_misses=_read_int("ASSET_INVENTORY_STALE_AFTER_MISSES", default=1, minimum=1),
        asset_inventory_deleted_after_misses=_read_int("ASSET_INVENTORY_DELETED_AFTER_MISSES", default=3, minimum=1),
        # Google OAuth
        google_oauth_client_id=os.getenv("GOOGLE_OAUTH_CLIENT_ID", "").strip() or None,
        google_oauth_client_secret=os.getenv("GOOGLE_OAUTH_CLIENT_SECRET", "").strip() or None,
        # AI Copilot Platform
        ai_provider_url=os.getenv("AI_PROVIDER_URL", "").strip() or None,
        ai_provider_type=os.getenv("AI_PROVIDER_TYPE", "openai_compatible").strip() or "openai_compatible",
        ai_api_key=os.getenv("AI_API_KEY", "").strip() or None,
        ai_model=os.getenv("AI_MODEL", "gpt-5.3-chat").strip() or "gpt-5.3-chat",
        ai_embedding_model=os.getenv("AI_EMBEDDING_MODEL", "text-embedding-3-small").strip() or "text-embedding-3-small",
        ai_embedding_url=os.getenv("AI_EMBEDDING_URL", "").strip() or None,
        ai_embedding_api_key=os.getenv("AI_EMBEDDING_API_KEY", "").strip() or None,
        ai_max_tokens=_read_int("AI_MAX_TOKENS", default=4096, minimum=256),
        ai_temperature=_read_float("AI_TEMPERATURE", default=0.3, minimum=0.0, maximum=2.0),
        ai_streaming_enabled=_read_bool("AI_STREAMING_ENABLED", default=True),
        ai_encryption_key=os.getenv("AI_ENCRYPTION_KEY", "").strip() or None,
        ai_qdrant_url=os.getenv("AI_QDRANT_URL", "").strip() or None,
        ai_qdrant_api_key=os.getenv("AI_QDRANT_API_KEY", "").strip() or None,
        ai_langfuse_enabled=_read_bool("AI_LANGFUSE_ENABLED", default=False),
        ai_langfuse_public_key=os.getenv("AI_LANGFUSE_PUBLIC_KEY", "").strip() or None,
        ai_langfuse_secret_key=os.getenv("AI_LANGFUSE_SECRET_KEY", "").strip() or None,
        ai_langfuse_host=os.getenv("AI_LANGFUSE_HOST", "").strip() or None,
        ai_approval_expiry_hours=_read_int("AI_APPROVAL_EXPIRY_HOURS", default=72, minimum=1),
        ai_job_worker_enabled=_read_bool("AI_JOB_WORKER_ENABLED", default=True),
        ai_job_worker_poll_interval_seconds=_read_int("AI_JOB_WORKER_POLL_INTERVAL_SECONDS", default=5, minimum=1),
        ai_job_worker_max_concurrent=_read_int("AI_JOB_WORKER_MAX_CONCURRENT", default=3, minimum=1),
        ai_job_global_max_concurrent=_read_int("AI_JOB_GLOBAL_MAX_CONCURRENT", default=5, minimum=1),
        ai_job_type_concurrency=os.getenv("AI_JOB_TYPE_CONCURRENCY", "").strip(),
        signal_store_root=os.getenv("SIGNAL_STORE_ROOT", "").strip(),
        qdrant_url=os.getenv("QDRANT_URL", "").strip() or os.getenv("AI_QDRANT_URL", "").strip() or None,
        qdrant_api_key=os.getenv("QDRANT_API_KEY", "").strip() or os.getenv("AI_QDRANT_API_KEY", "").strip() or None,
        framework_builder_batch_size=_read_int("FRAMEWORK_BUILDER_BATCH_SIZE", default=8, minimum=1),
        framework_builder_concurrency=_read_int("FRAMEWORK_BUILDER_CONCURRENCY", default=3, minimum=1),
        task_builder_batch_size=_read_int("TASK_BUILDER_BATCH_SIZE", default=8, minimum=1),
        task_builder_concurrency=_read_int("TASK_BUILDER_CONCURRENCY", default=5, minimum=1),
        ai_pageindex_enabled=_read_bool("AI_PAGEINDEX_ENABLED", default=False),
        ai_pageindex_model=os.getenv("AI_PAGEINDEX_MODEL", "").strip() or None,
    )
