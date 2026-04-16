"use client"

import { PlusCircle, History } from "lucide-react"
import { Badge, cn } from "@kcontrol/ui"
import { type BuilderSession } from "@/lib/api/ai"

interface BuilderSidebarProps {
  sessions: BuilderSession[]
  activeSessionId: string | null
  onSessionSelect: (session: BuilderSession) => void
  onNewSession: () => void
  className?: string
}

export function BuilderSidebar({
  sessions,
  activeSessionId,
  onSessionSelect,
  onNewSession,
  className,
}: BuilderSidebarProps) {
  return (
    <aside className={cn("flex flex-col h-full bg-muted/5", className)}>
      <header className="flex items-center justify-between px-4 h-12 border-b shrink-0 bg-background/50 backdrop-blur-sm">
        <div className="flex items-center gap-2">
          <History className="h-4 w-4 text-muted-foreground/60" />
          <span className="text-xs font-bold uppercase tracking-widest text-muted-foreground/80">Recent Sessions</span>
        </div>
        <button
          onClick={onNewSession}
          className="p-1 hover:bg-primary/10 rounded-full transition-colors group"
          title="New Session"
        >
          <PlusCircle className="h-4 w-4 text-muted-foreground/60 group-hover:text-primary transition-colors" />
        </button>
      </header>

      <div className="flex-1 overflow-y-auto overflow-x-hidden p-2 space-y-1 custom-scrollbar">
        {sessions.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 gap-3 opacity-20 grayscale">
            <PlusCircle className="h-8 w-8" />
            <p className="text-[10px] font-bold uppercase tracking-widest">No sessions yet</p>
          </div>
        ) : (
          sessions.map((s) => (
            <SessionItem
              key={s.id}
              session={s}
              isActive={activeSessionId === s.id}
              onSelect={onSessionSelect}
            />
          ))
        )}
      </div>
    </aside>
  )
}

// ── Session item ─────────────────────────────────────────────────────────────

function SessionItem({
  session: s,
  isActive,
  onSelect,
}: {
  session: BuilderSession
  isActive: boolean
  onSelect: (session: BuilderSession) => void
}) {
  return (
    <button
      onClick={() => onSelect(s)}
      className={cn(
        "group w-full flex flex-col p-3 rounded-xl transition-all border duration-200 text-left",
        isActive
          ? "bg-primary/10 border-primary/20 shadow-lg shadow-primary/5 ring-1 ring-primary/10"
          : "bg-transparent border-transparent hover:bg-muted/40 hover:border-border/40"
      )}
    >
      <div className="flex items-center justify-between w-full mb-1">
        <span className={cn(
          "text-[11px] font-bold truncate pr-2 transition-colors",
          isActive ? "text-primary" : "text-foreground/80 group-hover:text-foreground"
        )}>
          {s.framework_name || "Untitled Framework"}
        </span>
        {sessionStatusBadge(s.status)}
      </div>
      <div className="flex items-center justify-between w-full">
        <span className="text-[9px] font-bold text-muted-foreground/40 uppercase tracking-tighter">
          {new Date(s.updated_at || s.created_at).toLocaleDateString(undefined, {
            month: "short",
            day: "numeric",
            hour: "numeric",
            minute: "2-digit",
          })}
        </span>
        <span className="text-[9px] font-black uppercase tracking-widest text-primary/40 group-hover:text-primary/70 transition-colors">
          {s.session_type === "enhance" ? "Enhance" : s.session_type === "gap" ? "Coverage" : "Build"}
        </span>
      </div>
    </button>
  )
}

// ── Status badge ────────────────────────────────────────────────────────────

function sessionStatusBadge(status: string) {
  switch (status) {
    case "idle":
    case "draft":
      return (
        <Badge variant="outline" className="text-[9px] bg-muted/20 text-muted-foreground border-border/50 px-1.5 h-4 font-black uppercase tracking-tighter">
          Idle
        </Badge>
      )
    case "phase1_streaming":
    case "phase2_streaming":
      return (
        <Badge variant="outline" className="text-[9px] bg-blue-500/10 text-blue-400 border-blue-500/20 animate-pulse px-1.5 h-4 font-black uppercase tracking-tighter">
          Building
        </Badge>
      )
    case "creating":
      return (
        <Badge variant="outline" className="text-[9px] bg-amber-500/10 text-amber-400 border-amber-500/20 animate-pulse px-1.5 h-4 font-black uppercase tracking-tighter">
          Creating
        </Badge>
      )
    case "phase1_review":
    case "phase2_review":
      return (
        <Badge variant="outline" className="text-[9px] bg-violet-500/10 text-violet-400 border-violet-500/20 px-1.5 h-4 font-black uppercase tracking-tighter">
          Review
        </Badge>
      )
    case "complete":
    case "completed":
      return (
        <Badge variant="outline" className="text-[9px] bg-emerald-500/10 text-emerald-400 border-emerald-500/20 px-1.5 h-4 font-black uppercase tracking-tighter">
          Ready
        </Badge>
      )
    case "failed":
      return (
        <Badge variant="outline" className="text-[9px] bg-red-500/10 text-red-400 border-red-500/20 px-1.5 h-4 font-black uppercase tracking-tighter">
          Error
        </Badge>
      )
    default:
      return (
        <Badge variant="outline" className="text-[9px] bg-muted/20 text-muted-foreground border-border/50 px-1.5 h-4 font-black uppercase tracking-tighter">
          {status}
        </Badge>
      )
  }
}
