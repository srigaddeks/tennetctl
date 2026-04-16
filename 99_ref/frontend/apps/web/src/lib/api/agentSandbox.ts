import { fetchWithAuth } from "./apiClient"

const BASE = "/api/v1/asb"

// ─────────────────────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────────────────────

export interface AgentResponse {
  id: string
  tenant_key: string
  org_id: string
  workspace_id: string | null
  agent_code: string
  version_number: number
  agent_status_code: string
  agent_status_name: string | null
  graph_type: string
  llm_model_id: string | null
  temperature: number
  max_iterations: number
  max_tokens_budget: number
  max_tool_calls: number
  max_duration_ms: number
  max_cost_usd: number
  requires_approval: boolean
  python_hash: string | null
  is_active: boolean
  created_at: string
  updated_at: string
  name: string | null
  description: string | null
  graph_source: string | null
  properties: Record<string, string> | null
}

export interface AgentListResponse {
  items: AgentResponse[]
  total: number
}

export interface ToolResponse {
  id: string
  tenant_key: string
  org_id: string
  tool_code: string
  tool_type_code: string
  input_schema: Record<string, unknown>
  output_schema: Record<string, unknown>
  endpoint_url: string | null
  mcp_server_url: string | null
  python_source: string | null
  signal_id: string | null
  requires_approval: boolean
  is_destructive: boolean
  timeout_ms: number
  is_active: boolean
  created_at: string
  updated_at: string
  name: string | null
  description: string | null
  properties: Record<string, string> | null
}

export interface ToolListResponse {
  items: ToolResponse[]
  total: number
}

export interface AgentRunResponse {
  id: string
  tenant_key: string
  org_id: string
  workspace_id: string | null
  agent_id: string
  execution_status_code: string
  execution_status_name: string | null
  tokens_used: number
  tool_calls_made: number
  llm_calls_made: number
  cost_usd: number
  iterations_used: number
  error_message: string | null
  started_at: string | null
  completed_at: string | null
  execution_time_ms: number | null
  agent_code_snapshot: string | null
  version_snapshot: number | null
  agent_name: string | null
  created_at: string
}

export interface AgentRunListResponse {
  items: AgentRunResponse[]
  total: number
}

export interface AgentRunStepResponse {
  id: string
  agent_run_id: string
  step_index: number
  node_name: string
  step_type: string
  transition: string | null
  tokens_used: number
  cost_usd: number
  duration_ms: number | null
  error_message: string | null
  started_at: string
  completed_at: string | null
}

export interface ScenarioResponse {
  id: string
  tenant_key: string
  org_id: string
  workspace_id: string | null
  scenario_code: string
  scenario_type_code: string
  agent_id: string | null
  is_active: boolean
  created_at: string
  updated_at: string
  name: string | null
  description: string | null
  test_cases: TestCaseResponse[] | null
  properties: Record<string, string> | null
}

export interface ScenarioListResponse {
  items: ScenarioResponse[]
  total: number
}

export interface TestCaseResponse {
  id: string
  scenario_id: string
  case_index: number
  input_messages: Record<string, unknown>[]
  initial_context: Record<string, unknown>
  expected_behavior: Record<string, unknown>
  evaluation_method_code: string
  evaluation_config: Record<string, unknown>
  is_active: boolean
  created_at: string
}

export interface CompileCheckResponse {
  success: boolean
  errors: string[] | null
  handler_names: string[] | null
}

export interface TestRunResult {
  test_run_id: string
  scenario_id: string
  agent_id: string
  total_cases: number
  passed: number
  failed: number
  pass_rate: number
  total_tokens: number
  total_cost_usd: number
  total_duration_ms: number
  results: TestCaseResult[]
}

export interface TestCaseResult {
  case_id: string
  case_index: number
  passed: boolean
  score: number
  reason: string
  execution_time_ms: number
}

