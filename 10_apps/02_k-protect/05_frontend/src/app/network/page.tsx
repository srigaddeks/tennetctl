'use client'
import { useEffect, useState, useMemo } from 'react'
import { useAuth } from '@/components/auth-provider'
import { SignalBadge } from '@/components/signal-badge'
import { scoreColor } from '@/lib/colors'
import type { Decision, NetworkAggregate } from '@/lib/types'

function resolveIp(d: Decision): string {
  const meta = d.metadata as Record<string, unknown> ?? {}
  return d.ip_address ?? (meta.ip_address as string) ?? (meta.ip as string) ?? 'unknown'
}

function aggregateByIp(decisions: Decision[]): NetworkAggregate[] {
  const map = new Map<string, NetworkAggregate>()
  for (const d of decisions) {
    const meta = d.metadata as Record<string, unknown> ?? {}
    const ip = resolveIp(d)
    if (!ip || ip === 'unknown') continue
    const existing = map.get(ip) ?? {
      ip_address: ip,
      country: d.country ?? (meta.country as string) ?? '',
      is_vpn: d.is_vpn ?? (meta.is_vpn as boolean) ?? false,
      is_tor: d.is_tor ?? (meta.is_tor as boolean) ?? false,
      is_datacenter: (meta.is_datacenter as boolean) ?? false,
      session_count: 0,
      distinct_users: 0,
      threat_score: 0,
      last_seen: d.created_at,
    }
    existing.session_count++
    if (new Date(d.created_at) > new Date(existing.last_seen)) existing.last_seen = d.created_at
    map.set(ip, existing)
  }
  return Array.from(map.values()).map(net => {
    const ipDecisions = decisions.filter(d => resolveIp(d) === net.ip_address)
    const blocks = ipDecisions.filter(d => d.action === 'block').length
    return {
      ...net,
      distinct_users: new Set(ipDecisions.map(d => d.user_hash)).size,
      threat_score: Math.min(1, (blocks / Math.max(1, ipDecisions.length)) + (net.is_tor ? 0.5 : 0) + (net.is_vpn ? 0.2 : 0)),
    }
  }).sort((a, b) => b.threat_score - a.threat_score || b.session_count - a.session_count)
}

export default function NetworkPage() {
  const { session } = useAuth()
  const [decisions, setDecisions] = useState<Decision[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!session) return
    fetch(`/api/decisions?org_id=${session.org_id}&limit=500`)
      .then(r => r.json())
      .then(j => { if (j.ok) setDecisions(j.data?.items ?? []) })
      .finally(() => setLoading(false))
  }, [])

  const ips = useMemo(() => aggregateByIp(decisions), [decisions])

  if (loading) return <Loading />

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ margin: '0 0 4px', fontSize: 24, fontWeight: 700, letterSpacing: '-0.025em' }}>Network / IP</h1>
        <p style={{ margin: 0, fontSize: 13, color: 'var(--foreground-muted)' }}>{ips.length} distinct IP addresses</p>
      </div>

      <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 6 }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--border)' }}>
              {['IP Address', 'Country', 'Flags', 'Sessions', 'Users', 'Threat Score', 'Last Seen'].map(h => (
                <th key={h} style={{ textAlign: 'left', padding: '10px 16px', fontSize: 9, fontWeight: 600, color: 'var(--foreground-subtle)', textTransform: 'uppercase' as const, letterSpacing: '0.04em' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {ips.map(net => (
              <tr key={net.ip_address} style={{ borderBottom: '1px solid var(--border)' }}>
                <td style={{ padding: '10px 16px', fontSize: 12, fontFamily: 'var(--font-mono)', color: 'var(--foreground)', fontWeight: 500 }}>{net.ip_address}</td>
                <td style={{ padding: '10px 16px', fontSize: 12, color: 'var(--foreground-muted)' }}>{net.country || '—'}</td>
                <td style={{ padding: '10px 16px' }}>
                  <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                    {net.is_vpn && <SignalBadge label="VPN" variant="vpn" />}
                    {net.is_tor && <SignalBadge label="TOR" variant="tor" />}
                    {net.is_datacenter && <SignalBadge label="DC" variant="dc" />}
                    {!net.is_vpn && !net.is_tor && !net.is_datacenter && <span style={{ color: 'var(--foreground-subtle)', fontSize: 11 }}>—</span>}
                  </div>
                </td>
                <td style={{ padding: '10px 16px', fontSize: 12, fontFamily: 'var(--font-mono)', color: 'var(--foreground-muted)' }}>{net.session_count}</td>
                <td style={{ padding: '10px 16px', fontSize: 12, fontFamily: 'var(--font-mono)', color: 'var(--foreground-muted)' }}>{net.distinct_users}</td>
                <td style={{ padding: '10px 16px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <div style={{ width: 60, height: 4, background: 'var(--surface-3)', borderRadius: 2, overflow: 'hidden' }}>
                      <div style={{ height: '100%', background: scoreColor(net.threat_score), borderRadius: 2, width: `${net.threat_score * 100}%` }} />
                    </div>
                    <span style={{ fontSize: 11, fontFamily: 'var(--font-mono)', color: scoreColor(net.threat_score) }}>{(net.threat_score * 100).toFixed(0)}%</span>
                  </div>
                </td>
                <td style={{ padding: '10px 16px', fontSize: 11, color: 'var(--foreground-subtle)' }}>{new Date(net.last_seen).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {ips.length === 0 && (
          <div style={{ padding: 40, textAlign: 'center', color: 'var(--foreground-subtle)', fontSize: 13 }}>No network data yet</div>
        )}
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
