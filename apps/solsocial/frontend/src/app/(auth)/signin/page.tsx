"use client";

/**
 * SolSocial sign-in — multi-method.
 *
 * Tabs: password · magic link · one-time code.
 * OAuth buttons below the divider (Google, GitHub) — unwired until the
 * provider credentials are seeded into the tennetctl vault.
 *
 * Keeps the almanac aesthetic: ember accent, ink typography, no icons,
 * everything paper-grounded.
 */

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";

import { Field, PasswordField, Spinner } from "@/components/fields";
import { tc, setToken } from "@/lib/api";
import type { AuthResponse } from "@/types/api";

type Method = "password" | "magic" | "otp";

// ─── OAuth button (unwired placeholder) ──────────────────────────────────────

function OAuthButton({
  provider,
  onClick,
  disabled,
}: {
  provider: "google" | "github";
  onClick: () => void;
  disabled?: boolean;
}) {
  const label = provider === "google" ? "Google" : "GitHub";
  const mark = provider === "google" ? "G" : "";
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className="flex items-center justify-center gap-2 h-10 px-3 rounded-md border border-[color:var(--rule)] bg-[color:var(--paper-deep)] text-[13px] text-[color:var(--ink-70)] hover:bg-[color:var(--paper)] hover:border-[color:var(--ink-40)] transition-colors disabled:opacity-50"
    >
      <span className="mono text-[11px] tracking-widest text-[color:var(--ink-40)]">{mark || "gh"}</span>
      {label}
    </button>
  );
}

// ─── Method pill ─────────────────────────────────────────────────────────────

function MethodPill({
  label,
  active,
  onClick,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-selected={active}
      role="tab"
      className={`kicker px-3 py-2 border-b-2 transition-colors ${
        active
          ? "border-[color:var(--ember)] text-[color:var(--ink)]"
          : "border-transparent text-[color:var(--ink-40)] hover:text-[color:var(--ink-70)]"
      }`}
    >
      {label}
    </button>
  );
}

// ─── Page ────────────────────────────────────────────────────────────────────

