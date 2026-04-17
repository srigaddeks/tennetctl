"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";

import { usePasswordResetComplete } from "@/features/auth/hooks/use-auth";

function PasswordResetForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token") ?? "";

  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [mismatch, setMismatch] = useState(false);

  const complete = usePasswordResetComplete();

  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-50 dark:bg-zinc-950">
      <div className="w-full max-w-sm rounded-2xl bg-white p-8 shadow-sm dark:bg-zinc-900">
        <h1 className="mb-1 text-lg font-semibold" data-testid="password-reset-heading">
          Set new password
        </h1>
        <p className="mb-6 text-sm text-zinc-500">Choose a new password for your account.</p>

        {!token ? (
          <p className="text-sm text-red-600" data-testid="password-reset-no-token">
            Invalid reset link. Please request a new one.
          </p>
        ) : (
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
                className="rounded-md border border-zinc-200 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-900"
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
                className="rounded-md border border-zinc-200 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-900"
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
              className="mt-2 rounded-md bg-zinc-900 px-3 py-2 text-sm font-medium text-white transition hover:bg-zinc-800 disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900"
            >
              {complete.isPending ? "Saving…" : "Set new password"}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}

export default function PasswordResetPage() {
  return (
    <Suspense>
      <PasswordResetForm />
    </Suspense>
  );
}
