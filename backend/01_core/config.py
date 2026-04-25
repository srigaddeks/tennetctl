"""
TennetCTL configuration — loads from environment variables.

Config is a frozen dataclass. Immutable after creation.

Env-var contract (ADR-028):
  Allowed TENNETCTL_* vars are listed in _ALLOWED_TENNET_ENV. Any other
  TENNETCTL_* variable whose name looks like a secret (matches SECRET|TOKEN|
  PASSWORD|PRIVATE_KEY|API_KEY) blocks startup. Secrets belong in the vault.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root
_project_root = Path(__file__).resolve().parent.parent.parent
load_dotenv(_project_root / ".env")

_DEFAULT_MODULES = "core,iam,audit,featureflags,vault,notify,monitoring,social_publisher,social_capture,product_ops"
_DEFAULT_PORT = 51734

_ALLOWED_TENNET_ENV = frozenset({
    "TENNETCTL_VAULT_ROOT_KEY",
    "TENNETCTL_MODULES",
    "TENNETCTL_SINGLE_TENANT",
    "TENNETCTL_APP_PORT",
    "TENNETCTL_ALLOW_UNAUTHENTICATED_VAULT",
    "TENNETCTL_NATS_URL",
    "TENNETCTL_MONITORING_ENABLED",
    "TENNETCTL_MONITORING_STORE_KIND",
    "TENNETCTL_MONITORING_AUTO_INSTRUMENT",
    "TENNETCTL_MONITORING_OTLP_AUTH_ENABLED",
    "TENNETCTL_MONITORING_APISIX_SCRAPE_ENABLED",
    "TENNETCTL_MONITORING_APISIX_URL",
    "TENNETCTL_MONITORING_CONSUMER_BATCH_SIZE",
    "TENNETCTL_MONITORING_CONSUMER_MAX_DELIVER",
    "TENNETCTL_MONITORING_CONSUMER_ACK_WAIT_S",
    "TENNETCTL_MONITORING_ROLLUP_ENABLED",
    "TENNETCTL_MONITORING_PARTITION_MANAGER_ENABLED",
    "TENNETCTL_MONITORING_SYNTHETIC_RUNNER_ENABLED",
    "TENNETCTL_MONITORING_NOTIFY_LISTENER_ENABLED",
    "TENNETCTL_MONITORING_ALERT_EVALUATOR_ENABLED",
    "TENNETCTL_MONITORING_ALERT_EVAL_INTERVAL_S",
    "TENNETCTL_MONITORING_ALERT_NOTIFY_THROTTLE_MINUTES",
})

_SECRETISH_RE = re.compile(
    r"(SECRET|TOKEN|PASSWORD|PRIVATE_KEY|API_KEY)$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Config:
    database_url: str
    modules: frozenset[str]
    single_tenant: bool
    app_port: int
    debug: bool
    allow_unauthenticated_vault: bool
    nats_url: str
    monitoring_enabled: bool
    monitoring_store_kind: str
    monitoring_auto_instrument: bool
    monitoring_otlp_auth_enabled: bool
    monitoring_apisix_scrape_enabled: bool
    monitoring_apisix_url: str
    monitoring_consumer_batch_size: int
    monitoring_consumer_max_deliver: int
    monitoring_consumer_ack_wait_s: int
    monitoring_rollup_enabled: bool
    monitoring_partition_manager_enabled: bool
    monitoring_synthetic_runner_enabled: bool
    monitoring_notify_listener_enabled: bool
    monitoring_alert_evaluator_enabled: bool
    monitoring_alert_eval_interval_s: int
    monitoring_alert_notify_throttle_minutes: int


def _enforce_env_contract() -> None:
    """Block startup when any TENNETCTL_* env var looks like a secret outside the allowlist."""
    stray_secretish = []
    stray_unknown = []
    for name in os.environ:
        if not name.startswith("TENNETCTL_"):
            continue
        if name in _ALLOWED_TENNET_ENV:
            continue
        if _SECRETISH_RE.search(name):
            stray_secretish.append(name)
        else:
            stray_unknown.append(name)

    if stray_secretish:
        raise RuntimeError(
            "Secrets must live in the vault, not in env.\n"
            f"  Forbidden TENNETCTL_* vars: {sorted(stray_secretish)}\n"
            f"  Allowed TENNETCTL_* vars:   {sorted(_ALLOWED_TENNET_ENV)}\n"
            "See ADR-028 + .env.example.\n"
            "Move these to the vault: POST /v1/vault {'key': '<lowercase.dotted>', 'value': '<value>'}"
        )
    # Unknown non-secretish TENNETCTL_* vars are logged at startup, not blocking.


def env_var(name: str, *, default: str | None = None) -> str | None:
    """Read an environment variable with an optional default."""
    return os.environ.get(name, default)


def load_config() -> Config:
    """Load configuration from environment variables with sensible defaults."""
    _enforce_env_contract()

    modules_str = os.environ.get("TENNETCTL_MODULES", _DEFAULT_MODULES)
    modules = frozenset(m.strip() for m in modules_str.split(",") if m.strip())

    single_tenant = os.environ.get("TENNETCTL_SINGLE_TENANT", "false").lower() in (
        "true", "1", "yes",
    )
    allow_unauth_vault = os.environ.get(
        "TENNETCTL_ALLOW_UNAUTHENTICATED_VAULT", "false",
    ).lower() in ("true", "1", "yes")

    nats_url = os.environ.get("TENNETCTL_NATS_URL", "nats://localhost:4222")
    monitoring_enabled = os.environ.get(
        "TENNETCTL_MONITORING_ENABLED", "true",
    ).lower() in ("true", "1", "yes")
    monitoring_store_kind = os.environ.get("TENNETCTL_MONITORING_STORE_KIND", "postgres")
    monitoring_auto_instrument = os.environ.get(
        "TENNETCTL_MONITORING_AUTO_INSTRUMENT", "true",
    ).lower() in ("true", "1", "yes")
    monitoring_otlp_auth_enabled = os.environ.get(
        "TENNETCTL_MONITORING_OTLP_AUTH_ENABLED", "false",
    ).lower() in ("true", "1", "yes")
    monitoring_apisix_scrape_enabled = os.environ.get(
        "TENNETCTL_MONITORING_APISIX_SCRAPE_ENABLED", "true",
    ).lower() in ("true", "1", "yes")
    monitoring_apisix_url = os.environ.get(
        "TENNETCTL_MONITORING_APISIX_URL",
        "http://localhost:51791/apisix/prometheus/metrics",
    )
    monitoring_consumer_batch_size = int(
        os.environ.get("TENNETCTL_MONITORING_CONSUMER_BATCH_SIZE", "200")
    )
    monitoring_consumer_max_deliver = int(
        os.environ.get("TENNETCTL_MONITORING_CONSUMER_MAX_DELIVER", "5")
    )
    monitoring_consumer_ack_wait_s = int(
        os.environ.get("TENNETCTL_MONITORING_CONSUMER_ACK_WAIT_S", "30")
    )
    monitoring_rollup_enabled = os.environ.get(
        "TENNETCTL_MONITORING_ROLLUP_ENABLED", "true",
    ).lower() in ("true", "1", "yes")
    monitoring_partition_manager_enabled = os.environ.get(
        "TENNETCTL_MONITORING_PARTITION_MANAGER_ENABLED", "true",
    ).lower() in ("true", "1", "yes")
    monitoring_synthetic_runner_enabled = os.environ.get(
        "TENNETCTL_MONITORING_SYNTHETIC_RUNNER_ENABLED", "true",
    ).lower() in ("true", "1", "yes")
    monitoring_notify_listener_enabled = os.environ.get(
        "TENNETCTL_MONITORING_NOTIFY_LISTENER_ENABLED", "true",
    ).lower() in ("true", "1", "yes")
    monitoring_alert_evaluator_enabled = os.environ.get(
        "TENNETCTL_MONITORING_ALERT_EVALUATOR_ENABLED", "true",
    ).lower() in ("true", "1", "yes")
    monitoring_alert_eval_interval_s = int(
        os.environ.get("TENNETCTL_MONITORING_ALERT_EVAL_INTERVAL_S", "30")
    )
    monitoring_alert_notify_throttle_minutes = int(
        os.environ.get("TENNETCTL_MONITORING_ALERT_NOTIFY_THROTTLE_MINUTES", "15")
    )

    return Config(
        database_url=os.environ.get(
            "DATABASE_URL",
            "postgresql://tennetctl:tennetctl_dev@localhost:5434/tennetctl",
        ),
        modules=modules,
        single_tenant=single_tenant,
        app_port=int(
            os.environ.get("TENNETCTL_APP_PORT", os.environ.get("APP_PORT", str(_DEFAULT_PORT)))
        ),
        debug=os.environ.get("DEBUG", "false").lower() in ("true", "1", "yes"),
        allow_unauthenticated_vault=allow_unauth_vault,
        nats_url=nats_url,
        monitoring_enabled=monitoring_enabled,
        monitoring_store_kind=monitoring_store_kind,
        monitoring_auto_instrument=monitoring_auto_instrument,
        monitoring_otlp_auth_enabled=monitoring_otlp_auth_enabled,
        monitoring_apisix_scrape_enabled=monitoring_apisix_scrape_enabled,
        monitoring_apisix_url=monitoring_apisix_url,
        monitoring_consumer_batch_size=monitoring_consumer_batch_size,
        monitoring_consumer_max_deliver=monitoring_consumer_max_deliver,
        monitoring_consumer_ack_wait_s=monitoring_consumer_ack_wait_s,
        monitoring_rollup_enabled=monitoring_rollup_enabled,
        monitoring_partition_manager_enabled=monitoring_partition_manager_enabled,
        monitoring_synthetic_runner_enabled=monitoring_synthetic_runner_enabled,
        monitoring_notify_listener_enabled=monitoring_notify_listener_enabled,
        monitoring_alert_evaluator_enabled=monitoring_alert_evaluator_enabled,
        monitoring_alert_eval_interval_s=monitoring_alert_eval_interval_s,
        monitoring_alert_notify_throttle_minutes=monitoring_alert_notify_throttle_minutes,
    )
