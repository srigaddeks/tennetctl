"use client"

import { createContext, useContext, useEffect, useState, useCallback, useMemo } from "react"
import { listOrgs } from "@/lib/api/orgs"
import { listWorkspaces, createWorkspace } from "@/lib/api/workspaces"
import { fetchUserProperties } from "@/lib/api/auth"
import { fetchAccessContext } from "@/lib/api/access"
import { setSessionOrg, setSessionWorkspace } from "@/lib/api/apiClient"
import { useAccess } from "@/components/providers/AccessProvider"
import type { OrgResponse, WorkspaceResponse } from "@/lib/types/orgs"

function slugify(val: string) {
  return val.toLowerCase().replace(/[^a-z0-9-]/g, "-").replace(/--+/g, "-")
}

async function ensureDefaultWorkspaces(orgId: string, canCreate: boolean): Promise<WorkspaceResponse[]> {
  const existing = await listWorkspaces(orgId)
  const nonSandbox = existing.filter(w => w.workspace_type_code !== "sandbox")
  if (nonSandbox.length > 0 || !canCreate) return existing

  // No non-sandbox workspaces and user can create — auto-create both defaults
  const created: WorkspaceResponse[] = [...existing]
  const defaults = [
    { name: "K-Control", slug: "k-control", workspace_type_code: "project" },
    { name: "K-Control Sandbox", slug: "k-control-sandbox", workspace_type_code: "sandbox" },
  ]
  for (const ws of defaults) {
    try {
      const already = existing.find(w => w.workspace_type_code === ws.workspace_type_code)
      if (!already) {
        const w = await createWorkspace(orgId, ws)
        created.push(w)
      }
    } catch { /* already exists — skip */ }
  }
  return created
}

const LS_ORG_KEY = "kcontrol:selectedOrgId"
const LS_WS_KEY = "kcontrol:selectedWorkspaceId"

interface OrgWorkspaceContextValue {
  orgs: OrgResponse[]
  workspaces: WorkspaceResponse[]
  selectedOrgId: string
  selectedWorkspaceId: string
  setSelectedOrgId: (id: string) => void
  setSelectedWorkspaceId: (id: string) => void
  ready: boolean
}

const OrgWorkspaceContext = createContext<OrgWorkspaceContextValue>({
  orgs: [],
  workspaces: [],
  selectedOrgId: "",
  selectedWorkspaceId: "",
  setSelectedOrgId: () => {},
  setSelectedWorkspaceId: () => {},
  ready: false,
})

