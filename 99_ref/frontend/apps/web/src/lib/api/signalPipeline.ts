import { fetchWithAuth, API_BASE_URL, getAccessToken } from "./apiClient"

function getApiBase(): string { return API_BASE_URL }

// ── Types ──────────────────────────────────────────────────────────────────────

export interface CreateSpecSessionRequest {
  connector_type_code: string
  source_dataset_id?: string | null
  org_id?: string | null
  workspace_id?: string | null
  initial_prompt?: string | null
}

export interface SpecSessionResponse {
  id: string
  tenant_key: string
  user_id: string
  org_id: string | null
  workspace_id: string | null
  signal_id: string | null
  connector_type_code: string | null
  source_dataset_id: string | null
  status: string
  current_spec: SignalSpec | null
  feasibility_result: FeasibilityResult | null
  conversation_history: ConversationTurn[]
  job_id: string | null
  error_message: string | null
  created_at: string
  updated_at: string
}

export interface SpecSessionListResponse {
  items: SpecSessionResponse[]
  total: number
}

export interface SpecJobStatusResponse {
  job_id: string
  status: string
  job_type: string
  signal_id: string | null
  error_message: string | null
  started_at: string | null
  completed_at: string | null
  output_json: CodeGenProgress | null
}

export interface CodeGenTestResult {
  case_id: string | null
  scenario: string | null
  expected: string
  actual: string
  passed: boolean
  error: string | null
  stdout: string | null
}

export interface CodeGenIterationEntry {
  iteration: number
  compile_success: boolean
  compile_errors?: string[]
  pass_rate: number
  passed_count: number
  total_count: number
  note: string
}

export interface CodeGenProgress {
  current_iteration: number
  max_iterations: number
  generated_code_preview: string
  compile_success: boolean
  compile_errors: string[]
  test_results: CodeGenTestResult[]
  pass_rate: number
  status: "iterating" | "completed" | "exhausted"
  iteration_history: CodeGenIterationEntry[]
}

export interface SignalSpec {
  schema_version: string
  signal_code: string
  display_name: string
  description: string
  intent: string
  connector_type_code: string
  asset_types: string[]
  dataset_fields_used: FieldUsed[]
  feasibility: FeasibilityResult
  detection_logic: string
  configurable_args: ConfigurableArg[]
  test_scenarios: TestScenario[]
  ssf_mapping: SsfMapping
  expected_output_format: object
  spec_locked: boolean
  approved_at: string | null
}

export interface FieldUsed {
  field_path: string
  type: string
  required: boolean
  example: unknown
}

export interface FeasibilityResult {
  status: "feasible" | "partial" | "infeasible" | "pending" | "unknown"
  confidence: "high" | "medium" | "low"
  missing_fields: MissingField[]
  blocking_issues: string[]
  notes: string
}

export interface MissingField {
  field_path: string
  required: boolean
  reason: string
}

export interface ConfigurableArg {
  key: string
  label: string
  type: "integer" | "string" | "boolean" | "enum"
  default: unknown
  description: string
  min?: number | null
  max?: number | null
  options?: string[]
}

export interface TestScenario {
  scenario_name: string
  result_expectation: "pass" | "fail" | "warning"
}

export interface SsfMapping {
  standard: string
  event_type: string
  event_uri: string
  custom_event_uri: string | null
  signal_severity: string
  subject_type: string
}

export interface ConversationTurn {
  role: "user" | "assistant"
  content: string
}

export interface RichSchemaField {
  type: string
  example: unknown
  nullable: boolean
}

// ── SSE Event Types ────────────────────────────────────────────────────────────

export type SpecSseEvent =
  | { type: "spec_analyzing"; data: { message: string; pct: number } }
  | { type: "spec_field_identified"; data: { field_path: string; type: string; example: unknown; pct: number } }
  | { type: "spec_section_ready"; data: { section: string; value: unknown; label: string } }
  | { type: "spec_complete"; data: { spec: SignalSpec } }
  | { type: "feasibility_checking"; data: { message: string } }
  | { type: "feasibility_result"; data: FeasibilityResult }
  | { type: "spec_refined"; data: { spec: SignalSpec; message: string } }
  | { type: "error"; data: { message: string; detail?: string } }

// ── API functions ──────────────────────────────────────────────────────────────

