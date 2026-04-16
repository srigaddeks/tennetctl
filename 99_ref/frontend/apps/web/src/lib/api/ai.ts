import { fetchWithAuth, getSessionOrg, getSessionWorkspace } from "./apiClient"

function withCurrentScope(params?: URLSearchParams): URLSearchParams {
  const scoped = params ? new URLSearchParams(params) : new URLSearchParams()
  const orgId = getSessionOrg()
  const workspaceId = getSessionWorkspace()

  if (orgId && !scoped.has("org_id")) scoped.set("org_id", orgId)
  if (workspaceId && !scoped.has("workspace_id")) scoped.set("workspace_id", workspaceId)

  return scoped
}

function withCurrentScopeUrl(path: string, params?: URLSearchParams): string {
  const scoped = withCurrentScope(params)
  const query = scoped.toString()
  return query ? `${path}?${query}` : path
}

// ── Types ─────────────────────────────────────────────────────────────────────

export interface ConversationResponse {
  id: string
  tenant_key: string
  user_id: string
  org_id: string | null
  workspace_id: string | null
  agent_type_code: string
  title: string | null
  page_context: Record<string, unknown> | null
  is_archived: boolean
  created_at: string
  updated_at: string
}

export interface ConversationListResponse {
  items: ConversationResponse[]
  total: number
}

export interface MessageResponse {
  id: string
  conversation_id: string
  role_code: string
  content: string
  token_count: number | null
  model_id: string | null
  created_at: string
}

export interface CreateConversationRequest {
  agent_type_code?: string
  title?: string
  page_context?: Record<string, unknown>
  org_id?: string
  workspace_id?: string
}

export interface SendMessageRequest {
  content: string
  page_context?: Record<string, unknown>
}

export interface ApprovalResponse {
  id: string
  tenant_key: string
  requester_id: string
  org_id: string | null
  approver_id: string | null
  status_code: string
  tool_name: string
  tool_category: string
  entity_type: string | null
  operation: string | null
  payload_json: Record<string, unknown>
  diff_json: Record<string, unknown> | null
  rejection_reason: string | null
  expires_at: string
  approved_at: string | null
  executed_at: string | null
  execution_result: Record<string, unknown> | null
  created_at: string
  updated_at: string
  is_overdue: boolean
}

export interface ApprovalListResponse {
  items: ApprovalResponse[]
  total: number
}

// ── Conversations ──────────────────────────────────────────────────────────────

