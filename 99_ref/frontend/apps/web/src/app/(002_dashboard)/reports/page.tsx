"use client"

import { useEffect, useLayoutEffect, useState, useCallback, useRef, useMemo } from "react"
import Link from "next/link"
import { MarkdownRenderer } from "@/components/ui/MarkdownRenderer"
import {
  FileText, Plus, Download, Trash2, RefreshCw, Clock, CheckCircle2,
  XCircle, Loader2, Eye, BarChart3, ShieldCheck, AlertTriangle,
  ClipboardList, BookOpen, TrendingUp, Map, Users, Wrench, Activity,
  Globe, LayoutGrid, ChevronDown, Sparkles, X, ChevronRight, Pencil, Save,
  ClipboardCheck, Search, Lock, CheckSquare, MessageSquare,
} from "lucide-react"
import {
  generateReport, listReports, getReport, updateReport, deleteReport,
  downloadReport, REPORT_TYPE_LABELS,
  downloadReportMarkdown, streamEnhanceReportSection, streamSuggestAssessment,
  type ReportSummaryResponse, type ReportResponse, type GenerateReportRequest,
  type AssessmentSuggestion,
} from "@/lib/api/ai"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@kcontrol/ui"
import { getControl, getFramework, getRisk, listAllControls, listRisks, listFrameworks } from "@/lib/api/grc"
import { engagementsApi, type Engagement } from "@/lib/api/engagements"
import { useOrgWorkspace } from "@/lib/context/OrgWorkspaceContext"
import { getReportPdfBlobUrl, getReportPdfFilename, type ReportPdfMeta, type PdfTemplateConfig } from "@/lib/utils/exportReportPdf"
import { listPdfTemplates, type PdfTemplateResponse } from "@/lib/api/pdfTemplates"
import {
  listAssessments, listAssessmentTypes, listAssessmentStatuses,
  createAssessment, updateAssessment, completeAssessment, deleteAssessment,
  listFindings, createFinding, updateFinding, deleteFinding,
  listFindingResponses, createFindingResponse, getAssessmentSummary,
} from "@/lib/api/assessments"
import type {
  AssessmentResponse, AssessmentDimension, FindingResponse,
  FindingResponseResponse, AssessmentSummaryResponse,
  CreateAssessmentRequest, CreateFindingRequest,
} from "@/lib/types/assessments"
import {
  Card, CardContent, Button, Input, Label,
  Dialog, DialogContent, DialogHeader, DialogFooter,
  DialogTitle, DialogDescription,
} from "@kcontrol/ui"

// ── Types & constants ────────────────────────────────────────────────────────

type ReportScope = "workspace" | "framework" | "control" | "risk" | "task"

type ReportLinkedEntityType = "workspace" | "engagement" | "framework" | "control" | "risk"

type ReportLinkedEntityRef = {
  type: ReportLinkedEntityType
  id: string
  cacheKey: string
  href?: string
  fallbackLabel: string
  frameworkId?: string
}

interface ReportScopeDef {
  scope: ReportScope
  label: string
  description: string
  pickers: Array<"workspace" | "framework" | "control" | "risk" | "task">
  required: Array<"framework" | "control" | "risk" | "task">
}

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" ? value as Record<string, unknown> : {}
}

function asString(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value : null
}

function dedupeLinkedEntities(items: ReportLinkedEntityRef[]): ReportLinkedEntityRef[] {
  const seen = new Set<string>()
  return items.filter(item => {
    if (seen.has(item.cacheKey)) return false
    seen.add(item.cacheKey)
    return true
  })
}

function getReportLinkedEntityRefs(
  report: Pick<ReportSummaryResponse, "workspace_id" | "parameters_json" | "trigger_entity_type" | "trigger_entity_id">,
  workspaceName?: string,
): ReportLinkedEntityRef[] {
  const params = asRecord(report.parameters_json)
  const frameworkId = asString(params.framework_id)
  const controlId = asString(params.control_id)
  const riskId = asString(params.risk_id)
  const engagementId =
    (report.trigger_entity_type === "engagement" ? report.trigger_entity_id : null) ??
    asString(params.engagement_id)

  const refs: ReportLinkedEntityRef[] = []

  if (engagementId) {
    refs.push({
      type: "engagement",
      id: engagementId,
      cacheKey: `engagement:${engagementId}`,
      fallbackLabel: "Engagement",
    })
  }
  if (frameworkId) {
    refs.push({
      type: "framework",
      id: frameworkId,
      cacheKey: `framework:${frameworkId}`,
      href: `/frameworks/${frameworkId}`,
      fallbackLabel: "Framework",
    })
  }
  if (controlId) {
    refs.push({
      type: "control",
      id: controlId,
      cacheKey: `control:${controlId}`,
      href: frameworkId ? `/controls/${frameworkId}/${controlId}` : undefined,
      fallbackLabel: "Control",
      frameworkId: frameworkId ?? undefined,
    })
  }
  if (riskId) {
    refs.push({
      type: "risk",
      id: riskId,
      cacheKey: `risk:${riskId}`,
      href: `/risks/${riskId}`,
      fallbackLabel: "Risk",
    })
  }
  if (report.workspace_id && workspaceName) {
    refs.push({
      type: "workspace",
      id: report.workspace_id,
      cacheKey: `workspace:${report.workspace_id}`,
      href: "/workspaces",
      fallbackLabel: workspaceName,
    })
  }

  return dedupeLinkedEntities(refs)
}

function SourceBadge({ entity, label }: { entity: ReportLinkedEntityRef; label: string }) {
  const chip = (
    <span className="inline-flex items-center gap-1 rounded-full border border-border/70 bg-muted/50 px-2 py-1 text-[10px] font-medium text-muted-foreground">
      <span className="capitalize">{entity.type}</span>
      <span className="text-foreground">{label}</span>
    </span>
  )

  if (!entity.href) return chip

  return (
    <Link href={entity.href} onClick={e => e.stopPropagation()} className="transition-opacity hover:opacity-80">
      {chip}
    </Link>
  )
}

const REPORT_SCOPE_MAP: Record<string, ReportScopeDef> = {
  executive_summary: { scope: "workspace", label: "Workspace", description: "Executive overview of the workspace", pickers: ["workspace"], required: [] },
  compliance_posture: { scope: "workspace", label: "Workspace", description: "Cross-framework compliance posture", pickers: ["workspace"], required: [] },
  board_risk_report: { scope: "workspace", label: "Workspace", description: "Board-level risk summary", pickers: ["workspace"], required: [] },
  vendor_risk: { scope: "workspace", label: "Workspace", description: "Third-party and vendor risk", pickers: ["workspace"], required: [] },
  remediation_plan: { scope: "workspace", label: "Workspace", description: "Prioritized remediation plan", pickers: ["workspace", "framework"], required: [] },
  audit_trail: { scope: "workspace", label: "Workspace", description: "Audit trail and event timeline", pickers: ["workspace"], required: [] },
  framework_compliance: { scope: "framework", label: "Framework", description: "Compliance status for a framework", pickers: ["workspace", "framework"], required: ["framework"] },
  framework_readiness: { scope: "framework", label: "Framework", description: "Readiness assessment for a framework", pickers: ["workspace", "framework"], required: ["framework"] },
  framework_gap_analysis: { scope: "framework", label: "Framework", description: "Gap analysis against a framework", pickers: ["workspace", "framework"], required: ["framework"] },
  control_status: { scope: "control", label: "Control", description: "Status for a control or all controls", pickers: ["workspace", "framework", "control"], required: [] },
  evidence_report: { scope: "control", label: "Control", description: "Evidence adequacy for a control", pickers: ["workspace", "framework", "control"], required: [] },
  risk_summary: { scope: "risk", label: "Risk", description: "Summary for a risk or all risks", pickers: ["workspace", "framework", "risk"], required: [] },
  task_health: { scope: "task", label: "Task", description: "Task backlog health and overdue analysis", pickers: ["workspace", "framework"], required: [] },
}

const SCOPE_ACCENT: Record<ReportScope, { border: string; text: string; badge: string; bg: string }> = {
  workspace: { border: "border-l-sky-500", text: "text-sky-500", badge: "bg-sky-500/10 text-sky-500 border-sky-500/30", bg: "bg-sky-500/5" },
  framework: { border: "border-l-violet-500", text: "text-violet-500", badge: "bg-violet-500/10 text-violet-500 border-violet-500/30", bg: "bg-violet-500/5" },
  control: { border: "border-l-emerald-500", text: "text-emerald-500", badge: "bg-emerald-500/10 text-emerald-500 border-emerald-500/30", bg: "bg-emerald-500/5" },
  risk: { border: "border-l-orange-500", text: "text-orange-500", badge: "bg-orange-500/10 text-orange-500 border-orange-500/30", bg: "bg-orange-500/5" },
  task: { border: "border-l-amber-500", text: "text-amber-500", badge: "bg-amber-500/10 text-amber-500 border-amber-500/30", bg: "bg-amber-500/5" },
}

const STATUS_CONFIG: Record<string, { icon: React.ReactNode; color: string; badge: string; label: string }> = {
  queued: { icon: <Clock className="w-3 h-3" />, color: "text-muted-foreground", badge: "bg-muted text-muted-foreground border-border", label: "Queued" },
  planning: { icon: <Loader2 className="w-3 h-3 animate-spin" />, color: "text-blue-500", badge: "bg-blue-500/10 text-blue-500 border-blue-500/30", label: "Planning" },
  collecting: { icon: <Loader2 className="w-3 h-3 animate-spin" />, color: "text-blue-500", badge: "bg-blue-500/10 text-blue-500 border-blue-500/30", label: "Collecting" },
  analyzing: { icon: <Loader2 className="w-3 h-3 animate-spin" />, color: "text-violet-500", badge: "bg-violet-500/10 text-violet-500 border-violet-500/30", label: "Analyzing" },
  writing: { icon: <Loader2 className="w-3 h-3 animate-spin" />, color: "text-amber-500", badge: "bg-amber-500/10 text-amber-500 border-amber-500/30", label: "Writing" },
  formatting: { icon: <Loader2 className="w-3 h-3 animate-spin" />, color: "text-amber-500", badge: "bg-amber-500/10 text-amber-500 border-amber-500/30", label: "Formatting" },
  completed: { icon: <CheckCircle2 className="w-3 h-3" />, color: "text-emerald-500", badge: "bg-emerald-500/10 text-emerald-500 border-emerald-500/30", label: "Completed" },
  failed: { icon: <XCircle className="w-3 h-3" />, color: "text-red-500", badge: "bg-red-500/10 text-red-500 border-red-500/30", label: "Failed" },
}

const REPORT_TYPE_ICONS: Record<string, React.ReactNode> = {
  executive_summary: <BarChart3 className="w-4 h-4" />,
  compliance_posture: <Activity className="w-4 h-4" />,
  framework_compliance: <ShieldCheck className="w-4 h-4" />,
  framework_readiness: <TrendingUp className="w-4 h-4" />,
  framework_gap_analysis: <Map className="w-4 h-4" />,
  control_status: <ClipboardList className="w-4 h-4" />,
  risk_summary: <AlertTriangle className="w-4 h-4" />,
  board_risk_report: <Globe className="w-4 h-4" />,
  vendor_risk: <Users className="w-4 h-4" />,
  remediation_plan: <Wrench className="w-4 h-4" />,
  task_health: <CheckCircle2 className="w-4 h-4" />,
  audit_trail: <BookOpen className="w-4 h-4" />,
  evidence_report: <Eye className="w-4 h-4" />,
}

const IN_PROGRESS = new Set(["queued", "planning", "collecting", "analyzing", "writing", "formatting"])
const SCOPE_ORDER: ReportScope[] = ["workspace", "framework", "control", "risk", "task"]

// ── Scope badge ───────────────────────────────────────────────────────────────

function ScopeBadge({ reportType }: { reportType: string }) {
  const def = REPORT_SCOPE_MAP[reportType]
  if (!def) return null
  const a = SCOPE_ACCENT[def.scope]
  return (
    <span className={`inline-flex items-center px-1.5 py-0.5 rounded-full text-[10px] font-semibold border ${a.badge}`}>
      {def.label}
    </span>
  )
}

// ── Generate dialog ───────────────────────────────────────────────────────────

