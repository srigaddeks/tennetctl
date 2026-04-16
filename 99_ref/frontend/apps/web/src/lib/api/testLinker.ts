import { fetchWithAuth } from "./apiClient"

export interface ControlSuggestion {
  control_id: string
  control_code: string
  confidence: number
  link_type: "covers" | "partially_covers" | "related"
  rationale: string
}

export interface TestSuggestion {
  test_id: string
  test_code: string
  confidence: number
  link_type: "covers" | "partially_covers" | "related"
  rationale: string
}

export interface PendingTestControlMapping {
  id: string
  control_test_id: string
  control_id: string
  link_type: "covers" | "partially_covers" | "related"
  ai_confidence: number | null
  ai_rationale: string | null
  approval_status: "pending" | "approved" | "rejected"
  created_at: string
  created_by: string | null
  test_name: string | null
  test_code: string | null
  control_name: string | null
  control_code: string | null
  framework_id: string | null
  framework_code: string | null
}

export interface PendingTestControlMappingListResponse {
  items: PendingTestControlMapping[]
  total: number
}

export interface ApplyResult {
  created: number
  skipped: number
}

export interface BulkTestLinkRequest {
  org_id: string
  workspace_id?: string | null
  framework_id?: string | null
  control_ids?: string[]
  test_ids?: string[]
  priority_code?: string
  dry_run?: boolean
}

export interface BulkTestLinkJobResponse {
  job_id: string
  status: string
  framework_id: string | null
  control_count: number | null
  test_count: number | null
  dry_run: boolean
}

export interface TestLinkerJobStatusResponse {
  job_id: string
  status_code: string
  job_type: string
  progress_pct: number | null
  output_json: Record<string, unknown> | null
  error_message: string | null
  created_at: string
  updated_at: string
}

export async function suggestControlsForTest(params: {
  test_id: string
  framework_id?: string
  org_id?: string
  workspace_id?: string
}): Promise<ControlSuggestion[]> {
  const res = await fetchWithAuth("/api/v1/ai/test-linker/suggest-controls", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || "Failed to get control suggestions")
  return data as ControlSuggestion[]
}

export async function suggestTestsForControl(params: {
  control_id: string
  org_id?: string
  workspace_id?: string
}): Promise<TestSuggestion[]> {
  const res = await fetchWithAuth("/api/v1/ai/test-linker/suggest-tests", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || "Failed to get test suggestions")
  return data as TestSuggestion[]
}

export async function applyTestLinkerSuggestions(params: {
  test_id: string
  suggestions: ControlSuggestion[]
}): Promise<ApplyResult> {
  const res = await fetchWithAuth("/api/v1/ai/test-linker/apply-for-test", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || "Failed to apply suggestions")
  return data as ApplyResult
}

export async function applyTestLinkerSuggestionsForControl(params: {
  control_id: string
  suggestions: TestSuggestion[]
}): Promise<ApplyResult> {
  const res = await fetchWithAuth("/api/v1/ai/test-linker/apply-for-control", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || "Failed to apply suggestions")
  return data as ApplyResult
}

export async function enqueueBulkTestLink(req: BulkTestLinkRequest): Promise<BulkTestLinkJobResponse> {
  const res = await fetchWithAuth("/api/v1/ai/test-linker/bulk-link", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || "Failed to enqueue bulk link job")
  return data as BulkTestLinkJobResponse
}

export async function getTestLinkerJobStatus(jobId: string): Promise<TestLinkerJobStatusResponse> {
  const res = await fetchWithAuth(`/api/v1/ai/test-linker/jobs/${jobId}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || "Failed to get job status")
  return data as TestLinkerJobStatusResponse
}

export async function approveTestControlMapping(mappingId: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/ai/test-linker/mappings/${mappingId}/approve`, {
    method: "POST",
  })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.detail || "Failed to approve mapping")
  }
}

export async function rejectTestControlMapping(mappingId: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/ai/test-linker/mappings/${mappingId}/reject`, {
    method: "POST",
  })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.detail || "Failed to reject mapping")
  }
}

export async function bulkApproveTestControlMappings(mappingIds: string[]): Promise<{ updated: number }> {
  const res = await fetchWithAuth("/api/v1/ai/test-linker/mappings/bulk-approve", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ mapping_ids: mappingIds }),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || "Failed to bulk approve")
  return data as { updated: number }
}

export async function bulkRejectTestControlMappings(
  mappingIds: string[],
  reason?: string,
): Promise<{ updated: number }> {
  const res = await fetchWithAuth("/api/v1/ai/test-linker/mappings/bulk-reject", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ mapping_ids: mappingIds, reason: reason ?? null }),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || "Failed to bulk reject")
  return data as { updated: number }
}

export async function listPendingTestControlMappings(params?: {
  org_id?: string
  workspace_id?: string
  framework_id?: string
  control_ids?: string[]
  test_ids?: string[]
  created_after?: string
  mine_only?: boolean
  limit?: number
  offset?: number
}): Promise<PendingTestControlMappingListResponse> {
  const qs = new URLSearchParams()
  if (params?.org_id) qs.set("org_id", params.org_id)
  if (params?.workspace_id) qs.set("workspace_id", params.workspace_id)
  if (params?.framework_id) qs.set("framework_id", params.framework_id)
  if (params?.created_after) qs.set("created_after", params.created_after)
  if (params?.mine_only !== undefined) qs.set("mine_only", String(params.mine_only))
  if (params?.limit !== undefined) qs.set("limit", String(params.limit))
  if (params?.offset !== undefined) qs.set("offset", String(params.offset))
  for (const controlId of params?.control_ids ?? []) qs.append("control_ids", controlId)
  for (const testId of params?.test_ids ?? []) qs.append("test_ids", testId)

  const res = await fetchWithAuth(`/api/v1/ai/test-linker/pending${qs.toString() ? `?${qs}` : ""}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || "Failed to list pending mappings")
  return data as PendingTestControlMappingListResponse
}
