from __future__ import annotations

from pydantic import BaseModel, Field


class CreateTemplateRequest(BaseModel):
    code: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="", max_length=500)
    notification_type_code: str = Field(..., min_length=1, max_length=50)
    channel_code: str = Field(..., min_length=1, max_length=50)
    base_template_id: str | None = None
    org_id: str | None = None
    static_variables: dict[str, str] = Field(default_factory=dict)


class CreateTemplateVersionRequest(BaseModel):
    subject_line: str | None = Field(None, max_length=500)
    body_html: str | None = None
    body_text: str | None = None
    body_short: str | None = Field(None, max_length=500)
    metadata_json: str | None = None
    change_notes: str | None = Field(None, max_length=500)


class TemplateVersionResponse(BaseModel):
    id: str
    template_id: str
    version_number: int
    subject_line: str | None = None
    body_html: str | None = None
    body_text: str | None = None
    body_short: str | None = None
    metadata_json: str | None = None
    change_notes: str | None = None
    is_active: bool
    created_at: str


class TemplateResponse(BaseModel):
    id: str
    tenant_key: str
    code: str
    name: str
    description: str
    notification_type_code: str
    channel_code: str
    category_code: str | None = None
    active_version_id: str | None = None
    base_template_id: str | None = None
    org_id: str | None = None
    static_variables: dict[str, str] = Field(default_factory=dict)
    is_active: bool
    is_system: bool
    created_at: str
    updated_at: str


class TemplateListResponse(BaseModel):
    items: list[TemplateResponse]
    total: int


class PreviewTemplateRequest(BaseModel):
    variables: dict[str, str]


class PreviewTemplateResponse(BaseModel):
    rendered_subject: str | None = None
    rendered_body_html: str | None = None
    rendered_body_text: str | None = None
    rendered_body_short: str | None = None


class RenderRawRequest(BaseModel):
    subject_line: str | None = None
    body_html: str | None = None
    body_text: str | None = None
    variables: dict[str, str] = Field(default_factory=dict)


class SetPreferenceRequest(BaseModel):
    scope_level: str = Field(..., pattern=r"^(global|channel|category|type)$")
    channel_code: str | None = None
    category_code: str | None = None
    notification_type_code: str | None = None
    scope_org_id: str | None = None
    scope_workspace_id: str | None = None
    is_enabled: bool


class PreferenceResponse(BaseModel):
    id: str
    user_id: str
    tenant_key: str
    scope_level: str
    channel_code: str | None = None
    category_code: str | None = None
    notification_type_code: str | None = None
    scope_org_id: str | None = None
    scope_workspace_id: str | None = None
    is_enabled: bool
    created_at: str
    updated_at: str


class PreferenceMatrixResponse(BaseModel):
    items: list[PreferenceResponse]


class WebPushSubscribeRequest(BaseModel):
    endpoint: str = Field(..., min_length=1)
    p256dh_key: str = Field(..., min_length=1)
    auth_key: str = Field(..., min_length=1)
    user_agent: str | None = None


class WebPushSubscriptionResponse(BaseModel):
    id: str
    user_id: str
    tenant_key: str
    endpoint: str
    is_active: bool
    last_used_at: str | None = None
    created_at: str
    updated_at: str


class CreateBroadcastRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    body_text: str = Field(..., min_length=1)
    body_html: str | None = None
    subject_line: str | None = None
    scope: str = Field(..., pattern=r"^(global|org|workspace)$")
    scope_org_id: str | None = None
    scope_workspace_id: str | None = None
    notification_type_code: str | None = None
    priority_code: str | None = Field(None, pattern=r"^(critical|high|normal|low)$")
    severity: str | None = Field(None, pattern=r"^(critical|high|medium|low|info)$")
    is_critical: bool = False
    template_code: str | None = None
    scheduled_at: str | None = None
    static_variables: dict[str, str] = Field(default_factory=dict)


class BroadcastResponse(BaseModel):
    id: str
    tenant_key: str
    title: str
    body_text: str
    body_html: str | None = None
    scope: str
    scope_org_id: str | None = None
    scope_workspace_id: str | None = None
    notification_type_code: str
    priority_code: str
    severity: str | None = None
    is_critical: bool = False
    template_code: str | None = None
    static_variables: dict[str, str] = Field(default_factory=dict)
    scheduled_at: str | None = None
    sent_at: str | None = None
    total_recipients: int | None = None
    is_active: bool
    created_at: str
    updated_at: str
    created_by: str


class BroadcastListResponse(BaseModel):
    items: list[BroadcastResponse]
    total: int


