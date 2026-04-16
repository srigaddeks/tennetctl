"use client"

import {
  AlertCircle,
  BarChart3,
  ChevronRight,
  FileText,
  Loader2,
  PlusCircle,
  Upload,
  X,
} from "lucide-react"
import {
  Button,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  cn,
} from "@kcontrol/ui"
import { type GapAnalysisReport } from "@/lib/api/ai"
import { type FrameworkResponse } from "@/lib/types/grc"

interface BuilderGapTabProps {
  availableFrameworks: FrameworkResponse[]
  gapFrameworkId: string | null
  setGapFrameworkId: (id: string | null) => void
  loadingFrameworks: boolean
  onRunGapAnalysis: () => void
  gapPolling: boolean
  gapReport: GapAnalysisReport | null
  gapUserContext: string
  setGapUserContext: (value: string) => void
  gapUploadedFiles: File[]
  setGapUploadedFiles: (files: File[] | ((prev: File[]) => File[])) => void
  gapDragOver: boolean
  setGapDragOver: (value: boolean) => void
  gapUploading: boolean
}

export function BuilderGapTab({
  availableFrameworks,
  gapFrameworkId,
  setGapFrameworkId,
  loadingFrameworks,
  onRunGapAnalysis,
  gapPolling,
  gapReport,
  gapUserContext,
  setGapUserContext,
  gapUploadedFiles,
  setGapUploadedFiles,
  gapDragOver,
  setGapDragOver,
  gapUploading,
}: BuilderGapTabProps) {
  const isDisabled = gapPolling || gapUploading

  return (
    <div className="custom-scrollbar mx-auto flex w-full max-w-6xl flex-1 flex-col space-y-6 overflow-y-auto px-3 py-4 sm:space-y-8 sm:px-4 sm:py-5 lg:px-6 lg:py-6">
      {/* ── Framework selector ──────────────────────────────────────────── */}
      <div className="space-y-3 sm:space-y-4">
        <label className="ml-1 text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground/50">
          Statistical Coverage Scope
        </label>
        <Select value={gapFrameworkId ?? ""} onValueChange={id => setGapFrameworkId(id || null)} disabled={isDisabled}>
          <SelectTrigger className="min-h-12 h-auto w-full rounded-2xl border border-border/40 border-primary/5 bg-card/40 px-4 py-3 text-left text-sm font-bold shadow-inner focus:border-primary/40 focus:ring-4 focus:ring-primary/5 sm:px-6">
            <SelectValue placeholder={loadingFrameworks ? "Syncing Metrics..." : "Select a framework for analysis"} />
          </SelectTrigger>
          <SelectContent>
            {availableFrameworks.map(f => (
              <SelectItem key={f.id} value={f.id}>
                {f.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* ── Context + Documents (two-column card layout) ─────────────── */}
      <div className="grid grid-cols-1 gap-4 xl:grid-cols-2 xl:gap-6">
        {/* Left: Analysis directive */}
        <div className="space-y-3 sm:space-y-4">
          <label className="ml-1 text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground/50">
            Analysis Directive <span className="text-muted-foreground/30">(optional)</span>
          </label>
          <textarea
            className="min-h-[160px] w-full resize-none rounded-2xl border border-border/40 bg-card/40 px-5 py-4 text-sm leading-relaxed text-foreground/90 shadow-inner transition-all placeholder:text-muted-foreground/25 focus:border-primary/30 focus:outline-none focus:ring-4 focus:ring-primary/5 disabled:opacity-50"
            placeholder="e.g. Compare against our last SOC 2 audit findings and highlight any requirements that still have no detective controls..."
            value={gapUserContext}
            onChange={e => setGapUserContext(e.target.value)}
            disabled={isDisabled}
          />
        </div>

        {/* Right: File upload zone */}
        <div className="space-y-3 sm:space-y-4">
          <label className="ml-1 text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground/50">
            Reference Documents <span className="text-muted-foreground/30">(optional)</span>
          </label>
          <div
            onDragOver={e => { e.preventDefault(); setGapDragOver(true) }}
            onDragLeave={() => setGapDragOver(false)}
            onDrop={e => {
              e.preventDefault()
              setGapDragOver(false)
              setGapUploadedFiles(prev => [...prev, ...Array.from(e.dataTransfer.files)])
            }}
            className={cn(
              "min-h-[160px] flex flex-col items-center justify-center rounded-2xl border-2 border-dashed border-border/40 p-6 transition-all duration-300",
              gapDragOver ? "bg-primary/5 scale-[0.98]" : "bg-primary/[0.02] hover:bg-primary/[0.04]",
              gapUploadedFiles.length > 0 ? "bg-emerald-500/[0.02]" : "",
              isDisabled ? "opacity-50 pointer-events-none" : "",
            )}
          >
            {gapUploadedFiles.length === 0 ? (
              <label className="flex cursor-pointer flex-col items-center gap-3 text-center">
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl border border-primary/20 bg-primary/10">
                  <Upload className="h-6 w-6 text-primary" />
                </div>
                <div className="space-y-1">
                  <span className="text-xs font-bold text-foreground/80">
                    Drop audit reports, test results, or assessments
                  </span>
                  <span className="block text-[10px] font-bold uppercase tracking-widest text-muted-foreground/40">
                    PDF, DOCX, TXT, CSV
                  </span>
                </div>
                <input type="file" multiple className="hidden" onChange={e => setGapUploadedFiles(prev => [...prev, ...Array.from(e.target.files || [])])} />
              </label>
            ) : (
              <div className="w-full space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-black uppercase tracking-[0.2em] text-emerald-400">Docs ({gapUploadedFiles.length})</span>
                  <button onClick={() => setGapUploadedFiles([])} className="text-[10px] font-black uppercase tracking-widest text-muted-foreground/40 hover:text-red-400 transition-colors">Clear All</button>
                </div>
                <div className="space-y-2">
                  {gapUploadedFiles.map((file, i) => (
                    <div key={i} className="flex items-center justify-between gap-3 rounded-xl border border-border/30 bg-card/30 px-3 py-2">
                      <div className="flex min-w-0 items-center gap-2">
                        <FileText className="h-4 w-4 text-emerald-400" />
                        <span className="truncate text-xs font-medium text-foreground/80">{file.name}</span>
                      </div>
                      <button
                        className="shrink-0 text-muted-foreground/40 hover:text-red-400 transition-colors"
                        onClick={() => setGapUploadedFiles(prev => prev.filter((_, idx) => idx !== i))}
                      >
                        <X className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  ))}
                </div>
                <label className="flex cursor-pointer items-center justify-center gap-2 rounded-xl border border-dashed border-border/30 p-2 text-[10px] font-bold uppercase tracking-widest text-muted-foreground/40 transition-colors hover:bg-primary/5 hover:text-primary/60">
                  <PlusCircle className="h-3.5 w-3.5" /> Add More
                  <input type="file" multiple className="hidden" onChange={e => setGapUploadedFiles(prev => [...prev, ...Array.from(e.target.files || [])])} />
                </label>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ── Run button ──────────────────────────────────────────────────── */}
      <div className="flex justify-end">
        <Button
          onClick={onRunGapAnalysis}
          disabled={!gapFrameworkId || isDisabled}
          className="min-h-12 h-auto gap-3 rounded-2xl px-8 py-3 text-[10px] font-black uppercase tracking-[0.2em] whitespace-normal shadow-xl shadow-primary/20"
        >
          {gapUploading ? (
            <><Loader2 className="h-4 w-4 animate-spin" /> Indexing Documents…</>
          ) : gapPolling ? (
            <><Loader2 className="h-4 w-4 animate-spin" /> Analyzing…</>
          ) : (
            <><BarChart3 className="h-4 w-4" /> Compute Gap Metrics</>
          )}
        </Button>
      </div>

      {gapPolling && !gapReport && (
        <div className="flex flex-col items-center justify-center gap-5 py-20 text-center text-primary sm:gap-6 sm:py-24 lg:py-32">
          <div className="relative flex h-20 w-20 items-center justify-center overflow-hidden rounded-[28px] border border-primary/20 bg-primary/10 shadow-2xl shadow-primary/10 sm:h-24 sm:w-24 sm:rounded-[40px]">
            <div className="absolute inset-0 animate-pulse bg-gradient-to-t from-primary/20 to-transparent" />
            <Loader2 className="relative z-10 h-8 w-8 animate-spin sm:h-10 sm:w-10" />
          </div>
          <div className="max-w-xl space-y-2 px-2">
            <h3 className="animate-pulse text-xs font-black uppercase tracking-[0.25em] sm:text-sm sm:tracking-[0.3em]">
              Running Neural Coverage Analysis
            </h3>
            <p className="text-[10px] font-bold uppercase tracking-[0.2em] opacity-60 sm:tracking-widest">
              Mapping controls to risks and benchmarks...
            </p>
          </div>
        </div>
      )}

      {gapReport && <GapReportCard report={gapReport} />}

      {!gapReport && !gapPolling && (
        <div className="animate-in fade-in zoom-in-95 flex flex-col items-center justify-center gap-5 py-20 text-center text-muted-foreground/40 duration-1000 sm:gap-6 sm:py-24 lg:py-32">
          <div className="flex h-20 w-20 items-center justify-center rounded-[28px] border border-border/40 bg-muted/20 shadow-inner sm:h-24 sm:w-24 sm:rounded-[40px]">
            <BarChart3 className="h-8 w-8 opacity-40 sm:h-10 sm:w-10" />
          </div>
          <div className="max-w-xl space-y-1 px-2">
            <h3 className="text-xs font-black uppercase tracking-[0.25em] sm:text-sm sm:tracking-[0.3em]">
              Statistical Engine Idle
            </h3>
            <p className="text-[10px] font-bold uppercase tracking-[0.2em] opacity-60 sm:tracking-widest">
              Select a framework to compute coverage insights
            </p>
          </div>
        </div>
      )}
    </div>
  )
}

function GapReportCard({ report }: { report: GapAnalysisReport }) {
  const benchmarkScore = normalizeBenchmarkScore(report.benchmark?.score ?? null)

  return (
    <div className="animate-in fade-in slide-in-from-bottom-8 space-y-6 duration-1000 sm:space-y-8">
      <div className="grid grid-cols-1 gap-4 xl:grid-cols-3 xl:gap-6">
        <div className="group relative flex flex-col items-center justify-center gap-5 overflow-hidden rounded-[24px] border border-border/40 bg-card/10 p-6 shadow-2xl ring-1 ring-white/5 backdrop-blur-xl sm:gap-6 sm:rounded-[32px] sm:p-8 xl:rounded-[40px] xl:p-10">
          <div className="absolute -right-12 -top-12 h-48 w-48 bg-primary/5 blur-[80px] transition-colors duration-1000 group-hover:bg-primary/10" />
          <div className="relative z-10 text-center">
            <div className={cn("text-5xl font-black tracking-tighter tabular-nums sm:text-6xl xl:text-7xl", healthScoreColor(report.health_score))}>
              {report.health_score}
            </div>
            <div className="mt-2 text-[9px] font-black uppercase tracking-[0.24em] text-muted-foreground opacity-60 sm:text-[10px] sm:tracking-[0.4em]">
              Architecture Health
            </div>
          </div>
        </div>

        <div className="space-y-8 rounded-[24px] border border-border/40 bg-card/10 p-6 shadow-2xl ring-1 ring-white/5 backdrop-blur-xl sm:space-y-10 sm:rounded-[32px] sm:p-8 xl:col-span-2 xl:rounded-[40px] xl:p-10">
          <div className="space-y-4">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
              <div>
                <h4 className="text-[10px] font-black uppercase tracking-[0.2em] text-primary/60">
                  Functional Automation
                </h4>
                <p className="mt-0.5 text-lg font-black tracking-tight sm:text-xl">
                  Automated Oversight Coverage
                </p>
              </div>
              <span className="font-mono text-2xl font-black text-primary sm:text-3xl">
                {report.automation_score}%
              </span>
            </div>
            <div className="h-3 overflow-hidden rounded-full bg-muted/20 p-0.5 ring-1 ring-white/5">
              <div
                className="h-full rounded-full bg-gradient-to-r from-primary/60 via-primary to-primary shadow-lg shadow-primary/20 transition-all duration-1000 ease-out"
                style={{ width: `${report.automation_score}%` }}
              />
            </div>
          </div>

          <div className="space-y-4">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
              <div>
                <h4 className="text-[10px] font-black uppercase tracking-[0.2em] text-primary/50">
                  Threat Mitigation
                </h4>
                <p className="mt-0.5 text-lg font-black tracking-tight sm:text-xl">
                  Risk Linkage Saturation
                </p>
              </div>
              <span className="font-mono text-2xl font-black text-primary/90 sm:text-3xl">
                {report.risk_coverage_pct}%
              </span>
            </div>
            <div className="h-3 overflow-hidden rounded-full bg-muted/20 p-0.5 ring-1 ring-white/5">
              <div
                className="h-full rounded-full bg-gradient-to-r from-primary/45 via-primary/80 to-primary shadow-lg shadow-primary/20 transition-all duration-1000 ease-out"
                style={{ width: `${report.risk_coverage_pct}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3 xl:gap-6">
        {[
          { label: "Requirement Nodes", value: report.requirement_count },
          { label: "Control Definitions", value: report.control_count },
          { label: "Identified Risks", value: report.risk_count },
        ].map(stat => (
          <div
            key={stat.label}
            className="group rounded-[24px] border border-border/40 bg-card/20 p-6 text-center shadow-xl ring-1 ring-white/5 backdrop-blur-md transition-transform duration-500 hover:-translate-y-1 sm:rounded-[28px] sm:p-7 xl:rounded-[32px] xl:p-8"
          >
            <div className="mb-1 text-3xl font-black tracking-tighter text-foreground transition-transform duration-500 group-hover:scale-110 sm:text-4xl">
              {stat.value}
            </div>
            <div className="text-[9px] font-black uppercase tracking-[0.2em] text-muted-foreground/60">
              {stat.label}
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-2 xl:gap-6">
        <FindingGroup
          label="Critical Gaps"
          items={report.findings.filter(f => f.severity === "critical")}
          colorClass="bg-red-500/5 border-red-500/20 text-red-300"
        />
        <FindingGroup
          label="Structural Risks"
          items={report.findings.filter(f => f.severity === "high")}
          colorClass="bg-amber-500/5 border-amber-500/20 text-amber-200"
        />
      </div>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-2 xl:gap-6">
        <FindingGroup
          label="Improvement Areas"
          items={report.findings.filter(f => f.severity === "medium")}
          colorClass="bg-card/30 border-border/40 text-foreground/85"
        />
        <FindingGroup
          label="Minor Signals"
          items={report.findings.filter(f => f.severity === "low")}
          colorClass="bg-card/20 border-border/30 text-foreground/80"
        />
      </div>

      {report.benchmark && (
        <div className="group/bench relative space-y-6 overflow-hidden rounded-[24px] border border-border/40 bg-card/40 p-6 shadow-2xl backdrop-blur-3xl sm:space-y-8 sm:rounded-[32px] sm:p-8 xl:rounded-[40px] xl:p-10">
          <div className="absolute -bottom-12 -right-12 h-64 w-64 bg-primary/5 blur-[100px] opacity-20 transition-opacity duration-1000 group-hover/bench:opacity-40" />
          <header className="relative z-10 flex flex-col gap-4 border-b border-border/40 pb-5 sm:flex-row sm:items-start sm:justify-between sm:gap-6 sm:pb-6">
            <div className="space-y-1">
              <span className="text-[10px] font-black uppercase tracking-[0.2em] text-primary/60">
                Cross-Audit Conformity
              </span>
              <h4 className="text-lg font-black tracking-tight sm:text-xl xl:text-2xl">
                Benchmark Profile: {report.benchmark.profile}
              </h4>
            </div>
            <div className="flex flex-col sm:items-end">
              <span className="mb-1 text-[10px] font-black uppercase tracking-widest text-muted-foreground/40">
                Fitment Rank
              </span>
              <span className="font-mono text-2xl font-black text-primary sm:text-3xl xl:text-4xl">
                {benchmarkScore}
                <span className="text-xs opacity-20 sm:text-sm">/100</span>
              </span>
            </div>
          </header>
          <ul className="relative z-10 grid grid-cols-1 gap-3 sm:gap-4 xl:grid-cols-2 xl:gap-x-8 xl:gap-y-4 2xl:gap-x-12">
            {report.benchmark.findings.map((f, i) => (
              <li
                key={i}
                className="group/bi flex gap-3 rounded-2xl border border-transparent p-3 text-[11px] text-muted-foreground/80 transition-colors hover:border-border/20 hover:bg-white/5 sm:gap-4 sm:p-4 sm:text-xs"
              >
                <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-lg border border-primary/20 bg-primary/10 transition-transform group-hover/bi:rotate-12">
                  <ChevronRight className="h-4 w-4 text-primary" />
                </div>
                <span className="font-medium leading-relaxed">{f}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

function FindingGroup({
  label,
  items,
  colorClass,
}: {
  label: string
  items: GapAnalysisReport["findings"]
  colorClass: string
}) {
  if (items.length === 0) return null

  return (
    <div className={cn("space-y-5 rounded-[24px] border p-5 shadow-xl sm:space-y-6 sm:rounded-[28px] sm:p-6 xl:rounded-[32px] xl:p-8", colorClass)}>
      <div className="flex items-center gap-3 border-b border-current/10 pb-4 sm:gap-4">
        <div className="flex h-8 w-8 items-center justify-center rounded-xl border border-current/20 bg-current/10">
          <AlertCircle className="h-5 w-5" />
        </div>
        <span className="text-[10px] font-black uppercase tracking-[0.18em] sm:text-[11px] sm:tracking-[0.2em]">
          {label} ({items.length})
        </span>
      </div>
      <ul className="space-y-4">
        {items.map((f, i) => (
          <li key={i} className="group/finding space-y-2 border-b border-current/5 pb-4 last:border-0 last:pb-0">
            <div className="text-sm font-black leading-snug text-foreground transition-transform group-hover:translate-x-1 sm:text-base">
              {f.title}
            </div>
            {f.description && (
              <div className="text-[11px] font-semibold italic leading-relaxed opacity-60 sm:text-xs">
                {f.description}
              </div>
            )}
            {(f.requirement_code || f.control_code) && (
              <div className="flex flex-wrap gap-2 pt-2">
                {f.requirement_code && (
                  <span className="rounded-full border border-current/15 bg-current/5 px-2 py-0.5 text-[9px] font-black uppercase tracking-wider">
                    Req {f.requirement_code}
                  </span>
                )}
                {f.control_code && (
                  <span className="rounded-full border border-current/15 bg-current/5 px-2 py-0.5 text-[9px] font-black uppercase tracking-wider">
                    Ctrl {f.control_code}
                  </span>
                )}
              </div>
            )}
          </li>
        ))}
      </ul>
    </div>
  )
}

function healthScoreColor(score: number): string {
  if (score < 40) return "text-red-500 shadow-red-500/20"
  if (score < 70) return "text-amber-500 shadow-amber-500/20"
  return "text-primary shadow-primary/20"
}

function normalizeBenchmarkScore(score: number | null): number {
  if (score == null || Number.isNaN(score)) return 0
  if (score <= 1) return Math.round(score * 100)
  return Math.round(score)
}
