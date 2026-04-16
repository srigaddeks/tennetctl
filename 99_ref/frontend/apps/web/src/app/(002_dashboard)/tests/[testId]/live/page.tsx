"use client"

import { useEffect, useState, useCallback, useRef } from "react"
import { useParams, useRouter } from "next/navigation"
import { Button, Badge, Tooltip, TooltipProvider, TooltipTrigger, TooltipContent } from "@kcontrol/ui"
import {
  ArrowLeft,
  Activity,
  Play,
  Square,
  Pause,
  RotateCcw,
  RefreshCw,
  AlertTriangle,
  Link2Off,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Zap,
  Clock,
  Database,
  Code2,
  ExternalLink,
  Github,
  Cloud,
  Server,
  ArrowRight,
  Wifi,
  WifiOff,
  Calendar,
  Gauge,
  FileText,
  Sparkles,
  ChevronDown,
  ChevronUp,
  TrendingUp,
  TrendingDown,
  Minus,
  CirclePlus,
  Eye,
  Shield,
  Lightbulb,
  ArrowUpRight,
  Layers,
  ListChecks,
  BookOpen,
} from "lucide-react"
import { useOrgWorkspace } from "@/lib/context/OrgWorkspaceContext"
import { getPromotedTest, listPromotedTests, getTest } from "@/lib/api/grc"
import {
  listLiveSessions,
  startLiveSession,
  stopSession,
  pauseSession,
  resumeSession,
  listRuns,
  triggerCollection,
} from "@/lib/api/sandbox"
import type { PromotedTestResponse, TestResponse } from "@/lib/types/grc"
import type { LiveSessionResponse, RunResponse } from "@/lib/api/sandbox"

// ── Connector helpers ─────────────────────────────────────────────────────────

function ConnectorIcon({ typeCode, className = "h-5 w-5" }: { typeCode: string | null; className?: string }) {
  if (!typeCode) return <Server className={className} />
  if (typeCode.startsWith("github")) return <Github className={className} />
  if (typeCode.startsWith("azure")) return <Cloud className={className} />
  return <Server className={className} />
}

function connectorTypeLabel(code: string | null): string {
  if (!code) return "Unknown"
  const map: Record<string, string> = {
    github: "GitHub",
    azure_storage: "Azure Storage",
    azure: "Azure",
    aws: "AWS",
  }
  return map[code] ?? code.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())
}

function connectorBg(typeCode: string | null): string {
  if (!typeCode) return "from-slate-800 to-slate-700"
  if (typeCode.startsWith("github")) return "from-neutral-950 to-neutral-800"
  if (typeCode.startsWith("azure")) return "from-blue-700 to-blue-600"
  return "from-slate-800 to-slate-700"
}

// ── Helpers ──────────────────────────────────────────────────────────────────

function formatRelative(dateStr: string | null): string {
  if (!dateStr) return "—"
  const diff = Date.now() - new Date(dateStr).getTime()
  const sec = Math.floor(diff / 1000)
  if (sec < 60) return `${sec}s ago`
  const min = Math.floor(sec / 60)
  if (min < 60) return `${min}m ago`
  const hr = Math.floor(min / 60)
  if (hr < 24) return `${hr}h ago`
  return new Date(dateStr).toLocaleDateString()
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return "—"
  return new Date(dateStr).toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  })
}

function formatFrequency(freq: string): string {
  const map: Record<string, string> = {
    manual: "On-Demand",
    hourly: "Hourly",
    daily: "Daily",
    weekly: "Weekly",
  }
  return map[freq] || freq.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())
}

// ── Session status ────────────────────────────────────────────────────────────

type SessionStatus = "active" | "starting" | "paused" | "stopped" | "failed" | "none"

function sessionStatusConfig(status: SessionStatus) {
  switch (status) {
    case "active":
      return { bg: "bg-emerald-500/10", text: "text-emerald-600", dot: "bg-emerald-500", label: "Active" }
    case "starting":
      return { bg: "bg-amber-500/10", text: "text-amber-600", dot: "bg-amber-500 animate-pulse", label: "Starting" }
    case "paused":
      return { bg: "bg-orange-500/10", text: "text-orange-600", dot: "bg-orange-500", label: "Paused" }
    case "stopped":
    case "failed":
      return { bg: "bg-red-500/10", text: "text-red-600", dot: "bg-red-500", label: "Stopped" }
    default:
      return { bg: "bg-muted", text: "text-muted-foreground", dot: "bg-slate-400", label: "No Session" }
  }
}

// ── Run result ────────────────────────────────────────────────────────────────

function RunResultBadge({ result }: { result: string | null }) {
  if (!result) return <Badge variant="secondary">—</Badge>
  switch (result.toLowerCase()) {
    case "pass":
      return (
        <span className="inline-flex items-center gap-1 text-xs font-medium text-emerald-700 bg-emerald-500/10 border border-emerald-500/20 rounded-full px-2 py-0.5">
          <CheckCircle2 className="h-3 w-3" /> PASS
        </span>
      )
    case "fail":
      return (
        <span className="inline-flex items-center gap-1 text-xs font-medium text-red-700 bg-red-500/10 border border-red-500/20 rounded-full px-2 py-0.5">
          <XCircle className="h-3 w-3" /> FAIL
        </span>
      )
    case "warning":
      return (
        <span className="inline-flex items-center gap-1 text-xs font-medium text-amber-700 bg-amber-500/10 border border-amber-500/20 rounded-full px-2 py-0.5">
          <AlertCircle className="h-3 w-3" /> WARN
        </span>
      )
    default:
      return (
        <span className="inline-flex items-center gap-1 text-xs font-medium text-red-700 bg-red-500/10 border border-red-500/20 rounded-full px-2 py-0.5">
          <XCircle className="h-3 w-3" /> ERROR
        </span>
      )
  }
}

// ── Skeleton ──────────────────────────────────────────────────────────────────

function Skeleton({ className }: { className?: string }) {
  return <div className={`animate-pulse rounded bg-muted ${className ?? ""}`} />
}

// ── Trend Sparkline ───────────────────────────────────────────────────────────

