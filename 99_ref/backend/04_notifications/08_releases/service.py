from __future__ import annotations

import uuid
from importlib import import_module

from .repository import ReleaseRepository
from ..schemas import (
    CreateBroadcastRequest,
    CreateIncidentRequest,
    CreateIncidentUpdateRequest,
    CreateReleaseRequest,
    IncidentListResponse,
    IncidentResponse,
    IncidentUpdateResponse,
    ReleaseListResponse,
    ReleaseResponse,
    UpdateIncidentRequest,
    UpdateReleaseRequest,
)

_database_module = import_module("backend.01_core.database")
_cache_module = import_module("backend.01_core.cache")
_logging_module = import_module("backend.01_core.logging_utils")
_telemetry_module = import_module("backend.01_core.telemetry")
_settings_module = import_module("backend.00_config.settings")
_errors_module = import_module("backend.01_core.errors")
_audit_module = import_module("backend.01_core.audit")
_perm_check_module = import_module("backend.03_auth_manage._permission_check")
_time_module = import_module("backend.01_core.time_utils")
_constants_module = import_module("backend.04_notifications.constants")

Settings = _settings_module.Settings
DatabasePool = _database_module.DatabasePool
CacheManager = _cache_module.CacheManager
NullCacheManager = _cache_module.NullCacheManager
get_logger = _logging_module.get_logger
instrument_class_methods = _telemetry_module.instrument_class_methods
NotFoundError = _errors_module.NotFoundError
ConflictError = _errors_module.ConflictError
AuditEntry = _audit_module.AuditEntry
AuditWriter = _audit_module.AuditWriter
require_permission = _perm_check_module.require_permission
utc_now_sql = _time_module.utc_now_sql
NotificationType = _constants_module.NotificationType
IncidentStatus = _constants_module.IncidentStatus

_CACHE_TTL_RELEASES = 300
_CACHE_TTL_INCIDENTS = 120

_AUDIT_EVENT_CATEGORY = "notification"


