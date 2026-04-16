"use client"

import { createContext, useContext, useEffect, useState, useCallback, useMemo } from "react"
import { listOrgs } from "@/lib/api/orgs"
import { listWorkspaces } from "@/lib/api/workspaces"
import { fetchUserProperties } from "@/lib/api/auth"
import { useAccess } from "@/components/providers/AccessProvider"
import type { OrgResponse, WorkspaceResponse } from "@/lib/types/orgs"

const LS_SB_ORG_KEY = "kcontrol:sandbox:selectedOrgId"
const LS_SB_WS_KEY = "kcontrol:sandbox:selectedWorkspaceId"

interface SandboxOrgWorkspaceContextValue {
  orgs: OrgResponse[]
  workspaces: WorkspaceResponse[]
  selectedOrgId: string
  selectedWorkspaceId: string
  setSelectedOrgId: (id: string) => void
  setSelectedWorkspaceId: (id: string) => void
  ready: boolean
}

const SandboxOrgWorkspaceContext = createContext<SandboxOrgWorkspaceContextValue>({
  orgs: [],
  workspaces: [],
  selectedOrgId: "",
  selectedWorkspaceId: "",
  setSelectedOrgId: () => {},
  setSelectedWorkspaceId: () => {},
  ready: false,
})

export function SandboxOrgWorkspaceProvider({ children }: { children: React.ReactNode }) {
  const [orgs, setOrgs] = useState<OrgResponse[]>([])
  const [workspaces, setWorkspaces] = useState<WorkspaceResponse[]>([])
  const [selectedOrgId, _setSelectedOrgId] = useState("")
  const [selectedWorkspaceId, _setSelectedWorkspaceId] = useState("")
  const [ready, setReady] = useState(false)
  const { setOrgWorkspaceContext } = useAccess()

  const setSelectedOrgId = useCallback((id: string) => {
    _setSelectedOrgId(id)
    if (typeof window !== "undefined") localStorage.setItem(LS_SB_ORG_KEY, id)
  }, [])

  const setSelectedWorkspaceId = useCallback((id: string) => {
    _setSelectedWorkspaceId(id)
    if (typeof window !== "undefined") localStorage.setItem(LS_SB_WS_KEY, id)
  }, [])

  useEffect(() => {
    async function init() {
      try {
        const [orgList, props] = await Promise.all([
          listOrgs(),
          fetchUserProperties().catch(() => ({} as Record<string, string>)),
        ])
        setOrgs(orgList)

        const storedOrg = typeof window !== "undefined" ? localStorage.getItem(LS_SB_ORG_KEY) : null
        const defaultOrg = props["default_org_id"] ?? ""
        const resolvedOrg = storedOrg && orgList.some(o => o.id === storedOrg)
          ? storedOrg
          : (defaultOrg && orgList.some(o => o.id === defaultOrg) ? defaultOrg : orgList[0]?.id ?? "")

        _setSelectedOrgId(resolvedOrg)

        if (resolvedOrg) {
          const allWs = await listWorkspaces(resolvedOrg).catch(() => [] as WorkspaceResponse[])
          // Show only sandbox workspaces (inverse of the dashboard filter)
          const wsList = allWs.filter(w => w.workspace_type_code === "sandbox")
          setWorkspaces(wsList)

          const storedWs = typeof window !== "undefined" ? localStorage.getItem(LS_SB_WS_KEY) : null
          const resolvedWs = storedWs && wsList.some(w => w.id === storedWs)
            ? storedWs
            : wsList[0]?.id ?? ""

          _setSelectedWorkspaceId(resolvedWs)
          setOrgWorkspaceContext(resolvedOrg, resolvedWs)
        }
      } catch {
        // non-blocking
      } finally {
        setReady(true)
      }
    }
    init()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // When org changes, reload sandbox workspaces
  useEffect(() => {
    if (!selectedOrgId || !ready) return
    listWorkspaces(selectedOrgId)
      .then(allWs => {
        const wsList = allWs.filter(w => w.workspace_type_code === "sandbox")
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

  // When workspace selection changes, re-sync access
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
    <SandboxOrgWorkspaceContext.Provider value={contextValue}>
      {children}
    </SandboxOrgWorkspaceContext.Provider>
  )
}

export function useSandboxOrgWorkspace() {
  return useContext(SandboxOrgWorkspaceContext)
}
