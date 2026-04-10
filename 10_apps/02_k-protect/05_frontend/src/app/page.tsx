'use client'
import { useEffect, useState, useCallback } from 'react'
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, Cell } from 'recharts'
import { StatCard } from '@/components/stat-card'
import { ActionBadge } from '@/components/action-badge'
import { actionColor, scoreColor } from '@/lib/colors'
import type { Decision } from '@/lib/types'
import { useAuth } from '@/components/auth-provider'

function getHour(iso: string) {
  return new Date(iso).getHours()
}

export default function DashboardPage() {
  const { session } = useAuth()
  const [decisions, setDecisions] = useState<Decision[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    if (!session) return
    try {
      const res = await fetch(`/api/decisions?org_id=${session.org_id}&limit=200`)
      const json = await res.json()
      if (json.ok) setDecisions(json.data?.items ?? [])
      else setError(json.error?.message ?? 'Failed to load')
    } catch {
      setError('Backend unavailable')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { if (session) load() }, [load, session])

  // Aggregate stats
  const total = decisions.length
  const byAction = decisions.reduce<Record<string, number>>((acc, d) => {
    const a = d.action ?? 'allow'
    acc[a] = (acc[a] ?? 0) + 1
    return acc
  }, {})

  // Hourly distribution
  const hourlyMap: Record<number, number> = {}
  for (let h = 0; h < 24; h++) hourlyMap[h] = 0
  decisions.forEach(d => { hourlyMap[getHour(d.created_at)] = (hourlyMap[getHour(d.created_at)] ?? 0) + 1 })
  const hourlyData = Object.entries(hourlyMap).map(([h, count]) => ({ hour: `${h}:00`, count }))

  // Top signals
  const sigCounts: Record<string, number> = {}
  decisions.forEach(d => {
    (d.signals_elevated ?? []).forEach(s => { sigCounts[s] = (sigCounts[s] ?? 0) + 1 })
  })
  const topSignals = Object.entries(sigCounts).sort((a, b) => b[1] - a[1]).slice(0, 8)

  // Top threats
  const threatCounts: Record<string, number> = {}
  decisions.forEach(d => {
    (d.threats_detected ?? []).forEach(t => { threatCounts[t] = (threatCounts[t] ?? 0) + 1 })
  })
  const topThreats = Object.entries(threatCounts).sort((a, b) => b[1] - a[1]).slice(0, 6)

  // Action distribution for bar chart
  const actionData = Object.entries(byAction).map(([action, count]) => ({ action, count }))

  if (loading) return <LoadingState />
  if (error) return <ErrorState message={error} onRetry={load} />

  return (
    <div>
      <div style={{ marginBottom: 28 }}>
        <h1 style={{ margin: '0 0 4px', fontSize: 24, fontWeight: 700, letterSpacing: '-0.025em' }}>Dashboard</h1>
        <p style={{ margin: 0, fontSize: 13, color: 'var(--foreground-muted)' }}>
          Behavioral threat intelligence — {total} decisions loaded
        </p>
      </div>

      {/* Stat cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 28 }}>
        <StatCard label="Total Decisions" value={total} sub="all time" />
        <StatCard label="Blocked" value={byAction.block ?? 0} color="var(--danger)" sub="hard blocks" />
        <StatCard label="Challenged" value={byAction.challenge ?? 0} color="var(--warning)" sub="step-up auth" />
        <StatCard label="Allowed" value={byAction.allow ?? 0} color="var(--success)" sub="clean sessions" />
      </div>

      {/* Charts row */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 16, marginBottom: 28 }}>
        {/* Hourly area chart */}
        <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 6, padding: 20 }}>
          <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--foreground-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 16 }}>Decisions per Hour</div>
          <ResponsiveContainer width="100%" height={160}>
            <AreaChart data={hourlyData}>
              <defs>
                <linearGradient id="grad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="oklch(0.58 0.14 240)" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="oklch(0.58 0.14 240)" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="hour" tick={{ fontSize: 10, fill: 'var(--foreground-subtle)' }} interval={3} />
              <YAxis tick={{ fontSize: 10, fill: 'var(--foreground-subtle)' }} width={30} />
              <Tooltip contentStyle={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 6, fontSize: 11 }} />
              <Area type="monotone" dataKey="count" stroke="var(--info)" fill="url(#grad)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Action bar chart */}
        <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 6, padding: 20 }}>
          <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--foreground-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 16 }}>By Action</div>
          <ResponsiveContainer width="100%" height={160}>
            <BarChart data={actionData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis type="number" tick={{ fontSize: 10, fill: 'var(--foreground-subtle)' }} />
              <YAxis dataKey="action" type="category" tick={{ fontSize: 10, fill: 'var(--foreground-subtle)' }} width={60} />
              <Tooltip contentStyle={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 6, fontSize: 11 }} />
              <Bar dataKey="count" radius={[0, 3, 3, 0]}>
                {actionData.map(entry => (
                  <Cell key={entry.action} fill={actionColor(entry.action).text} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Intelligence row */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 28 }}>
        {/* Top signals */}
        <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 6, padding: 20 }}>
          <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--foreground-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 12 }}>Top Elevated Signals</div>
          {topSignals.length === 0 ? (
            <div style={{ fontSize: 12, color: 'var(--foreground-subtle)', padding: '20px 0', textAlign: 'center' }}>No signal data yet</div>
          ) : (
            <div>
              {topSignals.map(([code, count]) => (
                <div key={code} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '6px 0', borderBottom: '1px solid var(--border)' }}>
                  <div style={{ flex: 1, fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--foreground)' }}>{code}</div>
                  <div style={{ width: 80, height: 4, background: 'var(--surface-3)', borderRadius: 2, overflow: 'hidden' }}>
                    <div style={{ height: '100%', background: 'var(--warning)', borderRadius: 2, width: `${Math.min(100, (count / (topSignals[0]?.[1] ?? 1)) * 100)}%` }} />
                  </div>
                  <div style={{ fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--foreground-muted)', width: 24, textAlign: 'right' }}>{count}</div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Top threats */}
        <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 6, padding: 20 }}>
          <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--foreground-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 12 }}>Top Detected Threats</div>
          {topThreats.length === 0 ? (
            <div style={{ fontSize: 12, color: 'var(--foreground-subtle)', padding: '20px 0', textAlign: 'center' }}>No threat detections yet</div>
          ) : (
            <div>
              {topThreats.map(([code, count]) => (
                <div key={code} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '6px 0', borderBottom: '1px solid var(--border)' }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--foreground)' }}>{code}</div>
                  </div>
                  <span style={{ padding: '2px 8px', borderRadius: 3, background: 'var(--danger-bg)', color: 'var(--danger)', fontSize: 10, fontWeight: 700, fontFamily: 'var(--font-mono)' }}>{count}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Recent decisions mini-table */}
      <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 6, padding: 20 }}>
        <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--foreground-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 12 }}>Recent Decisions</div>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--border)' }}>
              {['Time', 'User', 'Session', 'Action', 'Drift', 'Latency'].map(h => (
                <th key={h} style={{ textAlign: 'left', padding: '6px 0', fontSize: 9, fontWeight: 600, color: 'var(--foreground-subtle)', textTransform: 'uppercase', letterSpacing: '0.04em', paddingRight: 16 }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {decisions.slice(0, 10).map(d => (
              <tr key={d.id} style={{ borderBottom: '1px solid var(--border)' }}>
                <td style={{ padding: '7px 0', paddingRight: 16, fontSize: 11, color: 'var(--foreground-subtle)' }}>{new Date(d.created_at).toLocaleTimeString()}</td>
                <td style={{ padding: '7px 0', paddingRight: 16, fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--foreground)' }}>{d.user_hash?.slice(0, 8) ?? '—'}</td>
                <td style={{ padding: '7px 0', paddingRight: 16, fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--foreground-subtle)' }}>{d.session_id?.slice(0, 8) ?? '—'}</td>
                <td style={{ padding: '7px 0', paddingRight: 16 }}><ActionBadge action={d.action ?? 'allow'} /></td>
                <td style={{ padding: '7px 0', paddingRight: 16, fontSize: 11, fontFamily: 'var(--font-mono)', color: d.drift_score != null ? scoreColor(d.drift_score) : 'var(--foreground-subtle)' }}>
                  {d.drift_score != null ? `${(d.drift_score * 100).toFixed(1)}%` : '—'}
                </td>
                <td style={{ padding: '7px 0', fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--foreground-subtle)' }}>
                  {d.total_latency_ms != null ? `${d.total_latency_ms.toFixed(0)}ms` : '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function LoadingState() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: 400, gap: 16 }}>
      <div style={{ width: 32, height: 32, borderRadius: '50%', border: '2px solid var(--border)', borderTopColor: 'var(--foreground)', animation: 'spin 1s linear infinite' }} />
      <div style={{ fontSize: 14, color: 'var(--foreground-muted)' }}>Loading decisions...</div>
    </div>
  )
}

function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: 400, gap: 12 }}>
      <div style={{ fontSize: 16, color: 'var(--danger)' }}>⚠ {message}</div>
      <button onClick={onRetry} style={{ padding: '6px 16px', borderRadius: 4, border: '1px solid var(--border)', background: 'var(--surface)', cursor: 'pointer', fontSize: 13 }}>Retry</button>
    </div>
  )
}
