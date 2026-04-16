"use client"

import { useEffect, useState, useCallback } from "react"
import { useParams, useRouter } from "next/navigation"
import { Save, Play, Loader2, CheckCircle2, XCircle, ArrowLeft, Settings2, Wrench, ClipboardCheck } from "lucide-react"
import { useAgentSandbox } from "@/lib/context/AgentSandboxContext"
import {
  getAgent,
  updateAgent,
  executeAgent,
  compileCheck,
  listBoundTools,
  type AgentResponse,
  type CompileCheckResponse,
} from "@/lib/api/agentSandbox"

export default function AgentBuilderPage() {
  const params = useParams()
  const router = useRouter()
  const agentId = params.id as string
  const { selectedOrgId, ready } = useAgentSandbox()

  const [agent, setAgent] = useState<AgentResponse | null>(null)
  const [graphSource, setGraphSource] = useState("")
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [executing, setExecuting] = useState(false)
  const [compileResult, setCompileResult] = useState<CompileCheckResponse | null>(null)
  const [boundTools, setBoundTools] = useState<Record<string, unknown>[]>([])
  const [activeTab, setActiveTab] = useState<"code" | "tools" | "tests" | "settings">("code")
  const [dirty, setDirty] = useState(false)

  const loadAgent = useCallback(async () => {
    setLoading(true)
    try {
      const a = await getAgent(agentId)
      setAgent(a)
      setGraphSource(a.graph_source || a.properties?.graph_source || "")
      const tools = await listBoundTools(agentId)
      setBoundTools(tools)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }, [agentId])

  useEffect(() => {
    if (!ready) return
    loadAgent()
  }, [ready, loadAgent])

  const handleSave = async () => {
    if (!selectedOrgId || !agent) return
    setSaving(true)
    try {
      await updateAgent(selectedOrgId, agentId, {
        properties: { graph_source: graphSource },
      })
      setDirty(false)
      await loadAgent()
    } catch (e) {
      alert((e as Error).message)
    } finally {
      setSaving(false)
    }
  }

  const handleCompileCheck = async () => {
    try {
      const result = await compileCheck(graphSource)
      setCompileResult(result)
    } catch (e) {
      setCompileResult({ success: false, errors: [(e as Error).message], handler_names: null })
    }
  }

  const handleExecute = async () => {
    if (!selectedOrgId) return
    setExecuting(true)
    try {
      // Save first if dirty
      if (dirty) await handleSave()
      const run = await executeAgent(selectedOrgId, agentId, {})
      router.push(`/agent-sandbox/runs?run_id=${run.id}`)
    } catch (e) {
      alert((e as Error).message)
    } finally {
      setExecuting(false)
    }
  }

  if (loading) {
    return <div className="flex items-center justify-center h-64 text-muted-foreground">Loading agent...</div>
  }

  if (!agent) {
    return <div className="flex items-center justify-center h-64 text-muted-foreground">Agent not found</div>
  }

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      {/* Header */}
      <div className="flex items-center justify-between gap-4 pb-4 border-b">
        <div className="flex items-center gap-3">
          <button onClick={() => router.push("/agent-sandbox/agents")} className="rounded-md p-1.5 hover:bg-muted">
            <ArrowLeft className="h-4 w-4" />
          </button>
          <div>
            <h2 className="text-lg font-semibold">{agent.name || agent.agent_code}</h2>
            <p className="text-xs text-muted-foreground">
              {agent.agent_code} &middot; v{agent.version_number} &middot; {agent.agent_status_code} &middot; {agent.graph_type}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {compileResult && (
            <span className={`inline-flex items-center gap-1 text-xs ${compileResult.success ? "text-green-600" : "text-red-600"}`}>
              {compileResult.success ? <CheckCircle2 className="h-3.5 w-3.5" /> : <XCircle className="h-3.5 w-3.5" />}
              {compileResult.success ? `OK (${compileResult.handler_names?.length ?? 0} handlers)` : compileResult.errors?.[0]}
            </span>
          )}
          <button
            onClick={handleCompileCheck}
            className="rounded-md border px-3 py-1.5 text-xs font-medium hover:bg-muted"
          >
            Check
          </button>
          <button
            onClick={handleSave}
            disabled={saving || !dirty}
            className="inline-flex items-center gap-1.5 rounded-md border px-3 py-1.5 text-xs font-medium hover:bg-muted disabled:opacity-40"
          >
            {saving ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Save className="h-3.5 w-3.5" />}
            Save
          </button>
          <button
            onClick={handleExecute}
            disabled={executing}
            className="inline-flex items-center gap-1.5 rounded-md bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
          >
            {executing ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Play className="h-3.5 w-3.5" />}
            Execute
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b">
        {(["code", "tools", "tests", "settings"] as const).map((tab) => {
          const icons = { code: null, tools: Wrench, tests: ClipboardCheck, settings: Settings2 }
          const Icon = icons[tab]
          return (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`inline-flex items-center gap-1.5 px-4 py-2 text-sm border-b-2 transition-colors ${
                activeTab === tab ? "border-primary text-foreground font-medium" : "border-transparent text-muted-foreground hover:text-foreground"
              }`}
            >
              {Icon && <Icon className="h-3.5 w-3.5" />}
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
              {tab === "tools" && boundTools.length > 0 && (
                <span className="rounded-full bg-muted px-1.5 py-0.5 text-[10px] font-medium">{boundTools.length}</span>
              )}
            </button>
          )
        })}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden">
        {activeTab === "code" && (
          <div className="h-full flex flex-col">
            <textarea
              value={graphSource}
              onChange={(e) => { setGraphSource(e.target.value); setDirty(true); setCompileResult(null) }}
              spellCheck={false}
              className="flex-1 w-full p-4 font-mono text-sm leading-relaxed bg-muted/30 resize-none outline-none"
              placeholder="Write your agent code here..."
            />
          </div>
        )}

        {activeTab === "tools" && (
          <div className="p-4 space-y-3">
            <p className="text-sm text-muted-foreground">
              Tools bound to this agent ({boundTools.length}):
            </p>
            {boundTools.length === 0 ? (
              <div className="rounded-lg border border-dashed p-6 text-center text-sm text-muted-foreground">
                No tools bound yet. Go to Agent Tools to register tools, then bind them here.
              </div>
            ) : (
              <div className="space-y-2">
                {boundTools.map((t, i) => (
                  <div key={i} className="flex items-center justify-between rounded-lg border p-3">
                    <div className="flex items-center gap-2">
                      <Wrench className="h-4 w-4 text-muted-foreground" />
                      <span className="text-sm font-medium">{(t as Record<string, string>).tool_name || (t as Record<string, string>).tool_code}</span>
                      <span className="text-xs text-muted-foreground font-mono">{(t as Record<string, string>).tool_type_code}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === "tests" && (
          <div className="p-4">
            <div className="rounded-lg border border-dashed p-6 text-center text-sm text-muted-foreground">
              Test scenarios for this agent. Create scenarios from the Test Scenarios page and run them against this agent.
            </div>
          </div>
        )}

        {activeTab === "settings" && (
          <div className="p-4 space-y-4 max-w-xl">
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label className="text-xs font-medium text-muted-foreground">Max Iterations</label>
                <p className="text-sm font-mono">{agent.max_iterations}</p>
              </div>
              <div>
                <label className="text-xs font-medium text-muted-foreground">Max Tokens Budget</label>
                <p className="text-sm font-mono">{agent.max_tokens_budget.toLocaleString()}</p>
              </div>
              <div>
                <label className="text-xs font-medium text-muted-foreground">Max Tool Calls</label>
                <p className="text-sm font-mono">{agent.max_tool_calls}</p>
              </div>
              <div>
                <label className="text-xs font-medium text-muted-foreground">Max Duration</label>
                <p className="text-sm font-mono">{(agent.max_duration_ms / 1000).toFixed(0)}s</p>
              </div>
              <div>
                <label className="text-xs font-medium text-muted-foreground">Max Cost</label>
                <p className="text-sm font-mono">${agent.max_cost_usd.toFixed(2)}</p>
              </div>
              <div>
                <label className="text-xs font-medium text-muted-foreground">Temperature</label>
                <p className="text-sm font-mono">{agent.temperature}</p>
              </div>
              <div>
                <label className="text-xs font-medium text-muted-foreground">LLM Model</label>
                <p className="text-sm font-mono">{agent.llm_model_id || "default"}</p>
              </div>
              <div>
                <label className="text-xs font-medium text-muted-foreground">Requires Approval</label>
                <p className="text-sm">{agent.requires_approval ? "Yes" : "No"}</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
