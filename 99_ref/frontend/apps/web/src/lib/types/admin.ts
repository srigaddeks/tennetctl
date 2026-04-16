// ── Feature Flags ────────────────────────────────────────────────────────────

export interface FeatureCategoryResponse {
  id: string
  code: string
  name: string
  description: string
  sort_order: number
}

export interface FeaturePermissionResponse {
  id: string
  code: string
  feature_flag_code: string
  permission_action_code: string
  name: string
  description: string
}

export interface FeatureFlagResponse {
  id: string
  code: string
  name: string
  description: string
  category_code: string
  feature_scope: "platform" | "org" | "product" | string
  access_mode: string
  lifecycle_state: string
  initial_audience: string
  env_dev: boolean
  env_staging: boolean
  env_prod: boolean
  org_visibility: string | null  // "hidden" | "locked" | "unlocked" — only for org-scoped flags
  required_license: string | null  // "free" | "pro" | "internal" — if set
  permissions: FeaturePermissionResponse[]
  created_at: string
  updated_at: string
}

export interface FeatureFlagListResponse {
  categories: FeatureCategoryResponse[]
  flags: FeatureFlagResponse[]
}

export interface OrgAvailableFlagResponse {
  id: string
  code: string
  name: string
  description: string
  category_code: string
  feature_scope: string
  lifecycle_state: string
  env_dev: boolean
  env_staging: boolean
  env_prod: boolean
  org_visibility: "locked" | "unlocked"
  required_license: string | null
  permissions: FeaturePermissionResponse[]
}

export interface OrgAvailableFlagsResponse {
  categories: FeatureCategoryResponse[]
  flags: OrgAvailableFlagResponse[]
}


export interface PermissionActionResponse {
  id: string
  code: string
  name: string
  description: string
  sort_order: number
}

export interface PermissionActionListResponse {
  actions: PermissionActionResponse[]
}

export interface CreateFeaturePermissionRequest {
  permission_action_code: string
  name: string
  description: string
}

export interface CreateFeatureFlagRequest {
  code: string
  name: string
  description: string
  category_code: string
  feature_scope?: string
  access_mode: "public" | "authenticated" | "permissioned" | string
  lifecycle_state?: string
  initial_audience?: string
  env_dev?: boolean
  env_staging?: boolean
  env_prod?: boolean
  permissions?: string[]
}

export interface UpdateFeatureFlagRequest {
  name?: string
  description?: string
  category_code?: string
  feature_scope?: string
  access_mode?: string
  lifecycle_state?: string
  env_dev?: boolean
  env_staging?: boolean
  env_prod?: boolean
  permissions?: CreateFeaturePermissionRequest[]
}

// ── License Profiles ─────────────────────────────────────────────────────────

export interface LicenseProfileSettingResponse {
  key: string
  value: string
}

export interface LicenseProfileResponse {
  id: string
  code: string
  name: string
  description: string
  tier: string
  is_active: boolean
  sort_order: number
  settings: LicenseProfileSettingResponse[]
  org_count: number
  created_at: string
  updated_at: string
}

export interface LicenseProfileListResponse {
  profiles: LicenseProfileResponse[]
}

export interface CreateLicenseProfileRequest {
  code: string
  name: string
  description?: string
  tier?: string
  sort_order?: number
}

export interface UpdateLicenseProfileRequest {
  name?: string
  description?: string
  tier?: string
  is_active?: boolean
  sort_order?: number
}

// ── Roles ────────────────────────────────────────────────────────────────────

export interface RoleLevelResponse {
  id: string
  code: string
  name: string
  description: string
  sort_order: number
}

export interface RolePermissionResponse {
  id: string
  feature_permission_id: string
  feature_permission_code: string
  feature_flag_code: string
  permission_action_code: string
  permission_name: string
}

export interface RoleResponse {
  id: string
  code: string
  name: string
  description: string
  role_level_code: string
  tenant_key: string
  scope_org_id: string | null
  scope_workspace_id: string | null
  is_active: boolean
  is_disabled: boolean
  is_system: boolean
  permissions: RolePermissionResponse[]
  created_at: string
  updated_at: string
}

