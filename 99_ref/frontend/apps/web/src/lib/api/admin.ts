import { fetchWithAuth, API_BASE_URL } from "./apiClient"
import type {
  AuditEventListResponse,
  BroadcastFullResponse,
  BulkInviteRequest,
  BulkInviteResponse,
  CampaignListResponse,
  CampaignResponse,
  CreateBroadcastRequest,
  CreateCampaignRequest,
  CreateFeatureFlagRequest,
  FeatureCategoryResponse,
  CreateGroupRequest,
  CreateIncidentRequest,
  CreateIncidentUpdateRequest,
  CreateReleaseRequest,
  CreateRoleRequest,
  CreateTemplateRequest,
  CreateTemplateVersionRequest,
  DeliveryReportResponse,
  FeatureEvaluation,
  NotificationDetailResponse,
  QueueActionResponse,
  FeatureFlagListResponse,
  FeatureFlagResponse,
  InvitationListResponse,
  InvitationResponse,
  LicenseProfileListResponse,
  LicenseProfileResponse,
  LicenseProfileSettingResponse,
  CreateLicenseProfileRequest,
  UpdateCampaignRequest,
  UpdateLicenseProfileRequest,
  OrgAvailableFlagsResponse,
  GroupChildListResponse,
  GroupListResponse,
  GroupMemberListResponse,
  GroupMemberResponse,
  GroupResponse,
  ImpersonationHistoryResponse,
  ImpersonationStatusResponse,
  IncidentFullResponse,
  InvitationStatsResponse,
  PreviewTemplateResponse,
  ReleaseFullResponse,
  RoleListResponse,
  RoleResponse,
  SendTestNotificationRequest,
  SendTestNotificationResponse,
  SessionListResponse,
  SettingKeyResponse,
  SettingResponse,
  SmtpConfigRequest,
  SmtpConfigResponse,
  SmtpTestRequest,
  SmtpTestResponse,
  StartImpersonationRequest,
  StartImpersonationResponse,
  TemplateDetailResponse,
  TemplateResponse,
  TemplateVersionResponse,
  UpdateFeatureFlagRequest,
  UpdateGroupRequest,
  UpdateIncidentRequest,
  UpdateReleaseRequest,
  UpdateRoleRequest,
  UpdateTemplateRequest,
  UserAuditEventListResponse,
  UserDetailResponse,
  UserDisableResponse,
  UserListResponse,
  PermissionActionListResponse,
  VariableQueryListResponse,
  VariableQueryResponse,
  CreateVariableQueryRequest,
  UpdateVariableQueryRequest,
  TestQueryRequest,
  PreviewQueryRequest,
  QueryPreviewResponse,
  TemplateVariableKeyResponse,
  CreateVariableKeyRequest,
  UpdateVariableKeyRequest,
} from "../types/admin"

// ── Feature Flags ─────────────────────────────────────────────────────────────

export async function listFeatureFlags(): Promise<FeatureFlagListResponse> {
  const res = await fetchWithAuth("/api/v1/am/features")
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list feature flags")
  return data as FeatureFlagListResponse
}

export async function createFeatureFlag(payload: CreateFeatureFlagRequest): Promise<FeatureFlagResponse> {
  const res = await fetchWithAuth("/api/v1/am/features", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || data.detail || "Failed to create feature flag")
  return data as FeatureFlagResponse
}

export async function updateFeatureFlag(code: string, payload: UpdateFeatureFlagRequest): Promise<FeatureFlagResponse> {
  const res = await fetchWithAuth(`/api/v1/am/features/${code}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to update feature flag")
  return data as FeatureFlagResponse
}

export async function createFeatureCategory(payload: { code: string; name: string; description: string; sort_order: number }): Promise<FeatureCategoryResponse> {
  const res = await fetchWithAuth("/api/v1/am/features/categories", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || data.detail || "Failed to create category")
  return data as FeatureCategoryResponse
}

export async function listOrgAvailableFlags(): Promise<OrgAvailableFlagsResponse> {
  const res = await fetchWithAuth("/api/v1/am/features/org-available")
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list org-available flags")
  return data as OrgAvailableFlagsResponse
}

export async function listPermissionActionTypes(): Promise<{ code: string; name: string; description: string; sort_order: number }[]> {
  const res = await fetchWithAuth("/api/v1/am/features/action-types")
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list action types")
  return data
}

export async function addPermissionToFlag(flagCode: string, actionCode: string): Promise<import("../types/admin").FeaturePermissionResponse> {
  const res = await fetchWithAuth(`/api/v1/am/features/${flagCode}/permissions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action_code: actionCode }),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || data.detail || "Failed to add permission")
  return data
}

