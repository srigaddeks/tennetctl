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
  /** Present on /me response — true when user has verified their email address. */
  email_verified?: boolean;
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
  /** @deprecated use `status` instead */
  is_active?: boolean;
  /** Preferred status transition: "active" | "inactive" */
  status?: "active" | "inactive";
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

// ─── IAM: Auth Policy ────────────────────────────────────────────

export type AuthPolicyKey =
  | "password.min_length"
  | "password.require_upper"
  | "password.require_digit"
  | "password.require_symbol"
  | "password.min_unique_chars"
  | "lockout.threshold_failed_attempts"
  | "lockout.window_seconds"
  | "lockout.duration_seconds"
  | "session.max_concurrent_per_user"
  | "session.idle_timeout_seconds"
  | "session.absolute_ttl_seconds"
  | "session.eviction_policy"
  | "magic_link.ttl_seconds"
  | "magic_link.rate_limit_per_email"
  | "magic_link.rate_window_seconds"
  | "otp.email_ttl_seconds"
  | "otp.email_max_attempts"
  | "otp.rate_limit_per_email"
  | "otp.rate_window_seconds"
  | "password_reset.ttl_seconds";

export type PolicyGroup =
  | "password"
  | "lockout"
  | "session"
  | "magic_link"
  | "otp"
  | "password_reset";

export type PolicyEntry = VaultConfigMeta & { key: `iam.policy.${string}` };

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
  deep_link: string | null;
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

export type UnreadCountResponse = { count: number };

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

// ─── Notify: SMTP Configs ───────────────────────────────────────

