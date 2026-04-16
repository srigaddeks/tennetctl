import { fetchWithAuth } from "./apiClient"

// ── Error helper ────────────────────────────────────────────────────────────
// Pydantic validation errors come as { detail: [{ msg, loc, ... }] }
// App errors come as { error: { message } }
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
import type {
  ControlListResponse,
  ControlResponse,
  CreateControlRequest,
  CreateFrameworkRequest,
  CreateRequirementRequest,
  CreateRiskAssessmentRequest,
  CreateRiskControlMappingRequest,
  CreateRiskGroupAssignmentRequest,
  CreateRiskRequest,
  CreateRiskReviewEventRequest,
  CreateTaskAssignmentRequest,
  CreateTaskDependencyRequest,
  CreateTaskEventRequest,
  TaskDependencyListResponse,
  CreateTaskRequest,
  CreateTestControlMappingRequest,
  CreateTestExecutionRequest,
  CreateTestRequest,
  CreateTreatmentPlanRequest,
  CreateVersionRequest,
  DimensionResponse,
  FrameworkListResponse,
  FrameworkResponse,
  FrameworkSettingResponse,
  HeatMapResponse,
  OverdueReviewResponse,
  RequirementListResponse,
  RequirementResponse,
  ReviewScheduleResponse,
  ReviewSelectionResponse,
  RiskAppetiteResponse,
  RiskAssessmentResponse,
  RiskControlMappingResponse,
  RiskGroupAssignmentResponse,
  RiskLevelResponse,
  RiskListResponse,
  RiskResponse,
  RiskReviewEventResponse,
  RiskSummaryResponse,
  SetFrameworkSettingRequest,
  TaskAssignmentResponse,
  TaskDependencyResponse,
  TaskEventResponse,
  TaskListFilters,
  TaskListResponse,
  TaskResponse,
  TaskStatusResponse,
  TaskSummaryResponse,
  TestControlMappingResponse,
  TestExecutionListResponse,
  TestExecutionResponse,
  TestListResponse,
  TestResponse,
  TreatmentPlanResponse,
  UpdateControlRequest,
  UpdateFrameworkRequest,
  UpdateRequirementRequest,
  UpdateRiskRequest,
  UpdateTaskRequest,
  UpdateTestExecutionRequest,
  UpdateTestRequest,
  UpdateTreatmentPlanRequest,
  UpsertReviewScheduleRequest,
  UpsertRiskAppetiteRequest,
  VersionListResponse,
  VersionResponse,
} from "../types/grc"

// ═══════════════════════════════════════════════════════════════════════════════
// ── Framework Library (/api/v1/fr) ──────────────────────────────────────────
// ═══════════════════════════════════════════════════════════════════════════════

// ── Dimensions ──────────────────────────────────────────────────────────────

export async function listFrameworkTypes(): Promise<DimensionResponse[]> {
  const res = await fetchWithAuth("/api/v1/fr/framework-types")
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list framework types")
  return data as DimensionResponse[]
}

export async function listFrameworkCategories(): Promise<DimensionResponse[]> {
  const res = await fetchWithAuth("/api/v1/fr/framework-categories")
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list framework categories")
  return data as DimensionResponse[]
}

export async function listControlCategories(): Promise<DimensionResponse[]> {
  const res = await fetchWithAuth("/api/v1/fr/control-categories")
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list control categories")
  return data as DimensionResponse[]
}

export async function listControlCriticalities(): Promise<DimensionResponse[]> {
  const res = await fetchWithAuth("/api/v1/fr/control-criticalities")
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list control criticalities")
  return data as DimensionResponse[]
}

export async function listTestTypes(): Promise<DimensionResponse[]> {
  const res = await fetchWithAuth("/api/v1/fr/test-types")
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list test types")
  return data as DimensionResponse[]
}

export async function listTestResultStatuses(): Promise<DimensionResponse[]> {
  const res = await fetchWithAuth("/api/v1/fr/test-result-statuses")
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list test result statuses")
  return data as DimensionResponse[]
}

// ── Frameworks ──────────────────────────────────────────────────────────────

