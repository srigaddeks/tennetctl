"use client";
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { ss } from "@/lib/api";
import type { ProviderCode, WorkspaceApp } from "@/types/api";

type Provider = { code: ProviderCode; label: string; mark: string; hue: string; steps: string[]; redirectNote: string };

const PROVIDERS: Provider[] = [
  {
    code: "linkedin", label: "LinkedIn", mark: "in", hue: "#0A66C2",
    redirectNote: "http://localhost:51835/oauth/callback/linkedin",
    steps: [
      "Open developer.linkedin.com → My Apps → Create app.",
      "Associate with any LinkedIn Company Page you admin (create a minimal one if needed).",
      "Once created, open the Products tab. Request 'Sign In with LinkedIn using OpenID Connect' (instant) AND 'Share on LinkedIn' (usually instant).",
      "In the Auth tab, add the redirect URL shown below exactly — trailing slash matters.",
      "Copy Client ID and Client Secret from the Auth tab and paste them below.",
    ],
  },
  {
    code: "twitter", label: "Twitter · X", mark: "𝕏", hue: "#171512",
    redirectNote: "http://localhost:51835/oauth/callback/twitter",
    steps: [
      "Open developer.twitter.com → Projects & Apps → Create app.",
      "Note: free tier is 500 posts/month app-wide. Basic ($200/mo) unlocks real use.",
      "Under User authentication settings, enable OAuth 2.0 with PKCE.",
      "Set callback URL to the one below; set scopes to tweet.read, tweet.write, users.read, offline.access.",
      "Copy Client ID and Client Secret from Keys and tokens.",
    ],
  },
  {
    code: "instagram", label: "Instagram", mark: "ig", hue: "#C13584",
    redirectNote: "http://localhost:51835/oauth/callback/instagram",
    steps: [
      "Requires a Facebook Business Manager account and a Facebook Page linked to your Instagram Business account.",
      "Open developers.facebook.com → My Apps → Create App → Business type.",
      "Add products: Instagram Graph API + Facebook Login for Business.",
      "In Facebook Login settings, add the redirect URI below.",
      "Copy App ID and App Secret from the Settings → Basic tab.",
    ],
  },
];

export function ProviderAppConfig() {
  const qc = useQueryClient();
  const apps = useQuery({
    queryKey: ["provider-apps"],
    queryFn: () => ss.get<{ items: WorkspaceApp[]; total: number }>("/v1/provider-apps"),
  });
  const [openFor, setOpenFor] = useState<ProviderCode | null>(null);

  const byCode = new Map<ProviderCode, WorkspaceApp>(
    (apps.data?.items ?? []).map(a => [a.provider_code, a]),
  );

  return (
    <section className="mb-14">
      <div className="flex items-baseline justify-between mb-4">
        <p className="kicker">Provider apps · bring your own</p>
        <span className="mono text-[11px] text-[color:var(--ink-40)]">
          your credentials, encrypted at rest
        </span>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-0 hairline">
        {PROVIDERS.map((p, i) => {
          const app = byCode.get(p.code);
          const configured = !!app?.has_secret;
          return (
            <div key={p.code} className={`p-6 ${i > 0 ? "border-l border-[color:var(--rule)]" : ""}`}>
              <div className="flex items-start justify-between mb-4">
                <div
                  className="w-12 h-12 rounded-full grid place-items-center border border-[color:var(--ink)] mono text-[16px]"
                  style={{ background: p.hue, color: "#fff" }}
                >{p.mark}</div>
                <span className={`pip ${configured ? "pip-published" : "pip-draft"}`}>
                  {configured ? "configured" : "not configured"}
                </span>
              </div>
              <p className="display text-[20px]">{p.label}</p>
              <p className="mono text-[11px] text-[color:var(--ink-40)] mb-4">
                {configured ? `client_id · ${app!.client_id.slice(0, 20)}…` : "needs client_id + secret"}
              </p>
              <button
                className="btn text-[11px] w-full"
                onClick={() => setOpenFor(openFor === p.code ? null : p.code)}
              >
                {configured ? "Update credentials" : "Configure →"}
              </button>
            </div>
          );
        })}
      </div>

      {openFor && (
        <ConfigPanel
          provider={PROVIDERS.find(p => p.code === openFor)!}
          existing={byCode.get(openFor)}
          onClose={() => setOpenFor(null)}
          onSaved={() => { setOpenFor(null); qc.invalidateQueries({ queryKey: ["provider-apps"] }); }}
        />
      )}
    </section>
  );
}

