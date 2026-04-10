'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { useAuth } from '@/components/auth-provider'

const SECURITY_QUESTIONS = [
  "What is your mother's maiden name?",
  "What was the name of your first pet?",
  "What city were you born in?",
  "What was the name of your primary school?",
  "What is your oldest sibling's middle name?",
  "What street did you grow up on?",
  "What was the make of your first car?",
  "What was your childhood nickname?",
]

type FormData = {
  username: string
  email: string
  password: string
  confirm: string
  mobile_number: string
  mpin: string
  mpin_confirm: string
  q1: string; a1: string
  q2: string; a2: string
  q3: string; a3: string
}

const EMPTY: FormData = {
  username: '', email: '', password: '', confirm: '',
  mobile_number: '', mpin: '', mpin_confirm: '',
  q1: SECURITY_QUESTIONS[0], a1: '',
  q2: SECURITY_QUESTIONS[1], a2: '',
  q3: SECURITY_QUESTIONS[2], a3: '',
}

const STEPS = ['Credentials', 'Mobile & MPIN', 'Security Questions']

export default function SignupPage() {
  const { signup } = useAuth()
  const router = useRouter()
  const [step, setStep] = useState(0)
  const [form, setForm] = useState<FormData>(EMPTY)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  function set(field: keyof FormData, value: string) {
    setForm(f => ({ ...f, [field]: value }))
  }

  function validateStep(): string {
    if (step === 0) {
      if (!form.username.trim() || form.username.trim().length < 3) return 'Username must be at least 3 characters.'
      if (!form.email.includes('@')) return 'Enter a valid email address.'
      if (form.password.length < 6) return 'Password must be at least 6 characters.'
      if (form.password !== form.confirm) return 'Passwords do not match.'
    }
    if (step === 1) {
      if (!form.mobile_number.trim() || form.mobile_number.trim().length < 7) return 'Enter a valid mobile number.'
      if (!/^\d{4,6}$/.test(form.mpin)) return 'MPIN must be 4–6 digits.'
      if (form.mpin !== form.mpin_confirm) return 'MPINs do not match.'
    }
    if (step === 2) {
      if (!form.a1.trim()) return 'Answer question 1.'
      if (!form.a2.trim()) return 'Answer question 2.'
      if (!form.a3.trim()) return 'Answer question 3.'
      if (form.q1 === form.q2 || form.q1 === form.q3 || form.q2 === form.q3) return 'Choose 3 different security questions.'
    }
    return ''
  }

  function next() {
    const err = validateStep()
    if (err) { setError(err); return }
    setError('')
    setStep(s => s + 1)
  }

  async function submit() {
    const err = validateStep()
    if (err) { setError(err); return }
    setError('')
    setLoading(true)
    try {
      await signup({
        username: form.username.trim().toLowerCase(),
        email: form.email.trim(),
        password: form.password,
        mobile_number: form.mobile_number.trim(),
        mpin: form.mpin,
        security_questions: [
          { question: form.q1, answer: form.a1.trim() },
          { question: form.q2, answer: form.a2.trim() },
          { question: form.q3, answer: form.a3.trim() },
        ],
      })
      router.push('/')
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Signup failed.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{
      minHeight: '100vh', display: 'flex', alignItems: 'center',
      justifyContent: 'center', background: 'var(--background)', padding: 24,
    }}>
      <div style={{ width: '100%', maxWidth: 480 }}>
        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: 28 }}>
          <div style={{
            width: 44, height: 44, borderRadius: 10,
            background: 'var(--foreground)',
            display: 'inline-flex', alignItems: 'center', justifyContent: 'center', marginBottom: 14,
          }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--background)" strokeWidth="2">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>
            </svg>
          </div>
          <h1 style={{ margin: '0 0 4px', fontSize: 22, fontWeight: 700, color: 'var(--foreground)' }}>Create account</h1>
          <p style={{ margin: 0, fontSize: 13, color: 'var(--foreground-muted)' }}>kbio SDK demo — behavioral biometrics</p>
        </div>

        {/* Step indicator */}
        <div style={{ display: 'flex', alignItems: 'center', marginBottom: 24, gap: 0 }}>
          {STEPS.map((label, i) => (
            <div key={i} style={{ display: 'flex', alignItems: 'center', flex: 1 }}>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', flex: 1 }}>
                <div style={{
                  width: 28, height: 28, borderRadius: '50%',
                  background: i <= step ? 'var(--foreground)' : 'var(--surface)',
                  border: `2px solid ${i <= step ? 'var(--foreground)' : 'var(--border)'}`,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  color: i <= step ? 'var(--background)' : 'var(--foreground-subtle)',
                  fontSize: 12, fontWeight: 700, transition: 'all 0.2s',
                }}>{i < step ? '✓' : i + 1}</div>
                <span style={{ fontSize: 10, marginTop: 4, color: i === step ? 'var(--foreground)' : 'var(--foreground-subtle)', fontWeight: i === step ? 600 : 400 }}>
                  {label}
                </span>
              </div>
              {i < STEPS.length - 1 && (
                <div style={{ height: 2, flex: 1, background: i < step ? 'var(--foreground)' : 'var(--border)', margin: '0 4px', marginBottom: 20 }} />
              )}
            </div>
          ))}
        </div>

        {/* Card */}
        <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, padding: 32 }}>

          {step === 0 && (
            <>
              <Field label="Username" required>
                <Input type="text" value={form.username} onChange={v => set('username', v)} placeholder="e.g. alice" autoComplete="username" />
              </Field>
              <Field label="Email" required>
                <Input type="email" value={form.email} onChange={v => set('email', v)} placeholder="alice@example.com" autoComplete="email" />
              </Field>
              <Field label="Password" required>
                <Input type="password" value={form.password} onChange={v => set('password', v)} placeholder="At least 6 characters" autoComplete="new-password" />
              </Field>
              <Field label="Confirm password" required style={{ marginBottom: 0 }}>
                <Input type="password" value={form.confirm} onChange={v => set('confirm', v)} placeholder="Repeat password" autoComplete="new-password" />
              </Field>
            </>
          )}

          {step === 1 && (
            <>
              <Field label="Mobile number" required>
                <Input type="tel" value={form.mobile_number} onChange={v => set('mobile_number', v)} placeholder="+1 555 000 0000" autoComplete="tel" />
              </Field>
              <Field label="MPIN" required hint="4–6 digit PIN used for identity challenges">
                <Input type="password" value={form.mpin} onChange={v => set('mpin', v.replace(/\D/g, '').slice(0, 6))} placeholder="4–6 digits" autoComplete="off" inputMode="numeric" />
              </Field>
              <Field label="Confirm MPIN" required style={{ marginBottom: 0 }}>
                <Input type="password" value={form.mpin_confirm} onChange={v => set('mpin_confirm', v.replace(/\D/g, '').slice(0, 6))} placeholder="Repeat MPIN" autoComplete="off" inputMode="numeric" />
              </Field>
            </>
          )}

          {step === 2 && (
            <>
              {([1, 2, 3] as const).map(n => (
                <div key={n} style={{ marginBottom: n < 3 ? 20 : 0 }}>
                  <Field label={`Security question ${n}`} required>
                    <select
                      value={form[`q${n}` as 'q1' | 'q2' | 'q3']}
                      onChange={e => set(`q${n}` as keyof FormData, e.target.value)}
                      style={{ ...inputStyle, appearance: 'none' }}
                    >
                      {SECURITY_QUESTIONS.map(q => <option key={q} value={q}>{q}</option>)}
                    </select>
                  </Field>
                  <Field label="Your answer" required style={{ marginBottom: 0 }}>
                    <Input
                      type="text"
                      value={form[`a${n}` as 'a1' | 'a2' | 'a3']}
                      onChange={v => set(`a${n}` as keyof FormData, v)}
                      placeholder="Your answer"
                      autoComplete="off"
                    />
                  </Field>
                </div>
              ))}
            </>
          )}

          {error && (
            <div style={{
              marginTop: 16, padding: '10px 14px', borderRadius: 6,
              background: '#fee2e2', border: '1px solid #ef4444',
              color: '#dc2626', fontSize: 13,
            }}>{error}</div>
          )}

          {/* Navigation */}
          <div style={{ display: 'flex', gap: 10, marginTop: 24 }}>
            {step > 0 && (
              <button onClick={() => { setError(''); setStep(s => s - 1) }} style={{
                flex: 1, padding: 11, borderRadius: 6,
                border: '1px solid var(--border)', background: 'var(--surface)',
                color: 'var(--foreground)', fontSize: 14, fontWeight: 500, cursor: 'pointer',
              }}>Back</button>
            )}
            {step < 2 ? (
              <button onClick={next} style={{
                flex: 1, padding: 11, borderRadius: 6, border: 'none',
                background: 'var(--foreground)', color: 'var(--background)',
                fontSize: 14, fontWeight: 600, cursor: 'pointer',
              }}>Next</button>
            ) : (
              <button onClick={submit} disabled={loading} style={{
                flex: 1, padding: 11, borderRadius: 6, border: 'none',
                background: loading ? 'var(--foreground-subtle)' : 'var(--foreground)',
                color: 'var(--background)', fontSize: 14, fontWeight: 600,
                cursor: loading ? 'not-allowed' : 'pointer',
              }}>
                {loading ? 'Creating account…' : 'Create account'}
              </button>
            )}
          </div>
        </div>

        <p style={{ textAlign: 'center', marginTop: 18, fontSize: 13, color: 'var(--foreground-muted)' }}>
          Already have an account?{' '}
          <Link href="/login" style={{ color: 'var(--foreground)', fontWeight: 600 }}>Sign in</Link>
        </p>
      </div>
    </div>
  )
}