function GenerateDialog({
  orgId, workspaceId, workspaceName, onClose, onGenerated, prefill,
}: {
  orgId: string; workspaceId: string; workspaceName: string
  onClose: () => void; onGenerated: (r: ReportResponse) => void
  prefill?: { report_type?: string; framework_id?: string; engagement_id?: string; title?: string }
}) {
  const [reportType, setReportType] = useState(prefill?.report_type ?? "executive_summary")
  const [title, setTitle] = useState(prefill?.title ?? "")
  const [engagementId, setEngagementId] = useState(prefill?.engagement_id ?? "")
  const [selectedFrameworkId, setSelectedFrameworkId] = useState(prefill?.framework_id ?? "")
  const [controlId, setControlId] = useState("")
  const [riskId, setRiskId] = useState("")
  const [engagements, setEngagements] = useState<Engagement[]>([])
  const [frameworks, setFrameworks] = useState<{ id: string; name: string; framework_code: string }[]>([])
  const [controls, setControls] = useState<{ id: string; name: string; code: string }[]>([])
  const [risks, setRisks] = useState<{ id: string; name: string; level_code: string }[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const scopeDef = REPORT_SCOPE_MAP[reportType] ?? { scope: "workspace", pickers: [], required: [] }
  const needsControl = scopeDef.pickers.includes("control")
  const needsRisk = scopeDef.pickers.includes("risk")
  const selectedEngagement = useMemo(
    () => engagements.find((engagement) => engagement.id === engagementId) ?? null,
    [engagementId, engagements],
  )
  const engagementFrameworkId = selectedEngagement?.framework_id ?? ""
  const frameworkId = selectedFrameworkId || engagementFrameworkId

  useEffect(() => {
    engagementsApi.list(orgId)
      .then(setEngagements)
      .catch(() => { setEngagements([]) })
  }, [orgId])

  useEffect(() => {
    if (!orgId) return
    listFrameworks({ scope_org_id: orgId, scope_workspace_id: workspaceId || undefined, is_active: true })
      .then(r => setFrameworks((r.items ?? []).map((f: any) => ({ id: f.id, name: f.name, framework_code: f.framework_code }))))
      .catch(() => { setFrameworks([]) })
  }, [orgId, workspaceId])

  useEffect(() => {
    if (!needsControl) return
    if (!engagementId && !frameworkId) {
      setControls([])
      return
    }
    listAllControls({ engagement_id: engagementId || undefined, framework_id: frameworkId || undefined, limit: 100 })
      .then(r => setControls((r.items ?? []).map((c: any) => ({ id: c.id, name: c.name, code: c.control_code }))))
      .catch(() => { setControls([]) })
  }, [engagementId, frameworkId, needsControl])

  useEffect(() => {
    if (!needsRisk) return
    listRisks({ org_id: orgId, workspace_id: workspaceId || undefined, limit: 100 })
      .then(r => setRisks((r.items ?? []).map((r: any) => ({ id: r.id, name: r.title, level_code: r.risk_level_code ?? "" }))))
      .catch(() => { })
  }, [needsRisk, orgId, workspaceId])

  useEffect(() => { setEngagementId(prefill?.engagement_id ?? ""); }, [prefill?.engagement_id])
  useEffect(() => { setSelectedFrameworkId(prefill?.framework_id ?? ""); }, [prefill?.framework_id])
  useEffect(() => { setControlId(""); setRiskId("") }, [reportType])
  useEffect(() => { setControlId("") }, [engagementId, selectedFrameworkId])

  const isFrameworkRequired = scopeDef.required.includes("framework")
  const canSubmit = !loading && (!isFrameworkRequired || !!frameworkId)

  // Group types by scope for dialog picker
  const scopeGroups: Record<string, string[]> = {}
  Object.entries(REPORT_SCOPE_MAP).forEach(([type, def]) => {
    if (!scopeGroups[def.scope]) scopeGroups[def.scope] = []
    scopeGroups[def.scope].push(type)
  })

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!canSubmit) return
    setError(null); setLoading(true)
    try {
      const parameters: Record<string, unknown> = {}
      if (frameworkId) parameters.framework_id = frameworkId
      if (controlId) parameters.control_id = controlId
      if (riskId) parameters.risk_id = riskId
      const report = await generateReport({
        report_type: reportType,
        org_id: orgId,
        workspace_id: workspaceId || undefined,
        engagement_id: engagementId || undefined,
        title: title || undefined,
        parameters,
      })
      onGenerated(report)
    } catch (err: any) { setError(err.message || "Failed to queue report") }
    finally { setLoading(false) }
  }

  const accent = SCOPE_ACCENT[scopeDef.scope as ReportScope]

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={e => { if (e.target === e.currentTarget) onClose() }}>
      <div className="bg-card border border-border rounded-xl w-full max-w-lg mx-4 shadow-2xl max-h-[90vh] overflow-y-auto">

        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-border">
          <div>
            <h2 className="text-sm font-semibold">Generate Report</h2>
            {workspaceName && <p className="text-[11px] text-muted-foreground mt-px">{workspaceName}</p>}
          </div>
          <button onClick={onClose} className="rounded-lg p-1.5 hover:bg-accent text-muted-foreground hover:text-foreground transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-5 space-y-4">

          {/* Type picker — compact rows by scope */}
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mb-2">Report Type</p>
            <div className="rounded-lg border border-border overflow-hidden divide-y divide-border">
              {SCOPE_ORDER.map(scope => {
                const types = scopeGroups[scope]
                if (!types?.length) return null
                const a = SCOPE_ACCENT[scope]
                return (
                  <div key={scope} className="flex items-center gap-3 px-3 py-2">
                    <span className={`text-[9px] font-bold uppercase tracking-widest w-16 shrink-0 ${a.text}`}>{scope}</span>
                    <div className="flex flex-wrap gap-1">
                      {types.map(type => (
                        <button
                          key={type}
                          type="button"
                          onClick={() => setReportType(type)}
                          className={`flex items-center gap-1 px-2 py-1 rounded-md text-[11px] font-medium transition-all ${reportType === type
                              ? `${a.badge} border`
                              : "text-muted-foreground hover:text-foreground hover:bg-accent border border-transparent"
                            }`}
                        >
                          <span className="[&>svg]:w-3 [&>svg]:h-3 shrink-0">{REPORT_TYPE_ICONS[type] ?? <FileText className="w-3 h-3" />}</span>
                          {REPORT_TYPE_LABELS[type]}
                        </button>
                      ))}
                    </div>
                  </div>
                )
              })}
            </div>
            {/* Selected description */}
            <p className="text-[11px] text-muted-foreground mt-2 px-1">{scopeDef.description}</p>
          </div>

          <div>
            <label className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground block mb-1.5">
              Engagement <span className="normal-case font-normal text-muted-foreground">(optional)</span>
            </label>
            <div className="relative">
              <select
                value={engagementId}
                onChange={e => setEngagementId(e.target.value)}
                className="w-full h-9 appearance-none bg-background border border-input rounded-lg px-3 text-sm pr-8 focus:outline-none focus:ring-1 focus:ring-ring"
              >
                <option value="">No engagement selected (global scope)</option>
                {engagements.map(engagement => <option key={engagement.id} value={engagement.id}>{engagement.engagement_name} ({engagement.engagement_code})</option>)}
              </select>
              <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground pointer-events-none" />
            </div>
            {engagements.length > 0 && <p className="text-[11px] text-muted-foreground mt-1">Optionally link to an engagement, or select a framework directly below</p>}
          </div>

          <div>
            <label className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground block mb-1.5">
              Framework {isFrameworkRequired && <span className="text-red-500 normal-case font-normal">· required</span>}
            </label>
            <div className="space-y-2">
              {engagementFrameworkId && (
                <div className="w-full rounded-lg border border-input bg-blue-500/5 px-3 py-2 text-sm text-foreground">
                  <p className="text-[10px] text-blue-400 font-medium uppercase tracking-wide mb-0.5">From engagement</p>
                  <p className="font-medium">{engagementFrameworkId}</p>
                </div>
              )}
              <div className="relative">
                <select
                  value={selectedFrameworkId}
                  onChange={e => setSelectedFrameworkId(e.target.value)}
                  className="w-full h-9 appearance-none bg-background border border-input rounded-lg px-3 text-sm pr-8 focus:outline-none focus:ring-1 focus:ring-ring"
                >
                  <option value="">{engagementFrameworkId ? "Or select another framework..." : "Select a framework..."}</option>
                  {frameworks.map(fw => (
                    <option key={fw.id} value={fw.id}>
                      {fw.name} ({fw.framework_code})
                    </option>
                  ))}
                </select>
                <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground pointer-events-none" />
              </div>
            </div>
            {isFrameworkRequired && !frameworkId && (
              <p className="text-[11px] text-red-400 mt-1">Select a framework directly or via an engagement</p>
            )}
            {!isFrameworkRequired && (
              <p className="text-[11px] text-muted-foreground mt-1">Optional - select an engagement framework or choose from available frameworks</p>
            )}
          </div>

          {/* Control */}
          {needsControl && (
            <div>
              <label className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground block mb-1.5">Control <span className="normal-case font-normal">(optional)</span></label>
              <div className="relative">
                <select value={controlId} onChange={e => setControlId(e.target.value)} className="w-full h-9 appearance-none bg-background border border-input rounded-lg px-3 text-sm pr-8 focus:outline-none focus:ring-1 focus:ring-ring">
                  <option value="">All controls</option>
                  {controls.map(c => <option key={c.id} value={c.id}>{c.code} — {c.name}</option>)}
                </select>
                <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground pointer-events-none" />
              </div>
            </div>
          )}

          {/* Risk */}
          {needsRisk && (
            <div>
              <label className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground block mb-1.5">Risk <span className="normal-case font-normal">(optional)</span></label>
              <div className="relative">
                <select value={riskId} onChange={e => setRiskId(e.target.value)} className="w-full h-9 appearance-none bg-background border border-input rounded-lg px-3 text-sm pr-8 focus:outline-none focus:ring-1 focus:ring-ring">
                  <option value="">All risks</option>
                  {risks.map(r => <option key={r.id} value={r.id}>{r.name}{r.level_code ? ` [${r.level_code}]` : ""}</option>)}
                </select>
                <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground pointer-events-none" />
              </div>
            </div>
          )}

          {/* Title */}
          <div>
            <label className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground block mb-1.5">Title <span className="normal-case font-normal">(optional)</span></label>
            <input
              type="text"
              value={title}
              onChange={e => setTitle(e.target.value)}
              placeholder={REPORT_TYPE_LABELS[reportType] || "Report title"}
              className="w-full h-9 bg-background border border-input rounded-lg px-3 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring"
            />
          </div>

          {error && (
            <div className="flex items-center gap-2 px-3 py-2 bg-red-500/10 border border-red-500/20 rounded-lg text-xs text-red-500">
              <XCircle className="w-3.5 h-3.5 shrink-0" /> {error}
            </div>
          )}

          {isFrameworkRequired && !frameworkId && !error && (
            <div className="flex items-center gap-2 px-3 py-2 bg-amber-500/10 border border-amber-500/20 rounded-lg text-xs text-amber-500">
              <AlertTriangle className="w-3.5 h-3.5 shrink-0" /> Select a framework to generate this report type
            </div>
          )}

          <div className="flex gap-2 pt-1">
            <button type="button" onClick={onClose} className="px-4 py-2 rounded-lg border border-input text-sm text-muted-foreground hover:text-foreground hover:bg-accent transition-colors">
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading || !canSubmit}
              className="flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-primary hover:bg-primary/90 disabled:opacity-40 text-sm text-primary-foreground font-medium transition-colors"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
              {loading ? "Queuing…" : "Generate"}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

// ── ReactMarkdown components for report rendering ────────────────────────────


// ── AI Enhance helpers ─────────────────────────────────────────────────────────

