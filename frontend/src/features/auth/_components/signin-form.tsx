"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";

import { OAuthButtons } from "@/features/auth/_components/oauth-buttons";
import { useSignin } from "@/features/auth/hooks/use-auth";

export function SignInForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const next = searchParams.get("next") ?? "/";
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const signin = useSignin();

  return (
    <>
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
      </form>
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
