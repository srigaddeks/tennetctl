'use client'

type ScoreGaugeProps = {
  label: string
  score: number
  colorFn: (score: number) => string
  size?: number
  subtitle?: string
}

export function ScoreGauge({ label, score, colorFn, size = 140, subtitle }: ScoreGaugeProps) {
  const color = colorFn(score)
  const radius = (size - 16) / 2
  const circumference = 2 * Math.PI * radius
  const pct = score < 0 ? 0 : score
  const offset = circumference - pct * circumference
  const displayValue = score < 0 ? '--' : (score * 100).toFixed(1)

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8 }}>
      <div style={{ position: 'relative', width: size, height: size }}>
        <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
          <circle
            cx={size / 2} cy={size / 2} r={radius}
            fill="none" stroke="var(--border)" strokeWidth={8}
          />
          <circle
            cx={size / 2} cy={size / 2} r={radius}
            fill="none" stroke={color} strokeWidth={8}
            strokeDasharray={circumference} strokeDashoffset={offset}
            strokeLinecap="round"
            style={{ transition: 'stroke-dashoffset 0.6s ease, stroke 0.3s ease' }}
          />
        </svg>
        <div style={{
          position: 'absolute', inset: 0,
          display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
        }}>
          <span style={{
            fontSize: size * 0.22, fontWeight: 700, color,
            fontFamily: 'var(--font-mono)', letterSpacing: -1,
          }}>{displayValue}</span>
          {score >= 0 && (
            <span style={{ fontSize: size * 0.1, color: 'var(--foreground-subtle)', fontWeight: 500 }}>%</span>
          )}
        </div>
      </div>
      <div style={{ textAlign: 'center' }}>
        <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--foreground)' }}>{label}</div>
        {subtitle && (
          <div style={{ fontSize: 11, color: 'var(--foreground-subtle)', marginTop: 2 }}>{subtitle}</div>
        )}
      </div>
    </div>
  )
}

type MiniGaugeProps = {
  score: number
  colorFn: (score: number) => string
  label: string
}

export function MiniGauge({ score, colorFn, label }: MiniGaugeProps) {
  const color = colorFn(score)
  const pct = score < 0 ? 0 : score * 100

  return (
    <div style={{ marginBottom: 10 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
        <span style={{ fontSize: 11, color: 'var(--foreground-muted)', fontWeight: 500 }}>{label}</span>
        <span style={{ fontSize: 11, fontFamily: 'var(--font-mono)', color, fontWeight: 600 }}>
          {score < 0 ? '--' : `${pct.toFixed(1)}%`}
        </span>
      </div>
      <div style={{
        height: 4, background: 'var(--surface-3)', borderRadius: 2, overflow: 'hidden',
      }}>
        <div style={{
          height: '100%', width: `${pct}%`, background: color, borderRadius: 2,
          transition: 'width 0.5s ease, background 0.3s ease',
        }} />
      </div>
    </div>
  )
}
