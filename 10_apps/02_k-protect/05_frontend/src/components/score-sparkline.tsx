'use client'
import { LineChart, Line, ResponsiveContainer } from 'recharts'
import { scoreColor } from '@/lib/colors'

export function ScoreSparkline({ data, width = 80 }: { data: number[]; width?: number }) {
  if (!data.length) return <span style={{ color: 'var(--foreground-subtle)', fontSize: 10 }}>—</span>
  const chartData = data.map(v => ({ v }))
  const latest = data[data.length - 1]
  return (
    <div style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
      <ResponsiveContainer width={width} height={24}>
        <LineChart data={chartData}>
          <Line type="monotone" dataKey="v" stroke={scoreColor(latest)} strokeWidth={1.5} dot={false} isAnimationActive={false} />
        </LineChart>
      </ResponsiveContainer>
      <span style={{ fontSize: 11, fontFamily: 'var(--font-mono)', color: scoreColor(latest), fontWeight: 600 }}>
        {(latest * 100).toFixed(0)}%
      </span>
    </div>
  )
}
