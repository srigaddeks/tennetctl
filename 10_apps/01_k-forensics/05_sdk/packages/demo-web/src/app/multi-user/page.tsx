'use client'

import { useState, useRef, useCallback } from 'react'
import { useSdk } from '@/components/sdk-provider'
import { MockKProtect } from '@/lib/mock-sdk'
import { ScoreGauge } from '@/components/score-gauge'
import { scoreColor, trustColor, scoreLabel } from '@/lib/score-colors'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

type UserProfile = {
  name: string
  color: string
  switches: Array<{ time: number; drift: number }>
}

const USERS: UserProfile[] = [
  { name: 'Alice', color: '#6366f1', switches: [] },
  { name: 'Bob', color: '#f97316', switches: [] },
  { name: 'Charlie', color: '#22c55e', switches: [] },
  { name: 'Diana', color: '#ec4899', switches: [] },
  { name: 'Eve', color: '#eab308', switches: [] },
]

const USER_COLORS: Record<string, string> = {
  Alice: '#6366f1',
  Bob: '#f97316',
  Charlie: '#22c55e',
  Diana: '#ec4899',
  Eve: '#eab308',
}

type SwitchEvent = {
  id: number
  from: string
  to: string
  driftBefore: number
  driftAfter: number
  timestamp: number
}

