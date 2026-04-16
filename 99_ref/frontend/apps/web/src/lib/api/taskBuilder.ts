import { fetchWithAuth } from "./apiClient"

// ── Types ─────────────────────────────────────────────────────────────────────

export type TaskType = "evidence_collection" | "control_remediation" | "risk_mitigation"

export interface GeneratedTask {
  title: string
  description: string
  priority_code: "critical" | "high" | "medium" | "low"
  due_days_from_now: number
  acceptance_criteria: string
  remediation_plan?: string
  task_type_code: TaskType
  _selected?: boolean
}

export interface TaskGroup {
  control_id: string
  control_code: string
  tasks: GeneratedTask[]
}

export interface ApplyResult {
  created: number
  skipped: number
}

export interface TaskBuilderAttachment {
  id: string
  filename: string
  content_type: string
  file_size_bytes: number
  ingest_status: string
  pageindex_status: string
}

// ── Session types ─────────────────────────────────────────────────────────────

export interface TaskBuilderSession {
  id: string
  tenant_key: string
  user_id: string
  status: string     // idle | generating | reviewing | applying | complete | failed
  framework_id: string
  scope_org_id: string | null
  scope_workspace_id: string | null
  user_context: string
  attachment_ids: string[]
  control_ids: string[] | null
  proposed_tasks: TaskGroup[] | null
  apply_result: ApplyResult | null
  job_id: string | null
  error_message: string | null
  activity_log: Record<string, unknown>[]
  created_at: string
  updated_at: string
}

export interface TaskBuilderSessionList {
  items: TaskBuilderSession[]
  total: number
}

export interface TaskBuilderJobStatus {
  job_id: string
  status: string         // queued | running | completed | failed
  job_type: string
  creation_log: Record<string, unknown>[]
  stats: Record<string, unknown> | null
  error_message: string | null
  started_at: string | null
  completed_at: string | null
}

// ── Session API ───────────────────────────────────────────────────────────────

export async function createTaskBuilderSession(params: {
  framework_id: string
  scope_org_id: string
  scope_workspace_id: string
  user_context?: string
  attachment_ids?: string[]
  control_ids?: string[]
}): Promise<TaskBuilderSession> {
  const res = await fetchWithAuth("/api/v1/ai/task-builder/sessions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || "Failed to create session")
  return data
}

export async function listTaskBuilderSessions(params: {
  framework_id?: string
  scope_org_id: string
  scope_workspace_id: string
  limit?: number
  offset?: number
}): Promise<TaskBuilderSessionList> {
  const qs = new URLSearchParams()
  if (params.framework_id) qs.set("framework_id", params.framework_id)
  qs.set("scope_org_id", params.scope_org_id)
  qs.set("scope_workspace_id", params.scope_workspace_id)
  if (params.limit) qs.set("limit", String(params.limit))
  if (params.offset) qs.set("offset", String(params.offset))
  const res = await fetchWithAuth(`/api/v1/ai/task-builder/sessions?${qs}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || "Failed to list sessions")
  return data
}

export async function getTaskBuilderSession(sessionId: string): Promise<TaskBuilderSession> {
  const res = await fetchWithAuth(`/api/v1/ai/task-builder/sessions/${sessionId}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || "Failed to get session")
  return data
}

export async function patchTaskBuilderSession(sessionId: string, patch: {
  user_context?: string
  attachment_ids?: string[]
  control_ids?: string[]
  proposed_tasks?: TaskGroup[]
}): Promise<TaskBuilderSession> {
  const res = await fetchWithAuth(`/api/v1/ai/task-builder/sessions/${sessionId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(patch),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || "Failed to patch session")
  return data
}

// ── Job API ───────────────────────────────────────────────────────────────────

export async function enqueueTaskBuilderPreview(sessionId: string): Promise<TaskBuilderJobStatus> {
  const res = await fetchWithAuth(`/api/v1/ai/task-builder/sessions/${sessionId}/enqueue-preview`, {
    method: "POST",
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || "Failed to enqueue preview")
  return data
}

export async function enqueueTaskBuilderApply(
  sessionId: string,
  taskGroups?: TaskGroup[],
): Promise<TaskBuilderJobStatus> {
  const res = await fetchWithAuth(`/api/v1/ai/task-builder/sessions/${sessionId}/enqueue-apply`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(taskGroups ? { task_groups: taskGroups } : {}),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || "Failed to enqueue apply")
  return data
}

export async function getTaskBuilderSessionJob(sessionId: string): Promise<TaskBuilderJobStatus> {
  const res = await fetchWithAuth(`/api/v1/ai/task-builder/sessions/${sessionId}/job`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || "Failed to get session job")
  return data
}

export async function getTaskBuilderJob(jobId: string): Promise<TaskBuilderJobStatus> {
  const res = await fetchWithAuth(`/api/v1/ai/task-builder/jobs/${jobId}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || "Failed to get job")
  return data
}

// ── Legacy direct endpoints ───────────────────────────────────────────────────

export async function uploadTaskBuilderFile(
  file: File,
  orgId: string,
  workspaceId: string,
): Promise<TaskBuilderAttachment> {
  const form = new FormData()
  form.append("file", file)
  const res = await fetchWithAuth(
    `/api/v1/ai/task-builder/upload?org_id=${encodeURIComponent(orgId)}&workspace_id=${encodeURIComponent(workspaceId)}`,
    { method: "POST", body: form },
  )
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || data.error?.message || "Failed to upload file")
  return data as TaskBuilderAttachment
}

export async function previewTasks(params: {
  framework_id: string
  org_id: string
  workspace_id: string
  user_context?: string
  control_ids?: string[]
  attachment_ids?: string[]
}): Promise<TaskGroup[]> {
  const res = await fetchWithAuth("/api/v1/ai/task-builder/preview", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || data.error?.message || "Failed to generate tasks")
  return data as TaskGroup[]
}

export async function applyTasks(params: {
  framework_id: string
  org_id: string
  workspace_id: string
  task_groups: TaskGroup[]
}): Promise<ApplyResult> {
  const res = await fetchWithAuth("/api/v1/ai/task-builder/apply", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || data.error?.message || "Failed to create tasks")
  return data as ApplyResult
}
