"use client"

import { useEffect, useState, useCallback } from "react"
import {
  Button,
  Input,
  Label,
  Badge,
  Separator,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@kcontrol/ui"
import {
  Play,
  Search,
  RefreshCw,
  Loader2,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Minus,
  Eye,
  X,
  Timer,
  ArrowUpDown,
  Copy,
  Activity,
} from "lucide-react"

// Copy button with visual feedback
function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    const success = await copyToClipboard(text)
    if (success) {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  return (
    <button
      onClick={handleCopy}
      className={`text-muted-foreground hover:text-foreground transition-colors shrink-0 p-1 hover:bg-muted rounded ${copied ? "text-green-500" : ""}`}
      title={copied ? "Copied!" : "Copy"}
    >
      {copied ? <CheckCircle2 className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
    </button>
  )
}

import {
  listRuns,
  listSignals,
  listDatasets,
  executeSignal,
  getRun,
} from "@/lib/api/sandbox"
import { copyToClipboard } from "@/lib/utils/sandbox-helpers"
import { useSandboxOrgWorkspace } from "@/lib/context/SandboxOrgWorkspaceContext"
import type {
  RunResponse,
  SignalResponse,
  DatasetResponse,
} from "@/lib/api/sandbox"

// ─────────────────────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────────────────────

const RESULT_STYLES: Record<string, { bg: string; icon: typeof CheckCircle2 }> = {
  pass: { bg: "bg-green-500/10 text-green-500 border-green-500/30", icon: CheckCircle2 },
  fail: { bg: "bg-red-500/10 text-red-500 border-red-500/30", icon: XCircle },
  warning: { bg: "bg-yellow-500/10 text-yellow-600 dark:text-yellow-400 border-yellow-500/30", icon: AlertTriangle },
  error: { bg: "bg-muted text-muted-foreground", icon: Minus },
  skipped: { bg: "bg-muted text-muted-foreground", icon: Minus },
}

const STATUS_STYLES: Record<string, string> = {
  running: "bg-blue-500/10 text-blue-500 border-blue-500/30",
  completed: "bg-green-500/10 text-green-500 border-green-500/30",
  failed: "bg-red-500/10 text-red-500 border-red-500/30",
  queued: "bg-muted text-muted-foreground",
  cancelled: "bg-muted text-muted-foreground",
}

function borderForResult(code: string | null | undefined): string {
  if (!code) return "border-l-primary"
  if (code === "pass") return "border-l-green-500"
  if (code === "fail" || code === "failed") return "border-l-red-500"
  if (code === "warning" || code === "warn") return "border-l-amber-500"
  if (code === "running" || code === "in_progress" || code === "pending") return "border-l-blue-500"
  return "border-l-primary"
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  })
}

function formatMs(ms: number | null): string {
  if (ms === null) return "--"
  if (ms < 1000) return `${ms}ms`
  return `${(ms / 1000).toFixed(2)}s`
}

// ─────────────────────────────────────────────────────────────────────────────
// Execute Signal Dialog
// ─────────────────────────────────────────────────────────────────────────────