export default function MultiUserPage() {
  const { scores } = useSdk()
  const [activeUser, setActiveUser] = useState<string | null>(null)
  const [switchEvents, setSwitchEvents] = useState<SwitchEvent[]>([])
  const [comparisonData, setComparisonData] = useState<Array<Record<string, unknown>>>([])
  const counter = useRef(0)

  const switchUser = useCallback((userName: string) => {
    const prevUser = activeUser
    const prevDrift = scores.drift >= 0 ? scores.drift : 0

    // Trigger SDK logout + re-login
    MockKProtect.logout()
    MockKProtect.setUser(userName)
    MockKProtect._simulateUserSwitch(userName)

    const newDrift = MockKProtect.getLatestDrift()?.drift || 0.5

    if (prevUser && prevUser !== userName) {
      counter.current++
      const event: SwitchEvent = {
        id: counter.current,
        from: prevUser,
        to: userName,
        driftBefore: prevDrift,
        driftAfter: newDrift,
        timestamp: Date.now(),
      }
      setSwitchEvents(prev => [...prev, event])
    }

    // Update comparison chart data
    setComparisonData(prev => {
      const point: Record<string, unknown> = {
        idx: prev.length,
        time: new Date().toLocaleTimeString([], { minute: '2-digit', second: '2-digit' }),
      }
      point[userName] = +(newDrift * 100).toFixed(1)
      // Carry forward last known value for other users
      if (prev.length > 0) {
        const last = prev[prev.length - 1]
        for (const u of USERS) {
          if (u.name !== userName && last[u.name] !== undefined) {
            point[u.name] = last[u.name]
          }
        }
      }
      return [...prev, point]
    })

    setActiveUser(userName)
  }, [activeUser, scores.drift])

  return (
    <div>
      <div style={{ marginBottom: 28 }}>
        <h1 className="page-title">Multi-User Detection</h1>
        <p className="page-subtitle">
          Switch between users to see how drift scores change when a different person uses the session
        </p>
      </div>

      {/* User selector */}
      <div className="card" style={{ marginBottom: 24 }}>
        <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 14 }}>
          Select Active User
        </div>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          {USERS.map(user => (
            <button
              key={user.name}
              onClick={() => switchUser(user.name)}
              style={{
                padding: '10px 24px',
                borderRadius: 10,
                border: activeUser === user.name ? `2px solid ${user.color}` : '2px solid var(--border)',
                background: activeUser === user.name ? `${user.color}15` : 'var(--surface)',
                color: activeUser === user.name ? user.color : 'var(--text-secondary)',
                fontSize: 14,
                fontWeight: 600,
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                display: 'flex',
                alignItems: 'center',
                gap: 8,
              }}
            >
              <span style={{
                width: 10,
                height: 10,
                borderRadius: '50%',
                background: user.color,
                opacity: activeUser === user.name ? 1 : 0.4,
              }} />
              {user.name}
            </button>
          ))}
        </div>
        {activeUser && (
          <div style={{
            marginTop: 12,
            fontSize: 12,
            color: 'var(--text-muted)',
            fontFamily: 'monospace',
          }}>
            Active: {activeUser} &middot; Drift: {scoreLabel(scores.drift)} &middot; Trust: {scoreLabel(scores.trust)}
          </div>
        )}
      </div>

      {/* Current scores */}
      <div className="grid-4" style={{ marginBottom: 24 }}>
        {[
          { label: 'Drift Score', score: scores.drift, colorFn: scoreColor },
          { label: 'Anomaly Score', score: scores.anomaly, colorFn: scoreColor },
          { label: 'Trust Score', score: scores.trust, colorFn: trustColor },
          { label: 'Bot Score', score: scores.bot, colorFn: scoreColor },
        ].map(g => (
          <div key={g.label} className="card" style={{ display: 'flex', justifyContent: 'center', padding: '20px 12px' }}>
            <ScoreGauge label={g.label} score={g.score} colorFn={g.colorFn} size={120} />
          </div>
        ))}
      </div>

      {/* Chart + Events */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 360px', gap: 20 }}>
        {/* Drift comparison chart */}
        <div className="card">
          <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 16 }}>
            Drift Comparison by User
          </div>
          {comparisonData.length > 1 ? (
            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={comparisonData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis
                  dataKey="time"
                  tick={{ fontSize: 10, fill: 'var(--text-muted)' }}
                  interval="preserveStartEnd"
                />
                <YAxis
                  domain={[0, 100]}
                  tick={{ fontSize: 10, fill: 'var(--text-muted)' }}
                  tickFormatter={v => `${v}%`}
                  width={44}
                />
                <Tooltip
                  contentStyle={{
                    background: 'var(--surface)',
                    border: '1px solid var(--border)',
                    borderRadius: 8,
                    fontSize: 12,
                  }}
                />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                {USERS.map(user => (
                  <Line
                    key={user.name}
                    type="monotone"
                    dataKey={user.name}
                    stroke={user.color}
                    strokeWidth={2}
                    dot={{ r: 3, fill: user.color }}
                    connectNulls
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div style={{
              height: 280,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--text-muted)',
              fontSize: 13,
              flexDirection: 'column',
              gap: 8,
            }}>
              <div style={{ fontSize: 32, opacity: 0.2 }}>&#128101;</div>
              Switch between users to see drift comparison
            </div>
          )}
        </div>

        {/* Switch events log */}
        <div className="card">
          <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 14 }}>
            Switch Events ({switchEvents.length})
          </div>
          {switchEvents.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px 0', color: 'var(--text-muted)', fontSize: 12 }}>
              Switch between users to generate events
            </div>
          ) : (
            <div style={{ maxHeight: 360, overflow: 'auto' }}>
              {[...switchEvents].reverse().map(e => (
                <div key={e.id} style={{
                  padding: '10px 0',
                  borderBottom: '1px solid var(--border)',
                }}>
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 6,
                    marginBottom: 6,
                  }}>
                    <span style={{
                      fontSize: 12,
                      fontWeight: 600,
                      color: USER_COLORS[e.from] || 'var(--text-secondary)',
                    }}>{e.from}</span>
                    <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>&rarr;</span>
                    <span style={{
                      fontSize: 12,
                      fontWeight: 600,
                      color: USER_COLORS[e.to] || 'var(--text-secondary)',
                    }}>{e.to}</span>
                  </div>
                  <div style={{ display: 'flex', gap: 12 }}>
                    <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>
                      before: <span style={{ color: scoreColor(e.driftBefore), fontWeight: 600 }}>
                        {scoreLabel(e.driftBefore)}
                      </span>
                    </span>
                    <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>
                      after: <span style={{ color: scoreColor(e.driftAfter), fontWeight: 600 }}>
                        {scoreLabel(e.driftAfter)}
                      </span>
                    </span>
                    <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>
                      delta: <span style={{
                        color: e.driftAfter > e.driftBefore ? 'var(--danger)' : 'var(--success)',
                        fontWeight: 600,
                      }}>
                        {e.driftAfter > e.driftBefore ? '+' : ''}{((e.driftAfter - e.driftBefore) * 100).toFixed(1)}%
                      </span>
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Explanation */}
      <div className="card" style={{ marginTop: 24 }}>
        <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 10 }}>
          How Multi-User Detection Works
        </div>
        <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.7 }}>
          The kbio SDK builds a behavioral baseline for each user. When a different person starts using the same
          session, their typing rhythm, pointer movement patterns, and interaction habits differ from the baseline.
          This triggers a drift spike. The system can detect account sharing, credential theft, and session
          hijacking &mdash; all without passwords or MFA.
        </div>
      </div>
    </div>
  )
}