@instrument_class_methods(namespace="releases.service", logger_name="backend.notifications.releases.instrumentation")
class ReleaseIncidentService:
    def __init__(
        self, *, settings: Settings, database_pool: DatabasePool, cache: CacheManager | NullCacheManager
    ) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._cache = cache
        self._repository = ReleaseRepository()
        self._audit_writer = AuditWriter(schema_name="03_auth_manage")
        self._logger = get_logger("backend.notifications.releases")

    # ------------------------------------------------------------------ #
    # Releases
    # ------------------------------------------------------------------ #

    async def list_releases(
        self, *, user_id: str, tenant_key: str, limit: int = 50, offset: int = 0, status: str | None = None
    ) -> ReleaseListResponse:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "notification_broadcasts.view")
            records, total = await self._repository.list_releases(
                conn, tenant_key, limit=limit, offset=offset, status=status
            )
        return ReleaseListResponse(items=[_release_response(r) for r in records], total=total)

    async def get_release(self, *, user_id: str, release_id: str) -> ReleaseResponse:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "notification_broadcasts.view")
            record = await self._repository.get_release_by_id(conn, release_id)
        if not record:
            raise NotFoundError(f"Release '{release_id}' not found")
        return _release_response(record)

    async def create_release(
        self, *, user_id: str, tenant_key: str, request: CreateReleaseRequest
    ) -> ReleaseResponse:
        now = utc_now_sql()
        release_id = str(uuid.uuid4())
        async with self._database_pool.transaction() as conn:
            await require_permission(conn, user_id, "notification_broadcasts.create")
            record = await self._repository.create_release(
                conn,
                release_id=release_id,
                tenant_key=tenant_key,
                version=request.version,
                title=request.title,
                summary=request.summary,
                body_markdown=request.body_markdown,
                body_html=request.body_html,
                changelog_url=request.changelog_url,
                release_date=request.release_date,
                created_by=user_id,
                now=now,
            )
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="release",
                    entity_id=release_id,
                    event_type="release_created",
                    event_category=_AUDIT_EVENT_CATEGORY,
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={"version": request.version, "title": request.title},
                ),
            )
        return _release_response(record)

    async def update_release(
        self, *, user_id: str, release_id: str, request: UpdateReleaseRequest
    ) -> ReleaseResponse:
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            await require_permission(conn, user_id, "notification_broadcasts.update")
            record = await self._repository.update_release(
                conn, release_id, now=now,
                title=request.title,
                summary=request.summary,
                body_markdown=request.body_markdown,
                body_html=request.body_html,
                changelog_url=request.changelog_url,
                release_date=request.release_date,
            )
        if not record:
            raise NotFoundError(f"Release '{release_id}' not found")
        return _release_response(record)

    async def publish_release(
        self, *, user_id: str, tenant_key: str, release_id: str, notify_users: bool = True
    ) -> ReleaseResponse:
        """Publish a release and optionally broadcast to all users."""
        now = utc_now_sql()
        broadcast_id = None

        async with self._database_pool.transaction() as conn:
            await require_permission(conn, user_id, "notification_broadcasts.create")

            release = await self._repository.get_release_by_id(conn, release_id)
            if not release:
                raise NotFoundError(f"Release '{release_id}' not found")
            if release.status != "draft":
                raise ConflictError(f"Release '{release_id}' is already {release.status}")

            # Create a broadcast for this release if requested
            if notify_users:
                broadcast_id = await self._create_release_broadcast(
                    conn, release=release, tenant_key=tenant_key, user_id=user_id, now=now
                )

            record = await self._repository.publish_release(conn, release_id, broadcast_id, now)
            if not record:
                raise NotFoundError(f"Release '{release_id}' not found")

            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="release",
                    entity_id=release_id,
                    event_type="release_published",
                    event_category=_AUDIT_EVENT_CATEGORY,
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={
                        "version": release.version,
                        "broadcast_id": broadcast_id or "",
                        "notify_users": str(notify_users),
                    },
                ),
            )
        return _release_response(record)

    async def archive_release(self, *, user_id: str, release_id: str) -> ReleaseResponse:
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            await require_permission(conn, user_id, "notification_broadcasts.update")
            record = await self._repository.archive_release(conn, release_id, now)
        if not record:
            raise NotFoundError(f"Release '{release_id}' not found")
        return _release_response(record)

    async def _create_release_broadcast(self, conn, *, release, tenant_key, user_id, now) -> str:
        """Create a global broadcast for a published release."""
        _broadcast_repo_module = import_module("backend.04_notifications.06_broadcasts.repository")
        broadcast_repo = _broadcast_repo_module.BroadcastRepository()

        broadcast_id = str(uuid.uuid4())
        body_text = f"Version {release.version}: {release.summary}"
        body_html = None
        if release.body_html:
            body_html = release.body_html
        elif release.body_markdown:
            body_html = f"<h2>{release.title}</h2><p>{release.summary}</p>"

        await broadcast_repo.create_broadcast(
            conn,
            broadcast_id=broadcast_id,
            tenant_key=tenant_key,
            title=f"New Release: {release.title} (v{release.version})",
            body_text=body_text,
            body_html=body_html,
            scope="global",
            scope_org_id=None,
            scope_workspace_id=None,
            notification_type_code=NotificationType.PLATFORM_RELEASE,
            priority_code="normal",
            severity="info",
            is_critical=False,
            template_code=None,
            scheduled_at=None,
            created_by=user_id,
            now=now,
        )
        return broadcast_id

    # ------------------------------------------------------------------ #
    # Incidents
    # ------------------------------------------------------------------ #

    async def list_incidents(
        self, *, user_id: str, tenant_key: str, limit: int = 50, offset: int = 0, status: str | None = None
    ) -> IncidentListResponse:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "notification_broadcasts.view")
            records, total = await self._repository.list_incidents(
                conn, tenant_key, limit=limit, offset=offset, status=status
            )
        return IncidentListResponse(items=[_incident_response(r) for r in records], total=total)

    async def get_incident(self, *, user_id: str, incident_id: str) -> IncidentResponse:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "notification_broadcasts.view")
            record = await self._repository.get_incident_by_id(conn, incident_id)
            if not record:
                raise NotFoundError(f"Incident '{incident_id}' not found")
            updates = await self._repository.list_incident_updates(conn, incident_id)
        resp = _incident_response(record)
        resp.updates = [_incident_update_response(u) for u in updates]
        return resp

    async def create_incident(
        self, *, user_id: str, tenant_key: str, request: CreateIncidentRequest
    ) -> IncidentResponse:
        now = utc_now_sql()
        incident_id = str(uuid.uuid4())
        broadcast_id = None

        async with self._database_pool.transaction() as conn:
            await require_permission(conn, user_id, "notification_broadcasts.create")

            # Auto-create critical broadcast for incidents
            if request.notify_users:
                broadcast_id = await self._create_incident_broadcast(
                    conn,
                    title=request.title,
                    description=request.description,
                    severity=request.severity,
                    tenant_key=tenant_key,
                    user_id=user_id,
                    now=now,
                    template_code=request.template_code,
                )

            record = await self._repository.create_incident(
                conn,
                incident_id=incident_id,
                tenant_key=tenant_key,
                title=request.title,
                description=request.description,
                severity=request.severity,
                affected_components=request.affected_components,
                started_at=request.started_at or now,
                broadcast_id=broadcast_id,
                created_by=user_id,
                now=now,
            )

            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="incident",
                    entity_id=incident_id,
                    event_type="incident_created",
                    event_category=_AUDIT_EVENT_CATEGORY,
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={
                        "title": request.title,
                        "severity": request.severity,
                        "notify_users": str(request.notify_users),
                    },
                ),
            )
        return _incident_response(record)

    async def update_incident(
        self, *, user_id: str, incident_id: str, request: UpdateIncidentRequest
    ) -> IncidentResponse:
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            await require_permission(conn, user_id, "notification_broadcasts.update")
            record = await self._repository.update_incident(
                conn, incident_id, now=now,
                title=request.title,
                description=request.description,
                severity=request.severity,
                affected_components=request.affected_components,
            )
        if not record:
            raise NotFoundError(f"Incident '{incident_id}' not found")
        return _incident_response(record)

    async def post_incident_update(
        self, *, user_id: str, tenant_key: str, incident_id: str, request: CreateIncidentUpdateRequest
    ) -> IncidentResponse:
        """Post a status update to an incident, optionally notifying users."""
        now = utc_now_sql()
        update_id = str(uuid.uuid4())
        broadcast_id = None

        async with self._database_pool.transaction() as conn:
            await require_permission(conn, user_id, "notification_broadcasts.create")

            incident = await self._repository.get_incident_by_id(conn, incident_id)
            if not incident:
                raise NotFoundError(f"Incident '{incident_id}' not found")

            # Broadcast the update if requested
            if request.notify_users and request.is_public:
                broadcast_id = await self._create_incident_update_broadcast(
                    conn,
                    incident=incident,
                    status=request.status,
                    message=request.message,
                    tenant_key=tenant_key,
                    user_id=user_id,
                    now=now,
                )

            await self._repository.create_incident_update(
                conn,
                update_id=update_id,
                incident_id=incident_id,
                status=request.status,
                message=request.message,
                is_public=request.is_public,
                broadcast_id=broadcast_id,
                created_by=user_id,
                now=now,
            )

            # Update incident status
            update_kwargs = {"now": now, "status": request.status}
            if request.status == IncidentStatus.RESOLVED:
                update_kwargs["resolved_at"] = now
            await self._repository.update_incident(conn, incident_id, **update_kwargs)

            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="incident",
                    entity_id=incident_id,
                    event_type="incident_updated",
                    event_category=_AUDIT_EVENT_CATEGORY,
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={
                        "status": request.status,
                        "message": request.message[:200],
                    },
                ),
            )

        # Re-fetch with updates
        return await self.get_incident(user_id=user_id, incident_id=incident_id)

    async def _create_incident_broadcast(
        self, conn, *, title, description, severity, tenant_key, user_id, now, template_code=None
    ) -> str:
        """Create a critical broadcast for a new incident."""
        _broadcast_repo_module = import_module("backend.04_notifications.06_broadcasts.repository")
        broadcast_repo = _broadcast_repo_module.BroadcastRepository()

        broadcast_id = str(uuid.uuid4())
        is_critical = severity in ("critical", "major")
        priority = "critical" if severity == "critical" else "high"

        await broadcast_repo.create_broadcast(
            conn,
            broadcast_id=broadcast_id,
            tenant_key=tenant_key,
            title=f"[{severity.upper()}] Incident: {title}",
            body_text=description,
            body_html=None,
            scope="global",
            scope_org_id=None,
            scope_workspace_id=None,
            notification_type_code=NotificationType.PLATFORM_INCIDENT,
            priority_code=priority,
            severity=severity,
            is_critical=is_critical,
            template_code=template_code,
            scheduled_at=None,
            created_by=user_id,
            now=now,
        )
        return broadcast_id

    async def _create_incident_update_broadcast(
        self, conn, *, incident, status, message, tenant_key, user_id, now
    ) -> str:
        """Create a broadcast for an incident status update."""
        _broadcast_repo_module = import_module("backend.04_notifications.06_broadcasts.repository")
        broadcast_repo = _broadcast_repo_module.BroadcastRepository()

        broadcast_id = str(uuid.uuid4())
        is_resolved = status == IncidentStatus.RESOLVED

        await broadcast_repo.create_broadcast(
            conn,
            broadcast_id=broadcast_id,
            tenant_key=tenant_key,
            title=f"Incident Update [{status.upper()}]: {incident.title}",
            body_text=message,
            body_html=None,
            scope="global",
            scope_org_id=None,
            scope_workspace_id=None,
            notification_type_code=NotificationType.PLATFORM_INCIDENT,
            priority_code="normal" if is_resolved else "high",
            severity=incident.severity,
            is_critical=False,
            template_code=None,
            scheduled_at=None,
            created_by=user_id,
            now=now,
        )
        return broadcast_id

    # ------------------------------------------------------------------ #
    # Public read-only methods — JWT auth only, no platform permission
    # ------------------------------------------------------------------ #

    async def list_published_releases(
        self, *, tenant_key: str, limit: int = 50, offset: int = 0
    ) -> ReleaseListResponse:
        """List published releases — no platform permission required."""
        async with self._database_pool.acquire() as conn:
            records, total = await self._repository.list_releases(
                conn, tenant_key, limit=limit, offset=offset, status="published"
            )
        return ReleaseListResponse(items=[_release_response(r) for r in records], total=total)

    async def list_active_incidents(
        self, *, tenant_key: str, limit: int = 50, offset: int = 0
    ) -> IncidentListResponse:
        """List non-resolved incidents — no platform permission required."""
        async with self._database_pool.acquire() as conn:
            # Fetch investigating + identified + monitoring statuses (i.e. not resolved)
            records, total = await self._repository.list_active_incidents(
                conn, tenant_key, limit=limit, offset=offset
            )
        result = []
        async with self._database_pool.acquire() as conn:
            for r in records:
                updates = await self._repository.list_incident_updates(conn, r.id)
                resp = _incident_response(r)
                resp.updates = [_incident_update_response(u) for u in updates]
                result.append(resp)
        return IncidentListResponse(items=result, total=total)


