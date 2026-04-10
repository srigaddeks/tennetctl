'use client'

import { useState, useRef, useCallback, useEffect } from 'react'
import { useSdk } from '@/components/sdk-provider'
import { ScoreGauge } from '@/components/score-gauge'
import { scoreColor, trustColor, scoreLabel } from '@/lib/score-colors'

type UserProfile = {
  name: string
  color: string
}

const USERS: UserProfile[] = [
  { name: 'Alice', color: '#555555' },
  { name: 'Bob', color: '#888888' },
  { name: 'Charlie', color: '#22c55e' },
  { name: 'Diana', color: '#ef4444' },
  { name: 'Eve', color: '#eab308' },
]

type SwitchEvent = {
  id: number
  from: string
  to: string
  driftBefore: number | null
  driftAfter: number | 'pending'
  timestamp: number
}

export default function MultiUserPage() {
  const { scores, setUser, logout } = useSdk()
  const [activeUser, setActiveUser] = useState<string | null>(null)
  const [switchEvents, setSwitchEvents] = useState<SwitchEvent[]>([])
  const counter = useRef(0)

  useEffect(() => {
    if (scores?.drift === undefined) return
    setSwitchEvents(prev => {
      const lastPendingIdx = [...prev].map((e, i) => ({ e, i })).reverse().find(({ e }) => e.driftAfter === 'pending')
      if (lastPendingIdx === undefined) return prev
      return prev.map((e, i): SwitchEvent =>
        i === lastPendingIdx.i ? { ...e, driftAfter: scores.drift } : e
      )
    })
  }, [scores?.drift])

  const switchUserTo = useCallback((userName: string) => {
    const prevUser = activeUser
    const prevDrift = scores?.drift ?? null

    logout()
    setUser(userName)

    if (prevUser && prevUser !== userName) {
      counter.current++
      setSwitchEvents(prev => [...prev, {
        id: counter.current,
        from: prevUser,
        to: userName,
        driftBefore: prevDrift,
        driftAfter: 'pending',
        timestamp: Date.now(),
      }])
    }

    setActiveUser(userName)
  }, [activeUser, scores?.drift, setUser, logout])

  return (
    <div>
      <div style={{ marginBottom: 28 }}>
        <h1 style={{ margin: '0 0 4px', fontSize: 24, fontWeight: 700, letterSpacing: '-0.025em', color: 'var(--foreground)' }}>
          Multi-User Detection
        </h1>
        <p style={{ margin: 0, fontSize: 13, color: 'var(--foreground-muted)' }}>
          Switch between users to see how drift scores change when a different person uses the session
        </p>
      </div>

      {/* User selector */}
      <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 6, padding: 24, marginBottom: 24 }}>
        <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--foreground)', marginBottom: 14 }}>Select Active User</div>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          {USERS.map(user => (
            <button key={user.name} onClick={() => switchUserTo(user.name)} style={{
              padding: '10px 24px', borderRadius: 6,
              border: activeUser === user.name ? '2px solid var(--foreground)' : '2px solid var(--border)',
              background: activeUser === user.name ? 'var(--surface-3)' : 'var(--surface)',
              color: activeUser === user.name ? 'var(--foreground)' : 'var(--foreground-muted)',
              fontSize: 14, fontWeight: 600, cursor: 'pointer', transition: 'all 0.2s ease',
              display: 'flex', alignItems: 'center', gap: 8,
            }}>
              <span style={{
                width: 10, height: 10, borderRadius: '50%',
                background: user.color,
                opacity: activeUser === user.name ? 1 : 0.4,
              }} />
              {user.name}
            </button>
          ))}
        </div>
        {activeUser && (
          <div style={{ marginTop: 12, fontSize: 12, color: 'var(--foreground-subtle)', fontFamily: 'var(--font-mono)' }}>
            Active: {activeUser}
            {scores ? ` \u00B7 Drift: ${scoreLabel(scores.drift)} \u00B7 Trust: ${scoreLabel(scores.trust)}` : ' \u00B7 Waiting for scores...'}
          </div>
        )}
      </div>

      {/* Current scores */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 24 }}>
        {[
          { label: 'Drift Score', score: scores?.drift ?? -1, colorFn: scoreColor },
          { label: 'Anomaly Score', score: scores?.anomaly ?? -1, colorFn: scoreColor },
          { label: 'Trust Score', score: scores?.trust ?? -1, colorFn: trustColor },
          { label: 'Bot Score', score: scores?.bot ?? -1, colorFn: scoreColor },
        ].map(g => (
          <div key={g.label} style={{
            background: 'var(--surface)', border: '1px solid var(--border)',
            borderRadius: 6, display: 'flex', justifyContent: 'center', padding: '20px 12px',
          }}>
            <ScoreGauge label={g.label} score={g.score} colorFn={g.colorFn} size={120} />
          </div>
        ))}
      </div>

      {/* Switch Events */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 360px', gap: 16 }}>
        {/* Instructions */}
        <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 6, padding: 24 }}>
          <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--foreground)', marginBottom: 12 }}>How to Test</div>
          <div style={{ fontSize: 12, color: 'var(--foreground-muted)', lineHeight: 1.7 }}>
            <p style={{ margin: '0 0 12px' }}>
              <strong>1.</strong> Select a user (e.g. Alice) and type naturally for 15-30 seconds. This builds a behavioral baseline for that user.
            </p>
            <p style={{ margin: '0 0 12px' }}>
              <strong>2.</strong> Switch to a different user (e.g. Bob). The backend will detect the behavioral shift because your typing rhythm changes relative to Alice&apos;s baseline.
            </p>
            <p style={{ margin: '0 0 12px' }}>
              <strong>3.</strong> Watch the drift score spike after the switch. The scoring engine compares live behavior against the stored profile.
            </p>
            <p style={{ margin: 0 }}>
              <strong>Real-world use:</strong> This detects account sharing, credential theft, and session hijacking — all without passwords or MFA.
            </p>
          </div>

          {/* Typing area */}
          <div style={{ marginTop: 20 }}>
            <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--foreground-subtle)', marginBottom: 8, textTransform: 'uppercase' as const, letterSpacing: '0.04em' }}>
              Type here to generate behavioral data
            </div>
            <textarea
              placeholder="Type anything here... The SDK captures your keystroke timing, not your content."
              style={{
                width: '100%', height: 100, padding: '10px 14px', borderRadius: 6,
                border: '1px solid var(--border)', background: 'var(--surface-2)',
                color: 'var(--foreground)', fontSize: 13, outline: 'none',
                boxSizing: 'border-box', resize: 'none', fontFamily: 'inherit',
              }}
            />
          </div>
        </div>

        <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 6, padding: 24 }}>
          <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--foreground)', marginBottom: 14 }}>
            Switch Events ({switchEvents.length})
          </div>
          {switchEvents.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px 0', color: 'var(--foreground-subtle)', fontSize: 12 }}>
              Switch between users to generate events
            </div>
          ) : (
            <div style={{ maxHeight: 360, overflow: 'auto' }}>
              {[...switchEvents].reverse().map(e => (
                <div key={e.id} style={{ padding: '10px 0', borderBottom: '1px solid var(--border)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6 }}>
                    <span style={{ fontSize: 12, fontWeight: 600, color: USERS.find(u => u.name === e.from)?.color ?? 'var(--foreground-muted)' }}>{e.from}</span>
                    <span style={{ fontSize: 10, color: 'var(--foreground-subtle)' }}>&rarr;</span>
                    <span style={{ fontSize: 12, fontWeight: 600, color: USERS.find(u => u.name === e.to)?.color ?? 'var(--foreground-muted)' }}>{e.to}</span>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                    <span style={{ fontSize: 10, color: 'var(--foreground-subtle)' }}>
                      drift before: <span style={{ color: e.driftBefore != null ? scoreColor(e.driftBefore) : 'var(--foreground-subtle)', fontWeight: 600 }}>
                        {e.driftBefore != null ? scoreLabel(e.driftBefore) : '--'}
                      </span>
                    </span>
                    <span style={{ fontSize: 10, color: 'var(--foreground-subtle)' }}>
                      drift after: {e.driftAfter === 'pending'
                        ? <span style={{ color: 'var(--foreground-subtle)', fontWeight: 600, fontStyle: 'italic' }}>pending</span>
                        : <span style={{ color: scoreColor(e.driftAfter), fontWeight: 600 }}>{scoreLabel(e.driftAfter)}</span>
                      }
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
