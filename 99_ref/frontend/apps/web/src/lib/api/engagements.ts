import { fetchWithAuth } from "./apiClient";
import type { TaskListResponse, TaskResponse } from "../types/grc";

export interface DashboardStats {
  openRequests: number;
  totalControls: number;
  verifiedControls: number;
  remainingDays: number;
  readinessPercentage: number;
}

export interface EngagementControl {
  id: string;
  control_code: string;
  control_type: string;
  name: string;
  description: string;
  category_name: string;
  criticality_name: string;
  verification_status: string | null;
  verified_at: string | null;
  open_requests_count: number;
  evidence_count: number;
}

export interface Engagement {
  id: string;
  org_id: string;
  org_name: string;
  workspace_id?: string | null;
  workspace_name?: string | null;
  engagement_code: string;
  status_code: string;
  status_name: string;
  engagement_name: string;
  auditor_firm: string;
  scope_description: string | null;
  audit_period_start: string | null;
  audit_period_end: string | null;
  lead_grc_sme: string | null;
  target_completion_date: string | null;
  open_requests_count: number;
  total_controls_count: number;
  verified_controls_count: number;
  is_active: boolean;
  created_at: string;
  framework_id: string;
  framework_deployment_id: string;
  engagement_type?: string | null;
}

export interface AuditAccessToken {
  id: string;
  engagement_id: string;
  auditor_email: string;
  expires_at: string;
  is_revoked: boolean;
  last_accessed_at: string | null;
  created_at: string;
}

export interface AuditorRequest {
  id: string;
  engagement_id: string;
  requested_by_token_id: string;
  auditor_email: string | null;
  control_id: string | null;
  request_status: "open" | "fulfilled" | "dismissed";
  request_description: string | null;
  response_notes: string | null;
  fulfilled_at: string | null;
  fulfilled_by: string | null;
  created_at: string;
  updated_at: string;
  task_id: string | null;
}

export interface EngagementTaskCreateRequest {
  task_type_code: string;
  priority_code?: string;
  entity_type?: string;
  entity_id?: string;
  assignee_user_id?: string;
  due_date?: string;
  start_date?: string;
  estimated_hours?: number;
  title: string;
  description?: string;
  acceptance_criteria?: string;
  remediation_plan?: string;
}

export interface EngagementParticipant {
  user_id: string;
  display_name?: string | null;
  email?: string | null;
  membership_type_code?: string | null;
}

export interface EngagementAssessment {
  id: string;
  tenant_key: string;
  assessment_code: string;
  org_id: string;
  workspace_id: string | null;
  framework_id: string | null;
  assessment_type_code: string;
  assessment_status_code: string;
  lead_assessor_id: string | null;
  scheduled_start: string | null;
  scheduled_end: string | null;
  actual_start: string | null;
  actual_end: string | null;
  is_locked: boolean;
  assessment_type_name: string | null;
  assessment_status_name: string | null;
  name: string | null;
  description: string | null;
  scope_notes: string | null;
  finding_count: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  created_by: string | null;
}

export interface EngagementFinding {
  id: string;
  assessment_id: string;
  control_id: string | null;
  risk_id: string | null;
  severity_code: string;
  finding_type: string;
  finding_status_code: string;
  assigned_to: string | null;
  remediation_due_date: string | null;
  severity_name: string | null;
  finding_status_name: string | null;
  title: string | null;
  description: string | null;
  recommendation: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  created_by: string | null;
}

export interface EngagementFindingListResponse {
  items: EngagementFinding[];
  total: number;
}

export interface EngagementFindingCreateRequest {
  control_id?: string;
  risk_id?: string;
  severity_code: string;
  finding_type?: "non_conformity" | "observation" | "opportunity" | "recommendation";
  assigned_to?: string;
  remediation_due_date?: string;
  title: string;
  description?: string;
  recommendation?: string;
}

