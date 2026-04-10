import { actionColor } from '@/lib/colors'

export function ActionBadge({ action, size = 'sm' }: { action: string; size?: 'sm' | 'md' | 'lg' }) {
  const c = actionColor(action)
  const padding = size === 'lg' ? '6px 16px' : size === 'md' ? '4px 12px' : '2px 8px'
  const fontSize = size === 'lg' ? 13 : size === 'md' ? 11 : 10
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center',
      padding, borderRadius: 4,
      fontSize, fontWeight: 700, fontFamily: 'var(--font-mono)',
      textTransform: 'uppercase', letterSpacing: '0.05em',
      color: c.text, background: c.bg,
    }}>
      {action}
    </span>
  )
}