// ─────────────────────────────────────────────────────────────────────────────
// Dimensions
// ─────────────────────────────────────────────────────────────────────────────

export async function getAgentSandboxStats(orgId: string): Promise<Record<string, number>> {
  const res = await fetchWithAuth(`${BASE}/dimensions/stats?org_id=${orgId}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data?.detail || "Failed to fetch stats")
  return data
}

export async function listDimension(name: string): Promise<Record<string, unknown>[]> {
  const res = await fetchWithAuth(`${BASE}/dimensions/${name}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data?.detail || `Failed to list ${name}`)
  return data
}

// ─────────────────────────────────────────────────────────────────────────────
// Agents
// ─────────────────────────────────────────────────────────────────────────────

export async function listAgents(params: {
  org_id: string
  workspace_id?: string
  agent_status_code?: string
  search?: string
  limit?: number
  offset?: number
}): Promise<AgentListResponse> {
  const q = new URLSearchParams()
  q.set("org_id", params.org_id)
  if (params.workspace_id) q.set("workspace_id", params.workspace_id)
  if (params.agent_status_code) q.set("agent_status_code", params.agent_status_code)
  if (params.search) q.set("search", params.search)
  if (params.limit) q.set("limit", String(params.limit))
  if (params.offset) q.set("offset", String(params.offset))
  const res = await fetchWithAuth(`${BASE}/agents?${q}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data?.detail || "Failed to list agents")
  return data
}

export async function getAgent(agentId: string): Promise<AgentResponse> {
  const res = await fetchWithAuth(`${BASE}/agents/${agentId}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data?.detail || "Failed to get agent")
  return data
}

