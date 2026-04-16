from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, Query

from .catalog import get_catalog, get_agent_by_code, get_agents_by_category, AgentCatalogEntry

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")
_errors_module = import_module("backend.01_core.errors")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims
NotFoundError = _errors_module.NotFoundError

router = InstrumentedAPIRouter(prefix="/api/v1/asb/registry", tags=["agent-sandbox-registry"])


def _entry_to_dict(e: AgentCatalogEntry) -> dict:
    return {
        "code": e.code,
        "name": e.name,
        "description": e.description,
        "category": e.category,
        "execution_mode": e.execution_mode,
        "module_path": e.module_path,
        "inputs": [
            {"name": i.name, "type": i.type, "required": i.required,
             "description": i.description, "default": i.default, "options": i.options}
            for i in e.inputs
        ],
        "outputs": e.outputs,
        "tools_used": e.tools_used,
        "tags": e.tags,
        "default_model": e.default_model,
        "default_temperature": e.default_temperature,
        "max_iterations": e.max_iterations,
        "supports_conversation": e.supports_conversation,
        "icon": e.icon,
    }


@router.get("/")
async def list_registered_agents(
    claims=Depends(get_current_access_claims),
    category: str | None = Query(None, description="Filter by category"),
    tag: str | None = Query(None, description="Filter by tag"),
) -> dict:
    if category:
        agents = get_agents_by_category(category)
    elif tag:
        from .catalog import get_agents_by_tag
        agents = get_agents_by_tag(tag)
    else:
        agents = get_catalog()

    return {
        "items": [_entry_to_dict(a) for a in agents],
        "total": len(agents),
        "categories": sorted(set(a.category for a in get_catalog())),
        "tags": sorted(set(t for a in get_catalog() for t in a.tags)),
    }


@router.get("/{agent_code}")
async def get_registered_agent(
    agent_code: str,
    claims=Depends(get_current_access_claims),
) -> dict:
    entry = get_agent_by_code(agent_code)
    if entry is None:
        raise NotFoundError(f"Agent '{agent_code}' not found in registry")
    return _entry_to_dict(entry)
