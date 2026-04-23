"use client";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { ss } from "@/lib/api";
import type { Channel, ListPage, ProviderCode } from "@/types/api";
import { ProviderAppConfig } from "@/features/channels/provider-app-config";

const PROVIDERS: { code: ProviderCode; label: string; mark: string; hue: string }[] = [
  { code: "linkedin",  label: "LinkedIn",    mark: "in", hue: "#0A66C2" },
  { code: "twitter",   label: "Twitter · X", mark: "𝕏",  hue: "#171512" },
  { code: "instagram", label: "Instagram",   mark: "ig", hue: "#C13584" },
];

export default function ChannelsPage() {
  const qc = useQueryClient();
  const channels = useQuery({ queryKey: ["channels"], queryFn: () => ss.get<ListPage<Channel>>("/v1/channels") });

  // Start OAuth. If live, redirect the browser to the provider's real
  // authorize URL and let it redirect back to /oauth/callback/{code}.
  // If stub, short-circuit inline.
  const connect = useMutation({
    mutationFn: async (code: ProviderCode) => {
      const redirect_uri = `${window.location.origin}/oauth/callback/${code}`;
      const started = await ss.post<{ authorize_url: string; state: string; mode: "live" | "stub" }>(
        `/v1/oauth/${code}/start`, { redirect_uri },
      );
      if (started.mode === "live") {
        window.location.href = started.authorize_url;
        return null;
      }
      const url = new URL(started.authorize_url);
      const stubCode = url.searchParams.get("code") ?? `stub_${code}_manual`;
      return ss.post<{ channel_id: string; provider_code: string }>(
        `/v1/oauth/${code}/callback`,
        { code: stubCode, state: started.state, redirect_uri },
      );
    },
    onSuccess: (data) => { if (data) qc.invalidateQueries({ queryKey: ["channels"] }); },
  });
  const disconnect = useMutation({
    mutationFn: (id: string) => ss.del(`/v1/channels/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["channels"] }),
  });

  return (
    <div className="max-w-6xl mx-auto rise">
      <div className="mb-10">
        <p className="kicker rule mb-3">The roster</p>
        <h1 className="display text-[64px] leading-none">Channels.</h1>
        <p className="mt-4 text-[color:var(--ink-70)] max-w-xl">
          Bring your own provider app (LinkedIn, Twitter, Instagram). Your credentials are
          encrypted at rest and scoped to this workspace. Channels below use whichever
          apps you've configured.
        </p>
      </div>

      <ProviderAppConfig />

      {/* Connect row */}
      <section className="mb-14">
        <p className="kicker mb-4">Open a new channel</p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-0 hairline">
          {PROVIDERS.map((p, i) => (
            <div key={p.code} className={`p-6 group ${i > 0 ? "border-l border-[color:var(--rule)]" : ""}`}>
              <div className="flex items-start justify-between mb-4">
                <div
                  className="w-14 h-14 rounded-full grid place-items-center border border-[color:var(--ink)] mono text-[18px]"
                  style={{ background: p.hue, color: "#fff" }}
                >
                  {p.mark}
                </div>
                <span className="kicker">provider</span>
              </div>
              <p className="display text-[22px] mb-1">{p.label}</p>
              <p className="text-[12px] text-[color:var(--ink-40)] mb-5">
                {p.code === "linkedin"
                  ? "requires client_id + secret in secrets/"
                  : "stub mode — synthetic tokens"}
              </p>
              <button
                className="btn btn-ember w-full text-[11px]"
                disabled={connect.isPending}
                onClick={() => connect.mutate(p.code)}
              >
                {connect.isPending && connect.variables === p.code ? "Connecting…" : "Connect →"}
              </button>
            </div>
          ))}
        </div>
        {connect.isError && (
          <p className="mono text-[11px] text-[color:var(--ember-deep)] mt-3">× {(connect.error as Error).message}</p>
        )}
      </section>

      {/* Connected list */}
      <section>
        <p className="kicker mb-4">Currently connected</p>
        {channels.isLoading ? (
           <div className="space-y-3">
             <div className="h-3 w-32 bg-[color:var(--paper-edge)]" />
             <div className="h-12 bg-[color:var(--paper-edge)]" />
             <div className="h-12 bg-[color:var(--paper-edge)]" />
           </div>
         ) : (channels.data?.items.length ?? 0) === 0 ? (
           <p className="display-italic text-[26px] text-[color:var(--ink-40)] py-8">
             No channels yet — pick one above.
           </p>
         ) : (
          <div className="space-y-10">
            {PROVIDERS.map(p => {
              const accounts = (channels.data?.items ?? []).filter(c => c.provider_code === p.code);
              if (accounts.length === 0) return null;
              return (
                <div key={p.code}>
                  <div className="flex items-baseline justify-between mb-3 hairline-b pb-2">
                    <div className="flex items-baseline gap-3">
                      <span className="kicker">{p.label}</span>
                      <span className="mono text-[11px] text-[color:var(--ink-40)]">
                        {accounts.length} account{accounts.length === 1 ? "" : "s"}
                      </span>
                    </div>
                    <button
                      className="btn-ghost text-[11px] mono uppercase tracking-wider"
                      disabled={connect.isPending}
                      onClick={() => connect.mutate(p.code)}
                    >
                      ＋ add another →
                    </button>
                  </div>
                  <ul className="space-y-0 hairline-b">
                    {accounts.map(c => (
                      <li key={c.id} className="py-4 flex items-center gap-5 hairline-t">
                        <div
                          className="w-11 h-11 rounded-full grid place-items-center border border-[color:var(--ink)] mono text-[14px] shrink-0"
                          style={{ background: p.hue, color: "#fff" }}
                        >{p.mark}</div>
                        <div className="flex-1 min-w-0">
                          <p className="display text-[19px] truncate">{c.display_name ?? c.handle}</p>
                          <p className="mono text-[11px] text-[color:var(--ink-40)]">
                            {c.handle} · connected {new Date(c.connected_at).toLocaleDateString("en-US", { month: "short", day: "numeric" })}
                          </p>
                        </div>
                        <button
                          className="btn-ghost text-[11px] mono uppercase tracking-wider hover:text-[color:var(--ember-deep)]"
                          onClick={() => { if (confirm(`Disconnect ${c.handle}?`)) disconnect.mutate(c.id); }}
                        >disconnect</button>
                      </li>
                    ))}
                  </ul>
                </div>
              );
            })}
          </div>
         )}
      </section>
    </div>
  );
}
