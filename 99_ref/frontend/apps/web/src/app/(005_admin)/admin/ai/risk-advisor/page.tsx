"use client"

import { useEffect, useState, useCallback, useRef } from "react"
import {
  GitMerge, Play, Loader2, CheckCircle, XCircle, Clock,
  RefreshCw, AlertTriangle, Info,
} from "lucide-react"
import { Card, CardContent, Button } from "@kcontrol/ui"
import { listFrameworks } from "@/lib/api/grc"
import { listOrgs } from "@/lib/api/orgs"
import { listWorkspaces } from "@/lib/api/workspaces"
import { enqueueBulkLink, getRiskAdvisorJobStatus } from "@/lib/api/riskAdvisor"
import type { FrameworkResponse } from "@/lib/types/grc"
import type { OrgResponse, WorkspaceResponse } from "@/lib/types/orgs"
import type { BulkLinkJobResponse, JobStatusResponse } from "@/lib/api/riskAdvisor"

// ── Status helpers ─────────────────────────────────────────────────────────────

const STATUS_META: Record<string, { label: string; color: string; icon: React.ElementType }> = {
  queued:    { label: "Queued",    color: "text-amber-400",   icon: Clock },
  running:   { label: "Running",   color: "text-blue-400",    icon: Loader2 },
  completed: { label: "Completed", color: "text-green-400",   icon: CheckCircle },
  failed:    { label: "Failed",    color: "text-red-400",     icon: XCircle },
  cancelled: { label: "Cancelled", color: "text-muted-foreground", icon: XCircle },
}

// ── Job Status Card ───────────────────────────────────────────────────────────

