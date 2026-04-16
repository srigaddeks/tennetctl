from __future__ import annotations

from enum import StrEnum


class AccountType(StrEnum):
    LOCAL_PASSWORD = "local_password"
    GOOGLE = "google"
    GITHUB = "github"
    MICROSOFT = "microsoft"
    SAML = "saml"
    API_KEY = "api_key"
    MAGIC_LINK = "magic_link"


class ChallengeType(StrEnum):
    PASSWORD_RESET = "password_reset"
    EMAIL_VERIFICATION = "email_verification"
    MAGIC_LINK = "magic_link"
    MAGIC_LINK_ASSIGNEE = "magic_link_assignee"


class AuditEventType(StrEnum):
    REGISTERED = "registered"
    LOGIN_SUCCEEDED = "login_succeeded"
    LOGIN_FAILED = "login_failed"
    REFRESH_SUCCEEDED = "refresh_succeeded"
    REFRESH_REPLAY_DETECTED = "refresh_replay_detected"
    LOGOUT_SUCCEEDED = "logout_succeeded"
    PASSWORD_RESET_REQUESTED = "password_reset_requested"
    PASSWORD_RESET_COMPLETED = "password_reset_completed"
    EMAIL_VERIFICATION_REQUESTED = "email_verification_requested"
    EMAIL_VERIFICATION_COMPLETED = "email_verification_completed"
    PROPERTY_CHANGED = "property_changed"
    PROPERTY_REMOVED = "property_removed"
    ACCOUNT_LINKED = "account_linked"
    ACCOUNT_UNLINKED = "account_unlinked"
    # Feature flags
    FEATURE_FLAG_CREATED = "feature_flag_created"
    FEATURE_FLAG_UPDATED = "feature_flag_updated"
    # Roles
    ROLE_CREATED = "role_created"
    ROLE_UPDATED = "role_updated"
    ROLE_PERMISSION_ASSIGNED = "role_permission_assigned"
    ROLE_PERMISSION_REVOKED = "role_permission_revoked"
    # User groups
    GROUP_CREATED = "group_created"
    GROUP_UPDATED = "group_updated"
    GROUP_MEMBER_ADDED = "group_member_added"
    GROUP_MEMBER_REMOVED = "group_member_removed"
    GROUP_ROLE_ASSIGNED = "group_role_assigned"
    GROUP_ROLE_REVOKED = "group_role_revoked"
    # Orgs
    ORG_CREATED = "org_created"
    ORG_UPDATED = "org_updated"
    ORG_MEMBER_ADDED = "org_member_added"
    ORG_MEMBER_REMOVED = "org_member_removed"
    ORG_MEMBER_ROLE_CHANGED = "org_member_role_changed"
    # Workspaces
    WORKSPACE_CREATED = "workspace_created"
    WORKSPACE_UPDATED = "workspace_updated"
    WORKSPACE_MEMBER_ADDED = "workspace_member_added"
    WORKSPACE_MEMBER_REMOVED = "workspace_member_removed"
    WORKSPACE_MEMBER_UPDATED = "workspace_member_updated"
    # Magic link (passwordless)
    MAGIC_LINK_REQUESTED = "magic_link_requested"
    MAGIC_LINK_VERIFIED = "magic_link_verified"
    MAGIC_LINK_EXTERNAL_USER_CREATED = "magic_link_external_user_created"
    # Invitations
    INVITE_CREATED = "invite_created"
    INVITE_ACCEPTED = "invite_accepted"
    INVITE_REVOKED = "invite_revoked"
    INVITE_EXPIRED = "invite_expired"
    INVITE_DECLINED = "invite_declined"
    # Password change
    PASSWORD_CHANGED = "password_changed"
    # Impersonation
    IMPERSONATION_STARTED = "impersonation_started"
    IMPERSONATION_ENDED = "impersonation_ended"
    # Admin
    SESSION_REVOKED_BY_ADMIN = "session_revoked_by_admin"
    USER_DISABLED = "user_disabled"
    USER_ENABLED = "user_enabled"
    # API keys
    API_KEY_CREATED = "api_key_created"
    API_KEY_ROTATED = "api_key_rotated"
    API_KEY_REVOKED = "api_key_revoked"
    API_KEY_DELETED = "api_key_deleted"
    API_KEY_USED = "api_key_used"
    # Notifications
    NOTIFICATION_QUEUED = "notification_queued"
    NOTIFICATION_SENT = "notification_sent"
    NOTIFICATION_DELIVERED = "notification_delivered"
    NOTIFICATION_FAILED = "notification_failed"
    NOTIFICATION_OPENED = "notification_opened"
    NOTIFICATION_CLICKED = "notification_clicked"
    NOTIFICATION_BOUNCED = "notification_bounced"
    NOTIFICATION_PREFERENCE_CHANGED = "notification_preference_changed"
    TEMPLATE_CREATED = "template_created"
    TEMPLATE_VERSION_CREATED = "template_version_created"
    TEMPLATE_ACTIVATED = "template_activated"
    BROADCAST_CREATED = "broadcast_created"
    BROADCAST_SENT = "broadcast_sent"
    NOTIFICATION_RULE_CREATED = "notification_rule_created"
    NOTIFICATION_RULE_UPDATED = "notification_rule_updated"
    WEB_PUSH_SUBSCRIBED = "web_push_subscribed"
    WEB_PUSH_UNSUBSCRIBED = "web_push_unsubscribed"


class AuditEventCategory(StrEnum):
    AUTH = "auth"
    ACCESS = "access"
    PRODUCT = "product"
    ORG = "org"
    WORKSPACE = "workspace"
    SYSTEM = "system"
    NOTIFICATION = "notification"
    FRAMEWORK = "framework"
    RISK = "risk"
    TASK = "task"
    COMMENT = "comment"
    ATTACHMENT = "attachment"


ACCESS_TOKEN_TYPE = "access"
BEARER_TOKEN_TYPE = "Bearer"
