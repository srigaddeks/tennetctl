/**
 * TennetCTL — Shared API types.
 *
 * All shared TS types live in this one file.
 * No scattered type files. No enums — use string literal unions.
 */

// ─── Envelope ────────────────────────────────────────────────────

export type ApiSuccess<T> = {
  ok: true;
  data: T;
};

export type ApiError = {
  ok: false;
  error: {
    code: string;
    message: string;
  };
};

export type ApiResponse<T> = ApiSuccess<T> | ApiError;

export type Pagination = {
  total: number;
  limit: number;
  offset: number;
};

export type PaginatedResponse<T> = {
  ok: true;
  data: T[];
  pagination: Pagination;
};

export type ListResult<T> = {
  items: T[];
  pagination: Pagination;
};

// ─── Health ──────────────────────────────────────────────────────

export type HealthData = {
  status: string;
};

// ─── IAM: Orgs ───────────────────────────────────────────────────

export type Org = {
  id: string;
  slug: string;
  display_name: string | null;
  is_active: boolean;
  is_test: boolean;
  created_by: string;
  updated_by: string;
  created_at: string;
  updated_at: string;
};

export type OrgCreateBody = {
  slug: string;
  display_name: string;
};

export type OrgUpdateBody = {
  slug?: string;
  display_name?: string;
};

// ─── IAM: Workspaces ─────────────────────────────────────────────

export type Workspace = {
  id: string;
  org_id: string;
  slug: string;
  display_name: string | null;
  is_active: boolean;
  is_test: boolean;
  created_by: string;
  updated_by: string;
  created_at: string;
  updated_at: string;
};

export type WorkspaceCreateBody = {
  org_id: string;
  slug: string;
  display_name: string;
};

export type WorkspaceUpdateBody = {
  slug?: string;
  display_name?: string;
};

// ─── IAM: Users ──────────────────────────────────────────────────

export type AccountType =
  | "email_password"
  | "magic_link"
  | "google_oauth"
  | "github_oauth";

export type User = {
  id: string;
  account_type: AccountType;
  email: string | null;
  display_name: string | null;
  avatar_url: string | null;
  is_active: boolean;
  is_test: boolean;
  created_by: string;
  updated_by: string;
  created_at: string;
  updated_at: string;
};

export type UserCreateBody = {
  account_type: AccountType;
  email: string;
  display_name: string;
  avatar_url?: string;
};

export type UserUpdateBody = {
  email?: string;
  display_name?: string;
  avatar_url?: string;
  is_active?: boolean;
};

// ─── IAM: Auth ───────────────────────────────────────────────────

export type AuthSession = {
  id: string;
  user_id: string;
  org_id: string | null;
  workspace_id: string | null;
  expires_at: string;
  revoked_at: string | null;
  is_valid: boolean;
};

export type AuthResponseBody = {
  token: string;
  user: User;
  session: AuthSession;
};

export type AuthMeResponse = {
  user: User;
  session: {
    id: string;
    user_id: string;
    org_id: string | null;
    workspace_id: string | null;
  };
};

