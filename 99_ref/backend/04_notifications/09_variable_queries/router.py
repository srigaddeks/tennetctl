from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, Query, status

from .dependencies import get_variable_query_service
from .schema_metadata import QUERYABLE_TABLES
from .service import VariableQueryService
from ..schemas import (
    AuditEventTypesResponse,
    AuditEventTypeInfo,
    CreateVariableKeyRequest,
    CreateVariableQueryRequest,
    PreviewQueryRequest,
    QueryPreviewResponse,
    RecentAuditEventResponse,
    RecentAuditEventsResponse,
    ResolveVariablesForEventRequest,
    ResolveVariablesForEventResponse,
    SchemaMetadataResponse,
    TableMetadata,
    ColumnMetadata,
    TemplateVariableKeyResponse,
    TestQueryRequest,
    TriggerForAuditEventRequest,
    TriggerForAuditEventResponse,
    UpdateVariableKeyRequest,
    UpdateVariableQueryRequest,
    VariableQueryListResponse,
    VariableQueryResponse,
)

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")
_errors_module = import_module("backend.01_core.errors")
_perm_check_module = import_module("backend.03_auth_manage._permission_check")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims
NotFoundError = _errors_module.NotFoundError
require_permission = _perm_check_module.require_permission

router = InstrumentedAPIRouter(
    prefix="/api/v1/notifications/variable-queries",
    tags=["notification-variable-queries"],
)


# ── Collection endpoints (no path params — MUST come before /{query_id}) ──
# NOTE: ALL POST routes with fixed sub-paths (resolve-for-event, trigger-for-audit-event)
# MUST be declared before /{query_id} to avoid FastAPI treating them as path params.


@router.get("", response_model=VariableQueryListResponse)
async def list_variable_queries(
    service: Annotated[VariableQueryService, Depends(get_variable_query_service)],
    claims=Depends(get_current_access_claims),
) -> VariableQueryListResponse:
    return await service.list_queries(
        user_id=claims.subject, tenant_key=claims.tenant_key
    )


