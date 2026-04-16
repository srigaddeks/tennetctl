"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Button, Badge, Tooltip, TooltipProvider, TooltipTrigger, TooltipContent } from "@kcontrol/ui"
import {
  ChevronDown,
  ChevronRight,
  Github,
  Cloud,
  Database,
  Server,
  Link2,
  AlertTriangle,
  ExternalLink,
  Trash2,
  History,
  Zap,
  Activity,
  CheckCircle2,
  Circle,
  ArrowRight,
  Layers,
  Play,
  Loader2,
  XCircle,
} from "lucide-react"
import type { PromotedTestResponse } from "@/lib/types/grc"

// ── Connector helpers ─────────────────────────────────────────────────────────

function ConnectorIcon({ typeCode, className = "h-4 w-4" }: { typeCode: string | null; className?: string }) {
  if (!typeCode) return <Server className={className} />
  if (typeCode.startsWith("github")) return <Github className={className} />
  if (typeCode.startsWith("azure")) return <Cloud className={className} />
  if (typeCode.startsWith("aws")) return <Cloud className={className} />
  if (typeCode.startsWith("postgres") || typeCode.startsWith("mysql")) return <Database className={className} />
  return <Server className={className} />
}

function connectorColors(typeCode: string | null) {
  if (!typeCode) return { pill: "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border-slate-200 dark:border-slate-700", dot: "bg-slate-400", icon: "text-slate-500" }
  if (typeCode.startsWith("github")) return { pill: "bg-neutral-900 text-white border-neutral-700", dot: "bg-neutral-700", icon: "text-white" }
  if (typeCode.startsWith("azure")) return { pill: "bg-blue-600 text-white border-blue-500", dot: "bg-blue-500", icon: "text-white" }
  if (typeCode.startsWith("aws")) return { pill: "bg-orange-500 text-white border-orange-400", dot: "bg-orange-400", icon: "text-white" }
  return { pill: "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border-slate-200 dark:border-slate-700", dot: "bg-slate-400", icon: "text-slate-500" }
}

function connectorTypeLabel(code: string | null): string {
  if (!code) return "Unknown"
  const map: Record<string, string> = { github: "GitHub", azure_storage: "Azure Storage", azure: "Azure", aws: "AWS", postgres: "PostgreSQL", mysql: "MySQL" }
  return map[code] ?? code.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())
}

// ── Props ─────────────────────────────────────────────────────────────────────

interface TestExecutionResult {
  result_status: string
  summary: string
  executed_at: string
  task_created?: boolean
}

interface ControlTestCardProps {
  test: PromotedTestResponse
  versionHistory?: PromotedTestResponse[]
  onLinkAsset?: (testId: string) => void
  onDelete?: (testId: string) => void
  onLoadHistory?: (testId: string) => void
  onLinkControls?: (testId: string) => void
  onRun?: (testId: string) => void
  isRunning?: boolean
  lastResult?: TestExecutionResult | null
}

// ── Component ─────────────────────────────────────────────────────────────────

