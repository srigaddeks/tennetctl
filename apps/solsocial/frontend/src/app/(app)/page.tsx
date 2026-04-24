"use client";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { ss } from "@/lib/api";
import type { ListPage, Post, Channel, Idea } from "@/types/api";
import { useMe } from "@/features/auth/use-auth";
import { SunMark } from "@/components/sun-mark";
import { GetStartedBanner } from "@/features/onboarding/get-started";
import { SkeletonList, SkeletonTiles } from "@/components/skeleton";

const PIP: Record<string, string> = {
  draft: "pip-draft", queued: "pip-queued", scheduled: "pip-scheduled",
  publishing: "pip-publishing", published: "pip-published", failed: "pip-failed",
};

export default function Dashboard() {
  const me = useMe();
  const posts    = useQuery({ queryKey: ["posts"],    queryFn: () => ss.get<ListPage<Post>>("/v1/posts?limit=5") });
  const channels = useQuery({ queryKey: ["channels"], queryFn: () => ss.get<ListPage<Channel>>("/v1/channels?limit=5") });
  const ideas    = useQuery({ queryKey: ["ideas"],    queryFn: () => ss.get<ListPage<Idea>>("/v1/ideas?limit=5") });

  const hour = new Date().getHours();
  const greeting = hour < 5 ? "Late hours"
                  : hour < 12 ? "Good morning"
                  : hour < 18 ? "Good afternoon"
                  : "Good evening";

  return (
    <div className="max-w-6xl mx-auto">
      {/* Hero */}
      <section className="grid grid-cols-1 lg:grid-cols-[2fr_1fr] gap-10 mb-16 rise">
        <div>
          <p className="kicker rule mb-4">The front page</p>
          <h1 className="display text-[72px] md:text-[104px] leading-[0.92] -ml-1" suppressHydrationWarning>
            {greeting},
            <br />
            <span className="display-italic">{me.data?.user.display_name?.split(" ")[0] ?? "friend"}</span>.
          </h1>
          <p className="mt-6 max-w-lg text-[color:var(--ink-70)]">
            A quiet dashboard for a day of publishing. What follows is a reading of your feed —
            channels connected, posts underway, ideas to tend to.
          </p>

          <div className="mt-8 flex gap-3 flex-wrap">
            <Link href="/composer" className="btn btn-ember">✍ Compose a post</Link>
            <Link href="/channels" className="btn">＋ Connect a channel</Link>
          </div>
        </div>

        <div className="relative flex items-center justify-center">
          <SunMark size={280} className="opacity-90" />
        </div>
      </section>

      {/* Ledger tiles */}
      <GetStartedBanner />

      {channels.isLoading && posts.isLoading && ideas.isLoading ? (
        <div className="rise-d1 mb-16"><SkeletonTiles count={3} /></div>
      ) : (
        <section className="grid grid-cols-3 gap-0 hairline mb-16 rise-d1">
          <Tile kicker="Channels connected" value={channels.data?.total} href="/channels" />
          <Tile kicker="Posts on file" value={posts.data?.total} href="/posts" divider />
          <Tile kicker="Ideas brewing" value={ideas.data?.total} href="/ideas" divider />
        </section>
      )}

      {/* Recent posts */}
      <section className="rise-d2 mb-16">
        <div className="flex items-baseline justify-between mb-6">
          <h2 className="display text-[36px]">Dispatches</h2>
          <Link href="/posts" className="kicker hover:text-[color:var(--ink)]">See all →</Link>
        </div>
        {posts.isLoading ? (
          <SkeletonList rows={3} />
        ) : (posts.data?.items.length ?? 0) === 0 ? (
          <EmptyState
            title="Nothing dispatched yet."
            cta="Write the first"
            href="/composer"
          />
        ) : (
          <ul className="hairline-t">
            {posts.data!.items.map((p, i) => (
              <li key={p.id} className="hairline-b grid grid-cols-[120px_1fr_200px] gap-6 py-5 group">
                <div className="mono text-[11px] text-[color:var(--ink-40)]">
                  №{String(i + 1).padStart(3, "0")} · {new Date(p.created_at).toLocaleDateString("en-US", { month: "short", day: "numeric" })}
                </div>
                <div>
                  <p className="display text-[22px] leading-tight">{p.body.split("\n")[0].slice(0, 90) || "—"}</p>
                  {p.body.length > 90 && (
                    <p className="text-[13px] text-[color:var(--ink-40)] mt-1">
                      …{p.body.slice(90, 170)}
                    </p>
                  )}
                </div>
                <div className="flex items-center justify-end">
                  <span className={`pip ${PIP[p.status] ?? ""}`}>{p.status}</span>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      {/* Almanac footer */}
      <section className="grain-card p-8 rise-d3">
        <div className="grid grid-cols-3 gap-8 items-start">
          <div>
            <p className="kicker mb-2">Today’s reading</p>
            <p className="display-italic text-[28px] leading-tight">
              “Post with intent. Reply with patience.”
            </p>
          </div>
          <div>
            <p className="kicker mb-2">This week</p>
            <p className="text-[14px]">{channels.data?.total ?? 0} channel{(channels.data?.total ?? 0) === 1 ? "" : "s"} · {posts.data?.total ?? 0} post{(posts.data?.total ?? 0) === 1 ? "" : "s"} · {ideas.data?.total ?? 0} idea{(ideas.data?.total ?? 0) === 1 ? "" : "s"}</p>
          </div>
          <div>
            <p className="kicker mb-2">Next up</p>
            <Link href="/queue" className="text-[14px] underline underline-offset-4 decoration-[color:var(--ember)]">Review queue slots →</Link>
            <a
              href="http://localhost:51735/iam/applications"
              target="_blank"
              rel="noreferrer"
              className="mt-3 block border-l-2 border-[color:var(--ember)] bg-[color:var(--paper-deep)] px-3 py-2 hover:bg-[color:var(--paper)] transition group"
              title="Open the Tennetctl admin hub for this application"
              data-testid="ss-tennetctl-admin-card"
            >
              <p className="kicker text-[10px] text-[color:var(--ember)]">Applications Dashboard</p>
              <p className="mt-0.5 text-[13px] text-[color:var(--ink)] group-hover:text-[color:var(--ember)] transition">
                Open Tennetctl admin ↗
              </p>
            </a>
          </div>
        </div>
      </section>
    </div>
  );
}

function Tile({ kicker, value, href, divider = false }: { kicker: string; value: number | undefined; href: string; divider?: boolean }) {
  return (
    <Link
      href={href}
      className={`p-8 group hover:bg-[color:var(--paper-deep)] transition ${divider ? "border-l border-[color:var(--rule)]" : ""}`}
    >
      <p className="kicker">{kicker}</p>
      <div className="flex items-end gap-2 mt-4">
        <span className="display text-[72px] leading-none">{value ?? "—"}</span>
        <span className="kicker mb-3 group-hover:text-[color:var(--ember)] transition">visit →</span>
      </div>
    </Link>
  );
}

function EmptyState({ title, cta, href }: { title: string; cta: string; href: string }) {
  return (
    <div className="py-16 text-center">
      <p className="display-italic text-[28px] text-[color:var(--ink-70)] mb-4">{title}</p>
      <Link href={href} className="btn btn-ember">{cta} →</Link>
    </div>
  );
}
