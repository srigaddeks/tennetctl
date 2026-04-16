"use client"

import { useEffect, useRef } from "react"
import {
  CheckCircle2,
  AlertCircle,
  Zap,
  Shield,
  Link2,
  FileText,
  Database,
  Sparkles,
} from "lucide-react"
import { cn } from "@kcontrol/ui"

// ── Types ──────────────────────────────────────────────────────────────────────

export interface ProgressEvent {
  event: string
  [key: string]: unknown
}

interface BuildProgressFeedProps {
  events: ProgressEvent[]
  isStreaming?: boolean
  phase?: "idle" | "phase1" | "phase2" | "creating" | "complete" | "failed"
  className?: string
}

// ── Criticality badge ──────────────────────────────────────────────────────────

function CriticalityBadge({ value }: { value: string }) {
  const map: Record<string, string> = {
    critical: "bg-red-100 text-red-700 border-red-300",
    high: "bg-orange-100 text-orange-700 border-orange-300",
    medium: "bg-yellow-100 text-yellow-700 border-yellow-300",
    low: "bg-green-100 text-green-700 border-green-300",
  }
  return (
    <span className={cn("px-1.5 py-0.5 rounded border text-[10px] font-semibold uppercase tracking-wide", map[value] ?? "bg-muted text-muted-foreground border-border")}>
      {value}
    </span>
  )
}

// ── Individual event renderers ─────────────────────────────────────────────────

