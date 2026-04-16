"use client"

import { useCallback, useRef, useState } from "react"
import { Sparkles, Loader2, X, ArrowRight } from "lucide-react"
import { cn } from "@/lib/utils"
import { useAIFormFill } from "@/lib/hooks/useAIFormFill"
import type { FormFillRequest } from "@/lib/api/ai"

interface AIFormFillButtonProps {
  /** Build the FormFillRequest. Called when the user clicks "Fill". */
  buildRequest: (intent: string) => FormFillRequest
  /** Called with the parsed fields when fill_complete fires. */
  onFilled: (fields: Record<string, string>) => void
  /** Placeholder for the intent input */
  placeholder?: string
  className?: string
}

/**
 * A compact "AI fill" trigger that expands to an intent input inline.
 *
 * Usage: place this in the dialog header next to the title.
 * When the user types what they want and clicks the arrow (or presses Enter),
 * it streams the form fill and calls onFilled with the resulting field map.
 */
export function AIFormFillButton({
  buildRequest,
  onFilled,
  placeholder = "Describe what you want to create…",
  className,
}: AIFormFillButtonProps) {
  const [expanded, setExpanded] = useState(false)
  const [intent, setIntent] = useState("")
  const inputRef = useRef<HTMLInputElement>(null)

  const handleFilled = useCallback(
    (fields: Record<string, string>) => {
      onFilled(fields)
      setExpanded(false)
      setIntent("")
    },
    [onFilled],
  )

  const { phase, error, fill, reset } = useAIFormFill({ onFilled: handleFilled })

  function handleOpen() {
    setExpanded(true)
    setTimeout(() => inputRef.current?.focus(), 50)
  }

  function handleClose() {
    reset()
    setExpanded(false)
    setIntent("")
  }

  function handleSubmit() {
    if (!intent.trim() || phase === "loading") return
    fill(buildRequest(intent.trim()))
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter") {
      e.preventDefault()
      handleSubmit()
    }
    if (e.key === "Escape") handleClose()
  }

  if (!expanded) {
    return (
      <button
        type="button"
        onClick={handleOpen}
        className={cn(
          "inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-xs font-medium",
          "border border-violet-500/30 bg-violet-500/10 text-violet-600 dark:text-violet-400",
          "hover:bg-violet-500/20 transition-colors",
          className,
        )}
        title="Auto-fill form with AI"
      >
        <Sparkles className="h-3 w-3" />
        AI Fill
      </button>
    )
  }

  return (
    <div className={cn("flex flex-col gap-1.5", className)}>
      <div className="flex items-center gap-1.5">
        <div className="relative flex-1">
          <Sparkles className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3 w-3 text-violet-500 pointer-events-none" />
          <input
            ref={inputRef}
            value={intent}
            onChange={(e) => setIntent(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={phase === "loading"}
            className={cn(
              "w-full h-8 pl-7 pr-3 rounded-lg border text-xs bg-background",
              "border-violet-500/40 focus:outline-none focus:ring-1 focus:ring-violet-500/60",
              "placeholder:text-muted-foreground/50",
              phase === "loading" && "opacity-70 cursor-not-allowed",
            )}
          />
        </div>
        <button
          type="button"
          onClick={handleSubmit}
          disabled={!intent.trim() || phase === "loading"}
          className={cn(
            "h-8 w-8 flex items-center justify-center rounded-lg border transition-colors",
            "border-violet-500/40 bg-violet-500/10 text-violet-600 dark:text-violet-400",
            "hover:bg-violet-500/20",
            "disabled:opacity-40 disabled:cursor-not-allowed",
          )}
          title="Fill form"
        >
          {phase === "loading" ? (
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
          ) : (
            <ArrowRight className="h-3.5 w-3.5" />
          )}
        </button>
        <button
          type="button"
          onClick={handleClose}
          className="h-8 w-8 flex items-center justify-center rounded-lg border border-border/60 text-muted-foreground hover:text-foreground hover:bg-muted/60 transition-colors"
          title="Cancel"
        >
          <X className="h-3.5 w-3.5" />
        </button>
      </div>

      {phase === "loading" && (
        <p className="text-[10px] text-violet-500/80 flex items-center gap-1">
          <span className="inline-block h-1.5 w-1.5 rounded-full bg-violet-500 animate-pulse" />
          Generating form fields…
        </p>
      )}

      {phase === "error" && error && (
        <p className="text-[10px] text-destructive bg-destructive/10 rounded px-2 py-1">
          {error}
        </p>
      )}
    </div>
  )
}
