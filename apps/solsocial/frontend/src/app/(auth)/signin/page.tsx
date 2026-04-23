"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { tc, setToken } from "@/lib/api";
import type { AuthResponse } from "@/types/api";
import { Field, PasswordField, Spinner } from "@/components/fields";

export default function SignInPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [emailErr, setEmailErr] = useState<string | null>(null);
  const [passErr, setPassErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErr(null); setEmailErr(null); setPassErr(null);

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setEmailErr("Looks like that's not a valid email."); return;
    }
    if (password.length < 8) {
      setPassErr("Password needs at least 8 characters."); return;
    }

    setBusy(true);
    try {
      const data = await tc.post<AuthResponse>("/v1/auth/signin", { email, password });
      setToken(data.token);
      router.push("/");
    } catch (e) {
      const m = (e as Error).message;
      if (/password/i.test(m)) setPassErr(m);
      else if (/email|user|account/i.test(m)) setEmailErr(m);
      else setErr(m);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="rise">
      <p className="kicker rule mb-3">Return visitor</p>
      <h2 className="display text-[44px] leading-none mb-2">Sign in.</h2>
      <p className="text-[color:var(--ink-70)] mb-10">Continue where you left off.</p>

      <form onSubmit={onSubmit} className="space-y-7" noValidate>
        <Field
          label="Email" type="email" autoComplete="email" autoFocus required
          value={email} onChange={setEmail}
          placeholder="you@field.example" error={emailErr}
        />
        <PasswordField
          label="Password" autoComplete="current-password"
          value={password} onChange={setPassword}
          error={passErr}
        />

        {err && <div className="mono text-[12px] text-[color:var(--ember-deep)]">× {err}</div>}

        <button className="btn btn-ember w-full" disabled={busy || !email || !password}>
          {busy ? <><Spinner /> Signing in…</> : "Sign in →"}
        </button>

        <div className="flex justify-between items-center">
          <Link href="/forgot-password" className="kicker hover:text-[color:var(--ember-deep)]">
            Forgot password?
          </Link>
          <span className="mono text-[10px] text-[color:var(--ink-40)]">1 / 1</span>
        </div>
      </form>

      <p className="mt-8 text-sm text-[color:var(--ink-70)]">
        First time here?{" "}
        <Link href="/signup" className="text-[color:var(--ember-deep)] underline underline-offset-4 decoration-[color:var(--ember)]">
          Start your almanac
        </Link>
      </p>
    </div>
  );
}