export interface RoleListResponse {
  levels: RoleLevelResponse[]
  roles: RoleResponse[]
}

export interface RoleGroupResponse {
  id: string
  code: string
  name: string
  role_level_code: string
  is_system: boolean
  is_active: boolean
  member_count: number
}

export interface RoleGroupListResponse {
  groups: RoleGroupResponse[]
}

export interface CreateRoleRequest {
  code: string
  name: string
  description: string
  role_level_code: string
  tenant_key?: string
  scope_org_id?: string | null
  scope_workspace_id?: string | null
}

// ── Groups ───────────────────────────────────────────────────────────────────

export interface GroupMemberResponse {
  id: string
  user_id: string
  membership_status: string
  effective_from: string
  effective_to: string | null
  email: string | null
  display_name: string | null
  scope_org_id?: string | null
  scope_org_name?: string | null
  scope_workspace_id?: string | null
  scope_workspace_name?: string | null
}

export interface GroupRoleResponse {
  id: string
  role_id: string
  role_code: string
  role_name: string
  role_level_code: string
  assignment_status: string
}

export interface GroupResponse {
  id: string
  code: string
  name: string
  description: string
  role_level_code: string
  tenant_key: string
  parent_group_id: string | null
  scope_org_id: string | null
  scope_workspace_id: string | null
  is_active: boolean
  is_system: boolean
  is_locked: boolean
  member_count: number
  members: GroupMemberResponse[]
  roles: GroupRoleResponse[]
  created_at: string
  updated_at: string
}

export interface GroupListResponse {
  groups: GroupResponse[]
}

export interface GroupMemberListResponse {
  members: GroupMemberResponse[]
  total: number
  limit: number
  offset: number
}

export interface GroupChildListResponse {
  children: GroupResponse[]
  total: number
  limit: number
  offset: number
}

export interface CreateGroupRequest {
  code: string
  name: string
  description: string
  role_level_code: string
  tenant_key?: string
  parent_group_id?: string | null
  scope_org_id?: string | null
}

export interface UpdateGroupRequest {
  name?: string
  description?: string
  parent_group_id?: string | null
  is_disabled?: boolean
}

// ── Admin Users ──────────────────────────────────────────────────────────────

export interface UserSummaryResponse {
  user_id: string
  tenant_key: string
  email: string | null
  username: string | null
  display_name?: string | null
  account_status: string
  user_category?: string
  is_active: boolean
  is_disabled: boolean
  is_locked?: boolean
  is_system?: boolean
  is_test?: boolean
  created_at: string
}

export interface UserListResponse {
  users: UserSummaryResponse[]
  total: number
}

export interface UserPropertyDetail {
  key: string
  value: string
}

export interface UserOrgMembership {
  org_id: string
  org_name: string
  org_type: string
  role: string
  is_active: boolean
  joined_at: string
}

export interface UserWorkspaceMembership {
  workspace_id: string
  workspace_name: string
  workspace_type: string
  org_id: string
  org_name: string
  role: string
  is_active: boolean
  joined_at: string
}

export interface UserGroupMembership {
  group_id: string
  group_name: string
  group_code: string
  role_level_code: string
  scope_org_id: string | null
  scope_workspace_id: string | null
  is_system: boolean
  is_active: boolean
  joined_at: string
}

export interface UserDetailResponse {
  user_id: string
  tenant_key: string
  email: string | null
  username: string | null
  account_status: string
  is_active: boolean
  is_disabled: boolean
  created_at: string
  properties: UserPropertyDetail[]
  org_memberships: UserOrgMembership[]
  workspace_memberships: UserWorkspaceMembership[]
  group_memberships: UserGroupMembership[]
}

export interface SessionResponse {
  session_id: string
  user_id: string
  client_ip: string | null
  user_agent: string | null
  is_impersonation: boolean
  created_at: string
  revoked_at: string | null
}

export interface SessionListResponse {
  sessions: SessionResponse[]
}

// ── Impersonation ────────────────────────────────────────────────────────────

