'use client'
import { useEffect, useState, useMemo } from 'react'
import { useAuth } from '@/components/auth-provider'
import { ActionBadge } from '@/components/action-badge'
import { ScoreSparkline } from '@/components/score-sparkline'
import { scoreColor } from '@/lib/colors'
import type { Decision, UserAggregate } from '@/lib/types'

function aggregateByUser(decisions: Decision[]): UserAggregate[] {
  const map = new Map<string, UserAggregate>()
  for (const d of decisions) {
    const key = d.user_hash ?? 'unknown'
    const existing = map.get(key) ?? {
      user_hash: key,
      total_decisions: 0,
      total_sessions: 0,
      block_count: 0,
      challenge_count: 0,
      drift_history: [],
      avg_drift: 0,
      last_seen: d.created_at,
      trust_level: 'unknown',
      threat_count: 0,
    }
    existing.total_decisions++
    if (d.action === 'block') existing.block_count++
    if (d.action === 'challenge') existing.challenge_count++
    if (d.drift_score != null && d.drift_score >= 0) existing.drift_history.push(d.drift_score)
    existing.threat_count += (d.threats_detected ?? []).length
    if (new Date(d.created_at) > new Date(existing.last_seen)) existing.last_seen = d.created_at
    map.set(key, existing)
  }
  return Array.from(map.values()).map(u => ({
    ...u,
    total_sessions: new Set(
      decisions.filter(d => d.user_hash === u.user_hash).map(d => d.session_id)
    ).size,
    avg_drift: u.drift_history.length ? u.drift_history.reduce((a, b) => a + b, 0) / u.drift_history.length : 0,
    trust_level: u.block_count > 2 ? 'critical' : u.block_count > 0 ? 'low' : u.challenge_count > 1 ? 'medium' : 'high',
  })).sort((a, b) => b.total_decisions - a.total_decisions)
}

function trustBadge(level: string) {
  const colors: Record<string, { bg: string; text: string }> = {
    high:     { bg: 'var(--success-bg)', text: 'var(--success)' },
    medium:   { bg: 'var(--warning-bg)', text: 'var(--warning)' },
    low:      { bg: 'var(--danger-bg)',  text: 'var(--danger)' },
    critical: { bg: 'var(--danger-bg)',  text: 'var(--danger)' },
    unknown:  { bg: 'var(--surface-3)',  text: 'var(--foreground-subtle)' },
  }
  const c = colors[level] ?? colors.unknown
  return (
    <span style={{ padding: '2px 8px', borderRadius: 3, fontSize: 9, fontWeight: 700, textTransform: 'uppercase' as const, letterSpacing: '0.04em', background: c.bg, color: c.text }}>
      {level}
    </span>
  )
}