export async function listConversations(
  isArchived = false,
  limit = 50,
  offset = 0,
): Promise<ConversationListResponse> {
  const params = withCurrentScope(new URLSearchParams({
    is_archived: String(isArchived),
    limit: String(limit),
    offset: String(offset),
  }))
  const res = await fetchWithAuth(`/api/v1/ai/conversations?${params}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list conversations")
  return data as ConversationListResponse
}

export async function createConversation(
  payload: CreateConversationRequest,
): Promise<ConversationResponse> {
  const requestPayload: CreateConversationRequest = {
    ...payload,
    org_id: payload.org_id ?? (getSessionOrg() || undefined),
    workspace_id: payload.workspace_id ?? (getSessionWorkspace() || undefined),
  }
  const res = await fetchWithAuth("/api/v1/ai/conversations", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(requestPayload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to create conversation")
  return data as ConversationResponse
}

export async function getConversation(conversationId: string): Promise<ConversationResponse> {
  const res = await fetchWithAuth(withCurrentScopeUrl(`/api/v1/ai/conversations/${conversationId}`))
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to get conversation")
  return data as ConversationResponse
}

export async function archiveConversation(conversationId: string): Promise<void> {
  const res = await fetchWithAuth(withCurrentScopeUrl(`/api/v1/ai/conversations/${conversationId}/archive`), {
    method: "POST",
  })
  if (!res.ok) {
    const data = await res.json()
    throw new Error(data.error?.message || "Failed to archive conversation")
  }
}

export async function listMessages(
  conversationId: string,
  limit = 100,
): Promise<MessageResponse[]> {
  const params = withCurrentScope(new URLSearchParams({ limit: String(limit) }))
  const res = await fetchWithAuth(
    `/api/v1/ai/conversations/${conversationId}/messages?${params}`,
  )
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list messages")
  return data as MessageResponse[]
}

// Returns the raw Response so the caller can read the SSE stream
export async function streamMessage(
  conversationId: string,
  payload: SendMessageRequest,
): Promise<Response> {
  return fetchWithAuth(withCurrentScopeUrl(`/api/v1/ai/conversations/${conversationId}/stream`), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
}

// ── Admin: Agent Configs ───────────────────────────────────────────────────────

export type AgentProviderType = "openai" | "anthropic" | "azure_openai" | "openai_compatible"

export interface AgentConfigResponse {
  id: string
  tenant_key: string
  agent_type_code: string
  org_id: string | null
  provider_base_url: string
  provider_type: AgentProviderType
  has_api_key: boolean
  model_id: string
  temperature: number | null
  max_tokens: number | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface AgentConfigListResponse {
  items: AgentConfigResponse[]
  total: number
}

export interface AgentConfigCreateRequest {
  agent_type_code: string
  org_id?: string
  provider_base_url: string
  provider_type?: AgentProviderType
  api_key: string
  model_id: string
  temperature?: number
  max_tokens?: number
  is_active?: boolean
}

export async function listAgentConfigs(): Promise<AgentConfigListResponse> {
  const res = await fetchWithAuth("/api/v1/ai/admin/agent-configs")
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list agent configs")
  return data as AgentConfigListResponse
}

export async function createAgentConfig(payload: AgentConfigCreateRequest): Promise<AgentConfigResponse> {
  const res = await fetchWithAuth("/api/v1/ai/admin/agent-configs", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to create agent config")
  return data as AgentConfigResponse
}

export async function updateAgentConfig(
  id: string,
  payload: Partial<AgentConfigCreateRequest>,
): Promise<AgentConfigResponse> {
  const res = await fetchWithAuth(`/api/v1/ai/admin/agent-configs/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to update agent config")
  return data as AgentConfigResponse
}

export async function deleteAgentConfig(id: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/ai/admin/agent-configs/${id}`, { method: "DELETE" })
  if (!res.ok) {
    const data = await res.json()
    throw new Error(data.error?.message || "Failed to delete agent config")
  }
}

// ── Admin: Prompt Templates ────────────────────────────────────────────────────

export interface PromptTemplateResponse {
  id: string
  name: string | null
  description: string | null
  agent_type_code: string
  prompt_type: string
  template_content: string
  version: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface PromptTemplateListResponse {
  items: PromptTemplateResponse[]
  total: number
}

export interface PromptTemplateCreateRequest {
  name: string
  description?: string
  agent_type_code: string
  prompt_type: string
  template_content: string
  version?: number
  is_active?: boolean
}

export async function listPromptTemplates(): Promise<PromptTemplateListResponse> {
  const res = await fetchWithAuth("/api/v1/ai/admin/prompts")
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list prompt templates")
  return data as PromptTemplateListResponse
}

export async function createPromptTemplate(
  payload: PromptTemplateCreateRequest,
): Promise<PromptTemplateResponse> {
  const res = await fetchWithAuth("/api/v1/ai/admin/prompts", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to create prompt template")
  return data as PromptTemplateResponse
}

export async function updatePromptTemplate(
  id: string,
  payload: Partial<PromptTemplateCreateRequest>,
): Promise<PromptTemplateResponse> {
  const res = await fetchWithAuth(`/api/v1/ai/admin/prompts/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to update prompt template")
  return data as PromptTemplateResponse
}

export async function deletePromptTemplate(id: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/ai/admin/prompts/${id}`, { method: "DELETE" })
  if (!res.ok) {
    const data = await res.json()
    throw new Error(data.error?.message || "Failed to delete prompt template")
  }
}

export async function previewPromptTemplate(
  id: string,
  variables: Record<string, string>,
): Promise<{ rendered?: string; preview?: string }> {
  const res = await fetchWithAuth(`/api/v1/ai/admin/prompts/${id}/preview`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(variables),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to preview prompt template")
  return data as { rendered?: string; preview?: string }
}

// ── Admin: Approvals (all users) ───────────────────────────────────────────────

export async function listAllApprovals(
  params: { status_code?: string; limit?: number; offset?: number } = {},
): Promise<ApprovalListResponse> {
  const { status_code, limit = 50, offset = 0 } = params
  const qs = new URLSearchParams({ limit: String(limit), offset: String(offset) })
  if (status_code) qs.set("status_code", status_code)
  const res = await fetchWithAuth(`/api/v1/ai/approvals?${qs}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list approvals")
  return data as ApprovalListResponse
}

// ── Admin: Reporting ───────────────────────────────────────────────────────────

export interface AIReportingSummary {
  total_conversations: number
  total_messages: number
  total_tokens: number
  total_requests: number
  avg_tokens_per_conversation: number
  by_agent_type: Record<string, { conversations: number; tokens: number; requests: number }>
}

export async function getAIReportingSummary(): Promise<AIReportingSummary> {
  const res = await fetchWithAuth("/api/v1/ai/reporting/summary")
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to get AI reporting summary")
  return data as AIReportingSummary
}

// ── Admin: Agent Runs ──────────────────────────────────────────────────────────

export interface AgentRunResponse {
  id: string
  agent_type_code: string
  status_code: string
  token_count: number | null
  created_at: string
  completed_at: string | null
}

export interface AgentRunListResponse {
  items: AgentRunResponse[]
  total: number
}

export async function listAgentRuns(
  params: { limit?: number; offset?: number; status_code?: string } = {},
): Promise<AgentRunListResponse> {
  const { limit = 50, offset = 0, status_code } = params
  const qs = new URLSearchParams({ limit: String(limit), offset: String(offset) })
  if (status_code) qs.set("status_code", status_code)
  const res = await fetchWithAuth(`/api/v1/ai/agents/runs?${qs}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list agent runs")
  return data as AgentRunListResponse
}

// ── Approvals ──────────────────────────────────────────────────────────────────

export async function listApprovals(
  statusCode?: string,
  limit = 50,
  offset = 0,
): Promise<ApprovalListResponse> {
  const params = new URLSearchParams({ limit: String(limit), offset: String(offset) })
  if (statusCode) params.set("status_code", statusCode)
  const res = await fetchWithAuth(`/api/v1/ai/approvals?${params}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list approvals")
  return data as ApprovalListResponse
}

export async function getApproval(approvalId: string): Promise<ApprovalResponse> {
  const res = await fetchWithAuth(`/api/v1/ai/approvals/${approvalId}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to get approval")
  return data as ApprovalResponse
}

export async function approveAction(approvalId: string): Promise<ApprovalResponse> {
  const res = await fetchWithAuth(`/api/v1/ai/approvals/${approvalId}/approve`, {
    method: "POST",
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to approve")
  return data as ApprovalResponse
}

export async function rejectApproval(approvalId: string, reason: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/ai/approvals/${approvalId}/reject`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ reason }),
  })
  if (!res.ok) {
    const data = await res.json()
    throw new Error(data.error?.message || "Failed to reject")
  }
}

