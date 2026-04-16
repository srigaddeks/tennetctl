"use client"

import { createContext, useContext, useEffect, useState, useCallback, useMemo } from "react"
import { listOrgs } from "@/lib/api/orgs"
import { fetchUserProperties } from "@/lib/api/auth"
import { useAccess } from "@/components/providers/AccessProvider"
import type { OrgResponse } from "@/lib/types/orgs"

const LS_ASB_ORG_KEY = "kcontrol:agent_sandbox:selectedOrgId"

interface AgentSandboxContextValue {
  orgs: OrgResponse[]
  selectedOrgId: string
  setSelectedOrgId: (id: string) => void
  ready: boolean
}

const AgentSandboxContext = createContext<AgentSandboxContextValue>({
  orgs: [],
  selectedOrgId: "",
  setSelectedOrgId: () => {},
  ready: false,
})

export function AgentSandboxProvider({ children }: { children: React.ReactNode }) {
  const [orgs, setOrgs] = useState<OrgResponse[]>([])
  const [selectedOrgId, _setSelectedOrgId] = useState("")
  const [ready, setReady] = useState(false)
  const { setOrgWorkspaceContext } = useAccess()

  const setSelectedOrgId = useCallback((id: string) => {
    _setSelectedOrgId(id)
    if (typeof window !== "undefined") localStorage.setItem(LS_ASB_ORG_KEY, id)
  }, [])

  useEffect(() => {
    async function init() {
      try {
        const [orgList, props] = await Promise.all([
          listOrgs(),
          fetchUserProperties().catch(() => ({} as Record<string, string>)),
        ])
        setOrgs(orgList)

        const storedOrg = typeof window !== "undefined" ? localStorage.getItem(LS_ASB_ORG_KEY) : null
        const defaultOrg = props["default_org_id"] ?? ""
        const resolvedOrg = storedOrg && orgList.some(o => o.id === storedOrg)
          ? storedOrg
          : (defaultOrg && orgList.some(o => o.id === defaultOrg) ? defaultOrg : orgList[0]?.id ?? "")

        _setSelectedOrgId(resolvedOrg)
        if (resolvedOrg) {
          setOrgWorkspaceContext(resolvedOrg, "")
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

  useEffect(() => {
    if (!selectedOrgId || !ready) return
    setOrgWorkspaceContext(selectedOrgId, "")
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedOrgId, ready])

  const contextValue = useMemo(() => ({
    orgs,
    selectedOrgId,
    setSelectedOrgId,
    ready,
  }), [orgs, selectedOrgId, setSelectedOrgId, ready])

  return (
    <AgentSandboxContext.Provider value={contextValue}>
      {children}
    </AgentSandboxContext.Provider>
  )
}

export function useAgentSandbox() {
  return useContext(AgentSandboxContext)
}
