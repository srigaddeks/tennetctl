"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { Plus, Search, Play, Trash2, Loader2, Cpu } from "lucide-react"
import { useAgentSandbox } from "@/lib/context/AgentSandboxContext"
import {
  listAgents,
  createAgent,
  deleteAgent,
  executeAgent,
  type AgentResponse,
} from "@/lib/api/agentSandbox"

const STATUS_STYLES: Record<string, string> = {
  draft: "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300",
  testing: "bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300",
  validated: "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300",
  published: "bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300",
  deprecated: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300",
  archived: "bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300",
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-US", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })
}

export default function AgentsPage() {
  const router = useRouter()
  const { selectedOrgId, ready } = useAgentSandbox()

  const [agents, setAgents] = useState<AgentResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState("")
  const [createOpen, setCreateOpen] = useState(false)
  const [newCode, setNewCode] = useState("")
  const [newName, setNewName] = useState("")
  const [creating, setCreating] = useState(false)
  const [executing, setExecuting] = useState<string | null>(null)

  const loadAgents = () => {
    if (!selectedOrgId) return
    setLoading(true)
    listAgents({ org_id: selectedOrgId })
      .then((res) => setAgents(res.items))
      .catch(console.error)
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    if (!ready || !selectedOrgId) return
    loadAgents()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ready, selectedOrgId])

  const filtered = agents.filter(
    (a) =>
      (a.name?.toLowerCase().includes(searchQuery.toLowerCase()) ?? false) ||
      a.agent_code.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const handleCreate = async () => {
    if (!newCode || !newName || !selectedOrgId) return
    setCreating(true)
    try {
      const agent = await createAgent(selectedOrgId, {
        agent_code: newCode,
        properties: {
          name: newName,
          graph_source: `def build_graph(ctx):\n    return {\n        "nodes": {\n            "start": {\n                "handler": start_handler,\n                "transitions": {"done": "__end__"}\n            },\n        },\n        "entry_point": "start",\n    }\n\ndef start_handler(ctx):\n    result = ctx.llm(system="You are helpful.", user="Hello")\n    ctx.emit("response", {"content": result})\n    return "done"\n`,
        },
      })
      setCreateOpen(false)
      setNewCode("")
      setNewName("")
      router.push(`/agent-sandbox/agents/${agent.id}`)
    } catch (e) {
      alert((e as Error).message)
    } finally {
      setCreating(false)
    }
  }

  const handleExecute = async (agentId: string) => {
    if (!selectedOrgId) return
    setExecuting(agentId)
    try {
      await executeAgent(selectedOrgId, agentId, {})
      loadAgents()
    } catch (e) {
      alert((e as Error).message)
    } finally {
      setExecuting(null)
    }
  }

  const handleDelete = async (agentId: string) => {
    if (!selectedOrgId || !confirm("Delete this agent?")) return
    try {
      await deleteAgent(selectedOrgId, agentId)
      loadAgents()
    } catch (e) {
      alert((e as Error).message)
    }
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold">Agents</h2>
          <p className="text-sm text-muted-foreground">Build and manage autonomous AI agents</p>
        </div>
        <button
          onClick={() => setCreateOpen(true)}
          className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
        >
          <Plus className="h-4 w-4" />
          New Agent
        </button>
      </div>

      {/* Search */}
      <div className="flex items-center gap-2 rounded-md border px-3 py-2">
        <Search className="h-4 w-4 text-muted-foreground" />
        <input
          placeholder="Search agents..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="flex-1 bg-transparent text-sm outline-none placeholder:text-muted-foreground"
        />
      </div>

      {/* Table */}
      <div className="rounded-lg border">
        {loading ? (
          <div className="p-8 text-center text-sm text-muted-foreground">Loading...</div>
        ) : filtered.length === 0 ? (
          <div className="p-8 text-center text-sm text-muted-foreground">
            {agents.length === 0 ? "No agents yet. Create your first agent to get started." : "No agents match your search."}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="border-b bg-muted/50">
                <tr>
                  <th className="px-4 py-2.5 text-left text-xs font-semibold text-muted-foreground">Agent</th>
                  <th className="px-4 py-2.5 text-left text-xs font-semibold text-muted-foreground">Code</th>
                  <th className="px-4 py-2.5 text-left text-xs font-semibold text-muted-foreground">Status</th>
                  <th className="px-4 py-2.5 text-left text-xs font-semibold text-muted-foreground">Version</th>
                  <th className="px-4 py-2.5 text-left text-xs font-semibold text-muted-foreground">Graph</th>
                  <th className="px-4 py-2.5 text-left text-xs font-semibold text-muted-foreground">Created</th>
                  <th className="px-4 py-2.5 text-right text-xs font-semibold text-muted-foreground">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((agent) => (
                  <tr
                    key={agent.id}
                    className="border-b hover:bg-muted/30 cursor-pointer"
                    onClick={() => router.push(`/agent-sandbox/agents/${agent.id}`)}
                  >
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <Cpu className="h-4 w-4 text-muted-foreground" />
                        <span className="font-medium text-sm">{agent.name || agent.agent_code}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm font-mono text-muted-foreground">{agent.agent_code}</td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_STYLES[agent.agent_status_code] ?? ""}`}>
                        {agent.agent_status_code}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-muted-foreground">v{agent.version_number}</td>
                    <td className="px-4 py-3 text-sm text-muted-foreground">{agent.graph_type}</td>
                    <td className="px-4 py-3 text-sm text-muted-foreground">{formatDate(agent.created_at)}</td>
                    <td className="px-4 py-3 text-right" onClick={(e) => e.stopPropagation()}>
                      <button
                        className="inline-flex items-center justify-center rounded-md p-1.5 hover:bg-muted"
                        onClick={() => handleExecute(agent.id)}
                        title="Execute agent"
                      >
                        {executing === agent.id ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
                      </button>
                      <button
                        className="inline-flex items-center justify-center rounded-md p-1.5 hover:bg-destructive/10 text-destructive"
                        onClick={() => handleDelete(agent.id)}
                        title="Delete agent"
                      >
                        <Trash2 className="h-4 w-4" />
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
            <h3 className="text-lg font-semibold mb-4">New Agent</h3>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium">Agent Code</label>
                <input
                  value={newCode}
                  onChange={(e) => setNewCode(e.target.value.toLowerCase().replace(/[^a-z0-9_]/g, ""))}
                  placeholder="my_security_agent"
                  className="mt-1 w-full rounded-md border px-3 py-2 text-sm bg-transparent"
                />
              </div>
              <div>
                <label className="text-sm font-medium">Name</label>
                <input
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  placeholder="My Security Agent"
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
                {creating ? <Loader2 className="h-4 w-4 animate-spin" /> : "Create Agent"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
