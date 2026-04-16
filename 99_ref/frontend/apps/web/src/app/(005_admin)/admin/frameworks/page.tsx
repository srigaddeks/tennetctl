"use client"

import { useEffect, useState, useCallback, useMemo } from "react"
import {
  Button,
  Input,
  Label,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogFooter,
  DialogTitle,
  DialogDescription,
} from "@kcontrol/ui"
import {
  Library,
  Plus,
  Search,
  AlertTriangle,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  Shield,
  FileText,
  X,
  Download,
  Pencil,
  Trash2,
  CheckSquare,
  Square,
  ChevronLeft,
  ChevronRight,
  Layers,
  ClipboardList,
  FlaskConical,
} from "lucide-react"
import {
  listFrameworks,
  createFramework,
  updateFramework,
  deleteFramework,
  listFrameworkTypes,
  listFrameworkCategories,
  listVersions,
  createVersion,
  publishVersion,
  listFrameworkSettings,
  setFrameworkSetting,
  deleteFrameworkSetting,
  listControls,
  listTasks,
  createTask,
} from "@/lib/api/grc"
import type {
  FrameworkResponse,
  CreateFrameworkRequest,
  UpdateFrameworkRequest,
  VersionResponse,
  CreateVersionRequest,
  FrameworkSettingResponse,
  ControlResponse,
  TaskResponse,
  CreateTaskRequest,
} from "@/lib/types/grc"

// -- Constants ----------------------------------------------------------------

const PAGE_SIZE = 50

type SortField = "name" | "type_name" | "category_name" | "created_at"
type SortDir = "asc" | "desc"

interface FrameworkTypeOption { code: string; name: string }
interface FrameworkCategoryOption { code: string; name: string }

// -- Helpers ------------------------------------------------------------------

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })
}

function SortIcon({ field, sortBy, sortDir }: { field: SortField; sortBy: SortField; sortDir: SortDir }) {
  if (field !== sortBy) return null
  return sortDir === "asc" ? <ChevronUp className="w-3 h-3 inline ml-0.5" /> : <ChevronDown className="w-3 h-3 inline ml-0.5" />
}

// -- Framework row left-border color ------------------------------------------

function fwBorderCls(fw: FrameworkResponse): string {
  if (fw.is_marketplace_visible) return "border-l-green-500"
  if (!fw.is_active) return "border-l-slate-400"
  return "border-l-primary"
}

// -- Skeleton -----------------------------------------------------------------

function Skeleton() {
  return (
    <div className="rounded-xl border border-l-[3px] border-l-muted border-border bg-card p-4 animate-pulse space-y-2">
      <div className="flex items-center gap-3">
        <div className="h-4 w-36 bg-muted rounded" />
        <div className="h-4 w-20 bg-muted rounded" />
      </div>
      <div className="h-3 w-52 bg-muted rounded" />
    </div>
  )
}

// -- Version lifecycle badge -------------------------------------------------

const VERSION_LIFECYCLE_META: Record<string, { label: string; color: string }> = {
  draft:      { label: "Draft",      color: "text-muted-foreground bg-muted border-border" },
  published:  { label: "Published",  color: "text-emerald-600 bg-emerald-500/10 border-emerald-500/20" },
  deprecated: { label: "Deprecated", color: "text-yellow-600 bg-yellow-500/10 border-yellow-500/20" },
  archived:   { label: "Archived",   color: "text-slate-500 bg-slate-100/10 border-slate-500/20" },
}

