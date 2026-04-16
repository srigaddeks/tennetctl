"use client"

import { useEffect, useState, useCallback } from "react"
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
  CheckSquare,
  Plus,
  Search,
  AlertTriangle,
  RefreshCw,
  ChevronDown,
  ChevronRight,
  Clock,
  Users,
  MessageSquare,
  Ban,
  Calendar,
  X,
} from "lucide-react"
import {
  listTasks,
  createTask,
  listTaskTypes,
  listTaskPriorities,
  listTaskStatuses,
} from "@/lib/api/grc"
import type { TaskResponse, CreateTaskRequest } from "@/lib/types/grc"

// -- Constants ----------------------------------------------------------------

const PRIORITY_META: Record<string, { label: string; color: string }> = {
  critical: { label: "Critical", color: "text-red-600 bg-red-500/10 border-red-500/20" },
  high:     { label: "High",     color: "text-orange-600 bg-orange-500/10 border-orange-500/20" },
  medium:   { label: "Medium",   color: "text-yellow-600 bg-yellow-500/10 border-yellow-500/20" },
  low:      { label: "Low",      color: "text-emerald-600 bg-emerald-500/10 border-emerald-500/20" },
}

const STATUS_META: Record<string, { label: string; color: string }> = {
  open:                  { label: "Open",                 color: "text-muted-foreground bg-muted border-border" },
  in_progress:           { label: "In Progress",          color: "text-blue-600 bg-blue-500/10 border-blue-500/20" },
  pending_verification:  { label: "Pending Verification", color: "text-yellow-600 bg-yellow-500/10 border-yellow-500/20" },
  resolved:              { label: "Resolved",             color: "text-emerald-600 bg-emerald-500/10 border-emerald-500/20" },
  cancelled:             { label: "Cancelled",            color: "text-slate-500 bg-slate-500/10 border-slate-500/20" },
  overdue:               { label: "Overdue",              color: "text-red-600 bg-red-500/10 border-red-500/20" },
}

// border-l-[3px] color by status
function taskBorderCls(statusCode: string, dueDate: string | null, isTerminal: boolean): string {
  if (!isTerminal && dueDate && new Date(dueDate) < new Date()) return "border-l-red-500"
  const map: Record<string, string> = {
    open:                 "border-l-blue-500",
    in_progress:          "border-l-amber-500",
    completed:            "border-l-green-500",
    resolved:             "border-l-green-500",
    pending_verification: "border-l-amber-500",
    overdue:              "border-l-red-500",
    cancelled:            "border-l-primary",
  }
  return map[statusCode] ?? "border-l-primary"
}

// KPI stat card accent color
function statNumCls(label: string): string {
  if (label === "Overdue") return "text-red-500"
  return "text-foreground"
}
function statBorderCls(label: string): string {
  if (label === "Overdue") return "border-l-red-500"
  if (label === "Open Tasks") return "border-l-amber-500"
  return "border-l-primary"
}

interface TaskTypeOption {
  code: string
  name: string
}

interface TaskPriorityOption {
  code: string
  name: string
}

interface TaskStatusOption {
  code: string
  name: string
  is_terminal: boolean
}

// -- Helpers ------------------------------------------------------------------

function PriorityBadge({ code, name }: { code?: string; name: string }) {
  const meta = PRIORITY_META[code ?? name.toLowerCase()] ?? { label: name, color: "text-muted-foreground bg-muted border-border" }
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full border text-xs font-medium ${meta.color}`}>
      {meta.label}
    </span>
  )
}

function TaskStatusBadge({ code, name, isTerminal }: { code?: string; name: string; isTerminal?: boolean }) {
  const meta = STATUS_META[code ?? name.toLowerCase().replace(/\s+/g, "_")] ?? { label: name, color: "text-muted-foreground bg-muted border-border" }
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full border text-xs font-medium ${meta.color}`}>
      {isTerminal && <Ban className="w-2.5 h-2.5" />}
      {meta.label}
    </span>
  )
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })
}