// ── Evidence Checker ───────────────────────────────────────────────────────────

export interface EvidenceJobStatus {
  id: string
  status_code: "queued" | "ingesting" | "evaluating" | "completed" | "failed" | "superseded" | "cancelled"
  queue_position: number | null
  estimated_wait_seconds: number | null
  progress_criteria_done: number
  progress_criteria_total: number
  pages_analyzed: number
  error_message: string | null
  started_at: string | null
  completed_at: string | null
  created_at: string
}

export interface EvidenceReference {
  document_filename: string
  page_number: number | null
  section_or_sheet: string | null
  excerpt: string
  confidence: number
}

export interface EvidenceCriterionResult {
  id: string
  criterion_id: string | null
  criterion_text: string
  verdict: "MET" | "PARTIALLY_MET" | "NOT_MET" | "INSUFFICIENT_EVIDENCE"
  threshold_met: boolean | null
  justification: string
  gap_analysis: string | null
  evidence_references: EvidenceReference[]
  conflicting_references: EvidenceReference[]
  agent_run_id: string | null
  langfuse_trace_id: string | null
}

export interface EvidenceReport {
  id: string
  tenant_key: string
  org_id: string
  task_id: string
  job_id: string
  version: number
  is_active: boolean
  overall_verdict: "ALL_MET" | "PARTIALLY_MET" | "NOT_MET" | "INCONCLUSIVE"
  attachment_count: number
  total_pages_analyzed: number
  langfuse_trace_id: string | null
  tokens_consumed: number
  duration_seconds: number
  criteria_results: EvidenceCriterionResult[]
  created_at: string
  markdown_report_available: boolean
}

export interface EvidenceReportSummary {
  id: string
  version: number
  overall_verdict: string
  attachment_count: number
  total_pages_analyzed: number
  created_at: string
}

export async function getEvidenceJob(taskId: string): Promise<{ job: EvidenceJobStatus | null }> {
  const res = await fetchWithAuth(`/api/v1/ai/evidence-check/tasks/${taskId}/jobs/current`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || data.error?.message || "Failed to get evidence job")
  return data as { job: EvidenceJobStatus | null }
}

export async function listEvidenceReports(
  taskId: string,
  limit = 20,
  offset = 0,
): Promise<{ reports: EvidenceReportSummary[]; total: number }> {
  const qs = new URLSearchParams({ limit: String(limit), offset: String(offset) })
  const res = await fetchWithAuth(`/api/v1/ai/evidence-check/tasks/${taskId}/reports?${qs}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || data.error?.message || "Failed to list evidence reports")
  return data as { reports: EvidenceReportSummary[]; total: number }
}

export async function getActiveEvidenceReport(taskId: string): Promise<{ report: EvidenceReport }> {
  const res = await fetchWithAuth(`/api/v1/ai/evidence-check/tasks/${taskId}/reports/active`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || data.error?.message || "Failed to get active evidence report")
  return data as { report: EvidenceReport }
}

export async function getEvidenceReport(reportId: string): Promise<{ report: EvidenceReport }> {
  const res = await fetchWithAuth(`/api/v1/ai/evidence-check/reports/${reportId}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || data.error?.message || "Failed to get evidence report")
  return data as { report: EvidenceReport }
}

export async function triggerEvidenceCheck(taskId: string): Promise<{ message: string; queued: boolean; job_id?: string }> {
  const res = await fetchWithAuth(`/api/v1/ai/evidence-check/tasks/${taskId}/trigger`, { method: "POST" })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || data.error?.message || "Failed to trigger evidence check")
  return data as { message: string; queued: boolean; job_id?: string }
}

export async function downloadEvidenceReportMarkdown(reportId: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/ai/evidence-check/reports/${reportId}/download`)
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error((data as any).detail || "Failed to download report")
  }
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement("a")
  a.href = url
  a.download = `evidence_report_${reportId.slice(0, 8)}.md`
  a.click()
  URL.revokeObjectURL(url)
}

export async function getEvidenceBatchVerdicts(
  taskIds: string[],
): Promise<{ verdicts: Record<string, string> }> {
  if (taskIds.length === 0) return { verdicts: {} }
  const qs = taskIds.map(id => `task_ids=${encodeURIComponent(id)}`).join("&")
  const res = await fetchWithAuth(`/api/v1/ai/evidence-check/tasks/verdicts?${qs}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || "Failed to get evidence verdicts")
  return data as { verdicts: Record<string, string> }
}

// ── Inline Text Enhancer ───────────────────────────────────────────────────────

export interface EnhanceTextRequest {
  entity_type: string
  entity_id: string | null
  field_name: string
  current_value: string | string[]
  instruction: string
  org_id: string | null
  workspace_id: string | null
  entity_context?: Record<string, unknown>
  model_id?: string
}