export interface StartImpersonationRequest {
  target_user_id: string
  reason: string
}

export interface StartImpersonationResponse {
  access_token: string
  token_type: string
  expires_in: number
  refresh_token: string
  refresh_expires_in: number
  impersonation_session_id: string
  target_user: {
    user_id: string
    email: string | null
    username: string | null
  }
}

export interface ImpersonationStatusResponse {
  is_impersonating: boolean
  impersonator_id: string | null
  target_user_id: string | null
  session_id: string | null
  expires_at: string | null
}

export interface ImpersonationSessionResponse {
  session_id: string
  target_user_id: string
  impersonator_user_id: string
  reason: string | null
  created_at: string
  revoked_at: string | null
  target_email?: string | null
  impersonator_email?: string | null
}

export interface ImpersonationHistoryResponse {
  sessions: ImpersonationSessionResponse[]
}

// ── Audit ────────────────────────────────────────────────────────────────────

export interface AuditEventResponse {
  id: string
  tenant_key: string
  entity_type: string
  entity_id: string
  event_type: string
  event_category: string
  actor_id: string | null
  actor_type: string | null
  ip_address: string | null
  session_id: string | null
  occurred_at: string
  properties: Record<string, string | null>
}

export interface AuditEventListResponse {
  events: AuditEventResponse[]
  total: number
}

export interface UserDisableResponse {
  user_id: string
  is_disabled: boolean
}

export interface UserAuditEventListResponse {
  events: AuditEventResponse[]
  total: number
}

// ── Notifications ────────────────────────────────────────────────────────────

export interface ChannelResponse {
  id: string
  code: string
  name: string
  description: string
  is_available: boolean
  sort_order: number
}

export interface CategoryResponse {
  id: string
  code: string
  name: string
  description: string
  is_mandatory: boolean
  sort_order: number
}

export interface NotificationTypeResponse {
  id: string
  code: string
  name: string
  description: string
  category_code: string
  is_mandatory: boolean
  is_user_triggered: boolean
  default_enabled: boolean
  cooldown_seconds: number | null
  sort_order: number
}

export interface TemplateVariableKeyResponse {
  id: string
  code: string
  name: string
  description: string
  data_type: string
  example_value: string | null
  preview_default: string | null
  resolution_source: string
  resolution_key: string | null
  static_value: string | null
  query_id: string | null
  is_user_defined: boolean
  sort_order: number
}

export interface CreateVariableKeyRequest {
  code: string
  name: string
  description?: string
  data_type?: string
  example_value?: string
  resolution_source: "static" | "custom_query" | "user_property" | "audit_property" | string
  resolution_key?: string
  static_value?: string
  query_id?: string
}

export interface UpdateVariableKeyRequest {
  name?: string
  description?: string
  static_value?: string
  resolution_source?: string
  resolution_key?: string
  query_id?: string
  example_value?: string
}

export interface NotificationConfigResponse {
  channels: ChannelResponse[]
  categories: CategoryResponse[]
  types: NotificationTypeResponse[]
  variable_keys: TemplateVariableKeyResponse[]
}

export interface TemplateResponse {
  id: string
  tenant_key: string
  code: string
  name: string
  description: string
  notification_type_code: string
  channel_code: string
  active_version_id: string | null
  base_template_id: string | null
  org_id: string | null
  static_variables: Record<string, string>
  is_active: boolean
  is_system: boolean
  created_at: string
  updated_at: string
}

export interface TemplateListResponse {
  items: TemplateResponse[]
  total: number
}

export interface BroadcastResponse {
  id: string
  tenant_key: string
  title: string
  body_text: string
  body_html: string | null
  status: string
  target_scope: string
  scheduled_at: string | null
  sent_at: string | null
  created_at: string
  updated_at: string
}

export interface BroadcastListResponse {
  items: BroadcastResponse[]
  total: number
}

export interface ReleaseResponse {
  id: string
  tenant_key: string
  version: string
  title: string
  summary: string
  body_html: string | null
  body_text: string | null
  status: string
  published_at: string | null
  created_at: string
  updated_at: string
}

