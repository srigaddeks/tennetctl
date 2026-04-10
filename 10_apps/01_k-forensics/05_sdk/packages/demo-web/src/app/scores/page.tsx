'use client'

import { useSdk } from '@/components/sdk-provider'
import { ScoreGauge } from '@/components/score-gauge'
import { scoreColor, trustColor, scoreLabel } from '@/lib/score-colors'

export default function ScoresPage() {
  const { scores, session, v2Scores } = useSdk()

  const identity = v2Scores?.identity
  const fusionWeights = identity?.fusion_weights ?? {}
  const modalityDrifts = identity?.modality_drifts ?? {}
  const fp = session?.device_fingerprint
  const totalEvents = session ? Object.values(session.event_counts).reduce((s, n) => s + n, 0) : 0

  return (
    <div>
      <div style={{ marginBottom: 28 }}>
        <h1 style={{ margin: '0 0 4px', fontSize: 24, fontWeight: 700, letterSpacing: '-0.025em', color: 'var(--foreground)' }}>
          Scores Dashboard
        </h1>
        <p style={{ margin: 0, fontSize: 13, color: 'var(--foreground-muted)' }}>
          Real-time composite and per-modality behavioral scores
        </p>
      </div>

      {!v2Scores && (
        <div style={{
          background: 'var(--surface)', border: '1px dashed var(--border)',
          borderRadius: 6, padding: '48px 24px', textAlign: 'center', marginBottom: 28,
        }}>
          <div style={{ fontSize: 16, color: 'var(--foreground-muted)', fontWeight: 500 }}>Waiting for scores...</div>
          <div style={{ fontSize: 12, color: 'var(--foreground-subtle)', marginTop: 6 }}>
            Type or move your mouse to generate behavioral data. Scores appear after the first backend response.
          </div>
        </div>
      )}

      {/* 4 Gauge Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 28 }}>
        {[
          { label: 'Drift Score', score: scores?.drift ?? -1, colorFn: scoreColor, sub: 'Behavioral deviation' },
          { label: 'Anomaly Score', score: scores?.anomaly ?? -1, colorFn: scoreColor, sub: 'Statistical outlier' },
          { label: 'Trust Score', score: scores?.trust ?? -1, colorFn: trustColor, sub: 'Session confidence' },
          { label: 'Bot Score', score: scores?.bot ?? -1, colorFn: scoreColor, sub: 'Automation likelihood' },
        ].map(g => (
          <div key={g.label} style={{
            background: 'var(--surface)', border: '1px solid var(--border)',
            borderRadius: 6, display: 'flex', justifyContent: 'center', padding: '28px 16px',
          }}>
            <ScoreGauge label={g.label} score={g.score} colorFn={g.colorFn} size={150} subtitle={g.sub} />
          </div>
        ))}
      </div>

      {/* Modality Drifts + Fusion Weights */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 6, padding: 24 }}>
          <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--foreground)', marginBottom: 14 }}>
            Per-Modality Drift
          </div>
          {Object.keys(modalityDrifts).length > 0 ? (
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '2px solid var(--border)' }}>
                  {['Modality', 'Drift', 'Z-Score', 'Raw Distance'].map(h => (
                    <th key={h} style={{
                      textAlign: 'left', padding: '8px 0', fontSize: 10, fontWeight: 600,
                      color: 'var(--foreground-subtle)', textTransform: 'uppercase' as const, letterSpacing: '0.04em',
                    }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {Object.entries(modalityDrifts).map(([name, m]) => (
                  <tr key={name} style={{ borderBottom: '1px solid var(--border)' }}>
                    <td style={{ padding: '10px 0', fontSize: 13, fontWeight: 500, color: 'var(--foreground)', textTransform: 'capitalize' as const }}>{name}</td>
                    <td style={{ padding: '10px 0', fontSize: 12, fontFamily: 'var(--font-mono)', color: m.drift >= 0 ? scoreColor(m.drift) : 'var(--foreground-subtle)', fontWeight: 600 }}>
                      {m.drift >= 0 ? scoreLabel(m.drift) : 'n/a'}
                    </td>
                    <td style={{ padding: '10px 0', fontSize: 12, fontFamily: 'var(--font-mono)', color: 'var(--foreground-muted)' }}>
                      {m.z_score.toFixed(2)}
                    </td>
                    <td style={{ padding: '10px 0', fontSize: 12, fontFamily: 'var(--font-mono)', color: 'var(--foreground-muted)' }}>
                      {m.raw_distance.toFixed(3)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div style={{ color: 'var(--foreground-subtle)', fontSize: 12, padding: '32px 0', textAlign: 'center' }}>
              No modality data yet
            </div>
          )}
        </div>

        <div>
          {/* Fusion Weights */}
          <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 6, padding: 24, marginBottom: 16 }}>
            <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--foreground)', marginBottom: 14 }}>Fusion Weights</div>
            {Object.keys(fusionWeights).length > 0 ? (
              <>
                <div style={{ height: 24, borderRadius: 4, overflow: 'hidden', display: 'flex', background: 'var(--surface-2)' }}>
                  {Object.entries(fusionWeights).map(([key, weight], i) => {
                    const opacity = 0.3 + (i * 0.12)
                    return (
                      <div key={key} title={`${key}: ${(weight * 100).toFixed(0)}%`} style={{
                        width: `${weight * 100}%`, background: `var(--foreground)`, opacity,
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        transition: 'width 0.5s ease',
                      }}>
                        {weight >= 0.1 && <span style={{ fontSize: 9, color: 'var(--background)', fontWeight: 600, whiteSpace: 'nowrap' }}>{key}</span>}
                      </div>
                    )
                  })}
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 10 }}>
                  {Object.entries(fusionWeights).map(([key, weight], i) => {
                    const opacity = 0.3 + (i * 0.12)
                    return (
                      <span key={key} style={{ fontSize: 10, display: 'flex', alignItems: 'center', gap: 4, color: 'var(--foreground-subtle)' }}>
                        <span style={{ width: 8, height: 8, borderRadius: 2, background: 'var(--foreground)', opacity, display: 'inline-block' }} />
                        {key} {(weight * 100).toFixed(0)}%
                      </span>
                    )
                  })}
                </div>
              </>
            ) : (
              <div style={{ color: 'var(--foreground-subtle)', fontSize: 12, textAlign: 'center', padding: '16px 0' }}>
                No fusion data yet
              </div>
            )}
          </div>

          {/* Device Fingerprint */}
          {fp && (
            <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 6, padding: 24, marginBottom: 16 }}>
              <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--foreground)', marginBottom: 10 }}>Device Fingerprint</div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6 }}>
                {[
                  ['Platform', fp.platform], ['Browser', fp.browser], ['Screen', fp.screen], ['Timezone', fp.timezone],
                  ['Language', fp.language], ['Cores', String(fp.cores)], ['Memory', `${fp.memory}GB`],
                ].map(([k, v]) => (
                  <div key={k}>
                    <span style={{ fontSize: 10, color: 'var(--foreground-subtle)' }}>{k}: </span>
                    <span style={{ fontSize: 10, color: 'var(--foreground-muted)', fontFamily: 'var(--font-mono)' }}>{v}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Session Metadata */}
          {session && (
            <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 6, padding: 24 }}>
              <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--foreground)', marginBottom: 10 }}>Session Metadata</div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                {[
                  ['Session ID', session.session_id.slice(0, 12) + '...'],
                  ['Pulses', String(session.pulse_count)],
                  ['Duration', `${Math.floor((Date.now() - session.started_at) / 1000)}s`],
                  ['Events', String(totalEvents)],
                  ['Trust Level', scores && scores.trust >= 0.75 ? 'HIGH' : scores && scores.trust >= 0.5 ? 'MEDIUM' : scores ? 'LOW' : '--'],
                  ['User', session.user_hash ? session.user_hash.slice(0, 16) + '...' : 'Anonymous'],
                ].map(([k, v]) => (
                  <div key={k} style={{ padding: '8px 10px', background: 'var(--surface-2)', borderRadius: 4 }}>
                    <div style={{ fontSize: 10, color: 'var(--foreground-subtle)', fontWeight: 600, textTransform: 'uppercase' as const, letterSpacing: '0.03em' }}>{k}</div>
                    <div style={{ fontSize: 13, color: 'var(--foreground)', fontFamily: 'var(--font-mono)', marginTop: 2 }}>{v}</div>
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
