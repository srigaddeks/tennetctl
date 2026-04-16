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

// Metadata shape — list + create + rotate responses use this. NEVER carries plaintext.
export type VaultSecretMeta = {
  key: string;
  version: number;
  description: string | null;
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
};

export type VaultSecretRotateBody = {
  value: string;
  description?: string | null;
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
