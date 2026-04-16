"use client"

import { useEffect, useState, useCallback, useRef } from "react"
import { Button, Badge } from "@kcontrol/ui"
import {
  Activity,
  Play,
  Pause,
  Square,
  RefreshCw,
  Loader2,
  ArrowLeft,
  Plus,
  Clock,
  Database,
  Zap,
  ShieldAlert,
  X,
  CheckCircle2,
  AlertCircle,
  Save,
  FlaskConical,
  XCircle,
  AlertTriangle,
  Timer,
  ChevronDown,
  ChevronUp,
} from "lucide-react"
import Link from "next/link"
import {
  listLiveSessions,
  stopSession,
  pauseSession,
  resumeSession,
  listConnectors,
  listSignals,
  runLiveTest,
} from "@/lib/api/sandbox"
import type {
  LiveSessionResponse,
  ConnectorInstanceResponse,
  SignalResponse,
  LiveTestResponse,
  LiveTestResultItem,
} from "@/lib/api/sandbox"
import { useSandboxOrgWorkspace } from "@/lib/context/SandboxOrgWorkspaceContext"

// ─────────────────────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────────────────────

function formatDate(iso: string | null) {
  if (!iso) return "\u2014"
  return new Date(iso).toLocaleString("en-US", {
    month: "short", day: "numeric", year: "numeric",
    hour: "2-digit", minute: "2-digit",
  })
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function statusBadge(status: string) {
  const styles: Record<string, string> = {
    active: "text-green-500 border-green-500/30 bg-green-500/5",
    paused: "text-amber-500 border-amber-500/30 bg-amber-500/5",
    stopped: "text-muted-foreground border-border",
    expired: "text-red-500 border-red-500/30 bg-red-500/5",
    saved: "text-blue-500 border-blue-500/30 bg-blue-500/5",
  }
  return styles[status] ?? "text-muted-foreground border-border"
}

function statusDot(status: string) {
  const dots: Record<string, string> = {
    active: "bg-green-500 animate-pulse",
    paused: "bg-amber-500",
    stopped: "bg-muted-foreground/40",
    expired: "bg-red-500",
    saved: "bg-blue-500",
  }
  return dots[status] ?? "bg-muted-foreground/40"
}

function resultBadgeStyle(result: string): string {
  const styles: Record<string, string> = {
    pass: "text-green-600 bg-green-500/10 border-green-500/30",
    fail: "text-red-600 bg-red-500/10 border-red-500/30",
    warning: "text-amber-600 bg-amber-500/10 border-amber-500/30",
    error: "text-red-600 bg-red-500/10 border-red-500/30",
    timeout: "text-orange-600 bg-orange-500/10 border-orange-500/30",
  }
  return styles[result] ?? "text-muted-foreground border-border"
}

function ResultIcon({ result }: { result: string }) {
  switch (result) {
    case "pass":
      return <CheckCircle2 className="h-3.5 w-3.5 text-green-500" />
    case "fail":
      return <XCircle className="h-3.5 w-3.5 text-red-500" />
    case "warning":
      return <AlertTriangle className="h-3.5 w-3.5 text-amber-500" />
    case "timeout":
      return <Timer className="h-3.5 w-3.5 text-orange-500" />
    default:
      return <AlertCircle className="h-3.5 w-3.5 text-red-500" />
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Session Card
// ─────────────────────────────────────────────────────────────────────────────

function SessionCard({
  session,
  onAction,
  orgId,
}: {
  session: LiveSessionResponse
  onAction: () => void
  orgId: string
}) {
  const [acting, setActing] = useState(false)
  const [actionError, setActionError] = useState<string | null>(null)

  async function doStop() {
    setActing(true); setActionError(null)
    try { await stopSession(orgId, session.id); onAction() }
    catch (e) { setActionError(e instanceof Error ? e.message : "Failed to stop") }
    finally { setActing(false) }
  }

  async function doPause() {
    setActing(true); setActionError(null)
    try { await pauseSession(orgId, session.id); onAction() }
    catch (e) { setActionError(e instanceof Error ? e.message : "Failed to pause") }
    finally { setActing(false) }
  }

  async function doResume() {
    setActing(true); setActionError(null)
    try { await resumeSession(orgId, session.id); onAction() }
    catch (e) { setActionError(e instanceof Error ? e.message : "Failed to resume") }
    finally { setActing(false) }
  }

  const isActive = session.session_status === "active"
  const isPaused = session.session_status === "paused"
  const isTerminal = ["stopped", "expired", "saved"].includes(session.session_status)

  return (
    <div className="rounded-xl border bg-card overflow-hidden">
      {/* Header */}
      <div className="flex items-start gap-3 px-4 py-3.5 border-b border-border">
        <div className={`h-2 w-2 rounded-full mt-1.5 shrink-0 ${statusDot(session.session_status)}`} />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <p className="text-sm font-medium text-foreground">
              {session.connector_name ?? session.connector_instance_id.slice(0, 8)}
            </p>
            <Badge variant="outline" className={`text-[10px] ${statusBadge(session.session_status)}`}>
              {session.session_status}
            </Badge>
            {session.connector_type_code && (
              <Badge variant="outline" className="text-[10px] text-muted-foreground">
                {session.connector_type_code}
              </Badge>
            )}
          </div>
          <p className="text-[11px] text-muted-foreground mt-0.5 font-mono">{session.id.slice(0, 16)}...</p>
        </div>
        {/* Controls */}
        {!isTerminal && (
          <div className="flex items-center gap-1.5 shrink-0">
            {isActive && (
              <Button variant="outline" size="sm" className="h-7 text-xs gap-1.5" onClick={doPause} disabled={acting}>
                {acting ? <Loader2 className="h-3 w-3 animate-spin" /> : <Pause className="h-3 w-3" />}
                Pause
              </Button>
            )}
            {isPaused && (
              <Button variant="outline" size="sm" className="h-7 text-xs gap-1.5" onClick={doResume} disabled={acting}>
                {acting ? <Loader2 className="h-3 w-3 animate-spin" /> : <Play className="h-3 w-3" />}
                Resume
              </Button>
            )}
            <Button variant="outline" size="sm" className="h-7 text-xs gap-1.5 text-red-500 hover:text-red-500 border-red-500/30 hover:bg-red-500/5" onClick={doStop} disabled={acting}>
              <Square className="h-3 w-3" />
              Stop
            </Button>
          </div>
        )}
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-0 divide-x divide-y sm:divide-y-0 divide-border border-b border-border">
        <div className="flex flex-col items-center justify-center gap-0.5 px-3 py-2.5 text-center">
          <span className="text-xs font-semibold tabular-nums text-foreground">{session.data_points_received.toLocaleString()}</span>
          <span className="text-[10px] text-muted-foreground">Data Points</span>
        </div>
        <div className="flex flex-col items-center justify-center gap-0.5 px-3 py-2.5 text-center">
          <span className="text-xs font-semibold tabular-nums text-foreground">{formatBytes(session.bytes_received)}</span>
          <span className="text-[10px] text-muted-foreground">Received</span>
        </div>
        <div className="flex flex-col items-center justify-center gap-0.5 px-3 py-2.5 text-center">
          <span className="text-xs font-semibold tabular-nums text-foreground">{session.signals_executed}</span>
          <span className="text-[10px] text-muted-foreground">Signals Run</span>
        </div>
        <div className="flex flex-col items-center justify-center gap-0.5 px-3 py-2.5 text-center">
          <span className="text-xs font-semibold tabular-nums text-foreground">{session.threats_evaluated}</span>
          <span className="text-[10px] text-muted-foreground">Threats Eval</span>
        </div>
      </div>

      {/* Footer meta */}
      <div className="flex flex-wrap items-center gap-4 px-4 py-2.5 text-[11px] text-muted-foreground">
        <span className="flex items-center gap-1"><Clock className="h-3 w-3" />{session.duration_minutes}m duration</span>
        {session.started_at && <span>Started {formatDate(session.started_at)}</span>}
        {session.expires_at && !isTerminal && <span className="text-amber-500">Expires {formatDate(session.expires_at)}</span>}
        {session.attached_signals.length > 0 && (
          <span className="flex items-center gap-1">
            <Zap className="h-3 w-3" />
            {session.attached_signals.length} signal{session.attached_signals.length !== 1 ? "s" : ""}
          </span>
        )}
        {session.attached_threats.length > 0 && (
          <span className="flex items-center gap-1">
            <ShieldAlert className="h-3 w-3" />
            {session.attached_threats.length} threat{session.attached_threats.length !== 1 ? "s" : ""}
          </span>
        )}
      </div>

      {actionError && (
        <div className="px-4 pb-2.5 text-xs text-red-500">{actionError}</div>
      )}
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Start Session Dialog
// ─────────────────────────────────────────────────────────────────────────────

function StartSessionDialog({
  orgId,
  workspaceId,
  connectors,
  signals,
  onStarted,
  onClose,
}: {
  orgId: string
  workspaceId: string
  connectors: ConnectorInstanceResponse[]
  signals: SignalResponse[]
  onStarted: () => void
  onClose: () => void
}) {
  const [connectorId, setConnectorId] = useState(connectors[0]?.id ?? "")
  const [durationMinutes, setDurationMinutes] = useState(30)
  const [selectedSignals, setSelectedSignals] = useState<string[]>([])
  const [starting, setStarting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleStart() {
    if (!connectorId) { setError("Select a connector"); return }
    setStarting(true); setError(null)
    try {
      const { startLiveSession } = await import("@/lib/api/sandbox")
      await startLiveSession({
        org_id: orgId,
        connector_instance_id: connectorId,
        signal_ids: selectedSignals.length > 0 ? selectedSignals : undefined,
        duration_minutes: durationMinutes,
        workspace_id: workspaceId,
      })
      onStarted()
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to start session")
    } finally {
      setStarting(false)
    }
  }

  function toggleSignal(id: string) {
    setSelectedSignals((prev) =>
      prev.includes(id) ? prev.filter((s) => s !== id) : [...prev, id]
    )
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
      <div className="bg-background rounded-2xl border shadow-xl w-full max-w-lg">
        <div className="flex items-center justify-between px-5 py-4 border-b">
          <h2 className="text-sm font-semibold">Start Live Session</h2>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground">
            <X className="h-4 w-4" />
          </button>
        </div>
        <div className="px-5 py-4 space-y-4">
          {/* Connector */}
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-muted-foreground">Connector</label>
            <select
              value={connectorId}
              onChange={(e) => setConnectorId(e.target.value)}
              className="w-full h-9 rounded-md border border-input bg-background px-3 text-sm focus:outline-none focus:ring-1 focus:ring-ring"
            >
              {connectors.map((c) => (
                <option key={c.id} value={c.id}>{c.name ?? c.instance_code}</option>
              ))}
            </select>
          </div>

          {/* Duration */}
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-muted-foreground">Duration (minutes)</label>
            <input
              type="number"
              min={1}
              max={480}
              value={durationMinutes}
              onChange={(e) => setDurationMinutes(Number(e.target.value))}
              className="w-full h-9 rounded-md border border-input bg-background px-3 text-sm focus:outline-none focus:ring-1 focus:ring-ring"
            />
          </div>

          {/* Signals */}
          {signals.length > 0 && (
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-muted-foreground">
                Attach Signals <span className="text-muted-foreground/50">(optional)</span>
              </label>
              <div className="max-h-36 overflow-y-auto rounded-md border border-input divide-y divide-border">
                {signals.slice(0, 20).map((s) => (
                  <label key={s.id} className="flex items-center gap-2.5 px-3 py-2 cursor-pointer hover:bg-muted/10">
                    <input
                      type="checkbox"
                      checked={selectedSignals.includes(s.id)}
                      onChange={() => toggleSignal(s.id)}
                      className="rounded"
                    />
                    <span className="text-xs font-mono text-foreground truncate">{s.signal_code}</span>
                    {s.name && <span className="text-[11px] text-muted-foreground truncate">{s.name}</span>}
                  </label>
                ))}
              </div>
            </div>
          )}

          {error && <p className="text-xs text-red-500">{error}</p>}
        </div>
        <div className="flex items-center justify-end gap-2 px-5 py-4 border-t">
          <Button variant="outline" size="sm" onClick={onClose}>Cancel</Button>
          <Button size="sm" onClick={handleStart} disabled={starting || !connectorId} className="gap-1.5">
            {starting ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Play className="h-3.5 w-3.5" />}
            Start Session
          </Button>
        </div>
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Live Test Dialog
// ─────────────────────────────────────────────────────────────────────────────

function LiveTestDialog({
  orgId,
  workspaceId,
  connectors,
  signals,
  onClose,
}: {
  orgId: string
  workspaceId: string
  connectors: ConnectorInstanceResponse[]
  signals: SignalResponse[]
  onClose: (result?: LiveTestResponse) => void
}) {
  const [connectorId, setConnectorId] = useState(connectors[0]?.id ?? "")
  const [selectedSignals, setSelectedSignals] = useState<string[]>([])
  const [running, setRunning] = useState(false)
  const [phase, setPhase] = useState<"config" | "running">("config")
  const [error, setError] = useState<string | null>(null)

  // Filter signals that have generated code (status = validated means codegen passed)
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const testableSignals = signals.filter((s) => s.signal_status_code === "validated" || (s as any).properties?.python_source)

  function toggleSignal(id: string) {
    setSelectedSignals((prev) =>
      prev.includes(id) ? prev.filter((s) => s !== id) : [...prev, id]
    )
  }

  function selectAll() {
    if (selectedSignals.length === testableSignals.length) {
      setSelectedSignals([])
    } else {
      setSelectedSignals(testableSignals.map((s) => s.id))
    }
  }

  async function handleRun() {
    if (!connectorId) { setError("Select a connector"); return }
    if (selectedSignals.length === 0) { setError("Select at least one signal to test"); return }
    setRunning(true)
    setPhase("running")
    setError(null)
    try {
      const result = await runLiveTest(orgId, workspaceId, {
        connector_id: connectorId,
        signal_ids: selectedSignals,
      })
      onClose(result)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to run live test")
      setPhase("config")
    } finally {
      setRunning(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
      <div className="bg-background rounded-2xl border shadow-xl w-full max-w-lg">
        <div className="flex items-center justify-between px-5 py-4 border-b">
          <div className="flex items-center gap-2">
            <FlaskConical className="h-4 w-4 text-primary" />
            <h2 className="text-sm font-semibold">New Live Test</h2>
          </div>
          <button onClick={() => onClose()} className="text-muted-foreground hover:text-foreground">
            <X className="h-4 w-4" />
          </button>
        </div>

        {phase === "running" ? (
          <div className="px-5 py-12 flex flex-col items-center gap-4">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
            <div className="text-center">
              <p className="text-sm font-medium text-foreground">Running tests...</p>
              <p className="text-xs text-muted-foreground mt-1">
                Executing {selectedSignals.length} signal{selectedSignals.length !== 1 ? "s" : ""} against collected assets
              </p>
            </div>
          </div>
        ) : (
          <>
            <div className="px-5 py-4 space-y-4">
              {/* Connector */}
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-muted-foreground">Connector</label>
                <select
                  value={connectorId}
                  onChange={(e) => setConnectorId(e.target.value)}
                  className="w-full h-9 rounded-md border border-input bg-background px-3 text-sm focus:outline-none focus:ring-1 focus:ring-ring"
                >
                  {connectors.map((c) => (
                    <option key={c.id} value={c.id}>{c.name ?? c.instance_code}</option>
                  ))}
                </select>
                <p className="text-[11px] text-muted-foreground">
                  Tests will run against the latest collected assets from this connector.
                </p>
              </div>

              {/* Signals */}
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-medium text-muted-foreground">
                    Control Tests to Run
                  </label>
                  {testableSignals.length > 0 && (
                    <button
                      onClick={selectAll}
                      className="text-[11px] text-primary hover:underline"
                    >
                      {selectedSignals.length === testableSignals.length ? "Deselect all" : "Select all"}
                    </button>
                  )}
                </div>
                {testableSignals.length > 0 ? (
                  <div className="max-h-48 overflow-y-auto rounded-md border border-input divide-y divide-border">
                    {testableSignals.map((s) => (
                      <label key={s.id} className="flex items-center gap-2.5 px-3 py-2 cursor-pointer hover:bg-muted/10">
                        <input
                          type="checkbox"
                          checked={selectedSignals.includes(s.id)}
                          onChange={() => toggleSignal(s.id)}
                          className="rounded"
                        />
                        <div className="flex-1 min-w-0">
                          <span className="text-xs font-mono text-foreground truncate block">{s.signal_code}</span>
                          {s.name && <span className="text-[11px] text-muted-foreground truncate block">{s.name}</span>}
                        </div>
                      </label>
                    ))}
                  </div>
                ) : (
                  <div className="rounded-md border border-dashed border-border px-3 py-4 text-center">
                    <p className="text-xs text-muted-foreground">
                      No signals with Python source found. Create signals with code first.
                    </p>
                  </div>
                )}
                <p className="text-[11px] text-muted-foreground">
                  {selectedSignals.length} of {testableSignals.length} signal{testableSignals.length !== 1 ? "s" : ""} selected
                </p>
              </div>

              {error && <p className="text-xs text-red-500">{error}</p>}
            </div>

            <div className="flex items-center justify-end gap-2 px-5 py-4 border-t">
              <Button variant="outline" size="sm" onClick={() => onClose()}>Cancel</Button>
              <Button
                size="sm"
                onClick={handleRun}
                disabled={running || !connectorId || selectedSignals.length === 0}
                className="gap-1.5"
              >
                {running ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <FlaskConical className="h-3.5 w-3.5" />}
                Collect & Test
              </Button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Live Test Results View
// ─────────────────────────────────────────────────────────────────────────────

function LiveTestResultsView({
  result,
  connectors,
  onClose,
}: {
  result: LiveTestResponse
  connectors: ConnectorInstanceResponse[]
  onClose: () => void
}) {
  const [filterResult, setFilterResult] = useState("")
  const [expandedRow, setExpandedRow] = useState<number | null>(null)

  const connector = connectors.find((c) => c.id === result.connector_id)
  const connectorLabel = connector?.name ?? connector?.instance_code ?? result.connector_id.slice(0, 8)

  const filteredResults = filterResult
    ? result.results.filter((r) => r.result === filterResult)
    : result.results

  return (
    <div className="space-y-4">
      {/* Summary bar */}
      <div className="rounded-xl border bg-card overflow-hidden">
        <div className="flex items-center justify-between px-4 py-3 border-b border-border">
          <div className="flex items-center gap-2">
            <FlaskConical className="h-4 w-4 text-primary" />
            <h3 className="text-sm font-semibold text-foreground">Live Test Results</h3>
            <Badge variant="outline" className="text-[10px] text-muted-foreground">
              {connectorLabel}
            </Badge>
          </div>
          <Button variant="outline" size="sm" className="h-7 text-xs" onClick={onClose}>
            <X className="h-3 w-3 mr-1" />
            Close
          </Button>
        </div>

        {/* Summary stats */}
        <div className="px-4 py-3 bg-muted/30">
          <p className="text-xs text-muted-foreground">
            {result.total_assets} asset{result.total_assets !== 1 ? "s" : ""} x{" "}
            {result.total_signals} signal{result.total_signals !== 1 ? "s" : ""} ={" "}
            <span className="font-semibold text-foreground">{result.total_tests} tests</span>
          </p>
        </div>

        {/* KPI row */}
        <div className="grid grid-cols-4 gap-0 divide-x divide-border">
          <button
            onClick={() => setFilterResult(filterResult === "pass" ? "" : "pass")}
            className={`flex flex-col items-center gap-0.5 px-3 py-3 transition-colors hover:bg-muted/20 ${filterResult === "pass" ? "bg-green-500/5" : ""}`}
          >
            <span className="text-lg font-bold text-green-600 tabular-nums">{result.passed}</span>
            <span className="text-[10px] text-muted-foreground">Passed</span>
          </button>
          <button
            onClick={() => setFilterResult(filterResult === "fail" ? "" : "fail")}
            className={`flex flex-col items-center gap-0.5 px-3 py-3 transition-colors hover:bg-muted/20 ${filterResult === "fail" ? "bg-red-500/5" : ""}`}
          >
            <span className="text-lg font-bold text-red-600 tabular-nums">{result.failed}</span>
            <span className="text-[10px] text-muted-foreground">Failed</span>
          </button>
          <button
            onClick={() => setFilterResult(filterResult === "warning" ? "" : "warning")}
            className={`flex flex-col items-center gap-0.5 px-3 py-3 transition-colors hover:bg-muted/20 ${filterResult === "warning" ? "bg-amber-500/5" : ""}`}
          >
            <span className="text-lg font-bold text-amber-600 tabular-nums">{result.warnings}</span>
            <span className="text-[10px] text-muted-foreground">Warnings</span>
          </button>
          <button
            onClick={() => setFilterResult(filterResult === "error" ? "" : "error")}
            className={`flex flex-col items-center gap-0.5 px-3 py-3 transition-colors hover:bg-muted/20 ${filterResult === "error" ? "bg-red-500/5" : ""}`}
          >
            <span className="text-lg font-bold text-red-600 tabular-nums">{result.errors}</span>
            <span className="text-[10px] text-muted-foreground">Errors</span>
          </button>
        </div>
      </div>

      {/* Results table */}
      <div className="rounded-xl border bg-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-border bg-muted/30">
                <th className="text-left px-3 py-2.5 font-medium text-muted-foreground w-8"></th>
                <th className="text-left px-3 py-2.5 font-medium text-muted-foreground">Asset</th>
                <th className="text-left px-3 py-2.5 font-medium text-muted-foreground">Type</th>
                <th className="text-left px-3 py-2.5 font-medium text-muted-foreground">Signal</th>
                <th className="text-left px-3 py-2.5 font-medium text-muted-foreground">Result</th>
                <th className="text-left px-3 py-2.5 font-medium text-muted-foreground">Summary</th>
                <th className="text-right px-3 py-2.5 font-medium text-muted-foreground">Time</th>
              </tr>
            </thead>
            <tbody>
              {filteredResults.length === 0 ? (
                <tr>
                  <td colSpan={7} className="text-center py-8 text-muted-foreground">
                    {filterResult ? `No ${filterResult} results found.` : "No results."}
                  </td>
                </tr>
              ) : (
                filteredResults.map((item, idx) => (
                  <LiveTestResultRow
                    key={`${item.asset_id}-${item.signal_id}-${idx}`}
                    item={item}
                    index={idx}
                    isExpanded={expandedRow === idx}
                    onToggle={() => setExpandedRow(expandedRow === idx ? null : idx)}
                  />
                ))
              )}
            </tbody>
          </table>
        </div>
        {filteredResults.length > 0 && (
          <div className="px-3 py-2 border-t border-border bg-muted/20 text-[11px] text-muted-foreground">
            Showing {filteredResults.length} of {result.results.length} results
            {filterResult && (
              <button
                className="ml-2 text-primary hover:underline"
                onClick={() => setFilterResult("")}
              >
                Clear filter
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

function LiveTestResultRow({
  item,
  index,
  isExpanded,
  onToggle,
}: {
  item: LiveTestResultItem
  index: number
  isExpanded: boolean
  onToggle: () => void
}) {
  return (
    <>
      <tr
        className={`border-b border-border hover:bg-muted/10 cursor-pointer transition-colors ${
          index % 2 === 0 ? "" : "bg-muted/5"
        }`}
        onClick={onToggle}
      >
        <td className="px-3 py-2">
          {item.details.length > 0 ? (
            isExpanded ? (
              <ChevronUp className="h-3 w-3 text-muted-foreground" />
            ) : (
              <ChevronDown className="h-3 w-3 text-muted-foreground" />
            )
          ) : null}
        </td>
        <td className="px-3 py-2 font-mono text-foreground max-w-[180px] truncate" title={item.asset_external_id}>
          {item.asset_external_id}
        </td>
        <td className="px-3 py-2 text-muted-foreground">
          {item.asset_type}
        </td>
        <td className="px-3 py-2 font-mono text-foreground">
          <div className="flex flex-col">
            <span className="truncate max-w-[120px]" title={item.signal_code}>{item.signal_code}</span>
            {item.signal_name && (
              <span className="text-[10px] text-muted-foreground truncate max-w-[120px]">{item.signal_name}</span>
            )}
          </div>
        </td>
        <td className="px-3 py-2">
          <Badge variant="outline" className={`text-[10px] gap-1 ${resultBadgeStyle(item.result)}`}>
            <ResultIcon result={item.result} />
            {item.result}
          </Badge>
        </td>
        <td className="px-3 py-2 text-muted-foreground max-w-[220px] truncate" title={item.summary}>
          {item.summary || "\u2014"}
        </td>
        <td className="px-3 py-2 text-right text-muted-foreground tabular-nums">
          {item.execution_time_ms}ms
        </td>
      </tr>
      {isExpanded && item.details.length > 0 && (
        <tr className="border-b border-border">
          <td colSpan={7} className="px-6 py-3 bg-muted/10">
            <div className="space-y-1.5">
              <p className="text-[11px] font-medium text-muted-foreground mb-1.5">Detail Checks</p>
              {item.details.map((detail, dIdx) => (
                <div key={dIdx} className="flex items-start gap-2 text-[11px]">
                  <ResultIcon result={String(detail.status ?? detail.result ?? "unknown")} />
                  <span className="font-medium text-foreground">{String(detail.check ?? detail.name ?? `Check ${dIdx + 1}`)}</span>
                  <span className="text-muted-foreground">{String(detail.message ?? detail.description ?? "")}</span>
                </div>
              ))}
            </div>
          </td>
        </tr>
      )}
    </>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Main Page
// ─────────────────────────────────────────────────────────────────────────────

export default function LiveSessionsPage() {
  const { selectedOrgId, selectedWorkspaceId, ready } = useSandboxOrgWorkspace()

  const [sessions, setSessions] = useState<LiveSessionResponse[]>([])
  const [connectors, setConnectors] = useState<ConnectorInstanceResponse[]>([])
  const [signals, setSignals] = useState<SignalResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [statusFilter, setStatusFilter] = useState("")
  const [showStart, setShowStart] = useState(false)
  const [showLiveTest, setShowLiveTest] = useState(false)
  const [liveTestResult, setLiveTestResult] = useState<LiveTestResponse | null>(null)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const load = useCallback(async () => {
    if (!selectedOrgId) return
    setError(null)
    try {
      const [sRes, cRes, sigRes] = await Promise.all([
        listLiveSessions({ org_id: selectedOrgId, session_status: statusFilter || undefined }),
        listConnectors({ org_id: selectedOrgId }),
        listSignals({ org_id: selectedOrgId }),
      ])
      setSessions(sRes.items)
      setConnectors(cRes.items)
      setSignals(sigRes.items)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load live sessions")
    }
  }, [selectedOrgId, statusFilter])

  useEffect(() => {
    if (!ready) return
    setLoading(true)
    load().finally(() => setLoading(false))
  }, [ready, load])

  // Poll every 10s when there are active sessions
  useEffect(() => {
    const hasActive = sessions.some((s) => s.session_status === "active")
    if (hasActive) {
      pollRef.current = setInterval(() => load(), 10000)
    } else {
      if (pollRef.current) clearInterval(pollRef.current)
    }
    return () => { if (pollRef.current) clearInterval(pollRef.current) }
  }, [sessions, load])

  const activeSessions = sessions.filter((s) => s.session_status === "active")
  const pausedSessions = sessions.filter((s) => s.session_status === "paused")

  function handleLiveTestClose(result?: LiveTestResponse) {
    setShowLiveTest(false)
    if (result) {
      setLiveTestResult(result)
    }
  }

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="h-8 w-48 bg-muted rounded animate-pulse" />
        <div className="h-24 bg-muted rounded-xl animate-pulse" />
        <div className="h-24 bg-muted rounded-xl animate-pulse" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <Button variant="ghost" size="sm" asChild className="gap-1.5 -ml-2 text-muted-foreground hover:text-foreground">
        <Link href="/sandbox"><ArrowLeft className="h-4 w-4" />Sandbox</Link>
      </Button>

      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-4">
          <div className="rounded-xl bg-green-500/10 p-3 shrink-0">
            <Activity className="h-6 w-6 text-green-500" />
          </div>
          <div>
            <h2 className="text-2xl font-semibold text-foreground">Live Sessions</h2>
            <p className="text-sm text-muted-foreground mt-1">
              Stream live data from connectors and evaluate signals in real-time.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <Button variant="outline" size="sm" onClick={async () => { setRefreshing(true); await load(); setRefreshing(false); }} disabled={refreshing} className="gap-1.5">
            {refreshing ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <RefreshCw className="h-3.5 w-3.5" />}
            {refreshing ? "Refreshing..." : "Refresh"}
          </Button>
          {connectors.length > 0 && selectedWorkspaceId && (
            <>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowLiveTest(true)}
                className="gap-1.5"
              >
                <FlaskConical className="h-3.5 w-3.5" />
                New Live Test
              </Button>
              <Button size="sm" onClick={() => setShowStart(true)} className="gap-1.5">
                <Plus className="h-3.5 w-3.5" />
                New Session
              </Button>
            </>
          )}
        </div>
      </div>

      {/* Live test results (shown above sessions when present) */}
      {liveTestResult && (
        <LiveTestResultsView
          result={liveTestResult}
          connectors={connectors}
          onClose={() => setLiveTestResult(null)}
        />
      )}

      {/* KPI cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="flex items-center gap-3 rounded-xl border border-l-[3px] border-l-primary bg-card px-4 py-3">
          <div className="shrink-0 rounded-lg p-2 bg-muted"><Activity className="h-4 w-4 text-muted-foreground" /></div>
          <div><span className="text-2xl font-bold text-foreground tabular-nums">{sessions.length}</span><span className="text-[11px] text-muted-foreground mt-0.5 block">Total</span></div>
        </div>
        <div className="flex items-center gap-3 rounded-xl border border-l-[3px] border-l-green-500 bg-card px-4 py-3">
          <div className="shrink-0 rounded-lg p-2 bg-muted"><CheckCircle2 className="h-4 w-4 text-green-500" /></div>
          <div><span className="text-2xl font-bold text-green-500 tabular-nums">{activeSessions.length}</span><span className="text-[11px] text-muted-foreground mt-0.5 block">Active</span></div>
        </div>
        <div className="flex items-center gap-3 rounded-xl border border-l-[3px] border-l-amber-500 bg-card px-4 py-3">
          <div className="shrink-0 rounded-lg p-2 bg-muted"><AlertCircle className="h-4 w-4 text-amber-500" /></div>
          <div><span className="text-2xl font-bold text-amber-500 tabular-nums">{pausedSessions.length}</span><span className="text-[11px] text-muted-foreground mt-0.5 block">Paused</span></div>
        </div>
        <div className="flex items-center gap-3 rounded-xl border border-l-[3px] border-l-blue-500 bg-card px-4 py-3">
          <div className="shrink-0 rounded-lg p-2 bg-muted"><Save className="h-4 w-4 text-blue-500" /></div>
          <div><span className="text-2xl font-bold text-blue-500 tabular-nums">{sessions.filter((s) => s.session_status === "saved").length}</span><span className="text-[11px] text-muted-foreground mt-0.5 block">Saved</span></div>
        </div>
      </div>

      {/* Status filter */}
      <div className="flex items-center gap-2 flex-wrap">
        {["", "active", "paused", "stopped", "expired", "saved"].map((s) => (
          <button
            key={s}
            onClick={() => setStatusFilter(s)}
            className={`px-3 py-1 rounded-full text-xs border transition-colors ${
              statusFilter === s
                ? "bg-foreground text-background border-foreground"
                : "border-border text-muted-foreground hover:border-foreground/30 hover:text-foreground"
            }`}
          >
            {s === "" ? "All" : s.charAt(0).toUpperCase() + s.slice(1)}
          </button>
        ))}
      </div>

      {/* Error */}
      {error && (
        <div className="flex items-center justify-between rounded-xl border border-red-500/30 bg-red-500/5 px-4 py-3">
          <p className="text-sm text-red-500">{error}</p>
          <button onClick={() => setError(null)}><X className="h-4 w-4 text-red-500" /></button>
        </div>
      )}

      {/* No connector warning */}
      {!selectedWorkspaceId && (
        <div className="rounded-xl border border-amber-500/30 bg-amber-500/5 px-4 py-3 text-sm text-amber-500">
          Select a workspace to start a live session.
        </div>
      )}

      {/* Sessions list */}
      {sessions.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-border flex flex-col items-center gap-3 py-16 text-center">
          <Activity className="h-10 w-10 text-muted-foreground/30" />
          <div>
            <p className="text-sm font-medium text-foreground mb-1">No live sessions</p>
            <p className="text-xs text-muted-foreground">
              {statusFilter ? `No ${statusFilter} sessions found.` : "Start a session to stream real-time data from a connector."}
            </p>
          </div>
          {connectors.length > 0 && selectedWorkspaceId && (
            <div className="flex items-center gap-2 mt-2">
              <Button size="sm" variant="outline" onClick={() => setShowLiveTest(true)} className="gap-1.5">
                <FlaskConical className="h-3.5 w-3.5" />
                Run Live Test
              </Button>
              <Button size="sm" onClick={() => setShowStart(true)} className="gap-1.5">
                <Play className="h-3.5 w-3.5" />
                Start Session
              </Button>
            </div>
          )}
          {connectors.length === 0 && (
            <Button size="sm" variant="outline" asChild className="mt-2">
              <Link href="/sandbox/connectors">
                <Database className="h-3.5 w-3.5 mr-1.5" />
                Add a Connector First
              </Link>
            </Button>
          )}
        </div>
      ) : (
        <div className="space-y-3">
          {sessions.map((s) => (
            <SessionCard key={s.id} session={s} onAction={load} orgId={selectedOrgId} />
          ))}
        </div>
      )}

      {/* Start dialog */}
      {showStart && selectedOrgId && selectedWorkspaceId && (
        <StartSessionDialog
          orgId={selectedOrgId}
          workspaceId={selectedWorkspaceId}
          connectors={connectors}
          signals={signals}
          onStarted={() => { setShowStart(false); load() }}
          onClose={() => setShowStart(false)}
        />
      )}

      {/* Live test dialog */}
      {showLiveTest && selectedOrgId && selectedWorkspaceId && (
        <LiveTestDialog
          orgId={selectedOrgId}
          workspaceId={selectedWorkspaceId}
          connectors={connectors}
          signals={signals}
          onClose={handleLiveTestClose}
        />
      )}
    </div>
  )
}
