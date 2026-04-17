"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";

import { OAuthButtons } from "@/features/auth/_components/oauth-buttons";
import { useSignup } from "@/features/auth/hooks/use-auth";

export function SignUpForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const next = searchParams.get("next") ?? "/";
  const [email, setEmail] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [password, setPassword] = useState("");
  const signup = useSignup();

  return (
    <>
      <form
        className="flex flex-col gap-3"
        data-testid="signup-form"
        onSubmit={async (e) => {
          e.preventDefault();
          await signup.mutateAsync(
            { email, display_name: displayName, password },
            { onSuccess: () => router.replace(next) }
          );
        }}
      >
        <label className="flex flex-col gap-1 text-xs font-medium">
          Display name
          <input
            type="text"
            required
            minLength={1}
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            className="rounded-md border border-zinc-200 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-900"
            data-testid="signup-display-name"
          />
        </label>
        <label className="flex flex-col gap-1 text-xs font-medium">
          Email
          <input
            type="email"
            required
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="rounded-md border border-zinc-200 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-900"
            data-testid="signup-email"
          />
        </label>
        <label className="flex flex-col gap-1 text-xs font-medium">
          Password (min 8 chars)
          <input
            type="password"
            required
            minLength={8}
            autoComplete="new-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="rounded-md border border-zinc-200 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-900"
            data-testid="signup-password"
          />
        </label>
        {signup.error ? (
          <p className="text-xs text-red-600" data-testid="signup-error">
            {signup.error.message}
          </p>
        ) : null}
        <button
          type="submit"
          disabled={signup.isPending}
          data-testid="signup-submit"
          className="mt-2 rounded-md bg-zinc-900 px-3 py-2 text-sm font-medium text-white transition hover:bg-zinc-800 disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-200"
        >
          {signup.isPending ? "Creating account…" : "Create account"}
        </button>
      </form>
      <div className="my-5 flex items-center gap-3 text-[11px] uppercase text-zinc-400">
        <span className="h-px flex-1 bg-zinc-200 dark:bg-zinc-800" />
        or
        <span className="h-px flex-1 bg-zinc-200 dark:bg-zinc-800" />
      </div>
      <OAuthButtons />
      <p className="mt-6 text-sm text-zinc-600 dark:text-zinc-400">
        Already have an account?{" "}
        <Link
          href={`/auth/signin${next !== "/" ? `?next=${encodeURIComponent(next)}` : ""}`}
          className="font-medium text-zinc-900 underline dark:text-zinc-100"
          data-testid="signup-to-signin"
        >
          Sign in
        </Link>
      </p>
    </>
  );
}
