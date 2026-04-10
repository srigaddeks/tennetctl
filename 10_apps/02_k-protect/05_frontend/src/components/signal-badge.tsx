export function SignalBadge({ label, variant = 'default' }: { label: string; variant?: 'vpn' | 'tor' | 'dc' | 'proxy' | 'default' }) {
  const colors: Record<string, { bg: string; text: string }> = {
    vpn:     { bg: 'var(--warning-bg)', text: 'var(--warning)' },
    tor:     { bg: 'var(--danger-bg)',  text: 'var(--danger)' },
    dc:      { bg: 'var(--info-bg)',    text: 'var(--info)' },
    proxy:   { bg: 'var(--warning-bg)', text: 'var(--warning)' },
    default: { bg: 'var(--surface-3)', text: 'var(--foreground-muted)' },
  }
  const c = colors[variant] ?? colors.default
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', padding: '1px 7px',
      borderRadius: 3, fontSize: 9, fontWeight: 700, letterSpacing: '0.06em',
      textTransform: 'uppercase', color: c.text, background: c.bg,
    }}>
      {label}
    </span>
  )
}
