"use client";
import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { ss } from "@/lib/api";
import type { Post, PostStatus } from "@/types/api";
import { Spinner } from "@/components/fields";

const PIP: Record<string, string> = {
  draft: "pip-draft", queued: "pip-queued", scheduled: "pip-scheduled",
  publishing: "pip-publishing", published: "pip-published", failed: "pip-failed",
};

function fmt(ts: string | null | undefined): string {
  if (!ts) return "";
  return new Date(ts).toLocaleString("en-US", {
    month: "short", day: "numeric", hour: "numeric", minute: "2-digit",
  });
}

// Local ISO for <input type=datetime-local> (strips seconds + TZ).
function toLocalIso(ts: string | null): string {
  if (!ts) return "";
  const d = new Date(ts);
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

export function PostRow({ post, index, total }: { post: Post; index: number; total: number }) {
  const qc = useQueryClient();
  const editable = post.status !== "publishing" && post.status !== "published";
  const [open, setOpen] = useState(false);
  const [body, setBody] = useState(post.body);
  const [link, setLink] = useState(post.link ?? "");
  const [status, setStatus] = useState<PostStatus>(post.status);
  const [scheduledAt, setScheduledAt] = useState<string>(toLocalIso(post.scheduled_at));

  const patch = useMutation({
    mutationFn: (payload: Record<string, unknown>) => ss.patch<Post>(`/v1/posts/${post.id}`, payload),
    onSuccess: () => { setOpen(false); qc.invalidateQueries({ queryKey: ["posts"] }); },
  });
  const publish = useMutation({
    mutationFn: () => ss.post<Post>(`/v1/posts/${post.id}/publish`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["posts"] }),
  });
  const del = useMutation({
    mutationFn: () => ss.del(`/v1/posts/${post.id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["posts"] }),
  });

  function saveEdits() {
    const payload: Record<string, unknown> = {};
    if (body !== post.body) payload.body = body;
    if ((link || null) !== post.link) payload.link = link || null;
    if (status !== post.status) payload.status = status;
    // Always send scheduled_at when the status is scheduled; clear otherwise if it was set.
    if (status === "scheduled") {
      const iso = scheduledAt ? new Date(scheduledAt).toISOString() : null;
      if (iso !== post.scheduled_at) payload.scheduled_at = iso;
    } else if (post.scheduled_at) {
      payload.scheduled_at = null;
    }
    if (Object.keys(payload).length === 0) { setOpen(false); return; }
    patch.mutate(payload);
  }

  return (
    <li className="hairline-b py-6">
      <div className="grid grid-cols-[80px_1fr_auto] gap-6 items-start">
        <div className="mono text-[11px] text-[color:var(--ink-40)]">
          №{String(total - index).padStart(3, "0")}
        </div>
        <div className="min-w-0">
          <div className="flex items-center gap-4 mb-2 flex-wrap">
            <span className={`pip ${PIP[post.status] ?? ""}`}>{post.status}</span>
            <span className="mono text-[11px] text-[color:var(--ink-40)]">
              {fmt(post.created_at)}
            </span>
            {post.scheduled_at && (
              <span className="mono text-[11px] text-[color:var(--lapis)]">
                ↑ scheduled · {fmt(post.scheduled_at)}
              </span>
            )}
            {post.published_at && (
              <span className="mono text-[11px] text-[color:var(--sage)]">
                ✓ published · {fmt(post.published_at)}
              </span>
            )}
          </div>

          {!open ? (
            <button
              onClick={() => editable && setOpen(true)}
              className={`block text-left w-full ${editable ? "hover:opacity-80 cursor-pointer" : "cursor-default"}`}
              title={editable ? "Click to edit" : undefined}
            >
              <p className="display text-[22px] leading-[1.3] whitespace-pre-wrap">{post.body}</p>
            </button>
          ) : (
            <div className="paper-deep p-4 rise">
              <p className="kicker mb-2">Editing · click save when done</p>
              <textarea
                className="w-full min-h-[140px] bg-transparent resize-y outline-none
                           font-[Fraunces] text-[20px] leading-[1.4] placeholder:text-[color:var(--ink-20)]"
                value={body} onChange={e => setBody(e.target.value)} maxLength={10000} autoFocus
              />
              <div className="mt-3 hairline-t pt-3 space-y-3">
                <label className="block">
                  <span className="kicker block mb-1">Link (optional)</span>
                  <input className="boxed" value={link} onChange={e => setLink(e.target.value)} placeholder="https://…" />
                </label>
                <div className="grid grid-cols-[1fr_1fr] gap-3">
                  <label className="block">
                    <span className="kicker block mb-1">Status</span>
                    <select className="boxed" value={status} onChange={e => setStatus(e.target.value as PostStatus)}>
                      <option value="draft">draft</option>
                      <option value="queued">queued</option>
                      <option value="scheduled">scheduled</option>
                    </select>
                  </label>
                  {status === "scheduled" && (
                    <label className="block">
                      <span className="kicker block mb-1">Publish at</span>
                      <input className="boxed" type="datetime-local"
                             value={scheduledAt} onChange={e => setScheduledAt(e.target.value)} required />
                    </label>
                  )}
                </div>
              </div>
              {patch.isError && (
                <div className="mt-3 mono text-[12px] text-[color:var(--ember-deep)]">
                  × {(patch.error as Error).message}
                </div>
              )}
              <div className="mt-4 flex gap-2">
                <button className="btn btn-ember" disabled={patch.isPending} onClick={saveEdits}>
                  {patch.isPending ? <><Spinner /> Saving…</> : "Save →"}
                </button>
                <button className="btn" onClick={() => {
                  setOpen(false);
                  setBody(post.body); setLink(post.link ?? "");
                  setStatus(post.status); setScheduledAt(toLocalIso(post.scheduled_at));
                }}>Cancel</button>
              </div>
            </div>
          )}

          {post.link && !open && (
            <a href={post.link} target="_blank" rel="noreferrer"
               className="inline-block mt-2 mono text-[11px] text-[color:var(--ember-deep)] underline underline-offset-4">
              ↗ {post.link}
            </a>
          )}
          {post.external_url && (
            <a href={post.external_url} target="_blank" rel="noreferrer"
               className="inline-block mt-2 ml-4 mono text-[11px] text-[color:var(--sage)] underline underline-offset-4">
              ↗ view on provider
            </a>
          )}
        </div>

        <div className="flex flex-col gap-2 shrink-0">
          {!open && editable && (
            <>
              <button className="btn btn-ember text-[11px]" disabled={publish.isPending}
                      onClick={() => publish.mutate()}>
                {publish.isPending ? <><Spinner /> Publishing…</> : "Publish now"}
              </button>
              <button className="btn-ghost text-[11px] mono uppercase tracking-wider"
                      onClick={() => setOpen(true)}>edit</button>
            </>
          )}
          <button
            className="btn-ghost text-[11px] mono uppercase tracking-wider hover:text-[color:var(--ember-deep)]"
            onClick={() => { if (confirm("Delete this post?")) del.mutate(); }}
          >delete</button>
        </div>
      </div>
    </li>
  );
}
