"use client"

import { useEffect, useState } from "react"
import { Play, XCircle, CheckCircle2, Clock, AlertTriangle, Loader2 } from "lucide-react"
import { useAgentSandbox } from "@/lib/context/AgentSandboxContext"
import { listRuns, getRunSteps, cancelRun, type AgentRunResponse, type AgentRunStepResponse } from "@/lib/api/agentSandbox"

const STATUS_ICONS: Record<string, React.ElementType> = {
  completed: CheckCircle2,
  failed: XCircle,
  running: Loader2,
  queued: Clock,
  timeout: AlertTriangle,
  cancelled: XCircle,
  awaiting_approval: Clock,
}

const STATUS_COLORS: Record<string, string> = {
  completed: "text-green-600",
  failed: "text-red-600",
  running: "text-blue-600",
  queued: "text-gray-500",
  timeout: "text-yellow-600",
  cancelled: "text-gray-500",
  awaiting_approval: "text-orange-500",
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-US", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })
}

export default function RunsPage() {
  const { selectedOrgId, ready } = useAgentSandbox()

  const [runs, setRuns] = useState<AgentRunResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [expandedRun, setExpandedRun] = useState<string | null>(null)
  const [steps, setSteps] = useState<AgentRunStepResponse[]>([])
  const [stepsLoading, setStepsLoading] = useState(false)

  useEffect(() => {
    if (!ready || !selectedOrgId) return
    setLoading(true)
    listRuns({ org_id: selectedOrgId })
      .then((res) => setRuns(res.items))
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [ready, selectedOrgId])

  const handleExpandRun = async (runId: string) => {
    if (expandedRun === runId) {
      setExpandedRun(null)
      return
    }
    setExpandedRun(runId)
    setStepsLoading(true)
    try {
      const s = await getRunSteps(runId)
      setSteps(s)
    } catch {
      setSteps([])
    } finally {
      setStepsLoading(false)
    }
  }

  const handleCancel = async (runId: string) => {
    try {
      await cancelRun(runId)
      // Refresh
      listRuns({ org_id: selectedOrgId }).then((res) => setRuns(res.items))
    } catch (e) {
      alert((e as Error).message)
    }
  }

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold">Agent Runs</h2>
        <p className="text-sm text-muted-foreground">Execution history with full trace visibility</p>
      </div>

      <div className="rounded-lg border">
        {loading ? (
          <div className="p-8 text-center text-sm text-muted-foreground">Loading...</div>
        ) : runs.length === 0 ? (
          <div className="p-8 text-center text-sm text-muted-foreground">No agent runs yet. Execute an agent to see results here.</div>
        ) : (
          <div className="divide-y">
            {runs.map((run) => {
              const StatusIcon = STATUS_ICONS[run.execution_status_code] ?? Play
              const statusColor = STATUS_COLORS[run.execution_status_code] ?? "text-gray-500"
              const isExpanded = expandedRun === run.id

              return (
                <div key={run.id}>
                  <div
                    className="flex items-center gap-4 px-4 py-3 hover:bg-muted/30 cursor-pointer"
                    onClick={() => handleExpandRun(run.id)}
                  >
                    <StatusIcon className={`h-4 w-4 shrink-0 ${statusColor} ${run.execution_status_code === "running" ? "animate-spin" : ""}`} />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium truncate">{run.agent_name || run.agent_code_snapshot || "Unknown"}</span>
                        <span className="text-xs text-muted-foreground">v{run.version_snapshot}</span>
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {run.execution_status_code} &middot; {run.iterations_used} iters &middot; {run.tokens_used.toLocaleString()} tokens &middot; ${run.cost_usd.toFixed(4)}
                        {run.execution_time_ms && ` \u00b7 ${(run.execution_time_ms / 1000).toFixed(1)}s`}
                      </div>
                    </div>
                    <span className="text-xs text-muted-foreground shrink-0">{formatDate(run.created_at)}</span>
                    {["running", "queued", "paused", "awaiting_approval"].includes(run.execution_status_code) && (
                      <button
                        onClick={(e) => { e.stopPropagation(); handleCancel(run.id) }}
                        className="rounded-md border px-2 py-1 text-xs hover:bg-destructive/10 text-destructive"
                      >
                        Cancel
                      </button>
                    )}
                  </div>

                  {/* Expanded trace */}
                  {isExpanded && (
                    <div className="px-4 pb-4 pl-12">
                      {run.error_message && (
                        <div className="mb-3 rounded-md bg-destructive/10 p-3 text-xs text-destructive">
                          {run.error_message}
                        </div>
                      )}
                      {stepsLoading ? (
                        <p className="text-xs text-muted-foreground">Loading steps...</p>
                      ) : steps.length === 0 ? (
                        <p className="text-xs text-muted-foreground">No execution steps recorded</p>
                      ) : (
                        <div className="space-y-1">
                          <p className="text-xs font-medium text-muted-foreground mb-2">Execution Trace ({steps.length} steps)</p>
                          {steps.map((step) => (
                            <div key={step.id} className="flex items-center gap-3 text-xs rounded-md bg-muted/30 px-3 py-2">
                              <span className="font-mono text-muted-foreground w-6">#{step.step_index}</span>
                              <span className="font-medium">{step.node_name}</span>
                              {step.transition && (
                                <span className="text-muted-foreground">&rarr; {step.transition}</span>
                              )}
                              <span className="ml-auto text-muted-foreground">
                                {step.tokens_used > 0 && `${step.tokens_used} tok`}
                                {step.duration_ms != null && ` \u00b7 ${step.duration_ms}ms`}
                              </span>
                              {step.error_message && (
                                <span className="text-destructive truncate max-w-[200px]">{step.error_message}</span>
                              )}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