export default function SignInPage() {
  const router = useRouter();
  const params = useSearchParams();
  const nextUrl = params.get("next") || "/";

  const [method, setMethod] = useState<Method>("password");

  // Shared
  const [email, setEmail] = useState("");
  const [emailErr, setEmailErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [banner, setBanner] = useState<string | null>(null);

  // Password
  const [password, setPassword] = useState("");
  const [passErr, setPassErr] = useState<string | null>(null);

  // OTP
  const [otpSent, setOtpSent] = useState(false);
  const [otp, setOtp] = useState("");
  const [otpErr, setOtpErr] = useState<string | null>(null);

  // ── Validators
  function validateEmail(): boolean {
    setEmailErr(null);
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setEmailErr("That doesn't look like a valid email.");
      return false;
    }
    return true;
  }

  // ── Password sign-in
  async function handlePassword(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    setPassErr(null);
    if (!validateEmail()) return;
    if (password.length < 8) {
      setPassErr("Password needs at least 8 characters.");
      return;
    }
    setBusy(true);
    try {
      const data = await tc.post<AuthResponse>("/v1/auth/signin", { email, password });
      setToken(data.token);
      router.push(nextUrl);
    } catch (e) {
      const m = (e as Error).message;
      if (/password/i.test(m)) setPassErr(m);
      else if (/email|user|account/i.test(m)) setEmailErr(m);
      else if (/locked/i.test(m)) setErr("Account is locked. Try again in a few minutes, or reset your password.");
      else setErr(m);
    } finally {
      setBusy(false);
    }
  }

  // ── Magic link
  async function handleMagicLink(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    setBanner(null);
    if (!validateEmail()) return;
    setBusy(true);
    try {
      await tc.post("/v1/auth/magic-link/request", { email, redirect_url: nextUrl });
      setBanner("Check your inbox — we just sent a sign-in link. It expires in 15 minutes.");
    } catch (e) {
      const m = (e as Error).message;
      if (/user|account|email/i.test(m)) setEmailErr(m);
      else setErr(m);
    } finally {
      setBusy(false);
    }
  }

  // ── OTP request
  async function handleOtpRequest(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    if (!validateEmail()) return;
    setBusy(true);
    try {
      await tc.post("/v1/auth/otp/request", { email });
      setOtpSent(true);
      setBanner("Code sent. Check your inbox.");
    } catch (e) {
      const m = (e as Error).message;
      if (/user|account|email/i.test(m)) setEmailErr(m);
      else setErr(m);
    } finally {
      setBusy(false);
    }
  }

  // ── OTP verify
  async function handleOtpVerify(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    setOtpErr(null);
    if (!/^\d{6}$/.test(otp)) {
      setOtpErr("Enter the 6-digit code from your email.");
      return;
    }
    setBusy(true);
    try {
      const data = await tc.post<AuthResponse>("/v1/auth/otp/verify", { email, code: otp });
      setToken(data.token);
      router.push(nextUrl);
    } catch (e) {
      setOtpErr((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  // ── OAuth unwired
  function handleOAuth(provider: "google" | "github") {
    setBanner(`${provider === "google" ? "Google" : "GitHub"} sign-in — configure the OAuth app in tennetctl vault to enable.`);
    setTimeout(() => setBanner(null), 4000);
  }

  function switchMethod(next: Method) {
    setMethod(next);
    setErr(null);
    setBanner(null);
    setEmailErr(null);
    setPassErr(null);
    setOtpErr(null);
    if (next !== "otp") {
      setOtpSent(false);
      setOtp("");
    }
  }

  // ─── Render ─────────────────────────────────────────────────────────

  return (
    <div className="rise">
      <p className="kicker rule mb-3">Return visitor</p>
      <h2 className="display text-[44px] leading-none mb-2">Sign in.</h2>
      <p className="text-[color:var(--ink-70)] mb-7">Continue where you left off.</p>

      {/* ── Tabs ── */}
      <div
        role="tablist"
        aria-label="Sign-in method"
        className="flex gap-1 border-b border-[color:var(--rule)] mb-6"
      >
        <MethodPill label="Password" active={method === "password"} onClick={() => switchMethod("password")} />
        <MethodPill label="Magic link" active={method === "magic"} onClick={() => switchMethod("magic")} />
        <MethodPill label="One-time code" active={method === "otp"} onClick={() => switchMethod("otp")} />
      </div>

      {/* ── Banner ── */}
      {banner && (
        <div className="mb-5 px-3 py-2.5 rounded-md bg-[color:var(--paper-deep)] border border-[color:var(--rule)] text-[12px] text-[color:var(--ink-70)] leading-relaxed">
          {banner}
        </div>
      )}

      {/* ── Password form ── */}
      {method === "password" && (
        <form onSubmit={handlePassword} className="space-y-6" noValidate>
          <Field
            label="Email"
            type="email"
            autoComplete="email"
            autoFocus
            required
            value={email}
            onChange={setEmail}
            placeholder="you@field.example"
            error={emailErr}
          />
          <PasswordField
            label="Password"
            autoComplete="current-password"
            value={password}
            onChange={setPassword}
            error={passErr}
          />
          {err && <div className="mono text-[12px] text-[color:var(--ember-deep)]">× {err}</div>}
          <button className="btn btn-ember w-full" disabled={busy || !email || !password}>
            {busy ? (
              <>
                <Spinner /> Signing in…
              </>
            ) : (
              "Sign in →"
            )}
          </button>
          <div className="flex justify-between items-center">
            <Link href="/forgot-password" className="kicker hover:text-[color:var(--ember-deep)]">
              Forgot password?
            </Link>
            <button
              type="button"
              onClick={() => switchMethod("magic")}
              className="kicker text-[color:var(--ink-40)] hover:text-[color:var(--ember-deep)]"
            >
              Email me a link instead
            </button>
          </div>
        </form>
      )}

      {/* ── Magic link form ── */}
      {method === "magic" && (
        <form onSubmit={handleMagicLink} className="space-y-6" noValidate>
          <p className="text-[13px] text-[color:var(--ink-70)] leading-relaxed">
            We'll email you a one-tap sign-in link. No password needed.
          </p>
          <Field
            label="Email"
            type="email"
            autoComplete="email"
            autoFocus
            required
            value={email}
            onChange={setEmail}
            placeholder="you@field.example"
            error={emailErr}
          />
          {err && <div className="mono text-[12px] text-[color:var(--ember-deep)]">× {err}</div>}
          <button className="btn btn-ember w-full" disabled={busy || !email}>
            {busy ? (
              <>
                <Spinner /> Sending link…
              </>
            ) : (
              "Email me a sign-in link →"
            )}
          </button>
        </form>
      )}

      {/* ── OTP form ── */}
      {method === "otp" && (
        <form onSubmit={otpSent ? handleOtpVerify : handleOtpRequest} className="space-y-6" noValidate>
          <p className="text-[13px] text-[color:var(--ink-70)] leading-relaxed">
            {otpSent
              ? "Enter the 6-digit code we just sent."
              : "We'll email you a 6-digit code. Enter it to continue."}
          </p>
          {!otpSent && (
            <Field
              label="Email"
              type="email"
              autoComplete="email"
              autoFocus
              required
              value={email}
              onChange={setEmail}
              placeholder="you@field.example"
              error={emailErr}
            />
          )}
          {otpSent && (
            <>
              <div className="mono text-[11px] text-[color:var(--ink-40)]">
                Code sent to <span className="text-[color:var(--ink-70)]">{email}</span>
              </div>
              <Field
                label="Verification code"
                type="text"
                autoFocus
                required
                value={otp}
                onChange={(v) => setOtp(v.replace(/\D/g, "").slice(0, 6))}
                placeholder="000000"
                error={otpErr}
                hint="6 digits, expires in 10 minutes"
              />
            </>
          )}
          {err && <div className="mono text-[12px] text-[color:var(--ember-deep)]">× {err}</div>}
          <button
            className="btn btn-ember w-full"
            disabled={busy || (otpSent ? otp.length !== 6 : !email)}
          >
            {busy ? (
              <>
                <Spinner /> {otpSent ? "Verifying…" : "Sending code…"}
              </>
            ) : otpSent ? (
              "Verify & sign in →"
            ) : (
              "Send me a code →"
            )}
          </button>
          {otpSent && (
            <button
              type="button"
              onClick={() => {
                setOtpSent(false);
                setOtp("");
                setBanner(null);
              }}
              className="kicker text-[color:var(--ink-40)] hover:text-[color:var(--ember-deep)]"
            >
              ← Use a different email
            </button>
          )}
        </form>
      )}

      {/* ── Divider + OAuth ── */}
      <div className="my-8 flex items-center gap-3">
        <span className="flex-1 h-px bg-[color:var(--rule)]" />
        <span className="kicker text-[color:var(--ink-40)]">or continue with</span>
        <span className="flex-1 h-px bg-[color:var(--rule)]" />
      </div>

      <div className="grid grid-cols-2 gap-3">
        <OAuthButton provider="google" onClick={() => handleOAuth("google")} />
        <OAuthButton provider="github" onClick={() => handleOAuth("github")} />
      </div>

      <p className="mt-8 text-sm text-[color:var(--ink-70)]">
        First time here?{" "}
        <Link
          href="/signup"
          className="text-[color:var(--ember-deep)] underline underline-offset-4 decoration-[color:var(--ember)]"
        >
          Start your almanac
        </Link>
      </p>
    </div>
  );
}