function ConfigPanel({
  provider, existing, onClose, onSaved,
}: { provider: Provider; existing: WorkspaceApp | undefined; onClose: () => void; onSaved: () => void }) {
  const [clientId, setClientId] = useState(existing?.client_id ?? "");
  const [clientSecret, setClientSecret] = useState("");
  const [notes, setNotes] = useState(existing?.notes ?? "");
  const save = useMutation({
    mutationFn: (body: Record<string, unknown>) => ss.put<WorkspaceApp>("/v1/provider-apps", body),
    onSuccess: onSaved,
  });
  const remove = useMutation({
    mutationFn: () => ss.del(`/v1/provider-apps/${provider.code}`),
    onSuccess: onSaved,
  });

  return (
    <div className="mt-6 grain-card p-8 rise">
      <div className="flex items-start justify-between mb-6">
        <div>
          <p className="kicker rule mb-2">Configure · {provider.label}</p>
          <h3 className="display text-[28px] leading-tight">
            Bring your own <span className="display-italic">{provider.label}</span> app.
          </h3>
        </div>
        <button className="btn-ghost text-[11px]" onClick={onClose}>close</button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[1.1fr_1fr] gap-10">
        {/* Instructions */}
        <div>
          <p className="kicker mb-3">Steps</p>
          <ol className="space-y-3">
            {provider.steps.map((s, i) => (
              <li key={i} className="flex gap-3">
                <span className="mono text-[11px] text-[color:var(--ember)] pt-0.5">{String(i + 1).padStart(2, "0")}</span>
                <p className="text-[13px] text-[color:var(--ink-70)] leading-snug">{s}</p>
              </li>
            ))}
          </ol>
          <div className="mt-5 paper-deep p-3 hairline">
            <p className="kicker mb-1">Redirect URI to paste into {provider.label}</p>
            <code className="mono text-[12px] break-all">{provider.redirectNote}</code>
          </div>
        </div>

        {/* Form */}
        <form
          className="space-y-5"
          onSubmit={e => {
            e.preventDefault();
            if (!clientId || !clientSecret) return;
            save.mutate({
              provider_code: provider.code, client_id: clientId, client_secret: clientSecret,
              redirect_uri_hint: provider.redirectNote, notes: notes || null,
            });
          }}
        >
          <label className="block">
            <span className="kicker block mb-1">Client ID</span>
            <input className="boxed" value={clientId} onChange={e => setClientId(e.target.value)} required autoFocus />
          </label>
          <label className="block">
            <span className="kicker block mb-1">Client Secret {existing?.has_secret && <span className="text-[color:var(--ink-40)] normal-case tracking-normal"> (paste again to update)</span>}</span>
            <input className="boxed" type="password" value={clientSecret} onChange={e => setClientSecret(e.target.value)} required placeholder={existing?.has_secret ? "•••••••• (secret stored, not revealed)" : ""} />
          </label>
          <label className="block">
            <span className="kicker block mb-1">Notes (optional)</span>
            <textarea className="boxed" rows={2} value={notes} onChange={e => setNotes(e.target.value)} />
          </label>
          {save.isError && <div className="mono text-[12px] text-[color:var(--ember-deep)]">× {(save.error as Error).message}</div>}
          <div className="flex gap-2">
            <button className="btn btn-ember" disabled={!clientId || !clientSecret || save.isPending}>
              {save.isPending ? "Saving…" : "Save credentials →"}
            </button>
            {existing && (
              <button
                type="button" className="btn text-[color:var(--ember-deep)]"
                onClick={() => { if (confirm(`Remove ${provider.label} app?`)) remove.mutate(); }}
              >
                Remove
              </button>
            )}
          </div>
        </form>
      </div>
    </div>
  );
}
