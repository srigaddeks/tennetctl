"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { AuthShell } from "@/features/auth/_components/auth-shell";
import { OAUTH_STATE_KEY } from "@/features/auth/_components/oauth-buttons";
import { useOAuthExchange } from "@/features/auth/hooks/use-auth";

export function OAuthCallback({ provider }: { provider: "google" | "github" }) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const exchange = useOAuthExchange(provider);
  const ran = useRef(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (ran.current) return;
    ran.current = true;

    const code = searchParams.get("code");
    const state = searchParams.get("state");
    const oauthError = searchParams.get("error");
    if (oauthError) {
      setError(oauthError);
      return;
    }
    if (!code) {
      setError("missing OAuth code in callback URL");
      return;
    }

    // CSRF: the state nonce we stashed before redirecting must match.
    // Anyone linking a victim to this callback with an attacker-supplied code
    // will fail this check because sessionStorage is per-tab, same-origin.
    const expected = sessionStorage.getItem(OAUTH_STATE_KEY);
    sessionStorage.removeItem(OAUTH_STATE_KEY);
    if (!state || !expected || state !== expected || !state.startsWith(`${provider}.`)) {
      setError("OAuth state mismatch — this link may have been tampered with. Please sign in again.");
      return;
    }

    const redirectUri = `${window.location.origin}/auth/callback/${provider}`;
    exchange.mutate(
      { code, redirect_uri: redirectUri },
      {
        onSuccess: () => router.replace("/"),
        onError: (e) => setError(e.message),
      }
    );
  }, [exchange, provider, router, searchParams]);

  return (
    <AuthShell
      title={`Signing you in via ${provider === "google" ? "Google" : "GitHub"}…`}
      subtitle={
        error
          ? "Something went wrong with the OAuth handshake."
          : "Hold tight — exchanging the authorization code."
      }
    >
      {error ? (
        <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700 dark:bg-red-950 dark:text-red-300" data-testid="oauth-error">
          {error}
        </p>
      ) : (
        <div className="flex items-center gap-2 text-sm text-zinc-600 dark:text-zinc-400" data-testid="oauth-pending">
          <span className="inline-block h-2 w-2 animate-pulse rounded-full bg-zinc-400" />
          Working on it…
        </div>
      )}
    </AuthShell>
  );
}
