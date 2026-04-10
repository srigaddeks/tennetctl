'use client'

import { useState, useEffect, useMemo } from 'react'
import type { SignalSelection } from '@/lib/types'
import { kpFetch } from '@/lib/api'

type KbioSignal = {
  code: string
  name: string
  description: string
  category: string
  signal_type: 'boolean' | 'score'
  severity: number
  default_config: Record<string, unknown>
  tags: string[]
}

type SelectionMap = Map<string, SignalSelection>

const CATEGORIES = [
  'all',
  'behavioral', 'device', 'network', 'temporal', 'credential',
  'session', 'historical', 'bot', 'social_engineering', 'transaction',
  'fraud_ring', 'compliance',
]

function CategoryBadge({ category }: { category: string }) {
  const colors: Record<string, string> = {
    behavioral: 'oklch(0.58 0.14 240)',
    device: 'oklch(0.62 0.14 155)',
    network: 'oklch(0.72 0.15 75)',
    temporal: 'oklch(0.65 0.12 280)',
    credential: 'oklch(0.65 0.14 30)',
    session: 'oklch(0.60 0.12 200)',
    historical: 'oklch(0.55 0.10 300)',
    bot: 'oklch(0.58 0.20 25)',
    social_engineering: 'oklch(0.62 0.15 50)',
    transaction: 'oklch(0.60 0.14 170)',
    fraud_ring: 'oklch(0.55 0.18 15)',
    compliance: 'oklch(0.55 0.12 220)',
  }
  const color = colors[category] ?? 'oklch(0.55 0 0)'
  return (
    <span style={{ fontSize: 10, padding: '1px 6px', borderRadius: 3, background: `${color}22`, color, fontWeight: 500 }}>
      {category.replace('_', ' ')}
    </span>
  )
}

function SeverityIndicator({ value }: { value: number }) {
  const color = value >= 80 ? 'var(--danger)' : value >= 60 ? 'var(--warning)' : value >= 40 ? 'var(--info)' : 'var(--success)'
  const label = value >= 80 ? 'critical' : value >= 60 ? 'high' : value >= 40 ? 'medium' : 'low'
  return (
    <span style={{ fontSize: 10, padding: '1px 6px', borderRadius: 3, color, background: `${color}22`, fontWeight: 500 }}>
      {label}
    </span>
  )
}

type ConfigEditorProps = {
  signal: KbioSignal
  selection: SignalSelection | undefined
  onSave: (code: string, overrides: Record<string, unknown>) => Promise<void>
}

