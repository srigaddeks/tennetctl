'use client'

import { useState, useRef } from 'react'
import Link from 'next/link'
import { useSdk } from '@/components/sdk-provider'
import { useAuth } from '@/components/auth-provider'
import { scoreColor, scoreLabel } from '@/lib/score-colors'

export default function LoginPage() {
  const { scores, v2Scores } = useSdk()
  const { login } = useAuth()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [lastUsername, setLastUsername] = useState<string | null>(null)

  const prevScoresRef = useRef(scores)
  if (scores) prevScoresRef.current = scores
  const displayScores = scores ?? prevScoresRef.current

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!username || !password || submitting) return

    setSubmitting(true)
    setError(null)
    try {
      await login(username, password)
      setLastUsername(username)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Login failed')
    } finally {
      setSubmitting(false)
    }
  }

  const inputStyle = {
    width: '100%', padding: '10px 14px', borderRadius: 6,
    border: '1px solid var(--border)', background: 'var(--surface)',
    color: 'var(--foreground)', fontSize: 14, outline: 'none',
    boxSizing: 'border-box' as const,
  }

  const labelStyle = {
    display: 'block', marginBottom: 6, fontSize: 11, fontWeight: 600,
    color: 'var(--foreground-muted)', textTransform: 'uppercase' as const,
    letterSpacing: '0.04em',
  }

  return (
    <div>
      <div style={{ marginBottom: 28 }}>
        <h1 style={{ margin: '0 0 4px', fontSize: 24, fontWeight: 700, letterSpacing: '-0.025em', color: 'var(--foreground)' }}>
          Behavioral Login
        </h1>
        <p style={{ margin: 0, fontSize: 13, color: 'var(--foreground-muted)' }}>
          Type your credentials naturally. The SDK captures keystroke timing patterns to build a behavioral baseline.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
        {/* Login Form */}
        <div>
          <div style={{
            background: 'var(--surface)', border: '1px solid var(--border)',
            borderRadius: 6, padding: 32,
          }}>
            <div style={{ textAlign: 'center', marginBottom: 24 }}>
              <div style={{
                width: 48, height: 48, borderRadius: 12,
                background: 'var(--foreground)', display: 'inline-flex',
                alignItems: 'center', justifyContent: 'center', marginBottom: 12,
              }}>
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="var(--background)" strokeWidth="2">
                  <rect x="3" y="11" width="18" height="11" rx="2" />
                  <path d="M7 11V7a5 5 0 0110 0v4" />
                </svg>
              </div>
              <h2 style={{ margin: '0 0 4px', fontSize: 18, fontWeight: 700, color: 'var(--foreground)' }}>Sign In</h2>
              <p style={{ margin: 0, fontSize: 12, color: 'var(--foreground-subtle)' }}>
                Type naturally — keystroke timing is captured while you type
              </p>
            </div>

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
                  background: 'var(--danger-bg, #2d1212)', border: '1px solid var(--danger)',
                  color: 'var(--danger)', fontSize: 13,
                }}>
                  {error}
                </div>
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
                  transition: 'background 0.15s',
                }}
              >
                {submitting ? 'Signing in…' : 'Sign In'}
              </button>
            </form>

            <div style={{ marginTop: 20, textAlign: 'center', fontSize: 12, color: 'var(--foreground-subtle)' }}>
              No account?{' '}
              <Link href="/signup" style={{ color: 'var(--foreground-muted)', textDecoration: 'underline' }}>
                Sign up
              </Link>
            </div>
          </div>
        </div>

        {/* Right column: live scores while typing */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          {/* Live identity scores */}
          {v2Scores ? (
            <div style={{
              background: 'var(--surface)', border: '1px solid var(--border)',
              borderRadius: 6, padding: 24,
            }}>
              <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--foreground)', marginBottom: 12 }}>
                Live Identity Scores
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                {[
                  { label: 'Behavioral Drift', value: v2Scores.identity.behavioral_drift },
                  { label: 'Identity Confidence', value: v2Scores.identity.identity_confidence },
                  { label: 'Familiarity', value: v2Scores.identity.familiarity_score },
                  { label: 'Session Trust', value: v2Scores.trust.session_trust },
                ].map(s => (
                  <div key={s.label} style={{ padding: 10, borderRadius: 4, background: 'var(--surface-2)' }}>
                    <div style={{ fontSize: 10, color: 'var(--foreground-subtle)', marginBottom: 4 }}>{s.label}</div>
                    <div style={{
                      fontSize: 16, fontWeight: 700, fontFamily: 'var(--font-mono)',
                      color: s.value >= 0 ? scoreColor(s.value) : 'var(--foreground-subtle)',
                    }}>
                      {s.value >= 0 ? `${(s.value * 100).toFixed(1)}%` : '--'}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : displayScores ? (
            <div style={{
              background: 'var(--surface)', border: '1px solid var(--border)',
              borderRadius: 6, padding: 24,
            }}>
              <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--foreground)', marginBottom: 12 }}>
                Live Scores
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 10 }}>
                {[
                  { label: 'Drift', value: displayScores.drift },
                  { label: 'Anomaly', value: displayScores.anomaly },
                  { label: 'Trust', value: displayScores.trust },
                ].map(s => (
                  <div key={s.label} style={{ padding: 10, borderRadius: 4, background: 'var(--surface-2)', textAlign: 'center' }}>
                    <div style={{ fontSize: 10, color: 'var(--foreground-subtle)', marginBottom: 4 }}>{s.label}</div>
                    <div style={{
                      fontSize: 18, fontWeight: 700, fontFamily: 'var(--font-mono)',
                      color: s.value >= 0 ? scoreColor(s.value) : 'var(--foreground-subtle)',
                    }}>
                      {s.value >= 0 ? scoreLabel(s.value) : '--'}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div style={{
              background: 'var(--surface)', border: '1px dashed var(--border)',
              borderRadius: 6, padding: '32px 24px', textAlign: 'center',
            }}>
              <div style={{ fontSize: 13, color: 'var(--foreground-subtle)' }}>
                Type your credentials to generate behavioral data
              </div>
              <div style={{ fontSize: 11, color: 'var(--foreground-subtle)', marginTop: 4 }}>
                Scores will appear after the first scoring response
              </div>
            </div>
          )}

          {/* Last successful login indicator */}
          {lastUsername && (
            <div style={{
              padding: '12px 16px', borderRadius: 6,
              background: 'var(--success-bg, #0d2414)', border: '1px solid var(--success)',
              display: 'flex', alignItems: 'center', gap: 10,
            }}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--success)" strokeWidth="2">
                <polyline points="20 6 9 17 4 12" />
              </svg>
              <div>
                <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--foreground)' }}>
                  Signed in as {lastUsername}
                </div>
                <div style={{ fontSize: 11, color: 'var(--foreground-subtle)' }}>
                  Redirecting…
                </div>
              </div>
            </div>
          )}

          {/* Hint */}
          <div style={{
            background: 'var(--surface)', border: '1px solid var(--border)',
            borderRadius: 6, padding: 16,
          }}>
            <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--foreground-muted)', marginBottom: 8 }}>
              HOW IT WORKS
            </div>
            <ul style={{ margin: 0, padding: '0 0 0 16px', fontSize: 12, color: 'var(--foreground-subtle)', lineHeight: 1.7 }}>
              <li>SDK captures keystroke dwell + flight times as you type</li>
              <li>Behavioral batch sent to kbio scoring engine</li>
              <li>Drift, anomaly, trust scores update in real time</li>
              <li>Repeated logins build your personal baseline</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}
