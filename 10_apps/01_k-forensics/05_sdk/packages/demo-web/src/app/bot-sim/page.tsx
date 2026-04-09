'use client'

import { useState } from 'react'
import { useSdk } from '@/components/sdk-provider'
import { MockKProtect } from '@/lib/mock-sdk'
import { ScoreGauge } from '@/components/score-gauge'
import { scoreColor, trustColor, scoreLabel } from '@/lib/score-colors'

type DetectionLayer = {
  name: string
  description: string
  score: number
  features: string[]
}

export default function BotSimPage() {
  const { scores } = useSdk()
  const [mode, setMode] = useState<'idle' | 'human' | 'bot'>('idle')
  const [layers, setLayers] = useState<DetectionLayer[]>([])

  function simulateHuman() {
    MockKProtect._simulateHuman()
    setMode('human')
    setLayers([
      {
        name: 'Timing Analysis',
        description: 'Keystroke dwell/flight variance',
        score: 0.05 + Math.random() * 0.1,
        features: ['Dwell time CV: 0.42', 'Flight time CV: 0.38', 'Bigram variance: natural', 'Hold duration: varied'],
      },
      {
        name: 'Movement Analysis',
        description: 'Pointer trajectory curvature',
        score: 0.03 + Math.random() * 0.08,
        features: ['Curvature: organic', 'Acceleration: variable', 'Jitter: present', 'Overshoot: occasional'],
      },
      {
        name: 'Behavioral Entropy',
        description: 'Input pattern randomness',
        score: 0.04 + Math.random() * 0.1,
        features: ['Entropy: 3.82 bits', 'Sequence pattern: low', 'Timing regularity: 0.18', 'Pause distribution: log-normal'],
      },
      {
        name: 'Session Fingerprint',
        description: 'Device + environment consistency',
        score: 0.02 + Math.random() * 0.06,
        features: ['WebGL hash: stable', 'Canvas hash: consistent', 'Audio hash: present', 'Screen: native resolution'],
      },
    ])
  }

  function simulateBot() {
    MockKProtect._simulateBot()
    setMode('bot')
    setLayers([
      {
        name: 'Timing Analysis',
        description: 'Keystroke dwell/flight variance',
        score: 0.88 + Math.random() * 0.1,
        features: ['Dwell time CV: 0.01', 'Flight time CV: 0.005', 'Bigram variance: zero', 'Hold duration: constant 45ms'],
      },
      {
        name: 'Movement Analysis',
        description: 'Pointer trajectory curvature',
        score: 0.92 + Math.random() * 0.08,
        features: ['Curvature: linear', 'Acceleration: constant', 'Jitter: none', 'Overshoot: never'],
      },
      {
        name: 'Behavioral Entropy',
        description: 'Input pattern randomness',
        score: 0.95 + Math.random() * 0.05,
        features: ['Entropy: 0.12 bits', 'Sequence pattern: high', 'Timing regularity: 0.98', 'Pause distribution: uniform'],
      },
      {
        name: 'Session Fingerprint',
        description: 'Device + environment consistency',
        score: 0.78 + Math.random() * 0.15,
        features: ['WebGL hash: headless', 'Canvas hash: anomalous', 'Audio hash: missing', 'Screen: emulated'],
      },
    ])
  }

  function reset() {
    MockKProtect._simulateHuman()
    setMode('idle')
    setLayers([])
  }

  return (
    <div>
      <div style={{ marginBottom: 28 }}>
        <h1 className="page-title">Bot Detection Simulator</h1>
        <p className="page-subtitle">
          Compare how the SDK scores human vs. automated (bot) behavioral patterns
        </p>
      </div>

      {/* Control buttons */}
      <div className="card" style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
          <button
            onClick={simulateHuman}
            className="btn"
            style={{
              background: mode === 'human' ? '#22c55e' : 'var(--surface-alt)',
              color: mode === 'human' ? '#fff' : 'var(--text-primary)',
              border: '1px solid var(--border)',
              padding: '12px 28px',
              fontSize: 15,
            }}
          >
            &#9786; Simulate Human
          </button>
          <button
            onClick={simulateBot}
            className="btn"
            style={{
              background: mode === 'bot' ? '#ef4444' : 'var(--surface-alt)',
              color: mode === 'bot' ? '#fff' : 'var(--text-primary)',
              border: '1px solid var(--border)',
              padding: '12px 28px',
              fontSize: 15,
            }}
          >
            &#9881; Simulate Bot
          </button>
          {mode !== 'idle' && (
            <button onClick={reset} className="btn btn-secondary" style={{ marginLeft: 'auto' }}>
              Reset
            </button>
          )}
          {mode !== 'idle' && (
            <div style={{
              padding: '6px 14px',
              borderRadius: 20,
              background: mode === 'bot' ? '#ef444415' : '#22c55e15',
              color: mode === 'bot' ? 'var(--danger)' : 'var(--success)',
              fontSize: 13,
              fontWeight: 600,
            }}>
              {mode === 'bot' ? 'BOT DETECTED' : 'HUMAN VERIFIED'}
            </div>
          )}
        </div>
      </div>

      {/* Score gauges */}
      <div className="grid-4" style={{ marginBottom: 24 }}>
        {[
          { label: 'Bot Score', score: scores.bot, colorFn: scoreColor, sub: 'Primary detection' },
          { label: 'Drift Score', score: scores.drift, colorFn: scoreColor, sub: 'Pattern deviation' },
          { label: 'Anomaly Score', score: scores.anomaly, colorFn: scoreColor, sub: 'Statistical outlier' },
          { label: 'Trust Score', score: scores.trust, colorFn: trustColor, sub: 'Session trust' },
        ].map(g => (
          <div key={g.label} className="card" style={{ display: 'flex', justifyContent: 'center', padding: '24px 12px' }}>
            <ScoreGauge label={g.label} score={g.score} colorFn={g.colorFn} size={130} subtitle={g.sub} />
          </div>
        ))}
      </div>

      {/* Detection layers */}
      {layers.length > 0 && (
        <div>
          <h2 style={{ fontSize: 16, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 16 }}>
            Detection Layers
          </h2>
          <div className="grid-2">
            {layers.map(layer => (
              <div key={layer.name} className="card">
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  marginBottom: 12,
                }}>
                  <div>
                    <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>{layer.name}</div>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{layer.description}</div>
                  </div>
                  <div style={{
                    fontSize: 18,
                    fontWeight: 700,
                    fontFamily: 'monospace',
                    color: scoreColor(layer.score),
                  }}>
                    {scoreLabel(layer.score)}
                  </div>
                </div>

                {/* Score bar */}
                <div style={{
                  height: 6,
                  background: 'var(--surface-alt)',
                  borderRadius: 3,
                  marginBottom: 14,
                  overflow: 'hidden',
                }}>
                  <div style={{
                    height: '100%',
                    width: `${layer.score * 100}%`,
                    background: scoreColor(layer.score),
                    borderRadius: 3,
                    transition: 'width 0.5s ease',
                  }} />
                </div>

                {/* Feature details */}
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: '1fr 1fr',
                  gap: 6,
                }}>
                  {layer.features.map((f, i) => (
                    <div key={i} style={{
                      fontSize: 11,
                      fontFamily: 'monospace',
                      color: 'var(--text-secondary)',
                      padding: '4px 8px',
                      background: 'var(--surface-alt)',
                      borderRadius: 4,
                    }}>
                      {f}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Idle state */}
      {mode === 'idle' && (
        <div className="card" style={{ textAlign: 'center', padding: '60px 24px' }}>
          <div style={{ fontSize: 48, marginBottom: 16, opacity: 0.2 }}>&#9881;</div>
          <div style={{ fontSize: 16, color: 'var(--text-secondary)', fontWeight: 500, marginBottom: 8 }}>
            Choose a simulation mode
          </div>
          <div style={{ fontSize: 13, color: 'var(--text-muted)', maxWidth: 480, margin: '0 auto', lineHeight: 1.6 }}>
            Click &quot;Simulate Human&quot; to generate natural behavioral patterns, or &quot;Simulate Bot&quot;
            to generate automated patterns. Watch how the 4-layer detection system responds to each.
          </div>
        </div>
      )}
    </div>
  )
}
