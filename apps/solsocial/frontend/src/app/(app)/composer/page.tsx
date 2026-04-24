"use client";
import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { useQuery, useMutation } from "@tanstack/react-query";
import { ss } from "@/lib/api";
import type { Channel, ListPage, MediaItem, Post, PostStatus } from "@/types/api";
import { Spinner } from "@/components/fields";

const PROVIDER_MARK: Record<string, string> = {
  linkedin: "in", twitter: "𝕏", instagram: "ig",
};

export default function Composer() {
  const router = useRouter();
  const sp = useSearchParams();
  // Idea → compose: /composer?body=...&title=... pre-fills the textarea.
  const initialBody = (() => {
    const t = sp.get("title") ?? "";
    const b = sp.get("body") ?? "";
    if (t && b) return `${t}\n\n${b}`;
    return b || t;
  })();
  const channels = useQuery({ queryKey: ["channels"], queryFn: () => ss.get<ListPage<Channel>>("/v1/channels") });
  const [channelId, setChannelId] = useState<string>("");
  const [body, setBody] = useState(initialBody);
  const [link, setLink] = useState("");
  const [status, setStatus] = useState<PostStatus>("draft");
  const [scheduledAt, setScheduledAt] = useState<string>("");
  const [media, setMedia] = useState<MediaItem[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadErr, setUploadErr] = useState<string | null>(null);

  const create = useMutation({
    mutationFn: (payload: Record<string, unknown>) => ss.post<Post>("/v1/posts", payload),
    onSuccess: () => router.push("/posts"),
  });

  const available = channels.data?.items ?? [];
  const canSubmit = !!channelId && body.trim().length > 0 && (status !== "scheduled" || !!scheduledAt);
  const activeChannel = available.find(c => c.id === channelId);
  const count = body.length;
  const countPct = Math.min(100, (count / 10000) * 100);

  function submit(e: React.FormEvent) {
    e.preventDefault();
    create.mutate({
      channel_id: channelId,
      body, link: link || null, media: [],
      status,
      scheduled_at: status === "scheduled" && scheduledAt ? new Date(scheduledAt).toISOString() : null,
    });
  }

  return (
    <div className="max-w-6xl mx-auto rise">
      <div className="mb-10">
        <p className="kicker rule mb-3">The desk</p>
        <h1 className="display text-[56px] leading-none">Compose.</h1>
      </div>

      {available.length === 0 ? (
        <div className="grain-card p-10 text-center">
          <p className="display-italic text-[28px] mb-3">No channels yet.</p>
          <p className="text-[color:var(--ink-70)] mb-6">Connect a social account to begin publishing.</p>
          <Link href="/channels" className="btn btn-ember">＋ Connect a channel</Link>
        </div>
      ) : (
        <form onSubmit={submit} className="grid grid-cols-1 lg:grid-cols-[1.8fr_1fr] gap-10">
          {/* Writing page */}
          <div className="paper p-10 relative min-h-[480px]">
            <div className="flex items-center justify-between mb-4">
              <span className="kicker">— draft · page one</span>
              {activeChannel && (
                <span className="mono text-[11px] text-[color:var(--ink-40)]">
                  posting as {activeChannel.handle}
                </span>
              )}
            </div>
            <textarea
              className="w-full min-h-[380px] bg-transparent resize-none outline-none
                         font-[Fraunces] text-[26px] leading-[1.4] tracking-[-0.01em]
                         placeholder:text-[color:var(--ink-20)] placeholder:italic"
              placeholder="Begin writing. Your first line becomes the headline…"
              value={body}
              onChange={e => setBody(e.target.value)}
              maxLength={10000}
              autoFocus
            />
            <div className="mt-6 hairline-t pt-4">
              <label className="block">
                <span className="kicker block mb-1">Attach a link (optional)</span>
                <input className="input" value={link} onChange={e => setLink(e.target.value)} placeholder="https://…" />
              </label>
            </div>

            {/* Platform preview — mono caps + small italic */}
            <div className="mt-5 hairline-t pt-3 flex items-baseline justify-between">
              <span className="kicker">
                {activeChannel
                  ? `preview · ${activeChannel.provider_code}`
                  : "preview · no channel"}
              </span>
              <span className="display-italic text-[12px] text-[color:var(--ink-40)]">
                {count === 0
                  ? "awaiting first line"
                  : count > 280
                    ? "long-form — twitter will clip"
                    : `${count} / 280 chars`}
              </span>
            </div>

            {/* Word-count arc */}
            <div className="absolute top-6 right-6 w-14 h-14 grid place-items-center">
              <svg width="56" height="56" viewBox="0 0 56 56" className="-rotate-90">
                <circle cx="28" cy="28" r="24" fill="none" stroke="var(--rule)" strokeWidth="1.5" />
                <circle
                  cx="28" cy="28" r="24"
                  fill="none" stroke="var(--ember)" strokeWidth="1.5"
                  strokeDasharray={`${(countPct / 100) * 150.8} 150.8`}
                  strokeLinecap="round"
                />
              </svg>
              <span className="absolute mono text-[10px]">{count}</span>
            </div>
          </div>

          {/* Side panel */}
          <aside className="space-y-8">
            <section>
              <p className="kicker mb-3 rule">Channel</p>
              <div className="space-y-2">
                {available.map(c => (
                  <label
                    key={c.id}
                    className={`flex items-center gap-3 p-3 cursor-pointer hairline transition
                                ${channelId === c.id ? "bg-[color:var(--paper-deep)] border-[color:var(--ember)]" : "hover:bg-[color:var(--paper-deep)]"}`}
                  >
                    <input type="radio" name="ch" className="sr-only"
                           checked={channelId === c.id} onChange={() => setChannelId(c.id)} />
                    <span className="w-9 h-9 rounded-full border border-[color:var(--ink)] grid place-items-center mono text-[12px]">
                      {PROVIDER_MARK[c.provider_code] ?? c.provider_code.slice(0, 2)}
                    </span>
                    <div className="flex-1 min-w-0">
                      <p className="text-[14px] leading-tight">{c.display_name ?? c.handle}</p>
                      <p className="mono text-[11px] text-[color:var(--ink-40)]">{c.provider_code} · {c.handle}</p>
                    </div>
                    {channelId === c.id && <span className="text-[color:var(--ember)]">●</span>}
                  </label>
                ))}
              </div>
            </section>

            <section>
              <p className="kicker mb-3 rule">Disposition</p>
              <div className="grid grid-cols-3 gap-0 hairline">
                {(["draft", "queued", "scheduled"] as PostStatus[]).map((s, idx) => (
                  <button
                    type="button"
                    key={s}
                    onClick={() => setStatus(s)}
                    className={`p-3 text-[12px] tracking-wider uppercase transition
                                ${idx > 0 ? "border-l border-[color:var(--rule)]" : ""}
                                ${status === s ? "bg-[color:var(--ink)] text-[color:var(--paper)]" : "hover:bg-[color:var(--paper-deep)]"}`}
                  >
                    {s}
                  </button>
                ))}
              </div>
              {status === "scheduled" && (
                <label className="block mt-4">
                  <span className="kicker block mb-1">Publish at</span>
                  <input className="boxed" type="datetime-local"
                         value={scheduledAt} onChange={e => setScheduledAt(e.target.value)} required />
                </label>
              )}
            </section>

            {create.isError && (
              <div className="mono text-[12px] text-[color:var(--ember-deep)] hairline p-3">
                × {(create.error as Error).message}
              </div>
            )}

            <div className="flex flex-col gap-2 pt-4">
              <button className="btn btn-ember" disabled={!canSubmit || create.isPending}>
                {create.isPending ? "Saving…" : "Save post →"}
              </button>
              <button
                type="button"
                className="btn"
                disabled={!channelId || !body.trim() || create.isPending}
                onClick={() => create.mutate({ channel_id: channelId, body, link: link || null, media: [], status: "draft", scheduled_at: null })}
              >
                Save draft
              </button>
              <Link href="/posts" className="btn">Discard</Link>
            </div>
          </aside>
        </form>
      )}
    </div>
  );
}
