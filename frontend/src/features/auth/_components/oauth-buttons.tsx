"use client";

import { useEffect, useState } from "react";

const GOOGLE_CLIENT_ID = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID ?? "";
const GITHUB_CLIENT_ID = process.env.NEXT_PUBLIC_GITHUB_CLIENT_ID ?? "";

const OAUTH_STATE_KEY = "tennetctl_oauth_state";

function randomState(): string {
  const bytes = new Uint8Array(24);
  crypto.getRandomValues(bytes);
  return Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("");
}

function prepareState(provider: "google" | "github"): string {
  const state = `${provider}.${randomState()}`;
  sessionStorage.setItem(OAUTH_STATE_KEY, state);
  return state;
}

function buildGoogleUrl(redirectUri: string, state: string) {
  const params = new URLSearchParams({
    client_id: GOOGLE_CLIENT_ID,
    redirect_uri: redirectUri,
    response_type: "code",
    scope: "openid email profile",
    access_type: "online",
    prompt: "select_account",
    state,
  });
  return `https://accounts.google.com/o/oauth2/v2/auth?${params.toString()}`;
}

function buildGithubUrl(redirectUri: string, state: string) {
  const params = new URLSearchParams({
    client_id: GITHUB_CLIENT_ID,
    redirect_uri: redirectUri,
    scope: "read:user user:email",
    state,
  });
  return `https://github.com/login/oauth/authorize?${params.toString()}`;
}

export function OAuthButtons() {
  const [origin, setOrigin] = useState<string>("");
  useEffect(() => {
    setOrigin(window.location.origin);
  }, []);

  const googleEnabled = !!GOOGLE_CLIENT_ID;
  const githubEnabled = !!GITHUB_CLIENT_ID;

  const start = (provider: "google" | "github") => (e: React.MouseEvent) => {
    e.preventDefault();
    const state = prepareState(provider);
    const redirect = `${origin}/auth/callback/${provider}`;
    const url = provider === "google"
      ? buildGoogleUrl(redirect, state)
      : buildGithubUrl(redirect, state);
    window.location.href = url;
  };

  return (
    <div className="flex flex-col gap-2">
      <button
        type="button"
        onClick={googleEnabled ? start("google") : undefined}
        disabled={!googleEnabled}
        data-testid="oauth-google"
        className="flex items-center justify-center gap-2 rounded-md border border-zinc-200 bg-white px-3 py-2 text-sm font-medium transition hover:bg-zinc-50 disabled:cursor-not-allowed disabled:opacity-50 dark:border-zinc-700 dark:bg-zinc-900 dark:hover:bg-zinc-800"
      >
        <span className="font-bold">G</span> Continue with Google
      </button>
      <button
        type="button"
        onClick={githubEnabled ? start("github") : undefined}
        disabled={!githubEnabled}
        data-testid="oauth-github"
        className="flex items-center justify-center gap-2 rounded-md border border-zinc-200 bg-white px-3 py-2 text-sm font-medium transition hover:bg-zinc-50 disabled:cursor-not-allowed disabled:opacity-50 dark:border-zinc-700 dark:bg-zinc-900 dark:hover:bg-zinc-800"
      >
        <span className="font-bold">GH</span> Continue with GitHub
      </button>
      {!googleEnabled && !githubEnabled ? (
        <p className="text-[11px] text-zinc-500 dark:text-zinc-400">
          OAuth providers not configured. Set NEXT_PUBLIC_GOOGLE_CLIENT_ID or
          NEXT_PUBLIC_GITHUB_CLIENT_ID to enable.
        </p>
      ) : null}
    </div>
  );
}

export { OAUTH_STATE_KEY };
