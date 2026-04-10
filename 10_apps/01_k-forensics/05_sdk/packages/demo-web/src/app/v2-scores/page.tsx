'use client'

import { useSdk } from '@/components/sdk-provider'
import { ScoreGauge, MiniGauge } from '@/components/score-gauge'
import { scoreColor, trustColor, scoreLabel } from '@/lib/score-colors'
import type { V2Scores, KProtectDecision } from '@/lib/v2-types'

const ACTION_COLORS: Record<string, { bg: string; text: string }> = {
  allow: { bg: 'var(--success-bg)', text: 'var(--success)' },
  monitor: { bg: 'var(--warning-bg)', text: 'var(--warning)' },
  challenge: { bg: 'var(--warning-bg)', text: 'var(--warning)' },
  step_up: { bg: 'var(--danger-bg)', text: 'var(--danger)' },
  block: { bg: 'var(--danger-bg)', text: 'var(--danger)' },
}

const REASON_LABELS: Record<string, string> = {
  session_trust_high: 'High session trust',
  session_trust_moderate: 'Moderate session trust',
  session_trust_low: 'Low session trust',
  session_trust_critical: 'Critical trust deficit',
  bot_score: 'Bot behavior detected',
  replay_score: 'Replay attack detected',
  takeover_probability: 'Account takeover signal',
  credential_drift: 'Credential pattern drift',
  coercion_score: 'Coercion signal detected',
}

const RISK_COLORS: Record<string, string> = {
  low: 'var(--success)',
  medium: 'var(--warning)',
  high: 'var(--warning)',
  critical: 'var(--danger)',
}

function trustLevel(score: number): { label: string; color: string } {
  if (score >= 0.75) return { label: 'HIGH', color: 'var(--success)' }
  if (score >= 0.50) return { label: 'MEDIUM', color: 'var(--warning)' }
  if (score >= 0.25) return { label: 'LOW', color: 'var(--warning)' }
  return { label: 'CRITICAL', color: 'var(--danger)' }
}

function SectionCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{
      background: 'var(--surface)', border: '1px solid var(--border)',
      borderRadius: 6, padding: 24, position: 'relative',
    }}>
      <div style={{
        fontSize: 10, fontWeight: 700, color: 'var(--foreground-muted)', textTransform: 'uppercase' as const,
        letterSpacing: '0.08em', marginBottom: 16,
      }}>{title}</div>
      {children}
    </div>
  )
}

function Badge({ label, color }: { label: string; color: string }) {
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', padding: '3px 10px',
      borderRadius: 4, fontSize: 10, fontWeight: 700, fontFamily: 'var(--font-mono)',
      color, background: 'var(--surface-2)', border: '1px solid var(--border)', letterSpacing: '0.04em',
    }}>{label}</span>
  )
}

function WaitingState() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: 400, gap: 16 }}>
      <div style={{
        width: 48, height: 48, borderRadius: '50%',
        border: '3px solid var(--border)', borderTopColor: 'var(--foreground)',
        animation: 'spin 1s linear infinite',
      }} />
      <div style={{ fontSize: 16, fontWeight: 600, color: 'var(--foreground)' }}>Waiting for V2 scores...</div>
      <div style={{ fontSize: 13, color: 'var(--foreground-subtle)', textAlign: 'center', maxWidth: 400 }}>
        The mock SDK is posting behavioral batches to the scoring engine. Scores will appear once the first response arrives.
      </div>
    </div>
  )
}

export default function V2ScoresPage() {
  const { v2Scores, session, isEnrolling, isLearning } = useSdk()

  if (!v2Scores) return (
    <div>
      <div style={{ marginBottom: 28 }}>
        <h1 style={{ margin: '0 0 4px', fontSize: 24, fontWeight: 700, letterSpacing: '-0.025em', color: 'var(--foreground)' }}>V2 AI Scoring Engine</h1>
        <p style={{ margin: 0, fontSize: 13, color: 'var(--foreground-muted)' }}>Full 22-score behavioral biometrics analysis</p>
      </div>
      <WaitingState />
    </div>
  )

  const s = v2Scores
  const tl = trustLevel(s.trust.session_trust)

  return (
    <div>
      <div style={{ marginBottom: 28 }}>
        <h1 style={{ margin: '0 0 4px', fontSize: 24, fontWeight: 700, letterSpacing: '-0.025em', color: 'var(--foreground)' }}>V2 AI Scoring Engine</h1>
        <p style={{ margin: 0, fontSize: 13, color: 'var(--foreground-muted)' }}>Full 22-score behavioral biometrics analysis</p>
      </div>

      <StatusBanner
        isEnrolling={isEnrolling} isLearning={isLearning}
        maturity={s.meta.profile_maturity} batchesProcessed={s.session.batches_processed}
        processingMs={s.processing_ms} confidence={s.meta.confidence}
        sessionId={session?.session_id}
      />

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 16, marginTop: 20 }}>
        <IdentitySection s={s} />
        <AnomalySection s={s} />
        <HumannessSection s={s} />
        <ThreatSection s={s} />
        <TrustSection s={s} tl={tl} />
        <MetaSection s={s} />
      </div>
      {s.kprotect !== undefined && (
        <div style={{ marginTop: 16 }}>
          <KProtectSection kp={s.kprotect} />
        </div>
      )}
    </div>
  )
}

