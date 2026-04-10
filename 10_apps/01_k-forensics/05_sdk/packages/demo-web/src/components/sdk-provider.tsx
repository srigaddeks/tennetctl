'use client'

import { createContext, useContext, useEffect, useState, useCallback, type ReactNode } from 'react'
import { KBioSDK, type SessionState } from '@/lib/real-sdk'
import type { V2Scores } from '@/lib/v2-types'

type AlertData = {
  type: string
  severity: string
  score: number
  message: string
  timestamp: number
}

type DerivedScores = {
  drift: number
  anomaly: number
  trust: number
  bot: number
}

type SdkContextValue = {
  initialized: boolean
  scores: DerivedScores | null
  v2Scores: V2Scores | null
  session: SessionState | null
  alerts: AlertData[]
  isEnrolling: boolean
  isLearning: boolean
  clearAlerts: () => void
  setUser: (username: string) => void
  logout: () => void
}

const SdkContext = createContext<SdkContextValue>({
  initialized: false,
  scores: null,
  v2Scores: null,
  session: null,
  alerts: [],
  isEnrolling: false,
  isLearning: false,
  clearAlerts: () => {},
  setUser: () => {},
  logout: () => {},
})

export function useSdk(): SdkContextValue {
  return useContext(SdkContext)
}

export function SdkProvider({ children }: { children: ReactNode }) {
  const [initialized, setInitialized] = useState(false)
  const [v2Scores, setV2Scores] = useState<V2Scores | null>(null)
  const [session, setSession] = useState<SessionState | null>(null)
  const [alerts, setAlerts] = useState<AlertData[]>([])
  const [isEnrolling, setIsEnrolling] = useState(false)
  const [isLearning, setIsLearning] = useState(true)

  const clearAlerts = useCallback(() => setAlerts([]), [])

  const setUser = useCallback((username: string) => {
    KBioSDK.setUser(username)
    setSession(KBioSDK.getSessionState())
  }, [])

  const logout = useCallback(() => {
    KBioSDK.logout()
    setSession(KBioSDK.getSessionState())
  }, [])

  // Derive simple scores from v2Scores
  const scores: DerivedScores | null = v2Scores ? {
    drift: v2Scores.identity.behavioral_drift,
    anomaly: v2Scores.anomaly.session_anomaly,
    trust: v2Scores.trust.session_trust,
    bot: v2Scores.humanness.bot_score,
  } : null

  useEffect(() => {
    KBioSDK.init({ api_key: 'kp_test_demo' })
    setInitialized(true)

    const unsubs: Array<() => void> = []

    unsubs.push(KBioSDK.on('v2_scores', (data) => {
      const v2 = data as V2Scores
      setV2Scores(v2)
      setIsEnrolling(v2.meta.profile_maturity === 0)
      setIsLearning(v2.meta.profile_maturity > 0 && v2.meta.profile_maturity < 0.5)
      setSession(KBioSDK.getSessionState())
    }))

    unsubs.push(KBioSDK.on('alert', (data) => {
      const a = data as { type: string; severity: string; score: number; message: string }
      setAlerts(prev => [...prev.slice(-19), { ...a, timestamp: Date.now() }])
    }))

    unsubs.push(KBioSDK.on('session_start', () => {
      setSession(KBioSDK.getSessionState())
    }))

    unsubs.push(KBioSDK.on('session_end', () => {
      setSession(null)
    }))

    setSession(KBioSDK.getSessionState())

    return () => {
      unsubs.forEach(u => u())
      KBioSDK.destroy()
    }
  }, [])

  return (
    <SdkContext.Provider value={{ initialized, scores, v2Scores, session, alerts, isEnrolling, isLearning, clearAlerts, setUser, logout }}>
      {children}
    </SdkContext.Provider>
  )
}