export async function removePermissionFromFlag(flagCode: string, actionCode: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/am/features/${flagCode}/permissions/${actionCode}`, {
    method: "DELETE",
  })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.error?.message || "Failed to remove permission")
  }
}

// ── License Profiles ──────────────────────────────────────────────────────────

export async function listLicenseProfiles(): Promise<LicenseProfileListResponse> {
  const res = await fetchWithAuth("/api/v1/am/license-profiles")
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list license profiles")
  return data as LicenseProfileListResponse
}

export async function createLicenseProfile(payload: CreateLicenseProfileRequest): Promise<LicenseProfileResponse> {
  const res = await fetchWithAuth("/api/v1/am/license-profiles", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to create license profile")
  return data as LicenseProfileResponse
}

export async function updateLicenseProfile(code: string, payload: UpdateLicenseProfileRequest): Promise<LicenseProfileResponse> {
  const res = await fetchWithAuth(`/api/v1/am/license-profiles/${code}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to update license profile")
  return data as LicenseProfileResponse
}

export async function setLicenseProfileSetting(code: string, key: string, value: string): Promise<LicenseProfileSettingResponse> {
  const res = await fetchWithAuth(`/api/v1/am/license-profiles/${code}/settings/${key}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ value }),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to set profile setting")
  return data as LicenseProfileSettingResponse
}

export async function deleteLicenseProfileSetting(code: string, key: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/am/license-profiles/${code}/settings/${key}`, { method: "DELETE" })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.error?.message || "Failed to delete profile setting")
  }
}

// ── Roles ─────────────────────────────────────────────────────────────────────

export async function listRoles(params?: { scope_org_id?: string }): Promise<RoleListResponse> {
  const q = new URLSearchParams()
  if (params?.scope_org_id) q.set("scope_org_id", params.scope_org_id)
  const res = await fetchWithAuth(`/api/v1/am/roles${q.toString() ? `?${q}` : ""}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list roles")
  return data as RoleListResponse
}

export async function createRole(payload: CreateRoleRequest): Promise<RoleResponse> {
  const res = await fetchWithAuth("/api/v1/am/roles", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || data.detail || "Failed to create role")
  return data as RoleResponse
}

export async function updateRole(roleId: string, payload: UpdateRoleRequest): Promise<RoleResponse> {
  const res = await fetchWithAuth(`/api/v1/am/roles/${roleId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to update role")
  return data as RoleResponse
}

export async function assignPermissionToRole(roleId: string, featurePermissionId: string): Promise<RoleResponse> {
  const res = await fetchWithAuth(`/api/v1/am/roles/${roleId}/permissions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ feature_permission_id: featurePermissionId }),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to assign permission")
  return data as RoleResponse
}

export async function revokePermissionFromRole(roleId: string, permissionId: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/am/roles/${roleId}/permissions/${permissionId}`, { method: "DELETE" })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.error?.message || "Failed to revoke permission")
  }
}

export async function listGroupsUsingRole(roleId: string, params?: { scope_org_id?: string }): Promise<import("@/lib/types/admin").RoleGroupListResponse> {
  const q = new URLSearchParams()
  if (params?.scope_org_id) q.set("scope_org_id", params.scope_org_id)
  const res = await fetchWithAuth(`/api/v1/am/roles/${roleId}/groups${q.toString() ? `?${q}` : ""}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to fetch groups")
  return data as import("@/lib/types/admin").RoleGroupListResponse
}

export async function deleteRole(roleId: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/am/roles/${roleId}`, { method: "DELETE" })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.error?.message || "Failed to delete role")
  }
}

// ── Groups ────────────────────────────────────────────────────────────────────

export async function listGroups(params?: { scope_org_id?: string }): Promise<GroupListResponse> {
  const q = new URLSearchParams()
  if (params?.scope_org_id) q.set("scope_org_id", params.scope_org_id)
  const res = await fetchWithAuth(`/api/v1/am/groups${q.toString() ? `?${q}` : ""}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list groups")
  return data as GroupListResponse
}

export async function getGroup(groupId: string): Promise<GroupResponse> {
  const res = await fetchWithAuth(`/api/v1/am/groups/${groupId}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to fetch group")
  return data as GroupResponse
}

export async function createGroup(payload: CreateGroupRequest): Promise<GroupResponse> {
  const res = await fetchWithAuth("/api/v1/am/groups", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || data.detail || "Failed to create group")
  return data as GroupResponse
}

export async function updateGroup(groupId: string, payload: UpdateGroupRequest): Promise<GroupResponse> {
  const res = await fetchWithAuth(`/api/v1/am/groups/${groupId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to update group")
  return data as GroupResponse
}

export async function listGroupMembers(groupId: string, limit = 20, offset = 0): Promise<GroupMemberListResponse> {
  const res = await fetchWithAuth(`/api/v1/am/groups/${groupId}/members?limit=${limit}&offset=${offset}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list members")
  return data as GroupMemberListResponse
}

export async function listGroupChildren(groupId: string, limit = 20, offset = 0): Promise<GroupChildListResponse> {
  const res = await fetchWithAuth(`/api/v1/am/groups/${groupId}/children?limit=${limit}&offset=${offset}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list sub-groups")
  return data as GroupChildListResponse
}

export async function addGroupMember(groupId: string, userId: string): Promise<GroupResponse> {
  const res = await fetchWithAuth(`/api/v1/am/groups/${groupId}/members`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId }),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to add member")
  return data as GroupResponse
}

export async function removeGroupMember(groupId: string, userId: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/am/groups/${groupId}/members/${userId}`, { method: "DELETE" })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.error?.message || "Failed to remove member")
  }
}

