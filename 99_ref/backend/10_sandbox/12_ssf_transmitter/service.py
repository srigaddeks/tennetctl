from __future__ import annotations

import json
import uuid
from importlib import import_module

from .event_mapper import resolve_event_uri
from .push_delivery import push_set
from .repository import SSFTransmitterRepository
from .schemas import (
    AddSubjectRequest,
    CreateStreamRequest,
    PollResponse,
    StreamListResponse,
    StreamResponse,
    SubjectResponse,
    UpdateStreamRequest,
    UpdateStreamStatusRequest,
    VerifyResponse,
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

_CACHE_KEY_PREFIX = "sb:ssf_streams"
_CACHE_TTL = 300


@instrument_class_methods(namespace="sandbox.ssf_transmitter.service", logger_name="backend.sandbox.ssf_transmitter.instrumentation")
class SSFTransmitterService:
    def __init__(self, *, settings, database_pool, cache) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._cache = cache
        self._repository = SSFTransmitterRepository()
        self._audit_writer = AuditWriter(schema_name="03_auth_manage")
        self._logger = get_logger("backend.sandbox.ssf_transmitter")

    async def _require_stream_permission(
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

    # ── Stream CRUD ──────────────────────────────────────────────────────

    async def create_stream(
        self,
        *,
        user_id: str,
        tenant_key: str,
        org_id: str,
        request: CreateStreamRequest,
    ) -> StreamResponse:
        if request.delivery_method == "push" and not request.receiver_url:
            raise ValidationError("receiver_url is required for push delivery")

        now = utc_now_sql()
        stream_id = str(uuid.uuid4())

        async with self._database_pool.transaction() as conn:
            await self._require_stream_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.create",
                org_id=org_id,
            )
            await self._repository.create_stream(
                conn,
                id=stream_id,
                tenant_key=tenant_key,
                org_id=org_id,
                stream_description=request.description,
                receiver_url=request.receiver_url,
                delivery_method=request.delivery_method,
                events_requested=request.events_requested,
                authorization_header=request.authorization_header,
                created_by=user_id,
                now=now,
            )
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="ssf_stream",
                    entity_id=stream_id,
                    event_type=SandboxAuditEventType.SSF_STREAM_CREATED.value,
                    event_category="sandbox",
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={
                        "delivery_method": request.delivery_method,
                        "events_requested_count": str(len(request.events_requested)),
                    },
                ),
            )

        await self._cache.delete(f"{_CACHE_KEY_PREFIX}:{org_id}")

        async with self._database_pool.acquire() as conn:
            record = await self._repository.get_stream(conn, stream_id)
        return _stream_response(record)

    async def list_streams(
        self,
        *,
        user_id: str,
        tenant_key: str,
        org_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> StreamListResponse:
        cache_key = f"{_CACHE_KEY_PREFIX}:{org_id}"
        if offset == 0 and limit == 100:
            cached = await self._cache.get_json(cache_key)
            if cached is not None:
                return StreamListResponse(**cached)

        async with self._database_pool.acquire() as conn:
            await self._require_stream_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.view",
                org_id=org_id,
            )
            records = await self._repository.list_streams(
                conn, org_id, limit=limit, offset=offset,
            )
            total = await self._repository.count_streams(conn, org_id)

        items = [_stream_response(r) for r in records]
        result = StreamListResponse(items=items, total=total)

        if offset == 0 and limit == 100:
            await self._cache.set_json(cache_key, result.model_dump(), ttl_seconds=_CACHE_TTL)

        return result

    async def get_stream(
        self, *, user_id: str, stream_id: str
    ) -> StreamResponse:
        async with self._database_pool.acquire() as conn:
            record = await self._repository.get_stream(conn, stream_id)
            if record is None:
                raise NotFoundError(f"SSF stream '{stream_id}' not found")
            await self._require_stream_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.view",
                org_id=record.org_id,
            )
        return _stream_response(record)

    async def update_stream(
        self,
        *,
        user_id: str,
        tenant_key: str,
        org_id: str,
        stream_id: str,
        request: UpdateStreamRequest,
    ) -> StreamResponse:
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            stream = await self._repository.get_stream(conn, stream_id)
            if stream is None:
                raise NotFoundError(f"SSF stream '{stream_id}' not found")
            await self._require_stream_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.update",
                org_id=stream.org_id,
            )
            updated = await self._repository.update_stream(
                conn,
                stream_id,
                events_requested=request.events_requested,
                receiver_url=request.receiver_url,
                stream_description=request.description,
                updated_by=user_id,
                now=now,
            )
            if not updated:
                raise NotFoundError(f"SSF stream '{stream_id}' not found")
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="ssf_stream",
                    entity_id=stream_id,
                    event_type=SandboxAuditEventType.SSF_STREAM_UPDATED.value,
                    event_category="sandbox",
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={},
                ),
            )

        await self._cache.delete(f"{_CACHE_KEY_PREFIX}:{org_id}")

        async with self._database_pool.acquire() as conn:
            record = await self._repository.get_stream(conn, stream_id)
        return _stream_response(record)

    async def delete_stream(
        self, *, user_id: str, tenant_key: str, org_id: str, stream_id: str
    ) -> None:
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            stream = await self._repository.get_stream(conn, stream_id)
            if stream is None:
                raise NotFoundError(f"SSF stream '{stream_id}' not found")
            await self._require_stream_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.delete",
                org_id=stream.org_id,
            )
            deleted = await self._repository.delete_stream(conn, stream_id)
            if not deleted:
                raise NotFoundError(f"SSF stream '{stream_id}' not found")
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="ssf_stream",
                    entity_id=stream_id,
                    event_type=SandboxAuditEventType.SSF_STREAM_DELETED.value,
                    event_category="sandbox",
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={},
                ),
            )

        await self._cache.delete(f"{_CACHE_KEY_PREFIX}:{org_id}")

    # ── Stream status ────────────────────────────────────────────────────

    async def get_stream_status(
        self, *, user_id: str, stream_id: str
    ) -> dict:
        async with self._database_pool.acquire() as conn:
            record = await self._repository.get_stream(conn, stream_id)
            if record is None:
                raise NotFoundError(f"SSF stream '{stream_id}' not found")
            await self._require_stream_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.view",
                org_id=record.org_id,
            )
        return {"stream_id": record.id, "stream_status": record.stream_status, "is_active": record.is_active}

    async def update_stream_status(
        self,
        *,
        user_id: str,
        tenant_key: str,
        org_id: str,
        stream_id: str,
        request: UpdateStreamStatusRequest,
    ) -> dict:
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            stream = await self._repository.get_stream(conn, stream_id)
            if stream is None:
                raise NotFoundError(f"SSF stream '{stream_id}' not found")
            await self._require_stream_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.update",
                org_id=stream.org_id,
            )
            updated = await self._repository.update_stream_status(
                conn, stream_id, request.stream_status,
                updated_by=user_id, now=now,
            )
            if not updated:
                raise NotFoundError(f"SSF stream '{stream_id}' not found")
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="ssf_stream",
                    entity_id=stream_id,
                    event_type=SandboxAuditEventType.SSF_STREAM_STATUS_CHANGED.value,
                    event_category="sandbox",
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={"stream_status": request.stream_status},
                ),
            )

        await self._cache.delete(f"{_CACHE_KEY_PREFIX}:{org_id}")

        return {"stream_id": stream_id, "stream_status": request.stream_status, "is_active": request.stream_status == "enabled"}

    # ── Subjects ─────────────────────────────────────────────────────────

    async def add_subject(
        self,
        *,
        user_id: str,
        tenant_key: str,
        stream_id: str,
        request: AddSubjectRequest,
    ) -> SubjectResponse:
        now = utc_now_sql()
        subject_id = str(uuid.uuid4())
        async with self._database_pool.transaction() as conn:
            # Verify stream exists
            stream = await self._repository.get_stream(conn, stream_id)
            if stream is None:
                raise NotFoundError(f"SSF stream '{stream_id}' not found")
            await self._require_stream_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.create",
                org_id=stream.org_id,
            )
            await self._repository.add_subject(
                conn,
                id=subject_id,
                stream_id=stream_id,
                subject_type=request.subject_type,
                subject_format=request.subject_format,
                subject_id_data=request.subject_id_data,
                created_by=user_id,
                now=now,
            )
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="ssf_stream_subject",
                    entity_id=subject_id,
                    event_type=SandboxAuditEventType.SSF_SUBJECT_ADDED.value,
                    event_category="sandbox",
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={"stream_id": stream_id, "subject_type": request.subject_type},
                ),
            )

        async with self._database_pool.acquire() as conn:
            subjects = await self._repository.list_subjects(conn, stream_id)
        for s in subjects:
            if s.id == subject_id:
                return _subject_response(s)
        # Fallback — should not happen
        return SubjectResponse(
            id=subject_id,
            stream_id=stream_id,
            subject_type=request.subject_type,
            subject_format=request.subject_format,
            subject_id_data=request.subject_id_data,
            created_at=str(now),
        )

    async def remove_subject(
        self,
        *,
        user_id: str,
        tenant_key: str,
        stream_id: str,
        subject_id: str,
    ) -> None:
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            stream = await self._repository.get_stream(conn, stream_id)
            if stream is None:
                raise NotFoundError(f"SSF stream '{stream_id}' not found")
            await self._require_stream_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.delete",
                org_id=stream.org_id,
            )
            removed = await self._repository.remove_subject(conn, stream_id, subject_id)
            if not removed:
                raise NotFoundError(f"Subject '{subject_id}' not found on stream '{stream_id}'")
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="ssf_stream_subject",
                    entity_id=subject_id,
                    event_type=SandboxAuditEventType.SSF_SUBJECT_REMOVED.value,
                    event_category="sandbox",
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={"stream_id": stream_id},
                ),
            )

    # ── SET emission ─────────────────────────────────────────────────────

    async def emit_set(
        self,
        *,
        org_id: str,
        tenant_key: str,
        signal_code: str,
        signal_properties: dict,
        result: dict | None = None,
        subject_context: dict | None = None,
        caep_event_type: str | None = None,
        risc_event_type: str | None = None,
    ) -> list[str]:
        """Emit a SET to all active streams for the given org that subscribe to this event.

        Returns list of JTIs for emitted SETs.
        """
        from .set_builder import SETBuilder

        event_uri = resolve_event_uri(
            caep_event_type=caep_event_type,
            risc_event_type=risc_event_type,
            signal_code=signal_code,
        )

        now = utc_now_sql()
        jtis: list[str] = []

        async with self._database_pool.acquire() as conn:
            streams = await self._repository.find_active_streams_for_event(
                conn, org_id, event_uri,
            )

        if not streams:
            return jtis

        # Build SET builder — use settings for issuer/key config
        issuer = getattr(self._settings, "ssf_issuer", "https://kcontrol.io")
        signing_key = getattr(self._settings, "ssf_signing_key", "")
        key_id = getattr(self._settings, "ssf_key_id", "ssf-default")
        algorithm = getattr(self._settings, "ssf_algorithm", "RS256")

        if not signing_key:
            self._logger.warning("SSF signing key not configured — skipping SET emission")
            return jtis

        builder = SETBuilder(
            issuer=issuer,
            signing_key=signing_key,
            key_id=key_id,
            algorithm=algorithm,
        )

        event_claims = {**signal_properties}
        if result:
            event_claims["result"] = result

        subject_id = subject_context or {"format": "opaque", "id": org_id}

        for stream in streams:
            audience = stream.receiver_url or stream.id
            set_jwt, jti = builder.build_set(
                audience=audience,
                subject_id=subject_id,
                event_uri=event_uri,
                event_claims=event_claims,
            )
            jtis.append(jti)

            if stream.delivery_method == "push" and stream.receiver_url:
                # Push delivery
                async with self._database_pool.acquire() as conn:
                    auth_header = await self._repository.get_stream_authorization_header(
                        conn, stream.id,
                    )
                http_status, error_msg = await push_set(
                    receiver_url=stream.receiver_url,
                    set_jwt=set_jwt,
                    authorization_header=auth_header,
                )
                async with self._database_pool.transaction() as conn:
                    await self._repository.insert_delivery_log(
                        conn,
                        id=str(uuid.uuid4()),
                        stream_id=stream.id,
                        jti=jti,
                        delivery_method="push",
                        http_status=http_status,
                        error_message=error_msg,
                        now=now,
                    )
                    if http_status and 200 <= http_status < 300:
                        await self._repository.increment_events_delivered(conn, stream.id)
            else:
                # Poll delivery — enqueue in outbox
                async with self._database_pool.transaction() as conn:
                    await self._repository.enqueue_set(
                        conn,
                        id=str(uuid.uuid4()),
                        stream_id=stream.id,
                        set_jwt=set_jwt,
                        jti=jti,
                        now=now,
                    )
                    await self._repository.increment_events_delivered(conn, stream.id)

        return jtis

    # ── Poll ─────────────────────────────────────────────────────────────

    async def poll_sets(
        self,
        *,
        user_id: str,
        stream_id: str,
        acks: list[str] | None = None,
        limit: int = 25,
    ) -> PollResponse:
        async with self._database_pool.transaction() as conn:
            stream = await self._repository.get_stream(conn, stream_id)
            if stream is None:
                raise NotFoundError(f"SSF stream '{stream_id}' not found")
            await self._require_stream_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.view",
                org_id=stream.org_id,
            )
            # Acknowledge any provided jtis first
            if acks:
                now = utc_now_sql()
                await self._repository.acknowledge_sets(conn, stream_id, acks, now=now)
            # Fetch pending SETs
            records = await self._repository.poll_sets(conn, stream_id, limit=limit)
            total_pending = await self._repository.count_pending_sets(conn, stream_id)

        sets = [{"jti": r.jti, "set_jwt": r.set_jwt} for r in records]
        more_available = total_pending > len(records)

        return PollResponse(sets=sets, more_available=more_available)

    # ── Verify ───────────────────────────────────────────────────────────

    async def verify_stream(
        self,
        *,
        user_id: str,
        tenant_key: str,
        stream_id: str,
    ) -> VerifyResponse:
        """Send a test SET to verify stream connectivity."""
        from .set_builder import SETBuilder

        now = utc_now_sql()

        async with self._database_pool.acquire() as conn:
            stream = await self._repository.get_stream(conn, stream_id)
            if stream is None:
                raise NotFoundError(f"SSF stream '{stream_id}' not found")
            await self._require_stream_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.update",
                org_id=stream.org_id,
            )

        issuer = getattr(self._settings, "ssf_issuer", "https://kcontrol.io")
        signing_key = getattr(self._settings, "ssf_signing_key", "")
        key_id = getattr(self._settings, "ssf_key_id", "ssf-default")
        algorithm = getattr(self._settings, "ssf_algorithm", "RS256")

        if not signing_key:
            raise ValidationError("SSF signing key not configured — cannot verify stream")

        builder = SETBuilder(
            issuer=issuer,
            signing_key=signing_key,
            key_id=key_id,
            algorithm=algorithm,
        )

        event_uri = "https://schemas.kcontrol.io/secevent/sandbox/event-type/stream-verification"
        audience = stream.receiver_url or stream.id
        set_jwt, jti = builder.build_set(
            audience=audience,
            subject_id={"format": "opaque", "id": stream.id},
            event_uri=event_uri,
            event_claims={"state": "verification"},
        )

        delivered = False
        if stream.delivery_method == "push" and stream.receiver_url:
            async with self._database_pool.acquire() as conn:
                auth_header = await self._repository.get_stream_authorization_header(
                    conn, stream.id,
                )
            http_status, error_msg = await push_set(
                receiver_url=stream.receiver_url,
                set_jwt=set_jwt,
                authorization_header=auth_header,
            )
            delivered = bool(http_status and 200 <= http_status < 300)
            async with self._database_pool.transaction() as conn:
                await self._repository.insert_delivery_log(
                    conn,
                    id=str(uuid.uuid4()),
                    stream_id=stream.id,
                    jti=jti,
                    delivery_method="push",
                    http_status=http_status,
                    error_message=error_msg,
                    now=now,
                )
        else:
            # For poll streams, enqueue and consider it "delivered"
            async with self._database_pool.transaction() as conn:
                await self._repository.enqueue_set(
                    conn,
                    id=str(uuid.uuid4()),
                    stream_id=stream.id,
                    set_jwt=set_jwt,
                    jti=jti,
                    now=now,
                )
            delivered = True

        async with self._database_pool.transaction() as conn:
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="ssf_stream",
                    entity_id=stream_id,
                    event_type=SandboxAuditEventType.SSF_STREAM_VERIFIED.value,
                    event_category="sandbox",
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={"jti": jti, "delivered": str(delivered)},
                ),
            )

        return VerifyResponse(jti=jti, delivered=delivered)


# ── Helpers ──────────────────────────────────────────────────────────────

def _stream_response(r) -> StreamResponse:
    events = r.events_requested
    if isinstance(events, str):
        try:
            events = json.loads(events)
        except json.JSONDecodeError:
            events = []
    return StreamResponse(
        id=r.id,
        tenant_key=r.tenant_key,
        org_id=r.org_id,
        stream_description=r.stream_description,
        receiver_url=r.receiver_url,
        delivery_method=r.delivery_method,
        events_requested=events,
        events_delivered=r.events_delivered,
        stream_status=r.stream_status,
        is_active=r.is_active,
        created_at=r.created_at,
        updated_at=r.updated_at,
    )


def _subject_response(r) -> SubjectResponse:
    data = r.subject_id_data
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            data = {}
    return SubjectResponse(
        id=r.id,
        stream_id=r.stream_id,
        subject_type=r.subject_type,
        subject_format=r.subject_format,
        subject_id_data=data,
        created_at=r.created_at,
    )
