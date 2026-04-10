'use client'

import { useState, useMemo, useEffect } from 'react'
import { ThreatGraph } from '@/components/threat-graph'
import type { Decision, GraphNode, GraphEdge } from '@/lib/types'
import { kpFetch } from '@/lib/api'

function buildGraph(decisions: Decision[]): { nodes: GraphNode[]; edges: GraphEdge[] } {
  const nodes = new Map<string, GraphNode>()
  const edges: GraphEdge[] = []
  const edgeSet = new Set<string>()

  const addNode = (id: string, type: GraphNode['type'], label: string, data: Record<string, unknown>) => {
    if (!nodes.has(id)) {
      nodes.set(id, {
        id, type, label, data,
        x: 400 + (Math.random() - 0.5) * 400,
        y: 300 + (Math.random() - 0.5) * 300,
        vx: 0, vy: 0,
      })
    }
  }

  const addEdge = (source: string, target: string, type: GraphEdge['type']) => {
    const key = `${source}→${target}`
    if (!edgeSet.has(key)) {
      edgeSet.add(key)
      edges.push({ source, target, type })
    }
  }

  for (const d of decisions) {
    const sid = `session:${d.session_id ?? d.id}`
    addNode(sid, 'session', (d.session_id ?? d.id).slice(0, 8), {
      action: d.action, drift: d.drift_score, bot: d.bot_score,
    })

    if (d.user_hash) {
      const uid = `user:${d.user_hash}`
      addNode(uid, 'user', d.user_hash.slice(0, 8), { trust: 'trusted' })
      addEdge(uid, sid, 'user-session')
    }

    if (d.device_uuid) {
      const did = `device:${d.device_uuid}`
      addNode(did, 'device', d.device_uuid.slice(0, 8), { platform: 'web' })
      addEdge(did, sid, 'device-session')
      if (d.user_hash) addEdge(`user:${d.user_hash}`, did, 'user-device')
    }

    if (d.ip_address) {
      const ipid = `ip:${d.ip_address}`
      addNode(ipid, 'ip', d.ip_address, {
        vpn: d.is_vpn, tor: d.is_tor, country: d.country,
      })
      addEdge(ipid, sid, 'ip-session')
    }

    if (d.threats_detected) {
      for (const t of d.threats_detected) {
        const tid = `threat:${t}`
        addNode(tid, 'threat', t.replace('ato-', '').replace('bot-', '').replace('idf-', ''), { code: t })
        addEdge(sid, tid, 'session-threat')
      }
    }
  }

  return { nodes: [...nodes.values()], edges }
}

const FILTER_TYPES = ['all', 'user', 'device', 'ip', 'threat', 'session'] as const
type FilterType = typeof FILTER_TYPES[number]

