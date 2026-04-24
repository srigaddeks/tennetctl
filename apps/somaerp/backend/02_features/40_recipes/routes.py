"""Recipe routes — /v1/somaerp/recipes + nested ingredients/steps/equipment/cost."""

from __future__ import annotations

from importlib import import_module

from fastapi import APIRouter, Query, Request, Response

_service = import_module(
    "apps.somaerp.backend.02_features.40_recipes.service",
)
_schemas = import_module(
    "apps.somaerp.backend.02_features.40_recipes.schemas",
)
_response = import_module("apps.somaerp.backend.01_core.response")
_errors = import_module("apps.somaerp.backend.01_core.errors")

router = APIRouter(
    prefix="/v1/somaerp",
    tags=["recipes"],
)


def _require_workspace(request: Request) -> str:
    ws = getattr(request.state, "workspace_id", None)
    if not ws:
        raise _errors.AuthError("Authentication required (no workspace_id).")
    return ws


# ── Recipes CRUD ────────────────────────────────────────────────────────


@router.get("/recipes")
async def list_recipes(
    request: Request,
    product_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
    q: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    include_deleted: bool = Query(default=False),
) -> dict:
    workspace_id = _require_workspace(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        rows = await _service.list_recipes(
            conn,
            tenant_id=workspace_id,
            product_id=product_id,
            status=status,
            q=q,
            limit=limit,
            offset=offset,
            include_deleted=include_deleted,
        )
    data = [_schemas.RecipeOut(**r).model_dump(mode="json") for r in rows]
    return _response.ok(data)


@router.post("/recipes", status_code=201)
async def create_recipe(
    request: Request,
    payload: _schemas.RecipeCreate,
) -> dict:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    async with pool.acquire() as conn:
        row = await _service.create_recipe(
            conn,
            tennetctl=tennetctl,
            tenant_id=workspace_id,
            actor_user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            data=payload.model_dump(mode="python"),
        )
    return _response.ok(_schemas.RecipeOut(**row).model_dump(mode="json"))


@router.get("/recipes/{recipe_id}")
async def get_recipe(request: Request, recipe_id: str) -> dict:
    workspace_id = _require_workspace(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        row = await _service.get_recipe(
            conn, tenant_id=workspace_id, recipe_id=recipe_id,
        )
    return _response.ok(_schemas.RecipeOut(**row).model_dump(mode="json"))


@router.patch("/recipes/{recipe_id}")
async def patch_recipe(
    request: Request,
    recipe_id: str,
    payload: _schemas.RecipeUpdate,
) -> dict:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    async with pool.acquire() as conn:
        row = await _service.update_recipe(
            conn,
            tennetctl=tennetctl,
            tenant_id=workspace_id,
            actor_user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            recipe_id=recipe_id,
            patch=payload.model_dump(exclude_unset=True, mode="python"),
        )
    return _response.ok(_schemas.RecipeOut(**row).model_dump(mode="json"))


@router.delete(
    "/recipes/{recipe_id}", status_code=204, response_class=Response,
)
async def delete_recipe(request: Request, recipe_id: str) -> Response:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    async with pool.acquire() as conn:
        await _service.soft_delete_recipe(
            conn,
            tennetctl=tennetctl,
            tenant_id=workspace_id,
            actor_user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            recipe_id=recipe_id,
        )
    return Response(status_code=204)


# ── Ingredients (nested) ────────────────────────────────────────────────


@router.get("/recipes/{recipe_id}/ingredients")
async def list_ingredients(request: Request, recipe_id: str) -> dict:
    workspace_id = _require_workspace(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        rows = await _service.list_ingredients(
            conn, tenant_id=workspace_id, recipe_id=recipe_id,
        )
    data = [
        _schemas.RecipeIngredientOut(**r).model_dump(mode="json") for r in rows
    ]
    return _response.ok(data)


@router.post("/recipes/{recipe_id}/ingredients", status_code=201)
async def create_ingredient(
    request: Request,
    recipe_id: str,
    payload: _schemas.RecipeIngredientCreate,
) -> dict:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    async with pool.acquire() as conn:
        row = await _service.create_ingredient(
            conn,
            tennetctl=tennetctl,
            tenant_id=workspace_id,
            actor_user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            recipe_id=recipe_id,
            data=payload.model_dump(mode="python"),
        )
    return _response.ok(
        _schemas.RecipeIngredientOut(**row).model_dump(mode="json"),
    )


@router.patch("/recipes/{recipe_id}/ingredients/{ingredient_id}")
async def patch_ingredient(
    request: Request,
    recipe_id: str,
    ingredient_id: str,
    payload: _schemas.RecipeIngredientUpdate,
) -> dict:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    async with pool.acquire() as conn:
        row = await _service.update_ingredient(
            conn,
            tennetctl=tennetctl,
            tenant_id=workspace_id,
            actor_user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            recipe_id=recipe_id,
            ingredient_id=ingredient_id,
            patch=payload.model_dump(exclude_unset=True, mode="python"),
        )
    return _response.ok(
        _schemas.RecipeIngredientOut(**row).model_dump(mode="json"),
    )


@router.delete(
    "/recipes/{recipe_id}/ingredients/{ingredient_id}",
    status_code=204,
    response_class=Response,
)
async def delete_ingredient(
    request: Request, recipe_id: str, ingredient_id: str,
) -> Response:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    async with pool.acquire() as conn:
        await _service.delete_ingredient(
            conn,
            tennetctl=tennetctl,
            tenant_id=workspace_id,
            actor_user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            recipe_id=recipe_id,
            ingredient_id=ingredient_id,
        )
    return Response(status_code=204)


# ── Steps (nested) ──────────────────────────────────────────────────────


@router.get("/recipes/{recipe_id}/steps")
async def list_steps(request: Request, recipe_id: str) -> dict:
    workspace_id = _require_workspace(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        rows = await _service.list_steps(
            conn, tenant_id=workspace_id, recipe_id=recipe_id,
        )
    data = [_schemas.RecipeStepOut(**r).model_dump(mode="json") for r in rows]
    return _response.ok(data)


@router.post("/recipes/{recipe_id}/steps", status_code=201)
async def create_step(
    request: Request,
    recipe_id: str,
    payload: _schemas.RecipeStepCreate,
) -> dict:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    async with pool.acquire() as conn:
        row = await _service.create_step(
            conn,
            tennetctl=tennetctl,
            tenant_id=workspace_id,
            actor_user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            recipe_id=recipe_id,
            data=payload.model_dump(mode="python"),
        )
    return _response.ok(_schemas.RecipeStepOut(**row).model_dump(mode="json"))


@router.patch("/recipes/{recipe_id}/steps/{step_id}")
async def patch_step(
    request: Request,
    recipe_id: str,
    step_id: str,
    payload: _schemas.RecipeStepUpdate,
) -> dict:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    async with pool.acquire() as conn:
        row = await _service.update_step(
            conn,
            tennetctl=tennetctl,
            tenant_id=workspace_id,
            actor_user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            recipe_id=recipe_id,
            step_id=step_id,
            patch=payload.model_dump(exclude_unset=True, mode="python"),
        )
    return _response.ok(_schemas.RecipeStepOut(**row).model_dump(mode="json"))


@router.delete(
    "/recipes/{recipe_id}/steps/{step_id}",
    status_code=204,
    response_class=Response,
)
async def delete_step(
    request: Request, recipe_id: str, step_id: str,
) -> Response:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    async with pool.acquire() as conn:
        await _service.delete_step(
            conn,
            tennetctl=tennetctl,
            tenant_id=workspace_id,
            actor_user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            recipe_id=recipe_id,
            step_id=step_id,
        )
    return Response(status_code=204)


# ── Step-Equipment link ─────────────────────────────────────────────────


@router.get("/recipes/{recipe_id}/steps/{step_id}/equipment")
async def list_step_equipment(
    request: Request, recipe_id: str, step_id: str,
) -> dict:
    workspace_id = _require_workspace(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        rows = await _service.list_step_equipment(
            conn, tenant_id=workspace_id, recipe_id=recipe_id, step_id=step_id,
        )
    return _response.ok(rows)


@router.post(
    "/recipes/{recipe_id}/steps/{step_id}/equipment", status_code=201,
)
async def link_step_equipment(
    request: Request,
    recipe_id: str,
    step_id: str,
    payload: _schemas.StepEquipmentLinkCreate,
) -> dict:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    async with pool.acquire() as conn:
        row = await _service.link_step_equipment(
            conn,
            tennetctl=tennetctl,
            tenant_id=workspace_id,
            actor_user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            recipe_id=recipe_id,
            step_id=step_id,
            equipment_id=payload.equipment_id,
        )
    return _response.ok(row)


@router.delete(
    "/recipes/{recipe_id}/steps/{step_id}/equipment/{equipment_id}",
    status_code=204,
    response_class=Response,
)
async def unlink_step_equipment(
    request: Request, recipe_id: str, step_id: str, equipment_id: str,
) -> Response:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    async with pool.acquire() as conn:
        await _service.unlink_step_equipment(
            conn,
            tennetctl=tennetctl,
            tenant_id=workspace_id,
            actor_user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            recipe_id=recipe_id,
            step_id=step_id,
            equipment_id=equipment_id,
        )
    return Response(status_code=204)


# ── Cost rollup ─────────────────────────────────────────────────────────


@router.get("/recipes/{recipe_id}/cost")
async def get_recipe_cost(request: Request, recipe_id: str) -> dict:
    workspace_id = _require_workspace(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        row = await _service.get_recipe_cost(
            conn, tenant_id=workspace_id, recipe_id=recipe_id,
        )
    return _response.ok(_schemas.RecipeCostSummary(**row).model_dump(mode="json"))