export interface EnhanceCompleteEvent {
  enhanced_value: string
  usage: {
    input_tokens: number
    output_tokens: number
  }
}

// Returns the raw Response so the caller can read the SSE stream
export async function streamEnhanceText(payload: EnhanceTextRequest): Promise<Response> {
  return fetchWithAuth("/api/v1/ai/enhance-text/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
}

// ── AI Form Fill ───────────────────────────────────────────────────────────────

export interface FormFillOption {
  code: string
  name: string
}

export interface FormFillRequest {
  entity_type: string
  intent: string
  org_id?: string | null
  workspace_id?: string | null
  available_types?: FormFillOption[]
  available_categories?: FormFillOption[]
  available_criticalities?: FormFillOption[]
  available_treatment_types?: FormFillOption[]
  available_task_types?: FormFillOption[]
  entity_context?: Record<string, unknown>
  model_id?: string
}

export interface FormFillCompleteEvent {
  fill_id: string
  entity_type: string
  fields: Record<string, string>
  usage: { input_tokens: number; output_tokens: number }
}

// Returns the raw Response so the caller can read the SSE stream
export async function streamFormFill(payload: FormFillRequest): Promise<Response> {
  return fetchWithAuth("/api/v1/ai/form-fill/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
}

// ── AI Agent Form Fill (v2 — conversational, context-aware) ───────────────────

export interface AgentFillRequest {
  entity_type: string
  message: string
  session_id: string
  history: Array<{ role: "user" | "assistant"; content: string }>
  org_id?: string | null
  workspace_id?: string | null
  page_context?: Record<string, unknown>
}

export async function streamAgentFormFill(payload: AgentFillRequest): Promise<Response> {
  return fetchWithAuth("/api/v1/ai/form-fill/agent/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
}

// ── Conversation Attachments ───────────────────────────────────────────────────

export interface AttachmentResponse {
  id: string
  conversation_id: string
  filename: string
  content_type: string
  file_size_bytes: number
  chunk_count: number
  ingest_status: "pending" | "ingesting" | "ready" | "failed"
  error_message: string | null
  created_at: string
  // PageIndex hierarchical RAG status
  pageindex_status: "none" | "indexing" | "ready" | "failed"
  pageindex_error: string | null
  // CDN or signed URL for preview
  file_url?: string
}

export interface AttachmentListResponse {
  items: AttachmentResponse[]
  total: number
}

/**
 * Upload a file attachment to a conversation.
 * The backend extracts text, chunks it, embeds it, and stores in Qdrant
 * so the AI can answer questions about the document in-conversation.
 */
export async function uploadAttachment(
  conversationId: string,
  file: File,
): Promise<AttachmentResponse> {
  const form = new FormData()
  form.append("file", file)
  const res = await fetchWithAuth(withCurrentScopeUrl(`/api/v1/ai/conversations/${conversationId}/attachments`), {
    method: "POST",
    body: form,
    // No Content-Type header — browser sets multipart boundary automatically
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || data.detail || "Failed to upload attachment")
  return data as AttachmentResponse
}

export async function listAttachments(conversationId: string): Promise<AttachmentListResponse> {
  const res = await fetchWithAuth(withCurrentScopeUrl(`/api/v1/ai/conversations/${conversationId}/attachments`))
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list attachments")
  return data as AttachmentListResponse
}

export async function deleteAttachment(
  conversationId: string,
  attachmentId: string,
): Promise<void> {
  const res = await fetchWithAuth(
    withCurrentScopeUrl(`/api/v1/ai/conversations/${conversationId}/attachments/${attachmentId}`),
    { method: "DELETE" },
  )
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error((data as any).error?.message || "Failed to delete attachment")
  }
}

// ── GRC Report Generation ────────────────────────────────────────────────────

export interface ReportSummaryResponse {
  id: string
  report_type: string
  title: string | null
  status_code: "queued" | "planning" | "collecting" | "analyzing" | "writing" | "formatting" | "completed" | "failed"
  word_count: number | null
  is_auto_generated: boolean
  workspace_id: string | null
  parameters_json: Record<string, unknown>
  trigger_entity_type: string | null
  trigger_entity_id: string | null
  created_at: string
  completed_at: string | null
}

export interface ReportResponse extends ReportSummaryResponse {
  tenant_key: string
  org_id: string | null
  workspace_id: string | null
  parameters_json: Record<string, unknown>
  content_markdown: string | null
  token_count: number | null
  generated_by_user_id: string | null
  job_id: string | null
  error_message: string | null
  trigger_entity_type: string | null
  trigger_entity_id: string | null
  updated_at: string
}

export interface ReportListResponse {
  items: ReportSummaryResponse[]
  total: number
}

export interface GenerateReportRequest {
  report_type: string
  title?: string
  org_id: string
  workspace_id?: string
  engagement_id?: string
  parameters?: Record<string, unknown>
}

export interface ReportJobStatusResponse {
  job_id: string
  report_id: string | null
  status_code: string
  error_message: string | null
  started_at: string | null
  completed_at: string | null
  created_at: string
}

export const REPORT_TYPE_LABELS: Record<string, string> = {
  executive_summary: "Executive Summary",
  compliance_posture: "Compliance Posture",
  framework_compliance: "Framework Compliance",
  framework_readiness: "Framework Readiness",
  framework_gap_analysis: "Framework Gap Analysis",
  control_status: "Control Status",
  risk_summary: "Risk Summary",
  board_risk_report: "Board Risk Report",
  vendor_risk: "Vendor Risk Assessment",
  remediation_plan: "Remediation Plan",
  task_health: "Task Health",
  audit_trail: "Audit Trail",
  evidence_report: "Evidence Check",
}

export async function generateReport(payload: GenerateReportRequest): Promise<ReportResponse> {
  const params = new URLSearchParams()
  if (payload.engagement_id) params.set("engagement_id", payload.engagement_id)
  const qs = params.toString()
  const res = await fetchWithAuth(`/api/v1/ai/reports${qs ? `?${qs}` : ""}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || "Failed to generate report")
  return data as ReportResponse
}

export async function updateReport(
  reportId: string,
  payload: { title?: string; content_markdown?: string },
): Promise<ReportResponse> {
  const res = await fetchWithAuth(`/api/v1/ai/reports/${reportId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || "Failed to update report")
  return data as ReportResponse
}

export async function submitReport(
  reportId: string,
  engagementId: string,
  submissionNotes?: string,
): Promise<ReportResponse> {
  const res = await fetchWithAuth(`/api/v1/ai/reports/${reportId}/submit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      engagement_id: engagementId,
      submission_notes: submissionNotes,
    }),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || "Failed to submit report")
  return data as ReportResponse
}

export async function generateAndSubmitFrameworkReadinessReport(
  engagementId: string,
  orgId?: string,
  workspaceId?: string,
  frameworkId?: string,
  submissionNotes?: string,
): Promise<ReportResponse> {
  const params = new URLSearchParams()
  if (orgId) params.set("org_id", orgId)
  if (workspaceId) params.set("workspace_id", workspaceId)
  if (frameworkId) params.set("framework_id", frameworkId)
  
  const query = params.toString()
  const url = query 
    ? `/api/v1/ai/reports/framework-readiness/generate-and-submit?${query}`
    : `/api/v1/ai/reports/framework-readiness/generate-and-submit`
  
  const res = await fetchWithAuth(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      engagement_id: engagementId,
      submission_notes: submissionNotes,
    }),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || "Failed to generate and submit report")
  return data as ReportResponse
}

export async function uploadAndSubmitManualReport(
  file: File,
  engagementId: string,
  title: string,
  orgId?: string,
  workspaceId?: string,
  submissionNotes?: string,
): Promise<ReportResponse> {
  const formData = new FormData()
  formData.append("file", file)
  formData.append("engagement_id", engagementId)
  formData.append("title", title)
  if (orgId) formData.append("org_id", orgId)
  if (workspaceId) formData.append("workspace_id", workspaceId)
  if (submissionNotes) formData.append("submission_notes", submissionNotes)

  const res = await fetchWithAuth(`/api/v1/ai/reports/manual-upload-and-submit`, {
    method: "POST",
    body: formData,
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || "Failed to upload and submit manual report")
  return data as ReportResponse
}

export async function listReports(
  orgId?: string,
  reportType?: string,
  engagementId?: string,
  limit = 20,
  offset = 0
): Promise<ReportListResponse> {
  const params = new URLSearchParams()
  if (orgId) params.set("org_id", orgId)
  if (reportType) params.set("report_type", reportType)
  if (engagementId) params.set("engagement_id", engagementId)
  params.set("limit", String(limit))
  params.set("offset", String(offset))
  const res = await fetchWithAuth(`/api/v1/ai/reports?${params}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || "Failed to list reports")
  return data as ReportListResponse
}

export async function listEngagementReports(
  engagementId: string,
  limit = 20,
  offset = 0
): Promise<ReportListResponse> {
  const params = new URLSearchParams()
  params.set("limit", String(limit))
  params.set("offset", String(offset))
  const res = await fetchWithAuth(`/api/v1/ai/reports/engagement/${engagementId}?${params}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || "Failed to list engagement reports")
  return data as ReportListResponse
}

export async function getReport(reportId: string): Promise<ReportResponse> {
  const res = await fetchWithAuth(`/api/v1/ai/reports/${reportId}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || "Failed to get report")
  return data as ReportResponse
}

export async function deleteReport(reportId: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/ai/reports/${reportId}`, { method: "DELETE" })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error((data as any).detail || "Failed to delete report")
  }
}

export async function downloadReportMarkdown(reportId: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/ai/reports/${reportId}/download/md`)
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error((data as any).detail || "Failed to download report")
  }
  const blob = await res.blob()
  const cd = res.headers.get("content-disposition") ?? ""
  const match = cd.match(/filename="?([^"]+)"?/)
  const filename = match ? match[1] : `report_${reportId}.md`
  const url = URL.createObjectURL(blob)
  const a = document.createElement("a")
  a.href = url; a.download = filename; a.click()
  URL.revokeObjectURL(url)
}

export async function getReportJobStatus(jobId: string): Promise<ReportJobStatusResponse> {
  const res = await fetchWithAuth(`/api/v1/ai/reports/jobs/${jobId}/status`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || "Failed to get job status")
  return data as ReportJobStatusResponse
}

export interface EnhanceSectionRequest {
  section_title?: string
  current_section_markdown: string
  instruction: string
  org_id: string
  workspace_id?: string
}

/**
 * Stream AI enhancement for a single section of a completed report.
 * Returns the raw Response for SSE streaming — caller reads the body stream.
 * SSE events: content_delta, enhance_complete, enhance_error
 */
export async function streamEnhanceReportSection(
  reportId: string,
  payload: EnhanceSectionRequest,
  signal?: AbortSignal
): Promise<Response> {
  const res = await fetchWithAuth(`/api/v1/ai/reports/${reportId}/enhance-section`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    signal,
  })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error((data as any).detail || "Failed to start section enhancement")
  }
  return res
}

