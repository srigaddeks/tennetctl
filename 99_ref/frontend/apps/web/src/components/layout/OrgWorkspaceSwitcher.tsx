"use client"

import { useOrgWorkspace } from "@/lib/context/OrgWorkspaceContext"
import { Building2, Layers } from "lucide-react"

export function OrgWorkspaceSwitcher() {
  const { orgs, workspaces, selectedOrgId, selectedWorkspaceId, setSelectedOrgId, setSelectedWorkspaceId, ready } =
    useOrgWorkspace()

  if (!ready || orgs.length === 0) return null

  return (
    <div className="flex items-center gap-2 text-xs">
      {/* Org selector */}
      <div className="flex items-center gap-1.5">
        <Building2 className="w-3.5 h-3.5 text-muted-foreground shrink-0" />
        <select
          className="rounded-md border border-border bg-background px-2 py-1 text-xs focus:outline-none focus:ring-2 focus:ring-ring max-w-[160px]"
          value={selectedOrgId}
          onChange={(e) => setSelectedOrgId(e.target.value)}
          title="Organisation"
        >
          {orgs.map((o) => (
            <option key={o.id} value={o.id}>{o.name}</option>
          ))}
        </select>
      </div>

      <span className="text-muted-foreground">/</span>

      {/* Workspace selector */}
      <div className="flex items-center gap-1.5">
        <Layers className="w-3.5 h-3.5 text-muted-foreground shrink-0" />
        <select
          className="rounded-md border border-border bg-background px-2 py-1 text-xs focus:outline-none focus:ring-2 focus:ring-ring max-w-[160px]"
          value={selectedWorkspaceId}
          onChange={(e) => setSelectedWorkspaceId(e.target.value)}
          title="Workspace"
          disabled={workspaces.length === 0}
        >
          {workspaces.length === 0 ? (
            <option value="">No workspaces</option>
          ) : (
            workspaces.map((w) => (
              <option key={w.id} value={w.id}>{w.name}</option>
            ))
          )}
        </select>
      </div>
    </div>
  )
}
