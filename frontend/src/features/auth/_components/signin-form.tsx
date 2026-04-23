"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";

import { OAuthButtons } from "@/features/auth/_components/oauth-buttons";
import {
  useMagicLinkRequest,
  useOtpRequest,
  useOtpVerify,
  usePasskeyAuthBegin,
  usePasskeyAuthComplete,
  useSignin,
} from "@/features/auth/hooks/use-auth";

type Tab = "password" | "magic-link" | "otp" | "passkey";

export function SignInForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const next = searchParams.get("next") ?? "/";

  const [tab, setTab] = useState<Tab>("password");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [magicSent, setMagicSent] = useState(false);
  const [otpSent, setOtpSent] = useState(false);
  const [otpCode, setOtpCode] = useState("");

  const [passkeyError, setPasskeyError] = useState<string | null>(null);
  const [passkeyLoading, setPasskeyLoading] = useState(false);

  const signin = useSignin();
  const magicRequest = useMagicLinkRequest();
  const otpRequest = useOtpRequest();
  const otpVerify = useOtpVerify();
  const passkeyAuthBegin = usePasskeyAuthBegin();
  const passkeyAuthComplete = usePasskeyAuthComplete();

  const inputCls = "w-full rounded border bg-[var(--bg-base)] px-3 py-2 text-[13px] text-[var(--text-primary)] border-[var(--border)] placeholder:text-[var(--text-muted)] focus:outline-none focus:border-[var(--accent)] focus:ring-1 focus:ring-[var(--accent)] transition-all duration-150 hover:border-[var(--border-bright)]";
  const submitCls = "mt-2 w-full rounded border border-[var(--accent)] bg-[var(--accent)] px-3 py-2 text-[13px] font-semibold text-white transition-all duration-150 hover:bg-[var(--accent-hover)] hover:border-[var(--accent-hover)] disabled:opacity-40 shadow-[0_0_12px_rgba(45,126,247,0.25)]";

  return (
    <>
      {/* Tab bar */}
      <div
        className="mb-5 flex gap-px rounded overflow-hidden border"
        style={{ borderColor: "var(--border)", background: "var(--bg-base)" }}
        data-testid="signin-tabs"
      >
        {(["password", "magic-link", "otp", "passkey"] as Tab[]).map((t) => (
          <button
            key={t}
            type="button"
            data-testid={`tab-${t}`}
            onClick={() => { setTab(t); setMagicSent(false); setOtpSent(false); setOtpCode(""); setPasskeyError(null); }}
            className="flex-1 whitespace-nowrap px-2 py-1.5 text-[10px] font-semibold uppercase tracking-wider transition-all duration-100"
            style={
              tab === t
                ? {
                    background: "var(--accent-muted)",
                    color: "var(--accent-hover)",
                    borderBottom: "2px solid var(--accent)",
                  }
                : {
                    color: "var(--text-muted)",
                    background: "transparent",
                  }
            }
          >
            {t === "password" ? "Password" : t === "magic-link" ? "Magic Link" : t === "otp" ? "OTP" : "Passkey"}
          </button>
        ))}
      </div>

      {tab === "password" && (
        <form
          className="flex flex-col gap-3"
          data-testid="signin-form"
          onSubmit={async (e) => {
            e.preventDefault();
            await signin.mutateAsync(
              { email, password },
              { onSuccess: () => router.replace(next) }
            );
          }}
        >
          <label className="flex flex-col gap-1.5 text-[11px] font-semibold uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>
            Email
            <input type="email" required autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} className={inputCls} data-testid="signin-email" />
          </label>
          <label className="flex flex-col gap-1.5 text-[11px] font-semibold uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>
            Password
            <input type="password" required minLength={1} autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} className={inputCls} data-testid="signin-password" />
          </label>
          {signin.error ? (
            <p className="text-[11px]" style={{ color: "var(--danger)" }} data-testid="signin-error">
              {signin.error.message}
            </p>
          ) : null}
          <button type="submit" disabled={signin.isPending} data-testid="signin-submit" className={submitCls}>
            {signin.isPending ? "Signing in…" : "Sign in"}
          </button>
          <Link href="/auth/forgot-password" className="text-center text-[11px] transition-colors hover:text-[var(--text-primary)]" style={{ color: "var(--text-muted)" }} data-testid="forgot-password-link">
            Forgot your password?
          </Link>
        </form>
      )}

      {tab === "magic-link" && (
        <div className="flex flex-col gap-3" data-testid="magic-link-form">
          {magicSent ? (
            <div className="rounded border p-4" style={{ borderColor: "rgba(0,196,122,0.3)", background: "var(--success-muted)" }} data-testid="magic-link-sent">
              <p className="text-[13px] font-semibold" style={{ color: "var(--success)" }}>Check your inbox</p>
              <p className="mt-1 text-[11px] leading-relaxed" style={{ color: "var(--text-muted)" }}>
                If that email is registered, a sign-in link is on its way. It expires in 10 minutes.
              </p>
              <button type="button" onClick={() => setMagicSent(false)} className="mt-3 text-[11px] underline transition-colors" style={{ color: "var(--success)" }}>
                Send another link
              </button>
            </div>
          ) : (
            <form className="flex flex-col gap-3" onSubmit={async (e) => { e.preventDefault(); await magicRequest.mutateAsync({ email, redirect_url: `${window.location.origin}/auth/magic-link/callback` }, { onSuccess: () => setMagicSent(true) }); }}>
              <label className="flex flex-col gap-1.5 text-[11px] font-semibold uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>
                Email
                <input type="email" required autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} className={inputCls} data-testid="magic-link-email" />
              </label>
              {magicRequest.error ? (<p className="text-[11px]" style={{ color: "var(--danger)" }} data-testid="magic-link-error">{magicRequest.error.message}</p>) : null}
              <button type="submit" disabled={magicRequest.isPending} data-testid="magic-link-submit" className={submitCls}>
                {magicRequest.isPending ? "Sending…" : "Send sign-in link"}
              </button>
            </form>
          )}
        </div>
      )}

      {tab === "otp" && (
        <div className="flex flex-col gap-3" data-testid="otp-form">
          {!otpSent ? (
            <form className="flex flex-col gap-3" onSubmit={async (e) => { e.preventDefault(); await otpRequest.mutateAsync({ email }, { onSuccess: () => setOtpSent(true) }); }}>
              <label className="flex flex-col gap-1.5 text-[11px] font-semibold uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>
                Email
                <input type="email" required autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} className={inputCls} data-testid="otp-email" />
              </label>
              <button type="submit" disabled={otpRequest.isPending} data-testid="otp-send-submit" className={submitCls}>
                {otpRequest.isPending ? "Sending…" : "Send code"}
              </button>
            </form>
          ) : (
            <form className="flex flex-col gap-3" onSubmit={async (e) => { e.preventDefault(); await otpVerify.mutateAsync({ email, code: otpCode }, { onSuccess: () => router.replace(next) }); }}>
              <p className="text-[11px] leading-relaxed" style={{ color: "var(--text-muted)" }}>
                A 6-digit code was sent to <strong style={{ color: "var(--text-secondary)" }}>{email}</strong>.
              </p>
              <label className="flex flex-col gap-1.5 text-[11px] font-semibold uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>
                Code
                <input type="text" required inputMode="numeric" pattern="[0-9]{6}" maxLength={6} placeholder="000000" value={otpCode} onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, ""))} className={`${inputCls} text-center text-xl tracking-[0.4em] font-mono`} data-testid="otp-code-input" autoFocus />
              </label>
              {otpVerify.error ? (<p className="text-[11px]" style={{ color: "var(--danger)" }} data-testid="otp-error">{otpVerify.error.message}</p>) : null}
              <button type="submit" disabled={otpVerify.isPending || otpCode.length < 6} data-testid="otp-verify-submit" className={submitCls}>
                {otpVerify.isPending ? "Verifying…" : "Sign in"}
              </button>
              <button type="button" onClick={() => { setOtpSent(false); setOtpCode(""); }} className="text-[11px] underline transition-colors" style={{ color: "var(--text-muted)" }} data-testid="otp-resend">
                Send another code
              </button>
            </form>
          )}
        </div>
      )}

      {tab === "passkey" && (
        <div className="flex flex-col gap-3" data-testid="passkey-signin-form">
          <form
            className="flex flex-col gap-3"
            onSubmit={async (e) => {
              e.preventDefault();
              setPasskeyError(null);
              setPasskeyLoading(true);
              try {
                const beginResult = await passkeyAuthBegin.mutateAsync({ email });
                const options = JSON.parse(beginResult.options_json);
                const credential = await (navigator.credentials as unknown as { get(opts: unknown): Promise<unknown> }).get({
                  publicKey: {
                    ...options,
                    challenge: Uint8Array.from(atob(options.challenge.replace(/-/g, "+").replace(/_/g, "/")), (c) => c.charCodeAt(0)),
                    allowCredentials: (options.allowCredentials ?? []).map((c: { id: string; type: string }) => ({
                      ...c,
                      id: Uint8Array.from(atob(c.id.replace(/-/g, "+").replace(/_/g, "/")), (ch) => ch.charCodeAt(0)),
                    })),
                  },
                });
                await passkeyAuthComplete.mutateAsync({
                  challenge_id: beginResult.challenge_id,
                  credential_json: JSON.stringify(credential),
                });
                router.replace(next);
              } catch (err) {
                setPasskeyError(err instanceof Error ? err.message : "Sign-in failed.");
              } finally {
                setPasskeyLoading(false);
              }
            }}
          >
            <label className="flex flex-col gap-1.5 text-[11px] font-semibold uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>
              Email
              <input type="email" required autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} className={inputCls} data-testid="passkey-email" />
            </label>
            {passkeyError ? (<p className="text-[11px]" style={{ color: "var(--danger)" }} data-testid="passkey-signin-error">{passkeyError}</p>) : null}
            <button type="submit" disabled={passkeyLoading} data-testid="passkey-signin-submit" className={submitCls}>
              {passkeyLoading ? "Connecting…" : "Sign in with passkey"}
            </button>
          </form>
        </div>
      )}

      <div className="my-4 flex items-center gap-3 text-[10px] uppercase tracking-widest" style={{ color: "var(--text-muted)" }}>
        <span className="h-px flex-1" style={{ background: "var(--border)" }} />
        or
        <span className="h-px flex-1" style={{ background: "var(--border)" }} />
      </div>
      <OAuthButtons />

      <div className="my-4 flex items-center gap-3 text-[10px] uppercase tracking-widest" style={{ color: "var(--text-muted)" }}>
        <span className="h-px flex-1" style={{ background: "var(--border)" }} />
        SSO
        <span className="h-px flex-1" style={{ background: "var(--border)" }} />
      </div>
      <SSOEntry />

      <p className="mt-5 text-[12px]" style={{ color: "var(--text-muted)" }}>
        New here?{" "}
        <Link
          href={`/auth/signup${next !== "/" ? `?next=${encodeURIComponent(next)}` : ""}`}
          className="font-semibold transition-colors hover:text-[var(--text-primary)]"
          style={{ color: "var(--accent-hover)" }}
          data-testid="signin-to-signup"
        >
          Create an account →
        </Link>
      </p>
    </>
  );
}

function SSOEntry() {
  const [slug, setSlug] = useState("");
  function handleSSO(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (slug.trim()) {
      window.location.href = `/v1/auth/oidc/${encodeURIComponent(slug.trim())}/initiate`;
    }
  }
  return (
    <form onSubmit={handleSSO} className="flex gap-2">
      <input
        value={slug}
        onChange={(e) => setSlug(e.target.value)}
        placeholder="org-slug"
        className="flex-1 rounded border bg-[var(--bg-base)] px-3 py-1.5 text-[12px] text-[var(--text-primary)] border-[var(--border)] placeholder:text-[var(--text-muted)] focus:outline-none focus:border-[var(--accent)] focus:ring-1 focus:ring-[var(--accent)] transition-all duration-150 font-mono"
        data-testid="sso-org-slug"
      />
      <button
        type="submit"
        disabled={!slug.trim()}
        className="rounded border px-3 py-1.5 text-[11px] font-semibold uppercase tracking-wider transition-all duration-100 disabled:opacity-40"
        style={{
          borderColor: "var(--border-bright)",
          color: "var(--text-secondary)",
          background: "var(--bg-elevated)",
        }}
        data-testid="sso-continue"
      >
        Go
      </button>
    </form>
  );
}