# ------------------------------------------------------------------ #
# Releases
# ------------------------------------------------------------------ #


class CreateReleaseRequest(BaseModel):
    version: str = Field(..., min_length=1, max_length=50)
    title: str = Field(..., min_length=1, max_length=300)
    summary: str = Field(..., min_length=1, max_length=500)
    body_markdown: str | None = None
    body_html: str | None = None
    changelog_url: str | None = Field(None, max_length=500)
    release_date: str | None = None
    template_code: str | None = None


class UpdateReleaseRequest(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=300)
    summary: str | None = Field(None, min_length=1, max_length=500)
    body_markdown: str | None = None
    body_html: str | None = None
    changelog_url: str | None = Field(None, max_length=500)
    release_date: str | None = None
    template_code: str | None = None


class ReleaseResponse(BaseModel):
    id: str
    tenant_key: str
    version: str
    title: str
    summary: str
    body_markdown: str | None = None
    body_html: str | None = None
    changelog_url: str | None = None
    status: str
    release_date: str | None = None
    published_at: str | None = None
    broadcast_id: str | None = None
    template_code: str | None = None
    is_active: bool
    created_at: str
    updated_at: str
    created_by: str


class ReleaseListResponse(BaseModel):
    items: list[ReleaseResponse]
    total: int


# ------------------------------------------------------------------ #
# Incidents
# ------------------------------------------------------------------ #


class CreateIncidentRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    description: str = Field(..., min_length=1)
    severity: str = Field(..., pattern=r"^(critical|major|minor|informational)$")
    affected_components: str | None = Field(None, max_length=500)
    started_at: str | None = None
    notify_users: bool = True
    template_code: str | None = None


class UpdateIncidentRequest(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=300)
    description: str | None = None
    severity: str | None = Field(None, pattern=r"^(critical|major|minor|informational)$")
    affected_components: str | None = Field(None, max_length=500)


class CreateIncidentUpdateRequest(BaseModel):
    status: str = Field(..., pattern=r"^(investigating|identified|monitoring|resolved)$")
    message: str = Field(..., min_length=1)
    is_public: bool = True
    notify_users: bool = True


class IncidentUpdateResponse(BaseModel):
    id: str
    incident_id: str
    status: str
    message: str
    is_public: bool
    broadcast_id: str | None = None
    created_at: str
    created_by: str


class IncidentResponse(BaseModel):
    id: str
    tenant_key: str
    title: str
    description: str
    severity: str
    status: str
    affected_components: str | None = None
    started_at: str
    resolved_at: str | None = None
    broadcast_id: str | None = None
    is_active: bool
    created_at: str
    updated_at: str
    created_by: str
    updates: list[IncidentUpdateResponse] | None = None


class IncidentListResponse(BaseModel):
    items: list[IncidentResponse]
    total: int


# ------------------------------------------------------------------ #
# Admin queue monitor
# ------------------------------------------------------------------ #


class QueueItemAdminResponse(BaseModel):
    id: str
    tenant_key: str
    user_id: str | None = None
    notification_type_code: str
    channel_code: str
    status_code: str
    priority_code: str
    template_id: str | None = None
    source_rule_id: str | None = None
    broadcast_id: str | None = None
    rendered_subject: str | None = None
    recipient_email: str | None = None
    scheduled_at: str
    attempt_count: int
    max_attempts: int
    next_retry_at: str | None = None
    last_error: str | None = None
    created_at: str
    updated_at: str
    completed_at: str | None = None


class QueueAdminListResponse(BaseModel):
    items: list[QueueItemAdminResponse]
    total: int


class QueueStatsResponse(BaseModel):
    queued: int
    processing: int
    sent: int
    delivered: int
    failed: int
    dead_letter: int
    suppressed: int


class QueueAdminResponse(BaseModel):
    stats: QueueStatsResponse
    items: list[QueueItemAdminResponse]
    total: int



class NotificationHistoryItem(BaseModel):
    id: str
    notification_type_code: str
    channel_code: str
    status_code: str
    priority_code: str
    rendered_subject: str | None = None
    rendered_body: str | None = None
    scheduled_at: str
    attempt_count: int
    created_at: str
    completed_at: str | None = None


class NotificationHistoryResponse(BaseModel):
    items: list[NotificationHistoryItem]
    total: int


class ChannelResponse(BaseModel):
    id: str
    code: str
    name: str
    description: str
    is_available: bool
    sort_order: int


class CategoryResponse(BaseModel):
    id: str
    code: str
    name: str
    description: str
    is_mandatory: bool
    sort_order: int