export function OrgWorkspaceProvider({ children }: { children: React.ReactNode }) {
  const [orgs, setOrgs] = useState<OrgResponse[]>([])
  const [workspaces, setWorkspaces] = useState<WorkspaceResponse[]>([])
  const [selectedOrgId, _setSelectedOrgId] = useState("")
  const [selectedWorkspaceId, _setSelectedWorkspaceId] = useState("")
  const [ready, setReady] = useState(false)
  const { setOrgWorkspaceContext } = useAccess()

  const setSelectedOrgId = useCallback((id: string) => {
    _setSelectedOrgId(id)
    if (typeof window !== "undefined") localStorage.setItem(LS_ORG_KEY, id)
    setSessionOrg(id)
  }, [])

  const setSelectedWorkspaceId = useCallback((id: string) => {
    _setSelectedWorkspaceId(id)
    if (typeof window !== "undefined") localStorage.setItem(LS_WS_KEY, id)
    setSessionWorkspace(id)
  }, [])

  // Bootstrap: load orgs, restore selection from localStorage (fall back to default_org_id)
  // Always resolves a valid org and workspace — auto-creates defaults if org has no workspaces.
  useEffect(() => {
    async function init() {
      try {
        const [orgList, props] = await Promise.all([
          listOrgs(),
          fetchUserProperties().catch(() => ({} as Record<string, string>)),
        ])
        setOrgs(orgList)

        if (orgList.length === 0) return

        // Resolve org — prefer stored, then default, then first
        const storedOrg = typeof window !== "undefined" ? localStorage.getItem(LS_ORG_KEY) : null
        const defaultOrg = props["default_org_id"] ?? ""
        const resolvedOrg = (storedOrg && orgList.some(o => o.id === storedOrg))
          ? storedOrg
          : (defaultOrg && orgList.some(o => o.id === defaultOrg))
            ? defaultOrg
            : orgList[0].id

        _setSelectedOrgId(resolvedOrg)
        if (typeof window !== "undefined") localStorage.setItem(LS_ORG_KEY, resolvedOrg)
        setSessionOrg(resolvedOrg)

        // Fetch access context and workspace list in parallel
        const [orgAccess, initialWs] = await Promise.all([
          fetchAccessContext(resolvedOrg).catch(() => null),
          listWorkspaces(resolvedOrg).catch(() => [] as WorkspaceResponse[]),
        ])

        const canCreateWorkspace = orgAccess?.current_org?.actions.some(
          (a: { feature_code: string; action_code: string }) =>
            a.feature_code === "workspace_management" && a.action_code === "create"
        ) ?? false

        // Auto-create defaults only if needed (avoids re-fetching when workspaces already exist)
        const nonSandbox = initialWs.filter(w => w.workspace_type_code !== "sandbox")
        const allWs = (nonSandbox.length > 0 || !canCreateWorkspace)
          ? initialWs
          : await ensureDefaultWorkspaces(resolvedOrg, canCreateWorkspace).catch(() => [] as WorkspaceResponse[])
        const wsList = allWs.filter(w => w.workspace_type_code !== "sandbox")
        setWorkspaces(wsList)

        // Resolve workspace — prefer stored, then default, then first non-sandbox
        const storedWs = typeof window !== "undefined" ? localStorage.getItem(LS_WS_KEY) : null
        const defaultWs = props["default_workspace_id"] ?? ""
        const resolvedWs = (storedWs && wsList.some(w => w.id === storedWs))
          ? storedWs
          : (defaultWs && wsList.some(w => w.id === defaultWs))
            ? defaultWs
            : wsList[0]?.id ?? ""

        _setSelectedWorkspaceId(resolvedWs)
        if (resolvedWs && typeof window !== "undefined") localStorage.setItem(LS_WS_KEY, resolvedWs)
        setSessionWorkspace(resolvedWs)
        setOrgWorkspaceContext(resolvedOrg, resolvedWs)
      } catch {
        // non-blocking
      } finally {
        setReady(true)
      }
    }
    init()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // When org changes, reload workspaces (auto-create defaults if needed) and reset workspace selection
  useEffect(() => {
    if (!selectedOrgId || !ready) return
    fetchAccessContext(selectedOrgId)
      .then(orgAccess => {
        const canCreate = orgAccess.current_org?.actions.some(
          (a: { feature_code: string; action_code: string }) =>
            a.feature_code === "workspace_management" && a.action_code === "create"
        ) ?? false
        return ensureDefaultWorkspaces(selectedOrgId, canCreate)
      })
      .catch(() => ensureDefaultWorkspaces(selectedOrgId, false))
      .then(allWs => {
        const wsList = allWs.filter(w => w.workspace_type_code !== "sandbox")
        setWorkspaces(wsList)
        const resolvedWs = wsList.some(w => w.id === selectedWorkspaceId)
          ? selectedWorkspaceId
          : wsList[0]?.id ?? ""
        setSelectedWorkspaceId(resolvedWs)
        setOrgWorkspaceContext(selectedOrgId, resolvedWs)
      })
      .catch(() => setWorkspaces([]))
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedOrgId, ready])

  // When workspace selection changes (user picks a different workspace), re-sync access
  useEffect(() => {
    if (!ready || !selectedOrgId || !selectedWorkspaceId) return
    setOrgWorkspaceContext(selectedOrgId, selectedWorkspaceId)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedWorkspaceId, ready])

  const contextValue = useMemo(() => ({
    orgs,
    workspaces,
    selectedOrgId,
    selectedWorkspaceId,
    setSelectedOrgId,
    setSelectedWorkspaceId,
    ready,
  }), [orgs, workspaces, selectedOrgId, selectedWorkspaceId, setSelectedOrgId, setSelectedWorkspaceId, ready])

  return (
    <OrgWorkspaceContext.Provider value={contextValue}>
      {children}
    </OrgWorkspaceContext.Provider>
  )
}

export function useOrgWorkspace() {
  return useContext(OrgWorkspaceContext)
}