function EventRow({ ev }: { ev: ProgressEvent }) {
  switch (ev.event) {
    // ── Stage divider ──────────────────────────────────────────────────────────
    case "stage_start": {
      const label = (ev.label as string) || (ev.stage as string) || "Stage"
      return (
        <div className="flex items-center gap-2 py-1.5">
          <div className="h-px flex-1 bg-border" />
          <span className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-widest text-muted-foreground px-2">
            <Sparkles className="h-3 w-3" />
            {label}
          </span>
          <div className="h-px flex-1 bg-border" />
        </div>
      )
    }

    // ── LLM call lifecycle ────────────────────────────────────────────────────
    case "llm_call_start": {
      const message = (ev.message as string) || "Starting AI generation…"
      const model = ev.model as string
      return (
        <div className="flex items-center gap-2.5 px-3 py-2 rounded-lg bg-blue-50 border border-blue-200/60">
          <Sparkles className="h-4 w-4 text-blue-500 shrink-0 animate-pulse" />
          <div className="flex-1 min-w-0">
            <span className="text-sm font-semibold text-blue-800">{message}</span>
            {model && <span className="ml-2 text-[10px] text-blue-500/70 font-mono">{model}</span>}
          </div>
        </div>
      )
    }

    case "llm_call_complete": {
      const message = (ev.message as string) || "AI generation complete"
      const elapsed = ev.elapsed_seconds as number
      const promptTokens = ev.prompt_tokens as number | undefined
      const completionTokens = ev.completion_tokens as number | undefined
      const model = ev.model as string | undefined
      const systemChars = ev.system_chars as number | undefined
      const userChars = ev.user_chars as number | undefined
      const responseChars = ev.response_chars as number | undefined
      const hasTokenInfo = promptTokens || completionTokens
      return (
        <div className="rounded-lg bg-emerald-50 border border-emerald-200/60 px-3 py-2 space-y-1.5">
          <div className="flex items-center gap-2.5">
            <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0" />
            <span className="text-sm font-semibold text-emerald-800">{message}</span>
            {elapsed > 0 && (
              <span className="ml-auto text-xs text-emerald-600 font-mono shrink-0">{elapsed}s</span>
            )}
          </div>
          {(hasTokenInfo || model) && (
            <div className="flex flex-wrap gap-x-3 gap-y-1 pl-6 text-[10px] font-mono text-emerald-600/70">
              {model && <span>model: {model}</span>}
              {promptTokens != null && <span>prompt: {promptTokens.toLocaleString()} tk</span>}
              {completionTokens != null && <span>response: {completionTokens.toLocaleString()} tk</span>}
              {systemChars != null && <span>sys: {(systemChars / 1000).toFixed(1)}k chars</span>}
              {userChars != null && <span>user: {(userChars / 1000).toFixed(1)}k chars</span>}
              {responseChars != null && <span>output: {(responseChars / 1000).toFixed(1)}k chars</span>}
            </div>
          )}
        </div>
      )
    }

    // ── LLM response preview ────────────────────────────────────────────────
    case "llm_response_preview": {
      const preview = ev.preview as string
      const totalChars = ev.total_chars as number
      if (!preview) return null
      return (
        <details className="group rounded-lg border border-slate-200/60 bg-slate-50/50 px-3 py-2">
          <summary className="flex cursor-pointer items-center gap-2 text-[11px] font-semibold text-slate-500 select-none">
            <FileText className="h-3.5 w-3.5 shrink-0" />
            <span>AI Response Preview</span>
            {totalChars > 0 && <span className="ml-auto font-mono text-[10px] text-slate-400">{(totalChars / 1000).toFixed(1)}k chars</span>}
          </summary>
          <pre className="mt-2 max-h-40 overflow-y-auto whitespace-pre-wrap text-[11px] leading-relaxed text-slate-600 font-mono bg-white/60 rounded p-2 border border-slate-100">
            {preview}
          </pre>
        </details>
      )
    }

    // ── Heartbeat with progress message ─────────────────────────────────────
    case "heartbeat": {
      const message = ev.message as string
      if (!message) return null
      const elapsed = ev.elapsed_seconds as number
      return (
        <div className="flex items-center gap-1.5 pl-4 text-xs text-blue-600/70">
          <span className="h-1.5 w-1.5 rounded-full bg-blue-400 animate-pulse shrink-0" />
          <span className="font-medium">{message}</span>
          {elapsed > 0 && (
            <span className="ml-auto text-[10px] text-blue-400/60 font-mono shrink-0">{elapsed}s</span>
          )}
        </div>
      )
    }

    // ── LLM streaming chunk (real agent output) ──────────────────────────────
    case "llm_chunk": {
      const chars = ev.chars_received as number
      const elapsed = ev.elapsed_seconds as number
      const preview = ev.preview as string
      const model = ev.model as string | undefined
      return (
        <div className="pl-4 space-y-0.5">
          <div className="flex items-center gap-2 text-[10px] text-blue-500/70 font-mono">
            <span className="h-1.5 w-1.5 rounded-full bg-blue-400 animate-pulse shrink-0" />
            <span>{(chars / 1000).toFixed(1)}k chars</span>
            {elapsed > 0 && <span>{elapsed}s</span>}
            {model && <span className="text-blue-400/50">{model}</span>}
          </div>
          {preview && (
            <pre className="text-[10px] leading-relaxed text-slate-500 font-mono truncate max-w-[20rem] pl-3.5">{preview}</pre>
          )}
        </div>
      )
    }

    // ── LLM retry (transient error) ──────────────────────────────────────────
    case "llm_retry": {
      const message = (ev.message as string) || "Retrying…"
      const attempt = ev.attempt as number
      const maxRetries = ev.max_retries as number
      const wait = ev.wait_seconds as number
      return (
        <div className="rounded-lg border border-amber-300 bg-amber-50 px-3 py-2 space-y-1">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-4 w-4 text-amber-600 shrink-0" />
            <span className="text-sm font-semibold text-amber-800">Retry {attempt}/{maxRetries}</span>
            {wait > 0 && (
              <span className="ml-auto text-xs text-amber-600 font-mono shrink-0">wait {Math.round(wait / 60)}m</span>
            )}
          </div>
          <p className="text-xs text-amber-700 leading-relaxed pl-6">{message}</p>
        </div>
      )
    }

    // ── Enhance analysis started ──────────────────────────────────────────────
    case "analyzing_framework": {
      const message = (ev.message as string) || "Analyzing framework..."
      return (
        <div className="flex items-center gap-2.5 px-3 py-2 rounded-lg bg-amber-50 border border-amber-200/60">
          <Sparkles className="h-4 w-4 text-amber-500 shrink-0" />
          <span className="text-sm font-semibold text-amber-800">{message}</span>
        </div>
      )
    }

    // ── Framework creation header ──────────────────────────────────────────────
    case "creating_framework": {
      const code = ev.framework_code as string
      return (
        <div className="flex items-center gap-2.5 px-3 py-2 rounded-lg bg-indigo-50 border border-indigo-200/60">
          <Database className="h-4 w-4 text-indigo-500 shrink-0" />
          <span className="text-sm font-semibold text-indigo-800">Creating framework</span>
          {code && (
            <span className="ml-auto font-mono text-xs text-indigo-600 bg-indigo-100 px-2 py-0.5 rounded">
              {code}
            </span>
          )}
        </div>
      )
    }

    // ── Requirement created ────────────────────────────────────────────────────
    case "requirement_created": {
      const code = ev.code as string
      return (
        <div className="flex items-center gap-1.5 pl-4 text-xs text-muted-foreground">
          <CheckCircle2 className="h-3 w-3 shrink-0 text-slate-400" />
          <span className="font-mono text-slate-500">{code}</span>
          <span className="text-slate-400">requirement</span>
        </div>
      )
    }

    // ── Requirement ready (Phase 1 feed) ──────────────────────────────────────
    case "requirement_ready": {
      const code = ev.code as string
      const name = ev.name as string
      return (
        <div className="flex items-center gap-1.5 pl-4 text-xs text-muted-foreground">
          <CheckCircle2 className="h-3 w-3 shrink-0 text-slate-400" />
          <span className="font-mono text-slate-500">{code}</span>
          {name && <span className="text-slate-400 truncate max-w-[14rem]">{name}</span>}
        </div>
      )
    }

    // ── Control created ────────────────────────────────────────────────────────
    case "control_created": {
      const code = ev.code as string
      return (
        <div className="flex items-center gap-1.5 pl-6">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 shrink-0" />
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-50 border border-emerald-200 text-[11px] font-mono text-emerald-700">
            <Zap className="h-2.5 w-2.5" />
            {code}
          </span>
        </div>
      )
    }

    // ── Control proposed (Phase 2 SSE) ─────────────────────────────────────────
    case "control_proposed": {
      const code = ev.code as string
      const name = ev.name as string
      const criticality = (ev.criticality as string) || ""
      return (
        <div className="flex items-center gap-1.5 pl-6 flex-wrap">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 shrink-0" />
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-50 border border-emerald-200 text-[11px] font-mono text-emerald-700">
            <Zap className="h-2.5 w-2.5" />
            {code}
          </span>
          {name && <span className="text-xs text-muted-foreground truncate max-w-[12rem]">{name}</span>}
          {criticality && <CriticalityBadge value={criticality} />}
        </div>
      )
    }

    // ── Risk created ───────────────────────────────────────────────────────────
    case "risk_created": {
      const code = ev.code as string
      return (
        <div className="flex items-center gap-1.5 pl-6">
          <span className="h-1.5 w-1.5 rounded-full bg-purple-400 shrink-0" />
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-purple-50 border border-purple-200 text-[11px] font-mono text-purple-700">
            <Shield className="h-2.5 w-2.5" />
            {code}
          </span>
          <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-purple-600 text-white">NEW</span>
        </div>
      )
    }

    // ── Risk reused (existing) ────────────────────────────────────────────────
    case "risk_reused": {
      const code = ev.code as string
      const reason = ev.reason as string | undefined
      return (
        <div className="flex items-center gap-1.5 pl-6">
          <span className="h-1.5 w-1.5 rounded-full bg-indigo-400 shrink-0" />
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-indigo-50 border border-indigo-200 text-[11px] font-mono text-indigo-700">
            <Shield className="h-2.5 w-2.5" />
            {code}
          </span>
          <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-slate-600 text-white">REUSED</span>
          {reason && (
            <span className="text-[10px] text-muted-foreground">{reason.replaceAll("_", " ")}</span>
          )}
        </div>
      )
    }

    // ── Risk linked ────────────────────────────────────────────────────────────
    case "risk_linked": {
      const controlCode = (ev.control_code as string) || (ev.control_id as string)
      const riskCode = ev.risk_code as string
      return (
        <div className="flex items-center gap-1 pl-8 text-[11px] text-muted-foreground">
          <Link2 className="h-3 w-3 text-slate-400 shrink-0" />
          <span className="font-mono text-slate-400">{controlCode}</span>
          <span>→</span>
          <span className="font-mono text-purple-500">{riskCode}</span>
        </div>
      )
    }

    // ── Risk mapped (Phase 2 SSE) ──────────────────────────────────────────────
    case "risk_mapped": {
      const controlCode = ev.control_code as string
      const riskCode = ev.risk_code as string
      const isNew = ev.is_new as boolean
      return (
        <div className="flex items-center gap-1.5 pl-8">
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-indigo-50 border border-indigo-200 text-[11px] font-mono text-indigo-700">
            <Link2 className="h-2.5 w-2.5" />
            {controlCode} → {riskCode}
          </span>
          {isNew && (
            <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-purple-600 text-white">NEW</span>
          )}
        </div>
      )
    }

    // ── Risk mapping warning ────────────────────────────────────────────────
    case "risk_mapping_warning": {
      const message = (ev.message as string) || "Some controls remain unmapped."
      const unmapped = Array.isArray(ev.unmapped_control_codes)
        ? (ev.unmapped_control_codes as unknown[]).map((value) => String(value)).filter(Boolean)
        : []
      return (
        <div className="rounded-xl border border-red-300 bg-red-50 p-3 space-y-2">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-4 w-4 text-red-600 shrink-0" />
            <span className="text-sm font-semibold text-red-800">{message}</span>
          </div>
          {unmapped.length > 0 && (
            <div className="text-xs text-red-700">
              Unmapped controls:{" "}
              <span className="font-mono">{unmapped.slice(0, 10).join(", ")}</span>
              {unmapped.length > 10 ? ` +${unmapped.length - 10} more` : ""}
            </div>
          )}
        </div>
      )
    }

    // ── Enhance proposal streamed ─────────────────────────────────────────────
    case "change_proposed": {
      const changeType = (ev.change_type as string) || "change"
      const entityCode = (ev.entity_code as string) || (ev.entity_type as string) || "item"
      return (
        <div className="flex items-center gap-1.5 pl-4 text-xs text-muted-foreground">
          <Sparkles className="h-3 w-3 text-amber-500 shrink-0" />
          <span className="font-mono text-slate-500">{entityCode}</span>
          <span className="text-slate-400">{changeType}</span>
        </div>
      )
    }

    // ── Enhance stream complete ───────────────────────────────────────────────
    case "enhance_complete": {
      const count = ev.proposal_count as number
      return (
        <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-amber-50 border border-amber-200/60">
          <CheckCircle2 className="h-4 w-4 text-amber-600 shrink-0" />
          <span className="text-sm font-semibold text-amber-900">Enhancement analysis complete</span>
          <span className="ml-auto text-xs text-amber-700 font-medium">{count} proposals</span>
        </div>
      )
    }

    // ── Doc analyzed ──────────────────────────────────────────────────────────
    case "doc_analyzed": {
      const filename = ev.filename as string
      const pct = ev.pct as number
      return (
        <div className="flex items-center gap-2 pl-4 text-xs text-muted-foreground">
          <FileText className="h-3 w-3 text-slate-400 shrink-0" />
          <span className="truncate max-w-[12rem]">{filename}</span>
          <div className="flex-1 h-1.5 rounded-full bg-muted overflow-hidden min-w-[4rem]">
            <div
              className="h-full rounded-full bg-blue-400 transition-all"
              style={{ width: `${Math.min(pct, 100)}%` }}
            />
          </div>
          <span className="font-mono text-slate-500 shrink-0">{pct}%</span>
        </div>
      )
    }

    // ── Phase 1 complete ───────────────────────────────────────────────────────
    case "phase1_complete": {
      const reqCount = ev.requirement_count as number
      return (
        <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-blue-50 border border-blue-200/60">
          <CheckCircle2 className="h-4 w-4 text-blue-500 shrink-0" />
          <span className="text-sm font-semibold text-blue-800">Phase 1 complete</span>
          <span className="ml-auto text-xs text-blue-600 font-medium">{reqCount} requirements</span>
        </div>
      )
    }

    // ── Phase 2 complete ───────────────────────────────────────────────────────
    case "phase2_complete": {
      const controlCount = ev.control_count as number
      const riskCount = ev.risk_count as number
      return (
        <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-emerald-50 border border-emerald-200/60">
          <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0" />
          <span className="text-sm font-semibold text-emerald-800">Phase 2 complete</span>
          <span className="ml-auto text-xs text-emerald-600 font-medium">
            {controlCount} controls · {riskCount} risks
          </span>
        </div>
      )
    }

    // ── Creation complete ──────────────────────────────────────────────────────
    case "creation_complete": {
      const reqCount = ev.requirement_count as number
      const controlCount = ev.control_count as number
      const riskCount = ev.risk_count as number
      return (
        <div className="rounded-xl border border-emerald-300 bg-emerald-50 p-4 space-y-3">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="h-5 w-5 text-emerald-600 shrink-0" />
            <span className="text-base font-bold text-emerald-800">Framework created successfully</span>
          </div>
          <div className="grid grid-cols-2 gap-2 text-center">
            <div className="rounded-lg bg-white border border-emerald-200 py-2 px-1">
              <div className="text-xl font-bold text-emerald-700">{reqCount}</div>
              <div className="text-[11px] text-muted-foreground">Requirements</div>
            </div>
            <div className="rounded-lg bg-white border border-emerald-200 py-2 px-1">
              <div className="text-xl font-bold text-emerald-700">{controlCount}</div>
              <div className="text-[11px] text-muted-foreground">Controls</div>
            </div>
            <div className="col-span-2 rounded-lg bg-white border border-emerald-200 py-2 px-1">
              <div className="text-xl font-bold text-purple-600">{riskCount}</div>
              <div className="text-[11px] text-muted-foreground">Risks linked</div>
            </div>
          </div>
        </div>
      )
    }

    // ── Creation error ─────────────────────────────────────────────────────────
    case "creation_error": {
      const stage = ev.stage as string
      const message = ev.message as string
      return (
        <div className="rounded-xl border border-red-300 bg-red-50 p-4 space-y-1.5">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5 text-red-600 shrink-0" />
            <span className="text-sm font-bold text-red-800">Creation failed</span>
            {stage && (
              <span className="ml-auto font-mono text-xs text-red-500 bg-red-100 px-1.5 py-0.5 rounded">
                {stage}
              </span>
            )}
          </div>
          {message && <p className="text-xs text-red-700 leading-relaxed pl-7">{message}</p>}
        </div>
      )
    }

    // ── Enhance apply progress ────────────────────────────────────────────────
    case "change_applied": {
      const code = ev.entity_code as string
      const changeType = ev.change_type as string
      return (
        <div className="flex items-center gap-1.5 pl-4 text-xs text-emerald-700">
          <CheckCircle2 className="h-3.5 w-3.5 shrink-0 text-emerald-600" />
          <span className="font-mono">{code || "item"}</span>
          <span className="text-emerald-600/80">{changeType || "updated"}</span>
        </div>
      )
    }

    case "change_failed": {
      const code = ev.entity_code as string
      const changeType = ev.change_type as string
      const error = ev.error as string
      return (
        <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700">
          <div className="flex items-center gap-1.5">
            <AlertCircle className="h-3.5 w-3.5 shrink-0 text-red-500" />
            <span className="font-mono">{code || "item"}</span>
            <span>{changeType || "change"} failed</span>
          </div>
          {error && <p className="mt-1 text-red-600/90">{error}</p>}
        </div>
      )
    }

    // ── Document indexing events ───────────────────────────────────────────────
    case "doc_analyzing":
    case "indexing_documents": {
      const filename = ev.filename as string
      const message = (ev.message as string) || (filename ? `Indexing ${filename}…` : "Indexing documents…")
      const pct = ev.pct as number | undefined
      return (
        <div className="flex items-center gap-2 pl-4 text-xs text-blue-600/70">
          <FileText className="h-3.5 w-3.5 shrink-0 animate-pulse" />
          <span className="font-medium">{message}</span>
          {pct != null && <span className="ml-auto text-[10px] font-mono text-blue-400/60">{pct}%</span>}
        </div>
      )
    }

    case "doc_analysis_warning": {
      const message = (ev.message as string) || "Document analysis warning"
      return (
        <div className="flex items-center gap-2 pl-4 text-xs text-amber-600/80">
          <AlertCircle className="h-3.5 w-3.5 shrink-0" />
          <span className="font-medium">{message}</span>
        </div>
      )
    }

    case "generating_structure": {
      const message = (ev.message as string) || "Generating structure…"
      return (
        <div className="flex items-center gap-1.5 pl-4 text-xs text-blue-600/70">
          <span className="h-1.5 w-1.5 rounded-full bg-blue-400 animate-pulse shrink-0" />
          <span className="font-medium">{message}</span>
        </div>
      )
    }

    case "gap_analysis_complete": {
      const message = (ev.message as string) || "Gap analysis complete"
      const score = ev.health_score as number | undefined
      return (
        <div className="flex items-center gap-2.5 px-3 py-2 rounded-lg bg-emerald-50 border border-emerald-200/60">
          <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0" />
          <span className="text-sm font-semibold text-emerald-800">{message}</span>
          {score != null && <span className="ml-auto text-xs font-mono text-emerald-600">{score}/100</span>}
        </div>
      )
    }

    // ── Task builder: progress events ────────────────────────────────────────
    case "controls_loaded": {
      const controlCount = ev.control_count as number
      const existingCount = ev.existing_task_count as number
      return (
        <div className="flex items-center gap-2 pl-4 text-xs text-blue-600/70">
          <Database className="h-3.5 w-3.5 shrink-0" />
          <span className="font-medium">{(ev.message as string) || `${controlCount} controls, ${existingCount} existing tasks`}</span>
        </div>
      )
    }

    case "doc_ready": {
      return (
        <div className="flex items-center gap-2 pl-4 text-xs text-emerald-600/80">
          <CheckCircle2 className="h-3.5 w-3.5 shrink-0" />
          <span className="font-medium">{(ev.message as string) || "Document context ready"}</span>
        </div>
      )
    }

    case "chunk_start": {
      const chunk = ev.chunk as number
      const total = ev.total_chunks as number
      return (
        <div className="flex items-center gap-2 pl-4 text-xs text-blue-600/70">
          <span className="h-1.5 w-1.5 rounded-full bg-blue-400 animate-pulse shrink-0" />
          <span className="font-medium">{(ev.message as string) || `Processing batch ${chunk}/${total}`}</span>
          {total > 0 && (
            <span className="ml-auto text-[10px] font-mono text-blue-400/60">{Math.round((chunk / total) * 100)}%</span>
          )}
        </div>
      )
    }

    case "chunk_complete": {
      const chunk = ev.chunk as number
      const total = ev.total_chunks as number
      const chunkTasks = ev.chunk_task_count as number
      const runningTotal = ev.running_total as number
      return (
        <div className="flex items-center gap-2 pl-4 text-xs text-emerald-600/80">
          <CheckCircle2 className="h-3.5 w-3.5 shrink-0" />
          <span className="font-medium">Batch {chunk}/{total}: {chunkTasks} tasks</span>
          {runningTotal != null && (
            <span className="ml-auto text-[10px] font-mono text-emerald-500/70">{runningTotal} total</span>
          )}
        </div>
      )
    }

    case "chunk_error":
    case "chunk_parse_error": {
      return (
        <div className="flex items-center gap-2 pl-4 text-xs text-amber-600/80">
          <AlertCircle className="h-3.5 w-3.5 shrink-0" />
          <span className="font-medium">{(ev.message as string) || "Batch processing error"}</span>
        </div>
      )
    }

    case "preview_complete": {
      const taskCount = ev.task_count as number
      const groupCount = ev.group_count as number
      return (
        <div className="rounded-xl border border-emerald-300 bg-emerald-50 p-4 space-y-2">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="h-5 w-5 text-emerald-600 shrink-0" />
            <span className="text-base font-bold text-emerald-800">Preview complete</span>
          </div>
          <div className="grid grid-cols-2 gap-2 text-center">
            <div className="rounded-lg bg-white border border-emerald-200 py-2 px-1">
              <div className="text-xl font-bold text-emerald-700">{taskCount}</div>
              <div className="text-[11px] text-muted-foreground">Tasks generated</div>
            </div>
            <div className="rounded-lg bg-white border border-emerald-200 py-2 px-1">
              <div className="text-xl font-bold text-emerald-700">{groupCount}</div>
              <div className="text-[11px] text-muted-foreground">Controls covered</div>
            </div>
          </div>
        </div>
      )
    }

    case "control_processing": {
      const controlCode = ev.control_code as string
      const progress = ev.progress as number
      const total = ev.total as number
      return (
        <div className="flex items-center gap-2 pl-4 text-xs text-blue-600/70">
          <span className="h-1.5 w-1.5 rounded-full bg-blue-400 animate-pulse shrink-0" />
          <span className="font-medium">{controlCode}</span>
          <span className="text-blue-500/60">({progress}/{total})</span>
        </div>
      )
    }

    case "control_complete": {
      const controlCode = ev.control_code as string
      const created = ev.created as number
      const skipped = ev.skipped as number
      return (
        <div className="flex items-center gap-1.5 pl-4 text-xs text-emerald-700">
          <CheckCircle2 className="h-3.5 w-3.5 shrink-0 text-emerald-600" />
          <span className="font-mono">{controlCode}</span>
          <span className="text-emerald-600/80">{created} created{skipped > 0 ? `, ${skipped} skipped` : ""}</span>
        </div>
      )
    }

    case "apply_complete": {
      const created = ev.created as number
      const skipped = ev.skipped as number
      return (
        <div className="rounded-xl border border-emerald-300 bg-emerald-50 p-4 space-y-2">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="h-5 w-5 text-emerald-600 shrink-0" />
            <span className="text-base font-bold text-emerald-800">Tasks created successfully</span>
          </div>
          <div className="grid grid-cols-2 gap-2 text-center">
            <div className="rounded-lg bg-white border border-emerald-200 py-2 px-1">
              <div className="text-xl font-bold text-emerald-700">{created}</div>
              <div className="text-[11px] text-muted-foreground">Created</div>
            </div>
            <div className="rounded-lg bg-white border border-emerald-200 py-2 px-1">
              <div className="text-xl font-bold text-amber-600">{skipped}</div>
              <div className="text-[11px] text-muted-foreground">Skipped</div>
            </div>
          </div>
        </div>
      )
    }

    case "error": {
      const stage = ev.stage as string
      const message = ev.message as string
      return (
        <div className="rounded-xl border border-red-300 bg-red-50 p-4 space-y-1.5">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5 text-red-600 shrink-0" />
            <span className="text-sm font-bold text-red-800">Error</span>
            {stage && (
              <span className="ml-auto font-mono text-xs text-red-500 bg-red-100 px-1.5 py-0.5 rounded">
                {stage}
              </span>
            )}
          </div>
          {message && <p className="text-xs text-red-700 leading-relaxed pl-7">{message}</p>}
        </div>
      )
    }

    // ── Unknown event (dev fallback) ───────────────────────────────────────────
    default: {
      const message = ev.message as string
      if (message) {
        return (
          <div className="flex items-center gap-1.5 pl-4 text-xs text-muted-foreground">
            <span className="h-1.5 w-1.5 rounded-full bg-slate-300 shrink-0" />
            <span>{message}</span>
          </div>
        )
      }
      return (
        <div className="flex items-center gap-1.5 pl-4 text-[11px] text-muted-foreground/60 font-mono">
          <span className="text-slate-400">{ev.event}</span>
        </div>
      )
    }
  }
}

