'use client'

import { useSdk } from '@/components/sdk-provider'
import Link from 'next/link'

function scoreColor(score: number): string {
  if (score <= 0.3) return 'var(--success)'
  if (score <= 0.6) return 'var(--warning)'
  return 'var(--danger)'
}

function trustColor(score: number): string {
  if (score >= 0.75) return 'var(--success)'
  if (score >= 0.50) return 'var(--warning)'
  return 'var(--danger)'
}

const DEMOS = [
  {
    href: '/login',
    title: 'Behavioral Login',
    description: 'Keystroke timing analysis during authentication. The SDK captures typing rhythm to build per-user behavioral baselines.',
    tag: 'Identity',
  },
  {
    href: '/scores',
    title: 'Live Scores Dashboard',
    description: 'Real-time composite scores: drift, anomaly, trust, and bot detection. Includes per-modality breakdown.',
    tag: 'Scoring',
  },
  {
    href: '/v2-scores',
    title: 'AI Scoring Engine',
    description: 'Full 22-score analysis: identity, anomaly, humanness, threat, trust, and verdict. The complete behavioral scoring pipeline.',
    tag: 'AI Engine',
  },
  {
    href: '/challenge',
    title: 'KP-Challenge (Behavioral TOTP)',
    description: 'Type a challenge phrase to verify identity. Even with the correct phrase, only the real user\'s typing rhythm matches.',
    tag: 'Challenge',
  },
  {
    href: '/bot-sim',
    title: 'Bot Detection',
    description: 'Real-time bot detection scores from your actual browser behavior across 4 detection layers.',
    tag: 'Bot Detection',
  },
  {
    href: '/multi-user',
    title: 'Multi-User Detection',
    description: 'Switch between users mid-session to see drift spikes. Detects account sharing, credential theft, and session hijacking.',
    tag: 'Drift',
  },
]

