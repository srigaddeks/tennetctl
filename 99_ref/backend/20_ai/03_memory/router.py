from __future__ import annotations

from importlib import import_module
from typing import Annotated

_telemetry_module = import_module("backend.01_core.telemetry")
_deps_module = import_module("backend.03_auth_manage.dependencies")
_settings_module = import_module("backend.00_config.settings")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _deps_module.get_current_access_claims

router = InstrumentedAPIRouter(prefix="/api/v1/ai/memory", tags=["ai-memory"])


def _get_memory_service():
    settings = _settings_module.load_settings()
    _svc_mod = import_module("backend.20_ai.03_memory.service")
    return _svc_mod.MemoryService(settings=settings)


@router.get("")
async def list_memory(
    claims: Annotated[dict, get_current_access_claims],
) -> list[dict]:
    """List recent memory entries for the current user (last 20)."""
    # For now return empty — full listing requires a scroll/list endpoint on Qdrant
    # which is a heavier operation. Recall is the primary access pattern.
    return []


@router.delete("")
async def forget_all_memory(
    claims: Annotated[dict, get_current_access_claims],
) -> dict:
    """Delete all memory for the current user (GDPR erasure)."""
    settings = _settings_module.load_settings()
    svc = _get_memory_service()
    tenant_key = claims.get("tenant_key", settings.default_tenant_key)
    user_id = claims["sub"]
    ok = await svc.forget_user(tenant_key=tenant_key, user_id=user_id)
    return {"success": ok}