function ConfigEditor({ signal, selection, onSave }: ConfigEditorProps) {
  const base = { ...signal.default_config, ...(selection?.config_overrides ?? {}) }
  const [values, setValues] = useState<Record<string, unknown>>(base)
  const [saving, setSaving] = useState(false)

  const handleSave = async () => {
    setSaving(true)
    await onSave(signal.code, values)
    setSaving(false)
  }

  const entries = Object.entries(signal.default_config)
  if (entries.length === 0) return <div style={{ fontSize: 12, color: 'var(--foreground-subtle)', padding: '8px 0' }}>No configurable thresholds</div>

  return (
    <div style={{ padding: '12px 0' }}>
      <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--foreground-muted)', marginBottom: 10 }}>Thresholds</div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        {entries.map(([key, defVal]) => {
          const val = values[key] ?? defVal
          const isNum = typeof defVal === 'number'
          const isArr = Array.isArray(defVal)
          return (
            <div key={key}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                <span style={{ fontSize: 12, color: 'var(--foreground-muted)', fontFamily: 'var(--font-mono)' }}>{key}</span>
                <span style={{ fontSize: 12, fontWeight: 600 }}>{isArr ? '[]' : String(val)}</span>
              </div>
              {isNum && !isArr && (
                <input
                  type="range"
                  min={0}
                  max={typeof defVal === 'number' && defVal <= 1 ? 1 : typeof defVal === 'number' && defVal <= 100 ? 100 : 1000}
                  step={typeof defVal === 'number' && defVal <= 1 ? 0.05 : 1}
                  value={typeof val === 'number' ? val : Number(defVal)}
                  onChange={e => setValues(prev => ({ ...prev, [key]: Number(e.target.value) }))}
                  style={{ width: '100%' }}
                />
              )}
              {!isNum && !isArr && (
                <input
                  type="text"
                  value={String(val)}
                  onChange={e => setValues(prev => ({ ...prev, [key]: e.target.value }))}
                  style={{ width: '100%', padding: '5px 8px', borderRadius: 5, border: '1px solid var(--border)', background: 'var(--surface-2)', color: 'var(--foreground)', fontSize: 12 }}
                />
              )}
              {isArr && (
                <input
                  type="text"
                  placeholder={`Comma-separated (default: empty)`}
                  value={Array.isArray(val) ? (val as unknown[]).join(', ') : ''}
                  onChange={e => setValues(prev => ({ ...prev, [key]: e.target.value.split(',').map(s => s.trim()).filter(Boolean) }))}
                  style={{ width: '100%', padding: '5px 8px', borderRadius: 5, border: '1px solid var(--border)', background: 'var(--surface-2)', color: 'var(--foreground)', fontSize: 12 }}
                />
              )}
            </div>
          )
        })}
      </div>
      <button
        onClick={handleSave}
        disabled={saving}
        style={{ marginTop: 12, padding: '6px 14px', borderRadius: 6, border: 'none', background: 'var(--foreground)', color: 'var(--background)', cursor: 'pointer', fontSize: 12, fontWeight: 600 }}
      >{saving ? 'Saving…' : 'Save Thresholds'}</button>
    </div>
  )
}

