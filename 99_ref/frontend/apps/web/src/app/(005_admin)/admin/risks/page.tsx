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
  ShieldAlert,
  Plus,
  Search,
  AlertTriangle,
  RefreshCw,
  TrendingUp,
  TrendingDown,
  Activity,
  X,
  Download,
  Pencil,
  Trash2,
  ChevronLeft,
  ChevronRight,
  ChevronUp,
  ChevronDown,
  ClipboardList,
  Clock,
} from "lucide-react"
import {
  listRisks,
  createRisk,
  updateRisk,
  deleteRisk,
  createAssessment,
  listAssessments,
  getTreatmentPlan,
  createTreatmentPlan,
  updateTreatmentPlan,
  listRiskCategories,
  listRiskLevels,
  listTreatmentTypes,
  listReviewEvents,
  addReviewEvent,
} from "@/lib/api/grc"
import { useOrgWorkspace, OrgWorkspaceProvider } from "@/lib/context/OrgWorkspaceContext"
import type { RiskResponse, CreateRiskRequest, UpdateRiskRequest, CreateRiskAssessmentRequest, RiskAssessmentResponse, TreatmentPlanResponse, CreateTreatmentPlanRequest, UpdateTreatmentPlanRequest, RiskReviewEventResponse } from "@/lib/types/grc"

// -- Constants ----------------------------------------------------------------

const RISK_STATUS_META: Record<string, { label: string; color: string }> = {
  identified: { label: "Identified", color: "text-muted-foreground bg-muted border-border" },
  assessed:   { label: "Assessed",   color: "text-blue-600 bg-blue-500/10 border-blue-500/20" },
  treating:   { label: "Treating",   color: "text-yellow-600 bg-yellow-500/10 border-yellow-500/20" },
  accepted:   { label: "Accepted",   color: "text-emerald-600 bg-emerald-500/10 border-emerald-500/20" },
  closed:     { label: "Closed",     color: "text-slate-500 bg-slate-500/10 border-slate-500/20" },
}

const TREATMENT_STATUS_META: Record<string, { label: string; color: string }> = {
  draft:        { label: "Draft",        color: "text-muted-foreground" },
  active:       { label: "Active",       color: "text-blue-500" },
  completed:    { label: "Completed",    color: "text-emerald-500" },
  cancelled:    { label: "Cancelled",    color: "text-amber-500" },
}

const PAGE_SIZE = 50
type SortField = "title" | "risk_level_name" | "risk_status" | "created_at" | "residual_risk_score"
type SortDir = "asc" | "desc"

interface RiskCategoryOption { code: string; name: string }
interface RiskLevelOption { code: string; name: string; color: string; sort_order: number }
interface TreatmentTypeOption { code: string; name: string }

// border-l-[3px] color by severity / level name
function riskBorderCls(levelName: string): string {
  const n = levelName?.toLowerCase() ?? ""
  if (n === "critical")       return "border-l-red-500"
  if (n === "high")           return "border-l-orange-500"
  if (n === "medium")         return "border-l-amber-500"
  if (n === "low")            return "border-l-yellow-500"
  if (n === "informational")  return "border-l-blue-500"
  return "border-l-primary"
}

// KPI stat card accents
function statBorderCls(label: string): string {
  if (label === "Critical / High") return "border-l-red-500"
  if (label === "Open Risks")      return "border-l-amber-500"
  return "border-l-primary"
}
function statNumCls(label: string): string {
  if (label === "Critical / High") return "text-red-500"
  return "text-foreground"
}

// -- Helpers ------------------------------------------------------------------

