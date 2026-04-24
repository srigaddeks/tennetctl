"""Health service — pings tennetctl and reports somaerp uptime + version."""

from __future__ import annotations

import time
from importlib import import_module

_schemas = import_module("apps.somaerp.backend.02_features.00_health.schemas")

SOMAERP_VERSION = "0.1.0"


async def get_health(config, tennetctl_client, *, started_at_monotonic: float):
    base_url = config.tennetctl_base_url
    started = time.monotonic()
    proxy_ok = False
    last_error: str | None = None
    try:
        body = await tennetctl_client.ping()
        proxy_ok = bool(body.get("ok", False)) if isinstance(body, dict) else False
        if not proxy_ok:
            last_error = "tennetctl /health returned non-ok"
    except Exception as exc:
        last_error = f"{type(exc).__name__}: {exc}"
    latency_ms = round((time.monotonic() - started) * 1000.0, 2)

    return _schemas.HealthResponse(
        somaerp_version=SOMAERP_VERSION,
        somaerp_uptime_s=round(time.monotonic() - started_at_monotonic, 3),
        tennetctl_proxy=_schemas.TennetctlProxyStatus(
            ok=proxy_ok,
            base_url=base_url,
            latency_ms=latency_ms,
            last_error=last_error,
        ),
    )
