"use client"

import { usePathname } from "next/navigation"
import { useView } from "@/lib/context/ViewContext"
import { ShieldAlert } from "lucide-react"

/**
 * Wraps page content and checks that the current route is allowed
 * in the active view. If not, shows a restricted-access message.
 *
 * Usage: wrap your page return in <ViewGuard>…</ViewGuard>
 * or call useViewGuard() to check programmatically.
 */
export function ViewGuard({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const { isRouteAllowed, activeViewDef, ready } = useView()

  if (!ready) return null

  if (!isRouteAllowed(pathname)) {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-center gap-4">
        <div className="flex h-14 w-14 items-center justify-center rounded-full bg-muted">
          <ShieldAlert className="h-6 w-6 text-muted-foreground" />
        </div>
        <div>
          <h2 className="text-lg font-semibold">Not available in this view</h2>
          <p className="text-sm text-muted-foreground mt-1 max-w-md">
            The <span className="font-medium" style={{ color: activeViewDef.color }}>{activeViewDef.label}</span> view
            does not include this page. Switch to a different view to access it.
          </p>
        </div>
      </div>
    )
  }

  return <>{children}</>
}
