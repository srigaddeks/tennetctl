"use client"

import { useEffect, useState, useCallback } from "react"
import { FileCode2, Plus, Pencil, Trash2, Loader2, Check, X, Eye, ChevronDown, ChevronUp } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle, Button, Input } from "@kcontrol/ui"
import {
  listPromptTemplates, createPromptTemplate, updatePromptTemplate, deletePromptTemplate, previewPromptTemplate,
  type PromptTemplateResponse, type PromptTemplateCreateRequest,
} from "@/lib/api/ai"

const AGENT_TYPES = [
  "copilot", "signal_generator", "grc_assistant", "framework_agent",
  "risk_agent", "task_agent", "signal_agent", "connector_agent", "supervisor",
]

const PROMPT_TYPES = ["system", "user", "assistant"] as const

function TemplateRow({
  template,
  onUpdate,
  onDelete,
}: {
  template: PromptTemplateResponse
  onUpdate: (id: string, data: Partial<PromptTemplateCreateRequest>) => Promise<void>
  onDelete: (id: string) => Promise<void>
}) {
  const [editing, setEditing] = useState(false)
  const [expanded, setExpanded] = useState(false)
  const [saving, setSaving] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [previewing, setPreviewing] = useState(false)
  const [previewResult, setPreviewResult] = useState<string | null>(null)
  const [edit, setEdit] = useState({
    name: template.name ?? "",
    description: template.description ?? "",
    template_content: template.template_content ?? "",
    agent_type_code: template.agent_type_code ?? "",
    prompt_type: template.prompt_type ?? "system",
    version: template.version ?? 1,
    is_active: template.is_active ?? true,
  })

  async function handleSave() {
    setSaving(true)
    try { await onUpdate(template.id, edit); setEditing(false) } catch { /* ignore */ }
    finally { setSaving(false) }
  }

  async function handleDelete() {
    setDeleting(true)
    try { await onDelete(template.id) } catch { /* ignore */ }
    finally { setDeleting(false) }
  }

  async function handlePreview() {
    setPreviewing(true)
    setPreviewResult(null)
    try {
      const res = await previewPromptTemplate(template.id, {
        org_id: "preview-org",
        workspace_id: "preview-ws",
        user_id: "preview-user",
      })
      setPreviewResult(res.rendered ?? res.preview ?? JSON.stringify(res))
    } catch (e) {
      setPreviewResult(`Error: ${e instanceof Error ? e.message : "Unknown"}`)
    } finally { setPreviewing(false) }
  }

  return (
    <div className="rounded-xl border border-border bg-card overflow-hidden">
      <div className="flex items-start gap-3 px-4 py-3">
        <div className="w-8 h-8 rounded-lg bg-blue-500/10 flex items-center justify-center shrink-0 mt-0.5">
          <FileCode2 className="w-4 h-4 text-blue-400" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm font-semibold">{template.name ?? `Template ${template.id.slice(0, 8)}`}</span>
            <span className="text-[11px] px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-400 font-mono border border-blue-500/20">
              {template.agent_type_code}
            </span>
            <span className="text-[11px] px-1.5 py-0.5 rounded bg-muted text-muted-foreground border border-border">
              {template.prompt_type}
            </span>
            {!template.is_active && (
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-muted text-muted-foreground border border-border">inactive</span>
            )}
          </div>
          {template.description && (
            <p className="text-xs text-muted-foreground mt-0.5 truncate">{template.description}</p>
          )}
        </div>
        <div className="flex items-center gap-1 shrink-0">
          <button onClick={handlePreview} disabled={previewing}
            className="p-1.5 rounded-lg hover:bg-muted text-muted-foreground hover:text-foreground transition-colors disabled:opacity-50"
            title="Preview rendered output">
            {previewing ? <Loader2 className="w-4 h-4 animate-spin" /> : <Eye className="w-4 h-4" />}
          </button>
          <button onClick={() => { setExpanded(e => !e); setEditing(false) }}
            className="p-1.5 rounded-lg hover:bg-muted text-muted-foreground hover:text-foreground transition-colors">
            {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
          <button onClick={() => { setEditing(e => !e); setExpanded(true) }}
            className="p-1.5 rounded-lg hover:bg-muted text-muted-foreground hover:text-foreground transition-colors">
            <Pencil className="w-4 h-4" />
          </button>
          <button onClick={handleDelete} disabled={deleting}
            className="p-1.5 rounded-lg hover:bg-red-500/10 text-muted-foreground hover:text-red-400 transition-colors disabled:opacity-50">
            {deleting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {previewResult && (
        <div className="border-t border-amber-500/20 bg-amber-500/5 px-4 py-3">
          <p className="text-[10px] font-bold text-amber-400 uppercase tracking-wider mb-1.5">Preview</p>
          <pre className="text-xs text-foreground font-mono whitespace-pre-wrap max-h-40 overflow-auto">{previewResult}</pre>
        </div>
      )}

      {expanded && (
        <div className="border-t border-border bg-muted/10 px-4 py-4 space-y-3">
          {editing ? (
            <>
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Name</label>
                  <Input value={edit.name} onChange={e => setEdit(p => ({ ...p, name: e.target.value }))} className="h-8 text-sm" />
                </div>
                <div className="space-y-1">
                  <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Agent Type</label>
                  <select value={edit.agent_type_code} onChange={e => setEdit(p => ({ ...p, agent_type_code: e.target.value }))}
                    className="w-full h-8 rounded-lg border border-input bg-background text-sm px-3 focus:outline-none focus:ring-2 focus:ring-ring">
                    {AGENT_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
                  </select>
                </div>
                <div className="space-y-1">
                  <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Prompt Type</label>
                  <select value={edit.prompt_type} onChange={e => setEdit(p => ({ ...p, prompt_type: e.target.value as typeof edit.prompt_type }))}
                    className="w-full h-8 rounded-lg border border-input bg-background text-sm px-3 focus:outline-none focus:ring-2 focus:ring-ring">
                    {PROMPT_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
                  </select>
                </div>
                <div className="space-y-1">
                  <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Description</label>
                  <Input value={edit.description} onChange={e => setEdit(p => ({ ...p, description: e.target.value }))} className="h-8 text-sm" />
                </div>
              </div>
              <div className="space-y-1">
                <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Template Content</label>
                <textarea
                  value={edit.template_content}
                  onChange={e => setEdit(p => ({ ...p, template_content: e.target.value }))}
                  rows={8}
                  className="w-full rounded-xl border border-input bg-background text-sm px-3 py-2 font-mono resize-y focus:outline-none focus:ring-2 focus:ring-ring"
                />
              </div>
              <div className="flex items-center justify-between">
                <label className="flex items-center gap-2 cursor-pointer">
                  <button type="button" onClick={() => setEdit(p => ({ ...p, is_active: !p.is_active }))}
                    className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${edit.is_active ? "bg-emerald-500" : "bg-muted"}`}>
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
            </>
          ) : (
            <pre className="text-xs font-mono text-muted-foreground whitespace-pre-wrap max-h-48 overflow-auto bg-background rounded-lg border border-border p-3">
              {template.template_content}
            </pre>
          )}
        </div>
      )}
    </div>
  )
}

export default function PromptsPage() {
  const [templates, setTemplates] = useState<PromptTemplateResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [creating, setCreating] = useState(false)
  const [newT, setNewT] = useState<PromptTemplateCreateRequest>({
    name: "",
    agent_type_code: "copilot",
    prompt_type: "system",
    template_content: "",
    description: "",
    version: 1,
    is_active: true,
  })

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const res = await listPromptTemplates()
      setTemplates(res.items)
    } catch { /* ignore */ }
    finally { setLoading(false) }
  }, [])

  useEffect(() => { load() }, [load])

  async function handleCreate() {
    if (!newT.name || !newT.template_content) return
    setCreating(true)
    try {
      await createPromptTemplate(newT)
      await load()
      setShowCreate(false)
      setNewT({ name: "", agent_type_code: "copilot", prompt_type: "system", template_content: "", description: "", version: 1, is_active: true })
    } catch { /* ignore */ }
    finally { setCreating(false) }
  }

  async function handleUpdate(id: string, data: Partial<PromptTemplateCreateRequest>) {
    await updatePromptTemplate(id, data)
    await load()
  }

  async function handleDelete(id: string) {
    await deletePromptTemplate(id)
    setTemplates(prev => prev.filter(t => t.id !== id))
  }

  return (
    <div className="max-w-4xl space-y-6">
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-blue-500/15 flex items-center justify-center">
            <FileCode2 className="w-5 h-5 text-blue-400" />
          </div>
          <div>
            <h1 className="text-xl font-bold">Prompt Templates</h1>
            <p className="text-sm text-muted-foreground">System prompts for each AI agent. Use {"{{var}}"} for variable substitution.</p>
          </div>
        </div>
        <Button onClick={() => setShowCreate(v => !v)} className="gap-2">
          {showCreate ? <X className="w-4 h-4" /> : <Plus className="w-4 h-4" />}
          {showCreate ? "Cancel" : "New Template"}
        </Button>
      </div>

      {showCreate && (
        <Card className="rounded-xl border-blue-500/20">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-semibold">New Prompt Template</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Name</label>
                <Input value={newT.name} onChange={e => setNewT(p => ({ ...p, name: e.target.value }))} placeholder="e.g. copilot-system-v1" className="h-9 text-sm" />
              </div>
              <div className="space-y-1">
                <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Agent Type</label>
                <select value={newT.agent_type_code} onChange={e => setNewT(p => ({ ...p, agent_type_code: e.target.value }))}
                  className="w-full h-9 rounded-lg border border-input bg-background text-sm px-3 focus:outline-none focus:ring-2 focus:ring-ring">
                  {AGENT_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
                </select>
              </div>
              <div className="space-y-1">
                <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Prompt Type</label>
                <select value={newT.prompt_type} onChange={e => setNewT(p => ({ ...p, prompt_type: e.target.value as "system" | "user" | "assistant" }))}
                  className="w-full h-9 rounded-lg border border-input bg-background text-sm px-3 focus:outline-none focus:ring-2 focus:ring-ring">
                  {PROMPT_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
                </select>
              </div>
              <div className="space-y-1">
                <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Description</label>
                <Input value={newT.description} onChange={e => setNewT(p => ({ ...p, description: e.target.value }))} className="h-9 text-sm" />
              </div>
              <div className="space-y-1 col-span-2">
                <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Template Content</label>
                <textarea
                  value={newT.template_content}
                  onChange={e => setNewT(p => ({ ...p, template_content: e.target.value }))}
                  rows={6}
                  placeholder="You are a GRC assistant for {{org_name}}. Today is {{date}}."
                  className="w-full rounded-xl border border-input bg-background text-sm px-3 py-2 font-mono resize-y focus:outline-none focus:ring-2 focus:ring-ring"
                />
              </div>
            </div>
            <div className="flex justify-end gap-2">
              <Button size="sm" variant="ghost" onClick={() => setShowCreate(false)}>Cancel</Button>
              <Button size="sm" disabled={creating || !newT.name || !newT.template_content} onClick={handleCreate} className="gap-1.5">
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
      ) : templates.length === 0 ? (
        <div className="flex flex-col items-center py-16 gap-3 text-center">
          <div className="w-12 h-12 rounded-xl bg-muted flex items-center justify-center">
            <FileCode2 className="w-6 h-6 text-muted-foreground/40" />
          </div>
          <p className="text-sm text-muted-foreground">No prompt templates yet. Create one above.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {templates.map(t => (
            <TemplateRow key={t.id} template={t} onUpdate={handleUpdate} onDelete={handleDelete} />
          ))}
        </div>
      )}
    </div>
  )
}
