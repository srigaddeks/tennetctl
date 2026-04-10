'use client'

import { useState, useRef, useEffect } from 'react'
import { useSdk } from '@/components/sdk-provider'
import { trustColor } from '@/lib/score-colors'

type ChallengeData = {
  challenge_id: string
  prompt: string
  char_count: number
  expires_at: number
  nonce: string
}

type VerifyData = {
  challenge_id: string
  passed: boolean
  drift_score: number
  confidence: number
  action: string
}

type VerificationRecord = {
  id: number
  prompt: string
  result: VerifyData
  timestamp: number
}

export default function ChallengePage() {
  const { session } = useSdk()
  const [challenge, setChallenge] = useState<ChallengeData | null>(null)
  const [input, setInput] = useState('')
  const [verifying, setVerifying] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [lastResult, setLastResult] = useState<VerifyData | null>(null)
  const [history, setHistory] = useState<VerificationRecord[]>([])
  const [error, setError] = useState<string | null>(null)
  const [timeLeft, setTimeLeft] = useState(0)
  const inputRef = useRef<HTMLInputElement>(null)
  const counter = useRef(0)

  useEffect(() => {
    if (!challenge) {
      setTimeLeft(0)
      return
    }
    const compute = () => Math.max(0, Math.floor((challenge.expires_at - Date.now()) / 1000))
    setTimeLeft(compute())
    const id = setInterval(() => {
      const remaining = compute()
      setTimeLeft(remaining)
      if (remaining === 0) clearInterval(id)
    }, 1000)
    return () => clearInterval(id)
  }, [challenge])

  async function handleGenerate() {
    setGenerating(true)
    setError(null)
    try {
      const res = await fetch('/api/kp-challenge', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'generate',
          session_id: session?.session_id ?? 'demo-session',
          user_hash: session?.user_hash ?? 'demo-user',
          purpose: 'identity_verification',
        }),
      })
      const json = await res.json()
      if (!json.ok) {
        setError(json.error?.message ?? 'Failed to generate challenge')
        return
      }
      setChallenge(json.data)
      setInput('')
      setLastResult(null)
      setTimeout(() => inputRef.current?.focus(), 100)
    } catch {
      setError('Backend unavailable — cannot generate challenge')
    } finally {
      setGenerating(false)
    }
  }

  async function handleVerify() {
    if (!challenge || !input || !session) return
    setVerifying(true)
    setError(null)
    try {
      const res = await fetch('/api/kp-challenge', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'verify',
          challenge_id: challenge.challenge_id,
          session_id: session.session_id,
          user_hash: session.user_hash ?? 'demo-user',
          response_batch: { typed_text: input, timestamp: Date.now() },
        }),
      })
      const json = await res.json()
      if (!json.ok) {
        setError(json.error?.message ?? 'Verification failed')
        return
      }
      const result: VerifyData = json.data
      setLastResult(result)
      counter.current++
      setHistory(prev => [...prev, { id: counter.current, prompt: challenge.prompt, result, timestamp: Date.now() }])
    } catch {
      setError('Backend unavailable — cannot verify')
    } finally {
      setVerifying(false)
    }
  }

  const isExpired = challenge !== null && timeLeft === 0

  return (
    <div>
      <div style={{ marginBottom: 28 }}>
        <h1 style={{ margin: '0 0 4px', fontSize: 24, fontWeight: 700, letterSpacing: '-0.025em', color: 'var(--foreground)' }}>
          Behavioral Challenge (KP-TOTP)
        </h1>
        <p style={{ margin: 0, fontSize: 13, color: 'var(--foreground-muted)' }}>
          Generate a challenge phrase, type it naturally, and verify your behavioral identity
        </p>
      </div>

      {error && (
        <div style={{
          background: 'var(--danger-bg)', border: '1px solid var(--border)', borderRadius: 6,
          padding: '12px 16px', marginBottom: 20, fontSize: 12, color: 'var(--danger)',
        }}>
          {error}
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
        {/* Left: Challenge flow */}
        <div>
          {/* Step 1 */}
          <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 6, padding: 24, marginBottom: 20 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
              <span style={{
                width: 28, height: 28, borderRadius: '50%', background: 'var(--surface-3)',
                color: 'var(--foreground)', display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 13, fontWeight: 700,
              }}>1</span>
              <span style={{ fontSize: 14, fontWeight: 600, color: 'var(--foreground)' }}>Generate Challenge</span>
            </div>
            <button onClick={handleGenerate} disabled={generating} style={{
              width: '100%', padding: 12, borderRadius: 6, border: 'none',
              background: 'var(--foreground)', color: 'var(--background)',
              fontSize: 14, fontWeight: 600, cursor: 'pointer', opacity: generating ? 0.6 : 1,
            }}>
              {generating ? 'Generating...' : challenge ? 'New Challenge' : 'Generate Challenge'}
            </button>
          </div>

          {/* Step 2 */}
          {challenge && (
            <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 6, padding: 24, marginBottom: 20 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
                <span style={{
                  width: 28, height: 28, borderRadius: '50%', background: 'var(--surface-3)',
                  color: 'var(--foreground)', display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 13, fontWeight: 700,
                }}>2</span>
                <span style={{ fontSize: 14, fontWeight: 600, color: 'var(--foreground)' }}>Type the Phrase</span>
                {timeLeft > 0 ? (
                  <span style={{
                    marginLeft: 'auto', fontSize: 11, fontFamily: 'var(--font-mono)',
                    color: timeLeft < 15 ? 'var(--danger)' : 'var(--foreground-subtle)', fontWeight: 600,
                  }}>{timeLeft}s</span>
                ) : isExpired ? (
                  <span style={{
                    marginLeft: 'auto', fontSize: 11, fontFamily: 'var(--font-mono)',
                    color: 'var(--danger)', fontWeight: 700, letterSpacing: '0.04em',
                  }}>EXPIRED</span>
                ) : null}
              </div>

              <div style={{
                padding: '16px 20px', background: 'var(--surface-2)', borderRadius: 6,
                marginBottom: 14, textAlign: 'center', border: '1px dashed var(--border)',
              }}>
                <div style={{ fontSize: 10, color: 'var(--foreground-subtle)', marginBottom: 6, textTransform: 'uppercase' as const, letterSpacing: '0.04em', fontWeight: 600 }}>Challenge Phrase</div>
                <div style={{ fontSize: 20, fontWeight: 600, color: 'var(--foreground)', letterSpacing: 1, fontFamily: 'var(--font-mono)' }}>{challenge.prompt}</div>
              </div>

              <input
                ref={inputRef} type="text" placeholder="Type the phrase above..."
                value={input} onChange={e => setInput(e.target.value)}
                disabled={isExpired}
                style={{
                  width: '100%', padding: '12px 16px', borderRadius: 6, border: '1px solid var(--border)',
                  background: 'var(--surface)', color: 'var(--foreground)', fontSize: 16,
                  fontFamily: 'var(--font-mono)', textAlign: 'center', outline: 'none', boxSizing: 'border-box',
                  opacity: isExpired ? 0.5 : 1, cursor: isExpired ? 'not-allowed' : 'text',
                }}
              />

              <div style={{ display: 'flex', gap: 3, marginTop: 10, justifyContent: 'center', flexWrap: 'wrap' }}>
                {challenge.prompt.split('').map((ch: string, i: number) => {
                  const typed = input[i]
                  const match = typed === ch
                  const pending = typed === undefined
                  return (
                    <span key={i} style={{
                      width: 18, height: 24, borderRadius: 3,
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontSize: 12, fontFamily: 'var(--font-mono)', fontWeight: 600,
                      background: pending ? 'var(--surface-2)' : match ? 'var(--success-bg)' : 'var(--danger-bg)',
                      color: pending ? 'var(--foreground-subtle)' : match ? 'var(--success)' : 'var(--danger)',
                      border: `1px solid var(--border)`,
                    }}>{ch === ' ' ? '\u00B7' : ch}</span>
                  )
                })}
              </div>
            </div>
          )}

          {/* Step 3 */}
          {challenge && input.length > 0 && (
            <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 6, padding: 24 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
                <span style={{
                  width: 28, height: 28, borderRadius: '50%', background: 'var(--surface-3)',
                  color: 'var(--foreground)', display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 13, fontWeight: 700,
                }}>3</span>
                <span style={{ fontSize: 14, fontWeight: 600, color: 'var(--foreground)' }}>Verify</span>
              </div>

              <button onClick={handleVerify} disabled={verifying || isExpired} style={{
                width: '100%', padding: 12, borderRadius: 6, border: 'none',
                background: isExpired ? 'var(--surface-3)' : 'var(--foreground)',
                color: isExpired ? 'var(--danger)' : 'var(--background)',
                fontSize: 14, fontWeight: 600,
                cursor: verifying || isExpired ? 'not-allowed' : 'pointer',
                opacity: verifying ? 0.6 : 1,
              }}>
                {verifying ? 'Analyzing behavioral patterns...' : isExpired ? 'Challenge Expired' : 'Verify Identity'}
              </button>

              {lastResult && (
                <div style={{
                  marginTop: 16, padding: 20, borderRadius: 6, textAlign: 'center',
                  background: lastResult.passed ? 'var(--success-bg)' : 'var(--danger-bg)',
                  border: '1px solid var(--border)',
                }}>
                  <div style={{ fontSize: 32, marginBottom: 8 }}>{lastResult.passed ? '\u2713' : '\u2717'}</div>
                  <div style={{ fontSize: 18, fontWeight: 700, color: lastResult.passed ? 'var(--success)' : 'var(--danger)', marginBottom: 4 }}>
                    {lastResult.passed ? 'Verified' : 'Failed'}
                  </div>
                  <div style={{ fontSize: 12, color: 'var(--foreground-subtle)', marginBottom: 14 }}>
                    Behavioral pattern {lastResult.passed ? 'matches baseline' : 'does not match baseline'} — action: {lastResult.action}
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                    <div style={{ padding: 12, background: 'var(--surface)', borderRadius: 6 }}>
                      <div style={{ fontSize: 22, fontWeight: 700, fontFamily: 'var(--font-mono)', color: trustColor(lastResult.confidence) }}>
                        {(lastResult.confidence * 100).toFixed(1)}%
                      </div>
                      <div style={{ fontSize: 10, color: 'var(--foreground-subtle)', marginTop: 2 }}>Confidence</div>
                    </div>
                    <div style={{ padding: 12, background: 'var(--surface)', borderRadius: 6 }}>
                      <div style={{ fontSize: 22, fontWeight: 700, fontFamily: 'var(--font-mono)', color: trustColor(lastResult.drift_score) }}>
                        {(lastResult.drift_score * 100).toFixed(1)}%
                      </div>
                      <div style={{ fontSize: 10, color: 'var(--foreground-subtle)', marginTop: 2 }}>Drift Score</div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right: History */}
        <div>
          <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 6, padding: 24 }}>
            <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--foreground)', marginBottom: 14 }}>Verification History</div>

            {history.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '48px 0' }}>
                <div style={{ fontSize: 13, color: 'var(--foreground-subtle)' }}>No verifications yet</div>
                <div style={{ fontSize: 11, color: 'var(--foreground-subtle)', marginTop: 4 }}>Generate a challenge to begin</div>
              </div>
            ) : (
              <div>
                {[...history].reverse().map(h => (
                  <div key={h.id} style={{ padding: '12px 0', borderBottom: '1px solid var(--border)' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                      <span style={{
                        width: 20, height: 20, borderRadius: '50%',
                        background: h.result.passed ? 'var(--success-bg)' : 'var(--danger-bg)',
                        color: h.result.passed ? 'var(--success)' : 'var(--danger)',
                        display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 10, fontWeight: 700,
                      }}>{h.result.passed ? '\u2713' : '\u2717'}</span>
                      <span style={{ fontSize: 12, fontFamily: 'var(--font-mono)', color: 'var(--foreground-muted)' }}>&quot;{h.prompt}&quot;</span>
                    </div>
                    <div style={{ display: 'flex', gap: 16, paddingLeft: 28 }}>
                      <span style={{ fontSize: 10, color: 'var(--foreground-subtle)' }}>
                        confidence: <span style={{ color: trustColor(h.result.confidence), fontWeight: 600 }}>{(h.result.confidence * 100).toFixed(1)}%</span>
                      </span>
                      <span style={{ fontSize: 10, color: 'var(--foreground-subtle)' }}>
                        drift: <span style={{ color: trustColor(h.result.drift_score), fontWeight: 600 }}>{(h.result.drift_score * 100).toFixed(1)}%</span>
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 6, padding: 24, marginTop: 20 }}>
            <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--foreground)', marginBottom: 12 }}>How KP-Challenge Works</div>
            <div style={{ fontSize: 12, color: 'var(--foreground-muted)', lineHeight: 1.7 }}>
              <p style={{ margin: '0 0 10px' }}><strong>1. Generate:</strong> The server creates a unique challenge phrase tied to a cryptographic token.</p>
              <p style={{ margin: '0 0 10px' }}><strong>2. Type:</strong> As you type, the SDK captures your keystroke timing pattern &mdash; dwell times, flight times, and rhythm.</p>
              <p style={{ margin: '0 0 10px' }}><strong>3. Verify:</strong> The server compares the typing pattern against your baseline. Even with the phrase, others cannot replicate your typing rhythm.</p>
              <p style={{ margin: 0 }}><strong>Result:</strong> Behavioral TOTP &mdash; a one-time password that only <em>you</em> can type correctly.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
