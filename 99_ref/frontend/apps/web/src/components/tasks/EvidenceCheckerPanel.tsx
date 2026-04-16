"use client"

/**
 * EvidenceCheckerPanel
 *
 * Full evidence checker UI for the task detail page.
 * - Shows live job status with progress bar (SSE polling via interval)
 * - Displays the active report with per-criterion verdicts
 * - Collapsible evidence references with confidence scores
 * - Version picker dropdown for historical reports
 * - One-click "Re-run" trigger (with criteria change detection note)
 */

import { useEffect, useState, useCallback, useRef } from "react"
import {
  CheckCircle2, XCircle, AlertTriangle, Clock, Loader2,
  ChevronDown, ChevronUp, RefreshCw, FileText,
  Sparkles, History, BookOpen, ArrowRight, Shield, Download, Search,
} from "lucide-react"
import { Button } from "@kcontrol/ui"
import {
  getEvidenceJob,
  getActiveEvidenceReport,
  getEvidenceReport,
  listEvidenceReports,
  triggerEvidenceCheck,
  downloadEvidenceReportMarkdown,
  type EvidenceJobStatus,
  type EvidenceReport,
  type EvidenceCriterionResult,
  type EvidenceReportSummary,
} from "@/lib/api/ai"

// ── Types ──────────────────────────────────────────────────────────────────────

type OverallVerdict = "ALL_MET" | "PARTIALLY_MET" | "NOT_MET" | "INCONCLUSIVE"
type CriterionVerdict = "MET" | "PARTIALLY_MET" | "NOT_MET" | "INSUFFICIENT_EVIDENCE"

// ── Verdict colour maps ────────────────────────────────────────────────────────

const OVERALL_VERDICT_META: Record<
  OverallVerdict,
  { label: string; badge: string; glow: string; icon: React.ReactNode }
> = {
  ALL_MET: {
    label: "All Criteria Met",
    badge: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30",
    glow: "from-emerald-500/8",
    icon: <CheckCircle2 className="w-5 h-5 text-emerald-400" />,
  },
  PARTIALLY_MET: {
    label: "Partially Met",
    badge: "bg-amber-500/10 text-amber-400 border-amber-500/30",
    glow: "from-amber-500/8",
    icon: <AlertTriangle className="w-5 h-5 text-amber-400" />,
  },
  NOT_MET: {
    label: "Not Met",
    badge: "bg-red-500/10 text-red-400 border-red-500/30",
    glow: "from-red-500/8",
    icon: <XCircle className="w-5 h-5 text-red-400" />,
  },
  INCONCLUSIVE: {
    label: "Inconclusive",
    badge: "bg-slate-500/10 text-slate-400 border-slate-500/30",
    glow: "from-slate-500/8",
    icon: <AlertTriangle className="w-5 h-5 text-slate-400" />,
  },
}

const CRITERION_VERDICT_META: Record<
  CriterionVerdict,
  { label: string; dot: string; badge: string; bg: string }
> = {
  MET: {
    label: "Met",
    dot: "bg-emerald-500",
    badge: "text-emerald-400 bg-emerald-500/10 border-emerald-500/25",
    bg: "border-emerald-500/20",
  },
  PARTIALLY_MET: {
    label: "Partially Met",
    dot: "bg-amber-500",
    badge: "text-amber-400 bg-amber-500/10 border-amber-500/25",
    bg: "border-amber-500/20",
  },
  NOT_MET: {
    label: "Not Met",
    dot: "bg-red-500",
    badge: "text-red-400 bg-red-500/10 border-red-500/25",
    bg: "border-red-500/20",
  },
  INSUFFICIENT_EVIDENCE: {
    label: "Insufficient Evidence",
    dot: "bg-slate-500",
    badge: "text-slate-400 bg-slate-500/10 border-slate-500/25",
    bg: "border-slate-500/20",
  },
}

const STATUS_META: Record<
  string,
  { label: string; color: string; pulse: boolean }