export async function createSpecSession(req: CreateSpecSessionRequest): Promise<SpecSessionResponse> {
  const res = await fetchWithAuth("/api/v1/ai/signal-spec/sessions", {
    method: "POST",
    body: JSON.stringify(req),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data?.error?.message || data?.detail || "Failed to create session")
  return data
}

export async function listSpecSessions(params?: { limit?: number; offset?: number }): Promise<SpecSessionListResponse> {
  const q = new URLSearchParams()
  if (params?.limit) q.set("limit", String(params.limit))
  if (params?.offset) q.set("offset", String(params.offset))
  const res = await fetchWithAuth(`/api/v1/ai/signal-spec/sessions?${q}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data?.error?.message || "Failed to list sessions")
  return data
}

export async function getSpecSession(sessionId: string): Promise<SpecSessionResponse> {
  const res = await fetchWithAuth(`/api/v1/ai/signal-spec/sessions/${sessionId}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data?.error?.message || "Failed to get session")
  return data
}

export async function approveSpec(
  sessionId: string,
  opts?: {
    priority_code?: string
    auto_compose_threats?: boolean
    auto_build_library?: boolean
  }
): Promise<SpecJobStatusResponse> {
  const res = await fetchWithAuth(`/api/v1/ai/signal-spec/sessions/${sessionId}/approve`, {
    method: "POST",
    body: JSON.stringify({
      priority_code: opts?.priority_code ?? "normal",
      auto_compose_threats: opts?.auto_compose_threats ?? true,
      auto_build_library: opts?.auto_build_library ?? true,
    }),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data?.error?.message || data?.detail || "Failed to approve spec")
  return data
}

export async function getSpecJob(jobId: string): Promise<SpecJobStatusResponse> {
  const res = await fetchWithAuth(`/api/v1/ai/signal-spec/jobs/${jobId}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data?.error?.message || "Failed to get job")
  return data
}

export interface CodeGenJobDetails {
  id: string
  status_code: string
  job_type: string
  error_message: string | null
  output_json: CodeGenProgress | null
}

export async function getCodeGenJobDetails(jobId: string): Promise<CodeGenJobDetails> {
  const res = await fetchWithAuth(`/api/v1/ai/jobs/${jobId}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data?.error?.message || "Failed to get job details")
  return {
    id: data.id,
    status_code: data.status_code,
    job_type: data.job_type,
    error_message: data.error_message,
    output_json: data.output_json ?? null,
  }
}

export function streamSpecGenerate(
  sessionId: string,
  prompt: string,
  onEvent: (event: SpecSseEvent) => void,
  onDone: () => void,
  onError: (err: string) => void
): () => void {
  const url = `${getApiBase()}/api/v1/ai/signal-spec/sessions/${sessionId}/stream/generate?prompt=${encodeURIComponent(prompt)}`
  return _connectSSE(url, onEvent, onDone, onError)
}

export function streamSpecRefine(
  sessionId: string,
  message: string,
  onEvent: (event: SpecSseEvent) => void,
  onDone: () => void,
  onError: (err: string) => void
): () => void {
  const url = `${getApiBase()}/api/v1/ai/signal-spec/sessions/${sessionId}/stream/refine`
  // POST with SSE — use fetch + ReadableStream
  return _postSSE(url, { message }, onEvent, onDone, onError)
}

export function streamFeasibility(
  sessionId: string,
  onEvent: (event: SpecSseEvent) => void,
  onDone: () => void,
  onError: (err: string) => void
): () => void {
  const url = `${getApiBase()}/api/v1/ai/signal-spec/sessions/${sessionId}/stream/feasibility`
  return _connectSSE(url, onEvent, onDone, onError)
}

// ── SSE helpers ────────────────────────────────────────────────────────────────

function _connectSSE(
  url: string,
  onEvent: (event: SpecSseEvent) => void,
  onDone: () => void,
  onError: (err: string) => void
): () => void {
  let aborted = false
  const controller = new AbortController()

  const token = getAccessToken()

  fetch(url, {
    headers: { Authorization: token ? `Bearer ${token}` : "" },
    signal: controller.signal,
  }).then(async (res) => {
    if (!res.ok) {
      onError(`HTTP ${res.status}`)
      return
    }
    const reader = res.body?.getReader()
    if (!reader) { onDone(); return }
    const decoder = new TextDecoder()
    let buffer = ""

    while (!aborted) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const parts = buffer.split("\n\n")
      buffer = parts.pop() ?? ""
      for (const part of parts) {
        const evType = part.match(/^event: (.+)/m)?.[1]
        const dataStr = part.match(/^data: (.+)/m)?.[1]
        if (evType && dataStr) {
          try {
            const data = JSON.parse(dataStr)
            onEvent({ type: evType as SpecSseEvent["type"], data } as SpecSseEvent)
          } catch (_) { /* ignore parse errors */ }
        }
      }
    }
    onDone()
  }).catch((err) => {
    if (!aborted) onError(String(err))
  })

  return () => { aborted = true; controller.abort() }
}

function _postSSE(
  url: string,
  body: object,
  onEvent: (event: SpecSseEvent) => void,
  onDone: () => void,
  onError: (err: string) => void
): () => void {
  let aborted = false
  const controller = new AbortController()
  const token = getAccessToken()

  fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: token ? `Bearer ${token}` : "",
    },
    body: JSON.stringify(body),
    signal: controller.signal,
  }).then(async (res) => {
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}))
      onError(errData?.detail || errData?.error?.message || `HTTP ${res.status}`)
      return
    }
    const reader = res.body?.getReader()
    if (!reader) { onDone(); return }
    const decoder = new TextDecoder()
    let buffer = ""

    while (!aborted) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const parts = buffer.split("\n\n")
      buffer = parts.pop() ?? ""
      for (const part of parts) {
        const evType = part.match(/^event: (.+)/m)?.[1]
        const dataStr = part.match(/^data: (.+)/m)?.[1]
        if (evType && dataStr) {
          try {
            const data = JSON.parse(dataStr)
            onEvent({ type: evType as SpecSseEvent["type"], data } as SpecSseEvent)
          } catch (_) { /* ignore */ }
        }
      }
    }
    onDone()
  }).catch((err) => {
    if (!aborted) onError(String(err))
  })

  return () => { aborted = true; controller.abort() }
}


