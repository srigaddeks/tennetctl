"use client"

import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type KeyboardEvent,
} from "react"
import {
  AlertCircle,
  Check,
  ChevronDown,
  Loader2,
  RotateCcw,
  Sparkles,
  X,
  Zap,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { cn } from "@/lib/utils"
import {
  useInlineAIEnhance,
  type UseInlineAIEnhanceConfig,
} from "@/lib/hooks/useInlineAIEnhance"
import { TextDiffView } from "./TextDiffView"

// ── Quick-action presets per field ─────────────────────────────────────────────

const FIELD_PRESETS: Record<string, string[]> = {
  description: [
    "Make it more concise",
    "Add technical precision",
    "Improve clarity and flow",
    "Strengthen the 'why it matters' angle",
  ],
  guidance: [
    "Add framework references (NIST, ISO 27001)",
    "Expand the intent and scope",
    "Make it more actionable",
    "Tighten to 2 paragraphs",
  ],
  implementation_guidance: [
    "Add more specific steps",
    "Add tooling references",
    "Make steps more testable",
    "Reorder by priority",
  ],
  acceptance_criteria: [
    "Make criteria measurable",
    "Add audit evidence requirements",
    "Remove vague language",
    "Add negative test cases",
  ],
  remediation_plan: [
    "Add ownership and timelines",
    "Break into clearer phases",
    "Add validation steps",
    "Make it immediately actionable",
  ],
  notes: [
    "Add dates and versions",
    "Clarify open questions",
    "Flag risks and caveats",
    "Improve readability",
  ],
  business_impact: [
    "Quantify the financial impact",
    "Add regulatory/legal dimension",
    "Cover cascading effects",
    "Write for executive audience",
  ],
  comment_body: [
    "Make it more concise",
    "Add supporting evidence",
    "Add a clear next action",
    "Improve professional tone",
  ],
  title: [
    "Make it more specific",
    "Start with an action verb",
    "Use GRC terminology",
    "Make it unique and distinct",
  ],
  name: [
    "Make it more specific",
    "Use established GRC terminology",
    "Make it concise (3–8 words)",
    "Make it unique and distinct",
  ],
}

const DEFAULT_PRESETS = [
  "Make it more concise",
  "Add technical detail",
  "Improve clarity",
  "Fix grammar and flow",
]

function getPresets(fieldName: string): string[] {
  return FIELD_PRESETS[fieldName] ?? DEFAULT_PRESETS
}

// ── Types ──────────────────────────────────────────────────────────────────────

export interface AIEnhancePopoverProps extends UseInlineAIEnhanceConfig {
  fieldLabel?: string
  placeholder?: string
  className?: string
  popoverSide?: "left" | "right" | "bottom"
}

// ── Current value preview ──────────────────────────────────────────────────────

function CurrentValuePreview({
  value,
  isArray,
}: {
  value: string | string[]
  isArray?: boolean
}) {
  if (isArray) {
    const items = Array.isArray(value)
      ? value
      : value.split("\n").filter(Boolean)
    return (
      <div className="space-y-0.5">
        {items.slice(0, 3).map((item, i) => (
          <div key={i} className="flex items-start gap-1.5 text-xs text-muted-foreground">
            <span className="mt-0.5 h-1 w-1 shrink-0 rounded-full bg-muted-foreground/50" />
            <span className="line-clamp-1">{item}</span>
          </div>
        ))}
        {items.length > 3 && (
          <div className="pl-2.5 text-xs text-muted-foreground/40">
            +{items.length - 3} more…
          </div>
        )}
      </div>
    )
  }
  const text = Array.isArray(value) ? value.join(" ") : value
  return (
    <p className="line-clamp-2 text-xs leading-relaxed text-muted-foreground">
      {text || <span className="italic opacity-50">Empty</span>}
    </p>
  )
}

// ── Popover position classes ───────────────────────────────────────────────────

const POPOVER_POSITION: Record<"left" | "right" | "bottom", string> = {
  right: "left-full ml-2 top-0",
  left:  "right-full mr-2 top-0",
  bottom: "top-full mt-2 left-0",
}

// ── Main Component ─────────────────────────────────────────────────────────────

export function AIEnhancePopover({
  fieldLabel,
  placeholder,
  className,
  popoverSide = "right",
  ...enhanceConfig
}: AIEnhancePopoverProps) {
  const [open, setOpen] = useState(false)
  const [instruction, setInstruction] = useState("")
  const [showPresets, setShowPresets] = useState(false)

  const popoverRef  = useRef<HTMLDivElement>(null)
  const triggerRef  = useRef<HTMLButtonElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const { state, enhance, apply, cancel, reset } = useInlineAIEnhance(enhanceConfig)

  const presets = getPresets(enhanceConfig.fieldName)

  // ── Handlers ────────────────────────────────────────────────────────────────

  const handleClose = useCallback(() => {
    setOpen(false)
    setShowPresets(false)
    // Preserve instruction on close so user can reopen and resume
    if (state.phase !== "idle") reset()
  }, [reset, state.phase])

  const handleOpen = useCallback(() => {
    setOpen(o => !o)
    setShowPresets(false)
  }, [])

  const handleEnhance = useCallback(() => {
    if (!instruction.trim() || state.phase === "loading") return
    setShowPresets(false)
    enhance(instruction.trim())
  }, [instruction, state.phase, enhance])

  const handlePreset = useCallback((preset: string) => {
    setInstruction(preset)
    setShowPresets(false)
    // Auto-submit the preset
    enhance(preset)
  }, [enhance])

  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault()
        handleEnhance()
      }
      if (e.key === "Escape") handleClose()
    },
    [handleEnhance, handleClose],
  )

  const handleApply = useCallback(async () => {
    await apply()
    setInstruction("")
    setOpen(false)
  }, [apply])

  const handleCancelLoading = useCallback(() => {
    cancel()
    // Do NOT clear instruction — let user retry with same text
  }, [cancel])

  const handleTryAgain = useCallback(() => {
    reset()
    // Preserve instruction so user can just click "Enhance" again
  }, [reset])

  const handleKeyboardApply = useCallback(
    (e: globalThis.KeyboardEvent) => {
      if (!open || state.phase !== "showing_diff") return
      if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
        e.preventDefault()
        handleApply()
      }
    },
    [open, state.phase, handleApply],
  )

  // ── Click-outside to close ───────────────────────────────────────────────────

  useEffect(() => {
    if (!open) return
    const handleMouseDown = (e: MouseEvent) => {
      const target = e.target as Node
      if (
        popoverRef.current &&
        !popoverRef.current.contains(target) &&
        triggerRef.current &&
        !triggerRef.current.contains(target)
      ) {
        handleClose()
      }
    }
    document.addEventListener("mousedown", handleMouseDown)
    return () => document.removeEventListener("mousedown", handleMouseDown)
  }, [open, handleClose])

  // ── Global keyboard shortcuts ────────────────────────────────────────────────

  useEffect(() => {
    document.addEventListener("keydown", handleKeyboardApply)
    return () => document.removeEventListener("keydown", handleKeyboardApply)
  }, [handleKeyboardApply])

  useEffect(() => {
    if (!open) return
    const handleEsc = (e: globalThis.KeyboardEvent) => {
      if (e.key === "Escape") handleClose()
    }
    document.addEventListener("keyup", handleEsc)
    return () => document.removeEventListener("keyup", handleEsc)
  }, [open, handleClose])

  // ── Auto-focus textarea when opening in idle state ───────────────────────────

  useEffect(() => {
    if (open && state.phase === "idle") {
      const id = window.setTimeout(() => textareaRef.current?.focus(), 50)
      return () => window.clearTimeout(id)
    }
  }, [open, state.phase])

  // ── Derived ──────────────────────────────────────────────────────────────────

  const totalTokens = state.inputTokens + state.outputTokens
  const hasCurrentValue = Array.isArray(enhanceConfig.currentValue)
    ? enhanceConfig.currentValue.length > 0
    : enhanceConfig.currentValue.length > 0

  const defaultPlaceholder = enhanceConfig.isArrayField
    ? "e.g. Add more specific steps, make it more detailed, reorder by priority…"
    : "e.g. Make it more concise, add technical detail, improve clarity…"

  // ── Render ───────────────────────────────────────────────────────────────────

  return (
    <div className={cn("group/ai relative inline-flex items-center", className)}>
      {/* Trigger */}
      <button
        ref={triggerRef}
        type="button"
        title={`AI-enhance ${fieldLabel ?? "this field"}`}
        aria-label="AI enhance"
        aria-expanded={open}
        onClick={handleOpen}
        className={cn(
          "inline-flex h-6 w-6 items-center justify-center rounded-md",
          "transition-all duration-150",
          "opacity-40 hover:opacity-100 focus:opacity-100 focus-visible:ring-1 focus-visible:ring-violet-500/50 focus-visible:outline-none",
          "hover:bg-violet-500/10 active:bg-violet-500/20",
          (open || state.phase === "loading") && "opacity-100",
        )}
      >
        {state.phase === "loading" ? (
          <Loader2 className="h-3.5 w-3.5 animate-spin text-violet-400" />
        ) : (
          <Sparkles
            className={cn(
              "h-3.5 w-3.5 transition-colors",
              open
                ? "text-violet-400"
                : "text-violet-400",
            )}
          />
        )}
      </button>

      {/* Popover panel */}
      {open && (
        <div
          ref={popoverRef}
          style={{ width: "360px" }}
          className={cn(
            "absolute z-50 rounded-xl border border-border/60",
            "bg-card shadow-xl shadow-black/20",
            "animate-in fade-in-0 zoom-in-95 duration-150",
            POPOVER_POSITION[popoverSide],
          )}
        >
          {/* ── Header ── */}
          <div className="flex items-center justify-between border-b border-border/40 px-3.5 py-2.5">
            <div className="flex items-center gap-1.5">
              <Sparkles className="h-3.5 w-3.5 text-violet-400" />
              <span className="text-xs font-medium text-foreground">
                {fieldLabel ? `Enhance ${fieldLabel}` : "AI Enhance"}
              </span>
            </div>
            <button
              type="button"
              onClick={handleClose}
              aria-label="Close"
              className="rounded p-0.5 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
            >
              <X className="h-3 w-3" />
            </button>
          </div>

          {/* ── Body ── */}
          <div className="space-y-3 p-3.5">

            {/* IDLE */}
            {state.phase === "idle" && (
              <>
                {hasCurrentValue && (
                  <div>
                    <p className="mb-1.5 text-[10px] font-medium uppercase tracking-wide text-muted-foreground/60">
                      Current
                    </p>
                    <div className="rounded-lg border border-border/30 bg-muted/30 dark:bg-zinc-800/50 p-2.5">
                      <CurrentValuePreview
                        value={enhanceConfig.currentValue}
                        isArray={enhanceConfig.isArrayField}
                      />
                    </div>
                  </div>
                )}

                {/* Quick-action presets */}
                <div>
                  <div className="mb-1.5 flex items-center justify-between">
                    <p className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground/60">
                      What changes do you want?
                    </p>
                    <button
                      type="button"
                      onClick={() => setShowPresets(p => !p)}
                      className="flex items-center gap-0.5 rounded px-1 py-0.5 text-[10px] text-violet-400/70 transition-colors hover:bg-violet-500/10 hover:text-violet-400"
                    >
                      Quick actions
                      <ChevronDown className={cn("h-2.5 w-2.5 transition-transform", showPresets && "rotate-180")} />
                    </button>
                  </div>

                  {showPresets && (
                    <div className="mb-2 flex flex-wrap gap-1">
                      {presets.map(preset => (
                        <button
                          key={preset}
                          type="button"
                          onClick={() => handlePreset(preset)}
                          className="rounded-full border border-violet-500/20 bg-violet-500/8 px-2 py-0.5 text-[10px] text-violet-300/80 transition-colors hover:border-violet-500/40 hover:bg-violet-500/15 hover:text-violet-300"
                        >
                          {preset}
                        </button>
                      ))}
                    </div>
                  )}

                  <Textarea
                    ref={textareaRef}
                    value={instruction}
                    onChange={e => setInstruction(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder={placeholder ?? defaultPlaceholder}
                    rows={3}
                    className={cn(
                      "min-h-[72px] resize-none text-xs",
                      "border-border/40 bg-background dark:bg-zinc-800/60 dark:border-zinc-700 placeholder:text-muted-foreground/40",
                      "focus:border-violet-500/50",
                    )}
                  />
                  <p className="mt-1 text-[10px] text-muted-foreground/40">
                    Press Enter to enhance · Shift+Enter for new line
                  </p>
                </div>
              </>
            )}

            {/* LOADING */}
            {state.phase === "loading" && (
              <div>
                <div className="mb-1.5 flex items-center justify-between">
                  <p className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground/60">
                    Enhancing…
                  </p>
                  {instruction && (
                    <p className="max-w-[180px] truncate text-[10px] italic text-muted-foreground/50">
                      "{instruction}"
                    </p>
                  )}
                </div>
                <div className="max-h-[200px] overflow-y-auto min-h-[80px] rounded-lg border border-violet-500/20 bg-muted/30 dark:bg-zinc-800/50 p-2.5">
                  {state.streamedText ? (
                    <p className="whitespace-pre-wrap break-words text-xs leading-relaxed text-foreground/80">
                      {state.streamedText}
                      <span className="ml-0.5 inline-block h-3 w-0.5 animate-pulse bg-violet-400" />
                    </p>
                  ) : (
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      <Loader2 className="h-3 w-3 animate-spin text-violet-400" />
                      <span>Analyzing context and generating enhancement…</span>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* SHOWING DIFF */}
            {state.phase === "showing_diff" && (
              <div>
                <div className="mb-1.5 flex items-center justify-between">
                  <p className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground/60">
                    Proposed Changes
                  </p>
                  {totalTokens > 0 && (
                    <p className="text-[10px] text-muted-foreground/40">
                      {totalTokens.toLocaleString()} tokens
                    </p>
                  )}
                </div>
                <div className="max-h-[260px] overflow-y-auto rounded-lg border border-border/40">
                  <TextDiffView
                    original={state.original}
                    enhanced={state.enhanced}
                    isArrayField={enhanceConfig.isArrayField}
                  />
                </div>
                <p className="mt-1.5 text-[10px] text-muted-foreground/40">
                  ⌘↵ to apply · Esc to dismiss
                </p>
              </div>
            )}

            {/* ERROR */}
            {state.phase === "error" && (
              <div className="flex items-start gap-2 rounded-lg border border-destructive/20 bg-destructive/10 p-3">
                <AlertCircle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-destructive" />
                <div className="min-w-0">
                  <p className="text-xs font-medium text-destructive">Enhancement failed</p>
                  <p className="mt-0.5 text-xs text-muted-foreground">{state.error}</p>
                </div>
              </div>
            )}
          </div>

          {/* ── Footer actions ── */}
          <div className="px-3.5 pb-3.5">
            {state.phase === "idle" && (
              <Button
                type="button"
                size="sm"
                className="h-7 w-full bg-violet-600 text-xs text-white hover:bg-violet-500"
                onClick={handleEnhance}
                disabled={!instruction.trim()}
              >
                <Sparkles className="mr-1.5 h-3 w-3" />
                Enhance with AI
              </Button>
            )}

            {state.phase === "loading" && (
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="h-7 w-full text-xs text-muted-foreground hover:text-foreground"
                onClick={handleCancelLoading}
              >
                Cancel
              </Button>
            )}

            {state.phase === "showing_diff" && (
              <div className="flex gap-2">
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="h-7 flex-1 text-xs"
                  onClick={handleTryAgain}
                >
                  <RotateCcw className="mr-1.5 h-3 w-3" />
                  Try Again
                </Button>
                <Button
                  type="button"
                  size="sm"
                  className="h-7 flex-1 bg-emerald-600 text-xs text-white hover:bg-emerald-500"
                  onClick={handleApply}
                >
                  <Check className="mr-1.5 h-3 w-3" />
                  Apply
                </Button>
              </div>
            )}

            {state.phase === "error" && (
              <div className="flex gap-2">
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="h-7 flex-1 text-xs"
                  onClick={handleClose}
                >
                  Dismiss
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  className="h-7 flex-1 text-xs"
                  onClick={handleTryAgain}
                >
                  <RotateCcw className="mr-1.5 h-3 w-3" />
                  Try Again
                </Button>
              </div>
            )}
          </div>

          {/* ── Powered-by footer ── */}
          <div className="border-t border-border/20 px-3.5 pb-2.5 pt-2">
            <div className="flex items-center gap-1">
              <Zap className="h-2.5 w-2.5 text-muted-foreground/30" />
              <span className="text-[10px] text-muted-foreground/30">Powered by K-Control AI</span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
