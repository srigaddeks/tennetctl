'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useState, useEffect } from 'react'
import { useAuth } from './auth-provider'

const NAV_GROUPS = [
  {
    label: 'Overview',
    items: [
      { href: '/', label: 'Dashboard' },
      { href: '/threats', label: 'Threat Graph' },
    ],
  },
  {
    label: 'Intelligence',
    items: [
      { href: '/users', label: 'Users' },
      { href: '/devices', label: 'Devices' },
      { href: '/network', label: 'Network / IP' },
    ],
  },
  {
    label: 'Configuration',
    items: [
      { href: '/policies', label: 'Policy Sets' },
      { href: '/signals', label: 'Signals' },
    ],
  },
  {
    label: 'Activity',
    items: [
      { href: '/decisions', label: 'Decisions' },
    ],
  },
]

export function Nav() {
  const pathname = usePathname()
  const { session, logout } = useAuth()
  const [dark, setDark] = useState(false)

  useEffect(() => {
    const stored = typeof window !== 'undefined' ? localStorage.getItem('kp-dark') : null
    if (stored === 'true') {
      setDark(true)
      document.documentElement.classList.add('dark')
    }
  }, [])

  function toggleDark() {
    const next = !dark
    setDark(next)
    if (next) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
    localStorage.setItem('kp-dark', String(next))
  }

  return (
    <nav style={{
      width: 220,
      minWidth: 220,
      background: 'var(--surface)',
      borderRight: '1px solid var(--border)',
      display: 'flex',
      flexDirection: 'column',
      height: '100vh',
      position: 'sticky',
      top: 0,
      overflowY: 'auto',
    }}>
      {/* Brand */}
      <div style={{ padding: '16px 16px 14px', borderBottom: '1px solid var(--border)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{
            width: 32, height: 32, borderRadius: 6,
            background: 'var(--foreground)', color: 'var(--background)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 12, fontWeight: 800, flexShrink: 0,
          }}>KP</div>
          <div style={{ minWidth: 0, flex: 1 }}>
            <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--foreground)' }}>KProtect</div>
            <div style={{ fontSize: 10, color: 'var(--foreground-muted)' }}>Policy Intelligence</div>
          </div>
        </div>
      </div>

      {/* Nav groups */}
      <nav style={{ flex: 1, overflowY: 'auto', padding: '8px 0' }}>
        {NAV_GROUPS.map(group => (
          <div key={group.label} style={{ marginBottom: 4 }}>
            <div style={{ padding: '12px 16px 4px' }}>
              <span style={{
                fontSize: 10, fontWeight: 600,
                textTransform: 'uppercase' as const,
                letterSpacing: '0.08em',
                color: 'var(--foreground-subtle)',
              }}>{group.label}</span>
            </div>
            <ul style={{ listStyle: 'none', margin: 0, padding: '0 8px' }}>
              {group.items.map(item => {
                const isActive =
                  (item.href === '/' && pathname === '/') ||
                  (item.href !== '/' && (pathname === item.href || pathname.startsWith(`${item.href}/`)))
                return (
                  <li key={item.href}>
                    <Link href={item.href} style={{
                      display: 'flex', alignItems: 'center', gap: 10,
                      padding: '8px 10px', borderRadius: 6, fontSize: 13,
                      fontWeight: isActive ? 500 : 400,
                      color: isActive ? 'var(--foreground)' : 'var(--foreground-muted)',
                      background: isActive ? 'var(--surface-3)' : 'transparent',
                      textDecoration: 'none',
                      transition: 'background 0.15s, color 0.15s',
                    }}>
                      <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {item.label}
                      </span>
                      {isActive && (
                        <span style={{
                          width: 6, height: 6, borderRadius: '50%',
                          background: 'var(--foreground)', flexShrink: 0,
                        }} />
                      )}
                    </Link>
                  </li>
                )
              })}
            </ul>
          </div>
        ))}
      </nav>

      {/* Footer: user chip + dark mode */}
      <div style={{ borderTop: '1px solid var(--border)', padding: '12px 16px' }}>
        {session && (
          <div style={{
            display: 'flex', alignItems: 'center', gap: 8,
            padding: '8px 10px', borderRadius: 6,
            background: 'var(--surface-2)', border: '1px solid var(--border)',
            marginBottom: 10,
          }}>
            <div style={{
              width: 28, height: 28, borderRadius: '50%',
              background: 'var(--foreground)', color: 'var(--background)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 11, fontWeight: 700, flexShrink: 0,
            }}>
              {session.username.slice(0, 2).toUpperCase()}
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{
                fontSize: 12, fontWeight: 600, color: 'var(--foreground)',
                overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
              }}>{session.username}</div>
              <div style={{ fontSize: 10, color: 'var(--foreground-subtle)' }}>Authenticated</div>
            </div>
            <button
              onClick={() => logout()}
              title="Sign out"
              style={{
                background: 'none', border: 'none', cursor: 'pointer',
                padding: 4, color: 'var(--foreground-subtle)',
                display: 'flex', alignItems: 'center', borderRadius: 4, flexShrink: 0,
              }}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                <polyline points="16 17 21 12 16 7" />
                <line x1="21" y1="12" x2="9" y2="12" />
              </svg>
            </button>
          </div>
        )}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <span style={{ fontSize: 11, color: 'var(--foreground-subtle)' }}>kprotect v0.1</span>
          <button
            onClick={toggleDark}
            style={{
              background: 'var(--surface-2)', border: '1px solid var(--border)',
              borderRadius: 6, padding: '4px 8px', cursor: 'pointer',
              fontSize: 13, color: 'var(--foreground-muted)',
              display: 'flex', alignItems: 'center', gap: 4,
            }}
            title={dark ? 'Light mode' : 'Dark mode'}
          >
            {dark ? '☀' : '☾'}
            <span style={{ fontSize: 10 }}>{dark ? 'Light' : 'Dark'}</span>
          </button>
        </div>
      </div>
    </nav>
  )
}