export type SessionReadShape = {
  id: string;
  user_id: string;
  org_id: string | null;
  workspace_id: string | null;
  expires_at: string;
  revoked_at: string | null;
  is_valid: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type SessionPatchBody = {
  extend: boolean;
};

export type PasswordChangeBody = {
  current_password: string;
  new_password: string;
};

export type PasswordChangeResult = {
  changed: boolean;
  other_sessions_revoked: number;
};

export type SignupBody = {
  email: string;
  display_name: string;
  password: string;
};

export type SigninBody = {
  email: string;
  password: string;
};

export type OAuthCallbackBody = {
  code: string;
  redirect_uri: string;
};

// ─── IAM: Memberships ────────────────────────────────────────────

export type OrgMembership = {
  id: string;
  user_id: string;
  org_id: string;
  created_by: string;
  created_at: string;
};

export type OrgMembershipCreateBody = {
  user_id: string;
  org_id: string;
};

export type WorkspaceMembership = {
  id: string;
  user_id: string;
  workspace_id: string;
  org_id: string;
  created_by: string;
  created_at: string;
};

export type WorkspaceMembershipCreateBody = {
  user_id: string;
  workspace_id: string;
};

// ─── IAM: Roles ──────────────────────────────────────────────────

export type RoleType = "system" | "custom";

export type Role = {
  id: string;
  org_id: string | null;
  role_type: RoleType;
  code: string | null;
  label: string | null;
  description: string | null;
  is_active: boolean;
  is_test: boolean;
  created_by: string;
  updated_by: string;
  created_at: string;
  updated_at: string;
};

export type RoleCreateBody = {
  org_id: string | null;
  role_type: RoleType;
  code: string;
  label: string;
  description?: string;
};

export type RoleUpdateBody = {
  label?: string;
  description?: string;
  is_active?: boolean;
};

// ─── IAM: Groups ─────────────────────────────────────────────────

export type Group = {
  id: string;
  org_id: string;
  code: string | null;
  label: string | null;
  description: string | null;
  is_active: boolean;
  is_test: boolean;
  created_by: string;
  updated_by: string;
  created_at: string;
  updated_at: string;
};

export type GroupCreateBody = {
  org_id: string;
  code: string;
  label: string;
  description?: string;
};

export type GroupUpdateBody = {
  label?: string;
  description?: string;
  is_active?: boolean;
};

// ─── IAM: Applications ───────────────────────────────────────────

export type Application = {
  id: string;
  org_id: string;
  code: string | null;
  label: string | null;
  description: string | null;
  is_active: boolean;
  is_test: boolean;
  created_by: string;
  updated_by: string;
  created_at: string;
  updated_at: string;
};

export type ApplicationCreateBody = {
  org_id: string;
  code: string;
  label: string;
  description?: string;
};

export type ApplicationUpdateBody = {
  label?: string;
  description?: string;
  is_active?: boolean;
};

// ─── Feature Flags: Flags ────────────────────────────────────────

export type FlagScope = "global" | "org" | "application";
export type FlagValueType = "boolean" | "string" | "number" | "json";
export type FlagEnvironment = "dev" | "staging" | "prod" | "test";

export type Flag = {
  id: string;
  scope: FlagScope;
  org_id: string | null;
  application_id: string | null;
  flag_key: string;
  value_type: FlagValueType;
  default_value: unknown;
  description: string | null;
  is_active: boolean;
  is_test: boolean;
  created_by: string;
  updated_by: string;
  created_at: string;
  updated_at: string;
};

export type FlagCreateBody = {
  scope: FlagScope;
  org_id?: string | null;
  application_id?: string | null;
  flag_key: string;
  value_type: FlagValueType;
  default_value: unknown;
  description?: string;
};

export type FlagUpdateBody = {
  default_value?: unknown;
  description?: string;
  is_active?: boolean;
};

export type FlagState = {
  id: string;
  flag_id: string;
  environment: FlagEnvironment;
  is_enabled: boolean;
  env_default_value: unknown | null;
  is_test: boolean;
  created_by: string;
  updated_by: string;
  created_at: string;
  updated_at: string;
};

export type FlagStateUpdateBody = {
  is_enabled?: boolean;
  env_default_value?: unknown;
};

// ─── Feature Flags: Permissions ──────────────────────────────────

export type FlagPermission = "view" | "toggle" | "write" | "admin";

export type RoleFlagPermission = {
  id: string;
  role_id: string;
  flag_id: string;
  permission: FlagPermission;
  permission_rank: number;
  created_by: string;
  created_at: string;
};

export type RoleFlagPermissionCreateBody = {
  role_id: string;
  flag_id: string;
  permission: FlagPermission;
};

// ─── Feature Flags: Rules ────────────────────────────────────────

export type FlagRule = {
  id: string;
  flag_id: string;
  environment: FlagEnvironment;
  priority: number;
  conditions: Record<string, unknown>;
  value: unknown;
  rollout_percentage: number;
  is_active: boolean;
  is_test: boolean;
  created_by: string;
  updated_by: string;
  created_at: string;
  updated_at: string;
};

export type FlagRuleCreateBody = {
  flag_id: string;
  environment: FlagEnvironment;
  priority: number;
  conditions: Record<string, unknown>;
  value: unknown;
  rollout_percentage?: number;
};

export type FlagRuleUpdateBody = {
  priority?: number;
  conditions?: Record<string, unknown>;
  value?: unknown;
  rollout_percentage?: number;
  is_active?: boolean;
};

// ─── Feature Flags: Overrides ────────────────────────────────────

export type FlagOverrideEntityType =
  | "org"
  | "workspace"
  | "user"
  | "role"
  | "group"
  | "application";

export type FlagOverride = {
  id: string;
  flag_id: string;
  environment: FlagEnvironment;
  entity_type: FlagOverrideEntityType;
  entity_id: string;
  value: unknown;
  reason: string | null;
  is_active: boolean;
  is_test: boolean;
  created_by: string;
  updated_by: string;
  created_at: string;
  updated_at: string;
};

export type FlagOverrideCreateBody = {
  flag_id: string;
  environment: FlagEnvironment;
  entity_type: FlagOverrideEntityType;
  entity_id: string;
  value: unknown;
  reason?: string;
};

// ─── Feature Flags: Evaluation ───────────────────────────────────

export type EvalContext = {
  user_id?: string;
  org_id?: string;
  workspace_id?: string;
  application_id?: string;
  attrs?: Record<string, unknown>;
};

export type EvaluateRequest = {
  flag_key: string;
  environment: FlagEnvironment;
  context: EvalContext;
};

export type EvalReason =
  | "user_override"
  | "org_override"
  | "application_override"
  | "rule_match"
  | "default_env"
  | "default_flag"
  | "flag_disabled_in_env"
  | "flag_not_found"
  | "flag_inactive";

export type EvaluateResponse = {
  value: unknown;
  reason: EvalReason;
  flag_id: string | null;
  flag_scope: FlagScope | null;
  rule_id: string | null;
  override_id: string | null;
};

// ─── Vault ───────────────────────────────────────────────────────

export type VaultScope = "global" | "org" | "workspace";
export type VaultValueType = "boolean" | "string" | "number" | "json";

// ─── Vault: Secrets ──────────────────────────────────────────────

// Metadata shape — list + create + rotate responses use this. NEVER carries plaintext.
export type VaultSecretMeta = {
  key: string;
  version: number;
  description: string | null;
  scope: VaultScope;
  org_id: string | null;
  workspace_id: string | null;
  is_active: boolean;
  is_test: boolean;
  created_by: string;
  updated_by: string;
  created_at: string;
  updated_at: string;
};

export type VaultSecretCreateBody = {
  key: string;
  value: string;
  description?: string | null;
  scope?: VaultScope;
  org_id?: string | null;
  workspace_id?: string | null;
};

export type VaultSecretRotateBody = {
  value: string;
  description?: string | null;
};

// ─── Vault: Configs ──────────────────────────────────────────────

export type VaultConfigMeta = {
  id: string;
  key: string;
  value_type: VaultValueType;
  value: unknown;
  description: string | null;
  scope: VaultScope;
  org_id: string | null;
  workspace_id: string | null;
  is_active: boolean;
  is_test: boolean;
  created_by: string;
  updated_by: string;
  created_at: string;
  updated_at: string;
};

export type VaultConfigCreateBody = {
  key: string;
  value_type: VaultValueType;
  value: unknown;
  description?: string | null;
  scope?: VaultScope;
  org_id?: string | null;
  workspace_id?: string | null;
};

export type VaultConfigUpdateBody = {
  value?: unknown;
  description?: string | null;
  is_active?: boolean;
};

// ─── Catalog ─────────────────────────────────────────────────────

export type NodeKind = "request" | "effect" | "control";
export type TxMode = "caller" | "own" | "none";

export type CatalogNode = {
  node_key: string;
  kind: NodeKind;
  handler: string;
  emits_audit: boolean;
  timeout_ms: number;
  retries: number;
  tx_mode: TxMode;
  version: number;
  deprecated: boolean;
  sub_feature_key: string;
  feature_key: string;
  feature_number: number;
  module: string;
};

// ─── Audit Events (Phase 10 Plan 01) ─────────────────────────────

export type AuditOutcome = "success" | "failure";
export type AuditBucket = "hour" | "day";
export type AuditCategoryCode = "system" | "user" | "integration" | "setup";

export type AuditEventFilter = {
  event_key?: string | null;   // supports glob, e.g. "iam.orgs.*"
  category_code?: AuditCategoryCode | null;
  outcome?: AuditOutcome | null;
  actor_user_id?: string | null;
  actor_session_id?: string | null;
  org_id?: string | null;
  workspace_id?: string | null;
  trace_id?: string | null;
  since?: string | null;       // ISO-8601
  until?: string | null;
  q?: string | null;           // metadata substring
};

export type AuditEventListQuery = AuditEventFilter & {
  cursor?: string | null;
  limit?: number;
};

export type AuditEventRow = {
  id: string;
  event_key: string;
  event_label: string | null;
  event_description: string | null;
  category_code: AuditCategoryCode;
  category_label: string | null;
  actor_user_id: string | null;
  actor_session_id: string | null;
  org_id: string | null;
  workspace_id: string | null;
  trace_id: string;
  span_id: string;
  parent_span_id: string | null;
  outcome: AuditOutcome;
  metadata: Record<string, unknown>;
  created_at: string;
};

export type AuditEventListResponse = {
  items: AuditEventRow[];
  next_cursor: string | null;
};

export type AuditEventStatsQuery = AuditEventFilter & {
  bucket?: AuditBucket;
};

export type AuditEventStatsCountByKey = { event_key: string; count: number };
export type AuditEventStatsCountByOutcome = { outcome: AuditOutcome; count: number };
export type AuditEventStatsCountByCategory = { category_code: string; count: number };
export type AuditEventStatsTimePoint = { bucket: string; count: number };

export type AuditEventStatsResponse = {
  by_event_key: AuditEventStatsCountByKey[];
  by_outcome: AuditEventStatsCountByOutcome[];
  by_category: AuditEventStatsCountByCategory[];
  time_series: AuditEventStatsTimePoint[];
};

export type AuditEventKeyRow = {
  key: string;
  label: string;
  description: string | null;
  category_code: AuditCategoryCode;
  deprecated_at: string | null;
};

export type AuditEventKeyListResponse = {
  items: AuditEventKeyRow[];
  total: number;
};

// ─── Audit Funnel (Phase 10 Plan 03) ────────────────────────────────────────
export type AuditFunnelRequest = {
  steps: string[];
  org_id?: string | null;
  since?: string | null;
  until?: string | null;
};

export type AuditFunnelStep = {
  event_key: string;
  users: number;
  conversion_pct: number;
};

export type AuditFunnelResponse = {
  steps: AuditFunnelStep[];
};

// ─── Audit Retention (Phase 10 Plan 03) ─────────────────────────────────────
export type AuditRetentionBucket = "day" | "week";

export type AuditRetentionRetained = {
  offset: number;
  count: number;
  pct: number;
};

export type AuditRetentionCohort = {
  cohort_period: string;
  cohort_size: number;
  retained: AuditRetentionRetained[];
};

export type AuditRetentionResponse = {
  cohorts: AuditRetentionCohort[];
};

// ─── Audit Saved Views (Phase 10 Plan 03) ───────────────────────────────────
export type AuditSavedViewCreate = {
  name: string;
  filter_json: Record<string, unknown>;
  bucket?: "hour" | "day";
};

export type AuditSavedViewRow = {
  id: string;
  org_id: string;
  user_id: string | null;
  name: string;
  filter_json: Record<string, unknown>;
  bucket: "hour" | "day";
  created_at: string;
};

export type AuditSavedViewListResponse = {
  items: AuditSavedViewRow[];
  total: number;
};

// ─── Audit Outbox / Live Tail (Phase 10 Plan 04) ────────────────────────────
export type AuditTailEventRow = {
  outbox_id: number;
  id: string;
  event_key: string;
  event_label?: string | null;
  category_code: string;
  actor_user_id?: string | null;
  org_id?: string | null;
  trace_id: string;
  outcome: string;
  metadata: Record<string, unknown>;
  created_at: string;
};

export type AuditTailResponse = {
  items: AuditTailEventRow[];
  last_outbox_id: number;
};

export type AuditOutboxCursorResponse = {
  last_outbox_id: number;
};

// ─── Notify: In-App Deliveries ───────────────────────────────────

export type DeliveryStatusCode =
  | "pending"
  | "queued"
  | "sent"
  | "delivered"
  | "opened"
  | "clicked"
  | "bounced"
  | "failed"
  | "unsubscribed";

export type DeliveryPriorityCode = "low" | "normal" | "high" | "critical";

export type InAppDelivery = {
  id: string;
  org_id: string;
  subscription_id: string | null;
  template_id: string;
  recipient_user_id: string;
  channel_id: number;
  channel_code: string;
  channel_label: string;
  priority_id: number;
  priority_code: DeliveryPriorityCode;
  priority_label: string;
  status_id: number;
  status_code: DeliveryStatusCode;
  status_label: string;
  resolved_variables: Record<string, unknown>;
  audit_outbox_id: number | null;
  failure_reason: string | null;
  scheduled_at: string | null;
  attempted_at: string | null;
  delivered_at: string | null;
  created_at: string;
  updated_at: string;
};

export type InAppDeliveryListResponse = {
  items: InAppDelivery[];
  total: number;
};

// ─── Notify: User Preferences ────────────────────────────────────

export type NotifyChannelCode = "email" | "webpush" | "in_app" | "sms";
export type NotifyCategoryCode = "transactional" | "critical" | "marketing" | "digest";

export type NotifyPreference = {
  channel_id: number;
  channel_code: NotifyChannelCode;
  channel_label: string;
  category_id: number;
  category_code: NotifyCategoryCode;
  category_label: string;
  is_opted_in: boolean;
  is_locked: boolean; // true for critical — cannot opt out
};

export type NotifyPreferencePatchItem = {
  channel_code: NotifyChannelCode;
  category_code: NotifyCategoryCode;
  is_opted_in: boolean;
};

// ─── Notify: Campaigns ───────────────────────────────────────────

export type CampaignStatusCode =
  | "draft"
  | "scheduled"
  | "running"
  | "paused"
  | "completed"
  | "cancelled"
  | "failed";

export type AudienceQuery = {
  account_type_codes?: string[];
};

export type Campaign = {
  id: string;
  org_id: string;
  name: string;
  template_id: string;
  channel_id: number;
  channel_code: NotifyChannelCode;
  channel_label: string;
  audience_query: AudienceQuery;
  scheduled_at: string | null;
  throttle_per_minute: number;
  status_id: number;
  status_code: CampaignStatusCode;
  status_label: string;
  created_by: string;
  updated_by: string;
  created_at: string;
  updated_at: string;
};

export type CampaignListResponse = {
  items: Campaign[];
  total: number;
};

export type CampaignCreate = {
  org_id: string;
  name: string;
  template_id: string;
  channel_code: NotifyChannelCode;
  audience_query?: AudienceQuery;
  scheduled_at?: string | null;
  throttle_per_minute?: number;
};

export type CampaignPatch = {
  name?: string;
  template_id?: string;
  channel_code?: NotifyChannelCode;
  audience_query?: AudienceQuery;
  scheduled_at?: string | null;
  throttle_per_minute?: number;
  status?: "scheduled" | "cancelled";
};

// ─── Notify: Templates ───────────────────────────────────────────

export type NotifyPriorityCode = "low" | "normal" | "high" | "critical";

export type NotifyTemplateBody = {
  id: string;
  template_id: string;
  channel_id: number;
  body_html: string;
  body_text: string;
  preheader: string | null;
};

export type NotifyTemplate = {
  id: string;
  org_id: string;
  key: string;
  group_id: string;
  group_key: string;
  category_id: number;
  category_code: NotifyCategoryCode;
  category_label: string;
  subject: string;
  reply_to: string | null;
  priority_id: number;
  priority_code: NotifyPriorityCode;
  priority_label: string;
  is_active: boolean;
  created_by: string;
  updated_by: string;
  created_at: string;
  updated_at: string;
  bodies: NotifyTemplateBody[];
};

export type NotifyTemplateListResponse = {
  items: NotifyTemplate[];
  total: number;
};

export type NotifyTemplateCreate = {
  org_id: string;
  key: string;
  group_id: string;
  subject: string;
  reply_to?: string;
  priority_id?: number;
  bodies?: Array<{ channel_id: number; body_html: string; body_text?: string; preheader?: string }>;
};

export type NotifyTemplatePatch = {
  subject?: string;
  reply_to?: string;
  priority_id?: number;
  group_id?: string;
  is_active?: boolean;
};

// ─── Notify: Template Variables ──────────────────────────────────

export type NotifyVarType = "static" | "dynamic_sql";

export type NotifyTemplateVariable = {
  id: string;
  template_id: string;
  name: string;
  var_type: NotifyVarType;
  static_value: string | null;
  sql_template: string | null;
  param_bindings: Record<string, string> | null;
  description: string | null;
  created_at: string;
  updated_at: string;
};

export type NotifyTemplateVariableCreate = {
  name: string;
  var_type: NotifyVarType;
  static_value?: string;
  sql_template?: string;
  param_bindings?: Record<string, string>;
  description?: string;
};

export type NotifyTemplateVariableListResponse = {
  items: NotifyTemplateVariable[];
  total: number;
};

// ─── Notify: Template Groups (for pickers) ───────────────────────

export type NotifyTemplateGroup = {
  id: string;
  org_id: string;
  key: string;
  label: string;
  category_id: number;
  category_code: NotifyCategoryCode;
  category_label: string;
  smtp_config_id: string | null;
  smtp_config_key: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type NotifyTemplateGroupListResponse = {
  items: NotifyTemplateGroup[];
  total: number;
};

// ─── Notify: Deliveries ──────────────────────────────────────────

export type NotifyDelivery = {
  id: string;
  org_id: string;
  subscription_id: string | null;
  campaign_id: string | null;
  template_id: string;
  recipient_user_id: string;
  channel_id: number;
  channel_code: NotifyChannelCode;
  channel_label: string;
  priority_id: number;
  priority_code: string;
  priority_label: string;
  status_id: number;
  status_code: string;
  status_label: string;
  resolved_variables: Record<string, unknown>;
  failure_reason: string | null;
  scheduled_at: string | null;
  attempted_at: string | null;
  delivered_at: string | null;
  created_at: string;
  updated_at: string;
};

export type NotifyDeliveryListResponse = {
  items: NotifyDelivery[];
  total: number;
};

// ─── Notify: Campaign Stats ──────────────────────────────────────

export type NotifyCampaignStats = {
  total: number;
  by_status: Record<string, number>;
};

// ─── IAM: OTP ────────────────────────────────────────────────────

export type OtpRequestBody = {
  email: string;
};

export type OtpVerifyBody = {
  email: string;
  code: string;
};

export type TotpSetupBody = {
  device_name?: string;
};

export type TotpSetupResponse = {
  credential_id: string;
  otpauth_uri: string;
  device_name: string;
};

export type TotpVerifyBody = {
  credential_id: string;
  code: string;
};

export type TotpCredential = {
  id: string;
  user_id: string;
  device_name: string;
  is_active: boolean;
  last_used_at: string | null;
  created_at: string;
};

export type TotpListResponse = {
  items: TotpCredential[];
  total: number;
};

// ─── IAM: Passkeys (WebAuthn) ─────────────────────────────────────────────────

export type PasskeyRegisterBeginResponse = {
  challenge_id: string;
  options_json: string;
};

export type PasskeyAuthBeginResponse = {
  challenge_id: string;
  options_json: string;
};

export type PasskeyCredential = {
  id: string;
  user_id: string;
  device_name: string;
  aaguid: string;
  sign_count: number;
  last_used_at: string | null;
  created_at: string;
};

export type PasskeyListResponse = {
  items: PasskeyCredential[];
  total: number;
};

// ─── IAM: Password Reset ─────────────────────────────────────────────────────

export type PasswordResetRequestBody = {
  email: string;
};

export type PasswordResetCompleteBody = {
  token: string;
  new_password: string;
};