export interface ReleaseListResponse {
  items: ReleaseResponse[]
  total: number
}

export interface IncidentResponse {
  id: string
  tenant_key: string
  title: string
  summary: string
  severity: string
  status: string
  started_at: string
  resolved_at: string | null
  created_at: string
  updated_at: string
}

export interface IncidentListResponse {
  items: IncidentResponse[]
  total: number
}

// ── Incident Updates ────────────────────────────────────────────────────────

export interface IncidentUpdateResponse {
  id: string
  incident_id: string
  status: string
  message: string
  is_public: boolean
  broadcast_id: string | null
  created_at: string
  created_by: string
}

// ── Extended Broadcast (full shape from backend) ────────────────────────────

export interface BroadcastFullResponse {
  id: string
  tenant_key: string
  title: string
  body_text: string
  body_html: string | null
  scope: string
  scope_org_id: string | null
  scope_workspace_id: string | null
  notification_type_code: string
  priority_code: string
  severity: string | null
  is_critical: boolean
  template_code: string | null
  scheduled_at: string | null
  sent_at: string | null
  total_recipients: number | null
  is_active: boolean
  created_at: string
  updated_at: string
  created_by: string
}

// ── Extended Release (full shape from backend) ──────────────────────────────

export interface ReleaseFullResponse {
  id: string
  tenant_key: string
  version: string
  title: string
  summary: string
  body_markdown: string | null
  body_html: string | null
  changelog_url: string | null
  status: string
  release_date: string | null
  published_at: string | null
  broadcast_id: string | null
  is_active: boolean
  created_at: string
  updated_at: string
  created_by: string
}

// ── Extended Incident (full shape from backend) ─────────────────────────────

export interface IncidentFullResponse {
  id: string
  tenant_key: string
  title: string
  description: string
  severity: string
  status: string
  affected_components: string | null
  started_at: string
  resolved_at: string | null
  broadcast_id: string | null
  is_active: boolean
  created_at: string
  updated_at: string
  created_by: string
  updates: IncidentUpdateResponse[] | null
}

// ── Template Detail ─────────────────────────────────────────────────────────

export interface TemplateVersionResponse {
  id: string
  template_id: string
  version_number: number
  subject_line: string | null
  body_html: string | null
  body_text: string | null
  body_short: string | null
  metadata_json: string | null
  change_notes: string | null
  is_active: boolean
  created_at: string
}

export interface TemplateDetailResponse extends TemplateResponse {
  versions: TemplateVersionResponse[]
}

// ── Entity Settings ─────────────────────────────────────────────────────────

export interface SettingResponse {
  key: string
  value: string
}

export interface SettingKeyResponse {
  code: string
  name: string
  description: string
  data_type: string
  is_pii: boolean
  is_required: boolean
  sort_order: number
}

// ── User Accounts ───────────────────────────────────────────────────────────

export interface UserAccountResponse {
  account_type: string
  is_primary: boolean
  is_active: boolean
  properties: Record<string, string>
}

// ── Property Keys ───────────────────────────────────────────────────────────

export interface PropertyKeyResponse {
  code: string
  name: string
  description: string
  data_type: string
  is_pii: boolean
  is_required: boolean
  sort_order: number
}

// ── Invitation Stats ────────────────────────────────────────────────────────

export interface InvitationStatsResponse {
  total: number
  pending: number
  accepted: number
  expired: number
  revoked: number
  declined: number
}

// ── Invitation Accept ───────────────────────────────────────────────────────

export interface InvitationAcceptedResponse {
  message: string
  scope: string
  org_id: string | null
  workspace_id: string | null
  role: string | null
}

// ── Feature Evaluation ──────────────────────────────────────────────────────

export interface FeatureEvaluation {
  code: string
  name: string
  enabled: boolean
  permissions: string[]
}

// ── Create/Update Requests ──────────────────────────────────────────────────

export interface UpdateRoleRequest {
  name?: string
  description?: string
  is_disabled?: boolean
}

// ── Invite Campaigns ─────────────────────────────────────────────────────────