export interface SuggestedFinding {
  severity: string
  section: string
  title: string
  description: string
  recommendation: string
}

export interface AssessmentSuggestion {
  verdict: "satisfactory" | "needs_revision" | "rejected"
  verdict_rationale: string
  findings: SuggestedFinding[]
}

/**
 * Stream an AI-generated assessment suggestion for a completed report.
 * SSE events: content_delta, suggestion_complete, suggestion_error
 */
export async function streamSuggestAssessment(
  reportId: string,
  payload: { org_id: string; workspace_id?: string }
): Promise<Response> {
  const res = await fetchWithAuth(`/api/v1/ai/reports/${reportId}/suggest-assessment`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error((data as any).detail || "Failed to start assessment suggestion")
  }
  return res
}

// ── Framework Builder ──────────────────────────────────────────────────────────

export interface BuilderSession {
  id: string
  tenant_key: string
  user_id: string
  session_type: "create" | "enhance" | "gap"
  status: string
  framework_id: string | null
  framework_name: string | null
  framework_type_code: string | null
  framework_category_code: string | null
  user_context: string | null
  attachment_ids: string[]
  node_overrides: Record<string, string>
  proposed_hierarchy: Record<string, unknown> | null
  proposed_controls: unknown[] | null
  proposed_risks: unknown[] | null
  proposed_risk_mappings: unknown[] | null
  enhance_diff: unknown[] | null
  accepted_changes: unknown[] | null
  activity_log: Record<string, unknown>[]
  job_id: string | null
  result_framework_id: string | null
  error_message: string | null
  created_at: string
  updated_at: string
}

