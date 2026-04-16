"use client"

import { useEffect, useState, useCallback, useRef } from "react"
import { useRouter } from "next/navigation"
import {
  Button,
  Badge,
  Input,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@kcontrol/ui"
import {
  CheckCircle2,
  XCircle,
  Clock,
  Loader2,
  RefreshCw,
  Filter,
  ExternalLink,
  AlertTriangle,
  Zap,
  Database,
  Code2,
  Shield,
  Library,
  ChevronRight,
  FileJson2,
  RotateCw,
} from "lucide-react"
import { cn } from "@kcontrol/ui"
import { fetchWithAuth } from "@/lib/api/apiClient"
import { useSandboxOrgWorkspace } from "@/lib/context/SandboxOrgWorkspaceContext"
import {
  getSignalTestDatasets,
  getCodeGenJobDetails,
  type TestDatasetInfo,
  type CodeGenProgress,
  retryPipelineStep,
  retryAllFailedSteps,
} from "@/lib/api/signalPipeline"
import { getDatasetRecords, type DatasetDataRecord } from "@/lib/api/sandbox"

// ── Types ──────────────────────────────────────────────────────────────────────

type StageStatus = "done" | "running" | "failed" | "queued" | "skipped"

interface PipelineStage {
  label: string
  icon: React.ReactNode
  job_type: string
  status: StageStatus
  progress?: string
  error?: string
  job_id?: string
}

interface PipelineRow {
  signal_id: string
  signal_code: string
  signal_name: string
  connector_type_code: string
  stages: PipelineStage[]
  overall_status: "running" | "failed" | "completed" | "queued"
  started_at?: string
}

interface JobRow {
  id: string
  job_type: string
  status_code: string
  error_message?: string
  started_at?: string
  completed_at?: string
  input_json?: Record<string, unknown>
}

// ── Stage definitions ──────────────────────────────────────────────────────────

const STAGE_DEFS = [
  { label: "Spec", job_type: "signal_generate", icon: <Zap className="h-3.5 w-3.5" /> },
  { label: "Test Dataset", job_type: "signal_test_dataset_gen", icon: <Database className="h-3.5 w-3.5" /> },
  { label: "Code Gen", job_type: "signal_codegen", icon: <Code2 className="h-3.5 w-3.5" /> },
  { label: "Threats", job_type: "threat_composer", icon: <Shield className="h-3.5 w-3.5" /> },
  { label: "Library", job_type: "library_builder", icon: <Library className="h-3.5 w-3.5" /> },
]

// ── Stage Cell ──────────────────────────────────────────────────────────────────

function StageCell({ stage, onClick, onRetry, retrying }: { stage: PipelineStage; onClick?: () => void; onRetry?: () => void; retrying?: boolean }) {
  const map: Record<StageStatus, { cls: string; icon: React.ReactNode }> = {
    done: {
      cls: "bg-green-50 dark:bg-green-950/20 border-green-200 dark:border-green-800 text-green-700 dark:text-green-400",
      icon: <CheckCircle2 className="h-3 w-3 shrink-0" />,
    },
    running: {
      cls: "bg-blue-50 dark:bg-blue-950/20 border-blue-200 dark:border-blue-800 text-blue-700 dark:text-blue-400",
      icon: <Loader2 className="h-3 w-3 shrink-0 animate-spin" />,
    },
    failed: {
      cls: "bg-red-50 dark:bg-red-950/20 border-red-200 dark:border-red-800 text-red-700 dark:text-red-400",
      icon: <XCircle className="h-3 w-3 shrink-0" />,
    },
    queued: {
      cls: "bg-muted/50 border-border text-muted-foreground",
      icon: <Clock className="h-3 w-3 shrink-0" />,
    },
    skipped: {
      cls: "bg-muted/30 border-border/50 text-muted-foreground/50",
      icon: <span className="h-3 w-3 shrink-0 inline-block" />,
    },
  }

  const { cls, icon } = map[stage.status]
  const isClickable = !!onClick && (stage.status === "done" || stage.status === "running" || stage.status === "failed")

  return (
    <div
      className={cn(
        "flex flex-col items-center gap-1 rounded-lg border p-2 min-w-[90px]",
        cls,
        isClickable && "cursor-pointer hover:ring-2 hover:ring-primary/30 transition-shadow",
      )}
      onClick={isClickable ? onClick : undefined}
      role={isClickable ? "button" : undefined}
      tabIndex={isClickable ? 0 : undefined}
      onKeyDown={isClickable ? (e) => { if (e.key === "Enter" || e.key === " ") onClick() } : undefined}
    >
      <div className="flex items-center gap-1">
        {icon}
        <span className="text-[10px] font-semibold">{stage.label}</span>
      </div>
      {stage.progress && (
        <span className="text-[10px] opacity-75">{stage.progress}</span>
      )}
      {stage.status === "failed" && stage.error && (
        <span className="text-[9px] opacity-75 truncate max-w-[80px]">{stage.error}</span>
      )}
      {stage.status === "failed" && onRetry && (
        <button
          onClick={(e) => { e.stopPropagation(); onRetry() }}
          disabled={retrying}
          className="flex items-center gap-0.5 text-[9px] font-medium mt-0.5 px-1.5 py-0.5 rounded bg-red-100 dark:bg-red-900/30 hover:bg-red-200 dark:hover:bg-red-900/50 transition-colors disabled:opacity-50"
          title={`Retry ${stage.label}`}
        >
          <RotateCw className={cn("h-2.5 w-2.5", retrying && "animate-spin")} />
          Retry
        </button>
      )}
    </div>
  )
}

// ── Pipeline Row ────────────────────────────────────────────────────────────────

function PipelineRowCard({
  row,
  onView,
  onTestDatasetClick,
  onCodeGenClick,
  onRetryStep,
  onRetryAll,
  retryingSteps,
  retryingAll,
}: {
  row: PipelineRow
  onView: (id: string) => void
  onTestDatasetClick: (row: PipelineRow) => void
  onCodeGenClick: (row: PipelineRow) => void
  onRetryStep: (signalId: string, jobType: string) => void
  onRetryAll: (signalId: string) => void
  retryingSteps: Set<string>
  retryingAll: boolean
}) {
  const statusColors: Record<string, string> = {
    running: "border-l-blue-400",
    failed: "border-l-red-400",
    completed: "border-l-green-400",
    queued: "border-l-gray-300",
  }

  return (
    <div className={cn("border border-border rounded-xl p-4 space-y-3 border-l-4", statusColors[row.overall_status] ?? "border-l-border")}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="font-mono text-sm font-semibold">{row.signal_code}</span>
          {row.signal_name && row.signal_name !== row.signal_code && (
            <span className="text-xs text-muted-foreground">{row.signal_name}</span>
          )}
          <Badge variant="outline" className="text-[10px]">{row.connector_type_code}</Badge>
        </div>
        <Button
          variant="ghost"
          size="sm"
          className="text-xs gap-1.5 text-muted-foreground"
          onClick={() => onView(row.signal_id)}
        >
          View Signal <ExternalLink className="h-3 w-3" />
        </Button>
      </div>

      {/* 5-stage pipeline strip */}
      <div className="flex gap-2 overflow-x-auto pb-1">
        {row.stages.map((stage, i) => {
          const clickHandler =
            stage.job_type === "signal_test_dataset_gen" && (stage.status === "done" || stage.status === "running" || stage.status === "failed")
              ? () => onTestDatasetClick(row)
              : stage.job_type === "signal_codegen" && (stage.status === "done" || stage.status === "running" || stage.status === "failed")
                ? () => onCodeGenClick(row)
                : undefined

          return (
            <StageCell
              key={i}
              stage={stage}
              onClick={clickHandler}
              onRetry={
                stage.status === "failed" && stage.job_type !== "signal_generate"
                  ? () => onRetryStep(row.signal_id, stage.job_type)
                  : undefined
              }
              retrying={retryingSteps.has(`${row.signal_id}:${stage.job_type}`)}
            />
          )
        })}
      </div>

      {/* Failure action */}
      {row.overall_status === "failed" && (
        <div className="flex items-center gap-2 text-xs text-red-600 dark:text-red-400">
          <AlertTriangle className="h-3.5 w-3.5 shrink-0" />
          <span>Pipeline failed — retry individual stages above or all at once</span>
          <Button
            variant="outline"
            size="sm"
            className="text-xs h-6 px-2 border-red-300 text-red-600 ml-auto gap-1.5"
            onClick={() => onRetryAll(row.signal_id)}
            disabled={retryingAll}
          >
            <RotateCw className={cn("h-3 w-3", retryingAll && "animate-spin")} />
            Retry All Failed
          </Button>
        </div>
      )}

      {row.overall_status === "completed" && (
        <div className="text-xs text-muted-foreground">
          Pipeline complete
        </div>
      )}
    </div>
  )
}

// ── Test Dataset Dialog ──────────────────────────────────────────────────────

function TestDatasetDialog({
  open,
  onClose,
  signalId,
  signalCode,
}: {
  open: boolean
  onClose: () => void
  signalId: string
  signalCode: string
}) {
  const [datasets, setDatasets] = useState<TestDatasetInfo[]>([])
  const [loading, setLoading] = useState(false)
  const [selectedDatasetId, setSelectedDatasetId] = useState<string | null>(null)
  const [records, setRecords] = useState<DatasetDataRecord[]>([])
  const [loadingRecords, setLoadingRecords] = useState(false)
  const [expandedRecordId, setExpandedRecordId] = useState<string | null>(null)

  useEffect(() => {
    if (!open || !signalId) return
    setLoading(true)
    setSelectedDatasetId(null)
    setRecords([])
    getSignalTestDatasets(signalId)
      .then((ds) => {
        setDatasets(ds)
        if (ds.length > 0) setSelectedDatasetId(ds[0].id)
      })
      .catch((err) => console.error("Failed to load test datasets", err))
      .finally(() => setLoading(false))
  }, [open, signalId])

  useEffect(() => {
    if (!selectedDatasetId) return
    setLoadingRecords(true)
    setExpandedRecordId(null)
    getDatasetRecords(selectedDatasetId, { limit: 100 })
      .then((resp) => setRecords(resp.records))
      .catch((err) => console.error("Failed to load records", err))
      .finally(() => setLoadingRecords(false))
  }, [selectedDatasetId])

  const selectedDataset = datasets.find((d) => d.id === selectedDatasetId)

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) onClose() }}>
      <DialogContent className="sm:max-w-4xl max-h-[85vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <div className="flex items-center gap-2">
            <Database className="h-5 w-5 text-primary" />
            <div>
              <DialogTitle>Test Datasets for {signalCode}</DialogTitle>
              <DialogDescription>
                AI-generated test datasets with scenarios and expected results
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        {loading && (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
          </div>
        )}

        {!loading && datasets.length === 0 && (
          <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
            <Database className="h-8 w-8 mb-2 opacity-30" />
            <p className="text-sm">No test datasets found for this signal</p>
          </div>
        )}

        {!loading && datasets.length > 0 && (
          <div className="flex gap-4 min-h-0 flex-1 overflow-hidden">
            {/* Left: Dataset versions list */}
            <div className="w-56 shrink-0 border-r border-border pr-4 overflow-y-auto">
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
                Previous Versions
              </p>
              <div className="space-y-1">
                {datasets.map((ds) => (
                  <button
                    key={ds.id}
                    onClick={() => setSelectedDatasetId(ds.id)}
                    className={cn(
                      "w-full text-left rounded-lg px-3 py-2 text-xs transition-colors",
                      selectedDatasetId === ds.id
                        ? "bg-primary/10 text-primary border border-primary/20"
                        : "hover:bg-muted/50 text-muted-foreground border border-transparent",
                    )}
                  >
                    <p className="font-medium truncate">{ds.name || ds.dataset_code}</p>
                    <div className="flex items-center justify-between mt-1 text-[10px] opacity-75">
                      <span>{ds.record_count} records</span>
                      <span>{new Date(ds.created_at).toLocaleDateString()}</span>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Right: Records from selected dataset */}
            <div className="flex-1 overflow-y-auto min-h-0">
              {selectedDataset && (
                <div className="flex items-center gap-2 mb-3">
                  <h3 className="text-sm font-semibold">{selectedDataset.name || selectedDataset.dataset_code}</h3>
                  <Badge variant="outline" className="text-[10px]">
                    {selectedDataset.record_count} records
                  </Badge>
                </div>
              )}

              {loadingRecords && (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                </div>
              )}

              {!loadingRecords && records.length === 0 && selectedDatasetId && (
                <p className="text-xs text-muted-foreground text-center py-8">No records in this dataset</p>
              )}

              {!loadingRecords && records.length > 0 && (
                <div className="space-y-2">
                  {records.map((record) => {
                    const data = record.record_data || {}
                    const caseId = data.case_id as string | undefined
                    const scenarioName = data.scenario_name as string | undefined
                    const expectedResult = data.expected_result as string | undefined
                    const isExpanded = expandedRecordId === record.id

                    const resultColor = expectedResult === "pass"
                      ? "text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-950/20"
                      : expectedResult === "fail"
                        ? "text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-950/20"
                        : expectedResult === "warning"
                          ? "text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/20"
                          : "text-muted-foreground bg-muted/50"

                    return (
                      <div key={record.id} className="border border-border rounded-lg overflow-hidden">
                        <button
                          className="w-full flex items-center gap-2 px-3 py-2 text-left hover:bg-muted/30 transition-colors"
                          onClick={() => setExpandedRecordId(isExpanded ? null : record.id)}
                        >
                          <ChevronRight className={cn(
                            "h-3.5 w-3.5 shrink-0 text-muted-foreground transition-transform",
                            isExpanded && "rotate-90",
                          )} />
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                              {caseId && (
                                <span className="text-[10px] font-mono text-muted-foreground">{caseId}</span>
                              )}
                              <span className="text-xs font-medium truncate">
                                {scenarioName || record.record_name || `Record ${record.record_seq}`}
                              </span>
                            </div>
                          </div>
                          {expectedResult && (
                            <span className={cn("text-[10px] font-semibold px-2 py-0.5 rounded-full", resultColor)}>
                              {expectedResult}
                            </span>
                          )}
                          <FileJson2 className="h-3.5 w-3.5 shrink-0 text-muted-foreground/50" />
                        </button>

                        {isExpanded && (
                          <div className="border-t border-border bg-muted/20 p-3">
                            <pre className="text-[11px] font-mono leading-relaxed overflow-x-auto whitespace-pre-wrap break-all text-muted-foreground">
                              {JSON.stringify(data, null, 2)}
                            </pre>
                          </div>
                        )}
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}


// ── Code Gen Dialog ──────────────────────────────────────────────────────────

function CodeGenDialog({
  open,
  onClose,
  jobId,
  signalCode,
  stageStatus,
  errorMessage,
}: {
  open: boolean
  onClose: () => void
  jobId: string
  signalCode: string
  stageStatus: StageStatus
  errorMessage?: string
}) {
  const [progress, setProgress] = useState<CodeGenProgress | null>(null)
  const [loading, setLoading] = useState(false)
  const [fetchError, setFetchError] = useState<string | null>(null)
  const [selectedIter, setSelectedIter] = useState<number | null>(null)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const autoFollowLatest = useRef(true)
  const scrollRef = useRef<HTMLDivElement>(null)

  const fetchDetails = useCallback(async () => {
    if (!jobId) return
    try {
      const details = await getCodeGenJobDetails(jobId)
      setProgress(details.output_json)
      setFetchError(null)
      return details.status_code
    } catch (err) {
      setFetchError(err instanceof Error ? err.message : String(err))
      return null
    } finally {
      setLoading(false)
    }
  }, [jobId])

  useEffect(() => {
    if (!open || !jobId) return
    setLoading(true)
    setProgress(null)
    setFetchError(null)

    fetchDetails()

    // Poll every 3 seconds while running
    if (stageStatus === "running") {
      pollRef.current = setInterval(async () => {
        const statusCode = await fetchDetails()
        if (statusCode && statusCode !== "running") {
          if (pollRef.current) clearInterval(pollRef.current)
        }
      }, 3000)
    }

    return () => {
      if (pollRef.current) clearInterval(pollRef.current)
    }
  }, [open, jobId, stageStatus, fetchDetails])

  // Auto-scroll to bottom when iteration updates
  useEffect(() => {
    if (progress && autoFollowLatest.current && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [progress?.current_iteration])

  const isRunning = stageStatus === "running"
  const isFailed = stageStatus === "failed"

  const passRatePct = progress ? Math.round(progress.pass_rate * 100) : 0
  const totalTests = progress?.test_results?.length ?? 0
  const passedTests = progress?.test_results?.filter((t) => t.passed).length ?? 0

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) onClose() }}>
      <DialogContent className="sm:max-w-5xl max-h-[92vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <div className="flex items-center gap-2">
            <Code2 className="h-5 w-5 text-primary" />
            <div className="flex-1 min-w-0">
              <DialogTitle className="flex items-center gap-2 flex-wrap">
                Code Generation
                <span className="font-mono text-sm text-muted-foreground">{signalCode}</span>
              </DialogTitle>
              <DialogDescription className="flex items-center gap-3 mt-0.5">
                {progress && (
                  <>
                    <span>
                      Iteration {progress.current_iteration}/{progress.max_iterations}
                    </span>
                    <span className="text-foreground font-medium">{passRatePct}% pass rate</span>
                    {isRunning && <Loader2 className="h-3 w-3 animate-spin" />}
                  </>
                )}
                {!progress && loading && <span>Loading...</span>}
                {!progress && !loading && fetchError && (
                  <span className="text-red-500">{fetchError}</span>
                )}
                {!progress && !loading && !fetchError && (
                  <span>No iteration data available yet</span>
                )}
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        {loading && !progress && (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
          </div>
        )}

        {progress && (
          <div ref={scrollRef} className="flex-1 overflow-y-auto space-y-4 min-h-0">
            {/* Iteration tabs */}
            {progress.iteration_history && progress.iteration_history.length > 0 && (
              <div className="flex items-center gap-1 flex-wrap shrink-0">
                {progress.iteration_history.map((entry) => {
                  const pct = Math.round(entry.pass_rate * 100)
                  const isCurrent = entry.iteration === progress.current_iteration
                  return (
                    <button
                      key={entry.iteration}
                      className={cn(
                        "rounded-md px-2 py-1 text-[10px] font-mono border transition-colors",
                        isCurrent
                          ? "bg-primary/10 border-primary text-primary font-bold"
                          : "border-border text-muted-foreground hover:bg-muted/50",
                        !entry.compile_success && "border-red-500/30 text-red-500",
                      )}
                    >
                      {entry.iteration}
                      <span className={cn(
                        "ml-1 font-semibold",
                        pct === 100 ? "text-green-500" : pct >= 70 ? "text-amber-500" : "text-red-500",
                      )}>
                        {entry.compile_success ? `${pct}%` : "✗"}
                      </span>
                    </button>
                  )
                })}
                {isRunning && (
                  <span className="text-[10px] text-muted-foreground flex items-center gap-1 ml-1">
                    <Loader2 className="h-3 w-3 animate-spin" /> iterating...
                  </span>
                )}
              </div>
            )}

            {/* Status banner */}
            {progress.status === "completed" && (
              <div className="rounded-lg border border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-950/20 px-4 py-2.5 text-sm text-green-700 dark:text-green-400 flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 shrink-0" />
                All tests passed in {progress.current_iteration} iteration{progress.current_iteration > 1 ? "s" : ""}!
              </div>
            )}
            {progress.status === "exhausted" && (
              <div className="rounded-lg border border-amber-200 dark:border-amber-800 bg-amber-50 dark:bg-amber-950/20 px-4 py-2.5 text-sm text-amber-700 dark:text-amber-400 flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 shrink-0" />
                Exhausted {progress.max_iterations} iterations with {passRatePct}% pass rate ({passedTests}/{totalTests})
              </div>
            )}
            {isFailed && errorMessage && (
              <div className="rounded-lg border border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-950/20 px-4 py-2.5 text-sm text-red-700 dark:text-red-400 flex items-center gap-2">
                <XCircle className="h-4 w-4 shrink-0" />
                {errorMessage}
              </div>
            )}

            {/* Pass rate progress bar */}
            {totalTests > 0 && (
              <div className="space-y-1.5">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-muted-foreground">Pass Rate</span>
                  <span className="font-semibold">{passedTests}/{totalTests} ({passRatePct}%)</span>
                </div>
                <div className="h-2 rounded-full bg-muted overflow-hidden">
                  <div
                    className={cn(
                      "h-full rounded-full transition-all duration-500",
                      passRatePct === 100 ? "bg-green-500" : passRatePct >= 70 ? "bg-amber-500" : "bg-red-500",
                    )}
                    style={{ width: `${passRatePct}%` }}
                  />
                </div>
              </div>
            )}

            {/* Compile errors */}
            {!progress.compile_success && progress.compile_errors.length > 0 && (
              <div className="space-y-1.5">
                <p className="text-xs font-semibold text-red-600 dark:text-red-400 uppercase tracking-wider">
                  Compile Errors
                </p>
                <div className="rounded-lg border border-red-200 dark:border-red-800 bg-red-50/50 dark:bg-red-950/10 p-3">
                  {progress.compile_errors.map((err, i) => (
                    <p key={i} className="text-xs font-mono text-red-700 dark:text-red-400">{err}</p>
                  ))}
                </div>
              </div>
            )}

            {/* Generated Code Preview */}
            {progress.generated_code_preview && (
              <div className="space-y-1.5">
                <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  Generated Python Code
                </p>
                <pre className="rounded-lg border border-border bg-zinc-950 dark:bg-zinc-900 p-4 text-[11px] font-mono leading-relaxed text-zinc-100 max-h-[300px] overflow-auto whitespace-pre">
                  {progress.generated_code_preview}
                </pre>
              </div>
            )}

            {/* Test Results Table */}
            {progress.test_results && progress.test_results.length > 0 && (
              <div className="space-y-1.5">
                <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  Test Results
                </p>
                <div className="rounded-lg border border-border overflow-hidden max-h-[300px] overflow-y-auto">
                  <table className="w-full text-xs">
                    <thead className="sticky top-0 z-10">
                      <tr className="border-b border-border bg-muted/50">
                        <th className="px-3 py-1.5 text-left font-semibold text-muted-foreground bg-muted/50">Case</th>
                        <th className="px-3 py-1.5 text-left font-semibold text-muted-foreground bg-muted/50">Scenario</th>
                        <th className="px-3 py-1.5 text-center font-semibold text-muted-foreground bg-muted/50">Expected</th>
                        <th className="px-3 py-1.5 text-center font-semibold text-muted-foreground bg-muted/50">Actual</th>
                        <th className="px-3 py-1.5 text-center font-semibold text-muted-foreground bg-muted/50">Result</th>
                      </tr>
                    </thead>
                    <tbody>
                      {[...progress.test_results].sort((a, b) => (a.passed === b.passed ? 0 : a.passed ? 1 : -1)).map((tr, i) => (
                        <tr key={i} className={cn("border-b border-border last:border-b-0", !tr.passed && "bg-red-50/50 dark:bg-red-950/10")}>
                          <td className="px-3 py-1.5 font-mono text-muted-foreground">{tr.case_id || `#${i + 1}`}</td>
                          <td className="px-3 py-1.5 max-w-[200px] truncate">{tr.scenario || "—"}</td>
                          <td className="px-3 py-1.5 text-center">
                            <span className={cn(
                              "inline-block px-1.5 py-0.5 rounded text-[10px] font-semibold",
                              tr.expected === "pass" ? "bg-green-100 dark:bg-green-950/30 text-green-700 dark:text-green-400"
                                : tr.expected === "fail" ? "bg-red-100 dark:bg-red-950/30 text-red-700 dark:text-red-400"
                                : "bg-amber-100 dark:bg-amber-950/30 text-amber-700 dark:text-amber-400",
                            )}>
                              {tr.expected}
                            </span>
                          </td>
                          <td className="px-3 py-1.5 text-center">
                            <span className={cn(
                              "inline-block px-1.5 py-0.5 rounded text-[10px] font-semibold",
                              tr.actual === "pass" ? "bg-green-100 dark:bg-green-950/30 text-green-700 dark:text-green-400"
                                : tr.actual === "fail" ? "bg-red-100 dark:bg-red-950/30 text-red-700 dark:text-red-400"
                                : tr.actual === "error" ? "bg-red-100 dark:bg-red-950/30 text-red-700 dark:text-red-400"
                                : "bg-amber-100 dark:bg-amber-950/30 text-amber-700 dark:text-amber-400",
                            )}>
                              {tr.actual}
                            </span>
                          </td>
                          <td className="px-3 py-1.5 text-center">
                            {tr.passed
                              ? <CheckCircle2 className="h-3.5 w-3.5 text-green-600 dark:text-green-400 inline-block" />
                              : <XCircle className="h-3.5 w-3.5 text-red-600 dark:text-red-400 inline-block" />
                            }
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Iteration History */}
            {progress.iteration_history && progress.iteration_history.length > 0 && (
              <div className="space-y-1.5">
                <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  Iteration History
                </p>
                <div className="rounded-lg border border-border divide-y divide-border">
                  {progress.iteration_history.map((entry) => {
                    const entryPassPct = Math.round(entry.pass_rate * 100)
                    return (
                      <div key={entry.iteration} className="flex items-center gap-3 px-3 py-2 text-xs">
                        <span className="font-mono text-muted-foreground w-12 shrink-0">
                          Iter {entry.iteration}
                        </span>
                        {entry.compile_success ? (
                          <>
                            <div className="flex-1 flex items-center gap-2">
                              <div className="h-1.5 flex-1 rounded-full bg-muted overflow-hidden max-w-[120px]">
                                <div
                                  className={cn(
                                    "h-full rounded-full",
                                    entryPassPct === 100 ? "bg-green-500" : entryPassPct >= 70 ? "bg-amber-500" : "bg-red-500",
                                  )}
                                  style={{ width: `${entryPassPct}%` }}
                                />
                              </div>
                              <span className="font-semibold w-10">
                                {entryPassPct}%
                              </span>
                              <span className="text-muted-foreground">
                                ({entry.passed_count}/{entry.total_count})
                              </span>
                            </div>
                            <span className="text-muted-foreground text-[10px]">{entry.note}</span>
                          </>
                        ) : (
                          <div className="flex items-center gap-2 text-red-600 dark:text-red-400">
                            <XCircle className="h-3 w-3" />
                            <span>compilation failed</span>
                            {entry.compile_errors && entry.compile_errors.length > 0 && (
                              <span className="text-[10px] text-muted-foreground truncate max-w-[200px]">
                                {entry.compile_errors[0]}
                              </span>
                            )}
                          </div>
                        )}
                      </div>
                    )
                  })}
                  {isRunning && (
                    <div className="flex items-center gap-3 px-3 py-2 text-xs text-blue-600 dark:text-blue-400">
                      <Loader2 className="h-3 w-3 animate-spin" />
                      <span>Next iteration in progress...</span>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {!progress && !loading && !fetchError && (
          <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
            <Code2 className="h-8 w-8 mb-2 opacity-30" />
            <p className="text-sm">No codegen progress data available yet</p>
            <p className="text-xs mt-1">Data will appear once the first iteration starts</p>
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}


// ── Main Page ───────────────────────────────────────────────────────────────────

type FilterType = "all" | "running" | "failed" | "completed" | "queued"

export default function PipelineQueuePage() {
  const router = useRouter()
  const { selectedOrgId, ready } = useSandboxOrgWorkspace()
  const [rows, setRows] = useState<PipelineRow[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<FilterType>("all")
  const [testDatasetDialog, setTestDatasetDialog] = useState<{ signalId: string; signalCode: string } | null>(null)
  const [codeGenDialog, setCodeGenDialog] = useState<{
    jobId: string
    signalCode: string
    stageStatus: StageStatus
    errorMessage?: string
  } | null>(null)
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date())
  const [retryingSteps, setRetryingSteps] = useState<Set<string>>(new Set())
  const [retryingAll, setRetryingAll] = useState<string | null>(null)
  const [retryMessage, setRetryMessage] = useState<string | null>(null)

  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const rowsRef = useRef<PipelineRow[]>([])

  const fetchPipeline = useCallback(async () => {
    if (!selectedOrgId) return
    try {
      const res = await fetchWithAuth(`/api/v1/ai/jobs?org_id=${selectedOrgId}&limit=200`)
      if (!res.ok) return
      const data = await res.json()
      const jobs: JobRow[] = data.items ?? []

      // Group jobs by signal_id
      const bySignal: Record<string, JobRow[]> = {}
      for (const job of jobs) {
        const inp = job.input_json as Record<string, unknown> || {}
        const signalId = String(inp.signal_id || "")
        if (signalId) {
          if (!bySignal[signalId]) bySignal[signalId] = []
          bySignal[signalId].push(job)
        }
      }

      // Fetch signal metadata
      const pipelineRows: PipelineRow[] = []
      for (const [signalId, signalJobs] of Object.entries(bySignal)) {
        const sigRes = await fetchWithAuth(`/api/v1/sb/signals/${signalId}?org_id=${selectedOrgId}`)
        const sigData = sigRes.ok ? await sigRes.json() : {}

        const stages: PipelineStage[] = STAGE_DEFS.map((def) => {
          const job = signalJobs.find((j) => j.job_type === def.job_type)
          const status: StageStatus = !job ? "queued"
            : job.status_code === "completed" ? "done"
            : job.status_code === "running" ? "running"
            : job.status_code === "failed" ? "failed"
            : "queued"

          return {
            label: def.label,
            icon: def.icon,
            job_type: def.job_type,
            status,
            error: job?.error_message?.slice(0, 60),
            job_id: job?.id,
          }
        })

        const hasFailed = stages.some((s) => s.status === "failed")
        const hasRunning = stages.some((s) => s.status === "running")
        const allDone = stages.every((s) => s.status === "done")

        const overall: PipelineRow["overall_status"] = hasFailed ? "failed"
          : hasRunning ? "running"
          : allDone ? "completed"
          : "queued"

        pipelineRows.push({
          signal_id: signalId,
          signal_code: sigData.signal_code || signalId.slice(0, 8),
          signal_name: sigData.name || "",
          connector_type_code: sigData.connector_type_code || "",
          stages,
          overall_status: overall,
          started_at: signalJobs[0]?.started_at,
        })
      }

      rowsRef.current = pipelineRows
      setRows(pipelineRows)
      setLastRefresh(new Date())
    } catch (e) {
      console.error("pipeline fetch failed", e)
    } finally {
      setLoading(false)
    }
  }, [selectedOrgId])

  useEffect(() => {
    if (!ready) return
    fetchPipeline()
    // Auto-refresh every 5s if any jobs are running (use ref to avoid stale closure)
    pollRef.current = setInterval(() => {
      const hasRunning = rowsRef.current.some((r) => r.overall_status === "running")
      if (hasRunning) fetchPipeline()
    }, 5000)
    return () => { if (pollRef.current) clearInterval(pollRef.current) }
  }, [ready, fetchPipeline])

  const handleRetryStep = useCallback(async (signalId: string, jobType: string) => {
    if (!selectedOrgId) return
    const key = `${signalId}:${jobType}`
    setRetryingSteps((prev) => new Set(prev).add(key))
    setRetryMessage(null)
    try {
      await retryPipelineStep(signalId, jobType, selectedOrgId)
      setRetryMessage("Step re-queued successfully")
      await fetchPipeline()
    } catch (err) {
      setRetryMessage(`Retry failed: ${err instanceof Error ? err.message : String(err)}`)
    } finally {
      setRetryingSteps((prev) => {
        const next = new Set(prev)
        next.delete(key)
        return next
      })
      setTimeout(() => setRetryMessage(null), 4000)
    }
  }, [selectedOrgId, fetchPipeline])

  const handleRetryAll = useCallback(async (signalId: string) => {
    if (!selectedOrgId) return
    setRetryingAll(signalId)
    setRetryMessage(null)
    try {
      const result = await retryAllFailedSteps(signalId, selectedOrgId)
      setRetryMessage(`${result.retried.length} step(s) re-queued successfully`)
      await fetchPipeline()
    } catch (err) {
      setRetryMessage(`Retry failed: ${err instanceof Error ? err.message : String(err)}`)
    } finally {
      setRetryingAll(null)
      setTimeout(() => setRetryMessage(null), 4000)
    }
  }, [selectedOrgId, fetchPipeline])

  const filtered = rows.filter((r) => filter === "all" || r.overall_status === filter)

  const counts = {
    running: rows.filter((r) => r.overall_status === "running").length,
    failed: rows.filter((r) => r.overall_status === "failed").length,
    completed: rows.filter((r) => r.overall_status === "completed").length,
    queued: rows.filter((r) => r.overall_status === "queued").length,
  }

  const FILTERS: { label: string; value: FilterType; count?: number }[] = [
    { label: "All", value: "all" },
    { label: "Running", value: "running", count: counts.running },
    { label: "Failed", value: "failed", count: counts.failed },
    { label: "Completed", value: "completed", count: counts.completed },
    { label: "Queued", value: "queued", count: counts.queued },
  ]

  return (
    <div className="flex flex-col gap-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold">Signal Pipeline Queue</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            Real-time view of the autonomous signal generation pipeline
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground">
            Updated {lastRefresh.toLocaleTimeString()}
          </span>
          <Button variant="outline" size="sm" onClick={fetchPipeline} className="gap-1.5">
            <RefreshCw className="h-3.5 w-3.5" />
            Refresh
          </Button>
          <Button size="sm" onClick={() => router.push("/sandbox/signals/new")} className="gap-1.5">
            <Zap className="h-3.5 w-3.5" />
            New Signal
          </Button>
        </div>
      </div>

      {/* Filter bar */}
      <div className="flex gap-2">
        {FILTERS.map((f) => (
          <button
            key={f.value}
            onClick={() => setFilter(f.value)}
            className={cn(
              "flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium transition-colors border",
              filter === f.value
                ? "bg-foreground text-background border-foreground"
                : "bg-background text-muted-foreground border-border hover:border-foreground/50",
            )}
          >
            {f.label}
            {f.count !== undefined && f.count > 0 && (
              <span className={cn(
                "rounded-full px-1.5 py-0.5 text-[9px] font-bold",
                filter === f.value ? "bg-background/20" : "bg-muted",
              )}>
                {f.count}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Pipeline rows */}
      {loading && (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      )}

      {!loading && filtered.length === 0 && (
        <div className="flex flex-col items-center justify-center py-16 text-center text-muted-foreground">
          <Zap className="h-10 w-10 mb-3 opacity-20" />
          <p className="text-sm">No signals in the pipeline</p>
          <p className="text-xs mt-1">
            Build a signal spec to kick off the autonomous pipeline
          </p>
          <Button
            className="mt-4"
            size="sm"
            onClick={() => router.push("/sandbox/signals/new")}
          >
            <Zap className="mr-2 h-4 w-4" />
            New Spec-Driven Signal
          </Button>
        </div>
      )}

      {/* Retry toast */}
      {retryMessage && (
        <div className={cn(
          "fixed bottom-6 right-6 z-50 rounded-lg border px-4 py-2.5 text-sm shadow-lg animate-in slide-in-from-bottom-2",
          retryMessage.startsWith("Retry failed")
            ? "bg-red-50 dark:bg-red-950/40 border-red-200 dark:border-red-800 text-red-700 dark:text-red-400"
            : "bg-green-50 dark:bg-green-950/40 border-green-200 dark:border-green-800 text-green-700 dark:text-green-400",
        )}>
          {retryMessage}
        </div>
      )}

      <div className="space-y-3">
        {filtered.map((row) => (
          <PipelineRowCard
            key={row.signal_id}
            row={row}
            onView={(id) => router.push(`/sandbox/signals?signal_id=${id}`)}
            onTestDatasetClick={(r) => setTestDatasetDialog({ signalId: r.signal_id, signalCode: r.signal_code })}
            onCodeGenClick={(r) => {
              const codeGenStage = r.stages.find((s) => s.job_type === "signal_codegen")
              if (codeGenStage?.job_id) {
                setCodeGenDialog({
                  jobId: codeGenStage.job_id,
                  signalCode: r.signal_code,
                  stageStatus: codeGenStage.status,
                  errorMessage: codeGenStage.error,
                })
              }
            }}
            onRetryStep={handleRetryStep}
            onRetryAll={handleRetryAll}
            retryingSteps={retryingSteps}
            retryingAll={retryingAll === row.signal_id}
          />
        ))}
      </div>

      {/* Test Dataset Viewer Dialog */}
      <TestDatasetDialog
        open={!!testDatasetDialog}
        onClose={() => setTestDatasetDialog(null)}
        signalId={testDatasetDialog?.signalId ?? ""}
        signalCode={testDatasetDialog?.signalCode ?? ""}
      />

      {/* Code Gen Viewer Dialog */}
      <CodeGenDialog
        open={!!codeGenDialog}
        onClose={() => setCodeGenDialog(null)}
        jobId={codeGenDialog?.jobId ?? ""}
        signalCode={codeGenDialog?.signalCode ?? ""}
        stageStatus={codeGenDialog?.stageStatus ?? "queued"}
        errorMessage={codeGenDialog?.errorMessage}
      />
    </div>
  )
}