export async function createAgent(orgId: string, payload: {
  agent_code: string
  workspace_id?: string
  graph_type?: string
  llm_model_id?: string
  temperature?: number
  max_iterations?: number
  max_tokens_budget?: number
  max_tool_calls?: number
  max_duration_ms?: number
  max_cost_usd?: number
  requires_approval?: boolean
  properties: Record<string, string>
}): Promise<AgentResponse> {
  const res = await fetchWithAuth(`${BASE}/agents?org_id=${orgId}`, {
    method: "POST",
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data?.detail || "Failed to create agent")
  return data
}

export async function updateAgent(orgId: string, agentId: string, payload: {
  graph_type?: string
  llm_model_id?: string
  temperature?: number
  max_iterations?: number
  max_tokens_budget?: number
  max_tool_calls?: number
  max_duration_ms?: number
  max_cost_usd?: number
  requires_approval?: boolean
  properties?: Record<string, string>
}): Promise<AgentResponse> {
  const res = await fetchWithAuth(`${BASE}/agents/${agentId}?org_id=${orgId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data?.detail || "Failed to update agent")
  return data
}

export async function deleteAgent(orgId: string, agentId: string): Promise<void> {
  const res = await fetchWithAuth(`${BASE}/agents/${agentId}?org_id=${orgId}`, { method: "DELETE" })
  if (!res.ok) {
    const data = await res.json()
    throw new Error(data?.detail || "Failed to delete agent")
  }
}

export async function executeAgent(orgId: string, agentId: string, payload: {
  input_messages?: Record<string, unknown>[]
  initial_context?: Record<string, unknown>
}): Promise<AgentRunResponse> {
  const res = await fetchWithAuth(`${BASE}/agents/${agentId}/execute?org_id=${orgId}`, {
    method: "POST",
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data?.detail || "Failed to execute agent")
  return data
}

export async function compileCheck(graphSource: string): Promise<CompileCheckResponse> {
  const res = await fetchWithAuth(`${BASE}/compile-check`, {
    method: "POST",
    body: JSON.stringify({ graph_source: graphSource }),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data?.detail || "Failed to compile check")
  return data
}

// ─────────────────────────────────────────────────────────────────────────────
// Agent Tools
// ─────────────────────────────────────────────────────────────────────────────

export async function listTools(params: {
  org_id: string
  tool_type_code?: string
  search?: string
}): Promise<ToolListResponse> {
  const q = new URLSearchParams()
  q.set("org_id", params.org_id)
  if (params.tool_type_code) q.set("tool_type_code", params.tool_type_code)
  if (params.search) q.set("search", params.search)
  const res = await fetchWithAuth(`${BASE}/tools?${q}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data?.detail || "Failed to list tools")
  return data
}

export async function createTool(orgId: string, payload: {
  tool_code: string
  tool_type_code: string
  input_schema?: Record<string, unknown>
  output_schema?: Record<string, unknown>
  endpoint_url?: string
  mcp_server_url?: string
  python_source?: string
  signal_id?: string
  requires_approval?: boolean
  is_destructive?: boolean
  timeout_ms?: number
  properties?: Record<string, string>
}): Promise<ToolResponse> {
  const res = await fetchWithAuth(`${BASE}/tools?org_id=${orgId}`, {
    method: "POST",
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data?.detail || "Failed to create tool")
  return data
}

export async function deleteTool(orgId: string, toolId: string): Promise<void> {
  const res = await fetchWithAuth(`${BASE}/tools/${toolId}?org_id=${orgId}`, { method: "DELETE" })
  if (!res.ok) {
    const data = await res.json()
    throw new Error(data?.detail || "Failed to delete tool")
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Runs
// ─────────────────────────────────────────────────────────────────────────────

export async function listRuns(params: {
  org_id: string
  agent_id?: string
  execution_status_code?: string
  limit?: number
  offset?: number
}): Promise<AgentRunListResponse> {
  const q = new URLSearchParams()
  q.set("org_id", params.org_id)
  if (params.agent_id) q.set("agent_id", params.agent_id)
  if (params.execution_status_code) q.set("execution_status_code", params.execution_status_code)
  if (params.limit) q.set("limit", String(params.limit))
  if (params.offset) q.set("offset", String(params.offset))
  const res = await fetchWithAuth(`${BASE}/runs?${q}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data?.detail || "Failed to list runs")
  return data
}

export async function getRun(runId: string): Promise<AgentRunResponse> {
  const res = await fetchWithAuth(`${BASE}/runs/${runId}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data?.detail || "Failed to get run")
  return data
}

export async function getRunSteps(runId: string): Promise<AgentRunStepResponse[]> {
  const res = await fetchWithAuth(`${BASE}/runs/${runId}/steps`)
  const data = await res.json()
  if (!res.ok) throw new Error(data?.detail || "Failed to get run steps")
  return data
}

export async function cancelRun(runId: string): Promise<AgentRunResponse> {
  const res = await fetchWithAuth(`${BASE}/runs/${runId}/cancel`, { method: "POST" })
  const data = await res.json()
  if (!res.ok) throw new Error(data?.detail || "Failed to cancel run")
  return data
}

// ─────────────────────────────────────────────────────────────────────────────
// Test Scenarios
// ─────────────────────────────────────────────────────────────────────────────

export async function listScenarios(params: {
  org_id: string
  agent_id?: string
}): Promise<ScenarioListResponse> {
  const q = new URLSearchParams()
  q.set("org_id", params.org_id)
  if (params.agent_id) q.set("agent_id", params.agent_id)
  const res = await fetchWithAuth(`${BASE}/scenarios?${q}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data?.detail || "Failed to list scenarios")
  return data
}

export async function getScenario(scenarioId: string): Promise<ScenarioResponse> {
  const res = await fetchWithAuth(`${BASE}/scenarios/${scenarioId}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data?.detail || "Failed to get scenario")
  return data
}

export async function createScenario(orgId: string, payload: {
  scenario_code: string
  scenario_type_code?: string
  workspace_id?: string
  agent_id?: string
  properties?: Record<string, string>
}): Promise<ScenarioResponse> {
  const res = await fetchWithAuth(`${BASE}/scenarios?org_id=${orgId}`, {
    method: "POST",
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data?.detail || "Failed to create scenario")
  return data
}

export async function runScenario(orgId: string, scenarioId: string, agentId?: string): Promise<TestRunResult> {
  const q = new URLSearchParams()
  q.set("org_id", orgId)
  if (agentId) q.set("agent_id", agentId)
  const res = await fetchWithAuth(`${BASE}/scenarios/${scenarioId}/run?${q}`, { method: "POST" })
  const data = await res.json()
  if (!res.ok) throw new Error(data?.detail || "Failed to run scenario")
  return data
}

export async function listTestResults(orgId: string): Promise<{ items: Record<string, unknown>[]; total: number }> {
  const res = await fetchWithAuth(`${BASE}/test-results?org_id=${orgId}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data?.detail || "Failed to list test results")
  return data
}

// ─────────────────────────────────────────────────────────────────────────────
// Bound tools
// ─────────────────────────────────────────────────────────────────────────────

export async function listBoundTools(agentId: string): Promise<Record<string, unknown>[]> {
  const res = await fetchWithAuth(`${BASE}/agents/${agentId}/tools`)
  const data = await res.json()
  if (!res.ok) throw new Error(data?.detail || "Failed to list bound tools")
  return data
}

export async function bindTool(orgId: string, agentId: string, toolId: string, sortOrder?: number): Promise<void> {
  const res = await fetchWithAuth(`${BASE}/agents/${agentId}/tools?org_id=${orgId}`, {
    method: "POST",
    body: JSON.stringify({ tool_id: toolId, sort_order: sortOrder ?? 0 }),
  })
  if (!res.ok) {
    const data = await res.json()
    throw new Error(data?.detail || "Failed to bind tool")
  }
}

export async function unbindTool(orgId: string, agentId: string, toolId: string): Promise<void> {
  const res = await fetchWithAuth(`${BASE}/agents/${agentId}/tools/${toolId}?org_id=${orgId}`, { method: "DELETE" })
  if (!res.ok) {
    const data = await res.json()
    throw new Error(data?.detail || "Failed to unbind tool")
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Registry
// ─────────────────────────────────────────────────────────────────────────────

export interface AgentCatalogInput {
  name: string
  type: string
  required: boolean
  description: string
  default: string | null
  options: string[] | null
}

export interface AgentCatalogEntry {
  code: string
  name: string
  description: string
  category: string
  execution_mode: string
  module_path: string
  inputs: AgentCatalogInput[]
  outputs: string[]
  tools_used: string[]
  tags: string[]
  default_model: string
  default_temperature: number
  max_iterations: number
  supports_conversation: boolean
  icon: string
}

export interface RegistryResponse {
  items: AgentCatalogEntry[]
  total: number
  categories: string[]
  tags: string[]
}

export async function listRegisteredAgents(params?: {
  category?: string
  tag?: string
}): Promise<RegistryResponse> {
  const q = new URLSearchParams()
  if (params?.category) q.set("category", params.category)
  if (params?.tag) q.set("tag", params.tag)
  const qs = q.toString()
  const res = await fetchWithAuth(`${BASE}/registry/${qs ? `?${qs}` : ""}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data?.detail || "Failed to list registered agents")
  return data
}

export async function getRegisteredAgent(agentCode: string): Promise<AgentCatalogEntry> {
  const res = await fetchWithAuth(`${BASE}/registry/${agentCode}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data?.detail || "Failed to get registered agent")
  return data
}

// ─────────────────────────────────────────────────────────────────────────────
// Playground
// ─────────────────────────────────────────────────────────────────────────────

export function playgroundRunUrl(agentCode: string, orgId: string, workspaceId?: string): string {
  const q = new URLSearchParams()
  q.set("org_id", orgId)
  if (workspaceId) q.set("workspace_id", workspaceId)
  return `${BASE}/playground/${agentCode}/run?${q}`
}
