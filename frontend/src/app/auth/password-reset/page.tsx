"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";

import { AuthShell } from "@/features/auth/_components/auth-shell";
import { usePasswordResetComplete } from "@/features/auth/hooks/use-auth";

function PasswordResetForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token") ?? "";

  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [mismatch, setMismatch] = useState(false);

  const complete = usePasswordResetComplete();

  if (!token) {
    return (
      <div className="flex flex-col gap-4" data-testid="password-reset-no-token-state">
        <p className="text-sm text-red-600" data-testid="password-reset-no-token">
          Invalid or missing reset link.
        </p>
        <Link
          href="/auth/forgot-password"
          className="inline-flex items-center text-sm font-medium text-zinc-900 underline dark:text-zinc-100"
        >
          Request a new reset link →
        </Link>
      </div>
    );
  }

  return (
    <form
      className="flex flex-col gap-3"
      data-testid="password-reset-form"
      onSubmit={async (e) => {
        e.preventDefault();
        setMismatch(false);
        if (password !== confirm) {
          setMismatch(true);
          return;
        }
        await complete.mutateAsync(
          { token, new_password: password },
          { onSuccess: () => router.replace("/") }
        );
      }}
    >
      <label className="flex flex-col gap-1 text-xs font-medium">
        New password
        <input
          type="password"
          required
          minLength={8}
          autoComplete="new-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="rounded-md border border-zinc-200 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-800"
          data-testid="password-reset-new"
        />
      </label>
      <label className="flex flex-col gap-1 text-xs font-medium">
        Confirm password
        <input
          type="password"
          required
          minLength={8}
          autoComplete="new-password"
          value={confirm}
          onChange={(e) => setConfirm(e.target.value)}
          className="rounded-md border border-zinc-200 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-800"
          data-testid="password-reset-confirm"
        />
      </label>
      {mismatch ? (
        <p className="text-xs text-red-600" data-testid="password-reset-mismatch">Passwords do not match.</p>
      ) : null}
      {complete.error ? (
        <p className="text-xs text-red-600" data-testid="password-reset-error">{complete.error.message}</p>
      ) : null}
      <button
        type="submit"
        disabled={complete.isPending}
        data-testid="password-reset-submit"
        className="mt-2 rounded-md bg-zinc-900 px-3 py-2 text-sm font-medium text-white transition hover:bg-zinc-800 disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-200"
      >
        {complete.isPending ? "Saving…" : "Set new password"}
      </button>
    </form>
  );
}

export default function PasswordResetPage() {
  return (
    <AuthShell
      title="Set new password"
      subtitle="Choose a new password for your account."
    >
      <Suspense fallback={<p className="text-sm text-zinc-400">Loading…</p>}>
        <PasswordResetForm />
      </Suspense>
    </AuthShell>
  );
}
