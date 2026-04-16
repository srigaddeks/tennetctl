"use client"

import { useEffect, useState } from "react"
import { Plus, Search, Trash2, Loader2, Wrench } from "lucide-react"
import { useAgentSandbox } from "@/lib/context/AgentSandboxContext"
import { listTools, createTool, deleteTool, type ToolResponse } from "@/lib/api/agentSandbox"

const TYPE_LABELS: Record<string, string> = {
  mcp_server: "MCP Server",
  api_endpoint: "API Endpoint",
  python_function: "Python Function",
  sandbox_signal: "Sandbox Signal",
  db_query: "Database Query",
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-US", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })
}

export default function ToolsPage() {
  const { selectedOrgId, ready } = useAgentSandbox()

  const [tools, setTools] = useState<ToolResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState("")
  const [createOpen, setCreateOpen] = useState(false)
  const [newCode, setNewCode] = useState("")
  const [newName, setNewName] = useState("")
  const [newType, setNewType] = useState("python_function")
  const [creating, setCreating] = useState(false)

  const loadTools = () => {
    if (!selectedOrgId) return
    setLoading(true)
    listTools({ org_id: selectedOrgId })
      .then((res) => setTools(res.items))
      .catch(console.error)
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    if (!ready || !selectedOrgId) return
    loadTools()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ready, selectedOrgId])

  const filtered = tools.filter(
    (t) =>
      (t.name?.toLowerCase().includes(searchQuery.toLowerCase()) ?? false) ||
      t.tool_code.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const handleCreate = async () => {
    if (!newCode || !newName || !selectedOrgId) return
    setCreating(true)
    try {
      await createTool(selectedOrgId, {
        tool_code: newCode,
        tool_type_code: newType,
        properties: { name: newName },
      })
      setCreateOpen(false)
      setNewCode("")
      setNewName("")
      loadTools()
    } catch (e) {
      alert((e as Error).message)
    } finally {
      setCreating(false)
    }
  }

  const handleDelete = async (toolId: string) => {
    if (!selectedOrgId || !confirm("Delete this tool?")) return
    try {
      await deleteTool(selectedOrgId, toolId)
      loadTools()
    } catch (e) {
      alert((e as Error).message)
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold">Agent Tools</h2>
          <p className="text-sm text-muted-foreground">Register tools that agents can call via ctx.tool()</p>
        </div>
        <button
          onClick={() => setCreateOpen(true)}
          className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
        >
          <Plus className="h-4 w-4" />
          Register Tool
        </button>
      </div>

      <div className="flex items-center gap-2 rounded-md border px-3 py-2">
        <Search className="h-4 w-4 text-muted-foreground" />
        <input
          placeholder="Search tools..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="flex-1 bg-transparent text-sm outline-none placeholder:text-muted-foreground"
        />
      </div>

      <div className="rounded-lg border">
        {loading ? (
          <div className="p-8 text-center text-sm text-muted-foreground">Loading...</div>
        ) : filtered.length === 0 ? (
          <div className="p-8 text-center text-sm text-muted-foreground">
            {tools.length === 0 ? "No tools registered yet." : "No tools match your search."}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="border-b bg-muted/50">
                <tr>
                  <th className="px-4 py-2.5 text-left text-xs font-semibold text-muted-foreground">Tool</th>
                  <th className="px-4 py-2.5 text-left text-xs font-semibold text-muted-foreground">Code</th>
                  <th className="px-4 py-2.5 text-left text-xs font-semibold text-muted-foreground">Type</th>
                  <th className="px-4 py-2.5 text-left text-xs font-semibold text-muted-foreground">Flags</th>
                  <th className="px-4 py-2.5 text-left text-xs font-semibold text-muted-foreground">Created</th>
                  <th className="px-4 py-2.5 text-right text-xs font-semibold text-muted-foreground">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((tool) => (
                  <tr key={tool.id} className="border-b hover:bg-muted/30">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <Wrench className="h-4 w-4 text-muted-foreground" />
                        <span className="font-medium text-sm">{tool.name || tool.tool_code}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm font-mono text-muted-foreground">{tool.tool_code}</td>
                    <td className="px-4 py-3 text-sm text-muted-foreground">{TYPE_LABELS[tool.tool_type_code] ?? tool.tool_type_code}</td>
                    <td className="px-4 py-3">
                      <div className="flex gap-1">
                        {tool.requires_approval && (
                          <span className="rounded-full bg-yellow-100 px-2 py-0.5 text-[10px] font-medium text-yellow-700">approval</span>
                        )}
                        {tool.is_destructive && (
                          <span className="rounded-full bg-red-100 px-2 py-0.5 text-[10px] font-medium text-red-700">destructive</span>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm text-muted-foreground">{formatDate(tool.created_at)}</td>
                    <td className="px-4 py-3 text-right">
                      <button
                        className="inline-flex items-center justify-center rounded-md p-1.5 hover:bg-destructive/10 text-destructive"
                        onClick={() => handleDelete(tool.id)}
                        title="Delete tool"
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
            <h3 className="text-lg font-semibold mb-4">Register Tool</h3>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium">Tool Code</label>
                <input
                  value={newCode}
                  onChange={(e) => setNewCode(e.target.value.toLowerCase().replace(/[^a-z0-9_]/g, ""))}
                  placeholder="fetch_github_repos"
                  className="mt-1 w-full rounded-md border px-3 py-2 text-sm bg-transparent"
                />
              </div>
              <div>
                <label className="text-sm font-medium">Name</label>
                <input
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  placeholder="Fetch GitHub Repos"
                  className="mt-1 w-full rounded-md border px-3 py-2 text-sm bg-transparent"
                />
              </div>
              <div>
                <label className="text-sm font-medium">Type</label>
                <select
                  value={newType}
                  onChange={(e) => setNewType(e.target.value)}
                  className="mt-1 w-full rounded-md border px-3 py-2 text-sm bg-transparent"
                >
                  {Object.entries(TYPE_LABELS).map(([k, v]) => (
                    <option key={k} value={k}>{v}</option>
                  ))}
                </select>
              </div>
            </div>
            <div className="flex justify-end gap-2 mt-6">
              <button onClick={() => setCreateOpen(false)} className="rounded-md border px-4 py-2 text-sm hover:bg-muted">Cancel</button>
              <button
                onClick={handleCreate}
                disabled={creating || !newCode || !newName}
                className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
              >
                {creating ? <Loader2 className="h-4 w-4 animate-spin" /> : "Register"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