export interface CampaignResponse {
  id: string
  tenant_key: string
  code: string
  name: string
  description: string
  campaign_type: string
  status: string
  default_scope: string
  default_role: string | null
  default_org_id: string | null
  default_workspace_id: string | null
  default_expires_hours: number
  starts_at: string | null
  ends_at: string | null
  invite_count: number
  accepted_count: number
  notes: string | null
  created_at: string
  updated_at: string
  created_by: string | null
}

export interface CampaignListResponse {
  campaigns: CampaignResponse[]
  total: number
}

export interface CreateCampaignRequest {
  code: string
  name: string
  description?: string
  campaign_type?: "event" | "referral" | "form" | "import" | "other"
  default_scope?: "platform" | "organization" | "workspace"
  default_role?: string | null
  default_org_id?: string | null
  default_workspace_id?: string | null
  default_expires_hours?: number
  starts_at?: string | null
  ends_at?: string | null
  notes?: string | null
}

export interface UpdateCampaignRequest {
  name?: string
  description?: string
  status?: "active" | "paused" | "closed" | "archived"
  default_role?: string | null
  default_expires_hours?: number
  starts_at?: string | null
  ends_at?: string | null
  notes?: string | null
}

export interface BulkInviteRequest {
  emails?: string[]
  scope?: string
  org_id?: string | null
  workspace_id?: string | null
  role?: string | null
  expires_in_hours?: number
  source_tag?: string | null
}

export interface BulkInviteResultEntry {
  email: string
  status: "sent" | "skipped" | "error"
  reason: string | null
  invitation_id: string | null
}

export interface BulkInviteResponse {
  sent: number
  skipped: number
  errors: number
  results: BulkInviteResultEntry[]
}

// ── Invitation (full shape) ──────────────────────────────────────────────────

export interface InvitationResponse {
  id: string
  email: string
  scope: string
  org_id: string | null
  workspace_id: string | null
  role: string | null
  grc_role_code: string | null
  engagement_id: string | null
  framework_id: string | null
  status: string
  invited_by: string
  expires_at: string
  accepted_at: string | null
  accepted_by: string | null
  revoked_at: string | null
  revoked_by: string | null
  campaign_id: string | null
  source_tag: string | null
  created_at: string
  updated_at: string
}

export interface InvitationListResponse {
  items: InvitationResponse[]
  total: number
  page: number
  page_size: number
}

export interface CreateBroadcastRequest {
  title: string
  body_text: string
  body_html?: string | null
  subject_line?: string | null
  scope: string
  scope_org_id?: string | null
  scope_workspace_id?: string | null
  notification_type_code?: string | null
  priority_code?: string | null
  severity?: string | null
  is_critical?: boolean
  template_code?: string | null
  scheduled_at?: string | null
}

export interface CreateTemplateRequest {
  code: string
  name: string
  description?: string
  notification_type_code: string
  channel_code: string
  base_template_id?: string | null
  org_id?: string | null
  static_variables?: Record<string, string>
}

export interface UpdateTemplateRequest {
  name?: string
  description?: string
  is_disabled?: boolean
  active_version_id?: string | null
  static_variables?: Record<string, string>
}

export interface CreateTemplateVersionRequest {
  subject_line?: string | null
  body_html?: string | null
  body_text?: string | null
  body_short?: string | null
  metadata_json?: string | null
  change_notes?: string | null
}

export interface PreviewTemplateResponse {
  rendered_subject: string | null
  rendered_body_html: string | null
  rendered_body_text: string | null
  rendered_body_short: string | null
}

export interface QueueItemAdminResponse {
  id: string
  tenant_key: string
  user_id: string | null
  notification_type_code: string
  channel_code: string
  status_code: string
  priority_code: string
  template_id: string | null
  source_rule_id: string | null
  broadcast_id: string | null
  rendered_subject: string | null
  recipient_email: string | null
  scheduled_at: string
  attempt_count: number
  max_attempts: number
  next_retry_at: string | null
  last_error: string | null
  created_at: string
  updated_at: string
  completed_at: string | null
}

