import { fetchWithAuth } from "./apiClient"
import type {
  AssessmentDimension,
  AssessmentResponse,
  AssessmentListResponse,
  CreateAssessmentRequest,
  UpdateAssessmentRequest,
  AssessmentSummaryResponse,
  FindingResponse,
  FindingListResponse,
  CreateFindingRequest,
  UpdateFindingRequest,
  FindingResponseResponse,
  FindingResponseListResponse,
  CreateFindingResponseRequest,
} from "../types/assessments"

function parseApiError(data: Record<string, unknown>, fallback: string): string {
  if (data.error && typeof (data.error as Record<string, unknown>).message === "string")
    return (data.error as Record<string, unknown>).message as string
  if (Array.isArray(data.detail)) {
    return data.detail
      .map((d: Record<string, unknown>) => {
        const field = Array.isArray(d.loc) ? (d.loc as string[]).slice(1).join(".") : ""
        return field ? `${field}: ${d.msg}` : (d.msg as string)
      })
      .join("; ")
  }
  if (typeof data.detail === "string") return data.detail
  return fallback
}

// ── Dimensions ───────────────────────────────────────────────────────────────

export async function listAssessmentTypes(): Promise<AssessmentDimension[]> {
  const res = await fetchWithAuth("/api/v1/as/assessments/types")
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list assessment types")
  return (data.items ?? data) as AssessmentDimension[]
}

export async function listAssessmentStatuses(): Promise<AssessmentDimension[]> {
  const res = await fetchWithAuth("/api/v1/as/assessments/statuses")
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list assessment statuses")
  return (data.items ?? data) as AssessmentDimension[]
}

export async function listFindingSeverities(): Promise<AssessmentDimension[]> {
  const res = await fetchWithAuth("/api/v1/as/assessments/finding-severities")
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list finding severities")
  return (data.items ?? data) as AssessmentDimension[]
}

export async function listFindingStatuses(): Promise<AssessmentDimension[]> {
  const res = await fetchWithAuth("/api/v1/as/assessments/finding-statuses")
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list finding statuses")
  return (data.items ?? data) as AssessmentDimension[]
}

// ── Assessments ──────────────────────────────────────────────────────────────

export async function listAssessments(
  orgId: string,
  params?: { workspace_id?: string; type_code?: string; status?: string; search?: string; limit?: number; offset?: number }
): Promise<AssessmentListResponse> {
  const query = new URLSearchParams({ org_id: orgId })
  if (params?.workspace_id) query.set("workspace_id", params.workspace_id)
  if (params?.type_code) query.set("type_code", params.type_code)
  if (params?.status) query.set("status", params.status)
  if (params?.search) query.set("search", params.search)
  if (params?.limit != null) query.set("limit", String(params.limit))
  if (params?.offset != null) query.set("offset", String(params.offset))
  const res = await fetchWithAuth(`/api/v1/as/assessments?${query}`)
  const data = await res.json()
  if (!res.ok) throw new Error(parseApiError(data, "Failed to list assessments"))
  return data as AssessmentListResponse
}

export async function getAssessment(assessmentId: string): Promise<AssessmentResponse> {
  const res = await fetchWithAuth(`/api/v1/as/assessments/${assessmentId}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to get assessment")
  return data as AssessmentResponse
}

export async function createAssessment(payload: CreateAssessmentRequest): Promise<AssessmentResponse> {
  const res = await fetchWithAuth(`/api/v1/as/assessments`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(parseApiError(data, "Failed to create assessment"))
  return data as AssessmentResponse
}

export async function updateAssessment(assessmentId: string, payload: UpdateAssessmentRequest): Promise<AssessmentResponse> {
  const res = await fetchWithAuth(`/api/v1/as/assessments/${assessmentId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(parseApiError(data, "Failed to update assessment"))
  return data as AssessmentResponse
}

export async function completeAssessment(assessmentId: string): Promise<AssessmentResponse> {
  const res = await fetchWithAuth(`/api/v1/as/assessments/${assessmentId}/complete`, { method: "POST" })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to complete assessment")
  return data as AssessmentResponse
}

export async function getAssessmentSummary(assessmentId: string): Promise<AssessmentSummaryResponse> {
  const res = await fetchWithAuth(`/api/v1/as/assessments/${assessmentId}/summary`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to get assessment summary")
  return data as AssessmentSummaryResponse
}

export async function deleteAssessment(assessmentId: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/as/assessments/${assessmentId}`, { method: "DELETE" })
  if (res.status === 204) return
  if (!res.ok) {
    const data = await res.json()
    throw new Error(data.error?.message || "Failed to delete assessment")
  }
}

// ── Findings ─────────────────────────────────────────────────────────────────

export async function listFindings(assessmentId: string): Promise<FindingListResponse> {
  const res = await fetchWithAuth(`/api/v1/as/assessments/${assessmentId}/findings`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list findings")
  return data as FindingListResponse
}

export async function createFinding(assessmentId: string, payload: CreateFindingRequest): Promise<FindingResponse> {
  const res = await fetchWithAuth(`/api/v1/as/assessments/${assessmentId}/findings`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(parseApiError(data, "Failed to create finding"))
  return data as FindingResponse
}

export async function updateFinding(findingId: string, payload: UpdateFindingRequest): Promise<FindingResponse> {
  const res = await fetchWithAuth(`/api/v1/as/findings/${findingId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(parseApiError(data, "Failed to update finding"))
  return data as FindingResponse
}

export async function deleteFinding(findingId: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/as/findings/${findingId}`, { method: "DELETE" })
  if (res.status === 204) return
  if (!res.ok) {
    const data = await res.json()
    throw new Error(data.error?.message || "Failed to delete finding")
  }
}

// ── Finding Responses ────────────────────────────────────────────────────────

export async function listFindingResponses(findingId: string): Promise<FindingResponseListResponse> {
  const res = await fetchWithAuth(`/api/v1/as/findings/${findingId}/responses`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list finding responses")
  return data as FindingResponseListResponse
}

export async function createFindingResponse(findingId: string, payload: CreateFindingResponseRequest): Promise<FindingResponseResponse> {
  const res = await fetchWithAuth(`/api/v1/as/findings/${findingId}/responses`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(parseApiError(data, "Failed to submit finding response"))
  return data as FindingResponseResponse
}