export interface BuilderSessionListResponse {
  items: BuilderSession[]
  total: number
}

export interface CreateBuilderSessionRequest {
  session_type?: "create" | "enhance" | "gap"
  framework_id?: string
  framework_name?: string
  framework_type_code?: string
  framework_category_code?: string
  user_context?: string
  attachment_ids?: string[]
  scope_org_id: string
  scope_workspace_id: string
}

export interface PatchBuilderSessionRequest {
  framework_name?: string
  framework_type_code?: string
  framework_category_code?: string
  user_context?: string
  attachment_ids?: string[]
  node_overrides?: Record<string, string>
  accepted_changes?: unknown[]
  proposed_hierarchy?: Record<string, unknown> | null
  proposed_controls?: unknown[] | null
  proposed_risks?: unknown[] | null
  proposed_risk_mappings?: unknown[] | null
}

export interface BuildJobStatus {
  job_id: string
  status: string
  job_type: string
  creation_log: Array<Record<string, unknown>>
  framework_id: string | null
  stats: Record<string, unknown> | null
  error_message: string | null
  started_at: string | null
  completed_at: string | null
}

export interface GapFinding {
  severity: "critical" | "high" | "medium" | "low"
  category: string
  title: string
  description: string
  requirement_code: string | null
  control_code: string | null
}

export interface GapAnalysisReport {
  framework_id: string
  framework_name: string
  generated_at: string
  requirement_count: number
  control_count: number
  risk_count: number
  health_score: number
  automation_score: number
  risk_coverage_pct: number
  findings: GapFinding[]
  benchmark: { profile: string; findings: string[]; score: number } | null
}

export interface GapAnalysisJobStatus {
  job_id: string
  status: string
  report: GapAnalysisReport | null
  error_message: string | null
  started_at: string | null
  completed_at: string | null
}

const FB = "/api/v1/ai/framework-builder"

export async function createBuilderSession(payload: CreateBuilderSessionRequest): Promise<BuilderSession> {
  const res = await fetchWithAuth(`${FB}/sessions`, { method: "POST", body: JSON.stringify(payload) })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || "Failed to create builder session")
  return data as BuilderSession
}

export async function listBuilderSessions(params: {
  org_id: string
  workspace_id: string
  limit?: number
  offset?: number
}): Promise<BuilderSessionListResponse> {
  const { org_id, workspace_id, limit = 50, offset = 0 } = params
  const qs = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
    scope_org_id: org_id,
    scope_workspace_id: workspace_id,
  })
  const res = await fetchWithAuth(`${FB}/sessions?${qs}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || data.error?.message || "Failed to list sessions")
  return data as BuilderSessionListResponse
}

export async function getBuilderSession(sessionId: string): Promise<BuilderSession> {
  const res = await fetchWithAuth(`${FB}/sessions/${sessionId}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || "Failed to get session")
  return data as BuilderSession
}

export async function patchBuilderSession(sessionId: string, payload: PatchBuilderSessionRequest): Promise<BuilderSession> {
  const res = await fetchWithAuth(`${FB}/sessions/${sessionId}`, { method: "PATCH", body: JSON.stringify(payload) })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || "Failed to update session")
  return data as BuilderSession
}

