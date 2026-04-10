'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useAuth } from '@/components/auth-provider'

export default function LoginPage() {
  const { login } = useAuth()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!username || !password || submitting) return
    setSubmitting(true)
    setError(null)
    try {
      await login(username, password)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Login failed')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div>
      <div style={{ textAlign: 'center', marginBottom: 28 }}>
        <div style={{
          width: 44, height: 44, borderRadius: 10,
          background: 'var(--foreground)', color: 'var(--background)',
          display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 14, fontWeight: 800, marginBottom: 14,
        }}>KP</div>
        <h1 style={{ margin: '0 0 4px', fontSize: 22, fontWeight: 700, color: 'var(--foreground)' }}>KProtect</h1>
        <p style={{ margin: 0, fontSize: 13, color: 'var(--foreground-muted)' }}>
          Sign in to your policy intelligence dashboard
        </p>
      </div>

      <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, padding: 32 }}>
        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: 18 }}>
            <label style={labelStyle}>Username</label>
            <input
              type="text"
              placeholder="your username"
              value={username}
              onChange={e => setUsername(e.target.value)}
              autoComplete="username"
              disabled={submitting}
              style={inputStyle}
            />
          </div>

          <div style={{ marginBottom: 22 }}>
            <label style={labelStyle}>Password</label>
            <input
              type="password"
              placeholder="your password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              autoComplete="current-password"
              disabled={submitting}
              style={inputStyle}
            />
          </div>

          {error && (
            <div style={{
              marginBottom: 16, padding: '10px 14px', borderRadius: 6,
              background: 'var(--danger-bg)', border: '1px solid var(--danger)',
              color: 'var(--danger)', fontSize: 13,
            }}>{error}</div>
          )}

          <button
            type="submit"
            disabled={submitting || !username || !password}
            style={{
              width: '100%', padding: 12, borderRadius: 6, border: 'none',
              background: submitting || !username || !password ? 'var(--surface-2)' : 'var(--foreground)',
              color: submitting || !username || !password ? 'var(--foreground-subtle)' : 'var(--background)',
              fontSize: 14, fontWeight: 600,
              cursor: submitting || !username || !password ? 'not-allowed' : 'pointer',
            }}
          >
            {submitting ? 'Signing in…' : 'Sign In'}
          </button>
        </form>

        <div style={{ marginTop: 20, textAlign: 'center', fontSize: 12, color: 'var(--foreground-subtle)' }}>
          No account?{' '}
          <Link href="/signup" style={{ color: 'var(--foreground)', fontWeight: 600 }}>Sign up</Link>
        </div>
      </div>
    </div>
  )
}

const inputStyle: React.CSSProperties = {
  width: '100%', padding: '10px 14px', borderRadius: 6,
  border: '1px solid var(--border)', background: 'var(--surface)',
  color: 'var(--foreground)', fontSize: 14, outline: 'none', boxSizing: 'border-box',
}

const labelStyle: React.CSSProperties = {
  display: 'block', marginBottom: 6, fontSize: 11, fontWeight: 600,
  color: 'var(--foreground-muted)', textTransform: 'uppercase', letterSpacing: '0.04em',
}
