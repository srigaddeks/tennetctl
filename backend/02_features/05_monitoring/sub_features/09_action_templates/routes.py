"""FastAPI routes for action templates and deliveries."""

from importlib import import_module
from fastapi import APIRouter, Query, Request, status

from . import schemas
from .repository import ActionDeliveryRepository
from .service import ActionTemplateService

_response = import_module("backend.01_core.response")
_errors = import_module("backend.01_core.errors")

router = APIRouter(prefix="/v1/monitoring", tags=["monitoring"])


def _scope(request: Request) -> tuple[str, str]:
    state = request.state
    org_id = getattr(state, "org_id", None) or request.headers.get("x-org-id")
    user_id = getattr(state, "user_id", None) or request.headers.get("x-user-id")
    if not org_id:
        raise _errors.AppError("UNAUTHORIZED", "org_id required", 401)
    if not user_id:
        raise _errors.AppError("UNAUTHORIZED", "user_id required", 401)
    return org_id, user_id


@router.get("/action-templates", response_model=dict)
async def list_action_templates(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: bool | None = Query(None, alias="isActive"),
) -> dict:
    """List action templates for the authenticated org."""
    org_id, _ = _scope(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        service = ActionTemplateService(conn)
        rows = await service.repo.list_by_org(org_id, skip=skip, limit=limit, is_active=is_active)
    items = [dict(r) for r in rows]
    return _response.ok(data={"templates": items, "total": len(items)})


@router.post("/action-templates", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_action_template(
    request: Request,
    input_schema: schemas.ActionTemplateCreate,
) -> dict:
    """Create a new action template."""
    org_id, user_id = _scope(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        service = ActionTemplateService(conn)
        row = await service.create(org_id, user_id, input_schema)
    return _response.ok(data=dict(row) if row else {})


@router.get("/action-templates/{template_id}", response_model=dict)
async def get_action_template(
    request: Request,
    template_id: str,
) -> dict:
    """Get a single action template by ID."""
    org_id, _ = _scope(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        service = ActionTemplateService(conn)
        row = await service.repo.get_by_id(template_id, org_id)
    if not row:
        raise _errors.AppError("NOT_FOUND", "Action template not found", 404)
    return _response.ok(data=dict(row))


@router.patch("/action-templates/{template_id}", response_model=dict)
async def update_action_template(
    request: Request,
    template_id: str,
    input_schema: schemas.ActionTemplateUpdate,
) -> dict:
    """Update an action template."""
    org_id, user_id = _scope(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        service = ActionTemplateService(conn)
        row = await service.update(template_id, org_id, user_id, input_schema)
    return _response.ok(data=dict(row) if row else {})


@router.delete("/action-templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_action_template(
    request: Request,
    template_id: str,
) -> None:
    """Soft-delete an action template."""
    org_id, user_id = _scope(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        service = ActionTemplateService(conn)
        await service.delete(template_id, org_id, user_id)


@router.post("/action-templates/{template_id}/test", response_model=dict)
async def test_action_template(
    request: Request,
    template_id: str,
    input_schema: schemas.TestDispatchRequest,
) -> dict:
    """Synchronously test-dispatch a template with sample variables."""
    org_id, _ = _scope(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        service = ActionTemplateService(conn)
        result = await service.test_dispatch(
            template_id,
            org_id,
            input_schema.sample_variables,
        )
    return _response.ok(data=result)


@router.get("/action-deliveries", response_model=dict)
async def list_action_deliveries(
    request: Request,
    template_id: str | None = Query(None),
    delivery_status: str | None = Query(None, alias="status", pattern="^(succeeded|failed|pending)$"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
) -> dict:
    """List action deliveries with optional filters."""
    _scope(request)  # auth check only
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        delivery_repo = ActionDeliveryRepository(conn)
        if template_id:
            rows = await delivery_repo.list_by_template(
                template_id=template_id,
                status=delivery_status,
                skip=skip,
                limit=limit,
            )
        else:
            rows = []
    items = [dict(r) for r in rows]
    return _response.ok(data={"deliveries": items, "total": len(items)})
