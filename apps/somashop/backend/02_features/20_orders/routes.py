"""Customer orders — proxies somaerp subscriptions on behalf of the
authenticated customer.

The customer's tennetctl user_id is the somaerp `customer_id` link
key. v1 keeps it simple: list subscriptions where customer_id matches
the caller's user_id; create subscriptions by mapping the customer's
chosen plan into somaerp.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

_proxy = import_module("apps.somashop.backend.01_core.proxy")

router = APIRouter(tags=["orders"])


def _bearer(request: Request) -> str | None:
    auth = request.headers.get("authorization") or ""
    if auth.lower().startswith("bearer "):
        return auth.split(None, 1)[1]
    return None


class CreateOrderRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    subscription_plan_id: str = Field(..., min_length=1)
    address_line1: str = Field(..., min_length=1, max_length=200)
    address_pincode: str = Field(..., min_length=4, max_length=10)
    city: str = Field(..., min_length=1, max_length=80)
    notes: str | None = None


def _service_workspace_headers(request: Request) -> dict[str, str]:
    cfg = request.app.state.config
    h: dict[str, str] = {}
    if getattr(cfg, "somaerp_default_org_id", None):
        h["x-org-id"] = cfg.somaerp_default_org_id
    if getattr(cfg, "somaerp_default_workspace_id", None):
        h["x-workspace-id"] = cfg.somaerp_default_workspace_id
    return h


@router.get("/v1/my-orders")
async def list_my_orders(request: Request) -> dict:
    """List subscriptions belonging to the signed-in customer.

    Resolves customer identity via the caller's bearer token, then queries
    somaerp using somashop's service session (since the customer has no
    org/workspace assignment in the back-office tenant).
    """
    bearer = _bearer(request)
    if not bearer:
        raise HTTPException(
            status_code=401,
            detail={"ok": False, "error": {"code": "UNAUTHORIZED", "message": "sign in required"}},
        )
    tnc: Any = request.app.state.tennetctl
    erp: Any = request.app.state.somaerp
    try:
        me = await tnc.request("GET", "/v1/auth/me", bearer=bearer)
        user_id = me["data"]["user"]["id"]
        result = await erp.request(
            "GET", "/v1/somaerp/subscriptions",
            use_service_session=True,
            params={"customer_id": user_id},
            extra_headers=_service_workspace_headers(request),
        )
        return result
    except _proxy.ProxyError as e:
        # If customer has no orders, somaerp may return empty list (200) —
        # 404 means the route exists but no rows; treat as empty too.
        if e.status == 404:
            return {"ok": True, "data": []}
        raise HTTPException(status_code=e.status, detail=e.body) from e