/** Extract section text by heading title from markdown */
function extractSectionText(markdown: string, sectionTitle: string): string {
  const lines = markdown.split("\n")
  let inSection = false
  const sectionLines: string[] = []
  for (const line of lines) {
    const m = line.match(/^(#{2,3})\s+(.+)/)
    if (m) {
      if (m[2].trim() === sectionTitle) { inSection = true; continue }
      if (inSection) break
    }
    if (inSection) sectionLines.push(line)
  }
  return sectionLines.join("\n").trim()
}

/** Replace the content of a heading section in markdown */
function patchSection(markdown: string, sectionTitle: string, newContent: string): string {
  const lines = markdown.split("\n")
  const result: string[] = []
  let inTarget = false
  let found = false
  for (const line of lines) {
    const m = line.match(/^(#{2,3})\s+(.+)/)
    if (m) {
      const title = m[2].trim()
      if (title === sectionTitle && !found) {
        result.push(line, "", newContent, "")
        inTarget = true
        found = true
      } else if (inTarget) {
        inTarget = false
        result.push(line)
      } else {
        result.push(line)
      }
    } else if (!inTarget) {
      result.push(line)
    }
  }
  return result.join("\n")
}

export interface PendingDiff {
  sectionTitle: string | null  // null = whole report
  original: string
  enhanced: string
  streaming: boolean
  streamedText: string
}

// ── Clean Enhance Panel ────────────────────────────────────────────────────────

function EnhancePanel({
  report,
  markdown,
  pendingDiff,
  onStartEnhance,
  onClearDiff,
  onSectionSelect,
}: {
  report: ReportResponse
  markdown: string
  pendingDiff: PendingDiff | null
  onStartEnhance: (sectionTitle: string | null, sectionText: string, instruction: string) => void
  onClearDiff: () => void
  onSectionSelect?: (sectionTitle: string) => void
}) {
  const [instruction, setInstruction] = useState("")
  const [selectedSection, setSelectedSection] = useState<string | null>(null)
  const [sectionSearch, setSectionSearch] = useState("")
  const [showSections, setShowSections] = useState(false)

  const sections = (() => {
    const lines = markdown.split("\n")
    const out: string[] = []
    for (const line of lines) {
      const m = line.match(/^#{2,3}\s+(.+)/)
      if (m) out.push(m[1].trim())
    }
    return out
  })()

  const filteredSections = sectionSearch.trim()
    ? sections.filter(s => s.toLowerCase().includes(sectionSearch.toLowerCase()))
    : sections

  const isStreaming = pendingDiff?.streaming === true

  const handleEnhance = () => {
    if (!instruction.trim() || isStreaming) return
    const sectionText = selectedSection ? extractSectionText(markdown, selectedSection) : markdown
    onStartEnhance(selectedSection, sectionText, instruction.trim())
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) handleEnhance()
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-4 pt-4 pb-3 border-b border-border">
        <div className="flex items-center gap-2">
          <Sparkles className="w-3.5 h-3.5 text-violet-400" />
          <p className="text-xs font-semibold text-foreground">Enhance with AI</p>
        </div>
        <p className="text-[11px] text-muted-foreground mt-0.5 leading-relaxed">
          Describe what to improve. The AI will use the same live GRC data that generated this report.
        </p>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">

        {/* Section chip (optional) */}
        <div>
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-[11px] font-medium text-muted-foreground">Target section</span>
            {selectedSection && (
              <button onClick={() => { setSelectedSection(null); setSectionSearch(""); setShowSections(false) }} className="text-[10px] text-muted-foreground hover:text-foreground transition-colors">
                Clear
              </button>
            )}
          </div>

          {selectedSection ? (
            <div className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-violet-500/10 border border-violet-500/20 text-xs text-violet-400 font-medium">
              <span className="truncate">{selectedSection}</span>
              <button onClick={() => setSelectedSection(null)} className="shrink-0 hover:text-violet-300 transition-colors ml-auto">
                <X className="w-3 h-3" />
              </button>
            </div>
          ) : (
            <div className="relative">
              <button
                onClick={() => setShowSections(v => !v)}
                className="w-full text-left px-2.5 py-1.5 rounded-lg border border-dashed border-border hover:border-violet-500/40 text-[11px] text-muted-foreground hover:text-foreground transition-colors"
              >
                Whole report (or pick a section…)
              </button>
              {showSections && (
                <div className="absolute top-full mt-1 left-0 right-0 z-20 bg-popover border border-border rounded-xl shadow-xl overflow-hidden">
                  <div className="p-2 border-b border-border">
                    <input
                      autoFocus
                      value={sectionSearch}
                      onChange={e => setSectionSearch(e.target.value)}
                      placeholder="Filter sections…"
                      className="w-full text-xs bg-background rounded-md px-2 py-1.5 text-foreground placeholder:text-muted-foreground/50 focus:outline-none"
                    />
                  </div>
                  <div className="max-h-48 overflow-y-auto py-1">
                    {filteredSections.map(s => (
                      <button
                        key={s}
                        onClick={() => { setSelectedSection(s); setShowSections(false); setSectionSearch(""); onSectionSelect?.(s) }}
                        className="w-full text-left px-3 py-2 text-xs text-foreground/80 hover:bg-accent hover:text-foreground transition-colors truncate"
                      >
                        {s}
                      </button>
                    ))}
                    {filteredSections.length === 0 && (
                      <p className="text-center text-[11px] text-muted-foreground py-3">No sections found</p>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Instruction */}
        <div>
          <textarea
            value={instruction}
            onChange={e => setInstruction(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isStreaming}
            placeholder={
              selectedSection
                ? `What should change in "${selectedSection}"?`
                : "What should change in this report?"
            }
            rows={4}
            className="w-full text-xs bg-background border border-input rounded-xl px-3 py-2.5 text-foreground placeholder:text-muted-foreground/40 focus:outline-none focus:ring-1 focus:ring-violet-500/50 resize-none disabled:opacity-50 leading-relaxed"
          />
          <p className="text-[10px] text-muted-foreground/50 mt-1 text-right">⌘↵ to send</p>
        </div>

        {/* Pending diff status */}
        {pendingDiff && (
          <div className={`rounded-xl border px-3 py-2.5 text-xs ${
            pendingDiff.streaming
              ? "border-violet-500/20 bg-violet-500/5 text-violet-400"
              : "border-emerald-500/20 bg-emerald-500/5 text-emerald-400"
          }`}>
            {pendingDiff.streaming ? (
              <span className="flex items-center gap-1.5"><Loader2 className="w-3 h-3 animate-spin" /> Generating suggestion…</span>
            ) : (
              <span className="flex items-center gap-1.5"><CheckCircle2 className="w-3 h-3" /> Suggestion ready — review in the report</span>
            )}
          </div>
        )}

        {pendingDiff && !pendingDiff.streaming && (
          <button
            onClick={onClearDiff}
            className="w-full text-[11px] text-muted-foreground hover:text-foreground transition-colors text-center"
          >
            Discard suggestion
          </button>
        )}

        {/* Enhance button */}
        {!pendingDiff && (
          <button
            onClick={handleEnhance}
            disabled={!instruction.trim() || isStreaming}
            className="w-full flex items-center justify-center gap-1.5 h-9 rounded-xl bg-violet-500 hover:bg-violet-600 disabled:opacity-40 disabled:cursor-not-allowed text-white text-xs font-semibold transition-colors"
          >
            <Sparkles className="w-3.5 h-3.5" /> Generate suggestion
          </button>
        )}
      </div>
    </div>
  )
}

// ── Assess Tab ────────────────────────────────────────────────────────────────

const FINDING_SEVERITIES = [
  { code: "critical", label: "Critical", color: "text-red-500" },
  { code: "high", label: "High", color: "text-orange-500" },
  { code: "medium", label: "Medium", color: "text-yellow-500" },
  { code: "low", label: "Low", color: "text-blue-500" },
  { code: "informational", label: "Info", color: "text-muted-foreground" },
]

interface LocalFinding {
  id: string
  severity: string
  section: string  // empty = whole report
  title: string
  description: string
  recommendation: string
}

function AssessTab({ report, sections, onSaved, scrollToSection }: { report: ReportResponse; sections: string[]; onSaved?: () => void; scrollToSection?: (s: string) => void }) {
  const { selectedOrgId, selectedWorkspaceId } = useOrgWorkspace()
  const [verdict, setVerdict] = useState<"satisfactory" | "needs_revision" | "rejected">("satisfactory")
  const [verdictRationale, setVerdictRationale] = useState("")
  const [findings, setFindings] = useState<LocalFinding[]>([])
  const [showForm, setShowForm] = useState(false)
  const [formSeverity, setFormSeverity] = useState("medium")
  const [formTitle, setFormTitle] = useState("")
  const [formDescription, setFormDescription] = useState("")
  const [formRecommendation, setFormRecommendation] = useState("")
  const [formSection, setFormSection] = useState<string>("")
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState<string | null>(null)
  // AI suggest state
  const [aiThinking, setAiThinking] = useState(false)
  const [aiRawBuffer, setAiRawBuffer] = useState("")
  const [aiError, setAiError] = useState<string | null>(null)

  const handleAiSuggest = async () => {
    if (!selectedOrgId || aiThinking) return
    setAiThinking(true)
    setAiError(null)
    setAiRawBuffer("")
    try {
      const resp = await streamSuggestAssessment(report.id, {
        org_id: selectedOrgId,
        workspace_id: selectedWorkspaceId ?? undefined,
      })
      if (!resp.body) { setAiThinking(false); return }
      const reader = resp.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ""
      let rawAccum = ""
      let currentEvent = ""
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split("\n")
        buffer = lines.pop() ?? ""
        for (const line of lines) {
          if (line.startsWith("event: ")) {
            currentEvent = line.slice(7).trim()
          } else if (line.startsWith("data: ")) {
            const data = line.slice(6).trim()
            if (!data || data === "[DONE]") continue
            try {
              const parsed = JSON.parse(data)
              if (currentEvent === "content_delta") {
                rawAccum += parsed.delta ?? ""
                setAiRawBuffer(rawAccum)
              } else if (currentEvent === "suggestion_complete") {
                const s = parsed as AssessmentSuggestion
                setVerdict(s.verdict)
                setVerdictRationale(s.verdict_rationale ?? "")
                setFindings(s.findings.map(f => ({
                  id: crypto.randomUUID(),
                  severity: f.severity,
                  section: f.section ?? "",
                  title: f.title,
                  description: f.description ?? "",
                  recommendation: f.recommendation ?? "",
                })))
              } else if (currentEvent === "suggestion_error") {
                setAiError(parsed.message ?? "AI suggestion failed")
              }
            } catch { /* ignore */ }
          }
        }
      }
    } catch (err: any) {
      setAiError(err.message || "AI suggestion failed")
    } finally {
      setAiThinking(false)
      setAiRawBuffer("")
    }
  }

  const addFinding = () => {
    if (!formTitle.trim()) return
    setFindings(prev => [...prev, {
      id: crypto.randomUUID(),
      severity: formSeverity,
      section: formSection,
      title: formTitle.trim(),
      description: formDescription.trim(),
      recommendation: formRecommendation.trim(),
    }])
    setFormTitle(""); setFormDescription(""); setFormRecommendation(""); setFormSeverity("medium"); setFormSection("")
    setShowForm(false)
  }

  const removeFinding = (id: string) => setFindings(prev => prev.filter(f => f.id !== id))

  const handleSubmit = async () => {
    if (!selectedOrgId) return
    setSaving(true); setError(null)
    try {
      const { createAssessment, createFinding } = await import("@/lib/api/assessments")
      const assessment = await createAssessment({
        org_id: selectedOrgId,
        workspace_id: selectedWorkspaceId ?? undefined,
        assessment_type_code: "gap_analysis",
        name: `Review: ${report.title || REPORT_TYPE_LABELS[report.report_type] || "Report"}`,
        description: `Human assessment of AI-generated report. Verdict: ${verdict}.${verdictRationale ? " " + verdictRationale : ""}`,
        scope_notes: `report_id:${report.id}`,
      })
      for (const f of findings) {
        await createFinding(assessment.id, {
          severity_code: f.severity,
          finding_type: "observation",
          title: f.title,
          description: f.description,
          recommendation: f.recommendation,
        })
      }
      setSaved(true)
      onSaved?.()
    } catch (err) {
      setError((err as Error).message || "Failed to save assessment")
    } finally {
      setSaving(false)
    }
  }

  if (saved) {
    return (
      <div className="flex flex-col h-full items-center justify-center gap-4 p-6 text-center">
        <CheckCircle2 className="w-10 h-10 text-emerald-500" />
        <p className="font-semibold text-sm">Assessment saved</p>
        <p className="text-xs text-muted-foreground">Verdict: <span className="font-medium text-foreground capitalize">{verdict.replace("_", " ")}</span></p>
        {findings.length > 0 && <p className="text-xs text-muted-foreground">{findings.length} finding{findings.length !== 1 ? "s" : ""} recorded</p>}
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full">
    <div className="px-4 pt-4 pb-3 border-b border-border shrink-0">
      <div className="flex items-center gap-2">
        <ClipboardList className="w-3.5 h-3.5 text-emerald-400" />
        <p className="text-xs font-semibold text-foreground">Assess Report</p>
      </div>
      <p className="text-[11px] text-muted-foreground mt-0.5 leading-relaxed">
        Log your verdict and findings. AI can suggest a starting point.
      </p>
    </div>
    <div className="flex-1 overflow-y-auto px-4 py-4 space-y-5">

      {/* AI Assist banner */}
      <div className="rounded-xl border border-violet-500/20 bg-violet-500/5 px-4 py-3 flex items-start gap-3">
        <Sparkles className="w-4 h-4 text-violet-400 mt-0.5 shrink-0" />
        <div className="flex-1 min-w-0">
          <p className="text-xs font-semibold text-foreground">AI Assessment Assistant</p>
          <p className="text-[11px] text-muted-foreground mt-0.5 leading-relaxed">
            Let AI analyse the report and suggest a verdict and findings. Review and edit before saving.
          </p>
          {aiError && <p className="text-[11px] text-red-400 mt-1">{aiError}</p>}
        </div>
        <button
          onClick={handleAiSuggest}
          disabled={aiThinking}
          className="shrink-0 flex items-center gap-1.5 h-8 px-3 rounded-lg bg-violet-500 hover:bg-violet-600 disabled:opacity-50 text-white text-xs font-medium transition-colors"
        >
          {aiThinking ? <><Loader2 className="w-3.5 h-3.5 animate-spin" /> Analysing…</> : <><Sparkles className="w-3.5 h-3.5" /> Suggest</>}
        </button>
      </div>

      {/* Verdict */}
      <div>
        <p className="text-sm font-semibold mb-2">Overall Verdict</p>
        <div className="flex gap-2 flex-wrap">
          {(["satisfactory", "needs_revision", "rejected"] as const).map(v => (
            <button
              key={v}
              onClick={() => setVerdict(v)}
              className={`px-3 py-1.5 rounded-lg border text-xs font-medium transition-colors ${
                verdict === v
                  ? v === "satisfactory" ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-500"
                    : v === "needs_revision" ? "bg-amber-500/10 border-amber-500/30 text-amber-500"
                    : "bg-red-500/10 border-red-500/30 text-red-500"
                  : "border-input text-muted-foreground hover:bg-accent"
              }`}
            >
              {v === "satisfactory" ? "Satisfactory" : v === "needs_revision" ? "Needs Revision" : "Rejected"}
            </button>
          ))}
        </div>
        {verdictRationale && (
          <p className="text-[11px] text-muted-foreground mt-2 italic leading-relaxed">{verdictRationale}</p>
        )}
      </div>

      {/* Findings */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <p className="text-sm font-semibold">Findings</p>
          <button
            onClick={() => setShowForm(!showForm)}
            className="flex items-center gap-1 text-xs text-violet-500 hover:text-violet-600 font-medium"
          >
            + Add Finding
          </button>
        </div>

        {showForm && (
          <div className="border border-border rounded-xl p-4 mb-3 space-y-3 bg-muted/20">
            <div className="flex flex-col gap-2">
              <select
                value={formSeverity}
                onChange={e => setFormSeverity(e.target.value)}
                className="w-full text-xs bg-background border border-input rounded-lg px-2 py-1.5 text-foreground focus:outline-none"
              >
                {FINDING_SEVERITIES.map(s => <option key={s.code} value={s.code}>{s.label}</option>)}
              </select>
              <select
                value={formSection}
                onChange={e => setFormSection(e.target.value)}
                className="w-full text-xs bg-background border border-input rounded-lg px-2 py-1.5 text-foreground focus:outline-none"
              >
                <option value="">Whole report</option>
                {sections.map(s => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
            <input
              value={formTitle}
              onChange={e => setFormTitle(e.target.value)}
              placeholder="Finding title *"
              className="w-full text-xs bg-background border border-input rounded-lg px-2.5 py-1.5 text-foreground placeholder:text-muted-foreground/50 focus:outline-none"
            />
            <textarea
              value={formDescription}
              onChange={e => setFormDescription(e.target.value)}
              placeholder="Description (optional)"
              rows={2}
              className="w-full text-xs bg-background border border-input rounded-lg px-2.5 py-2 text-foreground placeholder:text-muted-foreground/50 focus:outline-none resize-none"
            />
            <textarea
              value={formRecommendation}
              onChange={e => setFormRecommendation(e.target.value)}
              placeholder="Recommendation (optional)"
              rows={2}
              className="w-full text-xs bg-background border border-input rounded-lg px-2.5 py-2 text-foreground placeholder:text-muted-foreground/50 focus:outline-none resize-none"
            />
            <div className="flex gap-2">
              <button
                onClick={addFinding}
                disabled={!formTitle.trim()}
                className="flex-1 h-7 rounded-md bg-violet-500 hover:bg-violet-600 disabled:opacity-40 text-white text-xs font-medium transition-colors"
              >
                Add
              </button>
              <button
                onClick={() => setShowForm(false)}
                className="flex-1 h-7 rounded-md border border-input hover:bg-accent text-xs text-muted-foreground transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        {findings.length === 0 && !showForm && (
          <p className="text-xs text-muted-foreground py-3">No findings added. Click "Add Finding" to log an observation.</p>
        )}

        <div className="space-y-2">
          {findings.map(f => {
            const sev = FINDING_SEVERITIES.find(s => s.code === f.severity)
            return (
              <div key={f.id} className="border border-border rounded-lg px-4 py-3 flex gap-3">
                <span className={`text-[10px] font-bold uppercase mt-0.5 shrink-0 ${sev?.color ?? "text-muted-foreground"}`}>
                  {sev?.label ?? f.severity}
                </span>
                <div className="flex-1 min-w-0">
                  {f.section && (
                    <button
                      onClick={() => scrollToSection?.(f.section)}
                      className="inline-block text-[10px] text-violet-400 bg-violet-500/10 border border-violet-500/20 rounded px-1.5 py-0.5 mb-1 font-medium truncate max-w-full hover:bg-violet-500/20 transition-colors"
                    >
                      ↑ {f.section}
                    </button>
                  )}
                  <p className="text-xs font-medium text-foreground">{f.title}</p>
                  {f.description && <p className="text-[11px] text-muted-foreground mt-0.5">{f.description}</p>}
                  {f.recommendation && <p className="text-[11px] text-muted-foreground/70 mt-0.5 italic">{f.recommendation}</p>}
                </div>
                <button onClick={() => removeFinding(f.id)} className="text-muted-foreground hover:text-red-400 transition-colors shrink-0">
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
            )
          })}
        </div>
      </div>

    </div>
    {/* Pinned footer */}
    <div className="px-4 py-3 border-t border-border shrink-0 space-y-2">
      {error && <p className="text-xs text-red-400 bg-red-500/8 border border-red-500/20 rounded-lg px-3 py-2">{error}</p>}
      <button
        onClick={handleSubmit}
        disabled={saving}
        className="w-full flex items-center justify-center gap-1.5 h-9 rounded-xl bg-foreground text-background text-xs font-semibold hover:opacity-90 disabled:opacity-40 transition-opacity"
      >
        {saving ? <><Loader2 className="w-3.5 h-3.5 animate-spin" /> Saving…</> : "Complete Assessment"}
      </button>
    </div>
    </div>
  )
}

// ── Inline Diff View ──────────────────────────────────────────────────────────

function InlineDiffView({
  markdown,
  pendingDiff,
  onAccept,
  onReject,
}: {
  markdown: string
  pendingDiff: PendingDiff
  onAccept: () => void
  onReject: () => void
}) {
  // Split markdown into before / original-section / after
  const { before, after } = (() => {
    if (!pendingDiff.sectionTitle) return { before: "", after: "" }
    const lines = markdown.split("\n")
    let sectionStart = -1
    let sectionEnd = lines.length
    const heading2 = `## ${pendingDiff.sectionTitle}`
    const heading3 = `### ${pendingDiff.sectionTitle}`

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim()
      if (line === heading2 || line === heading3) {
        sectionStart = i
        // Find the next heading of same or higher level
        const level = line.startsWith("## ") ? 2 : 3
        for (let j = i + 1; j < lines.length; j++) {
          const nextLine = lines[j].trim()
          const nextLevel = nextLine.startsWith("## ") ? 2 : nextLine.startsWith("### ") ? 3 : 0
          if (nextLevel > 0 && nextLevel <= level) { sectionEnd = j; break }
        }
        break
      }
    }
    if (sectionStart === -1) return { before: markdown, after: "" }
    return {
      before: lines.slice(0, sectionStart).join("\n"),
      after: lines.slice(sectionEnd).join("\n"),
    }
  })()

  return (
    <>
      {/* Before section */}
      {before && <MarkdownRenderer content={before} />}

      {/* Enhanced section highlighted */}
      <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/5 ring-1 ring-emerald-500/20 my-4 overflow-hidden">
        <div className="flex items-center gap-2 px-4 py-2 border-b border-emerald-500/20 bg-emerald-500/8">
          <Sparkles className="w-3 h-3 text-emerald-400" />
          <span className="text-[11px] font-semibold text-emerald-400">AI Enhanced{pendingDiff.sectionTitle ? ` — ${pendingDiff.sectionTitle}` : ""}</span>
        </div>
        <div className="px-4 py-3">
          <MarkdownRenderer content={pendingDiff.enhanced} />
        </div>
      </div>

      {/* After section */}
      {after && <MarkdownRenderer content={after} />}

      {/* Accept / Reject bar */}
      <div className="sticky bottom-4 mt-4">
        <div className="flex items-center justify-between gap-3 bg-card border border-border rounded-xl px-4 py-3 shadow-lg max-w-xl mx-auto">
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Sparkles className="w-3.5 h-3.5 text-violet-400" />
            <span>AI enhancement ready</span>
            {pendingDiff.sectionTitle && (
              <span className="text-violet-400 font-medium">· {pendingDiff.sectionTitle}</span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={onReject}
              className="flex items-center gap-1 h-7 px-3 rounded-lg border border-input bg-background hover:bg-accent text-xs text-muted-foreground hover:text-foreground transition-colors"
            >
              <X className="w-3 h-3" /> Reject
            </button>
            <button
              onClick={onAccept}
              className="flex items-center gap-1 h-7 px-3 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-medium transition-colors"
            >
              <CheckCircle2 className="w-3 h-3" /> Accept
            </button>
          </div>
        </div>
      </div>
    </>
  )
}

// ── PDF Preview Modal ─────────────────────────────────────────────────────────

function PdfPreviewModal({
  meta,
  markdown,
  onClose,
}: {
  meta: ReportPdfMeta
  markdown: string
  onClose: () => void
}) {
  const [blobUrl, setBlobUrl] = useState<string | null>(null)
  const [generating, setGenerating] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [templates, setTemplates] = useState<PdfTemplateResponse[]>([])
  const [selectedTemplateId, setSelectedTemplateId] = useState<string | null>(null)

  // Lock main scroll while open
  useEffect(() => {
    const main = document.querySelector("main")
    if (main) main.style.overflow = "hidden"
    return () => { if (main) main.style.overflow = "" }
  }, [])

  // Fetch available templates for this report type, auto-select default
  useEffect(() => {
    listPdfTemplates({ report_type: meta.reportType, limit: 50 })
      .then(res => {
        setTemplates(res.items)
        const def = res.items.find(t => t.is_default)
        if (def) setSelectedTemplateId(def.id)
      })
      .catch(() => {})
  }, [meta.reportType])

  // Build effective meta with selected template config
  const effectiveMeta: ReportPdfMeta = (() => {
    const t = templates.find(t => t.id === selectedTemplateId)
    if (!t) return meta
    const templateConfig: PdfTemplateConfig = {
      coverStyle: t.cover_style,
      primaryColor: t.primary_color,
      secondaryColor: t.secondary_color,
      headerText: t.header_text ?? undefined,
      footerText: t.footer_text ?? undefined,
      preparedBy: t.prepared_by ?? undefined,
      docRefPrefix: t.doc_ref_prefix ?? undefined,
      classificationLabel: t.classification_label ?? undefined,
    }
    return { ...meta, template: templateConfig }
  })()

  // Generate blob URL whenever meta or selected template changes
  useEffect(() => {
    let revoked = false
    setGenerating(true)
    setError(null)
    getReportPdfBlobUrl(markdown, effectiveMeta)
      .then(url => {
        if (!revoked) { setBlobUrl(url); setGenerating(false) }
      })
      .catch(err => {
        if (!revoked) { setError(err?.message ?? "Failed to generate PDF"); setGenerating(false) }
      })
    return () => {
      revoked = true
      if (blobUrl) URL.revokeObjectURL(blobUrl)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedTemplateId])

  const handleDownload = () => {
    if (!blobUrl) return
    const a = document.createElement("a")
    a.href = blobUrl
    a.download = getReportPdfFilename(effectiveMeta)
    a.click()
  }

  return (
    <div
      className="fixed inset-0 z-[60] flex flex-col bg-black/90 backdrop-blur-sm"
      onClick={e => { if (e.target === e.currentTarget) onClose() }}
    >
      {/* ── Top bar ──────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between px-5 py-3 bg-card border-b border-border shrink-0">
        <div className="flex items-center gap-3 min-w-0">
          <FileText className="w-4 h-4 text-indigo-400 shrink-0" />
          <div className="min-w-0">
            <p className="text-sm font-semibold truncate">{meta.title}</p>
            <p className="text-[11px] text-muted-foreground">PDF Preview</p>
          </div>
          {/* Template selector */}
          {templates.length > 0 && (
            <select
              value={selectedTemplateId ?? ""}
              onChange={e => setSelectedTemplateId(e.target.value || null)}
              className="ml-2 h-7 rounded-md border border-input bg-background px-2 text-xs text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring"
            >
              <option value="">No template (default style)</option>
              {templates.map(t => (
                <option key={t.id} value={t.id}>{t.name}{t.is_default ? " ★" : ""}</option>
              ))}
            </select>
          )}
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {blobUrl && (
            <button
              onClick={handleDownload}
              className="flex items-center gap-1.5 h-8 px-4 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition-colors"
            >
              <Download className="w-3.5 h-3.5" /> Download PDF
            </button>
          )}
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 hover:bg-accent text-muted-foreground hover:text-foreground transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* ── Preview area ─────────────────────────────────────────────── */}
      <div className="flex-1 overflow-hidden relative">
        {generating && (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-4 bg-background">
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-indigo-500/10">
              <Loader2 className="w-7 h-7 animate-spin text-indigo-500" />
            </div>
            <div className="text-center">
              <p className="font-semibold text-sm">Generating PDF…</p>
              <p className="text-muted-foreground text-xs mt-1">Building professional layout with cover page</p>
            </div>
          </div>
        )}
        {error && (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-4">
            <XCircle className="w-10 h-10 text-red-500" />
            <div className="text-center">
              <p className="font-semibold text-sm text-red-500">PDF generation failed</p>
              <p className="text-muted-foreground text-xs mt-1">{error}</p>
            </div>
            <button
              onClick={async () => {
                setError(null); setGenerating(true)
                try {
                  const url = await getReportPdfBlobUrl(markdown, effectiveMeta)
                  setBlobUrl(url); setGenerating(false)
                } catch (e: any) {
                  setError(e?.message ?? "Failed"); setGenerating(false)
                }
              }}
              className="flex items-center gap-1.5 h-8 px-4 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium"
            >
              <RefreshCw className="w-3.5 h-3.5" /> Retry
            </button>
          </div>
        )}
        {blobUrl && (
          <iframe
            src={blobUrl}
            className="w-full h-full border-0"
            title="PDF Preview"
          />
        )}
      </div>

      {/* ── Bottom info bar ───────────────────────────────────────────── */}
      {blobUrl && (
        <div className="flex items-center justify-between px-5 py-2 bg-card border-t border-border shrink-0">
          <span className="text-[11px] text-muted-foreground">
            Use your browser's built-in viewer to zoom, search, or print
          </span>
          <button
            onClick={handleDownload}
            className="flex items-center gap-1.5 text-xs text-indigo-400 hover:text-indigo-300 font-medium transition-colors"
          >
            <Download className="w-3 h-3" /> Save a copy
          </button>
        </div>
      )}
    </div>
  )
}
/** 
 * Splits markdown into logical blocks (headers, paragraphs, tables, lists).
 * This allows isolated editing of sections to prevent document corruption.
 */
function splitMarkdownIntoBlocks(md: string): string[] {
  if (!md) return []
  const blocks: string[] = []
  const lines = md.split("\n")
  let currentBlock: string[] = []
  let inTable = false

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i]
    const trimmed = line.trim()

    // Table detection (keep tables together even with internal newlines if any)
    if (trimmed.startsWith("|")) inTable = true
    if (inTable && !trimmed.startsWith("|") && trimmed !== "") inTable = false

    if (trimmed === "" && !inTable) {
      if (currentBlock.length > 0) {
        blocks.push(currentBlock.join("\n"))
        currentBlock = []
      }
    } else {
      currentBlock.push(line)
    }
  }
  if (currentBlock.length > 0) blocks.push(currentBlock.join("\n"))
  return blocks
}

/** Converts a rendered HTML block back to clean Markdown */
function blockToMarkdown(html: string): string {
  const div = document.createElement("div")
  div.innerHTML = html

  function walk(node: Node): string {
    if (node.nodeType === 3) return node.textContent || ""
    if (node.nodeType !== 1) return ""

    const el = node as HTMLElement
    if (el.style.display === "none") return ""

    const tag = el.tagName
    const children = Array.from(el.childNodes).map(walk).join("")

    switch (tag) {
      case "H1": case "H2": case "H3": case "H4": {
        const level = parseInt(tag.substring(1))
        const id = el.getAttribute("id")
        return `${"#".repeat(level)} ${children}${id ? ` {#${id}}` : ""}\n`
      }
      case "P": return `${children}\n`
      case "STRONG": case "B": return `**${children.trim()}**`
      case "EM": case "I": return `*${children.trim()}*`
      case "CODE": return `\`${children}\``
      case "A": {
        const href = el.getAttribute("href")
        return href ? `[${children}](${href})` : children
      }
      case "BLOCKQUOTE": return `> ${children.trim()}\n`
      case "LI": {
        const parent = el.parentElement?.tagName
        const prefix = parent === "OL" ? "1. " : "- "
        return `${prefix}${children.trim()}\n`
      }
      case "TABLE": {
        const rows = Array.from(el.querySelectorAll("tr"))
        const mdRows = rows.map(tr => {
          const cells = Array.from(tr.querySelectorAll("th, td"))
          return `| ${cells.map(c => Array.from(c.childNodes).map(walk).join("").trim().replace(/\|/g, "\\|")).join(" | ")} |`
        })
        if (mdRows.length > 0) {
          const firstRowCells = rows[0].querySelectorAll("th, td").length
          const sep = `| ${Array(firstRowCells).fill("---").join(" | ")} |`
          mdRows.splice(1, 0, sep)
        }
        return `\n${mdRows.join("\n")}\n`
      }
      default: return children
    }
  }

  return walk(div).trim()
}

// ── Report viewer ─────────────────────────────────────────────────────────────

function ReportViewer({ reportId, onClose, onAssessed, onEnhanced, orgName, workspaceName }: { reportId: string; onClose: () => void; onAssessed?: (id: string) => void; onEnhanced?: (id: string) => void; orgName?: string; workspaceName?: string }) {
  const [report, setReport] = useState<ReportResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [isEditing, setIsEditing] = useState(false)
  const [editedMarkdown, setEditedMarkdown] = useState<string | null>(null)
  
  // Ref for tracking block instances
  const blockRefs = useRef<Record<number, HTMLDivElement | null>>({})
  const editContentRef = useRef<HTMLDivElement | null>(null)
  const editSnapshotRef = useRef<string>("")
  const pollRef = useRef<NodeJS.Timeout | null>(null)
  const [enhancePanelOpen, setEnhancePanelOpen] = useState(false)
  const [assessPanelOpen, setAssessPanelOpen] = useState(false)
  // Patched markdown — starts as null (uses report.content_markdown), updates on Apply
  const [patchedMarkdown, setPatchedMarkdown] = useState<string | null>(null)
  // Pending inline diff — set while streaming or awaiting accept/reject
  const [pendingDiff, setPendingDiff] = useState<PendingDiff | null>(null)
  // Manual edit mode
  const [editMode, setEditMode] = useState(false)
  const [editDraft, setEditDraft] = useState("")
  // PDF preview
  const [pdfPreviewOpen, setPdfPreviewOpen] = useState(false)
  const abortRef = useRef<AbortController | null>(null)
  const reportBodyRef = useRef<HTMLDivElement | null>(null)
  const scrollContainerRef = useRef<HTMLDivElement | null>(null)

  const load = useCallback(async () => {
    try {
      const r = await getReport(reportId)
      setReport(r)
      if (IN_PROGRESS.has(r.status_code)) pollRef.current = setTimeout(load, 3000)
    } catch { /* ignore */ }
    finally { setLoading(false) }
  }, [reportId])

  useEffect(() => { load(); return () => { if (pollRef.current) clearTimeout(pollRef.current) } }, [load])

  // Lock scroll on the main layout container while modal is open
  useEffect(() => {
    const main = document.querySelector("main")
    if (main) main.style.overflow = "hidden"
    return () => { if (main) main.style.overflow = "" }
  }, [])

  // When edit mode opens, seed the contentEditable with the currently-rendered HTML
  useLayoutEffect(() => {
    if (!isEditing) return
    const editEl = editContentRef.current
    if (editEl && editSnapshotRef.current) {
      editEl.innerHTML = editSnapshotRef.current
    }
  }, [isEditing])

  const displayMarkdown = patchedMarkdown ?? report?.content_markdown ?? ""

  // Extract section headings for AssessTab
  const sections = (() => {
    const lines = displayMarkdown.split("\n")
    const out: string[] = []
    for (const line of lines) {
      const m = line.match(/^#{2,3}\s+(.+)/)
      if (m) out.push(m[1].trim())
    }
    return out
  })()

  // Start SSE streaming for an enhance request
  const handleStartEnhance = useCallback(async (
    sectionTitle: string | null,
    sectionText: string,
    instruction: string,
  ) => {
    if (!report) return
    abortRef.current?.abort()
    abortRef.current = new AbortController()

    const diff: PendingDiff = {
      sectionTitle,
      original: sectionText,
      enhanced: "",
      streaming: true,
      streamedText: "",
    }
    setPendingDiff(diff)

    // Auto-cancel if no enhance_complete within 90 seconds
    const timeoutId = setTimeout(() => abortRef.current?.abort(), 90_000)

    try {
      const resp = await streamEnhanceReportSection(report.id, {
        section_title: sectionTitle ?? undefined,
        current_section_markdown: sectionText,
        instruction,
        org_id: report.org_id ?? "",
        workspace_id: report.workspace_id ?? undefined,
      }, abortRef.current?.signal)

      if (!resp.body) {
        setPendingDiff(null)
        return
      }

      const reader = resp.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ""
      let accumulated = ""
      let currentEvent = ""
      let finished = false

      while (!finished) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split("\n")
        buffer = lines.pop() ?? ""

        for (const line of lines) {
          if (line.startsWith("event: ")) {
            currentEvent = line.slice(7).trim()
          } else if (line.startsWith("data: ")) {
            const data = line.slice(6).trim()
            if (!data || data === "[DONE]") continue
            try {
              const parsed = JSON.parse(data)
              if (currentEvent === "content_delta") {
                accumulated += parsed.delta ?? ""
                setPendingDiff(prev => prev ? { ...prev, streamedText: accumulated, enhanced: accumulated } : null)
              } else if (currentEvent === "enhance_complete") {
                const final = parsed.enhanced_section ?? accumulated
                setPendingDiff(prev => prev ? { ...prev, streaming: false, enhanced: final, streamedText: final } : null)
                finished = true
              } else if (currentEvent === "enhance_error") {
                setPendingDiff(null)
                finished = true
              }
            } catch { /* ignore malformed SSE */ }
          }
        }
      }
      reader.cancel()
    } catch (err: any) {
      if (err?.name !== "AbortError") setPendingDiff(null)
    } finally {
      clearTimeout(timeoutId)
    }
  }, [report])

  const handleAcceptDiff = useCallback(async () => {
    if (!pendingDiff) return
    const base = patchedMarkdown ?? report?.content_markdown ?? ""
    const newContent = pendingDiff.sectionTitle
      ? patchSection(base, pendingDiff.sectionTitle, pendingDiff.enhanced)
      : pendingDiff.enhanced
    // Optimistically update local view
    setPatchedMarkdown(newContent)
    setPendingDiff(null)
    onEnhanced?.(reportId)
    // Persist to server
    try {
      await updateReport(reportId, { content_markdown: newContent })
      const updated = await getReport(reportId)
      setReport(updated)
      setPatchedMarkdown(null) // server is now source of truth
    } catch {
      // keep local patch visible even if save failed
    }
  }, [pendingDiff, patchedMarkdown, report?.content_markdown, onEnhanced, reportId])

  const handleRejectDiff = useCallback(() => {
    abortRef.current?.abort()
    setPendingDiff(null)
  }, [])

  const handleSectionSelect = useCallback((sectionTitle: string) => {
    const container = scrollContainerRef.current
    const body = reportBodyRef.current
    if (!container || !body) return
    const headings = body.querySelectorAll("h2, h3")
    for (const h of Array.from(headings)) {
      if (h.textContent?.trim() === sectionTitle) {
        // offsetTop relative to the scroll container
        const headingTop = (h as HTMLElement).getBoundingClientRect().top
        const containerTop = container.getBoundingClientRect().top
        const offset = headingTop - containerTop + container.scrollTop - 16
        container.scrollTo({ top: offset, behavior: "smooth" })
        break
      }
    }
  }, [])
  // Split content into blocks for isolated editing
  const blocks = useMemo(() => {
    return splitMarkdownIntoBlocks(editedMarkdown ?? report?.content_markdown ?? "")
  }, [editedMarkdown, report?.content_markdown])

  const handleSaveAll = useCallback(async () => {
    const el = editContentRef.current
    const content = el ? blockToMarkdown(el.innerHTML) : (displayMarkdown)
    try {
      await updateReport(reportId, { content_markdown: content })
      const updated = await getReport(reportId)
      setReport(updated)
      setPatchedMarkdown(null)
      setEditedMarkdown(null)
      setIsEditing(false)
    } catch (err: any) {
      alert(err.message || "Failed to save report")
    }
  }, [reportId, displayMarkdown])

  const handleDownload = useCallback(async (format: string) => {
    try {
      await downloadReport(reportId, format)
    } catch (e: any) {
      alert(e.message || "Download failed")
    }
  }, [reportId])

  const status = report ? STATUS_CONFIG[report.status_code] : null
  const def = report ? REPORT_SCOPE_MAP[report.report_type] : null
  const accent = def ? SCOPE_ACCENT[def.scope] : null

  const accentBarColour: Record<string, string> = {
    workspace: "#38bdf8",
    framework: "#a78bfa",
    control: "#34d399",
    risk: "#fb923c",
    task: "#fbbf24",
  }
  const barColour = def ? (accentBarColour[def.scope] ?? "#6366f1") : "#6366f1"

  const isCompleted = report?.status_code === "completed"

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-6"
      onClick={e => { if (e.target === e.currentTarget) onClose() }}
    >
      <div
        className="report-viewer-modal bg-card border border-border rounded-2xl w-full shadow-2xl flex flex-col overflow-hidden mx-auto"
        style={{ 
          height: "90vh", 
          maxHeight: "90vh",
          width: "calc(100% - 2rem)",
          maxWidth: (enhancePanelOpen || assessPanelOpen) && isCompleted ? "1200px" : "900px" 
        }}
      >
        <div style={{ height: "3px", background: `linear-gradient(90deg, ${barColour}, ${barColour}88)` }} />
        <style dangerouslySetInnerHTML={{ __html: `
          .report-viewer-modal *::-webkit-scrollbar {
            width: 5px;
            height: 5px;
          }
          .report-viewer-modal *::-webkit-scrollbar-track {
            background: transparent;
          }
          .report-viewer-modal *::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
          }
          .report-viewer-modal *::-webkit-scrollbar-thumb:hover {
            background: rgba(255, 255, 255, 0.2);
          }
          .report-viewer-modal * {
            scrollbar-width: thin;
            scrollbar-color: rgba(255, 255, 255, 0.1) transparent;
          }
        `}} />

        <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-border px-5 py-3.5 shrink-0 gap-3">
          <div className="flex items-center gap-3 min-w-0">
            <div className={`shrink-0 rounded-lg p-2 ${accent?.bg ?? "bg-muted"} ${accent?.text ?? "text-muted-foreground"}`}>
              {REPORT_TYPE_ICONS[report?.report_type ?? ""] ?? <FileText className="w-4 h-4" />}
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <h2 className="text-sm font-semibold truncate">
                  {report?.title || REPORT_TYPE_LABELS[report?.report_type ?? ""] || "Report"}
                </h2>
                {report && <ScopeBadge reportType={report.report_type} />}
              </div>
              {status && (
                <span className={`mt-0.5 flex items-center gap-1 text-[11px] ${status.color}`}>
                  {status.icon} {status.label}
                </span>
              )}
            </div>
          </div>
          <div className="flex items-center gap-2 overflow-x-auto sm:overflow-x-visible pb-1 sm:pb-0 w-full sm:w-auto shrink-0">
            {isCompleted && (
              <>
                <button
                  onClick={() => { setAssessPanelOpen(v => !v); setEnhancePanelOpen(false) }}
                  className={`flex h-8 items-center gap-1.5 rounded-lg border px-3 text-xs font-medium whitespace-nowrap transition-colors ${
                    assessPanelOpen
                      ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-500"
                      : "border-input bg-background text-muted-foreground hover:bg-accent hover:text-foreground"
                  }`}
                >
                  <ClipboardList className="w-3.5 h-3.5" /> <span>Assess</span>
                </button>
                <button
                  onClick={() => { setEnhancePanelOpen(v => !v); setAssessPanelOpen(false) }}
                  className={`flex h-8 items-center gap-1.5 rounded-lg border px-3 text-xs font-medium whitespace-nowrap transition-colors ${
                    enhancePanelOpen
                      ? "border-violet-500/30 bg-violet-500/10 text-violet-500"
                      : "border-input bg-background text-muted-foreground hover:bg-accent hover:text-foreground"
                  }`}
                >
                  <Sparkles className="w-3.5 h-3.5" /> <span>Enhance</span>
                </button>
                <button
                  onClick={() => {
                    if (isEditing) {
                      setIsEditing(false)
                    } else {
                      // Capture the rendered HTML *before* the view switches
                      editSnapshotRef.current = reportBodyRef.current?.innerHTML ?? ""
                      setIsEditing(true)
                      setEnhancePanelOpen(false)
                      setAssessPanelOpen(false)
                      setPendingDiff(null)
                    }
                  }}
                  className={`flex h-8 items-center gap-1.5 rounded-lg border px-3 text-xs font-medium whitespace-nowrap transition-colors ${
                    isEditing
                      ? "border-amber-500/30 bg-amber-500/10 text-amber-500"
                      : "border-input bg-background text-muted-foreground hover:bg-accent hover:text-foreground"
                  }`}
                >
                  <Pencil className="w-3.5 h-3.5" /> <span>{isEditing ? "Cancel" : "Edit"}</span>
                </button>
                {isEditing && (
                  <button
                    onClick={handleSaveAll}
                    className="flex h-8 items-center gap-1.5 rounded-lg bg-amber-500 px-3 text-xs font-medium text-white transition-colors hover:bg-amber-400"
                  >
                    <Save className="w-3.5 h-3.5" /> Save
                  </button>
                )}
                <button
                  onClick={() => report && setPdfPreviewOpen(true)}
                  className="flex h-8 items-center gap-1.5 rounded-lg bg-indigo-600 px-3 text-xs font-medium text-white whitespace-nowrap transition-colors hover:bg-indigo-500"
                >
                  <Eye className="w-3.5 h-3.5" /> Preview PDF
                </button>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <button
                      className="flex h-8 items-center gap-1.5 rounded-lg bg-foreground px-3 text-[11px] font-bold text-background shadow-sm whitespace-nowrap transition-all hover:opacity-90"
                    >
                      <Download className="w-3.5 h-3.5" /> <span>Export</span>
                    </button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" className="w-48">
                    <DropdownMenuItem onClick={() => handleDownload("pdf")} className="cursor-pointer">
                      <FileText className="mr-2 h-4 w-4" />
                      <span>Download as PDF</span>
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => handleDownload("docx")} className="cursor-pointer">
                      <FileText className="mr-2 h-4 w-4" />
                      <span>Download as Word</span>
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </>
            )}
            <button onClick={onClose} className="rounded-lg p-1.5 text-muted-foreground transition-colors hover:bg-accent hover:text-foreground">
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        <div className="flex flex-col lg:flex-row flex-1 overflow-hidden">
          <div className="flex-1 overflow-y-auto" ref={scrollContainerRef}>
            {loading && (
              <div className="flex items-center justify-center py-28">
                <Loader2 className="w-7 h-7 animate-spin text-muted-foreground" />
              </div>
            )}

            {!loading && report && IN_PROGRESS.has(report.status_code) && (
              <div className="flex flex-col items-center justify-center gap-5 py-28">
                <div className="flex h-16 w-16 items-center justify-center rounded-2xl" style={{ background: `${barColour}18` }}>
                  <Loader2 className="w-7 h-7 animate-spin" style={{ color: barColour }} />
                </div>
                <div className="text-center">
                  <p className="text-sm font-semibold">Please wait while we generate your report.</p>
                  <p className="mt-1.5 text-xs text-muted-foreground">You can close this window. We&apos;ll notify you once it&apos;s complete.</p>
                </div>
              </div>
            )}

            {!loading && report?.status_code === "failed" && (
              <div className="m-8 rounded-xl border border-red-500/20 bg-red-500/8 p-6">
                <p className="text-sm font-semibold text-red-500">Report generation failed</p>
                {report.error_message && <p className="mt-2 text-xs text-red-400/70">{report.error_message}</p>}
              </div>
            )}

            {!loading && isCompleted && displayMarkdown && (
              <div className="px-8 pb-10 pt-6">
                <div
                  className="mb-8 rounded-xl px-4 py-4 sm:px-6 sm:py-5"
                  style={{ background: `linear-gradient(135deg, ${barColour}14, ${barColour}06)`, border: `1px solid ${barColour}22` }}
                >
                  <div className="flex flex-wrap items-start justify-between gap-4">
                    <div>
                      <p className="mb-1 text-xs font-semibold uppercase tracking-widest" style={{ color: barColour }}>
                        {def?.description ?? "K-Control Report"}
                      </p>
                      <h3 className="text-lg font-bold leading-snug text-foreground">
                        {report.title || REPORT_TYPE_LABELS[report.report_type] || "Report"}
                      </h3>
                    </div>
                    <span className={`flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-semibold ${accent?.badge ?? ""}`}>
                      <CheckCircle2 className="w-3.5 h-3.5" /> Completed
                    </span>
                  </div>
                  <div className="mt-3 flex flex-wrap gap-x-6 gap-y-1">
                    {report.word_count != null && (
                      <span className="flex items-center gap-1.5 text-[11px] text-muted-foreground">
                        <FileText className="w-3 h-3" />{report.word_count.toLocaleString()} words
                      </span>
                    )}
                    {report.completed_at && (
                      <span className="flex items-center gap-1.5 text-[11px] text-muted-foreground">
                        <Clock className="w-3 h-3" />
                        {new Date(report.completed_at).toLocaleString("en-US", { dateStyle: "medium", timeStyle: "short" })}
                      </span>
                    )}
                    {patchedMarkdown && (
                      <span className="flex items-center gap-1.5 text-[11px] text-violet-500">
                        <Sparkles className="w-3 h-3" /> Enhanced
                      </span>
                    )}
                  </div>
                </div>

                <div className="report-md relative" ref={reportBodyRef}>
                  {isEditing ? (
                    <div className="space-y-1">
                      <div className="flex items-center gap-2 text-[11px] text-amber-500/80 mb-3">
                        <Pencil className="w-3 h-3" />
                        <span>Click any section to edit. Save persists to server.</span>
                      </div>
                      <div
                        ref={editContentRef}
                        contentEditable
                        suppressContentEditableWarning
                        className="report-md outline-none focus:ring-1 focus:ring-amber-400/30 rounded-md px-2 py-1 min-h-[200px] cursor-text"
                      />
                    </div>
                  ) : pendingDiff && !pendingDiff.streaming ? (
                    <InlineDiffView
                      markdown={displayMarkdown}
                      pendingDiff={pendingDiff}
                      onAccept={handleAcceptDiff}
                      onReject={handleRejectDiff}
                    />
                  ) : (
                    <>
                      <MarkdownRenderer content={displayMarkdown} />
                      {pendingDiff?.streaming && (
                        <div className="sticky bottom-4 mx-auto mt-4 max-w-xl">
                          <div className="flex items-center gap-2 rounded-xl border border-border bg-card px-4 py-3 text-xs text-muted-foreground shadow-lg">
                            <Loader2 className="w-3.5 h-3.5 animate-spin text-violet-400" />
                            <span>Enhancing{pendingDiff.sectionTitle ? ` "${pendingDiff.sectionTitle}"` : " report"}...</span>
                            <button onClick={handleRejectDiff} className="ml-auto text-[10px] transition-colors hover:text-foreground">Cancel</button>
                          </div>
                        </div>
                      )}
                    </>
                  )}
                </div>
              </div>
            )}
          </div>

          {enhancePanelOpen && isCompleted && report && displayMarkdown && (
            <div className="h-1/2 lg:h-full w-full lg:w-72 shrink-0 overflow-y-auto border-t lg:border-t-0 lg:border-l border-border">
              <EnhancePanel
                report={report}
                markdown={displayMarkdown}
                pendingDiff={pendingDiff}
                onStartEnhance={handleStartEnhance}
                onClearDiff={handleRejectDiff}
                onSectionSelect={handleSectionSelect}
              />
            </div>
          )}

          {assessPanelOpen && isCompleted && report && (
            <div className="h-2/3 lg:h-full w-full lg:w-80 shrink-0 overflow-y-auto border-t lg:border-t-0 lg:border-l border-border">
              <AssessTab
                report={report}
                sections={sections}
                onSaved={() => { onAssessed?.(reportId); setAssessPanelOpen(false) }}
                scrollToSection={handleSectionSelect}
              />
            </div>
          )}
        </div>
      </div>

      {pdfPreviewOpen && report && (
        <PdfPreviewModal
          markdown={displayMarkdown}
          meta={{
            title: report.title || REPORT_TYPE_LABELS[report.report_type] || "Report",
            reportType: report.report_type,
            generatedAt: report.completed_at ?? report.created_at,
            wordCount: report.word_count ?? undefined,
            orgName,
            workspaceName,
            confidential: true,
          }}
          onClose={() => setPdfPreviewOpen(false)}
        />
      )}
    </div>
  )
}
// ── Assessment helpers ────────────────────────────────────────────────────────

const ASSESSMENT_STATUS_META: Record<string, { label: string; color: string }> = {
  planned:     { label: "Planned",     color: "text-muted-foreground bg-muted border-border" },
  in_progress: { label: "In Progress", color: "text-blue-600 bg-blue-500/10 border-blue-500/20" },
  in_review:   { label: "In Review",   color: "text-yellow-600 bg-yellow-500/10 border-yellow-500/20" },
  completed:   { label: "Completed",   color: "text-emerald-600 bg-emerald-500/10 border-emerald-500/20" },
  cancelled:   { label: "Cancelled",   color: "text-slate-500 bg-slate-500/10 border-slate-500/20" },
}

const SEVERITY_META: Record<string, { label: string; color: string }> = {
  critical: { label: "Critical", color: "text-red-700 bg-red-500/10 border-red-500/20" },
  high:     { label: "High",     color: "text-orange-600 bg-orange-500/10 border-orange-500/20" },
  medium:   { label: "Medium",   color: "text-yellow-600 bg-yellow-500/10 border-yellow-500/20" },
  low:      { label: "Low",      color: "text-blue-600 bg-blue-500/10 border-blue-500/20" },
  info:     { label: "Info",     color: "text-muted-foreground bg-muted border-border" },
}

const FINDING_STATUS_META: Record<string, { label: string; color: string }> = {
  open:            { label: "Open",            color: "text-red-600 bg-red-500/10 border-red-500/20" },
  in_remediation:  { label: "In Remediation",  color: "text-yellow-600 bg-yellow-500/10 border-yellow-500/20" },
  verified_closed: { label: "Verified Closed", color: "text-emerald-600 bg-emerald-500/10 border-emerald-500/20" },
  accepted:        { label: "Accepted",         color: "text-blue-600 bg-blue-500/10 border-blue-500/20" },
  disputed:        { label: "Disputed",         color: "text-purple-600 bg-purple-500/10 border-purple-500/20" },
}

function AssessmentBadge({ code, meta }: { code: string; meta: Record<string, { label: string; color: string }> }) {
  const m = meta[code] || { label: code, color: "text-muted-foreground bg-muted border-border" }
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${m.color}`}>
      {m.label}
    </span>
  )
}

function AssessmentsPanel({ orgId, workspaceId }: { orgId: string; workspaceId: string }) {
  const [assessments, setAssessments] = useState<AssessmentResponse[]>([])
  const [types, setTypes] = useState<AssessmentDimension[]>([])
  const [statuses, setStatuses] = useState<AssessmentDimension[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState("")
  const [filterStatus, setFilterStatus] = useState("")
  const [filterType, setFilterType] = useState("")
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [findings, setFindings] = useState<FindingResponse[]>([])
  const [findingsLoading, setFindingsLoading] = useState(false)
  const [summary, setSummary] = useState<AssessmentSummaryResponse | null>(null)
  const [expandedFindingId, setExpandedFindingId] = useState<string | null>(null)
  const [responses, setResponses] = useState<FindingResponseResponse[]>([])
  const [responsesLoading, setResponsesLoading] = useState(false)

  const [createOpen, setCreateOpen] = useState(false)
  const [editOpen, setEditOpen] = useState(false)
  const [editTarget, setEditTarget] = useState<AssessmentResponse | null>(null)
  const [deleteOpen, setDeleteOpen] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState<AssessmentResponse | null>(null)
  const [completeOpen, setCompleteOpen] = useState(false)
  const [completeTarget, setCompleteTarget] = useState<AssessmentResponse | null>(null)
  const [createFindingOpen, setCreateFindingOpen] = useState(false)
  const [editFindingOpen, setEditFindingOpen] = useState(false)
  const [editFindingTarget, setEditFindingTarget] = useState<FindingResponse | null>(null)
  const [respondOpen, setRespondOpen] = useState(false)
  const [respondFinding, setRespondFinding] = useState<FindingResponse | null>(null)

  const [createForm, setCreateForm] = useState<Partial<CreateAssessmentRequest>>({ assessment_type_code: "gap_analysis" })
  const [editForm, setEditForm] = useState<{ name?: string; description?: string; assessment_status_code?: string }>({})
  const [findingForm, setFindingForm] = useState<Partial<CreateFindingRequest>>({ finding_type: "observation", severity_code: "medium" })
  const [editFindingForm, setEditFindingForm] = useState<{ title?: string; description?: string; finding_status_code?: string; severity_code?: string }>({})
  const [responseText, setResponseText] = useState("")
  const [submitting, setSubmitting] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)

  const loadDimensions = useCallback(async () => {
    try {
      const [t, s] = await Promise.all([listAssessmentTypes(), listAssessmentStatuses()])
      setTypes(t); setStatuses(s)
    } catch {}
  }, [])

  const loadAssessments = useCallback(async () => {
    if (!orgId) return
    setLoading(true); setError(null)
    try {
      const res = await listAssessments(orgId, {
        workspace_id: workspaceId || undefined,
        type_code: filterType || undefined,
        status: filterStatus || undefined,
      })
      setAssessments(res.items)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load assessments")
    } finally { setLoading(false) }
  }, [orgId, workspaceId, filterType, filterStatus])

  useEffect(() => { loadDimensions() }, [loadDimensions])
  useEffect(() => { loadAssessments(); setExpandedId(null) }, [loadAssessments])

  const toggleExpand = useCallback(async (a: AssessmentResponse) => {
    if (expandedId === a.id) { setExpandedId(null); setFindings([]); setSummary(null); return }
    setExpandedId(a.id); setFindingsLoading(true)
    try {
      const [fRes, sumRes] = await Promise.all([listFindings(a.id), getAssessmentSummary(a.id)])
      setFindings(fRes.items); setSummary(sumRes)
    } catch {}
    setFindingsLoading(false)
  }, [expandedId])

  const toggleFinding = useCallback(async (f: FindingResponse) => {
    if (expandedFindingId === f.id) { setExpandedFindingId(null); setResponses([]); return }
    setExpandedFindingId(f.id); setResponsesLoading(true)
    try { const res = await listFindingResponses(f.id); setResponses(res.items) } catch {}
    setResponsesLoading(false)
  }, [expandedFindingId])

  async function handleCreate() {
    if (!orgId || !createForm.name || !createForm.assessment_type_code) return
    setSubmitting(true); setFormError(null)
    try {
      await createAssessment({ ...createForm, org_id: orgId, workspace_id: workspaceId || undefined } as CreateAssessmentRequest)
      setCreateOpen(false); setCreateForm({ assessment_type_code: "gap_analysis" }); loadAssessments()
    } catch (e: unknown) { setFormError(e instanceof Error ? e.message : "Failed to create") }
    finally { setSubmitting(false) }
  }

  async function handleUpdate() {
    if (!editTarget) return
    setSubmitting(true); setFormError(null)
    try { await updateAssessment(editTarget.id, editForm); setEditOpen(false); loadAssessments() }
    catch (e: unknown) { setFormError(e instanceof Error ? e.message : "Failed to update") }
    finally { setSubmitting(false) }
  }

  async function handleComplete() {
    if (!completeTarget) return
    setSubmitting(true)
    try { await completeAssessment(completeTarget.id); setCompleteOpen(false); loadAssessments() } catch {}
    setSubmitting(false)
  }

  async function handleDelete() {
    if (!deleteTarget) return
    setSubmitting(true)
    try { await deleteAssessment(deleteTarget.id); setDeleteOpen(false); setExpandedId(null); loadAssessments() } catch {}
    setSubmitting(false)
  }

  async function handleCreateFinding() {
    if (!expandedId || !findingForm.title) return
    setSubmitting(true); setFormError(null)
    try {
      const f = await createFinding(expandedId, findingForm as CreateFindingRequest)
      setFindings(prev => [...prev, f]); setCreateFindingOpen(false)
      setFindingForm({ finding_type: "observation", severity_code: "medium" })
    } catch (e: unknown) { setFormError(e instanceof Error ? e.message : "Failed") }
    finally { setSubmitting(false) }
  }

  async function handleUpdateFinding() {
    if (!editFindingTarget) return
    setSubmitting(true); setFormError(null)
    try {
      const f = await updateFinding(editFindingTarget.id, editFindingForm)
      setFindings(prev => prev.map(x => x.id === f.id ? f : x)); setEditFindingOpen(false)
    } catch (e: unknown) { setFormError(e instanceof Error ? e.message : "Failed") }
    finally { setSubmitting(false) }
  }

  async function handleDeleteFinding(id: string) {
    try { await deleteFinding(id); setFindings(prev => prev.filter(f => f.id !== id)) } catch {}
  }

  async function handleSubmitResponse() {
    if (!respondFinding || !responseText.trim()) return
    setSubmitting(true); setFormError(null)
    try {
      const r = await createFindingResponse(respondFinding.id, { response_text: responseText })
      setResponses(prev => [...prev, r]); setRespondOpen(false); setResponseText("")
      const fRes = await listFindings(expandedId!); setFindings(fRes.items)
    } catch (e: unknown) { setFormError(e instanceof Error ? e.message : "Failed") }
    finally { setSubmitting(false) }
  }

  const filtered = assessments.filter(a =>
    (a.name || "").toLowerCase().includes(search.toLowerCase()) ||
    (a.assessment_type_name || "").toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="space-y-4">
      {/* Toolbar */}
      <div className="flex items-center gap-2 flex-wrap">
        <div className="relative flex-1 max-w-xs">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <input className="w-full pl-8 pr-3 h-9 rounded-md border border-input bg-background text-sm outline-none focus:ring-1 focus:ring-ring" placeholder="Search assessments..."
            value={search} onChange={e => setSearch(e.target.value)} />
        </div>
        <select className="h-9 rounded-md border border-input bg-background px-2 text-sm"
          value={filterType} onChange={e => setFilterType(e.target.value)}>
          <option value="">All Types</option>
          {types.map(t => <option key={t.code} value={t.code}>{t.name}</option>)}
        </select>
        <select className="h-9 rounded-md border border-input bg-background px-2 text-sm"
          value={filterStatus} onChange={e => setFilterStatus(e.target.value)}>
          <option value="">All Statuses</option>
          {statuses.map(s => <option key={s.code} value={s.code}>{s.name}</option>)}
        </select>
        <div className="ml-auto flex items-center gap-2">
          <button onClick={loadAssessments} disabled={loading}
            className="flex items-center gap-1.5 h-9 px-3 rounded-lg border border-border bg-background hover:bg-muted text-sm transition-colors">
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} /> Refresh
          </button>
          <button onClick={() => { setCreateForm({ assessment_type_code: "gap_analysis" }); setCreateOpen(true) }}
            className="flex items-center gap-1.5 h-9 px-4 rounded-lg bg-primary hover:bg-primary/90 text-sm text-primary-foreground font-medium transition-colors">
            <Plus className="w-4 h-4" /> New Assessment
          </button>
        </div>
      </div>

      {/* Content */}
      {error && <div className="p-3 rounded-md bg-destructive/10 text-destructive text-sm">{error}</div>}
      {!orgId ? (
        <div className="flex flex-col items-center justify-center h-64 text-muted-foreground">
          <ClipboardCheck className="h-12 w-12 mb-3 opacity-20" />
          <p>Select an organization to view assessments</p>
        </div>
      ) : loading ? (
        <div className="space-y-2">{[...Array(3)].map((_, i) => <div key={i} className="h-16 rounded-lg bg-muted animate-pulse" />)}</div>
      ) : filtered.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-64 text-muted-foreground">
          <ClipboardCheck className="h-12 w-12 mb-3 opacity-20" />
          <p className="font-medium">No assessments found</p>
          <p className="text-sm mt-1">Create your first assessment to get started</p>
        </div>
      ) : (
        <div className="space-y-2">
          {filtered.map(a => (
            <Card key={a.id} className="overflow-hidden">
              <CardContent className="p-0">
                <div className="flex items-center gap-3 p-4 cursor-pointer hover:bg-muted/40 transition-colors"
                  onClick={() => toggleExpand(a)}>
                  <span className="text-muted-foreground">
                    {expandedId === a.id ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-sm">{a.name || "(untitled)"}</span>
                      {a.is_locked && <Lock className="h-3 w-3 text-muted-foreground" />}
                    </div>
                    <div className="text-xs text-muted-foreground mt-0.5">{a.assessment_type_name}</div>
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <AssessmentBadge code={a.assessment_status_code} meta={ASSESSMENT_STATUS_META} />
                    <span className="text-xs text-muted-foreground">{a.finding_count} findings</span>
                    <div className="flex items-center gap-1" onClick={e => e.stopPropagation()}>
                      {!a.is_locked && (
                        <>
                          <Button variant="ghost" size="sm" className="h-7 w-7 p-0"
                            onClick={() => { setEditTarget(a); setEditForm({ name: a.name ?? "", description: a.description ?? "", assessment_status_code: a.assessment_status_code }); setEditOpen(true) }}>
                            <Pencil className="h-3.5 w-3.5" />
                          </Button>
                          {!["completed","cancelled"].includes(a.assessment_status_code) && (
                            <Button variant="ghost" size="sm" className="h-7 w-7 p-0 text-emerald-600"
                              onClick={() => { setCompleteTarget(a); setCompleteOpen(true) }}>
                              <CheckSquare className="h-3.5 w-3.5" />
                            </Button>
                          )}
                        </>
                      )}
                      <Button variant="ghost" size="sm" className="h-7 w-7 p-0 text-destructive"
                        onClick={() => { setDeleteTarget(a); setDeleteOpen(true) }}>
                        <Trash2 className="h-3.5 w-3.5" />
                      </Button>
                    </div>
                  </div>
                </div>
                {expandedId === a.id && (
                  <div className="border-t border-border bg-muted/20 p-4">
                    {summary && (
                      <div className="flex gap-4 mb-4 p-3 rounded-md bg-background border border-border text-center">
                        <div><div className="text-lg font-bold">{summary.total_findings}</div><div className="text-xs text-muted-foreground">Total</div></div>
                        {Object.entries(summary.matrix).map(([sev, m]) => (
                          <div key={sev}>
                            <div className="text-lg font-bold">{(m as any).open}</div>
                            <div className="text-xs text-muted-foreground capitalize">{sev} open</div>
                          </div>
                        ))}
                      </div>
                    )}
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-sm font-medium">Findings</span>
                      {!a.is_locked && (
                        <Button size="sm" variant="outline" className="h-7 text-xs"
                          onClick={() => { setFindingForm({ finding_type: "observation", severity_code: "medium" }); setCreateFindingOpen(true) }}>
                          <Plus className="h-3.5 w-3.5 mr-1" />Add Finding
                        </Button>
                      )}
                    </div>
                    {findingsLoading ? (
                      <div className="space-y-2">{[...Array(2)].map((_, i) => <div key={i} className="h-10 rounded bg-muted animate-pulse" />)}</div>
                    ) : findings.length === 0 ? (
                      <p className="text-sm text-muted-foreground text-center py-4">No findings yet</p>
                    ) : (
                      <div className="space-y-1">
                        {findings.map(f => (
                          <div key={f.id} className="rounded-md border border-border bg-background">
                            <div className="flex items-center gap-2 p-3 cursor-pointer hover:bg-muted/40 transition-colors"
                              onClick={() => toggleFinding(f)}>
                              <span className="text-muted-foreground">
                                {expandedFindingId === f.id ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
                              </span>
                              <div className="flex-1 min-w-0">
                                <span className="text-sm font-medium">{f.title || "(untitled)"}</span>
                                <div className="text-xs text-muted-foreground capitalize">{f.finding_type?.replace(/_/g, " ")}</div>
                              </div>
                              <div className="flex items-center gap-2 flex-shrink-0">
                                <AssessmentBadge code={f.severity_code} meta={SEVERITY_META} />
                                <AssessmentBadge code={f.finding_status_code} meta={FINDING_STATUS_META} />
                                <div className="flex items-center gap-1" onClick={e => e.stopPropagation()}>
                                  {!a.is_locked && (
                                    <>
                                      <Button variant="ghost" size="sm" className="h-6 w-6 p-0"
                                        onClick={() => { setEditFindingTarget(f); setEditFindingForm({ title: f.title ?? "", description: f.description ?? "", finding_status_code: f.finding_status_code, severity_code: f.severity_code }); setEditFindingOpen(true) }}>
                                        <Pencil className="h-3 w-3" />
                                      </Button>
                                      <Button variant="ghost" size="sm" className="h-6 w-6 p-0 text-destructive"
                                        onClick={() => handleDeleteFinding(f.id)}>
                                        <Trash2 className="h-3 w-3" />
                                      </Button>
                                    </>
                                  )}
                                  <Button variant="ghost" size="sm" className="h-6 w-6 p-0 text-blue-600"
                                    onClick={() => { setRespondFinding(f); setRespondOpen(true) }}>
                                    <MessageSquare className="h-3 w-3" />
                                  </Button>
                                </div>
                              </div>
                            </div>
                            {expandedFindingId === f.id && (
                              <div className="border-t border-border bg-muted/10 p-3">
                                {f.description && <p className="text-sm text-muted-foreground mb-2">{f.description}</p>}
                                {responsesLoading ? (
                                  <div className="h-8 rounded bg-muted animate-pulse" />
                                ) : responses.length === 0 ? (
                                  <p className="text-xs text-muted-foreground">No responses yet</p>
                                ) : (
                                  <div className="space-y-2">
                                    {responses.map(r => (
                                      <div key={r.id} className="p-2 rounded bg-background border border-border">
                                        <div className="text-xs text-muted-foreground mb-1">{new Date(r.responded_at).toLocaleDateString()}</div>
                                        <p className="text-sm">{r.response_text}</p>
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
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Dialogs */}
      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>New Assessment</DialogTitle>
            <DialogDescription>Create a new assessment or gap analysis</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div>
              <Label>Assessment Type *</Label>
              <select className="w-full mt-1 h-9 rounded-md border border-input bg-background px-3 text-sm"
                value={createForm.assessment_type_code || ""}
                onChange={e => setCreateForm(f => ({ ...f, assessment_type_code: e.target.value }))}>
                {types.map(t => <option key={t.code} value={t.code}>{t.name}</option>)}
              </select>
            </div>
            <div>
              <Label>Name *</Label>
              <Input className="mt-1" placeholder="e.g. Q1 2026 SOC 2 Gap Analysis"
                value={createForm.name || ""}
                onChange={e => setCreateForm(f => ({ ...f, name: e.target.value }))} />
            </div>
            <div>
              <Label>Description</Label>
              <textarea className="w-full mt-1 rounded-md border border-input bg-background px-3 py-2 text-sm resize-none" rows={3}
                value={createForm.description || ""}
                onChange={e => setCreateForm(f => ({ ...f, description: e.target.value }))} />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label>Scheduled Start</Label>
                <Input type="date" className="mt-1" value={createForm.scheduled_start || ""}
                  onChange={e => setCreateForm(f => ({ ...f, scheduled_start: e.target.value }))} />
              </div>
              <div>
                <Label>Scheduled End</Label>
                <Input type="date" className="mt-1" value={createForm.scheduled_end || ""}
                  onChange={e => setCreateForm(f => ({ ...f, scheduled_end: e.target.value }))} />
              </div>
            </div>
            {formError && <p className="text-sm text-destructive">{formError}</p>}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateOpen(false)}>Cancel</Button>
            <Button onClick={handleCreate} disabled={submitting || !createForm.name}>
              {submitting ? "Creating..." : "Create Assessment"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={editOpen} onOpenChange={setEditOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader><DialogTitle>Edit Assessment</DialogTitle></DialogHeader>
          <div className="space-y-4 py-2">
            <div>
              <Label>Name</Label>
              <Input className="mt-1" value={editForm.name || ""}
                onChange={e => setEditForm(f => ({ ...f, name: e.target.value }))} />
            </div>
            <div>
              <Label>Status</Label>
              <select className="w-full mt-1 h-9 rounded-md border border-input bg-background px-3 text-sm"
                value={editForm.assessment_status_code || ""}
                onChange={e => setEditForm(f => ({ ...f, assessment_status_code: e.target.value }))}>
                {statuses.map(s => <option key={s.code} value={s.code}>{s.name}</option>)}
              </select>
            </div>
            <div>
              <Label>Description</Label>
              <textarea className="w-full mt-1 rounded-md border border-input bg-background px-3 py-2 text-sm resize-none" rows={3}
                value={editForm.description || ""}
                onChange={e => setEditForm(f => ({ ...f, description: e.target.value }))} />
            </div>
            {formError && <p className="text-sm text-destructive">{formError}</p>}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditOpen(false)}>Cancel</Button>
            <Button onClick={handleUpdate} disabled={submitting}>{submitting ? "Saving..." : "Save"}</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={completeOpen} onOpenChange={setCompleteOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Complete Assessment</DialogTitle>
            <DialogDescription>Mark &quot;{completeTarget?.name}&quot; as completed? This locks all findings.</DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCompleteOpen(false)}>Cancel</Button>
            <Button className="bg-emerald-600 hover:bg-emerald-700" onClick={handleComplete} disabled={submitting}>
              {submitting ? "Completing..." : "Complete"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={deleteOpen} onOpenChange={setDeleteOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Assessment</DialogTitle>
            <DialogDescription>Delete &quot;{deleteTarget?.name}&quot;? This cannot be undone.</DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteOpen(false)}>Cancel</Button>
            <Button variant="destructive" onClick={handleDelete} disabled={submitting}>{submitting ? "Deleting..." : "Delete"}</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={createFindingOpen} onOpenChange={setCreateFindingOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Add Finding</DialogTitle>
            <DialogDescription>Record a finding for this assessment</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label>Type *</Label>
                <select className="w-full mt-1 h-9 rounded-md border border-input bg-background px-3 text-sm"
                  value={findingForm.finding_type || "observation"}
                  onChange={e => setFindingForm(f => ({ ...f, finding_type: e.target.value }))}>
                  <option value="observation">Observation</option>
                  <option value="gap">Gap</option>
                  <option value="deficiency">Deficiency</option>
                  <option value="non_conformity">Non-Conformity</option>
                </select>
              </div>
              <div>
                <Label>Severity *</Label>
                <select className="w-full mt-1 h-9 rounded-md border border-input bg-background px-3 text-sm"
                  value={findingForm.severity_code || "medium"}
                  onChange={e => setFindingForm(f => ({ ...f, severity_code: e.target.value }))}>
                  {Object.entries(SEVERITY_META).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
                </select>
              </div>
            </div>
            <div>
              <Label>Title *</Label>
              <Input className="mt-1" placeholder="Finding title"
                value={findingForm.title || ""}
                onChange={e => setFindingForm(f => ({ ...f, title: e.target.value }))} />
            </div>
            <div>
              <Label>Description</Label>
              <textarea className="w-full mt-1 rounded-md border border-input bg-background px-3 py-2 text-sm resize-none" rows={3}
                value={findingForm.description || ""}
                onChange={e => setFindingForm(f => ({ ...f, description: e.target.value }))} />
            </div>
            {formError && <p className="text-sm text-destructive">{formError}</p>}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateFindingOpen(false)}>Cancel</Button>
            <Button onClick={handleCreateFinding} disabled={submitting || !findingForm.title}>
              {submitting ? "Adding..." : "Add Finding"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={editFindingOpen} onOpenChange={setEditFindingOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader><DialogTitle>Edit Finding</DialogTitle></DialogHeader>
          <div className="space-y-4 py-2">
            <div>
              <Label>Title</Label>
              <Input className="mt-1" value={editFindingForm.title || ""}
                onChange={e => setEditFindingForm(f => ({ ...f, title: e.target.value }))} />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label>Status</Label>
                <select className="w-full mt-1 h-9 rounded-md border border-input bg-background px-3 text-sm"
                  value={editFindingForm.finding_status_code || ""}
                  onChange={e => setEditFindingForm(f => ({ ...f, finding_status_code: e.target.value }))}>
                  {Object.entries(FINDING_STATUS_META).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
                </select>
              </div>
              <div>
                <Label>Severity</Label>
                <select className="w-full mt-1 h-9 rounded-md border border-input bg-background px-3 text-sm"
                  value={editFindingForm.severity_code || ""}
                  onChange={e => setEditFindingForm(f => ({ ...f, severity_code: e.target.value }))}>
                  {Object.entries(SEVERITY_META).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
                </select>
              </div>
            </div>
            <div>
              <Label>Description</Label>
              <textarea className="w-full mt-1 rounded-md border border-input bg-background px-3 py-2 text-sm resize-none" rows={3}
                value={editFindingForm.description || ""}
                onChange={e => setEditFindingForm(f => ({ ...f, description: e.target.value }))} />
            </div>
            {formError && <p className="text-sm text-destructive">{formError}</p>}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditFindingOpen(false)}>Cancel</Button>
            <Button onClick={handleUpdateFinding} disabled={submitting}>{submitting ? "Saving..." : "Save"}</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={respondOpen} onOpenChange={setRespondOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add Response</DialogTitle>
            <DialogDescription>Respond to finding: {respondFinding?.title}</DialogDescription>
          </DialogHeader>
          <div className="py-2">
            <textarea className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm resize-none" rows={4}
              placeholder="Enter your response..."
              value={responseText} onChange={e => setResponseText(e.target.value)} />
            {formError && <p className="text-sm text-destructive mt-2">{formError}</p>}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setRespondOpen(false)}>Cancel</Button>
            <Button onClick={handleSubmitResponse} disabled={submitting || !responseText.trim()}>
              {submitting ? "Submitting..." : "Submit Response"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function ReportsPage() {
  const { selectedOrgId, selectedWorkspaceId, workspaces, ready } = useOrgWorkspace()
  const selectedWorkspaceName = workspaces.find(w => w.id === selectedWorkspaceId)?.name ?? ""

  const [pageTab, setPageTab] = useState<"reports" | "assessments">("reports")
  const [reports, setReports] = useState<ReportSummaryResponse[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [showGenerate, setShowGenerate] = useState(false)
  const [generatePrefill, setGeneratePrefill] = useState<{ report_type?: string; framework_id?: string; title?: string } | undefined>()
  const [viewingId, setViewingId] = useState<string | null>(null)
  const [filterScope, setFilterScope] = useState<ReportScope | "all">("all")
  const [frameworkFilter, setFrameworkFilter] = useState<string>("all")
  const [deleting, setDeleting] = useState<string | null>(null)
  const [assessedIds, setAssessedIds] = useState<Set<string>>(new Set())
  const [enhancedIds, setEnhancedIds] = useState<Set<string>>(new Set())
  const [entityLabels, setEntityLabels] = useState<Record<string, string>>({})
  const pollRef = useRef<NodeJS.Timeout | null>(null)

  const load = useCallback(async () => {
    if (!selectedOrgId) return
    try {
      const result = await listReports(selectedOrgId, undefined, undefined, 50, 0)
      setReports(result.items); setTotal(result.total)
    } catch (err) {
      console.error("Failed to load reports:", err)
    }
    finally { setLoading(false) }
  }, [selectedOrgId])

  useEffect(() => { if (!ready) return; setLoading(true); load() }, [load, ready])
  useEffect(() => {
    if (reports.some(r => IN_PROGRESS.has(r.status_code))) pollRef.current = setInterval(load, 4000)
    return () => { if (pollRef.current) clearInterval(pollRef.current) }
  }, [reports, load])

  useEffect(() => {
    const refs = dedupeLinkedEntities(
      reports.flatMap(report => getReportLinkedEntityRefs(report, selectedWorkspaceName || undefined)),
    ).filter(ref => !entityLabels[ref.cacheKey])

    if (refs.length === 0) return

    let cancelled = false

    ;(async () => {
      const resolved = await Promise.all(refs.map(async (ref) => {
        try {
          if (ref.type === "workspace") return [ref.cacheKey, ref.fallbackLabel] as const
          if (ref.type === "framework") {
            const framework = await getFramework(ref.id)
            return [ref.cacheKey, framework.name || framework.framework_code || ref.fallbackLabel] as const
          }
          if (ref.type === "engagement") {
            const engagement = await engagementsApi.get(ref.id)
            return [ref.cacheKey, engagement.engagement_name || engagement.engagement_code || ref.fallbackLabel] as const
          }
          if (ref.type === "risk") {
            const risk = await getRisk(ref.id)
            return [ref.cacheKey, risk.title || risk.risk_code || ref.fallbackLabel] as const
          }
          if (ref.type === "control" && ref.frameworkId) {
            const control = await getControl(ref.frameworkId, ref.id)
            return [ref.cacheKey, control.name || control.control_code || ref.fallbackLabel] as const
          }
        } catch {
          // Keep the fallback label if the related entity cannot be resolved.
        }
        return [ref.cacheKey, ref.fallbackLabel] as const
      }))

      if (cancelled) return

      setEntityLabels(prev => {
        const next = { ...prev }
        for (const [key, value] of resolved) next[key] = value
        return next
      })
    })()

    return () => { cancelled = true }
  }, [entityLabels, reports, selectedWorkspaceName])

  async function handleDelete(id: string) {
    if (!confirm("Delete this report?")) return
    setDeleting(id)
    try { await deleteReport(id); setReports(prev => prev.filter(r => r.id !== id)) }
    catch (e: any) { alert(e.message || "Failed to delete") }
    finally { setDeleting(null) }
  }

  const handleDownload = useCallback(async (reportId: string, format: string) => {
    try {
      await downloadReport(reportId, format)
    } catch (e: any) {
      alert(e.message || "Download failed")
    }
  }, [])

  function handleGenerated(report: ReportResponse) {
    setShowGenerate(false)
    setReports(prev => [report as unknown as ReportSummaryResponse, ...prev])
    setViewingId(report.id)
  }

  // Build scope groups
  const scopeGroups: Record<string, string[]> = {}
  Object.entries(REPORT_SCOPE_MAP).forEach(([type, def]) => {
    if (!scopeGroups[def.scope]) scopeGroups[def.scope] = []
    scopeGroups[def.scope].push(type)
  })

  const inProgressCount = reports.filter(r => IN_PROGRESS.has(r.status_code)).length
  const frameworkOptions = dedupeLinkedEntities(
    reports.flatMap(report => getReportLinkedEntityRefs(report, selectedWorkspaceName || undefined)),
  )
    .filter(ref => ref.type === "framework")
    .map(ref => ({
      id: ref.id,
      label: entityLabels[ref.cacheKey] || ref.fallbackLabel,
    }))

  const displayedReports = reports.filter(report => {
    if (filterScope !== "all" && REPORT_SCOPE_MAP[report.report_type]?.scope !== filterScope) return false
    if (frameworkFilter !== "all") {
      const frameworkId = asString(asRecord(report.parameters_json).framework_id)
      if (frameworkId !== frameworkFilter) return false
    }
    return true
  })

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Reports</h1>
          <p className="text-sm text-muted-foreground mt-1">AI-generated GRC reports and assessments</p>
        </div>
        {pageTab === "reports" ? (
          <button
            onClick={() => { setGeneratePrefill(undefined); setShowGenerate(true) }}
            className="flex items-center gap-2 h-9 px-4 rounded-lg bg-primary hover:bg-primary/90 text-sm text-primary-foreground font-medium transition-colors"
          >
            <Sparkles className="w-4 h-4" /> New Report
          </button>
        ) : null}
      </div>

      {/* Page tabs */}
      <div className="flex items-center gap-1 border-b border-border">
        <button
          onClick={() => setPageTab("reports")}
          className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${pageTab === "reports" ? "border-primary text-foreground" : "border-transparent text-muted-foreground hover:text-foreground"}`}
        >
          <BarChart3 className="w-4 h-4" /> Reports
        </button>
        <button
          onClick={() => setPageTab("assessments")}
          className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${pageTab === "assessments" ? "border-primary text-foreground" : "border-transparent text-muted-foreground hover:text-foreground"}`}
        >
          <ClipboardCheck className="w-4 h-4" /> Assessments
        </button>
      </div>

      {pageTab === "assessments" && selectedOrgId && (
        <AssessmentsPanel orgId={selectedOrgId} workspaceId={selectedWorkspaceId ?? ""} />
      )}

      {pageTab === "assessments" && !selectedOrgId && (
        <div className="flex flex-col items-center justify-center h-64 text-muted-foreground">
          <ClipboardCheck className="h-12 w-12 mb-3 opacity-20" />
          <p>Select an organization to view assessments</p>
        </div>
      )}

      {pageTab === "reports" && (
      <>
      {/* Report type launcher — compact table */}
      <div className="hidden md:block rounded-xl border border-border bg-card overflow-hidden">
        <div className="px-4 py-2.5 border-b border-border bg-muted/40 flex items-center justify-between">
          <p className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Report Types</p>
          <p className="text-[11px] text-muted-foreground">Click to generate</p>
        </div>
        <div className="divide-y divide-border">
          {SCOPE_ORDER.map(scope => {
            const types = scopeGroups[scope]
            if (!types?.length) return null
            const a = SCOPE_ACCENT[scope]
            return (
              <div key={scope} className={`flex items-center gap-4 px-4 py-2.5 border-l-[3px] ${a.border}`}>
                <span className={`text-[10px] font-bold uppercase tracking-widest w-20 shrink-0 ${a.text}`}>{scope}</span>
                <div className="flex flex-wrap gap-1.5">
                  {types.map(type => (
                    <button
                      key={type}
                      onClick={() => { setGeneratePrefill({ report_type: type }); setShowGenerate(true) }}
                      className="group flex items-center gap-1.5 h-7 px-2.5 rounded-md border border-border bg-background hover:bg-accent hover:border-border/80 text-xs text-muted-foreground hover:text-foreground transition-all"
                    >
                      <span className={`[&>svg]:w-3 [&>svg]:h-3 shrink-0 ${a.text} opacity-70 group-hover:opacity-100`}>
                        {REPORT_TYPE_ICONS[type] ?? <FileText className="w-3 h-3" />}
                      </span>
                      {REPORT_TYPE_LABELS[type]}
                    </button>
                  ))}
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Reports list */}
      <div className="rounded-xl border border-border bg-card overflow-hidden">
        {/* List header */}
        <div className="flex items-center gap-2 px-4 py-2.5 border-b border-border bg-muted/40">
          <div className="flex-1 flex items-center gap-1 overflow-x-auto whitespace-nowrap scrollbar-hide min-w-0">
            {/* All tab */}
            <button
              onClick={() => setFilterScope("all")}
              className={`flex-shrink-0 h-7 px-3 rounded-md text-xs font-medium transition-colors ${filterScope === "all" ? "bg-background border border-border text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground"}`}
            >
              All {total > 0 && <span className="ml-1 text-muted-foreground font-normal">{total}</span>}
            </button>
            {SCOPE_ORDER.map(scope => {
              const count = reports.filter(r => REPORT_SCOPE_MAP[r.report_type]?.scope === scope).length
              if (!count) return null
              return (
                <button
                  key={scope}
                  onClick={() => setFilterScope(scope)}
                  className={`flex-shrink-0 h-7 px-3 rounded-md text-xs font-medium transition-colors capitalize ${filterScope === scope ? "bg-background border border-border text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground"}`}
                >
                  {scope} <span className="ml-1 text-muted-foreground font-normal">{count}</span>
                </button>
              )
            })}
          </div>
          <div className="ml-auto flex items-center gap-2">
            <select
              value={frameworkFilter}
              onChange={(e) => setFrameworkFilter(e.target.value)}
              className="h-7 rounded-md border border-border bg-background px-2.5 text-[11px] text-foreground"
            >
              <option value="all">All frameworks</option>
              {frameworkOptions.map(option => (
                <option key={option.id} value={option.id}>{option.label}</option>
              ))}
            </select>
            {inProgressCount > 0 && (
              <span className="flex items-center gap-1.5 text-[11px] text-blue-500">
                <Loader2 className="w-3 h-3 animate-spin" /> {inProgressCount} generating
              </span>
            )}
          </div>
        </div>

        {/* List body */}
        {loading && (
          <div className="flex items-center justify-center py-16">
            <Loader2 className="w-5 h-5 animate-spin text-muted-foreground" />
          </div>
        )}

        {!loading && displayedReports.length === 0 && (
          <div className="flex flex-col items-center justify-center py-16 gap-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-muted">
              <FileText className="w-5 h-5 text-muted-foreground" />
            </div>
            <div className="text-center">
              <p className="font-medium text-sm">No reports yet</p>
              <p className="text-muted-foreground text-xs mt-1">Click any report type above to generate one</p>
            </div>
          </div>
        )}

        {!loading && displayedReports.length > 0 && (
          <div className="divide-y divide-border">
            {displayedReports.map(report => {
              const sc = STATUS_CONFIG[report.status_code] ?? STATUS_CONFIG.queued
              const def = REPORT_SCOPE_MAP[report.report_type]
              const accent = def ? SCOPE_ACCENT[def.scope] : null
              const linkedEntities = getReportLinkedEntityRefs(report, selectedWorkspaceName || undefined)
              return (
                <div
                  key={report.id}
                  className={`group flex items-start sm:items-center gap-3 px-4 py-4 sm:py-3 hover:bg-muted/30 transition-colors cursor-pointer border-l-[3px] ${accent?.border ?? "border-l-border"}`}
                  onClick={() => setViewingId(report.id)}
                >
                  {/* Icon */}
                  <div className="shrink-0 rounded-lg p-1.5 bg-muted text-muted-foreground mt-0.5 sm:mt-0">
                    <span className="[&>svg]:w-3.5 [&>svg]:h-3.5">{REPORT_TYPE_ICONS[report.report_type] ?? <FileText className="w-3.5 h-3.5" />}</span>
                  </div>

                  {/* Info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex flex-col gap-2">
                      <p className="text-sm font-semibold text-foreground leading-snug">
                        {report.title || REPORT_TYPE_LABELS[report.report_type] || report.report_type}
                      </p>
                      <div className="flex items-center gap-x-2.5 gap-y-1.5 flex-wrap">
                        <p className="text-[11px] text-muted-foreground whitespace-nowrap">
                          {new Date(report.created_at).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" })}
                        </p>
                        <ScopeBadge reportType={report.report_type} />
                        {linkedEntities.map(entity => (
                          <SourceBadge
                            key={entity.cacheKey}
                            entity={entity}
                            label={entityLabels[entity.cacheKey] || entity.fallbackLabel}
                          />
                        ))}
                        {report.status_code === "completed" && enhancedIds.has(report.id) && (
                          <span className="flex items-center gap-1 text-[10px] font-semibold px-2 py-1 rounded-full border bg-violet-500/10 text-violet-500 border-violet-500/30 whitespace-nowrap">
                            <Sparkles className="w-3 h-3" /> Enhanced
                          </span>
                        )}
                        {report.status_code === "completed" && assessedIds.has(report.id) ? (
                          <span className="flex items-center gap-1 text-[10px] font-semibold px-2 py-1 rounded-full border bg-emerald-500/10 text-emerald-500 border-emerald-500/30 whitespace-nowrap">
                            <CheckCircle2 className="w-3 h-3" /> Assessed
                          </span>
                        ) : report.status_code === "completed" ? (
                          <span className="flex items-center gap-1 text-[10px] font-medium px-2 py-1 rounded-full border border-dashed border-muted-foreground/30 text-muted-foreground/60 whitespace-nowrap">
                            Not Assessed
                          </span>
                        ) : null}
                        <span className={`flex items-center gap-1.5 text-[11px] font-semibold px-2 py-1 rounded-full border ${sc.badge} whitespace-nowrap`}>
                          {sc.icon} {sc.label}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-0.5 sm:opacity-0 group-hover:opacity-100 transition-opacity shrink-0 mt-2 sm:mt-0" onClick={e => e.stopPropagation()}>
                    {report.status_code === "completed" && (
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <button className="rounded-md p-1.5 text-muted-foreground hover:text-foreground hover:bg-accent transition-colors" title="Download">
                            <Download className="w-3.5 h-3.5" />
                          </button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end" className="w-40">
                          <DropdownMenuItem onClick={() => handleDownload(report.id, "pdf")} className="cursor-pointer">
                            <FileText className="mr-2 h-3.5 w-3.5 text-sky-500" />
                            <span className="text-xs">PDF</span>
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => handleDownload(report.id, "docx")} className="cursor-pointer">
                            <FileText className="mr-2 h-3.5 w-3.5 text-blue-500" />
                            <span className="text-xs">Word</span>
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => handleDownload(report.id, "md")} className="cursor-pointer">
                            <FileText className="mr-2 h-3.5 w-3.5 text-violet-500" />
                            <span className="text-xs">Markdown</span>
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    )}
                    <button onClick={() => handleDelete(report.id)} disabled={deleting === report.id} className="rounded-md p-1.5 text-muted-foreground hover:text-red-500 hover:bg-red-500/10 transition-colors disabled:opacity-50" title="Delete">
                      {deleting === report.id ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Trash2 className="w-3.5 h-3.5" />}
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* Dialogs */}
      {showGenerate && (
        <GenerateDialog
          orgId={selectedOrgId} workspaceId={selectedWorkspaceId} workspaceName={selectedWorkspaceName}
          onClose={() => { setShowGenerate(false); setGeneratePrefill(undefined) }}
          onGenerated={handleGenerated} prefill={generatePrefill}
        />
      )}
      {viewingId && (
        <ReportViewer
          reportId={viewingId}
          onClose={() => setViewingId(null)}
          onAssessed={id => setAssessedIds(prev => new Set([...prev, id]))}
          onEnhanced={id => setEnhancedIds(prev => new Set([...prev, id]))}
          workspaceName={selectedWorkspaceName || undefined}
        />
      )}
      </>
      )}
    </div>
  )
}