> = {
  queued:     { label: "Queued",     color: "text-slate-400",   pulse: false },
  ingesting:  { label: "Ingesting documents…",  color: "text-sky-400",    pulse: true  },
  evaluating: { label: "Evaluating criteria…",  color: "text-purple-400", pulse: true  },
  completed:  { label: "Completed",  color: "text-emerald-400", pulse: false },
  failed:     { label: "Failed",     color: "text-red-400",     pulse: false },
  superseded: { label: "Superseded", color: "text-slate-400",   pulse: false },
  cancelled:  { label: "Cancelled",  color: "text-slate-400",   pulse: false },
}

// ── Helpers ────────────────────────────────────────────────────────────────────

function confidenceBar(conf: number) {
  const pct = Math.round(conf * 100)
  const color =
    pct >= 80 ? "bg-emerald-500" :
    pct >= 50 ? "bg-amber-500" :
    "bg-red-400"
  return (
    <div className="flex items-center gap-1.5 min-w-0">
      <div className="w-16 h-1.5 rounded-full bg-muted overflow-hidden shrink-0">
        <div className={`h-1.5 rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-[10px] text-muted-foreground tabular-nums shrink-0">{pct}%</span>
    </div>
  )
}

function formatDuration(seconds: number) {
  if (seconds < 60) return `${Math.round(seconds)}s`
  return `${Math.floor(seconds / 60)}m ${Math.round(seconds % 60)}s`
}

function formatDateShort(iso: string) {
  return new Date(iso).toLocaleString([], { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })
}

// ── Criterion Card ─────────────────────────────────────────────────────────────

function CriterionCard({ result }: { result: EvidenceCriterionResult }) {
  const [expanded, setExpanded] = useState(false)
  const vm = CRITERION_VERDICT_META[result.verdict] ?? CRITERION_VERDICT_META.INSUFFICIENT_EVIDENCE
  const hasRefs = result.evidence_references.length > 0 || result.conflicting_references.length > 0
  const hasDetails = hasRefs || Boolean(result.gap_analysis && result.verdict !== "MET")

  return (
    <div className={`rounded-xl border ${vm.bg} bg-card overflow-hidden transition-all`}>
      {/* Header row */}
      <button
        type="button"
        className="w-full text-left px-4 py-3.5 flex items-start gap-3 hover:bg-muted/20 transition-colors"
        onClick={() => setExpanded(e => !e)}
        aria-expanded={expanded}
      >
        <span className={`mt-1 w-2 h-2 rounded-full shrink-0 ${vm.dot}`} />
        <div className="flex-1 min-w-0">
          <p className="text-sm text-foreground leading-snug font-medium">{result.criterion_text}</p>
          {result.justification && (
            <p className="text-xs text-muted-foreground mt-1.5 leading-relaxed line-clamp-2">{result.justification}</p>
          )}
        </div>
        <div className="flex items-center gap-2 shrink-0 ml-2">
          <span className={`inline-flex items-center px-2 py-0.5 rounded-full border text-[10px] font-semibold ${vm.badge}`}>
            {vm.label}
          </span>
          {hasDetails && (
            expanded
              ? <ChevronUp className="w-3.5 h-3.5 text-muted-foreground" />
              : <ChevronDown className="w-3.5 h-3.5 text-muted-foreground" />
          )}
        </div>
      </button>

      {/* Expanded evidence */}
      {expanded && (hasRefs || result.gap_analysis) && (
        <div className="px-4 pb-4 pt-1 border-t border-border/50 space-y-3">

          {/* Gap Analysis */}
          {result.gap_analysis && result.verdict !== "MET" && (
            <div className="rounded-lg bg-amber-500/5 border border-amber-500/20 px-3 py-2.5">
              <p className="text-[10px] font-semibold text-amber-400 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
                <Search className="w-3 h-3" />
                Evidence Gap
              </p>
              <p className="text-xs text-muted-foreground leading-relaxed">{result.gap_analysis}</p>
            </div>
          )}

          {/* Supporting evidence */}
          {result.evidence_references.length > 0 && (
            <div>
              <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                Supporting Evidence ({result.evidence_references.length})
              </p>
              <div className="space-y-2">
                {result.evidence_references.map((ref, i) => (
                  <div key={i} className="rounded-lg bg-muted/30 border border-border/50 px-3 py-2.5 space-y-1.5">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-[11px] font-semibold text-foreground flex items-center gap-1">
                        <FileText className="w-3 h-3 text-sky-400" />
                        {ref.document_filename}
                      </span>
                      {ref.page_number != null && (
                        <span className="text-[10px] text-muted-foreground">p.{ref.page_number}</span>
                      )}
                      {ref.section_or_sheet && (
                        <span className="text-[10px] text-muted-foreground">{ref.section_or_sheet}</span>
                      )}
                      {confidenceBar(ref.confidence)}
                    </div>
                    <p className="text-xs text-muted-foreground italic leading-relaxed">&ldquo;{ref.excerpt}&rdquo;</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Conflicting evidence */}
          {result.conflicting_references.length > 0 && (
            <div>
              <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <XCircle className="w-3 h-3 text-red-400" />
                Conflicting Evidence ({result.conflicting_references.length})
              </p>
              <div className="space-y-2">
                {result.conflicting_references.map((ref, i) => (
                  <div key={i} className="rounded-lg bg-red-500/5 border border-red-500/20 px-3 py-2.5 space-y-1.5">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-[11px] font-semibold text-foreground flex items-center gap-1">
                        <FileText className="w-3 h-3 text-red-400" />
                        {ref.document_filename}
                      </span>
                      {ref.page_number != null && (
                        <span className="text-[10px] text-muted-foreground">p.{ref.page_number}</span>
                      )}
                      {confidenceBar(ref.confidence)}
                    </div>
                    <p className="text-xs text-muted-foreground italic leading-relaxed">&ldquo;{ref.excerpt}&rdquo;</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ── Job Progress Banner ────────────────────────────────────────────────────────

function JobProgressBanner({ job }: { job: EvidenceJobStatus }) {
  const sm = STATUS_META[job.status_code] ?? { label: job.status_code, color: "text-muted-foreground", pulse: false }
  const hasCriteria = job.progress_criteria_total > 0
  const pct = hasCriteria
    ? Math.round((job.progress_criteria_done / job.progress_criteria_total) * 100)
    : 0

  return (
    <div className="rounded-xl border border-purple-500/20 bg-purple-500/5 px-4 py-3 space-y-2.5">
      <div className="flex items-center justify-between gap-2 flex-wrap">
        <div className="flex items-center gap-2">
          {sm.pulse ? (
            <Loader2 className={`w-4 h-4 animate-spin ${sm.color}`} />
          ) : (
            <Clock className={`w-4 h-4 ${sm.color}`} />
          )}
          <span className={`text-sm font-semibold ${sm.color}`}>{sm.label}</span>
        </div>

        {job.queue_position != null && job.queue_position > 0 && (
          <span className="text-[10px] text-muted-foreground">
            Queue position: #{job.queue_position}
          </span>
        )}

        {job.status_code === "evaluating" && hasCriteria && (
          <span className="text-[10px] text-muted-foreground tabular-nums">
            {job.progress_criteria_done}/{job.progress_criteria_total} criteria
          </span>
        )}
      </div>

      {/* Progress bar */}
      {job.status_code === "evaluating" && hasCriteria && (
        <div>
          <div className="w-full bg-muted rounded-full h-1.5">
            <div
              className="bg-purple-500 h-1.5 rounded-full transition-all duration-700"
              style={{ width: `${pct}%` }}
            />
          </div>
          <p className="text-[10px] text-muted-foreground mt-1">{pct}% complete</p>
        </div>
      )}

      {job.status_code === "ingesting" && (
        <div className="w-full bg-muted rounded-full h-1.5 overflow-hidden">
          <div className="h-1.5 bg-sky-500 animate-pulse rounded-full w-1/3" />
        </div>
      )}

      {job.status_code === "failed" && job.error_message && (
        <p className="text-xs text-red-400 bg-red-500/10 rounded-lg px-3 py-2 border border-red-500/20">
          {job.error_message.slice(0, 200)}
        </p>
      )}
    </div>
  )
}

// ── Main Panel ─────────────────────────────────────────────────────────────────

interface EvidenceCheckerPanelProps {
  taskId: string
  /** Number of attachments on the task — used to show the empty state */
  attachmentCount: number
  /** Called when user clicks "Upload evidence" shortcut */
  onGoToAttachments?: () => void
}

export function EvidenceCheckerPanel({
  taskId,
  attachmentCount,
  onGoToAttachments,
}: EvidenceCheckerPanelProps) {
  const [job, setJob] = useState<EvidenceJobStatus | null>(null)
  const [report, setReport] = useState<EvidenceReport | null>(null)
  const [reportSummaries, setReportSummaries] = useState<EvidenceReportSummary[]>([])
  const [selectedReportId, setSelectedReportId] = useState<string | null>(null)
  const [loadingReport, setLoadingReport] = useState(false)
  const [triggering, setTriggering] = useState(false)
  const [triggerError, setTriggerError] = useState<string | null>(null)
  const [downloading, setDownloading] = useState(false)
  const [initialLoading, setInitialLoading] = useState(true)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // Load job status + active report
  const load = useCallback(async (quiet = false) => {
    if (!quiet) setInitialLoading(true)
    try {
      const [jobRes, summaries] = await Promise.allSettled([
        getEvidenceJob(taskId),
        listEvidenceReports(taskId),
      ])

      if (jobRes.status === "fulfilled") setJob(jobRes.value.job)
      if (summaries.status === "fulfilled") setReportSummaries(summaries.value.reports)

      // Load active report if not already viewing a historical one
      if (!selectedReportId) {
        try {
          const activeRes = await getActiveEvidenceReport(taskId)
          setReport(activeRes.report)
        } catch {
          setReport(null)
        }
      }
    } catch {
      // silently fail on poll
    } finally {
      if (!quiet) setInitialLoading(false)
    }
  }, [taskId, selectedReportId])

  useEffect(() => {
    load()
  }, [taskId]) // eslint-disable-line react-hooks/exhaustive-deps

  // Poll while job is active
  useEffect(() => {
    const isActive = job?.status_code === "queued" || job?.status_code === "ingesting" || job?.status_code === "evaluating"
    if (isActive) {
      pollRef.current = setInterval(() => load(true), 3000)
    } else {
      if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null }
      // Reload report after completion
      if (job?.status_code === "completed") {
        load(true)
      }
    }
    return () => { if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null } }
  }, [job?.status_code, load])

  // Load historical report by ID
  const loadHistoricalReport = useCallback(async (reportId: string) => {
    setLoadingReport(true)
    setSelectedReportId(reportId)
    try {
      const res = await getEvidenceReport(reportId)
      setReport(res.report)
    } catch {
      // ignore
    } finally {
      setLoadingReport(false)
    }
  }, [])

  const handleVersionChange = useCallback(async (e: React.ChangeEvent<HTMLSelectElement>) => {
    const id = e.target.value
    if (!id) {
      setSelectedReportId(null)
      try {
        const res = await getActiveEvidenceReport(taskId)
        setReport(res.report)
      } catch { setReport(null) }
      return
    }
    await loadHistoricalReport(id)
  }, [taskId, loadHistoricalReport])

  const handleTrigger = useCallback(async () => {
    setTriggering(true)
    setTriggerError(null)
    try {
      await triggerEvidenceCheck(taskId)
      // Start polling immediately
      await load(true)
    } catch (err) {
      setTriggerError(err instanceof Error ? err.message : "Failed to start evidence check")
    } finally {
      setTriggering(false)
    }
  }, [taskId, load])

  const handleDownload = useCallback(async () => {
    if (!report?.id) return
    setDownloading(true)
    try {
      await downloadEvidenceReportMarkdown(report.id)
    } catch (err) {
      console.error("Download failed:", err)
    } finally {
      setDownloading(false)
    }
  }, [report?.id])

  const isJobActive = job?.status_code === "queued" || job?.status_code === "ingesting" || job?.status_code === "evaluating"

  // ── Verdict summary ──────────────────────────────────────────────────────────

  const overallVm = report
    ? (OVERALL_VERDICT_META[report.overall_verdict as OverallVerdict] ?? OVERALL_VERDICT_META.INCONCLUSIVE)
    : null

  const metCount = report?.criteria_results.filter(r => r.verdict === "MET").length ?? 0
  const total = report?.criteria_results.length ?? 0

  // ── Loading skeleton ─────────────────────────────────────────────────────────

  if (initialLoading) {
    return (
      <div className="space-y-3">
        <div className="h-20 rounded-xl bg-muted animate-pulse" />
        <div className="h-12 rounded-xl bg-muted animate-pulse" />
        <div className="h-12 rounded-xl bg-muted animate-pulse" />
      </div>
    )
  }

  // ── No attachments state ─────────────────────────────────────────────────────

  if (attachmentCount === 0 && !job && !report) {
    return (
      <div className="rounded-xl bg-muted/20 border border-dashed border-border p-6 text-center space-y-3">
        <div className="w-12 h-12 rounded-xl bg-sky-500/10 flex items-center justify-center mx-auto">
          <FileText className="w-6 h-6 text-sky-400" />
        </div>
        <div>
          <p className="text-sm font-semibold text-foreground">No evidence files yet</p>
          <p className="text-xs text-muted-foreground mt-1">
            Upload evidence documents and the AI will automatically verify them against your acceptance criteria.
          </p>
        </div>
        {onGoToAttachments && (
          <Button size="sm" variant="outline" className="gap-1.5" onClick={onGoToAttachments}>
            <ArrowRight className="w-3.5 h-3.5" /> Upload evidence files
          </Button>
        )}
      </div>
    )
  }

  return (
    <div className="space-y-4">

      {/* Header: Trigger button + version picker */}
      <div className="flex items-center justify-between gap-2 flex-wrap">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-purple-400" />
          <span className="text-xs font-bold text-muted-foreground uppercase tracking-wider">AI Evidence Check</span>
        </div>
        <div className="flex items-center gap-2">
          {/* Version picker */}
          {reportSummaries.length > 1 && (
            <div className="flex items-center gap-1.5">
              <History className="w-3.5 h-3.5 text-muted-foreground" />
              <select
                className="h-7 text-xs bg-background border border-border rounded-lg px-2 focus:outline-none focus:ring-1 focus:ring-ring"
                value={selectedReportId ?? ""}
                onChange={handleVersionChange}
                aria-label="Select report version"
              >
                <option value="">Latest (v{reportSummaries[0]?.version})</option>
                {reportSummaries.slice(1).map(s => (
                  <option key={s.id} value={s.id}>
                    v{s.version} — {formatDateShort(s.created_at)}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Re-run button */}
          <Button
            size="sm"
            variant="outline"
            className="h-7 text-xs gap-1.5"
            disabled={isJobActive || triggering || attachmentCount === 0}
            onClick={handleTrigger}
            title={attachmentCount === 0 ? "Upload evidence files first" : "Re-run evidence check"}
          >
            {triggering || isJobActive ? (
              <Loader2 className="w-3 h-3 animate-spin" />
            ) : (
              <RefreshCw className="w-3 h-3" />
            )}
            {isJobActive ? "Running…" : "Re-run"}
          </Button>
        </div>
      </div>

      {/* Trigger error */}
      {triggerError && (
        <div className="rounded-lg bg-red-500/10 border border-red-500/20 px-3 py-2 text-xs text-red-400 flex items-center justify-between">
          {triggerError}
          <button onClick={() => setTriggerError(null)} className="text-muted-foreground hover:text-foreground ml-2">×</button>
        </div>
      )}

      {/* Active job banner */}
      {job && (isJobActive || job.status_code === "failed") && (
        <JobProgressBanner job={job} />
      )}

      {/* Report loading skeleton */}
      {loadingReport && (
        <div className="space-y-2">
          {[1, 2, 3].map(i => <div key={i} className="h-14 rounded-xl bg-muted animate-pulse" />)}
        </div>
      )}

      {/* Report */}
      {!loadingReport && report && (
        <div className="space-y-3">

          {/* Overall verdict summary card */}
          {overallVm && (
            <div className={`rounded-xl border bg-gradient-to-br ${overallVm.glow} to-transparent p-4`}>
              <div className="flex items-center justify-between gap-2 flex-wrap">
                <div className="flex items-center gap-3">
                  {overallVm.icon}
                  <div>
                    <div className={`text-sm font-bold ${overallVm.badge.split(" ").find(c => c.startsWith("text-"))}`}>
                      {overallVm.label}
                    </div>
                    <div className="text-[11px] text-muted-foreground mt-0.5">
                      {metCount}/{total} criteria met
                      {report.total_pages_analyzed > 0 && ` · ${report.total_pages_analyzed} pages analyzed`}
                      {report.duration_seconds > 0 && ` · ${formatDuration(report.duration_seconds)}`}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`inline-flex items-center px-2.5 py-1 rounded-full border text-[11px] font-bold ${overallVm.badge}`}>
                    v{report.version}
                  </span>
                  {selectedReportId && (
                    <span className="text-[10px] text-amber-400 bg-amber-500/10 border border-amber-500/20 rounded-full px-2 py-0.5">
                      Historical
                    </span>
                  )}
                  {report.markdown_report_available && (
                    <Button
                      size="sm"
                      variant="outline"
                      className="h-6 gap-1 px-2 text-[10px]"
                      disabled={downloading}
                      onClick={handleDownload}
                    >
                      {downloading ? <Loader2 className="w-3 h-3 animate-spin" /> : <Download className="w-3 h-3" />}
                      Report
                    </Button>
                  )}
                </div>
              </div>

              {/* Mini scorecard */}
              {total > 0 && (
                <div className="mt-3 grid grid-cols-4 gap-2 text-center">
                  {(["MET", "PARTIALLY_MET", "NOT_MET", "INSUFFICIENT_EVIDENCE"] as CriterionVerdict[]).map(v => {
                    const count = report.criteria_results.filter(r => r.verdict === v).length
                    const vm = CRITERION_VERDICT_META[v]
                    return (
                      <div key={v} className={`rounded-lg border py-2 px-1 ${vm.bg} bg-card/50`}>
                        <div className={`text-lg font-bold ${vm.badge.split(" ").find(c => c.startsWith("text-"))}`}>{count}</div>
                        <div className="text-[9px] text-muted-foreground font-medium mt-0.5 leading-tight">{vm.label}</div>
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          )}

          {/* Criteria list */}
          {report.criteria_results.length > 0 ? (
            <div className="space-y-2">
              <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
                <BookOpen className="w-3 h-3" />
                Criteria Breakdown
              </p>
              {report.criteria_results.map((result) => (
                <CriterionCard key={result.id} result={result} />
              ))}
            </div>
          ) : (
            <div className="rounded-xl border border-dashed border-border p-4 text-center">
              <Shield className="w-6 h-6 text-muted-foreground/40 mx-auto mb-1.5" />
              <p className="text-xs text-muted-foreground">No criteria results in this report.</p>
            </div>
          )}

          {/* Report metadata footer */}
          <div className="flex items-center gap-3 pt-1 text-[10px] text-muted-foreground/60 flex-wrap">
            <span>Report v{report.version}</span>
            <span>·</span>
            <span>{report.attachment_count} attachment{report.attachment_count !== 1 ? "s" : ""}</span>
            {report.tokens_consumed > 0 && (
              <>
                <span>·</span>
                <span>{report.tokens_consumed.toLocaleString()} tokens</span>
              </>
            )}
            <span>·</span>
            <span>{formatDateShort(report.created_at)}</span>
          </div>
        </div>
      )}

      {/* No report yet + not running */}
      {!report && !loadingReport && !isJobActive && attachmentCount > 0 && (
        <div className="rounded-xl border border-dashed border-purple-500/20 bg-purple-500/5 p-5 text-center space-y-2">
          <Sparkles className="w-6 h-6 text-purple-400/60 mx-auto" />
          <p className="text-sm font-medium text-foreground">Ready to evaluate</p>
          <p className="text-xs text-muted-foreground">
            {attachmentCount} file{attachmentCount !== 1 ? "s" : ""} uploaded. Run the AI evidence check to verify your acceptance criteria.
          </p>
          <Button
            size="sm"
            className="gap-1.5 mt-1"
            disabled={triggering}
            onClick={handleTrigger}
          >
            {triggering ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
            Run Evidence Check
          </Button>
        </div>
      )}
    </div>
  )
}

export default EvidenceCheckerPanel