export const engagementsApi = {
  list: async (orgId: string, statusCode?: string): Promise<Engagement[]> => {
    const params = new URLSearchParams({ org_id: orgId });
    if (statusCode) params.append("status_code", statusCode);
    const res = await fetchWithAuth(`/api/v1/engagements/?${params.toString()}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      const msg = err.error?.message || err.detail || "Failed to list engagements";
      throw new Error(msg);
    }
    return res.json() as Promise<Engagement[]>;
  },

  listMyEngagements: async (orgId?: string): Promise<Engagement[]> => {
    const qs = orgId ? `?org_id=${encodeURIComponent(orgId)}` : "";
    const res = await fetchWithAuth(`/api/v1/engagements/my-engagements${qs}`);
    if (!res.ok) throw new Error("Failed to list my engagements");
    return res.json() as Promise<Engagement[]>;
  },

  listEngagementControls: async (engagementId: string): Promise<EngagementControl[]> => {
    const res = await fetchWithAuth(`/api/v1/engagements/${engagementId}/controls`);
    if (!res.ok) throw new Error("Failed to list engagement controls");
    return res.json() as Promise<EngagementControl[]>;
  },

  get: async (engagementId: string): Promise<Engagement> => {
    const res = await fetchWithAuth(`/api/v1/engagements/${engagementId}`);
    if (!res.ok) throw new Error("Failed to get engagement");
    return res.json() as Promise<Engagement>;
  },

  create: async (
    orgId: string,
    data: Partial<Engagement> & {
      framework_id: string;
      framework_deployment_id: string;
      engagement_code: string;
      status_code: string;
    }
  ): Promise<Engagement> => {
    const res = await fetchWithAuth(`/api/v1/engagements/?org_id=${orgId}`, {
      method: "POST",
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error((errData as { detail?: string }).detail || "Failed to create engagement");
    }
    return res.json() as Promise<Engagement>;
  },

  update: async (engagementId: string, data: Partial<Engagement>): Promise<Engagement> => {
    const res = await fetchWithAuth(`/api/v1/engagements/${engagementId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error("Failed to update engagement");
    return res.json() as Promise<Engagement>;
  },

  inviteAuditor: async (
    engagementId: string,
    email: string,
    expiresInDays: number = 30
  ): Promise<{ email: string; invite_url: string; expires_at: string }> => {
    const res = await fetchWithAuth(`/api/v1/engagements/${engagementId}/invite-auditor`, {
      method: "POST",
      body: JSON.stringify({ email, expires_in_days: expiresInDays }),
    });
    if (!res.ok) throw new Error("Failed to invite auditor");
    return res.json() as Promise<{ email: string; invite_url: string; expires_at: string }>;
  },

  listAccessTokens: async (engagementId: string, includeRevoked = true): Promise<AuditAccessToken[]> => {
    const res = await fetchWithAuth(
      `/api/v1/engagements/${engagementId}/access-tokens?include_revoked=${includeRevoked}`
    );
    if (!res.ok) throw new Error("Failed to list access tokens");
    return res.json() as Promise<AuditAccessToken[]>;
  },

  revokeAccessToken: async (engagementId: string, tokenId: string): Promise<void> => {
    const res = await fetchWithAuth(
      `/api/v1/engagements/${engagementId}/access-tokens/${tokenId}`,
      { method: "DELETE" }
    );
    if (!res.ok) throw new Error("Failed to revoke token");
  },

  listRequests: async (engagementId: string, status?: string): Promise<AuditorRequest[]> => {
    const params = new URLSearchParams();
    if (status) params.set("status", status);
    const qs = params.toString();
    const res = await fetchWithAuth(
      `/api/v1/engagements/${engagementId}/requests${qs ? `?${qs}` : ""}`
    );
    if (!res.ok) throw new Error("Failed to list auditor requests");
    return res.json() as Promise<AuditorRequest[]>;
  },

  fulfillRequest: async (
    engagementId: string,
    requestId: string,
    action: "fulfill" | "dismiss",
    responseNotes?: string,
    attachmentIds?: string[],
  ): Promise<AuditorRequest> => {
    const res = await fetchWithAuth(
      `/api/v1/engagements/${engagementId}/requests/${requestId}`,
      {
        method: "PATCH",
        body: JSON.stringify({ action, response_notes: responseNotes, attachment_ids: attachmentIds }),
      }
    );
    if (!res.ok) throw new Error("Failed to update request");
    return res.json() as Promise<AuditorRequest>;
  },

  revokeRequestAccess: async (
    engagementId: string,
    requestId: string,
    responseNotes?: string,
  ): Promise<AuditorRequest> => {
    const res = await fetchWithAuth(
      `/api/v1/engagements/${engagementId}/requests/${requestId}/revoke`,
      {
        method: "POST",
        body: JSON.stringify({ response_notes: responseNotes }),
      },
    );
    if (!res.ok) throw new Error("Failed to revoke evidence access");
    return res.json() as Promise<AuditorRequest>;
  },

  listEngagementTasks: async (engagementId: string): Promise<TaskListResponse> => {
    const res = await fetchWithAuth(`/api/v1/engagements/${engagementId}/tasks`);
    if (!res.ok) throw new Error("Failed to list engagement tasks");
    return res.json() as Promise<TaskListResponse>;
  },

  listEngagementParticipants: async (engagementId: string): Promise<EngagementParticipant[]> => {
    const res = await fetchWithAuth(`/api/v1/engagements/${engagementId}/participants`);
    if (!res.ok) throw new Error("Failed to list engagement participants");
    return res.json() as Promise<EngagementParticipant[]>;
  },

  createEngagementTask: async (
    engagementId: string,
    data: EngagementTaskCreateRequest,
  ): Promise<TaskResponse> => {
    const res = await fetchWithAuth(`/api/v1/engagements/${engagementId}/tasks`, {
      method: "POST",
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error((errData as { detail?: string }).detail || "Failed to create engagement task");
    }
    return res.json() as Promise<TaskResponse>;
  },

  listEngagementAssessments: async (engagementId: string): Promise<EngagementAssessment[]> => {
    const res = await fetchWithAuth(`/api/v1/engagements/${engagementId}/assessments`);
    if (!res.ok) throw new Error("Failed to list engagement assessments");
    return res.json() as Promise<EngagementAssessment[]>;
  },

  createEngagementAssessment: async (
    engagementId: string,
    data: {
      assessment_code?: string;
      name: string;
      description?: string;
      assessment_type_code?: string;
      scheduled_start?: string;
      scheduled_end?: string;
    }
  ): Promise<EngagementAssessment> => {
    const res = await fetchWithAuth(`/api/v1/engagements/${engagementId}/assessments`, {
      method: "POST",
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error((errData as { detail?: string }).detail || "Failed to create engagement assessment");
    }
    return res.json() as Promise<EngagementAssessment>;
  },

  listEngagementFindings: async (
    engagementId: string,
    assessmentId: string,
  ): Promise<EngagementFindingListResponse> => {
    const params = new URLSearchParams({ assessment_id: assessmentId });
    const res = await fetchWithAuth(`/api/v1/engagements/${engagementId}/findings?${params.toString()}`);
    if (!res.ok) throw new Error("Failed to list engagement findings");
    return res.json() as Promise<EngagementFindingListResponse>;
  },

  createEngagementFinding: async (
    engagementId: string,
    assessmentId: string,
    data: EngagementFindingCreateRequest,
  ): Promise<EngagementFinding> => {
    const params = new URLSearchParams({ assessment_id: assessmentId });
    const res = await fetchWithAuth(`/api/v1/engagements/${engagementId}/findings?${params.toString()}`, {
      method: "POST",
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error((errData as { detail?: string }).detail || "Failed to create engagement finding");
    }
    return res.json() as Promise<EngagementFinding>;
  },
  
  getControlDetail: async (engagementId: string, controlId: string): Promise<{
    verification: any;
    evidence: any[];
  }> => {
    const res = await fetchWithAuth(`/api/v1/engagements/${engagementId}/controls/${controlId}/detail`);
    if (!res.ok) throw new Error("Failed to get control detail");
    return res.json();
  },

  verifyControl: async (engagementId: string, controlId: string, data: {
    outcome: string;
    observations?: string;
    finding_details?: string;
  }): Promise<{ success: boolean }> => {
    const res = await fetchWithAuth(`/api/v1/engagements/${engagementId}/controls/${controlId}/verify`, {
      method: "POST",
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error((errData as { detail?: string }).detail || "Failed to verify control");
    }
    return res.json();
  },

  requestDocs: async (engagementId: string, controlId: string, data: {
    description: string;
  }): Promise<{ id: string }> => {
    const res = await fetchWithAuth(`/api/v1/engagements/${engagementId}/controls/${controlId}/request-docs`, {
      method: "POST",
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error((errData as { detail?: string }).detail || "Failed to request docs");
    }
    return res.json();
  },
  
  requestTaskAccess: async (engagementId: string, taskId: string, data: {
    description: string;
  }): Promise<{ id: string }> => {
    const res = await fetchWithAuth(`/api/v1/engagements/${engagementId}/tasks/${taskId}/request-access`, {
      method: "POST",
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error((errData as { detail?: string }).detail || "Failed to request task access");
    }
    return res.json();
  },
};
