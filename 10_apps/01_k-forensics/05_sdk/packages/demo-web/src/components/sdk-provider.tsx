'use client'

import { createContext, useContext, useEffect, useState, useCallback, type ReactNode } from 'react'
import { MockKProtect, type DriftScores, type SessionState, type EventName } from '@/lib/mock-sdk'

type AlertData = {
  type: string
  severity: string
  score: number
  message: string
  timestamp: number
}

type SdkContextValue = {
  initialized: boolean
  scores: DriftScores
  session: SessionState | null
  alerts: AlertData[]
  clearAlerts: () => void
}

const SdkContext = createContext<SdkContextValue>({
  initialized: false,
  scores: { drift: -1, anomaly: -1, trust: -1, bot: -1 },
  session: null,
  alerts: [],
  clearAlerts: () => {},
})

export function useSdk(): SdkContextValue {
  return useContext(SdkContext)
}

export function SdkProvider({ children }: { children: ReactNode }) {
  const [initialized, setInitialized] = useState(false)
  const [scores, setScores] = useState<DriftScores>({ drift: -1, anomaly: -1, trust: -1, bot: -1 })
  const [session, setSession] = useState<SessionState | null>(null)
  const [alerts, setAlerts] = useState<AlertData[]>([])

  const clearAlerts = useCallback(() => setAlerts([]), [])

  useEffect(() => {
    MockKProtect.init({
      api_key: 'kp_test_demo',
      overrides: {
        transport: { mode: 'proxy', endpoint: '/api/ingest' },
        environment: 'debug',
      },
    })
    setInitialized(true)

    const unsubs: Array<() => void> = []

    unsubs.push(MockKProtect.on('drift' as EventName, (data) => {
      const d = data as { scores: DriftScores }
      setScores({ ...d.scores })
      setSession(MockKProtect.getSessionState())
    }))

    unsubs.push(MockKProtect.on('alert' as EventName, (data) => {
      const a = data as { type: string; severity: string; score: number; message: string }
      setAlerts(prev => [...prev.slice(-19), { ...a, timestamp: Date.now() }])
    }))

    unsubs.push(MockKProtect.on('session_start' as EventName, () => {
      setSession(MockKProtect.getSessionState())
    }))

    unsubs.push(MockKProtect.on('session_end' as EventName, () => {
      setSession(null)
    }))

    // Set initial state
    const initial = MockKProtect.getLatestDrift()
    if (initial) setScores(initial)
    setSession(MockKProtect.getSessionState())

    return () => {
      unsubs.forEach(u => u())
      MockKProtect.destroy()
    }
  }, [])

  return (
    <SdkContext.Provider value={{ initialized, scores, session, alerts, clearAlerts }}>
      {children}
    </SdkContext.Provider>
  )
}
