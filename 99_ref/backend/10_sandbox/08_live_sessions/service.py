from __future__ import annotations

import uuid
from datetime import timedelta
from importlib import import_module

from .repository import LiveSessionRepository
from .schemas import (
    AttachSignalRequest,
    AttachThreatRequest,
    LiveSessionListResponse,
    LiveSessionResponse,
    LiveSessionSignalResponse,
    LiveSessionThreatResponse,
    SaveDatasetRequest,
    SaveDatasetResponse,
    StartSessionRequest,
    StreamResponse,
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
_constants_module = import_module("backend.10_sandbox.constants")

Settings = _settings_module.Settings
DatabasePool = _database_module.DatabasePool
CacheManager = _cache_module.CacheManager
NullCacheManager = _cache_module.NullCacheManager
get_logger = _logging_module.get_logger
instrument_class_methods = _telemetry_module.instrument_class_methods
NotFoundError = _errors_module.NotFoundError
ConflictError = _errors_module.ConflictError
ValidationError = _errors_module.ValidationError
AuditEntry = _audit_module.AuditEntry
AuditWriter = _audit_module.AuditWriter
SandboxAuditEventType = _constants_module.SandboxAuditEventType
require_permission = _perm_check_module.require_permission
utc_now_sql = _time_module.utc_now_sql

_CACHE_KEY_PREFIX = "sb:live_sessions"
_CACHE_TTL = 30  # 30-second TTL for live session lists
_MAX_ACTIVE_SESSIONS_PER_WORKSPACE = 5


@instrument_class_methods(
    namespace="sandbox.live_sessions.service",
    logger_name="backend.sandbox.live_sessions.instrumentation",
)
class LiveSessionService:
    def __init__(self, *, settings, database_pool, cache) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._cache = cache
        self._repository = LiveSessionRepository()
        self._audit_writer = AuditWriter(schema_name="03_auth_manage")
        self._logger = get_logger("backend.sandbox.live_sessions")

    async def _require_sandbox_permission(
        self,
        conn,
        *,
        user_id: str,
        permission_code: str,
        org_id: str,
    ) -> None:
        await require_permission(
            conn,
            user_id,
            permission_code,
            scope_org_id=org_id,
        )

    async def start_session(
        self,
        *,
        user_id: str,
        tenant_key: str,
        org_id: str,
        request: StartSessionRequest,
    ) -> LiveSessionResponse:
        now = utc_now_sql()
        session_id = str(uuid.uuid4())

        async with self._database_pool.transaction() as conn:
            await self._require_sandbox_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.create",
                org_id=org_id,
            )

            # 1. Check workspace session limit
            active_count = await self._repository.count_active_sessions(
                conn,
                request.workspace_id,
            )
            if active_count >= _MAX_ACTIVE_SESSIONS_PER_WORKSPACE:
                raise ConflictError(
                    f"Workspace already has {active_count} active sessions "
                    f"(max {_MAX_ACTIVE_SESSIONS_PER_WORKSPACE})"
                )

            # 2. Validate connector_instance_id exists
            # Import connector repo to check existence
            _connector_repo_module = import_module(
                "backend.10_sandbox.02_connectors.repository"
            )
            connector_repo = _connector_repo_module.ConnectorRepository()
            connector = await connector_repo.get_connector_by_id(
                conn,
                request.connector_instance_id,
            )
            if connector is None:
                raise NotFoundError(
                    f"Connector instance '{request.connector_instance_id}' not found"
                )
            if connector.org_id != org_id:
                raise NotFoundError(
                    f"Connector '{request.connector_instance_id}' not found in this org"
                )

            # 3. Create session record (status='starting')
            await self._repository.create_session(
                conn,
                id=session_id,
                tenant_key=tenant_key,
                org_id=org_id,
                workspace_id=request.workspace_id,
                connector_instance_id=request.connector_instance_id,
                session_status="starting",
                duration_minutes=request.duration_minutes,
                created_by=user_id,
                now=now,
            )

            # 4. Attach initial signals and threats
            for signal_id in request.signal_ids:
                await self._repository.attach_signal(
                    conn,
                    live_session_id=session_id,
                    signal_id=signal_id,
                    created_by=user_id,
                    now=now,
                )
            for threat_type_id in request.threat_type_ids:
                await self._repository.attach_threat_type(
                    conn,
                    live_session_id=session_id,
                    threat_type_id=threat_type_id,
                    created_by=user_id,
                    now=now,
                )

            # 5. Update status to 'active', set started_at + expires_at
            await self._repository.update_session_status(
                conn,
                session_id,
                "active",
                now=now,
            )
            expires_at = now + timedelta(minutes=request.duration_minutes)
            await self._repository.set_expires_at(
                conn,
                session_id,
                expires_at,
                now=now,
            )

            # 6. Audit
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="live_session",
                    entity_id=session_id,
                    event_type=SandboxAuditEventType.LIVE_SESSION_STARTED.value,
                    event_category="sandbox",
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={
                        "connector_instance_id": request.connector_instance_id,
                        "workspace_id": request.workspace_id,
                        "duration_minutes": str(request.duration_minutes),
                        "signal_count": str(len(request.signal_ids)),
                        "threat_count": str(len(request.threat_type_ids)),
                    },
                ),
            )

        # NOTE: Actual data streaming is handled by a separate async task manager (stub for now)

        await self._cache.delete(f"{_CACHE_KEY_PREFIX}:{org_id}")

        # 7. Return session
        return await self._get_session_with_attachments(session_id)

    async def get_session(
        self, *, user_id: str, session_id: str
    ) -> LiveSessionResponse:
        async with self._database_pool.acquire() as conn:
            record = await self._repository.get_session_by_id(conn, session_id)
            if record is None:
                raise NotFoundError(f"Live session '{session_id}' not found")
            await self._require_sandbox_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.view",
                org_id=record.org_id,
            )
        return await self._get_session_with_attachments(session_id)

    async def list_sessions(
        self,
        *,
        user_id: str,
        tenant_key: str,
        org_id: str,
        workspace_id: str | None = None,
        session_status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> LiveSessionListResponse:
        cache_key = f"{_CACHE_KEY_PREFIX}:{org_id}"
        # Only use cache for unfiltered first-page requests
        if not any([workspace_id, session_status]) and offset == 0 and limit == 100:
            cached = await self._cache.get_json(cache_key)
            if cached is not None:
                return LiveSessionListResponse(**cached)

        async with self._database_pool.acquire() as conn:
            await self._require_sandbox_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.view",
                org_id=org_id,
            )
            records = await self._repository.list_sessions(
                conn,
                org_id,
                workspace_id=workspace_id,
                session_status=session_status,
                limit=limit,
                offset=offset,
            )
            total = await self._repository.count_sessions(
                conn,
                org_id,
                workspace_id=workspace_id,
                session_status=session_status,
            )

        items = [_session_response(r) for r in records]
        result = LiveSessionListResponse(items=items, total=total)

        if not any([workspace_id, session_status]) and offset == 0 and limit == 100:
            await self._cache.set_json(
                cache_key, result.model_dump(), ttl_seconds=_CACHE_TTL
            )

        return result

    async def pause_session(
        self, *, user_id: str, tenant_key: str, org_id: str, session_id: str
    ) -> LiveSessionResponse:
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            record = await self._repository.get_session_by_id(conn, session_id)
            if record is None:
                raise NotFoundError(f"Live session '{session_id}' not found")
            await self._require_sandbox_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.update",
                org_id=record.org_id,
            )
            if record.session_status != "active":
                raise ValidationError(
                    f"Cannot pause session with status '{record.session_status}' — must be 'active'"
                )
            await self._repository.update_session_status(
                conn,
                session_id,
                "paused",
                now=now,
            )
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="live_session",
                    entity_id=session_id,
                    event_type=SandboxAuditEventType.LIVE_SESSION_PAUSED.value,
                    event_category="sandbox",
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={},
                ),
            )

        await self._cache.delete(f"{_CACHE_KEY_PREFIX}:{org_id}")
        return await self._get_session_with_attachments(session_id)

    async def resume_session(
        self, *, user_id: str, tenant_key: str, org_id: str, session_id: str
    ) -> LiveSessionResponse:
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            record = await self._repository.get_session_by_id(conn, session_id)
            if record is None:
                raise NotFoundError(f"Live session '{session_id}' not found")
            await self._require_sandbox_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.update",
                org_id=record.org_id,
            )
            if record.session_status != "paused":
                raise ValidationError(
                    f"Cannot resume session with status '{record.session_status}' — must be 'paused'"
                )
            await self._repository.update_session_status(
                conn,
                session_id,
                "active",
                now=now,
            )
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="live_session",
                    entity_id=session_id,
                    event_type=SandboxAuditEventType.LIVE_SESSION_RESUMED.value,
                    event_category="sandbox",
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={},
                ),
            )

        await self._cache.delete(f"{_CACHE_KEY_PREFIX}:{org_id}")
        return await self._get_session_with_attachments(session_id)

    async def stop_session(
        self, *, user_id: str, tenant_key: str, org_id: str, session_id: str
    ) -> LiveSessionResponse:
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            record = await self._repository.get_session_by_id(conn, session_id)
            if record is None:
                raise NotFoundError(f"Live session '{session_id}' not found")
            await self._require_sandbox_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.update",
                org_id=record.org_id,
            )
            await self._repository.update_session_status(
                conn,
                session_id,
                "completed",
                now=now,
            )
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="live_session",
                    entity_id=session_id,
                    event_type=SandboxAuditEventType.LIVE_SESSION_STOPPED.value,
                    event_category="sandbox",
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={},
                ),
            )

        await self._cache.delete(f"{_CACHE_KEY_PREFIX}:{org_id}")
        return await self._get_session_with_attachments(session_id)

    async def attach_signal(
        self,
        *,
        user_id: str,
        tenant_key: str,
        org_id: str,
        session_id: str,
        request: AttachSignalRequest,
    ) -> LiveSessionResponse:
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            record = await self._repository.get_session_by_id(conn, session_id)
            if record is None:
                raise NotFoundError(f"Live session '{session_id}' not found")
            await self._require_sandbox_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.update",
                org_id=record.org_id,
            )
            await self._repository.attach_signal(
                conn,
                live_session_id=session_id,
                signal_id=request.signal_id,
                created_by=user_id,
                now=now,
            )

        await self._cache.delete(f"{_CACHE_KEY_PREFIX}:{org_id}")
        return await self._get_session_with_attachments(session_id)

    async def detach_signal(
        self,
        *,
        user_id: str,
        tenant_key: str,
        org_id: str,
        session_id: str,
        request: AttachSignalRequest,
    ) -> LiveSessionResponse:
        async with self._database_pool.transaction() as conn:
            record = await self._repository.get_session_by_id(conn, session_id)
            if record is None:
                raise NotFoundError(f"Live session '{session_id}' not found")
            await self._require_sandbox_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.update",
                org_id=record.org_id,
            )
            removed = await self._repository.detach_signal(
                conn,
                session_id,
                request.signal_id,
            )
            if not removed:
                raise NotFoundError(
                    f"Signal '{request.signal_id}' not attached to session '{session_id}'"
                )

        await self._cache.delete(f"{_CACHE_KEY_PREFIX}:{org_id}")
        return await self._get_session_with_attachments(session_id)

    async def attach_threat(
        self,
        *,
        user_id: str,
        tenant_key: str,
        org_id: str,
        session_id: str,
        request: AttachThreatRequest,
    ) -> LiveSessionResponse:
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            record = await self._repository.get_session_by_id(conn, session_id)
            if record is None:
                raise NotFoundError(f"Live session '{session_id}' not found")
            await self._require_sandbox_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.update",
                org_id=record.org_id,
            )
            await self._repository.attach_threat_type(
                conn,
                live_session_id=session_id,
                threat_type_id=request.threat_type_id,
                created_by=user_id,
                now=now,
            )

        await self._cache.delete(f"{_CACHE_KEY_PREFIX}:{org_id}")
        return await self._get_session_with_attachments(session_id)

    async def detach_threat(
        self,
        *,
        user_id: str,
        tenant_key: str,
        org_id: str,
        session_id: str,
        request: AttachThreatRequest,
    ) -> LiveSessionResponse:
        async with self._database_pool.transaction() as conn:
            record = await self._repository.get_session_by_id(conn, session_id)
            if record is None:
                raise NotFoundError(f"Live session '{session_id}' not found")
            await self._require_sandbox_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.update",
                org_id=record.org_id,
            )
            removed = await self._repository.detach_threat_type(
                conn,
                session_id,
                request.threat_type_id,
            )
            if not removed:
                raise NotFoundError(
                    f"Threat type '{request.threat_type_id}' not attached to session '{session_id}'"
                )

        await self._cache.delete(f"{_CACHE_KEY_PREFIX}:{org_id}")
        return await self._get_session_with_attachments(session_id)

    async def get_stream(
        self,
        *,
        user_id: str,
        session_id: str,
        after_sequence: int = 0,
        limit: int = 100,
    ) -> StreamResponse:
        """Query ClickHouse for latest events.

        Stub implementation -- returns empty for now. Will use ClickHouseClient
        when the streaming infrastructure is wired.
        """
        async with self._database_pool.acquire() as conn:
            record = await self._repository.get_session_by_id(conn, session_id)
            if record is None:
                raise NotFoundError(f"Live session '{session_id}' not found")
            await self._require_sandbox_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.view",
                org_id=record.org_id,
            )

        # Stub: real implementation will query ClickHouse
        return StreamResponse(events=[], has_more=False, next_cursor=after_sequence)

    async def save_dataset(
        self,
        *,
        user_id: str,
        tenant_key: str,
        org_id: str,
        session_id: str,
        request: SaveDatasetRequest,
    ) -> SaveDatasetResponse:
        """Save the session's captured data as a new dataset.

        Stub implementation -- the ClickHouse query and dataset creation
        will be wired when the data pipeline is ready.
        """
        now = utc_now_sql()

        async with self._database_pool.transaction() as conn:
            record = await self._repository.get_session_by_id(conn, session_id)
            if record is None:
                raise NotFoundError(f"Live session '{session_id}' not found")
            await self._require_sandbox_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.create",
                org_id=record.org_id,
            )

            # Stub: In production this will:
            # 1. Query ClickHouse for session data
            # 2. Create a new dataset with source_code='live_capture'
            # 3. Store the payload
            dataset_id = str(uuid.uuid4())

        return SaveDatasetResponse(
            dataset_id=dataset_id,
            dataset_code=request.dataset_code,
            version_number=1,
            created_at=str(now),
        )

    # --- Internal helpers ---

    async def _get_session_with_attachments(
        self, session_id: str
    ) -> LiveSessionResponse:
        async with self._database_pool.acquire() as conn:
            record = await self._repository.get_session_by_id(conn, session_id)
            if record is None:
                raise NotFoundError(f"Live session '{session_id}' not found")
            signals = await self._repository.list_attached_signals(conn, session_id)
            threats = await self._repository.list_attached_threats(conn, session_id)

        resp = _session_response(record)
        resp.attached_signals = [
            LiveSessionSignalResponse(
                id=s.id,
                live_session_id=s.live_session_id,
                signal_id=s.signal_id,
                signal_code=s.signal_code,
                signal_name=s.signal_name,
            )
            for s in signals
        ]
        resp.attached_threats = [
            LiveSessionThreatResponse(
                id=t.id,
                live_session_id=t.live_session_id,
                threat_type_id=t.threat_type_id,
                threat_code=t.threat_code,
                threat_name=t.threat_name,
            )
            for t in threats
        ]
        return resp


def _session_response(r) -> LiveSessionResponse:
    return LiveSessionResponse(
        id=r.id,
        tenant_key=r.tenant_key,
        org_id=r.org_id,
        workspace_id=r.workspace_id,
        connector_instance_id=r.connector_instance_id,
        session_status=r.session_status,
        duration_minutes=r.duration_minutes,
        started_at=r.started_at,
        expires_at=r.expires_at,
        paused_at=r.paused_at,
        completed_at=r.completed_at,
        data_points_received=r.data_points_received,
        bytes_received=r.bytes_received,
        signals_executed=r.signals_executed,
        threats_evaluated=r.threats_evaluated,
        created_at=r.created_at,
        created_by=r.created_by,
    )
