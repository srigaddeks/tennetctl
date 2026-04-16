"use client"

import { useMemo, useContext } from "react"
import { usePathname, useParams } from "next/navigation"
import { useOrgWorkspace } from "@/lib/context/OrgWorkspaceContext"
import { CopilotContext } from "@/lib/context/CopilotContext"

export interface CopilotPageContext {
  org_id: string | null
  workspace_id: string | null
  org_name?: string
  workspace_name?: string
  route: string
  route_pattern: string
  framework_id?: string
  framework_name?: string
  control_id?: string
  control_code?: string
  control_name?: string
  risk_id?: string
  risk_title?: string
  task_id?: string
  task_title?: string
  url: string
  page_title: string
}

export function useCopilotPageContext(): CopilotPageContext {
  const pathname = usePathname()
  const params = useParams<Record<string, string>>()
  const { selectedOrgId, selectedWorkspaceId, orgs, workspaces } = useOrgWorkspace()
  const copilotCtx = useContext(CopilotContext)
  const entityNames = copilotCtx?.entityNames ?? {}

  return useMemo(() => {
    const url = typeof window !== "undefined" ? window.location.href : pathname
    const page_title = typeof document !== "undefined" ? document.title : ""

    // Resolve org/workspace display names from OrgWorkspaceContext
    const orgName = orgs.find(o => o.id === selectedOrgId)?.name ?? entityNames.org_name
    const wsName = workspaces.find(w => w.id === selectedWorkspaceId)?.name ?? entityNames.workspace_name

    // Derive route_pattern from params
    let route_pattern = pathname
    const entityIds: Pick<CopilotPageContext, "framework_id" | "control_id" | "risk_id" | "task_id"> = {}

    if (params.frameworkId) {
      route_pattern = route_pattern.replace(params.frameworkId, "[frameworkId]")
      entityIds.framework_id = params.frameworkId
    }
    if (params.controlId) {
      route_pattern = route_pattern.replace(params.controlId, "[controlId]")
      entityIds.control_id = params.controlId
    }
    if (params.riskId) {
      route_pattern = route_pattern.replace(params.riskId, "[riskId]")
      entityIds.risk_id = params.riskId
    }
    if (params.taskId) {
      route_pattern = route_pattern.replace(params.taskId, "[taskId]")
      entityIds.task_id = params.taskId
    }

    return {
      org_id: selectedOrgId,
      workspace_id: selectedWorkspaceId,
      org_name: orgName,
      workspace_name: wsName,
      route: pathname,
      route_pattern,
      url,
      page_title,
      ...entityIds,
      // Human-readable names from pages that call useCopilotEntityNames()
      ...(entityNames.framework_name ? { framework_name: entityNames.framework_name } : {}),
      ...(entityNames.control_code ? { control_code: entityNames.control_code } : {}),
      ...(entityNames.control_name ? { control_name: entityNames.control_name } : {}),
      ...(entityNames.risk_title ? { risk_title: entityNames.risk_title } : {}),
      ...(entityNames.task_title ? { task_title: entityNames.task_title } : {}),
    }
  }, [pathname, params, selectedOrgId, selectedWorkspaceId, orgs, workspaces, entityNames])
}