// ── Signal Test Datasets ────────────────────────────────────────────────────

export interface TestDatasetInfo {
  id: string
  dataset_code: string
  created_at: string
  record_count: number
  name: string | null
}

export async function getSignalTestDatasets(signalId: string): Promise<TestDatasetInfo[]> {
  const res = await fetchWithAuth(`/api/v1/ai/signal-spec/signals/${signalId}/test-datasets`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || "Failed to get test datasets")
  return data
}

// ── Data Sufficiency Check ──────────────────────────────────────────────────

export interface FieldCheck {
  field_path: string
  required: boolean
  status: "present" | "missing" | "inconsistent" | "partial"
  found_in_records: string[]
  missing_from_records: string[]
  sample_values: unknown[]
  notes: string
}

export interface RecordCoverage {
  record_name: string
  has_all_required_fields: boolean
  missing_fields: string[]
  extra_fields_available: string[]
}

export interface Disagreement {
  field_path: string
  primary_said: string
  verifier_says: string
  evidence: string
  resolution: string
}

export interface DataSufficiencyResponse {
  status: "sufficient" | "partial" | "insufficient"
  confidence: "high" | "medium" | "low"
  is_sufficient: boolean
  field_checks: FieldCheck[]
  record_coverage: RecordCoverage[]
  blocking_issues: string[]
  disagreements: Disagreement[]
  recommendations: string[]
  summary: string
  primary_check: Record<string, unknown>
  verifier_check: Record<string, unknown>
}

export interface GenerateTestDatasetResponse {
  overall_status: "ready" | "needs_fixes" | "failed"
  ready_for_codegen: boolean
  test_record_count: number
  scenario_coverage: {
    pass_scenarios?: number
    fail_scenarios?: number
    warning_scenarios?: number
    edge_case_scenarios?: number
  }
  generation: Record<string, unknown>
  verification: Record<string, unknown>
  saved_dataset_id?: string
  saved_dataset_name?: string
  save_error?: string
}

export async function generateSignalTestDataset(payload: {
  session_id: string
  dataset_id: string
  sufficiency_result?: Record<string, unknown>
}): Promise<GenerateTestDatasetResponse> {
  const res = await fetchWithAuth("/api/v1/ai/signal-spec/generate-test-dataset", {
    method: "POST",
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || data.error?.message || "Test dataset generation failed")
  return data as GenerateTestDatasetResponse
}

export async function retryPipelineStep(
  signalId: string,
  step: string,
  orgId: string
): Promise<{ job_id: string; job_type: string; status: string }> {
  const qs = new URLSearchParams({ org_id: orgId })
  const res = await fetchWithAuth(
    `/api/v1/ai/signal-spec/pipelines/${signalId}/retry-step?${qs}`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ step }),
    }
  )
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || "Failed to retry step")
  return data
}

export async function retryAllFailedSteps(
  signalId: string,
  orgId: string
): Promise<{ retried: Array<{ job_id: string; job_type: string; status: string }> }> {
  const qs = new URLSearchParams({ org_id: orgId })
  const res = await fetchWithAuth(
    `/api/v1/ai/signal-spec/pipelines/${signalId}/retry-all?${qs}`,
    { method: "POST" }
  )
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || "Failed to retry all steps")
  return data
}

export async function checkDataSufficiency(payload: {
  dataset_id: string
  signal_description: string
  required_fields?: string[]
}): Promise<DataSufficiencyResponse> {
  const res = await fetchWithAuth("/api/v1/ai/signal-spec/data-sufficiency", {
    method: "POST",
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || data.error?.message || "Data sufficiency check failed")
  return data as DataSufficiencyResponse
}
