"use client";
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { ss } from "@/lib/api";
import type { Idea, ListPage } from "@/types/api";
import { SkeletonCard } from "@/components/skeleton";

export default function IdeasPage() {
  const qc = useQueryClient();
  const ideas = useQuery({ queryKey: ["ideas"], queryFn: () => ss.get<ListPage<Idea>>("/v1/ideas") });

  const [title, setTitle] = useState("");
  const [notes, setNotes] = useState("");

  const create = useMutation({
    mutationFn: (payload: Record<string, unknown>) => ss.post<Idea>("/v1/ideas", payload),
    onSuccess: () => { setTitle(""); setNotes(""); qc.invalidateQueries({ queryKey: ["ideas"] }); },
  });
  const del = useMutation({
    mutationFn: (id: string) => ss.del(`/v1/ideas/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["ideas"] }),
  });

  return (
    <div className="max-w-5xl mx-auto rise">
      <div className="mb-10">
        <p className="kicker rule mb-3">The commonplace book</p>
        <h1 className="display text-[64px] leading-none">
          <span className="display-italic">Ideas</span>, in waiting.
        </h1>
      </div>

      {/* Add */}
      <form
        className="grain-card p-8 mb-12"
        onSubmit={e => { e.preventDefault(); if (title.trim()) create.mutate({ title, notes: notes || null, tags: [] }); }}
      >
        <p className="kicker mb-4">Note something down</p>
        <input
          className="w-full bg-transparent outline-none display text-[28px] placeholder:text-[color:var(--ink-20)] placeholder:italic border-b border-dashed border-[color:var(--rule)] pb-2 mb-3"
          value={title} onChange={e => setTitle(e.target.value)}
          placeholder="A new idea…" required
        />
        <textarea
          className="w-full bg-transparent outline-none resize-none text-[14px] text-[color:var(--ink-70)] placeholder:italic placeholder:text-[color:var(--ink-20)] py-2"
          value={notes} onChange={e => setNotes(e.target.value)}
          placeholder="Expand briefly (optional)…" rows={3}
        />
        <div className="mt-2 flex justify-end">
          <button className="btn btn-ember" disabled={!title.trim() || create.isPending}>
            {create.isPending ? "Saving…" : "File away →"}
          </button>
        </div>
      </form>

      {/* Ideas grid — staggered magazine spread */}
      {ideas.isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {Array.from({ length: 4 }).map((_, i) => <SkeletonCard key={i} />)}
        </div>
      ) : (ideas.data?.items.length ?? 0) === 0 ? (
        <p className="display-italic text-[26px] text-[color:var(--ink-40)] py-8">
          Nothing jotted down yet.
        </p>
      ) : (
        <ul className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {ideas.data!.items.map((i, idx) => (
            <li
              key={i.id}
              className={`paper p-6 group relative ${idx % 3 === 0 ? "md:rotate-[-0.4deg]" : idx % 3 === 1 ? "md:rotate-[0.3deg]" : ""}`}
            >
              <div className="flex items-start justify-between gap-3 mb-3">
                <span className="kicker">no. {String(idx + 1).padStart(3, "0")}</span>
                <button
                  className="opacity-0 group-hover:opacity-100 transition text-[color:var(--ink-40)] hover:text-[color:var(--ember-deep)] text-sm"
                  onClick={() => del.mutate(i.id)}
                  title="Delete"
                >×</button>
              </div>
              <p className="display text-[24px] leading-tight mb-2">{i.title}</p>
              {i.notes && (
                <p className="text-[13px] text-[color:var(--ink-70)] whitespace-pre-wrap leading-relaxed">{i.notes}</p>
              )}
              <div className="mt-4 flex items-center justify-between gap-3">
                <p className="mono text-[10px] text-[color:var(--ink-40)]">
                  filed {new Date(i.created_at).toLocaleDateString("en-US", { month: "short", day: "numeric" })}
                </p>
                <a
                  href={`/composer?title=${encodeURIComponent(i.title)}${i.notes ? `&body=${encodeURIComponent(i.notes)}` : ""}`}
                  className="mono text-[10px] uppercase tracking-widest text-[color:var(--ember-deep)] hover:text-[color:var(--ember)]"
                  title="Turn this idea into a post"
                >
                  → turn into post
                </a>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
