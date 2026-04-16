"use client"

import { useEffect, useState, useCallback } from "react"
import { Brain, Plus, Pencil, Trash2, Loader2, Check, X, ChevronUp } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle, Button, Input } from "@kcontrol/ui"
import {
  listAgentConfigs, createAgentConfig, updateAgentConfig, deleteAgentConfig,
  type AgentConfigResponse, type AgentConfigCreateRequest, type AgentProviderType,
} from "@/lib/api/ai"

const AGENT_TYPES = [
  "copilot", "signal_generator", "grc_assistant", "framework_agent",
  "risk_agent", "task_agent", "signal_agent", "connector_agent",
  "user_agent", "role_agent", "supervisor",
]

const PROVIDER_TYPES: { value: AgentProviderType; label: string }[] = [
  { value: "openai_compatible", label: "OpenAI Compatible (default)" },
  { value: "openai", label: "OpenAI" },
  { value: "anthropic", label: "Anthropic Claude" },
  { value: "azure_openai", label: "Azure OpenAI" },
]

const DEFAULTS: Partial<AgentConfigCreateRequest> = {
  provider_base_url: "https://llm.kreesalis.com/v1",
  provider_type: "openai_compatible",
  model_id: "gpt-5.3-chat",
  temperature: 0.3,
  max_tokens: 4096,
  is_active: true,
}

interface EditState {
  provider_base_url: string
  provider_type: AgentProviderType
  api_key: string
  model_id: string
  temperature: string
  max_tokens: string
  is_active: boolean
}

