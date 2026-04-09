'use client'

import { useSdk } from '@/components/sdk-provider'
import { MiniGauge } from '@/components/score-gauge'
import { scoreColor, trustColor } from '@/lib/score-colors'
import { useState } from 'react'

const TRANSACTIONS = [
  { date: 'Apr 9, 2026', desc: 'Whole Foods Market #10234', cat: 'Groceries', amount: '-$127.43', color: 'var(--text-primary)' },
  { date: 'Apr 8, 2026', desc: 'Direct Deposit — Kreesalis Inc', cat: 'Income', amount: '+$4,250.00', color: 'var(--success)' },
  { date: 'Apr 8, 2026', desc: 'Netflix Subscription', cat: 'Entertainment', amount: '-$15.99', color: 'var(--text-primary)' },
  { date: 'Apr 7, 2026', desc: 'Shell Gas Station', cat: 'Auto & Transport', amount: '-$58.20', color: 'var(--text-primary)' },
  { date: 'Apr 7, 2026', desc: 'Wire Transfer to J. Smith', cat: 'Transfer', amount: '-$2,500.00', color: 'var(--danger)' },
  { date: 'Apr 6, 2026', desc: 'Amazon.com', cat: 'Shopping', amount: '-$89.97', color: 'var(--text-primary)' },
  { date: 'Apr 5, 2026', desc: 'Starbucks #4521', cat: 'Dining', amount: '-$6.45', color: 'var(--text-primary)' },
  { date: 'Apr 4, 2026', desc: 'Rent Payment — Apt 12B', cat: 'Housing', amount: '-$2,100.00', color: 'var(--danger)' },
]