export async function assignRoleToGroup(groupId: string, roleId: string): Promise<GroupResponse> {
  const res = await fetchWithAuth(`/api/v1/am/groups/${groupId}/roles`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ role_id: roleId }),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to assign role")
  return data as GroupResponse
}

export async function revokeRoleFromGroup(groupId: string, roleId: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/am/groups/${groupId}/roles/${roleId}`, { method: "DELETE" })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.error?.message || "Failed to revoke role")
  }
}

export async function setGroupParent(groupId: string, parentGroupId: string | null): Promise<GroupResponse> {
  const res = await fetchWithAuth(`/api/v1/am/groups/${groupId}/parent`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ parent_group_id: parentGroupId }),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to set parent group")
  return data as GroupResponse
}

export async function deleteGroup(groupId: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/am/groups/${groupId}`, { method: "DELETE" })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.error?.message || "Failed to delete group")
  }
}

// ── Admin Users ───────────────────────────────────────────────────────────────

export async function listAdminUsers(params?: {
  limit?: number
  offset?: number
  search?: string
  is_active?: boolean
  is_disabled?: boolean
  account_status?: string
  org_id?: string
  group_id?: string
  user_category?: string
}): Promise<UserListResponse> {
  const q = new URLSearchParams()
  if (params?.limit) q.set("limit", String(params.limit))
  if (params?.offset) q.set("offset", String(params.offset))
  if (params?.search) q.set("search", params.search)
  if (params?.is_active !== undefined) q.set("is_active", String(params.is_active))
  if (params?.is_disabled !== undefined) q.set("is_disabled", String(params.is_disabled))
  if (params?.account_status) q.set("account_status", params.account_status)
  if (params?.org_id) q.set("org_id", params.org_id)
  if (params?.group_id) q.set("group_id", params.group_id)
  if (params?.user_category) q.set("user_category", params.user_category)
  const res = await fetchWithAuth(`/api/v1/am/admin/users${q.toString() ? `?${q}` : ""}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list users")
  return data as UserListResponse
}

export async function getAdminUserDetail(userId: string): Promise<UserDetailResponse> {
  const res = await fetchWithAuth(`/api/v1/am/admin/users/${userId}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to get user detail")
  return data as UserDetailResponse
}

export async function listUserSessions(userId: string, includeRevoked = false): Promise<SessionListResponse> {
  const res = await fetchWithAuth(`/api/v1/am/admin/users/${userId}/sessions?include_revoked=${includeRevoked}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list sessions")
  return data as SessionListResponse
}

export async function revokeUserSession(userId: string, sessionId: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/am/admin/users/${userId}/sessions/${sessionId}`, { method: "DELETE" })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.error?.message || "Failed to revoke session")
  }
}

export async function disableUser(userId: string): Promise<UserDisableResponse> {
  const res = await fetchWithAuth(`/api/v1/am/admin/users/${userId}/disable`, { method: "PATCH" })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || data.detail || "Failed to disable user")
  return data as UserDisableResponse
}

export async function enableUser(userId: string): Promise<UserDisableResponse> {
  const res = await fetchWithAuth(`/api/v1/am/admin/users/${userId}/enable`, { method: "PATCH" })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || data.detail || "Failed to enable user")
  return data as UserDisableResponse
}

export async function deleteUser(userId: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/am/admin/users/${userId}`, { method: "DELETE" })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.error?.message || data.detail || "Failed to delete user")
  }
}

export async function getUserAuditEvents(
  userId: string,
  params?: { limit?: number; offset?: number },
): Promise<UserAuditEventListResponse> {
  const q = new URLSearchParams()
  if (params?.limit) q.set("limit", String(params.limit))
  if (params?.offset) q.set("offset", String(params.offset))
  const res = await fetchWithAuth(`/api/v1/am/admin/users/${userId}/audit${q.toString() ? `?${q}` : ""}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to get user audit events")
  return data as UserAuditEventListResponse
}

// ── Impersonation ─────────────────────────────────────────────────────────────

export async function startImpersonation(payload: StartImpersonationRequest): Promise<StartImpersonationResponse> {
  const res = await fetchWithAuth("/api/v1/am/impersonation/start", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || data.detail || "Failed to start impersonation")
  return data as StartImpersonationResponse
}

export async function endImpersonation(): Promise<void> {
  const res = await fetchWithAuth("/api/v1/am/impersonation/end", { method: "POST" })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.error?.message || "Failed to end impersonation")
  }
}

export async function getImpersonationStatus(): Promise<ImpersonationStatusResponse> {
  const res = await fetchWithAuth("/api/v1/am/impersonation/status")
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to get impersonation status")
  return data as ImpersonationStatusResponse
}