function AgentConfigRow({
  config,
  onUpdate,
  onDelete,
}: {
  config: AgentConfigResponse
  onUpdate: (id: string, data: Partial<AgentConfigCreateRequest>) => Promise<void>
  onDelete: (id: string) => Promise<void>
}) {
  const [editing, setEditing] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [saving, setSaving] = useState(false)
  const [edit, setEdit] = useState<EditState>({
    provider_base_url: config.provider_base_url ?? "",
    provider_type: config.provider_type ?? "openai_compatible",
    api_key: "",
    model_id: config.model_id ?? "",
    temperature: String(config.temperature ?? 0.3),
    max_tokens: String(config.max_tokens ?? 4096),
    is_active: config.is_active,
  })

  async function handleSave() {
    setSaving(true)
    try {
      await onUpdate(config.id, {
        provider_base_url: edit.provider_base_url || undefined,
        provider_type: edit.provider_type,
        api_key: edit.api_key || undefined,
        model_id: edit.model_id || undefined,
        temperature: parseFloat(edit.temperature) || undefined,
        max_tokens: parseInt(edit.max_tokens) || undefined,
        is_active: edit.is_active,
      })
      setEditing(false)
    } catch { /* ignore */ }
    finally { setSaving(false) }
  }

  async function handleDelete() {
    setDeleting(true)
    try { await onDelete(config.id) } catch { /* ignore */ }
    finally { setDeleting(false) }
  }

  return (
    <div className="rounded-xl border border-border bg-card overflow-hidden">
      <div className="flex items-center gap-3 px-4 py-3">
        <div className="w-8 h-8 rounded-lg bg-purple-500/10 flex items-center justify-center shrink-0">
          <Brain className="w-4 h-4 text-purple-400" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm font-semibold font-mono">{config.agent_type_code}</span>
            {config.org_id && (
              <span className="text-[11px] px-1.5 py-0.5 rounded bg-muted text-muted-foreground font-mono">
                org: {config.org_id.slice(0, 8)}…
              </span>
            )}
            <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold border ${config.is_active ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" : "bg-muted text-muted-foreground border-border"}`}>
              {config.is_active ? "Active" : "Inactive"}
            </span>
          </div>
          <p className="text-xs text-muted-foreground mt-0.5 truncate">
            {config.model_id} · {config.provider_type} · {config.provider_base_url}
          </p>
        </div>
        <div className="flex items-center gap-1 shrink-0">
          <button
            onClick={() => setEditing(e => !e)}
            className="p-1.5 rounded-lg hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
          >
            {editing ? <ChevronUp className="w-4 h-4" /> : <Pencil className="w-4 h-4" />}
          </button>
          <button
            onClick={handleDelete}
            disabled={deleting}
            className="p-1.5 rounded-lg hover:bg-red-500/10 text-muted-foreground hover:text-red-400 transition-colors disabled:opacity-50"
          >
            {deleting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {editing && (
        <div className="border-t border-border bg-muted/20 px-4 py-4 space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Provider Type</label>
              <select
                value={edit.provider_type}
                onChange={e => setEdit(p => ({ ...p, provider_type: e.target.value as AgentProviderType }))}
                className="flex h-8 w-full rounded-md border border-input bg-background px-3 py-1 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                {PROVIDER_TYPES.map(pt => (
                  <option key={pt.value} value={pt.value}>{pt.label}</option>
                ))}
              </select>
            </div>
            <div className="space-y-1">
              <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Provider URL</label>
              <Input value={edit.provider_base_url} onChange={e => setEdit(p => ({ ...p, provider_base_url: e.target.value }))} className="h-8 text-sm font-mono" />
            </div>
            <div className="space-y-1">
              <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">API Key (leave blank to keep)</label>
              <Input type="password" value={edit.api_key} onChange={e => setEdit(p => ({ ...p, api_key: e.target.value }))} placeholder="sk-…" className="h-8 text-sm font-mono" />
            </div>
            <div className="space-y-1">
              <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Model ID</label>
              <Input value={edit.model_id} onChange={e => setEdit(p => ({ ...p, model_id: e.target.value }))} className="h-8 text-sm font-mono" />
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div className="space-y-1">
                <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Temperature</label>
                <Input type="number" min="0" max="2" step="0.1" value={edit.temperature} onChange={e => setEdit(p => ({ ...p, temperature: e.target.value }))} className="h-8 text-sm" />
              </div>
              <div className="space-y-1">
                <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Max Tokens</label>
                <Input type="number" min="256" max="32000" step="256" value={edit.max_tokens} onChange={e => setEdit(p => ({ ...p, max_tokens: e.target.value }))} className="h-8 text-sm" />
              </div>
            </div>
          </div>
          <div className="flex items-center justify-between">
            <label className="flex items-center gap-2 cursor-pointer">
              <button
                type="button"
                onClick={() => setEdit(p => ({ ...p, is_active: !p.is_active }))}
                className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${edit.is_active ? "bg-emerald-500" : "bg-muted"}`}
              >
                <span className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white shadow transition-transform ${edit.is_active ? "translate-x-4" : "translate-x-1"}`} />
              </button>
              <span className="text-xs text-muted-foreground">Active</span>
            </label>
            <div className="flex gap-2">
              <Button size="sm" variant="ghost" onClick={() => setEditing(false)}>Cancel</Button>
              <Button size="sm" disabled={saving} onClick={handleSave} className="gap-1.5">
                {saving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Check className="w-3.5 h-3.5" />}
                Save
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default function AgentConfigsPage() {
  const [configs, setConfigs] = useState<AgentConfigResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)
  const [showCreate, setShowCreate] = useState(false)
  const [newConfig, setNewConfig] = useState<AgentConfigCreateRequest>({
    agent_type_code: "copilot",
    provider_base_url: DEFAULTS.provider_base_url!,
    provider_type: DEFAULTS.provider_type,
    api_key: "",
    model_id: DEFAULTS.model_id!,
    temperature: DEFAULTS.temperature,
    max_tokens: DEFAULTS.max_tokens,
    is_active: true,
  })

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const res = await listAgentConfigs()
      setConfigs(res.items)
    } catch { /* ignore */ }
    finally { setLoading(false) }
  }, [])

  useEffect(() => { load() }, [load])

  async function handleCreate() {
    setCreating(true)
    try {
      await createAgentConfig(newConfig)
      await load()
      setShowCreate(false)
      setNewConfig({ agent_type_code: "copilot", provider_base_url: DEFAULTS.provider_base_url!, provider_type: DEFAULTS.provider_type, api_key: "", model_id: DEFAULTS.model_id!, temperature: DEFAULTS.temperature, max_tokens: DEFAULTS.max_tokens, is_active: true })
    } catch { /* ignore */ }
    finally { setCreating(false) }
  }

  async function handleUpdate(id: string, data: Partial<AgentConfigCreateRequest>) {
    await updateAgentConfig(id, data)
    await load()
  }

  async function handleDelete(id: string) {
    await deleteAgentConfig(id)
    setConfigs(prev => prev.filter(c => c.id !== id))
  }

  return (
    <div className="max-w-4xl space-y-6">
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-purple-500/15 flex items-center justify-center">
            <Brain className="w-5 h-5 text-purple-400" />
          </div>
          <div>
            <h1 className="text-xl font-bold">Agent Configs</h1>
            <p className="text-sm text-muted-foreground">LLM provider, model, and parameter settings per agent type.</p>
          </div>
        </div>
        <Button onClick={() => setShowCreate(v => !v)} className="gap-2">
          {showCreate ? <X className="w-4 h-4" /> : <Plus className="w-4 h-4" />}
          {showCreate ? "Cancel" : "New Config"}
        </Button>
      </div>

      {showCreate && (
        <Card className="rounded-xl border-purple-500/20">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-semibold">New Agent Config</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Agent Type</label>
                <select
                  value={newConfig.agent_type_code}
                  onChange={e => setNewConfig(p => ({ ...p, agent_type_code: e.target.value }))}
                  className="w-full h-9 rounded-lg border border-input bg-background text-sm px-3 focus:outline-none focus:ring-2 focus:ring-ring"
                >
                  {AGENT_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
                </select>
              </div>
              <div className="space-y-1">
                <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Model ID</label>
                <Input value={newConfig.model_id} onChange={e => setNewConfig(p => ({ ...p, model_id: e.target.value }))} className="h-9 text-sm font-mono" />
              </div>
              <div className="space-y-1">
                <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Provider Type</label>
                <select
                  value={newConfig.provider_type ?? "openai_compatible"}
                  onChange={e => setNewConfig(p => ({ ...p, provider_type: e.target.value as AgentProviderType }))}
                  className="w-full h-9 rounded-lg border border-input bg-background text-sm px-3 focus:outline-none focus:ring-2 focus:ring-ring"
                >
                  {PROVIDER_TYPES.map(pt => <option key={pt.value} value={pt.value}>{pt.label}</option>)}
                </select>
              </div>
              <div className="space-y-1 col-span-2">
                <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Provider URL</label>
                <Input value={newConfig.provider_base_url} onChange={e => setNewConfig(p => ({ ...p, provider_base_url: e.target.value }))} className="h-9 text-sm font-mono" />
              </div>
              <div className="space-y-1 col-span-2">
                <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">API Key</label>
                <Input type="password" value={newConfig.api_key} onChange={e => setNewConfig(p => ({ ...p, api_key: e.target.value }))} placeholder="sk-…" className="h-9 text-sm font-mono" />
              </div>
              <div className="space-y-1">
                <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Temperature</label>
                <Input type="number" min="0" max="2" step="0.1" value={newConfig.temperature} onChange={e => setNewConfig(p => ({ ...p, temperature: parseFloat(e.target.value) }))} className="h-9 text-sm" />
              </div>
              <div className="space-y-1">
                <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Max Tokens</label>
                <Input type="number" min="256" max="32000" step="256" value={newConfig.max_tokens} onChange={e => setNewConfig(p => ({ ...p, max_tokens: parseInt(e.target.value) }))} className="h-9 text-sm" />
              </div>
            </div>
            <div className="flex justify-end gap-2 pt-1">
              <Button size="sm" variant="ghost" onClick={() => setShowCreate(false)}>Cancel</Button>
              <Button size="sm" disabled={creating || !newConfig.api_key} onClick={handleCreate} className="gap-1.5">
                {creating ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Plus className="w-3.5 h-3.5" />}
                Create
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map(i => <div key={i} className="h-16 rounded-xl bg-muted animate-pulse" />)}
        </div>
      ) : configs.length === 0 ? (
        <div className="flex flex-col items-center py-16 gap-3 text-center">
          <div className="w-12 h-12 rounded-xl bg-muted flex items-center justify-center">
            <Brain className="w-6 h-6 text-muted-foreground/40" />
          </div>
          <p className="text-sm text-muted-foreground">No agent configs yet. Create one above.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {configs.map(c => (
            <AgentConfigRow key={c.id} config={c} onUpdate={handleUpdate} onDelete={handleDelete} />
          ))}
        </div>
      )}
    </div>
  )
}