function VersionLifecycleBadge({ state }: { state: string }) {
  const meta = VERSION_LIFECYCLE_META[state] ?? { label: state, color: "text-muted-foreground bg-muted border-border" }
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full border text-xs font-medium ${meta.color}`}>
      {meta.label}
    </span>
  )
}

// -- Create Version Dialog ---------------------------------------------------

function CreateVersionDialog({
  frameworkId,
  onCreated,
  onClose,
}: {
  frameworkId: string
  onCreated: (v: VersionResponse) => void
  onClose: () => void
}) {
  const [changeSeverity, setChangeSeverity] = useState("minor")
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setError(null)
    try {
      const payload: CreateVersionRequest = { change_severity: changeSeverity }
      const result = await createVersion(frameworkId, payload)
      onCreated(result)
      onClose()
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <Dialog open onOpenChange={(open) => { if (!open) onClose() }}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Create Version</DialogTitle>
          <DialogDescription>A new version number will be assigned automatically.</DialogDescription>
        </DialogHeader>
        {error && <div className="text-xs text-destructive bg-destructive/10 rounded-lg px-3 py-2">{error}</div>}
        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <Label className="text-xs text-muted-foreground mb-1 block">Change Severity</Label>
            <select
              value={changeSeverity}
              onChange={e => setChangeSeverity(e.target.value)}
              className="w-full h-8 px-2 rounded border border-border bg-background text-sm focus:outline-none focus:ring-1 focus:ring-primary"
            >
              <option value="patch">Patch</option>
              <option value="minor">Minor</option>
              <option value="major">Major</option>
              <option value="breaking">Breaking</option>
            </select>
          </div>
          <DialogFooter>
            <Button type="button" variant="ghost" onClick={onClose} className="h-9 px-4">Cancel</Button>
            <Button type="submit" disabled={saving} className="h-9">
              {saving ? "Creating..." : "Create Version"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

// -- Detail Side Panel --------------------------------------------------------

function FrameworkDetailPanel({
  fw,
  onEdit,
  onDelete,
  onClose,
}: {
  fw: FrameworkResponse
  onEdit: (fw: FrameworkResponse) => void
  onDelete: (fw: FrameworkResponse) => void
  onClose: () => void
}) {
  const [tab, setTab] = useState<"details" | "versions" | "controls" | "settings">("details")
  const [versions, setVersions] = useState<VersionResponse[]>([])
  const [loadingVersions, setLoadingVersions] = useState(false)
  const [showCreateVersion, setShowCreateVersion] = useState(false)
  const [publishingId, setPublishingId] = useState<string | null>(null)
  const [settings, setSettings] = useState<FrameworkSettingResponse[]>([])
  const [loadingSettings, setLoadingSettings] = useState(false)
  const [newSettingKey, setNewSettingKey] = useState("")
  const [newSettingValue, setNewSettingValue] = useState("")
  const [savingSetting, setSavingSetting] = useState(false)
  const [deletingSettingKey, setDeletingSettingKey] = useState<string | null>(null)
  // Controls tab state
  const [controls, setControls] = useState<ControlResponse[]>([])
  const [loadingControls, setLoadingControls] = useState(false)
  const [expandedControlId, setExpandedControlId] = useState<string | null>(null)
  const [controlTasks, setControlTasks] = useState<Record<string, TaskResponse[]>>({})
  const [loadingTasksFor, setLoadingTasksFor] = useState<string | null>(null)
  const [showCreateTaskFor, setShowCreateTaskFor] = useState<string | null>(null)
  const [newTaskTitle, setNewTaskTitle] = useState("")
  const [newTaskType, setNewTaskType] = useState("control_remediation")
  const [newTaskPriority, setNewTaskPriority] = useState("medium")
  const [creatingTask, setCreatingTask] = useState(false)

  const SUGGESTED_KEYS = [
    "auto_publish",
    "notification_on_update",
    "default_review_period_days",
    "require_approval_for_publish",
    "enable_cross_framework_mappings",
  ]

  const loadVersions = async () => {
    setLoadingVersions(true)
    try {
      const res = await listVersions(fw.id)
      setVersions(res.items)
    } catch {
      setVersions([])
    } finally {
      setLoadingVersions(false)
    }
  }

  const loadSettings = async () => {
    setLoadingSettings(true)
    try {
      const res = await listFrameworkSettings(fw.id)
      setSettings(res)
    } catch {
      setSettings([])
    } finally {
      setLoadingSettings(false)
    }
  }

  const loadControls = async () => {
    setLoadingControls(true)
    try {
      const res = await listControls(fw.id, { limit: 200 })
      setControls(res.items)
    } catch {
      setControls([])
    } finally {
      setLoadingControls(false)
    }
  }

  const loadControlTasks = async (controlId: string) => {
    setLoadingTasksFor(controlId)
    try {
      const res = await listTasks({ entity_type: "control", entity_id: controlId, limit: 50 })
      setControlTasks(prev => ({ ...prev, [controlId]: res.items }))
    } catch {
      setControlTasks(prev => ({ ...prev, [controlId]: [] }))
    } finally {
      setLoadingTasksFor(null)
    }
  }

  const handleExpandControl = (controlId: string) => {
    if (expandedControlId === controlId) {
      setExpandedControlId(null)
    } else {
      setExpandedControlId(controlId)
      if (!controlTasks[controlId]) loadControlTasks(controlId)
    }
  }

  const handleCreateControlTask = async (controlId: string) => {
    if (!newTaskTitle.trim()) return
    setCreatingTask(true)
    try {
      const payload: CreateTaskRequest = {
        task_type_code: newTaskType,
        priority_code: newTaskPriority,
        org_id: fw.scope_org_id ?? "",
        title: newTaskTitle.trim(),
        entity_type: "control",
        entity_id: controlId,
      }
      const task = await createTask(payload)
      setControlTasks(prev => ({ ...prev, [controlId]: [task, ...(prev[controlId] ?? [])] }))
      setNewTaskTitle("")
      setShowCreateTaskFor(null)
    } catch {
      // silent
    } finally {
      setCreatingTask(false)
    }
  }

  const handleAddSetting = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newSettingKey.trim() || !newSettingValue.trim()) return
    setSavingSetting(true)
    try {
      const updated = await setFrameworkSetting(fw.id, newSettingKey.trim(), { value: newSettingValue.trim() })
      setSettings(prev => {
        const idx = prev.findIndex(s => s.key === updated.key)
        if (idx >= 0) { const next = [...prev]; next[idx] = updated; return next }
        return [...prev, updated]
      })
      setNewSettingKey(""); setNewSettingValue("")
    } catch {
      // ignore
    } finally {
      setSavingSetting(false)
    }
  }

  const handleDeleteSetting = async (key: string) => {
    setDeletingSettingKey(key)
    try {
      await deleteFrameworkSetting(fw.id, key)
      setSettings(prev => prev.filter(s => s.key !== key))
    } catch {
      // ignore
    } finally {
      setDeletingSettingKey(null)
    }
  }

  useEffect(() => {
    if (tab === "versions") loadVersions()
    if (tab === "settings") loadSettings()
    if (tab === "controls") loadControls()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab, fw.id])

  const handlePublish = async (versionId: string) => {
    setPublishingId(versionId)
    try {
      const updated = await publishVersion(fw.id, versionId)
      setVersions(prev => prev.map(v => v.id === versionId ? updated : v))
    } catch {
      // ignore
    } finally {
      setPublishingId(null)
    }
  }

  return (
    <div className="fixed inset-y-0 right-0 w-full sm:w-[480px] bg-background border-l border-border shadow-xl z-40 flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-4 border-b border-border shrink-0">
        <div className="flex items-center gap-2">
          <Library className="w-4 h-4 text-primary" />
          <span className="font-semibold text-sm truncate">{fw.name ?? fw.framework_code}</span>
        </div>
        <div className="flex items-center gap-1">
          <Button variant="ghost" size="sm" className="h-8 px-2" onClick={() => onEdit(fw)}>
            <Pencil className="w-3.5 h-3.5" />
          </Button>
          <Button variant="ghost" size="sm" className="h-8 px-2 text-destructive hover:text-destructive" onClick={() => onDelete(fw)}>
            <Trash2 className="w-3.5 h-3.5" />
          </Button>
          <Button variant="ghost" size="sm" className="h-8 w-8 p-0" onClick={onClose}>
            <X className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-border px-5 shrink-0 overflow-x-auto">
        {(["details", "versions", "controls", "settings"] as const).map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-3 py-2.5 text-xs font-medium border-b-2 transition-colors capitalize whitespace-nowrap
              ${tab === t ? "border-primary text-primary" : "border-transparent text-muted-foreground hover:text-foreground"}`}
          >
            {t === "versions" ? `Versions${versions.length > 0 ? ` (${versions.length})` : ""}` :
             t === "controls" ? `Controls${controls.length > 0 ? ` (${controls.length})` : ""}` :
             t === "settings" ? "Settings" : "Details"}
          </button>
        ))}
      </div>

      {/* Body */}
      <div className="flex-1 overflow-y-auto p-5 space-y-5">

        {/* Details tab */}
        {tab === "details" && <>
          {/* Badges */}
          <div className="flex items-center gap-2 flex-wrap">
            {fw.is_marketplace_visible && (
              <span className="inline-flex items-center px-2 py-0.5 rounded-full border text-xs font-medium text-blue-600 bg-blue-500/10 border-blue-500/20">
                Published
              </span>
            )}
            {!fw.is_active && (
              <span className="inline-flex items-center px-2 py-0.5 rounded-full border text-xs font-medium text-muted-foreground bg-muted border-border">
                Inactive
              </span>
            )}
          </div>

          {/* Description */}
          {fw.description && (
            <div>
              <p className="text-xs font-medium text-muted-foreground mb-1">Description</p>
              <p className="text-sm text-foreground">{fw.description}</p>
            </div>
          )}

          {/* Details grid */}
          <div className="grid grid-cols-2 gap-x-4 gap-y-3 text-xs">
            <div>
              <p className="text-muted-foreground mb-0.5">Framework Code</p>
              <p className="font-mono text-foreground">{fw.framework_code}</p>
            </div>
            <div>
              <p className="text-muted-foreground mb-0.5">Type</p>
              <p className="text-foreground">{fw.type_name}</p>
            </div>
            <div>
              <p className="text-muted-foreground mb-0.5">Category</p>
              <p className="text-foreground">{fw.category_name}</p>
            </div>
            <div>
              <p className="text-muted-foreground mb-0.5">Publisher</p>
              <p className="text-foreground">{fw.publisher_name ?? "—"}</p>
            </div>
            <div>
              <p className="text-muted-foreground mb-0.5">Publisher Type</p>
              <p className="text-foreground capitalize">{fw.publisher_type ?? "—"}</p>
            </div>
            <div>
              <p className="text-muted-foreground mb-0.5">Latest Version</p>
              <p className="font-mono text-foreground">{fw.latest_version_code ? fw.latest_version_code.replace(/^v/, '') : "—"}</p>
            </div>
            <div>
              <p className="text-muted-foreground mb-0.5">Controls</p>
              <p className="font-semibold text-foreground">{fw.control_count}</p>
            </div>
            {fw.documentation_url && (
              <div className="col-span-2">
                <p className="text-muted-foreground mb-0.5">Documentation</p>
                <a href={fw.documentation_url} target="_blank" rel="noopener noreferrer" className="text-primary underline text-xs break-all">
                  {fw.documentation_url}
                </a>
              </div>
            )}
            <div>
              <p className="text-muted-foreground mb-0.5">Created</p>
              <p className="text-foreground">{formatDate(fw.created_at)}</p>
            </div>
            <div>
              <p className="text-muted-foreground mb-0.5">Updated</p>
              <p className="text-foreground">{formatDate(fw.updated_at)}</p>
            </div>
          </div>
        </>}

        {/* Versions tab */}
        {tab === "versions" && <>
          <div className="flex items-center justify-between">
            <p className="text-xs font-medium text-muted-foreground">Framework Versions</p>
            <Button size="sm" variant="outline" className="h-7 text-xs" onClick={() => setShowCreateVersion(true)}>
              <Plus className="w-3 h-3 mr-1" /> Create Version
            </Button>
          </div>

          {loadingVersions ? (
            <div className="text-xs text-muted-foreground">Loading versions...</div>
          ) : versions.length === 0 ? (
            <div className="text-xs text-muted-foreground text-center py-4">No versions yet. Create the first version.</div>
          ) : (
            <div className="space-y-2">
              {versions.map(v => (
                <div key={v.id} className="rounded-lg border border-border bg-card px-4 py-3 space-y-2">
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-sm font-semibold">{v.version_code.replace(/^v/, '')}</span>
                      <VersionLifecycleBadge state={v.lifecycle_state} />
                    </div>
                    {v.lifecycle_state === "draft" && (
                      <Button
                        size="sm"
                        variant="outline"
                        className="h-6 text-xs"
                        disabled={publishingId === v.id}
                        onClick={() => handlePublish(v.id)}
                      >
                        {publishingId === v.id ? "Publishing..." : "Publish"}
                      </Button>
                    )}
                  </div>
                  <div className="flex items-center gap-4 text-xs text-muted-foreground">
                    <span>Severity: <span className="capitalize font-medium text-foreground">{v.change_severity}</span></span>
                    <span>Controls: <span className="font-medium text-foreground">{v.control_count}</span></span>
                    <span>{formatDate(v.created_at)}</span>
                  </div>
                </div>
              ))}
            </div>
          )}

          {showCreateVersion && (
            <CreateVersionDialog
              frameworkId={fw.id}
              onCreated={v => { setVersions(prev => [v, ...prev]); setShowCreateVersion(false) }}
              onClose={() => setShowCreateVersion(false)}
            />
          )}
        </>}

        {/* Controls tab */}
        {tab === "controls" && <>
          <div className="flex items-center justify-between mb-1">
            <p className="text-xs font-medium text-muted-foreground">Framework Controls</p>
            <span className="text-xs text-muted-foreground">{controls.length} controls</span>
          </div>

          {loadingControls ? (
            <div className="text-xs text-muted-foreground py-2">Loading controls...</div>
          ) : controls.length === 0 ? (
            <div className="text-xs text-muted-foreground text-center py-4">No controls defined for this framework.</div>
          ) : (
            <div className="space-y-1.5">
              {controls.map(ctrl => (
                <div key={ctrl.id} className="rounded-lg border border-border bg-card overflow-hidden">
                  {/* Control row */}
                  <button
                    className="w-full flex items-center gap-3 px-3 py-2.5 text-left hover:bg-muted/30 transition-colors"
                    onClick={() => handleExpandControl(ctrl.id)}
                  >
                    <Layers className="w-3.5 h-3.5 text-primary shrink-0" />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 min-w-0">
                        <span className="font-mono text-xs text-muted-foreground">{ctrl.control_code}</span>
                        <span className="text-xs font-medium text-foreground truncate">{ctrl.name}</span>
                      </div>
                      {ctrl.requirement_code && (
                        <span className="text-xs text-muted-foreground/60">Req: {ctrl.requirement_code}</span>
                      )}
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <span className="text-xs text-muted-foreground flex items-center gap-0.5">
                        <ClipboardList className="w-3 h-3" />
                        {(controlTasks[ctrl.id] ?? []).length}
                      </span>
                      <span className="text-xs text-muted-foreground flex items-center gap-0.5">
                        <FlaskConical className="w-3 h-3" />
                        {ctrl.test_count}
                      </span>
                      {expandedControlId === ctrl.id ? <ChevronUp className="w-3 h-3 text-muted-foreground" /> : <ChevronDown className="w-3 h-3 text-muted-foreground" />}
                    </div>
                  </button>

                  {/* Expanded: tasks */}
                  {expandedControlId === ctrl.id && (
                    <div className="border-t border-border bg-muted/10 px-3 pb-3 pt-2 space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-medium text-muted-foreground">Tasks for this control</span>
                        <Button
                          size="sm"
                          variant="outline"
                          className="h-6 text-xs"
                          onClick={() => setShowCreateTaskFor(showCreateTaskFor === ctrl.id ? null : ctrl.id)}
                        >
                          <Plus className="w-2.5 h-2.5 mr-1" /> Add Task
                        </Button>
                      </div>

                      {showCreateTaskFor === ctrl.id && (
                        <div className="space-y-2 rounded-lg border border-primary/20 bg-primary/5 p-2.5">
                          {!fw.scope_org_id && (
                            <div className="text-xs text-orange-600 bg-orange-500/10 rounded px-2 py-1">
                              Tasks require an org-scoped framework. Set Org on this framework to enable.
                            </div>
                          )}
                          <Input
                            value={newTaskTitle}
                            onChange={e => setNewTaskTitle(e.target.value)}
                            placeholder="Task title..."
                            className="h-7 text-xs"
                            autoFocus
                          />
                          <div className="flex gap-2">
                            <select
                              value={newTaskType}
                              onChange={e => setNewTaskType(e.target.value)}
                              className="flex-1 h-7 px-2 rounded border border-border bg-background text-xs focus:outline-none focus:ring-1 focus:ring-primary"
                            >
                              <option value="control_remediation">Control Remediation</option>
                              <option value="evidence_collection">Evidence Collection</option>
                              <option value="general">General</option>
                            </select>
                            <select
                              value={newTaskPriority}
                              onChange={e => setNewTaskPriority(e.target.value)}
                              className="flex-1 h-7 px-2 rounded border border-border bg-background text-xs focus:outline-none focus:ring-1 focus:ring-primary"
                            >
                              <option value="critical">Critical</option>
                              <option value="high">High</option>
                              <option value="medium">Medium</option>
                              <option value="low">Low</option>
                            </select>
                          </div>
                          <div className="flex gap-1.5">
                            <Button size="sm" className="h-6 text-xs flex-1" disabled={creatingTask || !newTaskTitle.trim() || !fw.scope_org_id} onClick={() => handleCreateControlTask(ctrl.id)}>
                              {creatingTask ? "Creating..." : "Create Task"}
                            </Button>
                            <Button size="sm" variant="ghost" className="h-6 text-xs" onClick={() => setShowCreateTaskFor(null)}>
                              Cancel
                            </Button>
                          </div>
                        </div>
                      )}

                      {loadingTasksFor === ctrl.id ? (
                        <div className="text-xs text-muted-foreground py-1">Loading tasks...</div>
                      ) : (controlTasks[ctrl.id] ?? []).length === 0 ? (
                        <div className="text-xs text-muted-foreground py-1">No tasks linked to this control.</div>
                      ) : (
                        <div className="space-y-1">
                          {(controlTasks[ctrl.id] ?? []).map(task => (
                            <div key={task.id} className="flex items-center gap-2 rounded-md border border-border bg-card px-2.5 py-1.5">
                              <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${
                                task.status_code === "open" ? "bg-blue-500" :
                                task.status_code === "in_progress" ? "bg-yellow-500" :
                                task.status_code === "resolved" ? "bg-emerald-500" :
                                task.status_code === "overdue" ? "bg-red-500" : "bg-muted-foreground"
                              }`} />
                              <span className="text-xs text-foreground flex-1 truncate">{task.title}</span>
                              <span className="text-xs text-muted-foreground capitalize">{task.status_code?.replace(/_/g, " ")}</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </>}

        {/* Settings tab */}
        {tab === "settings" && <>
          <div className="flex items-center justify-between">
            <p className="text-xs font-medium text-muted-foreground">Framework Settings</p>
          </div>

          {loadingSettings ? (
            <div className="text-xs text-muted-foreground">Loading settings...</div>
          ) : settings.length === 0 ? (
            <div className="text-xs text-muted-foreground text-center py-2">No settings configured yet.</div>
          ) : (
            <div className="space-y-1.5">
              {settings.map(s => (
                <div key={s.key} className="flex items-center justify-between gap-2 rounded-lg border border-border bg-card px-3 py-2">
                  <div className="min-w-0 flex-1">
                    <p className="text-xs font-mono font-medium text-foreground truncate">{s.key}</p>
                    <p className="text-xs text-muted-foreground truncate">{s.value}</p>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-6 w-6 p-0 text-destructive hover:text-destructive shrink-0"
                    disabled={deletingSettingKey === s.key}
                    onClick={() => handleDeleteSetting(s.key)}
                  >
                    <Trash2 className="w-3 h-3" />
                  </Button>
                </div>
              ))}
            </div>
          )}

          <form onSubmit={handleAddSetting} className="space-y-2 pt-2 border-t border-border">
            <p className="text-xs font-medium text-foreground">Add Setting</p>
            <div>
              <Label className="text-xs text-muted-foreground mb-1 block">Key</Label>
              <Input
                list="setting-key-suggestions"
                value={newSettingKey}
                onChange={e => setNewSettingKey(e.target.value)}
                placeholder="setting_key"
                className="h-8 text-sm font-mono"
              />
              <datalist id="setting-key-suggestions">
                {SUGGESTED_KEYS.map(k => <option key={k} value={k} />)}
              </datalist>
            </div>
            <div>
              <Label className="text-xs text-muted-foreground mb-1 block">Value</Label>
              <Input
                value={newSettingValue}
                onChange={e => setNewSettingValue(e.target.value)}
                placeholder="setting_value"
                className="h-8 text-sm"
              />
            </div>
            <Button type="submit" size="sm" className="h-7 text-xs w-full" disabled={savingSetting || !newSettingKey.trim() || !newSettingValue.trim()}>
              {savingSetting ? "Saving..." : "Save Setting"}
            </Button>
          </form>
        </>}
      </div>
    </div>
  )
}

// -- Create / Edit Dialog -----------------------------------------------------

function FrameworkDialog({
  mode,
  framework,
  types,
  categories,
  onSaved,
  onClose,
}: {
  mode: "create" | "edit"
  framework?: FrameworkResponse
  types: FrameworkTypeOption[]
  categories: FrameworkCategoryOption[]
  onSaved: (fw: FrameworkResponse) => void
  onClose: () => void
}) {
  const [code, setCode] = useState(framework?.framework_code ?? "")
  const [name, setName] = useState(framework?.name ?? "")
  const [codeEdited, setCodeEdited] = useState(mode === "edit")
  const [desc, setDesc] = useState(framework?.description ?? "")
  const [typeCode, setTypeCode] = useState(framework?.framework_type_code ?? types[0]?.code ?? "")
  const [categoryCode, setCategoryCode] = useState(framework?.framework_category_code ?? categories[0]?.code ?? "")
  const [publisherType, setPublisherType] = useState(framework?.publisher_type ?? "internal")
  const [publisherName, setPublisherName] = useState(framework?.publisher_name ?? "")
  const [isMarketplace, setIsMarketplace] = useState(framework?.is_marketplace_visible ?? false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Auto-generate code from name (slugify)
  const handleNameChange = (val: string) => {
    setName(val)
    if (!codeEdited) {
      setCode(val.toLowerCase().replace(/\s+/g, "_").replace(/[^a-z0-9_]/g, ""))
    }
  }

  const handleCodeChange = (val: string) => {
    setCode(val.toLowerCase().replace(/[^a-z0-9_-]/g, "_"))
    setCodeEdited(true)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setError(null)
    try {
      let result: FrameworkResponse
      if (mode === "create") {
        const payload: CreateFrameworkRequest = {
          framework_code: code,
          name,
          description: desc || undefined,
          framework_type_code: typeCode,
          framework_category_code: categoryCode,
          publisher_type: publisherType,
          publisher_name: publisherName || undefined,
        }
        result = await createFramework(payload)
      } else {
        const payload: UpdateFrameworkRequest = {
          name,
          description: desc || undefined,
          framework_category_code: categoryCode,
          is_marketplace_visible: isMarketplace,
        }
        result = await updateFramework(framework!.id, payload)
      }
      onSaved(result)
      onClose()
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <Dialog open onOpenChange={(open) => { if (!open) onClose() }}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>{mode === "create" ? "Create Framework" : "Edit Framework"}</DialogTitle>
          <DialogDescription>
            {mode === "create"
              ? "Add a new compliance or governance framework to the library."
              : "Update framework details."}
          </DialogDescription>
        </DialogHeader>

        {error && (
          <div className="text-xs text-destructive bg-destructive/10 rounded-lg px-3 py-2">{error}</div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Name is primary */}
          <div>
            <Label className="text-xs text-muted-foreground mb-1 block">Name <span className="text-destructive">*</span></Label>
            <Input
              value={name}
              onChange={e => handleNameChange(e.target.value)}
              placeholder="e.g. NIST CSF 2.0"
              required
              className="h-8 text-sm"
            />
          </div>

          {/* Code is secondary, auto-generated */}
          <div>
            <Label className="text-xs text-muted-foreground mb-1 block">
              Code <span className="text-destructive">*</span>
              {!codeEdited && mode === "create" && (
                <span className="ml-1.5 text-[10px] text-muted-foreground/60 font-normal">(auto-generated)</span>
              )}
            </Label>
            <Input
              value={code}
              onChange={e => handleCodeChange(e.target.value)}
              placeholder="e.g. nist_csf_2"
              required
              disabled={mode === "edit"}
              className="h-8 text-sm font-mono"
            />
          </div>

          <div>
            <Label className="text-xs text-muted-foreground mb-1 block">Description</Label>
            <Input value={desc} onChange={e => setDesc(e.target.value)} placeholder="Brief description" className="h-8 text-sm" />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label className="text-xs text-muted-foreground mb-1 block">Type <span className="text-destructive">*</span></Label>
              <select
                value={typeCode}
                onChange={e => setTypeCode(e.target.value)}
                disabled={mode === "edit"}
                className="w-full h-8 px-2 rounded border border-border bg-background text-sm focus:outline-none focus:ring-1 focus:ring-primary disabled:opacity-50"
                required
              >
                {types.map(t => <option key={t.code} value={t.code}>{t.name}</option>)}
              </select>
            </div>
            <div>
              <Label className="text-xs text-muted-foreground mb-1 block">Category <span className="text-destructive">*</span></Label>
              <select
                value={categoryCode}
                onChange={e => setCategoryCode(e.target.value)}
                className="w-full h-8 px-2 rounded border border-border bg-background text-sm focus:outline-none focus:ring-1 focus:ring-primary"
                required
              >
                {categories.map(c => <option key={c.code} value={c.code}>{c.name}</option>)}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label className="text-xs text-muted-foreground mb-1 block">Publisher Type</Label>
              <select
                value={publisherType}
                onChange={e => setPublisherType(e.target.value)}
                disabled={mode === "edit"}
                className="w-full h-8 px-2 rounded border border-border bg-background text-sm focus:outline-none focus:ring-1 focus:ring-primary disabled:opacity-50"
              >
                <option value="internal">Internal</option>
                <option value="partner">Partner</option>
                <option value="community">Community</option>
                <option value="official">Official</option>
              </select>
            </div>
            <div>
              <Label className="text-xs text-muted-foreground mb-1 block">Publisher Name</Label>
              <Input value={publisherName} onChange={e => setPublisherName(e.target.value)} placeholder="e.g. NIST" disabled={mode === "edit"} className="h-8 text-sm" />
            </div>
          </div>

          {mode === "edit" && (
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="marketplace-visible"
                checked={isMarketplace}
                onChange={e => setIsMarketplace(e.target.checked)}
                className="h-4 w-4 rounded border-border"
              />
              <Label htmlFor="marketplace-visible" className="text-sm cursor-pointer">Visible in marketplace</Label>
            </div>
          )}

          <DialogFooter>
            <Button type="button" variant="ghost" onClick={onClose} className="h-9 px-4">Cancel</Button>
            <Button type="submit" disabled={saving} className="h-9">
              {saving ? (mode === "create" ? "Creating..." : "Saving...") : (mode === "create" ? "Create Framework" : "Save Changes")}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

// -- Delete Confirm Dialog ----------------------------------------------------

function DeleteConfirmDialog({
  framework,
  onConfirm,
  onClose,
}: {
  framework: FrameworkResponse
  onConfirm: () => Promise<void>
  onClose: () => void
}) {
  const [deleting, setDeleting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleDelete = async () => {
    setDeleting(true)
    setError(null)
    try {
      await onConfirm()
      onClose()
    } catch (e) {
      setError((e as Error).message)
      setDeleting(false)
    }
  }

  return (
    <Dialog open onOpenChange={(open) => { if (!open) onClose() }}>
      <DialogContent className="max-w-sm">
        <DialogHeader>
          <DialogTitle>Delete Framework</DialogTitle>
          <DialogDescription>
            Are you sure you want to delete <strong>{framework.name ?? framework.framework_code}</strong>? This action cannot be undone.
          </DialogDescription>
        </DialogHeader>
        {error && <div className="text-xs text-destructive bg-destructive/10 rounded-lg px-3 py-2">{error}</div>}
        <DialogFooter>
          <Button type="button" variant="ghost" onClick={onClose} className="h-9 px-4">Cancel</Button>
          <Button variant="destructive" onClick={handleDelete} disabled={deleting} className="h-9">
            {deleting ? "Deleting..." : "Delete"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// -- Main Page ----------------------------------------------------------------

export default function AdminFrameworksPage() {
  const [frameworks, setFrameworks] = useState<FrameworkResponse[]>([])
  const [types, setTypes] = useState<FrameworkTypeOption[]>([])
  const [categories, setCategories] = useState<FrameworkCategoryOption[]>([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // dialogs
  const [showCreate, setShowCreate] = useState(false)
  const [editTarget, setEditTarget] = useState<FrameworkResponse | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<FrameworkResponse | null>(null)
  const [detailTarget, setDetailTarget] = useState<FrameworkResponse | null>(null)

  // filters
  const [search, setSearch] = useState("")
  const [filterCategory, setFilterCategory] = useState("")
  const [filterType, setFilterType] = useState("")
  const [showAll, setShowAll] = useState(false)

  // sort + pagination
  const [sortBy, setSortBy] = useState<SortField>("name")
  const [sortDir, setSortDir] = useState<SortDir>("asc")
  const [page, setPage] = useState(0)

  // bulk select
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())

  const load = useCallback(async (quiet = false) => {
    if (quiet) setRefreshing(true); else setLoading(true)
    setError(null)
    try {
      const [fwRes, typesRes, catsRes] = await Promise.all([
        listFrameworks(),
        listFrameworkTypes(),
        listFrameworkCategories(),
      ])
      setFrameworks(fwRes.items)
      setTypes(typesRes)
      setCategories(catsRes)
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  const handleSaved = useCallback((fw: FrameworkResponse) => {
    setFrameworks(prev => {
      const idx = prev.findIndex(f => f.id === fw.id)
      if (idx >= 0) {
        const next = [...prev]
        next[idx] = fw
        return next
      }
      return [fw, ...prev]
    })
  }, [])

  const handleDelete = useCallback(async (fw: FrameworkResponse) => {
    await deleteFramework(fw.id)
    setFrameworks(prev => prev.filter(f => f.id !== fw.id))
    if (detailTarget?.id === fw.id) setDetailTarget(null)
  }, [detailTarget])

  const handleSort = (field: SortField) => {
    if (sortBy === field) {
      setSortDir(d => d === "asc" ? "desc" : "asc")
    } else {
      setSortBy(field)
      setSortDir("asc")
    }
    setPage(0)
  }

  const filtered = useMemo(() => {
    let items = frameworks.filter(fw => {
      // Default: show only published (marketplace visible). Toggle to show all.
      if (!showAll && !fw.is_marketplace_visible) return false
      if (search.trim()) {
        const q = search.toLowerCase()
        if (!fw.name?.toLowerCase().includes(q) && !fw.framework_code.toLowerCase().includes(q)) return false
      }
      if (filterCategory && fw.framework_category_code !== filterCategory) return false
      if (filterType && fw.framework_type_code !== filterType) return false
      return true
    })

    items = [...items].sort((a, b) => {
      let av = ""
      let bv = ""
      if (sortBy === "name") { av = a.name ?? ""; bv = b.name ?? "" }
      else if (sortBy === "type_name") { av = a.type_name ?? ""; bv = b.type_name ?? "" }
      else if (sortBy === "category_name") { av = a.category_name ?? ""; bv = b.category_name ?? "" }
      else if (sortBy === "created_at") { av = a.created_at; bv = b.created_at }
      const cmp = av.localeCompare(bv)
      return sortDir === "asc" ? cmp : -cmp
    })

    return items
  }, [frameworks, search, filterCategory, filterType, sortBy, sortDir, showAll])

  const totalPages = Math.ceil(filtered.length / PAGE_SIZE)
  const paginated = filtered.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE)
  const hasFilters = search.trim() || filterCategory || filterType

  const clearFilters = () => {
    setSearch("")
    setFilterCategory("")
    setFilterType("")
    setPage(0)
  }

  // Bulk select
  const allOnPageSelected = paginated.length > 0 && paginated.every(fw => selectedIds.has(fw.id))
  const toggleSelectAll = () => {
    if (allOnPageSelected) {
      setSelectedIds(prev => {
        const next = new Set(prev)
        paginated.forEach(fw => next.delete(fw.id))
        return next
      })
    } else {
      setSelectedIds(prev => {
        const next = new Set(prev)
        paginated.forEach(fw => next.add(fw.id))
        return next
      })
    }
  }

  // Export CSV
  const exportCsv = () => {
    const rows = [
      ["code", "name", "type", "category", "published", "publisher", "controls", "version", "created_at"],
      ...filtered.map(fw => [
        fw.framework_code,
        fw.name ?? "",
        fw.type_name ?? "",
        fw.category_name ?? "",
        fw.is_marketplace_visible ? "yes" : "no",
        fw.publisher_name ?? "",
        String(fw.control_count),
        fw.latest_version_code ?? "",
        fw.created_at,
      ]),
    ]
    const csv = rows.map(r => r.map(v => `"${String(v).replace(/"/g, '""')}"`).join(",")).join("\n")
    const blob = new Blob([csv], { type: "text/csv" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = "frameworks.csv"
    a.click()
    URL.revokeObjectURL(url)
  }

  const totalFrameworks = frameworks.length
  const publishedCount = frameworks.filter(f => f.is_marketplace_visible).length
  const totalControls = frameworks.reduce((s, f) => s + (f.control_count ?? 0), 0)

  // KPI stat meta
  const stats = [
    { label: "Total Frameworks", value: totalFrameworks, icon: Library,   borderCls: "border-l-primary",     numCls: "text-foreground" },
    { label: "Published",        value: publishedCount,  icon: Shield,    borderCls: "border-l-green-500",   numCls: "text-green-600" },
    { label: "Total Controls",   value: totalControls,   icon: FileText,  borderCls: "border-l-blue-500",    numCls: "text-blue-600" },
  ]

  return (
    <div className={`p-6 space-y-6 ${detailTarget ? "mr-[480px]" : ""} max-w-5xl transition-all`}>
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold">{showAll ? "All Frameworks" : "Published Frameworks"}</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            {showAll
              ? "All frameworks across all orgs and workspaces."
              : "Published frameworks available in the marketplace."
            }{" "}
            <button onClick={() => { setShowAll(!showAll); setPage(0) }} className="text-primary hover:underline font-medium">
              {showAll ? "Show Published Only" : "Show All Frameworks"}
            </button>
          </p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <Button variant="ghost" size="sm" className="h-8 px-2" onClick={exportCsv} title="Export CSV">
            <Download className="w-3.5 h-3.5 mr-1" /> Export
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="h-8 w-8 p-0"
            onClick={() => load(true)}
            disabled={refreshing}
            title="Refresh"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? "animate-spin" : ""}`} />
          </Button>
          <Button onClick={() => setShowCreate(true)} size="sm" className="h-8 px-3 shrink-0">
            <Plus className="w-3.5 h-3.5 mr-1" /> Create Framework
          </Button>
        </div>
      </div>

      {/* KPI stat cards */}
      <div className="grid grid-cols-3 gap-3">
        {stats.map(s => (
          <div key={s.label} className={`relative flex items-center gap-3 rounded-xl border border-l-[3px] ${s.borderCls} bg-card px-4 py-3`}>
            <div className="shrink-0 rounded-lg p-2 bg-muted">
              <s.icon className="w-4 h-4 text-muted-foreground" />
            </div>
            <div className="min-w-0">
              <div className={`text-2xl font-bold tabular-nums leading-none ${s.numCls}`}>{s.value}</div>
              <span className="text-[11px] text-muted-foreground mt-0.5 block truncate">{s.label}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Filter bar */}
      <div className="rounded-xl border border-border bg-card px-4 py-3 flex items-center gap-2 flex-wrap">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-2.5 w-4 h-4 text-muted-foreground" />
          <Input
            className="pl-9 h-9"
            placeholder="Search by name or code..."
            value={search}
            onChange={e => { setSearch(e.target.value); setPage(0) }}
          />
        </div>
        {categories.length > 0 && (
          <select
            value={filterCategory}
            onChange={e => { setFilterCategory(e.target.value); setPage(0) }}
            className="h-9 px-3 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-1 focus:ring-primary"
          >
            <option value="">All Categories</option>
            {categories.map(c => <option key={c.code} value={c.code}>{c.name}</option>)}
          </select>
        )}
        {types.length > 0 && (
          <select
            value={filterType}
            onChange={e => { setFilterType(e.target.value); setPage(0) }}
            className="h-9 px-3 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-1 focus:ring-primary"
          >
            <option value="">All Types</option>
            {types.map(t => <option key={t.code} value={t.code}>{t.name}</option>)}
          </select>
        )}
        {/* Active filter chips */}
        {search.trim() && (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-primary/10 border border-primary/20 text-xs text-primary">
            &ldquo;{search}&rdquo;
            <button onClick={() => { setSearch(""); setPage(0) }} className="hover:text-primary/60"><X className="w-3 h-3" /></button>
          </span>
        )}
        {filterCategory && (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-primary/10 border border-primary/20 text-xs text-primary">
            {categories.find(c => c.code === filterCategory)?.name ?? filterCategory}
            <button onClick={() => { setFilterCategory(""); setPage(0) }} className="hover:text-primary/60"><X className="w-3 h-3" /></button>
          </span>
        )}
        {filterType && (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-primary/10 border border-primary/20 text-xs text-primary">
            {types.find(t => t.code === filterType)?.name ?? filterType}
            <button onClick={() => { setFilterType(""); setPage(0) }} className="hover:text-primary/60"><X className="w-3 h-3" /></button>
          </span>
        )}
        {hasFilters && (
          <Button variant="ghost" size="sm" className="h-9 px-2 text-muted-foreground" onClick={clearFilters}>
            Clear all
          </Button>
        )}
      </div>

      {/* Sort bar + count */}
      {!loading && !error && (
        <div className="flex items-center gap-4 text-xs text-muted-foreground">
          <span>Showing {filtered.length} of {frameworks.length} frameworks</span>
          <span className="text-muted-foreground/50">|</span>
          <span>Sort by:</span>
          {(["name", "type_name", "category_name", "created_at"] as SortField[]).map(f => (
            <button
              key={f}
              className={`hover:text-foreground transition-colors ${sortBy === f ? "text-foreground font-medium" : ""}`}
              onClick={() => handleSort(f)}
            >
              {f === "type_name" ? "Type" : f === "category_name" ? "Category" : f === "created_at" ? "Created" : "Name"}
              <SortIcon field={f} sortBy={sortBy} sortDir={sortDir} />
            </button>
          ))}
        </div>
      )}

      {/* Bulk select toolbar */}
      {selectedIds.size > 0 && (
        <div className="flex items-center gap-3 px-4 py-2.5 rounded-xl bg-primary/5 border border-primary/20">
          <span className="text-sm font-medium">{selectedIds.size} selected</span>
          <Button size="sm" variant="ghost" className="h-7 px-2 ml-auto text-muted-foreground" onClick={() => setSelectedIds(new Set())}>
            <X className="w-3.5 h-3.5" />
          </Button>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="flex items-center gap-2 rounded-xl border border-destructive/20 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          <AlertTriangle className="w-4 h-4 shrink-0" /> {error}
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="space-y-2">
          {[...Array(5)].map((_, i) => <Skeleton key={i} />)}
        </div>
      )}

      {/* Table header */}
      {!loading && !error && filtered.length > 0 && (
        <div className="flex items-center gap-3 px-4 py-2 text-xs text-muted-foreground border-b border-border">
          <button className="shrink-0" onClick={toggleSelectAll}>
            {allOnPageSelected
              ? <CheckSquare className="w-4 h-4 text-primary" />
              : <Square className="w-4 h-4" />}
          </button>
          <span className="flex-1">Framework</span>
          <span className="hidden md:block w-24 text-center">Type</span>
          <span className="hidden lg:block w-28 text-center">Category</span>
          <span className="hidden md:block w-16 text-center">Controls</span>
          <span className="hidden sm:block w-24 text-right">Created</span>
        </div>
      )}

      {/* List */}
      {!loading && !error && (
        <div className="space-y-1">
          {paginated.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-8">
              {hasFilters ? "No frameworks match your filters." : "No frameworks yet. Create your first framework to get started."}
            </p>
          ) : (
            paginated.map(fw => (
              <div
                key={fw.id ?? fw.framework_code}
                className={`relative flex items-center gap-3 px-4 py-3 rounded-xl border border-l-[3px] ${fwBorderCls(fw)} transition-colors cursor-pointer
                  ${detailTarget?.id === fw.id ? "bg-primary/5 border-primary/20" : "bg-card hover:bg-muted/30"}
                  ${selectedIds.has(fw.id) ? "bg-primary/5 border-primary/30" : ""}`}
              >
                {/* Checkbox */}
                <button
                  className="shrink-0"
                  onClick={e => {
                    e.stopPropagation()
                    setSelectedIds(prev => {
                      const next = new Set(prev)
                      if (next.has(fw.id)) next.delete(fw.id)
                      else next.add(fw.id)
                      return next
                    })
                  }}
                >
                  {selectedIds.has(fw.id)
                    ? <CheckSquare className="w-4 h-4 text-primary" />
                    : <Square className="w-4 h-4 text-muted-foreground" />}
                </button>

                {/* Name + code */}
                <div
                  className="flex-1 min-w-0 flex items-center gap-2 flex-wrap"
                  onClick={() => setDetailTarget(prev => prev?.id === fw.id ? null : fw)}
                >
                  <Library className="w-4 h-4 shrink-0 text-primary" />
                  <span className="font-medium text-sm">{fw.name ?? fw.framework_code}</span>
                  <span className="font-mono text-xs text-muted-foreground hidden sm:inline">{fw.framework_code}</span>
                </div>

                {/* Type */}
                <span className="hidden md:block w-24 text-center text-xs text-muted-foreground truncate">
                  {fw.type_name}
                </span>

                {/* Category */}
                <span className="hidden lg:block w-28 text-center text-xs text-muted-foreground truncate">
                  {fw.category_name}
                </span>

                {/* Controls */}
                <span className="hidden md:block w-16 text-center text-xs text-muted-foreground">
                  {fw.control_count}
                </span>

                {/* Date */}
                <span className="hidden sm:block w-24 text-right text-xs text-muted-foreground">
                  {formatDate(fw.created_at)}
                </span>

                {/* Quick actions */}
                <div className="flex items-center gap-1 shrink-0" onClick={e => e.stopPropagation()}>
                  <Button variant="ghost" size="sm" className="h-7 w-7 p-0" onClick={() => setEditTarget(fw)} title="Edit">
                    <Pencil className="w-3 h-3" />
                  </Button>
                  <Button variant="ghost" size="sm" className="h-7 w-7 p-0 text-destructive hover:text-destructive" onClick={() => setDeleteTarget(fw)} title="Delete">
                    <Trash2 className="w-3 h-3" />
                  </Button>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between pt-2">
          <span className="text-xs text-muted-foreground">
            Page {page + 1} of {totalPages} ({filtered.length} total)
          </span>
          <div className="flex items-center gap-1">
            <Button
              variant="ghost"
              size="sm"
              className="h-8 w-8 p-0"
              disabled={page === 0}
              onClick={() => setPage(p => p - 1)}
            >
              <ChevronLeft className="w-4 h-4" />
            </Button>
            {Array.from({ length: Math.min(totalPages, 7) }, (_, i) => {
              const pageNum = totalPages <= 7 ? i : (page < 4 ? i : (page > totalPages - 4 ? totalPages - 7 + i : page - 3 + i))
              return (
                <Button
                  key={pageNum}
                  variant={pageNum === page ? "default" : "ghost"}
                  size="sm"
                  className="h-8 w-8 p-0 text-xs"
                  onClick={() => setPage(pageNum)}
                >
                  {pageNum + 1}
                </Button>
              )
            })}
            <Button
              variant="ghost"
              size="sm"
              className="h-8 w-8 p-0"
              disabled={page >= totalPages - 1}
              onClick={() => setPage(p => p + 1)}
            >
              <ChevronRight className="w-4 h-4" />
            </Button>
          </div>
        </div>
      )}

      {/* Detail panel */}
      {detailTarget && (
        <>
          <div className="fixed inset-0 z-30" onClick={() => setDetailTarget(null)} />
          <FrameworkDetailPanel
            fw={detailTarget}
            onEdit={fw => { setDetailTarget(null); setEditTarget(fw) }}
            onDelete={fw => { setDetailTarget(null); setDeleteTarget(fw) }}
            onClose={() => setDetailTarget(null)}
          />
        </>
      )}

      {/* Create dialog */}
      {showCreate && (
        <FrameworkDialog
          mode="create"
          types={types}
          categories={categories}
          onSaved={handleSaved}
          onClose={() => setShowCreate(false)}
        />
      )}

      {/* Edit dialog */}
      {editTarget && (
        <FrameworkDialog
          mode="edit"
          framework={editTarget}
          types={types}
          categories={categories}
          onSaved={fw => { handleSaved(fw); setEditTarget(null) }}
          onClose={() => setEditTarget(null)}
        />
      )}

      {/* Delete confirm */}
      {deleteTarget && (
        <DeleteConfirmDialog
          framework={deleteTarget}
          onConfirm={() => handleDelete(deleteTarget)}
          onClose={() => setDeleteTarget(null)}
        />
      )}
    </div>
  )
}
