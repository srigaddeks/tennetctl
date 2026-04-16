"use client"

import { useEffect, useState, useCallback } from "react"
import { useParams, useRouter } from "next/navigation"
import {
  Card, CardContent, Button, Input, Separator,
} from "@kcontrol/ui"
import {
  ChevronLeft, ChevronRight,
  AlertTriangle, CheckCircle2, Clock, Circle,
  User, Calendar, Tag, FileText, GitMerge,
  History, MessageSquare, Paperclip, Info,
  Pencil, Save, Loader2, ExternalLink,
  ClipboardCheck, Zap, Target, Flag,
  UserPlus, X, Users, Shield, Link2,
} from "lucide-react"
import { CommentsSection } from "@/components/comments/CommentsSection"
import { AttachmentsSection } from "@/components/attachments/AttachmentsSection"
import { EvidenceCheckerPanel } from "@/components/tasks/EvidenceCheckerPanel"
import {
  getTask, updateTask, listTaskEvents, addTaskEvent,
  listAssignments, addAssignment, removeAssignment,
  listTaskControls,
} from "@/lib/api/grc"
import { getAttachmentCount } from "@/lib/api/attachments"
import type {
  TaskResponse, TaskEventResponse, UpdateTaskRequest,
  TaskAssignmentResponse, CreateTaskAssignmentRequest,
  ControlResponse, RiskControlMappingResponse,
} from "@/lib/types/grc"
import { useAccess } from "@/components/providers/AccessProvider"
import { useCopilotEntityNames } from "@/lib/context/CopilotContext"
import { AIEnhancePopover } from "@/components/ai/AIEnhancePopover"

// ── Auth helper ───────────────────────────────────────────────────────────────

function getJwtSubject(): string | null {
  try {
    const token = localStorage.getItem("access_token")
    if (!token) return null
    const payload = JSON.parse(atob(token.split(".")[1]))
    return payload.sub || null
  } catch { return null }
}

// ── Style maps ────────────────────────────────────────────────────────────────

const PRIORITY_COLORS: Record<string, { badge: string; bar: string; glow: string }> = {
  critical: { badge: "bg-red-500/10 text-red-500 border-red-500/30",    bar: "bg-red-500",    glow: "from-red-500/10" },
  high:     { badge: "bg-orange-500/10 text-orange-500 border-orange-500/30", bar: "bg-orange-500", glow: "from-orange-500/10" },
  medium:   { badge: "bg-amber-500/10 text-amber-500 border-amber-500/30",   bar: "bg-amber-500",  glow: "from-amber-500/10" },
  low:      { badge: "bg-green-500/10 text-green-500 border-green-500/30",   bar: "bg-green-500",  glow: "from-green-500/10" },
}

const STATUS_META: Record<string, { badge: string; label: string; dot: string }> = {
  open:                 { badge: "bg-slate-500/10 text-slate-400 border-slate-500/30",    label: "Open",             dot: "bg-slate-400" },
  in_progress:          { badge: "bg-blue-500/10 text-blue-500 border-blue-500/30",       label: "In Progress",      dot: "bg-blue-500" },
  pending_verification: { badge: "bg-purple-500/10 text-purple-500 border-purple-500/30", label: "Pending Review",   dot: "bg-purple-500" },
  resolved:             { badge: "bg-emerald-500/10 text-emerald-500 border-emerald-500/30", label: "Resolved",       dot: "bg-emerald-500" },
  cancelled:            { badge: "bg-gray-500/10 text-gray-400 border-gray-500/30",       label: "Cancelled",        dot: "bg-gray-400" },
  blocked:              { badge: "bg-red-600/10 text-red-600 border-red-600/30",           label: "Blocked",          dot: "bg-red-600" },
}