export async function listImpersonationHistory(params?: { limit?: number; offset?: number }): Promise<ImpersonationHistoryResponse> {
  const q = new URLSearchParams()
  if (params?.limit) q.set("limit", String(params.limit))
  if (params?.offset) q.set("offset", String(params.offset))
  const res = await fetchWithAuth(`/api/v1/am/admin/impersonation/history${q.toString() ? `?${q}` : ""}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list impersonation history")
  return data as ImpersonationHistoryResponse
}

// ── Audit ─────────────────────────────────────────────────────────────────────

export async function listAuditEvents(params?: {
  entity_type?: string
  entity_id?: string
  actor_id?: string
  event_type?: string
  limit?: number
  offset?: number
}): Promise<AuditEventListResponse> {
  const q = new URLSearchParams()
  if (params?.entity_type) q.set("entity_type", params.entity_type)
  if (params?.entity_id) q.set("entity_id", params.entity_id)
  if (params?.actor_id) q.set("actor_id", params.actor_id)
  if (params?.event_type) q.set("event_type", params.event_type)
  if (params?.limit) q.set("limit", String(params.limit))
  if (params?.offset) q.set("offset", String(params.offset))
  const res = await fetchWithAuth(`/api/v1/am/admin/audit${q.toString() ? `?${q}` : ""}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list audit events")
  return data as AuditEventListResponse
}

// ── Notifications ─────────────────────────────────────────────────────────────

export async function getNotificationConfig() {
  const res = await fetchWithAuth("/api/v1/notifications/config")
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to get notification config")
  return data
}

export async function listNotificationTemplates() {
  const res = await fetchWithAuth("/api/v1/notifications/templates")
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list templates")
  return data
}

export async function listBroadcasts(params?: { limit?: number; offset?: number }) {
  const q = new URLSearchParams()
  if (params?.limit) q.set("limit", String(params.limit))
  if (params?.offset) q.set("offset", String(params.offset))
  const res = await fetchWithAuth(`/api/v1/notifications/broadcasts${q.toString() ? `?${q}` : ""}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list broadcasts")
  return data
}

export async function listReleases(params?: { limit?: number; offset?: number; status?: string }) {
  const q = new URLSearchParams()
  if (params?.limit) q.set("limit", String(params.limit))
  if (params?.offset) q.set("offset", String(params.offset))
  if (params?.status) q.set("status", params.status)
  const res = await fetchWithAuth(`/api/v1/notifications/releases${q.toString() ? `?${q}` : ""}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list releases")
  return data
}

export async function listIncidents(params?: { limit?: number; offset?: number; status?: string }) {
  const q = new URLSearchParams()
  if (params?.limit) q.set("limit", String(params.limit))
  if (params?.offset) q.set("offset", String(params.offset))
  if (params?.status) q.set("status", params.status)
  const res = await fetchWithAuth(`/api/v1/notifications/incidents${q.toString() ? `?${q}` : ""}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list incidents")
  return data
}

export async function getNotificationQueue(params?: {
  status_code?: string
  channel_code?: string
  limit?: number
  offset?: number
}) {
  const q = new URLSearchParams()
  if (params?.status_code) q.set("status_code", params.status_code)
  if (params?.channel_code) q.set("channel_code", params.channel_code)
  if (params?.limit) q.set("limit", String(params.limit))
  if (params?.offset) q.set("offset", String(params.offset))
  const res = await fetchWithAuth(`/api/v1/notifications/queue${q.toString() ? `?${q}` : ""}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to get notification queue")
  return data
}

// ── Entity Settings ─────────────────────────────────────────────────────────

export async function getEntitySettings(entityType: string, entityId: string): Promise<SettingResponse[]> {
  const res = await fetchWithAuth(`/api/v1/am/settings/${entityType}/${entityId}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to get settings")
  return (data.settings ?? []) as SettingResponse[]
}

export async function getEntitySettingKeys(entityType: string, entityId: string): Promise<SettingKeyResponse[]> {
  const res = await fetchWithAuth(`/api/v1/am/settings/${entityType}/${entityId}/keys`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to get setting keys")
  return (data.keys ?? []) as SettingKeyResponse[]
}

export async function setEntitySetting(entityType: string, entityId: string, key: string, value: string): Promise<SettingResponse> {
  const res = await fetchWithAuth(`/api/v1/am/settings/${entityType}/${entityId}/${key}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ value }),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to set setting")
  return data as SettingResponse
}

export async function batchSetEntitySettings(entityType: string, entityId: string, settings: Record<string, string>): Promise<SettingResponse[]> {
  const res = await fetchWithAuth(`/api/v1/am/settings/${entityType}/${entityId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ settings }),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to save settings")
  return (data.settings ?? []) as SettingResponse[]
}

export async function deleteEntitySetting(entityType: string, entityId: string, key: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/am/settings/${entityType}/${entityId}/${key}`, { method: "DELETE" })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.error?.message || "Failed to delete setting")
  }
}