function formatDueDate(iso: string | null) {
  if (!iso) return "—"
  const d = new Date(iso)
  const now = new Date()
  const isOverdue = d < now
  return (
    <span className={isOverdue ? "text-red-500 font-medium" : ""}>
      {formatDate(iso)}
      {isOverdue && " (overdue)"}
    </span>
  )
}

// -- Skeleton -----------------------------------------------------------------

function Skeleton() {
  return (
    <div className="rounded-xl border border-border border-l-[3px] border-l-primary bg-card p-4 animate-pulse space-y-2">
      <div className="flex items-center gap-3">
        <div className="h-4 w-36 bg-muted rounded" />
        <div className="h-4 w-20 bg-muted rounded" />
      </div>
      <div className="h-3 w-52 bg-muted rounded" />
    </div>
  )
}

// -- Task Row -----------------------------------------------------------------

function TaskRow({ task }: { task: TaskResponse }) {
  const [expanded, setExpanded] = useState(false)
  const borderCls = taskBorderCls(task.status_code ?? "", task.due_date ?? null, task.is_terminal ?? false)

  return (
    <div className="group/task">
      <div
        className={`flex items-center gap-3 px-4 py-3 rounded-xl border border-l-[3px] ${borderCls} transition-colors cursor-pointer
          ${expanded ? "border-primary/20 bg-primary/5" : "border-border bg-card hover:border-border/80 hover:bg-muted/30"}`}
        onClick={() => setExpanded(v => !v)}
      >
        <span className="text-muted-foreground shrink-0">
          {expanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
        </span>

        <div className="shrink-0 rounded-lg p-2 bg-muted">
          <CheckSquare className="w-3.5 h-3.5 text-primary" />
        </div>

        <div className="flex-1 min-w-0 flex items-center gap-2 flex-wrap">
          <span className="font-medium text-sm truncate">{task.title}</span>
          <PriorityBadge code={task.priority_code} name={task.priority_name} />
          <TaskStatusBadge code={task.status_code} name={task.status_name} isTerminal={task.is_terminal} />
          {task.version > 1 && (
            <span className="font-mono text-[10px] text-muted-foreground border border-border/50 rounded px-1 hidden md:inline">v{task.version}</span>
          )}
        </div>

        <div className="flex items-center gap-4 shrink-0 text-xs text-muted-foreground">
          <span className="hidden md:inline">{task.task_type_name}</span>
          {task.due_date && (
            <span className="hidden sm:flex items-center gap-1">
              <Calendar className="w-3 h-3" />
              {formatDueDate(task.due_date)}
            </span>
          )}
          <div className="flex items-center gap-2">
            {(task.co_assignee_count ?? 0) > 0 && (
              <span className="flex items-center gap-0.5" title="Co-assignees">
                <Users className="w-3 h-3" />
                {task.co_assignee_count}
              </span>
            )}
            {(task.blocker_count ?? 0) > 0 && (
              <span className="flex items-center gap-0.5 text-red-500" title="Blockers">
                <Ban className="w-3 h-3" />
                {task.blocker_count}
              </span>
            )}
            {(task.comment_count ?? 0) > 0 && (
              <span className="flex items-center gap-0.5" title="Comments">
                <MessageSquare className="w-3 h-3" />
                {task.comment_count}
              </span>
            )}
          </div>
        </div>
      </div>

      {expanded && (
        <div className="mt-1 mb-2 rounded-xl border border-border bg-card overflow-hidden">
          <div className="px-4 py-3 space-y-3">
            {task.description && (
              <p className="text-xs text-muted-foreground">{task.description}</p>
            )}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-x-4 gap-y-2 text-xs">
              <div>
                <span className="text-muted-foreground">Type</span>
                <p className="text-foreground">{task.task_type_name}</p>
              </div>
              <div>
                <span className="text-muted-foreground">Priority</span>
                <p><PriorityBadge code={task.priority_code} name={task.priority_name} /></p>
              </div>
              <div>
                <span className="text-muted-foreground">Status</span>
                <p><TaskStatusBadge code={task.status_code} name={task.status_name} isTerminal={task.is_terminal} /></p>
              </div>
              <div>
                <span className="text-muted-foreground">Due Date</span>
                <p className="text-foreground">{formatDueDate(task.due_date)}</p>
              </div>
              <div>
                <span className="text-muted-foreground">Co-Assignees</span>
                <p className="text-foreground">{task.co_assignee_count ?? 0}</p>
              </div>
              <div>
                <span className="text-muted-foreground">Blockers</span>
                <p className={`text-foreground ${(task.blocker_count ?? 0) > 0 ? "text-red-500 font-medium" : ""}`}>{task.blocker_count ?? 0}</p>
              </div>
              <div>
                <span className="text-muted-foreground">Comments</span>
                <p className="text-foreground">{task.comment_count ?? 0}</p>
              </div>
              <div>
                <span className="text-muted-foreground">Created</span>
                <p className="text-foreground">{formatDate(task.created_at)}</p>
              </div>
              <div>
                <span className="text-muted-foreground">Version</span>
                <p className="font-mono text-foreground">v{task.version ?? 1}</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// -- Create Dialog ------------------------------------------------------------

function CreateTaskDialog({
  taskTypes,
  priorities,
  onCreated,
  onClose,
}: {
  taskTypes: TaskTypeOption[]
  priorities: TaskPriorityOption[]
  onCreated: (task: TaskResponse) => void
  onClose: () => void
}) {
  const [title, setTitle] = useState("")
  const [desc, setDesc] = useState("")
  const [typeCode, setTypeCode] = useState(taskTypes[0]?.code ?? "")
  const [priorityCode, setPriorityCode] = useState(priorities[0]?.code ?? "")
  const [dueDate, setDueDate] = useState("")
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setError(null)
    try {
      const payload: CreateTaskRequest = {
        title,
        description: desc || undefined,
        task_type_code: typeCode,
        priority_code: priorityCode,
        org_id: "",
        due_date: dueDate || undefined,
      }
      const created = await createTask(payload)
      onCreated(created)
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
          <DialogTitle>Create Task</DialogTitle>
          <DialogDescription>Create a new task for tracking GRC activities and remediation actions.</DialogDescription>
        </DialogHeader>

        {error && (
          <div className="text-xs text-destructive bg-destructive/10 rounded-lg px-3 py-2">{error}</div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label className="text-xs text-muted-foreground mb-1 block">Title <span className="text-destructive">*</span></Label>
            <Input value={title} onChange={e => setTitle(e.target.value)} placeholder="e.g. Review access control policy" required className="h-8 text-sm" />
          </div>

          <div>
            <Label className="text-xs text-muted-foreground mb-1 block">Description</Label>
            <Input value={desc} onChange={e => setDesc(e.target.value)} placeholder="Describe the task details" className="h-8 text-sm" />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label className="text-xs text-muted-foreground mb-1 block">Type <span className="text-destructive">*</span></Label>
              <select
                value={typeCode}
                onChange={e => setTypeCode(e.target.value)}
                className="w-full h-8 px-2 rounded border border-border bg-background text-sm focus:outline-none focus:ring-1 focus:ring-primary"
                required
              >
                {taskTypes.map(t => <option key={t.code} value={t.code}>{t.name}</option>)}
              </select>
            </div>
            <div>
              <Label className="text-xs text-muted-foreground mb-1 block">Priority <span className="text-destructive">*</span></Label>
              <select
                value={priorityCode}
                onChange={e => setPriorityCode(e.target.value)}
                className="w-full h-8 px-2 rounded border border-border bg-background text-sm focus:outline-none focus:ring-1 focus:ring-primary"
                required
              >
                {priorities.map(p => <option key={p.code} value={p.code}>{p.name}</option>)}
              </select>
            </div>
          </div>

          <div>
            <Label className="text-xs text-muted-foreground mb-1 block">Due Date</Label>
            <Input type="date" value={dueDate} onChange={e => setDueDate(e.target.value)} className="h-8 text-sm" />
          </div>

          <DialogFooter>
            <Button type="button" variant="ghost" onClick={onClose} className="h-9 px-4">Cancel</Button>
            <Button type="submit" disabled={saving} className="h-9">
              {saving ? "Creating..." : "Create Task"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

// -- Active filter chip -------------------------------------------------------

function FilterChip({ label, onRemove }: { label: string; onRemove: () => void }) {
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-primary/10 border border-primary/20 text-xs text-primary font-medium">
      {label}
      <button type="button" onClick={onRemove} className="ml-0.5 hover:text-primary/70">
        <X className="w-3 h-3" />
      </button>
    </span>
  )
}

// -- Main Page ----------------------------------------------------------------

export default function AdminTasksPage() {
  const [tasks, setTasks] = useState<TaskResponse[]>([])
  const [taskTypes, setTaskTypes] = useState<TaskTypeOption[]>([])
  const [priorities, setPriorities] = useState<TaskPriorityOption[]>([])
  const [statuses, setStatuses] = useState<TaskStatusOption[]>([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showCreate, setShowCreate] = useState(false)
  const [search, setSearch] = useState("")
  const [filterType, setFilterType] = useState("")
  const [filterStatus, setFilterStatus] = useState("")
  const [filterPriority, setFilterPriority] = useState("")

  const load = useCallback(async (quiet = false) => {
    if (quiet) setRefreshing(true); else setLoading(true)
    setError(null)
    try {
      const [tasksRes, typesRes, priRes, statusRes] = await Promise.all([
        listTasks(),
        listTaskTypes(),
        listTaskPriorities(),
        listTaskStatuses(),
      ])
      setTasks(tasksRes.items ?? tasksRes)
      setTaskTypes(Array.isArray(typesRes) ? typesRes : [])
      setPriorities(Array.isArray(priRes) ? priRes : [])
      setStatuses(Array.isArray(statusRes) ? statusRes : [])
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  const handleCreated = useCallback((task: TaskResponse) => {
    setTasks(prev => [task, ...prev])
  }, [])

  const filtered = tasks.filter(task => {
    if (search.trim()) {
      const q = search.toLowerCase()
      if (!task.title.toLowerCase().includes(q)) return false
    }
    if (filterType && task.task_type_code !== filterType) return false
    if (filterStatus && task.status_code !== filterStatus) return false
    if (filterPriority && task.priority_code !== filterPriority) return false
    return true
  })

  const totalTasks = tasks.length
  const openTasks = tasks.filter(t => !t.is_terminal).length
  const overdueTasks = tasks.filter(t => {
    if (!t.due_date || t.is_terminal) return false
    return new Date(t.due_date) < new Date()
  }).length

  const filterTypeName = taskTypes.find(t => t.code === filterType)?.name ?? filterType
  const filterStatusName = statuses.find(s => s.code === filterStatus)?.name ?? STATUS_META[filterStatus]?.label ?? filterStatus
  const filterPriorityName = priorities.find(p => p.code === filterPriority)?.name ?? PRIORITY_META[filterPriority]?.label ?? filterPriority

  const statCards = [
    { label: "Total Tasks",  value: totalTasks,  icon: CheckSquare },
    { label: "Open Tasks",   value: openTasks,   icon: Clock },
    { label: "Overdue",      value: overdueTasks, icon: AlertTriangle },
  ]

  return (
    <div className="p-6 space-y-6 max-w-5xl">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold">Task Management</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            Track and manage GRC tasks, remediation actions, and compliance activities
          </p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
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
            <Plus className="w-3.5 h-3.5 mr-1" /> Create Task
          </Button>
        </div>
      </div>

      {/* KPI Stat Cards */}
      <div className="grid grid-cols-3 gap-3">
        {statCards.map(s => {
          const borderCls = statBorderCls(s.label)
          const numCls = statNumCls(s.label)
          return (
            <div key={s.label} className={`relative flex items-center gap-3 rounded-xl border border-l-[3px] ${borderCls} bg-card px-4 py-3`}>
              <div className="shrink-0 rounded-lg p-2 bg-muted">
                <s.icon className="w-4 h-4 text-muted-foreground" />
              </div>
              <div className="min-w-0">
                <div className={`text-2xl font-bold tabular-nums leading-none ${numCls}`}>{s.value}</div>
                <span className="text-[11px] text-muted-foreground mt-0.5 block truncate">{s.label}</span>
              </div>
            </div>
          )
        })}
      </div>

      {/* Filter bar */}
      <div className="rounded-xl border border-border bg-card px-4 py-3 space-y-3">
        <div className="flex items-center gap-3 flex-wrap">
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-3 top-2.5 w-4 h-4 text-muted-foreground" />
            <Input
              className="pl-9 h-9"
              placeholder="Search tasks by title..."
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
          </div>
          {taskTypes.length > 0 && (
            <select
              value={filterType}
              onChange={e => setFilterType(e.target.value)}
              className="h-9 px-3 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-1 focus:ring-primary"
            >
              <option value="">All Types</option>
              {taskTypes.map(t => <option key={t.code} value={t.code}>{t.name}</option>)}
            </select>
          )}
          <select
            value={filterStatus}
            onChange={e => setFilterStatus(e.target.value)}
            className="h-9 px-3 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-1 focus:ring-primary"
          >
            <option value="">All Statuses</option>
            {statuses.length > 0
              ? statuses.map(s => <option key={s.code} value={s.code}>{s.name}</option>)
              : Object.entries(STATUS_META).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)
            }
          </select>
          <select
            value={filterPriority}
            onChange={e => setFilterPriority(e.target.value)}
            className="h-9 px-3 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-1 focus:ring-primary"
          >
            <option value="">All Priorities</option>
            {priorities.length > 0
              ? priorities.map(p => <option key={p.code} value={p.code}>{p.name}</option>)
              : Object.entries(PRIORITY_META).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)
            }
          </select>
        </div>

        {/* Active chips */}
        {(search.trim() || filterType || filterStatus || filterPriority) && (
          <div className="flex items-center gap-2 flex-wrap">
            {search.trim() && <FilterChip label={`"${search}"`} onRemove={() => setSearch("")} />}
            {filterType && <FilterChip label={filterTypeName} onRemove={() => setFilterType("")} />}
            {filterStatus && <FilterChip label={filterStatusName} onRemove={() => setFilterStatus("")} />}
            {filterPriority && <FilterChip label={filterPriorityName} onRemove={() => setFilterPriority("")} />}
            <button
              type="button"
              className="text-xs text-muted-foreground hover:text-foreground ml-1"
              onClick={() => { setSearch(""); setFilterType(""); setFilterStatus(""); setFilterPriority("") }}
            >
              Clear all
            </button>
          </div>
        )}
      </div>

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

      {/* List */}
      {!loading && !error && (
        <div className="space-y-2">
          {filtered.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-8">
              {search.trim() || filterType || filterStatus || filterPriority
                ? "No tasks match your filters."
                : "No tasks yet. Create your first task to get started."}
            </p>
          ) : (
            filtered.map(task => <TaskRow key={task.id} task={task} />)
          )}
        </div>
      )}

      {/* Create dialog */}
      {showCreate && (
        <CreateTaskDialog
          taskTypes={taskTypes}
          priorities={priorities}
          onCreated={handleCreated}
          onClose={() => setShowCreate(false)}
        />
      )}
    </div>
  )
}