// ── Animated waiting dots ──────────────────────────────────────────────────────

function WaitingDots() {
  return (
    <span className="inline-flex gap-0.5 items-end ml-0.5">
      {[0, 1, 2].map(i => (
        <span
          key={i}
          className="block h-1 w-1 rounded-full bg-current animate-bounce"
          style={{ animationDelay: `${i * 0.15}s`, animationDuration: "0.8s" }}
        />
      ))}
    </span>
  )
}

// ── Main component ─────────────────────────────────────────────────────────────

export function BuildProgressFeed({ events, isStreaming, phase, className }: BuildProgressFeedProps) {
  const bottomRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom when new events arrive
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [events.length])

  const isEmpty = events.length === 0

  return (
    <div className={cn("flex flex-col h-full", className)}>
      <div className="flex-1 overflow-y-auto px-3 py-2 space-y-1.5">
        {isEmpty && isStreaming ? (
          <div className="flex items-center gap-1.5 text-xs text-muted-foreground py-4 justify-center">
            <Sparkles className="h-3.5 w-3.5 animate-pulse" />
            <span>Waiting for agent</span>
            <WaitingDots />
          </div>
        ) : isEmpty ? (
          <div className="flex flex-col items-center justify-center py-8 text-center gap-2 text-muted-foreground">
            <Database className="h-7 w-7 opacity-30" />
            <span className="text-xs">No activity yet</span>
          </div>
        ) : (
          events.map((ev, idx) => (
            <EventRow key={idx} ev={ev} />
          ))
        )}

        {/* Streaming pulse indicator */}
        {isStreaming && events.length > 0 && (
          <div className="flex items-center gap-1.5 pl-4 py-0.5 text-[11px] text-muted-foreground">
            <span className="h-1.5 w-1.5 rounded-full bg-blue-400 animate-pulse shrink-0" />
            <span>Streaming</span>
            <WaitingDots />
          </div>
        )}

        <div ref={bottomRef} />
      </div>
    </div>
  )
}
