import { fetchWithAuth } from "./apiClient";

// ── Types ─────────────────────────────────────────────────────────────────────

export interface GrcRoleAssignment {
  id: string;
  org_id: string;
  user_id: string;
  grc_role_code: string;
  role_name: string;
  role_description: string | null;
  email: string | null;
  display_name: string | null;
  assigned_by: string | null;
  assigned_at: string;
  active_grant_count: number;
  created_at: string;
}

export interface GrcAccessGrant {
  id: string;
  grc_role_assignment_id: string;
  scope_type: "workspace" | "framework" | "engagement";
  scope_id: string;
  scope_name: string | null;
  granted_by: string | null;
  granted_at: string;
  created_at: string;
}

export interface GrcTeamMember {
  assignment_id: string;
  org_id: string;
  user_id: string;
  grc_role_code: string;
  role_name: string;
  email: string | null;
  display_name: string | null;
  assigned_at: string;
  grants: GrcAccessGrant[];
}

export interface GrcTeamResponse {
  internal: GrcTeamMember[];
  auditors: GrcTeamMember[];
  vendors: GrcTeamMember[];
  total: number;
}

// ── API Functions ─────────────────────────────────────────────────────────────

const BASE = "/api/v1/am/orgs";

export async function listGrcRoleAssignments(
  orgId: string,
  params?: { grc_role_code?: string; user_id?: string }
): Promise<GrcRoleAssignment[]> {
  const qs = new URLSearchParams();
  if (params?.grc_role_code) qs.set("grc_role_code", params.grc_role_code);
  if (params?.user_id) qs.set("user_id", params.user_id);
  const suffix = qs.toString() ? `?${qs}` : "";
  const res = await fetchWithAuth(`${BASE}/${orgId}/grc-roles${suffix}`);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || "Failed to list GRC role assignments");
  return (data.items ?? []) as GrcRoleAssignment[];
}

export async function assignGrcRole(
  orgId: string,
  body: { user_id: string; grc_role_code: string }
): Promise<GrcRoleAssignment> {
  const res = await fetchWithAuth(`${BASE}/${orgId}/grc-roles`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || data.detail || "Failed to assign GRC role");
  return data as GrcRoleAssignment;
}

export async function revokeGrcRole(orgId: string, assignmentId: string): Promise<void> {
  const res = await fetchWithAuth(`${BASE}/${orgId}/grc-roles/${assignmentId}`, {
    method: "DELETE",
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.error?.message || "Failed to revoke GRC role");
  }
}

export async function listAccessGrants(
  orgId: string,
  assignmentId: string
): Promise<GrcAccessGrant[]> {
  const res = await fetchWithAuth(`${BASE}/${orgId}/grc-roles/${assignmentId}/grants`);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || "Failed to list access grants");
  return (data.items ?? []) as GrcAccessGrant[];
}

export async function createAccessGrant(
  orgId: string,
  assignmentId: string,
  body: { scope_type: string; scope_id: string }
): Promise<GrcAccessGrant> {
  const res = await fetchWithAuth(`${BASE}/${orgId}/grc-roles/${assignmentId}/grants`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || "Failed to create access grant");
  return data as GrcAccessGrant;
}

export async function revokeAccessGrant(
  orgId: string,
  assignmentId: string,
  grantId: string
): Promise<void> {
  const res = await fetchWithAuth(
    `${BASE}/${orgId}/grc-roles/${assignmentId}/grants/${grantId}`,
    { method: "DELETE" }
  );
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.error?.message || "Failed to revoke access grant");
  }
}

export async function getGrcTeam(
  orgId: string,
  params?: { workspace_id?: string; engagement_id?: string }
): Promise<GrcTeamResponse> {
  const qs = new URLSearchParams();
  if (params?.workspace_id) qs.set("workspace_id", params.workspace_id);
  if (params?.engagement_id) qs.set("engagement_id", params.engagement_id);
  const suffix = qs.toString() ? `?${qs}` : "";
  const res = await fetchWithAuth(`${BASE}/${orgId}/grc-roles/team${suffix}`);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || "Failed to load GRC team");
  return data as GrcTeamResponse;
}
