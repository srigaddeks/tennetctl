'use client'

import { createContext, useContext, useEffect, useState, useCallback } from 'react'
import type { Session } from '@/lib/auth'
import {
  login as authLogin,
  register as authRegister,
  logoutApi,
  fetchSession,
  getToken,
  setToken,
  clearToken,
} from '@/lib/auth'

type AuthState =
  | { status: 'loading' }
  | { status: 'unauthenticated' }
  | { status: 'authenticated'; session: Session; token: string }

type AuthContextValue = {
  state: AuthState
  session: Session | null
  isLoggedIn: boolean
  loading: boolean
  login: (username: string, password: string) => Promise<void>
  register: (username: string, email: string, password: string) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<AuthState>({ status: 'loading' })

  useEffect(() => {
    const token = getToken()
    if (!token) {
      setState({ status: 'unauthenticated' })
      return
    }
    fetchSession(token).then(session => {
      if (session) {
        setState({ status: 'authenticated', session, token })
      } else {
        clearToken()
        setState({ status: 'unauthenticated' })
      }
    })
  }, [])

  const login = useCallback(async (username: string, password: string) => {
    const { session, token } = await authLogin(username, password)
    setToken(token)
    setState({ status: 'authenticated', session, token })
  }, [])

  const register = useCallback(async (username: string, email: string, password: string) => {
    const { session, token } = await authRegister(username, email, password)
    setToken(token)
    setState({ status: 'authenticated', session, token })
  }, [])

  const logout = useCallback(async () => {
    const token = getToken()
    if (token) await logoutApi(token)
    clearToken()
    setState({ status: 'unauthenticated' })
  }, [])

  const session = state.status === 'authenticated' ? state.session : null

  return (
    <AuthContext.Provider value={{
      state,
      session,
      isLoggedIn: state.status === 'authenticated',
      loading: state.status === 'loading',
      login,
      register,
      logout,
    }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider')
  return ctx
}