export default function DashboardPage() {
  const { scores, session, alerts, initialized } = useSdk()
  const [panelOpen, setPanelOpen] = useState(true)

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: 28 }}>
        <h1 className="page-title">Good morning, welcome back</h1>
        <p className="page-subtitle">Here is your financial overview for today</p>
      </div>

      {/* Account Cards */}
      <div className="grid-3" style={{ marginBottom: 28 }}>
        {[
          { label: 'Checking Account', balance: '$24,832.50', acct: '****4832', status: 'Active' },
          { label: 'Savings Account', balance: '$156,420.00', acct: '****9071', status: 'Active' },
          { label: 'Credit Card', balance: '-$3,215.80', acct: '****7623', status: 'Payment due Jun 15', negative: true },
        ].map((a, i) => (
          <div key={i} className="card">
            <p style={{ margin: 0, fontSize: 13, color: 'var(--text-secondary)', fontWeight: 500 }}>{a.label}</p>
            <p style={{ margin: '8px 0 4px', fontSize: 30, fontWeight: 700, color: a.negative ? 'var(--danger)' : 'var(--text-primary)' }}>{a.balance}</p>
            <p style={{ margin: 0, fontSize: 12, color: 'var(--text-muted)' }}>{a.acct} &middot; {a.status}</p>
          </div>
        ))}
      </div>

      {/* Transactions */}
      <div className="card" style={{ marginBottom: 24 }}>
        <h2 style={{ margin: '0 0 20px', fontSize: 17, fontWeight: 600, color: 'var(--text-primary)' }}>Recent Transactions</h2>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: '2px solid var(--border)' }}>
              {['Date', 'Description', 'Category', 'Amount'].map((h, i) => (
                <th key={h} style={{
                  textAlign: i === 3 ? 'right' : 'left',
                  padding: '10px 0',
                  fontSize: 11,
                  fontWeight: 600,
                  color: 'var(--text-muted)',
                  textTransform: 'uppercase' as const,
                  letterSpacing: 0.5,
                }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {TRANSACTIONS.map((tx, i) => (
              <tr key={i} style={{ borderBottom: '1px solid var(--border)' }}>
                <td style={{ padding: '12px 0', fontSize: 13, color: 'var(--text-muted)' }}>{tx.date}</td>
                <td style={{ padding: '12px 0', fontSize: 14, color: 'var(--text-primary)', fontWeight: 500 }}>{tx.desc}</td>
                <td style={{ padding: '12px 0' }}>
                  <span style={{
                    fontSize: 11,
                    color: 'var(--text-secondary)',
                    background: 'var(--surface-alt)',
                    padding: '3px 10px',
                    borderRadius: 12,
                    fontWeight: 500,
                  }}>{tx.cat}</span>
                </td>
                <td style={{ padding: '12px 0', fontSize: 14, fontWeight: 600, color: tx.color, textAlign: 'right' }}>{tx.amount}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Quick Actions */}
      <div className="grid-2">
        <a href="/payment" style={{ textDecoration: 'none' }}>
          <div className="card" style={{ cursor: 'pointer', transition: 'border-color 0.2s' }}>
            <p style={{ margin: 0, fontSize: 15, fontWeight: 600, color: 'var(--text-primary)' }}>Make a Payment</p>
            <p style={{ margin: '6px 0 0', fontSize: 13, color: 'var(--text-secondary)' }}>Pay bills, credit cards, or vendors</p>
          </div>
        </a>
        <a href="/transfer" style={{ textDecoration: 'none' }}>
          <div className="card" style={{ cursor: 'pointer', transition: 'border-color 0.2s' }}>
            <p style={{ margin: 0, fontSize: 15, fontWeight: 600, color: 'var(--text-primary)' }}>Send a Wire Transfer</p>
            <p style={{ margin: '6px 0 0', fontSize: 13, color: 'var(--text-secondary)' }}>Domestic and international wires</p>
          </div>
        </a>
      </div>

      {/* Floating Score Panel */}
      {initialized && (
        <div style={{
          position: 'fixed',
          bottom: 20,
          right: 20,
          zIndex: 1000,
          width: panelOpen ? 280 : 48,
          transition: 'width 0.3s ease',
        }}>
          {/* Toggle button */}
          <button
            onClick={() => setPanelOpen(!panelOpen)}
            style={{
              position: 'absolute',
              top: -12,
              left: panelOpen ? -12 : 'auto',
              right: panelOpen ? 'auto' : -4,
              width: 28,
              height: 28,
              borderRadius: '50%',
              background: 'var(--accent)',
              color: '#fff',
              border: 'none',
              cursor: 'pointer',
              fontSize: 12,
              fontWeight: 700,
              zIndex: 2,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 2px 8px rgba(99,102,241,0.3)',
            }}
          >
            {panelOpen ? '\u2715' : '\u25C0'}
          </button>

          {panelOpen && (
            <div style={{
              background: 'var(--surface)',
              borderRadius: 12,
              padding: 18,
              boxShadow: 'var(--card-shadow-lg)',
              border: '1px solid var(--border)',
            }}>
              {/* Header */}
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                marginBottom: 14,
                paddingBottom: 10,
                borderBottom: '1px solid var(--border)',
              }}>
                <span style={{
                  width: 8,
                  height: 8,
                  borderRadius: '50%',
                  background: 'var(--success)',
                  boxShadow: '0 0 6px var(--success)',
                }} />
                <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)' }}>kbio Live Scores</span>
              </div>

              {/* Score bars */}
              <MiniGauge label="Drift" score={scores.drift} colorFn={scoreColor} />
              <MiniGauge label="Anomaly" score={scores.anomaly} colorFn={scoreColor} />
              <MiniGauge label="Trust" score={scores.trust} colorFn={trustColor} />
              <MiniGauge label="Bot" score={scores.bot} colorFn={scoreColor} />

              {/* Modality signals */}
              {session && (
                <div style={{ marginTop: 12, paddingTop: 10, borderTop: '1px solid var(--border)' }}>
                  <div style={{ fontSize: 10, color: 'var(--text-muted)', fontWeight: 600, marginBottom: 6, textTransform: 'uppercase' as const, letterSpacing: 0.5 }}>
                    Modalities
                  </div>
                  <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                    {session.modalities.map(m => (
                      <span key={m.modality} style={{
                        fontSize: 10,
                        padding: '2px 8px',
                        borderRadius: 10,
                        background: m.active ? 'var(--accent-bg)' : 'var(--surface-alt)',
                        color: m.active ? 'var(--accent)' : 'var(--text-muted)',
                        fontWeight: 500,
                      }}>
                        {m.modality}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Session info */}
              {session && (
                <div style={{ marginTop: 10, paddingTop: 8, borderTop: '1px solid var(--border)' }}>
                  <div style={{ fontSize: 10, fontFamily: 'monospace', color: 'var(--text-muted)', lineHeight: 1.6 }}>
                    <div>sid: {session.session_id.slice(0, 8)}...</div>
                    <div>pulses: {session.pulse_count}</div>
                    <div>uptime: {Math.floor((Date.now() - session.started_at) / 1000)}s</div>
                  </div>
                </div>
              )}

              {/* Recent alerts */}
              {alerts.length > 0 && (
                <div style={{ marginTop: 10, paddingTop: 8, borderTop: '1px solid var(--border)' }}>
                  <div style={{
                    fontSize: 10,
                    padding: '6px 8px',
                    borderRadius: 6,
                    background: alerts[alerts.length - 1].severity === 'critical' ? '#ef444420' : '#eab30820',
                    color: alerts[alerts.length - 1].severity === 'critical' ? 'var(--danger)' : 'var(--warning)',
                    fontWeight: 500,
                  }}>
                    {alerts[alerts.length - 1].message}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