@router.post(
    "",
    response_model=VariableQueryResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_variable_query(
    body: CreateVariableQueryRequest,
    service: Annotated[VariableQueryService, Depends(get_variable_query_service)],
    claims=Depends(get_current_access_claims),
) -> VariableQueryResponse:
    return await service.create_query(
        user_id=claims.subject, tenant_key=claims.tenant_key, request=body
    )


@router.post("/test", response_model=QueryPreviewResponse)
async def test_variable_query(
    body: TestQueryRequest,
    service: Annotated[VariableQueryService, Depends(get_variable_query_service)],
    claims=Depends(get_current_access_claims),
) -> QueryPreviewResponse:
    return await service.test_query(
        user_id=claims.subject, tenant_key=claims.tenant_key, request=body
    )


# ── Schema metadata + audit context endpoints (no path params) ────────────


@router.get("/schema", response_model=SchemaMetadataResponse)
async def get_schema_metadata(
    service: Annotated[VariableQueryService, Depends(get_variable_query_service)],
    claims=Depends(get_current_access_claims),
) -> SchemaMetadataResponse:
    """Return whitelisted table/column metadata for SQL editor autocomplete."""
    _perm_check_module = import_module("backend.03_auth_manage._permission_check")
    require_permission = _perm_check_module.require_permission

    async with service._database_pool.acquire() as conn:
        await require_permission(conn, claims.subject, "notification_system.view")
        raw = await service._repository.fetch_schema_metadata(conn, QUERYABLE_TABLES)

    # Group by (schema, table) → columns
    table_map: dict[tuple[str, str], list[ColumnMetadata]] = {}
    for row in raw:
        key = (row["table_schema"], row["table_name"])
        table_map.setdefault(key, []).append(
            ColumnMetadata(
                name=row["column_name"],
                data_type=row["data_type"],
                is_nullable=row["is_nullable"] == "YES",
            )
        )

    tables = [
        TableMetadata(schema_name=schema, table_name=table, columns=cols)
        for (schema, table), cols in sorted(table_map.items())
    ]
    return SchemaMetadataResponse(tables=tables)


@router.get("/audit-event-types", response_model=AuditEventTypesResponse)
async def get_audit_event_types(
    service: Annotated[VariableQueryService, Depends(get_variable_query_service)],
    claims=Depends(get_current_access_claims),
) -> AuditEventTypesResponse:
    """Return distinct audit event types with their available properties."""
    _perm_check_module = import_module("backend.03_auth_manage._permission_check")
    require_permission = _perm_check_module.require_permission

    async with service._database_pool.acquire() as conn:
        await require_permission(conn, claims.subject, "notification_system.view")
        event_types = await service._repository.fetch_audit_event_types(conn)

        # Enrich with available properties for each event type
        result = []
        for et in event_types:
            props = await service._repository.fetch_audit_event_properties(
                conn, et["event_type"]
            )
            result.append(
                AuditEventTypeInfo(
                    entity_type=et["entity_type"],
                    event_type=et["event_type"],
                    event_category=et["event_category"],
                    event_count=et["event_count"],
                    available_properties=props,
                )
            )

    return AuditEventTypesResponse(event_types=result)


@router.get("/recent-events", response_model=RecentAuditEventsResponse)
async def get_recent_audit_events(
    service: Annotated[VariableQueryService, Depends(get_variable_query_service)],
    claims=Depends(get_current_access_claims),
    event_type: str | None = Query(None, description="Filter by event type"),
    limit: int = Query(10, ge=1, le=50),
) -> RecentAuditEventsResponse:
    """Return recent audit events for test/preview context."""
    _perm_check_module = import_module("backend.03_auth_manage._permission_check")
    require_permission = _perm_check_module.require_permission

    async with service._database_pool.acquire() as conn:
        await require_permission(conn, claims.subject, "notification_system.view")
        raw = await service._repository.fetch_recent_audit_events(
            conn, event_type=event_type, limit=limit
        )

    events = [
        RecentAuditEventResponse(
            id=r["id"],
            entity_type=r["entity_type"],
            entity_id=r["entity_id"],
            event_type=r["event_type"],
            event_category=r["event_category"],
            actor_id=r.get("actor_id"),
            occurred_at=r["occurred_at"],
            properties=r.get("properties", {}),
        )
        for r in raw
    ]
    return RecentAuditEventsResponse(events=events)


# ── Resolve all variables against a real audit event ──────────────────────
# IMPORTANT: these fixed-path POST routes MUST come before /{query_id} routes
# so FastAPI doesn't try to match "resolve-for-event" as a query_id.


@router.post("/resolve-for-event", response_model=ResolveVariablesForEventResponse)
async def resolve_variables_for_event(
    body: ResolveVariablesForEventRequest,
    service: Annotated[VariableQueryService, Depends(get_variable_query_service)],
    claims=Depends(get_current_access_claims),
) -> ResolveVariablesForEventResponse:
    """Resolve all template variables using a real audit event as context.

    Useful for exploring what values each variable will have for a given
    event type — the output shows the exact values that would be injected
    into a template if that notification were sent now.
    """
    _perm_check_module = import_module("backend.03_auth_manage._permission_check")
    _errors_module = import_module("backend.01_core.errors")
    _variable_resolver_module = import_module(
        "backend.04_notifications.02_dispatcher.variable_resolver"
    )
    _audit_module = import_module("backend.01_core.audit")
    require_permission = _perm_check_module.require_permission
    NotFoundError = _errors_module.NotFoundError
    VariableResolver = _variable_resolver_module.VariableResolver
    AuditEntry = _audit_module.AuditEntry

    recipient_user_id = body.recipient_user_id or claims.subject

    async with service._database_pool.acquire() as conn:
        await require_permission(conn, claims.subject, "notification_system.view")

        # Fetch the audit event with its properties
        event_row = await conn.fetchrow(
            """
            SELECT ae.id::text, ae.entity_type, ae.entity_id::text,
                   ae.event_type, ae.event_category,
                   ae.actor_id::text, ae.occurred_at::text,
                   ae.tenant_key
            FROM "03_auth_manage"."40_aud_events" ae
            WHERE ae.id = $1
            """,
            body.audit_event_id,
        )
        if not event_row:
            raise NotFoundError(f"Audit event '{body.audit_event_id}' not found")

        props_rows = await conn.fetch(
            """
            SELECT meta_key, meta_value
            FROM "03_auth_manage"."41_dtl_audit_event_properties"
            WHERE event_id = $1
            """,
            body.audit_event_id,
        )
        properties = {r["meta_key"]: r["meta_value"] for r in props_rows}

        # Build AuditEntry
        audit_entry = AuditEntry(
            id=event_row["id"],
            tenant_key=event_row["tenant_key"],
            entity_type=event_row["entity_type"],
            entity_id=event_row["entity_id"],
            event_type=event_row["event_type"],
            event_category=event_row["event_category"],
            occurred_at=event_row["occurred_at"],
            actor_id=event_row["actor_id"],
            properties=properties,
        )

        settings = service._settings

        resolver = VariableResolver()
        resolved = await resolver.resolve_all(
            conn,
            audit_entry=audit_entry,
            recipient_user_id=recipient_user_id,
            settings=settings,
            template_id=body.template_id,
        )

    audit_event_response = RecentAuditEventResponse(
        id=event_row["id"],
        entity_type=event_row["entity_type"],
        entity_id=event_row["entity_id"],
        event_type=event_row["event_type"],
        event_category=event_row["event_category"],
        actor_id=event_row["actor_id"],
        occurred_at=event_row["occurred_at"],
        properties=properties,
    )
    return ResolveVariablesForEventResponse(
        resolved=resolved,
        audit_event=audit_event_response,
    )


# ── Trigger a real notification for an existing audit event ───────────────


@router.post("/trigger-for-audit-event", response_model=TriggerForAuditEventResponse)
async def trigger_for_audit_event(
    body: TriggerForAuditEventRequest,
    service: Annotated[VariableQueryService, Depends(get_variable_query_service)],
    claims=Depends(get_current_access_claims),
) -> TriggerForAuditEventResponse:
    """Manually trigger the full notification pipeline for an existing audit event.

    - Fetches the real audit event and its properties
    - Resolves all template variables from live data
    - Renders the template
    - If dry_run=False, sends the actual email and creates a queue entry
    - Useful for testing that templates render and deliver correctly end-to-end
    """
    _perm_check_module = import_module("backend.03_auth_manage._permission_check")
    _errors_module = import_module("backend.01_core.errors")
    _variable_resolver_module = import_module(
        "backend.04_notifications.02_dispatcher.variable_resolver"
    )
    _audit_module = import_module("backend.01_core.audit")
    _renderer_module = import_module("backend.04_notifications.01_templates.renderer")
    _email_module = import_module("backend.04_notifications.04_channels.email_provider")
    require_permission = _perm_check_module.require_permission
    NotFoundError = _errors_module.NotFoundError
    VariableResolver = _variable_resolver_module.VariableResolver
    AuditEntry = _audit_module.AuditEntry
    TemplateRenderer = _renderer_module.TemplateRenderer
    EmailProvider = _email_module.EmailProvider
    settings = service._settings

    async with service._database_pool.acquire() as conn:
        await require_permission(conn, claims.subject, "notification_system.view")

        # Fetch the audit event
        event_row = await conn.fetchrow(
            """
            SELECT ae.id::text, ae.entity_type, ae.entity_id::text,
                   ae.event_type, ae.event_category,
                   ae.actor_id::text, ae.occurred_at::text,
                   ae.tenant_key
            FROM "03_auth_manage"."40_aud_events" ae
            WHERE ae.id = $1
            """,
            body.audit_event_id,
        )
        if not event_row:
            raise NotFoundError(f"Audit event '{body.audit_event_id}' not found")

        props_rows = await conn.fetch(
            """
            SELECT meta_key, meta_value
            FROM "03_auth_manage"."41_dtl_audit_event_properties"
            WHERE event_id = $1
            """,
            body.audit_event_id,
        )
        properties = {r["meta_key"]: r["meta_value"] for r in props_rows}

        audit_entry = AuditEntry(
            id=event_row["id"],
            tenant_key=event_row["tenant_key"],
            entity_type=event_row["entity_type"],
            entity_id=event_row["entity_id"],
            event_type=event_row["event_type"],
            event_category=event_row["event_category"],
            occurred_at=event_row["occurred_at"],
            actor_id=event_row["actor_id"],
            properties=properties,
        )

        # Resolve template: use override or look up by notification_type + event_type
        template_row = None
        if body.template_id:
            template_row = await conn.fetchrow(
                """
                SELECT t.id::text AS template_id, v.id::text AS version_id,
                       v.subject_line, v.body_html, v.body_text, v.body_short,
                       bt_v.body_html AS base_body_html,
                       t.static_variables::text AS static_variables_json
                FROM "03_notifications"."10_fct_templates" t
                JOIN "03_notifications"."14_dtl_template_versions" v
                    ON v.id = t.active_version_id
                LEFT JOIN "03_notifications"."10_fct_templates" bt
                    ON bt.id = t.base_template_id AND bt.is_active = TRUE AND bt.is_deleted = FALSE
                LEFT JOIN "03_notifications"."14_dtl_template_versions" bt_v
                    ON bt_v.id = bt.active_version_id
                WHERE t.id = $1 AND t.is_active = TRUE AND t.is_deleted = FALSE
                LIMIT 1
                """,
                body.template_id,
            )
        elif body.notification_type_code:
            template_row = await conn.fetchrow(
                """
                SELECT t.id::text AS template_id, v.id::text AS version_id,
                       v.subject_line, v.body_html, v.body_text, v.body_short,
                       bt_v.body_html AS base_body_html,
                       t.static_variables::text AS static_variables_json
                FROM "03_notifications"."10_fct_templates" t
                JOIN "03_notifications"."14_dtl_template_versions" v
                    ON v.id = t.active_version_id
                LEFT JOIN "03_notifications"."10_fct_templates" bt
                    ON bt.id = t.base_template_id AND bt.is_active = TRUE AND bt.is_deleted = FALSE
                LEFT JOIN "03_notifications"."14_dtl_template_versions" bt_v
                    ON bt_v.id = bt.active_version_id
                WHERE t.notification_type_code = $1
                  AND t.channel_code = 'email'
                  AND (t.tenant_key = $2 OR t.tenant_key = '__system__')
                  AND t.is_active = TRUE AND t.is_deleted = FALSE
                ORDER BY CASE WHEN t.tenant_key = $2 THEN 0 ELSE 1 END
                LIMIT 1
                """,
                body.notification_type_code,
                audit_entry.tenant_key,
            )
        else:
            # Try matching a rule for the event_type
            rule_row = await conn.fetchrow(
                """
                SELECT notification_type_code FROM "03_notifications"."11_fct_notification_rules"
                WHERE source_event_type = $1
                  AND (tenant_key = $2 OR tenant_key = '__system__')
                  AND is_active = TRUE AND is_disabled = FALSE AND is_deleted = FALSE
                LIMIT 1
                """,
                audit_entry.event_type,
                audit_entry.tenant_key,
            )
            if rule_row:
                template_row = await conn.fetchrow(
                    """
                    SELECT t.id::text AS template_id, v.id::text AS version_id,
                           v.subject_line, v.body_html, v.body_text, v.body_short,
                           bt_v.body_html AS base_body_html,
                           t.static_variables::text AS static_variables_json
                    FROM "03_notifications"."10_fct_templates" t
                    JOIN "03_notifications"."14_dtl_template_versions" v
                        ON v.id = t.active_version_id
                    LEFT JOIN "03_notifications"."10_fct_templates" bt
                        ON bt.id = t.base_template_id AND bt.is_active = TRUE AND bt.is_deleted = FALSE
                    LEFT JOIN "03_notifications"."14_dtl_template_versions" bt_v
                        ON bt_v.id = bt.active_version_id
                    WHERE t.notification_type_code = $1
                      AND t.channel_code = 'email'
                      AND (t.tenant_key = $2 OR t.tenant_key = '__system__')
                      AND t.is_active = TRUE AND t.is_deleted = FALSE
                    ORDER BY CASE WHEN t.tenant_key = $2 THEN 0 ELSE 1 END
                    LIMIT 1
                    """,
                    rule_row["notification_type_code"],
                    audit_entry.tenant_key,
                )

        if not template_row:
            return TriggerForAuditEventResponse(
                success=False,
                message="No active template found for this audit event. Specify template_id or notification_type_code.",
            )

        # Resolve variables
        resolver = VariableResolver()
        resolved_vars = await resolver.resolve_all(
            conn,
            audit_entry=audit_entry,
            recipient_user_id=claims.subject,
            settings=settings,
            template_id=template_row["template_id"],
        )

        # Merge static variables as lowest-priority defaults
        import json as _json
        try:
            static_vars = _json.loads(template_row["static_variables_json"] or "{}")
        except Exception:
            static_vars = {}
        merged_vars = {**static_vars, **resolved_vars}

        # Render
        renderer = TemplateRenderer()
        rendered = renderer.render_template_version(
            subject_line=template_row["subject_line"],
            body_html=template_row["body_html"],
            body_text=template_row["body_text"],
            body_short=template_row["body_short"],
            variables=merged_vars,
            base_body_html=template_row["base_body_html"],
        )

        if body.dry_run:
            return TriggerForAuditEventResponse(
                success=True,
                message="Dry run complete — template rendered but not sent.",
                rendered_subject=rendered.get("subject_line"),
                rendered_body_html=rendered.get("body_html"),
                rendered_variables=merged_vars,
                dry_run=True,
            )

        # Resolve recipient email
        to_email = body.to_email
        if not to_email:
            email_row = await conn.fetchrow(
                """
                SELECT property_value FROM "03_auth_manage"."05_dtl_user_properties"
                WHERE user_id = $1 AND property_key = 'email' LIMIT 1
                """,
                claims.subject,
            )
            to_email = email_row["property_value"] if email_row else None

        if not to_email:
            return TriggerForAuditEventResponse(
                success=False,
                message="No recipient email — provide to_email or ensure your profile has an email.",
                rendered_subject=rendered.get("subject_line"),
                rendered_body_html=rendered.get("body_html"),
                rendered_variables=merged_vars,
            )

        # Fetch SMTP config
        smtp_row = await conn.fetchrow(
            """
            SELECT host, port, username, password, from_email, from_name, use_tls, start_tls
            FROM "03_notifications"."30_fct_smtp_config"
            WHERE tenant_key = 'default' AND is_active = TRUE LIMIT 1
            """
        )

    smtp_host = (smtp_row["host"] if smtp_row else None) or getattr(settings, "notification_smtp_host", None)
    smtp_port = (smtp_row["port"] if smtp_row else None) or getattr(settings, "notification_smtp_port", 587)
    smtp_user = (smtp_row["username"] if smtp_row else None) or getattr(settings, "notification_smtp_user", None)
    smtp_pass = (smtp_row["password"] if smtp_row else None) or getattr(settings, "notification_smtp_password", None)
    from_email = (smtp_row["from_email"] if smtp_row else None) or getattr(settings, "notification_from_email", None)
    from_name = (smtp_row["from_name"] if smtp_row else None) or getattr(settings, "notification_from_name", "K-Control")
    use_tls = (smtp_row["use_tls"] if smtp_row else None) if smtp_row else getattr(settings, "notification_smtp_use_tls", False)
    start_tls = (smtp_row["start_tls"] if smtp_row else None) if smtp_row else getattr(settings, "notification_smtp_start_tls", True)

    if not smtp_host or not from_email:
        return TriggerForAuditEventResponse(
            success=False,
            message="SMTP not configured — cannot send. Configure SMTP in the settings tab.",
            rendered_subject=rendered.get("subject_line"),
            rendered_body_html=rendered.get("body_html"),
            rendered_variables=merged_vars,
        )

    provider = EmailProvider(
        host=smtp_host,
        port=smtp_port,
        username=smtp_user,
        password=smtp_pass,
        from_email=from_email,
        from_name=from_name,
        use_tls=use_tls or False,
        start_tls=start_tls if start_tls is not None else True,
    )
    result = await provider.send(
        recipient=to_email,
        subject=rendered.get("subject_line") or f"[K-Control] {audit_entry.event_type}",
        body_html=rendered.get("body_html") or "",
        body_text=rendered.get("body_text") or "",
    )

    if result.success:
        return TriggerForAuditEventResponse(
            success=True,
            message=f"Email sent to {to_email}",
            rendered_subject=rendered.get("subject_line"),
            rendered_body_html=rendered.get("body_html"),
            rendered_variables=merged_vars,
        )
    return TriggerForAuditEventResponse(
        success=False,
        message=f"SMTP delivery failed: {result.error_message}",
        rendered_subject=rendered.get("subject_line"),
        rendered_body_html=rendered.get("body_html"),
        rendered_variables=merged_vars,
    )


# ── Item endpoints (with path param — MUST come AFTER fixed-path POST routes) ─


@router.get("/{query_id}", response_model=VariableQueryResponse)
async def get_variable_query(
    query_id: str,
    service: Annotated[VariableQueryService, Depends(get_variable_query_service)],
    claims=Depends(get_current_access_claims),
) -> VariableQueryResponse:
    async with service._database_pool.acquire() as conn:
        await require_permission(conn, claims.subject, "notification_system.view")
        record = await service._repository.get_by_id(conn, query_id)  # type: ignore[arg-type]
        if not record:
            raise NotFoundError("Variable query not found")
        variable_keys = await service._repository.get_variable_keys_for_query(conn, query_id)

    from .service import _query_response
    return _query_response(record, variable_keys)


@router.patch("/{query_id}", response_model=VariableQueryResponse)
async def update_variable_query(
    query_id: str,
    body: UpdateVariableQueryRequest,
    service: Annotated[VariableQueryService, Depends(get_variable_query_service)],
    claims=Depends(get_current_access_claims),
) -> VariableQueryResponse:
    return await service.update_query(
        user_id=claims.subject, query_id=query_id, request=body
    )


@router.delete("/{query_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_variable_query(
    query_id: str,
    service: Annotated[VariableQueryService, Depends(get_variable_query_service)],
    claims=Depends(get_current_access_claims),
) -> None:
    await service.delete_query(user_id=claims.subject, query_id=query_id)


@router.post("/{query_id}/preview", response_model=QueryPreviewResponse)
async def preview_variable_query(
    query_id: str,
    body: PreviewQueryRequest,
    service: Annotated[VariableQueryService, Depends(get_variable_query_service)],
    claims=Depends(get_current_access_claims),
) -> QueryPreviewResponse:
    return await service.preview_query(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        query_id=query_id,
        request=body,
    )


# ── Global Variable Key management endpoints ──────────────────────────────


_var_keys_router = InstrumentedAPIRouter(
    prefix="/api/v1/notifications/variable-keys",
    tags=["notification-variable-keys"],
)


@_var_keys_router.get("", response_model=list[TemplateVariableKeyResponse])
async def list_variable_keys(
    service: Annotated[VariableQueryService, Depends(get_variable_query_service)],
    claims=Depends(get_current_access_claims),
) -> list[TemplateVariableKeyResponse]:
    """Return all global variable keys (system + user-defined)."""
    _perm_check_module = import_module("backend.03_auth_manage._permission_check")
    require_permission = _perm_check_module.require_permission
    async with service._database_pool.acquire() as conn:
        await require_permission(conn, claims.subject, "notification_system.view")
        rows = await conn.fetch(
            """
            SELECT id::text, code, name, description, data_type, example_value,
                   example_value AS preview_default, resolution_source, resolution_key,
                   static_value, query_id::text, is_user_defined, sort_order
            FROM "03_notifications"."08_dim_template_variable_keys"
            ORDER BY sort_order, code
            """
        )
    return [TemplateVariableKeyResponse(**dict(r)) for r in rows]


@_var_keys_router.post(
    "",
    response_model=TemplateVariableKeyResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_variable_key(
    body: CreateVariableKeyRequest,
    service: Annotated[VariableQueryService, Depends(get_variable_query_service)],
    claims=Depends(get_current_access_claims),
) -> TemplateVariableKeyResponse:
    """Create a new user-defined variable key (static or custom_query)."""
    import uuid as _uuid
    _perm_check_module = import_module("backend.03_auth_manage._permission_check")
    _errors_module = import_module("backend.01_core.errors")
    require_permission = _perm_check_module.require_permission
    ConflictError = _errors_module.ConflictError

    async with service._database_pool.transaction() as conn:
        await require_permission(conn, claims.subject, "notification_system.create")
        existing = await conn.fetchrow(
            'SELECT id FROM "03_notifications"."08_dim_template_variable_keys" WHERE code = $1',
            body.code,
        )
        if existing:
            raise ConflictError(f"Variable key '{body.code}' already exists")

        row = await conn.fetchrow(
            """
            INSERT INTO "03_notifications"."08_dim_template_variable_keys"
                (id, code, name, description, data_type, example_value,
                 resolution_source, resolution_key, static_value, query_id,
                 is_user_defined, sort_order, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, TRUE, 9999, NOW(), NOW())
            RETURNING id::text, code, name, description, data_type, example_value,
                      example_value AS preview_default, resolution_source, resolution_key,
                      static_value, query_id::text, is_user_defined, sort_order
            """,
            str(_uuid.uuid4()),
            body.code,
            body.name,
            body.description or "",
            body.data_type or "string",
            body.example_value or body.static_value,
            body.resolution_source,
            body.resolution_key,
            body.static_value,
            body.query_id,
        )
    return TemplateVariableKeyResponse(**dict(row))


@_var_keys_router.patch("/{code}", response_model=TemplateVariableKeyResponse)
async def update_variable_key(
    code: str,
    body: UpdateVariableKeyRequest,
    service: Annotated[VariableQueryService, Depends(get_variable_query_service)],
    claims=Depends(get_current_access_claims),
) -> TemplateVariableKeyResponse:
    """Update a user-defined variable key."""
    _perm_check_module = import_module("backend.03_auth_manage._permission_check")
    _errors_module = import_module("backend.01_core.errors")
    require_permission = _perm_check_module.require_permission
    NotFoundError = _errors_module.NotFoundError
    ValidationError = _errors_module.ValidationError

    async with service._database_pool.transaction() as conn:
        await require_permission(conn, claims.subject, "notification_system.update")
        existing = await conn.fetchrow(
            'SELECT id, is_user_defined FROM "03_notifications"."08_dim_template_variable_keys" WHERE code = $1',
            code,
        )
        if not existing:
            raise NotFoundError(f"Variable key '{code}' not found")
        if not existing["is_user_defined"]:
            raise ValidationError("System variable keys cannot be modified")

        set_parts = ["updated_at = NOW()"]
        vals: list = []
        idx = 1

        for field, col in [
            ("name", "name"), ("description", "description"),
            ("static_value", "static_value"), ("resolution_source", "resolution_source"),
            ("resolution_key", "resolution_key"), ("query_id", "query_id"),
            ("example_value", "example_value"),
        ]:
            val = getattr(body, field)
            if val is not None:
                set_parts.append(f"{col} = ${idx}")
                vals.append(val)
                idx += 1

        vals.append(code)
        row = await conn.fetchrow(
            f"""
            UPDATE "03_notifications"."08_dim_template_variable_keys"
            SET {', '.join(set_parts)}
            WHERE code = ${idx}
            RETURNING id::text, code, name, description, data_type, example_value,
                      example_value AS preview_default, resolution_source, resolution_key,
                      static_value, query_id::text, is_user_defined, sort_order
            """,
            *vals,
        )
    return TemplateVariableKeyResponse(**dict(row))


@_var_keys_router.delete("/{code}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_variable_key(
    code: str,
    service: Annotated[VariableQueryService, Depends(get_variable_query_service)],
    claims=Depends(get_current_access_claims),
) -> None:
    """Delete a user-defined variable key."""
    _perm_check_module = import_module("backend.03_auth_manage._permission_check")
    _errors_module = import_module("backend.01_core.errors")
    require_permission = _perm_check_module.require_permission
    NotFoundError = _errors_module.NotFoundError
    ValidationError = _errors_module.ValidationError

    async with service._database_pool.transaction() as conn:
        await require_permission(conn, claims.subject, "notification_system.delete")
        existing = await conn.fetchrow(
            'SELECT id, is_user_defined FROM "03_notifications"."08_dim_template_variable_keys" WHERE code = $1',
            code,
        )
        if not existing:
            raise NotFoundError(f"Variable key '{code}' not found")
        if not existing["is_user_defined"]:
            raise ValidationError("System variable keys cannot be deleted")
        await conn.execute(
            'DELETE FROM "03_notifications"."08_dim_template_variable_keys" WHERE code = $1',
            code,
        )
