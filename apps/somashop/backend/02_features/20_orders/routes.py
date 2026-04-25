"""Customer orders — proxies somaerp subscriptions on behalf of the
authenticated customer.

Order placement (POST /v1/my-orders) does:
  1. Resolve customer's tennetctl user via /v1/auth/me
  2. Find or create a somaerp customer keyed on the user_id (slug derived)
  3. Create a somaerp subscription against the chosen plan
  4. Return the new subscription
"""

from __future__ import annotations

import re
from datetime import date
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


def _service_workspace_headers(request: Request) -> dict[str, str]:
    cfg = request.app.state.config
    h: dict[str, str] = {}
    if getattr(cfg, "somaerp_default_org_id", None):
        h["x-org-id"] = cfg.somaerp_default_org_id
    if getattr(cfg, "somaerp_default_workspace_id", None):
        h["x-workspace-id"] = cfg.somaerp_default_workspace_id
    return h


def _slug_from_user_id(user_id: str) -> str:
    """Customer slug for somaerp must match `^[a-z0-9][a-z0-9-]*$`. Use the
    last 12 chars of the UUID with dashes preserved."""
    s = re.sub(r"[^a-z0-9-]", "", user_id.lower())
    s = s.lstrip("-")
    return f"shop-{s[-16:]}" if s else "shop-customer"


class CreateOrderRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    subscription_plan_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1, max_length=200)
    phone: str = Field(..., min_length=4, max_length=20)
    address_line1: str = Field(..., min_length=1, max_length=200)
    address_pincode: str = Field(..., min_length=4, max_length=10)
    city: str = Field(..., min_length=1, max_length=80)
    notes: str | None = None


@router.get("/v1/my-orders/{subscription_id}")
async def get_my_order(request: Request, subscription_id: str) -> dict:
    """Single-subscription detail. Verifies the subscription belongs to the
    caller before returning."""
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
        customer_id = await _customer_id_for_user(request, erp, user_id)
        if customer_id is None:
            raise HTTPException(status_code=404, detail={"ok": False, "error": {"code": "NOT_FOUND", "message": "no order"}})

        result = await erp.request(
            "GET", f"/v1/somaerp/subscriptions/{subscription_id}",
            use_service_session=True,
            extra_headers=_service_workspace_headers(request),
        )
        sub = result.get("data") or {}
        if sub.get("customer_id") != customer_id:
            # Don't reveal cross-tenant sub identifiers — pretend it's missing.
            raise HTTPException(status_code=404, detail={"ok": False, "error": {"code": "NOT_FOUND", "message": "no order"}})
        return result
    except _proxy.ProxyError as e:
        raise HTTPException(status_code=e.status, detail=e.body) from e


async def _customer_id_for_user(request: Request, erp: Any, user_id: str) -> str | None:
    slug = _slug_from_user_id(user_id)
    headers = _service_workspace_headers(request)
    try:
        listing = await erp.request(
            "GET", "/v1/somaerp/customers",
            use_service_session=True, params={"slug": slug},
            extra_headers=headers,
        )
        for row in listing.get("data") or []:
            if row.get("slug") == slug:
                return row["id"]
    except _proxy.ProxyError:
        return None
    return None


@router.get("/v1/my-orders")
async def list_my_orders(request: Request) -> dict:
    """List subscriptions belonging to the signed-in customer.

    Resolves customer identity via the caller's bearer token, looks up
    the somaerp customer record (slug = `shop-<user_id_tail>`), then
    fetches subscriptions for that customer using somashop's service
    session.
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

        customer_id = await _customer_id_for_user(request, erp, user_id)
        if customer_id is None:
            # No somaerp customer record yet — first-time visitor.
            return {"ok": True, "data": []}

        result = await erp.request(
            "GET", "/v1/somaerp/subscriptions",
            use_service_session=True,
            params={"customer_id": customer_id},
            extra_headers=_service_workspace_headers(request),
        )
        return result
    except _proxy.ProxyError as e:
        if e.status == 404:
            return {"ok": True, "data": []}
        raise HTTPException(status_code=e.status, detail=e.body) from e


async def _ensure_crm_contact(
    request: Request,
    *,
    name: str,
    phone: str,
    somaerp_customer_id: str,
) -> None:
    """Best-effort cross-app handshake: create a somacrm contact linked
    to the new ERP customer so sales can follow up. Silent on any
    failure — an order must not break if the CRM is down."""
    crm = getattr(request.app.state, "somacrm", None)
    if crm is None:
        return
    parts = name.strip().split(" ", 1)
    first = parts[0] or "Customer"
    last = parts[1] if len(parts) > 1 else None
    body = {
        "first_name": first,
        "last_name": last,
        "phone": phone,
        "lead_source": "somashop",
        "somaerp_customer_id": somaerp_customer_id,
        "properties": {"acquisition_source": "somashop"},
    }
    try:
        await crm.request(
            "POST", "/v1/somacrm/contacts",
            use_service_session=True,
            json=body,
        )
    except _proxy.ProxyError:
        pass


async def _find_or_create_customer(
    request: Request,
    erp: Any,
    *,
    user_id: str,
    name: str,
    phone: str,
    address: dict[str, Any],
    notes: str | None,
) -> str:
    """Resolve a somaerp customer for this tennetctl user. Slug is derived
    from the user_id so re-orders reuse the same customer record."""
    slug = _slug_from_user_id(user_id)
    headers = _service_workspace_headers(request)
    # Look up first by slug filter
    try:
        listing = await erp.request(
            "GET", "/v1/somaerp/customers",
            use_service_session=True, params={"slug": slug},
            extra_headers=headers,
        )
        for row in listing.get("data") or []:
            if row.get("slug") == slug:
                return row["id"]
    except _proxy.ProxyError:
        pass
    # Create
    created = await erp.request(
        "POST", "/v1/somaerp/customers",
        use_service_session=True,
        json={
            "name": name,
            "slug": slug,
            "phone": phone,
            "address_jsonb": address,
            "delivery_notes": notes,
            "acquisition_source": "somashop",
            "status": "active",
            "properties": {"tennetctl_user_id": user_id},
        },
        extra_headers=headers,
    )
    return created["data"]["id"]


@router.post("/v1/my-orders", status_code=201)
async def place_order(request: Request, body: CreateOrderRequest) -> dict:
    """Customer-facing order placement.

    Creates a somaerp customer (or reuses one slugged by the caller's
    tennetctl user_id), then creates a subscription against the chosen
    plan starting today. Returns the new subscription.
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

        customer_id = await _find_or_create_customer(
            request, erp,
            user_id=user_id,
            name=body.name,
            phone=body.phone,
            address={
                "line1": body.address_line1,
                "city": body.city,
                "pincode": body.address_pincode,
            },
            notes=body.notes,
        )

        sub = await erp.request(
            "POST", "/v1/somaerp/subscriptions",
            use_service_session=True,
            json={
                "customer_id": customer_id,
                "plan_id": body.subscription_plan_id,
                "start_date": date.today().isoformat(),
                "properties": {"placed_via": "somashop"},
            },
            extra_headers=_service_workspace_headers(request),
        )

        # Cross-app: ensure a somacrm contact exists for sales follow-up,
        # linked to the ERP customer via somaerp_customer_id. Best-effort —
        # an order must not fail if CRM is down or rejects a duplicate.
        await _ensure_crm_contact(
            request,
            name=body.name,
            phone=body.phone,
            somaerp_customer_id=customer_id,
        )

        return sub
    except _proxy.ProxyError as e:
        raise HTTPException(status_code=e.status, detail=e.body) from e