/** Phase 1 SSE — streams requirement_ready events live. Returns raw Response for streaming. */
export async function streamBuilderHierarchy(sessionId: string): Promise<Response> {
  return fetchWithAuth(`${FB}/sessions/${sessionId}/stream/hierarchy`)
}

/** Phase 2 SSE — streams control_proposed + risk_mapped events live. */
export async function streamBuilderControls(sessionId: string): Promise<Response> {
  return fetchWithAuth(`${FB}/sessions/${sessionId}/stream/controls`)
}

/** Enqueue Phase 1 hierarchy as a background job. Returns immediately with job_id. */
export async function enqueueBuilderHierarchy(sessionId: string): Promise<BuildJobStatus> {
  const res = await fetchWithAuth(`${FB}/sessions/${sessionId}/enqueue-hierarchy`, { method: "POST" })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || "Failed to enqueue hierarchy generation")
  return data as BuildJobStatus
}

/** Enqueue Phase 2 controls as a background job. Returns immediately with job_id. */
export async function enqueueBuilderControls(sessionId: string): Promise<BuildJobStatus> {
  const res = await fetchWithAuth(`${FB}/sessions/${sessionId}/enqueue-controls`, { method: "POST" })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || "Failed to enqueue control generation")
  return data as BuildJobStatus
}

/** Enqueue Phase 3 background creation job. Returns immediately with job_id. */
export async function enqueueFrameworkCreation(sessionId: string): Promise<BuildJobStatus> {
  const res = await fetchWithAuth(`${FB}/sessions/${sessionId}/create`, { method: "POST", body: JSON.stringify({}) })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || "Failed to enqueue framework creation")
  return data as BuildJobStatus
}

/** Enhance SSE — streams change_proposed diff events for an existing framework. */
export async function streamBuilderEnhance(sessionId: string): Promise<Response> {
  return fetchWithAuth(`${FB}/sessions/${sessionId}/stream/enhance`)
}

