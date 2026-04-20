"""FastAPI routes for action templates and deliveries."""

from importlib import import_module
from fastapi import APIRouter, Depends, Query, status

from . import schemas
from .service import ActionTemplateService

_response = import_module("backend.01_core.response")

router = APIRouter(prefix="/v1/monitoring", tags=["monitoring"])


@router.get("/action-templates", response_model=dict)
async def list_action_templates(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: bool = Query(None, alias="isActive"),
    ctx = Depends(lambda: None),  # Will be injected by middleware
) -> dict:
    """List action templates for the authenticated org."""
    # Placeholder: real implementation would use ctx for org_id/user_id
    return _response.ok(data={"templates": [], "total": 0})


@router.post("/action-templates", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_action_template(
    input_schema: schemas.ActionTemplateCreate,
    ctx = Depends(lambda: None),
) -> dict:
    """Create a new action template."""
    # Placeholder
    return _response.ok(data={"id": "template-id", **input_schema.dict()})


@router.get("/action-templates/{template_id}", response_model=dict)
async def get_action_template(
    template_id: str,
    ctx = Depends(lambda: None),
) -> dict:
    """Get a single action template by ID."""
    # Placeholder
    return _response.ok(data={})


@router.patch("/action-templates/{template_id}", response_model=dict)
async def update_action_template(
    template_id: str,
    input_schema: schemas.ActionTemplateUpdate,
    ctx = Depends(lambda: None),
) -> dict:
    """Update an action template."""
    # Placeholder
    return _response.ok(data={})


@router.delete("/action-templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_action_template(
    template_id: str,
    ctx = Depends(lambda: None),
) -> None:
    """Soft-delete an action template."""
    # Placeholder
    pass


@router.post("/action-templates/{template_id}/test", response_model=dict)
async def test_action_template(
    template_id: str,
    input_schema: schemas.TestDispatchRequest,
    ctx = Depends(lambda: None),
) -> dict:
    """Synchronously test-dispatch a template with sample variables."""
    # Placeholder
    return _response.ok(
        data={
            "success": True,
            "status_code": 200,
            "response_excerpt": "OK",
        }
    )


@router.get("/action-deliveries", response_model=dict)
async def list_action_deliveries(
    template_id: str = Query(None),
    status: str = Query(None, pattern="^(succeeded|failed|pending)$"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    ctx = Depends(lambda: None),
) -> dict:
    """List action deliveries with optional filters."""
    # Placeholder
    return _response.ok(data={"deliveries": [], "total": 0})
