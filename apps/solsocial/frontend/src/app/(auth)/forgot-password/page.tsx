"use client";
import { useState } from "react";
import Link from "next/link";
import { Field, Spinner } from "@/components/fields";

/**
 * Stub flow for now: we collect an email, show a success screen, and
 * rely on tennetctl's future email wiring to actually deliver a link.
 * The UI path is the final one — swapping in the API call is a one-liner
 * once tennetctl exposes /v1/auth/password-reset.
 */
export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setErr("That doesn't look like a valid email.");
      return;
    }
    setBusy(true);
    try {
      // Intentionally no-op today. We tell users to sit tight.
      await new Promise(r => setTimeout(r, 400));
      setSent(true);
    } catch (e) {
      setErr((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  if (sent) {
    return (
      <div className="rise">
        <p className="kicker rule mb-3">Check your inbox</p>
        <h2 className="display text-[42px] leading-none mb-3">
          If that email is on file…
        </h2>
        <p className="text-[color:var(--ink-70)] mb-8">
          …we'll send a reset link shortly. Email delivery is still being wired
          — in the meantime, contact your administrator to reset your password
          directly.
        </p>
        <Link href="/signin" className="btn">← back to sign in</Link>
      </div>
    );
  }

  return (
    <div className="rise">
      <p className="kicker rule mb-3">Forgot your password?</p>
      <h2 className="display text-[42px] leading-none mb-3">
        Let's <span className="display-italic">fix</span> that.
      </h2>
      <p className="text-[color:var(--ink-70)] mb-10">
        Enter the email on your account and we'll send a reset link.
      </p>

      <form onSubmit={onSubmit} className="space-y-7" noValidate>
        <Field
          label="Email" type="email" autoComplete="email" autoFocus required
          value={email} onChange={setEmail}
          placeholder="you@field.example"
          error={err}
        />
        <button className="btn btn-ember w-full" disabled={busy || !email}>
          {busy ? <><Spinner /> Sending…</> : "Send reset link →"}
        </button>
      </form>

      <p className="mt-8 text-sm text-[color:var(--ink-70)]">
        Remembered it?{" "}
        <Link href="/signin" className="text-[color:var(--ember-deep)] underline underline-offset-4 decoration-[color:var(--ember)]">
          Back to sign in
        </Link>
      </p>
    </div>
  );
}