/** Apply accepted enhance-mode changes as a background job. */
export async function applyBuilderEnhancements(sessionId: string, acceptedChanges: unknown[]): Promise<BuildJobStatus> {
  const res = await fetchWithAuth(`${FB}/sessions/${sessionId}/apply`, {
    method: "POST",
    body: JSON.stringify({ accepted_changes: acceptedChanges }),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || "Failed to apply enhancements")
  return data as BuildJobStatus
}

/** Poll Phase 3 or enhance job status for a session. */
export async function getBuilderSessionJob(sessionId: string): Promise<BuildJobStatus> {
  const res = await fetchWithAuth(`${FB}/sessions/${sessionId}/job`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || "Failed to get job status")
  return data as BuildJobStatus
}

/** Poll any builder job by ID. */
export async function getBuilderJob(jobId: string): Promise<BuildJobStatus> {
  const res = await fetchWithAuth(`${FB}/jobs/${jobId}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || "Failed to get builder job")
  return data as BuildJobStatus
}

export interface BuilderAttachmentResponse {
  id: string
  filename: string
  file_size_bytes: number | null
  status_code: "ready" | "failed" | "pending" | "processing"
}

/** Upload a document for use in the framework builder. Returns an attachment ID for use in session attachment_ids. */
export async function uploadBuilderAttachment(file: File): Promise<BuilderAttachmentResponse> {
  const form = new FormData()
  form.append("file", file)
  const res = await fetchWithAuth(`${FB}/attachments`, {
    method: "POST",
    body: form,
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || "Failed to upload attachment")
  return data as BuilderAttachmentResponse
}

/** Enqueue enhance diff analysis as a background job (survives navigation). */
export async function enqueueBuilderEnhanceDiff(sessionId: string): Promise<BuildJobStatus> {
  const res = await fetchWithAuth(`${FB}/sessions/${sessionId}/enqueue-enhance`, {
    method: "POST",
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || "Failed to enqueue enhance diff")
  return data as BuildJobStatus
}

/** Enqueue gap analysis for any framework. Optional user_context and attachment_ids for audit reports, tests, etc. */
export async function enqueueGapAnalysis(
  frameworkId: string,
  opts?: { user_context?: string; attachment_ids?: string[] },
): Promise<BuildJobStatus> {
  const res = await fetchWithAuth(`${FB}/gap-analysis`, {
    method: "POST",
    body: JSON.stringify({
      framework_id: frameworkId,
      ...(opts?.user_context ? { user_context: opts.user_context } : {}),
      ...(opts?.attachment_ids?.length ? { attachment_ids: opts.attachment_ids } : {}),
    }),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || "Failed to enqueue gap analysis")
  return data as BuildJobStatus
}

// ── Admin: Job Queue ───────────────────────────────────────────────────────────

export interface JobQueueItem {
  id: string
  tenant_key: string
  user_id: string
  org_id: string | null
  workspace_id: string | null
  agent_type_code: string
  priority_code: string
  status_code: string
  job_type: string
  input_json: Record<string, unknown>
  output_json: Record<string, unknown> | null
  error_message: string | null
  scheduled_at: string
  started_at: string | null
  completed_at: string | null
  estimated_tokens: number
  actual_tokens: number | null
  retry_count: number
  max_retries: number
  batch_id: string | null
  conversation_id: string | null
  created_at: string
  updated_at: string
}

export interface JobQueueListResponse {
  items: JobQueueItem[]
  total: number
}

export interface QueueDepthItem {
  agent_type_code: string
  agent_type_name: string | null
  status_code: string
  priority_code: string
  job_count: number
  estimated_tokens: number
  oldest_job_at: string | null
}

export interface RateLimitStatusItem {
  agent_type_code: string
  agent_type_name: string | null
  window_start: string
  requests_count: number
  tokens_count: number
  max_requests_per_minute: number | null
  max_tokens_per_minute: number | null
  max_concurrent_jobs: number | null
  request_utilization_pct: number | null
  token_utilization_pct: number | null
  is_at_limit: boolean
}

export interface UpdateRateLimitPayload {
  max_requests_per_minute?: number
  max_tokens_per_minute?: number
  max_concurrent_jobs?: number
  batch_size?: number
  batch_interval_seconds?: number
  cooldown_seconds?: number
}

/** Admin: list all jobs across users (requires ai_copilot.admin permission). */
export async function adminListJobs(params: {
  user_id?: string
  agent_type_code?: string
  status_code?: string
  limit?: number
  offset?: number
} = {}): Promise<JobQueueListResponse> {
  const { user_id, agent_type_code, status_code, limit = 100, offset = 0 } = params
  const qs = new URLSearchParams({ limit: String(limit), offset: String(offset) })
  if (user_id) qs.set("user_id", user_id)
  if (agent_type_code) qs.set("agent_type_code", agent_type_code)
  if (status_code) qs.set("status_code", status_code)
  const res = await fetchWithAuth(`/api/v1/ai/jobs?${qs}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list jobs")
  return data as JobQueueListResponse
}

/** Admin: get a single job by ID. */
export async function adminGetJob(jobId: string): Promise<JobQueueItem> {
  const res = await fetchWithAuth(`/api/v1/ai/jobs/${jobId}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to get job")
  return data as JobQueueItem
}

/** Admin: cancel a job. */
export async function adminCancelJob(jobId: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/ai/jobs/${jobId}/cancel`, { method: "POST" })
  if (!res.ok) {
    const data = await res.json()
    throw new Error(data.error?.message || "Failed to cancel job")
  }
}

/** Admin: get live queue depth per agent type + status. */
export async function adminGetQueueDepth(): Promise<QueueDepthItem[]> {
  const res = await fetchWithAuth("/api/v1/ai/jobs/admin/queue-depth")
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to get queue depth")
  return data as QueueDepthItem[]
}

/** Admin: get rate limit utilization per agent type. */
export async function adminGetRateLimits(): Promise<RateLimitStatusItem[]> {
  const res = await fetchWithAuth("/api/v1/ai/jobs/admin/rate-limits")
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to get rate limits")
  return data as RateLimitStatusItem[]
}

/** Admin: update rate limit config for an agent type. */
export async function adminUpdateRateLimit(
  agentTypeCode: string,
  payload: UpdateRateLimitPayload,
): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/ai/jobs/admin/rate-limits/${agentTypeCode}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  if (!res.ok) {
    const data = await res.json()
    throw new Error(data.error?.message || "Failed to update rate limit")
  }
}

/**
 * Download a report in the specified format using authenticated fetch.
 */
export async function downloadReport(reportId: string, format: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/ai/reports/${reportId}/download?fmt=${format}`)
  if (!res.ok) {
    // Attempt to parse error message if JSON, else fallback
    try {
      const data = await res.json()
      throw new Error(data.error?.message || "Failed to download report")
    } catch {
      throw new Error("Failed to download report: Authentication required or server error")
    }
  }

  const blob = await res.blob()
  const url = window.URL.createObjectURL(blob)

  // Try to get filename from headers
  const contentDisposition = res.headers.get("Content-Disposition")
  let filename = `report_${reportId.substring(0, 8)}.${format}`
  if (contentDisposition) {
    const match = contentDisposition.match(/filename="(.+)"/)
    if (match) filename = match[1]
  }

  const a = document.createElement("a")
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  window.URL.revokeObjectURL(url)
}

// ── Framework Audit Readiness ────────────────────────────────────────────────

export interface AuditReadinessControls {
  passed: number
  total: number
}

export interface AuditReadinessEvidence {
  complete: number
  total: number
}

export interface AuditReadinessResponse {
  framework_id: string
  controls_passing: AuditReadinessControls
  evidence_complete: AuditReadinessEvidence
  open_gaps: number
  auditor_access: string
  readiness_pct: number
}

export async function getAuditReadiness(
  frameworkId: string,
  orgId: string,
): Promise<AuditReadinessResponse> {
  const params = new URLSearchParams({ org_id: orgId })
  const res = await fetchWithAuth(`/api/v1/ai/reports/framework/${frameworkId}/audit-readiness?${params}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || "Failed to get audit readiness")
  return data as AuditReadinessResponse
}

export async function getFrameworkReports(
  frameworkId: string,
  limit = 50,
  offset = 0,
): Promise<ReportListResponse> {
  const params = new URLSearchParams({ limit: String(limit), offset: String(offset) })
  const res = await fetchWithAuth(`/api/v1/ai/reports/framework/${frameworkId}?${params}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || "Failed to get framework reports")
  return data as ReportListResponse
}
