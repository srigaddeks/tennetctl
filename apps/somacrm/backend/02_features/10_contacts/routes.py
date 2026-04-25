"""Contact routes — /v1/somacrm/contacts."""

from __future__ import annotations

from importlib import import_module

import httpx
from fastapi import APIRouter, Query, Request, Response

_service = import_module("apps.somacrm.backend.02_features.10_contacts.service")
_schemas = import_module("apps.somacrm.backend.02_features.10_contacts.schemas")
_response = import_module("apps.somacrm.backend.01_core.response")
_errors = import_module("apps.somacrm.backend.01_core.errors")
_authz = import_module("apps.somacrm.backend.01_core.authz")

router = APIRouter(prefix="/v1/somacrm/contacts", tags=["contacts"])


def _require_workspace(request: Request) -> str:
    ws = getattr(request.state, "workspace_id", None)
    if not ws:
        raise _errors.AuthError("Authentication required (no workspace_id).")
    return ws


@router.get("")
async def list_contacts(
    request: Request,
    q: str | None = Query(default=None),
    status: str | None = Query(default=None),
    organization_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> dict:
    workspace_id = _require_workspace(request)
    async with request.app.state.pool.acquire() as conn:
        rows = await _service.list_contacts(
            conn,
            tenant_id=workspace_id,
            q=q,
            status=status,
            organization_id=organization_id,
            limit=limit,
            offset=offset,
        )
    return _response.ok([_schemas.ContactOut(**r).model_dump(mode="json") for r in rows])


@router.post("", status_code=201)
async def create_contact(
    request: Request,
    payload: _schemas.ContactCreate,
) -> dict:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    await _authz.require_permission(
        request.app.state.pool,
        user_id=user_id,
        perm_code="somacrm_contacts.create",
    )
    async with request.app.state.pool.acquire() as conn:
        row = await _service.create_contact(
            conn,
            tennetctl=request.app.state.tennetctl,
            tenant_id=workspace_id,
            actor_user_id=getattr(request.state, "user_id", None),
            org_id=getattr(request.state, "org_id", None),
            session_id=getattr(request.state, "session_id", None),
            data=payload.model_dump(),
        )
    return _response.ok(_schemas.ContactOut(**row).model_dump(mode="json"))


@router.get("/{contact_id}")
async def get_contact(request: Request, contact_id: str) -> dict:
    workspace_id = _require_workspace(request)
    async with request.app.state.pool.acquire() as conn:
        row = await _service.get_contact(conn, tenant_id=workspace_id, contact_id=contact_id)
    return _response.ok(_schemas.ContactOut(**row).model_dump(mode="json"))


@router.patch("/{contact_id}")
async def patch_contact(
    request: Request,
    contact_id: str,
    payload: _schemas.ContactUpdate,
) -> dict:
    workspace_id = _require_workspace(request)
    async with request.app.state.pool.acquire() as conn:
        row = await _service.update_contact(
            conn,
            tennetctl=request.app.state.tennetctl,
            tenant_id=workspace_id,
            actor_user_id=getattr(request.state, "user_id", None),
            org_id=getattr(request.state, "org_id", None),
            session_id=getattr(request.state, "session_id", None),
            contact_id=contact_id,
            patch=payload.model_dump(exclude_unset=True),
        )
    return _response.ok(_schemas.ContactOut(**row).model_dump(mode="json"))


@router.post("/{contact_id}/create-erp-customer", status_code=201)
async def create_erp_customer(request: Request, contact_id: str) -> dict:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    pool = request.app.state.pool
    config = request.app.state.config

    body = await request.json()
    delivery_notes = body.get("delivery_notes")
    acquisition_source = body.get("acquisition_source")

    async with pool.acquire() as conn:
        contact = await _service.get_contact(conn, tenant_id=workspace_id, contact_id=contact_id)

        if contact.get("somaerp_customer_id"):
            return _response.ok({
                "erp_customer_id": contact["somaerp_customer_id"],
                "already_existed": True,
            })

        token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
        slug_base = (contact.get("full_name") or contact.get("first_name") or "customer").lower()
        slug = "".join(c for c in slug_base.replace(" ", "-") if c.isalnum() or c == "-")[:42] + "-" + contact_id[:8]

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{config.somaerp_base_url}/v1/somaerp/customers",
                json={
                    "name": contact.get("full_name") or contact.get("first_name"),
                    "slug": slug,
                    "email": contact.get("email"),
                    "phone": contact.get("phone"),
                    "delivery_notes": delivery_notes,
                    "acquisition_source": acquisition_source or contact.get("lead_source"),
                    "status": "active",
                    "address_jsonb": {},
                },
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            )

        if resp.status_code not in (200, 201):
            raise _errors.TennetctlProxyError(
                f"somaerp returned {resp.status_code}: {resp.text[:200]}",
                code="ERP_CREATE_FAILED",
            )

        erp_data = resp.json()
        erp_customer_id = erp_data["data"]["id"]

        # Link CRM contact → ERP customer
        await _service.update_contact(
            conn,
            tennetctl=request.app.state.tennetctl,
            tenant_id=workspace_id,
            actor_user_id=user_id,
            org_id=getattr(request.state, "org_id", None),
            session_id=getattr(request.state, "session_id", None),
            contact_id=contact_id,
            patch={"somaerp_customer_id": erp_customer_id},
        )

        # Back-link ERP customer → CRM contact (best-effort, non-blocking)
        async with httpx.AsyncClient(timeout=5.0) as back_client:
            await back_client.patch(
                f"{config.somaerp_base_url}/v1/somaerp/customers/{erp_customer_id}",
                json={"somacrm_contact_id": contact_id},
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            )

    return _response.ok({"erp_customer_id": erp_customer_id, "already_existed": False})


@router.get("/{contact_id}/timeline")
async def get_contact_timeline(
    request: Request,
    contact_id: str,
    limit: int = Query(default=200, ge=1, le=500),
) -> dict:
    workspace_id = _require_workspace(request)
    async with request.app.state.pool.acquire() as conn:
        rows = await _service.get_contact_timeline(
            conn, tenant_id=workspace_id, contact_id=contact_id, limit=limit,
        )
    return _response.ok(rows)


@router.delete("/{contact_id}", status_code=204, response_class=Response)
async def delete_contact(request: Request, contact_id: str) -> Response:
    workspace_id = _require_workspace(request)
    async with request.app.state.pool.acquire() as conn:
        await _service.soft_delete_contact(
            conn,
            tennetctl=request.app.state.tennetctl,
            tenant_id=workspace_id,
            actor_user_id=getattr(request.state, "user_id", None),
            org_id=getattr(request.state, "org_id", None),
            session_id=getattr(request.state, "session_id", None),
            contact_id=contact_id,
        )
    return Response(status_code=204)
