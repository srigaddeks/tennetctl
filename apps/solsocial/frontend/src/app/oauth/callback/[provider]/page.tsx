"use client";
import { useEffect, useState } from "react";
import { useRouter, useSearchParams, useParams } from "next/navigation";
import Link from "next/link";
import { ss } from "@/lib/api";

/**
 * OAuth landing page. LinkedIn (and other real providers) redirect the
 * browser here with ?code=...&state=... in the URL.
 *
 * We post those to solsocial's callback endpoint, which exchanges the code
 * for tokens and creates the channel row, then we redirect back to the
 * channels page.
 */
export default function OAuthCallbackPage() {
  const router = useRouter();
  const sp = useSearchParams();
  const params = useParams<{ provider: string }>();
  const provider = params.provider;
  const [msg, setMsg] = useState("Completing authentication…");
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    const code = sp.get("code");
    const state = sp.get("state");
    const oauthError = sp.get("error");
    if (oauthError) {
      setErr(`${oauthError}${sp.get("error_description") ? `: ${sp.get("error_description")}` : ""}`);
      return;
    }
    if (!code || !state) {
      setErr("Missing code or state in callback URL");
      return;
    }
    const redirect_uri = `${window.location.origin}/oauth/callback/${provider}`;
    setMsg("Exchanging code with LinkedIn…");
    ss.post<{ channel_id: string; provider_code: string }>(
      `/v1/oauth/${provider}/callback`,
      { code, state, redirect_uri },
    )
      .then(() => {
        setMsg("Connected.");
        setTimeout(() => router.replace("/channels"), 400);
      })
      .catch(e => setErr((e as Error).message));
  }, [sp, provider, router]);

  return (
    <div className="min-h-screen grid place-items-center p-10">
      <div className="max-w-md text-center">
        <p className="kicker rule mb-3">Returning from {provider}</p>
        <h1 className="display text-[40px] leading-tight mb-4">
          {err ? "Something went awry." : "Connecting your channel…"}
        </h1>
        <p className={err ? "mono text-sm text-[color:var(--ember-deep)]" : "text-[color:var(--ink-70)]"}>
          {err ? `× ${err}` : msg}
        </p>
        {err && (
          <div className="mt-6">
            <Link href="/channels" className="btn">Back to channels</Link>
          </div>
        )}
      </div>
    </div>
  );
}
