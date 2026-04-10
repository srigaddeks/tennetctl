'use client'
import { useEffect, useState, useMemo } from 'react'
import { useAuth } from '@/components/auth-provider'
import { SignalBadge } from '@/components/signal-badge'
import type { Decision, DeviceAggregate } from '@/lib/types'

function aggregateByDevice(decisions: Decision[]): DeviceAggregate[] {
  const map = new Map<string, DeviceAggregate>()
  for (const d of decisions) {
    const key = d.device_uuid ?? 'unknown'
    const existing = map.get(key) ?? {
      device_uuid: key,
      platform: (d.metadata as Record<string, unknown>)?.platform as string ?? 'web',
      session_count: 0,
      distinct_users: 0,
      bot_detections: 0,
      first_seen: d.created_at,
      last_seen: d.created_at,
    }
    existing.session_count++
    if (d.bot_score != null && d.bot_score > 0.7) existing.bot_detections++
    if (new Date(d.created_at) > new Date(existing.last_seen)) existing.last_seen = d.created_at
    if (new Date(d.created_at) < new Date(existing.first_seen)) existing.first_seen = d.created_at
    map.set(key, existing)
  }
  return Array.from(map.values()).map(dev => {
    const deviceDecisions = decisions.filter(d => d.device_uuid === dev.device_uuid)
    return {
      ...dev,
      distinct_users: new Set(deviceDecisions.map(d => d.user_hash)).size,
    }
  }).sort((a, b) => b.session_count - a.session_count)
}

function platformBadge(platform: string) {
  const colors: Record<string, string> = {
    ios: 'var(--info)',
    android: 'var(--success)',
    web: 'var(--foreground-muted)',
    desktop: 'var(--foreground-subtle)',
  }
  const color = colors[platform.toLowerCase()] ?? colors.web
  return (
    <span style={{ padding: '2px 8px', borderRadius: 3, background: 'var(--surface-3)', color, fontSize: 10, fontWeight: 600, textTransform: 'uppercase' as const, letterSpacing: '0.04em' }}>
      {platform}
    </span>
  )
}

export default function DevicesPage() {
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

  const devices = useMemo(() => aggregateByDevice(decisions), [decisions])

  if (loading) return <Loading />

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ margin: '0 0 4px', fontSize: 24, fontWeight: 700, letterSpacing: '-0.025em' }}>Devices</h1>
        <p style={{ margin: 0, fontSize: 13, color: 'var(--foreground-muted)' }}>{devices.length} distinct devices</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16 }}>
        {devices.map(dev => (
          <div key={dev.device_uuid} style={{
            background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 6, padding: 20,
            borderLeft: dev.bot_detections > 0 ? '3px solid var(--danger)' : dev.distinct_users > 1 ? '3px solid var(--warning)' : '1px solid var(--border)',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
              <div>
                <div style={{ fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--foreground)', fontWeight: 500, marginBottom: 4 }}>
                  {dev.device_uuid.slice(0, 12)}…
                </div>
                {platformBadge(dev.platform)}
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 4 }}>
                {dev.bot_detections > 0 && <SignalBadge label={`${dev.bot_detections} BOT`} variant="tor" />}
                {dev.distinct_users > 1 && <SignalBadge label={`${dev.distinct_users} USERS`} variant="vpn" />}
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
              <div>
                <div style={{ fontSize: 9, fontWeight: 600, textTransform: 'uppercase' as const, color: 'var(--foreground-subtle)', letterSpacing: '0.04em', marginBottom: 2 }}>Sessions</div>
                <div style={{ fontSize: 18, fontWeight: 700, fontFamily: 'var(--font-mono)', color: 'var(--foreground)' }}>{dev.session_count}</div>
              </div>
              <div>
                <div style={{ fontSize: 9, fontWeight: 600, textTransform: 'uppercase' as const, color: 'var(--foreground-subtle)', letterSpacing: '0.04em', marginBottom: 2 }}>Users</div>
                <div style={{ fontSize: 18, fontWeight: 700, fontFamily: 'var(--font-mono)', color: dev.distinct_users > 1 ? 'var(--warning)' : 'var(--foreground)' }}>{dev.distinct_users}</div>
              </div>
            </div>

            <div style={{ marginTop: 12, fontSize: 10, color: 'var(--foreground-subtle)' }}>
              Last seen {new Date(dev.last_seen).toLocaleDateString()}
            </div>
          </div>
        ))}
      </div>

      {devices.length === 0 && (
        <div style={{ padding: 60, textAlign: 'center', color: 'var(--foreground-subtle)', fontSize: 13 }}>No device data yet</div>
      )}
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
