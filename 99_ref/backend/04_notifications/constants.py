from __future__ import annotations

from enum import StrEnum


class NotificationChannel(StrEnum):
    EMAIL = "email"
    WEB_PUSH = "web_push"
    WHATSAPP = "whatsapp"
    SLACK = "slack"
    GCHAT = "gchat"


class NotificationCategory(StrEnum):
    SECURITY = "security"
    TRANSACTIONAL = "transactional"
    SYSTEM = "system"
    ORG = "org"
    WORKSPACE = "workspace"
    ENGAGEMENT = "engagement"


class NotificationType(StrEnum):
    PASSWORD_RESET = "password_reset"
    EMAIL_VERIFICATION = "email_verification"
    LOGIN_FROM_NEW_DEVICE = "login_from_new_device"
    API_KEY_CREATED = "api_key_created"
    PASSWORD_CHANGED = "password_changed"
    EMAIL_VERIFIED = "email_verified"
    ORG_INVITE_RECEIVED = "org_invite_received"
    ORG_MEMBER_ADDED = "org_member_added"
    ORG_MEMBER_REMOVED = "org_member_removed"
    ORG_BROADCAST = "org_broadcast"
    WORKSPACE_INVITE_RECEIVED = "workspace_invite_received"
    WORKSPACE_MEMBER_ADDED = "workspace_member_added"
    WORKSPACE_MEMBER_REMOVED = "workspace_member_removed"
    WORKSPACE_BROADCAST = "workspace_broadcast"
    GLOBAL_BROADCAST = "global_broadcast"
    ROLE_CHANGED = "role_changed"
    INACTIVITY_REMINDER = "inactivity_reminder"
    # Platform announcements
    PLATFORM_RELEASE = "platform_release"
    PLATFORM_INCIDENT = "platform_incident"
    PLATFORM_MAINTENANCE = "platform_maintenance"
    # Passwordless / magic link
    MAGIC_LINK_LOGIN = "magic_link_login"


class NotificationStatus(StrEnum):
    QUEUED = "queued"
    PROCESSING = "processing"
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    FAILED = "failed"
    BOUNCED = "bounced"
    SUPPRESSED = "suppressed"
    DEAD_LETTER = "dead_letter"


class NotificationPriority(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class RecipientStrategy(StrEnum):
    ACTOR = "actor"
    ENTITY_OWNER = "entity_owner"
    ORG_MEMBERS = "org_members"
    WORKSPACE_MEMBERS = "workspace_members"
    ALL_USERS = "all_users"
    SPECIFIC_USERS = "specific_users"


class PreferenceScopeLevel(StrEnum):
    GLOBAL = "global"
    CHANNEL = "channel"
    CATEGORY = "category"
    TYPE = "type"


class BroadcastScope(StrEnum):
    GLOBAL = "global"
    ORG = "org"
    WORKSPACE = "workspace"


class BroadcastSeverity(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ReleaseStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class IncidentStatus(StrEnum):
    INVESTIGATING = "investigating"
    IDENTIFIED = "identified"
    MONITORING = "monitoring"
    RESOLVED = "resolved"


class IncidentSeverity(StrEnum):
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"
    INFORMATIONAL = "informational"


class TrackingEventType(StrEnum):
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    BOUNCED = "bounced"
    FAILED = "failed"
    DISMISSED = "dismissed"
    UNSUBSCRIBED = "unsubscribed"


class RuleConditionType(StrEnum):
    PROPERTY_CHECK = "property_check"
    INACTIVITY = "inactivity"
    ENGAGEMENT = "engagement"
    SCHEDULE = "schedule"


class ConditionOperator(StrEnum):
    EQ = "eq"
    NEQ = "neq"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    IN = "in"
    NOT_IN = "not_in"
    CONTAINS = "contains"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"


class VariableResolutionSource(StrEnum):
    AUDIT_PROPERTY = "audit_property"
    USER_PROPERTY = "user_property"
    ACTOR_PROPERTY = "actor_property"
    USER_GROUP = "user_group"
    TENANT = "tenant"
    ORG = "org"
    WORKSPACE = "workspace"
    SETTINGS = "settings"
    COMPUTED = "computed"
    CUSTOM_QUERY = "custom_query"


NOTIFICATION_SCHEMA = "03_notifications"