class NotificationTypeResponse(BaseModel):
    id: str
    code: str
    name: str
    description: str
    category_code: str
    is_mandatory: bool
    is_user_triggered: bool
    default_enabled: bool
    cooldown_seconds: int | None = None
    sort_order: int


class NotificationConfigResponse(BaseModel):
    """All notification dimension data in one response."""
    channels: list[ChannelResponse]
    categories: list[CategoryResponse]
    types: list[NotificationTypeResponse]
    variable_keys: list[TemplateVariableKeyResponse]



class CampaignRunResponse(BaseModel):
    id: str
    tenant_key: str
    rule_id: str
    run_type: str
    started_at: str
    completed_at: str | None = None
    users_evaluated: int
    users_matched: int
    notifications_created: int
    status: str
    error_message: str | None = None
    created_at: str


# ------------------------------------------------------------------ #
# Notification Rules
# ------------------------------------------------------------------ #


class CreateRuleRequest(BaseModel):
    code: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=500)
    source_event_type: str = Field(..., min_length=1, max_length=100)
    source_event_category: str = Field(default="", max_length=100)
    notification_type_code: str = Field(..., min_length=1, max_length=50)
    recipient_strategy: str = Field(..., min_length=1, max_length=50)
    recipient_filter_json: str | None = None
    priority_code: str = Field(default="normal", max_length=20)
    delay_seconds: int = Field(default=0, ge=0)


class UpdateRuleRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=500)
    priority_code: str | None = Field(None, max_length=20)
    delay_seconds: int | None = Field(None, ge=0)
    is_disabled: bool | None = None


class RuleResponse(BaseModel):
    id: str
    tenant_key: str
    code: str
    name: str
    description: str | None = None
    source_event_type: str
    source_event_category: str | None = None
    notification_type_code: str
    recipient_strategy: str
    recipient_filter_json: str | None = None
    priority_code: str
    delay_seconds: int
    is_active: bool
    is_system: bool
    created_at: str
    updated_at: str


class RuleChannelResponse(BaseModel):
    id: str
    rule_id: str
    channel_code: str
    template_code: str | None = None
    is_active: bool


class RuleConditionResponse(BaseModel):
    id: str
    rule_id: str
    condition_type: str
    field_key: str
    operator: str
    value: str
    value_type: str
    logical_group: int
    sort_order: int
    is_active: bool
    created_at: str
    updated_at: str


class RuleDetailResponse(BaseModel):
    id: str
    tenant_key: str
    code: str
    name: str
    description: str | None = None
    source_event_type: str
    source_event_category: str | None = None
    notification_type_code: str
    recipient_strategy: str
    recipient_filter_json: str | None = None
    priority_code: str
    delay_seconds: int
    is_active: bool
    is_system: bool
    created_at: str
    updated_at: str
    channels: list[RuleChannelResponse] = Field(default_factory=list)
    conditions: list[RuleConditionResponse] = Field(default_factory=list)
    recent_runs: list[CampaignRunResponse] = Field(default_factory=list)


class SetRuleChannelRequest(BaseModel):
    template_code: str | None = None
    is_active: bool = True


class CreateRuleConditionRequest(BaseModel):
    condition_type: str = Field(..., min_length=1, max_length=50)
    field_key: str = Field(..., min_length=1, max_length=100)
    operator: str = Field(..., min_length=1, max_length=50)
    value: str = Field(..., min_length=1, max_length=500)
    value_type: str = Field(default="string", max_length=20)
    logical_group: int = Field(default=0, ge=0)
    sort_order: int = Field(default=0, ge=0)


class TemplateVariableKeyResponse(BaseModel):
    id: str
    code: str
    name: str
    description: str
    data_type: str
    example_value: str | None = None
    preview_default: str | None = None
    resolution_source: str
    resolution_key: str | None = None
    static_value: str | None = None
    query_id: str | None = None
    is_user_defined: bool = False
    sort_order: int


class CreateVariableKeyRequest(BaseModel):
    code: str = Field(..., min_length=1, max_length=100, pattern=r"^[\w.]+$")
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="", max_length=1000)
    data_type: str = Field(default="string", max_length=50)
    example_value: str | None = None
    resolution_source: str = Field(default="static")
    resolution_key: str | None = None
    static_value: str | None = None
    query_id: str | None = None


class UpdateVariableKeyRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    static_value: str | None = None
    resolution_source: str | None = None
    resolution_key: str | None = None
    query_id: str | None = None
    example_value: str | None = None


