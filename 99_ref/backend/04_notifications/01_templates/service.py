import uuid
import json as _json
from importlib import import_module

import asyncpg

from .repository import TemplateRepository
from .schemas import (
    CreateTemplateRequest,
    CreateTemplateVersionRequest,
    PreviewTemplateResponse,
    TemplateDetailResponse,
    TemplateListResponse,
    TemplateResponse,
    TemplateVersionResponse,
    UpdateTemplateRequest,
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

Settings = _settings_module.Settings
DatabasePool = _database_module.DatabasePool
CacheManager = _cache_module.CacheManager
NullCacheManager = _cache_module.NullCacheManager
get_logger = _logging_module.get_logger
instrument_class_methods = _telemetry_module.instrument_class_methods
ConflictError = _errors_module.ConflictError
NotFoundError = _errors_module.NotFoundError
ValidationError = _errors_module.ValidationError
AuditEntry = _audit_module.AuditEntry
AuditWriter = _audit_module.AuditWriter
require_permission = _perm_check_module.require_permission
utc_now_sql = _time_module.utc_now_sql

_CACHE_KEY_TEMPLATES = "notif:templates:{tenant}"
_CACHE_TTL_TEMPLATES = 300  # 5 minutes


@instrument_class_methods(namespace="notification_templates.service", logger_name="backend.notification_templates.instrumentation")
class TemplateService:
    def __init__(self, *, settings: Settings, database_pool: DatabasePool, cache: CacheManager | NullCacheManager) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._cache = cache
        self._repository = TemplateRepository()
        self._audit_writer = AuditWriter(schema_name="03_auth_manage")
        self._logger = get_logger("backend.notification_templates")

    async def list_templates(
        self, *, user_id: str, tenant_key: str, include_test: bool = False
    ) -> TemplateListResponse:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "notification_templates.view")

        if not include_test:
            cache_key = _CACHE_KEY_TEMPLATES.format(tenant=tenant_key)
            cached = await self._cache.get(cache_key)
            if cached is not None:
                return TemplateListResponse.model_validate_json(cached)

        async with self._database_pool.acquire() as conn:
            templates = await self._repository.list_templates(
                conn, tenant_key=tenant_key, include_test=include_test
            )
        items = [_template_response(t) for t in templates]
        result = TemplateListResponse(items=items, total=len(items))
        if not include_test:
            await self._cache.set(cache_key, result.model_dump_json(), _CACHE_TTL_TEMPLATES)
        return result

    async def delete_template(self, *, user_id: str, template_id: str, tenant_key: str) -> None:
        async with self._database_pool.transaction() as conn:
            await require_permission(conn, user_id, "notification_templates.delete")
            deleted = await self._repository.delete_template(conn, template_id, deleted_by=user_id)
            if not deleted:
                raise NotFoundError(
                    f"Template '{template_id}' not found or is a system template"
                )
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="template",
                    entity_id=template_id,
                    event_type="template_deleted",
                    event_category="notification",
                    occurred_at=utc_now_sql(),
                    actor_id=user_id,
                    actor_type="user",
                    properties={},
                ),
            )
        await self._cache.delete_pattern("notif:templates:*")

    async def get_template_detail(self, *, user_id: str, template_id: str) -> TemplateDetailResponse:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "notification_templates.view")
            template = await self._repository.get_template_by_id(conn, template_id)
            if template is None:
                raise NotFoundError(f"Template '{template_id}' not found")
            versions = await self._repository.list_versions(conn, template_id)
        return TemplateDetailResponse(
            id=template.id,
            tenant_key=template.tenant_key,
            code=template.code,
            name=template.name,
            description=template.description,
            notification_type_code=template.notification_type_code,
            channel_code=template.channel_code,
            category_code=getattr(template, "category_code", None),
            active_version_id=template.active_version_id,
            base_template_id=template.base_template_id,
            org_id=template.org_id,
            static_variables=template.static_variables or {},
            is_active=template.is_active,
            is_system=template.is_system,
            created_at=template.created_at,
            updated_at=template.updated_at,
            versions=[_version_response(v) for v in versions],
        )

    async def create_template(
        self, *, user_id: str, tenant_key: str, request: CreateTemplateRequest
    ) -> TemplateResponse:
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            await require_permission(conn, user_id, "notification_templates.create")
            existing = await self._repository.get_template_by_code(conn, request.code, tenant_key)
            if existing:
                raise ConflictError(f"Template code '{request.code}' already exists")
            
            try:
                template = await self._repository.create_template(
                    conn,
                    template_id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    code=request.code,
                    name=request.name,
                    description=request.description,
                    notification_type_code=request.notification_type_code,
                    channel_code=request.channel_code,
                    base_template_id=request.base_template_id,
                    org_id=request.org_id,
                    static_variables=_json.dumps(request.static_variables),
                    created_by=user_id,
                    now=now,
                )
            except asyncpg.exceptions.ForeignKeyViolationError as e:
                err_msg = str(e)
                if "fk_10_fct_templates_type_04_dim" in err_msg:
                    raise ValidationError(f"Invalid notification_type_code: '{request.notification_type_code}'")
                if "fk_10_fct_templates_channel_02_dim" in err_msg:
                    raise ValidationError(f"Invalid channel_code: '{request.channel_code}'")
                if "fk_10_fct_templates_base_10_fct" in err_msg:
                    raise ValidationError(f"Invalid base_template_id: '{request.base_template_id}'")
                raise
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="template",
                    entity_id=template.id,
                    event_type="template_created",
                    event_category="notification",
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={
                        "code": request.code,
                        "name": request.name,
                        "notification_type_code": request.notification_type_code,
                        "channel_code": request.channel_code,
                    },
                ),
            )
        await self._cache.delete_pattern("notif:templates:*")
        return _template_response(template)

    async def update_template(
        self, *, user_id: str, template_id: str, request: UpdateTemplateRequest
    ) -> TemplateResponse:
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            await require_permission(conn, user_id, "notification_templates.update")

            # If activating a specific version, validate it belongs to this template
            if request.active_version_id is not None:
                version = await self._repository.get_version(conn, request.active_version_id)
                if version is None or version.template_id != template_id:
                    raise NotFoundError(
                        f"Version '{request.active_version_id}' not found for template '{template_id}'"
                    )

            template = await self._repository.update_template(
                conn,
                template_id,
                name=request.name,
                description=request.description,
                is_disabled=request.is_disabled,
                active_version_id=request.active_version_id,
                static_variables=_json.dumps(request.static_variables) if request.static_variables is not None else None,
                updated_by=user_id,
                now=now,
            )
            if template is None:
                raise NotFoundError(f"Template '{template_id}' not found")

            event_type = "template_activated" if request.active_version_id else "template_updated"
            properties: dict[str, str | None] = {
                "name": request.name,
                "description": request.description,
                "is_disabled": str(request.is_disabled) if request.is_disabled is not None else None,
            }
            if request.active_version_id:
                properties["active_version_id"] = request.active_version_id

            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=template.tenant_key,
                    entity_type="template",
                    entity_id=template_id,
                    event_type=event_type,
                    event_category="notification",
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties=properties,
                ),
            )
        await self._cache.delete_pattern("notif:templates:*")
        return _template_response(template)

    async def create_version(
        self, *, user_id: str, template_id: str, request: CreateTemplateVersionRequest
    ) -> TemplateVersionResponse:
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            await require_permission(conn, user_id, "notification_templates.create")
            template = await self._repository.get_template_by_id(conn, template_id)
            if template is None:
                raise NotFoundError(f"Template '{template_id}' not found")
            next_version = await self._repository.get_next_version_number(conn, template_id)
            version_id = str(uuid.uuid4())
            version = await self._repository.create_version(
                conn,
                version_id=version_id,
                template_id=template_id,
                version_number=next_version,
                subject_line=request.subject_line,
                body_html=request.body_html,
                body_text=request.body_text,
                body_short=request.body_short,
                metadata_json=request.metadata_json,
                change_notes=request.change_notes,
                created_by=user_id,
                now=now,
            )
            # Auto-activate the new version
            await self._repository.update_template(
                conn,
                template_id,
                active_version_id=version_id,
                updated_by=user_id,
                now=now,
            )
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=template.tenant_key,
                    entity_type="template",
                    entity_id=template_id,
                    event_type="template_version_created",
                    event_category="notification",
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={
                        "version_id": version_id,
                        "version_number": str(next_version),
                    },
                ),
            )
        await self._cache.delete_pattern("notif:templates:*")
        return _version_response(version)

    async def preview_template(
        self, *, user_id: str, template_id: str, variables: dict[str, str]
    ) -> PreviewTemplateResponse:
        from .renderer import TemplateRenderer

        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "notification_templates.view")
            template = await self._repository.get_template_by_id(conn, template_id)
            if template is None:
                raise NotFoundError(f"Template '{template_id}' not found")
            if template.active_version_id is None:
                raise NotFoundError(f"Template '{template_id}' has no active version")
            version = await self._repository.get_version(conn, template.active_version_id)
            if version is None:
                raise NotFoundError(f"Active version not found for template '{template_id}'")

            # If template has a base template, fetch its active version for wrapping
            base_body_html: str | None = None
            if template.base_template_id:
                base_template = await self._repository.get_template_by_id(conn, template.base_template_id)
                if base_template and base_template.active_version_id:
                    base_version = await self._repository.get_version(conn, base_template.active_version_id)
                    if base_version:
                        base_body_html = base_version.body_html

        renderer = TemplateRenderer()
        rendered = renderer.render_template_version(
            subject_line=version.subject_line,
            body_html=version.body_html,
            body_text=version.body_text,
            body_short=version.body_short,
            variables=variables,
            base_body_html=base_body_html,
        )
        return PreviewTemplateResponse(
            rendered_subject=rendered["subject_line"],
            rendered_body_html=rendered["body_html"],
            rendered_body_text=rendered["body_text"],
            rendered_body_short=rendered["body_short"],
        )

    async def render_raw(
        self, *, user_id: str, request: "RenderRawRequest"
    ) -> PreviewTemplateResponse:
        """Render raw subject/html/text with variables — no DB template needed."""
        from .renderer import TemplateRenderer
        from ..schemas import RenderRawRequest  # noqa: F401 (type hint only)

        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "notification_templates.view")

        renderer = TemplateRenderer()
        rendered = renderer.render_template_version(
            subject_line=request.subject_line,
            body_html=request.body_html,
            body_text=request.body_text,
            body_short=None,
            variables=request.variables,
        )
        return PreviewTemplateResponse(
            rendered_subject=rendered["subject_line"],
            rendered_body_html=rendered["body_html"],
            rendered_body_text=rendered["body_text"],
            rendered_body_short=None,
        )


def _template_response(t) -> TemplateResponse:
    return TemplateResponse(
        id=t.id,
        tenant_key=t.tenant_key,
        code=t.code,
        name=t.name,
        description=t.description,
        notification_type_code=t.notification_type_code,
        channel_code=t.channel_code,
        category_code=getattr(t, "category_code", None),
        active_version_id=t.active_version_id,
        base_template_id=t.base_template_id,
        org_id=t.org_id,
        static_variables=t.static_variables or {},
        is_active=t.is_active,
        is_system=t.is_system,
        created_at=t.created_at,
        updated_at=t.updated_at,
    )


def _version_response(v) -> TemplateVersionResponse:
    return TemplateVersionResponse(
        id=v.id,
        template_id=v.template_id,
        version_number=v.version_number,
        subject_line=v.subject_line,
        body_html=v.body_html,
        body_text=v.body_text,
        body_short=v.body_short,
        metadata_json=v.metadata_json,
        change_notes=v.change_notes,
        is_active=v.is_active,
        created_at=v.created_at,
    )
