'use client'

import { usePathname } from 'next/navigation'
import Link from 'next/link'
import { useState, useEffect } from 'react'
import { useSdk } from './sdk-provider'
import { useAuth } from './auth-provider'

const NAV_GROUPS = [
  {
    label: 'Overview',
    items: [
      { href: '/', label: 'Dashboard', icon: 'grid' },
    ],
  },
  {
    label: 'SDK Demos',
    items: [
      { href: '/login', label: 'Behavioral Login', icon: 'lock' },
      { href: '/scores', label: 'Live Scores', icon: 'activity' },
      { href: '/v2-scores', label: 'V2 AI Engine', icon: 'cpu' },
      { href: '/challenge', label: 'KP-Challenge', icon: 'key' },
      { href: '/bot-sim', label: 'Bot Detection', icon: 'shield' },
      { href: '/multi-user', label: 'Multi-User', icon: 'users' },
    ],
  },
]

const ICONS: Record<string, React.ReactNode> = {
  grid: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>,
  lock: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0110 0v4"/></svg>,
  activity: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>,
  cpu: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/><path d="M15 2v2"/><path d="M15 20v2"/><path d="M2 15h2"/><path d="M2 9h2"/><path d="M20 15h2"/><path d="M20 9h2"/><path d="M9 2v2"/><path d="M9 20v2"/></svg>,
  key: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 2l-2 2m-7.61 7.61a5.5 5.5 0 1 1-7.778 7.778 5.5 5.5 0 0 1 7.777-7.777zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3m-3.5 3.5L19 4"/></svg>,
  shield: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>,
  users: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>,
}

function scoreColor(score: number): string {
  if (score < 0) return 'var(--foreground-subtle)'
  if (score <= 0.3) return 'var(--success)'
  if (score <= 0.6) return 'var(--warning)'
  if (score <= 0.8) return 'var(--danger)'
  return 'var(--danger)'
}

export function Sidebar() {
  const pathname = usePathname()

  return (
    <>
      {/* Desktop sidebar */}
      <aside style={{
        position: 'sticky',
        top: 0,
        height: '100vh',
        width: 240,
        flexShrink: 0,
        display: 'flex',
        flexDirection: 'column',
        borderRight: '1px solid var(--border)',
        background: 'var(--surface)',
      }}>
        <SidebarContent pathname={pathname} />
      </aside>
    </>
  )
}

