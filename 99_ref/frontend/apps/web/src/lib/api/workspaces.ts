import { fetchWithAuth } from "./apiClient";
import type { CreateWorkspacePayload, WorkspaceResponse, WorkspaceMemberResponse } from "../types/orgs";

export async function listWorkspaces(orgId: string): Promise<WorkspaceResponse[]> {
  const res = await fetchWithAuth(`/api/v1/am/orgs/${orgId}/workspaces`);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || "Failed to list workspaces");
  return (data.items ?? []) as WorkspaceResponse[];
}

export async function createWorkspace(orgId: string, payload: CreateWorkspacePayload): Promise<WorkspaceResponse> {
  const res = await fetchWithAuth(`/api/v1/am/orgs/${orgId}/workspaces`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  if (!res.ok) {
    if (Array.isArray(data.detail)) {
      throw new Error(data.detail.map((e: { msg: string }) => e.msg).join(", "));
    }
    throw new Error(data.error?.message || data.detail || "Failed to create workspace");
  }
  return data as WorkspaceResponse;
}

export async function updateWorkspace(orgId: string, workspaceId: string, payload: Partial<Pick<WorkspaceResponse, "name" | "description"> & { is_disabled: boolean }>): Promise<WorkspaceResponse> {
  const res = await fetchWithAuth(`/api/v1/am/orgs/${orgId}/workspaces/${workspaceId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || "Failed to update workspace");
  return data as WorkspaceResponse;
}

export async function listWorkspaceMembers(orgId: string, workspaceId: string): Promise<WorkspaceMemberResponse[]> {
  const res = await fetchWithAuth(`/api/v1/am/orgs/${orgId}/workspaces/${workspaceId}/members`);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || "Failed to list workspace members");
  return (Array.isArray(data) ? data : data.members ?? data.items ?? []) as WorkspaceMemberResponse[];
}

export async function addWorkspaceMember(orgId: string, workspaceId: string, userId: string, role: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/am/orgs/${orgId}/workspaces/${workspaceId}/members`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId, role }),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.error?.message || "Failed to add workspace member");
  }
}

export async function updateWorkspaceMemberRole(orgId: string, workspaceId: string, targetUserId: string, role: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/am/orgs/${orgId}/workspaces/${workspaceId}/members/${targetUserId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ role }),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.error?.message || "Failed to update workspace member role");
  }
}

export async function updateWorkspaceMemberGrcRole(
  orgId: string,
  workspaceId: string,
  targetUserId: string,
  grcRoleCode: string | null,
): Promise<WorkspaceMemberResponse> {
  const res = await fetchWithAuth(`/api/v1/am/orgs/${orgId}/workspaces/${workspaceId}/members/${targetUserId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ grc_role_code: grcRoleCode }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || "Failed to update GRC role");
  return data as WorkspaceMemberResponse;
}

export async function removeWorkspaceMember(orgId: string, workspaceId: string, targetUserId: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/am/orgs/${orgId}/workspaces/${workspaceId}/members/${targetUserId}`, {
    method: "DELETE",
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.error?.message || "Failed to remove workspace member");
  }
}
