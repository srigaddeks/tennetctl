"""
somashop configuration — frozen dataclass loaded from environment variables.

somashop is the customer-facing app. It does NOT own a Postgres schema —
all writes go through tennetctl IAM (mobile-OTP) + somaerp (catalog,
subscriptions, deliveries) over HTTP.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


def _bool(v: str | None, default: bool = False) -> bool:
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes", "on")


@dataclass(frozen=True)
class Config:
    somashop_port: int
    somashop_debug: bool
    somashop_frontend_origin: str
    tennetctl_base_url: str
    tennetctl_service_api_key: str | None
    somaerp_base_url: str
    # Tenant context for service-scoped reads (catalog browsing). Customers
    # don't carry org/workspace; somashop pins to a single tenant in v1
    # ("the Soma Delights org") which lives in tennetctl IAM.
    somaerp_default_org_id: str | None
    somaerp_default_workspace_id: str | None


def load_config() -> Config:
    return Config(
        somashop_port=int(os.environ.get("SOMASHOP_PORT", "51740")),
        somashop_debug=_bool(os.environ.get("SOMASHOP_DEBUG"), default=False),
        somashop_frontend_origin=os.environ.get(
            "SOMASHOP_FRONTEND_ORIGIN", "http://localhost:51741",
        ),
        tennetctl_base_url=os.environ.get(
            "TENNETCTL_BASE_URL", "http://localhost:51734",
        ),
        tennetctl_service_api_key=os.environ.get("TENNETCTL_SERVICE_API_KEY"),
        somaerp_base_url=os.environ.get(
            "SOMAERP_BASE_URL", "http://localhost:51736",
        ),
        somaerp_default_org_id=os.environ.get("SOMAERP_DEFAULT_ORG_ID"),
        somaerp_default_workspace_id=os.environ.get(
            "SOMAERP_DEFAULT_WORKSPACE_ID",
        ),
    )
