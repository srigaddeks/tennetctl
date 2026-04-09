'use client'

type HeatmapProps = {
  matrix: number[][]
  labels?: string[]
  cellSize?: number
  title?: string
}

function heatColor(value: number): string {
  if (value <= 0.05) return 'var(--hm-0)'
  if (value <= 0.15) return 'var(--hm-1)'
  if (value <= 0.3) return 'var(--hm-2)'
  if (value <= 0.5) return 'var(--hm-3)'
  if (value <= 0.7) return 'var(--hm-4)'
  return 'var(--hm-5)'
}

export function Heatmap({ matrix, labels, cellSize = 32, title }: HeatmapProps) {
  const size = matrix.length
  const defaultLabels = labels || Array.from({ length: size }, (_, i) => `Z${i}`)

  return (
    <div>
      {title && (
        <div style={{
          fontSize: 13,
          fontWeight: 600,
          color: 'var(--text-primary)',
          marginBottom: 10,
        }}>{title}</div>
      )}
      <div style={{ display: 'inline-block' }}>
        {/* Column labels */}
        <div style={{ display: 'flex', marginLeft: cellSize + 4 }}>
          {defaultLabels.map((l, i) => (
            <div key={i} style={{
              width: cellSize,
              textAlign: 'center',
              fontSize: 9,
              color: 'var(--text-muted)',
              fontFamily: 'monospace',
            }}>{l}</div>
          ))}
        </div>

        {/* Rows */}
        {matrix.map((row, ri) => (
          <div key={ri} style={{ display: 'flex', alignItems: 'center' }}>
            {/* Row label */}
            <div style={{
              width: cellSize,
              textAlign: 'right',
              paddingRight: 4,
              fontSize: 9,
              color: 'var(--text-muted)',
              fontFamily: 'monospace',
            }}>{defaultLabels[ri]}</div>

            {/* Cells */}
            {row.map((val, ci) => (
              <div
                key={ci}
                title={`${defaultLabels[ri]} -> ${defaultLabels[ci]}: ${(val * 100).toFixed(1)}%`}
                style={{
                  width: cellSize - 2,
                  height: cellSize - 2,
                  margin: 1,
                  borderRadius: 3,
                  background: heatColor(val),
                  transition: 'background 0.4s ease',
                  cursor: 'default',
                }}
              />
            ))}
          </div>
        ))}

        {/* Legend */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: 6,
          marginTop: 8,
          marginLeft: cellSize + 4,
        }}>
          <span style={{ fontSize: 9, color: 'var(--text-muted)' }}>Low</span>
          {['var(--hm-0)', 'var(--hm-1)', 'var(--hm-2)', 'var(--hm-3)', 'var(--hm-4)', 'var(--hm-5)'].map((c, i) => (
            <div key={i} style={{
              width: 14,
              height: 10,
              borderRadius: 2,
              background: c,
            }} />
          ))}
          <span style={{ fontSize: 9, color: 'var(--text-muted)' }}>High</span>
        </div>
      </div>
    </div>
  )
}