def _release_response(r) -> ReleaseResponse:
    return ReleaseResponse(
        id=r.id,
        tenant_key=r.tenant_key,
        version=r.version,
        title=r.title,
        summary=r.summary,
        body_markdown=r.body_markdown,
        body_html=r.body_html,
        changelog_url=r.changelog_url,
        status=r.status,
        release_date=r.release_date,
        published_at=r.published_at,
        broadcast_id=r.broadcast_id,
        is_active=r.is_active,
        created_at=r.created_at,
        updated_at=r.updated_at,
        created_by=r.created_by,
    )


def _incident_response(r) -> IncidentResponse:
    return IncidentResponse(
        id=r.id,
        tenant_key=r.tenant_key,
        title=r.title,
        description=r.description,
        severity=r.severity,
        status=r.status,
        affected_components=r.affected_components,
        started_at=r.started_at,
        resolved_at=r.resolved_at,
        broadcast_id=r.broadcast_id,
        is_active=r.is_active,
        created_at=r.created_at,
        updated_at=r.updated_at,
        created_by=r.created_by,
    )


def _incident_update_response(r) -> IncidentUpdateResponse:
    return IncidentUpdateResponse(
        id=r.id,
        incident_id=r.incident_id,
        status=r.status,
        message=r.message,
        is_public=r.is_public,
        broadcast_id=r.broadcast_id,
        created_at=r.created_at,
        created_by=r.created_by,
    )
