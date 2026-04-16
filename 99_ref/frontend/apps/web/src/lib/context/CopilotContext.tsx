"use client"

import { createContext, useContext, useState, useEffect, useCallback, useRef, type ReactNode } from "react"

export interface CopilotEntityNames {
  framework_name?: string
  control_code?: string
  control_name?: string
  risk_title?: string
  task_title?: string
  org_name?: string
  workspace_name?: string
}

interface CopilotContextValue {
  isOpen: boolean
  open: () => void
  close: () => void
  toggle: () => void
  width: number
  setWidth: (w: number | ((prev: number) => number)) => void
  entityNames: CopilotEntityNames
  setEntityNames: (names: CopilotEntityNames) => void
  clearEntityNames: () => void
}

export const CopilotContext = createContext<CopilotContextValue | null>(null)

const STORAGE_KEY_OPEN = "kcontrol:copilot:open"
const STORAGE_KEY_WIDTH = "kcontrol:copilot:width"
const DEFAULT_WIDTH = 480
const MIN_WIDTH = 360
const MAX_WIDTH = 800

export function CopilotProvider({ children }: { children: ReactNode }) {
  const [isOpen, setIsOpen] = useState(false)
  const [width, setWidthState] = useState(DEFAULT_WIDTH)
  const [entityNames, setEntityNamesState] = useState<CopilotEntityNames>({})
  const initialized = useRef(false)

  useEffect(() => {
    if (initialized.current) return
    initialized.current = true
    try {
      const storedOpen = localStorage.getItem(STORAGE_KEY_OPEN)
      if (storedOpen === "true") setIsOpen(true)
      const storedWidth = localStorage.getItem(STORAGE_KEY_WIDTH)
      if (storedWidth) {
        const w = parseInt(storedWidth, 10)
        if (w >= MIN_WIDTH && w <= MAX_WIDTH) setWidthState(w)
      }
    } catch { /* ignore */ }
  }, [])

  const open = useCallback(() => {
    setIsOpen(true)
    try { localStorage.setItem(STORAGE_KEY_OPEN, "true") } catch { /* ignore */ }
  }, [])

  const close = useCallback(() => {
    setIsOpen(false)
    try { localStorage.setItem(STORAGE_KEY_OPEN, "false") } catch { /* ignore */ }
  }, [])

  const toggle = useCallback(() => {
    setIsOpen(prev => {
      const next = !prev
      try { localStorage.setItem(STORAGE_KEY_OPEN, String(next)) } catch { /* ignore */ }
      return next
    })
  }, [])

  const setWidth = useCallback((w: number | ((prev: number) => number)) => {
    setWidthState(prev => {
      const next = typeof w === "function" ? w(prev) : w
      const clamped = Math.max(MIN_WIDTH, Math.min(MAX_WIDTH, next))
      try { localStorage.setItem(STORAGE_KEY_WIDTH, String(clamped)) } catch { /* ignore */ }
      return clamped
    })
  }, [])

  const setEntityNames = useCallback((names: CopilotEntityNames) => {
    setEntityNamesState(names)
  }, [])

  const clearEntityNames = useCallback(() => {
    setEntityNamesState({})
  }, [])

  return (
    <CopilotContext.Provider value={{ isOpen, open, close, toggle, width, setWidth, entityNames, setEntityNames, clearEntityNames }}>
      {children}
    </CopilotContext.Provider>
  )
}

export function useCopilot() {
  const ctx = useContext(CopilotContext)
  if (!ctx) throw new Error("useCopilot must be used inside CopilotProvider")
  return ctx
}

/** Call this from any page that loads entity data — registers human-readable names into copilot context */
export function useCopilotEntityNames(names: CopilotEntityNames) {
  const ctx = useContext(CopilotContext)
  const setEntityNames = ctx?.setEntityNames
  const clearEntityNames = ctx?.clearEntityNames
  const namesKey = JSON.stringify(names)

  useEffect(() => {
    if (!setEntityNames) return
    setEntityNames(names)
    return () => { clearEntityNames?.() }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [namesKey, setEntityNames, clearEntityNames])
}

export { MIN_WIDTH, MAX_WIDTH }