function StatusBanner({
  isEnrolling, isLearning, maturity, batchesProcessed, processingMs, confidence, sessionId,
}: {
  isEnrolling: boolean; isLearning: boolean; maturity: number
  batchesProcessed: number; processingMs: number; confidence: number; sessionId?: string
}) {
  const bannerLabel = isEnrolling ? 'ENROLLING' : isLearning ? 'LEARNING' : 'ACTIVE'
  const bannerText = isEnrolling
    ? `ENROLLMENT MODE \u2014 Collecting behavioral baseline (batch ${batchesProcessed} processed)`
    : isLearning
    ? `LEARNING MODE \u2014 Profile maturity: ${(maturity * 100).toFixed(0)}% \u2014 Scores will improve as more sessions are collected`
    : 'ACTIVE \u2014 Full scoring enabled'

  return (
    <div style={{
      background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 6,
      padding: '14px 20px', display: 'flex', alignItems: 'center', gap: 16, flexWrap: 'wrap',
    }}>
      <Badge label={bannerLabel} color={isEnrolling ? 'var(--info)' : isLearning ? 'var(--warning)' : 'var(--success)'} />
      <span style={{ fontSize: 12, color: 'var(--foreground-muted)', flex: 1 }}>{bannerText}</span>
      <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
        {sessionId && <span style={{ fontSize: 10, fontFamily: 'var(--font-mono)', color: 'var(--foreground-subtle)' }}>SID: {sessionId.slice(0, 8)}</span>}
        <span style={{ fontSize: 10, fontFamily: 'var(--font-mono)', color: 'var(--foreground-subtle)' }}>{processingMs.toFixed(0)}ms</span>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '3px 10px', background: 'var(--surface-2)', borderRadius: 4 }}>
          <span style={{ fontSize: 10, color: 'var(--foreground-subtle)' }}>Confidence</span>
          <div style={{ width: 60, height: 4, background: 'var(--surface-3)', borderRadius: 2, overflow: 'hidden' }}>
            <div style={{ width: `${confidence * 100}%`, height: '100%', borderRadius: 2, background: trustColor(confidence), transition: 'width 0.5s ease' }} />
          </div>
          <span style={{ fontSize: 10, fontFamily: 'var(--font-mono)', color: trustColor(confidence), fontWeight: 600 }}>{(confidence * 100).toFixed(0)}%</span>
        </div>
      </div>
    </div>
  )
}