export default function ThreatsPage() {
  const [decisions, setDecisions] = useState<Decision[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selected, setSelected] = useState<GraphNode | null>(null)
  const [filterType, setFilterType] = useState<FilterType>('all')
  const [width, setWidth] = useState(900)

  useEffect(() => {
    const update = () => setWidth(Math.max(600, window.innerWidth - 280 - 48))
    update()
    window.addEventListener('resize', update)
    return () => window.removeEventListener('resize', update)
  }, [])

  useEffect(() => {
    kpFetch<{ items: Decision[] }>('/api/decisions?limit=200')
      .then(d => { setDecisions(d.items); setLoading(false) })
      .catch(e => { setError(e.message); setLoading(false) })
  }, [])

  const { nodes, edges } = useMemo(() => buildGraph(decisions), [decisions])

  const filteredNodes = useMemo(
    () => filterType === 'all' ? nodes : nodes.filter(n => n.type === filterType),
    [nodes, filterType],
  )
  const filteredEdges = useMemo(() => {
    if (filterType === 'all') return edges
    const ids = new Set(filteredNodes.map(n => n.id))
    return edges.filter(e => ids.has(e.source) && ids.has(e.target))
  }, [edges, filteredNodes, filterType])

  const stats = useMemo(() => ({
    users: nodes.filter(n => n.type === 'user').length,
    devices: nodes.filter(n => n.type === 'device').length,
    ips: nodes.filter(n => n.type === 'ip').length,
    threats: nodes.filter(n => n.type === 'threat').length,
    sessions: nodes.filter(n => n.type === 'session').length,
  }), [nodes])

  return (
    <div style={{ padding: '32px 40px' }}>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700, margin: '0 0 4px' }}>Threat Graph</h1>
        <p style={{ margin: 0, color: 'var(--foreground-muted)', fontSize: 14 }}>
          Visual relationship map of users, devices, IPs, sessions, and detected threats
        </p>
      </div>

      {/* Stats row */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 20, flexWrap: 'wrap' }}>
        {[
          { label: 'Users', value: stats.users, color: 'oklch(0.58 0.14 240)' },
          { label: 'Devices', value: stats.devices, color: 'oklch(0.62 0.14 155)' },
          { label: 'IPs', value: stats.ips, color: 'oklch(0.72 0.15 75)' },
          { label: 'Active Threats', value: stats.threats, color: 'oklch(0.58 0.20 25)' },
          { label: 'Sessions', value: stats.sessions, color: 'oklch(0.65 0.12 280)' },
        ].map(s => (
          <div key={s.label} style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, padding: '10px 16px', display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{ width: 8, height: 8, borderRadius: '50%', background: s.color }} />
            <span style={{ fontSize: 13, color: 'var(--foreground-muted)' }}>{s.label}</span>
            <strong style={{ fontSize: 18 }}>{s.value}</strong>
          </div>
        ))}
      </div>

      {/* Filter tabs */}
      <div style={{ display: 'flex', gap: 6, marginBottom: 16 }}>
        {FILTER_TYPES.map(t => (
          <button
            key={t}
            onClick={() => setFilterType(t)}
            style={{
              padding: '5px 14px', borderRadius: 6, border: '1px solid var(--border)',
              background: filterType === t ? 'var(--foreground)' : 'var(--surface)',
              color: filterType === t ? 'var(--background)' : 'var(--foreground-muted)',
              cursor: 'pointer', fontSize: 12, fontWeight: filterType === t ? 600 : 400,
            }}
          >{t}</button>
        ))}
        <div style={{ marginLeft: 'auto', fontSize: 12, color: 'var(--foreground-subtle)', display: 'flex', alignItems: 'center' }}>
          {filteredNodes.length} nodes · {filteredEdges.length} edges · drag to rearrange
        </div>
      </div>

      {loading && (
        <div style={{ height: 500, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--foreground-muted)' }}>
          Loading graph data…
        </div>
      )}
      {error && (
        <div style={{ background: 'var(--danger-bg)', color: 'var(--danger)', padding: '12px 16px', borderRadius: 8 }}>
          {error}
        </div>
      )}
      {!loading && !error && (
        <ThreatGraph
          nodes={filteredNodes}
          edges={filteredEdges}
          width={width}
          height={560}
          onNodeClick={setSelected}
        />
      )}

      {/* Selected node panel */}
      {selected && (
        <div style={{ marginTop: 16, background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 10, padding: '16px 20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <h3 style={{ margin: 0, fontSize: 15 }}>
              {selected.type.charAt(0).toUpperCase() + selected.type.slice(1)}: {selected.label}
            </h3>
            <button onClick={() => setSelected(null)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--foreground-muted)', fontSize: 18 }}>×</button>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))', gap: 8 }}>
            {Object.entries(selected.data).map(([k, v]) => (
              <div key={k} style={{ background: 'var(--surface-2)', borderRadius: 6, padding: '8px 10px' }}>
                <div style={{ fontSize: 10, color: 'var(--foreground-subtle)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 2 }}>{k}</div>
                <div style={{ fontSize: 13, fontWeight: 500 }}>{v === null ? 'null' : String(v)}</div>
              </div>
            ))}
          </div>
          {/* Related decisions */}
          {selected.type === 'user' && (
            <div style={{ marginTop: 12 }}>
              <div style={{ fontSize: 12, color: 'var(--foreground-subtle)', marginBottom: 6 }}>Recent decisions</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                {decisions.filter(d => `user:${d.user_hash}` === selected.id).slice(0, 5).map(d => (
                  <div key={d.id} style={{ display: 'flex', gap: 10, fontSize: 12, alignItems: 'center' }}>
                    <span style={{ padding: '1px 6px', borderRadius: 4, background: d.action === 'block' ? 'var(--danger-bg)' : d.action === 'challenge' ? 'var(--warning-bg)' : 'var(--success-bg)', color: d.action === 'block' ? 'var(--danger)' : d.action === 'challenge' ? 'var(--warning)' : 'var(--success)', fontSize: 10 }}>{d.action}</span>
                    <span style={{ color: 'var(--foreground-muted)' }}>drift {(d.drift_score ?? 0).toFixed(2)}</span>
                    <span style={{ color: 'var(--foreground-subtle)' }}>{new Date(d.created_at).toLocaleTimeString()}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
