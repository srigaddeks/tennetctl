"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { tc, setToken } from "@/lib/api";
import type { AuthResponse } from "@/types/api";
import { Field, PasswordField, Spinner } from "@/components/fields";

export default function SignUpPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [nameErr, setNameErr] = useState<string | null>(null);
  const [emailErr, setEmailErr] = useState<string | null>(null);
  const [passErr, setPassErr] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErr(null); setNameErr(null); setEmailErr(null); setPassErr(null);

    if (!name.trim()) { setNameErr("Tell us what to call you."); return; }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setEmailErr("That doesn't look like a valid email."); return;
    }
    if (password.length < 8) {
      setPassErr("At least 8 characters, please."); return;
    }

    setBusy(true);
    try {
      const data = await tc.post<AuthResponse>("/v1/auth/signup", {
        email, password, display_name: name.trim(),
      });
      setToken(data.token);
      setDone(true);
      setTimeout(() => router.push("/"), 500);
    } catch (e) {
      const m = (e as Error).message;
      if (/email|already/i.test(m)) setEmailErr(m);
      else if (/password/i.test(m)) setPassErr(m);
      else setErr(m);
    } finally {
      setBusy(false);
    }
  }

  if (done) {
    return (
      <div className="rise text-center py-10">
        <p className="kicker rule mb-3">Welcome aboard</p>
        <h2 className="display text-[44px] leading-none mb-2">
          <span className="display-italic">almanac</span> opened.
        </h2>
        <p className="text-[color:var(--ink-70)]">Minting your workspace…</p>
      </div>
    );
  }

  return (
    <div className="rise">
      <p className="kicker rule mb-3">New subscriber</p>
      <h2 className="display text-[44px] leading-none mb-2">
        Start your <span className="display-italic">almanac</span>.
      </h2>
      <p className="text-[color:var(--ink-70)] mb-10">
        A workspace is minted for you the moment you sign up.
      </p>

      <form onSubmit={onSubmit} className="space-y-7" noValidate>
        <Field
          label="What should we call you?" autoComplete="name" autoFocus required
          value={name} onChange={setName}
          placeholder="J. Appleseed" error={nameErr}
        />
        <Field
          label="Email" type="email" autoComplete="email" required
          value={email} onChange={setEmail}
          placeholder="you@field.example" error={emailErr}
        />
        <PasswordField
          label="Password" autoComplete="new-password"
          value={password} onChange={setPassword}
          minLength={8} showStrength
          hint="At least 8 characters. Longer + mixed = stronger."
          error={passErr}
        />

        {err && <div className="mono text-[12px] text-[color:var(--ember-deep)]">× {err}</div>}

        <button className="btn btn-ember w-full" disabled={busy || !name || !email || !password}>
          {busy ? <><Spinner /> Minting your workspace…</> : "Create account →"}
        </button>

        <p className="text-[11px] text-[color:var(--ink-40)] text-center">
          By signing up you agree to behave kindly and post on occasion.
        </p>
      </form>

      <p className="mt-8 text-sm text-[color:var(--ink-70)]">
        Already enrolled?{" "}
        <Link href="/signin" className="text-[color:var(--ember-deep)] underline underline-offset-4 decoration-[color:var(--ember)]">
          Sign in
        </Link>
      </p>
    </div>
  );
}
