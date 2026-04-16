from __future__ import annotations

from pydantic import BaseModel


class UserSummaryResponse(BaseModel):
    user_id: str
    tenant_key: str
    email: str | None
    username: str | None
    display_name: str | None = None
    account_status: str
    user_category: str = "full"
    is_active: bool
    is_disabled: bool
    is_locked: bool = False
    is_system: bool = False
    is_test: bool = False
    created_at: str


class UserListResponse(BaseModel):
    users: list[UserSummaryResponse]
    total: int


class SessionResponse(BaseModel):
    session_id: str
    user_id: str
    client_ip: str | None
    user_agent: str | None
    is_impersonation: bool
    created_at: str
    revoked_at: str | None


class SessionListResponse(BaseModel):
    sessions: list[SessionResponse]


class AuditEventResponse(BaseModel):
    id: str
    tenant_key: str
    entity_type: str
    entity_id: str
    event_type: str
    event_category: str
    actor_id: str | None
    actor_type: str | None
    ip_address: str | None
    session_id: str | None
    occurred_at: str
    properties: dict[str, str | None]


class AuditEventListResponse(BaseModel):
    events: list[AuditEventResponse]
    total: int


class ImpersonationSessionResponse(BaseModel):
    session_id: str
    target_user_id: str
    impersonator_user_id: str
    reason: str | None
    created_at: str
    revoked_at: str | None
    target_email: str | None = None
    impersonator_email: str | None = None


class ImpersonationHistoryResponse(BaseModel):
    sessions: list[ImpersonationSessionResponse]


class UserPropertyResponse(BaseModel):
    key: str
    value: str


class UserOrgMembershipResponse(BaseModel):
    org_id: str
    org_name: str
    org_type: str
    role: str
    is_active: bool
    joined_at: str


class UserWorkspaceMembershipResponse(BaseModel):
    workspace_id: str
    workspace_name: str
    workspace_type: str
    org_id: str
    org_name: str
    role: str
    is_active: bool
    joined_at: str


class UserGroupMembershipResponse(BaseModel):
    group_id: str
    group_name: str
    group_code: str
    role_level_code: str
    scope_org_id: str | None = None
    scope_workspace_id: str | None = None
    is_system: bool = False
    is_active: bool
    joined_at: str


class UserDetailResponse(BaseModel):
    user_id: str
    tenant_key: str
    email: str | None
    username: str | None
    account_status: str
    is_active: bool
    is_disabled: bool
    created_at: str
    properties: list[UserPropertyResponse]
    org_memberships: list[UserOrgMembershipResponse]
    workspace_memberships: list[UserWorkspaceMembershipResponse]
    group_memberships: list[UserGroupMembershipResponse]


class UserDisableResponse(BaseModel):
    user_id: str
    is_disabled: bool


class UserAuditEventListResponse(BaseModel):
    events: list[AuditEventResponse]
    total: int


class FeatureEvaluation(BaseModel):
    code: str
    name: str
    enabled: bool
    permissions: list[str]


class FeatureEvaluationResponse(BaseModel):
    features: list[FeatureEvaluation]