export type NotifySMTPConfig = {
  id: string;
  org_id: string;
  key: string;
  label: string;
  host: string;
  port: number;
  tls: boolean;
  username: string;
  auth_vault_key: string;
  from_email: string | null;
  from_name: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type NotifySMTPConfigListResponse = {
  items: NotifySMTPConfig[];
  total: number;
};

export type NotifySMTPConfigCreate = {
  org_id: string;
  key: string;
  label: string;
  host: string;
  port: number;
  tls: boolean;
  username: string;
  auth_vault_key: string;
  from_email?: string | null;
  from_name?: string | null;
};

// ─── Notify: Subscriptions ──────────────────────────────────────

export type NotifySubscriptionRecipientMode = "actor" | "users" | "roles";

export type NotifySubscription = {
  id: string;
  org_id: string;
  name: string;
  event_key_pattern: string;
  template_id: string;
  channel_id: number;
  channel_code: NotifyChannelCode;
  channel_label: string;
  recipient_mode: NotifySubscriptionRecipientMode;
  recipient_filter: Record<string, unknown>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type NotifySubscriptionCreate = {
  org_id: string;
  name: string;
  event_key_pattern: string;
  template_id: string;
  channel_id: number;
  recipient_mode?: NotifySubscriptionRecipientMode;
  recipient_filter?: Record<string, unknown>;
};

export type NotifySubscriptionListResponse = {
  items: NotifySubscription[];
  total: number;
};

export type NotifyTemplateGroupCreate = {
  org_id: string;
  key: string;
  label: string;
  category_id: number;
  smtp_config_id?: string | null;
};

// ─── Notify: Deliveries ──────────────────────────────────────────

export type NotifyDelivery = {
  id: string;
  org_id: string;
  subscription_id: string | null;
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

// ─── Notify: Template Analytics ─────────────────────────────────

export type NotifyTemplateAnalytics = {
  by_status: Record<string, number>;
  by_event_type: Record<string, number>;
  total_deliveries: number;
};

// ─── IAM: API Keys ───────────────────────────────────────────────

export type ApiKeyScope = "notify:send" | "notify:read" | "audit:read";

export type ApiKey = {
  id: string;
  org_id: string;
  user_id: string;
  key_id: string;
  label: string;
  scopes: string[];
  last_used_at: string | null;
  expires_at: string | null;
  revoked_at: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type ApiKeyCreate = {
  label: string;
  scopes: string[];
  expires_at?: string | null;
};

export type ApiKeyCreatedResponse = ApiKey & { token: string };

export type ApiKeyListResponse = {
  items: ApiKey[];
  total: number;
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

// ─── IAM: Email Verification ─────────────────────────────────────────────────

export type EmailVerifySendBody = {
  email: string;
};

export type EmailVerifyConsumeBody = {
  token: string;
};

export type EmailVerifyConsumeResult = {
  verified: boolean;
  user_id: string | null;
};

// ─── Monitoring: Metrics ─────────────────────────────────────────────────────

export type MetricKind = 'counter' | 'gauge' | 'histogram';

export type ResourceIdentity = {
  service_name: string;
  service_instance_id?: string | null;
  service_version?: string | null;
  attributes?: Record<string, string>;
};

export type MetricRegisterRequest = {
  key: string;
  kind: MetricKind;
  label_keys?: string[];
  description?: string;
  unit?: string;
  histogram_buckets?: number[] | null;
  max_cardinality?: number;
};

export type MetricIncrementRequest = {
  labels?: Record<string, string>;
  value?: number;
  resource?: ResourceIdentity | null;
};

export type MetricSetRequest = {
  labels?: Record<string, string>;
  value: number;
  resource?: ResourceIdentity | null;
};

export type MetricObserveRequest = {
  labels?: Record<string, string>;
  value: number;
  resource?: ResourceIdentity | null;
};

export type Metric = {
  id: number;
  org_id: string;
  key: string;
  kind: MetricKind;
  label_keys: string[];
  histogram_buckets: number[] | null;
  description: string;
  unit: string;
  max_cardinality: number;
  created_at: string;
  updated_at: string;
};

export type MetricResponse = Metric;

export type MetricListResponse = {
  items: Metric[];
  total: number;
};

export type MetricIngestResponse = {
  metric_id: number;
  accepted: boolean;
};

// ── Monitoring Query DSL (ADR-029) ─────────────────────────────────────
// Mirrors backend/02_features/05_monitoring/query_dsl/types.py.

export type QueryTarget = "logs" | "metrics" | "traces";

export type LastToken = "15m" | "1h" | "24h" | "7d" | "30d" | "90d";

export type Timerange =
  | { last: LastToken; from_ts?: never; to_ts?: never }
  | { from_ts: string; to_ts: string; last?: never };

export type FieldValue = { field: string; value: unknown };
export type FieldValues = { field: string; values: unknown[] };

export type Filter =
  | { and: Filter[] }
  | { or: Filter[] }
  | { not: Filter }
  | { eq: FieldValue }
  | { ne: FieldValue }
  | { in: FieldValues }
  | { nin: FieldValues }
  | { lt: FieldValue }
  | { lte: FieldValue }
  | { gt: FieldValue }
  | { gte: FieldValue }
  | { contains: FieldValue }
  | { jsonb_path: FieldValue }
  | { regex_limited: FieldValue };

export type LogsQuery = {
  target: "logs";
  filter?: Filter;
  timerange: Timerange;
  severity_min?: number;
  body_contains?: string;
  trace_id?: string;
  limit?: number;
  cursor?: string | null;
};

export type MetricAggregate =
  | "sum" | "avg" | "min" | "max" | "count" | "rate"
  | "p50" | "p95" | "p99";

export type MetricBucket = "1m" | "5m" | "1h" | "1d";

export type MetricsQuery = {
  target: "metrics";
  metric_key: string;
  labels?: Record<string, string>;
  filter?: Filter;
  timerange: Timerange;
  aggregate?: MetricAggregate;
  bucket?: MetricBucket;
  groupby?: string[];
  limit?: number;
};

export type TracesQuery = {
  target: "traces";
  filter?: Filter;
  timerange: Timerange;
  service_name?: string;
  span_name_contains?: string;
  duration_min_ms?: number;
  duration_max_ms?: number;
  has_error?: boolean;
  trace_id?: string;
  limit?: number;
  cursor?: string | null;
};

export type LogRow = {
  id: string;
  recorded_at: string;
  severity_id: number;
  severity_code?: string | null;
  body: string;
  service_name?: string | null;
  trace_id?: string | null;
  span_id?: string | null;
  attributes?: Record<string, unknown> | unknown[] | null;
};

export type TimeseriesPoint = {
  bucket_ts: string;
  value: number | null;
  group?: Record<string, unknown> | null;
};

export type SpanRow = {
  trace_id: string;
  span_id: string;
  parent_span_id: string | null;
  recorded_at: string;
  name: string;
  kind_code?: string | null;
  status_code?: string | null;
  duration_ns?: number | null;
  service_name?: string | null;
};

export type TraceSpanNode = SpanRow & { children?: TraceSpanNode[] };

export type QueryResult<T> = {
  items: T[];
  next_cursor?: string | null;
};

export type SavedQuery = {
  id: string;
  org_id: string;
  owner_user_id: string;
  name: string;
  description?: string | null;
  target: QueryTarget;
  dsl: LogsQuery | MetricsQuery | TracesQuery;
  shared: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type SavedQueryListResponse = {
  items: SavedQuery[];
  total: number;
};

// ─── Monitoring: Traces ─────────────────────────────────────────────────────

export type TraceDetailResponse = {
  trace_id: string;
  spans: SpanRow[];
};

// ─── Monitoring: Dashboards (Plan 13-06) ────────────────────────────────────

export type PanelType =
  | "timeseries"
  | "stat"
  | "table"
  | "log_stream"
  | "trace_list";

export type GridPos = {
  x: number;
  y: number;
  w: number;
  h: number;
};

export type Panel = {
  id: string;
  dashboard_id: string;
  title: string;
  panel_type: PanelType;
  dsl: Record<string, unknown>;
  grid_pos: GridPos;
  display_opts: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type Dashboard = {
  id: string;
  org_id: string;
  owner_user_id: string;
  name: string;
  description: string | null;
  layout: Record<string, unknown>;
  shared: boolean;
  panel_count: number;
  created_at: string;
  updated_at: string;
};

export type DashboardDetail = Dashboard & {
  panels: Panel[];
};

export type DashboardListResponse = {
  items: Dashboard[];
  total: number;
};

export type DashboardCreateRequest = {
  name: string;
  description?: string | null;
  shared?: boolean;
  layout?: Record<string, unknown>;
};

export type DashboardUpdateRequest = {
  name?: string;
  description?: string | null;
  shared?: boolean;
  layout?: Record<string, unknown>;
};

export type PanelCreateRequest = {
  title: string;
  panel_type: PanelType;
  dsl: Record<string, unknown>;
  grid_pos?: GridPos;
  display_opts?: Record<string, unknown>;
};

export type PanelUpdateRequest = {
  title?: string;
  panel_type?: PanelType;
  dsl?: Record<string, unknown>;
  grid_pos?: GridPos;
  display_opts?: Record<string, unknown>;
};

// ─── Monitoring Alerts ─────────────────────────────────────────────────────
export type AlertSeverity = "info" | "warn" | "error" | "critical";
export type AlertTarget = "metrics" | "logs";
export type AlertConditionOp = "gt" | "gte" | "lt" | "lte" | "eq" | "ne";
export type AlertState = "firing" | "resolved";

export type AlertCondition = {
  op: AlertConditionOp;
  threshold: number;
  for_duration_seconds: number;
};

export type AlertRule = {
  id: string;
  org_id: string;
  name: string;
  description: string | null;
  target: AlertTarget;
  dsl: Record<string, unknown>;
  condition: AlertCondition;
  severity: AlertSeverity;
  severity_label: string;
  notify_template_key: string;
  labels: Record<string, string>;
  is_active: boolean;
  paused_until: string | null;
  created_at: string;
  updated_at: string;
};

export type AlertRuleCreateRequest = {
  name: string;
  description?: string | null;
  target: AlertTarget;
  dsl: Record<string, unknown>;
  condition: AlertCondition;
  severity: AlertSeverity;
  notify_template_key: string;
  labels?: Record<string, string>;
};

export type AlertRuleUpdateRequest = Partial<AlertRuleCreateRequest> & {
  is_active?: boolean;
  paused_until?: string | null;
};

export type AlertRuleListResponse = {
  items: AlertRule[];
  total: number;
  limit: number;
  offset: number;
};

export type SilenceMatcher = {
  rule_id?: string | null;
  labels?: Record<string, string> | null;
};

export type Silence = {
  id: string;
  org_id: string;
  matcher: SilenceMatcher;
  starts_at: string;
  ends_at: string;
  reason: string;
  created_by: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type SilenceCreateRequest = {
  matcher: SilenceMatcher;
  starts_at: string;
  ends_at: string;
  reason: string;
};

export type SilenceListResponse = {
  items: Silence[];
  total: number;
  limit: number;
  offset: number;
};

export type AlertEvent = {
  id: string;
  rule_id: string;
  rule_name: string | null;
  severity: AlertSeverity | null;
  severity_label: string | null;
  fingerprint: string;
  state: AlertState;
  value: number | null;
  threshold: number | null;
  org_id: string;
  started_at: string;
  resolved_at: string | null;
  last_notified_at: string | null;
  notification_count: number;
  silenced: boolean;
  silence_id: string | null;
  labels: Record<string, unknown>;
  annotations: Record<string, unknown>;
};

export type AlertEventListResponse = {
  items: AlertEvent[];
  total: number;
  limit: number;
  offset: number;
};



// ── Setup ─────────────────────────────────────────────────────────────────────

export type SetupStatus = {
  initialized: boolean;
  user_count: number;
  setup_required: boolean;
};

export type InitialAdminBody = {
  email: string;
  password: string;
  display_name: string;
};

export type InitialAdminResult = {
  user_id: string;
  email: string;
  display_name: string;
  totp_credential_id: string;
  otpauth_uri: string;
  backup_codes: string[];
  session_token: string;
  session: Record<string, unknown>;
};

// ── IAM Invites ───────────────────────────────────────────────────────────────

export type Invite = {
  id: string;
  org_id: string;
  email: string;
  invited_by: string;
  inviter_email: string | null;
  inviter_display_name: string | null;
  role_id: string | null;
  status: 1 | 2 | 3 | 4; // 1=pending 2=accepted 3=cancelled 4=expired
  expires_at: string;
  accepted_at: string | null;
  created_at: string;
  updated_at: string;
};

export type InviteCreateBody = {
  email: string;
  role_id?: string | null;
};

export type AcceptInviteBody = {
  token: string;
  password: string;
  display_name: string;
};
