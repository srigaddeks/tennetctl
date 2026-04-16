"use client"

import React, { useEffect, useState, useCallback } from "react"
import { useParams, useRouter } from "next/navigation"
import { Button } from "@kcontrol/ui"
import {
  ChevronLeft, ShieldAlert, Loader2, AlertTriangle,
  ClipboardCheck, FileText, Link2, MessageSquare,
  Wrench, TrendingUp, TrendingDown, CheckCircle2,
  Clock, Circle, CalendarCheck, User2, X, Activity, ShieldCheck, Calendar,
  Plus, ExternalLink
} from "lucide-react"
import { CommentsSection } from "@/components/comments/CommentsSection"
import { AttachmentsSection } from "@/components/attachments/AttachmentsSection"
import {
  getRisk, listRiskControls, listTasks,
  addRiskControl, removeRiskControl,
  listAssessments, createAssessment, getTreatmentPlan,
  listReviewEvents, addReviewEvent, listRiskGroups,
  getReviewSchedule, upsertReviewSchedule, completeReview,
  listAllControls,
} from "@/lib/api/grc"
import { getCommentCount } from "@/lib/api/comments"
import { getAttachmentCount } from "@/lib/api/attachments"
import type {
  RiskResponse, RiskControlMappingResponse, TaskResponse,
  RiskAssessmentResponse, TreatmentPlanResponse, RiskReviewEventResponse,
  RiskGroupAssignmentResponse, ReviewScheduleResponse, ControlResponse,
} from "@/lib/types/grc"
import type { OrgMemberResponse } from "@/lib/types/orgs"
import { useOrgWorkspace } from "@/lib/context/OrgWorkspaceContext"
import { useAccess } from "@/components/providers/AccessProvider"
import { TaskCreateSlideOver } from "@/components/tasks/TaskCreateSlideOver"
import {
  Dialog, DialogContent, DialogHeader, DialogTitle,
  DialogDescription, DialogFooter, Input, Label,
  Card, CardContent
} from "@kcontrol/ui"

// ── Constants ──────────────────────────────────────────────────────────────

const RISK_STATUS_META: Record<string, { label: string; cls: string }> = {
  identified: { label: "Identified", cls: "text-muted-foreground bg-muted border-border" },
  assessed:   { label: "Assessed",   cls: "text-blue-600 bg-blue-500/10 border-blue-500/20" },
  treating:   { label: "Treating",   cls: "text-yellow-600 bg-yellow-500/10 border-yellow-500/20" },
  accepted:   { label: "Accepted",   cls: "text-emerald-600 bg-emerald-500/10 border-emerald-500/20" },
  closed:     { label: "Closed",     cls: "text-slate-500 bg-slate-500/10 border-slate-500/20" },
}

const LEVEL_COLORS: Record<string, { label: string; border: string; badge: string; icon: string }> = {
  critical: { label: "Critical", border: "border-l-red-500",    badge: "bg-red-500/15 text-red-400 border-red-500/30",    icon: "text-red-400" },
  high:     { label: "High",     border: "border-l-orange-500", badge: "bg-orange-500/15 text-orange-400 border-orange-500/30", icon: "text-orange-400" },
  medium:   { label: "Medium",   border: "border-l-amber-500",  badge: "bg-amber-500/15 text-amber-400 border-amber-500/30",  icon: "text-amber-400" },
  low:      { label: "Low",      border: "border-l-green-500",  badge: "bg-green-500/15 text-green-400 border-green-500/30",  icon: "text-green-400" },
}

const TREATMENT_PLAN_STATUS_META: Record<string, { label: string; cls: string }> = {
  draft:     { label: "Draft",     cls: "text-muted-foreground" },
  active:    { label: "Active",    cls: "text-blue-500" },
  completed: { label: "Completed", cls: "text-emerald-500" },
  cancelled: { label: "Cancelled", cls: "text-amber-500" },
}

// ── Helpers ────────────────────────────────────────────────────────────────

function getJwtSubject(): string | null {
  if (typeof window === "undefined") return null
  try {
    const token = localStorage.getItem("access_token")
    if (!token) return null
    const base64Url = token.split(".")[1]
    const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/")
    const pad = base64.length % 4
    const padded = pad ? base64 + "=".repeat(4 - pad) : base64
    const payload = JSON.parse(atob(padded))
    return payload.sub ?? null
  } catch { return null }
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })
}

function StatusBadge({ status }: { status: string }) {
  const meta = RISK_STATUS_META[status] ?? { label: status, cls: "text-muted-foreground bg-muted border-border" }
  return <span className={`inline-flex items-center px-2 py-0.5 rounded-full border text-[10px] font-semibold ${meta.cls}`}>{meta.label}</span>
}

function ScoreBar({ score, max = 25 }: { score: number | null; max?: number }) {
  if (score == null) return <span className="text-xs text-muted-foreground">--</span>
  const pct = Math.min((score / max) * 100, 100)
  const color = score >= 16 ? "#ef4444" : score >= 11 ? "#f97316" : score >= 6 ? "#f59e0b" : "#10b981"
  return (
    <div className="flex flex-col gap-1 w-full">
      <div className="flex items-center justify-between text-[10px]">
        <span className="font-medium" style={{ color }}>{score} / {max}</span>
        <span className="text-muted-foreground">{Math.round(pct)}%</span>
      </div>
      <div className="h-1.5 w-full rounded-full bg-muted overflow-hidden">
        <div className="h-full rounded-full transition-all duration-500" style={{ width: `${pct}%`, backgroundColor: color }} />
      </div>
    </div>
  )
}

function RiskScoreGauge({ score, label, color }: { score: number | null; label: string; color: string }) {
  const max = 25
  const pct = score ? Math.min((score / max) * 100, 100) : 0
  const radius = 36
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (pct / 100) * circumference

  return (
    <div className="flex flex-col items-center gap-2 group">
      <div className="relative h-24 w-24">
        <svg className="h-full w-full rotate-[-90deg]">
          <circle
            cx="48" cy="48" r={radius}
            fill="transparent"
            stroke="currentColor"
            strokeWidth="6"
            className="text-muted/20"
          />
          <circle
            cx="48" cy="48" r={radius}
            fill="transparent"
            stroke={color}
            strokeWidth="6"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
            className="transition-all duration-1000 ease-out"
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center rotate-0">
          <span className="text-xl font-bold">{score ?? "--"}</span>
          <span className="text-[9px] uppercase tracking-wider text-muted-foreground font-bold">/ 25</span>
        </div>
      </div>
      <span className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground group-hover:text-foreground transition-colors">{label}</span>
    </div>
  )
}

function TaskStatusIcon({ status }: { status: string }) {
  if (status === "completed") return <CheckCircle2 className="w-3 h-3 text-green-500" />
  if (status === "in_progress") return <Clock className="w-3 h-3 text-blue-500" />
  if (status === "blocked") return <AlertTriangle className="w-3 h-3 text-red-500" />
  return <Circle className="w-3 h-3 text-muted-foreground" />
}

// ── AddControlDialog ───────────────────────────────────────────────────────

