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

  return (
    <>
      {/* Tab bar */}
      <div className="mb-4 flex gap-1 rounded-lg bg-zinc-100 p-1 dark:bg-zinc-800" data-testid="signin-tabs">
        {(["password", "magic-link", "otp", "passkey"] as Tab[]).map((t) => (
          <button
            key={t}
            type="button"
            data-testid={`tab-${t}`}
            onClick={() => { setTab(t); setMagicSent(false); setOtpSent(false); setOtpCode(""); setPasskeyError(null); }}
            className={[
              "flex-1 whitespace-nowrap rounded-md px-2 py-1.5 text-[11px] font-medium transition",
              tab === t
                ? "bg-white shadow-sm dark:bg-zinc-700"
                : "text-zinc-500 hover:text-zinc-700 dark:hover:text-zinc-300",
            ].join(" ")}
          >
            {t === "password" ? "Password" : t === "magic-link" ? "Magic Link" : t === "otp" ? "OTP Code" : "Passkey"}
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
          <label className="flex flex-col gap-1 text-xs font-medium">
            Email
            <input
              type="email"
              required
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="rounded-md border border-zinc-200 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-900"
              data-testid="signin-email"
            />
          </label>
          <label className="flex flex-col gap-1 text-xs font-medium">
            Password
            <input
              type="password"
              required
              minLength={1}
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="rounded-md border border-zinc-200 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-900"
              data-testid="signin-password"
            />
          </label>
          {signin.error ? (
            <p className="text-xs text-red-600" data-testid="signin-error">
              {signin.error.message}
            </p>
          ) : null}
          <button
            type="submit"
            disabled={signin.isPending}
            data-testid="signin-submit"
            className="mt-2 rounded-md bg-zinc-900 px-3 py-2 text-sm font-medium text-white transition hover:bg-zinc-800 disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-200"
          >
            {signin.isPending ? "Signing in…" : "Sign in"}
          </button>
          <Link
            href="/auth/forgot-password"
            className="text-center text-xs text-zinc-500 hover:text-zinc-700 dark:hover:text-zinc-300"
            data-testid="forgot-password-link"
          >
            Forgot your password?
          </Link>
        </form>
      )}

      {tab === "magic-link" && (
        <div className="flex flex-col gap-3" data-testid="magic-link-form">
          {magicSent ? (
            <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-4 dark:border-emerald-800 dark:bg-emerald-950" data-testid="magic-link-sent">
              <p className="text-sm font-medium text-emerald-800 dark:text-emerald-200">Check your inbox</p>
              <p className="mt-1 text-xs text-emerald-700 dark:text-emerald-300">
                If that email is registered, a sign-in link is on its way. It expires in 10 minutes.
              </p>
              <button
                type="button"
                onClick={() => setMagicSent(false)}
                className="mt-3 text-xs text-emerald-600 underline dark:text-emerald-400"
              >
                Send another link
              </button>
            </div>
          ) : (
            <form
              className="flex flex-col gap-3"
              onSubmit={async (e) => {
                e.preventDefault();
                await magicRequest.mutateAsync(
                  { email, redirect_url: `${window.location.origin}/auth/magic-link/callback` },
                  { onSuccess: () => setMagicSent(true) }
                );
              }}
            >
              <label className="flex flex-col gap-1 text-xs font-medium">
                Email
                <input
                  type="email"
                  required
                  autoComplete="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="rounded-md border border-zinc-200 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-900"
                  data-testid="magic-link-email"
                />
              </label>
              {magicRequest.error ? (
                <p className="text-xs text-red-600" data-testid="magic-link-error">
                  {magicRequest.error.message}
                </p>
              ) : null}
              <button
                type="submit"
                disabled={magicRequest.isPending}
                data-testid="magic-link-submit"
                className="mt-2 rounded-md bg-zinc-900 px-3 py-2 text-sm font-medium text-white transition hover:bg-zinc-800 disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-200"
              >
                {magicRequest.isPending ? "Sending…" : "Send sign-in link"}
              </button>
            </form>
          )}
        </div>
      )}

      {tab === "otp" && (
        <div className="flex flex-col gap-3" data-testid="otp-form">
          {!otpSent ? (
            <form
              className="flex flex-col gap-3"
              onSubmit={async (e) => {
                e.preventDefault();
                await otpRequest.mutateAsync(
                  { email },
                  { onSuccess: () => setOtpSent(true) }
                );
              }}
            >
              <label className="flex flex-col gap-1 text-xs font-medium">
                Email
                <input
                  type="email"
                  required
                  autoComplete="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="rounded-md border border-zinc-200 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-900"
                  data-testid="otp-email"
                />
              </label>
              <button
                type="submit"
                disabled={otpRequest.isPending}
                data-testid="otp-send-submit"
                className="mt-2 rounded-md bg-zinc-900 px-3 py-2 text-sm font-medium text-white transition hover:bg-zinc-800 disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-200"
              >
                {otpRequest.isPending ? "Sending…" : "Send code"}
              </button>
            </form>
          ) : (
            <form
              className="flex flex-col gap-3"
              onSubmit={async (e) => {
                e.preventDefault();
                await otpVerify.mutateAsync(
                  { email, code: otpCode },
                  { onSuccess: () => router.replace(next) }
                );
              }}
            >
              <p className="text-xs text-zinc-600 dark:text-zinc-400">
                A 6-digit code was sent to <strong>{email}</strong>. Enter it below.
              </p>
              <label className="flex flex-col gap-1 text-xs font-medium">
                Code
                <input
                  type="text"
                  required
                  inputMode="numeric"
                  pattern="[0-9]{6}"
                  maxLength={6}
                  placeholder="000000"
                  value={otpCode}
                  onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, ""))}
                  className="rounded-md border border-zinc-200 bg-white px-3 py-2 text-center text-lg font-mono tracking-[0.3em] dark:border-zinc-700 dark:bg-zinc-900"
                  data-testid="otp-code-input"
                  autoFocus
                />
              </label>
              {otpVerify.error ? (
                <p className="text-xs text-red-600" data-testid="otp-error">
                  {otpVerify.error.message}
                </p>
              ) : null}
              <button
                type="submit"
                disabled={otpVerify.isPending || otpCode.length < 6}
                data-testid="otp-verify-submit"
                className="mt-2 rounded-md bg-zinc-900 px-3 py-2 text-sm font-medium text-white transition hover:bg-zinc-800 disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-200"
              >
                {otpVerify.isPending ? "Verifying…" : "Sign in"}
              </button>
              <button
                type="button"
                onClick={() => { setOtpSent(false); setOtpCode(""); }}
                className="text-xs text-zinc-500 underline"
                data-testid="otp-resend"
              >
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
            <label className="flex flex-col gap-1 text-xs font-medium">
              Email
              <input
                type="email"
                required
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="rounded-md border border-zinc-200 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-900"
                data-testid="passkey-email"
              />
            </label>
            {passkeyError ? (
              <p className="text-xs text-red-600" data-testid="passkey-signin-error">{passkeyError}</p>
            ) : null}
            <button
              type="submit"
              disabled={passkeyLoading}
              data-testid="passkey-signin-submit"
              className="mt-2 rounded-md bg-zinc-900 px-3 py-2 text-sm font-medium text-white transition hover:bg-zinc-800 disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-200"
            >
              {passkeyLoading ? "Connecting…" : "Sign in with passkey"}
            </button>
          </form>
        </div>
      )}

      <div className="my-5 flex items-center gap-3 text-[11px] uppercase text-zinc-400">
        <span className="h-px flex-1 bg-zinc-200 dark:bg-zinc-800" />
        or
        <span className="h-px flex-1 bg-zinc-200 dark:bg-zinc-800" />
      </div>
      <OAuthButtons />
      <p className="mt-6 text-sm text-zinc-600 dark:text-zinc-400">
        New here?{" "}
        <Link
          href={`/auth/signup${next !== "/" ? `?next=${encodeURIComponent(next)}` : ""}`}
          className="font-medium text-zinc-900 underline dark:text-zinc-100"
          data-testid="signin-to-signup"
        >
          Create an account
        </Link>
      </p>
    </>
  );
}
