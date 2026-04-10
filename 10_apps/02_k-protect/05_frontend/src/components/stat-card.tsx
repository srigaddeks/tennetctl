export function StatCard({
  label,
  value,
  sub,
  color,
  delta,
}: {
  label: string
  value: string | number
  sub?: string
  color?: string
  delta?: { value: string; positive: boolean }
}) {
  return (
    <div style={{
      background: 'var(--surface)',
      border: '1px solid var(--border)',
      borderRadius: 6,
      padding: '16px 20px',
    }}>
      <div style={{ fontSize: 10, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--foreground-subtle)', marginBottom: 8 }}>
        {label}
      </div>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
        <div style={{ fontSize: 28, fontWeight: 700, fontFamily: 'var(--font-mono)', color: color ?? 'var(--foreground)', letterSpacing: '-0.02em' }}>
          {value}
        </div>
        {delta && (
          <div style={{ fontSize: 11, color: delta.positive ? 'var(--success)' : 'var(--danger)', fontWeight: 600 }}>
            {delta.positive ? '↑' : '↓'} {delta.value}
          </div>
        )}
      </div>
      {sub && <div style={{ fontSize: 11, color: 'var(--foreground-subtle)', marginTop: 2 }}>{sub}</div>}
    </div>
  )
}
