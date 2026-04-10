'use client'

import { createContext, useContext, useEffect, useState, useCallback, type ReactNode } from 'react'
import { useRouter } from 'next/navigation'
import { KBioSDK } from '@/lib/real-sdk'
import * as auth from '@/lib/auth'
import type { DemoSession, SignupPayload } from '@/lib/auth'

type AuthContextValue = {
  session: DemoSession | null
  isLoggedIn: boolean
  loading: boolean
  login: (username: string, password: string) => Promise<void>
  signup: (payload: SignupPayload) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue>({
  session: null,
  isLoggedIn: false,
  loading: true,
  login: async () => {},
  signup: async () => {},
  logout: async () => {},
})

export function useAuth(): AuthContextValue {
  return useContext(AuthContext)
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<DemoSession | null>(null)
  const [loading, setLoading] = useState(true)
  const router = useRouter()

  // Hydrate from localStorage on mount; validate with backend
  useEffect(() => {
    const stored = auth.getSession()
    if (!stored) {
      setLoading(false)
      return
    }
    // Optimistic set so the UI doesn't flash unauthenticated
    setSession(stored)
    KBioSDK.setUser(stored.user_id)
    auth.validateSession(stored.access_token).then(valid => {
      if (valid) {
        setSession(valid)
        KBioSDK.setUser(valid.user_id)
      } else {
        auth.clearSession()
        setSession(null)
        KBioSDK.logout()  
      }
      setLoading(false)
    })
  }, [])

  const doLogin = useCallback(async (username: string, password: string) => {
    const s = await auth.login(username, password)
    setSession(s)
    KBioSDK.setUser(s.user_id)
  }, [])

  const doSignup = useCallback(async (payload: SignupPayload) => {
    const s = await auth.signup(payload)
    setSession(s)
    KBioSDK.setUser(s.user_id)
  }, [])

  const doLogout = useCallback(async () => {
    const token = session?.access_token ?? ''
    await auth.logout(token)
    setSession(null)
    KBioSDK.logout()
    router.push('/login')
  }, [session, router])

  return (
    <AuthContext.Provider value={{
      session,
      isLoggedIn: session !== null,
      loading,
      login: doLogin,
      signup: doSignup,
      logout: doLogout,
    }}>
      {children}
    </AuthContext.Provider>
  )
}
