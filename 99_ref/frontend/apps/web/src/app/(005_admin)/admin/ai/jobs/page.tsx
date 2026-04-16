"use client"

import { useEffect, useState, useCallback, useRef } from "react"
import {
  ListTodo, RefreshCw, Loader2, ChevronDown, ChevronUp,
  XCircle, Clock, CheckCircle, AlertTriangle, Play,
  Zap, BarChart3, Activity, Gauge, PencilLine, X, Check,
  ArrowRight, GitBranch,
} from "lucide-react"
import { Button } from "@kcontrol/ui"
import {
  adminListJobs, adminCancelJob, adminGetQueueDepth,
  type JobQueueItem, type QueueDepthItem,
} from "@/lib/api/ai"

// ── Types ──────────────────────────────────────────────────────────────────────

type StatusFilter = "all" | "queued" | "running" | "completed" | "failed"

const STATUS_META: Record<string, { label: string; color: string; bg: string; border: string; icon: React.ElementType }> = {
  queued:    { label: "Queued",    color: "text-amber-400",   bg: "bg-amber-500/10",   border: "border-amber-500/20",   icon: Clock },
  running:   { label: "Running",   color: "text-blue-400",    bg: "bg-blue-500/10",    border: "border-blue-500/20",    icon: Play },
  completed: { label: "Completed", color: "text-emerald-400", bg: "bg-emerald-500/10", border: "border-emerald-500/20", icon: CheckCircle },
  failed:    { label: "Failed",    color: "text-red-400",     bg: "bg-red-500/10",     border: "border-red-500/20",     icon: XCircle },
  cancelled: { label: "Cancelled", color: "text-slate-400",   bg: "bg-slate-500/10",   border: "border-slate-500/20",   icon: X },
}

const PRIORITY_META: Record<string, { label: string; color: string }> = {
  urgent: { label: "Urgent", color: "text-red-400" },
  high:   { label: "High",   color: "text-orange-400" },
  normal: { label: "Normal", color: "text-muted-foreground" },
  low:    { label: "Low",    color: "text-slate-400" },
}

// Signal pipeline job types in order
const PIPELINE_CHAIN = [
  { type: "signal_generate",         label: "Signal\nGenerate",        color: "text-violet-400",  bg: "bg-violet-500/10",  border: "border-violet-500/30" },
  { type: "signal_test_dataset_gen", label: "Test Dataset\nGen",       color: "text-blue-400",    bg: "bg-blue-500/10",    border: "border-blue-500/30" },
  { type: "signal_codegen",          label: "Signal\nCodegen",         color: "text-cyan-400",    bg: "bg-cyan-500/10",    border: "border-cyan-500/30" },
  { type: "threat_composer",         label: "Threat\nComposer",        color: "text-amber-400",   bg: "bg-amber-500/10",   border: "border-amber-500/30" },
  { type: "library_builder",         label: "Library\nBuilder",        color: "text-emerald-400", bg: "bg-emerald-500/10", border: "border-emerald-500/30" },
]

// ── Helper ─────────────────────────────────────────────────────────────────────

function fmtDuration(startedAt: string | null, completedAt: string | null): string {
  if (!startedAt) return "—"
  const start = new Date(startedAt).getTime()
  const end = completedAt ? new Date(completedAt).getTime() : Date.now()
  const secs = Math.round((end - start) / 1000)
  if (secs < 60) return `${secs}s`
  if (secs < 3600) return `${Math.floor(secs / 60)}m ${secs % 60}s`
  return `${Math.floor(secs / 3600)}h ${Math.floor((secs % 3600) / 60)}m`
}

function fmtTime(iso: string | null): string {
  if (!iso) return "—"
  return new Date(iso).toLocaleString(undefined, { dateStyle: "short", timeStyle: "medium" })
}

function fmtTokens(n: number | null): string {
  if (n == null) return "—"
  if (n >= 1000) return `${(n / 1000).toFixed(1)}k`
  return String(n)
}

// ── Queue Depth Cards ─────────────────────────────────────────────────────────

