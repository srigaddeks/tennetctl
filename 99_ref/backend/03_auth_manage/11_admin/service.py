from __future__ import annotations

import json
from importlib import import_module
from uuid import uuid4

from ..constants import AuditEventCategory, AuditEventType
from .repository import AdminRepository
from .schemas import (
    AuditEventListResponse,
    AuditEventResponse,
    FeatureEvaluation,
    FeatureEvaluationResponse,
    ImpersonationHistoryResponse,
    ImpersonationSessionResponse,
    SessionListResponse,
    SessionResponse,
    UserAuditEventListResponse,
    UserDetailResponse,
    UserDisableResponse,
    UserGroupMembershipResponse,
    UserListResponse,
    UserOrgMembershipResponse,
    UserPropertyResponse,
    UserSummaryResponse,
    UserWorkspaceMembershipResponse,
)

_settings_module = import_module("backend.00_config.settings")
_database_module = import_module("backend.01_core.database")
_cache_module = import_module("backend.01_core.cache")
_audit_module = import_module("backend.01_core.audit")
_logging_module = import_module("backend.01_core.logging_utils")
_telemetry_module = import_module("backend.01_core.telemetry")
_permission_module = import_module("backend.03_auth_manage._permission_check")
_engagement_repository_module = import_module("backend.12_engagements.repository")

Settings = _settings_module.Settings
DatabasePool = _database_module.DatabasePool
CacheManager = _cache_module.CacheManager
NullCacheManager = _cache_module.NullCacheManager
AuditEntry = _audit_module.AuditEntry
AuditWriter = _audit_module.AuditWriter
get_logger = _logging_module.get_logger
instrument_class_methods = _telemetry_module.instrument_class_methods
require_permission = _permission_module.require_permission
utc_now_sql = import_module("backend.01_core.time_utils").utc_now_sql
EngagementRepository = _engagement_repository_module.EngagementRepository


