"use client"

import { Sparkles, Loader2, ArrowRight } from "lucide-react"
import { Button, cn } from "@kcontrol/ui"
import { BuildProgressFeed, type ProgressEvent } from "@/components/grc/BuildProgressFeed"
import { type PagePhase } from "../hooks/useBuilder"

interface BuilderActivityPanelProps {
  phase: PagePhase
  feedEvents: ProgressEvent[]
  isStreaming: boolean
  resultFrameworkId: string | null
  onLaunchFramework: (id: string) => void
  className?: string
}

export function BuilderActivityPanel({
  phase,
  feedEvents,
  isStreaming,
  resultFrameworkId,
  onLaunchFramework,
  className,
}: BuilderActivityPanelProps) {
  const isInProgress = isStreaming || phase === "creating" || phase === "enhance_applying"

  return (
    <aside className={cn("flex flex-col h-full bg-muted/5", className)}>
      <header className="flex items-center gap-2 px-4 h-12 border-b shrink-0 bg-background/50 backdrop-blur-sm">
        <Sparkles className="h-4 w-4 text-primary" />
        <span className="text-xs font-bold uppercase tracking-widest">{phaseLabelText(phase)}</span>
        {isInProgress && <Loader2 className="h-3.5 w-3.5 animate-spin text-primary/60 ml-auto shrink-0" />}
      </header>

      <div className="flex-1 overflow-hidden min-h-0">
        <BuildProgressFeed
          events={feedEvents}
          isStreaming={isInProgress}
          phase={
            phase === "idle" ? "idle"
              : ["phase1_streaming", "phase1_review"].includes(phase) ? "phase1"
                : ["phase2_streaming", "phase2_review"].includes(phase) ? "phase2"
                  : phase === "creating" || phase === "enhance_applying" ? "creating"
                    : phase === "complete" || phase === "enhance_complete" ? "complete"
                      : "failed"
          }
          className="h-full"
        />
      </div>

      {(phase === "complete" || phase === "enhance_complete") && resultFrameworkId && (
        <div className="border-t px-4 py-3 shrink-0 bg-background/30">
          <Button
            className="w-full h-8 text-xs font-black uppercase tracking-widest gap-2 shadow-lg shadow-primary/20"
            onClick={() => onLaunchFramework(resultFrameworkId)}
          >
            Launch Framework
            <ArrowRight className="h-3.5 w-3.5" />
          </Button>
        </div>
      )}
    </aside>
  )
}

function phaseLabelText(phase: PagePhase): string {
  switch (phase) {
    case "phase1_streaming": return "Phase 1 - Proposed Structure"
    case "phase1_review": return "Hierarchy Proposed"
    case "phase2_streaming":
    case "phase2_review": return "Ready to Create"
    case "creating": return "Building Framework…"
    case "enhance_applying": return "Applying Changes…"
    case "enhance_complete": return "Enhancements Applied"
    case "complete": return "Build Success"
    case "failed": return "Process Failed"
    default: return "Build Activity"
  }
}
