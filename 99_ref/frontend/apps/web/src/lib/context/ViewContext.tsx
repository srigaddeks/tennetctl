"use client"

import { createContext, useContext, useEffect, useState, useCallback, useMemo } from "react"
import { getMyViews } from "@/lib/api/views"
import { useOrgWorkspace } from "@/lib/context/OrgWorkspaceContext"
import type { PortalViewResponse, ViewRouteResponse } from "@/lib/types/views"

// ─────────────────────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────────────────────

export type ViewId = string  // e.g. "grc", "auditor", "engineering", etc.

export interface ViewDefinition {
  id: ViewId
  label: string
  description: string
  color: string
  icon: string | null
  allowedRoutes: string[]
  routes: ViewRouteResponse[]
}

// ─────────────────────────────────────────────────────────────────────────────
// Fallback definitions (used when API is unavailable)
// ─────────────────────────────────────────────────────────────────────────────

const FALLBACK_VIEW: ViewDefinition = {
  id: "grc",
  label: "GRC Practitioner",
  description: "Full compliance management",
  color: "#2878ff",
  icon: "ShieldCheck",
  allowedRoutes: ["/dashboard", "/frameworks", "/controls", "/tests", "/risks", "/tasks", "/workspaces", "/sandbox", "/feedback", "/policies", "/copilot", "/notifications", "/audit-workspace"],
  routes: [],
}

// ─────────────────────────────────────────────────────────────────────────────
// Convert API response to ViewDefinition
// ─────────────────────────────────────────────────────────────────────────────

function apiViewToDefinition(v: PortalViewResponse): ViewDefinition {
  return {
    id: v.code,
    label: v.name,
    description: v.description ?? "",
    color: v.color ?? "#2878ff",
    icon: v.icon ?? null,
    allowedRoutes: v.routes.map(r => r.route_prefix),
    routes: v.routes,
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Context
// ─────────────────────────────────────────────────────────────────────────────

const LS_VIEW_KEY = "kcontrol:activeView"

interface ViewContextValue {
  /** All views available to this user */
  availableViews: ViewDefinition[]
  /** Currently active view ID */
  activeView: ViewId
  /** Switch view */
  setActiveView: (v: ViewId) => void
  /** The full definition of the active view */
  activeViewDef: ViewDefinition
  /** Whether a given route is allowed in the current view */
  isRouteAllowed: (path: string) => boolean
  /** Whether the current route is read-only in this view */
  isReadOnly: (path: string) => boolean
  /** Ready flag */
  ready: boolean
}

const ViewContext = createContext<ViewContextValue>({
  availableViews: [FALLBACK_VIEW],
  activeView: "grc",
  setActiveView: () => {},
  activeViewDef: FALLBACK_VIEW,
  isRouteAllowed: () => true,
  isReadOnly: () => false,
  ready: false,
})

export function ViewProvider({ children }: { children: React.ReactNode }) {
  const { selectedOrgId, ready: orgReady } = useOrgWorkspace()
  const [availableViews, setAvailableViews] = useState<ViewDefinition[]>([FALLBACK_VIEW])
  const [activeView, _setActiveView] = useState<ViewId>("grc")
  const [ready, setReady] = useState(false)

  const setActiveView = useCallback((v: ViewId) => {
    _setActiveView(v)
    if (typeof window !== "undefined") localStorage.setItem(LS_VIEW_KEY, v)
  }, [])

  // Load views from API scoped to the selected org — re-runs when org changes
  useEffect(() => {
    if (!orgReady) return
    async function init() {
      try {
        const resp = await getMyViews(selectedOrgId || undefined)
        const defs = resp.views.map(apiViewToDefinition)

        if (defs.length === 0) {
          setAvailableViews([FALLBACK_VIEW])
        } else {
          setAvailableViews(defs)
        }

        const viewIds = defs.length > 0 ? defs.map(d => d.id) : ["grc"]

        // Restore last active view from localStorage (reset if not in new view list)
        const stored = typeof window !== "undefined" ? localStorage.getItem(LS_VIEW_KEY) : null
        const resolved = (stored && viewIds.includes(stored)) ? stored : viewIds[0]
        _setActiveView(resolved)
      } catch {
        setAvailableViews([FALLBACK_VIEW])
        _setActiveView("grc")
      } finally {
        setReady(true)
      }
    }
    init()
  }, [orgReady, selectedOrgId])

  const activeViewDef = useMemo(
    () => availableViews.find(v => v.id === activeView) ?? availableViews[0] ?? FALLBACK_VIEW,
    [availableViews, activeView]
  )

  // Routes that are universally available regardless of view profile
  const UNIVERSAL_ROUTES = ["/notifications", "/audit-workspace"]

  const isRouteAllowed = useCallback((path: string) => {
    if (UNIVERSAL_ROUTES.some(r => path === r || path.startsWith(r + "/"))) return true
    return activeViewDef.allowedRoutes.some(prefix =>
      prefix === "/*" || path === prefix || path.startsWith(prefix + "/")
    )
  }, [activeViewDef])

  const isReadOnly = useCallback((path: string) => {
    const route = activeViewDef.routes.find(r => path === r.route_prefix || path.startsWith(r.route_prefix + "/"))
    return route?.is_read_only ?? false
  }, [activeViewDef])

  return (
    <ViewContext.Provider value={{
      availableViews,
      activeView,
      setActiveView,
      activeViewDef,
      isRouteAllowed,
      isReadOnly,
      ready,
    }}>
      {children}
    </ViewContext.Provider>
  )
}

export function useView() {
  return useContext(ViewContext)
}