function QueueDepthPanel({ items, loading }: { items: QueueDepthItem[]; loading: boolean }) {
  // Aggregate by job_type
  const byType: Record<string, { queued: number; running: number; failed: number }> = {}
  for (const item of items) {
    if (!byType[item.agent_type_code]) byType[item.agent_type_code] = { queued: 0, running: 0, failed: 0 }
    const sc = item.status_code as "queued" | "running" | "failed"
    if (sc in byType[item.agent_type_code]) {
      byType[item.agent_type_code][sc] += item.job_count
    }
  }

  const totalQueued  = items.filter(i => i.status_code === "queued").reduce((s, i) => s + i.job_count, 0)
  const totalRunning = items.filter(i => i.status_code === "running").reduce((s, i) => s + i.job_count, 0)
  const totalFailed  = items.filter(i => i.status_code === "failed").reduce((s, i) => s + i.job_count, 0)

  if (loading) {
    return <div className="grid grid-cols-3 gap-3">{[1,2,3].map(i => <div key={i} className="h-16 rounded-xl bg-muted animate-pulse" />)}</div>
  }

  return (
    <div className="space-y-4">
      {/* Summary row */}
      <div className="grid grid-cols-3 gap-3">
        {[
          { label: "Queued",  value: totalQueued,  color: "border-l-amber-500",   icon: Clock },
          { label: "Running", value: totalRunning, color: "border-l-blue-500",    icon: Activity },
          { label: "Failed",  value: totalFailed,  color: "border-l-red-500",     icon: AlertTriangle },
        ].map(s => (
          <div key={s.label} className={`rounded-xl border border-l-[3px] ${s.color} bg-card px-4 py-2.5 flex items-center gap-3`}>
            <div className="rounded-lg p-1.5 bg-muted">
              <s.icon className="h-3.5 w-3.5 text-muted-foreground" />
            </div>
            <div className="flex flex-col">
              <span className="text-xl font-bold tabular-nums text-foreground leading-none">{s.value}</span>
              <span className="text-[10px] text-muted-foreground">{s.label}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Per-type breakdown */}
      {Object.keys(byType).length > 0 && (
        <div className="grid grid-cols-2 gap-2 lg:grid-cols-3">
          {Object.entries(byType).map(([type, counts]) => (
            <div key={type} className="rounded-lg border bg-card px-3 py-2 flex items-center justify-between gap-2">
              <span className="text-xs font-mono text-muted-foreground truncate flex-1">{type}</span>
              <div className="flex items-center gap-2 shrink-0">
                {counts.queued > 0  && <span className="text-[10px] font-medium text-amber-400">{counts.queued}q</span>}
                {counts.running > 0 && <span className="text-[10px] font-medium text-blue-400">{counts.running}r</span>}
                {counts.failed > 0  && <span className="text-[10px] font-medium text-red-400">{counts.failed}f</span>}
                {counts.queued === 0 && counts.running === 0 && counts.failed === 0 && (
                  <span className="text-[10px] text-muted-foreground/50">idle</span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// ── Pipeline Chain Viz ────────────────────────────────────────────────────────

function PipelineChainView({ jobs }: { jobs: JobQueueItem[] }) {
  // Count recent jobs per type (last 200)
  const counts: Record<string, { queued: number; running: number; completed: number; failed: number }> = {}
  for (const step of PIPELINE_CHAIN) {
    counts[step.type] = { queued: 0, running: 0, completed: 0, failed: 0 }
  }
  for (const job of jobs) {
    if (counts[job.job_type]) {
      const sc = job.status_code as keyof (typeof counts)[string]
      if (sc in counts[job.job_type]) counts[job.job_type][sc]++
    }
  }

  return (
    <div className="rounded-xl border bg-card px-4 py-4">
      <div className="flex items-center gap-2 mb-3">
        <GitBranch className="w-4 h-4 text-muted-foreground" />
        <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Signal Pipeline Chain</span>
      </div>
      <div className="flex items-center gap-1 flex-wrap">
        {PIPELINE_CHAIN.map((step, idx) => {
          const c = counts[step.type]
          const hasActive = c.queued > 0 || c.running > 0
          return (
            <div key={step.type} className="flex items-center gap-1">
              <div className={`rounded-lg border ${step.border} ${hasActive ? step.bg : "bg-muted/30"} px-3 py-2 text-center min-w-[80px]`}>
                <div className={`text-[10px] font-semibold ${hasActive ? step.color : "text-muted-foreground"} whitespace-pre-line leading-tight`}>
                  {step.label}
                </div>
                <div className="flex items-center justify-center gap-1.5 mt-1.5">
                  {c.running > 0  && <span className="text-[9px] text-blue-400 font-medium">{c.running}r</span>}
                  {c.queued > 0   && <span className="text-[9px] text-amber-400 font-medium">{c.queued}q</span>}
                  {c.completed > 0 && <span className="text-[9px] text-emerald-400">{c.completed}✓</span>}
                  {c.failed > 0   && <span className="text-[9px] text-red-400">{c.failed}✗</span>}
                  {c.running === 0 && c.queued === 0 && c.completed === 0 && c.failed === 0 && (
                    <span className="text-[9px] text-muted-foreground/40">—</span>
                  )}
                </div>
              </div>
              {idx < PIPELINE_CHAIN.length - 1 && (
                <ArrowRight className="w-3 h-3 text-muted-foreground/40 shrink-0" />
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

// ── Job Row ───────────────────────────────────────────────────────────────────

function JobRow({ job, onCancel }: { job: JobQueueItem; onCancel: (id: string) => Promise<void> }) {
  const [expanded, setExpanded] = useState(false)
  const [cancelling, setCancelling] = useState(false)

  const status = STATUS_META[job.status_code] ?? STATUS_META.queued
  const StatusIcon = status.icon
  const priority = PRIORITY_META[job.priority_code] ?? PRIORITY_META.normal
  const canCancel = job.status_code === "queued" || job.status_code === "running"

  const duration = fmtDuration(job.started_at, job.completed_at)
  const tokens = fmtTokens(job.actual_tokens ?? job.estimated_tokens)

  async function handleCancel(e: React.MouseEvent) {
    e.stopPropagation()
    setCancelling(true)
    try { await onCancel(job.id) } catch { /* ignore */ }
    finally { setCancelling(false) }
  }

  return (
    <div className="rounded-xl border border-border bg-card overflow-hidden">
      <div
        className="flex items-center gap-3 px-4 py-3 cursor-pointer hover:bg-muted/20 transition-colors"
        onClick={() => setExpanded(e => !e)}
      >
        {/* Status icon */}
        <StatusIcon className={`w-4 h-4 shrink-0 ${status.color}`} />

        {/* Job type */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm font-mono font-medium">{job.job_type}</span>
            <span className={`text-[10px] px-1.5 py-0.5 rounded border ${status.bg} ${status.color} ${status.border}`}>
              {status.label}
            </span>
            <span className={`text-[10px] font-medium ${priority.color}`}>
              {priority.label}
            </span>
          </div>
          <p className="text-[11px] text-muted-foreground mt-0.5 font-mono">
            {job.id.slice(0, 8)}…
            {job.user_id && ` · user ${job.user_id.slice(0, 8)}…`}
            {" · "}{fmtTime(job.created_at)}
          </p>
        </div>

        {/* Metrics */}
        <div className="hidden sm:flex items-center gap-4 shrink-0 text-[11px] text-muted-foreground">
          <div className="flex items-center gap-1">
            <Clock className="w-3 h-3" />
            <span>{duration}</span>
          </div>
          <div className="flex items-center gap-1">
            <Zap className="w-3 h-3" />
            <span>{tokens}</span>
          </div>
          {job.retry_count > 0 && (
            <span className="text-amber-400">retry {job.retry_count}/{job.max_retries}</span>
          )}
        </div>

        {/* Actions */}
        <div className="flex items-center gap-1 shrink-0 ml-2">
          {canCancel && (
            <button
              onClick={handleCancel}
              disabled={cancelling}
              className="p-1.5 rounded-lg text-muted-foreground hover:text-red-400 hover:bg-red-500/10 transition-colors"
              title="Cancel job"
            >
              {cancelling ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <XCircle className="w-3.5 h-3.5" />}
            </button>
          )}
          <button className="p-1 rounded text-muted-foreground">
            {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* Expanded detail */}
      {expanded && (
        <div className="border-t border-border bg-muted/10 px-4 py-3 space-y-3">
          {/* Timing row */}
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            {[
              { label: "Scheduled", value: fmtTime(job.scheduled_at) },
              { label: "Started",   value: fmtTime(job.started_at) },
              { label: "Completed", value: fmtTime(job.completed_at) },
              { label: "Duration",  value: duration },
            ].map(f => (
              <div key={f.label}>
                <p className="text-[10px] text-muted-foreground uppercase tracking-wide font-semibold mb-0.5">{f.label}</p>
                <p className="text-xs font-mono">{f.value}</p>
              </div>
            ))}
          </div>

          {/* IDs row */}
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
            {[
              { label: "Job ID",        value: job.id },
              { label: "Org",           value: job.org_id ?? "—" },
              { label: "Workspace",     value: job.workspace_id ?? "—" },
            ].map(f => (
              <div key={f.label}>
                <p className="text-[10px] text-muted-foreground uppercase tracking-wide font-semibold mb-0.5">{f.label}</p>
                <p className="text-xs font-mono truncate" title={f.value}>{f.value}</p>
              </div>
            ))}
          </div>

          {/* Error */}
          {job.error_message && (
            <div className="rounded-lg bg-red-500/5 border border-red-500/20 px-3 py-2">
              <p className="text-[10px] font-semibold text-red-400 uppercase tracking-wide mb-1">Error</p>
              <p className="text-xs text-red-300/80 font-mono whitespace-pre-wrap break-all">{job.error_message}</p>
            </div>
          )}

          {/* Input JSON */}
          {job.input_json && Object.keys(job.input_json).length > 0 && (
            <details className="group">
              <summary className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wide cursor-pointer hover:text-foreground select-none">
                Input JSON
              </summary>
              <div className="mt-1.5 rounded-lg bg-background border border-border p-3 overflow-x-auto">
                <pre className="text-[11px] font-mono text-muted-foreground whitespace-pre-wrap break-all">
                  {JSON.stringify(job.input_json, null, 2)}
                </pre>
              </div>
            </details>
          )}

          {/* Output JSON */}
          {job.output_json && Object.keys(job.output_json).length > 0 && (
            <details className="group">
              <summary className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wide cursor-pointer hover:text-foreground select-none">
                Output JSON
              </summary>
              <div className="mt-1.5 rounded-lg bg-background border border-border p-3 overflow-x-auto">
                <pre className="text-[11px] font-mono text-emerald-400/80 whitespace-pre-wrap break-all">
                  {JSON.stringify(job.output_json, null, 2)}
                </pre>
              </div>
            </details>
          )}
        </div>
      )}
    </div>
  )
}

// ── Main Page ─────────────────────────────────────────────────────────────────

const STATUS_TABS: { id: StatusFilter; label: string }[] = [
  { id: "all",       label: "All" },
  { id: "queued",    label: "Queued" },
  { id: "running",   label: "Running" },
  { id: "failed",    label: "Failed" },
  { id: "completed", label: "Completed" },
]

const JOB_TYPE_OPTIONS = [
  "all",
  "signal_generate",
  "signal_test_dataset_gen",
  "signal_codegen",
  "threat_composer",
  "library_builder",
  "evidence_check",
  "generate_report",
  "framework_build",
  "framework_apply_changes",
  "framework_gap_analysis",
]

export default function AIJobQueuePage() {
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all")
  const [typeFilter,   setTypeFilter]   = useState("all")
  const [jobs,         setJobs]         = useState<JobQueueItem[]>([])
  const [queueDepth,   setQueueDepth]   = useState<QueueDepthItem[]>([])
  const [loading,      setLoading]      = useState(true)
  const [depthLoading, setDepthLoading] = useState(true)
  const [autoRefresh,  setAutoRefresh]  = useState(true)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const loadJobs = useCallback(async () => {
    try {
      const params: { status_code?: string; agent_type_code?: string } = {}
      if (statusFilter !== "all") params.status_code = statusFilter
      if (typeFilter   !== "all") params.agent_type_code = typeFilter
      const res = await adminListJobs({ ...params, limit: 200 })
      setJobs(res.items ?? [])
    } catch { /* ignore */ }
    finally { setLoading(false) }
  }, [statusFilter, typeFilter])

  const loadDepth = useCallback(async () => {
    setDepthLoading(true)
    try {
      const items = await adminGetQueueDepth()
      setQueueDepth(items ?? [])
    } catch { /* ignore */ }
    finally { setDepthLoading(false) }
  }, [])

  useEffect(() => {
    setLoading(true)
    loadJobs()
    loadDepth()
  }, [loadJobs, loadDepth])

  // Auto-refresh every 5s
  useEffect(() => {
    if (!autoRefresh) { if (intervalRef.current) clearInterval(intervalRef.current); return }
    intervalRef.current = setInterval(() => { loadJobs(); loadDepth() }, 5000)
    return () => { if (intervalRef.current) clearInterval(intervalRef.current) }
  }, [autoRefresh, loadJobs, loadDepth])

  async function handleCancel(id: string) {
    await adminCancelJob(id)
    setJobs(prev => prev.map(j => j.id === id ? { ...j, status_code: "cancelled" } : j))
    loadDepth()
  }

  function handleRefresh() {
    setLoading(true)
    loadJobs()
    loadDepth()
  }

  // Per-status counts for tabs
  const statusCounts: Record<string, number> = {}
  for (const j of jobs) {
    statusCounts[j.status_code] = (statusCounts[j.status_code] ?? 0) + 1
  }

  return (
    <div className="max-w-5xl space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-blue-500/15 flex items-center justify-center">
            <ListTodo className="w-5 h-5 text-blue-400" />
          </div>
          <div>
            <h1 className="text-xl font-bold">Job Queue</h1>
            <p className="text-sm text-muted-foreground">Monitor and manage AI background jobs across all users and pipelines.</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {/* Auto-refresh toggle */}
          <button
            onClick={() => setAutoRefresh(v => !v)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-medium transition-colors ${
              autoRefresh
                ? "border-blue-500/30 bg-blue-500/10 text-blue-400"
                : "border-border text-muted-foreground hover:text-foreground"
            }`}
          >
            <Activity className={`w-3.5 h-3.5 ${autoRefresh ? "animate-pulse" : ""}`} />
            {autoRefresh ? "Live" : "Paused"}
          </button>
          <Button variant="ghost" size="sm" onClick={handleRefresh} disabled={loading} className="gap-1.5">
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Queue depth cards */}
      <QueueDepthPanel items={queueDepth} loading={depthLoading} />

      {/* Pipeline chain visualization */}
      <PipelineChainView jobs={jobs} />

      {/* Filters */}
      <div className="flex items-center gap-3 flex-wrap">
        {/* Status tabs */}
        <div className="flex gap-1 rounded-xl bg-muted/40 p-1">
          {STATUS_TABS.map(t => {
            const count = t.id === "all"
              ? jobs.length
              : (statusCounts[t.id] ?? 0)
            return (
              <button
                key={t.id}
                onClick={() => setStatusFilter(t.id)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors flex items-center gap-1.5 ${
                  statusFilter === t.id
                    ? "bg-background text-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                {t.label}
                {count > 0 && (
                  <span className={`px-1.5 py-0.5 rounded-full text-[10px] font-bold ${
                    statusFilter === t.id ? "bg-muted text-foreground" : "text-muted-foreground/60"
                  }`}>
                    {count}
                  </span>
                )}
              </button>
            )
          })}
        </div>

        {/* Type filter */}
        <select
          value={typeFilter}
          onChange={e => setTypeFilter(e.target.value)}
          className="h-8 rounded-lg border border-input bg-background text-xs px-3 pr-8 focus:outline-none focus:ring-2 focus:ring-ring"
        >
          {JOB_TYPE_OPTIONS.map(t => (
            <option key={t} value={t}>{t === "all" ? "All job types" : t}</option>
          ))}
        </select>
      </div>

      {/* Job list */}
      {loading ? (
        <div className="space-y-3">
          {[1,2,3,4].map(i => <div key={i} className="h-16 rounded-xl bg-muted animate-pulse" />)}
        </div>
      ) : jobs.length === 0 ? (
        <div className="flex flex-col items-center py-20 gap-3 text-center">
          <div className="w-14 h-14 rounded-2xl bg-muted flex items-center justify-center">
            <ListTodo className="w-7 h-7 text-muted-foreground/30" />
          </div>
          <div>
            <p className="text-sm font-medium text-muted-foreground">No jobs found</p>
            <p className="text-xs text-muted-foreground/60 mt-0.5">
              {statusFilter !== "all" || typeFilter !== "all" ? "Try adjusting your filters." : "The queue is empty."}
            </p>
          </div>
        </div>
      ) : (
        <div className="space-y-2">
          {jobs.map(job => (
            <JobRow key={job.id} job={job} onCancel={handleCancel} />
          ))}
          <p className="text-[11px] text-muted-foreground text-center pt-1">
            Showing {jobs.length} jobs · auto-refresh {autoRefresh ? "every 5s" : "paused"}
          </p>
        </div>
      )}
    </div>
  )
}
