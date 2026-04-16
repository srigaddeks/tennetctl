"use client"

import * as React from "react"
import {
  Activity,
  AlertTriangle,
  BarChart3,
  BookOpen,
  CheckCircle2,
  ClipboardList,
  Clock,
  Download,
  Eye,
  FileText,
  Globe,
  Loader2,
  Map as MapIcon,
  RefreshCw,
  ShieldCheck,
  Sparkles,
  Trash2,
  Users,
  Wrench,
  X,
  XCircle,
} from "lucide-react"

import {
  Badge,
  Button,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Input,
  Label,
} from "@kcontrol/ui"
import { toast } from "sonner"

import {
  deleteReport,
  downloadReport,
  generateReport,
  listReports,
  REPORT_TYPE_LABELS,
  type ReportResponse,
  type ReportSummaryResponse,
} from "@/lib/api/ai"
import type { Engagement } from "@/lib/api/engagements"
import { getFramework, listAllControls, listRisks } from "@/lib/api/grc"

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" ? (value as Record<string, unknown>) : {}
}

function asString(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value : null
}

function getReportEngagementId(report: ReportSummaryResponse): string | null {
  const params = asRecord(report.parameters_json)
  return (
    (report.trigger_entity_type === "engagement" ? report.trigger_entity_id : null) ??
    asString(params.engagement_id)
  )
}

function getReportFrameworkId(report: ReportSummaryResponse): string | null {
  const params = asRecord(report.parameters_json)
  return asString(params.framework_id)
}

function isReportInEngagementContext(
  report: ReportSummaryResponse,
  engagementFrameworks: Map<string, string>,
  workspaceId?: string,
): boolean {
  if (!engagementFrameworks.size) return false

  const reportEngagementId = getReportEngagementId(report)
  const reportFrameworkId = getReportFrameworkId(report)
  if (!reportEngagementId || !reportFrameworkId) return false

  const expectedFrameworkId = engagementFrameworks.get(reportEngagementId)
  if (!expectedFrameworkId) return false
  if (reportFrameworkId !== expectedFrameworkId) return false
  if (workspaceId && report.workspace_id !== workspaceId) return false
  return true
}

type ReportScope = "workspace" | "framework" | "control" | "risk" | "task"

interface ReportScopeDef {
  scope: ReportScope
  label: string
  description: string
  pickers: Array<"framework" | "control" | "risk">
  required: Array<"framework" | "control" | "risk">
}

const REPORT_SCOPE_MAP: Record<string, ReportScopeDef> = {
  executive_summary: {
    scope: "workspace",
    label: "Engagement",
    description: "Executive summary for the selected engagement",
    pickers: [],
    required: [],
  },
  compliance_posture: {
    scope: "workspace",
    label: "Engagement",
    description: "Compliance posture for the selected engagement",
    pickers: [],
    required: [],
  },
  board_risk_report: {
    scope: "workspace",
    label: "Engagement",
    description: "Board-level risk perspective for the selected engagement",
    pickers: [],
    required: [],
  },
  vendor_risk: {
    scope: "workspace",
    label: "Engagement",
    description: "Vendor and third-party risk context",
    pickers: [],
    required: [],
  },
  remediation_plan: {
    scope: "workspace",
    label: "Engagement",
    description: "Prioritized remediation roadmap",
    pickers: [],
    required: [],
  },
  audit_trail: {
    scope: "workspace",
    label: "Engagement",
    description: "Timeline and evidence audit trail",
    pickers: [],
    required: [],
  },
  framework_compliance: {
    scope: "framework",
    label: "Framework",
    description: "Compliance status for the engagement framework",
    pickers: ["framework"],
    required: ["framework"],
  },
  framework_readiness: {
    scope: "framework",
    label: "Framework",
    description: "Readiness report for the engagement framework",
    pickers: ["framework"],
    required: ["framework"],
  },
  framework_gap_analysis: {
    scope: "framework",
    label: "Framework",
    description: "Gap analysis against the engagement framework",
    pickers: ["framework"],
    required: ["framework"],
  },
  control_status: {
    scope: "control",
    label: "Control",
    description: "Control status for the engagement",
    pickers: ["framework", "control"],
    required: [],
  },
  evidence_report: {
    scope: "control",
    label: "Control",
    description: "Evidence adequacy for a control in this engagement",
    pickers: ["framework", "control"],
    required: [],
  },
  risk_summary: {
    scope: "risk",
    label: "Risk",
    description: "Risk summary for the engagement context",
    pickers: ["framework", "risk"],
    required: [],
  },
  task_health: {
    scope: "task",
    label: "Task",
    description: "Task backlog and due-date health",
    pickers: ["framework"],
    required: [],
  },
}