export function ControlTestCard({
  test,
  versionHistory,
  onLinkAsset,
  onDelete,
  onLoadHistory,
  onLinkControls,
  onRun,
  isRunning,
  lastResult,
}: ControlTestCardProps) {
  const router = useRouter()
  const [historyExpanded, setHistoryExpanded] = useState(false)
  const [selectedVersionId, setSelectedVersionId] = useState<string | null>(null)
  const result = lastResult
  const history = versionHistory

  const hasAsset = !!test.linked_asset_id
  const colors = connectorColors(test.connector_type_code)
  const promotedDate = test.promoted_at
    ? new Date(test.promoted_at).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })
    : null
  const historyArray = Array.isArray(history) ? history : null

  const selectedVersion = selectedVersionId ? historyArray?.find(v => v.id === selectedVersionId) : null

  const sourceLabel = test.source_signal_id ? "Signal" : test.source_policy_id ? "Control Test" : test.source_library_id ? "Library" : "Sandbox"

  function handleHistoryToggle() {
    if (!historyExpanded && !versionHistory && onLoadHistory) {
      onLoadHistory(test.id)
    }
    setHistoryExpanded((v) => !v)
  }

  return (
    <TooltipProvider delayDuration={0}>
      <div className="group relative overflow-hidden transition-all duration-300 hover:shadow-2xl hover:-translate-y-1 hover:border-primary/50 border border-border/50 bg-card/60 backdrop-blur-xl rounded-xl shadow-lg">
        {/* ── Main row ──────────────────────────────────────────────────────────── */}
        <div className="flex items-stretch gap-0 min-h-[85px]">

          {/* Left accent stripe */}
          <div className={`w-1 shrink-0 ${hasAsset ? "bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.3)]" : "bg-amber-400 shadow-[0_0_8px_rgba(251,191,36,0.3)]"}`} />

          {/* Test identity */}
          <div className="flex-1 min-w-0 px-5 py-4 flex flex-col justify-center gap-1">
            <div className="flex items-center gap-2.5 flex-wrap">
              <span className="text-sm sm:text-[15px] font-bold text-foreground tracking-tight group-hover:text-primary transition-colors truncate">
                {test.name || test.test_code}
              </span>
              <Badge variant="outline" className="text-[10px] font-mono bg-muted/50 text-muted-foreground px-1.5 py-0 border-border/60 uppercase tracking-tighter h-5">
                v{test.version_number}
              </Badge>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Badge className={`text-[9px] px-1.5 py-0 font-bold uppercase tracking-wider h-5 shrink-0 border-none cursor-help ${test.test_type_code === "automated"
                      ? "bg-violet-500/10 text-violet-500"
                      : "bg-muted text-muted-foreground"
                    }`}>
                    {test.test_type_code}
                  </Badge>
                </TooltipTrigger>
                <TooltipContent side="top" className="text-xs bg-zinc-900 text-slate-100 border-none">
                  {test.test_type_code === "automated" ? "This check runs automatically in the background on a schedule." : "This check requires manual verification."}
                </TooltipContent>
              </Tooltip>
            </div>
            {test.name && (
              <Tooltip>
                <TooltipTrigger asChild>
                  <p
                    className="text-[10px] font-mono text-muted-foreground/70 uppercase tracking-tighter cursor-copy hover:text-primary transition-colors inline-block"
                    onClick={() => navigator.clipboard.writeText(test.test_code)}
                  >
                    {test.test_code}
                  </p>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="text-xs bg-zinc-900 text-slate-100 border-none">
                  Click to copy Test ID
                </TooltipContent>
              </Tooltip>
            )}
            {test.description && (
              <p className="text-xs text-muted-foreground mt-1 line-clamp-1 opacity-80 group-hover:opacity-100 transition-opacity">{test.description}</p>
            )}
          </div>

          {/* ── Data source connector ─── THE HERO ──────────────────────────────── */}
          <div className="flex items-center shrink-0 px-5 py-4 border-l border-border/40 bg-muted/5">
            {hasAsset ? (
              <div className="flex items-center gap-3">
                {/* Flow line: test → connector */}
                <div className="hidden lg:flex items-center gap-2 text-muted-foreground/30">
                  <div className="w-10 h-px bg-current" />
                  <ArrowRight className="h-3 w-3" />
                </div>
                {/* Connector pill */}
                <div className={`flex items-center gap-3 rounded-xl border px-3.5 py-2 shadow-sm transition-all group-hover:border-primary/20 ${colors.pill}`}>
                  <div className="h-8 w-8 rounded-lg bg-white/10 flex items-center justify-center shrink-0 border border-white/10 shadow-inner">
                    <ConnectorIcon typeCode={test.connector_type_code} className="h-4 w-4 shrink-0 text-white" />
                  </div>
                  <div className="flex flex-col min-w-0">
                    <span className="text-[11px] font-bold leading-tight truncate max-w-[140px] tracking-tight">
                      {test.connector_name || connectorTypeLabel(test.connector_type_code)}
                    </span>
                    {test.connector_name && (
                      <span className="text-[10px] font-bold text-white/60 leading-tight mt-0.5 truncate uppercase tracking-tighter">
                        {connectorTypeLabel(test.connector_type_code)}
                      </span>
                    )}
                  </div>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <div className="h-5 w-5 rounded-full bg-emerald-500/20 flex items-center justify-center shrink-0 ml-1 cursor-help">
                        <CheckCircle2 className="h-3 w-3 text-emerald-400" />
                      </div>
                    </TooltipTrigger>
                    <TooltipContent side="top" className="text-xs bg-zinc-900 text-slate-100 border-none">
                      Connection active and healthy
                    </TooltipContent>
                  </Tooltip>
                </div>
              </div>
            ) : (
              <div className="flex items-center gap-3">
                <div className="hidden lg:flex items-center gap-2 text-muted-foreground/30">
                  <div className="w-10 h-px bg-current border-dashed" />
                  <ArrowRight className="h-3 w-3" />
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onLinkAsset?.(test.id)}
                  className="h-10 px-4 rounded-xl border-dashed border-amber-500/40 bg-amber-500/5 text-amber-600 font-bold hover:bg-amber-500/10 hover:border-amber-500 transition-all shadow-sm"
                >
                  <Link2 className="h-4 w-4 mr-2" />
                  Map Source
                </Button>
              </div>
            )}
          </div>

          {/* Actions */}
          <div className="flex items-center shrink-0 px-5 border-l border-border/40 gap-3">
            <div className="flex items-center gap-2">
              {onRun && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onRun?.(test.id)}
                  disabled={isRunning || !hasAsset}
                  title={!hasAsset ? "Map a connector source first" : "Trigger live collection and run test"}
                  className="h-9 font-bold text-emerald-600 border-emerald-500/20 bg-emerald-500/5 hover:bg-emerald-500 hover:text-white transition-all shadow-sm disabled:opacity-40"
                >
                  {isRunning ? (
                    <Loader2 className="h-3.5 w-3.5 mr-2 animate-spin" />
                  ) : (
                    <Play className="h-3.5 w-3.5 mr-2" />
                  )}
                  {isRunning ? "Running" : "Execute"}
                </Button>
              )}

              <Button
                variant="outline"
                size="sm"
                onClick={() => router.push(`/tests/${test.id}/live`)}
                className="h-9 font-bold text-primary border-primary/20 bg-primary/5 hover:bg-primary hover:text-white transition-all shadow-sm"
                title="Live Monitoring"
              >
                <Activity className="h-4 w-4 mr-2" />
                <span className="text-xs">Live</span>
              </Button>

              <div className="h-8 w-[1px] bg-border/40 mx-1" />

              {onLinkControls && (
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => onLinkControls?.(test.id)}
                  className="h-9 w-9 rounded-lg text-muted-foreground hover:bg-muted"
                  title="Map to controls"
                >
                  <Layers className="h-4.5 w-4.5" />
                </Button>
              )}

              {onDelete && (
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => onDelete?.(test.id)}
                  className="h-9 w-9 rounded-lg text-muted-foreground hover:text-red-500 hover:bg-red-500/10"
                  title="Remove Test"
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              )}
            </div>
          </div>
        </div>

        {/* ── Last execution result ────────────────────────────────────────────── */}
        {result && (
          <div className={`border-t px-4 py-2 flex items-center gap-3 text-xs ${result.result_status === "pass" ? "border-emerald-500/20 bg-emerald-500/5" :
              result.result_status === "fail" ? "border-red-500/20 bg-red-500/5" :
                "border-amber-500/20 bg-amber-500/5"
            }`}>
            {result.result_status === "pass" ? (
              <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500 shrink-0" />
            ) : result.result_status === "fail" ? (
              <XCircle className="h-3.5 w-3.5 text-red-500 shrink-0" />
            ) : (
              <AlertTriangle className="h-3.5 w-3.5 text-amber-500 shrink-0" />
            )}
            <span className={`font-medium ${result.result_status === "pass" ? "text-emerald-600 dark:text-emerald-400" :
                result.result_status === "fail" ? "text-red-600 dark:text-red-400" :
                  "text-amber-600 dark:text-amber-400"
              }`}>
              {result.result_status.toUpperCase()}
            </span>
            <span className="text-muted-foreground truncate flex-1">{result.summary}</span>
            <span className="text-[10px] text-muted-foreground shrink-0">
              {new Date(result.executed_at).toLocaleString("en-US", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })}
            </span>
            {result.task_created && (
              <span className="text-[9px] font-medium text-red-500 bg-red-500/10 px-1.5 py-0.5 rounded">Task Created</span>
            )}
          </div>
        )}

        {/* ── Footer meta row ──────────────────────────────────────────────────── */}
        <div className="border-t border-border flex items-center gap-4 px-4 py-2 bg-muted/20">
          {/* Source */}
          <Tooltip>
            <TooltipTrigger asChild>
              <span className="flex items-center gap-1 text-[10px] text-muted-foreground cursor-help">
                <Zap className="h-3 w-3 text-amber-500" />
                {sourceLabel}
              </span>
            </TooltipTrigger>
            <TooltipContent side="bottom" className="text-[10px] bg-zinc-900 text-slate-100 border-none">
              {sourceLabel === "Signal" ? "This test was generated from a Sandbox Signal" : `Originating source: ${sourceLabel}`}
            </TooltipContent>
          </Tooltip>

          {/* Promoted date */}
          {promotedDate && (
            <Tooltip>
              <TooltipTrigger asChild>
                <span className="text-[10px] text-muted-foreground cursor-help">
                  Promoted {promotedDate}
                </span>
              </TooltipTrigger>
              <TooltipContent side="bottom" className="text-[10px] bg-zinc-900 text-slate-100 border-none">
                The date this test was moved from Draft to Active
              </TooltipContent>
            </Tooltip>
          )}

          {/* Signal link */}
          {test.source_signal_id && (
            <a
              href={`/sandbox/signals`}
              className="flex items-center gap-0.5 text-[10px] text-muted-foreground hover:text-primary transition-colors"
            >
              View in Sandbox <ExternalLink className="h-2.5 w-2.5 ml-0.5" />
            </a>
          )}

          {/* Spacer */}
          <div className="flex-1" />

          {/* Version history toggle */}
          <button
            className="flex items-center gap-1 text-[10px] text-muted-foreground hover:text-foreground transition-colors"
            onClick={handleHistoryToggle}
          >
            <History className="h-3 w-3" />
            Version History
            {historyExpanded ? (
              <ChevronDown className="h-3 w-3" />
            ) : (
              <ChevronRight className="h-3 w-3" />
            )}
          </button>
        </div>

        {/* ── Version history panel ─────────────────────────────────────────────── */}
        {historyExpanded && (
          <div className="border-t border-border bg-muted/10 px-4 py-3">
            {!historyArray ? (
              <div className="flex gap-2 items-center text-[11px] text-muted-foreground animate-pulse">
                <Circle className="h-3 w-3" />
                Loading history…
              </div>
            ) : historyArray.length === 0 ? (
              <p className="text-[11px] text-muted-foreground">No history available.</p>
            ) : (
              <div className="space-y-3">
                {/* Version pills */}
                <div className="flex flex-wrap gap-2">
                  {historyArray.map((v) => (
                    <button
                      key={v.id}
                      onClick={() => setSelectedVersionId(selectedVersionId === v.id ? null : v.id)}
                      className={`inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-medium transition-colors ${v.is_active
                          ? "bg-primary/10 border-primary/30 text-primary"
                          : selectedVersionId === v.id
                            ? "bg-violet-500/20 border-violet-500/40 text-violet-600"
                            : "border-border text-muted-foreground hover:border-primary/20 hover:text-foreground"
                        }`}
                    >
                      <span className="font-semibold">{v.name || `Version ${v.version_number}`}</span>
                      {v.is_active && (
                        <span className="text-[9px] bg-emerald-500/20 text-emerald-600 px-1.5 py-0.5 rounded-full">Active</span>
                      )}
                    </button>
                  ))}
                </div>

                {/* Selected version details */}
                {selectedVersion && (
                  <div className="rounded-lg border border-border bg-background p-4 space-y-4">
                    <div className="flex items-center justify-between border-b border-border pb-3">
                      <div>
                        <p className="text-base font-bold text-foreground">{selectedVersion.name || "Untitled Test"}</p>
                        <p className="text-xs text-muted-foreground mt-0.5">
                          Version {selectedVersion.version_number} · Updated {selectedVersion.updated_at ? new Date(selectedVersion.updated_at).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }) : "Unknown"}
                        </p>
                      </div>
                      {selectedVersion.is_active && (
                        <button
                          onClick={() => router.push(`/tests/${selectedVersion.id}/live`)}
                          className="text-xs text-primary hover:underline font-medium"
                        >
                          View Live →
                        </button>
                      )}
                    </div>

                    {selectedVersion.evaluation_rule && (
                      <div>
                        <p className="text-xs font-bold uppercase text-muted-foreground mb-2">Evaluation Rule</p>
                        <div className="relative">
                          <pre className="text-xs leading-relaxed whitespace-pre-wrap font-mono bg-slate-950 text-slate-100 rounded-lg p-4 max-h-[400px] overflow-y-auto border border-slate-800">
                            {selectedVersion.evaluation_rule}
                          </pre>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </TooltipProvider>
  )
}
