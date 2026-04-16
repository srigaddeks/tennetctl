"use client"

/**
 * SignalTestResults — beautiful test results viewer for signal test suites.
 *
 * Shows: overall verdict, pass rate bar, per-scenario cards with expected vs actual,
 * justification, metadata details, execution time, and error info.
 */

import { useState, useEffect, useCallback } from "react"
import {
  Button,
  Badge,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@kcontrol/ui"
import {
  FlaskConical,
  Loader2,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  ChevronDown,
  ChevronRight,
  Clock,
  Play,
  RotateCcw,
  FileJson,
  Shield,
  Zap,
  TrendingUp,
} from "lucide-react"
import {
  runSignalTestSuite,
  listDatasets,
} from "@/lib/api/sandbox"
import type {
  SignalResponse,
  TestSuiteResponse,
  DatasetResponse,
} from "@/lib/api/sandbox"

interface Props {
  signal: SignalResponse
  orgId: string
  onClose: () => void
}

export function SignalTestResults({ signal, orgId, onClose }: Props) {
  const [datasets, setDatasets] = useState<DatasetResponse[]>([])
  const [selectedDatasetId, setSelectedDatasetId] = useState("")
  const [running, setRunning] = useState(false)
  const [result, setResult] = useState<TestSuiteResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [expandedCase, setExpandedCase] = useState<number | null>(null)

  // Load datasets
  useEffect(() => {
    listDatasets(orgId, { dataset_source_code: "ai_generated_tests" })
      .then((r) => setDatasets(r.items))
      .catch(() => {})
  }, [orgId])

  const handleRun = useCallback(async () => {
    setRunning(true)
    setError(null)
    setResult(null)
    try {
      const r = await runSignalTestSuite(signal.id, orgId, selectedDatasetId || undefined)
      setResult(r)
      // Auto-expand first failed case
      const firstFail = r.results.findIndex((c) => !c.passed)
      if (firstFail >= 0) setExpandedCase(firstFail)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Test suite failed")
    } finally {
      setRunning(false)
    }
  }, [signal.id, orgId, selectedDatasetId])

  const passRate = result ? result.pass_rate : 0
  const passColor = passRate >= 0.9 ? "text-green-500" : passRate >= 0.6 ? "text-amber-500" : "text-red-500"
  const passBg = passRate >= 0.9 ? "bg-green-500" : passRate >= 0.6 ? "bg-amber-500" : "bg-red-500"

  const resultIcon = (status: string | null, passed: boolean) => {
    if (passed) return <CheckCircle2 className="h-4 w-4 text-green-500 shrink-0" />
    if (status === "error") return <AlertTriangle className="h-4 w-4 text-amber-500 shrink-0" />
    return <XCircle className="h-4 w-4 text-red-500 shrink-0" />
  }

  const statusBadge = (status: string | null) => {
    if (!status) return null
    const cls = status === "pass" ? "bg-green-500/15 text-green-500 border-green-500/30"
      : status === "fail" ? "bg-red-500/15 text-red-500 border-red-500/30"
      : status === "warning" ? "bg-amber-500/15 text-amber-500 border-amber-500/30"
      : "bg-muted text-muted-foreground"
    return <Badge variant="outline" className={`text-[10px] font-semibold ${cls}`}>{status}</Badge>
  }

  return (
    <Dialog open onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="sm:max-w-3xl max-h-[90vh] overflow-hidden flex flex-col">
        <DialogHeader className="shrink-0">
          <div className="flex items-center gap-2">
            <FlaskConical className="h-5 w-5 text-blue-500" />
            <DialogTitle>Test Results — {signal.name || signal.signal_code}</DialogTitle>
          </div>
          <DialogDescription>
            Run the signal against test scenarios and compare expected vs actual results.
          </DialogDescription>
        </DialogHeader>

        {/* Controls */}
        <div className="flex items-center gap-2 shrink-0 pb-3 border-b border-border">
          <select
            className="h-8 flex-1 rounded-md border border-input bg-background px-2 text-sm"
            value={selectedDatasetId}
            onChange={(e) => setSelectedDatasetId(e.target.value)}
            disabled={running}
          >
            <option value="">Default test dataset</option>
            {datasets.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name || d.dataset_code} ({d.row_count} records)
              </option>
            ))}
          </select>
          <Button
            size="sm"
            onClick={handleRun}
            disabled={running}
            className="gap-1.5 shrink-0"
          >
            {running ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Play className="h-3.5 w-3.5" />}
            {running ? "Running..." : result ? "Re-run" : "Run Tests"}
          </Button>
        </div>

        {error && (
          <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-500 flex items-center gap-2 shrink-0">
            <AlertTriangle className="h-4 w-4 shrink-0" />{error}
          </div>
        )}

        {/* Results */}
        <div className="flex-1 overflow-y-auto space-y-3 pr-1">
          {!result && !running && !error && (
            <div className="py-12 text-center">
              <FlaskConical className="h-10 w-10 text-blue-500/20 mx-auto mb-3" />
              <p className="text-sm text-muted-foreground mb-1">No test results yet</p>
              <p className="text-xs text-muted-foreground">Select a test dataset and click Run Tests</p>
            </div>
          )}

          {running && (
            <div className="py-12 text-center">
              <Loader2 className="h-8 w-8 animate-spin text-blue-500 mx-auto mb-3" />
              <p className="text-sm text-muted-foreground">Executing signal against test scenarios...</p>
            </div>
          )}

          {result && (
            <>
              {/* Overall verdict */}
              <div className={`rounded-xl border-2 p-4 ${passRate >= 0.9 ? "border-green-500/30 bg-green-500/5" : passRate >= 0.6 ? "border-amber-500/30 bg-amber-500/5" : "border-red-500/30 bg-red-500/5"}`}>
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    {passRate >= 0.9 ? (
                      <div className="rounded-full bg-green-500/20 p-2"><Shield className="h-6 w-6 text-green-500" /></div>
                    ) : passRate >= 0.6 ? (
                      <div className="rounded-full bg-amber-500/20 p-2"><AlertTriangle className="h-6 w-6 text-amber-500" /></div>
                    ) : (
                      <div className="rounded-full bg-red-500/20 p-2"><XCircle className="h-6 w-6 text-red-500" /></div>
                    )}
                    <div>
                      <p className={`text-2xl font-bold ${passColor}`}>
                        {Math.round(passRate * 100)}%
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {passRate >= 0.9 ? "All tests passing" : passRate >= 0.6 ? "Some tests failing" : "Significant failures"}
                      </p>
                    </div>
                  </div>
                  <div className="grid grid-cols-3 gap-4 text-center">
                    <div>
                      <p className="text-xl font-bold text-green-500">{result.passed}</p>
                      <p className="text-[10px] text-muted-foreground">Passed</p>
                    </div>
                    <div>
                      <p className="text-xl font-bold text-red-500">{result.failed}</p>
                      <p className="text-[10px] text-muted-foreground">Failed</p>
                    </div>
                    <div>
                      <p className="text-xl font-bold text-amber-500">{result.errored}</p>
                      <p className="text-[10px] text-muted-foreground">Errors</p>
                    </div>
                  </div>
                </div>

                {/* Pass rate bar */}
                <div className="h-2 rounded-full bg-muted overflow-hidden">
                  <div className={`h-full rounded-full transition-all duration-500 ${passBg}`}
                    style={{ width: `${Math.round(passRate * 100)}%` }}
                  />
                </div>
                <p className="text-[10px] text-muted-foreground mt-1 text-right">
                  {result.passed}/{result.total_cases} scenarios passed
                </p>
              </div>

              {/* Individual test cases */}
              <div className="space-y-1.5">
                {result.results.map((tc, i) => {
                  const isExpanded = expandedCase === i
                  return (
                    <div
                      key={tc.case_id || i}
                      className={`rounded-lg border overflow-hidden transition-colors ${
                        tc.passed
                          ? "border-green-500/20 bg-green-500/[0.02]"
                          : "border-red-500/20 bg-red-500/[0.02]"
                      }`}
                    >
                      {/* Case header */}
                      <button
                        onClick={() => setExpandedCase(isExpanded ? null : i)}
                        className="flex items-center gap-2 px-4 py-2.5 w-full text-left hover:bg-muted/20 transition-colors"
                      >
                        {resultIcon(tc.actual, tc.passed)}
                        <span className="text-sm font-medium flex-1 truncate">
                          {tc.scenario_name || tc.case_id || `Case ${i + 1}`}
                        </span>
                        <div className="flex items-center gap-2 shrink-0">
                          <div className="flex items-center gap-1">
                            <span className="text-[10px] text-muted-foreground">exp:</span>
                            {statusBadge(tc.expected)}
                          </div>
                          <span className="text-muted-foreground text-[10px]">→</span>
                          <div className="flex items-center gap-1">
                            <span className="text-[10px] text-muted-foreground">got:</span>
                            {statusBadge(tc.actual)}
                          </div>
                          {tc.execution_time_ms > 0 && (
                            <span className="text-[10px] text-muted-foreground flex items-center gap-0.5">
                              <Clock className="h-2.5 w-2.5" />{tc.execution_time_ms}ms
                            </span>
                          )}
                          {isExpanded ? <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" /> : <ChevronRight className="h-3.5 w-3.5 text-muted-foreground" />}
                        </div>
                      </button>

                      {/* Expanded details */}
                      {isExpanded && (
                        <div className="border-t border-border px-4 py-3 space-y-2">
                          {/* Match status */}
                          <div className={`flex items-center gap-2 rounded-md px-3 py-1.5 text-xs ${tc.passed ? "bg-green-500/10 text-green-600 dark:text-green-400" : "bg-red-500/10 text-red-500"}`}>
                            {tc.passed ? <CheckCircle2 className="h-3.5 w-3.5" /> : <XCircle className="h-3.5 w-3.5" />}
                            {tc.passed
                              ? `Expected "${tc.expected}" — got "${tc.actual}" ✓`
                              : `Expected "${tc.expected}" but got "${tc.actual}" ✗`
                            }
                          </div>

                          {/* Error message */}
                          {tc.error && (
                            <div className="rounded-md bg-red-500/5 border border-red-500/20 px-3 py-2">
                              <p className="text-xs font-semibold text-red-500 mb-0.5 flex items-center gap-1">
                                <AlertTriangle className="h-3 w-3" /> Error
                              </p>
                              <pre className="text-[10px] font-mono text-red-400 whitespace-pre-wrap">{tc.error}</pre>
                            </div>
                          )}

                          {/* Diff details */}
                          {Object.keys(tc.diff || {}).length > 0 && (
                            <div className="rounded-md bg-muted/30 px-3 py-2">
                              <p className="text-[10px] font-semibold text-muted-foreground mb-1 flex items-center gap-1">
                                <FileJson className="h-3 w-3" /> Diff Details
                              </p>
                              <pre className="text-[10px] font-mono text-muted-foreground whitespace-pre-wrap">
                                {JSON.stringify(tc.diff, null, 2)}
                              </pre>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>

              {result.results.length === 0 && (
                <div className="py-8 text-center">
                  <FlaskConical className="h-8 w-8 text-muted-foreground/20 mx-auto mb-2" />
                  <p className="text-sm text-muted-foreground">No test cases found</p>
                  <p className="text-xs text-muted-foreground">This signal has no test data yet. Generate a test dataset first.</p>
                </div>
              )}
            </>
          )}
        </div>

        <DialogFooter className="shrink-0 pt-2">
          <Button variant="outline" size="sm" onClick={onClose}>Close</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
