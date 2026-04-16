import { fetchWithAuth } from "./apiClient";
import type { CreateOrgPayload, OrgResponse, OrgMemberResponse } from "../types/orgs";

export async function listOrgs(): Promise<OrgResponse[]> {
  const res = await fetchWithAuth("/api/v1/am/orgs");
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || "Failed to list orgs");
  return (data.items ?? []) as OrgResponse[];
}

export async function createOrg(payload: CreateOrgPayload): Promise<OrgResponse> {
  const res = await fetchWithAuth("/api/v1/am/orgs", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  if (!res.ok) {
    if (Array.isArray(data.detail)) {
      throw new Error(data.detail.map((e: { msg: string }) => e.msg).join(", "));
    }
    throw new Error(data.error?.message || data.detail || "Failed to create organization");
  }
  return data as OrgResponse;
}

export async function updateOrg(orgId: string, payload: Partial<Pick<OrgResponse, "name" | "description"> & { is_disabled: boolean }>): Promise<OrgResponse> {
  const res = await fetchWithAuth(`/api/v1/am/orgs/${orgId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || "Failed to update organization");
  return data as OrgResponse;
}

export async function listOrgMembers(orgId: string): Promise<OrgMemberResponse[]> {
  const res = await fetchWithAuth(`/api/v1/am/orgs/${orgId}/members`);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || "Failed to list org members");
  return (Array.isArray(data) ? data : data.members ?? data.items ?? []) as OrgMemberResponse[];
}

export async function addOrgMember(orgId: string, userId: string, role: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/am/orgs/${orgId}/members`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId, role }),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.error?.message || "Failed to add org member");
  }
}

export async function updateOrgMemberRole(orgId: string, targetUserId: string, role: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/am/orgs/${orgId}/members/${targetUserId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ role }),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.error?.message || "Failed to update member role");
  }
}

export async function removeOrgMember(orgId: string, targetUserId: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/am/orgs/${orgId}/members/${targetUserId}`, {
    method: "DELETE",
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.error?.message || "Failed to remove org member");
  }
}
