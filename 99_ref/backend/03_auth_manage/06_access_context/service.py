from __future__ import annotations

from importlib import import_module

from .repository import AccessContextRepository
from .schemas import (
    AccessActionResponse,
    AccessContextResponse,
    OrgContextResponse,
    PlatformContextResponse,
    WorkspaceContextResponse,
)

_database_module = import_module("backend.01_core.database")
_cache_module = import_module("backend.01_core.cache")
_logging_module = import_module("backend.01_core.logging_utils")
_telemetry_module = import_module("backend.01_core.telemetry")
_settings_module = import_module("backend.00_config.settings")
_scoped_groups = import_module("backend.03_auth_manage._scoped_group_provisioning")

Settings = _settings_module.Settings
DatabasePool = _database_module.DatabasePool
CacheManager = _cache_module.CacheManager
NullCacheManager = _cache_module.NullCacheManager
get_logger = _logging_module.get_logger
instrument_class_methods = _telemetry_module.instrument_class_methods

_CACHE_TTL_ACCESS = 300  # 5 minutes


@instrument_class_methods(namespace="access_context.service", logger_name="backend.access_context.instrumentation")
class AccessContextService:
    def __init__(self, *, settings: Settings, database_pool: DatabasePool, cache: CacheManager | NullCacheManager) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._cache = cache
        self._repository = AccessContextRepository()
        self._logger = get_logger("backend.access_context")

    async def resolve(
        self,
        *,
        user_id: str,
        tenant_key: str,
        org_id: str | None = None,
        workspace_id: str | None = None,
    ) -> AccessContextResponse:
        cache_key = f"access:{user_id}:{org_id or '_'}:{workspace_id or '_'}"
        cached = await self._cache.get(cache_key)
        if cached is not None:
            return AccessContextResponse.model_validate_json(cached)

        async with self._database_pool.acquire() as connection:
            resolved_org_id = org_id
            resolved_workspace_id = workspace_id

            if resolved_org_id is None:
                resolved_org_id = await self._repository.get_user_property(
                    connection,
                    user_id=user_id,
                    property_key="default_org_id",
                )
                if resolved_org_id is None:
                    resolved_org_id = await self._repository.get_first_org_id_for_user(
                        connection,
                        user_id=user_id,
                    )

            if resolved_workspace_id is None and resolved_org_id is not None:
                default_workspace_id = await self._repository.get_user_property(
                    connection,
                    user_id=user_id,
                    property_key="default_workspace_id",
                )
                if default_workspace_id:
                    ws_info = await self._repository.get_workspace_info(
                        connection,
                        default_workspace_id,
                    )
                    if ws_info and ws_info.org_id == resolved_org_id:
                        resolved_workspace_id = default_workspace_id
                if resolved_workspace_id is None:
                    resolved_workspace_id = await self._repository.get_first_workspace_id_for_user(
                        connection,
                        user_id=user_id,
                        org_id=resolved_org_id,
                    )

            platform_actions = await self._repository.get_platform_actions(
                connection, user_id=user_id
            )

            org_context = None
            if resolved_org_id:
                org_info = await self._repository.get_org_info(connection, resolved_org_id)
                if org_info:
                    org_actions = await self._repository.get_org_actions(
                        connection, user_id=user_id, org_id=resolved_org_id
                    )
                    org_context = OrgContextResponse(
                        org_id=org_info.id,
                        name=org_info.name,
                        slug=org_info.slug,
                        org_type_code=org_info.org_type_code,
                        actions=[_action_resp(a) for a in org_actions],
                    )

            workspace_context = None
            if resolved_org_id and resolved_workspace_id:
                ws_info = await self._repository.get_workspace_info(connection, resolved_workspace_id)
                if ws_info and ws_info.org_id == resolved_org_id:
                    ws_actions = await self._repository.get_workspace_actions(
                        connection,
                        user_id=user_id,
                        org_id=resolved_org_id,
                        workspace_id=resolved_workspace_id,
                    )
                    product_actions = []
                    if ws_info.product_id:
                        product_actions = await self._repository.get_product_actions(
                            connection,
                            user_id=user_id,
                            org_id=resolved_org_id,
                            workspace_id=resolved_workspace_id,
                            product_id=ws_info.product_id,
                        )
                    # Resolve GRC role for this user in this workspace (None for non-GRC workspaces)
                    grc_role_code: str | None = None
                    if ws_info.workspace_type_code == "grc":
                        grc_role_code = await _scoped_groups.get_workspace_member_grc_role(
                            connection,
                            workspace_id=resolved_workspace_id,
                            user_id=user_id,
                        )
                    workspace_context = WorkspaceContextResponse(
                        workspace_id=ws_info.id,
                        org_id=ws_info.org_id,
                        name=ws_info.name,
                        slug=ws_info.slug,
                        workspace_type_code=ws_info.workspace_type_code,
                        product_id=ws_info.product_id,
                        product_name=ws_info.product_name,
                        product_code=ws_info.product_code,
                        grc_role_code=grc_role_code,
                        actions=[_action_resp(a) for a in ws_actions],
                        product_actions=[_action_resp(a) for a in product_actions],
                    )

        result = AccessContextResponse(
            user_id=user_id,
            tenant_key=tenant_key,
            platform=PlatformContextResponse(actions=[_action_resp(a) for a in platform_actions]),
            current_org=org_context,
            current_workspace=workspace_context,
        )
        await self._cache.set(cache_key, result.model_dump_json(), _CACHE_TTL_ACCESS)
        return result


def _action_resp(a) -> AccessActionResponse:
    return AccessActionResponse(
        feature_code=a.feature_code,
        feature_name=a.feature_name,
        action_code=a.action_code,
        category_code=a.category_code,
        access_mode=a.access_mode,
        env_dev=a.env_dev,
        env_staging=a.env_staging,
        env_prod=a.env_prod,
    )
