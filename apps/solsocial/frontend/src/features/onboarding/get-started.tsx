"use client";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { ss } from "@/lib/api";
import type { Channel, ListPage, Post, WorkspaceApp } from "@/types/api";

type Step = {
  key: string;
  kicker: string;
  title: string;
  body: string;
  cta: { href: string; label: string };
  done: boolean;
};

export function GetStartedBanner() {
  const apps     = useQuery({ queryKey: ["provider-apps"], queryFn: () => ss.get<{ items: WorkspaceApp[]; total: number }>("/v1/provider-apps") });
  const channels = useQuery({ queryKey: ["channels"],      queryFn: () => ss.get<ListPage<Channel>>("/v1/channels") });
  const posts    = useQuery({ queryKey: ["posts"],         queryFn: () => ss.get<ListPage<Post>>("/v1/posts") });

  if (apps.isLoading || channels.isLoading || posts.isLoading) return null;

  const hasApp     = (apps.data?.total    ?? 0) > 0;
  const hasChannel = (channels.data?.total ?? 0) > 0;
  const hasPost    = (posts.data?.total    ?? 0) > 0;
  if (hasApp && hasChannel && hasPost) return null;

  const steps: Step[] = [
    {
      key: "app",
      kicker: "step 01",
      title: "Bring a provider app",
      body: "Paste your LinkedIn, Twitter, or Instagram app credentials. You only need one to start. Stored in tennetctl vault, encrypted.",
      cta: { href: "/channels", label: "Configure →" },
      done: hasApp,
    },
    {
      key: "channel",
      kicker: "step 02",
      title: "Connect an account",
      body: "Once an app is in place, connect one or more accounts from that provider. Use the stub mode button to try the pipeline end-to-end.",
      cta: { href: "/channels", label: "Connect →" },
      done: hasChannel,
    },
    {
      key: "post",
      kicker: "step 03",
      title: "Write your first dispatch",
      body: "Draft something small. Save it, then click Publish — your text goes live to the connected account.",
      cta: { href: "/composer", label: "Compose →" },
      done: hasPost,
    },
  ];

  const completed = steps.filter(s => s.done).length;

  return (
    <section className="grain-card p-8 mb-12 rise-d1">
      <div className="flex items-start justify-between mb-6">
        <div>
          <p className="kicker rule mb-2">A gentle welcome</p>
          <h2 className="display text-[36px] leading-tight">
            Three small steps to get going.
          </h2>
        </div>
        <div className="text-right shrink-0">
          <p className="mono text-[11px] text-[color:var(--ink-40)]">progress</p>
          <p className="display text-[32px] leading-none">
            {completed}<span className="display-italic text-[color:var(--ink-40)]">/3</span>
          </p>
        </div>
      </div>

      <ol className="grid grid-cols-1 md:grid-cols-3 gap-0 hairline">
        {steps.map((s, i) => (
          <li
            key={s.key}
            className={`p-6 ${i > 0 ? "md:border-l border-[color:var(--rule)]" : ""} ${s.done ? "opacity-60" : ""}`}
          >
            <div className="flex items-start justify-between mb-3">
              <span className="kicker">{s.kicker}</span>
              {s.done ? (
                <span className="pip pip-published">done</span>
              ) : (
                <span className="pip pip-queued">to do</span>
              )}
            </div>
            <p className="display text-[20px] leading-tight mb-2">{s.title}</p>
            <p className="text-[13px] text-[color:var(--ink-70)] mb-4 leading-snug">{s.body}</p>
            {s.done ? (
              <p className="mono text-[11px] text-[color:var(--sage)]">✓ complete</p>
            ) : (
              <Link href={s.cta.href} className="btn btn-ember text-[11px] w-full">{s.cta.label}</Link>
            )}
          </li>
        ))}
      </ol>
    </section>
  );
}
