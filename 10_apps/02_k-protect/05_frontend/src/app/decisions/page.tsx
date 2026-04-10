'use client'
import { useEffect, useState, useCallback } from 'react'
import { useAuth } from '@/components/auth-provider'
import { ActionBadge } from '@/components/action-badge'
import { scoreColor } from '@/lib/colors'
import type { Decision } from '@/lib/types'

const POLL_INTERVAL = 5000

export default function DecisionsPage() {
  const { session } = useAuth()
  const [decisions, setDecisions] = useState<Decision[]>([])
  const [loading, setLoading] = useState(true)
  const [expanded, setExpanded] = useState<string | null>(null)
  const [filterAction, setFilterAction] = useState<string>('all')
  const [newIds, setNewIds] = useState<Set<string>>(new Set())

  const load = useCallback(async (silent = false) => {
    if (!session) return
    if (!silent) setLoading(true)
    try {
      const res = await fetch(`/api/decisions?org_id=${session.org_id}&limit=50`)
      const json = await res.json()
      if (json.ok) {
        const incoming: Decision[] = json.data?.items ?? []
        setDecisions(prev => {
          const prevIds = new Set(prev.map(d => d.id))
          const fresh = incoming.filter(d => !prevIds.has(d.id))
          if (fresh.length > 0) setNewIds(new Set(fresh.map(d => d.id)))
          return incoming
        })
      }
    } finally {
      if (!silent) setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
    const iv = setInterval(() => load(true), POLL_INTERVAL)
    return () => clearInterval(iv)
  }, [load])

  // Clear new highlights after 2s
  useEffect(() => {
    if (newIds.size > 0) {
      const t = setTimeout(() => setNewIds(new Set()), 2000)
      return () => clearTimeout(t)
    }
  }, [newIds])

  const filtered = filterAction === 'all' ? decisions : decisions.filter(d => d.action === filterAction)

  if (loading) return <Loading />

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 24 }}>
        <div>
          <h1 style={{ margin: '0 0 4px', fontSize: 24, fontWeight: 700, letterSpacing: '-0.025em' }}>Decisions</h1>
          <p style={{ margin: 0, fontSize: 13, color: 'var(--foreground-muted)' }}>Live feed — polls every 5s</p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          {['all', 'allow', 'monitor', 'challenge', 'block'].map(a => (
            <button key={a} onClick={() => setFilterAction(a)} style={{
              padding: '5px 12px', borderRadius: 4, border: '1px solid var(--border)',
              background: filterAction === a ? 'var(--foreground)' : 'var(--surface)',
              color: filterAction === a ? 'var(--background)' : 'var(--foreground-muted)',
              cursor: 'pointer', fontSize: 11, fontWeight: 600, textTransform: 'uppercase' as const, letterSpacing: '0.04em',
            }}>{a}</button>
          ))}
        </div>
      </div>

      <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 6 }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--border)' }}>
              {['Time', 'Session', 'User', 'Action', 'Drift', 'Bot', 'Threats', 'Signals', 'Latency'].map(h => (
                <th key={h} style={{ textAlign: 'left', padding: '10px 16px', fontSize: 9, fontWeight: 600, color: 'var(--foreground-subtle)', textTransform: 'uppercase' as const, letterSpacing: '0.04em' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.map(d => (
              <>
                <tr
                  key={d.id}
                  style={{
                    borderBottom: '1px solid var(--border)', cursor: 'pointer',
                    borderLeft: newIds.has(d.id) ? '3px solid var(--success)' : '3px solid transparent',
                    transition: 'border-color 0.5s',
                    background: expanded === d.id ? 'var(--surface-2)' : undefined,
                  }}
                  onClick={() => setExpanded(expanded === d.id ? null : d.id)}
                >
                  <td style={{ padding: '9px 16px', fontSize: 11, color: 'var(--foreground-subtle)' }}>{new Date(d.created_at).toLocaleTimeString()}</td>
                  <td style={{ padding: '9px 16px', fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--foreground-muted)' }}>{d.session_id?.slice(0, 8) ?? '—'}</td>
                  <td style={{ padding: '9px 16px', fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--foreground)' }}>{d.user_hash?.slice(0, 10) ?? '—'}</td>
                  <td style={{ padding: '9px 16px' }}><ActionBadge action={d.action ?? 'allow'} /></td>
                  <td style={{ padding: '9px 16px', fontSize: 11, fontFamily: 'var(--font-mono)', color: d.drift_score != null ? scoreColor(d.drift_score) : 'var(--foreground-subtle)' }}>
                    {d.drift_score != null && d.drift_score >= 0 ? `${(d.drift_score * 100).toFixed(1)}%` : '—'}
                  </td>
                  <td style={{ padding: '9px 16px', fontSize: 11, fontFamily: 'var(--font-mono)', color: d.bot_score != null ? scoreColor(d.bot_score) : 'var(--foreground-subtle)' }}>
                    {d.bot_score != null ? `${(d.bot_score * 100).toFixed(1)}%` : '—'}
                  </td>
                  <td style={{ padding: '9px 16px' }}>
                    {(d.threats_detected ?? []).length > 0 ? (
                      <span style={{ padding: '2px 7px', borderRadius: 3, background: 'var(--danger-bg)', color: 'var(--danger)', fontSize: 10, fontFamily: 'var(--font-mono)', fontWeight: 700 }}>
                        {(d.threats_detected ?? []).length}
                      </span>
                    ) : <span style={{ color: 'var(--foreground-subtle)', fontSize: 11 }}>0</span>}
                  </td>
                  <td style={{ padding: '9px 16px' }}>
                    {(d.signals_elevated ?? []).length > 0 ? (
                      <span style={{ padding: '2px 7px', borderRadius: 3, background: 'var(--warning-bg)', color: 'var(--warning)', fontSize: 10, fontFamily: 'var(--font-mono)', fontWeight: 700 }}>
                        {(d.signals_elevated ?? []).length}
                      </span>
                    ) : <span style={{ color: 'var(--foreground-subtle)', fontSize: 11 }}>0</span>}
                  </td>
                  <td style={{ padding: '9px 16px', fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--foreground-subtle)' }}>
                    {d.total_latency_ms != null ? `${d.total_latency_ms.toFixed(0)}ms` : '—'}
                  </td>
                </tr>
                {expanded === d.id && (
                  <tr key={`${d.id}-detail`} style={{ background: 'var(--surface-2)', borderBottom: '1px solid var(--border)' }}>
                    <td colSpan={9} style={{ padding: '12px 16px' }}>
                      <DecisionDetail decision={d} />
                    </td>
                  </tr>
                )}
              </>
            ))}
          </tbody>
        </table>
        {filtered.length === 0 && (
          <div style={{ padding: 40, textAlign: 'center', color: 'var(--foreground-subtle)', fontSize: 13 }}>No decisions yet</div>
        )}
      </div>
    </div>
  )
}

function DecisionDetail({ decision: d }: { decision: Decision }) {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16 }}>
      <div>
        <div style={{ fontSize: 10, fontWeight: 700, textTransform: 'uppercase' as const, color: 'var(--foreground-subtle)', letterSpacing: '0.05em', marginBottom: 8 }}>Identity</div>
        <div style={{ fontSize: 11, color: 'var(--foreground-muted)', display: 'flex', flexDirection: 'column', gap: 4 }}>
          <div><span style={{ color: 'var(--foreground-subtle)' }}>Decision: </span><span style={{ fontFamily: 'var(--font-mono)', fontSize: 10 }}>{d.id}</span></div>
          <div><span style={{ color: 'var(--foreground-subtle)' }}>User: </span><span style={{ fontFamily: 'var(--font-mono)' }}>{d.user_hash ?? '—'}</span></div>
          <div><span style={{ color: 'var(--foreground-subtle)' }}>Device: </span><span style={{ fontFamily: 'var(--font-mono)' }}>{d.device_uuid ?? '—'}</span></div>
          <div><span style={{ color: 'var(--foreground-subtle)' }}>Latency: </span><span style={{ fontFamily: 'var(--font-mono)' }}>kbio {d.kbio_latency_ms?.toFixed(0) ?? '?'}ms / policy {d.policy_latency_ms?.toFixed(0) ?? '?'}ms</span></div>
        </div>
      </div>
      <div>
        <div style={{ fontSize: 10, fontWeight: 700, textTransform: 'uppercase' as const, color: 'var(--foreground-subtle)', letterSpacing: '0.05em', marginBottom: 8 }}>Threats</div>
        {(d.threats_detected ?? []).length === 0 ? (
          <div style={{ fontSize: 11, color: 'var(--foreground-subtle)' }}>None detected</div>
        ) : (d.threats_detected ?? []).map(t => (
          <div key={t} style={{ display: 'inline-block', margin: '2px 4px 2px 0', padding: '2px 8px', borderRadius: 3, background: 'var(--danger-bg)', color: 'var(--danger)', fontSize: 10, fontFamily: 'var(--font-mono)' }}>{t}</div>
        ))}
      </div>
      <div>
        <div style={{ fontSize: 10, fontWeight: 700, textTransform: 'uppercase' as const, color: 'var(--foreground-subtle)', letterSpacing: '0.05em', marginBottom: 8 }}>Elevated Signals</div>
        {(d.signals_elevated ?? []).length === 0 ? (
          <div style={{ fontSize: 11, color: 'var(--foreground-subtle)' }}>None</div>
        ) : (d.signals_elevated ?? []).slice(0, 8).map(s => (
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
