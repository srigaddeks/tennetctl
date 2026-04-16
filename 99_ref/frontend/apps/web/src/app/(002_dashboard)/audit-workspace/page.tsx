"use client"

import * as React from "react"
import { useRouter } from "next/navigation"
import { useView } from "@/lib/context/ViewContext"
import { Loader2 } from "lucide-react"

/**
 * Audit Workspace Root Redirector
 * Automatically routes the user to the correct perspective
 * based on their active Portal View.
 */
export default function AuditWorkspaceRedirector() {
  const router = useRouter()
  const { activeView, ready } = useView()

  React.useEffect(() => {
    if (!ready) return

    // Valid audit workspace views
    const validViews = ["grc", "auditor", "engineering", "executive"]
    
    // Determine target route
    const targetView = validViews.includes(activeView) ? activeView : "grc"
    
    // Redirect
    router.replace(`/audit-workspace/${targetView}`)
  }, [activeView, ready, router])

  return (
    <div className="flex-1 flex flex-col items-center justify-center min-h-[60vh] gap-4">
      <div className="relative">
        <div className="h-16 w-16 rounded-full border-4 border-primary/20 animate-pulse" />
        <Loader2 className="h-8 w-8 text-primary animate-spin absolute inset-0 m-auto" />
      </div>
      <div className="flex flex-col items-center text-center gap-1.5">
        <p className="text-lg font-bold tracking-tight">Initializing Audit Workspace...</p>
        <p className="text-sm text-muted-foreground font-medium uppercase tracking-widest">
           Applying perspective: {activeView.toUpperCase()}
        </p>
      </div>
    </div>
  )
}