function AddControlDialog({ riskId, orgId, workspaceId, open, onAdded, onClose }: {
  riskId: string; orgId?: string | null; workspaceId?: string | null; open: boolean
  onAdded: () => void; onClose: () => void
}) {
  const [controls, setControls] = useState<ControlResponse[]>([])
  const [search, setSearch] = useState("")
  const [selectedId, setSelectedId] = useState("")
  const [linkType, setLinkType] = useState("mitigating")
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!open) return
    listAllControls({ deployed_org_id: orgId ?? undefined, deployed_workspace_id: workspaceId ?? undefined })
      .then(r => setControls(r.items ?? []))
      .catch(() => {})
  }, [orgId, workspaceId, open])

  const filtered = search
    ? controls.filter(c => c.name?.toLowerCase().includes(search.toLowerCase()) || c.control_code?.toLowerCase().includes(search.toLowerCase()))
    : controls

  const handle = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedId) { setError("Select a control"); return }
    setSaving(true); setError(null)
    try {
      await addRiskControl(riskId, { control_id: selectedId, link_type: linkType })
      onAdded(); onClose()
    } catch (e) { setError((e as Error).message) }
    finally { setSaving(false) }
  }

  return (
    <Dialog open={open} onOpenChange={o => { if (!o) onClose() }}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Link Control</DialogTitle>
          <DialogDescription>Link an existing control to this risk.</DialogDescription>
        </DialogHeader>
        {error && <div className="text-xs text-destructive bg-destructive/10 rounded-lg px-3 py-2">{error}</div>}
        <form onSubmit={handle} className="space-y-4">
          <div>
            <Label className="text-xs text-muted-foreground mb-1 block">Search Controls</Label>
            <Input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search..." className="h-8 text-sm mb-2" />
            <div className="max-h-48 overflow-y-auto border border-border rounded-md divide-y divide-border">
              {filtered.slice(0, 50).map(c => (
                <button key={c.id} type="button"
                  className={`w-full text-left px-3 py-2 text-xs hover:bg-accent transition-colors ${selectedId === c.id ? "bg-accent/50 font-medium" : ""}`}
                  onClick={() => setSelectedId(c.id)}>
                  <span className="font-mono text-muted-foreground mr-2">{c.control_code}</span>{c.name}
                </button>
              ))}
              {filtered.length === 0 && <p className="px-3 py-3 text-xs text-muted-foreground">No controls found.</p>}
            </div>
          </div>
          <div>
            <Label className="text-xs text-muted-foreground mb-1 block">Link Type</Label>
            <select value={linkType} onChange={e => setLinkType(e.target.value)} className="w-full h-8 px-2 rounded border border-input bg-background text-sm">
              <option value="mitigating">Mitigating</option>
              <option value="compensating">Compensating</option>
              <option value="related">Related</option>
            </select>
          </div>
          <DialogFooter>
            <Button type="button" variant="ghost" onClick={onClose} className="h-9 px-4">Cancel</Button>
            <Button type="submit" disabled={saving} className="h-9">{saving ? "Linking..." : "Link Control"}</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

// ── AddReviewDialog ────────────────────────────────────────────────────────

function AddReviewDialog({ riskId, open, onAdded, onClose }: { riskId: string; open: boolean; onAdded: () => void; onClose: () => void }) {
  const [eventType, setEventType] = useState("comment_added")
  const [comment, setComment] = useState("")
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const handle = async (e: React.FormEvent) => {
    e.preventDefault(); setSaving(true); setError(null)
    try { await addReviewEvent(riskId, { event_type: eventType, comment: comment || undefined }); onAdded(); onClose() }
    catch (e) { setError((e as Error).message) } finally { setSaving(false) }
  }
  return (
    <Dialog open={open} onOpenChange={o => { if (!o) onClose() }}>
      <DialogContent className="max-w-sm">
        <DialogHeader><DialogTitle>Add Review Event</DialogTitle><DialogDescription>Record a review comment or event.</DialogDescription></DialogHeader>
        {error && <div className="text-xs text-destructive bg-destructive/10 rounded-lg px-3 py-2">{error}</div>}
        <form onSubmit={handle} className="space-y-4">
          <div>
            <Label className="text-xs text-muted-foreground mb-1 block">Event Type</Label>
            <select value={eventType} onChange={e => setEventType(e.target.value)} className="w-full h-8 px-2 rounded border border-input bg-background text-sm">
              <option value="comment_added">Comment</option>
              <option value="reviewed">Review</option>
              <option value="assessed">Assessment Note</option>
              <option value="treatment_updated">Treatment Update</option>
            </select>
          </div>
          <div>
            <Label className="text-xs text-muted-foreground mb-1 block">Comment</Label>
            <textarea value={comment} onChange={e => setComment(e.target.value)} placeholder="Write your comment..." className="w-full min-h-[60px] px-3 py-2 rounded-md border border-input bg-background text-sm resize-y focus:outline-none focus:ring-1 focus:ring-ring" />
          </div>
          <DialogFooter>
            <Button type="button" variant="ghost" onClick={onClose} className="h-9 px-4">Cancel</Button>
            <Button type="submit" disabled={saving} className="h-9">{saving ? "Adding..." : "Add Event"}</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

// ── ReviewScheduleDialog ───────────────────────────────────────────────────

function ReviewScheduleDialog({ riskId, existing, open, onSaved, onClose }: {
  riskId: string; existing: ReviewScheduleResponse | null; open: boolean; onSaved: () => void; onClose: () => void
}) {
  const [frequency, setFrequency] = useState(existing?.review_frequency ?? "quarterly")
  const [nextDate, setNextDate] = useState(existing?.next_review_date?.split("T")[0] ?? "")
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const handle = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!nextDate) { setError("Next review date is required"); return }
    setSaving(true); setError(null)
    try { await upsertReviewSchedule(riskId, { review_frequency: frequency, next_review_date: nextDate }); onSaved(); onClose() }
    catch (e) { setError((e as Error).message) } finally { setSaving(false) }
  }
  return (
    <Dialog open={open} onOpenChange={o => { if (!o) onClose() }}>
      <DialogContent className="max-w-sm">
        <DialogHeader><DialogTitle>{existing ? "Edit Review Schedule" : "Set Review Schedule"}</DialogTitle><DialogDescription>Configure the review schedule for this risk.</DialogDescription></DialogHeader>
        {error && <div className="text-xs text-destructive bg-destructive/10 rounded-lg px-3 py-2">{error}</div>}
        <form onSubmit={handle} className="space-y-4">
          <div>
            <Label className="text-xs text-muted-foreground mb-1 block">Frequency</Label>
            <select value={frequency} onChange={e => setFrequency(e.target.value)} className="w-full h-8 px-2 rounded border border-input bg-background text-sm">
              <option value="monthly">Monthly</option>
              <option value="quarterly">Quarterly</option>
              <option value="semi_annual">Semi-Annual</option>
              <option value="annual">Annual</option>
            </select>
          </div>
          <div>
            <Label className="text-xs text-muted-foreground mb-1 block">Next Review Date *</Label>
            <Input type="date" value={nextDate} onChange={e => setNextDate(e.target.value)} required className="h-8 text-sm" />
          </div>
          <DialogFooter>
            <Button type="button" variant="ghost" onClick={onClose} className="h-9 px-4">Cancel</Button>
            <Button type="submit" disabled={saving} className="h-9">{saving ? "Saving..." : "Save Schedule"}</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

// ── AssessmentDialog ───────────────────────────────────────────────────────

function AssessmentDialog({ riskId, orgId, workspaceId, open, onCreated, onClose }: {
  riskId: string; orgId?: string | null; workspaceId?: string | null; open: boolean; onCreated: () => void; onClose: () => void
}) {
  const [assessmentType, setAssessmentType] = useState("inherent")
  const [likelihood, setLikelihood] = useState(3)
  const [impact, setImpact] = useState(3)
  const [notes, setNotes] = useState("")
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const computedScore = likelihood * impact
  const handle = async (e: React.FormEvent) => {
    e.preventDefault(); setSaving(true); setError(null)
    try {
      await createAssessment(riskId, { assessment_type: assessmentType, likelihood_score: likelihood, impact_score: impact, assessment_notes: notes || undefined })
      onCreated(); onClose()
    } catch (e) { setError((e as Error).message) } finally { setSaving(false) }
  }
  const LABELS = ["", "Very Low", "Low", "Medium", "High", "Very High"]
  return (
    <Dialog open={open} onOpenChange={o => { if (!o) onClose() }}>
      <DialogContent className="max-w-md">
        <DialogHeader><DialogTitle>New Assessment</DialogTitle><DialogDescription>Create a risk assessment with likelihood and impact scores.</DialogDescription></DialogHeader>
        {error && <div className="text-xs text-destructive bg-destructive/10 rounded-lg px-3 py-2">{error}</div>}
        <form onSubmit={handle} className="space-y-4">
          <div>
            <Label className="text-xs text-muted-foreground mb-1 block">Assessment Type *</Label>
            <select value={assessmentType} onChange={e => setAssessmentType(e.target.value)} className="w-full h-8 px-2 rounded border border-input bg-background text-sm">
              <option value="inherent">Inherent</option>
              <option value="residual">Residual</option>
            </select>
          </div>
          <div className="grid grid-cols-2 gap-4">
            {[{ label: "Likelihood", val: likelihood, set: setLikelihood }, { label: "Impact", val: impact, set: setImpact }].map(({ label, val, set }) => (
              <div key={label}>
                <Label className="text-xs text-muted-foreground mb-1 block">{label} *</Label>
                <div className="flex items-center gap-2 mt-1">
                  <input type="range" min={1} max={5} value={val} onChange={e => set(Number(e.target.value))} className="flex-1 h-2 accent-primary" />
                  <span className="text-sm font-semibold tabular-nums w-4 text-center">{val}</span>
                </div>
                <p className="text-[10px] text-muted-foreground mt-0.5">{LABELS[val]}</p>
              </div>
            ))}
          </div>
          <div className="flex items-center gap-2 p-3 rounded-lg bg-muted/50 border border-border">
            <span className="text-xs text-muted-foreground">Computed Risk Score:</span>
            <span className="text-lg font-bold">{computedScore}</span>
            <span className="text-xs text-muted-foreground">/ 25</span>
            <div className="flex-1" />
            <ScoreBar score={computedScore} />
          </div>
          <div>
            <Label className="text-xs text-muted-foreground mb-1 block">Assessment Notes</Label>
            <textarea value={notes} onChange={e => setNotes(e.target.value)} placeholder="Notes about this assessment..." className="w-full min-h-[50px] px-3 py-2 rounded-md border border-input bg-background text-sm resize-y focus:outline-none focus:ring-1 focus:ring-ring" />
          </div>
          <DialogFooter>
            <Button type="button" variant="ghost" onClick={onClose} className="h-9 px-4">Cancel</Button>
            <Button type="submit" disabled={saving} className="h-9">{saving ? "Saving..." : "Create Assessment"}</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

// ── TaskDetailSlideOver ────────────────────────────────────────────────────

const TASK_PRIORITY_COLORS: Record<string, string> = {
  critical: "bg-red-500/10 text-red-500 border-red-500/30",
  high:     "bg-orange-500/10 text-orange-500 border-orange-500/30",
  medium:   "bg-amber-500/10 text-amber-500 border-amber-500/30",
  low:      "bg-green-500/10 text-green-500 border-green-500/30",
}

const TASK_STATUS_META: Record<string, { label: string; badge: string }> = {
  open:                 { label: "Open",           badge: "bg-slate-500/10 text-slate-400 border-slate-500/30" },
  in_progress:          { label: "In Progress",    badge: "bg-blue-500/10 text-blue-500 border-blue-500/30" },
  pending_verification: { label: "Pending Review", badge: "bg-purple-500/10 text-purple-500 border-purple-500/30" },
  resolved:             { label: "Resolved",       badge: "bg-emerald-500/10 text-emerald-500 border-emerald-500/30" },
  cancelled:            { label: "Cancelled",      badge: "bg-gray-500/10 text-gray-400 border-gray-500/30" },
  blocked:              { label: "Blocked",        badge: "bg-red-600/10 text-red-600 border-red-600/30" },
}

function TaskDetailSlideOver({
  task,
  onClose,
  onNavigate,
}: {
  task: TaskResponse
  onClose: () => void
  onNavigate: (taskId: string) => void
}) {
  const sm = TASK_STATUS_META[task.status_code] ?? { label: task.status_code, badge: "bg-muted text-muted-foreground border-border" }
  const pm = TASK_PRIORITY_COLORS[task.priority_code] ?? "bg-muted text-muted-foreground border-border"

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/40 backdrop-blur-sm z-40"
        onClick={onClose}
        aria-hidden="true"
      />
      {/* Panel */}
      <div className="fixed right-0 top-0 h-full w-[420px] max-w-[90vw] bg-background border-l border-border shadow-2xl z-50 flex flex-col animate-in slide-in-from-right duration-300 ease-out">
        {/* Header */}
        <div className="flex items-start justify-between px-5 py-4 border-b border-border bg-muted/20 shrink-0">
          <div className="flex items-start gap-2.5 min-w-0 flex-1">
            <TaskStatusIcon status={task.status_code} />
            <div className="min-w-0">
              <p className="text-sm font-semibold text-foreground leading-snug line-clamp-2">{task.title}</p>
              {task.task_type_name && (
                <p className="text-[10px] text-muted-foreground mt-0.5 uppercase tracking-wider font-bold">{task.task_type_name}</p>
              )}
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-muted transition-colors shrink-0 ml-2 mt-0.5"
            title="Close"
          >
            <X className="w-4 h-4 text-muted-foreground" />
          </button>
        </div>

        {/* Scrollable content */}
        <div className="flex-1 overflow-y-auto p-5 space-y-5">

          {/* Badges row */}
          <div className="flex items-center gap-2 flex-wrap">
            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-semibold border ${sm.badge}`}>
              {sm.label}
            </span>
            {task.priority_code && (
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-semibold border capitalize ${pm}`}>
                {task.priority_code}
              </span>
            )}
          </div>

          {/* Description */}
          {task.description && (
            <div>
              <div className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground mb-1.5">Description</div>
              <p className="text-sm text-foreground leading-relaxed">{task.description}</p>
            </div>
          )}

          {/* Key fields grid */}
          <div className="grid grid-cols-2 gap-2.5">
            {task.due_date && (
              <div className="rounded-xl bg-muted/30 border border-border px-3 py-2.5">
                <div className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground mb-0.5 flex items-center gap-1">
                  <Calendar className="w-2.5 h-2.5" /> Due Date
                </div>
                <div className="text-sm font-semibold text-foreground">{formatDate(task.due_date)}</div>
              </div>
            )}
            {task.start_date && (
              <div className="rounded-xl bg-muted/30 border border-border px-3 py-2.5">
                <div className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground mb-0.5 flex items-center gap-1">
                  <Calendar className="w-2.5 h-2.5" /> Start Date
                </div>
                <div className="text-sm font-semibold text-foreground">{formatDate(task.start_date)}</div>
              </div>
            )}
            {task.estimated_hours != null && (
              <div className="rounded-xl bg-muted/30 border border-border px-3 py-2.5">
                <div className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground mb-0.5">Est. Hours</div>
                <div className="text-sm font-semibold text-foreground">{task.estimated_hours}h</div>
              </div>
            )}
            {task.actual_hours != null && (
              <div className="rounded-xl bg-muted/30 border border-border px-3 py-2.5">
                <div className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground mb-0.5">Actual Hours</div>
                <div className="text-sm font-semibold text-foreground">{task.actual_hours}h</div>
              </div>
            )}
          </div>

          {/* Acceptance criteria */}
          {task.acceptance_criteria && (
            <div>
              <div className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground mb-1.5">Acceptance Criteria</div>
              <div className="rounded-xl bg-muted/20 border border-border px-4 py-3">
                <p className="text-sm text-foreground leading-relaxed whitespace-pre-wrap">{task.acceptance_criteria}</p>
              </div>
            </div>
          )}

          {/* Remediation plan */}
          {task.remediation_plan && (
            <div>
              <div className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground mb-1.5">Remediation Plan</div>
              <div className="rounded-xl bg-muted/20 border border-border px-4 py-3">
                <p className="text-sm text-foreground leading-relaxed whitespace-pre-wrap">{task.remediation_plan}</p>
              </div>
            </div>
          )}

          {/* Resolution notes */}
          {task.resolution_notes && (
            <div>
              <div className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground mb-1.5">Resolution Notes</div>
              <div className="rounded-xl bg-emerald-500/5 border border-emerald-500/20 px-4 py-3">
                <p className="text-sm text-foreground leading-relaxed whitespace-pre-wrap">{task.resolution_notes}</p>
              </div>
            </div>
          )}

          {/* Metadata footer */}
          <div className="pt-2 border-t border-border/50 space-y-1.5">
            <div className="flex items-center justify-between text-[11px] text-muted-foreground">
              <span>Created</span>
              <span>{formatDate(task.created_at)}</span>
            </div>
            <div className="flex items-center justify-between text-[11px] text-muted-foreground">
              <span>Last updated</span>
              <span>{formatDate(task.updated_at)}</span>
            </div>
          </div>
        </div>

        {/* Footer — View Full Task CTA */}
        <div className="px-5 py-4 border-t border-border bg-muted/20 shrink-0">
          <Button
            className="w-full gap-2 h-10 rounded-xl font-semibold shadow-sm hover:shadow-md transition-all"
            onClick={() => onNavigate(task.id)}
          >
            <ExternalLink className="w-4 h-4" /> View Full Task
          </Button>
        </div>
      </div>
    </>
  )
}

// ── Main Page ──────────────────────────────────────────────────────────────

export default function RiskDetailPage() {
  const { riskId } = useParams<{ riskId: string }>()
  const router = useRouter()
  const { selectedOrgId, selectedWorkspaceId } = useOrgWorkspace()
  const { isWorkspaceAdmin } = useAccess()

  // Core data
  const [risk, setRisk] = useState<RiskResponse | null>(null)
  const [assessments, setAssessments] = useState<RiskAssessmentResponse[]>([])
  const [treatmentPlan, setTreatmentPlan] = useState<TreatmentPlanResponse | null>(null)
  const [controls, setControls] = useState<RiskControlMappingResponse[]>([])
  const [events, setEvents] = useState<RiskReviewEventResponse[]>([])
  const [riskGroups, setRiskGroups] = useState<RiskGroupAssignmentResponse[]>([])
  const [reviewSchedule, setReviewSchedule] = useState<ReviewScheduleResponse | null>(null)
  const [riskTasks, setRiskTasks] = useState<TaskResponse[]>([])
  const [commentCount, setCommentCount] = useState<number | null>(null)
  const [attachmentCount, setAttachmentCount] = useState<number | null>(null)
  const [members, setMembers] = useState<OrgMemberResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Navigation helpers
  const [frameworkIdMap, setFrameworkIdMap] = useState<Record<string, string>>({})

  // Task detail slide-over
  const [selectedTask, setSelectedTask] = useState<TaskResponse | null>(null)
  const [showTaskDetail, setShowTaskDetail] = useState(false)

  // Dialogs
  const [showAssessment, setShowAssessment] = useState(false)
  const [showAddControl, setShowAddControl] = useState(false)
  const [showAddReview, setShowAddReview] = useState(false)
  const [showReviewSchedule, setShowReviewSchedule] = useState(false)
  const [showTaskSlideOver, setShowTaskSlideOver] = useState(false)
  const [taskTypeMode, setTaskTypeMode] = useState<{ code: string; label: string } | null>(null)

  // Tab
  const [tab, setTab] = useState<"overview" | "details" | "assessments" | "controls" | "tasks" | "schedule" | "reviews" | "comments" | "attachments">("overview")

  const load = useCallback(async () => {
    if (!riskId) return
    setLoading(true); setError(null)
    try {
      const [riskRes, aRes, cRes, eRes, gRes, rsRes, ccnt, acnt, tRes] = await Promise.all([
        getRisk(riskId),
        listAssessments(riskId),
        listRiskControls(riskId),
        listReviewEvents(riskId),
        listRiskGroups(riskId).catch(() => []),
        getReviewSchedule(riskId).catch(() => null),
        getCommentCount("risk", riskId).catch(() => null),
        getAttachmentCount("risk", riskId).catch(() => null),
        listTasks({ 
          orgId: selectedOrgId ?? undefined, 
          workspaceId: selectedWorkspaceId ?? undefined, 
          entity_type: "risk", 
          entity_id: riskId, 
          limit: 50 
        }).catch(() => ({ items: [] })),
      ])
      setRisk(riskRes)
      setAssessments(Array.isArray(aRes) ? aRes : [])
      const controlMappings = Array.isArray(cRes) ? cRes : []
      setControls(controlMappings)
      setEvents(Array.isArray(eRes) ? eRes : [])
      setRiskGroups(Array.isArray(gRes) ? gRes : [])
      setReviewSchedule(rsRes)
      setRiskTasks(tRes?.items ?? [])
      if (ccnt !== null) setCommentCount(ccnt)
      if (acnt !== null) setAttachmentCount(acnt)
      try { setTreatmentPlan(await getTreatmentPlan(riskId)) } catch { setTreatmentPlan(null) }
      // Resolve framework_id for each linked control (needed for navigation to /controls/{fwId}/{ctrlId})
      if (controlMappings.length > 0) {
        try {
          const allControls = await listAllControls({
            deployed_org_id: selectedOrgId ?? undefined,
            deployed_workspace_id: selectedWorkspaceId ?? undefined,
            limit: 500,
          })
          const map: Record<string, string> = {}
          for (const c of allControls.items ?? []) {
            map[c.id] = c.framework_id
          }
          setFrameworkIdMap(map)
        } catch { /* silent — View button stays hidden if unavailable */ }
      }
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setLoading(false)
    }
  }, [riskId, selectedOrgId, selectedWorkspaceId])

  useEffect(() => { load() }, [load])

  useEffect(() => {
    if (!selectedOrgId) return
    import("@/lib/api/orgs").then(({ listOrgMembers }) =>
      listOrgMembers(selectedOrgId).then(setMembers).catch(() => {})
    )
  }, [selectedOrgId])

  const handleRemoveControl = async (mappingId: string) => {
    if (!risk) return
    try { await removeRiskControl(risk.id, mappingId); load() } catch {}
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-32">
        <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (error || !risk) {
    return (
      <div className="space-y-4 p-8">
        <button onClick={() => router.back()} className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors">
          <ChevronLeft className="w-4 h-4" /> Back to Risk Registry
        </button>
        <div className="flex items-center gap-2 rounded-xl border border-destructive/20 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          <AlertTriangle className="w-4 h-4 shrink-0" /> {error ?? "Risk not found."}
        </div>
      </div>
    )
  }

  const lm = LEVEL_COLORS[risk.risk_level_code] ?? LEVEL_COLORS.medium

  const tabConfig = [
    { key: "overview",    label: "Overview" },
    { key: "details",     label: "Full Details" },
    { key: "assessments", label: `Assessments (${assessments.length})` },
    { key: "controls",    label: `Controls (${controls.length})` },
    { key: "tasks",       label: `Tasks (${riskTasks.length})` },
    { key: "schedule",    label: "Schedule" },
    { key: "reviews",     label: `Reviews (${events.length})` },
    { key: "comments",    label: `Comments (${commentCount ?? 0})` },
    { key: "attachments", label: `Files (${attachmentCount ?? 0})` },
  ] as const

  return (
    <div className="space-y-6 pb-20">
      {/* Hero Header */}
      <div className="relative overflow-hidden rounded-3xl border border-border bg-card">
        {/* Subtle Background Decoration */}
        <div className={`absolute top-0 right-0 w-96 h-96 -mr-20 -mt-20 opacity-20 blur-3xl rounded-full pointer-events-none ${lm.badge.split(" ")[0]}`} />
        <div className="absolute top-0 left-0 p-4">
          <button onClick={() => router.back()} className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors">
            <ChevronLeft className="w-3.5 h-3.5" /> Back to Registry
          </button>
        </div>

        <div className="px-8 pt-12 pb-8">
          <div className="flex flex-col lg:flex-row lg:items-center gap-8">
            {/* Title & Identity */}
            <div className="flex-1 space-y-4">
              <div className="flex items-center gap-3">
                <div className={`p-3 rounded-2xl bg-muted/50 border border-border shrink-0 ${lm.icon}`}>
                  <ShieldAlert className="w-8 h-8" />
                </div>
                <div>
                  <div className="flex items-center gap-3 mb-1">
                    <span className="font-mono text-xs text-muted-foreground bg-muted/80 px-2 py-0.5 rounded border border-border/50">{risk.risk_code}</span>
                    <span className="text-xs text-muted-foreground">{risk.category_name}</span>
                  </div>
                  <h1 className="text-3xl font-bold tracking-tight text-foreground">{risk.title}</h1>
                </div>
              </div>
              
              <div className="flex items-center gap-3 flex-wrap">
                <span className={`inline-flex items-center gap-2 px-3 py-1 rounded-xl text-xs font-bold border transition-all hover:scale-105 shadow-sm ${lm.badge}`}>
                  <div className={`w-2 h-2 rounded-full animate-pulse ${lm.icon.split(" ")[0].replace("text-", "bg-")}`} />
                  {lm.label} Level
                </span>
                <div className="scale-110">
                  <StatusBadge status={risk.risk_status} />
                </div>
                {risk.treatment_plan_status && (() => {
                  const m = TREATMENT_PLAN_STATUS_META[risk.treatment_plan_status]
                  return m ? (
                    <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-xl text-xs font-medium border border-border bg-background/50 backdrop-blur-sm ${m.cls}`}>
                      <FileText className="w-3.5 h-3.5" />
                      {m.label} Plan
                    </span>
                  ) : null
                })()}
              </div>
            </div>

            {/* Score Gauges */}
            <div className="flex items-center gap-10 bg-muted/30 backdrop-blur-sm px-8 py-5 rounded-3xl border border-border/50 shadow-inner">
              <RiskScoreGauge 
                score={risk.inherent_risk_score} 
                label="Inherent" 
                color={risk.inherent_risk_score && risk.inherent_risk_score >= 16 ? "#ef4444" : "#f97316"} 
              />
              <div className="w-[1px] h-16 bg-border/50" />
              <RiskScoreGauge 
                score={risk.residual_risk_score} 
                label="Residual" 
                color={risk.residual_risk_score && risk.residual_risk_score <= 10 ? "#10b981" : "#3b82f6"} 
              />
            </div>
          </div>
        </div>
        
        {/* Action Bar */}
        <div className="px-8 py-4 bg-muted/20 border-t border-border/40 flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center gap-3 text-xs text-muted-foreground">
            <div className="flex -space-x-2">
              <div className="w-6 h-6 rounded-full bg-primary/20 border border-background flex items-center justify-center">
                <User2 className="w-3 h-3 text-primary" />
              </div>
            </div>
            <span>Owned by <span className="font-medium text-foreground">{risk.owner_display_name || "Unknown"}</span></span>
            <span className="opacity-30">•</span>
            <span className="flex items-center gap-1"><Clock className="w-3 h-3" /> Updated {formatDate(risk.updated_at)}</span>
          </div>
          
          <div className="flex items-center gap-2">
            <Button size="sm" variant="outline" className="h-8 rounded-xl px-4 gap-2 border-border/60 hover:bg-background shadow-sm" onClick={() => setShowAssessment(true)}>
              <ClipboardCheck className="w-4 h-4 text-blue-500" /> Assess Risk
            </Button>
            <Button size="sm" variant="outline" className="h-8 rounded-xl px-4 gap-2 border-border/60 hover:bg-background shadow-sm" onClick={() => setShowAddControl(true)}>
              <Link2 className="w-4 h-4 text-purple-500" /> Link Control
            </Button>
            <Button size="sm" variant="outline" className="h-8 rounded-xl px-4 gap-2 border-border/60 hover:bg-background shadow-sm" onClick={() => setShowAddReview(true)}>
              <MessageSquare className="w-4 h-4 text-emerald-500" /> Add Note
            </Button>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="rounded-2xl border border-border bg-card/60 backdrop-blur-md overflow-hidden shadow-xl border-t-border/50">
        <div className="flex border-b border-border bg-muted/30 px-6 backdrop-blur-sm overflow-x-auto no-scrollbar" role="tablist">
          {tabConfig.map(({ key, label }) => (
            <button key={key} role="tab" aria-selected={tab === key} onClick={() => setTab(key as typeof tab)}
              className={`px-4 py-4 text-xs font-bold uppercase tracking-widest border-b-2 transition-all whitespace-nowrap outline-none ${tab === key ? "border-primary text-primary" : "border-transparent text-muted-foreground hover:text-foreground hover:bg-muted/30"}`}>
              {label}
            </button>
          ))}
        </div>

        <div className="px-8 py-8 transition-all duration-300">
          {/* Overview Tab */}
          {tab === "overview" && (
            <div className="space-y-8 animate-in fade-in slide-in-from-bottom-2 duration-500">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {[
                  { label: "Current Status", value: <StatusBadge status={risk.risk_status} />, icon: <Activity className="w-5 h-5 text-blue-500" />, tab: "schedule" },
                  { label: "Owner", value: risk.owner_display_name || "Unassigned", icon: <User2 className="w-5 h-5 text-indigo-500" />, tab: "details" },
                  { label: "Control Health", value: `${controls.length} Linked Controls`, icon: <ShieldCheck className="w-5 h-5 text-emerald-500" />, tab: "controls" },
                  { label: "Assigned Tasks", value: `${riskTasks.filter(t => t.status_code !== 'completed').length} Open Tasks`, icon: <Wrench className="w-5 h-5 text-amber-500" />, tab: "tasks" },
                ].map((stat, i) => (
                  <button key={i} onClick={() => setTab(stat.tab as any)} 
                    className="group p-5 rounded-2xl bg-muted/20 border border-border/50 hover:bg-muted/40 transition-all hover:shadow-md hover:border-primary/20 text-left outline-none">
                    <div className="flex items-center justify-between mb-3">
                      <div className="p-2 rounded-xl bg-background border border-border shadow-sm group-hover:scale-110 transition-transform">{stat.icon}</div>
                    </div>
                    <div>
                      <div className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground mb-1">{stat.label}</div>
                      <div className="text-sm font-bold text-foreground">{stat.value}</div>
                    </div>
                  </button>
                ))}
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Score Summary */}
                <Card className="lg:col-span-2 rounded-2xl border-border/40 bg-muted/10 shadow-sm overflow-hidden border-l-[4px] border-l-primary/50">
                  <CardContent className="p-6">
                    <h3 className="text-sm font-bold uppercase tracking-widest text-muted-foreground mb-6 flex items-center gap-2">
                       <TrendingUp className="w-4 h-4" /> Score Distribution
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                       <div className="space-y-4">
                          <p className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">Detailed Score Analysis</p>
                          <div className="space-y-4">
                             <div className="p-4 rounded-xl bg-background border border-border">
                                <div className="text-[10px] text-muted-foreground mb-1">Likelihood × Impact (Current)</div>
                                <div className="text-xl font-bold flex items-center gap-2">
                                   {risk.residual_risk_score ?? risk.inherent_risk_score ?? "--"}
                                   <span className="text-xs text-muted-foreground font-normal">/ 25 total score</span>
                                </div>
                             </div>
                             <ScoreBar score={risk.inherent_risk_score} max={25} />
                             <ScoreBar score={risk.residual_risk_score} max={25} />
                          </div>
                       </div>
                       <div className="flex flex-col justify-center items-center bg-background/50 rounded-2xl border border-border/40 p-6">
                          <div className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground mb-4">Risk Level Summary</div>
                          <div className={`text-4xl font-black mb-2 px-6 py-2 rounded-2xl bg-muted/50 border border-border shadow-sm transform -rotate-1 ${lm.icon}`}>
                             {risk.inherent_risk_score ?? "--"}
                          </div>
                          <div className={`text-xs font-bold uppercase tracking-widest ${lm.icon}`}>{lm.label} Exposure</div>
                       </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Next Action Widget */}
                <Card className="rounded-2xl border-border/40 bg-muted/10 shadow-sm overflow-hidden flex flex-col">
                   <CardContent className="p-6 flex-1 flex flex-col">
                      <h3 className="text-sm font-bold uppercase tracking-widest text-muted-foreground mb-6 flex items-center gap-2">
                         <CalendarCheck className="w-4 h-4" /> Next Milestone
                      </h3>
                      <div className="flex-1 flex flex-col justify-center items-center text-center space-y-4">
                         {reviewSchedule ? (
                            <>
                               <div className={`p-4 rounded-3xl border-2 ${reviewSchedule.is_overdue ? 'bg-red-500/10 border-red-500/30' : 'bg-primary/10 border-primary/30'}`}>
                                  <Calendar className="w-10 h-10 mb-2" />
                                  <div className="text-lg font-bold">{formatDate(reviewSchedule.next_review_date)}</div>
                                  <div className="text-[10px] font-bold uppercase tracking-widest opacity-70">Review Due</div>
                               </div>
                               <Button variant="ghost" size="sm" className="text-xs font-bold uppercase tracking-widest" onClick={() => setShowReviewSchedule(true)}>
                                  Configure Schedule
                               </Button>
                            </>
                         ) : (
                            <>
                               <div className="p-4 rounded-3xl border-2 border-dashed border-muted flex flex-col items-center">
                                  <Clock className="w-10 h-10 mb-2 text-muted-foreground" />
                                  <div className="text-sm font-medium text-muted-foreground">No review scheduled</div>
                               </div>
                               <Button variant="outline" size="sm" className="mt-4 rounded-xl" onClick={() => setShowReviewSchedule(true)}>
                                  Set Schedule
                               </Button>
                            </>
                         )}
                      </div>
                   </CardContent>
                </Card>
              </div>

              {/* Quick Details Grid */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                 {risk.description && (
                   <div className="rounded-2xl bg-muted/10 border border-border px-6 py-5">
                     <div className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground mb-3">Description</div>
                     <p className="text-foreground text-sm leading-relaxed">{risk.description}</p>
                   </div>
                 )}
                 {risk.business_impact && (
                   <div className="rounded-2xl bg-red-500/5 border border-red-500/10 px-6 py-5 border-l-[4px] border-l-red-500/50">
                     <div className="text-[10px] font-bold uppercase tracking-widest text-red-600 mb-3 flex items-center gap-2">
                        <AlertTriangle className="w-3.5 h-3.5" /> Business Impact
                     </div>
                     <p className="text-foreground text-sm leading-relaxed font-medium">{risk.business_impact}</p>
                   </div>
                 )}
              </div>
            </div>
          )}

          {/* Full Details tab */}
          {tab === "details" && (
            <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-500 text-xs">
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                {[
                  { label: "Risk Code", value: <span className="font-mono">{risk.risk_code}</span> },
                  { label: "Category", value: risk.category_name },
                  { label: "Source", value: <span className="capitalize">{risk.source_type?.replace(/_/g, " ")}</span> },
                  { label: "Created", value: formatDate(risk.created_at) },
                ].map(({ label, value }) => (
                  <div key={label} className="rounded-2xl bg-muted/20 border border-border/50 px-5 py-3 text-xs">
                    <div className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground mb-1">{label}</div>
                    <div className="text-sm font-bold text-foreground">{value}</div>
                  </div>
                ))}
              </div>

              <div className="rounded-2xl bg-muted/20 border border-border/50 divide-y divide-border/50 overflow-hidden">
                {[
                  { label: "Description", value: risk.description },
                  { label: "Business Impact", value: risk.business_impact, cls: "bg-red-500/5 text-xs" },
                  { label: "Notes", value: risk.notes },
                ].map((item, i) => item.value && (
                  <div key={i} className={`px-6 py-5 ${item.cls || ""}`}>
                    <div className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground mb-2">{item.label}</div>
                    <p className="text-sm text-foreground leading-relaxed whitespace-pre-wrap">{item.value}</p>
                  </div>
                ))}
              </div>

              {risk.owner_user_id && (() => {
                const m = members.find(x => x.user_id === risk.owner_user_id)
                const name = risk.owner_display_name || m?.display_name || m?.email
                return name ? (
                  <div className="flex items-center gap-3 p-4 rounded-2xl bg-primary/5 border border-primary/20 text-primary">
                    <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                      <User2 className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="text-[10px] font-bold uppercase tracking-widest opacity-70">Risk Owner</div>
                      <div className="text-sm font-bold">{name}</div>
                    </div>
                  </div>
                ) : null
              })()}
            </div>
          )}

          {/* Assessments */}
          {tab === "assessments" && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <p className="font-semibold text-foreground">Assessment History ({assessments.length})</p>
                <Button size="sm" variant="outline" className="h-7 text-xs gap-1" onClick={() => setShowAssessment(true)}>
                  <ClipboardCheck className="w-3 h-3" /> Add Assessment
                </Button>
              </div>
              {assessments.length === 0 ? (
                <div className="flex flex-col items-center py-8 gap-2 text-muted-foreground">
                  <ClipboardCheck className="w-8 h-8 opacity-30" />
                  <p>No assessments recorded yet.</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {assessments.map(a => {
                    const score = a.risk_score ?? a.likelihood_score * a.impact_score
                    const scorePct = Math.min((score / 25) * 100, 100)
                    const scoreColor = score >= 16 ? "#ef4444" : score >= 11 ? "#f97316" : score >= 6 ? "#f59e0b" : "#10b981"
                    const scoreLabel = score >= 16 ? "Critical" : score >= 11 ? "High" : score >= 6 ? "Medium" : "Low"
                    const typeCls = a.assessment_type === "inherent"
                      ? "text-orange-600 bg-orange-500/10 border-orange-500/20"
                      : "text-blue-600 bg-blue-500/10 border-blue-500/20"
                    return (
                      <div key={a.id} className="rounded-lg bg-muted/30 border border-border overflow-hidden">
                        <div className="px-3 py-2 flex items-center gap-3">
                          <span className={`inline-flex items-center px-2 py-0.5 rounded-full border text-[10px] font-semibold capitalize ${typeCls}`}>{a.assessment_type}</span>
                          <div className="flex items-center gap-2 text-muted-foreground">
                            <span className="font-mono">L={a.likelihood_score}</span>
                            <span>×</span>
                            <span className="font-mono">I={a.impact_score}</span>
                            <span>=</span>
                            <span className="font-bold text-sm" style={{ color: scoreColor }}>{score}</span>
                            <span className="text-[10px] font-semibold" style={{ color: scoreColor }}>({scoreLabel})</span>
                          </div>
                          <span className="text-muted-foreground ml-auto text-[11px]">{formatDate(a.assessed_at)}</span>
                        </div>
                        <div className="px-3 pb-2">
                          <div className="h-1.5 w-full rounded-full bg-muted overflow-hidden">
                            <div className="h-full rounded-full" style={{ width: `${scorePct}%`, backgroundColor: scoreColor }} />
                          </div>
                        </div>
                        {a.assessment_notes && <div className="px-3 pb-2 text-muted-foreground italic">{a.assessment_notes}</div>}
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          )}

          {/* Controls */}
          {tab === "controls" && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <p className="font-semibold text-foreground">Linked Controls ({controls.length})</p>
                <Button size="sm" variant="outline" className="h-7 text-xs gap-1" onClick={() => setShowAddControl(true)}>
                  <Link2 className="w-3 h-3" /> Link Control
                </Button>
              </div>
              {controls.length === 0 ? (
                <div className="flex flex-col items-center py-8 gap-2 text-muted-foreground">
                  <Link2 className="w-8 h-8 opacity-30" />
                  <p>No controls linked yet.</p>
                </div>
              ) : (
                <div className="space-y-1.5">
                  {controls.map(c => (
                    <div 
                      key={c.id} 
                      className={`flex items-center gap-3 px-3 py-2 rounded-lg bg-muted/30 border border-border group hover:bg-muted/50 transition-colors ${frameworkIdMap[c.control_id] ? "cursor-pointer" : ""}`}
                      onClick={() => {
                        if (frameworkIdMap[c.control_id]) {
                          router.push(`/controls/${frameworkIdMap[c.control_id]}/${c.control_id}`)
                        }
                      }}
                    >
                      <span className="font-mono text-[10px] text-muted-foreground shrink-0">{c.control_code}</span>
                      <span className="text-xs font-medium flex-1 truncate">{c.control_name}</span>
                      {c.link_type && (
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-primary/10 text-primary border border-primary/20 capitalize shrink-0">{c.link_type}</span>
                      )}
                      
                      {/* ✅ View Button (Control) - Always visible for clarity, matching control page pattern */}
                      {frameworkIdMap[c.control_id] ? (
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            router.push(`/controls/${frameworkIdMap[c.control_id]}/${c.control_id}`)
                          }}
                          className="flex items-center gap-1.5 px-2 py-1 rounded text-[10px] font-semibold text-primary border border-primary/30 hover:bg-primary/10 bg-primary/5 transition-all shrink-0"
                          title="View control detail"
                        >
                          <ExternalLink className="w-3 h-3" /> View
                        </button>
                      ) : (
                        <div className="flex items-center gap-1.5 px-2 py-1 rounded text-[10px] font-medium text-muted-foreground border border-border bg-muted/20 shrink-0 cursor-not-allowed">
                          <Loader2 className="w-3 h-3 animate-spin" /> Loading
                        </div>
                      )}

                      <button 
                        onClick={(e) => { 
                          e.stopPropagation()
                          handleRemoveControl(c.id) 
                        }} 
                        className="p-1 rounded text-muted-foreground hover:text-red-500 hover:bg-red-500/10 transition-all shrink-0 ml-1" 
                        title="Unlink"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Tasks */}
          {tab === "tasks" && (
            <div className="space-y-3">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                   <p className="text-sm font-bold uppercase tracking-widest text-muted-foreground">Action Registry ({riskTasks.length})</p>
                   <p className="text-[10px] text-muted-foreground mt-0.5">Manage mitigation and evidence collection workflows.</p>
                </div>
                <div className="flex items-center gap-2">
                   <Button size="sm" variant="outline" className="h-8 rounded-xl px-4 gap-2 border-primary/20 hover:bg-primary/5 text-primary" 
                    onClick={() => { setTaskTypeMode({ code: "risk_mitigation", label: "Mitigation" }); setShowTaskSlideOver(true) }}>
                     <Wrench className="w-4 h-4" /> Add Mitigation Task
                   </Button>
                   <Button size="sm" className="h-8 rounded-xl px-4 gap-2 shadow-lg shadow-primary/20" 
                    onClick={() => { setTaskTypeMode({ code: "evidence_collection", label: "Evidence" }); setShowTaskSlideOver(true) }}>
                     <FileText className="w-4 h-4" /> Add Evidence Task
                   </Button>
                </div>
              </div>
              {riskTasks.length === 0 ? (
                <div className="flex flex-col items-center py-8 gap-2 text-muted-foreground">
                  <Wrench className="w-8 h-8 opacity-30" />
                  <p>No tasks created yet.</p>
                </div>
              ) : (
                <div className="space-y-1.5">
                  {riskTasks.map(t => (
                    <div 
                      key={t.id} 
                      className="flex items-center gap-2 px-3 py-2 rounded-lg bg-muted/30 border border-border group hover:bg-muted/50 transition-colors cursor-pointer"
                      onClick={() => { setSelectedTask(t); setShowTaskDetail(true) }}
                    >
                      <TaskStatusIcon status={t.status_code} />
                      <span className="text-xs font-medium flex-1 truncate">{t.title}</span>
                      {t.priority_code && (
                        <span className={`text-[10px] px-1.5 py-0.5 rounded border capitalize ${t.priority_code === "critical" ? "bg-red-500/10 text-red-500 border-red-500/30" : t.priority_code === "high" ? "bg-orange-500/10 text-orange-500 border-orange-500/30" : t.priority_code === "medium" ? "bg-amber-500/10 text-amber-500 border-amber-500/30" : "bg-green-500/10 text-green-500 border-green-500/30"}`}>{t.priority_code}</span>
                      )}
                      {t.due_date && <span className="text-[10px] text-muted-foreground shrink-0">{formatDate(t.due_date)}</span>}
                      {/* ✅ View Button (Task hover) */}
                      <button 
                        onClick={(e) => { e.stopPropagation(); router.push(`/tasks/${t.id}`) }}
                        className="opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1.5 px-2 py-1 rounded text-[10px] font-semibold text-primary border border-primary/30 hover:bg-primary/10 shrink-0 ml-1"
                        title="View full task"
                      >
                        <ExternalLink className="w-3 h-3" /> View
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Schedule */}
          {tab === "schedule" && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <p className="font-semibold text-foreground">Review Schedule</p>
                <Button size="sm" variant="outline" className="h-7 text-xs gap-1" onClick={() => setShowReviewSchedule(true)}>
                  <CalendarCheck className="w-3 h-3" /> {reviewSchedule ? "Edit Schedule" : "Set Schedule"}
                </Button>
              </div>
              {reviewSchedule ? (
                <div className="px-3 py-3 rounded-lg bg-muted/30 border border-border space-y-2">
                  <div className="flex items-center gap-3 flex-wrap">
                    <span className="font-medium capitalize">{reviewSchedule.review_frequency.replace(/_/g, " ")}</span>
                    <span className="text-muted-foreground flex items-center gap-1"><CalendarCheck className="w-3 h-3" /> Next: {formatDate(reviewSchedule.next_review_date)}</span>
                    {reviewSchedule.is_overdue && <span className="inline-flex items-center px-2 py-0.5 rounded-full border text-[10px] font-semibold text-red-600 bg-red-500/10 border-red-500/20">Overdue</span>}
                  </div>
                  {reviewSchedule.last_reviewed_at && (
                    <div className="flex items-center gap-2 text-muted-foreground">
                      <Clock className="w-3 h-3" /> Last reviewed: {formatDate(reviewSchedule.last_reviewed_at)}
                    </div>
                  )}
                  <Button size="sm" variant="outline" className="h-7 text-xs gap-1"
                    onClick={async () => {
                      const now = new Date()
                      const freq = reviewSchedule.review_frequency
                      if (freq === "monthly") now.setMonth(now.getMonth() + 1)
                      else if (freq === "quarterly") now.setMonth(now.getMonth() + 3)
                      else if (freq === "semi_annual") now.setMonth(now.getMonth() + 6)
                      else now.setFullYear(now.getFullYear() + 1)
                      try { await completeReview(risk.id, now.toISOString().split("T")[0]); load() } catch {}
                    }}>
                    <ClipboardCheck className="w-3 h-3" /> Complete Review
                  </Button>
                </div>
              ) : (
                <p className="text-muted-foreground">No review schedule configured yet.</p>
              )}
            </div>
          )}

          {/* Reviews */}
          {tab === "reviews" && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <p className="font-semibold text-foreground">Review Events ({events.length})</p>
                <Button size="sm" variant="outline" className="h-7 text-xs gap-1" onClick={() => setShowAddReview(true)}>
                  <MessageSquare className="w-3 h-3" /> Add Review
                </Button>
              </div>
              {events.length === 0 ? (
                <div className="flex flex-col items-center py-8 gap-2 text-muted-foreground">
                  <MessageSquare className="w-8 h-8 opacity-30" />
                  <p>No review events yet.</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {events.map(ev => (
                    <div key={ev.id} className="px-3 py-2 rounded-lg bg-muted/30 border border-border space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] text-muted-foreground capitalize px-1.5 py-0.5 rounded bg-muted border border-border">{ev.event_type?.replace(/_/g, " ")}</span>
                        <span className="text-[10px] text-muted-foreground ml-auto">{formatDate(ev.occurred_at)}</span>
                      </div>
                      {ev.comment && <p className="text-foreground leading-relaxed">{ev.comment}</p>}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Comments */}
          {tab === "comments" && (
            <CommentsSection entityType="risk" entityId={risk.id} currentUserId={getJwtSubject() ?? ""} isWorkspaceAdmin={isWorkspaceAdmin} orgId={risk.org_id ?? null} workspaceId={risk.workspace_id ?? null} />
          )}

          {/* Attachments */}
          {tab === "attachments" && (
            <AttachmentsSection entityType="risk" entityId={risk.id} currentUserId={getJwtSubject() ?? ""} canUpload={true} isWorkspaceAdmin={isWorkspaceAdmin} />
          )}

        </div>
      </div>

      {/* Dialogs */}
      <AssessmentDialog riskId={risk.id} orgId={selectedOrgId} workspaceId={selectedWorkspaceId} open={showAssessment} onCreated={load} onClose={() => setShowAssessment(false)} />
      <AddControlDialog riskId={risk.id} orgId={selectedOrgId} workspaceId={selectedWorkspaceId} open={showAddControl} onAdded={load} onClose={() => setShowAddControl(false)} />
      <AddReviewDialog riskId={risk.id} open={showAddReview} onAdded={load} onClose={() => setShowAddReview(false)} />
      <ReviewScheduleDialog riskId={risk.id} existing={reviewSchedule} open={showReviewSchedule} onSaved={load} onClose={() => setShowReviewSchedule(false)} />
      {showTaskSlideOver && risk && selectedOrgId && selectedWorkspaceId && (
        <TaskCreateSlideOver
          open={showTaskSlideOver}
          onClose={() => { setShowTaskSlideOver(false); setTaskTypeMode(null) }}
          orgId={selectedOrgId}
          workspaceId={selectedWorkspaceId}
          entityType="risk"
          entityId={risk.id}
          entityTitle={risk.title ?? risk.risk_code}
          taskTypeCode={taskTypeMode?.code}
          taskTypeName={taskTypeMode?.label}
          onCreated={load}
        />
      )}
      {showTaskDetail && selectedTask && (
        <TaskDetailSlideOver
          task={selectedTask}
          onClose={() => { setShowTaskDetail(false); setSelectedTask(null) }}
          onNavigate={(taskId) => router.push(`/tasks/${taskId}`)}
        />
      )}
    </div>
  )
}