export default function UsersPage() {
  const { session } = useAuth()
  const [decisions, setDecisions] = useState<Decision[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [expanded, setExpanded] = useState<string | null>(null)

  useEffect(() => {
    if (!session) return
    fetch(`/api/decisions?org_id=${session.org_id}&limit=500`)
      .then(r => r.json())
      .then(j => { if (j.ok) setDecisions(j.data?.items ?? []) })
      .finally(() => setLoading(false))
  }, [])

  const users = useMemo(() => aggregateByUser(decisions), [decisions])
  const filtered = useMemo(() => search ? users.filter(u => u.user_hash.includes(search)) : users, [users, search])

  if (loading) return <Loading />

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ margin: '0 0 4px', fontSize: 24, fontWeight: 700, letterSpacing: '-0.025em' }}>Users</h1>
        <p style={{ margin: 0, fontSize: 13, color: 'var(--foreground-muted)' }}>{users.length} distinct users across {decisions.length} decisions</p>
      </div>

      <div style={{ marginBottom: 16 }}>
        <input
          placeholder="Search by user hash..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          style={{ width: 320, padding: '7px 12px', borderRadius: 5, border: '1px solid var(--border)', background: 'var(--surface)', color: 'var(--foreground)', fontSize: 13 }}
        />
      </div>

      <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 6 }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--border)' }}>
              {['User Hash', 'Trust', 'Drift Trend', 'Sessions', 'Decisions', 'Blocks', 'Threats', 'Last Seen'].map(h => (
                <th key={h} style={{ textAlign: 'left', padding: '10px 16px', fontSize: 9, fontWeight: 600, color: 'var(--foreground-subtle)', textTransform: 'uppercase' as const, letterSpacing: '0.04em' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.map(u => (
              <>
                <tr
                  key={u.user_hash}
                  style={{ borderBottom: '1px solid var(--border)', cursor: 'pointer' }}
                  onClick={() => setExpanded(expanded === u.user_hash ? null : u.user_hash)}
                >
                  <td style={{ padding: '10px 16px', fontSize: 12, fontFamily: 'var(--font-mono)', color: 'var(--foreground)', fontWeight: 500 }}>
                    {u.user_hash.slice(0, 16)}{u.user_hash.length > 16 ? '…' : ''}
                  </td>
                  <td style={{ padding: '10px 16px' }}>{trustBadge(u.trust_level)}</td>
                  <td style={{ padding: '10px 16px' }}>
                    <ScoreSparkline data={u.drift_history.slice(-20)} />
                  </td>
                  <td style={{ padding: '10px 16px', fontSize: 12, fontFamily: 'var(--font-mono)', color: 'var(--foreground-muted)' }}>{u.total_sessions}</td>
                  <td style={{ padding: '10px 16px', fontSize: 12, fontFamily: 'var(--font-mono)', color: 'var(--foreground)' }}>{u.total_decisions}</td>
                  <td style={{ padding: '10px 16px' }}>
                    {u.block_count > 0 ? (
                      <span style={{ padding: '2px 8px', borderRadius: 3, background: 'var(--danger-bg)', color: 'var(--danger)', fontSize: 11, fontFamily: 'var(--font-mono)', fontWeight: 700 }}>{u.block_count}</span>
                    ) : <span style={{ color: 'var(--foreground-subtle)', fontSize: 12 }}>0</span>}
                  </td>
                  <td style={{ padding: '10px 16px' }}>
                    {u.threat_count > 0 ? (
                      <span style={{ padding: '2px 8px', borderRadius: 3, background: 'var(--warning-bg)', color: 'var(--warning)', fontSize: 11, fontFamily: 'var(--font-mono)', fontWeight: 700 }}>{u.threat_count}</span>
                    ) : <span style={{ color: 'var(--foreground-subtle)', fontSize: 12 }}>0</span>}
                  </td>
                  <td style={{ padding: '10px 16px', fontSize: 11, color: 'var(--foreground-subtle)' }}>{new Date(u.last_seen).toLocaleString()}</td>
                </tr>
                {expanded === u.user_hash && (
                  <tr key={`${u.user_hash}-detail`} style={{ background: 'var(--surface-2)' }}>
                    <td colSpan={8} style={{ padding: '12px 16px' }}>
                      <UserDetail decisions={decisions.filter(d => d.user_hash === u.user_hash)} />
                    </td>
                  </tr>
                )}
              </>
            ))}
          </tbody>
        </table>
        {filtered.length === 0 && (
          <div style={{ padding: 40, textAlign: 'center', color: 'var(--foreground-subtle)', fontSize: 13 }}>
            {search ? `No users matching "${search}"` : 'No user data yet'}
          </div>
        )}
      </div>
    </div>
  )
}

function UserDetail({ decisions }: { decisions: Decision[] }) {
  const sorted = [...decisions].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
  const threats = [...new Set(decisions.flatMap(d => d.threats_detected ?? []))]
  const signals = [...new Set(decisions.flatMap(d => d.signals_elevated ?? []))]

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16 }}>
      <div>
        <div style={{ fontSize: 10, fontWeight: 700, textTransform: 'uppercase' as const, letterSpacing: '0.05em', color: 'var(--foreground-subtle)', marginBottom: 8 }}>Recent Decisions</div>
        {sorted.slice(0, 5).map(d => (
          <div key={d.id} style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 6 }}>
            <span style={{ fontSize: 10, color: 'var(--foreground-subtle)' }}>{new Date(d.created_at).toLocaleTimeString()}</span>
            <ActionBadge action={d.action ?? 'allow'} />
            {d.drift_score != null && <span style={{ fontSize: 10, fontFamily: 'var(--font-mono)', color: scoreColor(d.drift_score) }}>{(d.drift_score * 100).toFixed(1)}%</span>}
          </div>
        ))}
      </div>
      <div>
        <div style={{ fontSize: 10, fontWeight: 700, textTransform: 'uppercase' as const, letterSpacing: '0.05em', color: 'var(--foreground-subtle)', marginBottom: 8 }}>Detected Threats</div>
        {threats.length === 0 ? <div style={{ fontSize: 11, color: 'var(--foreground-subtle)' }}>None</div> : threats.map(t => (
          <div key={t} style={{ display: 'inline-block', margin: '2px 4px 2px 0', padding: '2px 8px', borderRadius: 3, background: 'var(--danger-bg)', color: 'var(--danger)', fontSize: 10, fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{t}</div>
        ))}
      </div>
      <div>
        <div style={{ fontSize: 10, fontWeight: 700, textTransform: 'uppercase' as const, letterSpacing: '0.05em', color: 'var(--foreground-subtle)', marginBottom: 8 }}>Elevated Signals</div>
        {signals.length === 0 ? <div style={{ fontSize: 11, color: 'var(--foreground-subtle)' }}>None</div> : signals.slice(0, 6).map(s => (
          <div key={s} style={{ display: 'inline-block', margin: '2px 4px 2px 0', padding: '2px 7px', borderRadius: 3, background: 'var(--warning-bg)', color: 'var(--warning)', fontSize: 10, fontFamily: 'var(--font-mono)' }}>{s}</div>
        ))}
      </div>
    </div>
  )
}

function Loading() {
  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: 400 }}>
      <div style={{ width: 32, height: 32, borderRadius: '50%', border: '2px solid var(--border)', borderTopColor: 'var(--foreground)', animation: 'spin 1s linear infinite' }} />
    </div>
  )
}