@instrument_class_methods(namespace="admin.service", logger_name="backend.admin.service.instrumentation")
class AdminService:

    def __init__(
        self,
        *,
        settings: Settings,
        database_pool: DatabasePool,
        cache: CacheManager | NullCacheManager,
    ) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._cache = cache
        self._repository = AdminRepository()
        self._engagement_repository = EngagementRepository()
        self._audit_writer = AuditWriter(schema_name="03_auth_manage")
        self._logger = get_logger("backend.admin")

    async def list_users(
        self,
        *,
        actor_id: str,
        tenant_key: str,
        limit: int = 50,
        offset: int = 0,
        search: str | None = None,
        is_active: bool | None = None,
        is_disabled: bool | None = None,
        account_status: str | None = None,
        org_id: str | None = None,
        group_id: str | None = None,
        user_category: str | None = None,
    ) -> UserListResponse:
        async with self._database_pool.acquire() as connection:
            if org_id is not None:
                await require_permission(
                    connection,
                    actor_id,
                    "org_management.view",
                    scope_org_id=org_id,
                )
            else:
                await require_permission(connection, actor_id, "admin_console.view")
            users, total = await self._repository.list_users(
                connection,
                tenant_key=tenant_key,
                limit=limit,
                offset=offset,
                search=search,
                is_active=is_active,
                is_disabled=is_disabled,
                account_status=account_status,
                org_id=org_id,
                group_id=group_id,
                user_category=user_category,
            )
        return UserListResponse(
            users=[
                UserSummaryResponse(
                    user_id=str(u["user_id"]),
                    tenant_key=u["tenant_key"],
                    email=u.get("email"),
                    username=u.get("username"),
                    display_name=u.get("display_name"),
                    account_status=u.get("account_status", "unknown"),
                    user_category=u.get("user_category", "full"),
                    is_active=u["is_active"],
                    is_disabled=u["is_disabled"],
                    is_locked=u.get("is_locked", False),
                    is_system=u.get("is_system", False),
                    is_test=u.get("is_test", False),
                    created_at=u["created_at"].isoformat(),
                )
                for u in users
            ],
            total=total,
        )

    async def get_user_detail(
        self,
        *,
        actor_id: str,
        user_id: str,
    ) -> UserDetailResponse:
        from fastapi import HTTPException
        async with self._database_pool.acquire() as connection:
            await require_permission(connection, actor_id, "admin_console.view")
            user = await self._repository.get_user_detail(connection, user_id=user_id)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            properties = await self._repository.get_user_properties(connection, user_id=user_id)
            org_memberships = await self._repository.get_user_org_memberships(connection, user_id=user_id)
            workspace_memberships = await self._repository.get_user_workspace_memberships(connection, user_id=user_id)
            group_memberships = await self._repository.get_user_group_memberships(connection, user_id=user_id)

        return UserDetailResponse(
            user_id=str(user["user_id"]),
            tenant_key=user["tenant_key"],
            email=user.get("email"),
            username=user.get("username"),
            account_status=user.get("account_status", "unknown"),
            is_active=user["is_active"],
            is_disabled=user["is_disabled"],
            created_at=user["created_at"].isoformat(),
            properties=[UserPropertyResponse(key=p["key"], value=p["value"]) for p in properties],
            org_memberships=[
                UserOrgMembershipResponse(
                    org_id=str(m["org_id"]),
                    org_name=m["org_name"],
                    org_type=m.get("org_type") or "unknown",
                    role=m["role"],
                    is_active=m["is_active"],
                    joined_at=m["joined_at"].isoformat(),
                )
                for m in org_memberships
            ],
            workspace_memberships=[
                UserWorkspaceMembershipResponse(
                    workspace_id=str(m["workspace_id"]),
                    workspace_name=m["workspace_name"],
                    workspace_type=m.get("workspace_type") or "unknown",
                    org_id=str(m["org_id"]),
                    org_name=m["org_name"],
                    role=m["role"],
                    is_active=m["is_active"],
                    joined_at=m["joined_at"].isoformat(),
                )
                for m in workspace_memberships
            ],
            group_memberships=[
                UserGroupMembershipResponse(
                    group_id=str(m["group_id"]),
                    group_name=m["group_name"],
                    group_code=m["group_code"],
                    role_level_code=m["role_level_code"],
                    scope_org_id=str(m["scope_org_id"]) if m["scope_org_id"] else None,
                    scope_workspace_id=str(m["scope_workspace_id"]) if m["scope_workspace_id"] else None,
                    is_system=m["is_system"],
                    is_active=m["is_active"],
                    joined_at=m["joined_at"].isoformat(),
                )
                for m in group_memberships
            ],
        )

    async def list_user_sessions(
        self,
        *,
        actor_id: str,
        user_id: str,
        include_revoked: bool = False,
    ) -> SessionListResponse:
        async with self._database_pool.acquire() as connection:
            if actor_id != user_id:
                await require_permission(connection, actor_id, "admin_console.view")
            sessions = await self._repository.list_user_sessions(
                connection, user_id=user_id, include_revoked=include_revoked,
            )
        return SessionListResponse(
            sessions=[
                SessionResponse(
                    session_id=str(s["session_id"]),
                    user_id=str(s["user_id"]),
                    client_ip=s.get("client_ip"),
                    user_agent=s.get("user_agent"),
                    is_impersonation=s["is_impersonation"],
                    created_at=s["created_at"].isoformat(),
                    revoked_at=s["revoked_at"].isoformat() if s.get("revoked_at") else None,
                )
                for s in sessions
            ],
        )

    async def revoke_user_session(
        self,
        *,
        actor_id: str,
        user_id: str,
        session_id: str,
        client_ip: str | None,
        request_id: str | None,
    ) -> None:
        now = utc_now_sql()
        async with self._database_pool.transaction() as connection:
            session_owner = await self._repository.get_session_owner(
                connection,
                session_id=session_id,
            )
            if session_owner is None:
                return
            if actor_id != user_id or session_owner != actor_id:
                await require_permission(connection, actor_id, "admin_console.update")
            await self._repository.revoke_user_session(
                connection,
                session_id=session_id,
                reason="revoked_by_user" if session_owner == actor_id else "revoked_by_admin",
                now=now,
            )
            await self._audit_writer.write_entry(
                connection,
                AuditEntry(
                    id=str(uuid4()),
                    tenant_key="system",
                    entity_type="session",
                    entity_id=session_id,
                    event_type=AuditEventType.SESSION_REVOKED_BY_ADMIN.value,
                    event_category=AuditEventCategory.AUTH.value,
                    occurred_at=now,
                    actor_id=actor_id,
                    actor_type="user",
                    ip_address=client_ip,
                    session_id=None,
                    properties={
                        "revoked_session_id": session_id,
                        "self_service": str(session_owner == actor_id),
                    },
                ),
            )
        self._logger.info(
            "session_revoked_by_admin",
            extra={
                "request_id": request_id,
                "actor_id": actor_id,
                "revoked_session_id": session_id,
                "outcome": "success",
            },
        )

    async def list_audit_events(
        self,
        *,
        actor_id: str,
        tenant_key: str,
        entity_type: str | None = None,
        entity_id: str | None = None,
        actor_id_filter: str | None = None,
        event_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> AuditEventListResponse:
        async with self._database_pool.acquire() as connection:
            if entity_id and entity_type in (None, "org"):
                await require_permission(
                    connection,
                    actor_id,
                    "org_management.view",
                    scope_org_id=entity_id,
                )
            elif entity_id and entity_type == "workspace":
                await require_permission(
                    connection,
                    actor_id,
                    "workspace_management.view",
                    scope_workspace_id=entity_id,
                )
            else:
                await require_permission(connection, actor_id, "admin_console.view")
            events = await self._repository.list_audit_events(
                connection,
                tenant_key=tenant_key,
                entity_type=entity_type,
                entity_id=entity_id,
                actor_id=actor_id_filter,
                event_type=event_type,
                limit=limit,
                offset=offset,
            )
            total = await self._repository.count_audit_events(
                connection,
                tenant_key=tenant_key,
                entity_type=entity_type,
                entity_id=entity_id,
                actor_id=actor_id_filter,
                event_type=event_type,
            )
        return AuditEventListResponse(
            events=[
                AuditEventResponse(
                    id=str(e["id"]),
                    tenant_key=e["tenant_key"],
                    entity_type=e["entity_type"],
                    entity_id=str(e["entity_id"]),
                    event_type=e["event_type"],
                    event_category=e["event_category"],
                    actor_id=str(e["actor_id"]) if e.get("actor_id") else None,
                    actor_type=e.get("actor_type"),
                    ip_address=e.get("ip_address"),
                    session_id=str(e["session_id"]) if e.get("session_id") else None,
                    occurred_at=e["occurred_at"].isoformat(),
                    properties=json.loads(e["properties"]) if isinstance(e.get("properties"), str) else (e.get("properties") or {}),
                )
                for e in events
            ],
            total=total,
        )

    async def list_impersonation_history(
        self,
        *,
        actor_id: str,
        tenant_key: str,
        limit: int = 50,
        offset: int = 0,
    ) -> ImpersonationHistoryResponse:
        async with self._database_pool.acquire() as connection:
            await require_permission(connection, actor_id, "admin_console.view")
            sessions = await self._repository.list_impersonation_sessions(
                connection, tenant_key=tenant_key, limit=limit, offset=offset,
            )
        return ImpersonationHistoryResponse(
            sessions=[
                ImpersonationSessionResponse(
                    session_id=str(s["session_id"]),
                    target_user_id=str(s["target_user_id"]),
                    impersonator_user_id=str(s["impersonator_user_id"]),
                    reason=s.get("reason"),
                    created_at=s["created_at"].isoformat(),
                    revoked_at=s["revoked_at"].isoformat() if s.get("revoked_at") else None,
                    target_email=s.get("target_email"),
                    impersonator_email=s.get("impersonator_email"),
                )
                for s in sessions
            ],
        )

    async def disable_user(
        self,
        *,
        actor_id: str,
        user_id: str,
        client_ip: str | None,
        request_id: str | None,
    ) -> UserDisableResponse:
        from fastapi import HTTPException
        now = utc_now_sql()
        async with self._database_pool.transaction() as connection:
            await require_permission(connection, actor_id, "admin_console.update")
            found = await self._repository.set_user_disabled(
                connection, user_id=user_id, is_disabled=True, now=now,
            )
            if not found:
                raise HTTPException(status_code=404, detail="User not found")
            revoked_sessions = await self._repository.revoke_all_user_sessions(
                connection,
                user_id=user_id,
                reason="user_disabled",
                now=now,
            )
            revoked_memberships = await self._engagement_repository.deactivate_memberships_for_user(
                connection,
                user_id=user_id,
                actor_id=actor_id,
                now=now,
            )
            revoked_grants = await self._engagement_repository.revoke_evidence_grants_for_user(
                connection,
                user_id=user_id,
                revoked_by=actor_id,
                now=now,
            )
            await self._audit_writer.write_entry(
                connection,
                AuditEntry(
                    id=str(uuid4()),
                    tenant_key="system",
                    entity_type="user",
                    entity_id=user_id,
                    event_type=AuditEventType.USER_DISABLED.value,
                    event_category=AuditEventCategory.AUTH.value,
                    occurred_at=now,
                    actor_id=actor_id,
                    actor_type="user",
                    ip_address=client_ip,
                    session_id=None,
                    properties={
                        "target_user_id": user_id,
                        "revoked_session_count": str(revoked_sessions),
                        "revoked_membership_count": str(revoked_memberships),
                        "revoked_evidence_grant_count": str(revoked_grants),
                    },
                ),
            )
        self._logger.info("user_disabled", extra={"actor_id": actor_id, "target_user_id": user_id, "request_id": request_id})
        return UserDisableResponse(user_id=user_id, is_disabled=True)

    async def enable_user(
        self,
        *,
        actor_id: str,
        user_id: str,
        client_ip: str | None,
        request_id: str | None,
    ) -> UserDisableResponse:
        from fastapi import HTTPException
        now = utc_now_sql()
        async with self._database_pool.transaction() as connection:
            await require_permission(connection, actor_id, "admin_console.update")
            found = await self._repository.set_user_disabled(
                connection, user_id=user_id, is_disabled=False, now=now,
            )
            if not found:
                raise HTTPException(status_code=404, detail="User not found")
            await self._audit_writer.write_entry(
                connection,
                AuditEntry(
                    id=str(uuid4()),
                    tenant_key="system",
                    entity_type="user",
                    entity_id=user_id,
                    event_type=AuditEventType.USER_ENABLED.value,
                    event_category=AuditEventCategory.AUTH.value,
                    occurred_at=now,
                    actor_id=actor_id,
                    actor_type="user",
                    ip_address=client_ip,
                    session_id=None,
                    properties={"target_user_id": user_id},
                ),
            )
        self._logger.info("user_enabled", extra={"actor_id": actor_id, "target_user_id": user_id, "request_id": request_id})
        return UserDisableResponse(user_id=user_id, is_disabled=False)

    async def get_user_audit_events(
        self,
        *,
        actor_id: str,
        user_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> UserAuditEventListResponse:
        async with self._database_pool.acquire() as connection:
            await require_permission(connection, actor_id, "admin_console.view")
            events = await self._repository.get_user_audit_events(
                connection, user_id=user_id, limit=limit, offset=offset,
            )
            total = await self._repository.count_user_audit_events(
                connection, user_id=user_id,
            )
        return UserAuditEventListResponse(
            events=[
                AuditEventResponse(
                    id=str(e["id"]),
                    tenant_key=e["tenant_key"],
                    entity_type=e["entity_type"],
                    entity_id=str(e["entity_id"]),
                    event_type=e["event_type"],
                    event_category=e["event_category"],
                    actor_id=str(e["actor_id"]) if e.get("actor_id") else None,
                    actor_type=e.get("actor_type"),
                    ip_address=e.get("ip_address"),
                    session_id=str(e["session_id"]) if e.get("session_id") else None,
                    occurred_at=e["occurred_at"].isoformat(),
                    properties=json.loads(e["properties"]) if isinstance(e.get("properties"), str) else (e.get("properties") or {}),
                )
                for e in events
            ],
            total=total,
        )

    async def delete_user(
        self,
        *,
        actor_id: str,
        user_id: str,
        client_ip: str | None,
        request_id: str | None,
    ) -> None:
        from fastapi import HTTPException
        if actor_id == user_id:
            raise HTTPException(status_code=400, detail="Cannot delete your own account.")
        now = utc_now_sql()
        async with self._database_pool.transaction() as connection:
            await require_permission(connection, actor_id, "admin_console.delete")
            deleted = await self._repository.soft_delete_user(connection, user_id=user_id, now=now)
            if not deleted:
                raise HTTPException(status_code=404, detail="User not found.")
            await self._audit_writer.write_entry(
                connection,
                AuditEntry(
                    id=str(uuid4()),
                    tenant_key=self._settings.default_tenant_key,
                    entity_type="user",
                    entity_id=user_id,
                    event_type="user_deleted",
                    event_category=AuditEventCategory.AUTH.value,
                    occurred_at=now,
                    actor_id=actor_id,
                    actor_type="user",
                    ip_address=client_ip,
                    session_id=None,
                    properties={"deleted_user_id": user_id},
                ),
            )

    async def evaluate_features(
        self,
        *,
        user_id: str,
    ) -> FeatureEvaluationResponse:
        async with self._database_pool.acquire() as connection:
            features = await self._repository.evaluate_user_features(
                connection, user_id=user_id,
            )
        return FeatureEvaluationResponse(
            features=[
                FeatureEvaluation(
                    code=f["code"],
                    name=f["name"],
                    enabled=f["enabled"],
                    permissions=list(f["permissions"]),
                )
                for f in features
            ],
        )
