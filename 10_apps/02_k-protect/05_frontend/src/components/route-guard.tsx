'use client'

import { useEffect } from 'react'
import { usePathname, useRouter } from 'next/navigation'
import { useAuth } from './auth-provider'
import { AppShell } from './app-shell'

const PUBLIC_PATHS = new Set(['/login', '/signup'])

export function RouteGuard({ children }: { children: React.ReactNode }) {
  const { isLoggedIn, loading } = useAuth()
  const pathname = usePathname()
  const router = useRouter()
  const isPublic = PUBLIC_PATHS.has(pathname)

  useEffect(() => {
    if (loading) return
    if (!isLoggedIn && !isPublic) {
      router.replace('/login')
    } else if (isLoggedIn && isPublic) {
      router.replace('/')
    }
  }, [loading, isLoggedIn, isPublic, pathname, router])

  if (loading) {
    return (
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        minHeight: '100vh', background: 'var(--background)',
        color: 'var(--foreground-subtle)', fontSize: 13,
      }}>
        Loading…
      </div>
    )
  }

  if (isPublic) {
    return (
      <div style={{
        minHeight: '100vh', background: 'var(--background)',
        color: 'var(--foreground)', display: 'flex', flexDirection: 'column',
      }}>
        <main style={{
          flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center',
          padding: '32px 16px',
        }}>
          <div style={{ width: '100%', maxWidth: 480 }}>
            {children}
          </div>
        </main>
      </div>
    )
  }

  if (!isLoggedIn) return null

  return <AppShell>{children}</AppShell>
}