const SCOPE_ACCENT: Record<ReportScope, { border: string; text: string; badge: string; bg: string }> = {
  workspace: { border: "border-l-sky-500", text: "text-sky-500", badge: "bg-sky-500/10 text-sky-500 border-sky-500/30", bg: "bg-sky-500/5" },
  framework: { border: "border-l-violet-500", text: "text-violet-400", badge: "bg-violet-500/10 text-violet-400 border-violet-500/30", bg: "bg-violet-500/5" },
  control: { border: "border-l-emerald-500", text: "text-emerald-400", badge: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30", bg: "bg-emerald-500/5" },
  risk: { border: "border-l-orange-500", text: "text-orange-400", badge: "bg-orange-500/10 text-orange-400 border-orange-500/30", bg: "bg-orange-500/5" },
  task: { border: "border-l-amber-500", text: "text-amber-400", badge: "bg-amber-500/10 text-amber-400 border-amber-500/30", bg: "bg-amber-500/5" },
}

const STATUS_CONFIG: Record<string, { icon: React.ReactNode; badge: string; label: string }> = {
  queued: { icon: <Clock className="h-3 w-3" />, badge: "bg-muted text-muted-foreground border-border", label: "Queued" },
  planning: { icon: <Loader2 className="h-3 w-3 animate-spin" />, badge: "bg-blue-500/10 text-blue-400 border-blue-500/30", label: "Planning" },
  collecting: { icon: <Loader2 className="h-3 w-3 animate-spin" />, badge: "bg-blue-500/10 text-blue-400 border-blue-500/30", label: "Collecting" },
  analyzing: { icon: <Loader2 className="h-3 w-3 animate-spin" />, badge: "bg-violet-500/10 text-violet-400 border-violet-500/30", label: "Analyzing" },
  writing: { icon: <Loader2 className="h-3 w-3 animate-spin" />, badge: "bg-amber-500/10 text-amber-400 border-amber-500/30", label: "Writing" },
  formatting: { icon: <Loader2 className="h-3 w-3 animate-spin" />, badge: "bg-amber-500/10 text-amber-400 border-amber-500/30", label: "Formatting" },
  completed: { icon: <CheckCircle2 className="h-3 w-3" />, badge: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30", label: "Completed" },
  failed: { icon: <XCircle className="h-3 w-3" />, badge: "bg-red-500/10 text-red-400 border-red-500/30", label: "Failed" },
}

const REPORT_TYPE_ICONS: Record<string, React.ReactNode> = {
  executive_summary: <BarChart3 className="h-4 w-4" />,
  compliance_posture: <Activity className="h-4 w-4" />,
  framework_compliance: <ShieldCheck className="h-4 w-4" />,
  framework_readiness: <ShieldCheck className="h-4 w-4" />,
  framework_gap_analysis: <MapIcon className="h-4 w-4" />,
  control_status: <ClipboardList className="h-4 w-4" />,
  risk_summary: <AlertTriangle className="h-4 w-4" />,
  board_risk_report: <Globe className="h-4 w-4" />,
  vendor_risk: <Users className="h-4 w-4" />,
  remediation_plan: <Wrench className="h-4 w-4" />,
  task_health: <CheckCircle2 className="h-4 w-4" />,
  audit_trail: <BookOpen className="h-4 w-4" />,
  evidence_report: <Eye className="h-4 w-4" />,
}

const IN_PROGRESS = new Set(["queued", "planning", "collecting", "analyzing", "writing", "formatting"])
const SCOPE_ORDER: ReportScope[] = ["workspace", "framework", "control", "risk", "task"]

interface ReportsViewProps {
  orgId?: string
  workspaceId?: string
  workspaceName?: string
  engagementId?: string
  engagementName?: string
  engagementFrameworkId?: string
  engagements?: Engagement[]
}

export function ReportsView({
  orgId,
  workspaceId,
  workspaceName,
  engagementId,
  engagementName,
  engagementFrameworkId,
  engagements = [],
}: ReportsViewProps) {
  const [reports, setReports] = React.useState<ReportSummaryResponse[]>([])
  const [isLoading, setIsLoading] = React.useState(false)
  const [showGenerate, setShowGenerate] = React.useState(false)
  const [deleting, setDeleting] = React.useState<string | null>(null)
  const pollRef = React.useRef<number | null>(null)
  const eligibleEngagements = React.useMemo(
    () => engagements.filter((engagement) => !!engagement.framework_id),
    [engagements],
  )
  const engagementFrameworks = React.useMemo(
    () =>
      new Map(
        eligibleEngagements.map((engagement) => [engagement.id, engagement.framework_id] as const),
      ),
    [eligibleEngagements],
  )
  const engagementNames = React.useMemo(
    () =>
      new Map(
        engagements.map((engagement) => [engagement.id, engagement.engagement_name] as const),
      ),
    [engagements],
  )

  const loadReports = React.useCallback(async () => {
    if (!orgId || !engagementFrameworks.size) {
      setReports([])
      setIsLoading(false)
      return
    }

    setIsLoading(true)
    try {
      const data = await listReports(orgId, undefined, undefined, 100, 0)
      const sorted = [...(data.items || [])].sort(
        (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
      )
      setReports(
        sorted.filter((report) => isReportInEngagementContext(report, engagementFrameworks, workspaceId)),
      )
    } catch (error) {
      console.error("Failed to load reports:", error)
      toast.error((error as Error).message || "Failed to load reports")
    } finally {
      setIsLoading(false)
    }
  }, [engagementFrameworks, orgId, workspaceId])

  React.useEffect(() => {
    loadReports()
  }, [loadReports])

  React.useEffect(() => {
    if (pollRef.current) window.clearInterval(pollRef.current)

    if (reports.some((report) => IN_PROGRESS.has(report.status_code))) {
      pollRef.current = window.setInterval(loadReports, 4000)
    }

    return () => {
      if (pollRef.current) window.clearInterval(pollRef.current)
    }
  }, [loadReports, reports])

  const handleDelete = async (reportId: string) => {
    if (!window.confirm("Delete this report?")) return

    setDeleting(reportId)
    try {
      await deleteReport(reportId)
      setReports((current) => current.filter((report) => report.id !== reportId))
      toast.success("Report deleted")
    } catch (error) {
      toast.error((error as Error).message || "Failed to delete report")
    } finally {
      setDeleting(null)
    }
  }

  const handleDownload = async (reportId: string, format: string) => {
    try {
      await downloadReport(reportId, format)
    } catch (error) {
      toast.error((error as Error).message || "Failed to download report")
    }
  }

  const handleGenerated = (report: ReportResponse) => {
    setShowGenerate(false)
    setReports((current) => [report as ReportSummaryResponse, ...current])
    toast.success("Report queued")
  }

  if (!orgId) {
    return (
      <div className="rounded-3xl border border-dashed border-border/60 bg-card/70 px-6 py-20 text-center">
        <FileText className="mx-auto mb-4 h-12 w-12 text-muted-foreground/30" />
        <h3 className="text-lg font-black uppercase tracking-tight text-foreground">
          Select an organization to access reports
        </h3>
        <p className="mx-auto mt-2 max-w-xl text-sm text-muted-foreground">
          This tab is engagement-scoped. Choose an engagement from the workspace header to load live report history and generate a new report against that engagement’s framework.
        </p>
      </div>
    )
  }

  if (!eligibleEngagements.length) {
    return (
      <div className="rounded-3xl border border-dashed border-border/60 bg-card/70 px-6 py-20 text-center">
        <FileText className="mx-auto mb-4 h-12 w-12 text-muted-foreground/30" />
        <h3 className="text-lg font-black uppercase tracking-tight text-foreground">
          Create or link an engagement framework first
        </h3>
        <p className="mx-auto mt-2 max-w-xl text-sm text-muted-foreground">
          This reports tab only lists reports explicitly connected to an engagement and whose saved framework matches that engagement.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div className="space-y-1">
          <p className="text-[10px] font-black uppercase tracking-[0.3em] text-primary/70">
            Report Hub
          </p>
          <h2 className="text-2xl font-black tracking-tight text-foreground">
            {workspaceName || "Engagement Portfolio"}
          </h2>
          <p className="text-sm text-muted-foreground">
            Engagement-linked reports across all framework-backed engagements in this workspace.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={loadReports}
            disabled={isLoading}
            className="h-10 rounded-xl border-border/60 bg-background/80 px-4 text-muted-foreground hover:bg-muted hover:text-foreground"
          >
            <RefreshCw className={`mr-2 h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
            Refresh
          </Button>
          <Button
            onClick={() => setShowGenerate(true)}
            title="Generate a report from an engagement in this workspace"
            className="h-10 rounded-xl border border-primary/30 bg-primary/15 px-5 text-[11px] font-black uppercase tracking-[0.2em] text-primary hover:bg-primary/20"
          >
            <Sparkles className="mr-2 h-4 w-4" />
            Generate Report
          </Button>
        </div>
      </div>

      {reports.length === 0 && !isLoading ? (
        <div className="rounded-3xl border border-border/60 bg-card/70 py-24 text-center">
          <Sparkles className="mx-auto mb-4 h-12 w-12 text-muted-foreground/30" />
          <p className="text-sm font-black uppercase tracking-[0.25em] text-muted-foreground">
            No engagement-linked reports generated for {workspaceName || "this workspace"} yet
          </p>
          <Button
            variant="link"
            onClick={() => setShowGenerate(true)}
            className="mt-4 h-auto p-0 text-primary"
          >
            Create the first report
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-5 md:grid-cols-2 xl:grid-cols-3">
          {reports.map((report) => {
            const status = STATUS_CONFIG[report.status_code] || STATUS_CONFIG.queued
            const scopeDef = REPORT_SCOPE_MAP[report.report_type] || REPORT_SCOPE_MAP.executive_summary
            const accent = SCOPE_ACCENT[scopeDef.scope]
            const reportEngagementId = getReportEngagementId(report)
            const reportEngagementName = reportEngagementId
              ? engagementNames.get(reportEngagementId) ?? "Linked engagement"
              : null

            return (
              <Card
                key={report.id}
                className={`overflow-hidden border border-border/60 bg-card/85 shadow-sm transition-all hover:border-primary/30 ${accent.border} border-l-4`}
              >
                <CardHeader className="border-b border-border/60 bg-muted/20 pb-3">
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-center gap-3">
                      <div className={`flex h-10 w-10 items-center justify-center rounded-2xl ${accent.bg} ${accent.text}`}>
                        {REPORT_TYPE_ICONS[report.report_type] || <FileText className="h-4 w-4" />}
                      </div>
                      <div>
                        <CardTitle className="text-sm font-black uppercase tracking-tight text-foreground">
                          {report.title || REPORT_TYPE_LABELS[report.report_type]}
                        </CardTitle>
                        <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-muted-foreground">
                          {REPORT_TYPE_LABELS[report.report_type]}
                        </p>
                      </div>
                    </div>
                    <Badge variant="outline" className={`flex h-6 items-center gap-1.5 ${status.badge}`}>
                      {status.icon}
                      {status.label}
                    </Badge>
                  </div>
                </CardHeader>

                <CardContent className="space-y-4 pt-5">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-[10px] font-black uppercase tracking-[0.22em] text-muted-foreground">Created</p>
                      <p className="text-xs font-medium text-foreground/80">
                        {new Date(report.created_at).toLocaleDateString()} ·{" "}
                        {new Date(report.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                      </p>
                    </div>
                    <div className="flex flex-wrap items-center justify-end gap-2">
                      {reportEngagementName && (
                        <Badge variant="outline" className="border-primary/20 bg-primary/10 text-primary">
                          {reportEngagementName}
                        </Badge>
                      )}
                      <Badge variant="outline" className={accent.badge}>
                        {scopeDef.label}
                      </Badge>
                    </div>
                  </div>

                  <div className="flex items-center justify-between border-t border-border/60 pt-4">
                    <div className="flex items-center gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        disabled={IN_PROGRESS.has(report.status_code)}
                        onClick={() => handleDownload(report.id, "pdf")}
                        className="h-9 rounded-xl bg-muted/40 px-3 text-[10px] font-black uppercase tracking-[0.15em] text-muted-foreground hover:bg-muted hover:text-foreground"
                      >
                        <Download className="mr-1.5 h-3.5 w-3.5" />
                        PDF
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        disabled={IN_PROGRESS.has(report.status_code)}
                        onClick={() => handleDownload(report.id, "md")}
                        className="h-9 rounded-xl bg-muted/40 px-3 text-[10px] font-black uppercase tracking-[0.15em] text-muted-foreground hover:bg-muted hover:text-foreground"
                      >
                        MD
                      </Button>
                    </div>

                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => handleDelete(report.id)}
                      disabled={deleting === report.id}
                      className="h-9 w-9 rounded-xl text-muted-foreground hover:bg-red-500/10 hover:text-red-500 dark:hover:text-red-400"
                    >
                      {deleting === report.id ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4" />}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}

      {showGenerate && orgId && (
        <GenerateDialog
          orgId={orgId}
          workspaceId={workspaceId ?? ""}
          workspaceName={workspaceName ?? ""}
          engagements={engagements}
          initialEngagementId={engagementId}
          initialEngagementName={engagementName ?? ""}
          engagementFrameworkId={engagementFrameworkId}
          onClose={() => setShowGenerate(false)}
          onGenerated={handleGenerated}
          isEngagementRequired={true}
        />
      )}
    </div>
  )
}

export function GenerateDialog({
  orgId,
  workspaceId,
  workspaceName,
  engagements,
  initialEngagementId,
  initialEngagementName,
  engagementFrameworkId,
  onClose,
  onGenerated,
  isEngagementRequired = true,
}: {
  orgId: string
  workspaceId: string
  workspaceName: string
  engagements: Engagement[]
  initialEngagementId?: string
  initialEngagementName?: string
  engagementFrameworkId?: string
  onClose: () => void
  onGenerated: (report: ReportResponse) => void
  isEngagementRequired?: boolean
}) {
  const [reportType, setReportType] = React.useState("executive_summary")
  const [title, setTitle] = React.useState("")
  const [selectedEngagementId, setSelectedEngagementId] = React.useState(initialEngagementId ?? "")
  const [frameworkName, setFrameworkName] = React.useState<string>("")
  const [frameworkCode, setFrameworkCode] = React.useState<string>("")
  const [controlId, setControlId] = React.useState("")
  const [riskId, setRiskId] = React.useState("")
  const [controls, setControls] = React.useState<Array<{ id: string; name: string; code: string }>>([])
  const [risks, setRisks] = React.useState<Array<{ id: string; name: string; level_code: string }>>([])
  const [loadingFramework, setLoadingFramework] = React.useState(false)
  const [loading, setLoading] = React.useState(false)
  const [error, setError] = React.useState<string | null>(null)

  const scopeDef = REPORT_SCOPE_MAP[reportType] ?? REPORT_SCOPE_MAP.executive_summary
  const needsFramework = scopeDef.pickers.includes("framework")
  const needsControl = scopeDef.pickers.includes("control")
  const needsRisk = scopeDef.pickers.includes("risk")
  const isFrameworkRequired = scopeDef.required.includes("framework")
  const selectedEngagement = React.useMemo(
    () => engagements.find((engagement) => engagement.id === selectedEngagementId),
    [engagements, selectedEngagementId],
  )
  const engagementId = selectedEngagement?.id ?? initialEngagementId ?? ""
  const engagementName = selectedEngagement?.engagement_name ?? initialEngagementName ?? ""
  const frameworkId = selectedEngagement?.framework_id ?? engagementFrameworkId ?? ""

  React.useEffect(() => {
    setSelectedEngagementId(initialEngagementId ?? "")
  }, [initialEngagementId])

  React.useEffect(() => {
    if (!frameworkId) {
      setFrameworkName("")
      setFrameworkCode("")
      return
    }

    let cancelled = false
    setLoadingFramework(true)

    getFramework(frameworkId)
      .then((framework) => {
        if (cancelled) return
        setFrameworkName(framework.name)
        setFrameworkCode(framework.framework_code)
      })
      .catch((frameworkError) => {
        console.error("Failed to load engagement framework:", frameworkError)
        if (cancelled) return
        setFrameworkName("")
        setFrameworkCode("")
      })
      .finally(() => {
        if (!cancelled) setLoadingFramework(false)
      })

    return () => {
      cancelled = true
    }
  }, [frameworkId])

  React.useEffect(() => {
    if (!needsControl || !engagementId) {
      setControls([])
      return
    }

    listAllControls({
      engagement_id: engagementId,
      framework_id: frameworkId || undefined,
      limit: 100,
    })
      .then((result) => {
        setControls((result.items ?? []).map((control) => ({
          id: control.id,
          name: control.name,
          code: control.control_code,
        })))
      })
      .catch((controlsError) => {
        console.error("Failed to load controls:", controlsError)
        setControls([])
      })
  }, [engagementId, frameworkId, needsControl])

  React.useEffect(() => {
    if (!needsRisk) {
      setRisks([])
      return
    }

    listRisks({
      org_id: orgId,
      workspace_id: workspaceId || undefined,
      limit: 100,
    })
      .then((result) => {
        setRisks((result.items ?? []).map((risk) => ({
          id: risk.id,
          name: risk.title,
          level_code: risk.risk_level_code,
        })))
      })
      .catch((riskError) => {
        console.error("Failed to load risks:", riskError)
        setRisks([])
      })
  }, [needsRisk, orgId, workspaceId])

  React.useEffect(() => {
    setControlId("")
    setRiskId("")
  }, [reportType])

  React.useEffect(() => {
    setControlId("")
  }, [selectedEngagementId, frameworkId])

  const canSubmit = !loading && (isEngagementRequired ? !!engagementId : true) && (!isFrameworkRequired || !!frameworkId)

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    if (!canSubmit) return

    setError(null)
    setLoading(true)

    try {
      const parameters: Record<string, unknown> = {}
      if (frameworkId) parameters.framework_id = frameworkId
      if (controlId) parameters.control_id = controlId
      if (riskId) parameters.risk_id = riskId

      const report = await generateReport({
        report_type: reportType,
        title: title || undefined,
        org_id: orgId,
        workspace_id: workspaceId || undefined,
        engagement_id: engagementId || undefined,
        parameters,
      })

      onGenerated(report)
    } catch (submitError) {
      setError((submitError as Error).message || "Failed to queue report")
    } finally {
      setLoading(false)
    }
  }

  const scopeGroups = React.useMemo(() => {
    const groups: Partial<Record<ReportScope, string[]>> = {}
    Object.entries(REPORT_SCOPE_MAP).forEach(([type, definition]) => {
      groups[definition.scope] = [...(groups[definition.scope] ?? []), type]
    })
    return groups
  }, [])

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md"
      onClick={(event) => {
        if (event.target === event.currentTarget) onClose()
      }}
    >
      <Card className="mx-4 w-full max-w-2xl overflow-hidden rounded-3xl border border-border/60 bg-background shadow-2xl">
        <CardHeader className="border-b border-border/60 bg-card/70 px-8 py-6">
          <div className="flex items-start justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-primary/15 text-primary">
                <Sparkles className="h-5 w-5" />
              </div>
              <div>
                <CardTitle className="text-lg font-black uppercase tracking-tight text-foreground">
                  Generate Report
                </CardTitle>
                <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground">
                  {engagementName || workspaceName || "Selected Engagement"}
                </p>
              </div>
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={onClose}
              className="rounded-xl text-muted-foreground hover:bg-muted hover:text-foreground"
            >
              <X className="h-5 w-5" />
            </Button>
          </div>
        </CardHeader>

        <form onSubmit={handleSubmit} className="space-y-6 p-8">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="rounded-2xl border border-border/60 bg-card/70 p-4">
              <p className="text-[10px] font-black uppercase tracking-[0.22em] text-muted-foreground">
                Engagement Scope {isEngagementRequired ? "*" : "(optional)"}
              </p>
              <div className="mt-2">
                <select
                  value={selectedEngagementId}
                  onChange={(event) => setSelectedEngagementId(event.target.value)}
                  className="w-full rounded-xl border border-border/60 bg-background px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                >
                  <option value="">
                    {isEngagementRequired ? "Select an engagement..." : "Optional - No engagement selected"}
                  </option>
                  {engagements.map((engagement) => (
                    <option key={engagement.id} value={engagement.id}>
                      {engagement.engagement_name}
                    </option>
                  ))}
                </select>
              </div>
              <p className="mt-2 text-xs text-muted-foreground">
                {engagementId
                  ? "Every report generated here is tied to the selected engagement."
                  : isEngagementRequired
                    ? "Pick the engagement here and this dialog will use its linked framework automatically."
                    : "Optionally tie this report to an engagement for contextual analysis."}
              </p>
            </div>

            <div className="rounded-2xl border border-border/60 bg-card/70 p-4">
              <p className="text-[10px] font-black uppercase tracking-[0.22em] text-muted-foreground">Framework</p>
              {loadingFramework ? (
                <div className="mt-2 flex items-center gap-2 text-sm text-muted-foreground">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Loading engagement framework...
                </div>
              ) : frameworkId ? (
                <>
                  <p className="mt-2 text-sm font-semibold text-foreground">
                    {frameworkName || "Framework attached to engagement"}
                  </p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    {frameworkCode || "Framework code unavailable"}
                  </p>
                </>
              ) : (
                <p className="mt-2 text-sm text-muted-foreground">
                  No framework is linked to this engagement yet.
                </p>
              )}
            </div>
          </div>

          <div>
            <Label className="mb-3 block text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground">
              Report Type
            </Label>
            <div className="grid gap-2 rounded-2xl border border-border/60 bg-card/70 p-2">
              {SCOPE_ORDER.map((scope) => {
                const types = scopeGroups[scope] ?? []
                if (!types.length) return null

                const accent = SCOPE_ACCENT[scope]

                return (
                  <div key={scope} className="space-y-2 p-2">
                    <p className={`px-1 text-[9px] font-black uppercase tracking-[0.28em] ${accent.text}`}>
                      {scope} reports
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {types.map((type) => (
                        <button
                          key={type}
                          type="button"
                          onClick={() => setReportType(type)}
                          className={`rounded-xl px-3 py-2 text-[10px] font-black uppercase tracking-[0.15em] transition-all ${
                            reportType === type
                              ? `${accent.badge} border border-border/60`
                              : "text-muted-foreground hover:bg-muted hover:text-foreground"
                          }`}
                        >
                          {REPORT_TYPE_LABELS[type]}
                        </button>
                      ))}
                    </div>
                  </div>
                )
              })}
            </div>
            <p className="mt-2 text-xs text-muted-foreground">{scopeDef.description}</p>
          </div>

          <div className="space-y-2">
            <Label className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground">Custom Title</Label>
            <Input
              placeholder="Optional report title"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              className="h-11 rounded-xl border-border/60 bg-background text-foreground placeholder:text-muted-foreground/50"
            />
          </div>

          {needsFramework && (
            <div className="space-y-2">
              <Label className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground">
                Framework Anchor {isFrameworkRequired ? "*" : ""}
              </Label>
              <div className="rounded-2xl border border-border/60 bg-card/70 px-4 py-3">
                <p className="text-sm font-semibold text-foreground">
                  {frameworkName || "Framework attached to engagement"}
                </p>
                <p className="mt-1 text-xs text-muted-foreground">
                  {frameworkCode || "This page uses the framework already linked to the engagement."}
                </p>
              </div>
            </div>
          )}

          {needsControl && (
            <div className="space-y-2">
              <Label className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground">Control</Label>
              <select
                className="h-11 w-full rounded-xl border border-border/60 bg-background px-4 text-xs text-foreground outline-none"
                value={controlId}
                onChange={(event) => setControlId(event.target.value)}
              >
                <option value="">All controls in engagement</option>
                {controls.map((control) => (
                  <option key={control.id} value={control.id}>
                    {control.code} · {control.name}
                  </option>
                ))}
              </select>
            </div>
          )}

          {needsRisk && (
            <div className="space-y-2">
              <Label className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground">Risk</Label>
              <select
                className="h-11 w-full rounded-xl border border-border/60 bg-background px-4 text-xs text-foreground outline-none"
                value={riskId}
                onChange={(event) => setRiskId(event.target.value)}
              >
                <option value="">All risks in workspace scope</option>
                {risks.map((risk) => (
                  <option key={risk.id} value={risk.id}>
                    {risk.name} {risk.level_code ? `· ${risk.level_code}` : ""}
                  </option>
                ))}
              </select>
            </div>
          )}

          {error && <p className="text-xs font-semibold text-red-400">{error}</p>}
          {isEngagementRequired && !engagementId && !error && (
            <p className="text-xs font-semibold text-amber-300">
              Select an engagement to enable report generation.
            </p>
          )}

          <Button
            type="submit"
            disabled={!canSubmit}
            className="h-12 w-full rounded-2xl border border-primary/30 bg-primary/15 text-[11px] font-black uppercase tracking-[0.28em] text-primary hover:bg-primary/20"
          >
            {loading ? <Loader2 className="h-5 w-5 animate-spin" /> : "Queue Report"}
          </Button>
        </form>
      </Card>
    </div>
  )
}