function SidebarContent({ pathname, onNavigate }: { pathname: string; onNavigate?: () => void }) {
  const { initialized, scores, session } = useSdk()
  const { session: authSession, isLoggedIn, logout } = useAuth()
  const [dark, setDark] = useState(false)

  useEffect(() => {
    const stored = typeof window !== 'undefined' ? localStorage.getItem('kbio-dark') : null
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
    localStorage.setItem('kbio-dark', String(next))
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', flex: 1, minHeight: 0 }}>
      {/* App branding */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        padding: '14px 16px',
        borderBottom: '1px solid var(--border)',
      }}>
        <div style={{
          width: 32,
          height: 32,
          borderRadius: 6,
          background: 'var(--foreground)',
          color: 'var(--background)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: 12,
          fontWeight: 800,
          flexShrink: 0,
        }}>kb</div>
        <div style={{ minWidth: 0, flex: 1 }}>
          <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--foreground)' }}>kbio Demo</div>
          <div style={{ fontSize: 10, color: 'var(--foreground-muted)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
            Behavioral Biometrics SDK
          </div>
        </div>
      </div>

      {/* SDK Status */}
      {initialized && (
        <div style={{
          padding: '10px 16px',
          borderBottom: '1px solid var(--border)',
          display: 'flex',
          alignItems: 'center',
          gap: 8,
        }}>
          <span style={{
            width: 7,
            height: 7,
            borderRadius: '50%',
            background: 'var(--success)',
            display: 'inline-block',
            boxShadow: `0 0 6px var(--success)`,
            flexShrink: 0,
          }} />
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: 11, color: 'var(--foreground-muted)', fontWeight: 500 }}>SDK Active</div>
            <div style={{
              fontSize: 10,
              fontFamily: 'var(--font-mono)',
              color: 'var(--foreground-subtle)',
              display: 'flex',
              gap: 8,
            }}>
              <span>D:<span style={{ color: scores && scores.drift >= 0 ? scoreColor(scores.drift) : 'var(--foreground-subtle)', fontWeight: 600 }}>{scores && scores.drift >= 0 ? `${(scores.drift * 100).toFixed(0)}%` : '--'}</span></span>
              <span>T:<span style={{ color: scores && scores.trust >= 0 ? scoreColor(1 - scores.trust) : 'var(--foreground-subtle)', fontWeight: 600 }}>{scores && scores.trust >= 0 ? `${(scores.trust * 100).toFixed(0)}%` : '--'}</span></span>
            </div>
          </div>
          {session && (
            <div style={{ fontSize: 9, fontFamily: 'var(--font-mono)', color: 'var(--foreground-subtle)' }}>
              p:{session.pulse_count}
            </div>
          )}
        </div>
      )}

      {/* Nav groups */}
      <nav style={{ flex: 1, overflowY: 'auto', padding: '8px 0' }}>
        {NAV_GROUPS.map((group) => (
          <div key={group.label} style={{ marginBottom: 4 }}>
            <div style={{ padding: '12px 16px 4px' }}>
              <span style={{
                fontSize: 10,
                fontWeight: 600,
                textTransform: 'uppercase' as const,
                letterSpacing: '0.08em',
                color: 'var(--foreground-subtle)',
              }}>{group.label}</span>
            </div>
            <ul style={{ listStyle: 'none', margin: 0, padding: '0 8px' }}>
              {group.items.map((item) => {
                const isActive =
                  (item.href === '/' && pathname === '/') ||
                  (item.href !== '/' && (pathname === item.href || pathname.startsWith(`${item.href}/`)))
                return (
                  <li key={item.href}>
                    <Link
                      href={item.href}
                      onClick={onNavigate}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 10,
                        padding: '8px 10px',
                        borderRadius: 6,
                        fontSize: 13,
                        fontWeight: isActive ? 500 : 400,
                        color: isActive ? 'var(--foreground)' : 'var(--foreground-muted)',
                        background: isActive ? 'var(--surface-3)' : 'transparent',
                        textDecoration: 'none',
                        transition: 'background 0.15s, color 0.15s',
                      }}
                    >
                      <span style={{
                        color: isActive ? 'var(--foreground)' : 'var(--foreground-subtle)',
                        display: 'flex',
                        alignItems: 'center',
                        flexShrink: 0,
                      }}>
                        {ICONS[item.icon]}
                      </span>
                      <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {item.label}
                      </span>
                      {isActive && (
                        <span style={{
                          width: 6,
                          height: 6,
                          borderRadius: '50%',
                          background: 'var(--foreground)',
                          flexShrink: 0,
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

      {/* Footer: user chip + session info + theme toggle */}
      <div style={{
        borderTop: '1px solid var(--border)',
        padding: '12px 16px',
      }}>
        {/* SDK session info */}
        {session && (
          <div style={{
            fontSize: 10,
            fontFamily: 'var(--font-mono)',
            color: 'var(--foreground-subtle)',
            marginBottom: 10,
            lineHeight: 1.6,
          }}>
            <div>sid: {session.session_id.slice(0, 8)}...</div>
            <div>uptime: {Math.floor((Date.now() - session.started_at) / 1000)}s</div>
          </div>
        )}

        {/* Authenticated user chip */}
        {isLoggedIn && authSession && (
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
              {authSession.username.slice(0, 2).toUpperCase()}
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{
                fontSize: 12, fontWeight: 600, color: 'var(--foreground)',
                overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
              }}>
                {authSession.username}
              </div>
              <div style={{ fontSize: 10, color: 'var(--foreground-subtle)' }}>Authenticated</div>
            </div>
            <button
              onClick={() => logout()}
              title="Sign out"
              style={{
                background: 'none', border: 'none', cursor: 'pointer',
                padding: 4, color: 'var(--foreground-subtle)',
                display: 'flex', alignItems: 'center', borderRadius: 4,
                flexShrink: 0,
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
          <span style={{ fontSize: 11, color: 'var(--foreground-subtle)' }}>
            kbio SDK Demo
          </span>
          <button
            onClick={toggleDark}
            style={{
              background: 'var(--surface-2)',
              border: '1px solid var(--border)',
              borderRadius: 6,
              padding: '4px 8px',
              cursor: 'pointer',
              fontSize: 13,
              color: 'var(--foreground-muted)',
              lineHeight: 1,
              display: 'flex',
              alignItems: 'center',
              gap: 4,
            }}
            title={dark ? 'Switch to light mode' : 'Switch to dark mode'}
          >
            {dark ? '\u2600' : '\u263E'}
            <span style={{ fontSize: 10 }}>{dark ? 'Light' : 'Dark'}</span>
          </button>
        </div>
      </div>
    </div>
  )
}

/* Mobile topbar for smaller screens */
export function MobileTopbar({ onToggle, open }: { onToggle: () => void; open: boolean }) {
  return (
    <header style={{
      display: 'flex',
      alignItems: 'center',
      height: 48,
      padding: '0 12px',
      borderBottom: '1px solid var(--border)',
      background: 'var(--surface)',
    }}>
      <button
        onClick={onToggle}
        style={{
          background: 'none',
          border: 'none',
          cursor: 'pointer',
          padding: 8,
          color: 'var(--foreground)',
          fontSize: 18,
        }}
        aria-label={open ? 'Close menu' : 'Open menu'}
      >
        {open ? '\u2715' : '\u2630'}
      </button>
      <span style={{ marginLeft: 8, fontSize: 14, fontWeight: 600, color: 'var(--foreground)' }}>
        kbio Demo
      </span>
    </header>
  )
}

export function MobileSidebar({ open, onClose }: { open: boolean; onClose: () => void }) {
  const pathname = usePathname()

  if (!open) return null

  return (
    <>
      {/* Backdrop */}
      <div
        onClick={onClose}
        style={{
          position: 'fixed',
          inset: 0,
          zIndex: 30,
          background: 'rgba(0,0,0,0.4)',
        }}
      />
      {/* Drawer */}
      <aside style={{
        position: 'fixed',
        top: 0,
        left: 0,
        bottom: 0,
        width: 280,
        zIndex: 40,
        display: 'flex',
        flexDirection: 'column',
        borderRight: '1px solid var(--border)',
        background: 'var(--surface)',
      }}>
        <SidebarContent pathname={pathname} onNavigate={onClose} />
      </aside>
    </>
  )
}
