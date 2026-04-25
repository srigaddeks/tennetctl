"""Products — read-through proxy to somaerp catalog.

Customers see a curated, public-friendly subset of somaerp's product
catalog (active SKUs only, with descriptive fields). All reads go
through somaerp; somashop never owns product data.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

from fastapi import APIRouter, HTTPException, Request

_proxy = import_module("apps.somashop.backend.01_core.proxy")

router = APIRouter(tags=["products"])


def _bearer(request: Request) -> str | None:
    auth = request.headers.get("authorization") or ""
    if auth.lower().startswith("bearer "):
        return auth.split(None, 1)[1]
    return None


def _ws(request: Request) -> dict[str, str]:
    """Forward x-org-id / x-workspace-id headers to somaerp."""
    h: dict[str, str] = {}
    org = request.headers.get("x-org-id")
    ws = request.headers.get("x-workspace-id")
    if org:
        h["x-org-id"] = org
    if ws:
        h["x-workspace-id"] = ws
    return h


def _service_workspace_headers(request: Request) -> dict[str, str]:
    """Service-scoped reads need to declare somaerp's tenant context.

    Catalog browsing is public from a customer POV — they don't have an
    org/workspace assignment. We resolve somaerp's default tenant from
    config + service-key auth, so customers can read the menu without
    sign-in.
    """
    cfg = request.app.state.config
    h: dict[str, str] = {}
    if getattr(cfg, "somaerp_default_org_id", None):
        h["x-org-id"] = cfg.somaerp_default_org_id
    if getattr(cfg, "somaerp_default_workspace_id", None):
        h["x-workspace-id"] = cfg.somaerp_default_workspace_id
    return h


@router.get("/v1/products")
async def list_products(request: Request) -> dict:
    """Public catalog list. Proxies somaerp /v1/somaerp/catalog/products
    using somashop's service API key — customers don't need to be signed
    in to browse."""
    erp: Any = request.app.state.somaerp
    try:
        result = await erp.request(
            "GET",
            "/v1/somaerp/catalog/products",
            use_service_session=True,
            extra_headers=_service_workspace_headers(request),
        )
    except _proxy.ProxyError as e:
        raise HTTPException(status_code=e.status, detail=e.body) from e
    return result


@router.get("/v1/subscription-plans")
async def list_subscription_plans(request: Request) -> dict:
    """Public list of buyable plans (service-scoped)."""
    erp: Any = request.app.state.somaerp
    try:
        result = await erp.request(
            "GET",
            "/v1/somaerp/subscriptions/plans",
            use_service_session=True,
            extra_headers=_service_workspace_headers(request),
        )
    except _proxy.ProxyError as e:
        raise HTTPException(status_code=e.status, detail=e.body) from e
    return result