export interface QueueStatsResponse {
  queued: number
  processing: number
  sent: number
  delivered: number
  failed: number
  dead_letter: number
  suppressed: number
}

export interface QueueAdminResponse {
  stats: QueueStatsResponse
  items: QueueItemAdminResponse[]
  total: number
}

export interface CreateReleaseRequest {
  version: string
  title: string
  summary: string
  body_markdown?: string | null
  body_html?: string | null
  changelog_url?: string | null
  release_date?: string | null
}

export interface UpdateReleaseRequest {
  title?: string
  summary?: string
  body_markdown?: string | null
  body_html?: string | null
  changelog_url?: string | null
  release_date?: string | null
}

export interface CreateIncidentRequest {
  title: string
  description: string
  severity: string
  affected_components?: string | null
  started_at?: string | null
  notify_users?: boolean
}

export interface UpdateIncidentRequest {
  title?: string
  description?: string
  severity?: string
  affected_components?: string | null
}

export interface CreateIncidentUpdateRequest {
  status: string
  message: string
  is_public?: boolean
  notify_users?: boolean
}

// ── SMTP Config ──────────────────────────────────────────────────────────────

export interface SmtpConfigResponse {
  host: string | null
  port: number
  username: string | null
  from_email: string | null
  from_name: string
  use_tls: boolean
  start_tls: boolean
  is_configured: boolean
  source?: "db" | "env"
}

export interface SmtpConfigRequest {
  host: string
  port: number
  username?: string | null
  password?: string | null
  from_email: string
  from_name: string
  use_tls: boolean
  start_tls: boolean
}

export interface SmtpTestRequest {
  to_email: string
  host?: string | null
  port?: number | null
  username?: string | null
  password?: string | null
  from_email?: string | null
  from_name?: string | null
  use_tls?: boolean | null
  start_tls?: boolean | null
}

export interface SmtpTestResponse {
  success: boolean
  message: string
  detail: string | null
}

// ── Send Test Notification ────────────────────────────────────────────────────

export interface SendTestNotificationRequest {
  to_email: string
  notification_type_code: string
  channel_code?: string
  subject?: string | null
  body?: string | null
}

export interface SendTestNotificationResponse {
  success: boolean
  message: string
  queue_id: string | null
}

// ── Delivery Reports ─────────────────────────────────────────────────────────

export interface DeliveryFunnelResponse {
  queued: number
  processing: number
  sent: number
  delivered: number
  opened: number
  clicked: number
  failed: number
  dead_letter: number
  suppressed: number
  delivery_rate: number
  open_rate: number
  click_rate: number
}

export interface DeliveryReportRow {
  notification_type_code: string
  channel_code: string
  status_code: string
  total_count: number
  hour_bucket: string
}

export interface DeliveryReportResponse {
  funnel: DeliveryFunnelResponse
  rows: DeliveryReportRow[]
  period_hours: number
}

// ── Queue Management ─────────────────────────────────────────────────────────

export interface QueueActionResponse {
  success: boolean
  message: string
}

export interface DeliveryLogResponse {
  id: string
  notification_id: string
  channel_code: string
  attempt_number: number
  status: string
  provider_response: string | null
  provider_message_id: string | null
  error_code: string | null
  error_message: string | null
  duration_ms: number | null
  occurred_at: string
  created_at: string
}

export interface TrackingEventResponse {
  id: string
  notification_id: string
  tracking_event_type_code: string
  channel_code: string
  click_url: string | null
  user_agent: string | null
  ip_address: string | null
  occurred_at: string
  created_at: string
}

export interface NotificationDetailResponse {
  notification: QueueItemAdminResponse
  delivery_logs: DeliveryLogResponse[]
  tracking_events: TrackingEventResponse[]
}

// ── Notification Rules ──────────────────────────────────────────────────────

