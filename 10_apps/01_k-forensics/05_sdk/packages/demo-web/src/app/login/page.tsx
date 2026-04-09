'use client'

import { useState, useRef } from 'react'
import { useSdk } from '@/components/sdk-provider'
import { Heatmap } from '@/components/heatmap'
import { scoreColor, scoreLabel } from '@/lib/score-colors'

type LoginAttempt = {
  id: number
  username: string
  drift: number
  anomaly: number
  match: boolean
  timestamp: number
}

export default function LoginPage() {
  const { scores, session } = useSdk()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [attempts, setAttempts] = useState<LoginAttempt[]>([])
  const [showResult, setShowResult] = useState(false)
  const [lastResult, setLastResult] = useState<LoginAttempt | null>(null)
  const attemptCounter = useRef(0)

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!username) return

    attemptCounter.current++
    // Drift score gets lower (more trusted) with repeated attempts
    const baseDrift = scores.drift >= 0 ? scores.drift : 0.3
    const repetitionBonus = Math.min(attempts.filter(a => a.username === username).length * 0.05, 0.2)
    const drift = Math.max(0, baseDrift - repetitionBonus)
    const match = drift < 0.5

    const attempt: LoginAttempt = {
      id: attemptCounter.current,
      username,
      drift,
      anomaly: scores.anomaly >= 0 ? scores.anomaly : 0.15,
      match,
      timestamp: Date.now(),
    }

    setAttempts(prev => [...prev, attempt])
    setLastResult(attempt)
    setShowResult(true)
  }

  return (
    <div>
      <div style={{ marginBottom: 28 }}>
        <h1 className="page-title">Behavioral Login Test</h1>
        <p className="page-subtitle">
          Type your credentials naturally. The SDK captures keystroke timing patterns to build a behavioral baseline.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
        {/* Login Form */}
        <div>
          <div className="card-lg">
            <div style={{ textAlign: 'center', marginBottom: 24 }}>
              <div style={{
                width: 52,
                height: 52,
                borderRadius: 14,
                background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginBottom: 12,
              }}>
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2">
                  <rect x="3" y="11" width="18" height="11" rx="2" />
                  <path d="M7 11V7a5 5 0 0110 0v4" />
                </svg>
              </div>
              <h2 style={{ margin: '0 0 4px', fontSize: 20, fontWeight: 700, color: 'var(--text-primary)' }}>Sign in to SecurBank</h2>
              <p style={{ margin: 0, fontSize: 13, color: 'var(--text-muted)' }}>Try logging in multiple times to build a baseline</p>
            </div>

            <form onSubmit={handleSubmit}>
              <div style={{ marginBottom: 18 }}>
                <label style={{ display: 'block', marginBottom: 6, fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)' }}>
                  Username
                </label>
                <input
                  type="text"
                  className="input"
                  placeholder="alice, bob, or charlie"
                  value={username}
                  onChange={e => setUsername(e.target.value)}
                  autoComplete="username"
                />
              </div>

              <div style={{ marginBottom: 22 }}>
                <label style={{ display: 'block', marginBottom: 6, fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)' }}>
                  Password
                </label>
                <input
                  type="password"
                  className="input"
                  placeholder="Type any password"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  autoComplete="current-password"
                />
              </div>

              <button type="submit" className="btn btn-primary" style={{ width: '100%', padding: '12px' }}>
                Sign In
              </button>
            </form>

            {/* Result display */}
            {showResult && lastResult && (
              <div style={{
                marginTop: 20,
                padding: 16,
                borderRadius: 10,
                background: lastResult.match ? '#22c55e10' : '#ef444410',
                border: `1px solid ${lastResult.match ? '#22c55e40' : '#ef444440'}`,
              }}>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 10,
                  marginBottom: 10,
                }}>
                  <span style={{
                    width: 32,
                    height: 32,
                    borderRadius: '50%',
                    background: lastResult.match ? '#22c55e20' : '#ef444420',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: 16,
                  }}>
                    {lastResult.match ? '\u2713' : '\u2717'}
                  </span>
                  <div>
                    <div style={{
                      fontSize: 15,
                      fontWeight: 700,
                      color: lastResult.match ? 'var(--success)' : 'var(--danger)',
                    }}>
                      {lastResult.match ? 'Behavioral Match' : 'Behavioral Mismatch'}
                    </div>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                      Credential drift: {scoreLabel(lastResult.drift)}
                    </div>
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                  <div style={{
                    padding: 10,
                    borderRadius: 8,
                    background: 'var(--surface)',
                    textAlign: 'center',
                  }}>
                    <div style={{ fontSize: 20, fontWeight: 700, color: scoreColor(lastResult.drift), fontFamily: 'monospace' }}>
                      {scoreLabel(lastResult.drift)}
                    </div>
                    <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 2 }}>Drift Score</div>
                  </div>
                  <div style={{
                    padding: 10,
                    borderRadius: 8,
                    background: 'var(--surface)',
                    textAlign: 'center',
                  }}>
                    <div style={{ fontSize: 20, fontWeight: 700, color: scoreColor(lastResult.anomaly), fontFamily: 'monospace' }}>
                      {scoreLabel(lastResult.anomaly)}
                    </div>
                    <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 2 }}>Anomaly Score</div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right column: heatmap + attempt history */}
        <div>
          {/* Zone Transition Matrix */}
          {session && (
            <div className="card" style={{ marginBottom: 20 }}>
              <Heatmap
                matrix={session.zone_matrix}
                title="Zone Transition Matrix"
                cellSize={28}
              />
            </div>
          )}

          {/* Attempt History */}
          {attempts.length > 0 && (
            <div className="card">
              <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 12 }}>
                Login Attempts ({attempts.length})
              </div>
              <div style={{ maxHeight: 280, overflow: 'auto' }}>
                {[...attempts].reverse().map(a => (
                  <div key={a.id} style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 10,
                    padding: '8px 0',
                    borderBottom: '1px solid var(--border)',
                  }}>
                    <span style={{
                      width: 8,
                      height: 8,
                      borderRadius: '50%',
                      background: a.match ? 'var(--success)' : 'var(--danger)',
                      flexShrink: 0,
                    }} />
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)' }}>
                        {a.username}
                      </div>
                      <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>
                        #{a.id} &middot; drift {scoreLabel(a.drift)}
                      </div>
                    </div>
                    <span style={{
                      fontSize: 11,
                      fontWeight: 600,
                      color: a.match ? 'var(--success)' : 'var(--danger)',
                    }}>
                      {a.match ? 'MATCH' : 'MISMATCH'}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {attempts.length === 0 && (
            <div className="card" style={{ textAlign: 'center', padding: '48px 24px' }}>
              <div style={{ fontSize: 32, marginBottom: 12, opacity: 0.3 }}>&#9000;</div>
              <div style={{ fontSize: 14, color: 'var(--text-muted)', fontWeight: 500 }}>
                No login attempts yet
              </div>
              <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>
                Try logging in to see behavioral analysis
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
