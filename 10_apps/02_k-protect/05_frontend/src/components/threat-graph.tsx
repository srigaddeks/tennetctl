'use client'

import { useEffect, useRef, useState, useCallback } from 'react'
import type { GraphNode, GraphEdge, GraphNodeType } from '@/lib/types'

const NODE_RADIUS: Record<GraphNodeType, number> = {
  user: 18, device: 14, ip: 12, threat: 20, session: 10,
}
const NODE_COLOR: Record<GraphNodeType, string> = {
  user: 'oklch(0.58 0.14 240)',
  device: 'oklch(0.62 0.14 155)',
  ip: 'oklch(0.72 0.15 75)',
  threat: 'oklch(0.58 0.20 25)',
  session: 'oklch(0.65 0.12 280)',
}
const EDGE_COLOR: Record<GraphEdge['type'], string> = {
  'user-device': 'oklch(0.75 0.10 240)',
  'user-session': 'oklch(0.78 0.08 280)',
  'device-session': 'oklch(0.72 0.10 155)',
  'session-threat': 'oklch(0.68 0.14 25)',
  'ip-session': 'oklch(0.76 0.10 75)',
}

const REPULSION = 2800
const SPRING_LENGTH = 100
const SPRING_STRENGTH = 0.04
const DAMPING = 0.85
const CENTERING = 0.005

type Props = {
  nodes: GraphNode[]
  edges: GraphEdge[]
  width?: number
  height?: number
  onNodeClick?: (node: GraphNode) => void
}