export default function DashboardPage() {
  const { scores, session, alerts, initialized, v2Scores, isEnrolling, isLearning } = useSdk()
  const batchesProcessed = v2Scores?.session?.batches_processed ?? 0
  const profileMaturity = v2Scores?.meta?.profile_maturity ?? 0
  const confidence = v2Scores?.meta?.confidence ?? 0

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: 32 }}>
        <h1 style={{
          margin: '0 0 4px',
          fontSize: 24,
          fontWeight: 700,
          letterSpacing: '-0.025em',
          color: 'var(--foreground)',
        }}>kbio SDK Showcase</h1>
        <p style={{
          margin: 0,
          fontSize: 13,
          color: 'var(--foreground-muted)',
        }}>
          Explore behavioral biometrics capabilities &mdash; invisible identity, real-time scoring, bot detection
        </p>
      </div>

      {/* Live score summary cards */}
      {initialized && (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(4, 1fr)',
          gap: 16,
          marginBottom: 32,
        }}>
          {[
            { label: 'Drift', score: scores?.drift, colorFn: scoreColor, desc: 'Behavioral deviation' },
            { label: 'Anomaly', score: scores?.anomaly, colorFn: scoreColor, desc: 'Statistical outlier' },
            { label: 'Trust', score: scores?.trust, colorFn: trustColor, desc: 'Session confidence' },
            { label: 'Bot', score: scores?.bot, colorFn: scoreColor, desc: 'Automation likelihood' },
          ].map(s => (
            <div key={s.label} style={{
              background: 'var(--surface)',
              border: '1px solid var(--border)',
              borderRadius: 6,
              padding: '16px 20px',
            }}>
              <div style={{
                fontSize: 10,
                fontWeight: 600,
                textTransform: 'uppercase' as const,
                letterSpacing: '0.05em',
                color: 'var(--foreground-subtle)',
                marginBottom: 8,
              }}>{s.label}</div>
              <div style={{
                fontSize: 28,
                fontWeight: 700,
                fontFamily: 'var(--font-mono)',
                color: s.score != null ? s.colorFn(s.score) : 'var(--foreground-subtle)',
                letterSpacing: '-0.02em',
              }}>
                {s.score != null && s.score >= 0 ? `${(s.score * 100).toFixed(1)}%` : '--'}
              </div>
              <div style={{ fontSize: 11, color: 'var(--foreground-subtle)', marginTop: 2 }}>{s.desc}</div>
            </div>
          ))}
        </div>
      )}

      {/* SDK Status Banner */}
      {initialized && session && (
        <div style={{
          background: 'var(--surface)',
          border: '1px solid var(--border)',
          borderRadius: 6,
          padding: '14px 20px',
          marginBottom: 32,
          display: 'flex',
          alignItems: 'center',
          gap: 16,
          flexWrap: 'wrap',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{
              width: 8,
              height: 8,
              borderRadius: '50%',
              background: v2Scores ? 'var(--success)' : 'var(--warning)',
              boxShadow: v2Scores ? '0 0 6px var(--success)' : '0 0 6px var(--warning)',
            }} />
            <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--foreground)' }}>
              {v2Scores ? 'SDK Active' : 'Capturing...'}
            </span>
          </div>
          <div style={{ display: 'flex', gap: 16, fontSize: 10, fontFamily: 'var(--font-mono)', color: 'var(--foreground-subtle)' }}>
            <span>sid: {session.session_id.slice(0, 8)}</span>
            <span>pulses: {session.pulse_count}</span>
            <span>uptime: {Math.floor((Date.now() - session.started_at) / 1000)}s</span>
            <span>keys: {session.event_counts.keystroke} ptr: {session.event_counts.pointer}</span>
          </div>
          {alerts.length > 0 && (
            <div style={{
              marginLeft: 'auto',
              fontSize: 10,
              padding: '3px 10px',
              borderRadius: 4,
              background: 'var(--danger-bg)',
              color: 'var(--danger)',
              fontWeight: 500,
            }}>
              {alerts.length} alert{alerts.length !== 1 ? 's' : ''}
            </div>
          )}
        </div>
      )}

      {/* Enrollment / Training Status */}
      {initialized && (
        <div style={{
          background: 'var(--surface)',
          border: `1px solid ${isEnrolling ? 'var(--warning)' : isLearning ? 'var(--warning)' : 'var(--border)'}`,
          borderRadius: 6,
          padding: '16px 20px',
          marginBottom: 32,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: v2Scores ? 12 : 0 }}>
            <div style={{
              padding: '3px 10px', borderRadius: 4, fontSize: 10, fontWeight: 700,
              fontFamily: 'var(--font-mono)', letterSpacing: '0.04em',
              background: isEnrolling ? 'var(--warning-bg)' : isLearning ? 'var(--warning-bg)' : 'var(--success-bg)',
              color: isEnrolling ? 'var(--warning)' : isLearning ? 'var(--warning)' : 'var(--success)',
            }}>
              {!v2Scores ? 'WAITING' : isEnrolling ? 'ENROLLING' : isLearning ? 'LEARNING' : 'ACTIVE'}
            </div>
            <div style={{ fontSize: 12, color: 'var(--foreground-muted)' }}>
              {!v2Scores
                ? 'Type or move your mouse to generate behavioral data'
                : isEnrolling
                  ? 'Collecting behavioral data to build your profile'
                  : isLearning
                    ? 'Profile forming \u2014 scoring accuracy improving with more data'
                    : 'Profile active \u2014 full behavioral scoring enabled'}
            </div>
          </div>

          {v2Scores && (
            <div style={{ display: 'flex', gap: 24, fontSize: 11 }}>
              <div>
                <span style={{ color: 'var(--foreground-subtle)' }}>Batches: </span>
                <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--foreground)' }}>{batchesProcessed}</span>
                <span style={{ color: 'var(--foreground-subtle)' }}> / 3 min</span>
              </div>
              <div>
                <span style={{ color: 'var(--foreground-subtle)' }}>Profile maturity: </span>
                <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--foreground)' }}>{(profileMaturity * 100).toFixed(0)}%</span>
              </div>
              <div>
                <span style={{ color: 'var(--foreground-subtle)' }}>Confidence: </span>
                <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--foreground)' }}>{(confidence * 100).toFixed(0)}%</span>
              </div>
              {/* Progress bar */}
              <div style={{ flex: 1, display: 'flex', alignItems: 'center', gap: 8 }}>
                <div style={{ flex: 1, height: 4, background: 'var(--surface-3)', borderRadius: 2, overflow: 'hidden' }}>
                  <div style={{
                    height: '100%', borderRadius: 2,
                    width: `${Math.min(100, profileMaturity * 100)}%`,
                    background: profileMaturity >= 0.5 ? 'var(--success)' : 'var(--warning)',
                    transition: 'width 0.5s ease',
                  }} />
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Demo cards grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(2, 1fr)',
        gap: 16,
      }}>
        {DEMOS.map(demo => (
          <Link key={demo.href} href={demo.href} style={{ textDecoration: 'none' }}>
            <div style={{
              background: 'var(--surface)',
              border: '1px solid var(--border)',
              borderRadius: 6,
              padding: '20px 24px',
              transition: 'background 0.15s',
              cursor: 'pointer',
              height: '100%',
            }}
              onMouseEnter={e => (e.currentTarget.style.background = 'var(--surface-2)')}
              onMouseLeave={e => (e.currentTarget.style.background = 'var(--surface)')}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                <span style={{
                  fontSize: 9,
                  fontWeight: 600,
                  textTransform: 'uppercase' as const,
                  letterSpacing: '0.06em',
                  color: 'var(--foreground-subtle)',
                  background: 'var(--surface-2)',
                  padding: '2px 8px',
                  borderRadius: 3,
                  border: '1px solid var(--border)',
                }}>{demo.tag}</span>
              </div>
              <div style={{
                fontSize: 15,
                fontWeight: 600,
                color: 'var(--foreground)',
                marginBottom: 6,
              }}>{demo.title}</div>
              <div style={{
                fontSize: 12,
                color: 'var(--foreground-muted)',
                lineHeight: 1.5,
              }}>{demo.description}</div>
            </div>
          </Link>
        ))}
      </div>

      {/* How it works + Profile Training */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginTop: 32 }}>
        <div style={{
          background: 'var(--surface)',
          border: '1px solid var(--border)',
          borderRadius: 6,
          padding: '24px 28px',
        }}>
          <div style={{
            fontSize: 14,
            fontWeight: 600,
            color: 'var(--foreground)',
            marginBottom: 16,
          }}>How kbio Works</div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            {[
              { step: '1', title: 'Capture', desc: 'The SDK passively captures keystroke timing, pointer movement, and touch patterns. No content is recorded.' },
              { step: '2', title: 'Extract', desc: 'Feature extraction produces zone-based timing vectors every 5 seconds and sends them to the scoring backend.' },
              { step: '3', title: 'Score', desc: 'The AI engine compares live features against stored baselines using drift, anomaly, and bot detection models.' },
              { step: '4', title: 'Decide', desc: 'A fusion layer combines 22 scores into a single verdict: allow, monitor, challenge, step-up, or block.' },
            ].map(s => (
              <div key={s.step}>
                <div style={{
                  width: 28,
                  height: 28,
                  borderRadius: '50%',
                  background: 'var(--surface-3)',
                  color: 'var(--foreground)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 12,
                  fontWeight: 700,
                  marginBottom: 10,
                }}>{s.step}</div>
                <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--foreground)', marginBottom: 4 }}>{s.title}</div>
                <div style={{ fontSize: 11, color: 'var(--foreground-muted)', lineHeight: 1.5 }}>{s.desc}</div>
              </div>
            ))}
          </div>
        </div>

        <div style={{
          background: 'var(--surface)',
          border: '1px solid var(--border)',
          borderRadius: 6,
          padding: '24px 28px',
        }}>
          <div style={{
            fontSize: 14,
            fontWeight: 600,
            color: 'var(--foreground)',
            marginBottom: 16,
          }}>Profile Training</div>
          <div style={{ fontSize: 12, color: 'var(--foreground-muted)', lineHeight: 1.7 }}>
            <p style={{ margin: '0 0 12px' }}>
              kbio builds a behavioral profile by collecting data over multiple batches. Each batch (sent every 5 seconds) contains keystroke timing, pointer movement, and other behavioral signals.
            </p>
            <div style={{
              display: 'grid', gridTemplateColumns: '1fr', gap: 8, marginBottom: 12,
            }}>
              {[
                { phase: 'Enrolling', batches: '0\u20133', desc: 'Buffering behavioral data. Drift scores not yet computed. Verdict: always monitor.', color: 'var(--warning)' },
                { phase: 'Forming', batches: '3+', desc: 'Initial clustering runs. Profile created with baseline quality "forming". Drift scoring begins.', color: 'var(--warning)' },
                { phase: 'Active', batches: '10+', desc: 'Full scoring active. Baseline updates via EMA from genuine sessions (low drift, high trust).', color: 'var(--success)' },
              ].map(p => (
                <div key={p.phase} style={{
                  padding: '8px 12px', background: 'var(--surface-2)', borderRadius: 4,
                  borderLeft: `3px solid ${p.color}`,
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={{ fontSize: 11, fontWeight: 700, color: p.color }}>{p.phase}</span>
                    <span style={{ fontSize: 10, fontFamily: 'var(--font-mono)', color: 'var(--foreground-subtle)' }}>{p.batches} batches</span>
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--foreground-muted)', marginTop: 2 }}>{p.desc}</div>
                </div>
              ))}
            </div>
            <p style={{ margin: 0, fontSize: 11, color: 'var(--foreground-subtle)' }}>
              The more you interact, the stronger the profile. After enrollment, the system detects drift (someone else using your account), anomalies, and bots in real-time.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
