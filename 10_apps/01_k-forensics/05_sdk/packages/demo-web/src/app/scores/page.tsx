'use client'

import { useSdk } from '@/components/sdk-provider'
import { ScoreGauge } from '@/components/score-gauge'
import { Heatmap } from '@/components/heatmap'
import { scoreColor, trustColor, scoreLabel } from '@/lib/score-colors'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

export default function ScoresPage() {
  const { scores, session } = useSdk()

  const driftHistory = (session?.drift_history || []).map((h, i) => ({
    idx: i,
    time: new Date(h.time).toLocaleTimeString([], { minute: '2-digit', second: '2-digit' }),
    drift: +(h.drift * 100).toFixed(1),
  }))

  const modalities = session?.modalities || []
  const fusionWeights = session?.fusion_weights || {}
  const fp = session?.device_fingerprint

  return (
    <div>
      <div style={{ marginBottom: 28 }}>
        <h1 className="page-title">Scores Dashboard</h1>
        <p className="page-subtitle">Real-time composite and per-modality behavioral scores</p>
      </div>

      {/* 4 Gauge Cards */}
      <div className="grid-4" style={{ marginBottom: 28 }}>
        {[
          { label: 'Drift Score', score: scores.drift, colorFn: scoreColor, sub: 'Behavioral deviation' },
          { label: 'Anomaly Score', score: scores.anomaly, colorFn: scoreColor, sub: 'Statistical outlier' },
          { label: 'Trust Score', score: scores.trust, colorFn: trustColor, sub: 'Session confidence' },
          { label: 'Bot Score', score: scores.bot, colorFn: scoreColor, sub: 'Automation likelihood' },
        ].map(g => (
          <div key={g.label} className="card" style={{ display: 'flex', justifyContent: 'center', padding: '28px 16px' }}>
            <ScoreGauge label={g.label} score={g.score} colorFn={g.colorFn} size={150} subtitle={g.sub} />
          </div>
        ))}
      </div>

      {/* Timeline + Heatmap row */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 380px', gap: 20, marginBottom: 24 }}>
        {/* Drift Timeline */}
        <div className="card">
          <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 16 }}>
            Drift Score Timeline
          </div>
          {driftHistory.length > 2 ? (
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={driftHistory}>
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
                  formatter={(v: number) => [`${v}%`, 'Drift']}
                />
                <Line
                  type="monotone"
                  dataKey="drift"
                  stroke="#6366f1"
                  strokeWidth={2}
                  dot={false}
                  activeDot={{ r: 4, fill: '#6366f1' }}
                />
                {/* Threshold line at 60% */}
                <Line
                  type="monotone"
                  dataKey={() => 60}
                  stroke="#ef4444"
                  strokeWidth={1}
                  strokeDasharray="4 4"
                  dot={false}
                  name="Threshold"
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div style={{
              height: 220,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--text-muted)',
              fontSize: 13,
            }}>
              Collecting drift data...
            </div>
          )}
        </div>

        {/* Zone Transition Matrix */}
        <div className="card">
          {session ? (
            <Heatmap matrix={session.zone_matrix} title="Zone Transition Matrix" cellSize={28} />
          ) : (
            <div style={{ color: 'var(--text-muted)', fontSize: 13, textAlign: 'center', padding: '40px 0' }}>
              Waiting for session data...
            </div>
          )}
        </div>
      </div>

      {/* Modality Breakdown + Fusion Weights + Device + Session */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
        {/* Modality Breakdown */}
        <div className="card">
          <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 14 }}>
            Per-Modality Breakdown
          </div>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid var(--border)' }}>
                {['Modality', 'Status', 'Drift', 'Events', 'Weight'].map(h => (
                  <th key={h} style={{
                    textAlign: 'left',
                    padding: '8px 0',
                    fontSize: 10,
                    fontWeight: 600,
                    color: 'var(--text-muted)',
                    textTransform: 'uppercase' as const,
                    letterSpacing: 0.5,
                  }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {modalities.map(m => (
                <tr key={m.modality} style={{ borderBottom: '1px solid var(--border)' }}>
                  <td style={{ padding: '10px 0', fontSize: 13, fontWeight: 500, color: 'var(--text-primary)', textTransform: 'capitalize' as const }}>
                    {m.modality}
                  </td>
                  <td style={{ padding: '10px 0' }}>
                    <span style={{
                      width: 8,
                      height: 8,
                      borderRadius: '50%',
                      display: 'inline-block',
                      background: m.active ? 'var(--success)' : 'var(--text-muted)',
                      boxShadow: m.active ? '0 0 4px var(--success)' : 'none',
                    }} />
                  </td>
                  <td style={{ padding: '10px 0', fontSize: 12, fontFamily: 'monospace', color: scoreColor(m.drift), fontWeight: 600 }}>
                    {scoreLabel(m.drift)}
                  </td>
                  <td style={{ padding: '10px 0', fontSize: 12, fontFamily: 'monospace', color: 'var(--text-secondary)' }}>
                    {m.events}
                  </td>
                  <td style={{ padding: '10px 0', fontSize: 12, fontFamily: 'monospace', color: 'var(--text-secondary)' }}>
                    {(m.weight * 100).toFixed(0)}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Right column: fusion weights + device + session */}
        <div>
          {/* Fusion Weights */}
          <div className="card" style={{ marginBottom: 16 }}>
            <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 14 }}>
              Fusion Weights
            </div>
            <div style={{
              height: 24,
              borderRadius: 12,
              overflow: 'hidden',
              display: 'flex',
              background: 'var(--surface-alt)',
            }}>
              {Object.entries(fusionWeights).map(([key, weight], i) => {
                const colors = ['#6366f1', '#8b5cf6', '#a78bfa', '#c4b5fd', '#ddd6fe', '#ede9fe']
                return (
                  <div
                    key={key}
                    title={`${key}: ${(weight * 100).toFixed(0)}%`}
                    style={{
                      width: `${weight * 100}%`,
                      background: colors[i % colors.length],
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      transition: 'width 0.5s ease',
                    }}
                  >
                    {weight >= 0.1 && (
                      <span style={{ fontSize: 9, color: '#fff', fontWeight: 600, whiteSpace: 'nowrap' }}>
                        {key}
                      </span>
                    )}
                  </div>
                )
              })}
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 10 }}>
              {Object.entries(fusionWeights).map(([key, weight], i) => {
                const colors = ['#6366f1', '#8b5cf6', '#a78bfa', '#c4b5fd', '#ddd6fe', '#ede9fe']
                return (
                  <span key={key} style={{
                    fontSize: 10,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 4,
                    color: 'var(--text-muted)',
                  }}>
                    <span style={{ width: 8, height: 8, borderRadius: 2, background: colors[i % colors.length], display: 'inline-block' }} />
                    {key} {(weight * 100).toFixed(0)}%
                  </span>
                )
              })}
            </div>
          </div>

          {/* Device Fingerprint */}
          {fp && (
            <div className="card" style={{ marginBottom: 16 }}>
              <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 10 }}>
                Device Fingerprint
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6 }}>
                {[
                  ['Platform', fp.platform],
                  ['Browser', fp.browser],
                  ['Screen', fp.screen],
                  ['Timezone', fp.timezone],
                  ['Language', fp.language],
                  ['Cores', String(fp.cores)],
                  ['Memory', `${fp.memory}GB`],
                  ['GPU', fp.gpu],
                ].map(([k, v]) => (
                  <div key={k}>
                    <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>{k}: </span>
                    <span style={{ fontSize: 10, color: 'var(--text-secondary)', fontFamily: 'monospace' }}>{v}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Session Metadata */}
          {session && (
            <div className="card">
              <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 10 }}>
                Session Metadata
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                {[
                  ['Session ID', session.session_id.slice(0, 12) + '...'],
                  ['Pulses', String(session.pulse_count)],
                  ['Duration', `${Math.floor((Date.now() - session.started_at) / 1000)}s`],
                  ['Events', String(modalities.reduce((s, m) => s + m.events, 0))],
                  ['Trust Level', scores.trust >= 0.75 ? 'HIGH' : scores.trust >= 0.5 ? 'MEDIUM' : 'LOW'],
                  ['User', session.user_hash ? session.user_hash.slice(0, 16) + '...' : 'Anonymous'],
                ].map(([k, v]) => (
                  <div key={k} style={{
                    padding: '8px 10px',
                    background: 'var(--surface-alt)',
                    borderRadius: 6,
                  }}>
                    <div style={{ fontSize: 10, color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase' as const, letterSpacing: 0.3 }}>{k}</div>
                    <div style={{ fontSize: 13, color: 'var(--text-primary)', fontFamily: 'monospace', marginTop: 2 }}>{v}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