export function ThreatGraph({ nodes: initialNodes, edges, width = 900, height = 600, onNodeClick }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const nodesRef = useRef<GraphNode[]>(initialNodes.map(n => ({ ...n })))
  const rafRef = useRef<number>(0)
  const [selected, setSelected] = useState<GraphNode | null>(null)
  const draggingRef = useRef<{ id: string; offX: number; offY: number } | null>(null)

  // Map node id → index for fast lookup
  const nodeIndex = useCallback((id: string) => nodesRef.current.findIndex(n => n.id === id), [])

  const simulate = useCallback(() => {
    const ns = nodesRef.current
    const cx = width / 2
    const cy = height / 2

    // Reset forces
    for (const n of ns) {
      n.vx = (n.vx ?? 0)
      n.vy = (n.vy ?? 0)
      if (n.pinned) { n.vx = 0; n.vy = 0 }
    }

    // Repulsion between all pairs
    for (let i = 0; i < ns.length; i++) {
      for (let j = i + 1; j < ns.length; j++) {
        const dx = ns[i].x - ns[j].x || 0.01
        const dy = ns[i].y - ns[j].y || 0.01
        const d2 = dx * dx + dy * dy
        const force = REPULSION / d2
        const fx = (dx / Math.sqrt(d2)) * force
        const fy = (dy / Math.sqrt(d2)) * force
        if (!ns[i].pinned) { ns[i].vx += fx; ns[i].vy += fy }
        if (!ns[j].pinned) { ns[j].vx -= fx; ns[j].vy -= fy }
      }
    }

    // Spring forces along edges
    for (const e of edges) {
      const si = nodeIndex(e.source)
      const ti = nodeIndex(e.target)
      if (si < 0 || ti < 0) continue
      const s = ns[si]
      const t = ns[ti]
      const dx = t.x - s.x
      const dy = t.y - s.y
      const d = Math.sqrt(dx * dx + dy * dy) || 0.01
      const force = (d - SPRING_LENGTH) * SPRING_STRENGTH
      const fx = (dx / d) * force
      const fy = (dy / d) * force
      if (!s.pinned) { s.vx += fx; s.vy += fy }
      if (!t.pinned) { t.vx -= fx; t.vy -= fy }
    }

    // Centering force
    for (const n of ns) {
      if (!n.pinned) {
        n.vx += (cx - n.x) * CENTERING
        n.vy += (cy - n.y) * CENTERING
      }
    }

    // Integrate
    for (const n of ns) {
      if (!n.pinned) {
        n.vx *= DAMPING
        n.vy *= DAMPING
        n.x += n.vx
        n.y += n.vy
        n.x = Math.max(20, Math.min(width - 20, n.x))
        n.y = Math.max(20, Math.min(height - 20, n.y))
      }
    }
  }, [edges, width, height, nodeIndex])

  const draw = useCallback(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    const dpr = window.devicePixelRatio || 1
    ctx.clearRect(0, 0, canvas.width, canvas.height)
    ctx.save()
    ctx.scale(dpr, dpr)

    const ns = nodesRef.current

    // Draw edges
    for (const e of edges) {
      const si = nodeIndex(e.source)
      const ti = nodeIndex(e.target)
      if (si < 0 || ti < 0) continue
      const s = ns[si]
      const t = ns[ti]
      ctx.beginPath()
      ctx.moveTo(s.x, s.y)
      ctx.lineTo(t.x, t.y)
      ctx.strokeStyle = EDGE_COLOR[e.type]
      ctx.lineWidth = 1.5
      ctx.globalAlpha = 0.5
      ctx.stroke()
      ctx.globalAlpha = 1
    }

    // Draw nodes
    for (const n of ns) {
      const r = NODE_RADIUS[n.type]
      const color = NODE_COLOR[n.type]
      const isSelected = selected?.id === n.id

      // Glow for threats
      if (n.type === 'threat') {
        ctx.beginPath()
        ctx.arc(n.x, n.y, r + 6, 0, Math.PI * 2)
        ctx.fillStyle = 'oklch(0.58 0.20 25 / 0.15)'
        ctx.fill()
      }

      // Selection ring
      if (isSelected) {
        ctx.beginPath()
        ctx.arc(n.x, n.y, r + 4, 0, Math.PI * 2)
        ctx.strokeStyle = color
        ctx.lineWidth = 2
        ctx.stroke()
      }

      // Node circle
      ctx.beginPath()
      ctx.arc(n.x, n.y, r, 0, Math.PI * 2)
      ctx.fillStyle = color
      ctx.fill()

      // Icon letter
      ctx.fillStyle = 'white'
      ctx.font = `bold ${r * 0.75}px sans-serif`
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      ctx.fillText(n.type[0].toUpperCase(), n.x, n.y)

      // Label
      ctx.fillStyle = 'oklch(0.35 0 0)'
      ctx.font = `11px sans-serif`
      ctx.textAlign = 'center'
      ctx.textBaseline = 'top'
      ctx.fillText(n.label.slice(0, 10) + (n.label.length > 10 ? '…' : ''), n.x, n.y + r + 3)
    }

    ctx.restore()
  }, [edges, selected, nodeIndex])

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const dpr = window.devicePixelRatio || 1
    canvas.width = width * dpr
    canvas.height = height * dpr
    canvas.style.width = `${width}px`
    canvas.style.height = `${height}px`

    let frame = 0
    const loop = () => {
      if (frame < 300) simulate()
      frame++
      draw()
      rafRef.current = requestAnimationFrame(loop)
    }
    rafRef.current = requestAnimationFrame(loop)
    return () => cancelAnimationFrame(rafRef.current)
  }, [simulate, draw, width, height])

  // Update nodes when props change
  useEffect(() => {
    nodesRef.current = initialNodes.map(n => {
      const existing = nodesRef.current.find(e => e.id === n.id)
      return existing ? { ...existing, label: n.label, data: n.data } : { ...n }
    })
  }, [initialNodes])

  const hitTest = useCallback((mx: number, my: number) => {
    const ns = nodesRef.current
    for (let i = ns.length - 1; i >= 0; i--) {
      const n = ns[i]
      const r = NODE_RADIUS[n.type]
      const dx = mx - n.x
      const dy = my - n.y
      if (dx * dx + dy * dy <= r * r) return ns[i]
    }
    return null
  }, [])

  const getCanvasXY = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const rect = canvasRef.current!.getBoundingClientRect()
    return { mx: e.clientX - rect.left, my: e.clientY - rect.top }
  }

  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const { mx, my } = getCanvasXY(e)
    const hit = hitTest(mx, my)
    if (hit) {
      draggingRef.current = { id: hit.id, offX: mx - hit.x, offY: my - hit.y }
      hit.pinned = true
    }
  }

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const { mx, my } = getCanvasXY(e)
    if (draggingRef.current) {
      const n = nodesRef.current.find(n => n.id === draggingRef.current!.id)
      if (n) {
        n.x = mx - draggingRef.current.offX
        n.y = my - draggingRef.current.offY
        n.vx = 0; n.vy = 0
      }
    }
    // Cursor
    const hit = hitTest(mx, my)
    if (canvasRef.current) canvasRef.current.style.cursor = hit ? 'pointer' : 'default'
  }

  const handleMouseUp = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const { mx, my } = getCanvasXY(e)
    if (draggingRef.current) {
      const n = nodesRef.current.find(n => n.id === draggingRef.current!.id)
      if (n) n.pinned = false
      draggingRef.current = null
    } else {
      const hit = hitTest(mx, my)
      if (hit) { setSelected(hit); onNodeClick?.(hit) }
      else setSelected(null)
    }
  }

  return (
    <div style={{ position: 'relative', borderRadius: 'var(--radius)', overflow: 'hidden', border: '1px solid var(--border)', background: 'var(--surface)' }}>
      <canvas
        ref={canvasRef}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={() => { if (draggingRef.current) { const n = nodesRef.current.find(n => n.id === draggingRef.current!.id); if (n) n.pinned = false; draggingRef.current = null } }}
      />
      {/* Legend */}
      <div style={{ position: 'absolute', bottom: 12, left: 12, display: 'flex', gap: 12, background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 6, padding: '6px 10px' }}>
        {(Object.keys(NODE_COLOR) as GraphNodeType[]).map(t => (
          <div key={t} style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 11 }}>
            <div style={{ width: 10, height: 10, borderRadius: '50%', background: NODE_COLOR[t] }} />
            <span style={{ color: 'var(--foreground-muted)' }}>{t}</span>
          </div>
        ))}
      </div>
      {/* Selected node info */}
      {selected && (
        <div style={{ position: 'absolute', top: 12, right: 12, background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, padding: '10px 14px', minWidth: 180, maxWidth: 240 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6 }}>
            <div style={{ width: 10, height: 10, borderRadius: '50%', background: NODE_COLOR[selected.type], flexShrink: 0 }} />
            <strong style={{ fontSize: 13 }}>{selected.label}</strong>
          </div>
          <div style={{ fontSize: 11, color: 'var(--foreground-muted)', marginBottom: 4 }}>Type: {selected.type}</div>
          {Object.entries(selected.data).slice(0, 4).map(([k, v]) => (
            <div key={k} style={{ fontSize: 11, display: 'flex', justifyContent: 'space-between', gap: 8 }}>
              <span style={{ color: 'var(--foreground-subtle)' }}>{k}</span>
              <span>{String(v).slice(0, 20)}</span>
            </div>
          ))}
          <button
            onClick={() => setSelected(null)}
            style={{ position: 'absolute', top: 6, right: 8, background: 'none', border: 'none', cursor: 'pointer', color: 'var(--foreground-muted)', fontSize: 14, lineHeight: 1 }}
          >×</button>
        </div>
      )}
    </div>
  )
}