# ------------------------------------------------------------------ #
# SMTP config
# ------------------------------------------------------------------ #


class SmtpConfigRequest(BaseModel):
    host: str = Field(..., min_length=1, max_length=253)
    port: int = Field(..., ge=1, le=65535)
    username: str | None = Field(None, max_length=200)
    password: str | None = Field(None, max_length=500)
    from_email: str = Field(..., min_length=5, max_length=254)
    from_name: str = Field(..., min_length=1, max_length=100)
    use_tls: bool = False
    start_tls: bool = True


class SmtpConfigResponse(BaseModel):
    host: str | None
    port: int
    username: str | None
    from_email: str | None
    from_name: str
    use_tls: bool
    start_tls: bool
    is_configured: bool
    source: str = "env"  # "db" or "env"


class SmtpTestRequest(BaseModel):
    to_email: str = Field(..., min_length=5, max_length=254)
    host: str | None = None
    port: int | None = None
    username: str | None = None
    password: str | None = None
    from_email: str | None = None
    from_name: str | None = None
    use_tls: bool | None = None
    start_tls: bool | None = None


class SmtpTestResponse(BaseModel):
    success: bool
    message: str
    detail: str | None = None


# ------------------------------------------------------------------ #
# Send test notification
# ------------------------------------------------------------------ #


class SendTestNotificationRequest(BaseModel):
    to_email: str = Field(..., min_length=5, max_length=254)
    notification_type_code: str = Field(..., min_length=1, max_length=50)
    channel_code: str = Field(default="email", min_length=1, max_length=50)
    subject: str | None = Field(None, max_length=500)
    body: str | None = None
    variables: dict[str, str] = Field(default_factory=dict)


class SendTestNotificationResponse(BaseModel):
    success: bool
    message: str
    queue_id: str | None = None


# ------------------------------------------------------------------ #
# Reports / analytics
# ------------------------------------------------------------------ #


class QueueActionRequest(BaseModel):
    reason: str | None = Field(None, max_length=500)


class QueueActionResponse(BaseModel):
    success: bool
    message: str


class DeliveryLogResponse(BaseModel):
    id: str
    notification_id: str
    channel_code: str
    attempt_number: int
    status: str
    provider_response: str | None = None
    provider_message_id: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    duration_ms: int | None = None
    occurred_at: str
    created_at: str


class TrackingEventResponse(BaseModel):
    id: str
    notification_id: str
    tracking_event_type_code: str
    channel_code: str
    click_url: str | None = None
    user_agent: str | None = None
    ip_address: str | None = None
    occurred_at: str
    created_at: str


class NotificationDetailResponse(BaseModel):
    """Full notification with delivery logs and tracking events."""
    notification: QueueItemAdminResponse
    delivery_logs: list[DeliveryLogResponse]
    tracking_events: list[TrackingEventResponse]


class DeliveryReportRow(BaseModel):
    notification_type_code: str
    channel_code: str
    status_code: str
    total_count: int
    hour_bucket: str


class DeliveryFunnelResponse(BaseModel):
    queued: int
    processing: int
    sent: int
    delivered: int
    opened: int
    clicked: int
    failed: int
    dead_letter: int
    suppressed: int
    delivery_rate: float
    open_rate: float
    click_rate: float


class DeliveryReportResponse(BaseModel):
    funnel: DeliveryFunnelResponse
    rows: list[DeliveryReportRow]
    period_hours: int


# ------------------------------------------------------------------ #
# Variable Queries
# ------------------------------------------------------------------ #


class BindParamDefinition(BaseModel):
    key: str = Field(..., min_length=1, max_length=50)
    position: int = Field(..., ge=1, le=20)
    source: str = Field(..., pattern=r"^(context|audit_property)$")
    required: bool = False
    default_value: str | None = None


class ResultColumnDefinition(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-z][a-z0-9_]*$")
    data_type: str = Field(default="string", pattern=r"^(string|integer|boolean|datetime)$")
    default_value: str | None = None


class CreateVariableQueryRequest(BaseModel):
    code: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-z][a-z0-9_]*$")
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=500)
    sql_template: str = Field(..., min_length=10)
    bind_params: list[BindParamDefinition] = Field(default_factory=list)
    result_columns: list[ResultColumnDefinition] = Field(..., min_length=1)
    timeout_ms: int = Field(default=3000, ge=100, le=10000)
    linked_event_type_codes: list[str] = Field(default_factory=list)


class UpdateVariableQueryRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=500)
    sql_template: str | None = Field(None, min_length=10)
    bind_params: list[BindParamDefinition] | None = None
    result_columns: list[ResultColumnDefinition] | None = None
    timeout_ms: int | None = Field(None, ge=100, le=10000)
    is_active: bool | None = None
    linked_event_type_codes: list[str] | None = None


class VariableQueryResponse(BaseModel):
    id: str
    tenant_key: str
    code: str
    name: str
    description: str | None = None
    sql_template: str
    bind_params: list[BindParamDefinition]
    result_columns: list[ResultColumnDefinition]
    timeout_ms: int
    is_active: bool
    is_system: bool = False
    variable_keys: list[str] = Field(default_factory=list)
    linked_event_type_codes: list[str] = Field(default_factory=list)
    created_at: str
    updated_at: str


class VariableQueryListResponse(BaseModel):
    items: list[VariableQueryResponse]
    total: int


# ── Schema metadata (for SQL editor autocomplete) ─────────────────────────


class ColumnMetadata(BaseModel):
    name: str
    data_type: str
    is_nullable: bool = True


class TableMetadata(BaseModel):
    schema_name: str
    table_name: str
    columns: list[ColumnMetadata]


class SchemaMetadataResponse(BaseModel):
    tables: list[TableMetadata]


# ── Audit event types (for context explorer) ───────────────────────────────


class AuditEventTypeInfo(BaseModel):
    entity_type: str
    event_type: str
    event_category: str
    event_count: int
    available_properties: list[str] = Field(default_factory=list)


class AuditEventTypesResponse(BaseModel):
    event_types: list[AuditEventTypeInfo]


class RecentAuditEventResponse(BaseModel):
    id: str
    entity_type: str
    entity_id: str
    event_type: str
    event_category: str
    actor_id: str | None = None
    occurred_at: str
    properties: dict[str, str] = Field(default_factory=dict)


class RecentAuditEventsResponse(BaseModel):
    events: list[RecentAuditEventResponse]


class TestQueryRequest(BaseModel):
    sql_template: str = Field(..., min_length=10)
    bind_params: list[BindParamDefinition] = Field(default_factory=list)
    param_values: dict[str, str] = Field(default_factory=dict)
    use_my_profile: bool = True


# ── Variable resolution for a real audit event ────────────────────────────


class ResolveVariablesForEventRequest(BaseModel):
    audit_event_id: str = Field(..., min_length=1)
    recipient_user_id: str | None = None  # defaults to caller's user_id
    template_id: str | None = None  # if set, only resolves that template's variables


class ResolveVariablesForEventResponse(BaseModel):
    resolved: dict[str, str] = Field(default_factory=dict)
    audit_event: RecentAuditEventResponse


# ── Trigger a real notification for an audit event ────────────────────────


class TriggerForAuditEventRequest(BaseModel):
    audit_event_id: str = Field(..., min_length=1)
    to_email: str | None = Field(None, max_length=254)  # override recipient email
    notification_type_code: str | None = None  # override notification type
    template_id: str | None = None  # override template
    bypass_preferences: bool = False
    dry_run: bool = False  # if True, render but do not send


class TriggerForAuditEventResponse(BaseModel):
    success: bool
    message: str
    rendered_subject: str | None = None
    rendered_body_html: str | None = None
    rendered_variables: dict[str, str] = Field(default_factory=dict)
    notification_id: str | None = None
    dry_run: bool = False


class PreviewQueryRequest(BaseModel):
    param_values: dict[str, str] = Field(default_factory=dict)
    use_my_profile: bool = True
    audit_event_id: str | None = None


class QueryPreviewResponse(BaseModel):
    success: bool
    columns: list[str] = Field(default_factory=list)
    rows: list[dict[str, str]] = Field(default_factory=list)
    resolved_params: dict[str, str] = Field(default_factory=dict)
    error: str | None = None
    execution_ms: int | None = None


# ------------------------------------------------------------------ #
# User notification inbox
# ------------------------------------------------------------------ #


class InboxNotificationItem(BaseModel):
    id: str
    notification_type_code: str
    category_code: str | None = None
    channel_code: str
    status_code: str
    priority_code: str
    rendered_subject: str | None = None
    rendered_body: str | None = None
    rendered_body_html: str | None = None
    is_read: bool
    read_at: str | None = None
    scheduled_at: str
    completed_at: str | None = None
    created_at: str


class InboxResponse(BaseModel):
    items: list[InboxNotificationItem]
    total: int
    unread_count: int


class MarkReadRequest(BaseModel):
    notification_ids: list[str] = Field(default_factory=list)  # empty = mark all


