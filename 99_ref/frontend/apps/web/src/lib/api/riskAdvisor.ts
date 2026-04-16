import { fetchWithAuth } from "./apiClient"

// ── Types ─────────────────────────────────────────────────────────────────────

export interface ControlSuggestion {
  control_id: string
  control_code: string
  control_name: string | null
  control_category_code: string | null
  criticality_code: string | null
  framework_id: string
  framework_code: string
  framework_name: string | null
  suggested_link_type: "mitigating" | "compensating" | "related"
  relevance_score: number
  rationale: string
  already_linked: boolean
}

export interface SuggestControlsResponse {
  risk_id: string
  risk_code: string
  risk_title: string
  suggestions: ControlSuggestion[]
  total_candidates_evaluated: number
  suggestion_error: string | null
}

export interface BulkLinkRequest {
  framework_id?: string | null   // null/undefined = all frameworks
  risk_id?: string | null        // null/undefined = all risks in workspace
  org_id: string
  workspace_id: string
  priority_code?: string
  dry_run?: boolean
}

export interface BulkLinkJobResponse {
  job_id: string
  status: string
  framework_id: string
  dry_run: boolean
}

export interface JobStatusResponse {
  job_id: string
  status_code: string
  job_type: string
  progress_pct: number | null
  output_json: Record<string, unknown> | null
  error_message: string | null
  created_at: string
  updated_at: string
}

/** A pending (AI-proposed) risk-control mapping awaiting approval */
export interface PendingMapping {
  id: string
  risk_id: string
  control_id: string
  link_type: "mitigating" | "compensating" | "related"
  notes: string | null
  created_at: string
  approval_status: "pending" | "approved" | "rejected"
  ai_confidence: number | null
  ai_rationale: string | null
  control_code: string | null
  control_name: string | null
  risk_code: string | null
  risk_title: string | null
}

export interface PendingMappingsResponse {
  items: PendingMapping[]
  total: number
}

// ── Bulk link / job ────────────────────────────────────────────────────────────

export async function suggestControlsForRisk(params: {
  risk_id: string
  org_id: string
  workspace_id: string
  framework_ids?: string[]
  top_n?: number
}): Promise<SuggestControlsResponse> {
  const res = await fetchWithAuth("/api/v1/ai/risk-advisor/suggest-controls", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || "Failed to get control suggestions")
  return data as SuggestControlsResponse
}

export async function enqueueBulkLink(req: BulkLinkRequest): Promise<BulkLinkJobResponse> {
  const res = await fetchWithAuth("/api/v1/ai/risk-advisor/bulk-link", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || "Failed to enqueue bulk link job")
  return data as BulkLinkJobResponse
}

export async function getRiskAdvisorJobStatus(jobId: string): Promise<JobStatusResponse> {
  const res = await fetchWithAuth(`/api/v1/ai/risk-advisor/jobs/${jobId}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || "Failed to get job status")
  return data as JobStatusResponse
}

// ── Pending mappings (approval queue) ─────────────────────────────────────────

export async function listPendingMappings(params: {
  org_id: string
  workspace_id?: string
  limit?: number
  offset?: number
}): Promise<PendingMappingsResponse> {
  const qs = new URLSearchParams({ org_id: params.org_id })
  if (params.workspace_id) qs.set("workspace_id", params.workspace_id)
  if (params.limit) qs.set("limit", String(params.limit))
  if (params.offset) qs.set("offset", String(params.offset))
  const res = await fetchWithAuth(`/api/v1/rr/risks-controls/pending?${qs}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || "Failed to list pending mappings")
  return data as PendingMappingsResponse
}

export async function approveMapping(
  riskId: string,
  mappingId: string,
  notes?: string,
): Promise<PendingMapping> {
  const res = await fetchWithAuth(
    `/api/v1/rr/risks/${riskId}/controls/${mappingId}/approve`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ notes: notes ?? null }),
    },
  )
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || "Failed to approve mapping")
  return data as PendingMapping
}

export async function rejectMapping(
  riskId: string,
  mappingId: string,
  rejection_reason?: string,
): Promise<void> {
  const res = await fetchWithAuth(
    `/api/v1/rr/risks/${riskId}/controls/${mappingId}/reject`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ rejection_reason: rejection_reason ?? null }),
    },
  )
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.detail || "Failed to reject mapping")
  }
}

export async function bulkApproveMappings(
  orgId: string,
  mappingIds: string[],
): Promise<{ approved: number }> {
  const res = await fetchWithAuth(
    `/api/v1/rr/risks-controls/bulk-approve?org_id=${orgId}`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mapping_ids: mappingIds }),
    },
  )
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || "Failed to bulk approve")
  return data as { approved: number }
}

export async function bulkRejectMappings(
  orgId: string,
  mappingIds: string[],
  rejection_reason?: string,
): Promise<{ rejected: number }> {
  const res = await fetchWithAuth(
    `/api/v1/rr/risks-controls/bulk-reject?org_id=${orgId}`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mapping_ids: mappingIds, rejection_reason: rejection_reason ?? null }),
    },
  )
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || "Failed to bulk reject")
  return data as { rejected: number }
}
