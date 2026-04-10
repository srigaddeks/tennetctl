'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useAuth } from '@/components/auth-provider'

export default function SignupPage() {
  const { register } = useAuth()
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  function validate(): string | null {
    if (username.trim().length < 3) return 'Username must be at least 3 characters.'
    if (!email.includes('@')) return 'Enter a valid email address.'
    if (password.length < 6) return 'Password must be at least 6 characters.'
    if (password !== confirm) return 'Passwords do not match.'
    return null
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const err = validate()
    if (err) { setError(err); return }
    setSubmitting(true)
    setError(null)
    try {
      await register(username.trim().toLowerCase(), email.trim(), password)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Registration failed')
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
        <h1 style={{ margin: '0 0 4px', fontSize: 22, fontWeight: 700, color: 'var(--foreground)' }}>Create Account</h1>
        <p style={{ margin: 0, fontSize: 13, color: 'var(--foreground-muted)' }}>
          Your own policy workspace, ready in seconds
        </p>
      </div>

      <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, padding: 32 }}>
        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: 18 }}>
            <label style={labelStyle}>Username</label>
            <input
              type="text"
              placeholder="min 3 characters"
              value={username}
              onChange={e => setUsername(e.target.value)}
              autoComplete="username"
              disabled={submitting}
              style={inputStyle}
            />
          </div>

          <div style={{ marginBottom: 18 }}>
            <label style={labelStyle}>Email</label>
            <input
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={e => setEmail(e.target.value)}
              autoComplete="email"
              disabled={submitting}
              style={inputStyle}
            />
          </div>

          <div style={{ marginBottom: 18 }}>
            <label style={labelStyle}>Password</label>
            <input
              type="password"
              placeholder="at least 6 characters"
              value={password}
              onChange={e => setPassword(e.target.value)}
              autoComplete="new-password"
              disabled={submitting}
              style={inputStyle}
            />
          </div>

          <div style={{ marginBottom: 22 }}>
            <label style={labelStyle}>Confirm password</label>
            <input
              type="password"
              placeholder="repeat password"
              value={confirm}
              onChange={e => setConfirm(e.target.value)}
              autoComplete="new-password"
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
            disabled={submitting}
            style={{
              width: '100%', padding: 12, borderRadius: 6, border: 'none',
              background: submitting ? 'var(--surface-2)' : 'var(--foreground)',
              color: submitting ? 'var(--foreground-subtle)' : 'var(--background)',
              fontSize: 14, fontWeight: 600,
              cursor: submitting ? 'not-allowed' : 'pointer',
            }}
          >
            {submitting ? 'Creating account…' : 'Create Account'}
          </button>
        </form>

        <div style={{ marginTop: 20, textAlign: 'center', fontSize: 12, color: 'var(--foreground-subtle)' }}>
          Already have an account?{' '}
          <Link href="/login" style={{ color: 'var(--foreground)', fontWeight: 600 }}>Sign in</Link>
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