const TASK_TYPE_META: Record<string, { icon: React.ReactNode; bg: string; label?: string }> = {
  evidence_collection: { icon: <FileText className="w-5 h-5 text-sky-400" />,    bg: "bg-sky-500/10" },
  control_remediation: { icon: <GitMerge className="w-5 h-5 text-orange-400" />, bg: "bg-orange-500/10" },
  risk_treatment:      { icon: <Target className="w-5 h-5 text-purple-400" />,   bg: "bg-purple-500/10" },
  general:             { icon: <ClipboardCheck className="w-5 h-5 text-blue-400" />, bg: "bg-blue-500/10" },
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function formatDate(iso: string | null | undefined): string {
  if (!iso) return "—"
  const d = new Date(iso)
  return d.toLocaleDateString([], { month: "short", day: "numeric", year: "numeric" })
}

function formatRelative(iso: string | null | undefined): string {
  if (!iso) return "—"
  const diff = Date.now() - new Date(iso).getTime()
  if (diff < 60_000) return "just now"
  if (diff < 3_600_000) return `${Math.floor(diff / 60_000)}m ago`
  if (diff < 86_400_000) return `${Math.floor(diff / 3_600_000)}h ago`
  if (diff < 7 * 86_400_000) return `${Math.floor(diff / 86_400_000)}d ago`
  return formatDate(iso)
}

function isOverdue(task: TaskResponse): boolean {
  if (!task.due_date || task.is_terminal) return false
  return new Date(task.due_date) < new Date()
}

function overdueDays(task: TaskResponse): number {
  if (!task.due_date) return 0
  return Math.floor((Date.now() - new Date(task.due_date).getTime()) / 86_400_000)
}

function parseAssigneeEmails(raw: string): { emails: string[]; invalid: string[] } {
  const candidates = raw
    .split(",")
    .map((token) => token.trim().toLowerCase())
    .filter((token) => token.length > 0)
  const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  const seen = new Set<string>()
  const emails: string[] = []
  const invalid: string[] = []
  for (const token of candidates) {
    if (!emailPattern.test(token)) {
      invalid.push(token)
      continue
    }
    if (seen.has(token)) continue
    seen.add(token)
    emails.push(token)
  }
  return { emails, invalid }
}

function Pill({ label, className }: { label: string; className?: string }) {
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-semibold border ${className}`}>
      {label}
    </span>
  )
}

function StatusIcon({ status }: { status: string }) {
  if (status === "resolved")             return <CheckCircle2 className="w-4 h-4 text-emerald-500" />
  if (status === "in_progress")          return <Clock className="w-4 h-4 text-blue-500" />
  if (status === "blocked")              return <AlertTriangle className="w-4 h-4 text-red-600" />
  if (status === "cancelled")            return <Circle className="w-4 h-4 text-gray-400" />
  if (status === "pending_verification") return <Zap className="w-4 h-4 text-purple-500" />
  return <Circle className="w-4 h-4 text-slate-400" />
}

// ── Entity link ───────────────────────────────────────────────────────────────

function EntityLink({ task }: { task: TaskResponse }) {
  const router = useRouter()
  if (!task.entity_type || !task.entity_id) return null
  const label = task.entity_type.replace(/_/g, " ")
  const handleClick = () => {
    if (task.entity_type === "control") {
      // We need framework_id for the control URL, or use a search page
      router.push(`/controls?search=${task.entity_id}`)
    }
    else if (task.entity_type === "risk") router.push(`/risks/${task.entity_id}`)
    else if (task.entity_type === "framework") router.push(`/frameworks/${task.entity_id}`)
  }
  return (
    <button
      type="button"
      onClick={handleClick}
      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-blue-500/20 bg-blue-500/5 text-xs text-blue-400 hover:bg-blue-500/10 transition-colors font-medium"
    >
      <ExternalLink className="w-3 h-3" />
      View linked {label}
    </button>
  )
}

// ── Edit Panel ────────────────────────────────────────────────────────────────

function EditPanel({
  task,
  onSaved,
  onCancel,
}: {
  task: TaskResponse
  onSaved: (updated: TaskResponse) => void
  onCancel: () => void
}) {
  const [form, setForm] = useState({
    title: task.title,
    description: task.description ?? "",
    priority_code: task.priority_code,
    status_code: task.status_code,
    due_date: task.due_date ? task.due_date.split(" ")[0].split("T")[0] : "",
    start_date: task.start_date ? task.start_date.split(" ")[0].split("T")[0] : "",
    estimated_hours: task.estimated_hours?.toString() ?? "",
    actual_hours: task.actual_hours?.toString() ?? "",
    acceptance_criteria: task.acceptance_criteria ?? "",
    resolution_notes: task.resolution_notes ?? "",
    remediation_plan: task.remediation_plan ?? "",
  })
  const [saving, setSaving] = useState(false)
  const [saveError, setSaveError] = useState("")

  async function handleSave(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true); setSaveError("")
    try {
      const payload: UpdateTaskRequest = {
        title: form.title || undefined,
        description: form.description || undefined,
        priority_code: form.priority_code || undefined,
        status_code: form.status_code || undefined,
        due_date: form.due_date || undefined,
        start_date: form.start_date || undefined,
        estimated_hours: form.estimated_hours ? parseFloat(form.estimated_hours) : undefined,
        actual_hours: form.actual_hours ? parseFloat(form.actual_hours) : undefined,
        acceptance_criteria: form.acceptance_criteria || undefined,
        resolution_notes: form.resolution_notes || undefined,
        remediation_plan: form.remediation_plan || undefined,
      }
      const updated = await updateTask(task.id, payload)
      onSaved(updated)
    } catch (err: unknown) {
      setSaveError(err instanceof Error ? err.message : "Failed to save")
    } finally { setSaving(false) }
  }

  return (
    <form onSubmit={handleSave} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div className="col-span-2">
          <label className="text-xs font-semibold text-muted-foreground block mb-1.5">Title</label>
          <Input value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} className="h-9" />
        </div>

        <div className="col-span-2">
          <div className="flex items-center gap-1.5 mb-1.5">
            <label className="text-xs font-semibold text-muted-foreground">Description</label>
            <AIEnhancePopover
              entityType="task"
              entityId={task.id}
              fieldName="description"
              fieldLabel="Description"
              currentValue={form.description}
              orgId={task.org_id ?? null}
              workspaceId={task.workspace_id ?? null}
              entityContext={{ task_title: task.title, task_type: task.task_type_code, priority: task.priority_code }}
              onApply={(v) => setForm(f => ({ ...f, description: v as string }))}
              popoverSide="right"
            />
          </div>
          <textarea value={form.description} onChange={e => setForm({ ...form, description: e.target.value })}
            rows={3} className="w-full rounded-lg border border-input bg-background text-sm px-3 py-2 resize-none focus:outline-none focus:ring-2 focus:ring-ring" />
        </div>

        <div>
          <label className="text-xs font-semibold text-muted-foreground block mb-1.5">Priority</label>
          <select value={form.priority_code} onChange={e => setForm({ ...form, priority_code: e.target.value })}
            className="w-full h-9 rounded-lg border border-input bg-background text-sm px-3 focus:outline-none focus:ring-2 focus:ring-ring">
            {["critical","high","medium","low"].map(p => <option key={p} value={p}>{p}</option>)}
          </select>
        </div>
        <div>
          <label className="text-xs font-semibold text-muted-foreground block mb-1.5">Status</label>
          <select value={form.status_code} onChange={e => setForm({ ...form, status_code: e.target.value })}
            className="w-full h-9 rounded-lg border border-input bg-background text-sm px-3 focus:outline-none focus:ring-2 focus:ring-ring">
            {["open","in_progress","pending_verification","resolved","cancelled","blocked"].map(s => (
              <option key={s} value={s}>{s.replace(/_/g, " ")}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="text-xs font-semibold text-muted-foreground block mb-1.5">Start Date</label>
          <Input type="date" value={form.start_date} onChange={e => setForm({ ...form, start_date: e.target.value })} className="h-9" />
        </div>
        <div>
          <label className="text-xs font-semibold text-muted-foreground block mb-1.5">Due Date</label>
          <Input type="date" value={form.due_date} onChange={e => setForm({ ...form, due_date: e.target.value })} className="h-9" />
        </div>

        <div>
          <label className="text-xs font-semibold text-muted-foreground block mb-1.5">Est. Hours</label>
          <Input type="number" value={form.estimated_hours} onChange={e => setForm({ ...form, estimated_hours: e.target.value })} className="h-9" />
        </div>
        <div>
          <label className="text-xs font-semibold text-muted-foreground block mb-1.5">Actual Hours</label>
          <Input type="number" value={form.actual_hours} onChange={e => setForm({ ...form, actual_hours: e.target.value })} className="h-9" />
        </div>

        <div className="col-span-2">
          <div className="flex items-center gap-1.5 mb-1.5">
            <label className="text-xs font-semibold text-muted-foreground">Acceptance Criteria</label>
            <AIEnhancePopover
              entityType="task"
              entityId={task.id}
              fieldName="acceptance_criteria"
              fieldLabel="Acceptance Criteria"
              currentValue={form.acceptance_criteria}
              orgId={task.org_id ?? null}
              workspaceId={task.workspace_id ?? null}
              entityContext={{ task_title: task.title, task_type: task.task_type_code, priority: task.priority_code }}
              onApply={(v) => setForm(f => ({ ...f, acceptance_criteria: v as string }))}
              popoverSide="right"
            />
          </div>
          <textarea value={form.acceptance_criteria} onChange={e => setForm({ ...form, acceptance_criteria: e.target.value })}
            rows={3} className="w-full rounded-lg border border-input bg-background text-sm px-3 py-2 resize-none focus:outline-none focus:ring-2 focus:ring-ring" />
        </div>

        <div className="col-span-2">
          <div className="flex items-center gap-1.5 mb-1.5">
            <label className="text-xs font-semibold text-muted-foreground">Remediation Plan</label>
            <AIEnhancePopover
              entityType="task"
              entityId={task.id}
              fieldName="remediation_plan"
              fieldLabel="Remediation Plan"
              currentValue={form.remediation_plan}
              orgId={task.org_id ?? null}
              workspaceId={task.workspace_id ?? null}
              entityContext={{ task_title: task.title, task_type: task.task_type_code, priority: task.priority_code }}
              onApply={(v) => setForm(f => ({ ...f, remediation_plan: v as string }))}
              popoverSide="right"
            />
          </div>
          <textarea value={form.remediation_plan} onChange={e => setForm({ ...form, remediation_plan: e.target.value })}
            rows={2} className="w-full rounded-lg border border-input bg-background text-sm px-3 py-2 resize-none focus:outline-none focus:ring-2 focus:ring-ring" />
        </div>

        <div className="col-span-2">
          <label className="text-xs font-semibold text-muted-foreground block mb-1.5">Resolution Notes</label>
          <textarea value={form.resolution_notes} onChange={e => setForm({ ...form, resolution_notes: e.target.value })}
            rows={2} className="w-full rounded-lg border border-input bg-background text-sm px-3 py-2 resize-none focus:outline-none focus:ring-2 focus:ring-ring" />
        </div>
      </div>

      {saveError && (
        <div className="rounded-lg bg-red-500/10 border border-red-500/20 px-3 py-2 text-sm text-red-500">
          {saveError}
        </div>
      )}

      <div className="flex items-center gap-2 pt-1">
        <Button type="submit" size="sm" className="gap-1.5" disabled={saving}>
          {saving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />} Save Changes
        </Button>
        <Button type="button" size="sm" variant="ghost" onClick={onCancel}>Cancel</Button>
      </div>
    </form>
  )
}

// ── Timeline Panel ────────────────────────────────────────────────────────────

const EVENT_TYPE_ICONS: Record<string, React.ReactNode> = {
  comment:         <MessageSquare className="w-3.5 h-3.5 text-blue-400" />,
  status_changed:  <Zap className="w-3.5 h-3.5 text-purple-400" />,
  reassigned:      <User className="w-3.5 h-3.5 text-orange-400" />,
  created:         <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />,
  priority_changed:<Flag className="w-3.5 h-3.5 text-amber-400" />,
}

function TimelinePanel({ taskId }: { taskId: string }) {
  const [events, setEvents] = useState<TaskEventResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [comment, setComment] = useState("")
  const [submitting, setSubmitting] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const data = await listTaskEvents(taskId)
      setEvents(data)
    } catch { /* ignore */ }
    finally { setLoading(false) }
  }, [taskId])

  useEffect(() => { load() }, [load])

  async function handleAddComment(e: React.FormEvent) {
    e.preventDefault()
    if (!comment.trim()) return
    setSubmitting(true)
    try {
      await addTaskEvent(taskId, comment.trim())
      setComment("")
      load()
    } catch { /* ignore */ }
    finally { setSubmitting(false) }
  }

  const sorted = [...events].sort((a, b) => new Date(b.occurred_at).getTime() - new Date(a.occurred_at).getTime())

  return (
    <div className="space-y-5">
      {/* Add comment */}
      <form onSubmit={handleAddComment} className="space-y-2">
        <textarea
          value={comment}
          onChange={e => setComment(e.target.value)}
          placeholder="Add a comment or update…"
          rows={2}
          className="w-full rounded-lg border border-border bg-background text-sm px-3 py-2 resize-none focus:outline-none focus:ring-2 focus:ring-ring"
        />
        <Button type="submit" size="sm" className="gap-1.5" disabled={submitting || !comment.trim()}>
          {submitting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <MessageSquare className="w-3.5 h-3.5" />}
          Post Comment
        </Button>
      </form>

      {loading ? (
        <div className="space-y-3">
          {[1,2,3].map(i => <div key={i} className="h-12 rounded-lg bg-muted animate-pulse" />)}
        </div>
      ) : sorted.length === 0 ? (
        <div className="text-center py-10 text-muted-foreground/60">
          <History className="w-8 h-8 mx-auto mb-2 opacity-40" />
          <p className="text-sm">No activity yet</p>
        </div>
      ) : (
        <div className="relative pl-5">
          {/* Vertical line */}
          <div className="absolute left-2 top-2 bottom-2 w-px bg-border/60" />
          <div className="space-y-4">
            {sorted.map((event) => {
              const icon = EVENT_TYPE_ICONS[event.event_type] ?? <Clock className="w-3.5 h-3.5 text-muted-foreground" />
              return (
                <div key={event.id} className="relative flex gap-3">
                  {/* Timeline dot with icon */}
                  <div className="absolute -left-3 top-0.5 w-6 h-6 rounded-full bg-background border-2 border-border flex items-center justify-center shrink-0">
                    {icon}
                  </div>
                  <div className="flex-1 pl-4 min-w-0 pb-1">
                    {event.event_type === "comment" ? (
                      <div className="rounded-xl border border-border/60 bg-muted/30 p-3">
                        <p className="text-sm text-foreground leading-relaxed">{event.comment}</p>
                      </div>
                    ) : (
                      <div className="rounded-lg border border-border/40 bg-background/50 px-3 py-2">
                        <p className="text-sm text-foreground font-medium capitalize">
                          {event.event_type.replace(/_/g, " ")}
                        </p>
                        {event.old_value && event.new_value && (
                          <p className="text-xs text-muted-foreground mt-0.5">
                            <span className="line-through opacity-60">{event.old_value}</span>
                            <span className="mx-1.5">→</span>
                            <span className="text-foreground font-medium">{event.new_value}</span>
                          </p>
                        )}
                      </div>
                    )}
                    <p className="text-[10px] text-muted-foreground/60 mt-1 pl-1">
                      {formatRelative(event.occurred_at)}
                    </p>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}

// ── Acceptance Criteria Checklist ─────────────────────────────────────────────

function CriteriaChecklist({ text }: { text: string }) {
  const lines = text.split("\n").filter(l => l.trim().length > 0)
  const [checked, setChecked] = useState<Set<number>>(new Set())
  const progress = lines.length > 0 ? Math.round((checked.size / lines.length) * 100) : 0
  const circumference = 2 * Math.PI * 20

  if (lines.length === 0) return <p className="text-sm text-muted-foreground">No acceptance criteria defined.</p>

  return (
    <div className="space-y-3">
      {/* Progress ring + bar */}
      <div className="flex items-center gap-4 p-3 rounded-xl bg-muted/30 border border-border/50">
        <svg className="w-14 h-14 -rotate-90 shrink-0" viewBox="0 0 48 48">
          <circle cx="24" cy="24" r="20" fill="none" stroke="currentColor" strokeWidth="4" className="text-border" />
          <circle
            cx="24" cy="24" r="20" fill="none" stroke="currentColor" strokeWidth="4"
            className="text-emerald-500 transition-all duration-500"
            strokeDasharray={circumference}
            strokeDashoffset={circumference * (1 - progress / 100)}
            strokeLinecap="round"
          />
        </svg>
        <div className="flex-1 min-w-0">
          <div className="flex items-baseline gap-1.5">
            <span className="text-2xl font-bold tabular-nums text-foreground">{checked.size}</span>
            <span className="text-sm text-muted-foreground">/ {lines.length} complete</span>
          </div>
          <div className="w-full bg-muted rounded-full h-1.5 mt-2">
            <div
              className="bg-emerald-500 h-1.5 rounded-full transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
          <p className="text-xs text-muted-foreground mt-1">{progress}% done</p>
        </div>
      </div>

      {/* Items */}
      <div className="space-y-1.5">
        {lines.map((line, i) => {
          const isChecked = checked.has(i)
          return (
            <div
              key={i}
              className={`flex items-start gap-3 p-3 rounded-lg cursor-pointer group transition-all
                ${isChecked ? "bg-emerald-500/5 border border-emerald-500/20" : "hover:bg-muted/40 border border-transparent"}`}
              onClick={() => setChecked(prev => {
                const next = new Set(prev)
                if (isChecked) next.delete(i)
                else next.add(i)
                return next
              })}
            >
              <div className={`mt-0.5 shrink-0 w-5 h-5 rounded-full border-2 flex items-center justify-center transition-all duration-200
                ${isChecked ? "bg-emerald-500 border-emerald-500" : "border-border group-hover:border-emerald-400"}`}>
                {isChecked && (
                  <svg className="w-3 h-3 text-white" viewBox="0 0 12 12" fill="none">
                    <path d="M2 6l3 3 5-5" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                )}
              </div>
              <span className={`text-sm leading-snug transition-colors ${isChecked ? "line-through text-muted-foreground/50" : "text-foreground"}`}>
                {line}
              </span>
            </div>
          )
        })}
      </div>

      {/* AI placeholder */}
      <div className="rounded-xl border border-dashed border-purple-500/30 bg-purple-500/5 p-3 flex items-center justify-between">
        <div>
          <p className="text-xs font-semibold text-purple-400">AI JUSTIFICATION READY</p>
          <p className="text-[11px] text-muted-foreground mt-0.5">Automatically verify criteria against evidence</p>
        </div>
        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold border border-purple-500/30 bg-purple-500/10 text-purple-400">
          Coming Soon
        </span>
      </div>
    </div>
  )
}

// ── Assignees Panel ───────────────────────────────────────────────────────────

const ROLE_LABELS: Record<string, { label: string; badge: string }> = {
  co_assignee: { label: "Co-assignee", badge: "bg-blue-500/10 text-blue-400 border-blue-500/20" },
  reviewer:    { label: "Reviewer",    badge: "bg-purple-500/10 text-purple-400 border-purple-500/20" },
  observer:    { label: "Observer",    badge: "bg-slate-500/10 text-slate-400 border-slate-500/20" },
}

function AssigneesPanel({ taskId }: { taskId: string }) {
  const [assignments, setAssignments] = useState<TaskAssignmentResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [showAdd, setShowAdd] = useState(false)
  const [addAssigneeInput, setAddAssigneeInput] = useState("")
  const [addRole, setAddRole] = useState<string>("co_assignee")
  const [adding, setAdding] = useState(false)
  const [addError, setAddError] = useState("")
  const [removingId, setRemovingId] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const data = await listAssignments(taskId)
      setAssignments(data)
    } catch { /* ignore */ }
    finally { setLoading(false) }
  }, [taskId])

  useEffect(() => { load() }, [load])

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault()
    if (!addAssigneeInput.trim()) return
    const parsed = parseAssigneeEmails(addAssigneeInput)
    if (parsed.invalid.length > 0) {
      setAddError(`Invalid email(s): ${parsed.invalid.join(", ")}`)
      return
    }
    if (parsed.emails.length === 0) return
    setAdding(true); setAddError("")
    try {
      await Promise.all(
        parsed.emails.map((email) => {
          const payload: CreateTaskAssignmentRequest = { email, role: addRole }
          return addAssignment(taskId, payload)
        }),
      )
      setAddAssigneeInput(""); setShowAdd(false)
      load()
    } catch (err: unknown) {
      setAddError(err instanceof Error ? err.message : "Failed to add assignee")
    } finally { setAdding(false) }
  }

  async function handleRemove(assignmentId: string) {
    setRemovingId(assignmentId)
    try {
      await removeAssignment(taskId, assignmentId)
      load()
    } catch { /* ignore */ }
    finally { setRemovingId(null) }
  }

  return (
    <div className="space-y-3">
      {loading ? (
        <div className="space-y-2">
          {[1, 2].map(i => <div key={i} className="h-8 rounded-lg bg-muted animate-pulse" />)}
        </div>
      ) : assignments.length === 0 && !showAdd ? (
        <p className="text-xs text-muted-foreground/60">No additional assignees.</p>
      ) : (
        <div className="space-y-1.5">
          {assignments.map((a) => {
            const rm = ROLE_LABELS[a.role] ?? { label: a.role, badge: "bg-muted text-muted-foreground border-border" }
            return (
              <div key={a.id} className="flex items-center gap-2 group">
                <div className="w-6 h-6 rounded-full bg-muted flex items-center justify-center shrink-0">
                  <User className="w-3 h-3 text-muted-foreground" />
                </div>
                <span className="font-mono text-[11px] text-foreground flex-1 truncate">{a.user_id.slice(0, 8)}…</span>
                <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold border ${rm.badge}`}>
                  {rm.label}
                </span>
                <button
                  type="button"
                  onClick={() => handleRemove(a.id)}
                  disabled={removingId === a.id}
                  className="opacity-0 group-hover:opacity-100 transition-opacity p-0.5 rounded hover:bg-red-500/10 text-muted-foreground hover:text-red-400"
                >
                  {removingId === a.id ? <Loader2 className="w-3 h-3 animate-spin" /> : <X className="w-3 h-3" />}
                </button>
              </div>
            )
          })}
        </div>
      )}

      {showAdd ? (
        <form onSubmit={handleAdd} className="space-y-2 pt-1">
          <input
            value={addAssigneeInput}
            onChange={e => setAddAssigneeInput(e.target.value)}
            placeholder="alice@company.com, bob@company.com"
            className="w-full h-8 rounded-lg border border-input bg-background text-xs px-2.5 focus:outline-none focus:ring-2 focus:ring-ring"
          />
          <select
            value={addRole}
            onChange={e => setAddRole(e.target.value)}
            className="w-full h-8 rounded-lg border border-input bg-background text-xs px-2.5 focus:outline-none focus:ring-2 focus:ring-ring"
          >
            <option value="co_assignee">Co-assignee</option>
            <option value="reviewer">Reviewer</option>
            <option value="observer">Observer</option>
          </select>
          {addError && <p className="text-[11px] text-red-500">{addError}</p>}
          <div className="flex items-center gap-1.5">
            <button
              type="submit"
              disabled={adding || !addAssigneeInput.trim()}
              className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-primary text-primary-foreground text-[11px] font-semibold disabled:opacity-50"
            >
              {adding ? <Loader2 className="w-3 h-3 animate-spin" /> : <UserPlus className="w-3 h-3" />}
              Add
            </button>
            <button
              type="button"
              onClick={() => { setShowAdd(false); setAddAssigneeInput(""); setAddError("") }}
              className="px-2.5 py-1 rounded-lg text-[11px] text-muted-foreground hover:text-foreground transition-colors"
            >
              Cancel
            </button>
          </div>
        </form>
      ) : (
        <button
          type="button"
          onClick={() => setShowAdd(true)}
          className="flex items-center gap-1.5 text-[11px] text-muted-foreground hover:text-foreground transition-colors pt-0.5"
        >
          <UserPlus className="w-3 h-3" />
          Add assignee
        </button>
      )}
    </div>
  )
}

