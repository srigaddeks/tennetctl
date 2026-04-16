from __future__ import annotations


from importlib import import_module
from uuid import uuid4

from asyncpg import Pool

from .repository import PortalViewRepository
from .schemas import (
    AddViewRouteRequest,
    AssignViewToRoleRequest,
    CreatePortalViewRequest,
    PortalViewDetailResponse,
    PortalViewListResponse,
    RoleViewListResponse,
    UpdatePortalViewRequest,
    UserViewsResponse,
    ViewRouteResponse,
)

_audit_module = import_module("backend.01_core.audit")
_perm_check_module = import_module("backend.03_auth_manage._permission_check")
_time_module = import_module("backend.01_core.time_utils")
_grc_access = import_module("backend.03_auth_manage.18_grc_roles.access_check")

AuditEntry = _audit_module.AuditEntry
AuditWriter = _audit_module.AuditWriter
require_permission = _perm_check_module.require_permission
utc_now_sql = _time_module.utc_now_sql


class PortalViewService:
    def __init__(self, *, settings=None, database_pool: Pool, cache=None, **_kwargs) -> None:
        self._repo = PortalViewRepository(database_pool)
        self._pool = database_pool
        self._audit_writer = AuditWriter(schema_name="03_auth_manage")

    # ── helpers ──────────────────────────────────────────────────────────────

    def _build_view_list(self, views: list[dict], all_routes: list[dict]) -> list[PortalViewDetailResponse]:
        routes_by_view: dict[str, list[ViewRouteResponse]] = {}
        for r in all_routes:
            routes_by_view.setdefault(r["view_code"], []).append(ViewRouteResponse(**r))
        return [
            PortalViewDetailResponse(**v, routes=routes_by_view.get(v["code"], []))
            for v in views
        ]

    # ── Public (no permission required, JWT-only) ────────────────────────────

    async def resolve_user_views(self, user_id: str, org_id: str | None = None) -> UserViewsResponse:
        """Resolve all views for the current user through the role chain, scoped to org.

        When a user has GRC access grants (scoped to specific frameworks/engagements),
        their portal views come only from the GRC role on their workspace membership
        (Path 4), not from generic org membership (Path 2) which grants all views.
        """
        try:
            # Check if user has GRC grants — if so, restrict to GRC-role-based views only
            if org_id:
                async with self._pool.acquire() as conn:
                    has_grants = await _grc_access.has_any_grants(conn, user_id=user_id, org_id=org_id)
                if has_grants:
                    view_codes = await self._repo.resolve_grc_role_views(user_id, org_id=org_id)
                    if not view_codes:
                        view_codes = ["grc"]
                    try:
                        views = await self._repo.list_views()
                        all_routes = await self._repo.list_view_routes()
                    except Exception:
                        return UserViewsResponse(views=[])
                    all_items = self._build_view_list(views, all_routes)
                    items = [v for v in all_items if v.code in view_codes]
                    return UserViewsResponse(views=items)

            view_codes = await self._repo.resolve_user_views(user_id, org_id=org_id)
        except Exception:
            # Tables may not exist yet (migration not run) — return empty
            return UserViewsResponse(views=[])

        if not view_codes:
            # No role-view assignments yet — fallback to GRC for backwards compat
            view_codes = ["grc"]

        try:
            views = await self._repo.list_views()
            all_routes = await self._repo.list_view_routes()
        except Exception:
            return UserViewsResponse(views=[])

        all_items = self._build_view_list(views, all_routes)
        items = [v for v in all_items if v.code in view_codes]
        return UserViewsResponse(views=items)

    # ── Admin (requires platform permissions) ────────────────────────────────

    async def list_views(self, actor_id: str) -> PortalViewListResponse:
        async with self._pool.acquire() as conn:
            await require_permission(conn, actor_id, "access_governance_console.view")
        views = await self._repo.list_views(include_inactive=True)
        all_routes = await self._repo.list_view_routes()
        return PortalViewListResponse(views=self._build_view_list(views, all_routes))

    async def create_view(
        self, payload: CreatePortalViewRequest, actor_id: str,
        client_ip: str | None = None, session_id: str | None = None, request_id: str | None = None,
    ) -> PortalViewDetailResponse:
        async with self._pool.acquire() as conn:
            await require_permission(conn, actor_id, "feature_flag_registry.create")
        view = await self._repo.create_view(
            code=payload.code, name=payload.name, description=payload.description,
            color=payload.color, icon=payload.icon, sort_order=payload.sort_order,
            default_route=payload.default_route,
        )
        async with self._pool.acquire() as conn:
            await self._audit_writer.write_entry(conn, AuditEntry(
                id=str(uuid4()), tenant_key="default", entity_type="portal_view",
                entity_id=str(view["id"]), event_type="view_created", event_category="access",
                occurred_at=utc_now_sql(), actor_id=actor_id,
                ip_address=client_ip, session_id=session_id,
                properties={"code": payload.code, "name": payload.name},
            ))
        return PortalViewDetailResponse(**view, routes=[])

    async def update_view(
        self, code: str, payload: UpdatePortalViewRequest, actor_id: str,
        client_ip: str | None = None, session_id: str | None = None, request_id: str | None = None,
    ) -> PortalViewDetailResponse:
        async with self._pool.acquire() as conn:
            await require_permission(conn, actor_id, "feature_flag_registry.update")
        view = await self._repo.update_view(
            code,
            name=payload.name, description=payload.description,
            color=payload.color, icon=payload.icon,
            sort_order=payload.sort_order, is_active=payload.is_active,
            default_route=payload.default_route,
        )
        if view is None:
            _errors_module = import_module("backend.01_core.errors")
            raise _errors_module.NotFoundError(f"View '{code}' not found.")
        routes = await self._repo.list_view_routes(code)
        async with self._pool.acquire() as conn:
            await self._audit_writer.write_entry(conn, AuditEntry(
                id=str(uuid4()), tenant_key="default", entity_type="portal_view",
                entity_id=str(view["id"]), event_type="view_updated", event_category="access",
                occurred_at=utc_now_sql(), actor_id=actor_id,
                ip_address=client_ip, session_id=session_id,
                properties={"code": code},
            ))
        routes_by_view: dict[str, list[ViewRouteResponse]] = {}
        for r in routes:
            routes_by_view.setdefault(r["view_code"], []).append(ViewRouteResponse(**r))
        return PortalViewDetailResponse(**view, routes=routes_by_view.get(code, []))

    async def delete_view(
        self, code: str, actor_id: str,
        client_ip: str | None = None, session_id: str | None = None, request_id: str | None = None,
    ) -> None:
        async with self._pool.acquire() as conn:
            await require_permission(conn, actor_id, "feature_flag_registry.delete")
        deleted_view = await self._repo.delete_view(code)
        if not deleted_view:
            _errors_module = import_module("backend.01_core.errors")
            raise _errors_module.NotFoundError(f"View '{code}' not found.")
        async with self._pool.acquire() as conn:
            await self._audit_writer.write_entry(conn, AuditEntry(
                id=str(uuid4()), tenant_key="default", entity_type="portal_view",
                entity_id=str(deleted_view["id"]), event_type="view_deleted", event_category="access",
                occurred_at=utc_now_sql(), actor_id=actor_id,
                ip_address=client_ip, session_id=session_id,
                properties={"code": code},
            ))

    async def add_route(
        self, view_code: str, payload: AddViewRouteRequest, actor_id: str,
    ) -> ViewRouteResponse:
        async with self._pool.acquire() as conn:
            await require_permission(conn, actor_id, "feature_flag_registry.update")
        route = await self._repo.add_route(
            view_code=view_code, route_prefix=payload.route_prefix,
            is_read_only=payload.is_read_only, sort_order=payload.sort_order,
            sidebar_label=payload.sidebar_label, sidebar_icon=payload.sidebar_icon,
            sidebar_section=payload.sidebar_section,
        )
        return ViewRouteResponse(**route)

    async def remove_route(self, view_code: str, route_prefix: str, actor_id: str) -> None:
        async with self._pool.acquire() as conn:
            await require_permission(conn, actor_id, "feature_flag_registry.update")
        removed = await self._repo.remove_route(view_code, route_prefix)
        if not removed:
            _errors_module = import_module("backend.01_core.errors")
            raise _errors_module.NotFoundError(f"Route '{route_prefix}' not found in view '{view_code}'.")

    async def list_role_views(self, role_id: str, actor_id: str) -> RoleViewListResponse:
        async with self._pool.acquire() as conn:
            await require_permission(conn, actor_id, "access_governance_console.view")
        assignments = await self._repo.list_role_views(role_id)
        return RoleViewListResponse(
            assignments=[{"role_id": a["role_id"], "view_code": a["view_code"]} for a in assignments]
        )

    async def list_all_role_view_assignments(self, actor_id: str) -> RoleViewListResponse:
        async with self._pool.acquire() as conn:
            await require_permission(conn, actor_id, "access_governance_console.view")
        assignments = await self._repo.list_all_role_view_assignments()
        return RoleViewListResponse(
            assignments=[{"role_id": a["role_id"], "view_code": a["view_code"]} for a in assignments]
        )

    async def assign_view_to_role(
        self,
        role_id: str,
        payload: AssignViewToRoleRequest,
        actor_id: str,
        client_ip: str | None = None,
        session_id: str | None = None,
        request_id: str | None = None,
    ) -> None:
        async with self._pool.acquire() as conn:
            await require_permission(conn, actor_id, "group_access_assignment.assign")
        await self._repo.assign_view_to_role(role_id, payload.view_code, actor_id)
        async with self._pool.acquire() as conn:
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid4()),
                    tenant_key="default",
                    entity_type="role",
                    entity_id=role_id,
                    event_type="view_assigned",
                    event_category="access",
                    occurred_at=utc_now_sql(),
                    actor_id=actor_id,
                    ip_address=client_ip,
                    session_id=session_id,
                    properties={"view_code": payload.view_code},
                ),
            )

    async def revoke_view_from_role(
        self,
        role_id: str,
        view_code: str,
        actor_id: str,
        client_ip: str | None = None,
        session_id: str | None = None,
        request_id: str | None = None,
    ) -> None:
        async with self._pool.acquire() as conn:
            await require_permission(conn, actor_id, "group_access_assignment.assign")
        await self._repo.revoke_view_from_role(role_id, view_code)
        async with self._pool.acquire() as conn:
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid4()),
                    tenant_key="default",
                    entity_type="role",
                    entity_id=role_id,
                    event_type="view_revoked",
                    event_category="access",
                    occurred_at=utc_now_sql(),
                    actor_id=actor_id,
                    ip_address=client_ip,
                    session_id=session_id,
                    properties={"view_code": view_code},
                ),
            )
