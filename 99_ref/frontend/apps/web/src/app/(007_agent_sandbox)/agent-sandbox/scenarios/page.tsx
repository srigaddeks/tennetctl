"use client"

import { useEffect, useState } from "react"
import { Plus, Search, Trash2, Play, Loader2, ClipboardCheck, CheckCircle2, XCircle } from "lucide-react"
import { useAgentSandbox } from "@/lib/context/AgentSandboxContext"
import {
  listScenarios,
  createScenario,
  runScenario,
  type ScenarioResponse,
  type TestRunResult,
} from "@/lib/api/agentSandbox"

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-US", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })
}

export default function ScenariosPage() {
  const { selectedOrgId, ready } = useAgentSandbox()

  const [scenarios, setScenarios] = useState<ScenarioResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState("")
  const [createOpen, setCreateOpen] = useState(false)
  const [newCode, setNewCode] = useState("")
  const [newName, setNewName] = useState("")
  const [creating, setCreating] = useState(false)
  const [runningScenario, setRunningScenario] = useState<string | null>(null)
  const [lastResult, setLastResult] = useState<TestRunResult | null>(null)

  const loadScenarios = () => {
    if (!selectedOrgId) return
    setLoading(true)
    listScenarios({ org_id: selectedOrgId })
      .then((res) => setScenarios(res.items))
      .catch(console.error)
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    if (!ready || !selectedOrgId) return
    loadScenarios()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ready, selectedOrgId])

  const filtered = scenarios.filter(
    (s) =>
      (s.name?.toLowerCase().includes(searchQuery.toLowerCase()) ?? false) ||
      s.scenario_code.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const handleCreate = async () => {
    if (!newCode || !newName || !selectedOrgId) return
    setCreating(true)
    try {
      await createScenario(selectedOrgId, {
        scenario_code: newCode,
        properties: { name: newName },
      })
      setCreateOpen(false)
      setNewCode("")
      setNewName("")
      loadScenarios()
    } catch (e) {
      alert((e as Error).message)
    } finally {
      setCreating(false)
    }
  }

  const handleRun = async (scenarioId: string) => {
    if (!selectedOrgId) return
    setRunningScenario(scenarioId)
    setLastResult(null)
    try {
      const result = await runScenario(selectedOrgId, scenarioId)
      setLastResult(result)
    } catch (e) {
      alert((e as Error).message)
    } finally {
      setRunningScenario(null)
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold">Test Scenarios</h2>
          <p className="text-sm text-muted-foreground">Define and run test scenarios against agents</p>
        </div>
        <button
          onClick={() => setCreateOpen(true)}
          className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
        >
          <Plus className="h-4 w-4" />
          New Scenario
        </button>
      </div>

      <div className="flex items-center gap-2 rounded-md border px-3 py-2">
        <Search className="h-4 w-4 text-muted-foreground" />
        <input
          placeholder="Search scenarios..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="flex-1 bg-transparent text-sm outline-none placeholder:text-muted-foreground"
        />
      </div>

      {/* Last run result */}
      {lastResult && (
        <div className="rounded-lg border p-4 bg-card">
          <div className="flex items-center gap-2 mb-2">
            {lastResult.pass_rate === 1 ? (
              <CheckCircle2 className="h-4 w-4 text-green-600" />
            ) : (
              <XCircle className="h-4 w-4 text-red-600" />
            )}
            <span className="text-sm font-medium">
              Test Run: {lastResult.passed}/{lastResult.total_cases} passed ({(lastResult.pass_rate * 100).toFixed(0)}%)
            </span>
            <span className="text-xs text-muted-foreground ml-auto">
              {lastResult.total_tokens.toLocaleString()} tokens &middot; ${lastResult.total_cost_usd.toFixed(4)} &middot; {(lastResult.total_duration_ms / 1000).toFixed(1)}s
            </span>
          </div>
          <div className="space-y-1">
            {lastResult.results.map((r) => (
              <div key={r.case_id} className="flex items-center gap-2 text-xs">
                {r.passed ? <CheckCircle2 className="h-3 w-3 text-green-600" /> : <XCircle className="h-3 w-3 text-red-600" />}
                <span>Case #{r.case_index}: {r.reason}</span>
                <span className="ml-auto text-muted-foreground">{r.execution_time_ms}ms</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="rounded-lg border">
        {loading ? (
          <div className="p-8 text-center text-sm text-muted-foreground">Loading...</div>
        ) : filtered.length === 0 ? (
          <div className="p-8 text-center text-sm text-muted-foreground">
            {scenarios.length === 0 ? "No test scenarios yet." : "No scenarios match your search."}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="border-b bg-muted/50">
                <tr>
                  <th className="px-4 py-2.5 text-left text-xs font-semibold text-muted-foreground">Scenario</th>
                  <th className="px-4 py-2.5 text-left text-xs font-semibold text-muted-foreground">Code</th>
                  <th className="px-4 py-2.5 text-left text-xs font-semibold text-muted-foreground">Type</th>
                  <th className="px-4 py-2.5 text-left text-xs font-semibold text-muted-foreground">Created</th>
                  <th className="px-4 py-2.5 text-right text-xs font-semibold text-muted-foreground">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((scenario) => (
                  <tr key={scenario.id} className="border-b hover:bg-muted/30">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <ClipboardCheck className="h-4 w-4 text-muted-foreground" />
                        <span className="font-medium text-sm">{scenario.name || scenario.scenario_code}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm font-mono text-muted-foreground">{scenario.scenario_code}</td>
                    <td className="px-4 py-3 text-sm text-muted-foreground">{scenario.scenario_type_code}</td>
                    <td className="px-4 py-3 text-sm text-muted-foreground">{formatDate(scenario.created_at)}</td>
                    <td className="px-4 py-3 text-right">
                      <button
                        className="inline-flex items-center justify-center rounded-md p-1.5 hover:bg-muted"
                        onClick={() => handleRun(scenario.id)}
                        title="Run scenario"
                      >
                        {runningScenario === scenario.id ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Create dialog */}
      {createOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="w-full max-w-md rounded-xl border bg-background p-6 shadow-lg">
            <h3 className="text-lg font-semibold mb-4">New Test Scenario</h3>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium">Scenario Code</label>
                <input
                  value={newCode}
                  onChange={(e) => setNewCode(e.target.value.toLowerCase().replace(/[^a-z0-9_]/g, ""))}
                  placeholder="basic_security_scan"
                  className="mt-1 w-full rounded-md border px-3 py-2 text-sm bg-transparent"
                />
              </div>
              <div>
                <label className="text-sm font-medium">Name</label>
                <input
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  placeholder="Basic Security Scan Test"
                  className="mt-1 w-full rounded-md border px-3 py-2 text-sm bg-transparent"
                />
              </div>
            </div>
            <div className="flex justify-end gap-2 mt-6">
              <button onClick={() => setCreateOpen(false)} className="rounded-md border px-4 py-2 text-sm hover:bg-muted">Cancel</button>
              <button
                onClick={handleCreate}
                disabled={creating || !newCode || !newName}
                className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
              >
                {creating ? <Loader2 className="h-4 w-4 animate-spin" /> : "Create"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
