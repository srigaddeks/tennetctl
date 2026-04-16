"use client"

import { Sparkles } from "lucide-react"
import { useCopilot } from "@/lib/context/CopilotContext"

export function CopilotTrigger() {
  const { isOpen, toggle } = useCopilot()

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={isOpen ? "Close AI Copilot" : "Open AI Copilot"}
      className={`relative flex items-center gap-1.5 h-8 px-3 rounded-lg text-xs font-medium transition-all duration-200 hover:opacity-90
        ${isOpen
          ? "bg-violet-500/15 text-violet-400 ring-1 ring-violet-500/30"
          : "bg-gradient-to-r from-violet-500/15 to-purple-500/10 text-violet-400 hover:from-violet-500/25 hover:to-purple-500/20"
        }`}
    >
      <span className="relative flex items-center justify-center w-4 h-4">
        <Sparkles className="w-3.5 h-3.5 relative z-10" />
        {/* Pulse ring when closed */}
        {!isOpen && (
          <span className="absolute inset-0 rounded-full bg-violet-400/30 animate-ping" />
        )}
      </span>
      <span>Copilot</span>
    </button>
  )
}
