'use client'

import { usePathname } from 'next/navigation'
import Link from 'next/link'
import { useState, useEffect } from 'react'
import { useSdk } from './sdk-provider'
import { scoreColor } from '@/lib/score-colors'

const NAV_ITEMS = [
  { href: '/', label: 'Dashboard' },
  { href: '/login', label: 'Login' },
  { href: '/scores', label: 'Scores' },
  { href: '/challenge', label: 'Challenge' },
  { href: '/bot-sim', label: 'Bot Sim' },
  { href: '/multi-user', label: 'Multi-User' },
]

export function Nav() {
  const pathname = usePathname()
  const { initialized, scores } = useSdk()
  const [dark, setDark] = useState(false)

  useEffect(() => {
    const stored = typeof window !== 'undefined' ? localStorage.getItem('kbio-dark') : null
    if (stored === 'true') {
      setDark(true)
      document.documentElement.setAttribute('data-theme', 'dark')
    }
  }, [])

  function toggleDark() {
    const next = !dark
    setDark(next)
    document.documentElement.setAttribute('data-theme', next ? 'dark' : 'light')
    localStorage.setItem('kbio-dark', String(next))
  }

  return (
    <nav style={{
      background: 'var(--nav-bg)',
      padding: '0 24px',
      display: 'flex',
      alignItems: 'center',
      height: 56,
      borderBottom: '2px solid var(--accent)',
      position: 'sticky',
      top: 0,
      zIndex: 100,
      backdropFilter: 'blur(12px)',
    }}>
      <Link href="/" style={{ display: 'flex', alignItems: 'center', gap: 10, textDecoration: 'none' }}>
        <div style={{
          width: 32,
          height: 32,
          borderRadius: 8,
          background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontWeight: 800,
          fontSize: 14,
          color: '#fff',
          letterSpacing: -1,
        }}>kb</div>
        <span style={{
          color: 'var(--text-primary)',
          fontSize: 17,
          fontWeight: 700,
          letterSpacing: -0.5,
        }}>kbio Demo</span>
      </Link>

      <div style={{ display: 'flex', gap: 4, marginLeft: 40 }}>
        {NAV_ITEMS.map(item => {
          const active = pathname === item.href
          return (
            <Link
              key={item.href}
              href={item.href}
              style={{
                color: active ? 'var(--accent)' : 'var(--text-secondary)',
                textDecoration: 'none',
                fontSize: 13,
                fontWeight: active ? 600 : 500,
                padding: '6px 14px',
                borderRadius: 6,
                background: active ? 'var(--accent-bg)' : 'transparent',
                transition: 'all 0.15s ease',
              }}
            >
              {item.label}
            </Link>
          )
        })}
      </div>

      <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 16 }}>
        {initialized && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            fontSize: 11,
            fontFamily: 'monospace',
            color: 'var(--text-muted)',
            background: 'var(--surface-alt)',
            padding: '4px 10px',
            borderRadius: 6,
          }}>
            <span style={{
              width: 7,
              height: 7,
              borderRadius: '50%',
              background: scoreColor(scores.drift),
              display: 'inline-block',
              boxShadow: `0 0 6px ${scoreColor(scores.drift)}`,
            }} />
            <span>SDK Active</span>
            <span style={{ color: scoreColor(scores.drift), fontWeight: 600 }}>
              {scores.drift >= 0 ? `D:${(scores.drift * 100).toFixed(0)}%` : '...'}
            </span>
          </div>
        )}

        <button
          onClick={toggleDark}
          style={{
            background: 'var(--surface-alt)',
            border: '1px solid var(--border)',
            borderRadius: 6,
            padding: '5px 10px',
            cursor: 'pointer',
            fontSize: 14,
            color: 'var(--text-primary)',
            lineHeight: 1,
          }}
          title={dark ? 'Switch to light mode' : 'Switch to dark mode'}
        >
          {dark ? '\u2600' : '\u263E'}
        </button>
      </div>
    </nav>
  )
}
