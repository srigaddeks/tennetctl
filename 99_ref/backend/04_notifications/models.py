from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class TemplateRecord:
    id: str
    tenant_key: str
    code: str
    name: str
    description: str
    notification_type_code: str
    channel_code: str
    category_code: str | None
    active_version_id: str | None
    base_template_id: str | None
    org_id: str | None
    static_variables: dict  # Template-level default variable values
    is_active: bool
    is_disabled: bool
    is_deleted: bool
    is_system: bool
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class TemplateVersionRecord:
    id: str
    template_id: str
    version_number: int
    subject_line: str | None
    body_html: str | None
    body_text: str | None
    body_short: str | None
    metadata_json: str | None
    change_notes: str | None
    is_active: bool
    created_at: datetime


@dataclass(frozen=True, slots=True)
class TemplatePlaceholderRecord:
    id: str
    template_id: str
    variable_key_code: str
    is_required: bool
    default_value: str | None


@dataclass(frozen=True, slots=True)
class NotificationRuleRecord:
    id: str
    tenant_key: str
    code: str
    name: str
    description: str
    source_event_type: str
    source_event_category: str | None
    notification_type_code: str
    recipient_strategy: str
    recipient_filter_json: str | None
    priority_code: str
    delay_seconds: int
    is_active: bool
    is_disabled: bool
    is_deleted: bool
    is_system: bool
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class NotificationQueueRecord:
    id: str
    tenant_key: str
    user_id: str
    notification_type_code: str
    channel_code: str
    status_code: str
    priority_code: str
    template_id: str | None
    template_version_id: str | None
    source_audit_event_id: str | None
    source_rule_id: str | None
    broadcast_id: str | None
    rendered_subject: str | None
    rendered_body: str | None
    rendered_body_html: str | None
    recipient_email: str | None
    recipient_push_endpoint: str | None
    scheduled_at: datetime
    attempt_count: int
    max_attempts: int
    next_retry_at: datetime | None
    last_error: str | None
    idempotency_key: str | None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None


@dataclass(frozen=True, slots=True)
class DeliveryLogRecord:
    id: str
    notification_id: str
    channel_code: str
    attempt_number: int
    status: str
    provider_response: str | None
    provider_message_id: str | None
    error_code: str | None
    error_message: str | None
    duration_ms: int | None
    occurred_at: datetime
    created_at: datetime


@dataclass(frozen=True, slots=True)
class TrackingEventRecord:
    id: str
    notification_id: str
    tracking_event_type_code: str
    channel_code: str
    click_url: str | None
    user_agent: str | None
    ip_address: str | None
    occurred_at: datetime
    created_at: datetime


@dataclass(frozen=True, slots=True)
class WebPushSubscriptionRecord:
    id: str
    user_id: str
    tenant_key: str
    endpoint: str
    p256dh_key: str
    auth_key: str
    user_agent: str | None
    is_active: bool
    last_used_at: datetime | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class UserNotificationPreferenceRecord:
    id: str
    user_id: str
    tenant_key: str
    scope_level: str
    channel_code: str | None
    category_code: str | None
    notification_type_code: str | None
    scope_org_id: str | None
    scope_workspace_id: str | None
    is_enabled: bool
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class BroadcastRecord:
    id: str
    tenant_key: str
    title: str
    body_text: str
    body_html: str | None
    scope: str
    scope_org_id: str | None
    scope_workspace_id: str | None
    notification_type_code: str
    priority_code: str
    severity: str | None
    is_critical: bool
    template_code: str | None
    static_variables: dict[str, str] | None
    scheduled_at: datetime | None
    sent_at: datetime | None
    total_recipients: int | None
    is_active: bool
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    created_by: str


@dataclass(frozen=True, slots=True)
class ReleaseRecord:
    id: str
    tenant_key: str
    version: str
    title: str
    summary: str
    body_markdown: str | None
    body_html: str | None
    changelog_url: str | None
    status: str
    release_date: str | None
    published_at: str | None
    broadcast_id: str | None
    is_active: bool
    is_deleted: bool
    created_at: str
    updated_at: str
    created_by: str


@dataclass(frozen=True, slots=True)
class IncidentRecord:
    id: str
    tenant_key: str
    title: str
    description: str
    severity: str
    status: str
    affected_components: str | None
    started_at: str
    resolved_at: str | None
    broadcast_id: str | None
    is_active: bool
    is_deleted: bool
    created_at: str
    updated_at: str
    created_by: str


@dataclass(frozen=True, slots=True)
class IncidentUpdateRecord:
    id: str
    incident_id: str
    status: str
    message: str
    is_public: bool
    broadcast_id: str | None
    created_at: str
    created_by: str


@dataclass(frozen=True, slots=True)
class NotificationChannelRecord:
    id: str
    code: str
    name: str
    description: str
    is_available: bool
    sort_order: int


@dataclass(frozen=True, slots=True)
class NotificationCategoryRecord:
    id: str
    code: str
    name: str
    description: str
    is_mandatory: bool
    sort_order: int


@dataclass(frozen=True, slots=True)
class NotificationTypeRecord:
    id: str
    code: str
    name: str
    description: str
    category_code: str
    is_mandatory: bool
    is_user_triggered: bool
    default_enabled: bool
    cooldown_seconds: int | None
    sort_order: int


@dataclass(frozen=True, slots=True)
class RuleChannelRecord:
    id: str
    rule_id: str
    channel_code: str
    template_code: str | None
    is_active: bool


@dataclass(frozen=True, slots=True)
class RuleConditionRecord:
    id: str
    rule_id: str
    condition_type: str
    field_key: str
    operator: str
    value: str | None
    value_type: str
    logical_group: int
    sort_order: int
    is_active: bool
    created_at: str
    updated_at: str


@dataclass(frozen=True, slots=True)
class CampaignRunRecord:
    id: str
    tenant_key: str
    rule_id: str
    run_type: str
    started_at: str
    completed_at: str | None
    users_evaluated: int
    users_matched: int
    notifications_created: int
    status: str
    error_message: str | None
    created_at: str


@dataclass(frozen=True, slots=True)
class VariableQueryRecord:
    id: str
    tenant_key: str
    code: str
    name: str
    description: str | None
    sql_template: str
    bind_params: str      # JSONB as string
    result_columns: str   # JSONB as string
    timeout_ms: int
    is_active: bool
    is_deleted: bool
    is_system: bool
    linked_event_type_codes: list[str]  # event types this query supports
    created_at: str
    updated_at: str
    created_by: str | None
