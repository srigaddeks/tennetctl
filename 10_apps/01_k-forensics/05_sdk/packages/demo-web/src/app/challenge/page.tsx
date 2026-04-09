'use client'

import { useState, useRef } from 'react'
import { MockKProtect, type ChallengeResult, type VerifyResult } from '@/lib/mock-sdk'
import { scoreColor, trustColor } from '@/lib/score-colors'

type VerificationRecord = {
  id: number
  phrase: string
  result: VerifyResult
  timestamp: number
}

export default function ChallengePage() {
  const [challenge, setChallenge] = useState<ChallengeResult | null>(null)
  const [input, setInput] = useState('')
  const [verifying, setVerifying] = useState(false)
  const [lastResult, setLastResult] = useState<VerifyResult | null>(null)
  const [history, setHistory] = useState<VerificationRecord[]>([])
  const inputRef = useRef<HTMLInputElement>(null)
  const counter = useRef(0)

  async function handleGenerate() {
    const ch = await MockKProtect.challenge.generate({ purpose: 'identity_verification' })
    setChallenge(ch)
    setInput('')
    setLastResult(null)
    setTimeout(() => inputRef.current?.focus(), 100)
  }

  async function handleVerify() {
    if (!challenge || !input) return
    setVerifying(true)
    const result = await MockKProtect.challenge.verify(challenge.challenge_id, inputRef.current)
    setLastResult(result)
    counter.current++
    setHistory(prev => [...prev, {
      id: counter.current,
      phrase: challenge.phrase,
      result,
      timestamp: Date.now(),
    }])
    setVerifying(false)
  }

  const timeLeft = challenge ? Math.max(0, Math.floor((challenge.expires_at - Date.now()) / 1000)) : 0

  return (
    <div>
      <div style={{ marginBottom: 28 }}>
        <h1 className="page-title">Behavioral Challenge (KP-TOTP)</h1>
        <p className="page-subtitle">
          Generate a challenge phrase, type it naturally, and verify your behavioral identity
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
        {/* Left: Challenge flow */}
        <div>
          {/* Step 1: Generate */}
          <div className="card" style={{ marginBottom: 20 }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              marginBottom: 16,
            }}>
              <span style={{
                width: 28,
                height: 28,
                borderRadius: '50%',
                background: 'var(--accent-bg)',
                color: 'var(--accent)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 13,
                fontWeight: 700,
              }}>1</span>
              <span style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>Generate Challenge</span>
            </div>
            <button onClick={handleGenerate} className="btn btn-primary" style={{ width: '100%' }}>
              {challenge ? 'New Challenge' : 'Generate Challenge'}
            </button>
          </div>

          {/* Step 2: Type */}
          {challenge && (
            <div className="card" style={{ marginBottom: 20 }}>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                marginBottom: 16,
              }}>
                <span style={{
                  width: 28,
                  height: 28,
                  borderRadius: '50%',
                  background: 'var(--accent-bg)',
                  color: 'var(--accent)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 13,
                  fontWeight: 700,
                }}>2</span>
                <span style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>Type the Phrase</span>
                {timeLeft > 0 && (
                  <span style={{
                    marginLeft: 'auto',
                    fontSize: 11,
                    fontFamily: 'monospace',
                    color: timeLeft < 15 ? 'var(--danger)' : 'var(--text-muted)',
                    fontWeight: 600,
                  }}>
                    {timeLeft}s
                  </span>
                )}
              </div>

              {/* Challenge phrase display */}
              <div style={{
                padding: '16px 20px',
                background: 'var(--surface-alt)',
                borderRadius: 10,
                marginBottom: 14,
                textAlign: 'center',
                border: '1px dashed var(--border)',
              }}>
                <div style={{ fontSize: 10, color: 'var(--text-muted)', marginBottom: 6, textTransform: 'uppercase' as const, letterSpacing: 0.5, fontWeight: 600 }}>
                  Challenge Phrase
                </div>
                <div style={{
                  fontSize: 20,
                  fontWeight: 600,
                  color: 'var(--accent)',
                  letterSpacing: 1,
                  fontFamily: 'monospace',
                }}>
                  {challenge.phrase}
                </div>
              </div>

              <input
                ref={inputRef}
                type="text"
                className="input"
                placeholder="Type the phrase above..."
                value={input}
                onChange={e => setInput(e.target.value)}
                style={{ fontSize: 16, padding: '12px 16px', fontFamily: 'monospace', textAlign: 'center' }}
              />

              {/* Character match indicator */}
              <div style={{
                display: 'flex',
                gap: 3,
                marginTop: 10,
                justifyContent: 'center',
                flexWrap: 'wrap',
              }}>
                {challenge.phrase.split('').map((ch, i) => {
                  const typed = input[i]
                  const match = typed === ch
                  const pending = typed === undefined
                  return (
                    <span
                      key={i}
                      style={{
                        width: 18,
                        height: 24,
                        borderRadius: 4,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: 12,
                        fontFamily: 'monospace',
                        fontWeight: 600,
                        background: pending ? 'var(--surface-alt)' : match ? '#22c55e20' : '#ef444420',
                        color: pending ? 'var(--text-muted)' : match ? 'var(--success)' : 'var(--danger)',
                        border: `1px solid ${pending ? 'var(--border)' : match ? '#22c55e40' : '#ef444440'}`,
                      }}
                    >
                      {ch === ' ' ? '\u00B7' : ch}
                    </span>
                  )
                })}
              </div>
            </div>
          )}

          {/* Step 3: Verify */}
          {challenge && input.length > 0 && (
            <div className="card">
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                marginBottom: 16,
              }}>
                <span style={{
                  width: 28,
                  height: 28,
                  borderRadius: '50%',
                  background: 'var(--accent-bg)',
                  color: 'var(--accent)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 13,
                  fontWeight: 700,
                }}>3</span>
                <span style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>Verify</span>
              </div>

              <button
                onClick={handleVerify}
                disabled={verifying}
                className="btn btn-primary"
                style={{ width: '100%', opacity: verifying ? 0.6 : 1 }}
              >
                {verifying ? 'Analyzing behavioral patterns...' : 'Verify Identity'}
              </button>

              {/* Result */}
              {lastResult && (
                <div style={{
                  marginTop: 16,
                  padding: 20,
                  borderRadius: 12,
                  background: lastResult.verified ? '#22c55e08' : '#ef444408',
                  border: `1px solid ${lastResult.verified ? '#22c55e30' : '#ef444430'}`,
                  textAlign: 'center',
                }}>
                  <div style={{
                    fontSize: 40,
                    marginBottom: 8,
                  }}>
                    {lastResult.verified ? '\u2713' : '\u2717'}
                  </div>
                  <div style={{
                    fontSize: 20,
                    fontWeight: 700,
                    color: lastResult.verified ? 'var(--success)' : 'var(--danger)',
                    marginBottom: 4,
                  }}>
                    {lastResult.verified ? 'Verified' : 'Failed'}
                  </div>
                  <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 14 }}>
                    Behavioral pattern {lastResult.verified ? 'matches baseline' : 'does not match baseline'}
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                    <div style={{ padding: 12, background: 'var(--surface)', borderRadius: 8 }}>
                      <div style={{
                        fontSize: 24,
                        fontWeight: 700,
                        fontFamily: 'monospace',
                        color: trustColor(lastResult.confidence),
                      }}>
                        {(lastResult.confidence * 100).toFixed(1)}%
                      </div>
                      <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 2 }}>Confidence</div>
                    </div>
                    <div style={{ padding: 12, background: 'var(--surface)', borderRadius: 8 }}>
                      <div style={{
                        fontSize: 24,
                        fontWeight: 700,
                        fontFamily: 'monospace',
                        color: trustColor(lastResult.behavioral_match),
                      }}>
                        {(lastResult.behavioral_match * 100).toFixed(1)}%
                      </div>
                      <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 2 }}>Behavioral Match</div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right: History */}
        <div>
          <div className="card">
            <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 14 }}>
              Verification History
            </div>

            {history.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '48px 0' }}>
                <div style={{ fontSize: 32, opacity: 0.2, marginBottom: 8 }}>&#128274;</div>
                <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>No verifications yet</div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>Generate a challenge to begin</div>
              </div>
            ) : (
              <div>
                {[...history].reverse().map(h => (
                  <div key={h.id} style={{
                    padding: '12px 0',
                    borderBottom: '1px solid var(--border)',
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                      <span style={{
                        width: 20,
                        height: 20,
                        borderRadius: '50%',
                        background: h.result.verified ? '#22c55e20' : '#ef444420',
                        color: h.result.verified ? 'var(--success)' : 'var(--danger)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: 10,
                        fontWeight: 700,
                      }}>
                        {h.result.verified ? '\u2713' : '\u2717'}
                      </span>
                      <span style={{ fontSize: 12, fontFamily: 'monospace', color: 'var(--text-secondary)' }}>
                        &quot;{h.phrase}&quot;
                      </span>
                    </div>
                    <div style={{ display: 'flex', gap: 16, paddingLeft: 28 }}>
                      <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>
                        confidence: <span style={{ color: scoreColor(1 - h.result.confidence), fontWeight: 600 }}>
                          {(h.result.confidence * 100).toFixed(1)}%
                        </span>
                      </span>
                      <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>
                        match: <span style={{ color: scoreColor(1 - h.result.behavioral_match), fontWeight: 600 }}>
                          {(h.result.behavioral_match * 100).toFixed(1)}%
                        </span>
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* How it works */}
          <div className="card" style={{ marginTop: 20 }}>
            <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 12 }}>
              How KP-Challenge Works
            </div>
            <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.7 }}>
              <p style={{ margin: '0 0 10px' }}>
                <strong>1. Generate:</strong> The server creates a unique challenge phrase tied to a cryptographic token.
              </p>
              <p style={{ margin: '0 0 10px' }}>
                <strong>2. Type:</strong> As you type the phrase, the SDK captures your keystroke timing pattern &mdash; dwell times, flight times, and rhythm.
              </p>
              <p style={{ margin: '0 0 10px' }}>
                <strong>3. Verify:</strong> The server compares the typing pattern against your baseline. Even if someone knows the phrase, they cannot replicate your typing rhythm.
              </p>
              <p style={{ margin: 0 }}>
                <strong>Result:</strong> Behavioral TOTP &mdash; a one-time password that only <em>you</em> can type correctly.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