export async function listFrameworks(filters?: {
  scope_org_id?: string
  scope_workspace_id?: string
  deployed_org_id?: string
  deployed_workspace_id?: string
  category?: string
  framework_type?: string
  search?: string
  is_marketplace_visible?: boolean
  is_active?: boolean
  approval_status?: string
  only_engaged?: boolean
}): Promise<FrameworkListResponse> {
  const params = new URLSearchParams()
  if (filters?.scope_org_id) params.set("scope_org_id", filters.scope_org_id)
  if (filters?.scope_workspace_id) params.set("scope_workspace_id", filters.scope_workspace_id)
  if (filters?.deployed_org_id) params.set("deployed_org_id", filters.deployed_org_id)
  if (filters?.deployed_workspace_id) params.set("deployed_workspace_id", filters.deployed_workspace_id)
  if (filters?.category) params.set("category", filters.category)
  if (filters?.framework_type) params.set("framework_type", filters.framework_type)
  if (filters?.search) params.set("search", filters.search)
  if (filters?.is_marketplace_visible !== undefined) params.set("is_marketplace_visible", String(filters.is_marketplace_visible))
  if (filters?.is_active !== undefined) params.set("is_active", String(filters.is_active))
  if (filters?.approval_status) params.set("approval_status", filters.approval_status)
  if (filters?.only_engaged !== undefined) params.set("only_engaged", String(filters.only_engaged))
  
  const qs = params.toString()
  const res = await fetchWithAuth(`/api/v1/fr/frameworks${qs ? `?${qs}` : ""}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list frameworks")
  return data as FrameworkListResponse
}

export async function getFramework(frameworkId: string): Promise<FrameworkResponse> {
  const res = await fetchWithAuth(`/api/v1/fr/frameworks/${frameworkId}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to get framework")
  return data as FrameworkResponse
}

export async function createFramework(payload: CreateFrameworkRequest): Promise<FrameworkResponse> {
  const res = await fetchWithAuth("/api/v1/fr/frameworks", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(parseApiError(data, "Failed to create framework"))
  return data as FrameworkResponse
}

export async function updateFramework(frameworkId: string, payload: UpdateFrameworkRequest): Promise<FrameworkResponse> {
  const res = await fetchWithAuth(`/api/v1/fr/frameworks/${frameworkId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to update framework")
  return data as FrameworkResponse
}

export async function deleteFramework(frameworkId: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/fr/frameworks/${frameworkId}`, {
    method: "DELETE",
  })
  if (!res.ok) {
    const data = await res.json()
    throw new Error(data.error?.message || "Failed to delete framework")
  }
}

// ── Framework Approval Workflow ──────────────────────────────────────────────

export async function submitFrameworkForReview(frameworkId: string): Promise<FrameworkResponse> {
  const res = await fetchWithAuth(`/api/v1/fr/frameworks/${frameworkId}/submit`, { method: "POST" })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to submit for review")
  return data as FrameworkResponse
}

export async function submitFrameworkSelective(
  frameworkId: string,
  payload: {
    requirement_ids?: string[]
    control_ids?: string[]
    notes?: string
  }
): Promise<FrameworkResponse> {
  const res = await fetchWithAuth(`/api/v1/fr/frameworks/${frameworkId}/submit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to submit for review")
  return data as FrameworkResponse
}

export async function getReviewSelection(frameworkId: string): Promise<ReviewSelectionResponse> {
  const res = await fetchWithAuth(`/api/v1/fr/frameworks/${frameworkId}/review-selection`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to get review selection")
  return data as ReviewSelectionResponse
}

export type ReviewDiff = {
  has_previous_version: boolean
  previous_version_code: string | null
  added: Array<{ id: string; control_code: string; name: string | null; criticality_code: string | null }>
  removed: Array<{ id: string; control_code: string; name: string | null; criticality_code: string | null }>
  added_count: number
  removed_count: number
}

export async function getReviewDiff(frameworkId: string): Promise<ReviewDiff> {
  const res = await fetchWithAuth(`/api/v1/fr/frameworks/${frameworkId}/review-diff`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to get review diff")
  return data as ReviewDiff
}

export async function approveFramework(frameworkId: string, controlIds?: string[]): Promise<FrameworkResponse> {
  const res = await fetchWithAuth(`/api/v1/fr/frameworks/${frameworkId}/approve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ control_ids: controlIds ?? [] }),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to approve framework")
  return data as FrameworkResponse
}

export async function rejectFramework(frameworkId: string, reason?: string): Promise<FrameworkResponse> {
  const url = reason
    ? `/api/v1/fr/frameworks/${frameworkId}/reject?reason=${encodeURIComponent(reason)}`
    : `/api/v1/fr/frameworks/${frameworkId}/reject`
  const res = await fetchWithAuth(url, { method: "POST" })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to reject framework")
  return data as FrameworkResponse
}

// ── Versions ────────────────────────────────────────────────────────────────

export async function listVersions(
  frameworkId: string,
  filters?: { scope_org_id?: string; scope_workspace_id?: string },
): Promise<VersionListResponse> {
  const params = new URLSearchParams()
  if (filters?.scope_org_id) params.set("scope_org_id", filters.scope_org_id)
  if (filters?.scope_workspace_id) params.set("scope_workspace_id", filters.scope_workspace_id)
  const qs = params.toString()
  const res = await fetchWithAuth(`/api/v1/fr/frameworks/${frameworkId}/versions${qs ? `?${qs}` : ""}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list versions")
  return data as VersionListResponse
}

export async function getVersion(frameworkId: string, versionId: string): Promise<VersionResponse> {
  const res = await fetchWithAuth(`/api/v1/fr/frameworks/${frameworkId}/versions/${versionId}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to get version")
  return data as VersionResponse
}

export async function createVersion(frameworkId: string, payload: CreateVersionRequest): Promise<VersionResponse> {
  const res = await fetchWithAuth(`/api/v1/fr/frameworks/${frameworkId}/versions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(parseApiError(data, "Failed to create version"))
  return data as VersionResponse
}

export async function publishVersion(frameworkId: string, versionId: string): Promise<VersionResponse> {
  const res = await fetchWithAuth(`/api/v1/fr/frameworks/${frameworkId}/versions/${versionId}/publish`, {
    method: "POST",
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to publish version")
  return data as VersionResponse
}

export async function deprecateVersion(frameworkId: string, versionId: string): Promise<VersionResponse> {
  const res = await fetchWithAuth(`/api/v1/fr/frameworks/${frameworkId}/versions/${versionId}/deprecate`, {
    method: "POST",
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to deprecate version")
  return data as VersionResponse
}

export async function restoreVersion(frameworkId: string, versionId: string): Promise<VersionResponse> {
  const res = await fetchWithAuth(`/api/v1/fr/frameworks/${frameworkId}/versions/${versionId}/restore`, {
    method: "POST",
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to restore version")
  return data as VersionResponse
}

// ── Requirements ────────────────────────────────────────────────────────────

export async function listRequirements(frameworkId: string): Promise<RequirementListResponse> {
  const res = await fetchWithAuth(`/api/v1/fr/frameworks/${frameworkId}/requirements`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list requirements")
  return data as RequirementListResponse
}

export async function createRequirement(frameworkId: string, payload: CreateRequirementRequest): Promise<RequirementResponse> {
  const res = await fetchWithAuth(`/api/v1/fr/frameworks/${frameworkId}/requirements`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(parseApiError(data, "Failed to create requirement"))
  return data as RequirementResponse
}

export async function updateRequirement(frameworkId: string, requirementId: string, payload: UpdateRequirementRequest): Promise<RequirementResponse> {
  const res = await fetchWithAuth(`/api/v1/fr/frameworks/${frameworkId}/requirements/${requirementId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to update requirement")
  return data as RequirementResponse
}

export async function deleteRequirement(frameworkId: string, requirementId: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/fr/frameworks/${frameworkId}/requirements/${requirementId}`, {
    method: "DELETE",
  })
  if (!res.ok) {
    const data = await res.json()
    throw new Error(data.error?.message || "Failed to delete requirement")
  }
}

// ── Controls ────────────────────────────────────────────────────────────────
export async function listAllControls(filters?: {
  search?: string
  framework_id?: string
  scope_org_id?: string
  scope_workspace_id?: string
  deployed_org_id?: string
  deployed_workspace_id?: string
  control_category_code?: string
  criticality_code?: string
  control_type?: string
  automation_potential?: string
  limit?: number
  offset?: number
  engagement_id?: string
}): Promise<ControlListResponse> {
  const params = new URLSearchParams()
  if (filters?.search) params.set("search", filters.search)
  if (filters?.framework_id) params.set("framework_id", filters.framework_id)
  if (filters?.scope_org_id) params.set("scope_org_id", filters.scope_org_id)
  if (filters?.scope_workspace_id) params.set("scope_workspace_id", filters.scope_workspace_id)
  if (filters?.deployed_org_id) params.set("deployed_org_id", filters.deployed_org_id)
  if (filters?.deployed_workspace_id) params.set("deployed_workspace_id", filters.deployed_workspace_id)
  if (filters?.control_category_code) params.set("control_category_code", filters.control_category_code)
  if (filters?.criticality_code) params.set("criticality_code", filters.criticality_code)
  if (filters?.control_type) params.set("control_type", filters.control_type)
  if (filters?.automation_potential) params.set("automation_potential", filters.automation_potential)
  if (filters?.limit) params.set("limit", String(filters.limit))
  if (filters?.offset) params.set("offset", String(filters.offset))
  if (filters?.engagement_id) params.set("engagement_id", filters.engagement_id)
  const qs = params.toString()
  const res = await fetchWithAuth(`/api/v1/fr/controls${qs ? `?${qs}` : ""}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list controls")
  return data as ControlListResponse
}

export async function listControls(frameworkId: string, filters?: {
  search?: string
  control_category_code?: string
  criticality_code?: string
  control_type?: string
  automation_potential?: string
  limit?: number
  offset?: number
}): Promise<ControlListResponse> {
  const params = new URLSearchParams()
  if (filters?.search) params.set("search", filters.search)
  if (filters?.control_category_code) params.set("control_category_code", filters.control_category_code)
  if (filters?.criticality_code) params.set("criticality_code", filters.criticality_code)
  if (filters?.control_type) params.set("control_type", filters.control_type)
  if (filters?.automation_potential) params.set("automation_potential", filters.automation_potential)
  if (filters?.limit) params.set("limit", String(filters.limit))
  if (filters?.offset) params.set("offset", String(filters.offset))
  const qs = params.toString()
  const res = await fetchWithAuth(`/api/v1/fr/frameworks/${frameworkId}/controls${qs ? `?${qs}` : ""}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list controls")
  return data as ControlListResponse
}

export async function getControl(frameworkId: string, controlId: string): Promise<ControlResponse> {
  const res = await fetchWithAuth(`/api/v1/fr/frameworks/${frameworkId}/controls/${controlId}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to get control")
  return data as ControlResponse
}

export async function createControl(frameworkId: string, payload: CreateControlRequest): Promise<ControlResponse> {
  const res = await fetchWithAuth(`/api/v1/fr/frameworks/${frameworkId}/controls`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(parseApiError(data, "Failed to create control"))
  return data as ControlResponse
}

export async function updateControl(frameworkId: string, controlId: string, payload: UpdateControlRequest): Promise<ControlResponse> {
  const res = await fetchWithAuth(`/api/v1/fr/frameworks/${frameworkId}/controls/${controlId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to update control")
  return data as ControlResponse
}

export async function deleteControl(frameworkId: string, controlId: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/fr/frameworks/${frameworkId}/controls/${controlId}`, {
    method: "DELETE",
  })
  if (!res.ok) {
    const data = await res.json()
    throw new Error(data.error?.message || "Failed to delete control")
  }
}

// ── Tests ───────────────────────────────────────────────────────────────────

export async function listControlTests(frameworkId: string, controlId: string): Promise<TestListResponse> {
  const res = await fetchWithAuth(`/api/v1/fr/frameworks/${frameworkId}/controls/${controlId}/tests`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list tests")
  return data as TestListResponse
}

export async function listAvailableTestsForControl(
  frameworkId: string,
  controlId: string,
  filters?: { search?: string; limit?: number },
): Promise<TestListResponse> {
  const params = new URLSearchParams()
  if (filters?.search) params.set("search", filters.search)
  if (filters?.limit) params.set("limit", String(filters.limit))
  const qs = params.toString()
  const res = await fetchWithAuth(
    `/api/v1/fr/frameworks/${frameworkId}/controls/${controlId}/tests/available${qs ? `?${qs}` : ""}`,
  )
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list available tests")
  return data as TestListResponse
}

export async function listTests(filters?: {
  search?: string
  test_type_code?: string
  is_platform_managed?: boolean
  monitoring_frequency?: string
  scope_org_id?: string
  scope_workspace_id?: string
  limit?: number
  offset?: number
}): Promise<TestListResponse> {
  const params = new URLSearchParams()
  if (filters?.search) params.set("search", filters.search)
  if (filters?.test_type_code) params.set("test_type_code", filters.test_type_code)
  if (filters?.is_platform_managed !== undefined) params.set("is_platform_managed", String(filters.is_platform_managed))
  if (filters?.monitoring_frequency) params.set("monitoring_frequency", filters.monitoring_frequency)
  if (filters?.scope_org_id) params.set("scope_org_id", filters.scope_org_id)
  if (filters?.scope_workspace_id) params.set("scope_workspace_id", filters.scope_workspace_id)
  if (filters?.limit) params.set("limit", String(filters.limit))
  if (filters?.offset) params.set("offset", String(filters.offset))
  const qs = params.toString()
  const res = await fetchWithAuth(`/api/v1/fr/tests${qs ? `?${qs}` : ""}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list tests")
  return data as TestListResponse
}

export async function getTest(testId: string): Promise<TestResponse> {
  const res = await fetchWithAuth(`/api/v1/fr/tests/${testId}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to get test")
  return data as TestResponse
}

export async function createTest(payload: CreateTestRequest): Promise<TestResponse> {
  const res = await fetchWithAuth("/api/v1/fr/tests", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(parseApiError(data, "Failed to create test"))
  return data as TestResponse
}

export async function updateTest(testId: string, payload: UpdateTestRequest): Promise<TestResponse> {
  const res = await fetchWithAuth(`/api/v1/fr/tests/${testId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to update test")
  return data as TestResponse
}

export async function deleteTest(testId: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/fr/tests/${testId}`, {
    method: "DELETE",
  })
  if (!res.ok) {
    const data = await res.json()
    throw new Error(data.error?.message || "Failed to delete test")
  }
}

// ── Test Executions ─────────────────────────────────────────────────────────

export async function listTestExecutions(filters?: {
  control_test_id?: string
  control_id?: string
  result_status?: string
  limit?: number
  offset?: number
}): Promise<TestExecutionListResponse> {
  const params = new URLSearchParams()
  if (filters?.control_test_id) params.set("control_test_id", filters.control_test_id)
  if (filters?.control_id) params.set("control_id", filters.control_id)
  if (filters?.result_status) params.set("result_status", filters.result_status)
  if (filters?.limit) params.set("limit", String(filters.limit))
  if (filters?.offset) params.set("offset", String(filters.offset))
  const res = await fetchWithAuth(`/api/v1/fr/test-executions?${params}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list test executions")
  return data as TestExecutionListResponse
}

export async function createTestExecution(payload: CreateTestExecutionRequest): Promise<TestExecutionResponse> {
  const res = await fetchWithAuth("/api/v1/fr/test-executions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(parseApiError(data, "Failed to create test execution"))
  return data as TestExecutionResponse
}

export async function updateTestExecution(executionId: string, payload: UpdateTestExecutionRequest): Promise<TestExecutionResponse> {
  const res = await fetchWithAuth(`/api/v1/fr/test-executions/${executionId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to update test execution")
  return data as TestExecutionResponse
}

// ── Test-Control Mappings ───────────────────────────────────────────────────

export async function listTestMappings(testId: string): Promise<{ items: TestControlMappingResponse[]; total: number }> {
  const res = await fetchWithAuth(`/api/v1/fr/tests/${testId}/controls`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list test mappings")
  return data as { items: TestControlMappingResponse[]; total: number }
}

export async function createTestMapping(testId: string, payload: CreateTestControlMappingRequest): Promise<TestControlMappingResponse> {
  const res = await fetchWithAuth(`/api/v1/fr/tests/${testId}/controls`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(parseApiError(data, "Failed to create test mapping"))
  return data as TestControlMappingResponse
}

export async function deleteTestMapping(testId: string, mappingId: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/fr/tests/${testId}/controls/${mappingId}`, {
    method: "DELETE",
  })
  if (!res.ok) {
    const data = await res.json()
    throw new Error(data.error?.message || "Failed to delete test mapping")
  }
}

// ── Framework Settings ──────────────────────────────────────────────────────

export async function listFrameworkSettings(frameworkId: string): Promise<FrameworkSettingResponse[]> {
  const res = await fetchWithAuth(`/api/v1/fr/frameworks/${frameworkId}/settings`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list framework settings")
  return data as FrameworkSettingResponse[]
}

export async function setFrameworkSetting(frameworkId: string, key: string, payload: SetFrameworkSettingRequest): Promise<FrameworkSettingResponse> {
  const res = await fetchWithAuth(`/api/v1/fr/frameworks/${frameworkId}/settings/${key}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to set framework setting")
  return data as FrameworkSettingResponse
}

export async function deleteFrameworkSetting(frameworkId: string, key: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/fr/frameworks/${frameworkId}/settings/${key}`, {
    method: "DELETE",
  })
  if (!res.ok) {
    const data = await res.json()
    throw new Error(data.error?.message || "Failed to delete framework setting")
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// ── Risk Registry (/api/v1/rr) ──────────────────────────────────────────────
// ═══════════════════════════════════════════════════════════════════════════════

// ── Dimensions ──────────────────────────────────────────────────────────────

export async function listRiskCategories(): Promise<DimensionResponse[]> {
  const res = await fetchWithAuth("/api/v1/rr/risk-categories")
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list risk categories")
  return data as DimensionResponse[]
}

export async function listTreatmentTypes(): Promise<DimensionResponse[]> {
  const res = await fetchWithAuth("/api/v1/rr/treatment-types")
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list treatment types")
  return data as DimensionResponse[]
}

export async function listRiskLevels(): Promise<RiskLevelResponse[]> {
  const res = await fetchWithAuth("/api/v1/rr/risk-levels")
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list risk levels")
  return data as RiskLevelResponse[]
}

// ── Risks ───────────────────────────────────────────────────────────────────

export async function listRisks(filters?: {
  org_id?: string
  workspace_id?: string
  risk_category_code?: string
  risk_level_code?: string
  treatment_type_code?: string
  risk_status?: string
  search?: string
  control_id?: string
  limit?: number
  offset?: number
}): Promise<RiskListResponse> {
  const params = new URLSearchParams()
  if (filters?.org_id) params.set("org_id", filters.org_id)
  if (filters?.workspace_id) params.set("workspace_id", filters.workspace_id)
  if (filters?.risk_category_code) params.set("risk_category_code", filters.risk_category_code)
  if (filters?.risk_level_code) params.set("risk_level_code", filters.risk_level_code)
  if (filters?.treatment_type_code) params.set("treatment_type_code", filters.treatment_type_code)
  if (filters?.risk_status) params.set("risk_status", filters.risk_status)
  if (filters?.search) params.set("search", filters.search)
  if (filters?.control_id) params.set("control_id", filters.control_id)
  if (filters?.limit) params.set("limit", String(filters.limit))
  if (filters?.offset) params.set("offset", String(filters.offset))
  const qs = params.toString()
  const res = await fetchWithAuth(`/api/v1/rr/risks${qs ? `?${qs}` : ""}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list risks")
  return data as RiskListResponse
}

export async function getRisk(riskId: string): Promise<RiskResponse> {
  const res = await fetchWithAuth(`/api/v1/rr/risks/${riskId}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to get risk")
  return data as RiskResponse
}

export async function createRisk(payload: CreateRiskRequest): Promise<RiskResponse> {
  const res = await fetchWithAuth("/api/v1/rr/risks", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(parseApiError(data, "Failed to create risk"))
  return data as RiskResponse
}

export async function updateRisk(riskId: string, payload: UpdateRiskRequest): Promise<RiskResponse> {
  const res = await fetchWithAuth(`/api/v1/rr/risks/${riskId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to update risk")
  return data as RiskResponse
}

export async function deleteRisk(riskId: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/rr/risks/${riskId}`, {
    method: "DELETE",
  })
  if (!res.ok) {
    const data = await res.json()
    throw new Error(data.error?.message || "Failed to delete risk")
  }
}

// ── Assessments ─────────────────────────────────────────────────────────────

export async function listAssessments(riskId: string): Promise<RiskAssessmentResponse[]> {
  const res = await fetchWithAuth(`/api/v1/rr/risks/${riskId}/assessments`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list assessments")
  return data as RiskAssessmentResponse[]
}

export async function createAssessment(riskId: string, payload: CreateRiskAssessmentRequest): Promise<RiskAssessmentResponse> {
  const res = await fetchWithAuth(`/api/v1/rr/risks/${riskId}/assessments`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(parseApiError(data, "Failed to create assessment"))
  return data as RiskAssessmentResponse
}

// ── Treatment Plans ─────────────────────────────────────────────────────────

export async function getTreatmentPlan(riskId: string): Promise<TreatmentPlanResponse | null> {
  const res = await fetchWithAuth(`/api/v1/rr/risks/${riskId}/treatment-plan`)
  if (res.status === 404) return null
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to get treatment plan")
  return data as TreatmentPlanResponse
}

export async function createTreatmentPlan(riskId: string, payload: CreateTreatmentPlanRequest): Promise<TreatmentPlanResponse> {
  const res = await fetchWithAuth(`/api/v1/rr/risks/${riskId}/treatment-plan`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(parseApiError(data, "Failed to create treatment plan"))
  return data as TreatmentPlanResponse
}

export async function updateTreatmentPlan(riskId: string, payload: UpdateTreatmentPlanRequest): Promise<TreatmentPlanResponse> {
  const res = await fetchWithAuth(`/api/v1/rr/risks/${riskId}/treatment-plan`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to update treatment plan")
  return data as TreatmentPlanResponse
}

// ── Risk-Control Mappings ───────────────────────────────────────────────────

export async function listRiskControls(riskId: string): Promise<RiskControlMappingResponse[]> {
  const res = await fetchWithAuth(`/api/v1/rr/risks/${riskId}/controls`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list risk controls")
  return data as RiskControlMappingResponse[]
}

export async function addRiskControl(riskId: string, payload: CreateRiskControlMappingRequest): Promise<RiskControlMappingResponse> {
  const res = await fetchWithAuth(`/api/v1/rr/risks/${riskId}/controls`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(parseApiError(data, "Failed to add risk control"))
  return data as RiskControlMappingResponse
}

export async function removeRiskControl(riskId: string, mappingId: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/rr/risks/${riskId}/controls/${mappingId}`, {
    method: "DELETE",
  })
  if (!res.ok) {
    const data = await res.json()
    throw new Error(data.error?.message || "Failed to remove risk control")
  }
}

export async function listControlRisks(controlId: string, orgId: string): Promise<RiskControlMappingResponse[]> {
  const res = await fetchWithAuth(`/api/v1/rr/controls/${controlId}/risks?org_id=${orgId}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || data.error?.message || "Failed to list control risks")
  return data as RiskControlMappingResponse[]
}

export async function assignRiskToControl(controlId: string, orgId: string, payload: { risk_id: string; link_type?: string; notes?: string }): Promise<RiskControlMappingResponse> {
  const res = await fetchWithAuth(`/api/v1/rr/controls/${controlId}/risks?org_id=${orgId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || data.error?.message || "Failed to assign risk")
  return data as RiskControlMappingResponse
}

export async function unassignRiskFromControl(riskId: string, mappingId: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/rr/risks/${riskId}/controls/${mappingId}`, { method: "DELETE" })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.detail || data.error?.message || "Failed to unassign risk")
  }
}

// ── Review Events ───────────────────────────────────────────────────────────

export async function listReviewEvents(riskId: string): Promise<RiskReviewEventResponse[]> {
  const res = await fetchWithAuth(`/api/v1/rr/risks/${riskId}/events`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list review events")
  return data as RiskReviewEventResponse[]
}

export async function addReviewEvent(riskId: string, payload: CreateRiskReviewEventRequest): Promise<RiskReviewEventResponse> {
  const res = await fetchWithAuth(`/api/v1/rr/risks/${riskId}/events`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(parseApiError(data, "Failed to add review event"))
  return data as RiskReviewEventResponse
}

// ── Risk Heat Map ──────────────────────────────────────────────────────────

export async function getRiskHeatMap(orgId?: string, workspaceId?: string): Promise<HeatMapResponse> {
  const params = new URLSearchParams()
  if (orgId) params.set("org_id", orgId)
  if (workspaceId) params.set("workspace_id", workspaceId)
  const res = await fetchWithAuth(`/api/v1/rr/risks/heat-map?${params}`)
  if (!res.ok) throw new Error("Failed to load heat map data")
  return res.json()
}

// ── Risk Summary ───────────────────────────────────────────────────────────

export async function getRiskSummary(orgId?: string, workspaceId?: string): Promise<RiskSummaryResponse> {
  const params = new URLSearchParams()
  if (orgId) params.set("org_id", orgId)
  if (workspaceId) params.set("workspace_id", workspaceId)
  const res = await fetchWithAuth(`/api/v1/rr/risks/summary?${params}`)
  if (!res.ok) throw new Error("Failed to load risk summary")
  return res.json()
}

// ── Risk Export ────────────────────────────────────────────────────────────

export async function exportRisksCsv(orgId?: string): Promise<Blob> {
  const params = new URLSearchParams()
  if (orgId) params.set("org_id", orgId)
  const res = await fetchWithAuth(`/api/v1/rr/risks/export?${params}`)
  if (!res.ok) throw new Error("Failed to export risks")
  return res.blob()
}

// ── Risk Group Assignments ─────────────────────────────────────────────────

export async function listRiskGroups(riskId: string): Promise<RiskGroupAssignmentResponse[]> {
  const res = await fetchWithAuth(`/api/v1/rr/risks/${riskId}/groups`)
  if (!res.ok) throw new Error("Failed to load risk groups")
  const data = await res.json()
  return Array.isArray(data) ? data : (data.items ?? [])
}

export async function assignRiskGroup(riskId: string, payload: CreateRiskGroupAssignmentRequest): Promise<RiskGroupAssignmentResponse> {
  const res = await fetchWithAuth(`/api/v1/rr/risks/${riskId}/groups`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  if (!res.ok) throw new Error("Failed to assign group")
  return res.json()
}

export async function unassignRiskGroup(riskId: string, assignmentId: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/rr/risks/${riskId}/groups/${assignmentId}`, { method: "DELETE" })
  if (!res.ok) throw new Error("Failed to unassign group")
}

// ── Risk Appetite ──────────────────────────────────────────────────────────

export async function getRiskAppetite(orgId: string): Promise<RiskAppetiteResponse[]> {
  const res = await fetchWithAuth(`/api/v1/rr/risks/appetite?org_id=${orgId}`)
  if (!res.ok) throw new Error("Failed to load risk appetite")
  const data = await res.json()
  return Array.isArray(data) ? data : (data.items ?? [])
}

export async function upsertRiskAppetite(payload: UpsertRiskAppetiteRequest): Promise<RiskAppetiteResponse> {
  const res = await fetchWithAuth(`/api/v1/rr/risks/appetite`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  if (!res.ok) throw new Error("Failed to update risk appetite")
  return res.json()
}

// ── Review Scheduling ──────────────────────────────────────────────────────

export async function getReviewSchedule(riskId: string): Promise<ReviewScheduleResponse | null> {
  const res = await fetchWithAuth(`/api/v1/rr/risks/${riskId}/review-schedule`)
  if (res.status === 404) return null
  if (!res.ok) throw new Error("Failed to load review schedule")
  return res.json()
}

export async function upsertReviewSchedule(riskId: string, payload: UpsertReviewScheduleRequest): Promise<ReviewScheduleResponse> {
  const res = await fetchWithAuth(`/api/v1/rr/risks/${riskId}/review-schedule`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  if (!res.ok) throw new Error("Failed to update review schedule")
  return res.json()
}

export async function completeReview(riskId: string, nextReviewDate: string): Promise<ReviewScheduleResponse> {
  const res = await fetchWithAuth(`/api/v1/rr/risks/${riskId}/review-schedule/complete`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ next_review_date: nextReviewDate }),
  })
  if (!res.ok) throw new Error("Failed to complete review")
  return res.json()
}

export async function listOverdueReviews(orgId?: string): Promise<OverdueReviewResponse[]> {
  const params = new URLSearchParams()
  if (orgId) params.set("org_id", orgId)
  const res = await fetchWithAuth(`/api/v1/rr/risks/overdue-reviews?${params}`)
  if (!res.ok) throw new Error("Failed to load overdue reviews")
  const data = await res.json()
  return Array.isArray(data) ? data : (data.items ?? [])
}

// ═══════════════════════════════════════════════════════════════════════════════
// ── Tasks (/api/v1/tk) ─────────────────────────────────────────────────────
// ═══════════════════════════════════════════════════════════════════════════════

// ── Dimensions ──────────────────────────────────────────────────────────────

export async function listTaskTypes(): Promise<DimensionResponse[]> {
  const res = await fetchWithAuth("/api/v1/tk/task-types")
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list task types")
  return data as DimensionResponse[]
}

export async function listTaskPriorities(): Promise<DimensionResponse[]> {
  const res = await fetchWithAuth("/api/v1/tk/task-priorities")
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list task priorities")
  return data as DimensionResponse[]
}

export async function listTaskStatuses(): Promise<TaskStatusResponse[]> {
  const res = await fetchWithAuth("/api/v1/tk/task-statuses")
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list task statuses")
  return data as TaskStatusResponse[]
}

// ── Tasks ───────────────────────────────────────────────────────────────────

export async function listTasks(filters?: TaskListFilters & { orgId?: string; workspaceId?: string; engagementId?: string }): Promise<TaskListResponse> {
  const params = new URLSearchParams()
  if (filters?.orgId) params.set("org_id", filters.orgId)
  if (filters?.workspaceId) params.set("workspace_id", filters.workspaceId)
  if (filters?.engagementId) params.set("engagement_id", filters.engagementId)
  if (filters?.status_code) params.set("status_code", filters.status_code)
  if (filters?.priority_code) params.set("priority_code", filters.priority_code)
  if (filters?.task_type_code) params.set("task_type_code", filters.task_type_code)
  if (filters?.assignee_user_id) params.set("assignee_user_id", filters.assignee_user_id)
  if (filters?.reporter_user_id) params.set("reporter_user_id", filters.reporter_user_id)
  if (filters?.entity_type) params.set("entity_type", filters.entity_type)
  if (filters?.entity_id) params.set("entity_id", filters.entity_id)
  if (filters?.due_date_from) params.set("due_date_from", filters.due_date_from)
  if (filters?.due_date_to) params.set("due_date_to", filters.due_date_to)
  if (filters?.is_overdue) params.set("is_overdue", "true")
  if (filters?.sort_by) params.set("sort_by", filters.sort_by)
  if (filters?.sort_dir) params.set("sort_dir", filters.sort_dir)
  if (filters?.limit) params.set("limit", String(filters.limit))
  if (filters?.offset) params.set("offset", String(filters.offset))
  const qs = params.toString()
  const res = await fetchWithAuth(`/api/v1/tk/tasks${qs ? `?${qs}` : ""}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list tasks")
  return data as TaskListResponse
}

export async function getTaskSummary(orgId?: string, workspaceId?: string, engagementId?: string): Promise<TaskSummaryResponse> {
  const params = new URLSearchParams()
  if (orgId) params.set("org_id", orgId)
  if (workspaceId) params.set("workspace_id", workspaceId)
  const qs = params.toString()
  const res = await fetchWithAuth(`/api/v1/tk/tasks/summary${qs ? `?${qs}` : ""}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to load task summary")
  return data as TaskSummaryResponse
}

export async function getTask(taskId: string): Promise<TaskResponse> {
  const res = await fetchWithAuth(`/api/v1/tk/tasks/${taskId}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to get task")
  return data as TaskResponse
}

export async function createTask(payload: CreateTaskRequest): Promise<TaskResponse> {
  const normalizedPayload: CreateTaskRequest = {
    ...payload,
    entity_type: payload.entity_type?.trim() || undefined,
    entity_id: payload.entity_id?.trim() || undefined,
    assignee_user_id: payload.assignee_user_id?.trim() || undefined,
  }
  const res = await fetchWithAuth("/api/v1/tk/tasks", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(normalizedPayload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(parseApiError(data, "Failed to create task"))
  return data as TaskResponse
}

export async function updateTask(taskId: string, payload: UpdateTaskRequest): Promise<TaskResponse> {
  const res = await fetchWithAuth(`/api/v1/tk/tasks/${taskId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to update task")
  return data as TaskResponse
}

export async function submitTaskForReview(taskId: string): Promise<TaskResponse> {
  const res = await fetchWithAuth(`/api/v1/tk/tasks/${taskId}/submit-for-review`, {
    method: "POST",
  })
  const data = await res.json()
  if (!res.ok) throw new Error(parseApiError(data, "Failed to submit task for review"))
  return data as TaskResponse
}

export async function deleteTask(taskId: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/tk/tasks/${taskId}`, {
    method: "DELETE",
  })
  if (!res.ok) {
    const data = await res.json()
    throw new Error(data.error?.message || "Failed to delete task")
  }
}

export async function cloneTask(taskId: string): Promise<TaskResponse> {
  const res = await fetchWithAuth(`/api/v1/tk/tasks/${taskId}/clone`, {
    method: "POST",
  })
  const data = await res.json()
  if (!res.ok) throw new Error(parseApiError(data, "Failed to clone task"))
  return data as TaskResponse
}

export async function exportTasksCsv(filters?: TaskListFilters & { orgId?: string; workspaceId?: string }): Promise<Blob> {
  const params = new URLSearchParams()
  if (filters?.orgId) params.set("org_id", filters.orgId)
  if (filters?.workspaceId) params.set("workspace_id", filters.workspaceId)
  if (filters?.status_code) params.set("status_code", filters.status_code)
  if (filters?.priority_code) params.set("priority_code", filters.priority_code)
  if (filters?.task_type_code) params.set("task_type_code", filters.task_type_code)
  if (filters?.assignee_user_id) params.set("assignee_user_id", filters.assignee_user_id)
  if (filters?.is_overdue) params.set("is_overdue", "true")
  const qs = params.toString()
  const res = await fetchWithAuth(`/api/v1/tk/tasks/export${qs ? `?${qs}` : ""}`)
  if (!res.ok) throw new Error("Failed to export tasks")
  return res.blob()
}

export async function bulkUpdateTasks(payload: {
  task_ids: string[]
  status_code?: string
  priority_code?: string
  assignee_user_id?: string
}): Promise<{ updated_count: number; failed_ids: string[] }> {
  const res = await fetchWithAuth("/api/v1/tk/tasks/bulk-update", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(parseApiError(data, "Failed to bulk update tasks"))
  return data
}

// ── Task Assignments ────────────────────────────────────────────────────────

export async function listAssignments(taskId: string): Promise<TaskAssignmentResponse[]> {
  const res = await fetchWithAuth(`/api/v1/tk/tasks/${taskId}/assignments`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list assignments")
  return data as TaskAssignmentResponse[]
}

export async function addAssignment(taskId: string, payload: CreateTaskAssignmentRequest): Promise<TaskAssignmentResponse> {
  const res = await fetchWithAuth(`/api/v1/tk/tasks/${taskId}/assignments`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(parseApiError(data, "Failed to add assignment"))
  return data as TaskAssignmentResponse
}

export async function removeAssignment(taskId: string, assignmentId: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/tk/tasks/${taskId}/assignments/${assignmentId}`, {
    method: "DELETE",
  })
  if (!res.ok) {
    const data = await res.json()
    throw new Error(data.error?.message || "Failed to remove assignment")
  }
}

// ── Task Dependencies ───────────────────────────────────────────────────────

export async function listDependencies(taskId: string): Promise<TaskDependencyListResponse> {
  const res = await fetchWithAuth(`/api/v1/tk/tasks/${taskId}/dependencies`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list dependencies")
  return data as TaskDependencyListResponse
}

export async function addDependency(taskId: string, payload: CreateTaskDependencyRequest): Promise<TaskDependencyResponse> {
  const res = await fetchWithAuth(`/api/v1/tk/tasks/${taskId}/dependencies`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(parseApiError(data, "Failed to add dependency"))
  return data as TaskDependencyResponse
}

export async function removeDependency(taskId: string, dependencyId: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/tk/tasks/${taskId}/dependencies/${dependencyId}`, {
    method: "DELETE",
  })
  if (!res.ok) {
    const data = await res.json()
    throw new Error(data.error?.message || "Failed to remove dependency")
  }
}

// ── Task Events ─────────────────────────────────────────────────────────────

export async function listTaskEvents(taskId: string): Promise<TaskEventResponse[]> {
  const res = await fetchWithAuth(`/api/v1/tk/tasks/${taskId}/events`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list task events")
  // Backend returns { items: [], total: int }
  return (data.items ?? data) as TaskEventResponse[]
}

export async function addTaskEvent(taskId: string, comment: string): Promise<TaskEventResponse> {
  const res = await fetchWithAuth(`/api/v1/tk/tasks/${taskId}/events`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ comment }),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(parseApiError(data, "Failed to add task event"))
  return data as TaskEventResponse
}

export async function listTaskControls(taskId: string): Promise<ControlResponse[]> {
  const res = await fetchWithAuth(`/api/v1/tk/tasks/${taskId}/controls`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list task controls")
  return data as ControlResponse[]
}

// ── Deployments ──────────────────────────────────────────────────────────────

export async function listDeployments(
  orgId: string,
  workspaceId?: string,
): Promise<{ items: Array<{ id: string; framework_id: string; [key: string]: unknown }>; total: number }> {
  const params = new URLSearchParams({ org_id: orgId })
  if (workspaceId) params.set("workspace_id", workspaceId)
  const res = await fetchWithAuth(`/api/v1/fr/deployments?${params.toString()}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list deployments")
  return data
}

export async function deployFramework(payload: import("../types/grc").DeployFrameworkRequest & { org_id: string }): Promise<import("../types/grc").FrameworkDeploymentResponse> {
  const { org_id, ...body } = payload
  const res = await fetchWithAuth(`/api/v1/fr/deployments?org_id=${org_id}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to deploy framework")
  return data as import("../types/grc").FrameworkDeploymentResponse
}

export async function updateDeployment(deploymentId: string, payload: { version_id: string }): Promise<import("../types/grc").FrameworkDeploymentResponse> {
  const res = await fetchWithAuth(`/api/v1/fr/deployments/${deploymentId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to update deployment")
  return data as import("../types/grc").FrameworkDeploymentResponse
}

export async function deleteDeployment(deploymentId: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/fr/deployments/${deploymentId}`, { method: "DELETE" })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.error?.message || "Failed to remove deployment")
  }
}

export async function listDeploymentControls(deploymentId: string): Promise<{
  deployment_id: string; framework_name: string; deployed_version_code: string;
  controls: Array<{ id: string; control_code: string; name: string | null; control_category_code: string | null; category_name: string | null; criticality_code: string | null; criticality_name: string | null; control_type: string | null; sort_order: number | null }>;
  total: number;
}> {
  const res = await fetchWithAuth(`/api/v1/fr/deployments/${deploymentId}/controls`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list deployment controls")
  return data
}

export async function getUpgradeDiff(deploymentId: string, newVersionId: string): Promise<{
  deployment_id: string; from_version_code: string; to_version_id: string;
  to_version_code?: string | null;
  release_notes?: string | null;
  change_severity?: string | null;
  change_summary?: string | null;
  added: Array<{ id: string; control_code: string; name: string | null }>;
  removed: Array<{ id: string; control_code: string; name: string | null }>;
  added_count: number; removed_count: number;
}> {
  const res = await fetchWithAuth(`/api/v1/fr/deployments/${deploymentId}/upgrade-diff?new_version_id=${newVersionId}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to get upgrade diff")
  return data
}

export async function createAutoVersion(
  frameworkId: string,
  changeType: string,
  changeSummary?: string,
): Promise<VersionResponse> {
  const params = new URLSearchParams()
  params.set("change_type", changeType)
  if (changeSummary) params.set("change_summary", changeSummary)
  const res = await fetchWithAuth(`/api/v1/fr/frameworks/${frameworkId}/auto-version?${params}`, {
    method: "POST",
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to create auto version")
  return data as VersionResponse
}

// ── Global Risks ──────────────────────────────────────────────────────────────

export async function listGlobalRisks(params?: {
  category?: string; search?: string; limit?: number; offset?: number;
}): Promise<{
  items: Array<{
    id: string; risk_code: string; title: string | null; short_description: string | null;
    risk_category_code: string; risk_category_name: string | null;
    risk_level_code: string | null; risk_level_name: string | null; risk_level_color: string | null;
    inherent_likelihood: number | null; inherent_impact: number | null; inherent_risk_score: number | null;
    linked_control_count: number; is_active: boolean;
  }>;
  total: number;
}> {
  const qs = new URLSearchParams()
  if (params?.category) qs.set("category", params.category)
  if (params?.search) qs.set("search", params.search)
  if (params?.limit) qs.set("limit", String(params.limit))
  if (params?.offset) qs.set("offset", String(params.offset))
  const res = await fetchWithAuth(`/api/v1/fr/global-risks${qs.toString() ? "?" + qs.toString() : ""}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list global risks")
  return data
}

// ── Risk Library Deployments ──────────────────────────────────────────────────

export async function listRiskLibraryDeployments(orgId: string, workspaceId: string): Promise<{
  items: Array<{
    id: string; global_risk_id: string; workspace_risk_id: string | null;
    deployment_status: string; risk_code: string; title: string | null;
    short_description: string | null; risk_category_code: string; risk_category_name: string | null;
    risk_level_code: string | null; risk_level_name: string | null; risk_level_color: string | null;
    inherent_likelihood: number | null; inherent_impact: number | null; inherent_risk_score: number | null;
    linked_control_count: number;
  }>;
  total: number;
}> {
  const res = await fetchWithAuth(`/api/v1/fr/risk-library-deployments?org_id=${orgId}&workspace_id=${workspaceId}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list risk deployments")
  return data
}

export async function deployGlobalRisks(orgId: string, workspaceId: string, globalRiskIds: string[]): Promise<{
  deployed: number; inserted: number; skipped: number; org_id: string; workspace_id: string;
}> {
  const res = await fetchWithAuth(`/api/v1/fr/risk-library-deployments?org_id=${orgId}&workspace_id=${workspaceId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ global_risk_ids: globalRiskIds }),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to deploy risks")
  return data
}

export async function removeRiskDeployment(deploymentId: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/fr/risk-library-deployments/${deploymentId}`, { method: "DELETE" })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.error?.message || "Failed to remove risk deployment")
  }
}

// ── Export / Import ───────────────────────────────────────────────────────────

/** Download controls as file. Returns a Blob. */
export async function exportControls(
  frameworkId: string,
  format: "csv" | "json" | "xlsx" = "xlsx",
  simplified = false
): Promise<Blob> {
  const res = await fetchWithAuth(
    `/api/v1/fr/frameworks/${frameworkId}/controls/export?format=${format}&simplified=${simplified}`
  )
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.error?.message || "Export failed")
  }
  return res.blob()
}

/** Import controls from file. */
export async function importControls(
  frameworkId: string,
  file: File,
  dryRun = false
): Promise<import("../types/grc").ImportControlsResult> {
  const form = new FormData()
  form.append("file", file)
  const res = await fetchWithAuth(
    `/api/v1/fr/frameworks/${frameworkId}/controls/import?dry_run=${dryRun}`,
    { method: "POST", body: form }
  )
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Import failed")
  return data
}

/** Download controls import template. */
export async function getControlsImportTemplate(format: "csv" | "xlsx" = "xlsx"): Promise<Blob> {
  const res = await fetchWithAuth(`/api/v1/fr/frameworks/controls/import-template?format=${format}`)
  if (!res.ok) throw new Error("Failed to download template")
  return res.blob()
}

/** Export risks as file. */
export async function exportRisks(
  params: { orgId?: string; workspaceId?: string },
  format: "csv" | "json" | "xlsx" = "xlsx",
  simplified = false
): Promise<Blob> {
  const qs = new URLSearchParams({ format, simplified: String(simplified) })
  if (params.orgId) qs.set("org_id", params.orgId)
  if (params.workspaceId) qs.set("workspace_id", params.workspaceId)
  const res = await fetchWithAuth(`/api/v1/rr/risks/export?${qs}`)
  if (!res.ok) throw new Error("Export failed")
  return res.blob()
}

/** Import risks from file. */
export async function importRisks(
  file: File,
  params: { orgId?: string; workspaceId?: string; tenantKey?: string },
  dryRun = false
): Promise<import("../types/grc").ImportRisksResult> {
  const qs = new URLSearchParams({ dry_run: String(dryRun) })
  if (params.orgId) qs.set("org_id", params.orgId)
  if (params.workspaceId) qs.set("workspace_id", params.workspaceId)
  if (params.tenantKey) qs.set("tenant_key", params.tenantKey)
  const form = new FormData()
  form.append("file", file)
  const res = await fetchWithAuth(`/api/v1/rr/risks/import?${qs}`, { method: "POST", body: form })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Import failed")
  return data
}

/** Export tasks as file. */
export async function exportTasks(
  params: { orgId?: string; workspaceId?: string },
  format: "csv" | "json" | "xlsx" = "xlsx",
  simplified = false
): Promise<Blob> {
  const qs = new URLSearchParams({ format, simplified: String(simplified) })
  if (params.orgId) qs.set("org_id", params.orgId)
  if (params.workspaceId) qs.set("workspace_id", params.workspaceId)
  const res = await fetchWithAuth(`/api/v1/tk/tasks/export?${qs}`)
  if (!res.ok) throw new Error("Export failed")
  return res.blob()
}

/** Import tasks from file. */
export async function importTasks(
  file: File,
  params: { orgId?: string; workspaceId?: string },
  dryRun = false
): Promise<import("../types/grc").ImportTasksResult> {
  const qs = new URLSearchParams({ dry_run: String(dryRun) })
  if (params.orgId) qs.set("org_id", params.orgId)
  if (params.workspaceId) qs.set("workspace_id", params.workspaceId)
  const form = new FormData()
  form.append("file", file)
  const res = await fetchWithAuth(`/api/v1/tk/tasks/import?${qs}`, { method: "POST", body: form })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Import failed")
  return data
}

/** Download a blank import template for risks. */
export async function getRisksImportTemplate(format: "csv" | "xlsx" = "xlsx"): Promise<Blob> {
  const res = await fetchWithAuth(`/api/v1/rr/risks/import-template?format=${format}`)
  if (!res.ok) throw new Error("Failed to download template")
  return res.blob()
}

/** Download a blank import template for tasks. */
export async function getTasksImportTemplate(format: "csv" | "xlsx" = "xlsx"): Promise<Blob> {
  const res = await fetchWithAuth(`/api/v1/tk/tasks/import-template?format=${format}`)
  if (!res.ok) throw new Error("Failed to download template")
  return res.blob()
}

/** Export a framework as a portable bundle JSON. */
export async function exportFrameworkBundle(frameworkId: string): Promise<Blob> {
  const res = await fetchWithAuth(`/api/v1/fr/frameworks/bundle/export/${frameworkId}`)
  if (!res.ok) throw new Error("Bundle export failed")
  return res.blob()
}

/** Import a framework bundle JSON. */
export async function importFrameworkBundle(
  bundle: import("../types/grc").FrameworkBundle,
  params: {
    scopeOrgId?: string
    scopeWorkspaceId?: string
    dryRun?: boolean
  } = {}
): Promise<import("../types/grc").BundleImportResult> {
  const qs = new URLSearchParams({ dry_run: String(params.dryRun ?? false) })
  if (params.scopeOrgId) qs.set("scope_org_id", params.scopeOrgId)
  if (params.scopeWorkspaceId) qs.set("scope_workspace_id", params.scopeWorkspaceId)
  const res = await fetchWithAuth(`/api/v1/fr/frameworks/bundle/import?${qs}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(bundle),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Bundle import failed")
  return data
}

/** Get live vs published diff for a framework. */
export async function getFrameworkDiff(frameworkId: string): Promise<import("../types/grc").FrameworkDiff> {
  const res = await fetchWithAuth(`/api/v1/fr/frameworks/${frameworkId}/diff`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to get diff")
  return data
}

// ── Promoted Tests ────────────────────────────────────────────────────────────

/** List active promoted control tests for an org. */
export async function listPromotedTests(params: {
  orgId: string
  workspaceId?: string
  isActive?: boolean
  linkedAssetId?: string
  search?: string
  limit?: number
  offset?: number
}): Promise<import("../types/grc").PromotedTestListResponse> {
  const qs = new URLSearchParams({ org_id: params.orgId })
  if (params.workspaceId) qs.set("workspace_id", params.workspaceId)
  if (params.isActive !== undefined) qs.set("is_active", String(params.isActive))
  if (params.linkedAssetId) qs.set("linked_asset_id", params.linkedAssetId)
  if (params.search) qs.set("search", params.search)
  if (params.limit !== undefined) qs.set("limit", String(params.limit))
  if (params.offset !== undefined) qs.set("offset", String(params.offset))
  const res = await fetchWithAuth(`/api/v1/sb/promoted-tests?${qs}`)
  const data = await res.json()
  if (!res.ok) throw new Error(parseApiError(data, "Failed to list promoted tests"))
  return data
}

/** Get a single promoted test by ID. */
export async function getPromotedTest(id: string): Promise<import("../types/grc").PromotedTestResponse> {
  const res = await fetchWithAuth(`/api/v1/sb/promoted-tests/${id}`)
  const data = await res.json()
  if (!res.ok) throw new Error(parseApiError(data, "Failed to get promoted test"))
  return data
}

/** Get version history for a promoted test by ID. */
export async function getPromotedTestHistory(
  id: string
): Promise<import("../types/grc").PromotedTestResponse[]> {
  const res = await fetchWithAuth(`/api/v1/sb/promoted-tests/${id}/history`)
  const data = await res.json()
  if (!res.ok) throw new Error(parseApiError(data, "Failed to get test history"))
  return data.items ?? []
}

/** Update a promoted test (name, description, or linked_asset_id). */
export async function updatePromotedTest(
  id: string,
  req: import("../types/grc").UpdatePromotedTestRequest
): Promise<import("../types/grc").PromotedTestResponse> {
  const res = await fetchWithAuth(`/api/v1/sb/promoted-tests/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(parseApiError(data, "Failed to update promoted test"))
  return data
}

/** Delete (soft-delete) a promoted test. */
export async function deletePromotedTest(id: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/sb/promoted-tests/${id}`, { method: "DELETE" })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(parseApiError(data as Record<string, unknown>, "Failed to delete promoted test"))
  }
}

/** Execute a promoted test against its linked dataset. */
export interface ExecutePromotedTestResponse {
  test_id: string
  test_code: string
  result_status: string
  summary: string
  details: Array<Record<string, unknown>>
  metadata: Record<string, unknown>
  execution_id: string | null
  executed_at: string
  task_created: boolean
  task_id: string | null
}

export async function executePromotedTest(
  id: string,
  datasetId?: string
): Promise<ExecutePromotedTestResponse> {
  const res = await fetchWithAuth(`/api/v1/sb/promoted-tests/${id}/execute`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ dataset_id: datasetId || null }),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(parseApiError(data, "Failed to execute test"))
  return data as ExecutePromotedTestResponse
}

/** Monitoring dashboard data */
export interface MonitoringDashboardData {
  execution_summary: {
    total_executions: number
    pass_count: number
    fail_count: number
    error_count: number
    pass_rate: number
    last_execution_at: string | null
  }
  connector_health: Array<{
    connector_id: string
    connector_name: string | null
    connector_type_code: string
    health_status: string
    test_count: number
    last_pass_count: number
    last_fail_count: number
    last_execution_at: string | null
    collection_schedule: string
    last_collected_at: string | null
  }>
  recent_executions: Array<{
    execution_id: string
    test_code: string | null
    test_name: string | null
    result_status: string
    result_summary: string | null
    executed_at: string
    connector_type: string | null
    connector_id: string | null
    connector_name: string | null
  }>
  open_issues: Array<{
    task_id: string
    title: string | null
    priority_code: string
    entity_id: string | null
    created_at: string
  }>
  total_promoted_tests: number
  total_connectors: number
}

export async function getMonitoringDashboard(orgId: string, workspaceId?: string): Promise<MonitoringDashboardData> {
  const params = new URLSearchParams({ org_id: orgId })
  if (workspaceId) params.set("workspace_id", workspaceId)
  const res = await fetchWithAuth(`/api/v1/sb/promoted-tests/dashboard?${params}`)
  const data = await res.json()
  if (!res.ok) throw new Error(parseApiError(data, "Failed to load monitoring dashboard"))
  return data as MonitoringDashboardData
}


// ═══════════════════════════════════════════════════════════════════════════════
// Issues (from failed control tests)
// ═══════════════════════════════════════════════════════════════════════════════

export interface IssueResponse {
  id: string
  tenant_key: string
  org_id: string
  workspace_id: string | null
  promoted_test_id: string | null
  control_test_id: string | null
  execution_id: string | null
  connector_id: string | null
  status_code: string
  severity_code: string
  issue_code: string
  test_code: string | null
  test_name: string | null
  result_summary: string | null
  result_details: Array<Record<string, unknown>> | null
  connector_type_code: string | null
  assigned_to: string | null
  remediated_at: string | null
  remediation_notes: string | null
  verified_at: string | null
  is_active: boolean
  created_at: string
  updated_at: string
  closed_at: string | null
}

export interface IssueListResponse {
  items: IssueResponse[]
  total: number
}

export interface IssueStatsResponse {
  total: number
  open: number
  investigating: number
  remediated: number
  closed: number
  by_severity: Record<string, number>
  by_connector_type: Record<string, number>
}

export async function listIssues(params: {
  orgId: string
  status_code?: string
  severity_code?: string
  connector_id?: string
  search?: string
  limit?: number
  offset?: number
}): Promise<IssueListResponse> {
  const qs = new URLSearchParams({ org_id: params.orgId })
  if (params.status_code) qs.set("status_code", params.status_code)
  if (params.severity_code) qs.set("severity_code", params.severity_code)
  if (params.connector_id) qs.set("connector_id", params.connector_id)
  if (params.search) qs.set("search", params.search)
  if (params.limit !== undefined) qs.set("limit", String(params.limit))
  if (params.offset !== undefined) qs.set("offset", String(params.offset))
  const res = await fetchWithAuth(`/api/v1/issues?${qs}`)
  const data = await res.json()
  if (!res.ok) throw new Error(parseApiError(data, "Failed to list issues"))
  return data as IssueListResponse
}

export async function getIssueStats(orgId: string): Promise<IssueStatsResponse> {
  const res = await fetchWithAuth(`/api/v1/issues/stats?org_id=${orgId}`)
  const data = await res.json()
  if (!res.ok) throw new Error(parseApiError(data, "Failed to get issue stats"))
  return data as IssueStatsResponse
}

export async function updateIssue(issueId: string, payload: {
  status_code?: string
  severity_code?: string
  assigned_to?: string
  remediation_notes?: string
}): Promise<IssueResponse> {
  const res = await fetchWithAuth(`/api/v1/issues/${issueId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(parseApiError(data, "Failed to update issue"))
  return data as IssueResponse
}
