"use client";
import { useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { ss } from "@/lib/api";
import type { ListPage, Post, PostStatus } from "@/types/api";
import { PostRow } from "@/features/posts/post-row";
import { SkeletonList } from "@/components/skeleton";

const STATUS_ORDER: (PostStatus | "all")[] = ["all", "draft", "queued", "scheduled", "published", "failed"];

export default function PostsPage() {
  const [filter, setFilter] = useState<PostStatus | "all">("all");
  const qs = filter === "all" ? "" : `?status=${filter}`;
  const posts = useQuery({ queryKey: ["posts", filter], queryFn: () => ss.get<ListPage<Post>>(`/v1/posts${qs}`) });

  return (
    <div className="max-w-6xl mx-auto rise">
      <div className="flex items-end justify-between mb-10">
        <div>
          <p className="kicker rule mb-3">The ledger</p>
          <h1 className="display text-[64px] leading-none">Posts.</h1>
        </div>
        <Link href="/composer" className="btn btn-ember">＋ New post</Link>
      </div>

      <div className="flex gap-1 mb-8 flex-wrap hairline-b pb-2">
        {STATUS_ORDER.map(s => (
          <button
            key={s} onClick={() => setFilter(s)}
            className={`px-3 py-1.5 text-[11px] tracking-widest uppercase mono
                        ${filter === s ? "bg-[color:var(--ink)] text-[color:var(--paper)]" : "text-[color:var(--ink-70)] hover:text-[color:var(--ink)]"}`}
          >
            {s}
          </button>
        ))}
      </div>

      {posts.isLoading ? <SkeletonList rows={4} /> :
       (posts.data?.items.length ?? 0) === 0 ? (
        <div className="py-20 text-center">
          <p className="display-italic text-[32px] text-[color:var(--ink-70)] mb-4">
            {filter === "all" ? "Nothing filed yet." : `No ${filter} posts.`}
          </p>
          <Link href="/composer" className="btn btn-ember">Write the first</Link>
        </div>
       ) : (
        <ul className="hairline-t">
          {posts.data!.items.map((p, i) => (
            <PostRow key={p.id} post={p} index={i} total={posts.data!.total} />
          ))}
        </ul>
       )}
    </div>
  );
}