function StatusBadge({ status }: { status: string }) {
  const meta = RISK_STATUS_META[status] ?? { label: status, color: "text-muted-foreground bg-muted border-border" }
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full border text-xs font-medium ${meta.color}`}>
      {meta.label}
    </span>
  )
}

function RiskLevelBadge({ name, color }: { name: string; color?: string }) {
  const bgColor = color ? `${color}20` : undefined
  return (
    <span
      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full border text-xs font-medium"
      style={{
        color: color ?? undefined,
        backgroundColor: bgColor ?? undefined,
        borderColor: color ? `${color}40` : undefined,
      }}
    >
      {name}
    </span>
  )
}

function ScoreBar({ score, max = 25 }: { score: number | null; max?: number }) {
  if (score == null) return <span className="text-xs text-muted-foreground">--</span>
  const pct = Math.min(100, (score / max) * 100)
  const color = pct >= 75 ? "bg-red-500" : pct >= 50 ? "bg-orange-500" : pct >= 25 ? "bg-yellow-500" : "bg-emerald-500"
  return (
    <div className="flex items-center gap-2">
      <div className="w-16 h-1.5 rounded-full bg-muted overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs font-medium">{score}</span>
    </div>
  )
}

function formatDate(iso: string | null | undefined) {
  if (!iso) return "—"
  return new Date(iso).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })
}

function SortIcon({ field, sortBy, sortDir }: { field: SortField; sortBy: SortField; sortDir: SortDir }) {
  if (field !== sortBy) return null
  return sortDir === "asc" ? <ChevronUp className="w-3 h-3 inline ml-0.5" /> : <ChevronDown className="w-3 h-3 inline ml-0.5" />
}

// -- Skeleton -----------------------------------------------------------------

function Skeleton() {
  return (
    <div className="rounded-xl border border-l-[3px] border-l-primary border-border bg-card p-4 animate-pulse space-y-2">
      <div className="flex items-center gap-3">
        <div className="h-4 w-36 bg-muted rounded" />
        <div className="h-4 w-20 bg-muted rounded" />
      </div>
      <div className="h-3 w-52 bg-muted rounded" />
    </div>
  )
}

// -- Risk score color --------------------------------------------------------

function riskScoreBadgeColor(score: number): string {
  if (score >= 20) return "text-red-600 bg-red-500/10 border-red-500/20"
  if (score >= 12) return "text-orange-600 bg-orange-500/10 border-orange-500/20"
  if (score >= 6) return "text-yellow-600 bg-yellow-500/10 border-yellow-500/20"
  return "text-blue-600 bg-blue-500/10 border-blue-500/20"
}

// -- 5x5 Risk Matrix ---------------------------------------------------------

function RiskMatrix({ likelihood, impact }: { likelihood: number; impact: number }) {
  return (
    <div className="grid grid-cols-5 gap-0.5 w-32">
      {Array.from({ length: 5 }, (_, rowIdx) => {
        const l = 5 - rowIdx // likelihood 5 at top
        return Array.from({ length: 5 }, (_, colIdx) => {
          const i = colIdx + 1 // impact 1..5
          const s = l * i
          const isActive = l === likelihood && i === impact
          const color = s >= 20 ? "bg-red-500" : s >= 12 ? "bg-orange-400" : s >= 6 ? "bg-yellow-400" : "bg-blue-300"
          return (
            <div
              key={`${l}-${i}`}
              className={`h-5 w-5 rounded-sm ${color} ${isActive ? "ring-2 ring-white ring-offset-1 opacity-100" : "opacity-40"}`}
            />
          )
        })
      })}
    </div>
  )
}

// -- Treatment Plan Dialogs --------------------------------------------------

const PLAN_STATUS_META: Record<string, { label: string; color: string }> = {
  draft:       { label: "Draft",       color: "text-muted-foreground bg-muted border-border" },
  approved:    { label: "Approved",    color: "text-emerald-600 bg-emerald-500/10 border-emerald-500/20" },
  in_progress: { label: "In Progress", color: "text-yellow-600 bg-yellow-500/10 border-yellow-500/20" },
  completed:   { label: "Completed",   color: "text-emerald-600 bg-emerald-500/10 border-emerald-500/20" },
  overdue:     { label: "Overdue",     color: "text-red-600 bg-red-500/10 border-red-500/20" },
}

function PlanStatusBadge({ status }: { status: string }) {
  const meta = PLAN_STATUS_META[status] ?? { label: status, color: "text-muted-foreground bg-muted border-border" }
  return <span className={`inline-flex items-center px-2 py-0.5 rounded-full border text-xs font-medium ${meta.color}`}>{meta.label}</span>
}

function TreatmentPlanDialog({
  riskId,
  existing,
  onSaved,
  onClose,
}: {
  riskId: string
  existing: TreatmentPlanResponse | null
  onSaved: (p: TreatmentPlanResponse) => void
  onClose: () => void
}) {
  const [planStatus, setPlanStatus] = useState(existing?.plan_status ?? "draft")
  const [targetDate, setTargetDate] = useState(existing?.target_date?.slice(0, 10) ?? "")
  const [description, setDescription] = useState(existing?.properties?.plan_description ?? "")
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setError(null)
    try {
      let result: TreatmentPlanResponse
      if (existing) {
        const payload: UpdateTreatmentPlanRequest = {
          plan_status: planStatus,
          target_date: targetDate || undefined,
          plan_description: description || undefined,
        }
        result = await updateTreatmentPlan(riskId, payload)
      } else {
        const payload: CreateTreatmentPlanRequest = {
          plan_description: description || undefined,
          plan_status: planStatus,
          target_date: targetDate || undefined,
        }
        result = await createTreatmentPlan(riskId, payload)
      }
      onSaved(result)
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
          <DialogTitle>{existing ? "Update Treatment Plan" : "Create Treatment Plan"}</DialogTitle>
          <DialogDescription>Define how this risk will be treated.</DialogDescription>
        </DialogHeader>
        {error && <div className="text-xs text-destructive bg-destructive/10 rounded-lg px-3 py-2">{error}</div>}
        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <Label className="text-xs text-muted-foreground mb-1 block">Status</Label>
            <select
              value={planStatus}
              onChange={e => setPlanStatus(e.target.value)}
              className="w-full h-8 px-2 rounded border border-border bg-background text-sm focus:outline-none focus:ring-1 focus:ring-primary"
            >
              {Object.entries(PLAN_STATUS_META).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
            </select>
          </div>
          <div>
            <Label className="text-xs text-muted-foreground mb-1 block">Target Date</Label>
            <input
              type="date"
              value={targetDate}
              onChange={e => setTargetDate(e.target.value)}
              className="w-full h-8 px-2 rounded border border-border bg-background text-sm focus:outline-none focus:ring-1 focus:ring-primary"
            />
          </div>
          <div>
            <Label className="text-xs text-muted-foreground mb-1 block">Description <span className="text-destructive">*</span></Label>
            <textarea
              value={description}
              onChange={e => setDescription(e.target.value)}
              rows={3}
              required
              placeholder="Describe the treatment plan..."
              className="w-full px-2 py-1.5 rounded border border-border bg-background text-sm focus:outline-none focus:ring-1 focus:ring-primary resize-none"
            />
          </div>
          <DialogFooter>
            <Button type="button" variant="ghost" onClick={onClose} className="h-9 px-4">Cancel</Button>
            <Button type="submit" disabled={saving} className="h-9">
              {saving ? "Saving..." : (existing ? "Update Plan" : "Create Plan")}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

// -- Detail Side Panel --------------------------------------------------------

function RiskDetailPanel({
  risk,
  levels,
  onEdit,
  onDelete,
  onAssess,
  onClose,
}: {
  risk: RiskResponse
  levels: RiskLevelOption[]
  onEdit: (r: RiskResponse) => void
  onDelete: (r: RiskResponse) => void
  onAssess: (r: RiskResponse) => void
  onClose: () => void
}) {
  const levelMeta = levels.find(l => l.name === risk.risk_level_name)
  const [tab, setTab] = useState<"details" | "assessments" | "treatment" | "activity">("details")
  const [assessments, setAssessments] = useState<RiskAssessmentResponse[]>([])
  const [loadingAssessments, setLoadingAssessments] = useState(false)
  const [treatmentPlan, setTreatmentPlan] = useState<TreatmentPlanResponse | null>(null)
  const [loadingPlan, setLoadingPlan] = useState(false)
  const [showPlanDialog, setShowPlanDialog] = useState(false)
  const [reviewEvents, setReviewEvents] = useState<RiskReviewEventResponse[]>([])
  const [loadingEvents, setLoadingEvents] = useState(false)
  const [commentText, setCommentText] = useState("")
  const [addingComment, setAddingComment] = useState(false)

  useEffect(() => {
    if (tab === "assessments") {
      setLoadingAssessments(true)
      listAssessments(risk.id)
        .then(setAssessments)
        .catch(() => setAssessments([]))
        .finally(() => setLoadingAssessments(false))
    }
    if (tab === "treatment") {
      setLoadingPlan(true)
      getTreatmentPlan(risk.id)
        .then(setTreatmentPlan)
        .catch(() => setTreatmentPlan(null))
        .finally(() => setLoadingPlan(false))
    }
    if (tab === "activity") {
      setLoadingEvents(true)
      listReviewEvents(risk.id)
        .then(setReviewEvents)
        .catch(() => setReviewEvents([]))
        .finally(() => setLoadingEvents(false))
    }
  }, [tab, risk.id])

  const handleAddComment = async () => {
    if (!commentText.trim()) return
    setAddingComment(true)
    try {
      const evt = await addReviewEvent(risk.id, { event_type: "comment", comment: commentText.trim() })
      setReviewEvents(prev => [evt, ...prev])
      setCommentText("")
    } catch {
      // silently fail — user sees no new event
    } finally {
      setAddingComment(false)
    }
  }

  return (
    <div className="fixed inset-y-0 right-0 w-full sm:w-[480px] bg-background border-l border-border shadow-xl z-40 flex flex-col">
      <div className="flex items-center justify-between px-5 py-4 border-b border-border shrink-0">
        <div className="flex items-center gap-2 min-w-0">
          <ShieldAlert className="w-4 h-4 text-primary shrink-0" />
          <span className="font-semibold text-sm truncate">{risk.title}</span>
        </div>
        <div className="flex items-center gap-1 shrink-0">
          <Button variant="ghost" size="sm" className="h-8 px-2" onClick={() => onAssess(risk)} title="Add Assessment">
            <ClipboardList className="w-3.5 h-3.5" />
          </Button>
          <Button variant="ghost" size="sm" className="h-8 px-2" onClick={() => onEdit(risk)}>
            <Pencil className="w-3.5 h-3.5" />
          </Button>
          <Button variant="ghost" size="sm" className="h-8 px-2 text-destructive hover:text-destructive" onClick={() => onDelete(risk)}>
            <Trash2 className="w-3.5 h-3.5" />
          </Button>
          <Button variant="ghost" size="sm" className="h-8 w-8 p-0" onClick={onClose}>
            <X className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-border px-5 shrink-0">
        {(["details", "assessments", "treatment", "activity"] as const).map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-3 py-2.5 text-xs font-medium border-b-2 transition-colors
              ${tab === t ? "border-primary text-primary" : "border-transparent text-muted-foreground hover:text-foreground"}`}
          >
            {t === "details" ? "Details" : t === "assessments" ? "Assessments" : t === "treatment" ? "Treatment Plan" : "Activity"}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-y-auto p-5 space-y-5">

        {/* Details tab */}
        {tab === "details" && <>
          <div className="flex items-center gap-2 flex-wrap">
            <StatusBadge status={risk.risk_status} />
            <RiskLevelBadge name={risk.risk_level_name} color={risk.risk_level_color ?? levelMeta?.color} />
          </div>

          {risk.description && (
            <div>
              <p className="text-xs font-medium text-muted-foreground mb-1">Description</p>
              <p className="text-sm text-foreground">{risk.description}</p>
            </div>
          )}

          {risk.notes && (
            <div>
              <p className="text-xs font-medium text-muted-foreground mb-1">Notes</p>
              <p className="text-sm text-foreground">{risk.notes}</p>
            </div>
          )}

          {risk.business_impact && (
            <div>
              <p className="text-xs font-medium text-muted-foreground mb-1">Business Impact</p>
              <p className="text-sm text-foreground">{risk.business_impact}</p>
            </div>
          )}

          <div className="grid grid-cols-2 gap-x-4 gap-y-3 text-xs">
            <div>
              <p className="text-muted-foreground mb-0.5">Risk Code</p>
              <p className="font-mono text-foreground">{risk.risk_code}</p>
            </div>
            <div>
              <p className="text-muted-foreground mb-0.5">Category</p>
              <p className="text-foreground">{risk.category_name}</p>
            </div>
            <div>
              <p className="text-muted-foreground mb-0.5">Treatment Type</p>
              <p className="text-foreground capitalize">{risk.treatment_type_name ?? risk.treatment_type_code}</p>
            </div>
            <div>
              <p className="text-muted-foreground mb-0.5">Source</p>
              <p className="text-foreground capitalize">{risk.source_type.replace(/_/g, " ")}</p>
            </div>
            <div>
              <p className="text-muted-foreground mb-0.5">Inherent Risk Score</p>
              <ScoreBar score={risk.inherent_risk_score} />
            </div>
            <div>
              <p className="text-muted-foreground mb-0.5">Residual Risk Score</p>
              <ScoreBar score={risk.residual_risk_score} />
            </div>
            <div>
              <p className="text-muted-foreground mb-0.5">Treatment Plan</p>
              <p className={TREATMENT_STATUS_META[risk.treatment_plan_status ?? ""]?.color ?? "text-muted-foreground"}>
                {TREATMENT_STATUS_META[risk.treatment_plan_status ?? ""]?.label ?? risk.treatment_plan_status ?? "—"}
              </p>
            </div>
            <div>
              <p className="text-muted-foreground mb-0.5">Treatment Target</p>
              <p className="flex items-center gap-1 text-foreground">
                {risk.treatment_plan_target_date
                  ? <><Clock className="w-3 h-3" /> {formatDate(risk.treatment_plan_target_date)}</>
                  : "—"}
              </p>
            </div>
            <div>
              <p className="text-muted-foreground mb-0.5">Linked Controls</p>
              <p className="font-semibold text-foreground">{risk.linked_control_count}</p>
            </div>
            <div>
              <p className="text-muted-foreground mb-0.5">Version</p>
              <p className="font-mono text-foreground">v{risk.version}</p>
            </div>
            <div>
              <p className="text-muted-foreground mb-0.5">Created</p>
              <p className="text-foreground">{formatDate(risk.created_at)}</p>
            </div>
          </div>

          <Button
            size="sm"
            variant="outline"
            className="w-full h-8 text-xs"
            onClick={() => onAssess(risk)}
          >
            <ClipboardList className="w-3.5 h-3.5 mr-1" /> Add Risk Assessment
          </Button>
        </>}

        {/* Assessments tab */}
        {tab === "assessments" && <>
          <div className="flex items-center justify-between">
            <p className="text-xs font-medium text-muted-foreground">Assessment History</p>
            <Button size="sm" variant="outline" className="h-7 text-xs" onClick={() => onAssess(risk)}>
              <Plus className="w-3 h-3 mr-1" /> Add Assessment
            </Button>
          </div>

          {loadingAssessments ? (
            <div className="text-xs text-muted-foreground">Loading assessments...</div>
          ) : assessments.length === 0 ? (
            <div className="text-xs text-muted-foreground text-center py-4">No assessments recorded yet.</div>
          ) : (
            <div className="space-y-3">
              {assessments.map((a, idx) => {
                const score = a.risk_score ?? (a.likelihood_score * a.impact_score)
                const scoreColor = riskScoreBadgeColor(score)
                return (
                  <div key={a.id} className="rounded-lg border border-border bg-card px-4 py-3 space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-medium capitalize">{a.assessment_type}</span>
                        {idx === 0 && <span className="text-xs text-primary font-medium">(Latest)</span>}
                      </div>
                      <span className={`inline-flex items-center px-2 py-0.5 rounded-full border text-xs font-semibold ${scoreColor}`}>
                        Score: {score}
                      </span>
                    </div>
                    <div className="flex items-center gap-4">
                      <RiskMatrix likelihood={a.likelihood_score} impact={a.impact_score} />
                      <div className="space-y-1 text-xs">
                        <div><span className="text-muted-foreground">Likelihood:</span> <span className="font-medium">{a.likelihood_score}/5</span></div>
                        <div><span className="text-muted-foreground">Impact:</span> <span className="font-medium">{a.impact_score}/5</span></div>
                        <div><span className="text-muted-foreground">Risk Score:</span> <span className={`font-semibold ${score >= 20 ? "text-red-600" : score >= 12 ? "text-orange-600" : score >= 6 ? "text-yellow-600" : "text-blue-600"}`}>{score}</span></div>
                      </div>
                    </div>
                    {a.assessment_notes && (
                      <p className="text-xs text-muted-foreground">{a.assessment_notes}</p>
                    )}
                    <p className="text-xs text-muted-foreground">{formatDate(a.assessed_at)}</p>
                  </div>
                )
              })}
            </div>
          )}
        </>}

        {/* Treatment Plan tab */}
        {tab === "treatment" && <>
          {loadingPlan ? (
            <div className="text-xs text-muted-foreground">Loading treatment plan...</div>
          ) : treatmentPlan ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <PlanStatusBadge status={treatmentPlan.plan_status} />
                <Button size="sm" variant="outline" className="h-7 text-xs" onClick={() => setShowPlanDialog(true)}>
                  <Pencil className="w-3 h-3 mr-1" /> Update Plan
                </Button>
              </div>
              <div className="space-y-3 text-xs">
                {treatmentPlan.target_date && (
                  <div>
                    <p className="text-muted-foreground mb-0.5">Target Date</p>
                    <p className="flex items-center gap-1 text-foreground">
                      <Clock className="w-3 h-3" /> {formatDate(treatmentPlan.target_date)}
                    </p>
                  </div>
                )}
                {treatmentPlan.properties?.plan_description && (
                  <div>
                    <p className="text-muted-foreground mb-0.5">Description</p>
                    <p className="text-sm text-foreground leading-relaxed">{treatmentPlan.properties.plan_description}</p>
                  </div>
                )}
                <div>
                  <p className="text-muted-foreground mb-0.5">Created</p>
                  <p className="text-foreground">{formatDate(treatmentPlan.created_at)}</p>
                </div>
                <div>
                  <p className="text-muted-foreground mb-0.5">Updated</p>
                  <p className="text-foreground">{formatDate(treatmentPlan.updated_at)}</p>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-6 space-y-3">
              <p className="text-xs text-muted-foreground">No treatment plan has been created for this risk.</p>
              <Button size="sm" variant="outline" className="h-8 text-xs" onClick={() => setShowPlanDialog(true)}>
                <Plus className="w-3 h-3 mr-1" /> Create Plan
              </Button>
            </div>
          )}

          {showPlanDialog && (
            <TreatmentPlanDialog
              riskId={risk.id}
              existing={treatmentPlan}
              onSaved={plan => { setTreatmentPlan(plan); setShowPlanDialog(false) }}
              onClose={() => setShowPlanDialog(false)}
            />
          )}
        </>}

        {/* Activity tab */}
        {tab === "activity" && <>
          <div className="space-y-3">
            {/* Add comment input */}
            <div className="flex gap-2">
              <input
                type="text"
                value={commentText}
                onChange={e => setCommentText(e.target.value)}
                onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleAddComment() } }}
                placeholder="Add a comment..."
                className="flex-1 h-8 px-3 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-1 focus:ring-primary"
                disabled={addingComment}
              />
              <Button
                size="sm"
                className="h-8 px-3 shrink-0"
                onClick={handleAddComment}
                disabled={addingComment || !commentText.trim()}
              >
                {addingComment ? "..." : "Post"}
              </Button>
            </div>

            {/* Events list */}
            {loadingEvents ? (
              <div className="text-xs text-muted-foreground">Loading activity...</div>
            ) : reviewEvents.length === 0 ? (
              <div className="text-xs text-muted-foreground text-center py-4">No activity recorded yet.</div>
            ) : (
              <div className="space-y-2">
                {reviewEvents.map(evt => (
                  <div key={evt.id} className="rounded-lg border border-border bg-card px-3 py-2.5 space-y-1">
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-xs font-medium capitalize text-foreground">
                        {evt.event_type.replace(/_/g, " ")}
                      </span>
                      <span className="text-xs text-muted-foreground shrink-0">
                        {formatDate(evt.occurred_at)}
                      </span>
                    </div>
                    {evt.comment && (
                      <p className="text-xs text-muted-foreground leading-relaxed">{evt.comment}</p>
                    )}
                    <p className="text-xs text-muted-foreground/60 font-mono">
                      {evt.actor_id.slice(0, 8)}…
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </>}
      </div>
    </div>
  )
}

// -- Create / Edit Risk Dialog ------------------------------------------------

function RiskDialog({
  mode,
  risk,
  categories,
  levels,
  treatmentTypes,
  onSaved,
  onClose,
  orgId,
  workspaceId,
}: {
  mode: "create" | "edit"
  risk?: RiskResponse
  categories: RiskCategoryOption[]
  levels: RiskLevelOption[]
  treatmentTypes: TreatmentTypeOption[]
  onSaved: (r: RiskResponse) => void
  onClose: () => void
  orgId?: string
  workspaceId?: string
}) {
  const [title, setTitle] = useState(risk?.title ?? "")
  const [code, setCode] = useState(risk?.risk_code ?? "")
  const [desc, setDesc] = useState(risk?.description ?? "")
  const [notes, setNotes] = useState(risk?.notes ?? "")
  const [categoryCode, setCategoryCode] = useState(risk?.risk_category_code ?? categories[0]?.code ?? "")
  const [levelCode, setLevelCode] = useState(risk?.risk_level_code ?? levels[0]?.code ?? "")
  const [treatmentCode, setTreatmentCode] = useState(risk?.treatment_type_code ?? treatmentTypes[0]?.code ?? "mitigate")
  const [status, setStatus] = useState(risk?.risk_status ?? "identified")
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Auto-generate code from title on create
  useEffect(() => {
    if (mode === "create" && title) {
      setCode(
        title.toUpperCase()
          .replace(/[^A-Z0-9\s]/g, "")
          .trim()
          .replace(/\s+/g, "_")
          .slice(0, 24)
      )
    }
  }, [mode, title])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setError(null)
    try {
      let result: RiskResponse
      if (mode === "create") {
        const payload: CreateRiskRequest = {
          risk_code: code,
          title,
          description: desc || undefined,
          risk_category_code: categoryCode,
          risk_level_code: levelCode,
          treatment_type_code: treatmentCode,
          source_type: "manual",
          org_id: orgId || "00000000-0000-0000-0000-000000000000",
          workspace_id: workspaceId || undefined,
        }
        result = await createRisk(payload)
      } else {
        const payload: UpdateRiskRequest = {
          title,
          description: desc || undefined,
          notes: notes || undefined,
          risk_category_code: categoryCode,
          treatment_type_code: treatmentCode,
          risk_status: status,
        }
        result = await updateRisk(risk!.id, payload)
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
          <DialogTitle>{mode === "create" ? "Create Risk" : "Edit Risk"}</DialogTitle>
          <DialogDescription>
            {mode === "create"
              ? "Register a new risk in the risk registry."
              : "Update risk details and status."}
          </DialogDescription>
        </DialogHeader>

        {error && <div className="text-xs text-destructive bg-destructive/10 rounded-lg px-3 py-2">{error}</div>}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label className="text-xs text-muted-foreground mb-1 block">Title <span className="text-destructive">*</span></Label>
            <Input value={title} onChange={e => setTitle(e.target.value)} placeholder="e.g. Data Breach Risk" required className="h-8 text-sm" />
          </div>

          {mode === "create" && (
            <div>
              <Label className="text-xs text-muted-foreground mb-1 block">Risk Code <span className="text-destructive">*</span></Label>
              <Input
                value={code}
                onChange={e => setCode(e.target.value.toUpperCase().replace(/[^A-Z0-9_-]/g, "_"))}
                placeholder="Auto-generated from title"
                required
                className="h-8 text-sm font-mono"
              />
            </div>
          )}

          <div>
            <Label className="text-xs text-muted-foreground mb-1 block">Description</Label>
            <Input value={desc} onChange={e => setDesc(e.target.value)} placeholder="Describe the risk scenario" className="h-8 text-sm" />
          </div>

          {mode === "edit" && (
            <div>
              <Label className="text-xs text-muted-foreground mb-1 block">Notes</Label>
              <Input value={notes} onChange={e => setNotes(e.target.value)} placeholder="Additional notes" className="h-8 text-sm" />
            </div>
          )}

          <div className="grid grid-cols-2 gap-3">
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
            <div>
              <Label className="text-xs text-muted-foreground mb-1 block">Risk Level</Label>
              <select
                value={levelCode}
                onChange={e => setLevelCode(e.target.value)}
                className="w-full h-8 px-2 rounded border border-border bg-background text-sm focus:outline-none focus:ring-1 focus:ring-primary"
              >
                {levels.map(l => <option key={l.code} value={l.code}>{l.name}</option>)}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label className="text-xs text-muted-foreground mb-1 block">Treatment Type</Label>
              <select
                value={treatmentCode}
                onChange={e => setTreatmentCode(e.target.value)}
                className="w-full h-8 px-2 rounded border border-border bg-background text-sm focus:outline-none focus:ring-1 focus:ring-primary"
              >
                {treatmentTypes.length > 0
                  ? treatmentTypes.map(t => <option key={t.code} value={t.code}>{t.name}</option>)
                  : (
                    <>
                      <option value="mitigate">Mitigate</option>
                      <option value="accept">Accept</option>
                      <option value="transfer">Transfer</option>
                      <option value="avoid">Avoid</option>
                    </>
                  )}
              </select>
            </div>
            {mode === "edit" && (
              <div>
                <Label className="text-xs text-muted-foreground mb-1 block">Status</Label>
                <select
                  value={status}
                  onChange={e => setStatus(e.target.value)}
                  className="w-full h-8 px-2 rounded border border-border bg-background text-sm focus:outline-none focus:ring-1 focus:ring-primary"
                >
                  {Object.entries(RISK_STATUS_META).map(([k, v]) => (
                    <option key={k} value={k}>{v.label}</option>
                  ))}
                </select>
              </div>
            )}
          </div>

          <DialogFooter>
            <Button type="button" variant="ghost" onClick={onClose} className="h-9 px-4">Cancel</Button>
            <Button type="submit" disabled={saving} className="h-9">
              {saving ? (mode === "create" ? "Creating..." : "Saving...") : (mode === "create" ? "Create Risk" : "Save Changes")}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

// -- Assessment Dialog --------------------------------------------------------

function AssessmentDialog({
  risk,
  onClose,
}: {
  risk: RiskResponse
  onClose: () => void
}) {
  const [assessmentType, setAssessmentType] = useState("inherent")
  const [likelihood, setLikelihood] = useState(3)
  const [impact, setImpact] = useState(3)
  const [notes, setNotes] = useState("")
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  const score = likelihood * impact

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setError(null)
    try {
      const payload: CreateRiskAssessmentRequest = {
        assessment_type: assessmentType,
        likelihood_score: likelihood,
        impact_score: impact,
        assessment_notes: notes || undefined,
      }
      await createAssessment(risk.id, payload)
      setSuccess(true)
      setTimeout(() => onClose(), 1200)
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <Dialog open onOpenChange={(open) => { if (!open) onClose() }}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Add Risk Assessment</DialogTitle>
          <DialogDescription>Record a 5×5 risk assessment for: <strong>{risk.title}</strong></DialogDescription>
        </DialogHeader>

        {error && <div className="text-xs text-destructive bg-destructive/10 rounded-lg px-3 py-2">{error}</div>}
        {success && <div className="text-xs text-emerald-600 bg-emerald-500/10 rounded-lg px-3 py-2">Assessment saved successfully.</div>}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label className="text-xs text-muted-foreground mb-1 block">Assessment Type</Label>
            <select
              value={assessmentType}
              onChange={e => setAssessmentType(e.target.value)}
              className="w-full h-8 px-2 rounded border border-border bg-background text-sm focus:outline-none focus:ring-1 focus:ring-primary"
            >
              <option value="inherent">Inherent Risk</option>
              <option value="residual">Residual Risk</option>
            </select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label className="text-xs text-muted-foreground mb-2 block">Likelihood (1–5): {likelihood}</Label>
              <input
                type="range"
                min="1"
                max="5"
                value={likelihood}
                onChange={e => setLikelihood(Number(e.target.value))}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-muted-foreground mt-1">
                <span>Rare</span><span>Almost Certain</span>
              </div>
            </div>
            <div>
              <Label className="text-xs text-muted-foreground mb-2 block">Impact (1–5): {impact}</Label>
              <input
                type="range"
                min="1"
                max="5"
                value={impact}
                onChange={e => setImpact(Number(e.target.value))}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-muted-foreground mt-1">
                <span>Minimal</span><span>Catastrophic</span>
              </div>
            </div>
          </div>

          <div className="rounded-lg border border-border bg-muted/30 px-4 py-3 flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Risk Score</span>
            <span className={`text-lg font-bold ${score >= 20 ? "text-red-600" : score >= 12 ? "text-orange-600" : score >= 6 ? "text-yellow-600" : "text-emerald-600"}`}>
              {score} / 25
            </span>
          </div>

          <div>
            <Label className="text-xs text-muted-foreground mb-1 block">Assessment Notes</Label>
            <Input value={notes} onChange={e => setNotes(e.target.value)} placeholder="Add context for this assessment" className="h-8 text-sm" />
          </div>

          <DialogFooter>
            <Button type="button" variant="ghost" onClick={onClose} className="h-9 px-4">Cancel</Button>
            <Button type="submit" disabled={saving || success} className="h-9">
              {saving ? "Saving..." : "Save Assessment"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

// -- Delete Confirm -----------------------------------------------------------

function DeleteConfirmDialog({
  risk,
  onConfirm,
  onClose,
}: {
  risk: RiskResponse
  onConfirm: () => Promise<void>
  onClose: () => void
}) {
  const [deleting, setDeleting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleDelete = async () => {
    setDeleting(true)
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
          <DialogTitle>Delete Risk</DialogTitle>
          <DialogDescription>
            Are you sure you want to delete <strong>{risk.title}</strong>? This action cannot be undone.
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
function AdminRisksPageContent() {
  const { selectedOrgId, selectedWorkspaceId } = useOrgWorkspace()
  const [risks, setRisks] = useState<RiskResponse[]>([])
  const [categories, setCategories] = useState<RiskCategoryOption[]>([])
  const [levels, setLevels] = useState<RiskLevelOption[]>([])
  const [treatmentTypes, setTreatmentTypes] = useState<TreatmentTypeOption[]>([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // dialogs
  const [showCreate, setShowCreate] = useState(false)
  const [editTarget, setEditTarget] = useState<RiskResponse | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<RiskResponse | null>(null)
  const [detailTarget, setDetailTarget] = useState<RiskResponse | null>(null)
  const [assessTarget, setAssessTarget] = useState<RiskResponse | null>(null)

  // filters
  const [search, setSearch] = useState("")
  const [filterCategory, setFilterCategory] = useState("")
  const [filterStatus, setFilterStatus] = useState("")
  const [filterLevel, setFilterLevel] = useState("")
  const [filterTreatment, setFilterTreatment] = useState("")

  // sort + pagination
  const [sortBy, setSortBy] = useState<SortField>("created_at")
  const [sortDir, setSortDir] = useState<SortDir>("desc")
  const [page, setPage] = useState(0)

  const load = useCallback(async (quiet = false) => {
    if (quiet) setRefreshing(true); else setLoading(true)
    setError(null)
    try {
      const [risksRes, catsRes, levelsRes, treatRes] = await Promise.all([
        listRisks(),
        listRiskCategories(),
        listRiskLevels(),
        listTreatmentTypes(),
      ])
      setRisks(risksRes.items ?? [])
      setCategories(Array.isArray(catsRes) ? catsRes : [])
      setLevels(Array.isArray(levelsRes) ? levelsRes.map(l => ({ code: l.code, name: l.name, color: l.color_hex, sort_order: l.sort_order })) : [])
      setTreatmentTypes(Array.isArray(treatRes) ? treatRes : [])
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  const handleSaved = useCallback((risk: RiskResponse) => {
    setRisks(prev => {
      const idx = prev.findIndex(r => r.id === risk.id)
      if (idx >= 0) {
        const next = [...prev]
        next[idx] = risk
        return next
      }
      return [risk, ...prev]
    })
  }, [])

  const handleDelete = useCallback(async (risk: RiskResponse) => {
    await deleteRisk(risk.id)
    setRisks(prev => prev.filter(r => r.id !== risk.id))
    if (detailTarget?.id === risk.id) setDetailTarget(null)
  }, [detailTarget])

  const handleSort = (field: SortField) => {
    if (sortBy === field) setSortDir(d => d === "asc" ? "desc" : "asc")
    else { setSortBy(field); setSortDir("asc") }
    setPage(0)
  }

  const filtered = useMemo(() => {
    let items = risks.filter(risk => {
      if (search.trim()) {
        const q = search.toLowerCase()
        if (!risk.title.toLowerCase().includes(q) && !risk.risk_code.toLowerCase().includes(q)) return false
      }
      if (filterCategory && risk.risk_category_code !== filterCategory) return false
      if (filterStatus && risk.risk_status !== filterStatus) return false
      if (filterLevel && risk.risk_level_code !== filterLevel) return false
      if (filterTreatment && risk.treatment_type_code !== filterTreatment) return false
      return true
    })

    items = [...items].sort((a, b) => {
      let av: string | number = ""
      let bv: string | number = ""
      if (sortBy === "title") { av = a.title ?? ""; bv = b.title ?? "" }
      else if (sortBy === "risk_level_name") { av = a.risk_level_name ?? ""; bv = b.risk_level_name ?? "" }
      else if (sortBy === "risk_status") { av = a.risk_status; bv = b.risk_status }
      else if (sortBy === "created_at") { av = a.created_at; bv = b.created_at }
      else if (sortBy === "residual_risk_score") { av = a.residual_risk_score ?? -1; bv = b.residual_risk_score ?? -1 }
      if (typeof av === "number" && typeof bv === "number") {
        return sortDir === "asc" ? av - bv : bv - av
      }
      const cmp = String(av).localeCompare(String(bv))
      return sortDir === "asc" ? cmp : -cmp
    })

    return items
  }, [risks, search, filterCategory, filterStatus, filterLevel, filterTreatment, sortBy, sortDir])

  const totalPages = Math.ceil(filtered.length / PAGE_SIZE)
  const paginated = filtered.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE)
  const hasFilters = search.trim() || filterCategory || filterStatus || filterLevel || filterTreatment

  const clearFilters = () => {
    setSearch(""); setFilterCategory(""); setFilterStatus(""); setFilterLevel(""); setFilterTreatment(""); setPage(0)
  }

  const exportCsv = () => {
    const rows = [
      ["code", "title", "category", "risk_level", "status", "treatment_type", "inherent_score", "residual_score", "linked_controls", "created_at"],
      ...filtered.map(r => [
        r.risk_code,
        r.title,
        r.category_name,
        r.risk_level_name,
        r.risk_status,
        r.treatment_type_name ?? r.treatment_type_code,
        String(r.inherent_risk_score ?? ""),
        String(r.residual_risk_score ?? ""),
        String(r.linked_control_count),
        r.created_at,
      ]),
    ]
    const csv = rows.map(row => row.map(v => `"${String(v).replace(/"/g, '""')}"`).join(",")).join("\n")
    const blob = new Blob([csv], { type: "text/csv" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = "risks.csv"
    a.click()
    URL.revokeObjectURL(url)
  }

  const totalRisks = risks.length
  const criticalHighCount = risks.filter(r => ["critical", "high"].includes(r.risk_level_name?.toLowerCase() ?? "")).length
  const openCount = risks.filter(r => r.risk_status !== "closed" && r.risk_status !== "accepted").length

  // chip labels
  const filterCategoryName = categories.find(c => c.code === filterCategory)?.name ?? filterCategory
  const filterLevelName = levels.find(l => l.code === filterLevel)?.name ?? filterLevel
  const filterTreatmentName = treatmentTypes.find(t => t.code === filterTreatment)?.name ?? filterTreatment
  const filterStatusName = RISK_STATUS_META[filterStatus]?.label ?? filterStatus

  const statCards = [
    { label: "Total Risks",     value: totalRisks,       icon: ShieldAlert },
    { label: "Critical / High", value: criticalHighCount, icon: AlertTriangle },
    { label: "Open Risks",      value: openCount,        icon: Activity },
  ]

  return (
    <div className={`p-6 space-y-6 ${detailTarget ? "mr-[480px]" : ""} max-w-5xl transition-all`}>
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold">Risk Registry</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            Track, assess, and manage organizational risks across all domains
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
            <Plus className="w-3.5 h-3.5 mr-1" /> Create Risk
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
        <div className="flex items-center gap-2 flex-wrap">
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-3 top-2.5 w-4 h-4 text-muted-foreground" />
            <Input
              className="pl-9 h-9"
              placeholder="Search risks by title or code..."
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
          {levels.length > 0 && (
            <select
              value={filterLevel}
              onChange={e => { setFilterLevel(e.target.value); setPage(0) }}
              className="h-9 px-3 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-1 focus:ring-primary"
            >
              <option value="">All Levels</option>
              {levels.sort((a, b) => b.sort_order - a.sort_order).map(l => <option key={l.code} value={l.code}>{l.name}</option>)}
            </select>
          )}
          <select
            value={filterStatus}
            onChange={e => { setFilterStatus(e.target.value); setPage(0) }}
            className="h-9 px-3 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-1 focus:ring-primary"
          >
            <option value="">All Statuses</option>
            {Object.entries(RISK_STATUS_META).map(([k, v]) => (
              <option key={k} value={k}>{v.label}</option>
            ))}
          </select>
          {treatmentTypes.length > 0 && (
            <select
              value={filterTreatment}
              onChange={e => { setFilterTreatment(e.target.value); setPage(0) }}
              className="h-9 px-3 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-1 focus:ring-primary"
            >
              <option value="">All Treatments</option>
              {treatmentTypes.map(t => <option key={t.code} value={t.code}>{t.name}</option>)}
            </select>
          )}
        </div>

        {/* Active chips */}
        {hasFilters && (
          <div className="flex items-center gap-2 flex-wrap">
            {search.trim() && <FilterChip label={`"${search}"`} onRemove={() => { setSearch(""); setPage(0) }} />}
            {filterCategory && <FilterChip label={filterCategoryName} onRemove={() => { setFilterCategory(""); setPage(0) }} />}
            {filterLevel && <FilterChip label={filterLevelName} onRemove={() => { setFilterLevel(""); setPage(0) }} />}
            {filterStatus && <FilterChip label={filterStatusName} onRemove={() => { setFilterStatus(""); setPage(0) }} />}
            {filterTreatment && <FilterChip label={filterTreatmentName} onRemove={() => { setFilterTreatment(""); setPage(0) }} />}
            <button
              type="button"
              className="text-xs text-muted-foreground hover:text-foreground ml-1"
              onClick={clearFilters}
            >
              Clear all
            </button>
          </div>
        )}
      </div>

      {/* Sort + count */}
      {!loading && !error && (
        <div className="flex items-center gap-4 text-xs text-muted-foreground flex-wrap">
          <span>Showing {filtered.length} of {risks.length} risks</span>
          <span className="text-muted-foreground/50">|</span>
          <span>Sort by:</span>
          {(["title", "risk_level_name", "risk_status", "residual_risk_score", "created_at"] as SortField[]).map(f => (
            <button
              key={f}
              className={`hover:text-foreground transition-colors ${sortBy === f ? "text-foreground font-medium" : ""}`}
              onClick={() => handleSort(f)}
            >
              {f === "risk_level_name" ? "Level" : f === "risk_status" ? "Status" : f === "residual_risk_score" ? "Risk Score" : f === "created_at" ? "Created" : "Title"}
              <SortIcon field={f} sortBy={sortBy} sortDir={sortDir} />
            </button>
          ))}
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

      {/* List */}
      {!loading && !error && (
        <div className="space-y-1.5">
          {paginated.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-8">
              {hasFilters ? "No risks match your filters." : "No risks registered yet. Create your first risk to get started."}
            </p>
          ) : (
            paginated.map(risk => {
              const levelMeta = levels.find(l => l.code === risk.risk_level_code)
              const borderCls = riskBorderCls(risk.risk_level_name ?? "")
              return (
                <div
                  key={risk.id ?? risk.risk_code}
                  className={`flex items-center gap-3 px-4 py-3 rounded-xl border border-l-[3px] ${borderCls} transition-colors cursor-pointer
                    ${detailTarget?.id === risk.id ? "border-primary/20 bg-primary/5" : "border-border bg-card hover:border-border/80 hover:bg-muted/30"}`}
                  onClick={() => setDetailTarget(prev => prev?.id === risk.id ? null : risk)}
                >
                  <div className="shrink-0 rounded-lg p-2 bg-muted">
                    <ShieldAlert className="w-3.5 h-3.5 text-primary" />
                  </div>

                  <div className="flex-1 min-w-0 flex items-center gap-2 flex-wrap">
                    <span className="font-medium text-sm truncate">{risk.title}</span>
                    <span className="font-mono text-xs text-muted-foreground hidden sm:inline">{risk.risk_code}</span>
                    <RiskLevelBadge name={risk.risk_level_name} color={risk.risk_level_color ?? levelMeta?.color} />
                    <StatusBadge status={risk.risk_status} />
                    {risk.version > 1 && (
                      <span className="font-mono text-[10px] text-muted-foreground border border-border/50 rounded px-1 hidden md:inline">v{risk.version}</span>
                    )}
                  </div>

                  <div className="flex items-center gap-4 shrink-0 text-xs text-muted-foreground">
                    <span className="hidden md:flex items-center gap-1">
                      <TrendingUp className="w-3 h-3" />
                      {risk.inherent_risk_score ?? "--"}
                    </span>
                    <span className="hidden md:flex items-center gap-1">
                      <TrendingDown className="w-3 h-3" />
                      {risk.residual_risk_score ?? "--"}
                    </span>
                    <span className="hidden lg:inline">{risk.category_name}</span>
                    <span className="hidden sm:inline">{formatDate(risk.created_at)}</span>
                  </div>

                  <div className="flex items-center gap-1 shrink-0" onClick={e => e.stopPropagation()}>
                    <Button variant="ghost" size="sm" className="h-7 w-7 p-0" onClick={() => setAssessTarget(risk)} title="Assess">
                      <ClipboardList className="w-3 h-3" />
                    </Button>
                    <Button variant="ghost" size="sm" className="h-7 w-7 p-0" onClick={() => setEditTarget(risk)} title="Edit">
                      <Pencil className="w-3 h-3" />
                    </Button>
                    <Button variant="ghost" size="sm" className="h-7 w-7 p-0 text-destructive hover:text-destructive" onClick={() => setDeleteTarget(risk)} title="Delete">
                      <Trash2 className="w-3 h-3" />
                    </Button>
                  </div>
                </div>
              )
            })
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
            <Button variant="ghost" size="sm" className="h-8 w-8 p-0" disabled={page === 0} onClick={() => setPage(p => p - 1)}>
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
            <Button variant="ghost" size="sm" className="h-8 w-8 p-0" disabled={page >= totalPages - 1} onClick={() => setPage(p => p + 1)}>
              <ChevronRight className="w-4 h-4" />
            </Button>
          </div>
        </div>
      )}

      {/* Detail panel */}
      {detailTarget && (
        <>
          <div className="fixed inset-0 z-30" onClick={() => setDetailTarget(null)} />
          <RiskDetailPanel
            risk={detailTarget}
            levels={levels}
            onEdit={r => { setDetailTarget(null); setEditTarget(r) }}
            onDelete={r => { setDetailTarget(null); setDeleteTarget(r) }}
            onAssess={r => { setAssessTarget(r) }}
            onClose={() => setDetailTarget(null)}
          />
        </>
      )}

      {/* Dialogs */}
      {showCreate && (
        <RiskDialog
          mode="create"
          categories={categories}
          levels={levels}
          treatmentTypes={treatmentTypes}
          onSaved={r => { handleSaved(r as RiskResponse); setShowCreate(false) }}
          onClose={() => setShowCreate(false)}
          orgId={selectedOrgId || undefined}
          workspaceId={selectedWorkspaceId || undefined}
        />
      )}
      {editTarget && (
        <RiskDialog
          mode="edit"
          risk={editTarget}
          categories={categories}
          levels={levels}
          treatmentTypes={treatmentTypes}
          onSaved={r => { handleSaved(r as RiskResponse); setEditTarget(null) }}
          onClose={() => setEditTarget(null)}
        />
      )}
      {deleteTarget && (
        <DeleteConfirmDialog
          risk={deleteTarget}
          onConfirm={() => handleDelete(deleteTarget)}
          onClose={() => setDeleteTarget(null)}
        />
      )}
      {assessTarget && (
        <AssessmentDialog
          risk={assessTarget}
          onClose={() => { setAssessTarget(null); load(true) }}
        />
      )}
    </div>
  )
}

export default function AdminRisksPage() {
  return (
    <OrgWorkspaceProvider>
      <AdminRisksPageContent />
    </OrgWorkspaceProvider>
  )
}
