'use client'

import { useSdk } from '@/components/sdk-provider'
import { ScoreGauge } from '@/components/score-gauge'
import { scoreColor, trustColor } from '@/lib/score-colors'

const DETECTION_LAYERS: { name: string; description: string; features: string[]; scoreKey: 'bot_score' | 'replay_score' | 'automation_score' | 'population_anomaly' }[] = [
  {
    name: 'Timing Analysis',
    description: 'Keystroke dwell/flight variance and rhythm patterns',
    features: ['Dwell time coefficient of variation', 'Flight time consistency', 'Bigram timing variance', 'Hold duration distribution'],
    scoreKey: 'bot_score',
  },
  {
    name: 'Movement Analysis',
    description: 'Pointer trajectory curvature and acceleration',
    features: ['Curvature (organic vs. linear)', 'Acceleration variability', 'Jitter presence', 'Overshoot patterns'],
    scoreKey: 'replay_score',
  },
  {
    name: 'Behavioral Entropy',
    description: 'Input pattern randomness and timing regularity',
    features: ['Shannon entropy of input', 'Sequence pattern detection', 'Timing regularity score', 'Pause distribution shape'],
    scoreKey: 'automation_score',
  },
  {
    name: 'Session Fingerprint',
    description: 'Device + environment consistency checks',
    features: ['WebGL hash stability', 'Canvas fingerprint', 'Audio context presence', 'Screen resolution check'],
    scoreKey: 'population_anomaly',
  },
]

export default function BotDetectionPage() {
  const { scores, v2Scores } = useSdk()
  const humanness = v2Scores?.humanness

  return (
    <div>
      <div style={{ marginBottom: 28 }}>
        <h1 style={{ margin: '0 0 4px', fontSize: 24, fontWeight: 700, letterSpacing: '-0.025em', color: 'var(--foreground)' }}>
          Bot Detection
        </h1>
        <p style={{ margin: 0, fontSize: 13, color: 'var(--foreground-muted)' }}>
          Real-time bot detection from your actual browser behavior across 4 detection layers
        </p>
      </div>

      {!v2Scores && (
        <div style={{
          background: 'var(--surface)', border: '1px dashed var(--border)',
          borderRadius: 6, padding: '48px 24px', textAlign: 'center', marginBottom: 28,
        }}>
          <div style={{ fontSize: 16, color: 'var(--foreground-muted)', fontWeight: 500 }}>Analyzing your behavior...</div>
          <div style={{ fontSize: 12, color: 'var(--foreground-subtle)', marginTop: 6 }}>
            Type, move your mouse, or scroll to generate behavioral data. Scores appear after the first backend response.
          </div>
        </div>
      )}

      {/* Score gauges */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 24 }}>
        {[
          { label: 'Bot Score', score: scores?.bot ?? -1, colorFn: scoreColor, sub: 'Primary detection' },
          { label: 'Drift Score', score: scores?.drift ?? -1, colorFn: scoreColor, sub: 'Pattern deviation' },
          { label: 'Anomaly Score', score: scores?.anomaly ?? -1, colorFn: scoreColor, sub: 'Statistical outlier' },
          { label: 'Trust Score', score: scores?.trust ?? -1, colorFn: trustColor, sub: 'Session trust' },
        ].map(g => (
          <div key={g.label} style={{
            background: 'var(--surface)', border: '1px solid var(--border)',
            borderRadius: 6, display: 'flex', justifyContent: 'center', padding: '24px 12px',
          }}>
            <ScoreGauge label={g.label} score={g.score} colorFn={g.colorFn} size={130} subtitle={g.sub} />
          </div>
        ))}
      </div>

      {/* Humanness detail from v2Scores */}
      {humanness && (
        <div style={{
          background: 'var(--surface)', border: '1px solid var(--border)',
          borderRadius: 6, padding: 24, marginBottom: 24,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
            <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--foreground)' }}>Humanness Analysis</div>
            <div style={{
              padding: '4px 12px', borderRadius: 4, fontSize: 11, fontWeight: 700,
              fontFamily: 'var(--font-mono)', letterSpacing: '0.04em',
              background: humanness.is_human ? 'var(--success-bg)' : 'var(--danger-bg)',
              color: humanness.is_human ? 'var(--success)' : 'var(--danger)',
            }}>
              {humanness.is_human ? 'HUMAN VERIFIED' : 'BOT DETECTED'}
            </div>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
            {[
              { label: 'Bot Score', value: humanness.bot_score },
              { label: 'Replay Score', value: humanness.replay_score },
              { label: 'Automation', value: humanness.automation_score },
              { label: 'Population Anomaly', value: humanness.population_anomaly },
            ].map(s => (
              <div key={s.label} style={{ padding: 12, background: 'var(--surface-2)', borderRadius: 4, textAlign: 'center' }}>
                <div style={{ fontSize: 20, fontWeight: 700, fontFamily: 'var(--font-mono)', color: scoreColor(s.value) }}>
                  {(s.value * 100).toFixed(1)}%
                </div>
                <div style={{ fontSize: 10, color: 'var(--foreground-subtle)', marginTop: 4 }}>{s.label}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Detection layers (educational) */}
      <h2 style={{ fontSize: 14, fontWeight: 600, color: 'var(--foreground)', marginBottom: 16 }}>Detection Layers</h2>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        {DETECTION_LAYERS.map(layer => {
          const rawScore = humanness ? humanness[layer.scoreKey] : null
          return (
            <div key={layer.name} style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 6, padding: 24 }}>
              <div style={{ marginBottom: 12 }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--foreground)' }}>{layer.name}</div>
                  <div style={{
                    fontSize: 13, fontWeight: 700, fontFamily: 'var(--font-mono)',
                    color: rawScore != null ? scoreColor(rawScore) : 'var(--foreground-subtle)',
                  }}>
                    {rawScore != null ? `${(rawScore * 100).toFixed(1)}%` : '--'}
                  </div>
                </div>
                <div style={{ fontSize: 11, color: 'var(--foreground-subtle)' }}>{layer.description}</div>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6 }}>
                {layer.features.map((f, i) => (
                  <div key={i} style={{
                    fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--foreground-muted)',
                    padding: '4px 8px', background: 'var(--surface-2)', borderRadius: 3,
                  }}>{f}</div>
                ))}
              </div>
            </div>
          )
        })}
      </div>

      {/* Explanation */}
      <div style={{
        background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 6,
        padding: '16px 20px', marginTop: 24, fontSize: 12, color: 'var(--foreground-muted)', lineHeight: 1.6,
      }}>
        Interact with this page naturally. The scoring engine analyzes your real behavior in real-time. All scores above are from the live backend — no simulated data.
      </div>
    </div>
  )
}