// ── Invitation Stats ────────────────────────────────────────────────────────

export async function getInvitationStats(): Promise<InvitationStatsResponse> {
  const res = await fetchWithAuth("/api/v1/am/invitations/stats")
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to get invitation stats")
  return data as InvitationStatsResponse
}

export async function getInvitationDetail(invitationId: string) {
  const res = await fetchWithAuth(`/api/v1/am/invitations/${invitationId}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to get invitation")
  return data
}

// ── Invitation Accept (public) ──────────────────────────────────────────────

export interface InvitationPreview {
  scope: string;
  org_name: string | null;
  workspace_name: string | null;
  grc_role_code: string | null;
  expires_at: string;
  status: string;
  email: string;
  user_exists: boolean;
}

export async function previewInvitation(token: string): Promise<InvitationPreview | null> {
  const res = await fetch(`${API_BASE_URL}/api/v1/am/invitations/preview?token=${encodeURIComponent(token)}`);
  if (res.status === 404 || res.status === 204) return null;
  if (!res.ok) return null;
  return res.json();
}

export interface AcceptInvitationResult {
  message: string;
  scope: string;
  org_id: string | null;
  workspace_id: string | null;
  role: string | null;
  grc_role_code: string | null;
}

export class InviteUserNotFoundError extends Error {
  constructor() {
    super("user_not_found");
    this.name = "InviteUserNotFoundError";
  }
}

/**
 * Public accept (no auth). If the invited email already has an account, the
 * backend assigns roles/groups immediately and returns the assignment context.
 * Throws InviteUserNotFoundError if no matching user exists — caller should
 * route to /register in that case.
 */
export async function acceptInvitationPublic(token: string): Promise<AcceptInvitationResult> {
  const res = await fetch(`${API_BASE_URL}/api/v1/am/invitations/accept-public`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ invite_token: token }),
  });
  if (res.status === 404) {
    let message: string | undefined;
    try {
      const data = await res.json();
      message = data?.error?.message || data?.detail;
    } catch { /* ignore */ }
    if (message === "user_not_found") throw new InviteUserNotFoundError();
    throw new Error(message || "Invitation not found");
  }
  if (!res.ok) {
    let message = `Accept failed: ${res.status}`;
    try {
      const data = await res.json();
      message = data?.error?.message || data?.detail || message;
    } catch { /* ignore */ }
    throw new Error(message);
  }
  return res.json();
}

export async function acceptInvitation(inviteToken: string) {
  const res = await fetchWithAuth("/api/v1/am/invitations/accept", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ invite_token: inviteToken }),
  })
  if (res.status === 401) throw new Error("401")
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || data.detail || "Failed to accept invitation")
  return data
}

export async function declineInvitation(inviteToken: string): Promise<InvitationResponse> {
  const res = await fetchWithAuth("/api/v1/am/invitations/decline", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ invite_token: inviteToken }),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || data.detail || "Failed to decline invitation")
  return data
}

// ── Feature Evaluation ──────────────────────────────────────────────────────

export async function evaluateMyFeatures(): Promise<FeatureEvaluation[]> {
  const res = await fetchWithAuth("/api/v1/am/admin/me/features")
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to evaluate features")
  return (data.features ?? []) as FeatureEvaluation[]
}

// ── Notification Template CRUD ──────────────────────────────────────────────

export async function createTemplate(payload: CreateTemplateRequest): Promise<TemplateResponse> {
  const res = await fetchWithAuth("/api/v1/notifications/templates", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || data.detail || "Failed to create template")
  return data as TemplateResponse
}

export async function getTemplateDetail(templateId: string): Promise<TemplateDetailResponse> {
  const res = await fetchWithAuth(`/api/v1/notifications/templates/${templateId}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to get template")
  return data as TemplateDetailResponse
}

export async function updateTemplate(templateId: string, payload: UpdateTemplateRequest): Promise<TemplateResponse> {
  const res = await fetchWithAuth(`/api/v1/notifications/templates/${templateId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to update template")
  return data as TemplateResponse
}

export async function createTemplateVersion(templateId: string, payload: CreateTemplateVersionRequest): Promise<TemplateVersionResponse> {
  const res = await fetchWithAuth(`/api/v1/notifications/templates/${templateId}/versions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to create version")
  return data as TemplateVersionResponse
}

export async function previewTemplate(templateId: string, variables: Record<string, string>): Promise<PreviewTemplateResponse> {
  const res = await fetchWithAuth(`/api/v1/notifications/templates/${templateId}/preview`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ variables }),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to preview template")
  return data as PreviewTemplateResponse
}

// ── Broadcast CRUD ──────────────────────────────────────────────────────────

export async function createBroadcast(payload: CreateBroadcastRequest): Promise<BroadcastFullResponse> {
  const res = await fetchWithAuth("/api/v1/notifications/broadcasts", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || data.detail || "Failed to create broadcast")
  return data as BroadcastFullResponse
}

export async function sendBroadcast(broadcastId: string): Promise<BroadcastFullResponse> {
  const res = await fetchWithAuth(`/api/v1/notifications/broadcasts/${broadcastId}/send`, { method: "POST" })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to send broadcast")
  return data as BroadcastFullResponse
}

// ── Release CRUD ────────────────────────────────────────────────────────────

export async function createRelease(payload: CreateReleaseRequest): Promise<ReleaseFullResponse> {
  const res = await fetchWithAuth("/api/v1/notifications/releases", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || data.detail || "Failed to create release")
  return data as ReleaseFullResponse
}

export async function getReleaseDetail(releaseId: string): Promise<ReleaseFullResponse> {
  const res = await fetchWithAuth(`/api/v1/notifications/releases/${releaseId}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to get release")
  return data as ReleaseFullResponse
}

export async function updateRelease(releaseId: string, payload: UpdateReleaseRequest): Promise<ReleaseFullResponse> {
  const res = await fetchWithAuth(`/api/v1/notifications/releases/${releaseId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to update release")
  return data as ReleaseFullResponse
}

export async function publishRelease(releaseId: string, notify = true): Promise<ReleaseFullResponse> {
  const res = await fetchWithAuth(`/api/v1/notifications/releases/${releaseId}/publish?notify=${notify}`, { method: "POST" })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to publish release")
  return data as ReleaseFullResponse
}

export async function archiveRelease(releaseId: string): Promise<ReleaseFullResponse> {
  const res = await fetchWithAuth(`/api/v1/notifications/releases/${releaseId}/archive`, { method: "POST" })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to archive release")
  return data as ReleaseFullResponse
}

// ── Incident CRUD ───────────────────────────────────────────────────────────

export async function createIncident(payload: CreateIncidentRequest): Promise<IncidentFullResponse> {
  const res = await fetchWithAuth("/api/v1/notifications/incidents", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || data.detail || "Failed to create incident")
  return data as IncidentFullResponse
}

export async function getIncidentDetail(incidentId: string): Promise<IncidentFullResponse> {
  const res = await fetchWithAuth(`/api/v1/notifications/incidents/${incidentId}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to get incident")
  return data as IncidentFullResponse
}

export async function updateIncident(incidentId: string, payload: UpdateIncidentRequest): Promise<IncidentFullResponse> {
  const res = await fetchWithAuth(`/api/v1/notifications/incidents/${incidentId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to update incident")
  return data as IncidentFullResponse
}

export async function postIncidentUpdate(incidentId: string, payload: CreateIncidentUpdateRequest): Promise<IncidentFullResponse> {
  const res = await fetchWithAuth(`/api/v1/notifications/incidents/${incidentId}/updates`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to post incident update")
  return data as IncidentFullResponse
}

// ── Notification Preference Delete ──────────────────────────────────────────

export async function deleteNotificationPreference(preferenceId: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/notifications/preferences/${preferenceId}`, { method: "DELETE" })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.error?.message || "Failed to delete preference")
  }
}

// ── Org / Workspace Types ───────────────────────────────────────────────────

export async function listOrgTypes() {
  const res = await fetchWithAuth("/api/v1/am/org-types")
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list org types")
  return data.items ?? data.types ?? []
}

export async function listWorkspaceTypes() {
  const res = await fetchWithAuth("/api/v1/am/workspace-types")
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list workspace types")
  return data.items ?? data.types ?? []
}

// ── Invite Campaigns ─────────────────────────────────────────────────────────

export async function listCampaigns(params?: { status?: string; page?: number; page_size?: number }): Promise<CampaignListResponse> {
  const q = new URLSearchParams()
  if (params?.status) q.set("status", params.status)
  if (params?.page) q.set("page", String(params.page))
  if (params?.page_size) q.set("page_size", String(params.page_size))
  const res = await fetchWithAuth(`/api/v1/am/campaigns${q.toString() ? `?${q}` : ""}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list campaigns")
  return data as CampaignListResponse
}

export async function createCampaign(payload: CreateCampaignRequest): Promise<CampaignResponse> {
  const res = await fetchWithAuth("/api/v1/am/campaigns", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || data.detail || "Failed to create campaign")
  return data as CampaignResponse
}

export async function getCampaign(campaignId: string): Promise<CampaignResponse> {
  const res = await fetchWithAuth(`/api/v1/am/campaigns/${campaignId}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to get campaign")
  return data as CampaignResponse
}

export async function updateCampaign(campaignId: string, payload: UpdateCampaignRequest): Promise<CampaignResponse> {
  const res = await fetchWithAuth(`/api/v1/am/campaigns/${campaignId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to update campaign")
  return data as CampaignResponse
}

export async function bulkInviteCampaign(campaignId: string, payload: BulkInviteRequest): Promise<BulkInviteResponse> {
  const res = await fetchWithAuth(`/api/v1/am/campaigns/${campaignId}/bulk-invite`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to bulk invite")
  return data as BulkInviteResponse
}

export async function listCampaignInvitations(campaignId: string, params?: { page?: number; page_size?: number }): Promise<InvitationListResponse> {
  const q = new URLSearchParams()
  if (params?.page) q.set("page", String(params.page))
  if (params?.page_size) q.set("page_size", String(params.page_size))
  const res = await fetchWithAuth(`/api/v1/am/campaigns/${campaignId}/invitations${q.toString() ? `?${q}` : ""}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list campaign invitations")
  return data as InvitationListResponse
}

export async function bulkCreateInvitations(payload: BulkInviteRequest): Promise<BulkInviteResponse> {
  const res = await fetchWithAuth("/api/v1/am/invitations/bulk", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to send invitations")
  return data as BulkInviteResponse
}

export async function listInvitations(params?: { scope?: string; status?: string; email?: string; page?: number; page_size?: number }): Promise<InvitationListResponse> {
  const q = new URLSearchParams()
  if (params?.scope) q.set("scope", params.scope)
  if (params?.status) q.set("status", params.status)
  if (params?.email) q.set("email", params.email)
  if (params?.page) q.set("page", String(params.page))
  if (params?.page_size) q.set("page_size", String(params.page_size))
  const res = await fetchWithAuth(`/api/v1/am/invitations${q.toString() ? `?${q}` : ""}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list invitations")
  return data as InvitationListResponse
}

export async function revokeInvitation(invitationId: string): Promise<InvitationResponse> {
  const res = await fetchWithAuth(`/api/v1/am/invitations/${invitationId}/revoke`, { method: "PATCH" })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to revoke invitation")
  return data as InvitationResponse
}

export async function resendInvitation(invitationId: string): Promise<InvitationResponse> {
  const res = await fetchWithAuth(`/api/v1/am/invitations/${invitationId}/resend`, { method: "POST" })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to resend invitation")
  return data as InvitationResponse
}

// ── SMTP Config ──────────────────────────────────────────────────────────────

export async function getSmtpConfig(): Promise<SmtpConfigResponse> {
  const res = await fetchWithAuth("/api/v1/notifications/smtp/config")
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to get SMTP config")
  return data as SmtpConfigResponse
}

export async function saveSmtpConfig(payload: SmtpConfigRequest): Promise<SmtpConfigResponse> {
  const res = await fetchWithAuth("/api/v1/notifications/smtp/config", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to save SMTP config")
  return data as SmtpConfigResponse
}

export async function testSmtp(payload: SmtpTestRequest): Promise<SmtpTestResponse> {
  const res = await fetchWithAuth("/api/v1/notifications/smtp/test", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to test SMTP")
  return data as SmtpTestResponse
}

// ── Send Test Notification ────────────────────────────────────────────────────

export async function sendTestNotification(payload: SendTestNotificationRequest): Promise<SendTestNotificationResponse> {
  const res = await fetchWithAuth("/api/v1/notifications/send-test", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to send test notification")
  return data as SendTestNotificationResponse
}

// ── Delivery Reports ─────────────────────────────────────────────────────────

export async function getDeliveryReport(params?: { period_hours?: number }): Promise<DeliveryReportResponse> {
  const q = new URLSearchParams()
  if (params?.period_hours) q.set("period_hours", String(params.period_hours))
  const res = await fetchWithAuth(`/api/v1/notifications/reports/delivery${q.toString() ? `?${q}` : ""}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to get delivery report")
  return data as DeliveryReportResponse
}

// ── Queue Management ─────────────────────────────────────────────────────────

export async function getNotificationDetail(notificationId: string): Promise<NotificationDetailResponse> {
  const res = await fetchWithAuth(`/api/v1/notifications/queue/${notificationId}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to get notification detail")
  return data as NotificationDetailResponse
}

export async function retryQueueItem(notificationId: string): Promise<QueueActionResponse> {
  const res = await fetchWithAuth(`/api/v1/notifications/queue/${notificationId}/retry`, { method: "POST" })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to retry notification")
  return data as QueueActionResponse
}

export async function deadLetterQueueItem(notificationId: string, reason?: string): Promise<QueueActionResponse> {
  const res = await fetchWithAuth(`/api/v1/notifications/queue/${notificationId}/dead-letter`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ reason: reason || null }),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to dead-letter notification")
  return data as QueueActionResponse
}

// ── Raw template render (for announcements inline editor) ─────────────────────

export interface RenderRawRequest {
  subject_line?: string | null
  body_html?: string | null
  body_text?: string | null
  variables?: Record<string, string>
}

export async function renderRaw(body: RenderRawRequest): Promise<PreviewTemplateResponse> {
  const res = await fetchWithAuth("/api/v1/notifications/templates/render-raw", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to render template")
  return data as PreviewTemplateResponse
}

// ── Notification Rules (/api/v1/notifications/rules) ──────────────────────

export async function listNotificationRules(): Promise<unknown> {
  const res = await fetchWithAuth("/api/v1/notifications/rules")
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list rules")
  return data
}

export async function createRule(payload: Record<string, unknown>): Promise<unknown> {
  const res = await fetchWithAuth("/api/v1/notifications/rules", {
    method: "POST",
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to create rule")
  return data
}

export async function getRuleDetail(ruleId: string): Promise<Record<string, unknown>> {
  const res = await fetchWithAuth(`/api/v1/notifications/rules/${ruleId}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to get rule detail")
  return data as Record<string, unknown>
}

export async function updateRule(ruleId: string, payload: Record<string, unknown>): Promise<unknown> {
  const res = await fetchWithAuth(`/api/v1/notifications/rules/${ruleId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to update rule")
  return data
}

export async function setRuleChannel(ruleId: string, channelCode: string, payload: Record<string, unknown>): Promise<unknown> {
  const res = await fetchWithAuth(`/api/v1/notifications/rules/${ruleId}/channels/${channelCode}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to set rule channel")
  return data
}

export async function addRuleCondition(ruleId: string, payload: Record<string, unknown>): Promise<unknown> {
  const res = await fetchWithAuth(`/api/v1/notifications/rules/${ruleId}/conditions`, {
    method: "POST",
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to add condition")
  return data
}

export async function removeRuleCondition(ruleId: string, conditionId: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/notifications/rules/${ruleId}/conditions/${conditionId}`, {
    method: "DELETE",
  })
  if (!res.ok) {
    const data = await res.json()
    throw new Error(data.error?.message || "Failed to remove condition")
  }
}

// ── Variable Queries (/api/v1/notifications/variable-queries) ─────────────

export async function listVariableQueries(): Promise<VariableQueryListResponse> {
  const res = await fetchWithAuth("/api/v1/notifications/variable-queries")
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list variable queries")
  return data
}

export async function createVariableQuery(payload: CreateVariableQueryRequest): Promise<VariableQueryResponse> {
  const res = await fetchWithAuth("/api/v1/notifications/variable-queries", {
    method: "POST",
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to create variable query")
  return data
}

export async function updateVariableQuery(id: string, payload: UpdateVariableQueryRequest): Promise<VariableQueryResponse> {
  const res = await fetchWithAuth(`/api/v1/notifications/variable-queries/${id}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to update variable query")
  return data
}

export async function deleteVariableQuery(id: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/notifications/variable-queries/${id}`, {
    method: "DELETE",
  })
  if (!res.ok) {
    const data = await res.json()
    throw new Error(data.error?.message || "Failed to delete variable query")
  }
}

export async function previewVariableQuery(id: string, payload: PreviewQueryRequest): Promise<QueryPreviewResponse> {
  const res = await fetchWithAuth(`/api/v1/notifications/variable-queries/${id}/preview`, {
    method: "POST",
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to preview variable query")
  return data
}

export async function testVariableQuery(payload: TestQueryRequest): Promise<QueryPreviewResponse> {
  const res = await fetchWithAuth("/api/v1/notifications/variable-queries/test", {
    method: "POST",
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to test variable query")
  return data
}

// ── Schema metadata + audit context ─────────────────────────────────────────

export async function fetchSchemaMetadata(): Promise<import("@/lib/types/admin").SchemaMetadataResponse> {
  const res = await fetchWithAuth("/api/v1/notifications/variable-queries/schema")
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to fetch schema metadata")
  return data
}

export async function fetchAuditEventTypes(): Promise<import("@/lib/types/admin").AuditEventTypesResponse> {
  const res = await fetchWithAuth("/api/v1/notifications/variable-queries/audit-event-types")
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to fetch audit event types")
  return data
}

export async function fetchRecentAuditEvents(eventType?: string): Promise<import("@/lib/types/admin").RecentAuditEventsResponse> {
  const params = new URLSearchParams()
  if (eventType) params.set("event_type", eventType)
  const url = `/api/v1/notifications/variable-queries/recent-events${params.toString() ? `?${params}` : ""}`
  const res = await fetchWithAuth(url)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to fetch recent audit events")
  return data
}

// ── Variable Keys (/api/v1/notifications/variable-keys) ──────────────────────

export async function listVariableKeys(): Promise<TemplateVariableKeyResponse[]> {
  const res = await fetchWithAuth("/api/v1/notifications/variable-keys")
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list variable keys")
  return data
}

export async function createVariableKey(payload: CreateVariableKeyRequest): Promise<TemplateVariableKeyResponse> {
  const res = await fetchWithAuth("/api/v1/notifications/variable-keys", {
    method: "POST",
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to create variable key")
  return data
}

export async function updateVariableKey(code: string, payload: UpdateVariableKeyRequest): Promise<TemplateVariableKeyResponse> {
  const res = await fetchWithAuth(`/api/v1/notifications/variable-keys/${code}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to update variable key")
  return data
}

export async function deleteVariableKey(code: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/notifications/variable-keys/${code}`, {
    method: "DELETE",
  })
  if (!res.ok && res.status !== 204) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.error?.message || "Failed to delete variable key")
  }
}