// ── Small reusable sub-components ──────────────────────────────────────────

function Field({
  label, children, required, hint, style,
}: {
  label: string
  children: React.ReactNode
  required?: boolean
  hint?: string
  style?: React.CSSProperties
}) {
  return (
    <div style={{ marginBottom: 18, ...style }}>
      <label style={{
        display: 'block', marginBottom: 5, fontSize: 11, fontWeight: 600,
        color: 'var(--foreground-muted)', textTransform: 'uppercase', letterSpacing: '0.04em',
      }}>
        {label}{required && <span style={{ color: 'var(--danger, #ef4444)', marginLeft: 2 }}>*</span>}
      </label>
      {hint && <p style={{ margin: '0 0 6px', fontSize: 11, color: 'var(--foreground-subtle)' }}>{hint}</p>}
      {children}
    </div>
  )
}

const inputStyle: React.CSSProperties = {
  width: '100%', padding: '10px 14px', borderRadius: 6,
  border: '1px solid var(--border)', background: 'var(--surface)',
  color: 'var(--foreground)', fontSize: 14, outline: 'none', boxSizing: 'border-box',
}

function Input({
  type, value, onChange, placeholder, autoComplete, inputMode,
}: {
  type: string
  value: string
  onChange: (v: string) => void
  placeholder?: string
  autoComplete?: string
  inputMode?: React.HTMLAttributes<HTMLInputElement>['inputMode']
}) {
  return (
    <input
      type={type}
      value={value}
      onChange={e => onChange(e.target.value)}
      placeholder={placeholder}
      autoComplete={autoComplete}
      inputMode={inputMode}
      style={inputStyle}
    />
  )
}