function JobStatusCard({ job, onRefresh }: { job: JobStatusResponse; onRefresh: () => void }) {
  const meta = STATUS_META[job.status_code] ?? { label: job.status_code, color: "text-muted-foreground", icon: Info }
  const Icon = meta.icon
  const isActive = job.status_code === "running" || job.status_code === "queued"

  const output = job.output_json as {
    total_risks?: number
    total_controls?: number
    mappings_created?: number
    mappings_skipped?: number
    dry_run?: boolean
  } | null

  return (
    <Card className="border-border/60">
      <CardContent className="p-4 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Icon className={`w-4 h-4 ${meta.color} ${isActive ? "animate-spin" : ""}`} />
            <span className={`text-sm font-medium ${meta.color}`}>{meta.label}</span>
          </div>
          <button onClick={onRefresh} className="text-muted-foreground hover:text-foreground transition-colors">
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>

        {job.progress_pct !== null && isActive && (
          <div className="space-y-1">
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>Progress</span>
              <span>{job.progress_pct}%</span>
            </div>
            <div className="w-full bg-muted/50 rounded-full h-1.5">
              <div className="bg-primary h-1.5 rounded-full transition-all" style={{ width: `${job.progress_pct}%` }} />
            </div>
          </div>
        )}

        {output && job.status_code === "completed" && (
          <div className="grid grid-cols-2 gap-2 text-xs">
            {output.dry_run && (
              <div className="col-span-2 text-amber-400 bg-amber-500/10 rounded px-2 py-1 text-center">
                Dry run — no changes were made
              </div>
            )}
            {([
              { label: "Risks evaluated",  value: output.total_risks },
              { label: "Controls checked", value: output.total_controls },
              { label: "Mappings created", value: output.mappings_created },
              { label: "Already linked",   value: output.mappings_skipped },
            ] as const).map(({ label, value }) => value !== undefined && (
              <div key={label} className="bg-muted/30 rounded p-2">
                <p className="text-muted-foreground">{label}</p>
                <p className="font-semibold text-sm">{value}</p>
              </div>
            ))}
          </div>
        )}

        {job.error_message && (
          <p className="text-xs text-red-400 bg-red-500/10 rounded px-3 py-2">{job.error_message}</p>
        )}

        <p className="text-[10px] text-muted-foreground font-mono">
          Job {job.job_id.slice(0, 8)}… · {new Date(job.created_at).toLocaleString()}
        </p>
      </CardContent>
    </Card>
  )
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function RiskAdvisorAdminPage() {
  const [orgs, setOrgs] = useState<OrgResponse[]>([])
  const [workspaces, setWorkspaces] = useState<WorkspaceResponse[]>([])
  const [frameworks, setFrameworks] = useState<FrameworkResponse[]>([])

  const [selectedOrgId, setSelectedOrgId] = useState("")
  const [selectedWorkspaceId, setSelectedWorkspaceId] = useState("")
  const [selectedFrameworkId, setSelectedFrameworkId] = useState("")
  const [dryRun, setDryRun] = useState(false)
  const [priority, setPriority] = useState("normal")

  const [loadingOrgs, setLoadingOrgs] = useState(true)
  const [loadingWs, setLoadingWs] = useState(false)
  const [loadingFw, setLoadingFw] = useState(false)

  const [submitting, setSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [jobs, setJobs] = useState<JobStatusResponse[]>([])
  const [activeJobId, setActiveJobId] = useState<string | null>(null)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // Load orgs on mount
  useEffect(() => {
    listOrgs()
      .then(data => setOrgs(data))
      .catch(() => {})
      .finally(() => setLoadingOrgs(false))
  }, [])

  // Load workspaces when org changes
  useEffect(() => {
    if (!selectedOrgId) { setWorkspaces([]); setSelectedWorkspaceId(""); return }
    setLoadingWs(true)
    setSelectedWorkspaceId("")
    setSelectedFrameworkId("")
    listWorkspaces(selectedOrgId)
      .then(data => setWorkspaces(data))
      .catch(() => {})
      .finally(() => setLoadingWs(false))
  }, [selectedOrgId])

  // Load frameworks when org changes
  useEffect(() => {
    if (!selectedOrgId) { setFrameworks([]); return }
    setLoadingFw(true)
    setSelectedFrameworkId("")
    listFrameworks({ deployed_org_id: selectedOrgId })
      .then(res => setFrameworks(res.items ?? []))
      .catch(() => {})
      .finally(() => setLoadingFw(false))
  }, [selectedOrgId])

  // Poll active job
  const refreshJob = useCallback(async (jobId: string) => {
    try {
      const status = await getRiskAdvisorJobStatus(jobId)
      setJobs(prev => {
        const idx = prev.findIndex(j => j.job_id === jobId)
        if (idx >= 0) { const next = [...prev]; next[idx] = status; return next }
        return [status, ...prev]
      })
      if (["completed", "failed", "cancelled"].includes(status.status_code)) setActiveJobId(null)
    } catch { /* ignore */ }
  }, [])

  useEffect(() => {
    if (!activeJobId) { if (pollRef.current) clearInterval(pollRef.current); return }
    pollRef.current = setInterval(() => refreshJob(activeJobId), 3000)
    return () => { if (pollRef.current) clearInterval(pollRef.current) }
  }, [activeJobId, refreshJob])

  const handleSubmit = useCallback(async () => {
    if (!selectedFrameworkId || !selectedOrgId || !selectedWorkspaceId) return
    setSubmitting(true)
    setSubmitError(null)
    try {
      const res: BulkLinkJobResponse = await enqueueBulkLink({
        framework_id: selectedFrameworkId,
        org_id: selectedOrgId,
        workspace_id: selectedWorkspaceId,
        priority_code: priority,
        dry_run: dryRun,
      })
      setJobs(prev => [{
        job_id: res.job_id,
        status_code: res.status,
        job_type: "risk_advisor_bulk_link",
        progress_pct: 0,
        output_json: null,
        error_message: null,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }, ...prev])
      setActiveJobId(res.job_id)
    } catch (e) {
      setSubmitError(e instanceof Error ? e.message : "Failed to enqueue job")
    } finally {
      setSubmitting(false)
    }
  }, [selectedFrameworkId, selectedOrgId, selectedWorkspaceId, priority, dryRun])

  const canSubmit = !!(selectedFrameworkId && selectedOrgId && selectedWorkspaceId && !submitting)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start gap-3">
        <div className="p-2 rounded-lg bg-primary/10">
          <GitMerge className="w-5 h-5 text-primary" />
        </div>
        <div>
          <h1 className="text-xl font-semibold">Risk Advisor — Bulk Auto-Link</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            Automatically map all controls in a framework to matching risks using AI. Runs as a background job.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Config panel */}
        <Card className="border-border/60">
          <CardContent className="p-5 space-y-4">
            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Configuration</p>

            {/* Organisation */}
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-muted-foreground">Organisation</label>
              {loadingOrgs ? (
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <Loader2 className="w-3 h-3 animate-spin" /> Loading…
                </div>
              ) : (
                <select
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary"
                  value={selectedOrgId}
                  onChange={e => setSelectedOrgId(e.target.value)}
                >
                  <option value="">Select an organisation…</option>
                  {orgs.map(o => <option key={o.id} value={o.id}>{o.name}</option>)}
                </select>
              )}
            </div>

            {/* Workspace */}
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-muted-foreground">Workspace</label>
              {loadingWs ? (
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <Loader2 className="w-3 h-3 animate-spin" /> Loading…
                </div>
              ) : (
                <select
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary"
                  value={selectedWorkspaceId}
                  onChange={e => setSelectedWorkspaceId(e.target.value)}
                  disabled={!selectedOrgId}
                >
                  <option value="">Select a workspace…</option>
                  {workspaces.map(w => <option key={w.id} value={w.id}>{w.name}</option>)}
                </select>
              )}
            </div>

            {/* Framework */}
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-muted-foreground">Framework</label>
              {loadingFw ? (
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <Loader2 className="w-3 h-3 animate-spin" /> Loading…
                </div>
              ) : (
                <select
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary"
                  value={selectedFrameworkId}
                  onChange={e => setSelectedFrameworkId(e.target.value)}
                  disabled={!selectedOrgId}
                >
                  <option value="">Select a framework…</option>
                  {frameworks.map(f => (
                    <option key={f.id} value={f.id}>
                      {f.framework_code} — {f.name} ({f.control_count} controls)
                    </option>
                  ))}
                </select>
              )}
              {selectedOrgId && !loadingFw && frameworks.length === 0 && (
                <p className="text-xs text-muted-foreground flex items-center gap-1">
                  <AlertTriangle className="w-3 h-3" /> No frameworks deployed to this organisation.
                </p>
              )}
            </div>

            {/* Priority */}
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-muted-foreground">Priority</label>
              <select
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary"
                value={priority}
                onChange={e => setPriority(e.target.value)}
              >
                <option value="low">Low</option>
                <option value="normal">Normal</option>
                <option value="high">High</option>
                <option value="urgent">Urgent</option>
              </select>
            </div>

            {/* Dry run toggle */}
            <label className="flex items-center gap-3 cursor-pointer select-none">
              <div
                role="checkbox"
                aria-checked={dryRun}
                onClick={() => setDryRun(v => !v)}
                className={`relative w-9 h-5 rounded-full transition-colors cursor-pointer ${dryRun ? "bg-primary" : "bg-muted"}`}
              >
                <span className={`absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform ${dryRun ? "translate-x-4" : ""}`} />
              </div>
              <div>
                <p className="text-sm font-medium">Dry run</p>
                <p className="text-xs text-muted-foreground">Preview what would be linked without creating mappings</p>
              </div>
            </label>

            {/* How it works */}
            <div className="p-3 bg-blue-500/5 border border-blue-500/20 rounded-lg text-xs text-muted-foreground space-y-1">
              <p className="font-medium text-blue-400">How it works</p>
              <ul className="space-y-0.5 list-disc list-inside">
                <li>Fetches all controls in the selected framework</li>
                <li>For each control, AI evaluates relevance to all risks</li>
                <li>Links are created where confidence ≥ 70%</li>
                <li>Already-linked pairs are skipped (no duplicates)</li>
              </ul>
            </div>

            {submitError && (
              <p className="text-xs text-red-400 bg-red-500/10 rounded px-3 py-2">{submitError}</p>
            )}

            <Button className="w-full gap-2" disabled={!canSubmit} onClick={handleSubmit}>
              {submitting
                ? <><Loader2 className="w-4 h-4 animate-spin" /> Enqueueing…</>
                : <><Play className="w-4 h-4" /> {dryRun ? "Run Dry-Run" : "Start Bulk Link"}</>
              }
            </Button>
          </CardContent>
        </Card>

        {/* Job history */}
        <div className="space-y-3">
          <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide px-1">Job History</p>
          {jobs.length === 0 ? (
            <Card className="border-border/40">
              <CardContent className="p-8 text-center">
                <GitMerge className="w-8 h-8 text-muted-foreground/30 mx-auto mb-2" />
                <p className="text-sm text-muted-foreground">No jobs yet. Run a bulk link to get started.</p>
              </CardContent>
            </Card>
          ) : jobs.map(job => (
            <JobStatusCard key={job.job_id} job={job} onRefresh={() => refreshJob(job.job_id)} />
          ))}
        </div>
      </div>
    </div>
  )
}
