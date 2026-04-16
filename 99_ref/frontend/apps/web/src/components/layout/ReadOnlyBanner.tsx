"use client"

import { usePathname } from "next/navigation"
import { useView } from "@/lib/context/ViewContext"
import { Lock } from "lucide-react"

/**
 * Shows a subtle banner when the current page is read-only in the active view.
 * Place this in page headers to inform the user they can view but not edit.
 */
export function ReadOnlyBanner() {
  const pathname = usePathname()
  const { isReadOnly, activeViewDef, ready } = useView()

  if (!ready || !isReadOnly(pathname)) return null

  return (
    <div
      className="flex items-center gap-2 rounded-lg px-3 py-1.5 text-[11px] font-medium border"
      style={{
        backgroundColor: `${activeViewDef.color}08`,
        borderColor: `${activeViewDef.color}25`,
        color: activeViewDef.color,
      }}
    >
      <Lock className="w-3 h-3" />
      Read-only in {activeViewDef.label} view
    </div>
  )
}