export interface RuleResponse {
  id: string
  code: string
  name: string
  description: string | null
  source_event_type: string
  source_event_category: string
  notification_type_code: string
  recipient_strategy: string
  priority_code: string
  delay_seconds: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface RuleChannelResponse {
  channel_code: string
  template_code: string | null
  is_active: boolean
}

export interface RuleConditionResponse {
  id: string
  condition_type: string
  field_key: string
  operator: string
  value: string
}

export interface RuleDetailResponse {
  id: string
  code: string
  name: string
  description: string | null
  source_event_type: string
  source_event_category: string
  notification_type_code: string
  recipient_strategy: string
  priority_code: string
  delay_seconds: number
  is_active: boolean
  channels: RuleChannelResponse[]
  conditions: RuleConditionResponse[]
  created_at: string
  updated_at: string
}

export interface CreateRuleRequest {
  code: string
  name: string
  description?: string
  source_event_type: string
  source_event_category: string
  notification_type_code: string
  recipient_strategy: string
  priority_code: string
  delay_seconds: number
}

export interface UpdateRuleRequest {
  name?: string
  description?: string
  priority_code?: string
  delay_seconds?: number
}

export interface SetRuleChannelRequest {
  template_code?: string
  is_active: boolean
}

export interface CreateRuleConditionRequest {
  condition_type: string
  field_key: string
  operator: string
  value: string
}

// ── Variable Queries ────────────────────────────────────────────────────────

export interface BindParamDefinition {
  key: string
  position: number
  source: "context" | "audit_property"
  required: boolean
  default_value?: string | null
}

export interface ResultColumnDefinition {
  name: string
  data_type: "string" | "integer" | "boolean" | "datetime"
  default_value?: string | null
}

export interface VariableQueryResponse {
  id: string
  tenant_key: string
  code: string
  name: string
  description: string | null
  sql_template: string
  bind_params: BindParamDefinition[]
  result_columns: ResultColumnDefinition[]
  timeout_ms: number
  is_active: boolean
  is_system: boolean
  variable_keys: string[]
  linked_event_type_codes: string[]
  created_at: string
  updated_at: string
}

export interface VariableQueryListResponse {
  items: VariableQueryResponse[]
  total: number
}

export interface CreateVariableQueryRequest {
  code: string
  name: string
  description?: string
  sql_template: string
  bind_params: BindParamDefinition[]
  result_columns: ResultColumnDefinition[]
  timeout_ms?: number
  linked_event_type_codes?: string[]
}

export interface UpdateVariableQueryRequest {
  name?: string
  description?: string
  sql_template?: string
  bind_params?: BindParamDefinition[]
  result_columns?: ResultColumnDefinition[]
  timeout_ms?: number
  is_active?: boolean
  linked_event_type_codes?: string[]
}

export interface TestQueryRequest {
  sql_template: string
  bind_params: BindParamDefinition[]
  param_values?: Record<string, string>
  use_my_profile?: boolean
}

export interface PreviewQueryRequest {
  param_values?: Record<string, string>
  use_my_profile?: boolean
  audit_event_id?: string | null
}

export interface QueryPreviewResponse {
  success: boolean
  columns: string[]
  rows: Record<string, string>[]
  resolved_params: Record<string, string>
  error: string | null
  execution_ms: number | null
}

// ── Schema Metadata (SQL editor autocomplete) ───────────────────────────────

export interface ColumnMetadata {
  name: string
  data_type: string
  is_nullable: boolean
}

export interface TableMetadata {
  schema_name: string
  table_name: string
  columns: ColumnMetadata[]
}

export interface SchemaMetadataResponse {
  tables: TableMetadata[]
}

// ── Audit Event Types (context explorer) ────────────────────────────────────

export interface AuditEventTypeInfo {
  entity_type: string
  event_type: string
  event_category: string
  event_count: number
  available_properties: string[]
}

export interface AuditEventTypesResponse {
  event_types: AuditEventTypeInfo[]
}

export interface RecentAuditEventResponse {
  id: string
  entity_type: string
  entity_id: string
  event_type: string
  event_category: string
  actor_id: string | null
  occurred_at: string
  properties: Record<string, string>
}

export interface RecentAuditEventsResponse {
  events: RecentAuditEventResponse[]
}
