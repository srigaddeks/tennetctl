"use client";

import Link from "next/link";
import { useState } from "react";

import { AuthShell } from "@/features/auth/_components/auth-shell";
import { usePasswordResetRequest } from "@/features/auth/hooks/use-auth";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const request = usePasswordResetRequest();

  return (
    <AuthShell
      title="Reset your password"
      subtitle="Enter your email and we'll send a reset link if that account exists."
    >
      {sent ? (
        <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-4 dark:border-emerald-800 dark:bg-emerald-950" data-testid="forgot-password-sent">
          <p className="text-sm font-medium text-emerald-800 dark:text-emerald-200">Check your inbox</p>
          <p className="mt-1 text-xs text-emerald-700 dark:text-emerald-300">
            If that email is registered, a reset link is on its way. It expires in 15 minutes.
          </p>
          <button
            type="button"
            onClick={() => setSent(false)}
            className="mt-3 text-xs text-emerald-600 underline dark:text-emerald-400"
          >
            Send another link
          </button>
        </div>
      ) : (
        <form
          className="flex flex-col gap-3"
          data-testid="forgot-password-form"
          onSubmit={async (e) => {
            e.preventDefault();
            await request.mutateAsync({ email }, { onSuccess: () => setSent(true) });
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
              className="rounded-md border border-zinc-200 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-800"
              data-testid="forgot-password-email"
            />
          </label>
          {request.error ? (
            <p className="text-xs text-red-600" data-testid="forgot-password-error">
              {request.error.message}
            </p>
          ) : null}
          <button
            type="submit"
            disabled={request.isPending}
            data-testid="forgot-password-submit"
            className="mt-2 rounded-md bg-zinc-900 px-3 py-2 text-sm font-medium text-white transition hover:bg-zinc-800 disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-200"
          >
            {request.isPending ? "Sending…" : "Send reset link"}
          </button>
        </form>
      )}

      <p className="mt-6 text-sm text-zinc-500 dark:text-zinc-400">
        <Link
          href="/auth/signin"
          className="font-medium text-zinc-900 underline dark:text-zinc-100"
          data-testid="back-to-signin"
        >
          ← Back to sign in
        </Link>
      </p>
    </AuthShell>
  );
}
