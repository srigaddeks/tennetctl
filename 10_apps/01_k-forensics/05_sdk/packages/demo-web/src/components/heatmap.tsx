'use client'

type HeatmapProps = {
  matrix: number[][]
  labels?: string[]
  cellSize?: number
  title?: string
}

export function Heatmap({ matrix, labels, cellSize = 32, title }: HeatmapProps) {
  const size = matrix.length
  const defaultLabels = labels || Array.from({ length: size }, (_, i) => `Z${i}`)

  return (
    <div>
      {title && (
        <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--foreground)', marginBottom: 10 }}>{title}</div>
      )}
      <div style={{ display: 'inline-block' }}>
        {/* Column labels */}
        <div style={{ display: 'flex', marginLeft: cellSize + 4 }}>
          {defaultLabels.map((l, i) => (
            <div key={i} style={{
              width: cellSize, textAlign: 'center', fontSize: 9,
              color: 'var(--foreground-subtle)', fontFamily: 'var(--font-mono)',
            }}>{l}</div>
          ))}
        </div>

        {/* Rows */}
        {matrix.map((row, ri) => (
          <div key={ri} style={{ display: 'flex', alignItems: 'center' }}>
            <div style={{
              width: cellSize, textAlign: 'right', paddingRight: 4,
              fontSize: 9, color: 'var(--foreground-subtle)', fontFamily: 'var(--font-mono)',
            }}>{defaultLabels[ri]}</div>
            {row.map((val, ci) => (
              <div
                key={ci}
                title={`${defaultLabels[ri]} -> ${defaultLabels[ci]}: ${(val * 100).toFixed(1)}%`}
                style={{
                  width: cellSize - 2, height: cellSize - 2, margin: 1, borderRadius: 3,
                  background: `var(--hm-${Math.min(5, Math.floor(val * 6))})`,
                  transition: 'background 0.4s ease', cursor: 'default',
                }}
              />
            ))}
          </div>
        ))}

        {/* Legend */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: 6, marginTop: 8, marginLeft: cellSize + 4,
        }}>
          <span style={{ fontSize: 9, color: 'var(--foreground-subtle)' }}>Low</span>
          {[0, 1, 2, 3, 4, 5].map((i) => (
            <div key={i} style={{ width: 14, height: 10, borderRadius: 2, background: `var(--hm-${i})` }} />
          ))}
          <span style={{ fontSize: 9, color: 'var(--foreground-subtle)' }}>High</span>
        </div>
      </div>
    </div>
  )
}