function TrendSparkline({ runs }: { runs: Array<{ result_code: string | null }> }) {
  if (runs.length < 2) return null

  // Take the most recent runs (reversed so left = oldest, right = newest)
  const recentRuns = runs.slice(0, 10).reverse()
  const barW = 6
  const gap = 3
  const height = 28
  const totalW = recentRuns.length * (barW + gap) - gap

  // Compute trend
  const recentFailRate = runs.slice(0, 3).filter(r => r.result_code === "fail").length / Math.min(3, runs.length)
  const olderFailRate = runs.slice(3, 6).filter(r => r.result_code === "fail").length / Math.max(1, Math.min(3, runs.length - 3))
  const improving = recentFailRate < olderFailRate
  const degrading = recentFailRate > olderFailRate

  const TrendIcon = improving ? TrendingUp : degrading ? TrendingDown : Minus
  const trendColor = improving ? "text-emerald-500" : degrading ? "text-red-500" : "text-muted-foreground"
  const trendLabel = improving ? "Improving" : degrading ? "Needs attention" : "Stable"

  return (
    <div className="flex items-center gap-3">
      <Tooltip>
        <TooltipTrigger asChild>
          <div className="flex items-center gap-2 cursor-help">
            <svg width={totalW} height={height} className="shrink-0">
              {recentRuns.map((run, i) => {
                const isPassing = run.result_code === "pass"
                return (
                  <rect
                    key={i}
                    x={i * (barW + gap)}
                    y={isPassing ? 2 : 0}
                    width={barW}
                    height={isPassing ? height - 4 : height}
                    rx={2}
                    className={isPassing
                      ? "fill-emerald-500/60"
                      : run.result_code === "fail" ? "fill-red-500/70" : "fill-amber-500/50"
                    }
                  />
                )
              })}
            </svg>
            <div className={`flex items-center gap-1 ${trendColor}`}>
              <TrendIcon className="h-3.5 w-3.5" />
              <span className="text-[10px] font-bold uppercase tracking-wider">{trendLabel}</span>
            </div>
          </div>
        </TooltipTrigger>
        <TooltipContent side="bottom" className="text-xs bg-zinc-900 text-slate-100 border-none max-w-[240px]">
          Pass/fail trend across last {recentRuns.length} runs. Green bars = pass, Red bars = fail.
        </TooltipContent>
      </Tooltip>
    </div>
  )
}

// ── Run Health Banner ─────────────────────────────────────────────────────────