function ExecuteSignalDialog({
  open,
  orgId,
  signals,
  datasets,
  onExecuted,
  onClose,
}: {
  open: boolean
  orgId: string
  signals: SignalResponse[]
  datasets: DatasetResponse[]
  onExecuted: () => void
  onClose: () => void
}) {
  const [signalId, setSignalId] = useState("")
  const [datasetId, setDatasetId] = useState("")
  const [signalSearch, setSignalSearch] = useState("")
  const [datasetSearch, setDatasetSearch] = useState("")
  const [executing, setExecuting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<RunResponse | null>(null)

  useEffect(() => {
    if (open) {
      setSignalId("")
      setDatasetId("")
      setSignalSearch("")
      setDatasetSearch("")
      setExecuting(false)
      setError(null)
      setResult(null)
    }
  }, [open])

  const filteredSignals = signals.filter((s) => {
    if (!signalSearch) return true
    const q = signalSearch.toLowerCase()
    return (
      s.signal_code.toLowerCase().includes(q) ||
      (s.name && s.name.toLowerCase().includes(q))
    )
  })

  const filteredDatasets = datasets.filter((d) => {
    if (!datasetSearch) return true
    const q = datasetSearch.toLowerCase()
    return (
      d.dataset_code.toLowerCase().includes(q) ||
      (d.name && d.name.toLowerCase().includes(q))
    )
  })

  async function handleExecute() {
    if (!signalId || !datasetId) {
      setError("Select both a signal and a dataset.")
      return
    }
    setExecuting(true)
    setError(null)
    setResult(null)
    try {
      const run = await executeSignal(orgId, { signal_id: signalId, dataset_id: datasetId })
      setResult(run)
      onExecuted()
    } catch (e) {
      setError(e instanceof Error ? e.message : "Execution failed")
    } finally {
      setExecuting(false)
    }
  }

  const resultStyle = result?.result_code
    ? RESULT_STYLES[result.result_code] ?? RESULT_STYLES.error
    : null
  const ResultIcon = resultStyle?.icon ?? Minus

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) onClose() }}>
      <DialogContent className="sm:max-w-lg max-h-[85vh] flex flex-col">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-purple-500/10 p-2.5 shrink-0">
              <Play className="h-4 w-4 text-purple-500" />
            </div>
            <div>
              <DialogTitle>Execute Signal</DialogTitle>
              <DialogDescription className="text-xs">
                Run a signal against a dataset and view the result.
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>
        <Separator className="my-2" />

        <div className="space-y-4 overflow-y-auto pr-2" style={{ scrollbarWidth: 'thin' }}>
          {/* Signal selector */}
          <div>
            <Label className="text-xs font-medium">Signal</Label>
            <Input
              placeholder="Search signals..."
              value={signalSearch}
              onChange={(e) => setSignalSearch(e.target.value)}
              className="h-8 text-xs mt-1"
            />
            <select
              className="w-full mt-1.5 rounded-md border border-input bg-background px-3 py-2 text-sm"
              value={signalId}
              onChange={(e) => setSignalId(e.target.value)}
            >
              <option value="">-- Select Signal --</option>
              {filteredSignals.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name || s.signal_code} ({s.signal_code})
                </option>
              ))}
            </select>
          </div>

          {/* Dataset selector */}
          <div>
            <Label className="text-xs font-medium">Dataset</Label>
            <Input
              placeholder="Search datasets..."
              value={datasetSearch}
              onChange={(e) => setDatasetSearch(e.target.value)}
              className="h-8 text-xs mt-1"
            />
            <select
              className="w-full mt-1.5 rounded-md border border-input bg-background px-3 py-2 text-sm"
              value={datasetId}
              onChange={(e) => setDatasetId(e.target.value)}
            >
              <option value="">-- Select Dataset --</option>
              {filteredDatasets.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name || d.dataset_code} (v{d.version_number})
                </option>
              ))}
            </select>
          </div>

          {/* Execute button */}
          <Button
            size="sm"
            onClick={handleExecute}
            disabled={executing || !signalId || !datasetId}
            className="w-full gap-1.5"
          >
            {executing ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <Play className="h-3.5 w-3.5" />
            )}
            {executing ? "Executing..." : "Execute"}
          </Button>

          {/* Error */}
          {error && (
            <div className="rounded-lg border border-red-500/30 bg-red-500/5 px-3 py-2">
              <p className="text-xs text-red-500">{error}</p>
            </div>
          )}

          {/* Result */}
          {result && (
            <div className="space-y-3 rounded-xl border border-border bg-muted/10 p-4">
              <div className="flex items-center gap-2">
                <ResultIcon className="h-4 w-4" />
                <Badge
                  variant="outline"
                  className={`text-xs ${resultStyle?.bg ?? ""}`}
                >
                  {result.result_code ?? "unknown"}
                </Badge>
                {result.execution_time_ms !== null && (
                  <span className="text-xs text-muted-foreground ml-auto flex items-center gap-1">
                    <Timer className="h-3 w-3" />
                    {formatMs(result.execution_time_ms)}
                  </span>
                )}
              </div>
              {result.result_summary && (
                <p className="text-sm text-foreground break-words">{result.result_summary}</p>
              )}
              {!!result.result_details && (
                <div className="rounded-lg border border-border bg-slate-950 p-3 max-h-56 overflow-y-auto" style={{ scrollbarWidth: 'thin', scrollbarColor: '#666 transparent' }}>
                  <pre className="text-[10px] font-mono text-slate-300 whitespace-pre-wrap break-all m-0">
{JSON.stringify(result.result_details, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          )}
        </div>

        <DialogFooter className="mt-4 shrink-0">
          <Button variant="outline" size="sm" onClick={onClose}>
            Close
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Run Detail Dialog
// ─────────────────────────────────────────────────────────────────────────────

function RunDetailDialog({
  open,
  run,
  onClose,
}: {
  open: boolean
  run: RunResponse | null
  onClose: () => void
}) {
  const [detail, setDetail] = useState<RunResponse | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (open && run) {
      setLoading(true)
      getRun(run.id)
        .then(setDetail)
        .catch(() => setDetail(run))
        .finally(() => setLoading(false))
    } else {
      setDetail(null)
    }
  }, [open, run])

  const r = detail || run
  const resultStyle = r?.result_code
    ? RESULT_STYLES[r.result_code] ?? RESULT_STYLES.error
    : null
  const ResultIcon = resultStyle?.icon ?? Minus

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) onClose() }}>
      <DialogContent className="sm:max-w-lg max-h-[85vh] flex flex-col">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-purple-500/10 p-2.5 shrink-0">
              <Eye className="h-4 w-4 text-purple-500" />
            </div>
            <div className="min-w-0">
              <DialogTitle className="truncate">Run Detail</DialogTitle>
              <DialogDescription className="text-xs truncate">
                {r?.signal_name || r?.signal_code} — {r?.id?.slice(0, 8)}...
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>
        <Separator className="my-2" />

        {loading && (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
          </div>
        )}

        {r && !loading && (
          <div className="space-y-4 overflow-y-auto pr-2" style={{ scrollbarWidth: 'thin' }}>
            {/* Status + Result */}
            <div className="flex gap-3">
              <div className="flex-1 rounded-lg border border-border bg-muted/10 p-3 min-w-0">
                <p className="text-[10px] text-muted-foreground uppercase tracking-wider mb-1.5">
                  Execution Status
                </p>
                <Badge
                  variant="outline"
                  className={`text-xs ${STATUS_STYLES[r.execution_status_code] ?? ""}`}
                >
                  {r.execution_status_name}
                </Badge>
              </div>
              <div className="flex-1 rounded-lg border border-border bg-muted/10 p-3 min-w-0">
                <p className="text-[10px] text-muted-foreground uppercase tracking-wider mb-1.5">
                  Result
                </p>
                <div className="flex items-center gap-1.5">
                  <ResultIcon className="h-3.5 w-3.5 shrink-0" />
                  <Badge
                    variant="outline"
                    className={`text-xs ${resultStyle?.bg ?? ""}`}
                  >
                    {r.result_code ?? "pending"}
                  </Badge>
                </div>
              </div>
            </div>

            {/* Timing */}
            <div className="grid grid-cols-3 gap-2">
              <div className="rounded-lg border border-border bg-muted/10 p-2.5 min-w-0">
                <p className="text-[10px] text-muted-foreground uppercase tracking-wider mb-1">
                  Time
                </p>
                <p className="text-sm font-semibold text-foreground truncate">
                  {formatMs(r.execution_time_ms)}
                </p>
              </div>
              <div className="rounded-lg border border-border bg-muted/10 p-2.5 min-w-0">
                <p className="text-[10px] text-muted-foreground uppercase tracking-wider mb-1">
                  Started
                </p>
                <p className="text-xs text-foreground truncate">
                  {r.started_at ? formatDate(r.started_at) : "--"}
                </p>
              </div>
              <div className="rounded-lg border border-border bg-muted/10 p-2.5 min-w-0">
                <p className="text-[10px] text-muted-foreground uppercase tracking-wider mb-1">
                  Completed
                </p>
                <p className="text-xs text-foreground truncate">
                  {r.completed_at ? formatDate(r.completed_at) : "--"}
                </p>
              </div>
            </div>

            {/* Summary */}
            {r.result_summary && (
              <div>
                <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1.5">
                  Summary
                </h4>
                <p className="text-sm text-foreground rounded-lg border border-border bg-muted/10 p-3 break-words">
                  {r.result_summary}
                </p>
              </div>
            )}

            {/* Result details JSON */}
            {!!r.result_details && (
              <div>
                <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1.5">
                  Result Details
                </h4>
                <div className="rounded-lg border border-border bg-slate-950 p-3 max-h-72 overflow-y-auto" style={{ scrollbarWidth: 'thin', scrollbarColor: '#666 transparent' }}>
                  <pre className="text-[10px] font-mono text-slate-300 whitespace-pre-wrap break-all m-0">
{JSON.stringify(r.result_details, null, 2)}
                  </pre>
                </div>
              </div>
            )}

            {/* Identifiers */}
            <div>
              <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1.5">
                Identifiers
              </h4>
                <div className="space-y-2">
                <div className="rounded-lg border border-border bg-muted/10 px-3 py-2 flex items-center gap-2 min-w-0">
                  <span className="text-xs text-muted-foreground shrink-0">Run ID:</span>
                  <code className="text-xs font-mono text-foreground truncate flex-1">{r.id}</code>
                  <CopyButton text={r.id} />
                </div>
                <div className="rounded-lg border border-border bg-muted/10 px-3 py-2 flex items-center gap-2 min-w-0">
                  <span className="text-xs text-muted-foreground shrink-0">Signal:</span>
                  <code className="text-xs font-mono text-foreground truncate flex-1">{r.signal_code}</code>
                </div>
                {r.dataset_id && (
                  <div className="rounded-lg border border-border bg-muted/10 px-3 py-2 flex items-center gap-2 min-w-0">
                    <span className="text-xs text-muted-foreground shrink-0">Dataset:</span>
                    <code className="text-xs font-mono text-foreground truncate flex-1">{r.dataset_id}</code>
                  </div>
                )}
                {r.live_session_id && (
                  <div className="rounded-lg border border-border bg-muted/10 px-3 py-2 flex items-center gap-2 min-w-0">
                    <span className="text-xs text-muted-foreground shrink-0">Session:</span>
                    <code className="text-xs font-mono text-foreground truncate flex-1">{r.live_session_id}</code>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        <DialogFooter className="mt-4 shrink-0">
          <Button variant="outline" size="sm" onClick={onClose}>
            Close
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Page
// ─────────────────────────────────────────────────────────────────────────────

export default function SandboxRunsPage() {
  const { selectedOrgId, ready } = useSandboxOrgWorkspace()
  const [runs, setRuns] = useState<RunResponse[]>([])
  const [signals, setSignals] = useState<SignalResponse[]>([])
  const [datasets, setDatasets] = useState<DatasetResponse[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Filters (debounced search)
  const [searchInput, setSearchInput] = useState("")
  const [searchQuery, setSearchQuery] = useState("")
  useEffect(() => {
    const timer = setTimeout(() => setSearchQuery(searchInput), 300)
    return () => clearTimeout(timer)
  }, [searchInput])

  const [filterSignalId, setFilterSignalId] = useState("")
  const [filterResult, setFilterResult] = useState("")

  // Sort
  const [sortField, setSortField] = useState<"created_at" | "execution_time_ms">("created_at")
  const [sortAsc, setSortAsc] = useState(false)

  // Dialogs
  const [showExecute, setShowExecute] = useState(false)
  const [detailTarget, setDetailTarget] = useState<RunResponse | null>(null)

  const fetchData = useCallback(async () => {
    if (!selectedOrgId) return
    setLoading(true)
    setError(null)
    try {
      const params: Record<string, any> = { org_id: selectedOrgId }
      if (filterSignalId) params.signal_id = filterSignalId
      if (filterResult) params.result_code = filterResult

      const [rRes, sRes, dRes] = await Promise.all([
        listRuns(params),
        listSignals({ org_id: selectedOrgId }),
        listDatasets(selectedOrgId),
      ])
      setRuns(rRes.items)
      setTotal(rRes.total)
      setSignals(sRes.items)
      setDatasets(dRes.items)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load data")
    } finally {
      setLoading(false)
    }
  }, [filterSignalId, filterResult, selectedOrgId])

  useEffect(() => {
    if (ready) fetchData()
  }, [fetchData, ready])

  // Sort and filter
  const sortedRuns = [...runs]
    .filter((r) => {
      if (!searchQuery) return true
      const q = searchQuery.toLowerCase()
      return (
        r.signal_code.toLowerCase().includes(q) ||
        (r.signal_name && r.signal_name.toLowerCase().includes(q)) ||
        (r.result_summary && r.result_summary.toLowerCase().includes(q))
      )
    })
    .sort((a, b) => {
      let cmp = 0
      if (sortField === "created_at") {
        cmp = new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
      } else {
        cmp = (a.execution_time_ms ?? 0) - (b.execution_time_ms ?? 0)
      }
      return sortAsc ? cmp : -cmp
    })

  function toggleSort(field: "created_at" | "execution_time_ms") {
    if (sortField === field) {
      setSortAsc(!sortAsc)
    } else {
      setSortField(field)
      setSortAsc(false)
    }
  }

  // KPI derived counts
  const passCount = runs.filter((r) => r.result_code === "pass").length
  const failCount = runs.filter((r) => r.result_code === "fail").length
  const warnCount = runs.filter((r) => r.result_code === "warning").length

  const hasActiveFilters = !!(filterSignalId || filterResult || searchQuery)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-4">
          <div className="rounded-xl bg-purple-500/10 p-3 shrink-0">
            <Play className="h-6 w-6 text-purple-500" />
          </div>
          <div className="flex flex-col gap-1">
            <h2 className="text-2xl font-semibold text-foreground">Sandbox Runs</h2>
            <p className="text-sm text-muted-foreground">
              Execute signals against datasets and review results.
            </p>
          </div>
        </div>
        <Button size="sm" className="gap-1.5 shrink-0" onClick={() => setShowExecute(true)}>
          <Play className="h-3.5 w-3.5" /> Execute Signal
        </Button>
      </div>

      {/* KPI stat cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {/* Total */}
        <div className="relative flex items-center gap-3 rounded-xl border border-l-[3px] border-l-primary bg-card px-4 py-3">
          <div className="shrink-0 rounded-lg p-2 bg-muted">
            <Activity className="h-4 w-4 text-muted-foreground" />
          </div>
          <div className="min-w-0">
            <span className="text-2xl font-bold tabular-nums leading-none text-foreground">{total}</span>
            <span className="text-[11px] text-muted-foreground mt-0.5 block truncate">Total Runs</span>
          </div>
        </div>
        {/* Pass */}
        <div className="relative flex items-center gap-3 rounded-xl border border-l-[3px] border-l-green-500 bg-card px-4 py-3">
          <div className="shrink-0 rounded-lg p-2 bg-green-500/10">
            <CheckCircle2 className="h-4 w-4 text-green-500" />
          </div>
          <div className="min-w-0">
            <span className="text-2xl font-bold tabular-nums leading-none text-green-500">{passCount}</span>
            <span className="text-[11px] text-muted-foreground mt-0.5 block truncate">Passed</span>
          </div>
        </div>
        {/* Fail */}
        <div className="relative flex items-center gap-3 rounded-xl border border-l-[3px] border-l-red-500 bg-card px-4 py-3">
          <div className="shrink-0 rounded-lg p-2 bg-red-500/10">
            <XCircle className="h-4 w-4 text-red-500" />
          </div>
          <div className="min-w-0">
            <span className="text-2xl font-bold tabular-nums leading-none text-red-500">{failCount}</span>
            <span className="text-[11px] text-muted-foreground mt-0.5 block truncate">Failed</span>
          </div>
        </div>
        {/* Warning */}
        <div className="relative flex items-center gap-3 rounded-xl border border-l-[3px] border-l-amber-500 bg-card px-4 py-3">
          <div className="shrink-0 rounded-lg p-2 bg-amber-500/10">
            <AlertTriangle className="h-4 w-4 text-amber-500" />
          </div>
          <div className="min-w-0">
            <span className="text-2xl font-bold tabular-nums leading-none text-amber-500">{warnCount}</span>
            <span className="text-[11px] text-muted-foreground mt-0.5 block truncate">Warnings</span>
          </div>
        </div>
      </div>

      {/* Filter bar */}
      <div className="rounded-xl border border-border bg-card px-4 py-3">
        <div className="flex flex-wrap items-center gap-3 overflow-x-auto">
          <div className="relative flex-1 min-w-[200px] max-w-xs">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
            <Input
              placeholder="Search runs..."
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              className="h-9 pl-9 text-sm"
            />
          </div>

          <select
            className="h-9 rounded-md border border-input bg-background px-3 text-sm text-foreground shrink-0"
            value={filterSignalId}
            onChange={(e) => setFilterSignalId(e.target.value)}
          >
            <option value="">All Signals</option>
            {signals.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name || s.signal_code}
              </option>
            ))}
          </select>

          <select
            className="h-9 rounded-md border border-input bg-background px-3 text-sm text-foreground shrink-0"
            value={filterResult}
            onChange={(e) => setFilterResult(e.target.value)}
          >
            <option value="">All Results</option>
            <option value="pass">Pass</option>
            <option value="fail">Fail</option>
            <option value="warning">Warning</option>
            <option value="error">Error</option>
          </select>

          <Button variant="ghost" size="sm" className="h-9 gap-1.5 shrink-0" onClick={fetchData}>
            <RefreshCw className="h-3.5 w-3.5" /> Refresh
          </Button>

          {total > 0 && (
            <span className="text-xs text-muted-foreground ml-auto whitespace-nowrap shrink-0">
              {sortedRuns.length} of {total} runs
            </span>
          )}
        </div>

        {/* Active filter chips */}
        {hasActiveFilters && (
          <div className="flex flex-wrap items-center gap-2 mt-3 pt-3 border-t border-border">
            <span className="text-[11px] text-muted-foreground">Filters:</span>
            {searchQuery && (
              <span className="inline-flex items-center gap-1 rounded-full border border-border bg-muted/40 px-2.5 py-0.5 text-[11px] text-foreground">
                Search: {searchQuery}
                <button onClick={() => { setSearchInput(""); setSearchQuery("") }} className="ml-1 text-muted-foreground hover:text-foreground">
                  <X className="h-3 w-3" />
                </button>
              </span>
            )}
            {filterSignalId && (
              <span className="inline-flex items-center gap-1 rounded-full border border-border bg-muted/40 px-2.5 py-0.5 text-[11px] text-foreground">
                Signal: {signals.find((s) => s.id === filterSignalId)?.name || signals.find((s) => s.id === filterSignalId)?.signal_code || filterSignalId}
                <button onClick={() => setFilterSignalId("")} className="ml-1 text-muted-foreground hover:text-foreground">
                  <X className="h-3 w-3" />
                </button>
              </span>
            )}
            {filterResult && (
              <span className="inline-flex items-center gap-1 rounded-full border border-border bg-muted/40 px-2.5 py-0.5 text-[11px] text-foreground">
                Result: {filterResult}
                <button onClick={() => setFilterResult("")} className="ml-1 text-muted-foreground hover:text-foreground">
                  <X className="h-3 w-3" />
                </button>
              </span>
            )}
            <button
              onClick={() => { setSearchInput(""); setSearchQuery(""); setFilterSignalId(""); setFilterResult("") }}
              className="text-[11px] text-muted-foreground hover:text-foreground underline underline-offset-2 ml-1"
            >
              Clear all
            </button>
          </div>
        )}
      </div>

      {/* Error */}
      {error && (
        <div className="rounded-xl border border-red-500/30 bg-red-500/5 px-4 py-3">
          <p className="text-sm text-red-500">{error}</p>
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
          <span className="ml-2 text-sm text-muted-foreground">Loading runs...</span>
        </div>
      )}

      {/* Empty state */}
      {!loading && sortedRuns.length === 0 && (
        <div className="rounded-xl border border-border bg-muted/20 px-5 py-12 text-center">
          <Play className="h-8 w-8 text-muted-foreground mx-auto mb-3" />
          <p className="text-sm font-medium text-foreground mb-1">No runs found</p>
          <p className="text-xs text-muted-foreground mb-4">
            {hasActiveFilters
              ? "Try adjusting your filters."
              : "Execute your first signal to see results here."}
          </p>
          {!hasActiveFilters && (
            <Button size="sm" className="gap-1.5" onClick={() => setShowExecute(true)}>
              <Play className="h-3.5 w-3.5" /> Execute Signal
            </Button>
          )}
        </div>
      )}

      {/* Runs table */}
      {!loading && sortedRuns.length > 0 && (
        <div className="rounded-xl border border-border overflow-hidden">
          {/* Table container with horizontal scroll */}
          <div className="overflow-x-auto scrollbar-thin">
            <table className="w-full min-w-[650px]">
              <thead>
                <tr className="bg-muted/30 border-b border-border">
                  <th className="text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider px-4 py-2.5">Signal</th>
                  <th className="text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider px-2 py-2.5">Result</th>
                  <th className="text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider px-2 py-2.5">
                    <button className="flex items-center gap-1 hover:text-foreground transition-colors" onClick={() => toggleSort("execution_time_ms")}>
                      Time <ArrowUpDown className="h-3 w-3" />
                    </button>
                  </th>
                  <th className="text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider px-2 py-2.5">Summary</th>
                  <th className="text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider px-2 py-2.5">
                    <button className="flex items-center gap-1 hover:text-foreground transition-colors" onClick={() => toggleSort("created_at")}>
                      Timestamp <ArrowUpDown className="h-3 w-3" />
                    </button>
                  </th>
                  <th className="text-right text-[10px] font-semibold text-muted-foreground uppercase tracking-wider px-2 py-2.5">Action</th>
                </tr>
              </thead>
              <tbody>
                {sortedRuns.map((run) => {
                  const style = run.result_code
                    ? RESULT_STYLES[run.result_code] ?? RESULT_STYLES.error
                    : RESULT_STYLES.error
                  const ResultIcon = style.icon
                  const lBorder = borderForResult(run.result_code ?? run.execution_status_code)

                  return (
                    <tr
                      key={run.id}
                      className={`border-b border-border hover:bg-muted/10 transition-colors border-l-[3px] ${lBorder}`}
                    >
                      <td className="px-4 py-3 min-w-0">
                        <p className="text-sm font-medium text-foreground truncate max-w-[200px] block">
                          {run.signal_name || run.signal_code}
                        </p>
                        <p className="text-[10px] text-muted-foreground font-mono truncate max-w-[200px] block">
                          {run.signal_code}
                        </p>
                      </td>
                      <td className="px-2 py-3">
                        <div className="flex items-center gap-1">
                          <ResultIcon className="h-3.5 w-3.5 shrink-0" />
                          <Badge variant="outline" className={`text-[10px] ${style.bg}`}>
                            {run.result_code ?? "pending"}
                          </Badge>
                        </div>
                      </td>
                      <td className="px-2 py-3">
                        <span className="text-xs text-muted-foreground font-mono">
                          {formatMs(run.execution_time_ms)}
                        </span>
                      </td>
                      <td className="px-2 py-3">
                        <p className="text-xs text-muted-foreground truncate max-w-[150px] block">
                          {run.result_summary || "--"}
                        </p>
                      </td>
                      <td className="px-2 py-3">
                        <span className="text-[11px] text-muted-foreground whitespace-nowrap">
                          {run.started_at ? formatDate(run.started_at) : formatDate(run.created_at)}
                        </span>
                      </td>
                      <td className="px-2 py-3 text-right">
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-7 w-7 p-0 text-muted-foreground hover:text-foreground"
                          onClick={() => setDetailTarget(run)}
                        >
                          <Eye className="h-3.5 w-3.5" />
                        </Button>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Dialogs */}
      {selectedOrgId && (
        <ExecuteSignalDialog
          open={showExecute}
          orgId={selectedOrgId}
          signals={signals}
          datasets={datasets}
          onExecuted={fetchData}
          onClose={() => setShowExecute(false)}
        />
      )}
      <RunDetailDialog
        open={!!detailTarget}
        run={detailTarget}
        onClose={() => setDetailTarget(null)}
      />
    </div>
  )
}
