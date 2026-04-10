'use client'

import { useState, useEffect } from 'react'
import type { PolicySet, PolicySelection, LibraryPolicy } from '@/lib/types'
import { kpFetch } from '@/lib/api'

function ActionBadge({ action }: { action: string }) {
  const colors: Record<string, { bg: string; fg: string }> = {
    block: { bg: 'var(--danger-bg)', fg: 'var(--danger)' },
    challenge: { bg: 'var(--warning-bg)', fg: 'var(--warning)' },
    allow: { bg: 'var(--success-bg)', fg: 'var(--success)' },
    monitor: { bg: 'var(--info-bg)', fg: 'var(--info)' },
    flag: { bg: 'oklch(0.94 0.04 280)', fg: 'oklch(0.50 0.14 280)' },
    throttle: { bg: 'var(--surface-3)', fg: 'var(--foreground-muted)' },
  }
  const c = colors[action] ?? colors.monitor
  return (
    <span style={{ padding: '2px 8px', borderRadius: 4, fontSize: 11, fontWeight: 600, background: c.bg, color: c.fg }}>
      {action}
    </span>
  )
}

function SeverityBar({ value }: { value: number }) {
  const color = value >= 80 ? 'var(--danger)' : value >= 60 ? 'var(--warning)' : value >= 40 ? 'var(--info)' : 'var(--success)'
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
      <div style={{ flex: 1, height: 4, background: 'var(--surface-3)', borderRadius: 2 }}>
        <div style={{ width: `${value}%`, height: '100%', background: color, borderRadius: 2 }} />
      </div>
      <span style={{ fontSize: 11, color: 'var(--foreground-muted)', width: 22, textAlign: 'right' }}>{value}</span>
    </div>
  )
}

type Tab = 'sets' | 'selections' | 'library'

