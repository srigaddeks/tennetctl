import { fetchWithAuth } from "./apiClient";

export interface InvitationResponse {
  id: string;
  email: string;
  scope: string;
  org_id: string | null;
  workspace_id: string | null;
  role: string | null;
  grc_role_code: string | null;
  engagement_id: string | null;
  framework_id: string | null;
  framework_ids: string[] | null;
  engagement_ids: string[] | null;
  status: string;
  expires_at: string | null;
  created_at: string;
  accepted_at: string | null;
  revoked_at: string | null;
}

export interface CreateInvitationRequest {
  email: string;
  scope: string; // "organization" | "workspace" | "platform"
  org_id?: string;
  workspace_id?: string;
  role?: string;
  grc_role_code?: string;
  engagement_id?: string;
  framework_id?: string;
  framework_ids?: string[];
  engagement_ids?: string[];
}

export async function listInvitations(params?: {
  scope?: string;
  status?: string;
  org_id?: string;
  workspace_id?: string;
}): Promise<InvitationResponse[]> {
  const q = new URLSearchParams();
  if (params?.scope) q.set("scope", params.scope);
  if (params?.status) q.set("status", params.status);
  if (params?.org_id) q.set("org_id", params.org_id);
  if (params?.workspace_id) q.set("workspace_id", params.workspace_id);
  const res = await fetchWithAuth(`/api/v1/am/invitations${q.toString() ? `?${q}` : ""}`, { cache: "no-store" });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || "Failed to list invitations");
  return (data.items ?? data.invitations ?? []) as InvitationResponse[];
}

export async function createInvitation(payload: CreateInvitationRequest): Promise<InvitationResponse> {
  const res = await fetchWithAuth("/api/v1/am/invitations", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || data.detail || "Failed to create invitation");
  return data as InvitationResponse;
}

export async function revokeInvitation(invitationId: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/am/invitations/${invitationId}/revoke`, {
    method: "PATCH",
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.error?.message || "Failed to revoke invitation");
  }
}

export interface InvitationCreatedResponse extends InvitationResponse {
  invite_token: string | null;
}

export async function resendInvitation(invitationId: string): Promise<InvitationCreatedResponse> {
  const res = await fetchWithAuth(`/api/v1/am/invitations/${invitationId}/resend`, {
    method: "POST",
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error?.message || "Failed to resend invitation");
  return data as InvitationCreatedResponse;
}