function RunHealthBanner({ runs, testName }: { runs: Array<{ result_code: string | null; result_details: unknown | null; completed_at: string | null }>; testName: string }) {
  if (runs.length === 0) return null

  const latestRun = runs[0]
  const latestDetails = (Array.isArray(latestRun?.result_details) ? latestRun.result_details : []) as Array<{
    result?: string; asset_external_id?: string; asset_id?: string
  }>
  const failedCount = latestDetails.filter(d => d.result === "fail").length
  const passedCount = latestDetails.filter(d => d.result === "pass").length
  const totalAssets = latestDetails.length
  const isAllPassing = failedCount === 0 && passedCount > 0
  const hasFailures = failedCount > 0

  // Count consecutive passes
  let consecutivePasses = 0
  for (const run of runs) {
    if (run.result_code === "pass") consecutivePasses++
    else break
  }

  if (isAllPassing) {
    return (
      <div className="rounded-xl border border-emerald-500/20 bg-gradient-to-r from-emerald-500/5 via-emerald-500/[0.02] to-transparent px-5 py-4">
        <div className="flex items-start gap-4">
          <div className="h-10 w-10 rounded-xl bg-emerald-500/10 flex items-center justify-center shrink-0 border border-emerald-500/20">
            <CheckCircle2 className="h-5 w-5 text-emerald-500" />
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="text-sm font-bold text-emerald-700 dark:text-emerald-400">All {totalAssets} assets passing</h3>
            <p className="text-xs text-muted-foreground mt-0.5 leading-relaxed">
              {consecutivePasses > 1
                ? `${consecutivePasses} consecutive passing runs — your controls are holding steady.`
                : "Latest run shows full compliance across all checked assets."}
            </p>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <Tooltip>
              <TooltipTrigger asChild>
                <a
                  href="/monitoring"
                  className="inline-flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider text-emerald-600 dark:text-emerald-400 hover:text-emerald-500 transition-colors cursor-pointer"
                >
                  <Eye className="h-3.5 w-3.5" /> Live Monitor <ArrowUpRight className="h-3 w-3" />
                </a>
              </TooltipTrigger>
              <TooltipContent side="left" className="text-xs bg-zinc-900 text-slate-100 border-none">
                View all test signals in real-time
              </TooltipContent>
            </Tooltip>
          </div>
        </div>
      </div>
    )
  }

  if (hasFailures) {
    const failedAssetNames = latestDetails
      .filter(d => d.result === "fail")
      .slice(0, 3)
      .map(d => (d.asset_external_id || d.asset_id || "").split("/").pop())
      .filter(Boolean)

    return (
      <div className="rounded-xl border border-red-500/20 bg-gradient-to-r from-red-500/5 via-red-500/[0.02] to-transparent px-5 py-4">
        <div className="flex items-start gap-4">
          <div className="h-10 w-10 rounded-xl bg-red-500/10 flex items-center justify-center shrink-0 border border-red-500/20 shadow-[0_0_12px_rgba(239,68,68,0.1)]">
            <AlertTriangle className="h-5 w-5 text-red-500" />
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="text-sm font-bold text-red-700 dark:text-red-400">
              {failedCount} asset{failedCount !== 1 ? "s" : ""} need attention
            </h3>
            <p className="text-xs text-muted-foreground mt-0.5 leading-relaxed">
              {failedAssetNames.length > 0 && (
                <span className="text-red-600/70 dark:text-red-400/70 font-medium">
                  {failedAssetNames.join(", ")}{failedCount > 3 ? ` +${failedCount - 3} more` : ""}
                </span>
              )}
              {" "}— expand the latest run below to see details and take action.
            </p>
            <div className="flex items-center gap-3 mt-3">
              <Tooltip>
                <TooltipTrigger asChild>
                  <a
                    href={`/issues?search=${encodeURIComponent(testName)}`}
                    className="inline-flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider text-red-600 dark:text-red-400 bg-red-500/10 hover:bg-red-500/15 px-3 py-1.5 rounded-lg border border-red-500/20 transition-colors cursor-pointer"
                  >
                    <ListChecks className="h-3.5 w-3.5" /> View Issues
                  </a>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="text-xs bg-zinc-900 text-slate-100 border-none max-w-[220px]">
                  View and manage tracked findings for this failed control test
                </TooltipContent>
              </Tooltip>
              <Tooltip>
                <TooltipTrigger asChild>
                  <a
                    href="/monitoring"
                    className="inline-flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider text-muted-foreground hover:text-foreground px-3 py-1.5 rounded-lg border border-border hover:border-primary/30 transition-colors cursor-pointer"
                  >
                    <Eye className="h-3.5 w-3.5" /> View Monitor
                  </a>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="text-xs bg-zinc-900 text-slate-100 border-none">
                  View this test's signals in the live monitoring dashboard
                </TooltipContent>
              </Tooltip>
              <Tooltip>
                <TooltipTrigger asChild>
                  <a
                    href="/risk-registry"
                    className="inline-flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider text-muted-foreground hover:text-foreground px-3 py-1.5 rounded-lg border border-border hover:border-primary/30 transition-colors cursor-pointer"
                  >
                    <Shield className="h-3.5 w-3.5" /> Risk Registry
                  </a>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="text-xs bg-zinc-900 text-slate-100 border-none max-w-[220px]">
                  Check if this failure is linked to any registered risks in the risk registry
                </TooltipContent>
              </Tooltip>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return null
}

// ── Page ─────────────────────────────────────────────────────────────────────

export default function LiveControlTestPage() {
  const { testId } = useParams<{ testId: string }>()
  const router = useRouter()
  const { selectedOrgId, selectedWorkspaceId } = useOrgWorkspace()

  const [test, setTest] = useState<PromotedTestResponse | TestResponse | null>(null)
  const isPromoted = !!(test && ("promoted_at" in test || "linked_asset_id" in test && test.linked_asset_id))
  
  // Safe field access for TS
  const linkedAssetId = test && "linked_asset_id" in test ? test.linked_asset_id : null
  const sourceSignalId = test && "source_signal_id" in test ? test.source_signal_id : null
  
  const [testLoading, setTestLoading] = useState(true)
  const [testError, setTestError] = useState<string | null>(null)

  const [sessions, setSessions] = useState<LiveSessionResponse[]>([])
  const [sessionsLoading, setSessionsLoading] = useState(false)

  const [runs, setRuns] = useState<RunResponse[]>([])
  const [runsLoading, setRunsLoading] = useState(false)

  const [actionLoading, setActionLoading] = useState(false)
  const [actionError, setActionError] = useState<string | null>(null)
  const [expandedRunId, setExpandedRunId] = useState<string | null>(null)
  const [showEvaluationRule, setShowEvaluationRule] = useState(false)

  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // Load test
  useEffect(() => {
    if (!testId) return
    setTestLoading(true)
    setTestError(null)
    
    const loadTest = async () => {
      try {
        const pTest = await getPromotedTest(testId)
        setTest(pTest)
      } catch (e: any) {
        // Fallback: If 404, check if it's a standard test ID or a mapped ID
        if (e.message?.toLowerCase().includes("not found") || e.status === 404) {
          try {
            // Attempt 1: Look for a mapping in the promoted tests list
            if (selectedOrgId) {
              const res = await listPromotedTests({ 
                orgId: selectedOrgId, 
                limit: 500 
              })
              const found = res.items.find(t => t.control_test_id === testId || t.test_code === testId || t.id === testId)
              if (found) {
                setTest(found)
                return
              }
            }
            
            // Attempt 2: Fetch as a standard test (non-promoted)
            const sTest = await getTest(testId)
            setTest(sTest)
            return
          } catch (err) {
            console.error("Fallback search failed:", err)
          }
        }
        setTestError(e instanceof Error ? e.message : "Failed to load test")
      } finally {
        setTestLoading(false)
      }
    }
    
    loadTest()
  }, [testId, selectedOrgId])

  // Load sessions
  const loadSessions = useCallback(async () => {
    if (!linkedAssetId) return
    setSessionsLoading(true)
    try {
      const res = await listLiveSessions({ org_id: selectedOrgId ?? undefined, connector_instance_id: linkedAssetId })
      setSessions(res.items)
    } catch {
      // silently fail
    } finally {
      setSessionsLoading(false)
    }
  }, [linkedAssetId, selectedOrgId])

  // Load runs
  const loadRuns = useCallback(async () => {
    if (!test) return
    setRunsLoading(true)
    try {
      const res = await listRuns({
        org_id: selectedOrgId ?? undefined,
        signal_id: sourceSignalId ?? undefined,
        limit: 20,
      })
      setRuns(res.items)
    } catch {
      setRuns([])
    } finally {
      setRunsLoading(false)
    }
  }, [test, sourceSignalId, selectedOrgId])

  useEffect(() => {
    if (test) {
      loadSessions()
      loadRuns()
    }
  }, [test, loadSessions, loadRuns])

  // Polling
  useEffect(() => {
    if (!linkedAssetId) return
    pollRef.current = setInterval(() => { loadSessions() }, 30_000)
    return () => { if (pollRef.current) clearInterval(pollRef.current) }
  }, [linkedAssetId, loadSessions])

  // Derived
  const activeSession = sessions.find((s) => ["active", "starting", "paused"].includes(s.session_status)) ?? null
  const sessionStatus: SessionStatus = activeSession ? (activeSession.session_status as SessionStatus) : "none"
  const statusConfig = sessionStatusConfig(sessionStatus)

  // Actions
  async function handleStartSession() {
    if (!linkedAssetId || !selectedWorkspaceId) return
    setActionLoading(true); setActionError(null)
    try {
      await startLiveSession({ 
        org_id: selectedOrgId, 
        connector_instance_id: linkedAssetId, 
        workspace_id: selectedWorkspaceId, 
        signal_ids: sourceSignalId ? [sourceSignalId] : undefined 
      })
      await loadSessions()
    } catch (e) { setActionError(e instanceof Error ? e.message : "Failed to start session") }
    finally { setActionLoading(false) }
  }

  async function handlePauseSession() {
    if (!activeSession) return
    setActionLoading(true); setActionError(null)
    try { await pauseSession(selectedOrgId, activeSession.id); await loadSessions() }
    catch (e) { setActionError(e instanceof Error ? e.message : "Failed to pause session") }
    finally { setActionLoading(false) }
  }

  async function handleResumeSession() {
    if (!activeSession) return
    setActionLoading(true); setActionError(null)
    try { await resumeSession(selectedOrgId, activeSession.id); await loadSessions() }
    catch (e) { setActionError(e instanceof Error ? e.message : "Failed to resume session") }
    finally { setActionLoading(false) }
  }

  async function handleStopSession() {
    if (!activeSession) return
    setActionLoading(true); setActionError(null)
    try { await stopSession(selectedOrgId, activeSession.id); await loadSessions() }
    catch (e) { setActionError(e instanceof Error ? e.message : "Failed to stop session") }
    finally { setActionLoading(false) }
  }

  async function handleRunNow() {
    const orgId = selectedOrgId ?? (test && "org_id" in test ? test.org_id : null)
    if (!linkedAssetId || !orgId) return
    setActionLoading(true); setActionError(null)
    try {
      await triggerCollection(orgId, linkedAssetId)
      let attempts = 0
      const poll = setInterval(async () => {
        attempts++
        await loadRuns()
        if (attempts >= 12) clearInterval(poll)
      }, 5000)
    } catch (e) { setActionError(e instanceof Error ? e.message : "Failed to trigger collection run") }
    finally { setActionLoading(false) }
  }

  // Render
  return (
    <TooltipProvider delayDuration={0}>
      <div className="flex flex-col min-h-full">

        {/* Top Bar */}
        <div className="px-6 py-3 flex items-center">
          <Button variant="ghost" size="sm" onClick={() => router.push("/tests")} className="h-9">
            <ArrowLeft className="h-4 w-4 mr-1.5" />
            Back
          </Button>
        </div>

        <main className="flex-1 max-w-full mx-auto w-full px-6 py-6 space-y-6">

          {/* Loading */}
          {testLoading && (
            <div className="space-y-4">
              <div className="flex items-center gap-4">
                <Skeleton className="h-10 w-10 rounded-lg" />
                <Skeleton className="h-6 w-64" />
              </div>
              <Skeleton className="h-24 rounded-xl" />
              <Skeleton className="h-48 rounded-xl" />
            </div>
          )}

          {/* Error */}
          {testError && (
            <div className="flex items-center gap-2 text-sm text-destructive bg-destructive/5 rounded-lg px-4 py-3">
              <AlertTriangle className="h-4 w-4" />
              {testError}
            </div>
          )}

          {test && (
            <div className="space-y-6">
              
              {!isPromoted && (
                <div className="flex items-center gap-4 rounded-2xl border border-amber-500/20 bg-amber-500/5 px-6 py-5 shadow-sm">
                  <div className="h-10 w-10 rounded-full bg-amber-500/10 flex items-center justify-center shrink-0">
                    <Shield className="h-5 w-5 text-amber-500" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-amber-900 dark:text-amber-400 leading-none mb-1">Standard Test Definition</h3>
                    <p className="text-xs text-amber-700/80 dark:text-amber-500/80">
                      This test is not currently promoted to live monitoring. To enable automated runs and session collection, 
                      promote this test from the Sandbox.
                    </p>
                  </div>
                  <Button variant="outline" size="sm" className="ml-auto border-amber-500/30 text-amber-600 hover:bg-amber-500/10" asChild>
                    <a href="/sandbox/signals">
                      Go to Sandbox
                    </a>
                  </Button>
                </div>
              )}

              {/* Test Identity */}
              <div className="border-b border-border pb-5">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <div className="flex items-center gap-2.5 flex-wrap">
                      <h1 className="text-xl font-bold tracking-tight">{test.name || test.test_code}</h1>
                      {test.id && (
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <span className="text-[11px] font-mono bg-muted text-muted-foreground px-1.5 py-0.5 rounded border border-border cursor-help">
                              v{"version_number" in test ? test.version_number : 1}
                            </span>
                          </TooltipTrigger>
                          <TooltipContent side="top" className="text-xs bg-zinc-900 text-slate-100 border-none">
                            Current version of this test definition. Higher = newer.
                          </TooltipContent>
                        </Tooltip>
                      )}
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <span className={`text-[10px] px-1.5 py-0.5 rounded border font-medium cursor-help ${test.test_type_code === "automated"
                            ? "bg-violet-50 dark:bg-violet-950/30 text-violet-700 border-violet-200"
                            : "bg-muted text-muted-foreground border-border"
                            }`}>
                            {test.test_type_code}
                          </span>
                        </TooltipTrigger>
                        <TooltipContent side="top" className="text-xs bg-zinc-900 text-slate-100 border-none max-w-[220px]">
                          {test.test_type_code === "automated"
                            ? "Runs automatically on a schedule without manual intervention."
                            : "Requires a human to manually verify and record the result."}
                        </TooltipContent>
                      </Tooltip>
                    </div>
                    {test.description && (
                      <p className="text-sm text-muted-foreground mt-1 md:truncate md:whitespace-nowrap">{test.description}</p>
                    )}
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <p
                          className="text-[11px] font-mono text-muted-foreground/60 mt-0.5 break-all cursor-copy hover:text-primary transition-colors inline-block"
                          onClick={() => navigator.clipboard.writeText(test.test_code)}
                        >
                          {test.test_code}
                        </p>
                      </TooltipTrigger>
                      <TooltipContent side="bottom" className="text-xs bg-zinc-900 text-slate-100 border-none">
                        Click to copy Test ID
                      </TooltipContent>
                    </Tooltip>
                  </div>
                </div>
              </div>

              {/* Data Source & Live Session */}
              {isPromoted && "linked_asset_id" in test && test.linked_asset_id ? (
                <div className="rounded-xl border border-border bg-card overflow-hidden">
                  {/* Data Source Row */}
                  <div className={`flex items-center px-5 py-3 border-b border-border bg-muted/20`}>
                    <div className={`h-8 w-8 rounded-lg bg-gradient-to-r ${connectorBg("connector_type_code" in test ? test.connector_type_code : null)} flex items-center justify-center mr-3`}>
                      <ConnectorIcon typeCode={"connector_type_code" in test ? test.connector_type_code : null} className="h-4 w-4 text-white" />
                    </div>
                    <div className="flex-1">
                      <p className="text-xs text-muted-foreground">Data Source</p>
                      <p className="text-sm font-medium">{"connector_name" in test ? test.connector_name || connectorTypeLabel(test.connector_type_code) : "Not Configured"}</p>
                    </div>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <CheckCircle2 className="h-4 w-4 text-emerald-500 cursor-help" />
                      </TooltipTrigger>
                      <TooltipContent side="left" className="text-xs bg-zinc-900 text-slate-100 border-none">
                        Data source linked and authenticated successfully
                      </TooltipContent>
                    </Tooltip>
                  </div>

                  {/* Live Session Status */}
                  <div className={`flex items-center gap-3 px-5 py-3 border-b border-border ${statusConfig.bg}`}>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <span className={`inline-block h-2 w-2 rounded-full cursor-help ${statusConfig.dot}`} />
                      </TooltipTrigger>
                      <TooltipContent side="top" className="text-xs bg-zinc-900 text-slate-100 border-none max-w-[220px]">
                        {sessionStatus === "active" && "Session is running. Data is being collected and tests are executing automatically."}
                        {sessionStatus === "paused" && "Session is paused. No data collection or tests are running. Resume to continue."}
                        {sessionStatus === "starting" && "Session is booting up. Please wait…"}
                        {sessionStatus === "none" && "No active session. Start one to begin automated monitoring."}
                        {(sessionStatus === "stopped" || sessionStatus === "failed") && "Session was stopped. Start a new session to resume monitoring."}
                      </TooltipContent>
                    </Tooltip>
                    <span className={`text-xs font-semibold tracking-wide ${statusConfig.text}`}>
                      {sessionStatusLabel(sessionStatus)}
                    </span>
                    {sessionStatus === "active" && (
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <span className="flex items-center gap-1 text-xs text-emerald-600 cursor-help">
                            <Wifi className="h-3 w-3" /> Connected
                          </span>
                        </TooltipTrigger>
                        <TooltipContent side="top" className="text-xs bg-zinc-900 text-slate-100 border-none">
                          Live connection established. Receiving real-time data.
                        </TooltipContent>
                      </Tooltip>
                    )}
                    <div className="flex-1" />
                    {activeSession && (
                      <div className="flex items-center gap-4 text-xs text-muted-foreground">
                        {activeSession.data_points_received > 0 && (
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <span className="flex items-center gap-1 cursor-help"><Database className="h-3 w-3" /> {activeSession.data_points_received.toLocaleString()} pts</span>
                            </TooltipTrigger>
                            <TooltipContent side="top" className="text-xs bg-zinc-900 text-slate-100 border-none">
                              Total data points received from the connected source this session
                            </TooltipContent>
                          </Tooltip>
                        )}
                        {activeSession.started_at && (
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <span className="flex items-center gap-1 cursor-help"><Clock className="h-3 w-3" /> {formatRelative(activeSession.started_at)}</span>
                            </TooltipTrigger>
                            <TooltipContent side="top" className="text-xs bg-zinc-900 text-slate-100 border-none">
                              How long ago this session was started
                            </TooltipContent>
                          </Tooltip>
                        )}
                        {activeSession.signals_executed > 0 && (
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <span className="flex items-center gap-1 cursor-help"><Activity className="h-3 w-3" /> {activeSession.signals_executed} runs</span>
                            </TooltipTrigger>
                            <TooltipContent side="top" className="text-xs bg-zinc-900 text-slate-100 border-none">
                              Number of test executions completed in this session
                            </TooltipContent>
                          </Tooltip>
                        )}
                      </div>
                    )}
                  </div>

                  {/* Controls */}
                  <div className="px-5 py-4 flex items-center gap-2">
                    {sessionsLoading ? (
                      <Skeleton className="h-8 w-32" />
                    ) : (
                      <>
                        {sessionStatus === "none" && (
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <Button size="sm" className="gap-1.5" disabled={actionLoading} onClick={handleStartSession}>
                                <Play className="h-3.5 w-3.5" /> {actionLoading ? "Starting..." : "Start Session"}
                              </Button>
                            </TooltipTrigger>
                            <TooltipContent side="bottom" className="text-xs bg-zinc-900 text-slate-100 border-none max-w-[240px]">
                              Begin continuous automated monitoring. The system will collect data and run tests on a schedule.
                            </TooltipContent>
                          </Tooltip>
                        )}
                        {sessionStatus === "active" && (
                          <>
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <Button variant="outline" size="sm" className="gap-1.5" disabled={actionLoading} onClick={handlePauseSession}>
                                  <Pause className="h-3.5 w-3.5" /> Pause
                                </Button>
                              </TooltipTrigger>
                              <TooltipContent side="bottom" className="text-xs bg-zinc-900 text-slate-100 border-none max-w-[220px]">
                                Temporarily freeze monitoring. No data will be collected until you resume.
                              </TooltipContent>
                            </Tooltip>
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <Button variant="outline" size="sm" className="gap-1.5 text-destructive" disabled={actionLoading} onClick={handleStopSession}>
                                  <Square className="h-3.5 w-3.5" /> Stop
                                </Button>
                              </TooltipTrigger>
                              <TooltipContent side="bottom" className="text-xs bg-zinc-900 text-slate-100 border-none max-w-[220px]">
                                Permanently end this session. You will need to start a new session to resume monitoring.
                              </TooltipContent>
                            </Tooltip>
                          </>
                        )}
                        {sessionStatus === "paused" && (
                          <>
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <Button variant="outline" size="sm" className="gap-1.5" disabled={actionLoading} onClick={handleResumeSession}>
                                  <Play className="h-3.5 w-3.5" /> Resume
                                </Button>
                              </TooltipTrigger>
                              <TooltipContent side="bottom" className="text-xs bg-zinc-900 text-slate-100 border-none max-w-[220px]">
                                Resume the paused session. Data collection and test runs will continue.
                              </TooltipContent>
                            </Tooltip>
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <Button variant="outline" size="sm" className="gap-1.5 text-destructive" disabled={actionLoading} onClick={handleStopSession}>
                                  <Square className="h-3.5 w-3.5" /> Stop
                                </Button>
                              </TooltipTrigger>
                              <TooltipContent side="bottom" className="text-xs bg-zinc-900 text-slate-100 border-none max-w-[220px]">
                                Permanently end this session. You will need to start a new session to resume monitoring.
                              </TooltipContent>
                            </Tooltip>
                          </>
                        )}
                        {sessionStatus === "starting" && (
                          <Button variant="outline" size="sm" disabled className="gap-1.5">
                            <RotateCcw className="h-3.5 w-3.5 animate-spin" /> Starting
                          </Button>
                        )}
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <Button size="sm" variant="secondary" className="gap-1.5 ml-auto" disabled={actionLoading || !sourceSignalId} onClick={handleRunNow}>
                              <Zap className="h-3.5 w-3.5" /> Run Test Now
                            </Button>
                          </TooltipTrigger>
                          <TooltipContent side="bottom" className="text-xs bg-zinc-900 text-slate-100 border-none max-w-[260px]">
                            Force a single immediate test run right now, regardless of the schedule. Great for verifying a fix.
                          </TooltipContent>
                        </Tooltip>
                      </>
                    )}
                  </div>

                  {actionError && (
                    <div className="mx-5 mb-3 flex items-center gap-2 text-xs text-destructive bg-destructive/5 rounded-md px-3 py-2">
                      <AlertTriangle className="h-3.5 w-3.5" /> {actionError}
                    </div>
                  )}
                </div>
              ) : (
                <div className="rounded-xl border border-dashed border-amber-300 bg-amber-50 px-5 py-4 flex items-center gap-4">
                  <div className="h-10 w-10 rounded-full bg-amber-100 flex items-center justify-center">
                    <WifiOff className="h-5 w-5 text-amber-600" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-semibold text-amber-900">No data source linked</p>
                    <p className="text-xs text-amber-700">Link a connector to enable live sessions</p>
                  </div>
                  <Button variant="outline" size="sm" className="border-amber-300 text-amber-800" onClick={() => router.push("/tests")}>
                    <ExternalLink className="h-3.5 w-3.5 mr-1" /> Link Source
                  </Button>
                </div>
              )}

              {isPromoted && (
                <>
                  {/* Run Health Banner */}
                  <RunHealthBanner runs={runs} testName={test.name || test.test_code} />

                  {/* Recent Runs */}
                  <div className="rounded-xl border border-border bg-card">
                {/* Header */}
                <div className="flex items-center justify-between px-5 py-4 border-b border-border">
                  <div className="flex items-center gap-2">
                    <Activity className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm font-semibold">Recent Runs</span>
                    {runs.length > 0 && (
                      <span className="text-xs text-muted-foreground bg-muted px-2 py-0.5 rounded-full">
                        {runs.length}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-3">
                    <TrendSparkline runs={runs} />
                    <Button variant="ghost" size="sm" className="h-8 w-8 p-0" onClick={loadRuns}>
                      <RefreshCw className="h-4 w-4" />
                    </Button>
                  </div>
                </div>

                {runsLoading ? (
                  <div className="p-5 space-y-3">
                    {[1, 2, 3].map((i) => <Skeleton key={i} className="h-12 w-full rounded-lg" />)}
                  </div>
                ) : runs.length === 0 ? (
                  <div className="py-12 px-6">
                    <div className="max-w-md mx-auto">
                      <div className="h-12 w-12 mx-auto rounded-full bg-muted flex items-center justify-center mb-4">
                        <Lightbulb className="h-6 w-6 text-amber-500/60" />
                      </div>
                      <p className="text-sm font-bold text-foreground text-center">No runs recorded yet</p>
                      <p className="text-xs text-muted-foreground mt-1 text-center leading-relaxed">
                        Get started by completing the steps below to see your first test results.
                      </p>

                      {/* Getting Started Steps */}
                      <div className="mt-6 space-y-3">
                        <div className={`flex items-start gap-3 p-3 rounded-lg border ${test.linked_asset_id ? "border-emerald-500/20 bg-emerald-500/5" : "border-dashed border-amber-500/30 bg-amber-500/5"}`}>
                          <div className={`h-6 w-6 rounded-full flex items-center justify-center text-[10px] font-bold shrink-0 mt-0.5 ${test.linked_asset_id ? "bg-emerald-500 text-white" : "bg-amber-500/20 text-amber-600"}`}>
                            {test.linked_asset_id ? <CheckCircle2 className="h-3.5 w-3.5" /> : "1"}
                          </div>
                          <div>
                            <p className={`text-xs font-semibold ${test.linked_asset_id ? "text-emerald-700 dark:text-emerald-400" : "text-foreground"}`}>
                              {test.linked_asset_id ? "Data source connected" : "Connect a data source"}
                            </p>
                            <p className="text-[10px] text-muted-foreground mt-0.5">
                              {test.linked_asset_id ? "Your connector is linked and ready." : "Link a connector to collect data from your infrastructure."}
                            </p>
                          </div>
                        </div>

                        <div className={`flex items-start gap-3 p-3 rounded-lg border ${sessionStatus === "active" ? "border-emerald-500/20 bg-emerald-500/5" : "border-dashed border-border"}`}>
                          <div className={`h-6 w-6 rounded-full flex items-center justify-center text-[10px] font-bold shrink-0 mt-0.5 ${sessionStatus === "active" ? "bg-emerald-500 text-white" : "bg-muted text-muted-foreground"}`}>
                            {sessionStatus === "active" ? <CheckCircle2 className="h-3.5 w-3.5" /> : "2"}
                          </div>
                          <div>
                            <p className={`text-xs font-semibold ${sessionStatus === "active" ? "text-emerald-700 dark:text-emerald-400" : "text-foreground"}`}>
                              {sessionStatus === "active" ? "Session is running" : "Start a monitoring session"}
                            </p>
                            <p className="text-[10px] text-muted-foreground mt-0.5">
                              {sessionStatus === "active" ? "Data collection is active." : "Hit \"Start Session\" above to begin collecting data."}
                            </p>
                          </div>
                        </div>

                        <div className="flex items-start gap-3 p-3 rounded-lg border border-dashed border-border">
                          <div className="h-6 w-6 rounded-full flex items-center justify-center text-[10px] font-bold bg-muted text-muted-foreground shrink-0 mt-0.5">3</div>
                          <div>
                            <p className="text-xs font-semibold text-foreground">Run the test</p>
                            <p className="text-[10px] text-muted-foreground mt-0.5">
                              Click &quot;Run Test Now&quot; to execute immediately, or wait for the scheduled run.
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="divide-y divide-border/50">
                    {runs.map((run) => {
                      const isExpanded = expandedRunId === run.id
                      const details = (Array.isArray(run.result_details) ? run.result_details : []) as Array<{
                        asset_id?: string; asset_external_id?: string; result?: string; summary?: string;
                        execution_time_ms?: number; details?: Array<{ check?: string; status?: string; message?: string }>
                      }>
                      const failedCount = details.filter((d) => d.result === "fail").length
                      const passedCount = details.filter((d) => d.result === "pass").length
                      const warningCount = details.filter((d) => d.result === "warning").length

                      return (
                        <div key={run.id}>
                          <button
                            onClick={() => setExpandedRunId(isExpanded ? null : run.id)}
                            className="w-full flex items-center gap-4 px-5 py-3 text-left hover:bg-muted/30 transition-all"
                          >
                            <div className="shrink-0">
                              <RunResultBadge result={run.result_code} />
                            </div>
                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-medium truncate">{run.result_summary || "—"}</p>
                              <div className="flex items-center gap-3 mt-1">
                                {run.execution_time_ms !== null && (
                                  <span className="text-xs text-muted-foreground">
                                    {run.execution_time_ms}ms
                                  </span>
                                )}
                                {run.signal_name && (
                                  <span className="text-xs text-muted-foreground">• {run.signal_name}</span>
                                )}
                              </div>
                            </div>
                            <div className="flex items-center gap-2 shrink-0">
                              {passedCount > 0 && (
                                <span className="text-xs text-emerald-600 bg-emerald-50 dark:bg-emerald-950/30 px-2 py-0.5 rounded-full">
                                  {passedCount} pass
                                </span>
                              )}
                              {failedCount > 0 && (
                                <span className="text-xs text-red-600 bg-red-50 dark:bg-red-950/30 px-2 py-0.5 rounded-full">
                                  {failedCount} fail
                                </span>
                              )}
                              {warningCount > 0 && (
                                <span className="text-xs text-amber-600 bg-amber-50 dark:bg-amber-950/30 px-2 py-0.5 rounded-full">
                                  {warningCount} warn
                                </span>
                              )}
                              <span className="text-xs text-muted-foreground ml-2">
                                {formatDate(run.completed_at ?? run.started_at)}
                              </span>
                              {isExpanded ? (
                                <ChevronUp className="h-4 w-4 text-muted-foreground" />
                              ) : (
                                <ChevronDown className="h-4 w-4 text-muted-foreground" />
                              )}
                            </div>
                          </button>

                          {isExpanded && details.length > 0 && (
                            <div className="px-5 pb-4 pt-2 bg-muted/20">
                              <div className="grid grid-cols-3 gap-2 mb-4">
                                {passedCount > 0 && (
                                  <div className="flex items-center gap-2 text-xs text-emerald-600 bg-emerald-50 dark:bg-emerald-950/30 px-3 py-2 rounded-lg">
                                    <CheckCircle2 className="h-4 w-4" />
                                    <span className="font-medium">{passedCount} Passed</span>
                                  </div>
                                )}
                                {failedCount > 0 && (
                                  <div className="flex items-center gap-2 text-xs text-red-600 bg-red-50 dark:bg-red-950/30 px-3 py-2 rounded-lg">
                                    <XCircle className="h-4 w-4" />
                                    <span className="font-medium">{failedCount} Failed</span>
                                  </div>
                                )}
                                {warningCount > 0 && (
                                  <div className="flex items-center gap-2 text-xs text-amber-600 bg-amber-50 dark:bg-amber-950/30 px-3 py-2 rounded-lg">
                                    <AlertCircle className="h-4 w-4" />
                                    <span className="font-medium">{warningCount} Warnings</span>
                                  </div>
                                )}
                              </div>

                              {/* Failed Details */}
                              {details.filter(d => d.result === "fail").length > 0 && (
                                <div className="space-y-2 mb-4">
                                  <p className="text-xs font-semibold text-red-600 uppercase tracking-wide">Failed Assets</p>
                                  {details.filter(d => d.result === "fail").map((d, i) => (
                                    <div key={i} className="bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-800 rounded-lg p-3">
                                      <div className="flex items-center justify-between mb-1">
                                        <span className="text-sm font-medium text-red-700 dark:text-red-300 truncate">
                                          {d.asset_external_id || d.asset_id || `Asset ${i + 1}`}
                                        </span>
                                        <span className="text-xs text-muted-foreground">{d.execution_time_ms}ms</span>
                                      </div>
                                      <p className="text-xs text-muted-foreground">{d.summary}</p>
                                    </div>
                                  ))}

                                  {/* ── Next Steps for Failed Assets ── */}
                                  <div className="mt-4 rounded-lg border border-red-200/50 dark:border-red-800/30 bg-gradient-to-r from-red-50/50 via-transparent to-transparent dark:from-red-950/10 p-4">
                                    <div className="flex items-center gap-2 mb-3">
                                      <Lightbulb className="h-3.5 w-3.5 text-amber-500" />
                                      <span className="text-[10px] font-bold uppercase tracking-widest text-foreground/80">Recommended Next Steps</span>
                                    </div>
                                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                                      <a
                                        href={`/issues?search=${encodeURIComponent(test?.name || test?.test_code || "")}`}
                                        className="flex items-center gap-2.5 p-2.5 rounded-lg border border-red-200 dark:border-red-800/40 bg-white dark:bg-red-950/20 hover:bg-red-50 dark:hover:bg-red-950/30 transition-all group cursor-pointer"
                                      >
                                        <div className="h-7 w-7 rounded-lg bg-red-500/10 flex items-center justify-center shrink-0 group-hover:bg-red-500/20 transition-colors">
                                          <ListChecks className="h-3.5 w-3.5 text-red-600 dark:text-red-400" />
                                        </div>
                                        <div className="min-w-0">
                                          <p className="text-[11px] font-bold text-foreground group-hover:text-red-700 dark:group-hover:text-red-400 transition-colors">View Issues</p>
                                          <p className="text-[9px] text-muted-foreground leading-tight">Track investigation & fix</p>
                                        </div>
                                        <ArrowUpRight className="h-3 w-3 text-muted-foreground/40 ml-auto group-hover:text-red-500 transition-colors" />
                                      </a>

                                      <a
                                        href="/monitoring"
                                        className="flex items-center gap-2.5 p-2.5 rounded-lg border border-border bg-white dark:bg-card hover:bg-muted/30 transition-all group cursor-pointer"
                                      >
                                        <div className="h-7 w-7 rounded-lg bg-blue-500/10 flex items-center justify-center shrink-0 group-hover:bg-blue-500/20 transition-colors">
                                          <Eye className="h-3.5 w-3.5 text-blue-600 dark:text-blue-400" />
                                        </div>
                                        <div className="min-w-0">
                                          <p className="text-[11px] font-bold text-foreground group-hover:text-blue-700 dark:group-hover:text-blue-400 transition-colors">Live Monitor</p>
                                          <p className="text-[9px] text-muted-foreground leading-tight">Watch signals in real-time</p>
                                        </div>
                                        <ArrowUpRight className="h-3 w-3 text-muted-foreground/40 ml-auto group-hover:text-blue-500 transition-colors" />
                                      </a>

                                      <a
                                        href={`/controls?search=${encodeURIComponent(test?.name || test?.test_code || "")}`}
                                        className="flex items-center gap-2.5 p-2.5 rounded-lg border border-border bg-white dark:bg-card hover:bg-muted/30 transition-all group cursor-pointer"
                                      >
                                        <div className="h-7 w-7 rounded-lg bg-violet-500/10 flex items-center justify-center shrink-0 group-hover:bg-violet-500/20 transition-colors">
                                          <Shield className="h-3.5 w-3.5 text-violet-600 dark:text-violet-400" />
                                        </div>
                                        <div className="min-w-0">
                                          <p className="text-[11px] font-bold text-foreground group-hover:text-violet-700 dark:group-hover:text-violet-400 transition-colors">Mapped Controls</p>
                                          <p className="text-[9px] text-muted-foreground leading-tight">See affected compliance controls</p>
                                        </div>
                                        <ArrowUpRight className="h-3 w-3 text-muted-foreground/40 ml-auto group-hover:text-violet-500 transition-colors" />
                                      </a>
                                    </div>
                                  </div>
                                </div>
                              )}

                              {/* Warnings */}
                              {details.filter(d => d.result === "warning").length > 0 && (
                                <div className="space-y-2 mb-4">
                                  <p className="text-xs font-semibold text-amber-600 uppercase tracking-wide">Warnings</p>
                                  {details.filter(d => d.result === "warning").map((d, i) => (
                                    <div key={i} className="bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800 rounded-lg p-3">
                                      <div className="flex items-center justify-between mb-1">
                                        <span className="text-sm font-medium text-amber-700 dark:text-amber-300 truncate">
                                          {d.asset_external_id || d.asset_id || `Asset ${i + 1}`}
                                        </span>
                                        <span className="text-xs text-muted-foreground">{d.execution_time_ms}ms</span>
                                      </div>
                                      <p className="text-xs text-muted-foreground">{d.summary}</p>
                                    </div>
                                  ))}
                                </div>
                              )}

                              {/* Passed */}
                              {passedCount > 0 && (
                                <div>
                                  <p className="text-xs font-semibold text-emerald-600 uppercase tracking-wide mb-2">
                                    Passed ({passedCount})
                                  </p>
                                  <div className="flex flex-wrap gap-1.5">
                                    {details.filter(d => d.result === "pass").slice(0, 15).map((d, i) => (
                                      <span
                                        key={i}
                                        className="inline-flex items-center gap-1 text-xs px-2 py-1 rounded-full bg-emerald-50 dark:bg-emerald-950/30 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800"
                                      >
                                        <CheckCircle2 className="h-3 w-3" />
                                        {(d.asset_external_id || d.asset_id || "").split("/").pop()}
                                      </span>
                                    ))}
                                    {passedCount > 15 && (
                                      <span className="text-xs text-muted-foreground px-2 py-1">
                                        +{passedCount - 15} more
                                      </span>
                                    )}
                                  </div>
                                </div>
                              )}

                              {/* All passing — next steps */}
                              {failedCount === 0 && warningCount === 0 && passedCount > 0 && (
                                <div className="mt-4 rounded-lg border border-emerald-200/50 dark:border-emerald-800/30 bg-emerald-50/30 dark:bg-emerald-950/10 p-3">
                                  <div className="flex items-center gap-2">
                                    <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
                                    <span className="text-[10px] font-bold text-emerald-700 dark:text-emerald-400 uppercase tracking-wider">Run fully passing</span>
                                    <span className="text-[10px] text-muted-foreground ml-auto">No action needed</span>
                                  </div>
                                  <p className="text-[10px] text-muted-foreground mt-1.5 leading-relaxed pl-5">
                                    All {passedCount} asset{passedCount !== 1 ? "s" : ""} passed. Continue monitoring on the{" "}
                                    <a href="/monitoring" className="text-primary hover:underline font-medium">Live Monitor</a>{" "}
                                    to catch any future drift.
                                  </p>
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      )
                    })}
                  </div>
                )}
                  </div>
                </>
              )}

              {/* Test Details */}
              <div className="rounded-xl border border-border bg-card p-5">
                <div className="flex items-center gap-2 mb-4">
                  <FileText className="h-4 w-4 text-muted-foreground" />
                  <span className="text-[11px] font-semibold uppercase tracking-widest text-muted-foreground">Test Details</span>
                </div>

                <dl className="grid grid-cols-2 sm:grid-cols-4 gap-x-6 gap-y-4 mb-4">
                  <div>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <dt className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold mb-0.5 cursor-help inline-block">Code</dt>
                      </TooltipTrigger>
                      <TooltipContent side="top" className="text-xs bg-zinc-900 text-slate-100 border-none">Unique system identifier for this test</TooltipContent>
                    </Tooltip>
                    <dd className="text-sm font-mono break-all">{test.test_code}</dd>
                  </div>
                  <div>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <dt className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold mb-0.5 cursor-help inline-block">Type</dt>
                      </TooltipTrigger>
                      <TooltipContent side="top" className="text-xs bg-zinc-900 text-slate-100 border-none">Automated tests run on a schedule; Manual tests require human verification</TooltipContent>
                    </Tooltip>
                    <dd className="text-sm capitalize">{test.test_type_code}</dd>
                  </div>
                  <div>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <dt className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold mb-0.5 cursor-help inline-block">Monitoring</dt>
                      </TooltipTrigger>
                      <TooltipContent side="top" className="text-xs bg-zinc-900 text-slate-100 border-none">How often this test checks the data source for compliance</TooltipContent>
                    </Tooltip>
                    <dd className="text-sm">{formatFrequency(test.monitoring_frequency)}</dd>
                  </div>
                  <div>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <dt className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold mb-0.5 cursor-help inline-block">Promoted</dt>
                      </TooltipTrigger>
                      <TooltipContent side="top" className="text-xs bg-zinc-900 text-slate-100 border-none">When this test was moved from draft/sandbox to production</TooltipContent>
                    </Tooltip>
                    <dd className="text-sm">{"promoted_at" in test ? formatDate(test.promoted_at) : "Not Promoted"}</dd>
                  </div>
                  <div>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <dt className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold mb-0.5 cursor-help inline-block">Version</dt>
                      </TooltipTrigger>
                      <TooltipContent side="top" className="text-xs bg-zinc-900 text-slate-100 border-none">Current iteration of the test rules. Higher version = newer definition.</TooltipContent>
                    </Tooltip>
                    <dd className="text-sm">{"version_number" in test ? `v${test.version_number}` : "v1"}</dd>
                  </div>
                  <div>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <dt className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold mb-0.5 cursor-help inline-block">Status</dt>
                      </TooltipTrigger>
                      <TooltipContent side="top" className="text-xs bg-zinc-900 text-slate-100 border-none">Whether this test is currently enabled and running in production</TooltipContent>
                    </Tooltip>
                    <dd className="text-sm">
                      {test.is_active
                        ? <span className="text-green-600 font-medium">Active</span>
                        : <span className="text-muted-foreground">Inactive</span>
                      }
                    </dd>
                  </div>
                  {test.signal_type && (
                    <div>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <dt className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold mb-0.5 cursor-help inline-block">Signal Type</dt>
                        </TooltipTrigger>
                        <TooltipContent side="top" className="text-xs bg-zinc-900 text-slate-100 border-none">The category of check this signal performs (e.g., security, config)</TooltipContent>
                      </Tooltip>
                      <dd className="text-sm">{test.signal_type}</dd>
                    </div>
                  )}
                  {sourceSignalId && (
                    <div>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <dt className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold mb-0.5 cursor-help inline-block">Source</dt>
                        </TooltipTrigger>
                        <TooltipContent side="top" className="text-xs bg-zinc-900 text-slate-100 border-none">The original sandbox signal this test was created from</TooltipContent>
                      </Tooltip>
                      <dd>
                        <a href="/sandbox/signals" className="text-sm text-primary hover:underline flex items-center gap-1">
                          View Signal <ExternalLink className="h-3 w-3" />
                        </a>
                      </dd>
                    </div>
                  )}
                </dl>

                {/* Evaluation Rule - Collapsible */}
                {test.evaluation_rule && (
                  <div className="mt-4">
                    <div className="flex items-center gap-2">
                      <div className="flex items-center gap-1.5">
                        <Code2 className="h-3.5 w-3.5 text-foreground" />
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <span className="text-[10px] uppercase tracking-widest text-foreground font-semibold cursor-help">Evaluation Rule</span>
                          </TooltipTrigger>
                          <TooltipContent side="top" className="text-xs bg-zinc-900 text-slate-100 border-none max-w-[260px]">
                            The code logic that determines whether this test passes or fails when run against collected data.
                          </TooltipContent>
                        </Tooltip>
                      </div>
                      <Button variant="outline" size="sm" className="h-6 text-xs px-2" onClick={() => setShowEvaluationRule(!showEvaluationRule)}>
                        {showEvaluationRule ? "Hide" : "View"}
                      </Button>
                    </div>

                    {showEvaluationRule && (
                      <div className="mt-2 rounded-lg border border-border overflow-hidden">
                        <pre className="text-xs bg-black text-white p-4 max-h-[300px] overflow-auto whitespace-pre-wrap break-words" style={{ scrollbarWidth: 'thin', WebkitOverflowScrolling: 'touch' }}>
                          {test.evaluation_rule}
                        </pre>
                      </div>
                    )}
                  </div>
                )}

                {test.integration_guide && (
                  <div className="mt-4 text-sm text-muted-foreground bg-muted/40 rounded-lg px-4 py-3 border border-border">
                    <p className="text-[10px] uppercase tracking-widest text-muted-foreground font-semibold mb-1">Integration Guide</p>
                    <p className="text-sm">{test.integration_guide}</p>
                  </div>
                )}
              </div>
            </div>
          )}
        </main>
      </div>
    </TooltipProvider>
  )
}

// Helper for sessionStatusLabel
function sessionStatusLabel(status: SessionStatus): string {
  return status === "none" ? "NO SESSION" : status.toUpperCase()
}