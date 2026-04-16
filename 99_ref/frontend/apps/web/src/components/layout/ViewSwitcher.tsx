"use client"

import { useView } from "@/lib/context/ViewContext"

export function ViewSwitcher() {
  const { availableViews, activeView, setActiveView, ready } = useView()

  // Don't show if only one view available, or not ready
  if (!ready || availableViews.length <= 1) return null

  return (
    <div className="flex items-center gap-1.5 text-xs">
      <span className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground mr-1">
        View
      </span>
      {availableViews.map((def) => {
        const isActive = def.id === activeView
        return (
          <button
            key={def.id}
            type="button"
            onClick={() => setActiveView(def.id)}
            className="rounded-full px-3 py-1 text-[11px] font-medium border transition-all"
            style={{
              backgroundColor: isActive ? def.color : "transparent",
              borderColor: isActive ? def.color : "hsl(var(--border))",
              color: isActive ? "#fff" : "hsl(var(--muted-foreground))",
            }}
            title={def.description}
          >
            {def.label}
          </button>
        )
      })}
    </div>
  )
}