// ── Linked Controls Panel ───────────────────────────────────────────────────

const CONTROL_TYPE_COLORS_UI: Record<string, string> = {
  preventive:   "bg-blue-500/10 text-blue-500 border-blue-500/30",
  detective:    "bg-purple-500/10 text-purple-500 border-purple-500/30",
  corrective:   "bg-amber-500/10 text-amber-600 border-amber-500/30",
  compensating: "bg-teal-500/10 text-teal-500 border-teal-500/30",
}

const CRITICALITY_COLORS_UI: Record<string, string> = {
  critical: "bg-red-500/10 text-red-500 border-red-500/30",
  high:     "bg-orange-500/10 text-orange-500 border-orange-500/30",
  medium:   "bg-yellow-500/10 text-yellow-600 border-yellow-500/30",
  low:      "bg-green-500/10 text-green-500 border-green-500/30",
}

function LinkedControlsPanel({ task }: { task: TaskResponse }) {
  const router = useRouter()
  const [controls, setControls] = useState<ControlResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadData = useCallback(async () => {
    if (!task.id) {
      setLoading(false)
      return
    }

    setLoading(true)
    setError(null)

    try {
      const ctrls = await listTaskControls(task.id)
      setControls(ctrls)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load linked controls")
    } finally {
      setLoading(false)
    }
  }, [task.id])

  useEffect(() => {
    loadData()
  }, [loadData])

  if (loading) {
    return (
      <div className="space-y-4 py-4">
        {[1, 2].map(i => (
          <div key={i} className="h-40 w-full rounded-2xl bg-muted/30 animate-pulse border border-border/50" />
        ))}
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center gap-2 p-4 rounded-xl border border-destructive/20 bg-destructive/10 text-destructive text-sm">
        <AlertTriangle className="w-4 h-4" /> {error}
      </div>
    )
  }

  if (controls.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center space-y-4 rounded-2xl border-2 border-dashed border-muted">
        <div className="p-4 rounded-full bg-muted/50">
          <Shield className="w-8 h-8 text-muted-foreground opacity-30" />
        </div>
        <div>
          <p className="text-sm font-semibold text-muted-foreground">No linked controls found</p>
          <p className="text-xs text-muted-foreground/60 max-w-[240px] mt-1">
            This task is not directly linked to a control, or the linked risk has no controls.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4 py-4 animate-in fade-in slide-in-from-bottom-2 duration-500">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-xs font-bold uppercase tracking-widest text-muted-foreground">
          {controls.length === 1 ? "1 Associated Control" : `${controls.length} Associated Controls`}
        </h3>
      </div>
      
      {controls.map(control => (
        <Card key={control.id} className="group overflow-hidden rounded-2xl border-border/40 bg-card hover:border-primary/20 hover:shadow-lg transition-all duration-300">
          <CardContent className="p-0">
            <div className="flex flex-col sm:flex-row">
              {/* Left sidebar info */}
              <div className="sm:w-32 bg-muted/20 border-r border-border/40 p-4 flex flex-col gap-3 shrink-0">
                <div className="font-mono text-[10px] text-muted-foreground bg-background/50 border border-border/50 px-2 py-1 rounded text-center">
                  {control.control_code}
                </div>
                <div className="space-y-2">
                  <div className={`text-[9px] font-bold uppercase tracking-tight text-center px-1.5 py-0.5 rounded-full border ${CONTROL_TYPE_COLORS_UI[control.control_type] ?? "bg-muted text-muted-foreground border-border"}`}>
                    {control.control_type?.replace(/_/g, " ") ?? "Unknown"}
                  </div>
                  <div className={`text-[9px] font-bold uppercase tracking-tight text-center px-1.5 py-0.5 rounded-full border ${CRITICALITY_COLORS_UI[(control as any).criticality_code] ?? "bg-muted text-muted-foreground border-border"}`}>
                    {(control as any).criticality_code ?? "Medium"}
                  </div>
                </div>
              </div>

              {/* Main content */}
              <div className="flex-1 p-5 space-y-3">
                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                  <div className="space-y-1">
                    <h4 className="text-base font-bold text-foreground group-hover:text-primary transition-colors leading-tight">
                      {control.name}
                    </h4>
                    <div className="flex items-center gap-2 flex-wrap text-[10px] text-muted-foreground">
                      <span className="flex items-center gap-1">
                        <Tag className="w-3 h-3" /> {control.category_name}
                      </span>
                      <span className="opacity-30">•</span>
                      <span className="flex items-center gap-1 font-medium text-foreground/70">
                        <Link2 className="w-3 h-3 text-primary" /> {control.framework_name}
                      </span>
                    </div>
                  </div>
                  <Button 
                    size="sm" 
                    variant="outline" 
                    className="h-8 rounded-xl px-4 gap-2 border-border group-hover:border-primary/30 group-hover:bg-primary/5 shadow-sm transition-all"
                    onClick={() => router.push(`/controls/${control.framework_id}/${control.id}`)}
                  >
                    <ExternalLink className="w-3.5 h-3.5" /> View Detail
                  </Button>
                </div>

                <Separator className="bg-border/40" />

                <div className="text-sm text-foreground/80 leading-relaxed line-clamp-2 italic">
                  {control.description || "No description provided."}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}

// ── Page ──────────────────────────────────────────────────────────────────────

type DetailTab = "details" | "comments" | "attachments" | "timeline" | "linked_control"

export default function TaskDetailPage() {
  const { taskId } = useParams<{ taskId: string }>()
  const router = useRouter()
  const { isWorkspaceAdmin } = useAccess()
  const currentUserId = typeof window !== "undefined" ? (getJwtSubject() ?? "") : ""

  const [task, setTask] = useState<TaskResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<DetailTab>("details")
  const [editing, setEditing] = useState(false)
  // Track attachment count so EvidenceCheckerPanel knows when to show the empty state
  const [attachmentCount, setAttachmentCount] = useState(0)

  // Register human-readable names so copilot never shows raw UUIDs
  useCopilotEntityNames({ task_title: task?.title ?? undefined })

  const load = useCallback(async () => {
    if (!taskId) return
    setLoading(true); setError(null)
    try {
      const [t, cnt] = await Promise.all([
        getTask(taskId),
        getAttachmentCount("task", taskId),
      ])
      setTask(t)
      setAttachmentCount(cnt)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load task")
    } finally { setLoading(false) }
  }, [taskId])

  const refreshAttachmentCount = useCallback(async () => {
    if (!taskId) return
    try {
      const cnt = await getAttachmentCount("task", taskId)
      setAttachmentCount(cnt)
    } catch { /* ignore */ }
  }, [taskId])

  useEffect(() => { load() }, [load])

  const TABS: { id: DetailTab; label: string; icon: React.ReactNode }[] = [
    { id: "details",     label: "Details",     icon: <Info className="w-3.5 h-3.5" /> },
    { id: "linked_control", label: "Linked Control", icon: <Shield className="w-3.5 h-3.5" /> },
    { id: "timeline",    label: "Timeline",    icon: <History className="w-3.5 h-3.5" /> },
    { id: "comments",    label: "Comments",    icon: <MessageSquare className="w-3.5 h-3.5" /> },
    { id: "attachments", label: "Attachments", icon: <Paperclip className="w-3.5 h-3.5" /> },
  ]

  if (loading) {
    return (
      <div className="p-6 space-y-4 max-w-screen-xl mx-auto">
        <div className="h-6 w-40 rounded-lg bg-muted animate-pulse" />
        <div className="h-40 rounded-2xl bg-muted animate-pulse" />
        <div className="grid grid-cols-3 gap-5">
          <div className="col-span-2 h-80 rounded-2xl bg-muted animate-pulse" />
          <div className="h-80 rounded-2xl bg-muted animate-pulse" />
        </div>
      </div>
    )
  }

  if (error || !task) {
    return (
      <div className="flex flex-col items-center justify-center py-24 gap-4">
        <div className="w-16 h-16 rounded-2xl bg-red-500/10 flex items-center justify-center">
          <AlertTriangle className="h-8 w-8 text-red-400" />
        </div>
        <div className="text-center">
          <p className="font-semibold text-foreground">Task not found</p>
          <p className="text-sm text-muted-foreground mt-1">{error ?? "This task may have been deleted."}</p>
        </div>
        <Button variant="outline" size="sm" onClick={() => router.back()}>
          <ChevronLeft className="h-3.5 w-3.5 mr-1" /> Go back
        </Button>
      </div>
    )
  }

  const overdue = isOverdue(task)
  const pm = PRIORITY_COLORS[task.priority_code] ?? { badge: "bg-muted text-muted-foreground border-border", bar: "bg-muted", glow: "from-muted/20" }
  const sm = STATUS_META[task.status_code] ?? { badge: "bg-muted text-muted-foreground border-border", label: task.status_code, dot: "bg-muted-foreground" }
  const tm = TASK_TYPE_META[task.task_type_code] ?? { icon: <ClipboardCheck className="w-5 h-5 text-muted-foreground" />, bg: "bg-muted" }

  return (
    <div className="flex flex-col gap-5 p-6 max-w-screen-xl mx-auto">

      {/* Breadcrumb nav */}
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div className="flex items-center gap-2 text-sm">
          <button
            type="button"
            onClick={() => router.back()}
            className="text-muted-foreground hover:text-foreground transition-colors flex items-center gap-1"
          >
            <ChevronLeft className="h-3.5 w-3.5" />
            Back
          </button>
          <ChevronRight className="h-3.5 w-3.5 text-muted-foreground/40" />
          <span className="text-foreground font-medium truncate max-w-[280px]">{task.title}</span>
        </div>
        <div className="flex items-center gap-2">
          {!editing && (
            <Button size="sm" variant="outline" className="gap-1.5" onClick={() => setEditing(true)}>
              <Pencil className="h-3.5 w-3.5" /> Edit
            </Button>
          )}
        </div>
      </div>

      {/* Hero header card */}
      <Card className="rounded-2xl overflow-hidden border-0 shadow-lg">
        {/* Priority-colored top bar */}
        <div className={`h-1.5 w-full ${pm.bar}`} />
        {/* Subtle gradient bg */}
        <div className={`bg-gradient-to-br ${pm.glow} to-transparent`}>
          <CardContent className="pt-5 pb-5 px-6">
            <div className="flex flex-col lg:flex-row gap-5 lg:items-start lg:justify-between">

              {/* Left: icon + title + description */}
              <div className="flex gap-4 flex-1 min-w-0">
                <div className={`w-12 h-12 rounded-xl flex items-center justify-center shrink-0 ${tm.bg}`}>
                  {tm.icon}
                </div>
                <div className="min-w-0">
                  <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1">
                    {task.task_type_name}
                  </p>
                  <h1 className="text-xl font-bold tracking-tight text-foreground leading-snug">{task.title}</h1>
                  {task.description && (
                    <p className="text-sm text-muted-foreground leading-relaxed mt-2 max-w-2xl">{task.description}</p>
                  )}

                  {/* Meta row */}
                  <div className="flex items-center gap-3 flex-wrap mt-3 text-xs text-muted-foreground">
                    {task.assignee_user_id && (
                      <span className="flex items-center gap-1.5">
                        <div className="w-5 h-5 rounded-full bg-muted flex items-center justify-center">
                          <User className="w-3 h-3" />
                        </div>
                        <span className="font-mono">{task.assignee_user_id.slice(0, 8)}…</span>
                      </span>
                    )}
                    {task.due_date && (
                      <span className={`flex items-center gap-1 ${overdue ? "text-red-500 font-semibold" : ""}`}>
                        <Calendar className={`w-3.5 h-3.5 ${overdue ? "text-red-500" : ""}`} />
                        {overdue ? `${overdueDays(task)}d overdue · ` : "Due "}
                        {formatDate(task.due_date)}
                      </span>
                    )}
                    {task.start_date && (
                      <span className="flex items-center gap-1">
                        <Flag className="w-3.5 h-3.5" />
                        Started {formatDate(task.start_date)}
                      </span>
                    )}
                    {(task.estimated_hours != null || task.actual_hours != null) && (
                      <span className="flex items-center gap-1">
                        <Clock className="w-3.5 h-3.5" />
                        {task.actual_hours != null ? `${task.actual_hours}h actual` : ""}
                        {task.estimated_hours != null ? ` / ${task.estimated_hours}h est` : ""}
                      </span>
                    )}
                  </div>
                </div>
              </div>

              {/* Right: status + priority + badges */}
              <div className="flex flex-row lg:flex-col items-start lg:items-end gap-2 shrink-0 flex-wrap">
                {/* Status badge — large hero pill */}
                <div className={`flex items-center gap-2 px-4 py-2 rounded-xl border-2 ${sm.badge}`}>
                  <span className={`w-2 h-2 rounded-full shrink-0 ${sm.dot}`} />
                  <span className="font-bold text-sm tracking-wide">{sm.label}</span>
                </div>

                <Pill
                  label={task.priority_code.charAt(0).toUpperCase() + task.priority_code.slice(1)}
                  className={pm.badge}
                />

                {overdue && (
                  <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold border border-red-500/30 bg-red-500/10 text-red-500">
                    <AlertTriangle className="w-3 h-3" /> Overdue
                  </span>
                )}

                <span className="font-mono text-[10px] text-muted-foreground border border-border/50 rounded-full px-2 py-0.5">v{task.version}</span>
              </div>
            </div>
          </CardContent>
        </div>
      </Card>

      {/* Tabs bar */}
      <div className="flex items-center gap-0 border-b border-border">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            type="button"
            onClick={() => { setActiveTab(tab.id); setEditing(false) }}
            className={`flex items-center gap-1.5 px-5 py-2.5 text-sm font-medium border-b-2 transition-colors -mb-px
              ${activeTab === tab.id
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground hover:border-border"
              }`}
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab content — two-column on details tab */}
      <div>
        {activeTab === "linked_control" && (
          <LinkedControlsPanel task={task} />
        )}
        {activeTab === "details" && (
          editing ? (
            <Card className="rounded-xl">
              <CardContent className="p-6">
                <h2 className="text-sm font-bold text-foreground mb-4">Edit Task</h2>
                <EditPanel
                  task={task}
                  onSaved={(updated) => { setTask(updated); setEditing(false) }}
                  onCancel={() => setEditing(false)}
                />
              </CardContent>
            </Card>
          ) : (
            <div className="grid lg:grid-cols-3 gap-5">

              {/* Left (2/3): main content */}
              <div className="lg:col-span-2 space-y-5">

                {/* Acceptance Criteria */}
                <Card className="rounded-xl">
                  <CardContent className="p-5">
                    <h2 className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-4 flex items-center gap-2">
                      <ClipboardCheck className="w-3.5 h-3.5" />
                      Acceptance Criteria
                    </h2>
                    {task.acceptance_criteria ? (
                      <CriteriaChecklist text={task.acceptance_criteria} />
                    ) : (
                      <div className="rounded-lg border border-dashed border-border p-4 text-center">
                        <p className="text-sm text-muted-foreground/60">No acceptance criteria defined.</p>
                        <Button size="sm" variant="outline" className="mt-2 gap-1.5" onClick={() => setEditing(true)}>
                          <Pencil className="w-3 w-3" /> Add criteria
                        </Button>
                      </div>
                    )}
                  </CardContent>
                </Card>

                {/* Evidence & AI Analysis — shown for evidence_collection tasks AND any task with acceptance criteria */}
                <Card className="rounded-xl border-purple-500/20">
                  <CardContent className="p-5">
                    <h2 className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-4 flex items-center gap-2">
                      <FileText className="w-3.5 h-3.5 text-purple-400" />
                      Evidence &amp; AI Analysis
                    </h2>
                    <EvidenceCheckerPanel
                      taskId={taskId}
                      attachmentCount={attachmentCount}
                      onGoToAttachments={() => setActiveTab("attachments")}
                    />
                  </CardContent>
                </Card>

                {/* Remediation Plan */}
                {task.task_type_code === "control_remediation" && (
                  <Card className="rounded-xl">
                    <CardContent className="p-5">
                      <h2 className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-3 flex items-center gap-2">
                        <GitMerge className="w-3.5 h-3.5 text-orange-400" />
                        Remediation Plan
                      </h2>
                      {task.remediation_plan ? (
                        <p className="text-sm text-foreground leading-relaxed whitespace-pre-line bg-orange-500/5 border border-orange-500/15 rounded-xl p-4">{task.remediation_plan}</p>
                      ) : (
                        <p className="text-sm text-muted-foreground/60">No remediation plan defined.</p>
                      )}
                    </CardContent>
                  </Card>
                )}

                {/* Resolution Notes */}
                {task.resolution_notes && (
                  <Card className="rounded-xl border-emerald-500/20">
                    <CardContent className="p-5">
                      <h2 className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-3 flex items-center gap-2">
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                        Resolution Notes
                      </h2>
                      <p className="text-sm text-foreground leading-relaxed whitespace-pre-line bg-emerald-500/5 border border-emerald-500/15 rounded-xl p-4">{task.resolution_notes}</p>
                    </CardContent>
                  </Card>
                )}
              </div>

              {/* Right (1/3): properties sidebar */}
              <div className="space-y-5">

                {/* Properties card */}
                <Card className="rounded-xl">
                  <CardContent className="p-5">
                    <h2 className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-4">Properties</h2>
                    <div className="space-y-3">
                      {[
                        { label: "Type", value: <span className="text-xs font-medium">{task.task_type_name}</span> },
                        {
                          label: "Priority",
                          value: <Pill label={task.priority_code.charAt(0).toUpperCase() + task.priority_code.slice(1)} className={pm.badge} />,
                        },
                        {
                          label: "Status",
                          value: <Pill label={sm.label} className={sm.badge} />,
                        },
                        { label: "Version", value: <span className="font-mono text-xs text-muted-foreground">v{task.version}</span> },
                        ...(task.estimated_hours != null ? [{ label: "Est. Hours", value: <span className="text-xs font-medium">{task.estimated_hours}h</span> }] : []),
                        ...(task.actual_hours != null ? [{ label: "Actual Hours", value: <span className="text-xs font-medium">{task.actual_hours}h</span> }] : []),
                        ...(task.start_date ? [{ label: "Start Date", value: <span className="text-xs">{formatDate(task.start_date)}</span> }] : []),
                        ...(task.due_date ? [{
                          label: "Due Date",
                          value: (
                            <div className={`flex items-center gap-1 ${overdue ? "text-red-500" : ""}`}>
                              {overdue && <AlertTriangle className="w-3 h-3" />}
                              <span className="text-xs font-medium">{formatDate(task.due_date)}</span>
                            </div>
                          ),
                        }] : []),
                        ...(task.completed_at ? [{ label: "Completed", value: <span className="text-xs text-emerald-400 font-medium">{formatDate(task.completed_at)}</span> }] : []),
                        ...(task.blocker_count > 0 ? [{ label: "Blockers", value: <span className="text-xs font-bold text-orange-500">{task.blocker_count}</span> }] : []),
                        ...(task.co_assignee_count > 0 ? [{ label: "Co-assignees", value: <span className="text-xs font-medium">{task.co_assignee_count}</span> }] : []),
                      ].map(({ label, value }) => (
                        <div key={label} className="flex items-center justify-between gap-2">
                          <span className="text-xs text-muted-foreground">{label}</span>
                          {value}
                        </div>
                      ))}
                    </div>

                    <Separator className="my-4 opacity-40" />

                    <div className="space-y-1 text-[11px] text-muted-foreground/60">
                      <p>Created {formatRelative(task.created_at)}</p>
                      {task.updated_at !== task.created_at && (
                        <p>Updated {formatRelative(task.updated_at)}</p>
                      )}
                    </div>
                  </CardContent>
                </Card>

                {/* Assignees card */}
                <Card className="rounded-xl">
                  <CardContent className="p-5">
                    <h2 className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-4 flex items-center gap-2">
                      <Users className="w-3.5 h-3.5" />
                      Assignees
                    </h2>
                    <AssigneesPanel taskId={taskId} />
                  </CardContent>
                </Card>

                {/* Entity link card */}
                {task.entity_type && (
                  <Card className="rounded-xl border-blue-500/15">
                    <CardContent className="p-5">
                      <h2 className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-3">Linked Entity</h2>
                      <div className="flex flex-col gap-2">
                        <div className="flex items-center gap-2">
                          <Tag className="w-3.5 h-3.5 text-blue-400" />
                          <span className="text-sm capitalize font-medium">{task.entity_type.replace(/_/g, " ")}</span>
                        </div>
                        {task.entity_name ? (
                           <p className="text-sm font-bold text-foreground leading-tight px-1">{task.entity_name}</p>
                        ) : task.entity_id && (
                          <p className="font-mono text-[11px] text-muted-foreground bg-muted/50 rounded-lg px-2 py-1.5 break-all">{task.entity_id}</p>
                        )}
                        <EntityLink task={task} />
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Quick actions */}
                <Card className="rounded-xl">
                  <CardContent className="p-5">
                    <h2 className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-3">Actions</h2>
                    <div className="space-y-2">
                      <Button size="sm" variant="outline" className="w-full justify-start gap-2" onClick={() => setEditing(true)}>
                        <Pencil className="w-3.5 h-3.5" /> Edit Task
                      </Button>
                      <Button size="sm" variant="ghost" className="w-full justify-start gap-2 text-muted-foreground" onClick={() => setActiveTab("comments")}>
                        <MessageSquare className="w-3.5 h-3.5" /> Add Comment
                      </Button>
                      <Button size="sm" variant="ghost" className="w-full justify-start gap-2 text-muted-foreground" onClick={() => setActiveTab("attachments")}>
                        <Paperclip className="w-3.5 h-3.5" /> Upload Attachment
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          )
        )}

        {activeTab === "timeline" && (
          <Card className="rounded-xl">
            <CardContent className="p-6">
              <h2 className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-5 flex items-center gap-2">
                <History className="w-3.5 h-3.5" />
                Activity Timeline
              </h2>
              <TimelinePanel taskId={taskId} />
            </CardContent>
          </Card>
        )}

        {activeTab === "comments" && (
          <Card className="rounded-xl">
            <CardContent className="p-6">
              <CommentsSection
                entityType="task"
                entityId={taskId}
                currentUserId={currentUserId}
                isWorkspaceAdmin={isWorkspaceAdmin}
                active={activeTab === "comments"}
              />
            </CardContent>
          </Card>
        )}

        {activeTab === "attachments" && (
          <Card className="rounded-xl">
            <CardContent className="p-6">
              <AttachmentsSection
                entityType="task"
                entityId={taskId}
                currentUserId={currentUserId}
                canUpload
                isWorkspaceAdmin={isWorkspaceAdmin}
                active={activeTab === "attachments"}
                onCountChange={refreshAttachmentCount}
              />
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