export default function SignalsPage() {
  const [signals, setSignals] = useState<KbioSignal[]>([])
  const [selections, setSelections] = useState<SelectionMap>(new Map())
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [category, setCategory] = useState('all')
  const [search, setSearch] = useState('')
  const [typeFilter, setTypeFilter] = useState<'all' | 'boolean' | 'score'>('all')
  const [expanded, setExpanded] = useState<string | null>(null)
  const [bulkMode, setBulkMode] = useState(false)
  const [savingBulk, setSavingBulk] = useState(false)

  useEffect(() => {
    Promise.all([
      kpFetch<{ items: KbioSignal[] }>('/api/kbio-signals'),
      kpFetch<{ items: SignalSelection[] }>('/api/signals'),
    ]).then(([sigs, sels]) => {
      setSignals(sigs.items ?? [])
      const m = new Map<string, SignalSelection>()
      for (const s of sels.items ?? []) m.set(s.signal_code, s)
      setSelections(m)
      setLoading(false)
    }).catch(e => { setError(e.message); setLoading(false) })
  }, [])

  const filtered = useMemo(() => signals.filter(s =>
    (category === 'all' || s.category === category) &&
    (typeFilter === 'all' || s.signal_type === typeFilter) &&
    (search === '' || s.name.toLowerCase().includes(search.toLowerCase()) || s.code.includes(search.toLowerCase()))
  ), [signals, category, typeFilter, search])

  const enabledCount = selections.size
  const criticalEnabled = [...selections.values()].filter(s => {
    const sig = signals.find(sg => sg.code === s.signal_code)
    return sig && sig.severity >= 80
  }).length

  const toggle = async (code: string) => {
    const existing = selections.get(code)
    try {
      if (existing) {
        if (existing.is_active) {
          await kpFetch(`/api/signals/${existing.id}`, { method: 'PATCH', body: JSON.stringify({ is_active: false }) })
          setSelections(prev => { const n = new Map(prev); n.set(code, { ...existing, is_active: false }); return n })
        } else {
          await kpFetch(`/api/signals/${existing.id}`, { method: 'PATCH', body: JSON.stringify({ is_active: true }) })
          setSelections(prev => { const n = new Map(prev); n.set(code, { ...existing, is_active: true }); return n })
        }
      } else {
        const sel = await kpFetch<SignalSelection>('/api/signals', { method: 'POST', body: JSON.stringify({ signal_code: code }) })
        setSelections(prev => { const n = new Map(prev); n.set(code, sel); return n })
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e))
    }
  }

  const saveConfig = async (code: string, overrides: Record<string, unknown>) => {
    const existing = selections.get(code)
    try {
      if (existing) {
        await kpFetch(`/api/signals/${existing.id}`, { method: 'PATCH', body: JSON.stringify({ config_overrides: overrides }) })
        setSelections(prev => { const n = new Map(prev); n.set(code, { ...existing, config_overrides: overrides }); return n })
      } else {
        const sel = await kpFetch<SignalSelection>('/api/signals', { method: 'POST', body: JSON.stringify({ signal_code: code, config_overrides: overrides }) })
        setSelections(prev => { const n = new Map(prev); n.set(code, sel); return n })
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e))
    }
  }

  const enableAll = async () => {
    setSavingBulk(true)
    try {
      const codes = filtered.filter(s => !selections.get(s.code)?.is_active).map(s => s.code)
      await kpFetch('/api/signals/bulk', { method: 'POST', body: JSON.stringify({ signal_codes: codes }) })
      const newSels = await kpFetch<{ items: SignalSelection[] }>('/api/signals')
      const m = new Map<string, SignalSelection>()
      for (const s of newSels.items ?? []) m.set(s.signal_code, s)
      setSelections(m)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setSavingBulk(false)
    }
  }

  const isEnabled = (code: string) => {
    const s = selections.get(code)
    return s != null && s.is_active
  }

  if (loading) return <div style={{ padding: '32px 40px', color: 'var(--foreground-muted)' }}>Loading signals…</div>

  return (
    <div style={{ padding: '32px 40px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 24 }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 700, margin: '0 0 4px' }}>Signal Configuration</h1>
          <p style={{ margin: 0, color: 'var(--foreground-muted)', fontSize: 14 }}>
            Enable signals, set custom thresholds, and control what gets evaluated per session
          </p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button
            onClick={() => setBulkMode(m => !m)}
            style={{ padding: '7px 14px', borderRadius: 7, border: '1px solid var(--border)', background: bulkMode ? 'var(--surface-3)' : 'none', cursor: 'pointer', fontSize: 12, fontWeight: 600 }}
          >Bulk Mode</button>
          {bulkMode && (
            <button
              onClick={enableAll}
              disabled={savingBulk}
              style={{ padding: '7px 14px', borderRadius: 7, border: 'none', background: 'var(--foreground)', color: 'var(--background)', cursor: 'pointer', fontSize: 12, fontWeight: 600 }}
            >{savingBulk ? 'Enabling…' : `Enable All ${filtered.length}`}</button>
          )}
        </div>
      </div>

      {error && (
        <div style={{ background: 'var(--danger-bg)', color: 'var(--danger)', padding: '10px 14px', borderRadius: 8, marginBottom: 16, fontSize: 13 }}>
          {error}
          <button onClick={() => setError(null)} style={{ float: 'right', background: 'none', border: 'none', cursor: 'pointer', color: 'inherit' }}>×</button>
        </div>
      )}

      {/* Stats */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 20 }}>
        {[
          { label: 'Total Signals', value: signals.length },
          { label: 'Enabled', value: enabledCount, color: 'var(--success)' },
          { label: 'Critical Enabled', value: criticalEnabled, color: 'var(--danger)' },
          { label: 'Showing', value: filtered.length },
        ].map(s => (
          <div key={s.label} style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, padding: '10px 16px' }}>
            <div style={{ fontSize: 11, color: 'var(--foreground-muted)', marginBottom: 2 }}>{s.label}</div>
            <div style={{ fontSize: 22, fontWeight: 700, color: s.color ?? 'var(--foreground)' }}>{s.value}</div>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 16, flexWrap: 'wrap' }}>
        <input
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="Search signals…"
          style={{ padding: '7px 10px', borderRadius: 6, border: '1px solid var(--border)', background: 'var(--surface-2)', color: 'var(--foreground)', fontSize: 13, minWidth: 220 }}
        />
        <select
          value={typeFilter}
          onChange={e => setTypeFilter(e.target.value as 'all' | 'boolean' | 'score')}
          style={{ padding: '7px 10px', borderRadius: 6, border: '1px solid var(--border)', background: 'var(--surface-2)', color: 'var(--foreground)', fontSize: 12 }}
        >
          <option value="all">All Types</option>
          <option value="boolean">Boolean</option>
          <option value="score">Score</option>
        </select>
      </div>

      {/* Category tabs */}
      <div style={{ display: 'flex', gap: 4, marginBottom: 16, flexWrap: 'wrap' }}>
        {CATEGORIES.map(c => (
          <button
            key={c}
            onClick={() => setCategory(c)}
            style={{
              padding: '4px 10px', borderRadius: 5, border: '1px solid var(--border)',
              background: category === c ? 'var(--foreground)' : 'var(--surface)',
              color: category === c ? 'var(--background)' : 'var(--foreground-muted)',
              cursor: 'pointer', fontSize: 11, fontWeight: category === c ? 600 : 400,
            }}
          >
            {c === 'all' ? `All (${signals.length})` : `${c.replace('_', ' ')} (${signals.filter(s => s.category === c).length})`}
          </button>
        ))}
      </div>

      {/* Signals grid */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
        {filtered.map(sig => {
          const enabled = isEnabled(sig.code)
          const sel = selections.get(sig.code)
          const isExpanded = expanded === sig.code

          return (
            <div
              key={sig.code}
              style={{
                background: 'var(--surface)', border: `1px solid ${enabled ? 'oklch(0.62 0.14 155 / 0.4)' : 'var(--border)'}`,
                borderRadius: 8, overflow: 'hidden',
                borderLeft: `3px solid ${enabled ? 'var(--success)' : 'var(--border)'}`,
              }}
            >
              <div
                style={{ padding: '10px 14px', display: 'grid', gridTemplateColumns: '1fr auto auto auto', gap: 12, alignItems: 'center', cursor: 'pointer' }}
                onClick={() => setExpanded(isExpanded ? null : sig.code)}
              >
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 2 }}>
                    <span style={{ fontSize: 13, fontWeight: 600 }}>{sig.name}</span>
                    <span style={{ fontSize: 10, padding: '0 5px', borderRadius: 3, background: 'var(--surface-3)', color: 'var(--foreground-subtle)', fontFamily: 'var(--font-mono)' }}>{sig.signal_type}</span>
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--foreground-muted)' }}>{sig.description}</div>
                  <div style={{ display: 'flex', gap: 4, marginTop: 4 }}>
                    <CategoryBadge category={sig.category} />
                    <SeverityIndicator value={sig.severity} />
                    {sel?.config_overrides && Object.keys(sel.config_overrides).length > 0 && (
                      <span style={{ fontSize: 10, padding: '1px 5px', borderRadius: 3, background: 'var(--info-bg)', color: 'var(--info)' }}>custom config</span>
                    )}
                  </div>
                </div>
                <span style={{ fontSize: 11, color: 'var(--foreground-subtle)', fontFamily: 'var(--font-mono)' }}>{sig.code}</span>
                <span style={{ fontSize: 10, color: 'var(--foreground-subtle)' }}>{isExpanded ? '▲' : '▼'}</span>
                <div onClick={e => { e.stopPropagation(); toggle(sig.code) }}>
                  <button
                    style={{
                      width: 40, height: 22, borderRadius: 11, border: 'none', cursor: 'pointer',
                      background: enabled ? 'var(--success)' : 'var(--border)',
                      position: 'relative', transition: 'background 0.2s',
                    }}
                  >
                    <div style={{
                      position: 'absolute', top: 3, left: enabled ? 20 : 3,
                      width: 16, height: 16, borderRadius: '50%', background: 'white',
                      transition: 'left 0.2s',
                    }} />
                  </button>
                </div>
              </div>

              {isExpanded && (
                <div style={{ borderTop: '1px solid var(--border)', padding: '0 14px 14px', background: 'var(--surface-2)' }}>
                  <ConfigEditor signal={sig} selection={sel} onSave={saveConfig} />
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