function IdentitySection({ s }: { s: V2Scores }) {
  const id = s.identity
  const modDrifts = id.modality_drifts
  const mc = id.matched_cluster

  return (
    <SectionCard title="Identity">
      <div style={{ display: 'flex', gap: 20, alignItems: 'flex-start' }}>
        <ScoreGauge label="Behavioral Drift" score={id.behavioral_drift} colorFn={scoreColor} size={130} subtitle="Primary" />
        <div style={{ flex: 1, minWidth: 0 }}>
          <MiniGauge score={id.credential_drift ?? -1} colorFn={scoreColor} label="Credential Drift" />
          <MiniGauge score={id.identity_confidence} colorFn={trustColor} label="Identity Confidence" />
          <MiniGauge score={id.familiarity_score} colorFn={trustColor} label="Familiarity" />
          <MiniGauge score={id.cognitive_load} colorFn={scoreColor} label="Cognitive Load" />
        </div>
      </div>

      {mc && (
        <div style={{
          marginTop: 14, padding: '8px 12px', background: 'var(--surface-2)', borderRadius: 4,
          fontSize: 11, color: 'var(--foreground-muted)', display: 'flex', gap: 16,
        }}>
          <span>Cluster: <b style={{ color: 'var(--foreground)', fontFamily: 'var(--font-mono)' }}>{mc.cluster_id ?? 'none'}</b></span>
          <span>Quality: <b style={{ fontFamily: 'var(--font-mono)' }}>{(mc.match_quality * 100).toFixed(1)}%</b></span>
          <span>Posterior: <b style={{ fontFamily: 'var(--font-mono)' }}>{mc.posterior.toFixed(3)}</b></span>
        </div>
      )}

      <div style={{ marginTop: 14 }}>
        <div style={{ fontSize: 10, fontWeight: 600, color: 'var(--foreground-subtle)', textTransform: 'uppercase' as const, letterSpacing: '0.04em', marginBottom: 6 }}>
          Modality Drift Breakdown
        </div>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--border)' }}>
              {['Modality', 'Drift', 'Z-Score', 'Raw Dist'].map(h => (
                <th key={h} style={{ textAlign: 'left', padding: '6px 0', fontSize: 9, fontWeight: 600, color: 'var(--foreground-subtle)', textTransform: 'uppercase' as const, letterSpacing: '0.04em' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {Object.entries(modDrifts).map(([mod, d]) => (
              <tr key={mod} style={{ borderBottom: '1px solid var(--border)' }}>
                <td style={{ padding: '6px 0', fontSize: 11, fontWeight: 500, color: 'var(--foreground)', textTransform: 'capitalize' as const }}>{mod}</td>
                <td style={{ padding: '6px 0', fontSize: 11, fontFamily: 'var(--font-mono)', color: d.drift < 0 ? 'var(--foreground-subtle)' : scoreColor(d.drift), fontWeight: 600 }}>{d.drift < 0 ? 'N/A' : scoreLabel(d.drift)}</td>
                <td style={{ padding: '6px 0', fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--foreground-muted)' }}>{d.z_score.toFixed(2)}</td>
                <td style={{ padding: '6px 0', fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--foreground-muted)' }}>{d.raw_distance.toFixed(3)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </SectionCard>
  )
}

function AnomalySection({ s }: { s: V2Scores }) {
  const a = s.anomaly
  const t = a.takeover ?? { takeover_probability: 0, cusum_signal: 0, velocity_signal: 0, concordance_signal: 0, changepoint_detected: false }

  return (
    <SectionCard title="Anomaly">
      <div style={{ display: 'flex', gap: 20, alignItems: 'flex-start' }}>
        <ScoreGauge label="Takeover" score={t.takeover_probability} colorFn={scoreColor} size={130} subtitle="CUSUM" />
        <div style={{ flex: 1, minWidth: 0 }}>
          <MiniGauge score={a.session_anomaly ?? 0} colorFn={scoreColor} label="Session Anomaly" />
          <MiniGauge score={a.velocity_anomaly ?? 0} colorFn={scoreColor} label="Velocity Anomaly" />
          <MiniGauge score={a.pattern_break ?? 0} colorFn={scoreColor} label="Pattern Break" />
          <MiniGauge score={a.consistency ?? 0} colorFn={trustColor} label="Consistency" />
        </div>
      </div>
      <div style={{
        marginTop: 14, padding: '8px 12px', background: 'var(--surface-2)', borderRadius: 4,
        fontSize: 11, display: 'flex', gap: 12, flexWrap: 'wrap',
      }}>
        <span style={{ color: 'var(--foreground-subtle)' }}>CUSUM: <b style={{ fontFamily: 'var(--font-mono)', color: scoreColor(t.cusum_signal) }}>{(t.cusum_signal * 100).toFixed(1)}%</b></span>
        <span style={{ color: 'var(--foreground-subtle)' }}>Velocity: <b style={{ fontFamily: 'var(--font-mono)', color: scoreColor(t.velocity_signal) }}>{(t.velocity_signal * 100).toFixed(1)}%</b></span>
        <span style={{ color: 'var(--foreground-subtle)' }}>Concordance: <b style={{ fontFamily: 'var(--font-mono)', color: scoreColor(t.concordance_signal) }}>{(t.concordance_signal * 100).toFixed(1)}%</b></span>
        {t.changepoint_detected && <Badge label="CHANGEPOINT" color="var(--danger)" />}
      </div>
    </SectionCard>
  )
}

function HumannessSection({ s }: { s: V2Scores }) {
  const h = s.humanness

  return (
    <SectionCard title="Humanness">
      <div style={{ display: 'flex', gap: 20, alignItems: 'flex-start' }}>
        <ScoreGauge label="Bot Score" score={h.bot_score} colorFn={scoreColor} size={130} subtitle="ML Ensemble" />
        <div style={{ flex: 1, minWidth: 0 }}>
          <MiniGauge score={h.replay_score} colorFn={scoreColor} label="Replay Score" />
          <MiniGauge score={h.automation_score} colorFn={scoreColor} label="Automation Score" />
          <MiniGauge score={h.population_anomaly} colorFn={scoreColor} label="Population Anomaly" />
          <div style={{ marginTop: 12 }}>
            <Badge label={h.is_human ? '\u2713 HUMAN' : '\u2717 BOT'} color={h.is_human ? 'var(--success)' : 'var(--danger)'} />
          </div>
        </div>
      </div>
    </SectionCard>
  )
}

function ThreatSection({ s }: { s: V2Scores }) {
  const t = s.threat

  return (
    <SectionCard title="Threat">
      <div style={{ display: 'flex', gap: 24, justifyContent: 'center' }}>
        <ScoreGauge label="Coercion" score={t.coercion_score} colorFn={scoreColor} size={120} subtitle="Under duress" />
        <ScoreGauge label="Impersonation" score={t.impersonation_score} colorFn={scoreColor} size={120} subtitle="Wrong person" />
      </div>
      <div style={{
        marginTop: 14, padding: '8px 12px', background: 'var(--surface-2)', borderRadius: 4,
        fontSize: 11, color: 'var(--foreground-subtle)', lineHeight: 1.5,
      }}>
        <b>Coercion</b> = right person under duress &nbsp;|&nbsp; <b>Impersonation</b> = wrong person entirely
      </div>
    </SectionCard>
  )
}

function TrustSection({ s, tl }: { s: V2Scores; tl: { label: string; color: string } }) {
  const t = s.trust

  return (
    <SectionCard title="Trust">
      <div style={{ display: 'flex', gap: 20, alignItems: 'flex-start' }}>
        <ScoreGauge label="Session Trust" score={t.session_trust} colorFn={trustColor} size={130} subtitle="Primary" />
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', gap: 16, marginBottom: 12 }}>
            <ScoreGauge label="User Trust" score={t.user_trust} colorFn={trustColor} size={90} />
            <ScoreGauge label="Device Trust" score={t.device_trust} colorFn={trustColor} size={90} />
          </div>
          <div style={{ display: 'flex', justifyContent: 'center' }}>
            <Badge label={`TRUST: ${tl.label}`} color={tl.color} />
          </div>
        </div>
      </div>
    </SectionCard>
  )
}

function KProtectSection({ kp }: { kp: KProtectDecision | null | undefined }) {
  if (!kp) {
    return (
      <div style={{
        background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 6,
        padding: '16px 20px', display: 'flex', alignItems: 'center', gap: 12,
      }}>
        <div style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--border)' }} />
        <span style={{ fontSize: 12, color: 'var(--foreground-muted)' }}>kprotect not running — start with <code style={{ fontFamily: 'var(--font-mono)', background: 'var(--surface-2)', padding: '1px 5px', borderRadius: 3 }}>dev.sh</code></span>
      </div>
    )
  }

  const ac = ACTION_COLORS[kp.action] ?? ACTION_COLORS.allow

  return (
    <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 6, padding: '20px 24px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
        <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--foreground-muted)', textTransform: 'uppercase' as const, letterSpacing: '0.08em' }}>kprotect policy decision</div>
        <div style={{ flex: 1, height: 1, background: 'var(--border)' }} />
        {kp.degraded && <Badge label="DEGRADED" color="var(--warning)" />}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16, marginBottom: 16 }}>
        {/* Action */}
        <div>
          <div style={{ fontSize: 10, color: 'var(--foreground-subtle)', marginBottom: 6 }}>Policy Action</div>
          <span style={{
            padding: '8px 18px', borderRadius: 5, fontSize: 15, fontWeight: 800,
            fontFamily: 'var(--font-mono)', color: ac.text, background: ac.bg,
            textTransform: 'uppercase' as const, letterSpacing: '0.06em', display: 'inline-block',
          }}>{kp.action}</span>
          {kp.reason && <div style={{ fontSize: 11, color: 'var(--foreground-muted)', marginTop: 4 }}>{kp.reason}</div>}
        </div>

        {/* Policies */}
        <div>
          <div style={{ fontSize: 10, color: 'var(--foreground-subtle)', marginBottom: 6 }}>Policies</div>
          <div style={{ fontSize: 22, fontWeight: 700 }}>{kp.policies_triggered}</div>
          <div style={{ fontSize: 11, color: 'var(--foreground-muted)' }}>triggered / {kp.policies_evaluated} evaluated</div>
        </div>

        {/* Latency */}
        <div>
          <div style={{ fontSize: 10, color: 'var(--foreground-subtle)', marginBottom: 6 }}>Latency</div>
          <div style={{ fontSize: 22, fontWeight: 700 }}>{kp.latency_ms.total.toFixed(0)}<span style={{ fontSize: 12, fontWeight: 400, color: 'var(--foreground-muted)' }}>ms</span></div>
          <div style={{ fontSize: 11, color: 'var(--foreground-muted)' }}>kbio {kp.latency_ms.kbio.toFixed(0)}ms + policy {kp.latency_ms.policy_execution.toFixed(0)}ms</div>
        </div>
      </div>

      {/* Signals summary */}
      {kp.signals_summary && kp.signals_summary.elevated.length > 0 && (
        <div style={{ marginBottom: 12 }}>
          <div style={{ fontSize: 10, color: 'var(--foreground-subtle)', marginBottom: 6 }}>Elevated Signals ({kp.signals_summary.elevated_count})</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
            {kp.signals_summary.elevated.map(s => (
              <span key={s} style={{ fontSize: 10, padding: '2px 7px', borderRadius: 4, background: 'var(--warning-bg)', color: 'var(--warning)', fontFamily: 'var(--font-mono)' }}>{s}</span>
            ))}
          </div>
        </div>
      )}

      {/* Threats */}
      {kp.threats_detected && kp.threats_detected.length > 0 && (
        <div style={{ marginBottom: 12 }}>
          <div style={{ fontSize: 10, color: 'var(--foreground-subtle)', marginBottom: 6 }}>Threats Detected</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
            {kp.threats_detected.map(t => (
              <span key={t} style={{ fontSize: 10, padding: '2px 7px', borderRadius: 4, background: 'var(--danger-bg)', color: 'var(--danger)', fontFamily: 'var(--font-mono)' }}>{t}</span>
            ))}
          </div>
        </div>
      )}

      {/* Triggered policy details */}
      {kp.details.length > 0 && (
        <div>
          <div style={{ fontSize: 10, color: 'var(--foreground-subtle)', marginBottom: 6 }}>Triggered Rules</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            {kp.details.map(d => {
              const dc = ACTION_COLORS[d.action] ?? ACTION_COLORS.allow
              return (
                <div key={d.policy_code} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '4px 8px', background: 'var(--surface-2)', borderRadius: 4 }}>
                  <span style={{ fontSize: 10, padding: '1px 6px', borderRadius: 3, background: dc.bg, color: dc.text, fontWeight: 700 }}>{d.action}</span>
                  <span style={{ fontSize: 11, fontFamily: 'var(--font-mono)' }}>{d.policy_code}</span>
                  {d.reason && <span style={{ fontSize: 11, color: 'var(--foreground-muted)' }}>{d.reason}</span>}
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}

function MetaSection({ s }: { s: V2Scores }) {
  const m = s.meta
  const v = s.verdict
  const ac = ACTION_COLORS[v.action] ?? ACTION_COLORS.allow
  const rc = RISK_COLORS[v.risk_level] ?? RISK_COLORS.low

  return (
    <SectionCard title="Meta & Verdict">
      <div style={{ marginBottom: 16 }}>
        <MiniGauge score={m.confidence} colorFn={trustColor} label="Confidence" />
        <MiniGauge score={m.signal_richness} colorFn={trustColor} label="Signal Richness" />
        <MiniGauge score={m.profile_maturity} colorFn={trustColor} label="Profile Maturity" />
      </div>

      <div style={{
        padding: '16px 20px', background: 'var(--surface-2)', borderRadius: 6, border: '1px solid var(--border)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 6 }}>
          <span style={{
            padding: '5px 14px', borderRadius: 4, fontSize: 13, fontWeight: 800,
            fontFamily: 'var(--font-mono)', color: ac.text, background: ac.bg,
            textTransform: 'uppercase' as const, letterSpacing: '0.06em',
          }}>{v.action}</span>
          <Badge label={v.risk_level.toUpperCase()} color={rc} />
        </div>
        <div style={{ fontSize: 11, color: 'var(--foreground-muted)', marginBottom: 6 }}>
          {REASON_LABELS[v.primary_reason] ?? v.primary_reason}
        </div>
        <div style={{ fontSize: 10, color: 'var(--foreground-subtle)', marginTop: 6 }}>
          Processing: {s.processing_ms.toFixed(1)}ms &middot; Batch: {s.batch_id.slice(0, 16)} &middot; {new Date(s.processed_at).toLocaleTimeString()}
        </div>
      </div>
    </SectionCard>
  )
}