export default function PoliciesPage() {
  const [tab, setTab] = useState<Tab>('sets')
  const [sets, setSets] = useState<PolicySet[]>([])
  const [selections, setSelections] = useState<PolicySelection[]>([])
  const [library, setLibrary] = useState<LibraryPolicy[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedSet, setSelectedSet] = useState<PolicySet | null>(null)
  const [showNewSet, setShowNewSet] = useState(false)
  const [, setShowAddSelection] = useState(false)
  const [newSetName, setNewSetName] = useState('')
  const [newSetCode, setNewSetCode] = useState('')
  const [newSetMode, setNewSetMode] = useState<'first_match' | 'highest_severity'>('first_match')
  const [search, setSearch] = useState('')
  const [categoryFilter, setCategoryFilter] = useState('all')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    Promise.all([
      kpFetch<{ items: PolicySet[] }>('/api/policy-sets'),
      kpFetch<{ items: PolicySelection[] }>('/api/policy-selections'),
      kpFetch<{ items: LibraryPolicy[] }>('/api/library'),
    ]).then(([s, sel, lib]) => {
      setSets(s.items ?? [])
      setSelections(sel.items ?? [])
      setLibrary(lib.items ?? [])
      setLoading(false)
    }).catch(e => { setError(e.message); setLoading(false) })
  }, [])

  const categories = ['all', ...Array.from(new Set(library.map(p => p.category)))]

  const filteredLibrary = library.filter(p =>
    (categoryFilter === 'all' || p.category === categoryFilter) &&
    (search === '' || p.name.toLowerCase().includes(search.toLowerCase()) || p.code.includes(search.toLowerCase()))
  )

  const createSet = async () => {
    if (!newSetName || !newSetCode) return
    setSaving(true)
    try {
      const result = await kpFetch<PolicySet>('/api/policy-sets', {
        method: 'POST',
        body: JSON.stringify({ name: newSetName, code: newSetCode, evaluation_mode: newSetMode }),
      })
      setSets(prev => [result, ...prev])
      setShowNewSet(false)
      setNewSetName(''); setNewSetCode('')
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setSaving(false)
    }
  }

  const addToSet = async (policyCode: string) => {
    if (!selectedSet) return
    setSaving(true)
    try {
      const sel = await kpFetch<PolicySelection>('/api/policy-selections', {
        method: 'POST',
        body: JSON.stringify({
          policy_set_id: selectedSet.id,
          predefined_policy_code: policyCode,
          priority: (selections.filter(s => s.org_id === selectedSet.org_id).length + 1) * 10,
        }),
      })
      setSelections(prev => [sel, ...prev])
      setShowAddSelection(false)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setSaving(false)
    }
  }

  const toggleSelection = async (sel: PolicySelection) => {
    try {
      await kpFetch(`/api/policy-selections/${sel.id}`, {
        method: 'PATCH',
        body: JSON.stringify({ is_active: !sel.is_active }),
      })
      setSelections(prev => prev.map(s => s.id === sel.id ? { ...s, is_active: !s.is_active } : s))
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e))
    }
  }

  const setSelections_ = selections.filter(s => selectedSet && s.org_id === selectedSet.org_id)

  if (loading) return (
    <div style={{ padding: '32px 40px', color: 'var(--foreground-muted)' }}>Loading policies…</div>
  )

  return (
    <div style={{ padding: '32px 40px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 24 }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 700, margin: '0 0 4px' }}>Policy Configuration</h1>
          <p style={{ margin: 0, color: 'var(--foreground-muted)', fontSize: 14 }}>
            Manage policy sets, add rules from the library, configure actions and thresholds
          </p>
        </div>
        <button
          onClick={() => setShowNewSet(true)}
          style={{ padding: '8px 16px', borderRadius: 8, border: 'none', background: 'var(--foreground)', color: 'var(--background)', cursor: 'pointer', fontWeight: 600, fontSize: 13 }}
        >+ New Policy Set</button>
      </div>

      {error && (
        <div style={{ background: 'var(--danger-bg)', color: 'var(--danger)', padding: '10px 14px', borderRadius: 8, marginBottom: 16, fontSize: 13 }}>
          {error}
          <button onClick={() => setError(null)} style={{ float: 'right', background: 'none', border: 'none', cursor: 'pointer', color: 'inherit' }}>×</button>
        </div>
      )}

      {/* New Set Modal */}
      {showNewSet && (
        <div style={{ position: 'fixed', inset: 0, background: 'oklch(0 0 0 / 0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100 }}>
          <div style={{ background: 'var(--surface)', borderRadius: 12, padding: '24px 28px', width: 420, boxShadow: '0 20px 60px oklch(0 0 0 / 0.3)' }}>
            <h2 style={{ margin: '0 0 20px', fontSize: 17 }}>Create Policy Set</h2>
            <label style={{ display: 'block', marginBottom: 12 }}>
              <div style={{ fontSize: 12, color: 'var(--foreground-muted)', marginBottom: 4 }}>Name</div>
              <input
                value={newSetName}
                onChange={e => setNewSetName(e.target.value)}
                placeholder="My Fraud Prevention Set"
                style={{ width: '100%', padding: '8px 10px', borderRadius: 6, border: '1px solid var(--border)', background: 'var(--surface-2)', color: 'var(--foreground)', fontSize: 13 }}
              />
            </label>
            <label style={{ display: 'block', marginBottom: 12 }}>
              <div style={{ fontSize: 12, color: 'var(--foreground-muted)', marginBottom: 4 }}>Code (unique)</div>
              <input
                value={newSetCode}
                onChange={e => setNewSetCode(e.target.value.toLowerCase().replace(/\s+/g, '-'))}
                placeholder="my-fraud-prevention"
                style={{ width: '100%', padding: '8px 10px', borderRadius: 6, border: '1px solid var(--border)', background: 'var(--surface-2)', color: 'var(--foreground)', fontSize: 13, fontFamily: 'var(--font-mono)' }}
              />
            </label>
            <label style={{ display: 'block', marginBottom: 20 }}>
              <div style={{ fontSize: 12, color: 'var(--foreground-muted)', marginBottom: 4 }}>Evaluation Mode</div>
              <select
                value={newSetMode}
                onChange={e => setNewSetMode(e.target.value as 'first_match' | 'highest_severity')}
                style={{ width: '100%', padding: '8px 10px', borderRadius: 6, border: '1px solid var(--border)', background: 'var(--surface-2)', color: 'var(--foreground)', fontSize: 13 }}
              >
                <option value="first_match">First Match (stop at first triggered policy)</option>
                <option value="highest_severity">Highest Severity (evaluate all, take strictest)</option>
              </select>
            </label>
            <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
              <button onClick={() => setShowNewSet(false)} style={{ padding: '8px 16px', borderRadius: 6, border: '1px solid var(--border)', background: 'none', color: 'var(--foreground-muted)', cursor: 'pointer' }}>Cancel</button>
              <button onClick={createSet} disabled={saving || !newSetName || !newSetCode} style={{ padding: '8px 16px', borderRadius: 6, border: 'none', background: 'var(--foreground)', color: 'var(--background)', cursor: 'pointer', fontWeight: 600 }}>
                {saving ? 'Creating…' : 'Create Set'}
              </button>
            </div>
          </div>
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '280px 1fr', gap: 16 }}>
        {/* Policy sets sidebar */}
        <div>
          <div style={{ fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--foreground-subtle)', marginBottom: 8 }}>Policy Sets ({sets.length})</div>
          {sets.length === 0 ? (
            <div style={{ color: 'var(--foreground-muted)', fontSize: 13, padding: '12px 0' }}>No policy sets yet</div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {sets.map(set => (
                <button
                  key={set.id}
                  onClick={() => setSelectedSet(set)}
                  style={{
                    textAlign: 'left', padding: '10px 12px', borderRadius: 8,
                    border: `1px solid ${selectedSet?.id === set.id ? 'var(--foreground)' : 'var(--border)'}`,
                    background: selectedSet?.id === set.id ? 'var(--surface-3)' : 'var(--surface)',
                    cursor: 'pointer',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 2 }}>
                    <span style={{ fontSize: 13, fontWeight: 600 }}>{set.name ?? set.code}</span>
                    {set.is_default && <span style={{ fontSize: 10, color: 'var(--info)', background: 'var(--info-bg)', padding: '1px 5px', borderRadius: 3 }}>default</span>}
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--foreground-muted)', fontFamily: 'var(--font-mono)' }}>{set.code}</div>
                  <div style={{ fontSize: 11, color: 'var(--foreground-subtle)', marginTop: 2 }}>{set.evaluation_mode}</div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Right panel */}
        <div>
          {!selectedSet ? (
            <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 10, padding: '40px', textAlign: 'center', color: 'var(--foreground-muted)' }}>
              Select a policy set to view and manage its rules
            </div>
          ) : (
            <div>
              {/* Tabs */}
              <div style={{ display: 'flex', gap: 0, marginBottom: 16, borderBottom: '1px solid var(--border)' }}>
                {(['sets', 'library'] as Tab[]).map(t => (
                  <button
                    key={t}
                    onClick={() => setTab(t)}
                    style={{
                      padding: '8px 16px', border: 'none', background: 'none', cursor: 'pointer', fontSize: 13,
                      color: tab === t ? 'var(--foreground)' : 'var(--foreground-muted)',
                      borderBottom: `2px solid ${tab === t ? 'var(--foreground)' : 'transparent'}`,
                      marginBottom: -1,
                    }}
                  >{t === 'sets' ? `Active Rules (${setSelections_.length})` : `Library (${library.length})`}</button>
                ))}
              </div>

              {tab === 'sets' && (
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
                    <div style={{ fontSize: 13, color: 'var(--foreground-muted)' }}>
                      {selectedSet.evaluation_mode === 'first_match' ? 'First match wins — rules evaluated in priority order' : 'All rules evaluated — highest severity action taken'}
                    </div>
                    <button
                      onClick={() => setShowAddSelection(true)}
                      style={{ padding: '6px 12px', borderRadius: 6, border: '1px solid var(--border)', background: 'none', cursor: 'pointer', fontSize: 12, fontWeight: 600 }}
                    >+ Add Rule</button>
                  </div>
                  {setSelections_.length === 0 ? (
                    <div style={{ background: 'var(--surface)', border: '2px dashed var(--border)', borderRadius: 10, padding: '32px', textAlign: 'center', color: 'var(--foreground-muted)', fontSize: 13 }}>
                      No rules yet. Browse the library to add policies.
                    </div>
                  ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                      {setSelections_.sort((a, b) => a.priority - b.priority).map(sel => (
                        <div key={sel.id} style={{
                          background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8,
                          padding: '10px 14px', display: 'grid', gridTemplateColumns: '32px 1fr auto auto auto',
                          alignItems: 'center', gap: 12,
                          opacity: sel.is_active ? 1 : 0.5,
                        }}>
                          <span style={{ fontSize: 12, color: 'var(--foreground-subtle)', fontFamily: 'var(--font-mono)' }}>#{sel.priority}</span>
                          <div>
                            <div style={{ fontSize: 13, fontWeight: 500 }}>{sel.policy_name ?? sel.predefined_policy_code ?? sel.threat_type_code}</div>
                            {sel.policy_category && <div style={{ fontSize: 11, color: 'var(--foreground-subtle)' }}>{sel.policy_category}</div>}
                          </div>
                          {sel.action_override && <ActionBadge action={sel.action_override} />}
                          <button
                            onClick={() => toggleSelection(sel)}
                            style={{
                              width: 36, height: 20, borderRadius: 10, border: 'none', cursor: 'pointer',
                              background: sel.is_active ? 'var(--success)' : 'var(--border)',
                              position: 'relative', transition: 'background 0.2s',
                            }}
                          >
                            <div style={{
                              position: 'absolute', top: 3, left: sel.is_active ? 18 : 2,
                              width: 14, height: 14, borderRadius: '50%', background: 'white',
                              transition: 'left 0.2s',
                            }} />
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {tab === 'library' && (
                <div>
                  <div style={{ display: 'flex', gap: 8, marginBottom: 14 }}>
                    <input
                      value={search}
                      onChange={e => setSearch(e.target.value)}
                      placeholder="Search policies…"
                      style={{ flex: 1, padding: '7px 10px', borderRadius: 6, border: '1px solid var(--border)', background: 'var(--surface-2)', color: 'var(--foreground)', fontSize: 13 }}
                    />
                    <select
                      value={categoryFilter}
                      onChange={e => setCategoryFilter(e.target.value)}
                      style={{ padding: '7px 10px', borderRadius: 6, border: '1px solid var(--border)', background: 'var(--surface-2)', color: 'var(--foreground)', fontSize: 12 }}
                    >
                      {categories.map(c => <option key={c} value={c}>{c}</option>)}
                    </select>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                    {filteredLibrary.map(p => (
                      <div key={p.code} style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, padding: '12px 14px' }}>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 100px 80px auto', alignItems: 'center', gap: 12 }}>
                          <div>
                            <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 2 }}>{p.name}</div>
                            <div style={{ fontSize: 11, color: 'var(--foreground-muted)', marginBottom: 4 }}>{p.description}</div>
                            <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                              {p.tags.slice(0, 4).map(tag => (
                                <span key={tag} style={{ fontSize: 10, padding: '1px 5px', borderRadius: 3, background: 'var(--surface-3)', color: 'var(--foreground-subtle)' }}>{tag}</span>
                              ))}
                            </div>
                          </div>
                          <SeverityBar value={p.severity} />
                          <ActionBadge action={p.default_action} />
                          <button
                            onClick={() => addToSet(p.code)}
                            disabled={saving || setSelections_.some(s => s.predefined_policy_code === p.code)}
                            style={{
                              padding: '5px 12px', borderRadius: 6, border: '1px solid var(--border)',
                              background: setSelections_.some(s => s.predefined_policy_code === p.code) ? 'var(--success-bg)' : 'none',
                              color: setSelections_.some(s => s.predefined_policy_code === p.code) ? 'var(--success)' : 'var(--foreground-muted)',
                              cursor: setSelections_.some(s => s.predefined_policy_code === p.code) ? 'default' : 'pointer',
                              fontSize: 12, fontWeight: 600,
                            }}
                          >
                            {setSelections_.some(s => s.predefined_policy_code === p.code) ? '✓ Added' : '+ Add'}
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
